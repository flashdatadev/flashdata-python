"""Generated API wire types. Unknown provider fields remain available in dictionaries."""

from __future__ import annotations

from typing import Any, Literal

from typing_extensions import TypedDict, Required, Unpack

ApiAccess = TypedDict(
    "ApiAccess", {"sources": "Required[list[ApiAccessSource]]", "result_origin": "Required[str | None]"}, total=False
)

ApiAccessBalance = TypedDict(
    "ApiAccessBalance",
    {
        "scope": "Required[Literal['account']]",
        "unit": "Required[Literal['Credits']]",
        "balanceCredits": "Required[float]",
        "availableCredits": "Required[float]",
        "updatedAt": "Required[str | None]",
        "note": "Required[str]",
    },
    total=False,
)

ApiAccessLimits = TypedDict(
    "ApiAccessLimits",
    {
        "scope": "Required[Literal['account']]",
        "plan": "Required[ApiAccessPlan]",
        "limits": "Required[dict[str, Any]]",
        "current": "Required[dict[str, Any]]",
        "note": "Required[str]",
    },
    total=False,
)

ApiAccessPlan = TypedDict(
    "ApiAccessPlan", {"name": "str", "type": "str", "billingMode": "str", "status": "str"}, total=False
)

ApiAccessPricing = TypedDict(
    "ApiAccessPricing",
    {
        "unit": "Required[Literal['Credits']]",
        "plan": "Required[ApiAccessPlan]",
        "requestCount": "Required[int]",
        "prices": "Required[list[dict[str, Any]]]",
        "note": "Required[str]",
    },
    total=False,
)

ApiAccessSource = Literal[
    "google_search",
    "google_images",
    "google_news",
    "google_shopping",
    "google_videos",
    "google_places",
    "youtube_search",
    "youtube_search_extended",
    "youtube_metadata",
    "youtube_transcript",
    "youtube_captions",
    "youtube_trainability",
    "youtube_channel",
    "youtube_suggestions",
    "youtube_download",
]

ApiKeyUsage = TypedDict(
    "ApiKeyUsage",
    {
        "scope": "Required[Literal['account_authorized_sources']]",
        "unit": "Required[Literal['Credits']]",
        "from": "Required[str]",
        "to": "Required[str]",
        "observedAt": "Required[str]",
        "totals": "Required[UsageCounts]",
        "bySource": "Required[list[dict[str, Any]]]",
        "updating": "Required[bool]",
        "note": "Required[str]",
    },
    total=False,
)

