import ast
import json
import os
from pathlib import Path
import re
import runpy
from unittest.mock import patch

import httpx
import pytest

from flashdata import FlashData

ROOT = Path(__file__).parents[1]
EXAMPLES = json.loads((ROOT / "tests/fixtures/source-examples.json").read_text())


@pytest.mark.parametrize("source", list(EXAMPLES))
def test_source_example_runs_with_fake_transport(source, tmp_path):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=EXAMPLES[source]["response"])

    storage = tmp_path / "storage.json"
    storage.write_text(json.dumps(EXAMPLES["youtube_download"]["request"]["params"]["storage"]))
    with (
        patch.dict(os.environ, {"FLASHDATA_STORAGE_FILE": str(storage)}),
        patch("flashdata.FlashData", lambda: FlashData("offline-test", transport=httpx.MockTransport(respond))),
    ):
        runpy.run_path(str(ROOT / f"examples/{source}.py"), run_name="__main__")
    assert len(requests) == 1
    assert json.loads(requests[0].content)["source"] == source


def test_documentation_code_blocks_parse_and_relative_links_exist():
    pages = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", *ROOT.glob("docs/**/*.md"), ROOT / "examples/README.md"]
    blocks = 0
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for code in re.findall(r"```python\n(.*?)```", text, flags=re.S):
            ast.parse(code, filename=str(page))
            blocks += 1
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            assert (page.parent / target.split("#")[0]).exists(), (page, target)
    assert blocks >= 20


def test_contract_snapshot_has_all_developer_operations():
    api = json.loads((ROOT / "openapi.json").read_text())
    contracts = json.loads((ROOT / "source-contract.json").read_text())
    assert set(contracts) == set(EXAMPLES)
    assert len(contracts) == 15
    for item in api["paths"].values():
        for operation in item.values():
            assert operation["security"] in ([], [{"dataApiKey": []}])


def test_typed_source_parameters_reject_bad_types(tmp_path):
    # Checked by mypy's public API consumer, without executing paid examples.
    code = """from flashdata import FlashData
c = FlashData("offline")
result = c.google.search("coffee", num=3)
reveal_type(result)
c.youtube.search("coffee", max_results="bad")
"""
    path = tmp_path / "consumer.py"
    path.write_text(code)
    from mypy import api

    output, _errors, status = api.run([str(path), "--follow-imports=normal"])
    assert status == 1 and "max_results" in output
    assert "GoogleSearchResponse" in output
