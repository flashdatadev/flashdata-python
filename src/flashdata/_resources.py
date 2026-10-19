from __future__ import annotations
import asyncio
import time
from typing import Any, Literal, overload
from typing_extensions import Unpack
from .types import (
    ApiAccess,
    ApiAccessBalance,
    ApiAccessLimits,
    ApiAccessPricing,
    ApiKeyUsage,
    AsyncQuery,
    AsyncSubmission,
    BatchResponse,
    BulkJob,
    BulkJobCreated,
    BulkJobPage,
    ConsoleJob,
    CreateBulkJobRequest,
    DataQueryResponse,
    GoogleImagesParams,
    GoogleImagesResponse,
    GoogleNewsParams,
    GoogleNewsResponse,
    GooglePlacesParams,
    GooglePlacesResponse,
    GoogleSearchParams,
    GoogleSearchResponse,
    GoogleShoppingParams,
    GoogleShoppingResponse,
    GoogleVideosParams,
    GoogleVideosResponse,
    RealtimeQuery,
    Source,
    SourceCatalog,
    Health,
    PlanCatalog,
    PublicStatus,
    JobResult,
    UpdateBulkJobRequest,
    YoutubeCaptionsParams,
    YoutubeCaptionsResponse,
    YoutubeChannelParams,
    YoutubeChannelResponse,
    YoutubeDownloadParams,
    YoutubeMetadataParams,
    YoutubeMetadataResponse,
    YoutubeSearchExtendedParams,
    YoutubeSearchExtendedResponse,
    YoutubeSearchParams,
    YoutubeSearchResponse,
    YoutubeSuggestionsParams,
    YoutubeSuggestionsResponse,
    YoutubeTrainabilityParams,
    YoutubeTrainabilityResponse,
    YoutubeTranscriptParams,
    YoutubeTranscriptResponse,
)
from ._common import SOURCES, bulk_input, identifier, integer, positive, validate_query, result_rows, job_record
from .errors import (
    JobFailedError,
    JobPausedError,
    PollingTimeoutError,
    RequestTimeoutError,
    ProtocolError,
    ValidationError,
)


class Resource:
    def __init__(self, client: Any):
        self._client = client


class Queries(Resource):
    def realtime(self, query: RealtimeQuery, *, timeout: float | None = None) -> DataQueryResponse:
        return self._client._request(
            "POST", "/v1/queries/realtime", data=True, body=validate_query(query), timeout=timeout
        )

    def submit(self, query: AsyncQuery, *, timeout: float | None = None) -> AsyncSubmission:
        return self._client._request(
            "POST", "/v1/queries", data=True, body=validate_query(query, async_mode=True), timeout=timeout
        )

    def batch(self, queries: list[AsyncQuery], *, timeout: float | None = None) -> BatchResponse:
        if not isinstance(queries, list) or not queries:
            raise ValidationError("Provide a non-empty list of queries; plan batch limits apply.")
        return self._client._request(
            "POST",
            "/v1/queries/batch",
            data=True,
            body={"queries": [validate_query(q, async_mode=True) for q in queries]},
            timeout=timeout,
        )


class Account(Resource):
    def access(self, *, timeout: float | None = None) -> ApiAccess:
        return self._client._request("GET", "/api-access", timeout=timeout)

    def balance(self, *, timeout: float | None = None) -> ApiAccessBalance:
        return self._client._request("GET", "/api-access/balance", timeout=timeout)

    def pricing(
        self, *, source: Source | None = None, request_count: int = 1, timeout: float | None = None
    ) -> ApiAccessPricing:
        integer(request_count, "request_count", 1, 100000)
        if source is not None and source not in SOURCES:
            raise ValidationError("Unknown pricing source.")
        params: dict[str, Any] = {"request_count": request_count}
        if source is not None:
            params["source"] = source
        return self._client._request("GET", "/api-access/pricing", params=params, timeout=timeout)

    def limits(self, *, timeout: float | None = None) -> ApiAccessLimits:
        return self._client._request("GET", "/api-access/limits", timeout=timeout)

    def usage(
        self,
        *,
        source: Source | None = None,
        from_: str | None = None,
        to: str | None = None,
        timeout: float | None = None,
    ) -> ApiKeyUsage:
        if source is not None and source not in SOURCES:
            raise ValidationError("Unknown usage source.")
        params = {k: v for k, v in {"source": source, "from": from_, "to": to}.items() if v is not None}
        return self._client._request("GET", "/usage", params=params, timeout=timeout)


