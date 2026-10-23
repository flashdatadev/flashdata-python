# YouTube channels

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs/sources/youtube_channel)

Read channel identity, description, subscriber/view counts, and a bounded `videos` list. Pass a handle such as `@freecodecamp`, and set `video_limit` to control the number of recent entries.

## Example

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.youtube.channel("@freecodecamp", video_limit=5)
    for payload in response["results"]:
        for item in payload.get("videos", []):
            print(item.get("title"), item.get("link") or item.get("videoId") or item.get("address"))
```

Run `python examples/youtube_channel.py @freecodecamp --output artifacts/youtube_channel.json` from the checkout. Use `--help` for options. The command consumes credits.

## Parameters

`handle` is required. Source options are keyword arguments, or entries in `params` when using `queries`. Data helpers default to realtime; pass `mode="async"` for background work. `timeout` controls the HTTP request.

JSON is the default. Use `accept="text/plain"` for text, or `respond_with="markdown"`
for Markdown content in realtime results. For background work, choose Markdown when
reading the completed result. See [response formats](../response-formats.md).

| Option | Type / constraints | Default |
| --- | --- | --- |
| `video_limit` | integer; 1–100 | 20 |

## Use at scale

All sources support [background and batch queries](../jobs.md). Read [errors and recovery](../errors.md) before adding application retries.
