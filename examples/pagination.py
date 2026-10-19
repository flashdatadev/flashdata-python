"""At most two paid Google pages; iteration stops on an empty page."""

from flashdata import FlashData

with FlashData() as client:
    for response in client.google.pages("google_search", "coffee", max_pages=2, gl="us"):
        print(response["results"])
