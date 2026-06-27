import re
from pathlib import Path
from bs4 import BeautifulSoup

def extract_verse_numbers_and_text(text: str):
    m = re.match(r"^\s*([\d\s\-,]+)\.\s*(.*)$", text, re.DOTALL)
    if not m:
        return None, text
    
    nums_str = m.group(1).strip()
    rest_text = m.group(2).strip()
    
    if not re.search(r"\d", nums_str):
        return None, text
        
    verses = []
    if "-" in nums_str:
        parts = re.split(r"\s*-\s*", nums_str)
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            start, end = int(parts[0]), int(parts[1])
            verses = list(range(start, end + 1))
    else:
        parts = re.split(r"\s*,\s*", nums_str)
        if all(p.strip().isdigit() for p in parts if p.strip()):
            verses = [int(p.strip()) for p in parts if p.strip()]
            
    if not verses:
        return None, text
    return verses, rest_text

def parse_english_translation(html_content: str):
    soup = BeautifulSoup(html_content, "lxml")
    container = soup.find(class_="chapter-content")
    if not container:
        container = soup.find(class_="chapterDetail")
    if not container:
        container = soup.body
        
    elements = container.find_all(["p", "h1", "h2", "h3", "h4"])
    
    verse_translations = {}
    footnotes = {}
    
    current_footnote_id = None
    in_footnotes_section = False
    current_speaker = ""
    
    for el in elements:
        text = el.get_text().strip()
        if not text:
            continue
            
        is_fn_marker = False
        fn_classes = el.get("class", [])
        if "nr" in fn_classes or (el.name == "p" and text.startswith("[") and text.split("]")[0][1:].isdigit()):
            is_fn_marker = True
            
        if is_fn_marker:
            in_footnotes_section = True
            digits = re.findall(r"\d+", text)
            if digits:
                current_footnote_id = int(digits[0])
                footnotes[current_footnote_id] = []
            continue
            
        if in_footnotes_section:
            if current_footnote_id is not None:
                if "back to top" in text.lower():
                    current_footnote_id = None
                    continue
                footnotes[current_footnote_id].append(text)
            continue
            
        if el.name in ["h1", "h2", "h3", "h4"]:
            if "chapter" not in text.lower() and "purana" not in text.lower():
                current_speaker = text
            continue
            
        verses, rest_text = extract_verse_numbers_and_text(text)
        if verses:
            if current_speaker:
                rest_text = f"{current_speaker}\n{rest_text}"
                current_speaker = ""
            for v in verses:
                verse_translations[v] = rest_text
        else:
            if verse_translations:
                last_v = max(verse_translations.keys())
                verse_translations[last_v] += "\n" + text
                
    mapped_data = {}
    for v, trans in verse_translations.items():
        refs = [int(r) for r in re.findall(r"\[(\d+)\]", trans)]
        purport_parts = []
        for r in refs:
            if r in footnotes:
                purport_parts.append(f"Footnote [{r}]:\n" + "\n".join(footnotes[r]))
        
        purport_str = "\n\n".join(purport_parts)
        mapped_data[v] = {
            "translation": trans,
            "purport": purport_str
        }
        
    return mapped_data

# Test it
html_content = Path("test_english_page_2_1.html").read_text(encoding="utf-8")
res = parse_english_translation(html_content)
print(f"Parsed {len(res)} verses.")
for v in [1, 2, 27, 31, 37]:
    print(f"\nVerse {v} Translation snippet: {repr(res[v]['translation'][:100])}")
