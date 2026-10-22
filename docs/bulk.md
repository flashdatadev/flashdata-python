# Build a YouTube dataset with bulk jobs

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

Bulk jobs process a UTF-8 file containing one video ID per line. Supported sources:
`youtube_metadata`, `youtube_transcript`, `youtube_captions`, `youtube_trainability`,
and `youtube_download`. File uploads support 1 byte to 2 GiB. A bulk job uses one source
and one set of options for all IDs; use a [mixed batch](jobs.md) for different queries.

## Create, upload, start, export

Create a local `video-ids.txt` file containing, for example, `dQw4w9WgXcQ` on one line.
Then run:

```python
import json
import os
from pathlib import Path
from flashdata import FlashData

with (
    FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client,
    Path("videos.ndjson").open("x", encoding="utf-8") as output,
    Path("videos.ndjson.job.json").open("x", encoding="utf-8") as record,
):
    receipt = client.bulk.create({
        "source": "youtube_metadata",
        "options": {"include_formats": False},
    })
    bulk_id = receipt["job"]["id"]
    print("Save this bulk ID:", bulk_id, flush=True)
    json.dump({"id": bulk_id}, record)
    record.flush()
    os.fsync(record.fileno())
    client.bulk.upload_file(receipt, Path("video-ids.txt"))
    client.bulk.start(bulk_id)
    completed = client.bulk.wait(bulk_id, timeout=3600, poll_interval=5)

    for row in client.bulk.rows(bulk_id):
        output.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("Saved videos.ndjson; counts:", completed["counts"])
    if completed["counts"].get("failed") or completed["counts"].get("invalid"):
        raise RuntimeError("Some items failed; inspect the saved rows before retrying")
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

## Download media into your storage

Use `source="youtube_download"` and put the private destination in `options.storage`.
Prepare `video-ids.txt` and a private destination JSON file as described in
[storage configuration](storage.md), then run the complete task:

```python
import json
import os
from pathlib import Path
from flashdata import FlashData

storage = json.loads(Path("private-storage.json").read_text(encoding="utf-8"))

with (
    FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client,
    Path("downloads.ndjson").open("x", encoding="utf-8") as output,
    Path("downloads.ndjson.job.json").open("x", encoding="utf-8") as record,
):
    receipt = client.bulk.create({
        "source": "youtube_download",
        "options": {
            "download_type": "audio_video",
            "video_quality": "<=720",
            "output_format": "mp4",
            "storage": storage,
        },
    })
    bulk_id = receipt["job"]["id"]
    print("Save this bulk ID:", bulk_id, flush=True)
    json.dump({"id": bulk_id}, record)
    record.flush()
    os.fsync(record.fileno())
    client.bulk.upload_file(receipt, Path("video-ids.txt"))
    client.bulk.start(bulk_id)

    completed = client.bulk.wait(bulk_id, timeout=3600, poll_interval=5)
    print("Counts:", completed["counts"])
    for row in client.bulk.rows(bulk_id):
        output.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(row["video_id"], row["status"])
    if completed["counts"].get("failed") or completed["counts"].get("invalid"):
        raise RuntimeError("Some items failed; inspect downloads.ndjson before retrying")
```

For a runnable export:

```sh
python examples/bulk_download.py video-ids.txt --storage-file private-storage.json --output artifacts/downloads.ndjson
python examples/bulk_download.py --bulk-id bulk_YOUR_SAVED_ID --output artifacts/downloads-recovered.ndjson
```

Both bulk CLIs save only the job record to `OUTPUT.job.json` before upload and refresh
it on completion. They never save the signed upload descriptor. Result rows are exported
before an item-failure exit status, preserving successful and failed records for recovery.
The media goes to your bucket; the NDJSON describes delivery, rather than containing media.

A resume command waits for a task that has already started. An `awaiting_upload` draft
still needs its input uploaded and `start` called. A paused task requires resolving the
blocking condition and calling `resume` before waiting again.

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

## Safe local exports

The bulk scripts reserve new output and `OUTPUT.job.json` files before any API call,
refuse existing files, and sync accepted IDs before upload. Completion records are
replaced atomically. A lost start response leaves its accepted ID available; recovery
uses that ID and a fresh output path without another creation or upload. Empty reserved
records after an uncertain create require account/server reconciliation.

Use `bulk_download.py` with `--audio` for MP3; the default is MP4.
Compare [all SDKs and the CLI](sdk-parity.md) for coverage and persistence differences.
