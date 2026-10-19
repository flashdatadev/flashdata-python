"""Explicit production integration suite. These tests consume credits when enabled."""

import json
import os
from pathlib import Path

import pytest

from flashdata import APIError, AsyncFlashData, FlashData

ENABLED = os.environ.get("FLASHDATA_RUN_LIVE") == "1" and bool(os.environ.get("FLASHDATA_LIVE_API_KEY"))
pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not ENABLED, reason="Set FLASHDATA_RUN_LIVE=1 and FLASHDATA_LIVE_API_KEY to enable paid integration tests"
    ),
]
EXAMPLES = json.loads((Path(__file__).parent / "fixtures/source-examples.json").read_text())
DATA_SOURCES = [s for s in EXAMPLES if s != "youtube_download"]


@pytest.fixture
def live_client():
    with FlashData(os.environ["FLASHDATA_LIVE_API_KEY"], timeout=180) as client:
        yield client


@pytest.mark.parametrize("source", DATA_SOURCES)
def test_realtime_source(live_client, source):
    response = live_client.queries.realtime(EXAMPLES[source]["request"])
    assert response["source"] == source and response["status"] == "done"
    assert isinstance(response["results"], list) and response["results"]
    assert isinstance(response["usage"]["credits"], (int, float))


def test_account_and_public_contracts(live_client):
    assert set(live_client.account.access()["sources"]) == set(EXAMPLES)
    assert isinstance(live_client.account.balance()["availableCredits"], (int, float))
    assert live_client.account.pricing(source="google_search")["prices"]
    assert live_client.account.limits()["limits"]["batchSize"] > 0
    assert isinstance(live_client.account.usage()["totals"], dict)
    assert {s["id"] for s in live_client.public.sources()["data"]} == set(EXAMPLES)
    assert live_client.public.plans()["currency"] == "USD"
    assert live_client.public.health()["status"]
    assert live_client.public.status()["status"]


def test_background_and_all_data_sources_in_batch(live_client):
    receipt = live_client.google.search("coffee", mode="async", num=3, timeout=180)
    assert live_client.jobs.wait(receipt["id"], timeout=300, poll_interval=3)["status"] == "completed"
    assert live_client.jobs.result(receipt["id"])["source"] == "google_search"
    batch = live_client.queries.batch([EXAMPLES[s]["request"] for s in DATA_SOURCES])
    assert len(batch["queries"]) == len(DATA_SOURCES)
    for item in batch["queries"]:
        assert item.get("id"), item.get("error")
        assert live_client.jobs.wait(item["id"], timeout=300, poll_interval=3)["status"] == "completed"
        result = live_client.jobs.result(item["id"])
        assert result["source"] == item["source"] and result["results"]


def test_bulk_upload_export_and_draft_controls(live_client, tmp_path):
    draft = live_client.bulk.create({"source": "youtube_metadata"})
    draft_id = draft["job"]["id"]
    live_client.bulk.update(draft_id, {"options": {"include_formats": False}})
    assert live_client.bulk.cancel(draft_id)["status"] == "cancelled"
    receipt = live_client.bulk.create({"source": "youtube_metadata", "options": {"include_formats": False}})
    bulk_id = receipt["job"]["id"]
    path = tmp_path / "ids.txt"
    path.write_text("dQw4w9WgXcQ\ninvalid\n", encoding="utf-8")
    live_client.bulk.upload_file(receipt, path)
    live_client.bulk.start(bulk_id)
    completed = live_client.bulk.wait(bulk_id, timeout=360, poll_interval=3)
    assert completed["counts"]["completed"] == 1 and completed["counts"]["invalid"] == 1
    manifest = live_client.bulk.manifest(bulk_id)
    assert manifest["parts"] and manifest["expires_at"]
    rows = list(live_client.bulk.rows(bulk_id))
    assert len(rows) == 1 and rows[0]["video_id"] == "dQw4w9WgXcQ"
    assert rows[0]["status"] == "completed" and rows[0]["results"]
    assert list(live_client.bulk.iter_jobs(max_pages=2, limit=1))


async def test_async_client(live_client):
    async with AsyncFlashData(os.environ["FLASHDATA_LIVE_API_KEY"], timeout=180) as client:
        response = await client.youtube.metadata("dQw4w9WgXcQ", include_formats=False, timeout=180)
        assert response["results"][0]["videoId"] == "dQw4w9WgXcQ"
        jobs = [j async for j in client.bulk.iter_jobs(max_pages=1, limit=1)]
        assert jobs


def test_management_error_metadata(live_client):
    with pytest.raises(APIError) as error:
        live_client.jobs.get("job_sdk_review_nonexistent")
    assert error.value.status_code == 404
    assert error.value.request_id
