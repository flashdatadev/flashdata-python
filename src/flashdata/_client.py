from __future__ import annotations
import os
import ssl
from pathlib import Path
from typing import Any
import httpx
from ._common import (
    api_error,
    decode_json,
    decode_response,
    origin,
    positive,
    secret_values,
    signed_url,
    integer,
    response_headers,
    ResultRedirect,
)
from .types import ResponseAccept, ContentRepresentation
from .errors import (
    ConnectionError,
    ProtocolError,
    RequestTimeoutError,
    ResponseTooLargeError,
    SubmissionUnknownError,
    ValidationError,
)
from ._resources import Queries, Account, Jobs, Bulk, Google, YouTube, Public


class FlashData:
    """Synchronous API-key client. No network requests are automatically retried."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        data_url: str = "https://data.flashdata.dev",
        management_url: str = "https://api.flashdata.dev",
        timeout: float = 120,
        max_response_bytes: int = 64 * 1024 * 1024,
        max_line_bytes: int = 16 * 1024 * 1024,
        transport: Any = None,
        storage_transport: Any = None,
        proxy: str | None = None,
        verify: ssl.SSLContext | bool = True,
        trust_env: bool = True,
    ):
        key = api_key if api_key is not None else os.environ.get("FLASHDATA_API_KEY", "")
        if not isinstance(key, str) or any(not "\x20" <= char <= "\x7e" for char in key):
            raise ValidationError("api_key must be an ASCII string without control characters.")
        self._key = key.strip()
        self._result_origin: str | None = None
        self.data_url, self.management_url = origin(data_url), origin(management_url)
        self.timeout = positive(timeout, "timeout")
        self.max_response_bytes = integer(max_response_bytes, "max_response_bytes", 1, 2**53 - 1)
        self.max_line_bytes = integer(max_line_bytes, "max_line_bytes", 1, 2**53 - 1)
        self._http = httpx.Client(
            transport=transport,
            timeout=timeout,
            follow_redirects=False,
            proxy=proxy,
            verify=verify,
            trust_env=trust_env,
        )
        self._storage = httpx.Client(
            transport=storage_transport if storage_transport is not None else transport,
            timeout=timeout,
            follow_redirects=False,
            proxy=proxy,
            verify=verify,
            trust_env=trust_env,
        )
        self.queries = Queries(self)
        self.account = Account(self)
        self.jobs = Jobs(self)
        self.bulk = Bulk(self)
        self.google = Google(self)
        self.youtube = YouTube(self)
        self.public = Public(self)

    def __repr__(self) -> str:
        return "<FlashData>"

    def __enter__(self) -> FlashData:
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()
        self._storage.close()

    def _read(self, response: httpx.Response) -> bytes:
        content = bytearray()
        for chunk in response.iter_bytes():
            content.extend(chunk)
            if len(content) > self.max_response_bytes:
                raise ResponseTooLargeError("Response exceeds max_response_bytes.")
        return bytes(content)

    def _request(
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
        accept: ResponseAccept = "application/json",
        respond_with: ContentRepresentation | None = None,
    ) -> Any:
        if not public and not self._key:
            raise ValidationError("Set FLASHDATA_API_KEY or pass api_key before calling an authenticated endpoint.")
        if timeout is not None:
            positive(timeout, "timeout")
        base = self.data_url if data else self.management_url
        url = base + ("" if data else "/v2") + path
        headers = response_headers(accept, respond_with)
        headers["User-Agent"] = "flashdata-python/1.1.0"
        if not public:
            headers["X-API-Key"] = self._key
        try:
            with self._http.stream(
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
                    return ResultRedirect(location)
                raw = self._read(response)
                if not 200 <= response.status_code < 300:
                    raise api_error(response, raw, (self._key,) + secret_values(body))
                return decode_response(raw, accept)
        except httpx.TimeoutException:
            if method != "GET":
                raise SubmissionUnknownError(
                    "Request response was lost; it may have been accepted. Reconcile before repeating it."
                ) from None
            raise RequestTimeoutError("Read request timed out.") from None
        except httpx.RequestError:
            if method != "GET":
                raise SubmissionUnknownError(
                    "Request response was lost; it may have been accepted. Reconcile before repeating it."
                ) from None
            raise ConnectionError("Network request failed.") from None

    def _result(
        self,
        path: str,
        *,
        binary: bool = False,
        timeout: float | None = None,
        accept: ResponseAccept = "application/json",
        respond_with: ContentRepresentation | None = None,
    ) -> Any:
        location = self._request(
            "GET",
            path,
            redirect=accept == "application/json" and respond_with is None,
            timeout=timeout,
            accept=accept,
            respond_with=respond_with,
        )
        if not isinstance(location, ResultRedirect):
            if binary:
                raise ProtocolError("Expected a signed result redirect.")
            return location
        if self._result_origin is None:
            self._result_origin = self.account.access(timeout=timeout).get("result_origin")
        url = signed_url(location.location, self._result_origin)
        try:
            with self._storage.stream(
                "GET",
                url,
                headers={"Accept": "application/json"},
                timeout=timeout if timeout is not None else self.timeout,
            ) as response:
                raw = self._read(response)
                if not 200 <= response.status_code < 300:
                    raise api_error(response, raw, (self._key, url))
                return raw if binary else decode_json(raw)
        except httpx.TimeoutException:
            raise RequestTimeoutError("Signed result read timed out.") from None
        except httpx.RequestError:
            raise ConnectionError("Signed result read failed.") from None

    def _upload(self, created: dict[str, Any], path: str | os.PathLike[str], *, timeout: float | None = None) -> None:
        if timeout is not None:
            positive(timeout, "timeout")
        if not isinstance(created, dict) or not isinstance(created.get("upload"), dict):
            raise ValidationError("Pass the complete receipt returned by bulk.create().")
        upload = created.get("upload", {})
        if upload.get("method") != "PUT" or upload.get("contentType") != "text/plain; charset=utf-8":
            raise ProtocolError("Invalid bulk upload descriptor.")
        file = Path(path)
        size = file.stat().st_size
        if not 0 < size <= 2147483648:
            raise ValidationError("Bulk input must contain 1 byte to 2 GiB of UTF-8 video IDs.")
        if self._result_origin is None:
            self._result_origin = self.account.access(timeout=timeout).get("result_origin")
        url = signed_url(upload.get("href"), self._result_origin)

        def chunks():
            with file.open("rb") as stream:
                while True:
                    chunk = stream.read(65536)
                    if not chunk:
                        break
                    yield chunk

        try:
            with self._storage.stream(
                "PUT",
                url,
                content=chunks(),
                timeout=timeout if timeout is not None else self.timeout,
                headers={
                    "Content-Type": upload["contentType"],
                    "Content-Length": str(size),
                },
            ) as response:
                raw = self._read(response)
                if not 200 <= response.status_code < 300:
                    raise api_error(response, raw, (self._key, url))
        except httpx.RequestError:
            raise ConnectionError(
                "Bulk input upload failed. The bulk ID remains available; upload and start separately."
            ) from None
