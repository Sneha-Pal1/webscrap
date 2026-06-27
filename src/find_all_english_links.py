from pathlib import Path
from bs4 import BeautifulSoup
import re

html_dir = Path("data/scraped")
links_found = {}

for html_path in sorted(html_dir.glob("*_*_1.html")):
    # Only look at the first verse of each chapter to see if it links to the English translation
    parts = html_path.stem.split("_")
    book = int(parts[0])
    chapter = int(parts[1])
    
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")
    english_link = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/book/the-bhagavata-purana/" in href:
            english_link = href
            break
        elif "the-bhagavata-purana" in href:
            english_link = href
            break
            
    if english_link:
        links_found[(book, chapter)] = english_link
        print(f"Book {book} Ch {chapter} -> {english_link}")
    else:
        print(f"Book {book} Ch {chapter} -> NO LINK FOUND")
