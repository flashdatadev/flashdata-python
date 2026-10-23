# FlashData Python SDK

[English](https://github.com/flashdatadev/flashdata-python/blob/main/README.md) | [简体中文](https://github.com/flashdatadev/flashdata-python/blob/main/README.zh-CN.md)

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

Google search results and YouTube data for Python applications, research pipelines,
search monitoring, and retrieval workflows.

Get web, news, shopping, image, video, and local search results; discover YouTube videos,
read metadata and existing caption tracks; submit background jobs; and process video ID
files in bulk. The SDK includes synchronous and asynchronous clients, typed parameters,
local input validation, and structured errors. Python 3.10 or newer is required.

## What is FlashData?

[FlashData](https://flashdata.dev) provides APIs for Google search results, YouTube data,
and cloud media delivery. Developers and data teams use these APIs for search monitoring,
research, analytics, content discovery, and retrieval workflows for AI applications.

Retrieve web, news, shopping, image, video, and local search results; discover YouTube
videos and read metadata, existing caption tracks, channel data, and license labels.
Use realtime requests, background jobs, mixed batches, or bulk video ID files to fit your
workload. Media downloads deliver audio or video into your own cloud storage.
See the [API documentation](https://flashdata.dev/docs) and [pricing](https://flashdata.dev/pricing).

## Choose a workflow

| What you want to build | Start here |
| --- | --- |
| Web context and source links for an AI assistant | [Google search](#search-google) |
| Industry research or news monitoring | [News search](#follow-industry-news) |
| Video discovery for a topic or learning resource | [YouTube search](#find-youtube-videos-about-a-topic) |
| Video analytics and catalog enrichment | [Video metadata](#get-a-videos-metadata) |
| Text for video summaries, search or retrieval | [Existing transcripts](#get-transcript-text-for-an-ai-workflow) |
| A dataset from a list of video IDs | [Bulk metadata export](#build-a-youtube-metadata-dataset) |
| Audio or video files delivered to your own cloud bucket | [Bulk media download](#download-youtube-videos-in-bulk) |
| Continue an interrupted bulk job | [Recovery](#recover-an-already-started-bulk-job) |

The examples collect data; your application provides summarization, indexing, scheduling
and AI model calls.

## Install

```sh
pip install flashdata
```

This command requires FlashData's official PyPI publication. For local testing before
release, use [installation from source](#install-from-source).

## Configure your API key

Obtain an API key from your [FlashData account](https://flashdata.dev) and pass it through
the client's `api_key` argument. The examples below use `os.getenv("FLASHDATA_API_KEY")`
to read the key from your environment. You can also pass a key supplied by your secret manager.

The SDK does not automatically load `.env` files. Load application configuration before
calling `os.getenv` if you use them.

```sh
# macOS / Linux
export FLASHDATA_API_KEY="YOUR_API_KEY"
```

```powershell
# PowerShell
$env:FLASHDATA_API_KEY = "YOUR_API_KEY"
```

Each code block below is a standalone example. After installing and setting your API key,
save a block as `quickstart.py` and run:

```sh
python quickstart.py
```

## Search Google

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.google.search("coffee roasters", gl="us", hl="en", num=5)
    for page in response["results"]:
        for hit in page.get("organic", []):
            print(hit["title"], hit["link"])
```

By default, responses are ordinary dictionaries. `response["results"]` contains source payloads:
Google web hits are in each payload's `organic` list. Other sources have their own
fields. Credits charged for the request are in `response["usage"]["credits"]`.

## Choose a response format

JSON dictionaries remain the default. Set `accept="text/plain"` to get a string,
or `respond_with="markdown"` to get Markdown content. Both clients support these options.

| `accept` | `respond_with` | Result |
| --- | --- | --- |
| `"application/json"` (default) | Omitted | Dictionary with original `results` |
| `"text/plain"` | Omitted | Original fields as text |
| `"application/json"` (default) | `"markdown"` | Dictionary with Markdown in `content` |
| `"text/plain"` | `"markdown"` | Metadata followed by Markdown |

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.google.search("vector databases", respond_with="markdown")
    print(response["content"])
    text = client.youtube.transcript(
        "dQw4w9WgXcQ", accept="text/plain", respond_with="markdown"
    )
    print(text)
```

`accept` also works on background submissions, batches and `jobs.get()`.
Choose Markdown for completed jobs with `jobs.result(job_id, respond_with="markdown")`.
Formatting a completed result does not run another query or charge query credits.
See [response formats](docs/response-formats.md) for examples and supported methods.

## Follow industry news

Collect headlines, publishers and article links for a research tool or monitoring script.

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.google.news("battery recycling", gl="us", hl="en", num=5)
    for payload in response["results"]:
        for article in payload.get("news", []):
            print(article.get("title"), article.get("source"), article.get("link"))
```

## Find YouTube videos about a topic

Discover relevant videos and get IDs you can pass to metadata or transcript requests.

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.youtube.search("python tutorial", max_results=5)
    for payload in response["results"]:
        for video in payload.get("results", []):
            print(video.get("videoId"), video.get("title"), video.get("channel"))
```

## Get a video's metadata

Enrich a video catalog with titles, channels, duration and view counts. Replace the example
ID with a video you want to analyze.

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.youtube.metadata("dQw4w9WgXcQ", include_formats=False)
    for video in response["results"]:
        print(video.get("title"), video.get("channel"))
        print("Seconds:", video.get("duration"), "Views:", video.get("viewCount"))
```

## Get transcript text for an AI workflow

Read an existing English automatic caption track for your application to summarize or index.
The API returns text; your application performs the summarization or embedding.

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.youtube.transcript("dQw4w9WgXcQ", language="en", auto=True)
    for track in response["results"]:
        print(track.get("fullText", ""))
```

Transcripts depend on the language tracks available on the video; missing tracks are not
transcribed or translated. For uploaded captions, use the `captions` example below.

## Read a YouTube caption track

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.youtube.captions("dQw4w9WgXcQ", language="en", auto=False)
    for track in response["results"]:
        print(track["languageCode"], track["isAutoGenerated"])
        for segment in track.get("segments", [])[:3]:
            print(segment["start"], segment["text"])
```

Captions default to an uploaded track (`auto=False`); transcripts default to an automatic
track (`auto=True`). Choose a language and track that exist on the video. Missing tracks
return an API error; the service does not generate or translate them.

## Use asyncio

```python
import os
import asyncio
from flashdata import AsyncFlashData

async def main():
    async with AsyncFlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
        response = await client.youtube.search("python tutorial", max_results=5)
        for payload in response["results"]:
            for video in payload.get("results", []):
                print(video["title"], video["videoId"])

asyncio.run(main())
```

`AsyncFlashData` provides the same resources. Use `await` for requests and `async for`
for pagination and bulk row iterators. Reuse a client within an application or event loop.

## Run work in the background

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    submitted = client.youtube.metadata("dQw4w9WgXcQ", mode="async", include_formats=False)
    job_id = submitted["id"]
    print("Save this job ID:", job_id, flush=True)
    client.jobs.wait(job_id, timeout=300, poll_interval=2)
    result = client.jobs.result(job_id)
    print(result)
```

Save the ID before waiting so the same job can be resumed after a process restart.
`wait()` returns the completed job record; `result()` retrieves its JSON output.
Use [batch submission](docs/jobs.md) for mixed queries and [bulk jobs](docs/bulk.md)
for UTF-8 files containing one YouTube video ID per line.

## Build a YouTube metadata dataset

Create `video-ids.txt` with one YouTube video ID per line:

```text
dQw4w9WgXcQ
jNQXAC9IVRw
```

This example creates the job, uploads the IDs, starts processing, waits, and exports
NDJSON (one JSON object per line). Each row includes an input item's status and data.

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

The inline program saves the accepted ID to `videos.ndjson.job.json` before uploading. After a restart or timeout,
use the [recovery flow](#recover-an-already-started-bulk-job) below instead of rerunning creation.
The inline export uses exclusive creation and refuses to overwrite an existing file.

For a ready-to-run script, run these commands from the repository root. It saves the job
record to `OUTPUT.job.json` before upload and preserves exports with per-item failures:

```sh
python examples/bulk.py video-ids.txt --output artifacts/videos.ndjson
python examples/bulk.py --bulk-id bulk_YOUR_SAVED_ID --output artifacts/videos-recovered.ndjson
```

The create and recovery commands are separate runs; use the second only when recovering,
and replace the saved ID. Other bulk sources include `youtube_transcript`, `youtube_captions`
and `youtube_trainability`; each job applies one set of options to all IDs. See [bulk options](docs/bulk.md).

## Download YouTube videos in bulk

Create `video-ids.txt` with one video ID per line:

```text
dQw4w9WgXcQ
jNQXAC9IVRw
```

Create `private-storage.json` with your destination configuration. For example, for S3:

```json
{
  "storage_type": "s3",
  "storage_url": "your-media-bucket",
  "region": "us-east-1",
  "object_prefix": "youtube",
  "access_key": "YOUR_ACCESS_KEY",
  "secret_key": "YOUR_SECRET_KEY"
}
```

Then create the bulk download task, upload the ID file, and start processing:

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

The inline program saves its accepted ID to `downloads.ndjson.job.json` before uploading.
It saves delivery receipts to `downloads.ndjson` and refuses to overwrite
an existing file. Item failures are reported after receipts have been saved.

Media files are delivered to your configured bucket. `bulk.rows()` reads the task's
JSON result records, including each video's status and source output in `results`.
Check the final counts and row statuses: a completed task can contain failed items.
Downloads are billed by actual delivered bytes; your storage provider may charge separately.

After a process restart or polling timeout, use the saved ID with `client.bulk.get()`,
`client.bulk.wait()`, and `client.bulk.rows()` to continue reading the existing task.
See [bulk controls and recovery](docs/bulk.md), [download options](docs/sources/youtube_download.md),
and [all supported storage providers](docs/storage.md).

The runnable example saves the job record beside its NDJSON export and resumes an
already started task without creating another submission:

```sh
python examples/bulk_download.py video-ids.txt --storage-file private-storage.json --output artifacts/downloads.ndjson
python examples/bulk_download.py --bulk-id bulk_YOUR_SAVED_ID --output artifacts/downloads-recovered.ndjson
```

Run the second command only to recover an already started job, replacing the saved ID.
Use a fresh output path to retain any previous export.

### Deliver MP3 audio instead

Use the same ID file and private storage configuration. In the inline request, set
`download_type` to `audio`, set `output_format` to `mp3`, and remove `video_quality`;
or run the ready-to-use script from the repository root:

```sh
python examples/bulk_download.py video-ids.txt --audio --storage-file private-storage.json --output artifacts/audio.ndjson
```

## Recover an already started bulk job

Replace `bulk_YOUR_SAVED_ID` with the ID printed and saved from either the metadata or
download task. This flow only waits for and reads existing work: no creation, upload or
new download submission.

```python
import json
import os
from pathlib import Path
from flashdata import FlashData

bulk_id = "bulk_YOUR_SAVED_ID"
with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    completed = client.bulk.wait(bulk_id, timeout=3600, poll_interval=5)
    with Path("recovered.ndjson").open("x", encoding="utf-8") as output:
        for row in client.bulk.rows(bulk_id):
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("Saved recovered.ndjson; counts:", completed["counts"])
    if completed["counts"].get("failed") or completed["counts"].get("invalid"):
        raise RuntimeError("Some items failed; inspect the saved rows before retrying")
```

A polling timeout stops local waiting; accepted server work continues. An `awaiting_upload`
job still needs the original upload descriptor and an explicit `start`; a paused job needs
its cause fixed and an explicit `resume`. The example job records omit signed upload
descriptors, so an ID alone cannot recover a process interrupted before upload. Keep storage
credentials and signed URLs out of ordinary job records.

Export promptly: internal results are retained for 24 hours after completion. See
[bulk controls and recovery](docs/bulk.md).

## Handle failures

```python
import os
from flashdata import APIError, FlashData, SubmissionUnknownError

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY"), timeout=120) as client:
    try:
        response = client.google.search("coffee", timeout=60)
    except APIError as error:
        print(error.status_code, error.code, error.request_id, error.retry_after)
    except SubmissionUnknownError:
        # The server may have accepted this paid request. Reconcile before resubmitting.
        raise
```

The SDK sends each request once. It does not automatically retry paid queries or mutations.
See [errors and recovery](docs/errors.md) for rate limits, polling deadlines, failed jobs,
and storage errors. [Client configuration](docs/client.md) covers timeouts, proxies and TLS.

## Supported APIs

| Resource | Methods |
| --- | --- |
| Google | `search`, `images`, `news`, `shopping`, `videos`, `places`, bounded `pages` |
| YouTube | `search`, `search_extended`, `metadata`, `transcript`, `captions`, `license_check`, `channel`, `suggestions`, `download` |
| Queries | `realtime`, `submit`, `batch` with typed wire dictionaries |
| Jobs | `get`, `wait`, `result` |
| Bulk | `create`, `upload_file`, `start`, `get`, `list`, `iter_jobs`, `update`, `pause`, `resume`, `cancel`, `wait`, `manifest`, `part`, `iter_rows`, `rows` |
| Account | `access`, `balance`, `pricing`, `limits`, `usage` |
| Public | `sources`, `plans`, `health`, `status` (no key needed) |

All 15 sources support background submission and batch. The 14 data sources also support
realtime calls. Media downloads run in the background and require customer cloud storage.
Bulk supports metadata, transcripts, captions, license labels, and downloads.

## Guides and runnable examples

- [Getting started](docs/getting-started.md) — install, authenticate, understand responses.
- [Source guides](docs/sources/index.md) — parameters and useful recipes for every source.
- [Examples](examples/README.md) — CLI inputs, readable output, JSON/CSV/NDJSON export.
- [Pagination](docs/pagination.md), [jobs and batch](docs/jobs.md), [bulk datasets](docs/bulk.md).
- [Cloud storage](docs/storage.md), [account and usage](docs/account.md), [API reference](docs/api-reference.md).

```sh
python examples/google_search.py "coffee roasters" --output artifacts/search.json
python examples/search_to_csv.py "coffee roasters" --max-pages 2 --output artifacts/search.csv
python examples/youtube_captions.py dQw4w9WgXcQ --language en
python examples/async_query.py "python tutorial" --output artifacts/result.json
```

These commands call the live API and consume credits. Run `python examples/offline.py`
for a demonstration with a mock transport and no account.

The [SDK and CLI comparison](docs/sdk-parity.md) maps Python, TypeScript/JavaScript, Go
and CLI coverage, examples, bulk recovery and intentional language differences side by side.

Bulk scripts refuse existing exports or `OUTPUT.job.json` records before any API call.
After a timeout or interruption, recover the saved ID into a fresh output path; do not
rerun creation. An empty reserved record needs reconciliation before new work.

## Install from source

From a checkout of this repository:

```sh
python -m pip install .
```

## Development

```sh
python -m pip install -e ".[dev,docs]"
python -m pytest
python -m ruff check src tests examples scripts docs/conf.py
python -m ruff format --check src tests examples scripts docs/conf.py
python -m mypy src/flashdata
python -m sphinx -n -W --keep-going -b html docs docs/_build/html
python -m build
python scripts/verify_package.py
```

Tests use mock transports and a local HTTP server by default. Explicit opt-in tests
exercise live APIs; see [contributing](CONTRIBUTING.md). The project is MIT licensed.
Report sensitive issues through [the security policy](SECURITY.md).
