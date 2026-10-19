from flashdata import FlashData

with FlashData() as client:
    response = client.google.places("coffee in san francisco", gl="us", hl="en", num=10, page=1)
    print(response)
