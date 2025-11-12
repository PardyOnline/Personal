# login_once.py
from playwright.sync_api import sync_playwright

URL = "https://padeltennisireland.ie/Booking/Grid.aspx"

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # visible browser
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle")
        print("\n1) Log in fully in the opened Chromium window.")
        print("2) Navigate until you can see the booking grid.")
        input("3) When ready, come back here and press ENTER to save cookies... ")

        ctx.storage_state(path="auth.json")
        print("✅ Saved session to auth.json")
        browser.close()
