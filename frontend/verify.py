from playwright.sync_api import Page, expect, sync_playwright
import os

def verify_feature(page: Page):
    page.goto("http://localhost:4173")
    page.wait_for_timeout(1000)

    # Fill start station
    page.locator('.form-group').nth(0).locator('input').fill("PEOPLE'S SQUARE")
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    page.wait_for_timeout(500)

    # Fill end station
    page.locator('.form-group').nth(1).locator('input').fill("XUJIAHUI")
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    page.wait_for_timeout(500)

    # Exclude a line
    page.locator('.form-group').nth(3).locator('input').fill("LINE 1")
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    page.wait_for_timeout(500)

    # Click find route
    page.get_by_role("button", name="Find Route").click()
    page.wait_for_timeout(1500)

    page.screenshot(path="/home/jules/verification/verification.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    os.makedirs("/home/jules/verification/video", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/video")
        page = context.new_page()
        try:
            verify_feature(page)
        finally:
            context.close()
            browser.close()
