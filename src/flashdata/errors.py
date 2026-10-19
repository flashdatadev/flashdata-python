"""Public exceptions. Request bodies, keys and signed URLs are never in reprs."""

from typing import Any


class FlashDataError(Exception):
    """Base SDK exception."""


class ValidationError(FlashDataError, ValueError):
    """An input is invalid; no HTTP request was sent."""


class APIError(FlashDataError):
    """A non-success response from FlashData or signed storage."""

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        code: str | None = None,
        request_id: str | None = None,
        retry_after: str | None = None,
        body: Any = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.request_id = request_id
        self.retry_after = retry_after
        self.body = body


class ConnectionError(FlashDataError):
    """The network request failed."""


class RequestTimeoutError(ConnectionError):
    """A read request exceeded its network timeout."""


class SubmissionUnknownError(ConnectionError):
    """A mutation lost its response and may already have taken effect."""


class ProtocolError(FlashDataError):
    """An unexpected response, redirect or result origin was rejected."""


class ResponseTooLargeError(ProtocolError):
    """The configured response or decompressed-line limit was exceeded."""


class PollingTimeoutError(FlashDataError):
    def __init__(self, job_id: str):
        super().__init__(f"Waiting for {job_id} timed out; continue reading the same ID.")
        self.job_id = job_id


class JobFailedError(FlashDataError):
    def __init__(self, job: dict[str, Any]):
        super().__init__(f"Job {job.get('id', 'unknown')} ended with status {job.get('status')}.")
        self.job = job


class JobPausedError(JobFailedError):
    """A bulk job is paused and needs explicit user action."""