class Public(Resource):
    def sources(self, *, timeout: float | None = None) -> SourceCatalog:
        return self._client._request("GET", "/catalog/sources", public=True, timeout=timeout)

    def plans(self, *, timeout: float | None = None) -> PlanCatalog:
        return self._client._request("GET", "/plans", public=True, timeout=timeout)

    def status(self, *, timeout: float | None = None) -> PublicStatus:
        return self._client._request("GET", "/status", public=True, timeout=timeout)

    def health(self, *, timeout: float | None = None) -> Health:
        return self._client._request("GET", "/health", public=True, timeout=timeout)


class Jobs(Resource):
    def get(self, job_id: str, *, timeout: float | None = None) -> ConsoleJob:
        return job_record(self._client._request("GET", "/jobs/" + identifier(job_id), timeout=timeout))

    def result(self, job_id: str, *, timeout: float | None = None) -> JobResult:
        return self._client._result("/jobs/" + identifier(job_id) + "/results", timeout=timeout)

    def wait(self, job_id: str, *, timeout: float = 300, poll_interval: float = 2) -> ConsoleJob:
        """Poll an existing ID without resubmitting or canceling accepted work."""
        identifier(job_id)
        deadline = time.monotonic() + positive(timeout, "timeout")
        positive(poll_interval, "poll_interval")
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(job_id)
            try:
                job = job_record(
                    self._client._request("GET", "/jobs/" + job_id, timeout=min(remaining, self._client.timeout))
                )
            except RequestTimeoutError:
                if time.monotonic() >= deadline:
                    raise PollingTimeoutError(job_id) from None
                raise
            if time.monotonic() >= deadline:
                raise PollingTimeoutError(job_id)
            status = job.get("status")
            if status == "completed":
                return job
            if status in ("failed",):
                raise JobFailedError(job)
            if status not in ("pending", "processing"):
                raise ProtocolError("Unexpected job status.")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(job_id)
            time.sleep(min(poll_interval, remaining))


