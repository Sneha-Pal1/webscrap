from pathlib import Path
from bs4 import BeautifulSoup

html_path = Path("test_english_page_2_1.html")
soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")

content_div = soup.find(class_="chapter-content")
if content_div:
    paragraphs = content_div.find_all("p")
    print(f"Found {len(paragraphs)} paragraphs:")
    for i, p in enumerate(paragraphs):
        text = p.get_text(strip=True)
        if text:
            print(f"Para {i}: {text[:150]}...")
else:
    print("No chapter-content class found.")
