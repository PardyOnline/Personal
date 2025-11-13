import os
import time
import json
from datetime import datetime, date, time as dtime, timedelta

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import requests

# =========================
#  CONFIG
# =========================

load_dotenv()

BOOKING_URL = "https://padeltennisireland.ie/Booking/Grid.aspx"

# Path to your Playwright storage state (created by login_once.py)
STORAGE_STATE = os.getenv("STORAGE_STATE_PATH", "auth.json")

# Discord webhook URL (stored in .env)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

# Run headless or with visible browser
HEADLESS = os.getenv("HEADLESS", "1") == "1"

# How often to re-check (in seconds)
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))  # 5 minutes default

# Courts & times to monitor
TARGET_COURTS = {
    1: "Court 1 Indoor",
    2: "Court 2 Indoor",
    3: "Court 3 Indoor",
    4: "Court 4 Indoor",
    # You can add 5 here if you ever want Court 5 Outdoor again
}

TARGET_TIMES = [
    dtime(20, 0),  # 20:00
    dtime(21, 0),  # 21:00
    dtime(22, 0),  # 22:00
]

# 0 = Monday, 1 = Tuesday, 2 = Wednesday, ...
TARGET_WEEKDAYS = {1, 2}  # Tuesday & Wednesday


# =========================
#  LOGGING
# =========================

def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


# =========================
#  DISCORD
# =========================

def send_discord_notification(day: date, openings: list[tuple[dtime, str]]) -> None:
    """Send a nicely formatted Discord message when openings are found."""
    if not DISCORD_WEBHOOK_URL:
        log("[!] DISCORD_WEBHOOK_URL not set – skipping Discord notification.")
        return

    # Only include courts 1–4 in notifications as per your requirement
    filtered = [(t, c) for (t, c) in openings if c in TARGET_COURTS.values()]
    if not filtered:
        return

    lines = []
    for slot_time, court_name in filtered:
        lines.append(f"- **{slot_time.strftime('%H:%M')}** on **{court_name}**")

    content = (
        f"🎾 **Padel Court Openings Detected** 🎾\n"
        f"Date: **{day.isoformat()}**\n\n" +
        "\n".join(lines)
    )

    payload = {"content": content}

    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if resp.status_code >= 400:
            log(f"[!] Discord webhook error {resp.status_code}: {resp.text}")
        else:
            log("[✓] Discord notification sent.")
    except Exception as e:
        log(f"[!] Failed to send Discord notification: {e}")


# =========================
#  PAGE HELPERS
# =========================

def _scroll_to_grid(page) -> None:
    """Scroll down so the SVG booking grid is in view."""
    page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
    page.wait_for_timeout(1000)


def _goto_date(page, target_date: date) -> None:
    """
    Navigate the booking grid to the given date.

    NOTE:
    -----
    This is the one piece that can vary a lot depending on how Matchpoint
    is wired for this site. If you already have a working _goto_date in
    your existing script, KEEP THAT and ignore this version.

    This stub assumes that loading BOOKING_URL always shows the *current* date
    and that the site auto-switches when you click the weekday in the little
    weekly strip. We simplify by:
    - Reloading the page each time
    - Clicking the weekday cell that matches the target_date.weekday()
    - Assuming the grid will then show that date (for the current week / next)
    """
    # Reload the grid fresh each time to avoid stale state
    page.goto(BOOKING_URL, wait_until="networkidle")

    # Simple: if today == target_date, nothing else to do
    today = datetime.now().date()
    if target_date == today:
        return

    # Try to click in the weekly strip (Mo Tu We Th Fr Sa Su)
    # This is the same table we saw in earlier debug output.
    weekday_index = target_date.weekday()  # 0..6 (Mon..Sun)

    # Locate the calendar table that has weekday headers
    tables = page.query_selector_all("table")
    target_table = None
    for t in tables:
        header_cells = [c.inner_text().strip() for c in t.query_selector_all("th, td")]
        if header_cells[:7] == ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            target_table = t
            break

    if not target_table:
        log("⚠️ Could not find weekday header table to change date.")
        return

    # Click corresponding weekday cell in the body (best-effort; assumes first row)
    body_cells = target_table.query_selector_all("tbody td")
    if len(body_cells) >= 7:
        try:
            body_cells[weekday_index].click()
            page.wait_for_timeout(1500)
        except Exception as e:
            log(f"⚠️ Failed to click weekday cell: {e}")
    else:
        log("⚠️ Not enough cells in weekday table to select weekday.")


def _get_svg(page):
    svg = page.query_selector("svg#tablaReserva")
    if not svg:
        log("⚠️ Could not find SVG booking grid on this date.")
    return svg