class Bulk(Resource):
    def create(self, request: CreateBulkJobRequest, *, timeout: float | None = None) -> BulkJobCreated:
        return self._client._request("POST", "/bulk-jobs", body=bulk_input(request), timeout=timeout)

    def get(self, bulk_id: str, *, timeout: float | None = None) -> BulkJob:
        return job_record(self._client._request("GET", "/bulk-jobs/" + identifier(bulk_id, True), timeout=timeout))

    def list(self, *, cursor: str | None = None, limit: int = 20, timeout: float | None = None) -> BulkJobPage:
        integer(limit, "limit", 1, 50)
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        return self._client._request("GET", "/bulk-jobs", params=params, timeout=timeout)

    def update(self, bulk_id: str, request: UpdateBulkJobRequest, *, timeout: float | None = None) -> BulkJob:
        return job_record(
            self._client._request(
                "PATCH",
                "/bulk-jobs/" + identifier(bulk_id, True),
                body=bulk_input(request, partial=True),
                timeout=timeout,
            )
        )

    def upload_file(self, created: BulkJobCreated, path: Any, *, timeout: float | None = None) -> None:
        self._client._upload(created, path, timeout=timeout)

    def manifest(self, bulk_id: str, *, timeout: float | None = None) -> dict[str, Any]:
        return self._client._result("/bulk-jobs/" + identifier(bulk_id, True) + "/results", timeout=timeout)

    def part(self, bulk_id: str, part_number: int, *, timeout: float | None = None) -> bytes:
        integer(part_number, "part_number", 0, 2**53 - 1)
        return self._client._result(
            "/bulk-jobs/" + identifier(bulk_id, True) + "/results/" + str(part_number), binary=True, timeout=timeout
        )

    def iter_rows(self, bulk_id: str, part_number: int, *, timeout: float | None = None):
        """Iterate one bounded gzip/NDJSON part; decompressed lines use max_line_bytes."""
        raw = self.part(bulk_id, part_number, timeout=timeout)
        for row in result_rows(raw, self._client.max_response_bytes, self._client.max_line_bytes):
            yield row

    def wait(self, bulk_id: str, *, timeout: float = 3600, poll_interval: float = 5) -> BulkJob:
        """Poll an existing ID without resubmitting or canceling accepted work."""
        identifier(bulk_id, True)
        deadline = time.monotonic() + positive(timeout, "timeout")
        positive(poll_interval, "poll_interval")
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(bulk_id)
            try:
                job = job_record(
                    self._client._request("GET", "/bulk-jobs/" + bulk_id, timeout=min(remaining, self._client.timeout))
                )
            except RequestTimeoutError:
                if time.monotonic() >= deadline:
                    raise PollingTimeoutError(bulk_id) from None
                raise
            if time.monotonic() >= deadline:
                raise PollingTimeoutError(bulk_id)
            status = job.get("status")
            if status == "completed":
                return job
            if status == "paused":
                raise JobPausedError(job)
            if status in ("failed", "cancelled"):
                raise JobFailedError(job)
            if status not in ("awaiting_upload", "running", "finalizing"):
                raise ProtocolError("Unexpected job status.")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(bulk_id)
            time.sleep(min(poll_interval, remaining))

    def start(self, bulk_id: str, *, timeout: float | None = None) -> BulkJob:
        return job_record(
            self._client._request("POST", "/bulk-jobs/" + identifier(bulk_id, True) + "/start", timeout=timeout)
        )

    def pause(self, bulk_id: str, *, timeout: float | None = None) -> BulkJob:
        return job_record(
            self._client._request("POST", "/bulk-jobs/" + identifier(bulk_id, True) + "/pause", timeout=timeout)
        )

    def resume(self, bulk_id: str, *, timeout: float | None = None) -> BulkJob:
        return job_record(
            self._client._request("POST", "/bulk-jobs/" + identifier(bulk_id, True) + "/resume", timeout=timeout)
        )

    def cancel(self, bulk_id: str, *, timeout: float | None = None) -> BulkJob:
        return job_record(
            self._client._request("DELETE", "/bulk-jobs/" + identifier(bulk_id, True) + "", timeout=timeout)
        )

    def rows(self, bulk_id: str, *, timeout: float | None = None):
        """Yield all result rows in manifest order, buffering one bounded part."""
        manifest = self.manifest(bulk_id, timeout=timeout)
        parts = manifest.get("parts")
        if not isinstance(parts, list):
            raise ProtocolError("Bulk manifest is missing its parts list.")
        seen = set()
        for part in parts:
            if (
                not isinstance(part, dict)
                or type(part.get("number")) is not int
                or part["number"] < 0
                or part["number"] in seen
            ):
                raise ProtocolError("Invalid or duplicate bulk part number.")
            seen.add(part["number"])
            for row in self.iter_rows(bulk_id, part["number"], timeout=timeout):
                yield row

    def iter_jobs(self, *, max_pages: int, limit: int = 20, cursor: str | None = None, timeout: float | None = None):
        """Yield bulk job records from a bounded number of cursor pages."""
        integer(max_pages, "max_pages", 1, 1000)
        seen = {cursor} if cursor else set()
        for _ in range(max_pages):
            page = self.list(limit=limit, cursor=cursor, timeout=timeout)
            if not isinstance(page.get("data"), list) or not isinstance(page.get("pagination"), dict):
                raise ProtocolError("Invalid bulk listing response.")
            for job in page["data"]:
                if not isinstance(job, dict):
                    raise ProtocolError("Expected a bulk job object.")
                yield job
            pagination = page["pagination"]
            if not pagination.get("hasMore"):
                return
            cursor = pagination.get("nextCursor")
            if not isinstance(cursor, str) or not cursor or cursor in seen:
                raise ProtocolError("Bulk listing returned an invalid or repeated cursor.")
            seen.add(cursor)


