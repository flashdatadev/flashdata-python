from flashdata import FlashData

with FlashData() as client:
    response = client.youtube.license_check("dQw4w9WgXcQ")
    print(response)
