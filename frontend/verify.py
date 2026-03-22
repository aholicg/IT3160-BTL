from playwright.sync_api import Page, expect, sync_playwright
import os
import glob

def verify_feature(page: Page):
    page.goto("http://localhost:4173")
    page.wait_for_timeout(1000)

    # 1. Fill start station
    page.locator('.form-group').nth(0).locator('input[type="text"]').fill("PEOPLE'S SQUARE")
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    page.wait_for_timeout(500)

    # 2. Fill end station
    page.locator('.form-group').nth(1).locator('input[type="text"]').fill("XUJIAHUI")
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    page.wait_for_timeout(500)

    # Select A* Algorithm
    page.get_by_label("A* Search").click()
    page.wait_for_timeout(500)

    # Click find route
    page.get_by_role("button", name="Find Route").click()
    page.wait_for_timeout(2000)

    page.screenshot(path="/home/jules/verification/verification.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    os.makedirs("/home/jules/verification/video", exist_ok=True)
    # Clean previous videos
    for f in glob.glob("/home/jules/verification/video/*.webm"):
        os.remove(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/video", viewport={"width": 1280, "height": 800})
        page = context.new_page()
        try:
            verify_feature(page)
        finally:
            context.close()
            browser.close()