class Google(Resource):
    @overload
    def search(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleSearchParams],
    ) -> GoogleSearchResponse: ...
    @overload
    def search(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleSearchParams],
    ) -> AsyncSubmission: ...
    def search(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleSearchParams],
    ) -> Any:
        """google_search: https://flashdata.dev/docs/sources/google_search"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "google_search", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    def images(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleImagesParams],
    ) -> GoogleImagesResponse: ...
    @overload
    def images(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleImagesParams],
    ) -> AsyncSubmission: ...
    def images(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleImagesParams],
    ) -> Any:
        """google_images: https://flashdata.dev/docs/sources/google_images"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "google_images", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    def news(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleNewsParams],
    ) -> GoogleNewsResponse: ...
    @overload
    def news(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleNewsParams],
    ) -> AsyncSubmission: ...
    def news(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleNewsParams],
    ) -> Any:
        """google_news: https://flashdata.dev/docs/sources/google_news"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "google_news", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    def shopping(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleShoppingParams],
    ) -> GoogleShoppingResponse: ...
    @overload
    def shopping(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleShoppingParams],
    ) -> AsyncSubmission: ...
    def shopping(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleShoppingParams],
    ) -> Any:
        """google_shopping: https://flashdata.dev/docs/sources/google_shopping"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "google_shopping", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    def videos(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleVideosParams],
    ) -> GoogleVideosResponse: ...
    @overload
    def videos(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleVideosParams],
    ) -> AsyncSubmission: ...
    def videos(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleVideosParams],
    ) -> Any:
        """google_videos: https://flashdata.dev/docs/sources/google_videos"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "google_videos", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    def places(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[GooglePlacesParams],
    ) -> GooglePlacesResponse: ...
    @overload
    def places(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GooglePlacesParams],
    ) -> AsyncSubmission: ...
    def places(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GooglePlacesParams],
    ) -> Any:
        """google_places: https://flashdata.dev/docs/sources/google_places"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "google_places", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    def pages(
        self,
        source: Source,
        query: str,
        *,
        max_pages: int,
        start_page: int = 1,
        timeout: float | None = None,
        **params: Any,
    ):
        """Fetch at most max_pages paid Google pages, stopping on an empty result list."""
        keys = {
            "google_search": "organic",
            "google_images": "images",
            "google_news": "news",
            "google_shopping": "shopping",
            "google_videos": "videos",
            "google_places": "places",
        }
        if not isinstance(source, str) or source not in keys or "page" in params:
            raise ValidationError("Choose a Google source and use start_page for pagination.")
        integer(max_pages, "max_pages", 1, 100)
        integer(start_page, "start_page", 1, 100)
        if start_page + max_pages > 101:
            raise ValidationError("Requested pagination exceeds page 100.")
        for page in range(start_page, start_page + max_pages):
            payload: Any = {"source": source, "query": query, "params": {**params, "page": page}}
            response = self._client.queries.realtime(payload, timeout=timeout)
            yield response
            if not any(isinstance(item, dict) and item.get(keys[source]) for item in response.get("results", [])):
                break


class YouTube(Resource):
    @overload
    def search(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSearchParams],
    ) -> YoutubeSearchResponse: ...
    @overload
    def search(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSearchParams],
    ) -> AsyncSubmission: ...
    def search(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSearchParams],
    ) -> Any:
        """youtube_search: https://flashdata.dev/docs/sources/youtube_search"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_search", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    def search_extended(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSearchExtendedParams],
    ) -> YoutubeSearchExtendedResponse: ...
    @overload
    def search_extended(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSearchExtendedParams],
    ) -> AsyncSubmission: ...
    def search_extended(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSearchExtendedParams],
    ) -> Any:
        """youtube_search_extended: https://flashdata.dev/docs/sources/youtube_search_extended"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_search_extended", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    def metadata(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeMetadataParams],
    ) -> YoutubeMetadataResponse: ...
    @overload
    def metadata(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeMetadataParams],
    ) -> AsyncSubmission: ...
    def metadata(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeMetadataParams],
    ) -> Any:
        """youtube_metadata: https://flashdata.dev/docs/sources/youtube_metadata"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_metadata", "video_id": video_id}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    def transcript(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeTranscriptParams],
    ) -> YoutubeTranscriptResponse: ...
    @overload
    def transcript(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeTranscriptParams],
    ) -> AsyncSubmission: ...
    def transcript(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeTranscriptParams],
    ) -> Any:
        """youtube_transcript: https://flashdata.dev/docs/sources/youtube_transcript"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_transcript", "video_id": video_id}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    def captions(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeCaptionsParams],
    ) -> YoutubeCaptionsResponse: ...
    @overload
    def captions(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeCaptionsParams],
    ) -> AsyncSubmission: ...
    def captions(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeCaptionsParams],
    ) -> Any:
        """youtube_captions: https://flashdata.dev/docs/sources/youtube_captions"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_captions", "video_id": video_id}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    def license_check(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeTrainabilityParams],
    ) -> YoutubeTrainabilityResponse: ...
    @overload
    def license_check(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeTrainabilityParams],
    ) -> AsyncSubmission: ...
    def license_check(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeTrainabilityParams],
    ) -> Any:
        """youtube_trainability: https://flashdata.dev/docs/sources/youtube_trainability"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_trainability", "video_id": video_id}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    def channel(
        self,
        handle: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeChannelParams],
    ) -> YoutubeChannelResponse: ...
    @overload
    def channel(
        self,
        handle: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeChannelParams],
    ) -> AsyncSubmission: ...
    def channel(
        self,
        handle: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeChannelParams],
    ) -> Any:
        """youtube_channel: https://flashdata.dev/docs/sources/youtube_channel"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_channel", "handle": handle}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    def suggestions(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSuggestionsParams],
    ) -> YoutubeSuggestionsResponse: ...
    @overload
    def suggestions(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSuggestionsParams],
    ) -> AsyncSubmission: ...
    def suggestions(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSuggestionsParams],
    ) -> Any:
        """youtube_suggestions: https://flashdata.dev/docs/sources/youtube_suggestions"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_suggestions", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    def download(
        self,
        video_id: str,
        *,
        mode: Literal["async"] = "async",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeDownloadParams],
    ) -> AsyncSubmission:
        """Submit cloud media delivery. Downloads always run in the background."""
        if mode != "async":
            raise ValidationError("Downloads support mode=async only.")
        payload: Any = {"source": "youtube_download", "video_id": video_id}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return self._client.queries.submit(payload, timeout=timeout)


