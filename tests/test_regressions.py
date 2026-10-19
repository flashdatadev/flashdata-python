"""Production failure modes discovered during the API and reference SDK review."""

import gzip
import inspect
import json
from types import SimpleNamespace
from typing import get_type_hints

import httpx
import pytest

from flashdata import (
    APIError,
    AsyncFlashData,
    FlashData,
    PollingTimeoutError,
    ProtocolError,
    ResponseTooLargeError,
    ValidationError,
)
from flashdata._common import result_rows
from flashdata.types import ApiAccess, YoutubeDownloadParams, YouTubeSearchFilters


@pytest.mark.parametrize("kind", [FlashData, AsyncFlashData])
@pytest.mark.parametrize("key", ["bad\tkey", "bad\x00key", "bad\x7fkey", "bad\nkey", "bad\u4e2dkey"])
def test_api_key_control_characters_reject_before_transport_creation(kind, key):
    with pytest.raises(ValidationError) as error:
        kind(api_key=key)
    assert key not in str(error.value)


async def call(method, *args, **kwargs):
    value = method(*args, **kwargs)
    return await value if inspect.isawaitable(value) else value


@pytest.fixture(params=[FlashData, AsyncFlashData], ids=["sync", "async"])
async def api(request):
    created = []

    def factory(handler, **options):
        client = request.param(api_key="test-key", transport=httpx.MockTransport(handler), **options)
        created.append(client)
        return client

    yield factory
    for client in created:
        await call(client.aclose if isinstance(client, AsyncFlashData) else client.close)


async def test_per_request_timeout_is_transport_option_not_source_param(api):
    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(200, json={"job": {"status": "completed"}})

    client = api(handle, timeout=120)
    await call(client.google.search, "coffee", timeout=7, num=3)
    await call(client.youtube.metadata, "dQw4w9WgXcQ", mode="async", timeout=9)
    await call(client.account.balance, timeout=11)
    await call(client.bulk.get, "bulk_testing123", timeout=13)
    assert [r.extensions["timeout"]["read"] for r in seen] == [7, 9, 11, 13]
    assert all("timeout" not in json.loads(r.content or b"{}").get("params", {}) for r in seen)
    with pytest.raises(ValidationError):
        await call(client.google.search, "coffee", timeout=0)
    assert len(seen) == 4


@pytest.mark.parametrize(
    "callback",
    [
        "https://localhost/path",
        "https://127.0.0.1/path",
        "https://example.com:bad/path",
        "https://[broken",
        "http://example.com",
        123,
    ],
)
async def test_callback_errors_stay_in_sdk_and_do_not_submit(api, callback):
    seen = []
    client = api(lambda r: seen.append(r))
    with pytest.raises(ValidationError):
        await call(client.queries.submit, {"source": "google_search", "query": "coffee", "callback_url": callback})
    with pytest.raises(ValidationError):
        await call(client.bulk.create, {"source": "youtube_metadata", "callback_url": callback})
    assert not seen


@pytest.mark.parametrize("source", [[], {}, None, 12])
async def test_invalid_source_never_leaks_type_error(api, source):
    client = api(lambda _: pytest.fail("must not submit"))
    with pytest.raises(ValidationError):
        await call(client.queries.realtime, {"source": source, "query": "coffee"})


async def test_error_attributes_include_management_problem_and_data_retry(api):
    client = api(
        lambda _: httpx.Response(
            422,
            json={
                "title": "Invalid input",
                "requestId": "req_body123",
                "fieldErrors": [{"field": "options", "code": "invalid"}],
                "retry_after": 3,
            },
        )
    )
    with pytest.raises(APIError) as caught:
        await call(client.account.access)
    assert caught.value.request_id == "req_body123"
    assert caught.value.retry_after == "3"
    assert caught.value.field_errors[0]["field"] == "options"


async def test_missing_job_envelope_raises_protocol_error(api):
    client = api(lambda _: httpx.Response(200, json={"unexpected": True}))
    with pytest.raises(ProtocolError):
        await call(client.jobs.get, "job_testing123")
    with pytest.raises(ProtocolError):
        await call(client.bulk.wait, "bulk_testing123", timeout=1)


@pytest.mark.parametrize("bulk", [False, True])
async def test_polling_deadline_preserves_id_on_request_timeout(api, bulk, monkeypatch):
    clock = [0.0]
    monkeypatch.setattr("flashdata._resources.time", SimpleNamespace(monotonic=lambda: clock[0]))

    def handle(request):
        clock[0] = 2.0
        raise httpx.ReadTimeout("timed out", request=request)

    client = api(handle)
    id_ = "bulk_testing123" if bulk else "job_testing123"
    resource = client.bulk if bulk else client.jobs
    with pytest.raises(PollingTimeoutError) as caught:
        await call(resource.wait, id_, timeout=1, poll_interval=0.1)
    assert caught.value.job_id == id_


