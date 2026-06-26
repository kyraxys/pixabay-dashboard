from playwright.sync_api import sync_playwright
from datetime import datetime, timezone
import json
import re

URL = "https://pixabay.com/users/kyraxys-41857870/"


def to_int(value: str):
    """Convierte valores como 70,663 / 2.47M / 15K a enteros."""
    if not value:
        return None

    value = value.replace(",", "").strip()

    multipliers = {
        "": 1,
        "K": 1_000,
        "M": 1_000_000,
        "B": 1_000_000_000,
    }

    m = re.match(r"([\d\.]+)\s*([KMB]?)", value)

    if not m:
        return None

    number, suffix = m.groups()

    return int(float(number) * multipliers[suffix])


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/137 Safari/537.36"
    )

    page = context.new_page()

    page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    #page.wait_for_timeout(5000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    def get_metric(label):

        locator = page.locator(f"text={label}")

        if locator.count() == 0:
            return None

        try:
            parent = locator.first.locator("xpath=..")
            text = parent.inner_text()

            match = re.search(r"[\d,.]+[KMB]?", text)

            if match:
                return to_int(match.group(0))

        except Exception:
            pass

        return None


    def get_editor_choice():
        return 1 if page.locator("text=Editor's Choice").count() > 0 else 0


    now = datetime.now(timezone.utc)

    data = {
        "timestamp": now.isoformat(),
        "epoch_ms": int(now.timestamp() * 1000),

        "followers": get_metric("Followers"),
        "following": get_metric("Following"),
        "likes": get_metric("Likes"),
        "views": get_metric("Views"),
        "downloads": get_metric("Downloads"),
        "editor_choice": get_editor_choice()
    }
  
    with open("pixabay.json", "w") as f:
       json.dump(data, f, indent=2)
    print(json.dumps(data, indent=2))

    browser.close()