class AsyncResource:
    def __init__(self, client: Any):
        self._client = client


class AsyncQueries(AsyncResource):
    async def realtime(self, query: RealtimeQuery, *, timeout: float | None = None) -> DataQueryResponse:
        return await self._client._request(
            "POST", "/v1/queries/realtime", data=True, body=validate_query(query), timeout=timeout
        )

    async def submit(self, query: AsyncQuery, *, timeout: float | None = None) -> AsyncSubmission:
        return await self._client._request(
            "POST", "/v1/queries", data=True, body=validate_query(query, async_mode=True), timeout=timeout
        )

    async def batch(self, queries: list[AsyncQuery], *, timeout: float | None = None) -> BatchResponse:
        if not isinstance(queries, list) or not queries:
            raise ValidationError("Provide a non-empty list of queries; plan batch limits apply.")
        return await self._client._request(
            "POST",
            "/v1/queries/batch",
            data=True,
            body={"queries": [validate_query(q, async_mode=True) for q in queries]},
            timeout=timeout,
        )


class AsyncAccount(AsyncResource):
    async def access(self, *, timeout: float | None = None) -> ApiAccess:
        return await self._client._request("GET", "/api-access", timeout=timeout)

    async def balance(self, *, timeout: float | None = None) -> ApiAccessBalance:
        return await self._client._request("GET", "/api-access/balance", timeout=timeout)

    async def pricing(
        self, *, source: Source | None = None, request_count: int = 1, timeout: float | None = None
    ) -> ApiAccessPricing:
        integer(request_count, "request_count", 1, 100000)
        if source is not None and source not in SOURCES:
            raise ValidationError("Unknown pricing source.")
        params: dict[str, Any] = {"request_count": request_count}
        if source is not None:
            params["source"] = source
        return await self._client._request("GET", "/api-access/pricing", params=params, timeout=timeout)

    async def limits(self, *, timeout: float | None = None) -> ApiAccessLimits:
        return await self._client._request("GET", "/api-access/limits", timeout=timeout)

    async def usage(
        self,
        *,
        source: Source | None = None,
        from_: str | None = None,
        to: str | None = None,
        timeout: float | None = None,
    ) -> ApiKeyUsage:
        if source is not None and source not in SOURCES:
            raise ValidationError("Unknown usage source.")
        params = {k: v for k, v in {"source": source, "from": from_, "to": to}.items() if v is not None}
        return await self._client._request("GET", "/usage", params=params, timeout=timeout)


class AsyncPublic(AsyncResource):
    async def sources(self, *, timeout: float | None = None) -> SourceCatalog:
        return await self._client._request("GET", "/catalog/sources", public=True, timeout=timeout)

    async def plans(self, *, timeout: float | None = None) -> PlanCatalog:
        return await self._client._request("GET", "/plans", public=True, timeout=timeout)

    async def status(self, *, timeout: float | None = None) -> PublicStatus:
        return await self._client._request("GET", "/status", public=True, timeout=timeout)

    async def health(self, *, timeout: float | None = None) -> Health:
        return await self._client._request("GET", "/health", public=True, timeout=timeout)


class AsyncJobs(AsyncResource):
    async def get(self, job_id: str, *, timeout: float | None = None) -> ConsoleJob:
        return job_record(await self._client._request("GET", "/jobs/" + identifier(job_id), timeout=timeout))

    async def result(self, job_id: str, *, timeout: float | None = None) -> JobResult:
        return await self._client._result("/jobs/" + identifier(job_id) + "/results", timeout=timeout)

    async def wait(self, job_id: str, *, timeout: float = 300, poll_interval: float = 2) -> ConsoleJob:
        """Poll an existing ID without resubmitting or canceling accepted work."""
        identifier(job_id)
        deadline = time.monotonic() + positive(timeout, "timeout")
        positive(poll_interval, "poll_interval")
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(job_id)
            try:
                job = job_record(
                    await self._client._request("GET", "/jobs/" + job_id, timeout=min(remaining, self._client.timeout))
                )
            except RequestTimeoutError:
                if time.monotonic() >= deadline:
                    raise PollingTimeoutError(job_id) from None
                raise
            if time.monotonic() >= deadline:
                raise PollingTimeoutError(job_id)
            status = job.get("status")
            if status == "completed":
                return job
            if status in ("failed",):
                raise JobFailedError(job)
            if status not in ("pending", "processing"):
                raise ProtocolError("Unexpected job status.")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(job_id)
            await asyncio.sleep(min(poll_interval, remaining))


