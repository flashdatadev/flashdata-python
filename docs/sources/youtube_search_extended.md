# YouTube extended search

Collect a larger discovery set in one request. Request 1–700 entities with `max_results`; fewer may be available. Use an explicit bound for predictable workloads.

## Example

```python
from flashdata import FlashData

with FlashData() as client:
    response = client.youtube.search_extended("python tutorial", max_results=5)
    for payload in response["results"]:
        for item in payload.get("results", []):
            print(item.get("title"), item.get("link") or item.get("videoId") or item.get("address"))
```

Run `python examples/youtube_search_extended.py python tutorial --output artifacts/youtube_search_extended.json` from the checkout. Use `--help` for options. The command consumes credits.

## Parameters

`query` is required. Source options are keyword arguments, or entries in `params` when using `queries`. Data helpers default to realtime; pass `mode="async"` for background work. `timeout` controls the HTTP request.

| Option | Type / constraints | Default |
| --- | --- | --- |
| `max_results` | integer; 1–700 | 20 |
| `filters` | object / null | service default / optional |

### Search filters

`filters` is a dictionary. Supported fields:

| Field | Allowed values |
| --- | --- |
| `360` | boolean |
| `duration` | `<4`, `4-20`, `>20` |
| `sort_by` | `rating`, `relevance`, `view_count`, `upload_date` |
| `type` | `video`, `channel`, `playlist`, `movie` |
| `upload_date` | `today`, `last_hour`, `this_week`, `this_month`, `this_year` |
| `3d` | boolean |
| `4k` | boolean |
| `creative_commons` | boolean |
| `hd` | boolean |
| `hdr` | boolean |
| `live` | boolean |
| `location` | boolean |
| `purchased` | boolean |
| `subtitles` | boolean |
| `vr180` | boolean |

For example, `filters={"type": "video", "duration": "<4", "hd": True}`. Unsupported filters are rejected locally.

## Use at scale

All sources support [background and batch queries](../jobs.md). Read [errors and recovery](../errors.md) before adding application retries.
