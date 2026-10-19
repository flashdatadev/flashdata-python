# Contributing

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

Use a branch for changes and keep API examples runnable from a source checkout. Never
commit API keys, storage credentials, signed result URLs or customer data.

## Local setup

```sh
python -m venv .venv
# Activate .venv, then:
python -m pip install -e '.[dev,docs]'
python -m pytest
python -m ruff check src tests examples scripts docs/conf.py
python -m ruff format --check src tests examples scripts docs/conf.py
python -m mypy src/flashdata
python -m sphinx -n -W --keep-going -b html docs docs/_build/html
python -m build
python scripts/verify_package.py
python examples/offline.py
```

Default tests use HTTPX mock transports and loopback HTTP servers. The async suite
requires a runtime that can initialize local asyncio sockets. A restricted Windows
sandbox may block event-loop initialization even without external network access.

The normal suite never submits paid production requests. It executes every documentation
Python block and every example with source-shaped mock responses, and verifies that
imports and `--help` do no network work. Keep those tests aligned with live response shapes.

## Live integration tests

Set both `FLASHDATA_RUN_LIVE=1` and `FLASHDATA_LIVE_API_KEY` in your process environment,
then run `python -m pytest tests/test_live.py -q`. These tests consume credits: they run
14 realtime sources, a background query, a mixed 14-item batch, and a small metadata
bulk job. They also read account/public APIs, signed results and errors, and check the
async client. No test cancels other work. The suite needs a key with access to all sources
and sufficient plan limits.

Media download tests validate requests and storage transport offline. Successful delivery
to customer cloud storage needs separate destination credentials and is not part of this
live suite. Automatic CI does not use production keys. The manually dispatched live
workflow requires its explicit paid-call input and a repository secret.

When changing contracts, update runtime validation, exported types, source guides,
examples and fixtures together. Preserve omitted values and explicit false. Test all
affected source modes, unknown submission outcomes and API/storage credential separation.
Keep HTTP retries out of the default client. Read [architecture](docs/architecture.md)
and [API coverage](docs/api-reference.md) before adding new resources.

CI configuration is included for Linux/Windows and supported runtime versions. It has
not executed on GitHub while the repository remains local. [Release preparation](docs/release.md).
