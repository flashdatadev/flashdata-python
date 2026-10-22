"""Download a video ID file into cloud storage, or resume an already started task."""

from argparse import ArgumentParser
import json
import os
from pathlib import Path

from flashdata import FlashData
from _bulk import bulk_task, check_wait_timeout
from _support import run


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, help="UTF-8 file with one video ID per line")
    parser.add_argument("--bulk-id", help="Read an existing task without uploading or resubmitting")
    parser.add_argument("--storage-file", type=Path, help="Private cloud destination JSON file")
    parser.add_argument("--audio", action="store_true", help="Deliver MP3 audio instead of an MP4 video")
    parser.add_argument("--output", type=Path, default=Path("artifacts/downloads.ndjson"))
    parser.add_argument("--wait-timeout", type=float, default=3600)
    args = parser.parse_args(argv)
    check_wait_timeout(args.wait_timeout)

    def request():
        storage_file = args.storage_file or Path(os.getenv("FLASHDATA_STORAGE_FILE", "private-storage.json"))
        storage = json.loads(storage_file.read_text(encoding="utf-8"))
        options = (
            {"download_type": "audio", "output_format": "mp3"}
            if args.audio
            else {
                "download_type": "audio_video",
                "video_quality": "<=720",
                "output_format": "mp4",
            }
        )
        return {"source": "youtube_download", "options": {**options, "storage": storage}}

    with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
        bulk_task(client, args, request)


if __name__ == "__main__":
    run(main)
