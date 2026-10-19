import inspect
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from flashdata import AsyncFlashData, FlashData


@pytest.mark.parametrize("async_mode", [False, True])
async def test_real_http_origins_redirect_and_streamed_upload(async_mode, tmp_path):
    seen = []

    class Storage(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(("storage", dict(self.headers)))
            body = json.dumps({"stored": True}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_PUT(self):
            seen.append(("upload", dict(self.headers)))
            assert self.rfile.read(int(self.headers["Content-Length"])) == b"dQw4w9WgXcQ\n"
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_args):
            pass

    storage = ThreadingHTTPServer(("127.0.0.1", 0), Storage)
    storage_url = f"http://127.0.0.1:{storage.server_port}"

    class API(BaseHTTPRequestHandler):
        def do_GET(self):
            assert self.headers["X-API-Key"] == "local-http-key"
            if self.path == "/v2/api-access":
                body = json.dumps({"sources": [], "result_origin": storage_url}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(302)
                self.send_header("Location", storage_url + "/result?signed=local-only")
                self.send_header("Set-Cookie", "private=api-cookie")
                self.send_header("Content-Length", "0")
                self.end_headers()

        def do_POST(self):
            assert self.headers["X-API-Key"] == "local-http-key"
            body = self.rfile.read(int(self.headers["Content-Length"]))
            value = json.loads(body)
            assert value["params"]["autocorrect"] is False
            raw = json.dumps({"source": value["source"], "status": "done", "results": []}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), API)
    api_url = f"http://127.0.0.1:{server.server_port}"
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (storage, server)]
    for thread in threads:
        thread.start()
    client = (AsyncFlashData if async_mode else FlashData)("local-http-key", data_url=api_url, management_url=api_url)

    async def invoke(method, *args, **kwargs):
        result = method(*args, **kwargs)
        return await result if inspect.isawaitable(result) else result

    path = tmp_path / "ids.txt"
    path.write_bytes(b"dQw4w9WgXcQ\n")
    try:
        assert (await invoke(client.google.search, "coffee", autocorrect=False))["status"] == "done"
        assert await invoke(client.jobs.result, "job_local123") == {"stored": True}
        await invoke(
            client.bulk.upload_file,
            {
                "job": {"id": "bulk_local123"},
                "upload": {
                    "method": "PUT",
                    "contentType": "text/plain; charset=utf-8",
                    "href": storage_url + "/input",
                },
            },
            path,
        )
        assert {name for name, _ in seen} == {"storage", "upload"}
        assert all(
            not any(k.lower() in ("x-api-key", "authorization", "cookie") for k in headers) for _, headers in seen
        )
    finally:
        await invoke(client.aclose if async_mode else client.close)
        for item in (server, storage):
            item.shutdown()
            item.server_close()
        for thread in threads:
            thread.join()
