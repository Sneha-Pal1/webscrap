from pathlib import Path
from bs4 import BeautifulSoup

html_path = Path("data/scraped/2_3_1.html")
if html_path.exists():
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")
    
    # Look for any links on the page, especially those containing "English text" or pointing to English books
    print("ALL LINKS:")
    for a in soup.find_all("a"):
        text = a.get_text(strip=True)
        href = a.get("href")
        if href and ("bhagavata" in href or "english" in text.lower()):
            print(f"Text: '{text}' -> Link: '{href}'")
else:
    print("File not found.")
