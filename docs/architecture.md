# SDK architecture

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
| `src/flashdata/_common.py` | Validation, redaction, safe origins, JSON and NDJSON decoding |
| `src/flashdata/types.py` | Public wire types and source parameter hints |
| `src/flashdata/errors.py` | Stable public exception classes |
| `openapi.json`, `source-contract.json` | API-key endpoint and source contract snapshots |
| `tests/` | Transport, HTTP integration, typed consumer, documentation and opt-in live checks |

When API contracts change, update snapshots, schemas, types, guides, examples, and
contract tests together. HTTP errors must remain structured, and mutation failures must
never introduce implicit retries. Resource helpers preserve the API's source-specific
result shapes rather than inventing a universal row format.
