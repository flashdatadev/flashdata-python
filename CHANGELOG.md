# Changelog

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

Final local release check: verified Python 3.10/3.12, rejected API-key control characters
before transport creation, required explicit live-test opt-in, and checked dynamic
distribution versions and packaged English/Chinese README contents.

Cross-SDK review: aligned request/bulk typing and stored-result envelopes, added public
discovery and bulk download CLIs, saved bulk job records, preserved concurrent partial
results, validated waiting arguments before submission, fixed initial cursor loops,
added package-consumer verification, and linked every guide to official FlashData pages.

## 0.1.0 — local release candidate

- Document explicit `api_key=os.getenv("FLASHDATA_API_KEY")` initialization consistently
  across the README, guides, and authenticated CLI examples.
- Reworked the README and all source guides around executable tasks and actual response fields.
- Added a Sphinx documentation site, CLI inputs, JSON/CSV/NDJSON exports, and resumable workflows.
- Added per-request timeouts, proxy/TLS configuration, unauthenticated public discovery,
  cached authenticated storage origins, bounded bulk listing and all-part row iteration.
- Fixed malformed callback/URL validation, runtime required-key typing, structured error
  attributes, corrupt gzip handling, unexpected job envelopes, and polling deadline recovery.
- Added executable documentation tests, example integration checks, and opt-in paid live tests.

- All 15 Google and YouTube sources, source validation and typed requests.
- Realtime queries, background submissions, mixed batches and bounded Google pagination.
- Job readers, signed results and explicit bounded polling.
- Bulk create, streaming file upload, start, pause, resume, update, cancel, progress, manifest and gzip NDJSON parts.
- Account access, balance, pricing, limits, usage and public discovery.
- Documentation, runnable examples, offline tests, packaging and CI configuration.

GitHub and package-registry publication have not been performed.
