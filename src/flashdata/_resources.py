from __future__ import annotations
import asyncio
import gzip
import io
import json
import time
from typing import Any, Literal, overload
from typing_extensions import Unpack
from .types import *
from ._common import SOURCES, bulk_input, identifier, integer, positive, validate_query
from .errors import (
    JobFailedError,
    JobPausedError,
    PollingTimeoutError,
    ProtocolError,
    ResponseTooLargeError,
    ValidationError,
)


class Resource:
    def __init__(self, client: Any):
        self._client = client


class Queries(Resource):
    def realtime(self, query: RealtimeQuery) -> DataQueryResponse:
        return self._client._request("POST", "/v1/queries/realtime", data=True, body=validate_query(query))

    def submit(self, query: AsyncQuery) -> AsyncSubmission:
        return self._client._request("POST", "/v1/queries", data=True, body=validate_query(query, async_mode=True))

    def batch(self, queries: list[AsyncQuery]) -> dict[str, Any]:
        if not isinstance(queries, list) or not queries:
            raise ValidationError("Provide a non-empty list of queries; plan batch limits apply.")
        return self._client._request(
            "POST",
            "/v1/queries/batch",
            data=True,
            body={"queries": [validate_query(q, async_mode=True) for q in queries]},
        )


class Account(Resource):
    def access(self) -> ApiAccess:
        return self._client._request("GET", "/api-access")

    def balance(self) -> ApiAccessBalance:
        return self._client._request("GET", "/api-access/balance")

    def pricing(self, *, source: Source | None = None, request_count: int = 1) -> ApiAccessPricing:
        integer(request_count, "request_count", 1, 100000)
        if source is not None and source not in SOURCES:
            raise ValidationError("Unknown pricing source.")
        params: dict[str, Any] = {"request_count": request_count}
        if source is not None:
            params["source"] = source
        return self._client._request("GET", "/api-access/pricing", params=params)

    def limits(self) -> ApiAccessLimits:
        return self._client._request("GET", "/api-access/limits")

    def usage(self, *, source: Source | None = None, from_: str | None = None, to: str | None = None) -> ApiKeyUsage:
        if source is not None and source not in SOURCES:
            raise ValidationError("Unknown usage source.")
        params = {k: v for k, v in {"source": source, "from": from_, "to": to}.items() if v is not None}
        return self._client._request("GET", "/usage", params=params)


class Public(Resource):
    def sources(self) -> dict[str, Any]:
        return self._client._request("GET", "/catalog/sources", public=True)

    def plans(self) -> dict[str, Any]:
        return self._client._request("GET", "/plans", public=True)

    def status(self) -> dict[str, Any]:
        return self._client._request("GET", "/status", public=True)

    def health(self) -> dict[str, Any]:
        return self._client._request("GET", "/health", public=True)


class Jobs(Resource):
    def get(self, job_id: str) -> ConsoleJob:
        return (self._client._request("GET", "/jobs/" + identifier(job_id)))["job"]

    def result(self, job_id: str) -> dict[str, Any]:
        return self._client._result("/jobs/" + identifier(job_id) + "/results")

    def wait(self, job_id: str, *, timeout: float = 300, poll_interval: float = 2) -> ConsoleJob:
        identifier(job_id)
        deadline = time.monotonic() + positive(timeout, "timeout")
        positive(poll_interval, "poll_interval")
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(job_id)
            job = (self._client._request("GET", "/jobs/" + job_id, timeout=min(remaining, self._client.timeout)))["job"]
            if job.get("status") == "completed":
                return job
            if job.get("status") == "failed":
                raise JobFailedError(job)
            if job.get("status") not in ("pending", "processing"):
                raise ProtocolError("Unexpected job status.")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(job_id)
            time.sleep(min(poll_interval, remaining))


