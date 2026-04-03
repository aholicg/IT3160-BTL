from playwright.sync_api import Page, expect, sync_playwright
import os
import glob

def verify_feature(page: Page):
    page.goto("http://localhost:4173")
    page.wait_for_timeout(3000) # Give tiles time to load from openstreetmap

    # Just zoom out a bit and pan to show the colorful tiles
    # We don't necessarily need to route for this test, just show the map visuals
    page.screenshot(path="/home/jules/verification/screenshots/verification.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    os.makedirs("/home/jules/verification/videos", exist_ok=True)
    os.makedirs("/home/jules/verification/screenshots", exist_ok=True)
    # Clean previous videos
    for f in glob.glob("/home/jules/verification/videos/*.webm"):
        os.remove(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/videos", viewport={"width": 1280, "height": 800})
        page = context.new_page()
        try:
            verify_feature(page)
        finally:
            context.close()
            browser.close()
