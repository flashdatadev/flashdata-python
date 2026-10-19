"""Discover YouTube videos and print titles, channels, and watch links."""

from argparse import ArgumentParser
import os
from flashdata import FlashData
from _support import add_output, report_usage, run, save_json


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="python tutorial")
    parser.add_argument("--max-results", type=int, default=5, help="Maximum entities (1–700)")
    parser.add_argument("--short", action="store_true", help="Filter videos shorter than four minutes")
    add_output(parser)
    args = parser.parse_args(argv)
    filters = {"type": "video"}
    if args.short:
        filters["duration"] = "<4"
    with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
        response = client.youtube.search_extended(args.query, max_results=args.max_results, filters=filters)
    for payload in response["results"]:
        for video in payload.get("results", []):
            print(f"{video.get('title', '')} | {video.get('channel', '')} | {video.get('durationString', '')}")
            if video.get("videoId"):
                print("https://www.youtube.com/watch?v=" + video["videoId"])
    report_usage(response)
    save_json(response, args.output)


if __name__ == "__main__":
    run(main)
