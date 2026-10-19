import json
import os
from pathlib import Path
from flashdata import FlashData

storage = json.loads(Path(os.environ["FLASHDATA_STORAGE_FILE"]).read_text(encoding="utf-8"))
with FlashData() as client:
    receipt = client.youtube.download("dQw4w9WgXcQ", storage=storage, video_quality="<=720")
    print(receipt["id"])
