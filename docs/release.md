# Release preparation

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

## Final local release check — 2026-10-20

The 1.0.0 release candidate passes the local release checks below. English `README.md`
remains the default, with a visible 简体中文 link to the complete Chinese README.

| Check | Result |
| --- | --- |
| Supported runtimes exercised | Windows: Python 3.10.22 and 3.12.14 |
| Offline tests | 317 passed on each runtime; 20 live checks deliberately skipped |
| Documentation examples | All 40 Python blocks execute, including six Chinese README examples |
| Example CLIs | All 25 checked for import safety, help, outputs and applicable recovery flows |
| Formatting and typing | Ruff and mypy pass |
| Generated documentation | Sphinx builds with warnings treated as errors on both runtimes |
| Packages | Wheel and source archive build; clean installs pass sync/async, mypy and offline-example checks |
| Package metadata | Runtime/distribution versions agree; both source-archive READMEs match the checkout |
| Documentation navigation | Exact-case relative links pass; 18 distinct official URLs return HTTP 200 |
| API parity | Both SDKs agree on 24 operations, 15 sources and 46 resource methods |
| Credential checks | Package contents and Git history have no FlashData-key-shaped matches |

This check fixed control-character validation in both Python clients, made every live
test require explicit opt-in, and removed hard-coded package versions from the verifier.
The TypeScript consumer check now installs its own compiler and Node typings. Its
English and Chinese setup instructions explain those application dependencies.

No paid requests were repeated for this release check; earlier integration evidence is
recorded in [validation](validation.md). Successful customer cloud writes, external
webhook delivery, live pause/resume transitions, Linux and Python 3.14 still require
their respective integration or CI runs. No repository, package or documentation site
was published. Official owner URLs and package-name ownership must be set before release.

## Before publication

This repository is local. Before publication, create the official FlashData GitHub
account, choose the repository owner and verify package-name availability/ownership.
The planned Python distribution name is `flashdata` on PyPI; verify ownership before
publishing. No registry has been changed by this work.

1. Set repository/source/issue metadata to the actual official repository URL.
2. Review license, contact, source contract, changelog and test results.
3. Run all local checks and inspect the package contents listed below.
4. Initialize/push the existing local repository to the official GitHub repository.
5. Run GitHub CI on supported platforms and runtimes. The workflows do not publish.
6. Set up registry credentials or trusted publishing through the registry's official
   account settings, then deliberately publish the reviewed artifact.

```sh
python -m pytest
python -m ruff check src tests examples scripts docs/conf.py
python -m ruff format --check src tests examples scripts docs/conf.py
python -m mypy src/flashdata
python -m sphinx -n -W --keep-going -b html docs docs/_build/html
python -m build
python scripts/verify_package.py
```

The wheel contains the library, typing marker and source schemas. The sdist also includes
docs, examples, tests and API snapshots. Inspect archives and install the wheel into a
fresh environment before release. Verify `import flashdata`, typed source calls, and the
offline example against that installed wheel. No upload/publish workflow or registry
token is configured. The Read the Docs configuration is ready for an official project
to connect; local HTML builds do not create or publish a hosted documentation project.
