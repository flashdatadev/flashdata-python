# YouTube license labels

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs/sources/youtube_trainability)

Inspect the API’s `permitted` labels for a video. The source name is `youtube_trainability`, but these labels report detected license information; they do not grant model-training or media-reuse permission.

## Example

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.youtube.license_check("dQw4w9WgXcQ")
    for video in response["results"]:
        print(video["videoId"], video.get("permitted", []))
```

Run `python examples/youtube_trainability.py dQw4w9WgXcQ --output artifacts/youtube_trainability.json` from the checkout. Use `--help` for options. The command consumes credits.

## Parameters

`video_id` is required. Source options are keyword arguments, or entries in `params` when using `queries`. Data helpers default to realtime; pass `mode="async"` for background work. `timeout` controls the HTTP request.

| Option | Type / constraints | Default |
| --- | --- | --- |
| — | No source-specific options | — |

## Use at scale

Use [bulk jobs](../bulk.md) for a file of video IDs with the same options. All sources support [background and batch queries](../jobs.md). Read [errors and recovery](../errors.md) before adding application retries.
