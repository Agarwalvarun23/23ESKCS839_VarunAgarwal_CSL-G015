"""Drive the running Streamlit demo and save a screenshot of each feature.

Start the app first:   streamlit run salting_demo/app.py
Then run:              python tools/ui_screenshots.py [output_dir]

Uses the Microsoft Edge already installed on Windows (no browser download).
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "screenshots"
URL = "http://localhost:8501"


def wait_idle(page, ms=1500):
    # Streamlit shows a "Running..." status widget while the script executes.
    # Streamlit marks the app "running" while the script executes; wait for it to finish.
    page.wait_for_timeout(800)
    state = "document.querySelector('[data-testid=stApp]').getAttribute('data-test-script-state')"
    page.wait_for_function(f"{state} === 'notRunning'", timeout=180_000, polling=200)
    page.wait_for_timeout(ms)


def pick_scheme(page, scheme):
    page.locator("[data-testid=stSidebar]").get_by_text(scheme, exact=True).click()
    wait_idle(page)


def open_tab(page, label):
    page.get_by_role("tab", name=label).click()
    page.wait_for_timeout(500)


def click(page, label):
    page.get_by_role("button", name=label).click()
    wait_idle(page)


def shot(page, name):
    page.screenshot(path=str(OUT / name), full_page=True)
    print("saved", name)


def main():
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(URL)
        wait_idle(page, 2500)

        # Tab 1: unsalted vs salted vs bcrypt hashing
        for scheme, name in [("MD5", "ui_hash_md5.png"),
                             ("SHA-256 + salt", "ui_hash_salted.png"),
                             ("bcrypt", "ui_hash_bcrypt.png")]:
            pick_scheme(page, scheme)
            open_tab(page, "🔑 Hash a password")
            click(page, "Hash it twice")
            shot(page, name)

        # Tab 2: dictionary attack, fast vs slow
        for scheme, name in [("MD5", "ui_dict_md5.png"), ("Argon2id", "ui_dict_argon2.png")]:
            pick_scheme(page, scheme)
            open_tab(page, "📖 Dictionary attack")
            click(page, "Start the attack")
            shot(page, name)

        # Tab 3: brute force, fast vs slow
        for scheme, name in [("SHA-256", "ui_brute_sha256.png"), ("bcrypt", "ui_brute_bcrypt.png")]:
            pick_scheme(page, scheme)
            open_tab(page, "🔨 Brute force")
            click(page, "Start brute force")
            shot(page, name)

        # Tab 4: precomputed table vs salt
        open_tab(page, "🧂 Why salt matters")
        click(page, "Try the lookup table")
        shot(page, "ui_table_vs_salt.png")

        # Tab 5: benchmark graphs
        open_tab(page, "📊 The big picture")
        page.wait_for_timeout(1500)
        shot(page, "ui_benchmarks.png")

        browser.close()


if __name__ == "__main__":
    main()
