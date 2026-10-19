"""Two independently billed queries in one batch request; inspect each item."""

from flashdata import FlashData

with FlashData() as client:
    print(
        client.queries.batch(
            [
                {"source": "google_search", "query": "FlashData", "params": {"num": 3}},
                {"source": "youtube_metadata", "video_id": "dQw4w9WgXcQ", "params": {"include_formats": False}},
            ]
        )
    )