class Bulk(Resource):
    def create(self, request: CreateBulkJobRequest) -> BulkJobCreated:
        return self._client._request("POST", "/bulk-jobs", body=bulk_input(request))

    def get(self, bulk_id: str) -> BulkJob:
        return (self._client._request("GET", "/bulk-jobs/" + identifier(bulk_id, True)))["job"]

    def list(self, *, cursor: str | None = None, limit: int = 20) -> BulkJobPage:
        integer(limit, "limit", 1, 50)
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        return self._client._request("GET", "/bulk-jobs", params=params)

    def update(self, bulk_id: str, request: UpdateBulkJobRequest) -> BulkJob:
        return (
            self._client._request(
                "PATCH", "/bulk-jobs/" + identifier(bulk_id, True), body=bulk_input(request, partial=True)
            )
        )["job"]

    def upload_file(self, created: BulkJobCreated, path: Any) -> None:
        self._client._upload(created, path)

    def manifest(self, bulk_id: str) -> dict[str, Any]:
        return self._client._result("/bulk-jobs/" + identifier(bulk_id, True) + "/results")

    def part(self, bulk_id: str, part_number: int) -> bytes:
        integer(part_number, "part_number", 0, 2**53 - 1)
        return self._client._result(
            "/bulk-jobs/" + identifier(bulk_id, True) + "/results/" + str(part_number), binary=True
        )

    def iter_rows(self, bulk_id: str, part_number: int):
        """Iterate one bounded gzip/NDJSON part; decompressed lines are capped at 1 MiB."""
        raw = self.part(bulk_id, part_number)
        stream = gzip.GzipFile(fileobj=io.BytesIO(raw)) if raw.startswith(b"\x1f\x8b") else io.BytesIO(raw)
        with stream:
            total = 0
            while True:
                line = stream.readline(1024 * 1024 + 1)
                if not line:
                    break
                total += len(line)
                if len(line) > 1024 * 1024 or total > self._client.max_response_bytes:
                    raise ResponseTooLargeError("Decompressed result part exceeds configured limits.")
                if line.strip():
                    try:
                        row = json.loads(line)
                    except (ValueError, UnicodeDecodeError):
                        raise ProtocolError("Invalid NDJSON result row.") from None
                    if not isinstance(row, dict):
                        raise ProtocolError("Expected an NDJSON object.")
                    yield row

    def wait(self, bulk_id: str, *, timeout: float = 3600, poll_interval: float = 5) -> BulkJob:
        identifier(bulk_id, True)
        deadline = time.monotonic() + positive(timeout, "timeout")
        positive(poll_interval, "poll_interval")
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(bulk_id)
            job = (self._client._request("GET", "/bulk-jobs/" + bulk_id, timeout=min(remaining, self._client.timeout)))[
                "job"
            ]
            status = job.get("status")
            if status == "completed":
                return job
            if status == "paused":
                raise JobPausedError(job)
            if status in ("failed", "cancelled"):
                raise JobFailedError(job)
            if status not in ("awaiting_upload", "running", "finalizing"):
                raise ProtocolError("Unexpected bulk job status.")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(bulk_id)
            time.sleep(min(poll_interval, remaining))

    def start(self, bulk_id: str) -> BulkJob:
        return (self._client._request("POST", "/bulk-jobs/" + identifier(bulk_id, True) + "/start"))["job"]

    def pause(self, bulk_id: str) -> BulkJob:
        return (self._client._request("POST", "/bulk-jobs/" + identifier(bulk_id, True) + "/pause"))["job"]

    def resume(self, bulk_id: str) -> BulkJob:
        return (self._client._request("POST", "/bulk-jobs/" + identifier(bulk_id, True) + "/resume"))["job"]

    def cancel(self, bulk_id: str) -> BulkJob:
        return (self._client._request("DELETE", "/bulk-jobs/" + identifier(bulk_id, True) + ""))["job"]


