"""
Capture User Guide Screenshots

Launches a headless browser, navigates every key feature of Tendly Chat,
and saves screenshots to static/guide/.

Usage:
    python tests/capture_guide.py
    python tests/capture_guide.py --local   # use localhost:5002
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
GUIDE_DIR = ROOT / "static" / "guide"
BASE_URL = "https://chat.tendly.eu"


PAGES = [
    ("01_welcome.png",              None,                           "Welcome screen"),
    ("02_search_it_estonia.png",    "IT tenders in Estonia",        "Search: IT tenders in Estonia"),
    ("03_search_results.png",       "__scroll_results__",           "Search results list"),
    ("04_tender_detail.png",        "__click_tender__",             "Tender detail panel"),
    ("05_construction_latvia.png",  "Construction tenders in Latvia", "Search: Construction in Latvia"),
    ("06_medical_tenders.png",      "High-value medical tenders",   "Search: High-value medical"),
    ("07_language_estonian.png",    "__lang_et__",                  "Estonian language"),
    ("08_language_latvian.png",     "__lang_lv__",                  "Latvian language"),
    ("09_suggestion_chips.png",     "__suggestion_chips__",         "Suggestion chips"),
    ("10_sidebar.png",              "__sidebar__",                  "Sidebar with conversations"),
]


async def run():
    from playwright.async_api import async_playwright

    GUIDE_DIR.mkdir(parents=True, exist_ok=True)
    captured = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        # --- Welcome ---
        await page.goto(BASE_URL)
        await asyncio.sleep(3)
        await page.screenshot(path=str(GUIDE_DIR / "01_welcome.png"))
        print("  captured  01_welcome.png")
        captured += 1

        # --- Search: IT tenders in Estonia ---
        await page.fill('textarea, input[type="text"]', "IT tenders in Estonia")
        await page.keyboard.press("Enter")
        await asyncio.sleep(10)
        await page.screenshot(path=str(GUIDE_DIR / "02_search_it_estonia.png"))
        print("  captured  02_search_it_estonia.png")
        captured += 1

        # --- Scroll to top to see results ---
        await page.evaluate("() => window.scrollTo(0, 0)")
        await asyncio.sleep(1)
        await page.screenshot(path=str(GUIDE_DIR / "03_search_results.png"))
        print("  captured  03_search_results.png")
        captured += 1

        # --- Click first tender for detail panel ---
        tender_item = page.locator('.tender-list-item, [class*="tender-item"]').first
        if await tender_item.count() > 0:
            await tender_item.click()
            await asyncio.sleep(3)
            await page.screenshot(path=str(GUIDE_DIR / "04_tender_detail.png"))
            print("  captured  04_tender_detail.png")
            captured += 1

            # Close panel
            close_btn = page.locator('.detail-close, button:has(img)[class*="close"], .detail-panel button').first
            if await close_btn.count() > 0:
                await close_btn.click()
                await asyncio.sleep(1)

        # --- Suggestion chips screenshot ---
        await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
        await page.screenshot(path=str(GUIDE_DIR / "09_suggestion_chips.png"))
        print("  captured  09_suggestion_chips.png")
        captured += 1

        # --- New Chat: Construction in Latvia ---
        new_chat = page.locator('button:has-text("New Chat")')
        if await new_chat.count() > 0:
            await new_chat.first.click()
            await asyncio.sleep(2)

        await page.fill('textarea, input[type="text"]', "Construction tenders in Latvia")
        await page.keyboard.press("Enter")
        await asyncio.sleep(10)
        await page.screenshot(path=str(GUIDE_DIR / "05_construction_latvia.png"))
        print("  captured  05_construction_latvia.png")
        captured += 1

        # --- New Chat: Medical tenders ---
        new_chat = page.locator('button:has-text("New Chat")')
        if await new_chat.count() > 0:
            await new_chat.first.click()
            await asyncio.sleep(2)

        await page.fill('textarea, input[type="text"]', "High-value medical tenders")
        await page.keyboard.press("Enter")
        await asyncio.sleep(10)
        await page.screenshot(path=str(GUIDE_DIR / "06_medical_tenders.png"))
        print("  captured  06_medical_tenders.png")
        captured += 1

        # --- Sidebar screenshot (should show multiple conversations now) ---
        await page.screenshot(path=str(GUIDE_DIR / "10_sidebar.png"))
        print("  captured  10_sidebar.png")
        captured += 1

        # --- Language: Estonian ---
        lang_select = page.locator("select")
        if await lang_select.count() > 0:
            await lang_select.first.select_option(label="🇪🇪 Eesti")
            await asyncio.sleep(2)
            await page.screenshot(path=str(GUIDE_DIR / "07_language_estonian.png"))
            print("  captured  07_language_estonian.png")
            captured += 1

            # --- Language: Latvian ---
            await lang_select.first.select_option(label="🇱🇻 Latviešu")
            await asyncio.sleep(2)
            await page.screenshot(path=str(GUIDE_DIR / "08_language_latvian.png"))
            print("  captured  08_language_latvian.png")
            captured += 1

            # Reset to English
            await lang_select.first.select_option(label="🇬🇧 English")
            await asyncio.sleep(1)

        await browser.close()
    return captured


def main():
    global BASE_URL
    if "--local" in sys.argv:
        BASE_URL = "http://localhost:5002"

    print(f"\nCapturing User Guide screenshots to {GUIDE_DIR}/")
    print(f"Target: {BASE_URL}\n")

    captured = asyncio.run(run())

    print(f"\nDone — {captured} screenshots in static/guide/")


if __name__ == "__main__":
    main()
