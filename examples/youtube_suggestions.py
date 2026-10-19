"""Expand a partial query into YouTube autocomplete suggestions."""

from argparse import ArgumentParser
from flashdata import FlashData
from _support import add_output, report_usage, run, save_json


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="python")
    parser.add_argument("--language", default="en")
    parser.add_argument("--region", default="US")
    add_output(parser)
    args = parser.parse_args(argv)
    with FlashData() as client:
        response = client.youtube.suggestions(args.query, language=args.language, region=args.region)
    for suggestions in response["results"]:
        for suggestion in suggestions:
            print(suggestion)
    report_usage(response)
    save_json(response, args.output)


if __name__ == "__main__":
    run(main)
