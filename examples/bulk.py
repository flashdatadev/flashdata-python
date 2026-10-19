"""Create a metadata bulk job or resume its ID, then export bounded result parts."""

from argparse import ArgumentParser
import os
from pathlib import Path
from flashdata import FlashData
from _bulk import bulk_task, check_wait_timeout
from _support import run


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, help="UTF-8 file with one video ID per line")
    parser.add_argument("--bulk-id", help="Resume reading this existing job without creating another")
    parser.add_argument("--output", type=Path, default=Path("artifacts/dataset.ndjson"))
    parser.add_argument("--wait-timeout", type=float, default=3600)
    args = parser.parse_args(argv)
    check_wait_timeout(args.wait_timeout)
    with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
        bulk_task(client, args, lambda: {"source": "youtube_metadata", "options": {"include_formats": False}})


if __name__ == "__main__":
    run(main)
