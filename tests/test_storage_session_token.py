import inspect
import json

import httpx
import pytest

from flashdata import APIError, AsyncFlashData, FlashData, ValidationError
from flashdata._common import redact, secret_values

PROVIDERS = ["s3", "s3_compatible", "oss", "cos", "bos", "tos"]
TOKEN = "fixture-temporary-session-token"


async def invoke(method, *args, **kwargs):
    value = method(*args, **kwargs)
    return await value if inspect.isawaitable(value) else value


@pytest.mark.parametrize("kind", [FlashData, AsyncFlashData])
@pytest.mark.parametrize("provider", PROVIDERS)
async def test_temporary_credentials_reach_every_storage_submission(kind, provider):
    seen = []

    def handle(request):
        seen.append(json.loads(request.content))
        if request.method == "PATCH":
            return httpx.Response(200, json={"job": {"id": "bulk_example123", "status": "paused"}})
        return httpx.Response(200, json={"id": "job_example123"})

    storage = {
        "storage_type": provider,
        "storage_url": "example-bucket",
        "access_key": "temp-key",
        "secret_key": "temp-secret",
        "session_token": TOKEN,
    }
    client = kind(api_key="test-key", transport=httpx.MockTransport(handle))
    try:
        await invoke(client.youtube.download, "dQw4w9WgXcQ", storage=storage)
        await invoke(
            client.queries.batch,
            [{"source": "youtube_download", "video_id": "dQw4w9WgXcQ", "params": {"storage": storage}}],
        )
        await invoke(client.bulk.create, {"source": "youtube_download", "options": {"storage": storage}})
        await invoke(client.bulk.create, {"source": "youtube_metadata", "options": {"result_storage": storage}})
        await invoke(
            client.bulk.update,
            "bulk_example123",
            {
                "options": {
                    "result_storage": {"access_key": "temp-key", "secret_key": "temp-secret", "session_token": TOKEN}
                }
            },
        )
    finally:
        await invoke(client.aclose if kind is AsyncFlashData else client.close)
    assert seen[0]["params"]["storage"] == storage
    assert seen[1]["queries"][0]["params"]["storage"] == storage
    assert seen[2]["options"]["storage"] == storage
    assert seen[3]["options"]["result_storage"] == storage
    assert seen[4]["options"]["result_storage"]["session_token"] == TOKEN


@pytest.mark.parametrize("token", ["", 42, "x" * 16385])
def test_invalid_token_rejected_without_request_or_secret_disclosure(token):
    with FlashData(
        api_key="test-key", transport=httpx.MockTransport(lambda _: pytest.fail("must not submit"))
    ) as client:
        with pytest.raises(ValidationError):
            client.youtube.download(
                "dQw4w9WgXcQ",
                storage={
                    "storage_type": "s3",
                    "storage_url": "bucket",
                    "access_key": "key",
                    "secret_key": "secret",
                    "session_token": token,
                },
            )


def test_token_redacted_from_structured_and_echoed_api_errors():
    storage = {
        "storage_type": "s3",
        "storage_url": "bucket",
        "access_key": "key",
        "secret_key": "secret",
        "session_token": TOKEN,
    }
    assert TOKEN in secret_values({"storage": storage})
    assert redact({"storage": storage})["storage"]["session_token"] == "[REDACTED]"
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            403, json={"code": "expired_token", "detail": f"Expired {TOKEN}", "session_token": TOKEN}
        )
    )
    with FlashData(api_key="test-key", transport=transport) as client:
        with pytest.raises(APIError) as error:
            client.youtube.download("dQw4w9WgXcQ", storage=storage)
    assert TOKEN not in str(error.value)
    assert TOKEN not in repr(vars(error.value))
