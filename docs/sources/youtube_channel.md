# YouTube channels

Read channel identity, description, subscriber/view counts, and a bounded `videos` list. Pass a handle such as `@freecodecamp`, and set `video_limit` to control the number of recent entries.

## Example

```python
from flashdata import FlashData

with FlashData() as client:
    response = client.youtube.channel("@freecodecamp", video_limit=5)
    for payload in response["results"]:
        for item in payload.get("videos", []):
            print(item.get("title"), item.get("link") or item.get("videoId") or item.get("address"))
```

Run `python examples/youtube_channel.py @freecodecamp --output artifacts/youtube_channel.json` from the checkout. Use `--help` for options. The command consumes credits.

## Parameters

`handle` is required. Source options are keyword arguments, or entries in `params` when using `queries`. Data helpers default to realtime; pass `mode="async"` for background work. `timeout` controls the HTTP request.

| Option | Type / constraints | Default |
| --- | --- | --- |
| `video_limit` | integer; 1–100 | 20 |

## Use at scale

All sources support [background and batch queries](../jobs.md). Read [errors and recovery](../errors.md) before adding application retries.
