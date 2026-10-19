import gzip
import inspect
import json
import os
from pathlib import Path

import httpx
import pytest

from flashdata import (
    APIError,
    AsyncFlashData,
    FlashData,
    JobFailedError,
    JobPausedError,
    PollingTimeoutError,
    ProtocolError,
    RequestTimeoutError,
    ResponseTooLargeError,
    SubmissionUnknownError,
    ValidationError,
)

EXAMPLES = json.loads((Path(__file__).parent / "fixtures/source-examples.json").read_text())
JOB = "job_example123"
BULK = "bulk_example123"
KEY = "test-key-never-real"
STORAGE = "https://results.example"


async def invoke(function, *args, **kwargs):
    result = function(*args, **kwargs)
    return await result if inspect.isawaitable(result) else result


@pytest.fixture(params=[False, True], ids=["sync", "async"])
async def client_factory(request):
    clients = []

    def factory(handler=None, **options):
        calls = []

        def handle(req):
            calls.append(req)
            if handler:
                return handler(req)
            return httpx.Response(200, json={"ok": True})

        client = (AsyncFlashData if request.param else FlashData)(
            api_key=KEY, transport=httpx.MockTransport(handle), **options
        )
        clients.append(client)
        return client, calls

    yield factory
    for client in clients:
        await invoke(client.aclose if isinstance(client, AsyncFlashData) else client.close)


@pytest.mark.parametrize("source", list(EXAMPLES))
async def test_all_sources_use_real_wire_contract(client_factory, source):
    expected = EXAMPLES[source]["request"]
    client, calls = client_factory(lambda req: httpx.Response(200, json=EXAMPLES[source]["response"]))
    before = json.loads(json.dumps(expected))
    resource = getattr(client, source.split("_")[0])
    method = source.split("_", 1)[1]
    method = "license_check" if method == "trainability" else method
    main = next(k for k in ("query", "video_id", "handle") if k in expected)
    result = await invoke(getattr(resource, method), expected[main], **expected.get("params", {}))
    assert result == EXAMPLES[source]["response"]
    assert json.loads(calls[0].content) == expected
    assert calls[0].url.path == ("/v1/queries" if source == "youtube_download" else "/v1/queries/realtime")
    assert calls[0].headers["x-api-key"] == KEY
    assert expected == before


@pytest.mark.parametrize("source", list(EXAMPLES))
async def test_background_sources_and_callback(client_factory, source):
    client, calls = client_factory()
    query = {**EXAMPLES[source]["request"], "callback_url": "https://callbacks.example/completed"}
    await invoke(client.queries.submit, query)
    assert json.loads(calls[0].content) == query
    assert calls[0].url.path == "/v1/queries"
    assert len(calls) == 1


async def test_batch_preserves_each_source_and_false(client_factory):
    client, calls = client_factory()
    queries = [v["request"] for v in EXAMPLES.values()]
    await invoke(client.queries.batch, queries)
    assert json.loads(calls[0].content) == {"queries": queries}
    assert calls[0].url.path == "/v1/queries/batch"
    await invoke(client.youtube.metadata, "dQw4w9WgXcQ", include_formats=False, include_chapters=False)
    assert json.loads(calls[-1].content)["params"] == {"include_formats": False, "include_chapters": False}


@pytest.mark.parametrize(
    "query",
    [
        {},
        {"source": "unknown", "query": "x"},
        {"source": "google_search", "query": ""},
        {"source": "google_search", "query": "x", "params": {"num": True}},
        {"source": "youtube_metadata", "video_id": "../secret"},
        {"source": "youtube_search", "query": "x", "params": {"max_results": 21}},
        {"source": "youtube_transcript", "video_id": "dQw4w9WgXcQ", "params": {"auto": "false"}},
        {"source": "google_search", "query": "x", "api_key": KEY},
    ],
)
async def test_invalid_inputs_do_not_send_requests(client_factory, query):
    client, calls = client_factory()
    with pytest.raises(ValidationError):
        await invoke(client.queries.realtime, query)
    assert not calls


