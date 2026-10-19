"""Submit a mixed two-query batch; optionally wait and export every result."""

from argparse import ArgumentParser
from flashdata import FlashData
from _support import add_output, run, save_json


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="coffee")
    parser.add_argument("--video-id", default="dQw4w9WgXcQ")
    parser.add_argument("--wait", action="store_true")
    add_output(parser)
    args = parser.parse_args(argv)
    with FlashData() as client:
        batch = client.queries.batch(
            [
                {"source": "google_search", "query": args.query, "params": {"num": 3}},
                {"source": "youtube_metadata", "video_id": args.video_id, "params": {"include_formats": False}},
            ]
        )
        save_json(batch, args.output)
        results = []
        errors = []
        for item in batch["queries"]:
            if not item.get("id"):
                errors.append(item)
                print("Unexpected receipt without a job ID:", item.get("source"), flush=True)
                continue
            print("Save this job ID:", item["source"], item["id"], flush=True)
        if errors:
            raise ValueError("Unexpected batch receipt; inspect the saved response before submitting anything again")
        if args.wait:
            for item in batch["queries"]:
                client.jobs.wait(item["id"], timeout=300, poll_interval=3)
                results.append(client.jobs.result(item["id"]))
            save_json({"submission": batch, "results": results}, args.output)
            print(f"Completed {len(results)} jobs")


if __name__ == "__main__":
    run(main)
