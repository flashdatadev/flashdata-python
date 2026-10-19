from flashdata import FlashData

with FlashData() as client:
    response = client.youtube.transcript("dQw4w9WgXcQ", language="en", auto=True)
    print(response)
