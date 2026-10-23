"""Official FlashData Python SDK."""

from ._client import FlashData
from ._async_client import AsyncFlashData
from .types import ContentRepresentation, MarkdownQueryResult, ResponseAccept
from .errors import (
    APIError,
    ConnectionError,
    FlashDataError,
    JobFailedError,
    JobPausedError,
    PollingTimeoutError,
    ProtocolError,
    RequestTimeoutError,
    ResponseTooLargeError,
    SubmissionUnknownError,
    ValidationError,
)

__version__ = "1.1.0"
__all__ = [
    "FlashData",
    "AsyncFlashData",
    "ContentRepresentation",
    "MarkdownQueryResult",
    "ResponseAccept",
    "APIError",
    "ConnectionError",
    "FlashDataError",
    "JobFailedError",
    "JobPausedError",
    "PollingTimeoutError",
    "ProtocolError",
    "RequestTimeoutError",
    "ResponseTooLargeError",
    "SubmissionUnknownError",
    "ValidationError",
]
