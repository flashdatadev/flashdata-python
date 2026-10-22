# Runnable examples

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

Install from the repository root with `python -m pip install .`. Each live example passes
`api_key=os.getenv("FLASHDATA_API_KEY")` to its client, so set `FLASHDATA_API_KEY` in your
environment before running it. Live examples consume credits; `account.py` uses free account
reads and `offline.py` uses a mock transport. Use `--help` to see arguments without making
a request. If you use a `.env` file, load it in your application before reading the variable.

Every script has a `main` guard, accepts command-line inputs, and returns a nonzero exit
status on failure. Most support `--output artifacts/name.json` to save the complete response
while printing useful fields. Exports and credentials should stay outside version control.

## Search sources

| Command | Output |
| --- | --- |
| `python examples/google_search.py "coffee roasters"` | Title, URL, snippet, upstream position |
| `python examples/google_images.py "coffee beans"` | Image URL and source page |
| `python examples/google_news.py "renewable energy"` | Headline, publisher, date, article URL |
| `python examples/google_shopping.py "mechanical keyboard"` | Listing, price string, merchant, URL |
| `python examples/google_videos.py "espresso tutorial"` | Video page, duration, source |
| `python examples/google_places.py "coffee shops in Seattle"` | Business, address, rating, website |

All accept `--num`, `--page`, `--gl`, and `--hl`. Request one page at a time or use the
CSV recipe for a bounded set. Optional upstream fields can be empty.

## YouTube sources

| Command | Output |
| --- | --- |
| `python examples/youtube_search.py "python tutorial" --max-results 5` | Video title, channel, watch URL |
| `python examples/youtube_search_extended.py "python tutorial" --max-results 30` | A larger discovery set (up to 700 requested) |
| `python examples/youtube_metadata.py dQw4w9WgXcQ` | Title, channel, duration, caption languages |
| `python examples/youtube_transcript.py dQw4w9WgXcQ --language en` | Timestamped track segments |
| `python examples/youtube_captions.py dQw4w9WgXcQ --language en` | Uploaded caption segments |
| `python examples/youtube_trainability.py dQw4w9WgXcQ` | Detected license labels |
| `python examples/youtube_channel.py @freecodecamp --video-limit 5` | Channel and recent videos |
| `python examples/youtube_suggestions.py python` | Autocomplete suggestions |
| `python examples/youtube_download.py VIDEO_ID --storage-file private-storage.json --wait` | Saved job ID and delivery completion |

The transcript and captions CLI examples select uploaded English captions for the default
video so both are reproducible. Add `--auto` to select automatic captions when available.
The transcript SDK method itself defaults to `auto=True`. Missing tracks are errors;
there is no automatic transcription or translation. License labels are not a grant of rights.

The download script requires a real private cloud destination JSON file or
`FLASHDATA_STORAGE_FILE`; see the storage guide in `docs/storage.md`. It submits one paid
download and waits only when `--wait` is passed. Keep destination credentials private.

## Workflows

```sh
python examples/offline.py
python examples/discovery.py --output artifacts/discovery.json
python examples/account.py --output artifacts/account.json
python examples/async_client.py coffee tea --concurrency 2
python examples/async_query.py coffee --output artifacts/job.json
python examples/batch.py --wait --output artifacts/batch.json
python examples/search_to_csv.py coffee --max-pages 2 --output artifacts/search.csv
python examples/bulk.py examples/video-ids.example.txt --output artifacts/videos.ndjson
python examples/bulk_download.py examples/video-ids.example.txt --storage-file private-storage.json --output artifacts/downloads.ndjson
```

`async_client.py` demonstrates Python asyncio. `async_query.py` demonstrates a server-side
background job using the synchronous client. Both approaches also work together.
`discovery.py` uses public endpoints with an explicit empty key and needs no credentials.
The concurrency example uses a bounded worker pool, preserves individual successes/errors,
and saves them before returning a failure exit status.

Save the job/bulk ID printed before waiting. Resume after a polling deadline or process restart:

```sh
python examples/async_query.py --job-id job_YOUR_SAVED_ID --output artifacts/job.json
python examples/bulk.py --bulk-id bulk_YOUR_SAVED_ID --output artifacts/videos-recovered.ndjson
python examples/bulk_download.py --bulk-id bulk_YOUR_SAVED_ID --output artifacts/downloads-recovered.ndjson
```

Resume commands read existing work instead of submitting it again. A bulk export can contain
failed rows; check counts and row status. A script's nonzero exit code signals an error or
incomplete dataset. Inspect saved output before deciding which items to submit again.
The bulk CLIs save a job record as `OUTPUT.job.json` before upload and on completion;
signed upload descriptors are never saved. Resume assumes the task has already started.
Drafts need upload/start and paused jobs need their blocking condition resolved and `resume` called.

## Bulk export and recovery safety

Bulk scripts reserve fresh export and `OUTPUT.job.json` paths before contacting the API.
They refuse to overwrite either file, including an orphaned or empty recovery record.
Accepted IDs are synced before upload, and completion checkpoints are replaced atomically.
After interruption, use `--bulk-id` with a fresh `--output` filename; never rerun creation
with an old output path. Empty records after uncertain creation need reconciliation.

The media example defaults to MP4. Add `--audio` for MP3 using the same private storage
configuration. See the [workflow comparison](../docs/sdk-parity.md).
