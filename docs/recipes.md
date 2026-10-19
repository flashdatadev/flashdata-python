# Application recipes

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

All example scripts support `--help`. Run them from the repository root after installation.
Set `FLASHDATA_API_KEY` for live examples. Scripts do no network work when imported and
exit with an error message and nonzero code on failure. Output directories are created
as needed; JSON exports preserve the actual API response.

| Goal | Command |
| --- | --- |
| Search results for retrieval | `python examples/google_search.py "coffee" --output artifacts/search.json` |
| Deduplicated search CSV | `python examples/search_to_csv.py "coffee" --max-pages 2 --output artifacts/coffee.csv` |
| News monitoring | `python examples/google_news.py "renewable energy"` |
| Shopping comparison | `python examples/google_shopping.py "mechanical keyboard"` |
| YouTube discovery | `python examples/youtube_search.py "python tutorial" --max-results 5` |
| Uploaded English captions | `python examples/youtube_captions.py dQw4w9WgXcQ --language en --output artifacts/captions.json` |
| Background job with resume | `python examples/async_query.py "coffee" --output artifacts/job.json` |
| Bulk dataset export | `python examples/bulk.py video-ids.txt --output artifacts/dataset.ndjson` |
| Bulk cloud media delivery | `python examples/bulk_download.py video-ids.txt --storage-file private-storage.json --output artifacts/downloads.ndjson` |
| Public discovery without a key | `python examples/discovery.py` |
| Bounded asyncio | `python examples/async_client.py coffee tea` |

The CSV recipe is useful for search monitoring and retrieval ingestion: it preserves
source fields and deduplicates repeated links across pages. It does not infer a global
rank or rewrite snippets into facts. The bulk recipe writes one JSON object per result
line and checks final item counts, so downstream processing can handle source failures.

See [the example catalogue](examples.md) for every source, free account reads,
storage configuration, recovery commands, and expected outputs.
