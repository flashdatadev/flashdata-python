"""Read free account access, pricing, balance, limits, and key-scoped usage."""

from argparse import ArgumentParser
from flashdata import FlashData
from _support import add_output, run, save_json


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    add_output(parser)
    args = parser.parse_args(argv)
    with FlashData() as client:
        result = {
            "access": client.account.access(),
            "balance": client.account.balance(),
            "pricing": client.account.pricing(),
            "limits": client.account.limits(),
            "usage": client.account.usage(),
        }
    print("Available sources:", ", ".join(result["access"]["sources"]))
    print("Available credits:", result["balance"]["availableCredits"])
    print("Plan limits:", result["limits"]["limits"])
    print("Usage totals:", result["usage"]["totals"])
    save_json(result, args.output)


if __name__ == "__main__":
    run(main)
