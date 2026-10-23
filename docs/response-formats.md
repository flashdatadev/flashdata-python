# JSON, plain text and Markdown

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

Responses are JSON dictionaries by default. Use `accept="text/plain"` for a string,
or `respond_with="markdown"` for Markdown content. These options set the HTTP
`Accept` and `X-Respond-With` headers; keep them outside query `params`.

| `accept` | `respond_with` | Return value |
| --- | --- | --- |
| `"application/json"` (default) | Omitted | Dictionary with the original `results` |
| `"text/plain"` | Omitted | String with the original fields as indented text |
| `"application/json"` (default) | `"markdown"` | Dictionary with `content` replacing `results` |
| `"text/plain"` | `"markdown"` | String with metadata followed by Markdown |

Markdown responses retain source links, transcript timestamps, and response metadata.
The SDK returns the server's content without generating a summary.

## Search and transcripts

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    search = client.google.search("vector databases", respond_with="markdown")
    print(search["content"])

    transcript = client.youtube.transcript(
        "dQw4w9WgXcQ", accept="text/plain", respond_with="markdown"
    )
    print(transcript)
```

Each call above is a separate query. All realtime source helpers and
`queries.realtime()` accept both options. For original fields as text, pass only
`accept="text/plain"`.

## Background jobs and batches

`queries.submit()`, `queries.batch()`, background source helpers, and `jobs.get()`
accept `accept`. Their plain-text responses contain receipts or status fields.
Keep the default JSON receipt when your application needs to save job IDs.

Choose Markdown when retrieving completed results with `jobs.result()`:

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    receipt = client.google.search("vector databases", mode="async")
    job_id = receipt["id"]
    print(job_id, flush=True)
    client.jobs.wait(job_id)
    print(client.jobs.get(job_id, accept="text/plain"))
    print(client.jobs.result(job_id, accept="text/plain", respond_with="markdown"))
```

Retrieving the same completed result in another format does not run another query or
charge query credits. Format choices apply to each call and are not saved with a job.
`jobs.get()` unwraps the `job` object for JSON; plain text contains the full status
response. `jobs.wait()` continues to return a job dictionary.

Download receipts support `accept`; completed download manifests also support Markdown
through `jobs.result()`. Media files, bulk exports, account methods and public discovery
keep their existing formats.

## Async client and errors

`AsyncFlashData` uses the same options with `await`. Type hints distinguish original
response dictionaries, `MarkdownQueryResult`, and strings.

```python
import asyncio
import os
from flashdata import AsyncFlashData

async def main():
    async with AsyncFlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
        text = await client.google.search("vector databases", accept="text/plain")
        print(text)

asyncio.run(main())
```

The SDK accepts `"application/json"` and `"text/plain"` for `accept`, and `"markdown"`
or `None` for `respond_with`. Invalid choices raise `ValidationError` before a request.
`respond_with` applies to realtime queries and completed results; background helpers
reject it. API errors still raise `APIError`, including when plain text was requested.

For HTTP examples and response bodies, see the
[API response-format guide](https://flashdata.dev/docs/guides/response-formats).
