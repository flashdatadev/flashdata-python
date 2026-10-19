from flashdata import FlashData

with FlashData() as client:
    response = client.youtube.metadata("dQw4w9WgXcQ", include_formats=False, include_chapters=True)
    print(response)
