"""Source-shaped transport for executable documentation and CLI tests."""

import gzip
import json
from pathlib import Path

import httpx
import pytest
from flashdata import AsyncFlashData, FlashData

ROOT = Path(__file__).parents[1]
FIXTURES = json.loads((ROOT / "tests/fixtures/source-examples.json").read_text())


@pytest.fixture
def example_api(monkeypatch, tmp_path):
    calls = []
    jobs = {}

    def handle(request):
        calls.append(request)
        path = request.url.path
        if request.url.host == "results.example":
            if request.method == "PUT":
                return httpx.Response(200)
            if path == "/manifest":
                return httpx.Response(200, json={"parts": [{"number": 0}]})
            if path == "/part":
                row = {
                    "index": 0,
                    "status": "completed",
                    "video_id": "dQw4w9WgXcQ",
                    "results": [{"title": "Example video"}],
                }
                return httpx.Response(200, content=gzip.compress((json.dumps(row) + "\n").encode()))
            job_id = path.rsplit("/", 1)[-1]
            return httpx.Response(200, json=FIXTURES[jobs.get(job_id, "google_search")]["response"])
        if path.startswith("/v1/"):
            data = json.loads(request.content)
            if path.endswith("/realtime"):
                return httpx.Response(200, json=FIXTURES[data["source"]]["response"])
            if path.endswith("/batch"):
                receipts = []
                for index, item in enumerate(data["queries"]):
                    job_id = f"job_docs{index}"
                    jobs[job_id] = item["source"]
                    receipts.append({"id": job_id, "source": item["source"], "status": "pending"})
                return httpx.Response(200, json={"queries": receipts, "total_credits": 0.02})
            jobs["job_docs123"] = data["source"]
            return httpx.Response(200, json={"id": "job_docs123", "source": data["source"], "status": "pending"})
        if path.endswith("/api-access"):
            return httpx.Response(200, json={"sources": list(FIXTURES), "result_origin": "https://results.example"})
        if path.endswith("/balance"):
            return httpx.Response(200, json={"availableCredits": 100})
        if path.endswith("/pricing"):
            return httpx.Response(200, json={"prices": []})
        if path.endswith("/limits"):
            return httpx.Response(200, json={"limits": {"batchSize": 100, "concurrency": 5}})
        if path.endswith("/usage"):
            return httpx.Response(200, json={"totals": {}})
        if path.endswith("/catalog/sources"):
            return httpx.Response(200, json={"data": [{"id": s} for s in FIXTURES]})
        if path.endswith(("/health", "/status")):
            return httpx.Response(200, json={"status": "ok"})
        if "/jobs/" in path:
            if path.endswith("/results"):
                return httpx.Response(
                    302, headers={"location": "https://results.example/result/" + path.split("/")[-2]}
                )
            return httpx.Response(200, json={"job": {"id": path.split("/")[-1], "status": "completed"}})
        if "/bulk-jobs" in path:
            job = {
                "id": "bulk_docs12345",
                "status": "completed",
                "counts": {"accepted": 1, "completed": 1, "failed": 0, "invalid": 0},
            }
            if request.method == "POST" and path.endswith("/bulk-jobs"):
                return httpx.Response(
                    201,
                    json={
                        "job": job,
                        "upload": {
                            "method": "PUT",
                            "contentType": "text/plain; charset=utf-8",
                            "href": "https://results.example/input",
                        },
                    },
                )
            if path.endswith("/results"):
                return httpx.Response(302, headers={"location": "https://results.example/manifest"})
            if "/results/" in path:
                return httpx.Response(302, headers={"location": "https://results.example/part"})
            if path.endswith("/bulk-jobs"):
                return httpx.Response(200, json={"data": [job], "pagination": {"hasMore": False}})
            return httpx.Response(200, json={"job": job})
        raise AssertionError(f"Unexpected example request: {request.method} {path}")

    clients = []

    def factory(async_=False, *args, **kwargs):
        # Test proxy documentation without opening any proxy connection.
        kwargs.pop("proxy", None)
        kwargs["transport"] = httpx.MockTransport(handle)
        if not args and "api_key" not in kwargs:
            kwargs["api_key"] = "example-test-key"
        client = (AsyncFlashData if async_ else FlashData)(*args, **kwargs)
        clients.append(client)
        return client

    monkeypatch.setattr("flashdata.FlashData", lambda *a, **kw: factory(False, *a, **kw))
    monkeypatch.setattr("flashdata.AsyncFlashData", lambda *a, **kw: factory(True, *a, **kw))
    monkeypatch.syspath_prepend(str(ROOT / "examples"))
    monkeypatch.chdir(tmp_path)
    (tmp_path / "video-ids.txt").write_text("dQw4w9WgXcQ\n", encoding="utf-8")
    storage = tmp_path / "private-storage.json"
    storage.write_text(json.dumps(FIXTURES["youtube_download"]["request"]["params"]["storage"]))
    monkeypatch.setenv("FLASHDATA_STORAGE_FILE", str(storage))
    monkeypatch.setenv("FLASHDATA_API_KEY", "example-test-key")
    yield calls
    for client in clients:
        if isinstance(client, FlashData):
            client.close()
