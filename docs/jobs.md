# Background jobs and batch submission

## Submit, save, wait, retrieve

```python
from flashdata import FlashData

with FlashData() as client:
    receipt = client.youtube.metadata("dQw4w9WgXcQ", mode="async", include_formats=False)
    job_id = receipt["id"]
    print(job_id, flush=True)
    completed = client.jobs.wait(job_id, timeout=300, poll_interval=2)
    result = client.jobs.result(job_id)
    print(completed["status"], result)
```

Submissions return an ID and status such as `pending`. Jobs progress through `pending`,
`processing`, `completed` or `failed`. `jobs.get()` returns the job record, unwrapping the
HTTP response's `job` property. `wait()` returns that record on completion or raises
`JobFailedError` with `.job` on failure. A polling timeout retains `.job_id` and leaves
the server job running. Resume reads with the same ID instead of resubmitting.

`jobs.result()` retrieves a JSON object with `id`, `source`, `status`, `results`, `usage`,
`completed_at`, and `expires_at`. Decode the source payloads in `results` using the same
field paths as realtime queries.
The helper checks the signed-storage origin advertised by authenticated API discovery
and never forwards API credentials to storage. Read completed results within the
service's 24-hour retention window. 409 means not ready; 410 means expired.

## Submit a mixed batch

```python
from flashdata import FlashData

with FlashData() as client:
    batch = client.queries.batch([
        {"source": "google_search", "query": "coffee", "params": {"num": 3}},
        {"source": "youtube_metadata", "video_id": "dQw4w9WgXcQ",
         "params": {"include_formats": False}},
    ])
    for item in batch["queries"]:
        print(item["source"], item["id"], flush=True)
```

Input validation happens before submission. The server validates batch inputs and checks
plan limits; malformed batches can fail as a whole. A successful response contains a job
receipt for each input. Each job can subsequently complete or fail independently, so save
all IDs and check their final states. `total_credits` and `usage.credits` describe submission
charges; a background receipt is not proof of completion.
Use `account.limits()` to find the current plan's `batchSize`.

`queries.realtime()` and `queries.submit()` accept the same wire dictionaries as each
source helper: `source` and its main input at the top level, source options in `params`,
and `callback_url` at the top level. They are useful for dynamically configured pipelines.

## Callbacks

Supply `callback_url="https://your.example/jobs/callback"` on a background helper or
in a submitted query dictionary. The endpoint must be public HTTPS on port 443. Callback
delivery can be repeated or fail; use its delivery/job identifiers to deduplicate, and
read the job API for authoritative state. A callback does not replace saving the job ID.
Realtime requests do not support callbacks. The SDK does not run a webhook server.

The API-key API has no standard job listing or cancellation method. Persist IDs with
your own request metadata. If a mutation loses its response, see [unknown submissions](errors.md).
