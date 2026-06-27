import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

async def main():
    async with async_playwright() as p:
        browser_type = p.chromium
        # Use persistent context to reuse session
        user_data_dir = Path("data/scraped/.browser-profile")
        context = await browser_type.launch_persistent_context(
            user_data_dir,
            headless=True,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        url = "https://www.wisdomlib.org/hinduism/book/the-bhagavata-purana/d/doc1122471.html"
        print(f"Navigating to {url}...")
        
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        # Wait a bit for potential Cloudflare or lazy loads
        await page.wait_for_timeout(3000)
        
        title = await page.title()
        print("Title:", title)
        
        # Save HTML
        content = await page.content()
        Path("test_english_page.html").write_text(content, encoding="utf-8")
        print("Saved HTML to test_english_page.html")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
