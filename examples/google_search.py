"""Find web pages and print titles and source links."""

from argparse import ArgumentParser
from flashdata import FlashData
from _support import add_output, report_usage, run, save_json


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="coffee roasters")
    parser.add_argument("--num", type=int, default=5, help="Results requested per page (1–100)")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--gl", default="us", help="Country code")
    parser.add_argument("--hl", default="en", help="Interface language")
    add_output(parser)
    args = parser.parse_args(argv)
    with FlashData() as client:
        response = client.google.search(args.query, num=args.num, page=args.page, gl=args.gl, hl=args.hl)
    for payload in response["results"]:
        for hit in payload.get("organic", []):
            print(f"{hit.get('position', '?')}. {hit.get('title', '')}")
            print(f"   {hit.get('link', '')}")
            print(f"   {hit.get('snippet', '')}")
    report_usage(response)
    save_json(response, args.output)


if __name__ == "__main__":
    run(main)
