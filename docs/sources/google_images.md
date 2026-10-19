# Google images

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs/sources/google_images)

Discover visual assets and their source pages. `imageUrl` is the image resource, `thumbnailUrl` is the preview, and `link` is the source page. These URLs do not grant reuse rights.

## Example

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.google.images("coffee beans", num=5, gl="us", hl="en")
    for payload in response["results"]:
        for item in payload.get("images", []):
            print(item.get("title"), item.get("link") or item.get("videoId") or item.get("address"))
```

Run `python examples/google_images.py coffee beans --output artifacts/google_images.json` from the checkout. Use `--help` for options. The command consumes credits.

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
