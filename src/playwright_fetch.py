import time
from pathlib import Path
from playwright.sync_api import sync_playwright

url = "https://www.wisdomlib.org/hinduism/book/bhagavata-purana-sanskrit/d/doc1245012.html"
profile_dir = Path("data/scraped/.browser-profile")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        channel="chrome",
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        viewport={"width": 1280, "height": 900},
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    try:
        print("Navigating to:", url)
        page.goto(url, wait_until="load", timeout=60000)
        
        # Wait a bit for the page to stabilize
        print("Waiting 5s for page stability...")
        page.wait_for_timeout(5000)
        
        # Wait for Cloudflare if needed
        for _ in range(30):
            title = page.title()
            if title and "Just a moment" not in title:
                break
            time.sleep(1)
            
        html = page.content()
        title = page.title()
        print("Title:", title)
        
        out_path = Path("data/scraped/doc1245012.html")
        out_path.write_text(html, encoding="utf-8")
        print("Saved to:", out_path)
    except Exception as e:
        print("Error:", e)
    finally:
        ctx.close()
