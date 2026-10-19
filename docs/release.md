# Release preparation

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
python -m ruff check src tests examples
python -m mypy src/flashdata
python -m sphinx -n -W --keep-going -b html docs docs/_build/html
python -m build
```

The wheel contains the library, typing marker and source schemas. The sdist also includes
docs, examples, tests and API snapshots. Inspect archives and install the wheel into a
fresh environment before release. Verify `import flashdata`, typed source calls, and the
offline example against that installed wheel. No upload/publish workflow or registry
token is configured. The Read the Docs configuration is ready for an official project
to connect; local HTML builds do not create or publish a hosted documentation project.