async def test_validation_hides_secrets_and_rejects_bad_modes(client_factory):
    client, calls = client_factory()
    with pytest.raises(ValidationError) as error:
        await invoke(
            client.youtube.download, "dQw4w9WgXcQ", storage={"storage_type": "bad", "secret_key": "hidden-secret"}
        )
    assert "hidden-secret" not in str(error.value)
    with pytest.raises(ValidationError):
        await invoke(client.google.search, "x", mode="batch")
    with pytest.raises(ValidationError):
        await invoke(client.google.search, "x", callback_url="https://example.com/callback")
    with pytest.raises(ValidationError):
        await invoke(client.queries.realtime, EXAMPLES["youtube_download"]["request"])
    with pytest.raises(ValidationError):
        await invoke(client.jobs.get, "job_x/../../account")
    assert not calls


async def test_account_and_public_routes(client_factory):
    client, calls = client_factory()
    await invoke(client.account.access)
    await invoke(client.account.balance)
    await invoke(client.account.limits)
    await invoke(client.account.pricing, source="youtube_metadata", request_count=3)
    await invoke(client.account.usage, source="google_search", from_="2026-01-01T00:00:00Z", to="2026-01-02T00:00:00Z")
    assert [r.url.path for r in calls] == [
        "/v2/api-access",
        "/v2/api-access/balance",
        "/v2/api-access/limits",
        "/v2/api-access/pricing",
        "/v2/usage",
    ]
    assert calls[3].url.params["request_count"] == "3"
    assert calls[4].url.params["from"] == "2026-01-01T00:00:00Z"
    for method in ("sources", "plans", "status", "health"):
        await invoke(getattr(client.public, method))
        assert "x-api-key" not in calls[-1].headers
    assert KEY not in repr(client)


def result_handler(req):
    if req.url.host == "results.example":
        assert "x-api-key" not in req.headers
        assert "authorization" not in req.headers
        assert "cookie" not in req.headers
        return httpx.Response(200, json={"completed": True})
    if req.url.path == "/v2/api-access":
        return httpx.Response(200, json={"sources": [], "result_origin": STORAGE})
    return httpx.Response(302, headers={"location": STORAGE + "/private/result?signature=private"})


async def test_signed_results_never_forward_api_credentials(client_factory):
    client, calls = client_factory(result_handler)
    assert await invoke(client.jobs.result, JOB) == {"completed": True}
    assert len(calls) == 3
    assert [r.url.host for r in calls] == ["api.flashdata.dev", "api.flashdata.dev", "results.example"]


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example/result",
        "http://results.example/file",
        "https://user:pass@results.example/file",
        "https://results.example/file#fragment",
    ],
)
async def test_invalid_signed_origins_never_receive_requests(client_factory, url):
    def handler(req):
        if req.url.path == "/v2/api-access":
            return httpx.Response(200, json={"result_origin": STORAGE})
        return httpx.Response(302, headers={"location": url})

    client, calls = client_factory(handler)
    with pytest.raises(ProtocolError):
        await invoke(client.jobs.result, JOB)
    assert len(calls) == 2


async def test_storage_redirect_is_not_followed(client_factory):
    def handler(req):
        if req.url.host == "results.example":
            return httpx.Response(302, headers={"location": "https://evil.example"})
        return result_handler(req)

    client, calls = client_factory(handler)
    with pytest.raises(APIError) as error:
        await invoke(client.jobs.result, JOB)
    assert error.value.status_code == 302
    assert len(calls) == 3


@pytest.mark.parametrize("status", [400, 401, 402, 403, 404, 409, 410, 422, 429, 500, 503])
async def test_http_errors_are_structured_and_not_retried(client_factory, status):
    client, calls = client_factory(
        lambda req: httpx.Response(
            status,
            json={"code": "test_error", "message": f"Failure {KEY}"},
            headers={"Retry-After": "3", "X-Request-ID": "req_123"},
        )
    )
    with pytest.raises(APIError) as error:
        await invoke(client.google.search, "test")
    assert error.value.status_code == status
    assert error.value.code == "test_error"
    assert error.value.retry_after == "3"
    assert error.value.request_id == "req_123"
    assert KEY not in str(error.value)
    assert len(calls) == 1


