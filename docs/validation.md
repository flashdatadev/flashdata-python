# SDK review and validation — 2026-10-19

This review compared the Python implementation with the current FlashData backend,
the public source catalogue, live API responses, and
[SerpApi's Python SDK at commit 827ebf4](https://github.com/serpapi/serpapi-python/tree/827ebf4886d36dd7b40f294f6857dd2471ac7667).
The reference review covered its client/HTTP layer, result helpers, README, source
recipes, configuration, exceptions, Sphinx documentation, tests, packaging and workflows.
FlashData implementation code is original and follows FlashData's API contracts.

## Changes from the review

| Area | Finding and resulting change |
| --- | --- |
| Onboarding | Release notes crowded the quickstart. The README now starts with installation, working queries, response decoding, asyncio and recovery. |
| Source documentation | Raw JSON examples hid useful fields. Each of the 15 guides now describes a task, shows response traversal, lists parameters and links to scaling guidance. |
| Examples | Hard-coded top-level scripts were difficult to reuse. All 23 scripts now support import-safe entry points and help; live examples accept inputs and export results. |
| Transport | Per-request timeout overrides were not exposed. Both clients now expose them, plus proxy, TLS and environment configuration. Public discovery works without a key. |
| Errors | Management request IDs and Data API retry hints could be lost. Both response formats now populate exception attributes, including field errors. |
| Validation | Malformed URLs/callback ports and unhashable source values could escape as unrelated Python errors. They now raise SDK validation errors before submission. |
| Bulk results | Corrupt gzip could leak decompressor exceptions. Bounded decoding now normalizes them; row and cursor iterators check malformed manifests and repeated cursors. |
| Bulk throughput | Every result part repeated account discovery. The authenticated storage origin is now reused for the client's lifetime. |
| Typing | String-wrapped `Required` annotations had incorrect runtime metadata. Required keys now resolve correctly, and nested search/storage options have public types. |
| Recovery | Polling timeouts could lose the saved ID. Deadline handling now preserves it; job and bulk examples resume existing work. |
| Project quality | Added a navigable Sphinx site, warning-free docs build, executable documentation tests, opt-in live workflow and package-content checks. |

The SerpApi reference informed the onboarding, task-focused guides, configuration and
testable documentation structure. FlashData retains ordinary dictionaries, its own
source-specific result envelopes, separate execution/management origins, and explicit
bulk delivery. Unsupported SerpApi features such as provider-specific engines or output
formats are not exposed as invented FlashData APIs.

## Verification

Validated locally on Windows with Python 3.12.14:

- **278 offline tests:** both clients, all 15 source request contracts, background/batch,
  bulk lifecycle and controls, signed redirects, credential separation, bounded parsing,
  local HTTP integration, nested typing, and failure recovery.
- **31 documentation Python blocks executed**, rather than only parsed; every relative
  documentation link and every source's parameter coverage is checked.
- **23 example scripts checked** for import safety, help without a key, and execution
  with source-shaped test responses, including JSON/CSV/NDJSON exports and resume paths.
- **19 live integration tests passed:** all 14 realtime data sources, a background query,
  a 14-source batch with completed results, metadata bulk upload/start/wait/manifest/rows,
  draft update/cancel, cursor listing, account/public endpoints, async requests and errors.
- **21 CLI examples passed against production**, including every data source and account,
  asyncio, background, batch, pagination/CSV, and bulk/NDJSON workflows. Exports were read
  back and checked. No API key was saved in repository files or artifacts.
- Ruff formatting/linting and mypy pass. Sphinx builds with warnings treated as errors.
- Wheel and source distribution build; a fresh environment installs the wheel and runs
  the offline example. The installed wheel also reads existing live signed job results
  and bulk rows. Archive inspection confirms typing/schema data and excludes generated
  docs, local exports, caches and credentials.

## Remaining verification boundaries

Successful media delivery and bulk customer-result delivery need real destination
credentials. Their request contracts, storage transport, errors and examples are tested
offline; successful delivery to all eight cloud providers has not been asserted.
Bulk pause/resume transitions are covered offline, not by a timing-dependent live run.
Callback receipt/delivery is not exercised against an external webhook server.

CI is configured for Linux/Windows on Python 3.10, 3.12 and 3.14; the GitHub matrix has
not run while the repository remains local. Python 3.10 grammar is checked locally, but
only Python 3.12 has been executed here. GitHub, PyPI and hosted documentation publication
remain pending the official FlashData accounts. The TypeScript SDK was not changed in
this Python-focused review.
