import os
import requests

PART = "MK1F4LL/A"
ZIPS = ["08753", "08901"]
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
BASE = "https://www.apple.com/shop/fulfillment-messages"


def make_url(zip_code):
    return (
        f"{BASE}?fae=true&little=false&parts.0={PART}&cppart=UNLOCKED/US"
        f"&purchaseOption=fullPrice&mts.0=regular&mts.1=sticky&fts=true"
        f"&pl=true&location={zip_code}"
    )


stores = []
checked = 0
got_data = False
for z in ZIPS:
    try:
        r = requests.get(make_url(z), headers=HEADERS, timeout=20)
        r.raise_for_status()
        content = r.json().get("body", {}).get("content", {})
    except Exception as e:
        print("Check failed for", z, e)
        continue
    if content:
        got_data = True
    store_list = content.get("pickupMessage", {}).get("stores", [])
    checked += len(store_list)
    for s in store_list:
        for info in s.get("partsAvailability", {}).values():
            if info.get("pickupDisplay") == "available":
                name = s.get("storeName", "Apple Store")
                if name not in stores:
                    stores.append(name)

if not got_data:
    print("Empty response or blocked.")
elif stores:
    print("IN STOCK at:", stores)
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "title": "iPhone Duo IN STOCK",
            "message": "256GB Night Sky pickup available: " + ", ".join(stores),
            "url": "https://www.apple.com/shop/buy-iphone/iphone-duo",
            "priority": 2,
            "retry": 30,
            "expire": 3600,
            "sound": "siren",
        },
        timeout=20,
    )
else:
    print("Not available yet. Stores checked:", checked)
