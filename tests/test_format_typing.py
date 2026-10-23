"""Check public consumers, including combinations that must fail type checking."""

import json
from pathlib import Path
import re

from mypy import api

SOURCES = json.loads((Path(__file__).parent / "fixtures/source-examples.json").read_text(encoding="utf-8"))


def helper(source):
    resource, method = source.split("_", 1)
    return resource + "." + ("license_check" if method == "trainability" else method)


def test_valid_formats_preserve_precise_types_for_all_helpers(tmp_path):
    response_types = [
        "".join(part.capitalize() for part in source.split("_")) + "Response"
        for source in SOURCES
        if source != "youtube_download"
    ]
    lines = [
        "from typing import Literal",
        "from typing_extensions import assert_type",
        "from flashdata import FlashData, AsyncFlashData, MarkdownQueryResult, ResponseAccept, ContentRepresentation",
        "from flashdata.types import AsyncSubmission, " + ", ".join(response_types),
    ]
    for async_, client in [(False, "FlashData"), (True, "AsyncFlashData")]:
        lines.append(
            f'{"async " if async_ else ""}def check_{client}(c: {client}, accept: ResponseAccept, representation: ContentRepresentation | None, mode: Literal["realtime", "async"]) -> None:'
        )
        prefix = "await " if async_ else ""
        for source in SOURCES:
            method = f"{prefix}c.{helper(source)}"
            if source == "youtube_download":
                call = f'{method}("dQw4w9WgXcQ", storage={{"storage_type": "s3", "storage_url": "bucket"}}'
                lines.extend(
                    [
                        f"    assert_type({call}), AsyncSubmission)",
                        f'    assert_type({call}, accept="text/plain"), str)',
                        f"    assert_type({call}, accept=accept), AsyncSubmission | str)",
                    ]
                )
                continue
            response = "".join(part.capitalize() for part in source.split("_")) + "Response"
            call = method + '("example"'
            for options, expected in [
                ("", response),
                (', respond_with="markdown"', "MarkdownQueryResult"),
                (', accept="text/plain"', "str"),
                (', accept="text/plain", respond_with="markdown"', "str"),
                (', mode="async", callback_url="https://callback.example/done"', "AsyncSubmission"),
                (', mode="async", accept="text/plain"', "str"),
                (', mode="async", accept=accept', "AsyncSubmission | str"),
                (", accept=accept, respond_with=representation", response + " | MarkdownQueryResult | str"),
                (", mode=mode, accept=accept", response + " | AsyncSubmission | str"),
            ]:
                lines.append(f"    assert_type({call}{options}), {expected})")
    path = tmp_path / "valid_formats.py"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    output, errors, status = api.run([str(path), "--follow-imports=normal"])
    assert status == 0, output + errors


def test_invalid_mode_format_and_callback_combinations_are_rejected_for_all_helpers(tmp_path):
    lines = ["from flashdata import FlashData, AsyncFlashData"]
    expected_errors = set()
    for async_, client in [(False, "FlashData"), (True, "AsyncFlashData")]:
        lines.append(f"{'async ' if async_ else ''}def check_{client}(c: {client}) -> None:")
        for source in SOURCES:
            if source == "youtube_download":
                continue
            call = ("await " if async_ else "") + f'c.{helper(source)}("example"'
            for options in [
                ', mode="async", respond_with="markdown"',
                ', mode="async", accept="text/plain", respond_with="markdown"',
                ', callback_url="https://callback.example/done"',
                ', mode="realtime", accept="text/plain", callback_url="https://callback.example/done"',
            ]:
                lines.append(f"    {call}{options})")
                expected_errors.add(len(lines))
    path = tmp_path / "invalid_formats.py"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    output, errors, status = api.run([str(path), "--follow-imports=normal", "--no-pretty"])
    actual_errors = {int(line) for line in re.findall(r":(\d+): error:", output)}
    assert status == 1 and actual_errors == expected_errors, output + errors
