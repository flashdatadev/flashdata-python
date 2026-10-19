"""Usage: python examples/bulk.py path/to/video-ids.txt. Creates and starts paid work."""

import sys
from pathlib import Path
from flashdata import FlashData

if len(sys.argv) != 2 or not Path(sys.argv[1]).is_file():
    raise SystemExit("Usage: python examples/bulk.py path/to/video-ids.txt")

with FlashData() as client:
    created = client.bulk.create({"source": "youtube_metadata", "options": {"include_formats": False}})
    bulk_id = created["job"]["id"]
    print("Save this bulk ID:", bulk_id, flush=True)
    client.bulk.upload_file(created, sys.argv[1])
    print(client.bulk.start(bulk_id))
