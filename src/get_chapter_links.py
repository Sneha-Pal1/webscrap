import sys
import time
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def main():
    url = "https://www.wisdomlib.org/hinduism/book/bhagavata-purana-sanskrit/d/doc1241082.html"
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
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Wait for potential Cloudflare challenge to clear
        for _ in range(45):
            title = page.title()
            if title and "Just a moment" not in title:
                break
            time.sleep(1)
            
        time.sleep(5)  # Let it settle
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        
        # Print headings and paragraphs/main text container
        print("--- CONTENT ---", flush=True)
        main_content = soup.select_one(".main-content-area, article, #main")
        if not main_content:
            main_content = soup.body
            
        # Write to a file so we can view it
        with open("chapter25_content.txt", "w", encoding="utf-8") as f:
            f.write(main_content.get_text("\n", strip=True))
            
        print("Wrote chapter25_content.txt", flush=True)
        ctx.close()

if __name__ == "__main__":
    main()
