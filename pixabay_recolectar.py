from playwright.sync_api import sync_playwright
from datetime import datetime, timezone
import json
import re
import os

URL = "https://pixabay.com/users/kyraxys-41857870/"
FILE = "pixabay.json"  # JSON Lines (robusto en CI)


def to_int(value: str):
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
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )

    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/137 Safari/537.36"
    )

    page = context.new_page()

    page.goto(URL, wait_until="domcontentloaded", timeout=60000)

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(5000)

    def get_metric(label):
        locator = page.locator(f"text={label}")

        if locator.count() == 0:
            return None

        try:
            parent = locator.first.locator("xpath=ancestor::*[1]")
            text = parent.inner_text()

            match = re.search(r"[\d,.]+[KMB]?", text)

            if match:
                return to_int(match.group(0))

        except:
            return None

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


    # -------------------------
    # APPEND SAFE (NO JSON LOAD)
    # -------------------------
    with open(FILE, "a") as f:
        f.write(json.dumps(data) + "\n")


    print(json.dumps(data, indent=2))

    browser.close()
