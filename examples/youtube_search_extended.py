from flashdata import FlashData

with FlashData() as client:
    response = client.youtube.search_extended("python", max_results=20)
    print(response)