class AsyncBulk(AsyncResource):
    async def create(self, request: CreateBulkJobRequest, *, timeout: float | None = None) -> BulkJobCreated:
        return await self._client._request("POST", "/bulk-jobs", body=bulk_input(request), timeout=timeout)

    async def get(self, bulk_id: str, *, timeout: float | None = None) -> BulkJob:
        return job_record(
            await self._client._request("GET", "/bulk-jobs/" + identifier(bulk_id, True), timeout=timeout)
        )

    async def list(self, *, cursor: str | None = None, limit: int = 20, timeout: float | None = None) -> BulkJobPage:
        integer(limit, "limit", 1, 50)
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        return await self._client._request("GET", "/bulk-jobs", params=params, timeout=timeout)

    async def update(self, bulk_id: str, request: UpdateBulkJobRequest, *, timeout: float | None = None) -> BulkJob:
        return job_record(
            await self._client._request(
                "PATCH",
                "/bulk-jobs/" + identifier(bulk_id, True),
                body=bulk_input(request, partial=True),
                timeout=timeout,
            )
        )

    async def upload_file(self, created: BulkJobCreated, path: Any, *, timeout: float | None = None) -> None:
        await self._client._upload(created, path, timeout=timeout)

    async def manifest(self, bulk_id: str, *, timeout: float | None = None) -> dict[str, Any]:
        return await self._client._result("/bulk-jobs/" + identifier(bulk_id, True) + "/results", timeout=timeout)

    async def part(self, bulk_id: str, part_number: int, *, timeout: float | None = None) -> bytes:
        integer(part_number, "part_number", 0, 2**53 - 1)
        return await self._client._result(
            "/bulk-jobs/" + identifier(bulk_id, True) + "/results/" + str(part_number), binary=True, timeout=timeout
        )

    async def iter_rows(self, bulk_id: str, part_number: int, *, timeout: float | None = None):
        """Iterate one bounded gzip/NDJSON part; decompressed lines use max_line_bytes."""
        raw = await self.part(bulk_id, part_number, timeout=timeout)
        for row in result_rows(raw, self._client.max_response_bytes, self._client.max_line_bytes):
            yield row

    async def wait(self, bulk_id: str, *, timeout: float = 3600, poll_interval: float = 5) -> BulkJob:
        """Poll an existing ID without resubmitting or canceling accepted work."""
        identifier(bulk_id, True)
        deadline = time.monotonic() + positive(timeout, "timeout")
        positive(poll_interval, "poll_interval")
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(bulk_id)
            try:
                job = job_record(
                    await self._client._request(
                        "GET", "/bulk-jobs/" + bulk_id, timeout=min(remaining, self._client.timeout)
                    )
                )
            except RequestTimeoutError:
                if time.monotonic() >= deadline:
                    raise PollingTimeoutError(bulk_id) from None
                raise
            if time.monotonic() >= deadline:
                raise PollingTimeoutError(bulk_id)
            status = job.get("status")
            if status == "completed":
                return job
            if status == "paused":
                raise JobPausedError(job)
            if status in ("failed", "cancelled"):
                raise JobFailedError(job)
            if status not in ("awaiting_upload", "running", "finalizing"):
                raise ProtocolError("Unexpected job status.")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(bulk_id)
            await asyncio.sleep(min(poll_interval, remaining))

    async def start(self, bulk_id: str, *, timeout: float | None = None) -> BulkJob:
        return job_record(
            await self._client._request("POST", "/bulk-jobs/" + identifier(bulk_id, True) + "/start", timeout=timeout)
        )

    async def pause(self, bulk_id: str, *, timeout: float | None = None) -> BulkJob:
        return job_record(
            await self._client._request("POST", "/bulk-jobs/" + identifier(bulk_id, True) + "/pause", timeout=timeout)
        )

    async def resume(self, bulk_id: str, *, timeout: float | None = None) -> BulkJob:
        return job_record(
            await self._client._request("POST", "/bulk-jobs/" + identifier(bulk_id, True) + "/resume", timeout=timeout)
        )

    async def cancel(self, bulk_id: str, *, timeout: float | None = None) -> BulkJob:
        return job_record(
            await self._client._request("DELETE", "/bulk-jobs/" + identifier(bulk_id, True) + "", timeout=timeout)
        )

    async def rows(self, bulk_id: str, *, timeout: float | None = None):
        """Yield all result rows in manifest order, buffering one bounded part."""
        manifest = await self.manifest(bulk_id, timeout=timeout)
        parts = manifest.get("parts")
        if not isinstance(parts, list):
            raise ProtocolError("Bulk manifest is missing its parts list.")
        seen = set()
        for part in parts:
            if (
                not isinstance(part, dict)
                or type(part.get("number")) is not int
                or part["number"] < 0
                or part["number"] in seen
            ):
                raise ProtocolError("Invalid or duplicate bulk part number.")
            seen.add(part["number"])
            async for row in self.iter_rows(bulk_id, part["number"], timeout=timeout):
                yield row

    async def iter_jobs(
        self, *, max_pages: int, limit: int = 20, cursor: str | None = None, timeout: float | None = None
    ):
        """Yield bulk job records from a bounded number of cursor pages."""
        integer(max_pages, "max_pages", 1, 1000)
        seen = {cursor} if cursor else set()
        for _ in range(max_pages):
            page = await self.list(limit=limit, cursor=cursor, timeout=timeout)
            if not isinstance(page.get("data"), list) or not isinstance(page.get("pagination"), dict):
                raise ProtocolError("Invalid bulk listing response.")
            for job in page["data"]:
                if not isinstance(job, dict):
                    raise ProtocolError("Expected a bulk job object.")
                yield job
            pagination = page["pagination"]
            if not pagination.get("hasMore"):
                return
            cursor = pagination.get("nextCursor")
            if not isinstance(cursor, str) or not cursor or cursor in seen:
                raise ProtocolError("Bulk listing returned an invalid or repeated cursor.")
            seen.add(cursor)


