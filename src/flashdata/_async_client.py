from __future__ import annotations
import asyncio
import os
from pathlib import Path
from typing import Any
import httpx
from ._common import api_error, decode_json, origin, positive, secret_values, signed_url, integer
from .errors import (
    ConnectionError,
    ProtocolError,
    RequestTimeoutError,
    ResponseTooLargeError,
    SubmissionUnknownError,
    ValidationError,
)
from ._resources import AsyncQueries, AsyncAccount, AsyncJobs, AsyncBulk, AsyncGoogle, AsyncYouTube, AsyncPublic


class AsyncFlashData:
    """Asynchronous API-key client. No network requests are automatically retried."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        data_url: str = "https://data.flashdata.dev",
        management_url: str = "https://api.flashdata.dev",
        timeout: float = 120,
        max_response_bytes: int = 64 * 1024 * 1024,
        transport: Any = None,
        storage_transport: Any = None,
    ):
        key = api_key if api_key is not None else os.environ.get("FLASHDATA_API_KEY", "")
        if not isinstance(key, str) or not key.strip() or any(c in key for c in "\r\n"):
            raise ValidationError("Set FLASHDATA_API_KEY or pass a non-empty api_key.")
        self._key = key.strip()
        self.data_url, self.management_url = origin(data_url), origin(management_url)
        self.timeout = positive(timeout, "timeout")
        self.max_response_bytes = integer(max_response_bytes, "max_response_bytes", 1, 2**53 - 1)
        self._http = httpx.AsyncClient(transport=transport, timeout=timeout, follow_redirects=False)
        self._storage = httpx.AsyncClient(
            transport=storage_transport if storage_transport is not None else transport,
            timeout=timeout,
            follow_redirects=False,
        )
        self.queries = AsyncQueries(self)
        self.account = AsyncAccount(self)
        self.jobs = AsyncJobs(self)
        self.bulk = AsyncBulk(self)
        self.google = AsyncGoogle(self)
        self.youtube = AsyncYouTube(self)
        self.public = AsyncPublic(self)

    def __repr__(self) -> str:
        return "<AsyncFlashData>"

    async def __aenter__(self) -> AsyncFlashData:
        return self

    async def __aexit__(self, *_args: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()
        await self._storage.aclose()

    async def _read(self, response: httpx.Response) -> bytes:
        content = bytearray()
        async for chunk in response.aiter_bytes():
            content.extend(chunk)
            if len(content) > self.max_response_bytes:
                raise ResponseTooLargeError("Response exceeds max_response_bytes.")
        return bytes(content)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        params: Any = None,
        data: bool = False,
        public: bool = False,
        timeout: float | None = None,
        redirect: bool = False,
    ) -> Any:
        base = self.data_url if data else self.management_url
        url = base + ("" if data else "/v2") + path
        headers = {"Accept": "application/json", "User-Agent": "flashdata-python/0.1.0"}
        if not public:
            headers["X-API-Key"] = self._key
        try:
            async with self._http.stream(
                method,
                url,
                headers=headers,
                params=params,
                json=body,
                timeout=timeout if timeout is not None else self.timeout,
            ) as response:
                if redirect and response.status_code == 302:
                    location = response.headers.get("location")
                    if not location:
                        raise ProtocolError("Signed result redirect is missing its location.")
                    return location
                raw = await self._read(response)
                if not 200 <= response.status_code < 300:
                    raise api_error(response, raw, (self._key,) + secret_values(body))
                return decode_json(raw)
        except httpx.TimeoutException:
            if method != "GET":
                raise SubmissionUnknownError(
                    "Submission response was lost. Check Jobs before submitting again."
                ) from None
            raise RequestTimeoutError("Read request timed out.") from None
        except httpx.RequestError:
            if method != "GET":
                raise SubmissionUnknownError(
                    "Submission response was lost. Check Jobs before submitting again."
                ) from None
            raise ConnectionError("Network request failed.") from None

    async def _result(self, path: str, *, binary: bool = False) -> Any:
        location = await self._request("GET", path, redirect=True)
        if not isinstance(location, str):
            # Supports a future direct JSON response without exposing credentials to storage.
            if binary:
                raise ProtocolError("Expected a signed result redirect.")
            return location
        access = await self.account.access()
        url = signed_url(location, access.get("result_origin"))
        try:
            async with self._storage.stream("GET", url, headers={"Accept": "application/json"}) as response:
                raw = await self._read(response)
                if not 200 <= response.status_code < 300:
                    raise api_error(response, raw, (self._key, url))
                return raw if binary else decode_json(raw)
        except httpx.TimeoutException:
            raise RequestTimeoutError("Signed result read timed out.") from None
        except httpx.RequestError:
            raise ConnectionError("Signed result read failed.") from None

    async def _upload(self, created: dict[str, Any], path: str | os.PathLike[str]) -> None:
        upload = created.get("upload", {})
        if upload.get("method") != "PUT" or upload.get("contentType") != "text/plain; charset=utf-8":
            raise ProtocolError("Invalid bulk upload descriptor.")
        file = Path(path)
        size = file.stat().st_size
        if not 0 < size <= 2147483648:
            raise ValidationError("Bulk input must contain 1 byte to 2 GiB of UTF-8 video IDs.")
        access = await self.account.access()
        url = signed_url(upload.get("href"), access.get("result_origin"))

        async def chunks():
            with file.open("rb") as stream:
                while True:
                    chunk = await asyncio.to_thread(stream.read, 65536)
                    if not chunk:
                        break
                    yield chunk

        try:
            async with self._storage.stream(
                "PUT",
                url,
                content=chunks(),
                headers={
                    "Content-Type": upload["contentType"],
                    "Content-Length": str(size),
                },
            ) as response:
                raw = await self._read(response)
                if not 200 <= response.status_code < 300:
                    raise api_error(response, raw, (self._key, url))
        except httpx.RequestError:
            raise ConnectionError(
                "Bulk input upload failed. The bulk ID remains available; upload and start separately."
            ) from None
