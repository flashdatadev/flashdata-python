"""Small CLI helpers shared by the examples; application code can use its own I/O."""

from argparse import ArgumentParser
import json
from pathlib import Path
import sys

from flashdata import APIError, FlashDataError


def add_output(parser: ArgumentParser) -> None:
    parser.add_argument("--output", type=Path, help="Also save the complete API response as UTF-8 JSON")


def save_json(value, path: Path | None) -> None:
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Saved {path}", file=sys.stderr)


def report_usage(response) -> None:
    print(f"Credits: {response.get('usage', {}).get('credits', 'not reported')}", file=sys.stderr)


def run(main) -> None:
    try:
        main()
    except APIError as error:
        print(f"API error {error.status_code} ({error.code or 'no code'}): {error}", file=sys.stderr)
        if error.request_id:
            print(f"Request ID: {error.request_id}", file=sys.stderr)
        raise SystemExit(1) from None
    except (FlashDataError, OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        print("Stopped locally. Accepted server jobs continue; resume using their saved IDs.", file=sys.stderr)
        raise SystemExit(130) from None
