from pathlib import Path
from bs4 import BeautifulSoup

html_path = Path("data/scraped/2_3_1.html")
if html_path.exists():
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")
    
    # Let's print out the title, metadata and first few paragraph contents to see where the text resides
    print("PAGE TITLE:", soup.title.string if soup.title else "None")
    
    # Find all divs or paragraphs or sections
    print("\n--- BODY TEXT SAMPLES ---")
    for i, p in enumerate(soup.find_all(["p", "div", "section"])):
        text = p.get_text(strip=True)
        if len(text) > 100:
            print(f"[{p.name} {i}]: {text[:150]}...")
else:
    print("2_3_1.html not found.")
