# Local validation — 2026-10-19

Validated on Windows with Python 3.12.14:

- 164 offline tests pass; one optional live account test is skipped without an explicit key.
- Sync and async clients, all 15 sources, background/batch submission and the bulk lifecycle.
- Local HTTP integration for headers, redirects and streamed file uploads.
- Source examples run with fake transports; documentation code parses and relative links resolve.
- Ruff checks/formatting and mypy checks pass, including a public-type consumer.
- Source archive and wheel build successfully; a fresh virtual environment installs the wheel and executes a mocked query.
- The free live source catalog matches the 15-source snapshot. No paid production queries were run.

GitHub CI is configured for Linux/Windows on Python 3.10, 3.12 and 3.14. Those matrix
runs require publishing the repository and have not run on GitHub. Package-registry
and GitHub publication remain pending the official FlashData accounts.
