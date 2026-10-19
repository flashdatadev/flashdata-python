"""Submit a background search or resume a saved job, then export its result."""

from argparse import ArgumentParser
import os
from flashdata import FlashData
from _bulk import check_wait_timeout
from _support import add_output, run, save_json


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="coffee")
    parser.add_argument("--job-id", help="Resume this ID without submitting a new query")
    parser.add_argument("--wait-timeout", type=float, default=300)
    add_output(parser)
    args = parser.parse_args(argv)
    check_wait_timeout(args.wait_timeout)
    with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
        job_id = args.job_id
        if not job_id:
            receipt = client.google.search(args.query, mode="async", num=3)
            job_id = receipt["id"]
            print("Save this job ID:", job_id, flush=True)
            save_json(receipt, args.output)
        client.jobs.wait(job_id, timeout=args.wait_timeout, poll_interval=3)
        response = client.jobs.result(job_id)
    for payload in response["results"]:
        for hit in payload.get("organic", []):
            print(hit.get("title", ""), hit.get("link", ""))
    save_json(response, args.output)


if __name__ == "__main__":
    run(main)