AsyncQuery_google_images = TypedDict(
    "AsyncQuery_google_images",
    {
        "source": "Required[Literal['google_images']]",
        "query": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_google_news = TypedDict(
    "AsyncQuery_google_news",
    {
        "source": "Required[Literal['google_news']]",
        "query": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_google_places = TypedDict(
    "AsyncQuery_google_places",
    {
        "source": "Required[Literal['google_places']]",
        "query": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_google_search = TypedDict(
    "AsyncQuery_google_search",
    {
        "source": "Required[Literal['google_search']]",
        "query": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_google_shopping = TypedDict(
    "AsyncQuery_google_shopping",
    {
        "source": "Required[Literal['google_shopping']]",
        "query": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_google_videos = TypedDict(
    "AsyncQuery_google_videos",
    {
        "source": "Required[Literal['google_videos']]",
        "query": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_youtube_captions = TypedDict(
    "AsyncQuery_youtube_captions",
    {
        "source": "Required[Literal['youtube_captions']]",
        "video_id": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_youtube_channel = TypedDict(
    "AsyncQuery_youtube_channel",
    {
        "source": "Required[Literal['youtube_channel']]",
        "handle": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_youtube_download = TypedDict(
    "AsyncQuery_youtube_download",
    {
        "source": "Required[Literal['youtube_download']]",
        "video_id": "Required[str]",
        "params": "Required[dict[str, Any]]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_youtube_metadata = TypedDict(
    "AsyncQuery_youtube_metadata",
    {
        "source": "Required[Literal['youtube_metadata']]",
        "video_id": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_youtube_search = TypedDict(
    "AsyncQuery_youtube_search",
    {
        "source": "Required[Literal['youtube_search']]",
        "query": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_youtube_search_extended = TypedDict(
    "AsyncQuery_youtube_search_extended",
    {
        "source": "Required[Literal['youtube_search_extended']]",
        "query": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_youtube_suggestions = TypedDict(
    "AsyncQuery_youtube_suggestions",
    {
        "source": "Required[Literal['youtube_suggestions']]",
        "query": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_youtube_trainability = TypedDict(
    "AsyncQuery_youtube_trainability",
    {
        "source": "Required[Literal['youtube_trainability']]",
        "video_id": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncQuery_youtube_transcript = TypedDict(
    "AsyncQuery_youtube_transcript",
    {
        "source": "Required[Literal['youtube_transcript']]",
        "video_id": "Required[str]",
        "params": "dict[str, Any]",
        "callback_url": "str | None",
    },
    total=False,
)

AsyncSubmission = TypedDict(
    "AsyncSubmission",
    {
        "id": "str",
        "source": "str",
        "status": "str",
        "created_at": "str",
        "links": "list[JobLink]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

BulkJobCreated = TypedDict(
    "BulkJobCreated", {"job": "Required[BulkJob]", "upload": "Required[dict[str, Any]]"}, total=False
)

BulkJob = TypedDict(
    "BulkJob",
    {
        "id": "Required[str]",
        "source": "Required[Literal['youtube_metadata', 'youtube_transcript', 'youtube_captions', 'youtube_trainability', 'youtube_download']]",
        "status": "Required[Literal['awaiting_upload', 'running', 'paused', 'finalizing', 'completed', 'failed', 'cancelled']]",
        "input": "Required[dict[str, Any]]",
        "counts": "Required[dict[str, Any]]",
        "pauseReason": "Required[str | None]",
        "delivery": "Required[dict[str, Any]]",
        "error": "Required[None | dict[str, Any]]",
        "createdAt": "Required[str]",
        "startedAt": "Required[str | None]",
        "completedAt": "Required[str | None]",
        "expiresAt": "Required[str | None]",
        "links": "Required[list[JobLink]]",
    },
    total=False,
)

BulkJobPage = TypedDict(
    "BulkJobPage", {"data": "Required[list[BulkJob]]", "pagination": "Required[Pagination]"}, total=False
)

BulkJobResponse = TypedDict("BulkJobResponse", {"job": "Required[BulkJob]"}, total=False)

ConsoleJob = TypedDict(
    "ConsoleJob",
    {
        "createdAt": "Required[str]",
        "credits": "Required[float]",
        "durationMs": "Required[float | None]",
        "error": "Required[str | None]",
        "id": "Required[str]",
        "params": "Required[dict[str, Any]]",
        "progress": "Required[int]",
        "result": "Required[dict[str, Any] | None]",
        "source": "Required[str]",
        "status": "Required[Literal['completed', 'failed', 'pending', 'processing']]",
        "updatedAt": "Required[str | None]",
        "videoId": "Required[str | None]",
        "links": "list[JobLink]",
    },
    total=False,
)

CreateBulkJobRequest = TypedDict(
    "CreateBulkJobRequest",
    {
        "source": "Required[Literal['youtube_metadata', 'youtube_transcript', 'youtube_captions', 'youtube_trainability', 'youtube_download']]",
        "options": "dict[str, Any]",
        "callback_url": "str",
    },
    total=False,
)

DataQueryResponse = TypedDict(
    "DataQueryResponse",
    {"source": "str", "status": "str", "created_at": "str", "results": "list[Any]", "usage": "dict[str, Any]"},
    total=False,
)

DataSource = TypedDict(
    "DataSource",
    {
        "id": "Required[Literal['google_search', 'google_images', 'google_news', 'google_shopping', 'google_videos', 'google_places', 'youtube_search', 'youtube_search_extended', 'youtube_metadata', 'youtube_transcript', 'youtube_captions', 'youtube_trainability', 'youtube_channel', 'youtube_suggestions', 'youtube_download']]",
        "name": "Required[str]",
        "category": "Required[Literal['google', 'youtube']]",
        "product": "Required[Literal['google_search', 'youtube_data', 'youtube_download']]",
        "modes": "Required[list[Literal['realtime', 'async', 'batch']]]",
        "inputSchema": "Required[dict[str, Any]]",
        "estimatedCredits": "Required[float]",
        "requiresStorageDestination": "Required[bool]",
    },
    total=False,
)

Health = TypedDict(
    "Health",
    {
        "status": "Required[Literal['healthy', 'degraded']]",
        "service": "Required[str]",
        "version": "Required[str]",
        "time": "Required[str]",
    },
    total=False,
)

JobLink = TypedDict(
    "JobLink",
    {
        "rel": "Required[Literal['self', 'results', 'content', 'download']]",
        "href": "Required[str]",
        "method": "Required[Literal['GET']]",
        "expires_at": "str",
        "filename": "str",
        "content_type": "str",
        "size_bytes": "int",
    },
    total=False,
)

Pagination = TypedDict(
    "Pagination",
    {"nextCursor": "str | None", "previousCursor": "str | None", "hasMore": "Required[bool]", "limit": "Required[int]"},
    total=False,
)

PlanCatalog = TypedDict(
    "PlanCatalog",
    {
        "trialOffer": "PublicTrialOffer | None",
        "data": "Required[list[Plan]]",
        "currency": "Required[Literal['USD']]",
        "creditValueUsd": "Required[float]",
        "billingAvailability": "Required[Literal['available', 'unconfigured', 'unavailable']]",
        "billingMessage": "str | None",
    },
    total=False,
)

Plan = TypedDict(
    "Plan",
    {
        "id": "Required[str]",
        "slug": "Required[str]",
        "name": "Required[str]",
        "description": "Required[str]",
        "includedCredits": "Required[float]",
        "limits": "Required[PlanLimits]",
        "prices": "Required[list[PlanPrice]]",
        "features": "Required[list[str]]",
        "usagePrices": "Required[PlanUsagePrices]",
    },
    total=False,
)

PlanLimits = TypedDict(
    "PlanLimits",
    {"concurrency": "Required[int]", "maxBatchSize": "Required[int]", "maxPendingJobs": "Required[int]"},
    total=False,
)

PlanPrice = TypedDict(
    "PlanPrice",
    {
        "id": "Required[str]",
        "currency": "Required[Literal['USD']]",
        "unitAmount": "Required[int]",
        "credits": "Required[float]",
        "type": "Required[Literal['recurring', 'one_time']]",
        "interval": "Required[Literal['month', 'year', None]]",
    },
    total=False,
)

PlanUsagePrices = TypedDict(
    "PlanUsagePrices",
    {"googlePer1kCents": "Required[int]", "youtubePer1kCents": "Required[int]", "downloadPerTbCents": "Required[int]"},
    total=False,
)

Problem = TypedDict(
    "Problem",
    {
        "type": "Required[str]",
        "title": "Required[str]",
        "status": "Required[int]",
        "code": "Required[str]",
        "detail": "str",
        "requestId": "Required[str]",
        "fieldErrors": "list[FieldError]",
    },
    total=False,
)

FieldError = TypedDict(
    "FieldError", {"field": "Required[str]", "code": "Required[str]", "message": "Required[str]"}, total=False
)

PublicStatus = TypedDict(
    "PublicStatus",
    {
        "status": "Required[Literal['healthy', 'degraded', 'outage']]",
        "updatedAt": "Required[str]",
        "components": "Required[list[PublicStatusComponent]]",
    },
    total=False,
)

PublicStatusComponent = TypedDict(
    "PublicStatusComponent",
    {
        "id": "Required[str]",
        "name": "Required[str]",
        "status": "Required[Literal['operational', 'degraded', 'outage']]",
    },
    total=False,
)

PublicTrialOffer = TypedDict(
    "PublicTrialOffer",
    {
        "maxApiRequests": "int",
        "googleSearchRequests": "Required[int]",
        "youtubeDataRequests": "Required[int]",
        "downloadGigabytes": "Required[float]",
    },
    total=False,
)

Query_google_images = TypedDict(
    "Query_google_images",
    {"source": "Required[Literal['google_images']]", "query": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

Query_google_news = TypedDict(
    "Query_google_news",
    {"source": "Required[Literal['google_news']]", "query": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

Query_google_places = TypedDict(
    "Query_google_places",
    {"source": "Required[Literal['google_places']]", "query": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

Query_google_search = TypedDict(
    "Query_google_search",
    {"source": "Required[Literal['google_search']]", "query": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

Query_google_shopping = TypedDict(
    "Query_google_shopping",
    {"source": "Required[Literal['google_shopping']]", "query": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

Query_google_videos = TypedDict(
    "Query_google_videos",
    {"source": "Required[Literal['google_videos']]", "query": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

Query_youtube_captions = TypedDict(
    "Query_youtube_captions",
    {"source": "Required[Literal['youtube_captions']]", "video_id": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

Query_youtube_channel = TypedDict(
    "Query_youtube_channel",
    {"source": "Required[Literal['youtube_channel']]", "handle": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

Query_youtube_download = TypedDict(
    "Query_youtube_download",
    {
        "source": "Required[Literal['youtube_download']]",
        "video_id": "Required[str]",
        "params": "Required[dict[str, Any]]",
    },
    total=False,
)

Query_youtube_metadata = TypedDict(
    "Query_youtube_metadata",
    {"source": "Required[Literal['youtube_metadata']]", "video_id": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

Query_youtube_search = TypedDict(
    "Query_youtube_search",
    {"source": "Required[Literal['youtube_search']]", "query": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

Query_youtube_search_extended = TypedDict(
    "Query_youtube_search_extended",
    {"source": "Required[Literal['youtube_search_extended']]", "query": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

Query_youtube_suggestions = TypedDict(
    "Query_youtube_suggestions",
    {"source": "Required[Literal['youtube_suggestions']]", "query": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

Query_youtube_trainability = TypedDict(
    "Query_youtube_trainability",
    {"source": "Required[Literal['youtube_trainability']]", "video_id": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

Query_youtube_transcript = TypedDict(
    "Query_youtube_transcript",
    {"source": "Required[Literal['youtube_transcript']]", "video_id": "Required[str]", "params": "dict[str, Any]"},
    total=False,
)

UpdateBulkJobRequest = TypedDict(
    "UpdateBulkJobRequest", {"options": "dict[str, Any]", "callback_url": "str | None"}, total=False
)

UsageCounts = TypedDict(
    "UsageCounts",
    {
        "requests": "Required[int]",
        "completed": "Required[int]",
        "failed": "Required[int]",
        "credits": "Required[float]",
    },
    total=False,
)

GoogleSearchParams = TypedDict(
    "GoogleSearchParams",
    {"gl": "str", "hl": "str", "location": "str", "num": "int", "page": "int", "tbs": "str", "autocorrect": "bool"},
    total=False,
)

GoogleImagesParams = TypedDict(
    "GoogleImagesParams",
    {"gl": "str", "hl": "str", "location": "str", "num": "int", "page": "int", "tbs": "str", "autocorrect": "bool"},
    total=False,
)

GoogleNewsParams = TypedDict(
    "GoogleNewsParams",
    {"gl": "str", "hl": "str", "location": "str", "num": "int", "page": "int", "tbs": "str", "autocorrect": "bool"},
    total=False,
)

GoogleShoppingParams = TypedDict(
    "GoogleShoppingParams",
    {"gl": "str", "hl": "str", "location": "str", "num": "int", "page": "int", "tbs": "str", "autocorrect": "bool"},
    total=False,
)

GoogleVideosParams = TypedDict(
    "GoogleVideosParams",
    {"gl": "str", "hl": "str", "location": "str", "num": "int", "page": "int", "tbs": "str", "autocorrect": "bool"},
    total=False,
)

GooglePlacesParams = TypedDict(
    "GooglePlacesParams",
    {"gl": "str", "hl": "str", "location": "str", "num": "int", "page": "int", "tbs": "str", "autocorrect": "bool"},
    total=False,
)

YoutubeSearchParams = TypedDict(
    "YoutubeSearchParams", {"max_results": "int", "filters": "dict[str, Any] | None"}, total=False
)

YoutubeSearchExtendedParams = TypedDict(
    "YoutubeSearchExtendedParams", {"max_results": "int", "filters": "dict[str, Any] | None"}, total=False
)

YoutubeMetadataParams = TypedDict(
    "YoutubeMetadataParams", {"include_formats": "bool", "include_chapters": "bool"}, total=False
)

YoutubeTranscriptParams = TypedDict("YoutubeTranscriptParams", {"language": "str", "auto": "bool"}, total=False)

YoutubeCaptionsParams = TypedDict("YoutubeCaptionsParams", {"language": "str", "auto": "bool"}, total=False)

YoutubeTrainabilityParams = TypedDict("YoutubeTrainabilityParams", {}, total=False)

YoutubeChannelParams = TypedDict("YoutubeChannelParams", {"video_limit": "int"}, total=False)

YoutubeSuggestionsParams = TypedDict("YoutubeSuggestionsParams", {"language": "str", "region": "str"}, total=False)

YoutubeDownloadParams = TypedDict(
    "YoutubeDownloadParams",
    {
        "download_type": "Literal['audio_video', 'video', 'audio']",
        "video_quality": "Literal['best', 'worst', '<=144', '==144', '>=144', '<=360', '==360', '>=360', '<=480', '==480', '>=480', '<=720', '==720', '>=720', '<=1080', '==1080', '>=1080', '<=1440', '==1440', '>=1440', '<=2160', '==2160', '>=2160', '<=4320', '==4320', '>=4320']",
        "fps": "str",
        "audio_language": "Literal['default', 'original']",
        "audio_quality": "Literal['best', '320', '256', '192', '128']",
        "yt_dlp_format": "str",
        "upload_metadata": "bool",
        "output_format": "Literal['mp4', 'webm', 'mkv', 'm4a', 'mp3', 'opus']",
        "start_at": "str",
        "end_at": "str",
        "storage": "Required[dict[str, Any]]",
    },
    total=False,
)

RealtimeQuery = (
    Query_google_search
    | Query_google_images
    | Query_google_news
    | Query_google_shopping
    | Query_google_videos
    | Query_google_places
    | Query_youtube_search
    | Query_youtube_search_extended
    | Query_youtube_metadata
    | Query_youtube_transcript
    | Query_youtube_captions
    | Query_youtube_trainability
    | Query_youtube_channel
    | Query_youtube_suggestions
)

AsyncQuery = (
    AsyncQuery_google_search
    | AsyncQuery_google_images
    | AsyncQuery_google_news
    | AsyncQuery_google_shopping
    | AsyncQuery_google_videos
    | AsyncQuery_google_places
    | AsyncQuery_youtube_search
    | AsyncQuery_youtube_search_extended
    | AsyncQuery_youtube_metadata
    | AsyncQuery_youtube_transcript
    | AsyncQuery_youtube_captions
    | AsyncQuery_youtube_trainability
    | AsyncQuery_youtube_channel
    | AsyncQuery_youtube_suggestions
    | AsyncQuery_youtube_download
)

Source = Literal[
    "google_search",
    "google_images",
    "google_news",
    "google_shopping",
    "google_videos",
    "google_places",
    "youtube_search",
    "youtube_search_extended",
    "youtube_metadata",
    "youtube_transcript",
    "youtube_captions",
    "youtube_trainability",
    "youtube_channel",
    "youtube_suggestions",
    "youtube_download",
]

GoogleSearchResponse = TypedDict(
    "GoogleSearchResponse",
    {
        "source": "Required[Literal['google_search']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[dict[str, Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

GoogleImagesResponse = TypedDict(
    "GoogleImagesResponse",
    {
        "source": "Required[Literal['google_images']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[dict[str, Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

GoogleNewsResponse = TypedDict(
    "GoogleNewsResponse",
    {
        "source": "Required[Literal['google_news']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[dict[str, Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

GoogleShoppingResponse = TypedDict(
    "GoogleShoppingResponse",
    {
        "source": "Required[Literal['google_shopping']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[dict[str, Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

GoogleVideosResponse = TypedDict(
    "GoogleVideosResponse",
    {
        "source": "Required[Literal['google_videos']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[dict[str, Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

GooglePlacesResponse = TypedDict(
    "GooglePlacesResponse",
    {
        "source": "Required[Literal['google_places']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[dict[str, Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

YoutubeSearchResponse = TypedDict(
    "YoutubeSearchResponse",
    {
        "source": "Required[Literal['youtube_search']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[dict[str, Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

YoutubeSearchExtendedResponse = TypedDict(
    "YoutubeSearchExtendedResponse",
    {
        "source": "Required[Literal['youtube_search_extended']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[dict[str, Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

YoutubeMetadataResponse = TypedDict(
    "YoutubeMetadataResponse",
    {
        "source": "Required[Literal['youtube_metadata']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[dict[str, Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

YoutubeTranscriptResponse = TypedDict(
    "YoutubeTranscriptResponse",
    {
        "source": "Required[Literal['youtube_transcript']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[dict[str, Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

YoutubeCaptionsResponse = TypedDict(
    "YoutubeCaptionsResponse",
    {
        "source": "Required[Literal['youtube_captions']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[dict[str, Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

YoutubeTrainabilityResponse = TypedDict(
    "YoutubeTrainabilityResponse",
    {
        "source": "Required[Literal['youtube_trainability']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[dict[str, Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

YoutubeChannelResponse = TypedDict(
    "YoutubeChannelResponse",
    {
        "source": "Required[Literal['youtube_channel']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[dict[str, Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)

YoutubeSuggestionsResponse = TypedDict(
    "YoutubeSuggestionsResponse",
    {
        "source": "Required[Literal['youtube_suggestions']]",
        "status": "Required[str]",
        "created_at": "str",
        "results": "Required[list[list[Any]]]",
        "usage": "dict[str, Any]",
    },
    total=False,
)
