from flashdata import FlashData

with FlashData() as client:
    response = client.youtube.channel("@jawed", video_limit=10)
    print(response)
