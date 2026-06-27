from playwright.sync_api import sync_playwright
from datetime import datetime, timezone
import json
import re
import os
import time

URL = "https://pixabay.com/users/kyraxys-41857870/"
FILE = "pixabay.json"


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
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]
    )

    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    )

    page = context.new_page()

    # Hasta 3 intentos
    for intento in range(3):
        try:
            page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_selector("text=Followers", timeout=30000)
            break

        except Exception as e:
            print(f"Intento {intento + 1} falló: {e}")

            if intento == 2:
                browser.close()
                raise

            time.sleep(3)

    def get_metric(label):
        try:
            locator = page.locator(f"text={label}").first
            parent = locator.locator("xpath=ancestor::*[1]")
            text = parent.inner_text(timeout=5000)

            match = re.search(r"[\d,.]+[KMB]?", text)

            if match:
                return to_int(match.group(0))

        except Exception:
            return None

        return None

    def get_editor_choice():
        try:
            return 1 if page.locator("text=Editor's Choice").count() > 0 else 0
        except Exception:
            return 0

    now = datetime.now(timezone.utc)

    data = {
        "date": now.isoformat(),
        "followers": get_metric("Followers"),
        "following": get_metric("Following"),
        "likes": get_metric("Likes"),
        "views": get_metric("Views"),
        "downloads": get_metric("Downloads"),
        "editor_choice": get_editor_choice()
    }

    if os.path.exists(FILE):
        try:
            with open(FILE, "r", encoding="utf-8") as f:
                records = json.load(f)

            if not isinstance(records, list):
                records = []

        except (json.JSONDecodeError, FileNotFoundError):
            records = []
    else:
        records = []

    records.append(data)

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(json.dumps(data, indent=2, ensure_ascii=False))

    browser.close()