# YouTube metadata

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs/sources/youtube_metadata)

Enrich video IDs with title, channel, duration, upload date, counts, and available transcript languages. Disable formats and chapters when they are unnecessary to reduce payload size.

## Example

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.youtube.metadata("dQw4w9WgXcQ", include_formats=False, include_chapters=False)
    for video in response["results"]:
        print(video["title"], video.get("duration"), video.get("transcriptLanguages", []))
```

Run `python examples/youtube_metadata.py dQw4w9WgXcQ --output artifacts/youtube_metadata.json` from the checkout. Use `--help` for options. The command consumes credits.

## Parameters

`video_id` is required. Source options are keyword arguments, or entries in `params` when using `queries`. Data helpers default to realtime; pass `mode="async"` for background work. `timeout` controls the HTTP request.

| Option | Type / constraints | Default |
| --- | --- | --- |
| `include_formats` | boolean | true |
| `include_chapters` | boolean | true |

## Use at scale

Use [bulk jobs](../bulk.md) for a file of video IDs with the same options. All sources support [background and batch queries](../jobs.md). Read [errors and recovery](../errors.md) before adding application retries.
