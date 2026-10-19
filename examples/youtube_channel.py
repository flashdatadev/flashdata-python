"""Inspect a channel and a bounded set of recent videos."""

from argparse import ArgumentParser
from flashdata import FlashData
from _support import add_output, report_usage, run, save_json


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("handle", nargs="?", default="@freecodecamp")
    parser.add_argument("--video-limit", type=int, default=5)
    add_output(parser)
    args = parser.parse_args(argv)
    with FlashData() as client:
        response = client.youtube.channel(args.handle, video_limit=args.video_limit)
    for channel in response["results"]:
        print(channel.get("name", ""), "| Subscribers:", channel.get("subscriberCount"))
        for video in channel.get("videos", []):
            print(video.get("title", ""), video.get("videoId", ""))
    report_usage(response)
    save_json(response, args.output)


if __name__ == "__main__":
    run(main)
