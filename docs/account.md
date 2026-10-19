# Account, pricing and service discovery

Read current access and plan limits before scaling a workload. These endpoints are free;
they still have rate limits. Account credit balances and plan ceilings are shared across
the account's API keys; usage reads are scoped to the key used for the request.

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    access = client.account.access()
    balance = client.account.balance()
    prices = client.account.pricing(source="youtube_metadata", request_count=100)
    limits = client.account.limits()
    usage = client.account.usage(source="youtube_metadata")
    print(access["sources"], balance["availableCredits"], limits["limits"])
    print(prices["prices"], usage["totals"])
```

`pricing` accepts an optional `source` and `request_count` (1–100000). Its estimate is for
that many calls, not that many search hits. Download costs depend on actual uploaded
bytes and cannot be estimated by multiplying request count. Prices and availability can
change; query them instead of hard-coding example values.

`usage` accepts `source`, `from_`, and `to`. Date filters are ISO 8601 strings; the server
validates the range and may report delayed totals while processing. `limits` includes
batch size, concurrency ceiling and pending jobs, rather than free execution slots.

Public discovery needs no key:

```python
from flashdata import FlashData

with FlashData(api_key="") as client:
    sources = client.public.sources()["data"]
    print([item["id"] for item in sources])
    print(client.public.health()["status"])
```

`public.plans()` returns public USD plan data. `public.status()` returns service components.
Public requests do not carry an API-key header, even when the client has a key.
Account and job reads always require one. See [API reference](api-reference.md).
