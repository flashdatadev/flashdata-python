# SDK architecture

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

The public clients own two HTTPX pools: one for FlashData API requests, one for signed
storage. Separate pools prevent API cookies and credentials from reaching object storage.
The Data API handles execution; the Management API handles account, job, and bulk state.
Source helpers construct typed wire dictionaries and delegate to `queries`.

Local JSON Schema validation checks source names, fields, types and limits. The server
remains authoritative for plan admission, provider storage rules, state transitions,
available subtitle tracks, and source availability. Unknown response fields are preserved.

| Location | Purpose |
| --- | --- |
| `src/flashdata/_client.py`, `_async_client.py` | HTTP lifecycle, bounded reads, signed results and uploads |
| `src/flashdata/_resources.py` | Sync and async source, account, jobs, pagination and bulk resources |
| `src/flashdata/_common.py` | Validation, redaction, safe origins, JSON, text and NDJSON decoding |
| `src/flashdata/types.py` | Public wire types and source parameter hints |
| `src/flashdata/errors.py` | Stable public exception classes |
| `openapi.json`, `source-contract.json` | API-key endpoint and source contract snapshots |
| `tests/` | Transport, HTTP integration, typed consumer, documentation and opt-in live checks |

When API contracts change, update snapshots, schemas, types, guides, examples, and
contract tests together. HTTP errors must remain structured, and mutation failures must
never introduce implicit retries. Resource helpers preserve the API's source-specific
result shapes rather than inventing a universal row format.

Refresh `openapi.json` with `python scripts/update_contract.py --openapi PATH_TO_PUBLIC_OPENAPI_JSON`.
Add `--check` to detect drift without writing. The snapshot includes only the SDK's
supported operations and API-key authentication. Response options are per-request
headers; errors remain structured and polling continues to use JSON.

Stored-result test examples cover all 15 sources in all four response formats.
Regenerate them with `python scripts/update_response_fixtures.py --formatter PATH_TO_RESPONSE_FORMATTING_JS`;
add `--check` to compare them with the API serializer. Node.js is needed for regeneration
only. The normal Python test suite reads the saved examples and checks that formatting
preserves each job's identity, status, usage and completion/expiry timestamps.
