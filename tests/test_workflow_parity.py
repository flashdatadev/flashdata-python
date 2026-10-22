"""Recovery guarantees shared with the TypeScript CLI examples."""

import ast
import asyncio
import json
from pathlib import Path
import runpy
import sys

import pytest

from flashdata import APIError

ROOT = Path(__file__).parents[1]


def test_bulk_row_failure_is_reported_even_when_final_counts_are_zero(example_api, monkeypatch, tmp_path):
    from flashdata._resources import Bulk

    def rows(self, bulk_id):
        yield {"status": "invalid", "video_id": "dQw4w9WgXcQ"}

    monkeypatch.setattr(Bulk, "rows", rows)
    monkeypatch.setattr(sys, "argv", ["bulk.py", "video-ids.txt", "--output", "invalid.ndjson"])
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(ROOT / "examples/bulk.py"), run_name="__main__")
    assert error.value.code == 1
    assert json.loads((tmp_path / "invalid.ndjson").read_text())["status"] == "invalid"


@pytest.mark.parametrize("flags,kind,format_", [([], "audio_video", "mp4"), (["--audio"], "audio", "mp3")])
def test_bulk_media_examples_send_audio_or_video_options(flags, kind, format_, example_api, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["bulk_download.py", "video-ids.txt", *flags])
    runpy.run_path(str(ROOT / "examples/bulk_download.py"), run_name="__main__")
    created = [r for r in example_api if r.method == "POST" and r.url.path.endswith("/bulk-jobs")]
    options = json.loads(created[0].content)["options"]
    assert options["download_type"] == kind and options["output_format"] == format_
    assert ("video_quality" in options) == (kind == "audio_video")
    assert options["storage"]


@pytest.mark.parametrize("name", ["bulk", "bulk_download"])
@pytest.mark.parametrize("existing", ["export.ndjson", "export.ndjson.job.json"])
def test_existing_bulk_exports_or_records_block_submission(name, existing, example_api, monkeypatch, tmp_path):
    previous = tmp_path / existing
    previous.write_text("preserve this record", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [name + ".py", "video-ids.txt", "--output", "export.ndjson"])
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(ROOT / f"examples/{name}.py"), run_name="__main__")
    assert error.value.code == 1 and not example_api
    assert previous.read_text(encoding="utf-8") == "preserve this record"


@pytest.mark.parametrize("name", ["bulk", "bulk_download"])
def test_bulk_ids_survive_lost_start_and_reruns_never_create(name, example_api, monkeypatch, tmp_path):
    from flashdata._resources import Bulk

    original_upload, original_start = Bulk.upload_file, Bulk.start
    record = tmp_path / "export.ndjson.job.json"

    def upload(self, receipt, path):
        assert json.loads(record.read_text())["id"] == receipt["job"]["id"]
        assert "upload" not in json.loads(record.read_text())
        return original_upload(self, receipt, path)

    def lost_start(self, bulk_id, **kwargs):
        original_start(self, bulk_id, **kwargs)
        raise OSError("simulated lost start response")

    monkeypatch.setattr(Bulk, "upload_file", upload)
    monkeypatch.setattr(Bulk, "start", lost_start)
    monkeypatch.setattr(sys, "argv", [name + ".py", "video-ids.txt", "--output", "export.ndjson"])
    with pytest.raises(SystemExit):
        runpy.run_path(str(ROOT / f"examples/{name}.py"), run_name="__main__")
    accepted = record.read_bytes()
    before = len(example_api)
    for orphaned_record in (False, True):
        if orphaned_record:
            (tmp_path / "export.ndjson").unlink()
        with pytest.raises(SystemExit):
            runpy.run_path(str(ROOT / f"examples/{name}.py"), run_name="__main__")
        assert len(example_api) == before and record.read_bytes() == accepted
    monkeypatch.setattr(sys, "argv", [name + ".py", "--bulk-id", "bulk_docs12345", "--output", "recovered.ndjson"])
    runpy.run_path(str(ROOT / f"examples/{name}.py"), run_name="__main__")
    assert all(request.method == "GET" for request in example_api[before:])
    assert json.loads((tmp_path / "recovered.ndjson").read_text())["status"] == "completed"


@pytest.mark.parametrize("name", ["bulk", "bulk_download", "async_query"])
@pytest.mark.parametrize("value", ["0", "nan"])
def test_invalid_wait_argument_never_submits(name, value, example_api, monkeypatch):
    monkeypatch.setattr(sys, "argv", [name + ".py", "video-ids.txt", "--wait-timeout", value])
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(ROOT / f"examples/{name}.py"), run_name="__main__")
    assert error.value.code == 1 and not example_api