class AsyncGoogle(AsyncResource):
    @overload
    async def search(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleSearchParams],
    ) -> GoogleSearchResponse: ...
    @overload
    async def search(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleSearchParams],
    ) -> AsyncSubmission: ...
    async def search(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleSearchParams],
    ) -> Any:
        """google_search: https://flashdata.dev/docs/sources/google_search"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "google_search", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    async def images(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleImagesParams],
    ) -> GoogleImagesResponse: ...
    @overload
    async def images(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleImagesParams],
    ) -> AsyncSubmission: ...
    async def images(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleImagesParams],
    ) -> Any:
        """google_images: https://flashdata.dev/docs/sources/google_images"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "google_images", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    async def news(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleNewsParams],
    ) -> GoogleNewsResponse: ...
    @overload
    async def news(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleNewsParams],
    ) -> AsyncSubmission: ...
    async def news(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleNewsParams],
    ) -> Any:
        """google_news: https://flashdata.dev/docs/sources/google_news"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "google_news", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    async def shopping(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleShoppingParams],
    ) -> GoogleShoppingResponse: ...
    @overload
    async def shopping(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleShoppingParams],
    ) -> AsyncSubmission: ...
    async def shopping(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleShoppingParams],
    ) -> Any:
        """google_shopping: https://flashdata.dev/docs/sources/google_shopping"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "google_shopping", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    async def videos(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleVideosParams],
    ) -> GoogleVideosResponse: ...
    @overload
    async def videos(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleVideosParams],
    ) -> AsyncSubmission: ...
    async def videos(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GoogleVideosParams],
    ) -> Any:
        """google_videos: https://flashdata.dev/docs/sources/google_videos"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "google_videos", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    async def places(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[GooglePlacesParams],
    ) -> GooglePlacesResponse: ...
    @overload
    async def places(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GooglePlacesParams],
    ) -> AsyncSubmission: ...
    async def places(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[GooglePlacesParams],
    ) -> Any:
        """google_places: https://flashdata.dev/docs/sources/google_places"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "google_places", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    async def pages(
        self,
        source: Source,
        query: str,
        *,
        max_pages: int,
        start_page: int = 1,
        timeout: float | None = None,
        **params: Any,
    ):
        """Fetch at most max_pages paid Google pages, stopping on an empty result list."""
        keys = {
            "google_search": "organic",
            "google_images": "images",
            "google_news": "news",
            "google_shopping": "shopping",
            "google_videos": "videos",
            "google_places": "places",
        }
        if not isinstance(source, str) or source not in keys or "page" in params:
            raise ValidationError("Choose a Google source and use start_page for pagination.")
        integer(max_pages, "max_pages", 1, 100)
        integer(start_page, "start_page", 1, 100)
        if start_page + max_pages > 101:
            raise ValidationError("Requested pagination exceeds page 100.")
        for page in range(start_page, start_page + max_pages):
            payload: Any = {"source": source, "query": query, "params": {**params, "page": page}}
            response = await self._client.queries.realtime(payload, timeout=timeout)
            yield response
            if not any(isinstance(item, dict) and item.get(keys[source]) for item in response.get("results", [])):
                break


