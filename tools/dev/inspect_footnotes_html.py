from pathlib import Path
from bs4 import BeautifulSoup

html_path = Path("test_english_page_2_1.html")
soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")

content_div = soup.find(class_="chapter-content")
if content_div:
    # Let's find all paragraph texts and see how footnotes are formatted
    paras = content_div.find_all("p")
    # Let's look at paragraph index 39 and onwards
    for idx in range(39, len(paras)):
        p = paras[idx]
        print(f"Para {idx}: {repr(p.get_text(strip=True)[:100])} -- Tag: {p}")
