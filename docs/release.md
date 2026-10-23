# Releases and packages

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

The official package is `flashdata` for Python 3.10+. Version 1.1.0 adds JSON,
plain-text and Markdown response options. Read the [release notes](release-notes-1.1.0.md)
and [format examples](response-formats.md). Existing calls keep their original
JSON response defaults.

The [GitHub release](https://github.com/flashdatadev/flashdata-python/releases/tag/v1.1.0)
provides packages from the tagged source. Published registry versions are listed on
[PyPI](https://pypi.org/project/flashdata/). GitHub wheels can also be installed directly with pip.

## Maintainer checks

Run these before publishing a new immutable version:

```sh
python -m pytest
python -m ruff check src tests examples scripts docs/conf.py
python -m ruff format --check src tests examples scripts docs/conf.py
python -m mypy src/flashdata
python -m sphinx -n -W --keep-going -b html docs docs/_build/html
python scripts/verify_package.py
```

The verifier builds a wheel and source archive, checks their versions and contents, and installs the wheel in a clean consumer environment.
GitHub CI checks supported platforms and runtimes, submits no paid queries, and does
not publish packages. Publish verified distributions using the official registry
account, and keep released files unchanged.
