from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
html = ROOT / "outputs" / "dashboard.html"
png = ROOT / "outputs" / "dashboard.png"
if not html.exists():
    raise FileNotFoundError(f"Run src/dashboard.py first: {html}")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 1440, "height": 1050}, device_scale_factor=1.4)
    page.goto(html.as_uri(), wait_until="networkidle", timeout=90000)
    page.wait_for_timeout(1800)
    page.screenshot(path=str(png), full_page=True)
    browser.close()
print(f"Saved {png}")
