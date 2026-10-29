import os, json, subprocess, time, requests

PART = "MK1F4LL/A"
ZIPS = ["08753", "08901"]
STATE = "NJ"

def url_for(z):
    return ("/shop/fulfillment-messages?fae=true&little=false&parts.0=" + PART +
            "&cppart=UNLOCKED/US&purchaseOption=fullPrice&mts.0=regular&mts.1=sticky&fts=true&pl=true&location=" + z)

def safari_fetch(path):
    js = "var x=new XMLHttpRequest();x.open('GET','" + path + "',false);x.send();x.responseText;"
    script = '''
tell application "Safari"
  repeat with w in windows
    repeat with t in tabs of w
      if URL of t starts with "https://www.apple.com/shop/buy-iphone/iphone-duo" then
        return do JavaScript "''' + js + '''" in t
      end if
    end repeat
  end repeat
  return "NOTAB"
end tell
'''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=60)
    return r.stdout.strip(), r.stderr.strip()

def check(z):
    out, err = safari_fetch(url_for(z))
    if out == "NOTAB":
        raise RuntimeError("Open the Apple iPhone Duo page in Safari and leave it open.")
    try:
        content = json.loads(out).get("body", {}).get("content", {})
    except Exception:
        raise RuntimeError("Bad answer from Safari: " + (err or out[:100]))
    return content.get("pickupMessage", {}).get("stores", [])

stores, seen, ok = [], set(), False
for z in ZIPS:
    try:
        lst = check(z)
    except Exception as e:
        print("Check failed for", z, e)
        continue
    ok = True
    for s in lst:
        if s.get("state") != STATE:
            continue
        name = s.get("storeName", "Apple Store")
        seen.add(name)
        for info in s.get("partsAvailability", {}).values():
            if info.get("pickupDisplay") == "available" and name not in stores:
                stores.append(name)

if not ok:
    print("Could not read Apple. See messages above.")
elif stores:
    print("IN STOCK at:", stores)
    for attempt in range(5):
        try:
            r = requests.post("https://api.pushover.net/1/messages.json", data={
                "token": os.getenv("PUSHOVER_TOKEN"), "user": os.getenv("PUSHOVER_USER"),
                "title": "iPhone Duo IN STOCK",
                "message": "256GB Night Sky pickup available: " + ", ".join(stores),
                "url": "https://www.apple.com/shop/buy-iphone/iphone-duo",
                "priority": 2, "retry": 30, "expire": 3600, "sound": "siren"}, timeout=20)
            if r.status_code == 200:
                break
        except Exception as e:
            print("Alert failed, retrying:", e)
        time.sleep(10)
else:
    print("Not available yet. NJ stores watched (" + str(len(seen)) + "):", ", ".join(sorted(seen)))
