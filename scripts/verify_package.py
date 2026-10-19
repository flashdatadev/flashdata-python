"""Build local distributions and verify a clean installed-wheel consumer. Never publish."""

import ast
from email.parser import BytesParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
ENV = {
    key: value
    for key, value in os.environ.items()
    if key not in ("PYTHONPATH", "FLASHDATA_API_KEY", "FLASHDATA_LIVE_API_KEY", "FLASHDATA_RUN_LIVE")
}
ENV["PYTHONUTF8"] = "1"


def run(args, cwd=ROOT):
    result = subprocess.run(args, cwd=cwd, env=ENV, text=True, encoding="utf-8", capture_output=True, timeout=240)
    if result.returncode:
        raise RuntimeError(result.stdout[-4000:] + result.stderr[-4000:])
    return result.stdout


def main():
    with (ROOT / "pyproject.toml").open("rb") as file:
        project = tomllib.load(file)["project"]
    version = project["version"]
    module = ast.parse((ROOT / "src/flashdata/__init__.py").read_text(encoding="utf-8"))
    runtime_version = next(
        node.value
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)
    )
    assert ast.literal_eval(runtime_version) == version, "Runtime and distribution versions must match"
    run([sys.executable, "-m", "build"])
    contracts = json.loads((ROOT / "source-contract.json").read_text())
    assert len(contracts) == 15
    wheel = ROOT / f"dist/flashdata-{version}-py3-none-any.whl"
    source = ROOT / f"dist/flashdata-{version}.tar.gz"
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata = BytesParser().parsebytes(archive.read(f"flashdata-{version}.dist-info/METADATA"))
        assert metadata["Name"] == project["name"] and metadata["Version"] == version
        assert "flashdata/py.typed" in names and "flashdata/_schemas.json" in names
        for name in names:
            assert not re.search(rb"fd_[a-z0-9_-]{35,}", archive.read(name), re.I), name
    with tarfile.open(source) as archive:
        names = [member.name.split("/", 1)[-1] for member in archive.getmembers()]
        assert "examples/bulk_download.py" in names and "docs/sdk-parity.md" in names
        assert "README.zh-CN.md" in names
        assert "scripts/verify_package.py" in names
        for readme in ["README.md", "README.zh-CN.md"]:
            member = archive.getmember(f"flashdata-{version}/{readme}")
            assert archive.extractfile(member).read() == (ROOT / readme).read_bytes(), readme
        for member in archive.getmembers():
            name = member.name.split("/", 1)[-1]
            assert not any(
                part in ("_build", "artifacts", ".git", ".venv", "__pycache__") for part in Path(name).parts
            ), name
            assert not name.endswith(".log") and not Path(name).name.startswith(".env"), name
            if member.isfile():
                assert not re.search(rb"fd_[a-z0-9_-]{35,}", archive.extractfile(member).read(), re.I), name
    with tempfile.TemporaryDirectory(prefix="flashdata-wheel-") as directory:
        consumer = Path(directory)
        venv.EnvBuilder(with_pip=True).create(consumer / "venv")
        python = consumer / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", str(wheel)], consumer)
        smoke = consumer / "smoke.py"
        smoke.write_text(
            """from pathlib import Path
import asyncio
import httpx
import flashdata
from flashdata import FlashData, AsyncFlashData
assert Path(flashdata.__file__).is_relative_to(Path(__file__).parent / "venv")
def handle(request):
    return httpx.Response(200,json={"source":"google_search","status":"done","created_at":"now","usage":{"credits":0},"results":[{"organic":[{"title":"Coffee"}]}]})
with FlashData(api_key="offline-key",transport=httpx.MockTransport(handle)) as client:
    assert client.google.search("coffee")["results"][0]["organic"][0]["title"]=="Coffee"
async def main():
    async with AsyncFlashData(api_key="offline-key",transport=httpx.MockTransport(handle)) as client:
        assert (await client.google.search("coffee"))["status"]=="done"
asyncio.run(main())
""",
            encoding="utf-8",
        )
        run([str(python), str(smoke)], consumer)
        shutil.copyfile(ROOT / "examples/offline.py", consumer / "offline.py")
        assert "FlashData docs" in run([str(python), "offline.py"], consumer)
        typed = consumer / "consumer.py"
        typed.write_text(
            """from flashdata import FlashData
from flashdata.types import CreateBulkJobRequest, StorageConfig
storage: StorageConfig={"storage_type":"s3","storage_url":"bucket"}
request: CreateBulkJobRequest={"source":"youtube_download","options":{"storage":storage}}
def check(client: FlashData) -> str:
    response=client.google.search("coffee")
    receipt=client.google.search("coffee",mode="async")
    client.jobs.wait(receipt["id"])
    return response["status"]
""",
            encoding="utf-8",
        )
        run(
            [
                sys.executable,
                "-m",
                "mypy",
                "--python-executable",
                str(python),
                "--follow-imports=normal",
                "--ignore-missing-imports",
                str(typed),
            ],
            consumer,
        )
    print("Verified wheel and source archive; independent sync/async runtime, typing and offline example passed.")


if __name__ == "__main__":
    main()
