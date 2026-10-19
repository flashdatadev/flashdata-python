"""Submit a cloud media download, save its ID, and optionally wait for delivery."""

from argparse import ArgumentParser
import json
import os
from pathlib import Path
from flashdata import FlashData
from _support import add_output, run, save_json


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("video_id", nargs="?", default="dQw4w9WgXcQ")
    parser.add_argument(
        "--storage-file",
        type=Path,
        default=os.getenv("FLASHDATA_STORAGE_FILE"),
        help="Private JSON destination configuration (or FLASHDATA_STORAGE_FILE)",
    )
    parser.add_argument("--wait", action="store_true", help="Wait up to 600 seconds and read the delivery result")
    add_output(parser)
    args = parser.parse_args(argv)
    if not args.storage_file:
        parser.error("set --storage-file or FLASHDATA_STORAGE_FILE; see docs/storage.md")
    storage = json.loads(Path(args.storage_file).read_text(encoding="utf-8"))
    with FlashData() as client:
        receipt = client.youtube.download(args.video_id, storage=storage, video_quality="<=720", output_format="mp4")
        print("Save this job ID:", receipt["id"], flush=True)
        save_json(receipt, args.output)
        if args.wait:
            client.jobs.wait(receipt["id"], timeout=600, poll_interval=5)
            result = client.jobs.result(receipt["id"])
            save_json(result, args.output)
            print("Delivery completed. Inspect the result for destination object details.")


if __name__ == "__main__":
    run(main)
