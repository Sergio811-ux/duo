import os
import requests

PART = "MK1F4LL/A"
ZIPS = ["08753", "08901"]
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

stores = []
got_data = False
for z in ZIPS:
    try:
        r = requests.get(
            "https://www.apple.com/shop/fulfillment-messages",
            params={"pl": "true", "mts.0": "regular", "parts.0": PART, "location": z},
            headers=HEADERS,
            timeout=20,
        )
        r.raise_for_status()
        content = r.json().get("body", {}).get("content", {})
    except Exception as e:
        print("Check failed for", z, e)
        continue
    if content:
        got_data = True
    for s in content.get("pickupMessage", {}).get("stores", []):
        info = s.get("partsAvailability", {}).get(PART, {})
        name = s.get("storeName", "Apple Store")
        if info.get("pickupDisplay") == "available" and name not in stores:
            stores.append(name)

if not got_data:
    print("Empty response or blocked. Check part number or ZIP.")
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
    print("Not available yet.")