class Google(Resource):
    @overload
    def search(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[GoogleSearchParams],
    ) -> GoogleSearchResponse: ...
    @overload
    def search(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[GoogleSearchParams],
    ) -> AsyncSubmission: ...
    def search(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    @overload
    def images(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[GoogleImagesParams],
    ) -> GoogleImagesResponse: ...
    @overload
    def images(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[GoogleImagesParams],
    ) -> AsyncSubmission: ...
    def images(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    @overload
    def news(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[GoogleNewsParams],
    ) -> GoogleNewsResponse: ...
    @overload
    def news(
        self, query: str, *, mode: Literal["async"], callback_url: str | None = None, **params: Unpack[GoogleNewsParams]
    ) -> AsyncSubmission: ...
    def news(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    @overload
    def shopping(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[GoogleShoppingParams],
    ) -> GoogleShoppingResponse: ...
    @overload
    def shopping(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[GoogleShoppingParams],
    ) -> AsyncSubmission: ...
    def shopping(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    @overload
    def videos(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[GoogleVideosParams],
    ) -> GoogleVideosResponse: ...
    @overload
    def videos(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[GoogleVideosParams],
    ) -> AsyncSubmission: ...
    def videos(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    @overload
    def places(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[GooglePlacesParams],
    ) -> GooglePlacesResponse: ...
    @overload
    def places(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[GooglePlacesParams],
    ) -> AsyncSubmission: ...
    def places(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    def pages(self, source: Source, query: str, *, max_pages: int, start_page: int = 1, **params: Any):
        """Fetch at most max_pages paid Google pages, stopping on an empty result list."""
        keys = {
            "google_search": "organic",
            "google_images": "images",
            "google_news": "news",
            "google_shopping": "shopping",
            "google_videos": "videos",
            "google_places": "places",
        }
        if source not in keys or "page" in params:
            raise ValidationError("Choose a Google source and use start_page for pagination.")
        integer(max_pages, "max_pages", 1, 100)
        integer(start_page, "start_page", 1, 100)
        if start_page + max_pages > 101:
            raise ValidationError("Requested pagination exceeds page 100.")
        for page in range(start_page, start_page + max_pages):
            payload: Any = {"source": source, "query": query, "params": {**params, "page": page}}
            response = self._client.queries.realtime(payload)
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
        **params: Unpack[YoutubeSearchParams],
    ) -> YoutubeSearchResponse: ...
    @overload
    def search(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeSearchParams],
    ) -> AsyncSubmission: ...
    def search(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    @overload
    def search_extended(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeSearchExtendedParams],
    ) -> YoutubeSearchExtendedResponse: ...
    @overload
    def search_extended(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeSearchExtendedParams],
    ) -> AsyncSubmission: ...
    def search_extended(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    @overload
    def metadata(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeMetadataParams],
    ) -> YoutubeMetadataResponse: ...
    @overload
    def metadata(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeMetadataParams],
    ) -> AsyncSubmission: ...
    def metadata(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    @overload
    def transcript(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeTranscriptParams],
    ) -> YoutubeTranscriptResponse: ...
    @overload
    def transcript(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeTranscriptParams],
    ) -> AsyncSubmission: ...
    def transcript(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    @overload
    def captions(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeCaptionsParams],
    ) -> YoutubeCaptionsResponse: ...
    @overload
    def captions(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeCaptionsParams],
    ) -> AsyncSubmission: ...
    def captions(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    @overload
    def license_check(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeTrainabilityParams],
    ) -> YoutubeTrainabilityResponse: ...
    @overload
    def license_check(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeTrainabilityParams],
    ) -> AsyncSubmission: ...
    def license_check(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    @overload
    def channel(
        self,
        handle: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeChannelParams],
    ) -> YoutubeChannelResponse: ...
    @overload
    def channel(
        self,
        handle: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeChannelParams],
    ) -> AsyncSubmission: ...
    def channel(
        self,
        handle: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    @overload
    def suggestions(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeSuggestionsParams],
    ) -> YoutubeSuggestionsResponse: ...
    @overload
    def suggestions(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeSuggestionsParams],
    ) -> AsyncSubmission: ...
    def suggestions(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)

    def download(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "async",
        callback_url: str | None = None,
        **params: Unpack[YoutubeDownloadParams],
    ) -> Any:
        """youtube_download: https://flashdata.dev/docs/sources/youtube_download"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_download", "video_id": video_id}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)


class AsyncResource:
    def __init__(self, client: Any):
        self._client = client


class AsyncQueries(AsyncResource):
    async def realtime(self, query: RealtimeQuery) -> DataQueryResponse:
        return await self._client._request("POST", "/v1/queries/realtime", data=True, body=validate_query(query))

    async def submit(self, query: AsyncQuery) -> AsyncSubmission:
        return await self._client._request(
            "POST", "/v1/queries", data=True, body=validate_query(query, async_mode=True)
        )

    async def batch(self, queries: list[AsyncQuery]) -> dict[str, Any]:
        if not isinstance(queries, list) or not queries:
            raise ValidationError("Provide a non-empty list of queries; plan batch limits apply.")
        return await self._client._request(
            "POST",
            "/v1/queries/batch",
            data=True,
            body={"queries": [validate_query(q, async_mode=True) for q in queries]},
        )


class AsyncAccount(AsyncResource):
    async def access(self) -> ApiAccess:
        return await self._client._request("GET", "/api-access")

    async def balance(self) -> ApiAccessBalance:
        return await self._client._request("GET", "/api-access/balance")

    async def pricing(self, *, source: Source | None = None, request_count: int = 1) -> ApiAccessPricing:
        integer(request_count, "request_count", 1, 100000)
        if source is not None and source not in SOURCES:
            raise ValidationError("Unknown pricing source.")
        params: dict[str, Any] = {"request_count": request_count}
        if source is not None:
            params["source"] = source
        return await self._client._request("GET", "/api-access/pricing", params=params)

    async def limits(self) -> ApiAccessLimits:
        return await self._client._request("GET", "/api-access/limits")

    async def usage(
        self, *, source: Source | None = None, from_: str | None = None, to: str | None = None
    ) -> ApiKeyUsage:
        if source is not None and source not in SOURCES:
            raise ValidationError("Unknown usage source.")
        params = {k: v for k, v in {"source": source, "from": from_, "to": to}.items() if v is not None}
        return await self._client._request("GET", "/usage", params=params)


class AsyncPublic(AsyncResource):
    async def sources(self) -> dict[str, Any]:
        return await self._client._request("GET", "/catalog/sources", public=True)

    async def plans(self) -> dict[str, Any]:
        return await self._client._request("GET", "/plans", public=True)

    async def status(self) -> dict[str, Any]:
        return await self._client._request("GET", "/status", public=True)

    async def health(self) -> dict[str, Any]:
        return await self._client._request("GET", "/health", public=True)


class AsyncJobs(AsyncResource):
    async def get(self, job_id: str) -> ConsoleJob:
        return (await self._client._request("GET", "/jobs/" + identifier(job_id)))["job"]

    async def result(self, job_id: str) -> dict[str, Any]:
        return await self._client._result("/jobs/" + identifier(job_id) + "/results")

    async def wait(self, job_id: str, *, timeout: float = 300, poll_interval: float = 2) -> ConsoleJob:
        identifier(job_id)
        deadline = time.monotonic() + positive(timeout, "timeout")
        positive(poll_interval, "poll_interval")
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(job_id)
            job = (await self._client._request("GET", "/jobs/" + job_id, timeout=min(remaining, self._client.timeout)))[
                "job"
            ]
            if job.get("status") == "completed":
                return job
            if job.get("status") == "failed":
                raise JobFailedError(job)
            if job.get("status") not in ("pending", "processing"):
                raise ProtocolError("Unexpected job status.")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(job_id)
            await asyncio.sleep(min(poll_interval, remaining))


class AsyncBulk(AsyncResource):
    async def create(self, request: CreateBulkJobRequest) -> BulkJobCreated:
        return await self._client._request("POST", "/bulk-jobs", body=bulk_input(request))

    async def get(self, bulk_id: str) -> BulkJob:
        return (await self._client._request("GET", "/bulk-jobs/" + identifier(bulk_id, True)))["job"]

    async def list(self, *, cursor: str | None = None, limit: int = 20) -> BulkJobPage:
        integer(limit, "limit", 1, 50)
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        return await self._client._request("GET", "/bulk-jobs", params=params)

    async def update(self, bulk_id: str, request: UpdateBulkJobRequest) -> BulkJob:
        return (
            await self._client._request(
                "PATCH", "/bulk-jobs/" + identifier(bulk_id, True), body=bulk_input(request, partial=True)
            )
        )["job"]

    async def upload_file(self, created: BulkJobCreated, path: Any) -> None:
        await self._client._upload(created, path)

    async def manifest(self, bulk_id: str) -> dict[str, Any]:
        return await self._client._result("/bulk-jobs/" + identifier(bulk_id, True) + "/results")

    async def part(self, bulk_id: str, part_number: int) -> bytes:
        integer(part_number, "part_number", 0, 2**53 - 1)
        return await self._client._result(
            "/bulk-jobs/" + identifier(bulk_id, True) + "/results/" + str(part_number), binary=True
        )

    async def iter_rows(self, bulk_id: str, part_number: int):
        """Iterate one bounded gzip/NDJSON part; decompressed lines are capped at 1 MiB."""
        raw = await self.part(bulk_id, part_number)
        stream = gzip.GzipFile(fileobj=io.BytesIO(raw)) if raw.startswith(b"\x1f\x8b") else io.BytesIO(raw)
        with stream:
            total = 0
            while True:
                line = stream.readline(1024 * 1024 + 1)
                if not line:
                    break
                total += len(line)
                if len(line) > 1024 * 1024 or total > self._client.max_response_bytes:
                    raise ResponseTooLargeError("Decompressed result part exceeds configured limits.")
                if line.strip():
                    try:
                        row = json.loads(line)
                    except (ValueError, UnicodeDecodeError):
                        raise ProtocolError("Invalid NDJSON result row.") from None
                    if not isinstance(row, dict):
                        raise ProtocolError("Expected an NDJSON object.")
                    yield row

    async def wait(self, bulk_id: str, *, timeout: float = 3600, poll_interval: float = 5) -> BulkJob:
        identifier(bulk_id, True)
        deadline = time.monotonic() + positive(timeout, "timeout")
        positive(poll_interval, "poll_interval")
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(bulk_id)
            job = (
                await self._client._request(
                    "GET", "/bulk-jobs/" + bulk_id, timeout=min(remaining, self._client.timeout)
                )
            )["job"]
            status = job.get("status")
            if status == "completed":
                return job
            if status == "paused":
                raise JobPausedError(job)
            if status in ("failed", "cancelled"):
                raise JobFailedError(job)
            if status not in ("awaiting_upload", "running", "finalizing"):
                raise ProtocolError("Unexpected bulk job status.")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PollingTimeoutError(bulk_id)
            await asyncio.sleep(min(poll_interval, remaining))

    async def start(self, bulk_id: str) -> BulkJob:
        return (await self._client._request("POST", "/bulk-jobs/" + identifier(bulk_id, True) + "/start"))["job"]

    async def pause(self, bulk_id: str) -> BulkJob:
        return (await self._client._request("POST", "/bulk-jobs/" + identifier(bulk_id, True) + "/pause"))["job"]

    async def resume(self, bulk_id: str) -> BulkJob:
        return (await self._client._request("POST", "/bulk-jobs/" + identifier(bulk_id, True) + "/resume"))["job"]

    async def cancel(self, bulk_id: str) -> BulkJob:
        return (await self._client._request("DELETE", "/bulk-jobs/" + identifier(bulk_id, True) + ""))["job"]


class AsyncGoogle(AsyncResource):
    @overload
    async def search(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[GoogleSearchParams],
    ) -> GoogleSearchResponse: ...
    @overload
    async def search(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[GoogleSearchParams],
    ) -> AsyncSubmission: ...
    async def search(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    @overload
    async def images(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[GoogleImagesParams],
    ) -> GoogleImagesResponse: ...
    @overload
    async def images(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[GoogleImagesParams],
    ) -> AsyncSubmission: ...
    async def images(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    @overload
    async def news(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[GoogleNewsParams],
    ) -> GoogleNewsResponse: ...
    @overload
    async def news(
        self, query: str, *, mode: Literal["async"], callback_url: str | None = None, **params: Unpack[GoogleNewsParams]
    ) -> AsyncSubmission: ...
    async def news(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    @overload
    async def shopping(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[GoogleShoppingParams],
    ) -> GoogleShoppingResponse: ...
    @overload
    async def shopping(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[GoogleShoppingParams],
    ) -> AsyncSubmission: ...
    async def shopping(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    @overload
    async def videos(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[GoogleVideosParams],
    ) -> GoogleVideosResponse: ...
    @overload
    async def videos(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[GoogleVideosParams],
    ) -> AsyncSubmission: ...
    async def videos(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    @overload
    async def places(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[GooglePlacesParams],
    ) -> GooglePlacesResponse: ...
    @overload
    async def places(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[GooglePlacesParams],
    ) -> AsyncSubmission: ...
    async def places(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    async def pages(self, source: Source, query: str, *, max_pages: int, start_page: int = 1, **params: Any):
        """Fetch at most max_pages paid Google pages, stopping on an empty result list."""
        keys = {
            "google_search": "organic",
            "google_images": "images",
            "google_news": "news",
            "google_shopping": "shopping",
            "google_videos": "videos",
            "google_places": "places",
        }
        if source not in keys or "page" in params:
            raise ValidationError("Choose a Google source and use start_page for pagination.")
        integer(max_pages, "max_pages", 1, 100)
        integer(start_page, "start_page", 1, 100)
        if start_page + max_pages > 101:
            raise ValidationError("Requested pagination exceeds page 100.")
        for page in range(start_page, start_page + max_pages):
            payload: Any = {"source": source, "query": query, "params": {**params, "page": page}}
            response = await self._client.queries.realtime(payload)
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
        **params: Unpack[YoutubeSearchParams],
    ) -> YoutubeSearchResponse: ...
    @overload
    async def search(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeSearchParams],
    ) -> AsyncSubmission: ...
    async def search(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    @overload
    async def search_extended(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeSearchExtendedParams],
    ) -> YoutubeSearchExtendedResponse: ...
    @overload
    async def search_extended(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeSearchExtendedParams],
    ) -> AsyncSubmission: ...
    async def search_extended(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    @overload
    async def metadata(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeMetadataParams],
    ) -> YoutubeMetadataResponse: ...
    @overload
    async def metadata(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeMetadataParams],
    ) -> AsyncSubmission: ...
    async def metadata(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    @overload
    async def transcript(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeTranscriptParams],
    ) -> YoutubeTranscriptResponse: ...
    @overload
    async def transcript(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeTranscriptParams],
    ) -> AsyncSubmission: ...
    async def transcript(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    @overload
    async def captions(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeCaptionsParams],
    ) -> YoutubeCaptionsResponse: ...
    @overload
    async def captions(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeCaptionsParams],
    ) -> AsyncSubmission: ...
    async def captions(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    @overload
    async def license_check(
        self,
        video_id: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeTrainabilityParams],
    ) -> YoutubeTrainabilityResponse: ...
    @overload
    async def license_check(
        self,
        video_id: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeTrainabilityParams],
    ) -> AsyncSubmission: ...
    async def license_check(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    @overload
    async def channel(
        self,
        handle: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeChannelParams],
    ) -> YoutubeChannelResponse: ...
    @overload
    async def channel(
        self,
        handle: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeChannelParams],
    ) -> AsyncSubmission: ...
    async def channel(
        self,
        handle: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    @overload
    async def suggestions(
        self,
        query: str,
        *,
        mode: Literal["realtime"] = "realtime",
        callback_url: None = None,
        **params: Unpack[YoutubeSuggestionsParams],
    ) -> YoutubeSuggestionsResponse: ...
    @overload
    async def suggestions(
        self,
        query: str,
        *,
        mode: Literal["async"],
        callback_url: str | None = None,
        **params: Unpack[YoutubeSuggestionsParams],
    ) -> AsyncSubmission: ...
    async def suggestions(
        self,
        query: str,
        *,
        mode: Literal["realtime", "async"] = "realtime",
        callback_url: str | None = None,
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
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )

    async def download(
        self,
        video_id: str,
        *,
        mode: Literal["realtime", "async"] = "async",
        callback_url: str | None = None,
        **params: Unpack[YoutubeDownloadParams],
    ) -> Any:
        """youtube_download: https://flashdata.dev/docs/sources/youtube_download"""
        if mode not in ("realtime", "async"):
            raise ValidationError("mode must be realtime or async.")
        if mode == "realtime" and callback_url is not None:
            raise ValidationError("Callbacks apply only to background queries.")
        payload: Any = {"source": "youtube_download", "video_id": video_id}
        if params:
            payload["params"] = params
        if callback_url is not None:
            payload["callback_url"] = callback_url
        return await (
            self._client.queries.submit(payload) if mode == "async" else self._client.queries.realtime(payload)
        )
