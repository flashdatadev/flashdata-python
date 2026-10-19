# Pagination

Every Google result page is a separate paid query. The helper requires an explicit
maximum page count, uses sequential requests, and stops after an empty result list.
The first page counts toward that maximum. It adds only the requested page parameter.

```python
from flashdata import FlashData
with FlashData() as client:
    for response in client.google.pages("google_search", "coffee", max_pages=3, gl="us"):
        print(response["results"])
```

Use `async for` with `AsyncFlashData`. `start_page` defaults to 1. A partial iteration
only submits pages actually requested by the consumer.

Supported sources: all six Google sources. Pages are bounded to the API's range 1–100.
YouTube search uses `max_results` rather than an invented continuation token. Standard
YouTube search requests up to 20 results; Extended Search up to 700, at a separate rate.
Neither guarantees that many results.

Bulk collection listing uses free cursor pagination. Pass the returned `pagination.nextCursor`
to the next `bulk.list` call only when `hasMore` is true. Stop on a missing/repeated cursor.
This is independent of paid Google result pagination.
