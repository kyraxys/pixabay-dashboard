from playwright.sync_api import sync_playwright
from datetime import datetime, timezone
import json
import re
import os

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

        except Exception:
            return None

        return None

    def get_editor_choice():
        return 1 if page.locator("text=Editor's Choice").count() > 0 else 0

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

    # Si existe el archivo, cargar el contenido
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

    # Agregar el nuevo registro
    records.append(data)

    # Guardar el JSON completo
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(json.dumps(data, indent=2, ensure_ascii=False))

    browser.close()