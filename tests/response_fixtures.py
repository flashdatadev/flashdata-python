"""Render documentation fixtures while preserving their actual receipt and job state.

The text adapter is checked against API-generated examples. Markdown documents come
from the API serializer's stored-result fixtures; no Node.js is needed to run tests.
"""

from copy import deepcopy
import json
from pathlib import Path
import re

ROOT = Path(__file__).parents[1]
STORED_CASES = json.loads((ROOT / "tests/fixtures/stored-result-formats.json").read_text(encoding="utf-8"))


def stored_result(source, job_id):
    value = deepcopy(STORED_CASES[source][0]["response"])
    value["id"] = job_id
    return value


def label(key):
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(key).replace("_", " "))
    return text[:1].upper() + text[1:]


def scalar(value):
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def plain_fields(value, depth=0):
    items = enumerate(value, 1) if isinstance(value, list) else value.items()
    lines = []
    for key, item in items:
        prefix = "  " * depth + label(key) + ":"
        if isinstance(item, (dict, list)) and item:
            lines.append(prefix + "\n" + plain_fields(item, depth + 1))
        else:
            lines.append(prefix + " " + scalar(item))
    return "\n".join(lines)


def format_fixture(value, accept="application/json", respond_with=None, *, markdown=None):
    if respond_with is None:
        return plain_fields(value) + "\n" if accept == "text/plain" else value
    if markdown is None:
        cases = STORED_CASES[value["source"]]
        assert value["results"] == cases[0]["response"]["results"], "Generate a matching Markdown fixture first."
        markdown = cases[1]["response"]["content"]
    metadata = {key: item for key, item in value.items() if key != "results"}
    if accept == "application/json":
        return {**metadata, "content": markdown}
    fields = "\n".join(f"{label(key)}: {scalar(item)}" for key, item in metadata.items())
    return fields + "\n\nMarkdown Content:\n" + markdown
