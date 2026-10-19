"""Export deduplicated Google web results to CSV, with an explicit page budget."""

from argparse import ArgumentParser
import os
import csv
from pathlib import Path
from flashdata import FlashData
from _support import run


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="coffee")
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--num", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path("artifacts/search.csv"))
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    credits = 0
    with (
        FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client,
        args.output.open("w", encoding="utf-8", newline="") as output,
    ):
        writer = csv.DictWriter(output, fieldnames=["page", "position", "title", "link", "snippet"])
        writer.writeheader()
        for page, response in enumerate(
            client.google.pages("google_search", args.query, max_pages=args.max_pages, num=args.num), start=1
        ):
            credits += response.get("usage", {}).get("credits", 0)
            for payload in response["results"]:
                for hit in payload.get("organic", []):
                    link = hit.get("link")
                    if link and link not in seen:
                        seen.add(link)
                        writer.writerow(
                            {"page": page, **{k: hit.get(k, "") for k in ["position", "title", "link", "snippet"]}}
                        )
    print(f"Saved {len(seen)} unique links to {args.output}; credits: {credits}")


if __name__ == "__main__":
    run(main)
