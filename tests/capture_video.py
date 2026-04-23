"""
Capture Product Demo Video

Playwright script that walks through the Tendly Chat interface,
capturing frames for an animated GIF and MP4 video.

Usage:
    # App must be running on chat.tendly.eu or locally
    python tests/capture_video.py
    python tests/capture_video.py --local   # use localhost:5002

Output:
    docs/demo_video.mp4
    docs/demo_video.gif
    docs/frames/*.png
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
FRAMES_DIR = ROOT / "docs" / "frames"
BASE_URL = "https://chat.tendly.eu"

SEARCH_QUERIES = [
    "IT tenders in Estonia",
    "Construction tenders in Latvia",
    "High-value medical tenders",
]

LANGUAGES = [
    ("en", "🇬🇧 English"),
    ("et", "🇪🇪 Eesti"),
    ("lv", "🇱🇻 Latviešu"),
]

frame_num = 0


async def capture(page, label, pause=1.0):
    """Capture a frame with a pause for natural pacing."""
    global frame_num
    await asyncio.sleep(pause)
    path = FRAMES_DIR / f"{frame_num:03d}_{label}.png"
    await page.screenshot(path=str(path), type="png")
    print(f"  [{frame_num:03d}] {label}")
    frame_num += 1


async def send_chat(page, msg, wait=8.0):
    """Type and send a chat message, wait for response."""
    await page.fill('textarea, input[type="text"]', msg)
    await page.keyboard.press("Enter")
    await asyncio.sleep(wait)
    # Scroll chat to bottom
    await page.evaluate("""
        () => {
            var msgs = document.querySelector('.messages-container, .chat-messages, [class*="messages"]');
            if (msgs) msgs.scrollTop = msgs.scrollHeight;
        }
    """)


async def dismiss_overlay(page):
    """Dismiss any modal overlay (e.g. rate-limit upgrade modal)."""
    await page.evaluate("""
        () => {
            document.querySelectorAll('.upgrade-modal-overlay, .modal-overlay, [class*="overlay"]').forEach(el => {
                if (el.style.display !== 'none') el.remove();
            });
        }
    """)
    await asyncio.sleep(0.3)


async def click_new_chat(page):
    """Click the New Chat button."""
    await dismiss_overlay(page)
    btn = page.locator('button:has-text("New Chat"), button:has-text("Uus vestlus")')
    if await btn.count() > 0:
        await btn.first.click()
        await asyncio.sleep(2)


async def run():
    from playwright.async_api import async_playwright

    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        # ===== WELCOME SCREEN =====
        await page.goto(BASE_URL)
        await asyncio.sleep(3)
        await capture(page, "welcome_screen", 1.5)
        await capture(page, "welcome_screen_hold", 1.0)

        # ===== SEARCH: IT tenders in Estonia =====
        await send_chat(page, SEARCH_QUERIES[0], 10)
        await capture(page, "search_it_estonia", 1.0)

        # Scroll up to see AI analysis
        await page.evaluate("() => window.scrollTo(0, 0)")
        await capture(page, "search_it_estonia_top", 0.5)

        # ===== TENDER DETAIL PANEL =====
        tender_item = page.locator('.tender-list-item, [class*="tender-item"]').first
        if await tender_item.count() > 0:
            await tender_item.click()
            await asyncio.sleep(3)
            await capture(page, "tender_detail_panel", 1.5)

            # Close detail panel
            close_btn = page.locator('.detail-close, [class*="close"]').first
            if await close_btn.count() > 0:
                await close_btn.click()
                await asyncio.sleep(1)

        # ===== NEW CHAT: Construction in Latvia =====
        await click_new_chat(page)
        await capture(page, "new_chat", 0.5)

        await send_chat(page, SEARCH_QUERIES[1], 10)
        await capture(page, "search_construction_latvia", 1.0)

        # ===== SUGGESTION CHIPS =====
        chip = page.locator('.suggestion-chip, [class*="suggestion"], button:has-text("tenders")')
        if await chip.count() > 0:
            await capture(page, "suggestion_chips_visible", 0.5)

        # ===== VIEW ALL RESULTS =====
        await dismiss_overlay(page)
        view_all = page.locator('button:has-text("View all")')
        if await view_all.count() > 0:
            await view_all.first.click()
            await asyncio.sleep(2)
            await capture(page, "view_all_results", 1.0)

        # ===== LANGUAGE SWITCH: Estonian =====
        await dismiss_overlay(page)
        lang_select = page.locator("select, combobox")
        if await lang_select.count() > 0:
            await lang_select.first.select_option(label=LANGUAGES[1][1])
            await asyncio.sleep(2)
            await capture(page, "language_estonian", 1.5)

            # Switch back to English
            await lang_select.first.select_option(label=LANGUAGES[0][1])
            await asyncio.sleep(2)

        # ===== LANGUAGE SWITCH: Latvian =====
        if await lang_select.count() > 0:
            await lang_select.first.select_option(label=LANGUAGES[2][1])
            await asyncio.sleep(2)
            await capture(page, "language_latvian", 1.5)

            # Switch back to English
            await lang_select.first.select_option(label=LANGUAGES[0][1])
            await asyncio.sleep(2)

        # ===== NEW CHAT: Medical tenders =====
        await click_new_chat(page)
        await send_chat(page, SEARCH_QUERIES[2], 10)
        await capture(page, "search_medical", 1.0)

        # ===== SIDEBAR with conversations =====
        await capture(page, "sidebar_conversations", 0.5)

        # ===== FINAL WELCOME =====
        await click_new_chat(page)
        await asyncio.sleep(2)
        await capture(page, "final_welcome", 1.5)

        await browser.close()

    print(f"\n  Captured {frame_num} frames to docs/frames/")


def build_video():
    """Assemble frames into MP4 video and GIF."""
    from PIL import Image
    import av
    import numpy as np

    frames = sorted(FRAMES_DIR.glob("*.png"))
    if not frames:
        print("No frames found!")
        return

    images = [np.array(Image.open(f)) for f in frames]
    print(f"  Building video from {len(images)} frames...")

    # --- MP4 ---
    mp4_path = ROOT / "docs" / "demo_video.mp4"
    fps = 2
    hold_frames = 3  # each screenshot held for 1.5 seconds

    container = av.open(str(mp4_path), mode="w")
    h, w = images[0].shape[:2]
    w_enc = w if w % 2 == 0 else w - 1
    h_enc = h if h % 2 == 0 else h - 1
    stream = container.add_stream("libx264", rate=fps)
    stream.width = w_enc
    stream.height = h_enc
    stream.pix_fmt = "yuv420p"

    for img in images:
        img_cropped = img[:h_enc, :w_enc, :3]
        frame = av.VideoFrame.from_ndarray(img_cropped, format="rgb24")
        for _ in range(hold_frames):
            for packet in stream.encode(frame):
                container.mux(packet)

    for packet in stream.encode():
        container.mux(packet)
    container.close()
    total_secs = len(images) * hold_frames / fps
    print(f"  Saved MP4: {mp4_path} ({total_secs:.0f}s)")

    # --- GIF ---
    gif_path = ROOT / "docs" / "demo_video.gif"
    pil_frames = []
    for img in images:
        pil_img = Image.fromarray(img[:, :, :3])
        pil_img = pil_img.resize((w // 2, h // 2), Image.LANCZOS)
        pil_frames.append(pil_img)

    pil_frames[0].save(
        str(gif_path), save_all=True, append_images=pil_frames[1:],
        duration=1500, loop=0, optimize=True,
    )
    print(f"  Saved GIF: {gif_path}")


def main():
    global BASE_URL
    if "--local" in sys.argv:
        BASE_URL = "http://localhost:5002"

    print(f"\n{'='*60}")
    print(f"  Tendly Chat — Video Capture")
    print(f"  Target: {BASE_URL}")
    print(f"{'='*60}\n")

    asyncio.run(run())

    print(f"\n{'='*60}")
    print(f"  Building video and GIF...")
    print(f"{'='*60}\n")

    build_video()

    print(f"\n  Done!")
    print(f"  MP4: docs/demo_video.mp4")
    print(f"  GIF: docs/demo_video.gif")
    print(f"  Frames: docs/frames/\n")


if __name__ == "__main__":
    main()
