# Client configuration and responses

`FlashData(api_key=None, *, data_url="https://data.flashdata.dev", management_url="https://api.flashdata.dev", timeout=120, max_response_bytes=67108864, transport=None, storage_transport=None)`

`AsyncFlashData` has the same options. Timeouts are seconds. Use context managers to
close both HTTP pools, or call `close()` / `await aclose()`. HTTPX transports can be
injected for tests or a custom networking implementation. A client must stay within
its creating process and an async client within its event loop.

`flashdata.types` contains TypedDict request/response types and source parameter types.
Wire field names remain intact, including `from` in usage responses; the Python usage
method accepts `from_` and sends `from`.

Configured API URLs are HTTPS origins without paths, credentials, query strings or
fragments. Loopback HTTP is supported for local development. Do not append `/v1`, `/v2`
or `/mcp`; the SDK adds the appropriate route. Custom origins receive your API key.

Query methods return the original JSON envelope. Account reads return their original
JSON object. Job and bulk `get`/control methods unwrap the outer `job` field. A failed
HTTP response raises a structured exception. A failed item inside a successful batch
stays in the batch result; inspect every item.

The SDK validates source input shape without injecting catalog defaults. Server-side
admission, provider-specific storage rules, media format compatibility and permissions
remain enforced by FlashData. Public discovery requests omit the API key. Generic query
methods use the checked-in source contract and reject unknown fields until the SDK is
updated for a newer contract.
