from flashdata import FlashData

with FlashData() as client:
    response = client.google.videos("me at the zoo", gl="us", hl="en", num=10, page=1)
    print(response)
