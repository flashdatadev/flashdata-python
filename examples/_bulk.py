"""Shared bulk lifecycle: save the ID, upload/start once, then export result rows."""

import json
import math
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


def checkpoint(path, job):
    """Replace a reserved record only after its complete contents reach disk."""
    temporary = None
    try:
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as record:
            temporary = Path(record.name)
            json.dump(job, record, ensure_ascii=False, indent=2)
            record.write("\n")
            record.flush()
            os.fsync(record.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def check_wait_timeout(value):
    if not math.isfinite(value) or value <= 0:
        raise ValueError("--wait-timeout must be a finite positive number of seconds")
    return value


def bulk_task(client, args, request):
    timeout = check_wait_timeout(args.wait_timeout)
    job_path = Path(str(args.output) + ".job.json")
    bulk_id = args.bulk_id
    payload = None
    if not bulk_id:
        if not args.input or not args.input.is_file() or not 1 <= args.input.stat().st_size <= 2147483648:
            raise ValueError("Provide a regular ID file of 1 byte to 2 GiB, or --bulk-id")
        payload = request()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Reserve both paths before any API call. Empty records from uncertain
    # submissions remain a replay barrier; recovery always uses a fresh output.
    with args.output.open("x", encoding="utf-8") as output:
        with job_path.open("x", encoding="utf-8"):
            pass
        if not bulk_id:
            receipt = client.bulk.create(payload)
            bulk_id = receipt["job"]["id"]
            print("Save this bulk ID:", bulk_id, flush=True)
            checkpoint(job_path, receipt["job"])
            client.bulk.upload_file(receipt, args.input)
            client.bulk.start(bulk_id)
        else:
            checkpoint(job_path, {"id": bulk_id})
        completed = client.bulk.wait(bulk_id, timeout=timeout, poll_interval=3)
        checkpoint(job_path, completed)
        count = failed_rows = 0
        for row in client.bulk.rows(bulk_id):
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
            failed_rows += row.get("status") != "completed"
        output.flush()
        os.fsync(output.fileno())
    print(f"Saved {count} rows to {args.output}; counts: {completed['counts']}")
    if failed_rows or completed["counts"].get("failed") or completed["counts"].get("invalid"):
        raise ValueError("Bulk completed with failed or invalid items; inspect counts and exported rows")
