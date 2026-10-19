# Client configuration and asyncio

## API keys

Pass your key explicitly when constructing either client:

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    print(client.account.access()["sources"])
```

Here, `os.getenv` is application code that reads an environment variable and passes its
value as `api_key`. You can also pass a string obtained from your secret manager.
As a convenience, omitting `api_key` or passing `None` makes the SDK look up
`FLASHDATA_API_KEY` itself. An explicit string takes precedence over that lookup.

The SDK does not load `.env` files. If your application uses one, load it before calling
`os.getenv`, for example with your application's existing configuration loader.
Public discovery needs no key; authenticated methods reject a missing key before I/O.

## Reuse and close clients

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY"), timeout=120, max_response_bytes=64 * 1024 * 1024) as client:
    first = client.google.search("coffee", timeout=30)
    second = client.google.news("coffee", timeout=60)
```

`timeout` is a positive number of seconds applied to HTTPX's connect/read/write/pool
operations. It is not a wall-clock cap for the entire paid job. Each request method can
override it. `jobs.wait(timeout=...)` and `bulk.wait(timeout=...)` instead bound polling;
they do not cancel server work. Results and upload helpers also accept request timeouts.

The default maximum response size is 64 MiB after HTTP content decoding. Bulk NDJSON
decoding applies the same total limit and a configurable `max_line_bytes` limit (16 MiB
by default). Increase these bounds deliberately for larger metadata or transcript parts.
Part iterators buffer one bounded part; they do not stream a whole dataset into memory.

Use `client.close()` if you cannot use `with`. Async clients use `await client.aclose()`.
A sync client can be reused between threads; do not close it while requests are in flight.
Create an async client inside the event loop that will use it, and do not share it across
event loops. Canceling a coroutine does not cancel an accepted server job.

## Async requests

```python
import os
import asyncio
from flashdata import AsyncFlashData

async def main():
    async with AsyncFlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
        gate = asyncio.Semaphore(3)

        async def search(query):
            async with gate:
                return await client.google.search(query, num=5)

        responses = await asyncio.gather(*(search(q) for q in ["coffee", "tea"]))
        print([r["usage"]["credits"] for r in responses])

asyncio.run(main())
```

Set concurrency from your plan and workload. Account limits are shared by all keys and
do not report currently available worker slots. Avoid unbounded task creation.

## Proxies, TLS and environments

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY"), proxy="http://localhost:8080", trust_env=False) as client:
    print(client.public.health())
```

`proxy` configures the HTTP proxy for API and signed-storage requests. `trust_env=True`
(default) honors HTTPX proxy and certificate environment settings. `verify` accepts a
boolean or `ssl.SSLContext`; use a trusted CA context for private corporate certificates.
Do not place proxy credentials in logs. API and storage use separate cookie/connection pools.
The authenticated result-storage origin is cached for the client's lifetime to avoid an
extra discovery call for every result part. Create a new client if that origin changes.

For local testing, `data_url` and `management_url` accept HTTPS origins, or HTTP on
loopback only. They must not include a path such as `/v2`. Pass `httpx.MockTransport`
through `transport`, or use `storage_transport` to isolate storage fixtures. See the
credential-free `examples/offline.py` example.

There are no automatic retries or implicit billable defaults. Source parameters that
are omitted use the service's current defaults. Both clients validate inputs before I/O.
