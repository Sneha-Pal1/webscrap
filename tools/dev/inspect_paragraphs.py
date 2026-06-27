from pathlib import Path
from bs4 import BeautifulSoup
import re

html_path = Path("test_english_page.html")
soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")

content_div = soup.find(class_="chapter-content")
if content_div:
    paragraphs = content_div.find_all("p")
    print(f"Found {len(paragraphs)} paragraphs in chapter-content:")
    for i, p in enumerate(paragraphs):
        text = p.get_text(strip=True)
        if text:
            print(f"Para {i}: {text[:150]}...")
else:
    # If no specific chapter-content div, check general div
    print("No class='chapter-content' found, printing all paragraph tags in body:")
    for i, p in enumerate(soup.body.find_all("p")):
        text = p.get_text(strip=True)
        if text:
            print(f"Para {i}: {text[:150]}...")
