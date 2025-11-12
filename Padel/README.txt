🎾 Padel Court Availability Watcher
Automated Playwright-based scraper + Discord alerts for Padel Tennis Ireland

This project monitors the Padel Tennis Ireland booking grid and sends instant notifications to your phone via Discord whenever a free court becomes available during peak hours.

It is designed to run 24/7, checking court availability every few minutes, and notifying you only when a new opening appears.

🚀 Features
  ✔️ Automated login using saved authenticated cookies
  
  ✔️ Fully Playwright-driven scraping (no fragile table scraping)
  
  ✔️ Accurate availability detection using SVG geometry + event overlap logic
  
  ✔️ Monitors Courts 1–4 at 20:00, 21:00, and 22:00
  
  ✔️ Discord webhook alerts straight to your phone
  
  ✔️ Runs indefinitely with configurable intervals
  
  ✔️ Supports headless mode
  
  ✔️ Works both locally or 24/7 in the cloud

📸 How It Works (Short Explanation)
Padel Tennis Ireland renders bookings using an SVG grid, not a normal HTML table.

This script:
  Loads the booking page with your stored login cookies
  
  Navigates to the date + scrolls to reveal the court grid
  
  Reads every slot from SVG <rect> elements
  
  Detects availability by checking for overlapping red .evento blocks
  
  Alerts you if a monitored slot becomes free

📦 Requirements
  Python 3.10+
  Playwright
  A Discord server (to create your webhook)
  Install required libraries:
    pip install playwright python-dotenv requests
    playwright install chromium

📁 File Structure
  padel_scraper/
  │
    ├── padel_watcher.py        # Main script (checks + Discord alerts)
    ├── login_once.py           # One-time login script to generate auth.json
    ├── auth.json               # Saved authenticated Playwright state (generated)
    ├── .env                    # Environment variables (Discord webhook, settings)
    └── README.md               # This file

🔐 1. One-Time Login (Generate auth.json)
  Before automation works, manually log in once:
  
  python login_once.py
  
  
  A Playwright browser window will open:
  
  Log in to padeltennisireland.ie manually
  
  Navigate until you can see the booking grid
  
  Return to terminal → press ENTER
  
  auth.json will be created

⚙️ 2. .env Configuration
  Create a file named .env in the root folder:
  
  DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
  HEADLESS=1
  CHECK_INTERVAL=300
  STORAGE_STATE_PATH=auth.json
  
  Explanation:
  
  DISCORD_WEBHOOK_URL → Where notifications go
  
  HEADLESS=1 → Run without opening a real browser
  
  CHECK_INTERVAL=300 → Check every 5 minutes
  
  STORAGE_STATE_PATH → Points to your saved login cookies

🚀 3. Run the Watcher
  python padel_watcher.py
  
  
  You should see logs like:
  
  → Checking date: 2025-11-18
  
  == 20:00 ==
  Court 1 Indoor : BOOKED
  Court 2 Indoor : BOOKED
  Court 3 Indoor : OPEN
  Court 4 Indoor : BOOKED
  
  📲 Sent Discord notification.
  
  📲 Discord Notifications
  
  The script sends phone notifications via Discord Webhooks.

To create your webhook:
  Discord → Server Settings
  
  Integrations → Webhooks
  
  New Webhook → Copy Webhook URL
  
  Paste into .env as DISCORD_WEBHOOK_URL
  
  You will receive messages like:
  
  🎾 Court 3 Indoor available at 21:00 on 2025-11-19
  
  🔄 Running 24/7 (Hands-Off Mode)

🖥️ Windows Task Scheduler (recommended for local use)
  Create a .bat:
  
  @echo off
  cd /d C:\path\to\padel_scraper
  C:\path\to\padel_scraper\.venv\Scripts\python.exe padel_watcher.py
  
  
  Add it to Task Scheduler → Create Task → Run at logon/startup.

⚠️ Important Notes
  If the website changes the SVG layout, selectors may need minor updates
  
  Ensure your auth.json stays valid (re-run login if broken)
  
  Discord webhook must remain active

🛠️ Troubleshooting
  ❌ Discord 404 Error
  
  Your webhook URL is wrong or deleted.
  Create a new one in:
  
  Server Settings → Integrations → Webhooks
  
  ❌ auth.json not working
  
  Just re-run:
  
  python login_once.py

📝 License
  MIT License — free to modify and use as you like.

💬 Questions / Improvements
  Open an issue or submit a pull request!
  This project can easily be extended to:
  
  Monitor more time ranges
  
  Notify via email or SMS
  
  Add web dashboards
  
  Run across multiple clubs
