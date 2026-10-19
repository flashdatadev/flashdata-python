"""Read FlashData's public source catalogue, plans and service status without a key."""

from argparse import ArgumentParser

from flashdata import FlashData
from _support import add_output, run, save_json


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    add_output(parser)
    args = parser.parse_args(argv)
    with FlashData(api_key="") as client:
        result = {
            "sources": client.public.sources(),
            "health": client.public.health(),
            "status": client.public.status(),
            "plans": client.public.plans(),
        }
    print("Sources:", ", ".join(source["id"] for source in result["sources"]["data"]))
    print("Health:", result["health"]["status"])
    save_json(result, args.output)


if __name__ == "__main__":
    run(main)
