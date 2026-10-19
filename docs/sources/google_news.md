# Google news

Track coverage with headline `title`, publisher `source`, `link`, and `date`. Dates may be relative strings; retain the request timestamp when recording them.

## Example

```python
from flashdata import FlashData

with FlashData() as client:
    response = client.google.news("renewable energy", num=5, gl="us", hl="en")
    for payload in response["results"]:
        for item in payload.get("news", []):
            print(item.get("title"), item.get("link") or item.get("videoId") or item.get("address"))
```

Run `python examples/google_news.py renewable energy --output artifacts/google_news.json` from the checkout. Use `--help` for options. The command consumes credits.

## Parameters

`query` is required. Source options are keyword arguments, or entries in `params` when using `queries`. Data helpers default to realtime; pass `mode="async"` for background work. `timeout` controls the HTTP request.

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
