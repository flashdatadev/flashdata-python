import ast
import csv
import json
from pathlib import Path
import re
import runpy
import sys

import pytest

ROOT = Path(__file__).parents[1]
EXAMPLES = json.loads((ROOT / "tests/fixtures/source-examples.json").read_text())
SCRIPTS = sorted(p for p in (ROOT / "examples").glob("*.py") if not p.name.startswith("_"))
PAGES = [
    ROOT / "README.md",
    ROOT / "README.zh-CN.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "examples/README.md",
    *(p for p in ROOT.glob("docs/**/*.md") if "_build" not in p.parts),
]
BLOCKS = [
    (str(page.relative_to(ROOT)), index, code)
    for page in PAGES
    for index, code in enumerate(re.findall(r"```python\n(.*?)```", page.read_text(encoding="utf-8"), re.S))
]


@pytest.mark.parametrize("source", list(EXAMPLES))
def test_source_example_runs_exports_and_uses_expected_route(source, example_api, monkeypatch, tmp_path, capsys):
    output = tmp_path / "result.json"
    monkeypatch.setattr(sys, "argv", [source + ".py", "--output", str(output)])
    runpy.run_path(str(ROOT / f"examples/{source}.py"), run_name="__main__")
    value = json.loads(output.read_text(encoding="utf-8"))
    submissions = [r for r in example_api if r.method == "POST"]
    assert len(submissions) == 1
    assert json.loads(submissions[0].content)["source"] == source
    assert value.get("source") == source
    assert capsys.readouterr().out.strip()


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.stem)
def test_examples_are_import_safe_and_help_needs_no_key(path, example_api, monkeypatch):
    runpy.run_path(str(path), run_name="import_check")
    assert not example_api
    monkeypatch.setattr(sys, "argv", [str(path), "--help"])
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(path), run_name="__main__")
    assert error.value.code == 0
    assert not example_api


@pytest.mark.parametrize(
    "name,args",
    [
        ("account", []),
        ("discovery", []),
        ("async_client", ["coffee", "tea"]),
        ("async_query", ["coffee"]),
        ("batch", ["--wait"]),
        ("bulk", ["video-ids.txt"]),
        ("bulk_download", ["video-ids.txt"]),
        ("pagination", []),
        ("search_to_csv", []),
        ("offline", []),
    ],
)
def test_workflow_examples_complete(name, args, example_api, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(sys, "argv", [name + ".py", *args])
    runpy.run_path(str(ROOT / f"examples/{name}.py"), run_name="__main__")
    assert capsys.readouterr().out.strip()
    if name in ("pagination", "search_to_csv"):
        with (tmp_path / "artifacts/search.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        assert rows and len({r["link"] for r in rows}) == len(rows)
    if name in ("bulk", "bulk_download"):
        output = tmp_path / ("artifacts/dataset.ndjson" if name == "bulk" else "artifacts/downloads.ndjson")
        rows = [json.loads(x) for x in output.read_text().splitlines()]
        assert len(rows) == 1 and rows[0]["status"] == "completed"
        job = json.loads(Path(str(output) + ".job.json").read_text())
        assert job["id"] == "bulk_docs12345" and "upload" not in job


@pytest.mark.parametrize(
    "name,flag,id_",
    [
        ("async_query", "--job-id", "job_docs123"),
        ("bulk", "--bulk-id", "bulk_docs12345"),
        ("bulk_download", "--bulk-id", "bulk_docs12345"),
    ],
)
def test_resume_examples_never_submit(name, flag, id_, example_api, monkeypatch):
    monkeypatch.setattr(sys, "argv", [name + ".py", flag, id_])
    runpy.run_path(str(ROOT / f"examples/{name}.py"), run_name="__main__")
    assert all(r.method == "GET" for r in example_api)


@pytest.mark.parametrize("page,index,code", BLOCKS, ids=[f"{p}:{i}" for p, i, _ in BLOCKS])
def test_every_documentation_python_block_executes(page, index, code, example_api):
    tree = ast.parse(code, filename=f"{page}:{index}")
    exec(compile(tree, f"{page}:{index}", "exec"), {"__name__": "__main__"})


def test_documentation_relative_links_exist():
    for page in PAGES:
        text = page.read_text(encoding="utf-8")
        assert "[FlashData](https://flashdata.dev)" in text, page
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            assert (page.parent / target.split("#")[0]).exists(), (page, target)
    assert len(BLOCKS) >= 20


def test_source_guides_cover_every_validated_parameter():
    schemas = json.loads((ROOT / "src/flashdata/_schemas.json").read_text())
    for source, schema in schemas.items():
        page = (ROOT / f"docs/sources/{source}.md").read_text(encoding="utf-8")
        for field in schema["properties"].get("params", {}).get("properties", {}):
            assert f"`{field}`" in page, (source, field)
        assert f"examples/{source}.py" in page


def test_contract_snapshot_has_all_developer_operations():
    api = json.loads((ROOT / "openapi.json").read_text())
    contracts = json.loads((ROOT / "source-contract.json").read_text())
    assert set(contracts) == set(EXAMPLES) and len(contracts) == 15
    for item in api["paths"].values():
        for operation in item.values():
            assert operation["security"] in ([], [{"dataApiKey": []}])


def test_public_typing_rejects_invalid_nested_inputs(tmp_path):
    code = """from flashdata import FlashData
c = FlashData(api_key="offline")
result = c.google.search("coffee", num=3, timeout=30)
reveal_type(result)
c.youtube.search("coffee", filters={"sort_by": "wrong"})
c.youtube.download("dQw4w9WgXcQ")
"""
    path = tmp_path / "consumer.py"
    path.write_text(code)
    from mypy import api

    output, _errors, status = api.run([str(path), "--follow-imports=normal"])
    assert status == 1 and "consumer.py:5: error:" in output and "storage" in output
    assert "GoogleSearchResponse" in output
