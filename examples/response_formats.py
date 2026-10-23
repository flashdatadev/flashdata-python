"""Retrieve Google search or a YouTube transcript as JSON, plain text, or Markdown."""

from argparse import ArgumentParser
import json
import os
from pathlib import Path

from flashdata import FlashData
from _support import run


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=["google_search", "youtube_transcript"])
    parser.add_argument("input", help="Search query or YouTube video ID")
    parser.add_argument("--accept", choices=["application/json", "text/plain"], default="application/json")
    parser.add_argument("--respond-with", choices=["markdown"])
    parser.add_argument("--output", type=Path, help="Also save the response as UTF-8 text or JSON")
    args = parser.parse_args(argv)
    with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
        method = client.google.search if args.source == "google_search" else client.youtube.transcript
        result = method(args.input, accept=args.accept, respond_with=args.respond_with)
    text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="" if text.endswith("\n") else "\n")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    run(main)
