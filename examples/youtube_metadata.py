"""Enrich a video ID with title, duration, channel, and available caption languages."""

from argparse import ArgumentParser
from flashdata import FlashData
from _support import add_output, report_usage, run, save_json


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("video_id", nargs="?", default="dQw4w9WgXcQ")
    parser.add_argument("--include-formats", action="store_true")
    parser.add_argument("--include-chapters", action="store_true")
    add_output(parser)
    args = parser.parse_args(argv)
    with FlashData() as client:
        response = client.youtube.metadata(
            args.video_id, include_formats=args.include_formats, include_chapters=args.include_chapters
        )
    for video in response["results"]:
        print(video.get("title", ""))
        print("Channel:", video.get("channel", ""))
        print("Duration (seconds):", video.get("duration"))
        print("Caption languages:", ", ".join(video.get("transcriptLanguages", [])))
    report_usage(response)
    save_json(response, args.output)


if __name__ == "__main__":
    run(main)
