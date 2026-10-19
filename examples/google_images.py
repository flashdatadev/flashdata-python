from flashdata import FlashData

with FlashData() as client:
    response = client.google.images("tokyo skyline", gl="us", hl="en", num=50, page=1)
    print(response)
