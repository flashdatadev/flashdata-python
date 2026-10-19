# Contributing

Use a branch for changes and keep API examples runnable from a source checkout. Never
commit API keys, storage credentials, signed result URLs or customer data.

## Local setup

```sh
python -m venv .venv
# Activate .venv, then:
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check src tests examples
python -m mypy src/flashdata
python -m build
python examples/offline.py
```

Default tests use HTTPX mock transports and loopback HTTP servers. The async suite
requires a runtime that can initialize local asyncio sockets. A restricted Windows
sandbox may block event-loop initialization even without external network access.

The normal suite never submits paid production requests. Set `FLASHDATA_LIVE_API_KEY`
only when deliberately enabling the optional free account-access smoke check.

When changing contracts, update runtime validation, exported types, source guides,
examples and fixtures together. Preserve omitted values and explicit false. Test all
affected source modes, unknown submission outcomes and API/storage credential separation.
Keep HTTP retries out of the default client. Read [architecture](docs/architecture.md)
and [API coverage](docs/api-reference.md) before adding new resources.

CI configuration is included for Linux/Windows and supported runtime versions. It has
not executed on GitHub while the repository remains local. [Release preparation](docs/release.md).
