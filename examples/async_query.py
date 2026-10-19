"""One paid submission, then bounded reads of its existing ID."""

from flashdata import FlashData

with FlashData() as client:
    receipt = client.queries.submit({"source": "youtube_metadata", "video_id": "dQw4w9WgXcQ"})
    print("Save this job ID:", receipt["id"], flush=True)
    client.jobs.wait(receipt["id"], timeout=300, poll_interval=2)
    print(client.jobs.result(receipt["id"]))
