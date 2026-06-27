from pathlib import Path
from bs4 import BeautifulSoup

html_path = Path("test_english_page.html")
if html_path.exists():
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")
    
    # Print the page's headings
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        print(f"{h.name}: {h.get_text(strip=True)}")
        
    print("\n--- ALL PARAGRAPHS OR DIVS WITH TEXT ---")
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text:
            print(f"<p>: {text[:250]}")
            
    # Also find text blocks with classes containing "text" or "content"
    for div in soup.find_all("div", class_=True):
        if any(x in "".join(div["class"]).lower() for x in ["text", "content"]):
            text = div.get_text(strip=True)
            if text and len(text) > 100:
                print(f"<div class={div['class']}>: {text[:250]}...")
else:
    print("test_english_page.html not found.")
