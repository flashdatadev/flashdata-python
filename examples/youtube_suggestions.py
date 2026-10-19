from flashdata import FlashData

with FlashData() as client:
    response = client.youtube.suggestions("python", language="en", region="us")
    print(response)
