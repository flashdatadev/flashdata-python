"""Generate stored-result examples using FlashData's HTTP serializer (Node.js required)."""

import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = r"""
const fs = require('node:fs');
const {formatResponse} = require(process.argv[1]);
const examples = JSON.parse(fs.readFileSync(0, 'utf8'));
const output = {};
for (const [source, example] of Object.entries(examples)) {
  const original = {
    id: 'job_fixture0001', source, status: 'completed',
    results: source === 'youtube_download' ? [{
      file_url: 'https://customer.example/videos/example.mp4', downloaded_bytes: 1024,
      file_size: 1024, md5: '0123456789abcdef0123456789abcdef', videoId: 'dQw4w9WgXcQ',
    }] : example.response.results,
    ...(source === 'youtube_download' ? {} : {usage: example.response.usage}),
    completed_at: '2026-10-23T00:00:00Z', expires_at: '2026-10-24T00:00:00Z',
  };
  output[source] = [];
  for (const accept of ['application/json', 'text/plain']) {
    for (const respond_with of [null, 'markdown']) {
      output[source].push({accept, respond_with, response: formatResponse(original, {
        accept, representation: respond_with || 'original',
      })});
    }
  }
}
process.stdout.write(JSON.stringify(output));
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formatter", type=Path, required=True, help="Path to backend/http/responseFormatting.js")
    parser.add_argument("--node", default="node", help="Node.js executable")
    parser.add_argument("--check", action="store_true", help="Check fixtures without writing")
    args = parser.parse_args()
    result = subprocess.run(
        [args.node, "-e", SCRIPT, str(args.formatter.resolve())],
        input=(ROOT / "tests/fixtures/source-examples.json").read_text(encoding="utf-8"),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
        timeout=30,
    )
    generated = json.loads(result.stdout)
    path = ROOT / "tests/fixtures/stored-result-formats.json"
    if args.check:
        if json.loads(path.read_text(encoding="utf-8")) != generated:
            parser.exit(1, "Stored-result fixtures are out of date. Run without --check to refresh them.\n")
        print("Stored-result fixtures match the API serializer (15 sources, four formats each).")
    else:
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(generated, ensure_ascii=False, indent=2) + "\n")
        print("Updated stored-result fixtures.")


if __name__ == "__main__":
    main()
