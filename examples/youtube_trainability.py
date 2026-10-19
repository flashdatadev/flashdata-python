"""Read detected license labels; this is not a grant of reuse or training rights."""

from argparse import ArgumentParser
import os
from flashdata import FlashData
from _support import add_output, report_usage, run, save_json


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("video_id", nargs="?", default="dQw4w9WgXcQ")
    add_output(parser)
    args = parser.parse_args(argv)
    with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
        response = client.youtube.license_check(args.video_id)
    for video in response["results"]:
        print(video["videoId"], "Detected labels:", ", ".join(video.get("permitted", [])))
    report_usage(response)
    save_json(response, args.output)


if __name__ == "__main__":
    run(main)
