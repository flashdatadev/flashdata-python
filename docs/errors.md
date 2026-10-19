# Errors and recovery

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

All SDK exceptions inherit from `FlashDataError`. Catch specific errors when you can
recover and let unexpected failures reach your application's error reporting.

| Exception | Meaning and next step |
| --- | --- |
| `ValidationError` | Invalid local input; no request was sent. Correct the indicated field. |
| `APIError` | Non-success HTTP response from API or storage. Inspect structured attributes. |
| `RequestTimeoutError` | A read exceeded its network timeout. The same read can be repeated. |
| `ConnectionError` | Read or storage upload connection failed. Check network and existing job state. |
| `SubmissionUnknownError` | A mutation lost its response; it may have taken effect. Reconcile first. |
| `PollingTimeoutError` | Polling deadline reached. `.job_id` can be saved and read again. |
| `JobFailedError` | Terminal job failure/cancellation. Inspect `.job` for source details. |
| `JobPausedError` | Bulk needs action before progress can continue. Inspect `.job`. |
| `ProtocolError` | Malformed JSON, gzip, response envelope, or unsafe signed redirect. |
| `ResponseTooLargeError` | Response, decompressed part or line exceeded configured bounds. |

## HTTP errors

```python
import os
from flashdata import APIError, FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    try:
        client.youtube.captions("dQw4w9WgXcQ", language="en", auto=False)
    except APIError as error:
        print(error.status_code, error.code, error.request_id)
        print("Retry after:", error.retry_after)
        print("Invalid fields:", error.field_errors)
```

`APIError.body` preserves parsed JSON with known credential fields redacted. API-key and
request storage secret values are removed from server error text. Avoid dumping request
bodies, raw signed URLs or private application data in your own logs. `retry_after` is
the header value, or the Data API's `retry_after` field converted to a string. It may be
absent. `request_id` can come from a header or a Management API problem response.

Typical HTTP statuses are 400/422 for input errors, 401 for authentication, 402 for credit
admission, 403 for access, 404 for absent or inaccessible jobs, 409 for state conflicts,
410 for expired results, 429 for limits, and 5xx for service errors. Source-specific
errors such as an unavailable caption track still surface as API errors. Check the
message/code rather than assuming every failure is transient.

## Unknown submissions and retries

The SDK never retries automatically. POST/PATCH/DELETE connection failures and timeouts
raise `SubmissionUnknownError`, even when the precise server outcome cannot be known.
Repeating a paid query could create another charge. Save IDs as soon as receipts arrive;
on polling or process failure, continue with those IDs. Standard job listing is unavailable
to API keys, so if no ID was received, inspect your account or contact support before
resubmitting. No idempotency key behavior is promised by this SDK.

Read requests are safer to retry with application-controlled backoff. Respect `retry_after`
and your own retry budget. A polling deadline leaves accepted work running. `wait()`
stops on API/network errors rather than concealing a rate limit behind more requests.
Async task cancellation propagates as Python's `asyncio.CancelledError`; a local
interrupt or cancellation does not undo server work. If cancellation happened during a
submission, treat admission as unknown and reconcile before repeating the paid request.
