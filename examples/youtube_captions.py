from flashdata import FlashData

with FlashData() as client:
    response = client.youtube.captions("dQw4w9WgXcQ", language="en", auto=False)
    print(response)