async def collect(iterator):
    return [item async for item in iterator] if hasattr(iterator, "__aiter__") else list(iterator)


async def test_bulk_cursor_pages_are_bounded_and_checked(api):
    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(
            200,
            json={"data": [{"id": f"bulk_testing{len(seen)}"}], "pagination": {"hasMore": True, "nextCursor": "same"}},
        )

    client = api(handle)
    rows = await collect(client.bulk.iter_jobs(max_pages=1))
    assert len(rows) == len(seen) == 1
    with pytest.raises(ProtocolError):
        await collect(client.bulk.iter_jobs(max_pages=3))
    assert len(seen) == 3
    assert seen[-1].url.params["cursor"] == "same"


async def test_bulk_listing_detects_a_loop_back_to_the_initial_cursor(api):
    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(200, json={"data": [], "pagination": {"hasMore": True, "nextCursor": "initial"}})

    client = api(handle)
    with pytest.raises(ProtocolError):
        await collect(client.bulk.iter_jobs(max_pages=5, cursor="initial"))
    assert len(seen) == 1


async def test_bulk_rows_reject_duplicate_and_untrusted_part_descriptors(api):
    client = api(lambda _: httpx.Response(200, json={"parts": [{"number": -1, "href": "https://evil.example"}]}))
    with pytest.raises(ProtocolError):
        await collect(client.bulk.rows("bulk_testing123"))


@pytest.mark.parametrize(
    "raw",
    [b"\x1f\x8btruncated", gzip.compress(b'{"ok": true}\n')[:-4], b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\x07"],
)
def test_corrupt_gzip_uses_public_protocol_error(raw):
    with pytest.raises(ProtocolError):
        list(result_rows(raw, 10000, 1000))


def test_ndjson_memory_bounds_and_non_objects():
    with pytest.raises(ResponseTooLargeError):
        list(result_rows(gzip.compress(b'{"text":"' + b"a" * 1000 + b'"}\n'), 10000, 100))
    with pytest.raises(ResponseTooLargeError):
        list(result_rows(b'{"ok":1}\n' * 20, 50, 100))
    with pytest.raises(ProtocolError):
        list(result_rows(b"[]\n", 100, 100))


def test_runtime_required_keys_and_nested_hints_are_correct():
    assert ApiAccess.__required_keys__ == {"sources", "result_origin"}
    assert "storage" in YoutubeDownloadParams.__required_keys__
    assert "sort_by" in get_type_hints(YouTubeSearchFilters)


async def test_storage_origin_is_reused_for_many_parts(api):
    seen = []

    def handle(request):
        seen.append(request)
        if request.url.path == "/v2/api-access":
            return httpx.Response(200, json={"result_origin": "https://results.example"})
        if request.url.host == "results.example":
            assert "x-api-key" not in request.headers
            return httpx.Response(200, json={"results": []})
        return httpx.Response(302, headers={"location": "https://results.example/part"})

    client = api(handle)
    await call(client.jobs.result, "job_testing123")
    await call(client.jobs.result, "job_testing456")
    assert len([r for r in seen if r.url.path == "/v2/api-access"]) == 1
    assert len(seen) == 5


@pytest.mark.parametrize(
    "payload",
    [
        {"source": "youtube_metadata", "options": {"include_formats": "no"}},
        {"source": "youtube_trainability", "options": {"language": "en"}},
        {"source": "youtube_transcript", "options": {"auto": 1}},
    ],
)
async def test_bulk_source_options_are_validated_before_creation(api, payload):
    client = api(lambda _: pytest.fail("invalid options must not be submitted"))
    with pytest.raises(ValidationError):
        await call(client.bulk.create, payload)


@pytest.mark.parametrize("kind", [FlashData, AsyncFlashData])
async def test_public_discovery_without_credentials(kind, monkeypatch):
    monkeypatch.delenv("FLASHDATA_API_KEY", raising=False)
    seen = []

    def handle(request):
        seen.append(request)
        assert "x-api-key" not in request.headers
        return httpx.Response(200, json={"status": "ok"})

    client = kind(api_key=None, transport=httpx.MockTransport(handle))
    try:
        await call(client.public.health)
        with pytest.raises(ValidationError):
            await call(client.account.access)
        assert len(seen) == 1
    finally:
        await call(client.aclose if isinstance(client, AsyncFlashData) else client.close)
