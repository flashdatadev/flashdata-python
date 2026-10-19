# FlashData Python SDK

Use Google search data, YouTube discovery and transcripts, and media delivery to your
cloud storage from Python, with synchronous and asynchronous clients.

**Local release candidate:** source, docs, tests and package builds are prepared.
GitHub, PyPI and hosted documentation have not been published.

## Install locally

```sh
python -m pip install .
```

Requires Python 3.10+. [Setup and environment variables](docs/getting-started.md).

## First search

Set `FLASHDATA_API_KEY` in your environment, then run:

```python
from flashdata import FlashData

with FlashData() as client:
    response = client.google.search("coffee", gl="us", num=3)
    for item in response["results"][0].get("organic", []):
        print(item.get("title"), item.get("link"))
```

Use `AsyncFlashData` with `async with` and `await` for native asynchronous HTTP.

The SDK preserves the API envelope: `results` contains source-specific payloads; a
background submission returns a job ID. Downloads are background jobs and require
customer storage. Parameters use the same wire names as the API, including `video_id`,
`max_results` and `callback_url`. Explicit `false` and omitted defaults are preserved.

## Capabilities

| Area | Included |
| --- | --- |
| Google | Search, Images, News, Shopping, Videos and Places |
| YouTube | Search, Extended Search, metadata, existing transcripts, uploader captions, license labels, channels, suggestions and downloads |
| Execution | Realtime, background, mixed batches and explicitly bounded paid Google pagination |
| Jobs | Status, signed JSON result retrieval and opt-in polling |
| Bulk | Streaming ID-file upload, lifecycle controls, progress, manifest and gzip NDJSON parts |
| Account | Authorized sources, balance, current pricing, limits and usage |
| Discovery | Public catalog, plans, health and service status |

No HTTP request is automatically retried. If a paid submission loses its response,
inspect Jobs before submitting again. The software is MIT-licensed; API usage consumes
your account's Credits. [Errors and recovery](docs/errors.md).

## Guides and examples

[Documentation](docs/index.md) · [Source guides](docs/sources/index.md) ·
[Examples](examples/README.md) · [API coverage](docs/api-reference.md) ·
[Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [Security](SECURITY.md)

```sh
python examples/offline.py
python -m pytest
```

The default tests run against simulated HTTP and local servers. The optional live test
uses only free account discovery when `FLASHDATA_LIVE_API_KEY` is explicitly configured.
See [release preparation](docs/release.md) before adding official repository metadata
or publishing a package. Package names are planned names and registry availability has
not been reserved.

Support: support@flashdata.dev · [Product documentation](https://flashdata.dev/docs)
