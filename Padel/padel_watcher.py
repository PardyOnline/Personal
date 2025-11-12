import os
import re
import time
import json
import requests
from datetime import datetime, timedelta, date

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from dotenv import load_dotenv

# -----------------------------
# Config
# -----------------------------
load_dotenv()  # loads .env values

URL = "https://padeltennisireland.ie/Booking/Grid.aspx"

# Only notify for these courts & times
TARGET_COURT_NUMS = {1, 2, 3, 4, 5}
TARGET_TIMES = ["20:00", "21:00", "22:00"]

# How often to re-check (in seconds)
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))

# Discord webhook (put this in your .env)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

# Headless browser (set HEADLESS=0 in .env to watch it in a real window)
HEADLESS = os.getenv("HEADLESS", "1") != "0"

# Where your login cookies live
STORAGE_STATE_PATH = os.getenv("STORAGE_STATE_PATH", "auth.json")


# -----------------------------
# Utilities
# -----------------------------
def log(msg: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")


def safe_goto(page, url: str, wait_until: str = "networkidle", attempts: int = 2):
    last_err = None
    for i in range(attempts):
        try:
            page.goto(url, wait_until=wait_until, timeout=30000)
            return
        except Exception as e:
            last_err = e
            log(f"[!] goto({url}) failed (attempt {i+1}/{attempts}): {e}")
            time.sleep(1.2)
    if last_err:
        raise last_err


def next_weekday(d: date, target_weekday: int) -> date:
    """Return the next date with weekday target_weekday (Mon=0 ... Sun=6)."""
    return d + timedelta((target_weekday - d.weekday()) % 7)


# -----------------------------
# Navigation to correct date / bring SVG grid into view
# -----------------------------
def goto_date_ui(page, dt_local: date):
    log(f"→ Checking date: {dt_local.isoformat()}")
    safe_goto(page, URL)

    # Scroll towards grid/calendar
    for _ in range(3):
        page.mouse.wheel(0, 2000)
        page.wait_for_timeout(250)

    # Best-effort click on the numeric day in the mini-calendar
    day_num = str(dt_local.day)
    clicked = False

    # Try by role
    for role in ("link", "button", "cell"):
        try:
            el = page.get_by_role(role, name=day_num)
            if el.count() > 0 and el.first.is_visible():
                el.first.click()
                clicked = True
                break
        except Exception:
            pass

    # Fallback: literal text
    if not clicked:
        try:
            page.locator(f"text='{day_num}'").first.click(timeout=1200)
            clicked = True
        except Exception:
            pass

    # Give time for SVG to (re)render
    page.wait_for_timeout(1200)

    # Extra scroll to ensure the SVG is fully in view and laid out
    for _ in range(3):
        page.mouse.wheel(0, 2000)
        page.wait_for_timeout(250)

    # Wait for the SVG if possible (don't hard fail if it’s already on-screen)
    try:
        page.wait_for_selector("svg#tablaReserva", timeout=6000)
    except PWTimeout:
        log("⚠️ SVG booking grid not detected (continuing best-effort).")


# -----------------------------
# Core: read SVG & decide if a slot is OPEN
# -----------------------------
def scrape_svg_openings(page):
    """
    Returns list of cells:
    {
      time: "20:00",
      court_label: "Court 1 Indoor",
      court_num: 1,
      columna: "1",
      x, y, w, h,
      is_open: True/False
    }
    Rule: a cell is OPEN if there's NO overlapping red 'rect.evento' over it.
    """
    openings = page.evaluate(
        """
        () => {
          const svg = document.querySelector('svg#tablaReserva');
          if (!svg) return [];

          // Map columna -> "Court X ..." header text
          const headers = svg.querySelectorAll('#tituloColumna text.cabeceraTxtSup[columna]');
          const colToCourt = {};
          headers.forEach(t => {
            const col = t.getAttribute('columna');
            const label = (t.textContent || '').trim();
            if (col) colToCourt[col] = label;
          });

          // All busy event rectangles (red blocks)
          const events = Array.from(svg.querySelectorAll('rect.evento')).map(r => {
            const x = +r.getAttribute('x') || 0;
            const y = +r.getAttribute('y') || 0;
            const w = +r.getAttribute('width') || 0;
            const h = +r.getAttribute('height') || 0;
            return { x, y, w, h };
          });

          const overlaps = (a, b) => {
            return !(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y);
          };

          // Candidate cells exist for every time/column
          const cells = Array.from(svg.querySelectorAll('#CuerpoTabla rect.subDivision.buttonHora')).map(r => {
            const time  = r.getAttribute('time') || r.getAttribute('datahora') || '';
            const col   = r.getAttribute('columna') || '';
            const x     = +r.getAttribute('x') || 0;
            const y     = +r.getAttribute('y') || 0;
            const w     = +r.getAttribute('width') || 0;
            const h     = +r.getAttribute('height') || 0;

            const court_label = colToCourt[col] || ('Col ' + col);
            const m = court_label.match(/court\\s*(\\d+)/i);
            const court_num = m ? parseInt(m[1], 10) : null;

            const cellBox = { x, y, w, h };
            const covered = events.some(evt => overlaps(cellBox, evt));

            return {
              time, columna: col, x, y, w, h,
              court_label, court_num,
              is_open: !covered
            };
          });

          return cells;
        }
        """
    )
    return openings or []


# -----------------------------
# Notifications — Discord (phone)
# -----------------------------
def discord_notify(new_openings):
    """
    Send a Discord message for JUST the new openings (Courts 1–5).
    """
    if not DISCORD_WEBHOOK_URL:
        return

    if not new_openings:
        return

    lines = [f"🎾 **{o['court']}** available at **{o['time']}** on **{o['date']}**" for o in new_openings]
    content = "\n".join(lines)

    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json={"content": content}, timeout=10)
        if r.status_code >= 400:
            log(f"[!] Discord webhook error {r.status_code}: {r.text[:200]}")
        else:
            log("📲 Sent Discord notification.")
    except Exception as e:
        log(f"[!] Discord notify failed: {e}")


