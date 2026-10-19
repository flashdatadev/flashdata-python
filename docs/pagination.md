# Google pagination

Use `google.pages` to process a bounded number of realtime pages. It yields response
dictionaries lazily, stops on an empty hit list, and makes no request for pages you do
not consume. Every fetched page is a separate paid query, including the empty final page.

```python
from flashdata import FlashData

with FlashData() as client:
    for response in client.google.pages("google_search", "coffee", max_pages=2, num=5):
        for payload in response["results"]:
            for hit in payload.get("organic", []):
                print(hit.get("position"), hit["title"], hit["link"])
```

`source` is one of the six Google source names. `max_pages` is required (1–100).
`start_page` defaults to 1; the final page must be at most 100. Pass localization and
other source options as keyword arguments. Use `start_page` rather than `page` on the
iterator. For one page, call the source method with `page=2`.

In async code use `async for response in client.google.pages(...)`. Close an abandoned
async iterator with `await iterator.aclose()` if its lifetime extends beyond the loop.

The [CSV recipe](recipes.md) deduplicates links across pages and writes rank/title/link/snippet
columns. Returned positions are the upstream fields; the SDK does not infer global ranks.
YouTube search uses `max_results`, not Google's `page` parameter. Extended search can
request up to 700 entities in one request, subject to availability.
