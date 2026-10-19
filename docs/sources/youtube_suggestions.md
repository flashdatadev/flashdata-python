# YouTube suggestions

Expand query ideas using autocomplete. Each item of the outer `results` array is a list of suggestion strings, rather than an object with a `suggestions` property.

## Example

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.youtube.suggestions("python", language="en", region="US")
    for suggestions in response["results"]:
        for suggestion in suggestions:
            print(suggestion)
```

Run `python examples/youtube_suggestions.py python --output artifacts/youtube_suggestions.json` from the checkout. Use `--help` for options. The command consumes credits.

## Parameters

`query` is required. Source options are keyword arguments, or entries in `params` when using `queries`. Data helpers default to realtime; pass `mode="async"` for background work. `timeout` controls the HTTP request.

| Option | Type / constraints | Default |
| --- | --- | --- |
| `language` | string; pattern `^[A-Za-z0-9-]+$` | "en" |
| `region` | string; pattern `^[A-Za-z]{2}$` | "US" |

## Use at scale

All sources support [background and batch queries](../jobs.md). Read [errors and recovery](../errors.md) before adding application retries.
