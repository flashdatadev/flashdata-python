"""Create a metadata bulk job or resume its ID, then export bounded result parts."""

from argparse import ArgumentParser
import os
import json
from pathlib import Path
from flashdata import FlashData
from _support import run


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, help="UTF-8 file with one video ID per line")
    parser.add_argument("--bulk-id", help="Resume reading this existing job without creating another")
    parser.add_argument("--output", type=Path, default=Path("artifacts/dataset.ndjson"))
    parser.add_argument("--wait-timeout", type=float, default=3600)
    args = parser.parse_args(argv)
    if not args.bulk_id and (not args.input or not args.input.is_file()):
        parser.error("provide an ID file or --bulk-id")
    with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
        bulk_id = args.bulk_id
        if not bulk_id:
            receipt = client.bulk.create({"source": "youtube_metadata", "options": {"include_formats": False}})
            bulk_id = receipt["job"]["id"]
            print("Save this bulk ID:", bulk_id, flush=True)
            client.bulk.upload_file(receipt, args.input)
            client.bulk.start(bulk_id)
        completed = client.bulk.wait(bulk_id, timeout=args.wait_timeout, poll_interval=3)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with args.output.open("w", encoding="utf-8") as output:
            for row in client.bulk.rows(bulk_id):
                output.write(json.dumps(row, ensure_ascii=False) + "\n")
                count += 1
        print(f"Saved {count} rows to {args.output}; counts: {completed['counts']}")
        if completed["counts"].get("failed") or completed["counts"].get("invalid"):
            raise ValueError("Bulk completed with failed or invalid items; inspect counts and exported rows")


if __name__ == "__main__":
    run(main)
