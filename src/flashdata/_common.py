from __future__ import annotations

import copy
import json
import math
import re
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
    p = urlsplit(value)
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
    p = urlsplit(url)
    try:
        actual = origin(f"{p.scheme}://{p.netloc}")
        advertised = origin(expected)
    except ValidationError:
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
        request_id=response.headers.get("x-request-id"),
        retry_after=response.headers.get("retry-after"),
        body=data,
    )


def validate_query(value: Any, *, async_mode: bool = False) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("source") not in SCHEMAS:
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
        raise ValidationError(f"Invalid {path}: violates {error.validator}.")
    callback = data.get("callback_url")
    if callback:
        p = urlsplit(callback)
        if p.scheme != "https" or not p.hostname or p.username or p.password or p.fragment or p.port not in (None, 443):
            raise ValidationError("callback_url must be a public HTTPS URL on port 443.")
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
    if "callback_url" in data and data["callback_url"] is not None and not isinstance(data["callback_url"], str):
        raise ValidationError("callback_url must be a string or null.")
    if not partial and data["source"] == "youtube_download" and not data.get("options", {}).get("storage"):
        raise ValidationError("Bulk downloads require options.storage.")
    return data


def decode_json(body: bytes) -> dict[str, Any]:
    try:
        value = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        raise ProtocolError("The response was not valid JSON.") from None
    if not isinstance(value, dict):
        raise ProtocolError("Expected a JSON object response.")
    return value
