"""Search several queries with bounded asyncio concurrency and one reusable client."""

from argparse import ArgumentParser
import os
import asyncio
from flashdata import AsyncFlashData
from _support import add_output, run, save_json


async def search_all(queries, concurrency):
    gate = asyncio.Semaphore(concurrency)
    async with AsyncFlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:

        async def search(query):
            async with gate:
                return {"query": query, "response": await client.google.search(query, num=3)}

        return await asyncio.gather(*(search(q) for q in queries))


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("queries", nargs="*", default=["coffee", "tea"])
    parser.add_argument("--concurrency", type=int, default=2)
    add_output(parser)
    args = parser.parse_args(argv)
    if not 1 <= args.concurrency <= 50:
        parser.error("--concurrency must be between 1 and 50; account limits still apply")
    results = asyncio.run(search_all(args.queries, args.concurrency))
    for result in results:
        print(result["query"])
        for payload in result["response"]["results"]:
            for hit in payload.get("organic", []):
                print(" ", hit.get("title", ""), hit.get("link", ""))
    save_json(results, args.output)


if __name__ == "__main__":
    run(main)