class AsyncYouTube(AsyncResource):
    @overload
    async def search(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSearchParams],
    ) -> YoutubeSearchResponse: ...
    @overload
    async def search(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSearchParams],
    ) -> AsyncSubmission: ...
    async def search(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSearchParams],
    ) -> Any:
        """youtube_search: https://flashdata.dev/docs/sources/youtube_search"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_search", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    async def search_extended(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSearchExtendedParams],
    ) -> YoutubeSearchExtendedResponse: ...
    @overload
    async def search_extended(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSearchExtendedParams],
    ) -> AsyncSubmission: ...
    async def search_extended(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSearchExtendedParams],
    ) -> Any:
        """youtube_search_extended: https://flashdata.dev/docs/sources/youtube_search_extended"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_search_extended", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    async def metadata(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeMetadataParams],
    ) -> YoutubeMetadataResponse: ...
    @overload
    async def metadata(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeMetadataParams],
    ) -> AsyncSubmission: ...
    async def metadata(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeMetadataParams],
    ) -> Any:
        """youtube_metadata: https://flashdata.dev/docs/sources/youtube_metadata"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_metadata", "video_id": video_id}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    async def transcript(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeTranscriptParams],
    ) -> YoutubeTranscriptResponse: ...
    @overload
    async def transcript(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeTranscriptParams],
    ) -> AsyncSubmission: ...
    async def transcript(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeTranscriptParams],
    ) -> Any:
        """youtube_transcript: https://flashdata.dev/docs/sources/youtube_transcript"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_transcript", "video_id": video_id}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    async def captions(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeCaptionsParams],
    ) -> YoutubeCaptionsResponse: ...
    @overload
    async def captions(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeCaptionsParams],
    ) -> AsyncSubmission: ...
    async def captions(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeCaptionsParams],
    ) -> Any:
        """youtube_captions: https://flashdata.dev/docs/sources/youtube_captions"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_captions", "video_id": video_id}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    async def license_check(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeTrainabilityParams],
    ) -> YoutubeTrainabilityResponse: ...
    @overload
    async def license_check(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeTrainabilityParams],
    ) -> AsyncSubmission: ...
    async def license_check(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeTrainabilityParams],
    ) -> Any:
        """youtube_trainability: https://flashdata.dev/docs/sources/youtube_trainability"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_trainability", "video_id": video_id}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    async def channel(
        self,
        handle: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeChannelParams],
    ) -> YoutubeChannelResponse: ...
    @overload
    async def channel(
        self,
        handle: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeChannelParams],
    ) -> AsyncSubmission: ...
    async def channel(
        self,
        handle: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeChannelParams],
    ) -> Any:
        """youtube_channel: https://flashdata.dev/docs/sources/youtube_channel"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_channel", "handle": handle}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    @overload
    async def suggestions(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSuggestionsParams],
    ) -> YoutubeSuggestionsResponse: ...
    @overload
    async def suggestions(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSuggestionsParams],
    ) -> AsyncSubmission: ...
    async def suggestions(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeSuggestionsParams],
    ) -> Any:
        """youtube_suggestions: https://flashdata.dev/docs/sources/youtube_suggestions"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_suggestions", "query": query}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload, timeout=timeout)
            if mode == "async"
            else self._client.queries.realtime(payload, timeout=timeout)
        )

    async def download(
        self,
        video_id: str,
        *,
        mode: Literal["async"] = "async",
        callback_url: str | None = None,
        timeout: float | None = None,
        **params: Unpack[YoutubeDownloadParams],
    ) -> AsyncSubmission:
        """Submit cloud media delivery. Downloads always run in the background."""
        if mode != "async":
            raise ValidationError("Downloads support mode=async only.")
        payload: Any = {"source": "youtube_download", "video_id": video_id}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await self._client.queries.submit(payload, timeout=timeout)