async def test_mutation_timeout_is_unknown_and_never_retried(client_factory):
    def timeout(req):
        raise httpx.ReadTimeout("private url and key", request=req)

    client, calls = client_factory(timeout)
    with pytest.raises(SubmissionUnknownError):
        await invoke(client.google.search, "test")
    assert len(calls) == 1
    with pytest.raises(RequestTimeoutError):
        await invoke(client.account.balance)
    assert len(calls) == 2


async def test_malformed_and_oversized_responses(client_factory):
    client, _ = client_factory(lambda req: httpx.Response(200, content=b"not json"))
    with pytest.raises(ProtocolError):
        await invoke(client.account.balance)
    client, _ = client_factory(lambda req: httpx.Response(200, content=b"x" * 21), max_response_bytes=20)
    with pytest.raises(ResponseTooLargeError):
        await invoke(client.account.balance)


async def test_wait_reads_same_job_without_resubmitting(client_factory):
    statuses = iter(["pending", "processing", "completed"])
    client, calls = client_factory(lambda req: httpx.Response(200, json={"job": {"id": JOB, "status": next(statuses)}}))
    result = await invoke(client.jobs.wait, JOB, timeout=1, poll_interval=0.001)
    assert result["status"] == "completed"
    assert len(calls) == 3 and all(r.method == "GET" and r.url.path == "/v2/jobs/" + JOB for r in calls)


@pytest.mark.parametrize("status", ["failed", "paused", "cancelled"])
async def test_bulk_wait_stops_for_user_action(client_factory, status):
    client, calls = client_factory(lambda req: httpx.Response(200, json={"job": {"id": BULK, "status": status}}))
    with pytest.raises(JobPausedError if status == "paused" else JobFailedError):
        await invoke(client.bulk.wait, BULK, timeout=1, poll_interval=0.001)
    assert len(calls) == 1


async def test_wait_timeout_and_failed_job(client_factory):
    client, calls = client_factory(lambda req: httpx.Response(200, json={"job": {"id": JOB, "status": "pending"}}))
    with pytest.raises(PollingTimeoutError) as error:
        await invoke(client.jobs.wait, JOB, timeout=0.005, poll_interval=0.002)
    assert error.value.job_id == JOB
    assert all(r.method == "GET" for r in calls)
    client, _ = client_factory(lambda req: httpx.Response(200, json={"job": {"id": JOB, "status": "failed"}}))
    with pytest.raises(JobFailedError):
        await invoke(client.jobs.wait, JOB)


async def test_complete_bulk_lifecycle_and_streamed_upload(client_factory, tmp_path):
    created = {
        "job": {"id": BULK},
        "upload": {
            "method": "PUT",
            "contentType": "text/plain; charset=utf-8",
            "href": STORAGE + "/input?sig=hidden",
            "expiresAt": "2100-01-01T00:00:00Z",
        },
    }
    path = tmp_path / "ids.txt"
    path.write_text("dQw4w9WgXcQ\n" * 10000)

    def handler(req):
        if req.url.host == "results.example":
            assert "x-api-key" not in req.headers
            assert len(req.content) == path.stat().st_size
            assert req.headers["content-type"] == "text/plain; charset=utf-8"
            return httpx.Response(200)
        if req.url.path == "/v2/api-access":
            return httpx.Response(200, json={"result_origin": STORAGE})
        if req.method == "POST" and req.url.path == "/v2/bulk-jobs":
            return httpx.Response(201, json=created)
        if req.url.path == "/v2/bulk-jobs" and req.method == "GET":
            return httpx.Response(200, json={"data": [], "pagination": {"hasMore": False, "limit": 20}})
        return httpx.Response(200, json={"job": {"id": BULK, "status": "running"}})

    client, calls = client_factory(handler)
    collection = await invoke(client.bulk.create, {"source": "youtube_metadata", "options": {"include_formats": False}})
    await invoke(client.bulk.upload_file, collection, path)
    for action in ("start", "get", "pause", "resume", "cancel"):
        assert (await invoke(getattr(client.bulk, action), BULK))["id"] == BULK
    await invoke(client.bulk.update, BULK, {"callback_url": None})
    await invoke(client.bulk.list, cursor="next-cursor", limit=20)
    assert json.loads(next(r for r in calls if r.method == "PATCH").content) == {"callback_url": None}
    assert any(r.method == "DELETE" for r in calls)


