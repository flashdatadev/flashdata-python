"""Both clients preserve the server's negotiated response bodies and error handling."""

import inspect
import json
from pathlib import Path

import httpx
import pytest

from flashdata import APIError, AsyncFlashData, FlashData, ProtocolError, ResponseTooLargeError, ValidationError
from response_fixtures import STORED_CASES, format_fixture

ROOT = Path(__file__).parents[1]
CASES = json.loads((ROOT / "tests/fixtures/response-formats.json").read_text(encoding="utf-8"))
SOURCES = json.loads((ROOT / "tests/fixtures/source-examples.json").read_text(encoding="utf-8"))
FORMATS = [
    (accept, representation) for accept in ("application/json", "text/plain") for representation in (None, "markdown")
]
STORED_MATRIX = [(source, case) for source, cases in STORED_CASES.items() for case in cases]


async def invoke(method, *args, **kwargs):
    result = method(*args, **kwargs)
    return await result if inspect.isawaitable(result) else result


@pytest.fixture(params=[False, True], ids=["sync", "async"])
async def make_client(request):
    clients = []

    def make(handler, **kwargs):
        calls = []

        def handle(req):
            calls.append(req)
            return handler(req)

        client = (AsyncFlashData if request.param else FlashData)(
            api_key="format-test-key", transport=httpx.MockTransport(handle), **kwargs
        )
        clients.append(client)
        return client, calls

    yield make
    for client in clients:
        await invoke(client.aclose if isinstance(client, AsyncFlashData) else client.close)


def reply(value):
    if isinstance(value, str):
        return httpx.Response(200, text=value, headers={"Content-Type": "text/plain; charset=utf-8"})
    return httpx.Response(200, json=value)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["group"] + ":" + str(c["headers"]))
async def test_server_generated_examples(make_client, case):
    client, calls = make_client(lambda req: reply(case["response"]))
    options = {"accept": case["headers"]["Accept"]}
    if "X-Respond-With" in case["headers"]:
        options["respond_with"] = case["headers"]["X-Respond-With"]
    group = case["group"]
    if group == "status":
        result = await invoke(client.jobs.get, "job_example", **options)
    else:
        method = {"async": client.queries.submit, "batch": client.queries.batch}.get(group, client.queries.realtime)
        body = case["request"]["queries"] if group == "batch" else case["request"]
        result = await invoke(method, body, **options)
        assert json.loads(calls[0].content) == case["request"]
    expected = case["response"]
    if group == "status" and isinstance(expected, dict):
        expected = expected["job"]
    assert result == expected
    assert len(calls) == 1
    assert calls[0].headers["accept"] == options["accept"]
    assert calls[0].headers.get("x-respond-with") == options.get("respond_with")


@pytest.mark.parametrize("case", CASES)
def test_documentation_formatter_matches_api_generated_examples(case):
    original = next(
        item["response"]
        for item in CASES
        if item["group"] == case["group"] and item["headers"] == {"Accept": "application/json"}
    )
    representation = case["headers"].get("X-Respond-With")
    markdown = next(
        (
            item["response"]["content"]
            for item in CASES
            if item["group"] == case["group"]
            and item["headers"] == {"Accept": "application/json", "X-Respond-With": "markdown"}
        ),
        None,
    )
    assert format_fixture(original, case["headers"]["Accept"], representation, markdown=markdown) == case["response"]


@pytest.mark.parametrize("source,case", STORED_MATRIX)
async def test_completed_results_preserve_server_generated_metadata(make_client, source, case):
    original = STORED_CASES[source][0]["response"]
    formatted = case["accept"] == "text/plain" or case["respond_with"] is not None

    def handle(req):
        if req.url.path.endswith("/results"):
            return (
                reply(case["response"])
                if formatted
                else httpx.Response(302, headers={"Location": "https://results.example/stored"})
            )
        if req.url.path.endswith("/api-access"):
            return reply({"result_origin": "https://results.example"})
        assert req.url.host == "results.example" and "x-api-key" not in req.headers
        return reply(original)

    client, calls = make_client(handle)
    result = await invoke(client.jobs.result, original["id"], accept=case["accept"], respond_with=case["respond_with"])
    assert result == case["response"]
    assert format_fixture(original, case["accept"], case["respond_with"]) == result
    metadata = {key: value for key, value in original.items() if key != "results"}
    if isinstance(result, dict):
        assert {key: result[key] for key in metadata} == metadata
        assert ("content" in result) == (case["respond_with"] == "markdown")
        assert ("results" in result) == (case["respond_with"] is None)
    else:
        assert 'Id: "job_fixture0001"' in result and 'Status: "completed"' in result
        assert 'Completed at: "2026-10-23T00:00:00Z"' in result and 'Expires at: "2026-10-24T00:00:00Z"' in result
    assert len(calls) == (1 if formatted else 3)


@pytest.mark.parametrize("source", [s for s in SOURCES if s != "youtube_download"])
@pytest.mark.parametrize("accept,respond_with", FORMATS)
async def test_every_realtime_helper_sends_headers_outside_params(make_client, source, accept, respond_with):
    request = SOURCES[source]["request"]
    value = (
        "Source: café\nResults: 你好\n"
        if accept == "text/plain"
        else {"content": "# Example"}
        if respond_with
        else {"results": []}
    )
    client, calls = make_client(lambda req: reply(value))
    resource, method = source.split("_", 1)
    method = "license_check" if method == "trainability" else method
    main = next(k for k in ("query", "video_id", "handle") if k in request)
    result = await invoke(
        getattr(getattr(client, resource), method),
        request[main],
        accept=accept,
        respond_with=respond_with,
        **request.get("params", {}),
    )
    assert result == value
    assert json.loads(calls[0].content) == request
    assert calls[0].headers["accept"] == accept
    assert calls[0].headers.get("x-respond-with") == respond_with


