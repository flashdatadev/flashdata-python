# Google web search

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs/sources/google_search)

Build retrieval inputs or monitor search listings. Each organic hit may include `title`, `link`, `snippet`, and `position`.

## Example

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.google.search("coffee roasters", num=5, gl="us", hl="en")
    for payload in response["results"]:
        for item in payload.get("organic", []):
            print(item.get("title"), item.get("link") or item.get("videoId") or item.get("address"))
```

Run `python examples/google_search.py coffee roasters --output artifacts/google_search.json` from the checkout. Use `--help` for options. The command consumes credits.

## Parameters

`query` is required. Source options are keyword arguments, or entries in `params` when using `queries`. Data helpers default to realtime; pass `mode="async"` for background work. `timeout` controls the HTTP request.

JSON is the default. Use `accept="text/plain"` for text, or `respond_with="markdown"`
for Markdown content in realtime results. For background work, choose Markdown when
reading the completed result. See [response formats](../response-formats.md).

| Option | Type / constraints | Default |
| --- | --- | --- |
| `gl` | string; pattern `^[A-Za-z]{2}$` | service default / optional |
| `hl` | string; pattern `^[A-Za-z0-9-]+$` | service default / optional |
| `location` | string | service default / optional |
| `num` | integer; 1–100 | service default / optional |
| `page` | integer; 1–100 | service default / optional |
| `tbs` | string | service default / optional |
| `autocorrect` | boolean | service default / optional |

## Use at scale

Use [bounded Google pagination](../pagination.md) for multiple pages. Each page is a separately charged request. All sources support [background and batch queries](../jobs.md). Read [errors and recovery](../errors.md) before adding application retries.
