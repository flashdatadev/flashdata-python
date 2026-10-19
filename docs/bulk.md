# Build a YouTube dataset with bulk jobs

Bulk jobs process a UTF-8 file containing one video ID per line. Supported sources:
`youtube_metadata`, `youtube_transcript`, `youtube_captions`, `youtube_trainability`,
and `youtube_download`. File uploads support 1 byte to 2 GiB. A bulk job uses one source
and one set of options for all IDs; use a [mixed batch](jobs.md) for different queries.

## Create, upload, start, export

Create a local `video-ids.txt` file containing, for example, `dQw4w9WgXcQ` on one line.
Then run:

```python
import json
from pathlib import Path
from flashdata import FlashData

with FlashData() as client:
    receipt = client.bulk.create({"source": "youtube_metadata",
                                  "options": {"include_formats": False}})
    bulk_id = receipt["job"]["id"]
    print("Save this ID:", bulk_id, flush=True)
    client.bulk.upload_file(receipt, Path("video-ids.txt"))
    client.bulk.start(bulk_id)
    client.bulk.wait(bulk_id, timeout=3600, poll_interval=5)
    with Path("dataset.ndjson").open("w", encoding="utf-8") as output:
        for row in client.bulk.rows(bulk_id):
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
```

Creation returns a job plus a short-lived signed PUT upload descriptor (15 minutes).
`upload_file` streams the input file with the required content type and length; it does
not start the job. If upload fails, keep the ID and inspect its state. Retry the same
upload only while its descriptor is valid. An expired input upload needs a new draft;
cancel the unused draft before creating its replacement. Re-creation is not automatic.
Do not log the upload descriptor or signed URLs.

Bulk options use `options`, rather than individual query `params`. Metadata accepts
`include_formats` and `include_chapters`; transcript/captions accept `language` and `auto`;
license checks have no data options. Data sources may also set `result_storage` for
cloud delivery. Downloads require `options.storage`. See [storage](storage.md).

## Progress and controls

`get(id)` returns a record with counts, status, pause reason and delivery status.
Typical states are `awaiting_upload`, `running`, `paused`, `finalizing`, `completed`,
`failed`, and `cancelled`. Counts include accepted, completed, failed, invalid, and results.
A completed bulk can contain failed rows; inspect counts and each row's status.

- `pause(id)` requests a pause for running work; already active items may finish.
- `resume(id)` resumes a paused job once its blocking condition is resolved.
- `update(id, {"options": ...})` updates settings allowed in its current state.
  Storage credentials can be patched without reconstructing the whole destination.
- `cancel(id)` cancels remaining work; completed work may already be charged.

`wait` stops with `JobPausedError` on a pause and `JobFailedError` on failure/cancellation.
It does not resume or cancel work automatically. Download billing uses actual delivered
bytes; data bulk jobs are billed per admitted item under your plan's current pricing.

## Read results and list jobs

`manifest(id)` retrieves counts, expiry, and ordered part descriptors. `part(id, number)`
returns bounded bytes; `iter_rows(id, number)` decodes a gzip/NDJSON part. `rows(id)` walks
manifest parts in order and yields their JSON objects. It uses constructed API routes,
not arbitrary URLs supplied in a manifest. Parts are zero based. Result files expire
24 hours after completion; export them promptly.

`list(cursor=..., limit=20)` returns `data` and `pagination`. `iter_jobs(max_pages=..., limit=...)`
walks a bounded number of cursor pages. Both have async equivalents; use `async for`
for async job and row iterators.

The runnable [bulk example](examples.md) supports submitting and resuming an
existing ID, so a process restart does not require re-uploading or re-submitting work.
