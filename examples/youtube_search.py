from flashdata import FlashData

with FlashData() as client:
    response = client.youtube.search("python", max_results=20)
    print(response)