@pytest.mark.parametrize("name", ["bulk", "bulk_download"])
def test_empty_bulk_input_never_creates_a_task(name, example_api, monkeypatch, tmp_path):
    path = tmp_path / "empty.txt"
    path.touch()
    monkeypatch.setattr(sys, "argv", [name + ".py", str(path)])
    with pytest.raises(SystemExit):
        runpy.run_path(str(ROOT / f"examples/{name}.py"), run_name="__main__")
    assert not example_api


@pytest.mark.parametrize("name", ["bulk", "bulk_download"])
def test_partial_bulk_exports_and_saved_ids_survive_item_failure(name, example_api, monkeypatch, tmp_path):
    from flashdata._resources import Bulk

    original = Bulk.wait

    def failed_wait(self, *args, **kwargs):
        completed = original(self, *args, **kwargs)
        completed["counts"]["failed"] = 1
        return completed

    monkeypatch.setattr(Bulk, "wait", failed_wait)
    output = tmp_path / "partial.ndjson"
    monkeypatch.setattr(sys, "argv", [name + ".py", "video-ids.txt", "--output", str(output)])
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(ROOT / f"examples/{name}.py"), run_name="__main__")
    assert error.value.code == 1
    assert json.loads(output.read_text().strip())["status"] == "completed"
    job = json.loads(Path(str(output) + ".job.json").read_text())
    assert job["counts"]["failed"] == 1 and "upload" not in job


def test_concurrent_search_keeps_successes_and_errors_and_bounds_workers(example_api, monkeypatch, tmp_path):
    from flashdata._resources import AsyncGoogle

    active = peak = 0
    original = AsyncGoogle.search

    async def search(self, query, **params):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        try:
            await asyncio.sleep(0.001)
            if query == "bad":
                raise APIError(429, "Limited", code="limited", request_id="request-1", retry_after="2")
            return await original(self, query, **params)
        finally:
            active -= 1

    monkeypatch.setattr(AsyncGoogle, "search", search)
    output = tmp_path / "searches.json"
    monkeypatch.setattr(
        sys, "argv", ["async_client.py", "coffee", "bad", "tea", "--concurrency", "2", "--output", str(output)]
    )
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(ROOT / "examples/async_client.py"), run_name="__main__")
    assert error.value.code == 1 and peak <= 2
    results = json.loads(output.read_text())
    assert [item["query"] for item in results] == ["coffee", "bad", "tea"]
    assert "response" in results[0] and "response" in results[2]
    assert results[1]["error"]["request_id"] == "request-1"


def test_every_example_and_documentation_client_has_an_explicit_key():
    paths = [
        *ROOT.glob("examples/*.py"),
        *ROOT.glob("*.md"),
        *(p for p in ROOT.glob("docs/**/*.md") if "_build" not in p.parts),
    ]
    import re

    for path in paths:
        text = path.read_text(encoding="utf-8")
        blocks = [text] if path.suffix == ".py" else re.findall(r"```python\n(.*?)```", text, re.S)
        for code in blocks:
            for node in ast.walk(ast.parse(code)):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in ("FlashData", "AsyncFlashData")
                ):
                    assert any(keyword.arg == "api_key" for keyword in node.keywords), path


def test_bulk_and_wire_types_reject_invalid_options(tmp_path):
    from mypy import api

    code = """from flashdata import FlashData
from flashdata.types import AsyncQuery, CreateBulkJobRequest, StorageConfig
storage: StorageConfig={"storage_type":"s3","storage_url":"bucket"}
valid: CreateBulkJobRequest={"source":"youtube_download","options":{"storage":storage}}
disabled: CreateBulkJobRequest={"source":"youtube_metadata","options":{"result_storage":None}}
with FlashData(api_key="offline") as client:
    response=client.google.search("coffee")
    credits: dict = response["usage"]
    receipt=client.youtube.metadata("dQw4w9WgXcQ",mode="async")
    client.jobs.wait(receipt["id"])
    sources=client.public.sources()["data"]
    result=client.jobs.result(receipt["id"])
    completed: str=result["completed_at"]
wrong_query: AsyncQuery={"source":"google_search","query":"coffee","params":{"num":"5"}}
missing_storage: CreateBulkJobRequest={"source":"youtube_download"}
wrong_options: CreateBulkJobRequest={"source":"youtube_metadata","options":{"auto":True}}
bad_created_at: str=result["created_at"]
"""
    path = tmp_path / "consumer.py"
    path.write_text(code)
    stdout, stderr, status = api.run([str(path), "--follow-imports=normal"])
    assert status == 1, stdout + stderr
    for line in [14, 15, 16, 17]:
        assert f"consumer.py:{line}: error:" in stdout, stdout
    for line in range(1, 14):
        assert f"consumer.py:{line}: error:" not in stdout, stdout
