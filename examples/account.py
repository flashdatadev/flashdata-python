"""Free authenticated account reads."""

from flashdata import FlashData

with FlashData() as client:
    print(client.account.access())
    print(client.account.balance())
    print(client.account.pricing(source="google_search", request_count=1))
    print(client.account.limits())
