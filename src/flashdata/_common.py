from __future__ import annotations

import copy
import gzip
import io
import ipaddress
import json
import math
import re
import zlib
from importlib.resources import files
from typing import Any
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

from .errors import APIError, ProtocolError, ValidationError

SCHEMAS = json.loads(files("flashdata").joinpath("_schemas.json").read_text(encoding="utf-8"))
SOURCES = tuple(SCHEMAS)
BULK_SOURCES = (
    "youtube_metadata",
    "youtube_transcript",
    "youtube_captions",
    "youtube_trainability",
    "youtube_download",
)
SECRET_KEYS = {"api_key", "access_key", "secret_key", "private_key", "sas_token", "authorization", "x-api-key"}


def positive(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
        raise ValidationError(f"{name} must be a finite positive number.")
    return value


def integer(value: int, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValidationError(f"{name} must be an integer from {minimum} to {maximum}.")
    return value


def origin(value: str) -> str:
    if not isinstance(value, str):
        raise ValidationError("API URLs must be HTTPS origins, or loopback HTTP origins.")
    try:
        p = urlsplit(value)
    except ValueError:
        raise ValidationError("Invalid API URL.") from None
    if (
        p.scheme not in ("https", "http")
        or not p.hostname
        or p.username
        or p.password
        or p.query
        or p.fragment
        or p.path not in ("", "/")
    ):
        raise ValidationError("API URLs must be origins without credentials, paths, queries or fragments.")
    if p.scheme == "http" and p.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValidationError("HTTP is supported only for loopback development.")
    try:
        port = p.port
    except ValueError:
        raise ValidationError("Invalid API port.") from None
    host = f"[{p.hostname}]" if ":" in p.hostname else p.hostname
    port_text = f":{port}" if port and port != (443 if p.scheme == "https" else 80) else ""
    return f"{p.scheme}://{host}{port_text}"


def signed_url(url: str, expected: str | None) -> str:
    if not isinstance(url, str) or not isinstance(expected, str):
        raise ProtocolError("The API has not advertised a signed-storage origin.")
    try:
        p = urlsplit(url)
        actual = origin(f"{p.scheme}://{p.netloc}")
        advertised = origin(expected)
    except (ValidationError, ValueError):
        raise ProtocolError("Invalid signed-storage origin.") from None
    if p.username or p.password or p.fragment or actual != advertised:
        raise ProtocolError("Signed URL does not match the authenticated storage origin.")
    return url


def identifier(value: str, bulk: bool = False) -> str:
    pattern = r"bulk_[A-Za-z0-9_-]{8,}" if bulk else r"job_[A-Za-z0-9_-]+"
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValidationError("Invalid bulk ID." if bulk else "Invalid job ID.")
    return value


def redact(value: Any, secrets: tuple[str, ...] = ()) -> Any:
    if isinstance(value, dict):
        return {k: "[REDACTED]" if k.lower() in SECRET_KEYS else redact(v, secrets) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, secrets) for v in value]
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
    return value


def secret_values(value: Any) -> tuple[str, ...]:
    found = []
    if isinstance(value, dict):
        for k, v in value.items():
            if k.lower() in SECRET_KEYS and isinstance(v, str):
                found.append(v)
            else:
                found.extend(secret_values(v))
    elif isinstance(value, list):
        for item in value:
            found.extend(secret_values(item))
    return tuple(found)


def api_error(response: Any, body: bytes, secrets: tuple[str, ...]) -> APIError:
    try:
        data = redact(json.loads(body), secrets)
    except (ValueError, UnicodeDecodeError):
        data = None
    message = (data.get("detail") or data.get("message") or data.get("title")) if isinstance(data, dict) else None
    return APIError(
        response.status_code,
        message if isinstance(message, str) else f"HTTP {response.status_code}.",
        code=data.get("code") if isinstance(data, dict) else None,
        request_id=response.headers.get("x-request-id") or (data.get("requestId") if isinstance(data, dict) else None),
        retry_after=response.headers.get("retry-after")
        or (str(data["retry_after"]) if isinstance(data, dict) and data.get("retry_after") is not None else None),
        body=data,
    )


def validate_callback(callback: Any) -> None:
    if callback is None or callback == "":
        return
    message = "callback_url must be a public HTTPS URL on port 443."
    try:
        if not isinstance(callback, str) or len(callback) > 2048:
            raise ValueError
        p = urlsplit(callback)
        if (
            p.scheme != "https"
            or not p.hostname
            or "." not in p.hostname
            or p.username
            or p.password
            or p.fragment
            or p.port not in (None, 443)
        ):
            raise ValueError
        try:
            address = ipaddress.ip_address(p.hostname)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise ValueError
    except ValueError:
        raise ValidationError(message) from None


def validate_query(value: Any, *, async_mode: bool = False) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("source"), str) or value["source"] not in SCHEMAS:
        raise ValidationError("Choose a supported source and provide a query object.")
    data = copy.deepcopy(value)
    source = data["source"]
    if not async_mode and source == "youtube_download":
        raise ValidationError("youtube_download supports background submission and batch only.")
    schema = copy.deepcopy(SCHEMAS[source])
    schema["additionalProperties"] = False
    if async_mode:
        schema["properties"]["callback_url"] = {"type": ["string", "null"], "maxLength": 2048}
    error = next(Draft202012Validator(schema).iter_errors(data), None)
    if error:
        path = ".".join(str(part) for part in error.absolute_path) or "query"
        # ValidationError.message may contain credentials or whole input objects.
        constraint = error.validator
        expected = error.validator_value
        hint = {
            "minimum": f"must be at least {expected}",
            "maximum": f"must be at most {expected}",
            "type": f"must have type {expected}",
            "minLength": f"must contain at least {expected} characters",
            "maxLength": f"must contain at most {expected} characters",
            "required": "a required field is missing",
            "additionalProperties": "contains unsupported fields",
            "enum": f"must be one of {expected}",
            "pattern": "has an invalid format",
        }.get(constraint, f"violates {constraint}")
        raise ValidationError(f"Invalid {path}: {hint}.")
    validate_callback(data.get("callback_url"))
    for field in ("query", "handle", "video_id"):
        if field in data and not data[field].strip():
            raise ValidationError(f"{field} must not be blank.")
    return data


