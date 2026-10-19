"""Shared bulk lifecycle: save the ID, upload/start once, then export result rows."""

import json
import math
from pathlib import Path

from _support import save_json


def check_wait_timeout(value):
    if not math.isfinite(value) or value <= 0:
        raise ValueError("--wait-timeout must be a finite positive number of seconds")
    return value


def bulk_task(client, args, request):
    timeout = check_wait_timeout(args.wait_timeout)
    job_path = Path(str(args.output) + ".job.json")
    bulk_id = args.bulk_id
    if not bulk_id:
        if not args.input or not args.input.is_file() or not 1 <= args.input.stat().st_size <= 2147483648:
            raise ValueError("Provide a regular ID file of 1 byte to 2 GiB, or --bulk-id")
        receipt = client.bulk.create(request())
        bulk_id = receipt["job"]["id"]
        print("Save this bulk ID:", bulk_id, flush=True)
        save_json(receipt["job"], job_path)
        client.bulk.upload_file(receipt, args.input)
        client.bulk.start(bulk_id)
    completed = client.bulk.wait(bulk_id, timeout=timeout, poll_interval=3)
    save_json(completed, job_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.output.open("w", encoding="utf-8") as output:
        for row in client.bulk.rows(bulk_id):
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    print(f"Saved {count} rows to {args.output}; counts: {completed['counts']}")
    if completed["counts"].get("failed") or completed["counts"].get("invalid"):
        raise ValueError("Bulk completed with failed or invalid items; inspect counts and exported rows")
