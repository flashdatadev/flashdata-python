# Changelog

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