def bulk_input(value: Any, *, partial: bool = False) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or not value
        or set(value) - ({"options", "callback_url"} if partial else {"source", "options", "callback_url"})
    ):
        raise ValidationError("Invalid bulk request fields.")
    data = copy.deepcopy(value)
    if not partial and data.get("source") not in BULK_SOURCES:
        raise ValidationError("Bulk supports metadata, transcript, captions, license checks and downloads.")
    if "options" in data and not isinstance(data["options"], dict):
        raise ValidationError("Bulk options must be an object.")
    try:
        json.dumps(data, allow_nan=False)
    except (TypeError, ValueError):
        raise ValidationError("Bulk request values must be valid JSON.") from None
    validate_callback(data.get("callback_url"))
    if not partial:
        options = copy.deepcopy(data.get("options", {}))
        result_storage = options.pop("result_storage", None)
        if result_storage is not None:
            if data["source"] == "youtube_download" or not isinstance(result_storage, dict):
                raise ValidationError("result_storage applies to bulk data sources and must be an object.")
            storage_schema = SCHEMAS["youtube_download"]["properties"]["params"]["properties"]["storage"]
            if not Draft202012Validator(storage_schema).is_valid(result_storage):
                raise ValidationError("Invalid options.result_storage configuration.")
        validate_query({"source": data["source"], "video_id": "dQw4w9WgXcQ", "params": options}, async_mode=True)
    if not partial and data["source"] == "youtube_download" and not data.get("options", {}).get("storage"):
        raise ValidationError("Bulk downloads require options.storage.")
    return data


def response_headers(accept: Any, respond_with: Any = None) -> dict[str, str]:
    if accept not in ("application/json", "text/plain"):
        raise ValidationError("accept must be application/json or text/plain.")
    if respond_with not in (None, "markdown"):
        raise ValidationError("respond_with must be markdown or None.")
    headers = {"Accept": accept}
    if respond_with is not None:
        headers["X-Respond-With"] = respond_with
    return headers


class ResultRedirect:
    """Distinguish an HTTP redirect from a plain-text response body."""

    def __init__(self, location: str):
        self.location = location


def decode_response(body: bytes, accept: str) -> dict[str, Any] | str:
    if accept == "text/plain":
        try:
            return body.decode("utf-8")
        except UnicodeDecodeError:
            raise ProtocolError("The response was not valid UTF-8 text.") from None
    return decode_json(body)


def decode_json(body: bytes) -> dict[str, Any]:
    try:
        value = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        raise ProtocolError("The response was not valid JSON.") from None
    if not isinstance(value, dict):
        raise ProtocolError("Expected a JSON object response.")
    return value


def result_rows(raw: bytes, max_bytes: int, max_line_bytes: int):
    """Read a bounded NDJSON part, allowing HTTP stacks that already decoded gzip."""
    stream = gzip.GzipFile(fileobj=io.BytesIO(raw)) if raw.startswith(b"\x1f\x8b") else io.BytesIO(raw)
    try:
        with stream:
            total = 0
            while True:
                line = stream.readline(max_line_bytes + 1)
                if not line:
                    break
                total += len(line)
                if len(line) > max_line_bytes or total > max_bytes:
                    from .errors import ResponseTooLargeError

                    raise ResponseTooLargeError("Decompressed result part exceeds configured limits.")
                if line.strip():
                    yield decode_json(line)
    except (OSError, EOFError, zlib.error):
        raise ProtocolError("Invalid or truncated gzip result part.") from None


def job_record(value: Any) -> Any:
    if not isinstance(value, dict) or not isinstance(value.get("job"), dict):
        raise ProtocolError("Expected a job response containing a job object.")
    return value["job"]
