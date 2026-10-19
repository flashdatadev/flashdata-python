"""A complete first search using a fake HTTP transport. No key or network needed."""

from argparse import ArgumentParser
import httpx
from flashdata import FlashData


def main(argv=None):
    ArgumentParser(description=__doc__).parse_args(argv)

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

    with FlashData(api_key="offline-demo-key", transport=httpx.MockTransport(respond)) as client:
        response = client.google.search("FlashData SDK", num=1)
        for hit in response["results"][0]["organic"]:
            print(hit["title"], hit["link"])


if __name__ == "__main__":
    main()