# -----------------------------
# One-day scrape + notify
# -----------------------------
def scrape_day(page, dt_local: date, seen_keys: set):
    """
    Scrapes a single date, prints a small status table,
    and notifies on NEW OPENINGS for Courts 1–4 at 20/21/22.
    Uses 'seen_keys' to avoid duplicate notifications.
    """
    goto_date_ui(page, dt_local)

    try:
        page.wait_for_selector("svg#tablaReserva", timeout=6000)
    except PWTimeout:
        log("⚠️ SVG still not visible; proceeding best-effort.")

    cells = scrape_svg_openings(page)
    if not cells:
        log("No cells found in SVG.")
        return

    # Build status map for printing + collect open cells
    want_times = TARGET_TIMES
    want_courts = TARGET_COURT_NUMS

    # Map court_num -> label for nice output
    label_by_num = {}
    for c in cells:
        n = c.get("court_num")
        if n in want_courts and c.get("court_label"):
            label_by_num[n] = c["court_label"]

    # Prepare status
    status = {(t, n): "UNKNOWN" for t in want_times for n in want_courts}

    # Fill from first matching cell for each (t,n)
    seen_pair = set()
    for c in cells:
        t = c.get("time")
        n = c.get("court_num")
        if t in want_times and n in want_courts:
            key = (t, n)
            if key in seen_pair:
                continue
            seen_pair.add(key)
            status[key] = "OPEN" if c.get("is_open") else "BOOKED"

    # Pretty print per time
    for t in want_times:
        print(f"\n== {t} ==")
        for n in sorted(want_courts):
            label = label_by_num.get(n, f"Court {n}")
            print(f"{label:18} : {status[(t, n)]}")

    # Build just-open list (for Courts 1–4)
    newly_open = []
    for (t, n), s in status.items():
        if s == "OPEN":
            court_label = label_by_num.get(n, f"Court {n}")
            # Unique key per date-time-court
            key = (dt_local.isoformat(), t, n)
            if key not in seen_keys:
                seen_keys.add(key)
                newly_open.append({
                    "date": dt_local.isoformat(),
                    "time": t,
                    "court": court_label
                })

    # Notify via Discord for NEW openings
    discord_notify(newly_open)


# -----------------------------
# Main loop — runs forever
# -----------------------------
def main():
    if not DISCORD_WEBHOOK_URL:
        log("⚠️ No DISCORD_WEBHOOK_URL set. Add it to your .env to get phone notifications.")

    p = sync_playwright().start()
    browser = p.chromium.launch(headless=HEADLESS)
    context = browser.new_context(storage_state=STORAGE_STATE_PATH)
    page = context.new_page()

    log("🎾 Starting Padel Watcher (Ctrl+C to stop)\n")

    # Keep track of what we've already notified for (avoid spam)
    seen_keys = set()

    try:
        while True:
            today = date.today()
            next_tue = next_weekday(today, 1)  # Tue
            next_wed = next_weekday(today, 2)  # Wed

            for d in [next_tue, next_wed]:
                try:
                    scrape_day(page, d, seen_keys)
                except Exception as e:
                    log(f"[!] Error checking {d}: {e}")
                print("-" * 50)

            log(f"Sleeping {CHECK_INTERVAL//60} min...\n")
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        log("Stopping watcher…")
    finally:
        try:
            context.close()
            browser.close()
        except Exception:
            pass
        p.stop()


if __name__ == "__main__":
    main()