@pytest.mark.parametrize("accept,respond_with", FORMATS)
async def test_completed_result_formats_and_default_signed_redirect(make_client, accept, respond_with):
    formatted = accept == "text/plain" or respond_with is not None
    # URL-shaped content must never be interpreted as a storage redirect.
    value = (
        "https://results.example/this-is-content\n你好"
        if accept == "text/plain"
        else {"content": "# Result"}
        if respond_with
        else {"results": []}
    )

    def handle(req):
        if req.url.path.endswith("/results"):
            assert req.headers["accept"] == accept
            assert req.headers.get("x-respond-with") == respond_with
            return (
                reply(value)
                if formatted
                else httpx.Response(302, headers={"Location": "https://results.example/stored"})
            )
        if req.url.path.endswith("/api-access"):
            assert req.headers["accept"] == "application/json"
            assert "x-respond-with" not in req.headers
            return reply({"result_origin": "https://results.example"})
        assert req.url.host == "results.example"
        assert "x-api-key" not in req.headers and "x-respond-with" not in req.headers
        return reply(value)

    client, calls = make_client(handle)
    assert await invoke(client.jobs.result, "job_example", accept=accept, respond_with=respond_with) == value
    assert len(calls) == (1 if formatted else 3)


@pytest.mark.parametrize("source", list(SOURCES))
async def test_background_helpers_support_text_receipts(make_client, source):
    request = SOURCES[source]["request"]
    client, calls = make_client(lambda req: reply('Id: "job_example"\nStatus: "pending"\n'))
    resource, method = source.split("_", 1)
    method = "license_check" if method == "trainability" else method
    main = next(k for k in ("query", "video_id", "handle") if k in request)
    result = await invoke(
        getattr(getattr(client, resource), method),
        request[main],
        mode="async",
        accept="text/plain",
        **request.get("params", {}),
    )
    assert isinstance(result, str)
    assert calls[0].url.path == "/v1/queries"
    assert "x-respond-with" not in calls[0].headers
    assert json.loads(calls[0].content) == request


@pytest.mark.parametrize(
    "options",
    [
        {"accept": "text/html"},
        {"respond_with": "html"},
        {"accept": None},
        {"respond_with": []},
        {"mode": "async", "respond_with": "markdown"},
    ],
)
async def test_invalid_formats_fail_before_submission(make_client, options):
    client, calls = make_client(lambda req: reply({}))
    with pytest.raises(ValidationError):
        await invoke(client.google.search, "coffee", **options)
    assert not calls


@pytest.mark.parametrize("status", [400, 406, 409, 410, 429, 500])
async def test_plain_text_requests_preserve_structured_errors(make_client, status):
    client, calls = make_client(
        lambda req: httpx.Response(
            status, json={"error": "Example error", "code": "EXAMPLE"}, headers={"X-Request-ID": "request_example"}
        )
    )
    with pytest.raises(APIError) as error:
        await invoke(client.google.search, "coffee", accept="text/plain", respond_with="markdown")
    assert error.value.status_code == status and error.value.code == "EXAMPLE"
    assert error.value.request_id == "request_example"
    assert len(calls) == 1


@pytest.mark.parametrize("raw,error", [(b"\xff", ProtocolError), (b"x" * 11, ResponseTooLargeError)])
async def test_plain_text_decoding_and_size_limits(make_client, raw, error):
    client, _ = make_client(lambda req: httpx.Response(200, content=raw), max_response_bytes=10)
    with pytest.raises(error):
        await invoke(client.jobs.result, "job_example", accept="text/plain")


async def test_format_choices_do_not_leak_to_other_calls(make_client):
    def handle(req):
        if req.headers["accept"] == "text/plain":
            return reply("Source: google_search\n")
        if "/jobs/" in req.url.path:
            return reply({"job": {"id": "job_example", "status": "completed"}})
        if "/bulk-jobs/" in req.url.path:
            return reply({"job": {"id": "bulk_example123", "status": "completed"}})
        return reply({"results": [], "status": "ok"})

    client, calls = make_client(handle)
    await invoke(client.google.search, "coffee", accept="text/plain", respond_with="markdown")
    await invoke(client.jobs.wait, "job_example")
    await invoke(client.account.balance)
    await invoke(client.public.health)
    await invoke(client.bulk.get, "bulk_example123")
    assert isinstance(await invoke(client.google.search, "coffee"), dict)
    for req in calls[1:]:
        assert req.headers["accept"] == "application/json" and "x-respond-with" not in req.headers


def test_contract_documents_format_headers_only_on_supported_routes():
    spec = json.loads((ROOT / "openapi.json").read_text(encoding="utf-8"))
    for path, method in [("/v1/queries/realtime", "post"), ("/jobs/{jobId}/results", "get")]:
        operation = spec["paths"][path][method]
        assert set(operation["responses"]["200"]["content"]) == {"application/json", "text/plain"}
        assert {p.get("$ref", "").rsplit("/", 1)[-1] for p in operation["parameters"]} >= {
            "QueryRepresentation",
            "QueryRepresentationAccept",
        }
    for path, method in [("/v1/queries", "post"), ("/v1/queries/batch", "post"), ("/jobs/{jobId}", "get")]:
        operation = spec["paths"][path][method]
        assert "text/plain" in next(v["content"] for k, v in operation["responses"].items() if k.startswith("2"))
        assert all(not p.get("$ref", "").endswith("/QueryRepresentation") for p in operation["parameters"])