def _is_cell_open(svg, target_time: dtime, col_idx: int) -> bool:
    """
    Determine if a given (time, court column) is free.

    Logic:
      1) Find the button rect with class 'subDivision plantilla buttonHora'
         and attributes:
            - time="HH:MM"
            - columna="<col_idx>"
      2) Get its bounding box.
      3) Look at all rect.evento (booked blocks) and see if any overlap
         that bounding box significantly.
    """
    time_str = target_time.strftime("%H:%M")

    cell = svg.query_selector(
        f"rect.subDivision.buttonHora[time='{time_str}'][columna='{col_idx}']"
    )
    if not cell:
        # If there is no booking button at all, treat as not bookable
        return False

    cell_box = cell.bounding_box()
    if not cell_box:
        return False

    cx, cy, cw, ch = (
        cell_box["x"],
        cell_box["y"],
        cell_box["width"],
        cell_box["height"],
    )

    # Helper for overlap check
    def overlaps(a, b) -> bool:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        x_overlap = max(0, min(ax + aw, bx + bw) - max(ax, bx))
        y_overlap = max(0, min(ay + ah, by + bh) - max(ay, by))
        return x_overlap > 5 and y_overlap > 5

    # Check all event rects (booked blocks)
    events = svg.query_selector_all("rect.evento")
    for e in events:
        e_box = e.bounding_box()
        if not e_box:
            continue
        ex, ey, ew, eh = (
            e_box["x"],
            e_box["y"],
            e_box["width"],
            e_box["height"],
        )
        if overlaps((cx, cy, cw, ch), (ex, ey, ew, eh)):
            # There is a booked event overlapping this slot
            return False

    # No overlapping event found → appears open
    return True


# =========================
#  DATE GENERATION
# =========================

def generate_target_dates() -> list[date]:
    """
    Return all Tuesday/Wednesday dates within the next 2 weeks (rolling window).

    If today is Wednesday 2025-11-12, this will typically return:
      - 2025-11-12
      - 2025-11-18
      - 2025-11-19
      - 2025-11-25
      - 2025-11-26
    """
    today = datetime.now().date()
    dates: list[date] = []

    for offset in range(0, 15):  # today + 0..14 days
        d = today + timedelta(days=offset)
        if d.weekday() in TARGET_WEEKDAYS:
            dates.append(d)

    return dates


# =========================
#  SCRAPING A SINGLE DAY
# =========================

def scrape_day(page, target_date: date) -> list[tuple[dtime, str]]:
    """
    Return a list of (opening_time, court_name) that are open for target_date.
    Also prints [OPEN]/[BOOKED] lines for debugging.
    """
    log(f"→ Checking date: {target_date}")

    # Work out if this is "today" so we can ignore times in the past
    now = datetime.now()
    is_today = (target_date == now.date())

    _goto_date(page, target_date)
    page.wait_for_timeout(1500)
    _scroll_to_grid(page)

    svg = _get_svg(page)
    if not svg:
        return []

    openings: list[tuple[dtime, str]] = []

    for opening_time in TARGET_TIMES:
        # Skip past times for today
        if is_today:
            slot_dt = datetime.combine(target_date, opening_time)
            if slot_dt <= now:
                continue

        for col_idx, court_name in TARGET_COURTS.items():
            try:
                is_open = _is_cell_open(svg, opening_time, col_idx)
            except Exception as e:
                log(f"⚠️ Error checking {opening_time} {court_name}: {e}")
                continue

            if is_open:
                openings.append((opening_time, court_name))
                log(f"[OPEN]   {target_date}  {opening_time.strftime('%H:%M')}  {court_name}")
            else:
                log(f"[BOOKED] {target_date}  {opening_time.strftime('%H:%M')}  {court_name}")

    if not openings:
        log("No target openings on this date.")
    return openings


# =========================
#  MAIN LOOP
# =========================

def main():
    log("Starting padel watcher… (Stop with Ctrl+C)")
    log(f"Headless: {HEADLESS}, Check interval: {CHECK_INTERVAL}s")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(storage_state=STORAGE_STATE)
        page = context.new_page()

        # Initial load to make sure cookies/auth are valid
        log(f"Opening booking page: {BOOKING_URL}")
        page.goto(BOOKING_URL, wait_until="networkidle")
        _scroll_to_grid(page)

        try:
            while True:
                target_dates = generate_target_dates()

                for target_date in target_dates:
                    openings = scrape_day(page, target_date)

                    # Only notify if there are openings (and only courts 1–4
                    # will be included in the message inside the function).
                    if openings:
                        send_discord_notification(target_date, openings)

                log(f"Sleeping for {CHECK_INTERVAL} seconds…")
                time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            log("Received Ctrl+C – stopping watcher.")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