async def test_gzip_bulk_parts_and_manifest(client_factory):
    rows = [{"index": 0, "status": "completed"}, {"index": 1, "status": "invalid"}]
    compressed = gzip.compress(("\n".join(json.dumps(r) for r in rows) + "\n").encode())

    def handler(req):
        if req.url.host == "results.example":
            return (
                httpx.Response(200, content=compressed)
                if req.url.path == "/part"
                else httpx.Response(200, json={"parts": [{"number": 0}]})
            )
        if req.url.path == "/v2/api-access":
            return httpx.Response(200, json={"result_origin": STORAGE})
        return httpx.Response(
            302, headers={"location": STORAGE + ("/part" if req.url.path.endswith("/0") else "/manifest")}
        )

    client, _ = client_factory(handler)
    assert await invoke(client.bulk.manifest, BULK) == {"parts": [{"number": 0}]}
    iterator = client.bulk.iter_rows(BULK, 0)
    actual = [row async for row in iterator] if hasattr(iterator, "__aiter__") else list(iterator)
    assert actual == rows


async def test_google_pagination_budget_and_early_stop(client_factory):
    def handler(req):
        page = json.loads(req.content)["params"]["page"]
        return httpx.Response(
            200, json={"source": "google_search", "results": [{"organic": [{"title": "one"}] if page == 1 else []}]}
        )

    client, calls = client_factory(handler)
    iterator = client.google.pages("google_search", "coffee", max_pages=5)
    rows = [row async for row in iterator] if hasattr(iterator, "__aiter__") else list(iterator)
    assert len(rows) == len(calls) == 2
    assert [json.loads(r.content)["params"]["page"] for r in calls] == [1, 2]


async def test_google_pagination_consumer_break(client_factory):
    client, calls = client_factory(lambda req: httpx.Response(200, json={"results": [{"organic": [{"title": "one"}]}]}))
    iterator = client.google.pages("google_search", "coffee", max_pages=5)
    if hasattr(iterator, "__aiter__"):
        async for _ in iterator:
            break
        await iterator.aclose()
    else:
        for _ in iterator:
            break
        iterator.close()
    assert len(calls) == 1


async def test_missing_redirect_is_a_protocol_error(client_factory):
    client, calls = client_factory(lambda req: httpx.Response(302))
    with pytest.raises(ProtocolError):
        await invoke(client.jobs.result, JOB)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"data_url": "http://external.example"},
        {"management_url": "https://example.com/v2"},
        {"timeout": 0},
        {"max_response_bytes": -1},
    ],
)
def test_invalid_client_configuration(kwargs):
    with pytest.raises(ValidationError):
        FlashData(api_key=KEY, **kwargs)


@pytest.mark.live
@pytest.mark.skipif(
    os.getenv("FLASHDATA_RUN_LIVE") != "1" or not os.getenv("FLASHDATA_LIVE_API_KEY"),
    reason="Set FLASHDATA_RUN_LIVE=1 and FLASHDATA_LIVE_API_KEY to enable live requests",
)
def test_live_free_account_access():
    with FlashData(api_key=os.environ["FLASHDATA_LIVE_API_KEY"]) as client:
        assert isinstance(client.account.access()["sources"], list)
