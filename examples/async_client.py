"""Search several queries with bounded asyncio concurrency and one reusable client."""

from argparse import ArgumentParser
import os
import asyncio
from flashdata import AsyncFlashData
from _support import add_output, run, save_json


async def search_all(queries, concurrency):
    results = [None] * len(queries)
    pending = iter(enumerate(queries))
    async with AsyncFlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:

        async def worker():
            for index, query in pending:
                try:
                    results[index] = {"query": query, "response": await client.google.search(query, num=3)}
                except Exception as error:
                    results[index] = {
                        "query": query,
                        "error": {
                            "name": type(error).__name__,
                            "message": str(error),
                            "status_code": getattr(error, "status_code", None),
                            "code": getattr(error, "code", None),
                            "request_id": getattr(error, "request_id", None),
                            "retry_after": getattr(error, "retry_after", None),
                        },
                    }

        await asyncio.gather(*(worker() for _ in range(min(concurrency, len(queries)))))
    return results


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
        if "error" in result:
            print(" ", result["error"]["message"])
        else:
            for payload in result["response"]["results"]:
                for hit in payload.get("organic", []):
                    print(" ", hit.get("title", ""), hit.get("link", ""))
    save_json(results, args.output)
    if any("error" in result for result in results):
        raise ValueError("Some searches failed; inspect individual results before deciding what to submit again")


if __name__ == "__main__":
    run(main)
