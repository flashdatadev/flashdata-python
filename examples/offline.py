"""A complete first search using a fake HTTP transport. No key or network needed."""

import httpx
from flashdata import FlashData


def respond(request):
    return httpx.Response(
        200,
        json={
            "source": "google_search",
            "status": "done",
            "usage": {"credits": 0},
            "results": [{"organic": [{"title": "FlashData docs", "link": "https://flashdata.dev/docs"}]}],
        },
    )


with FlashData("offline-demo-key", transport=httpx.MockTransport(respond)) as client:
    result = client.google.search("FlashData SDK", num=1)
    print(result["results"][0]["organic"][0]["link"])
