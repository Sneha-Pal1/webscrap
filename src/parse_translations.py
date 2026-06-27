import re
from pathlib import Path
from bs4 import BeautifulSoup

def parse_english_translation(html_content: str):
    soup = BeautifulSoup(html_content, "lxml")
    container = soup.find(class_="chapter-content")
    if not container:
        container = soup.find(class_="chapterDetail")
    if not container:
        container = soup.body
        
    # Find all direct child elements or all elements inside container
    elements = container.find_all(["p", "h1", "h2", "h3", "h4"])
    
    verse_translations = {}
    footnotes = {}
    
    current_footnote_id = None
    in_footnotes_section = False
    
    current_speaker = ""
    
    # We will match verse headers like "1. ", "1-2. ", "1, 2. ", "14-15. "
    verse_pattern = re.compile(r"^\s*(\d+)(?:\s*[-,\s]\s*(\d+))?\.\s*(.*)$", re.DOTALL)
    
    for el in elements:
        text = el.get_text().strip()
        if not text:
            continue
            
        # Check if we hit the footnote section
        # Class "nr" is the container of footnote link. E.g. <p class="nr">[1]:</p>
        is_fn_marker = False
        fn_classes = el.get("class", [])
        if "nr" in fn_classes or (el.name == "p" and text.startswith("[") and text.split("]")[0][1:].isdigit()):
            is_fn_marker = True
            
        if is_fn_marker:
            in_footnotes_section = True
            # Extract footnote number
            digits = re.findall(r"\d+", text)
            if digits:
                current_footnote_id = int(digits[0])
                footnotes[current_footnote_id] = []
            continue
            
        if in_footnotes_section:
            if current_footnote_id is not None:
                # If there are links like "[back to top]", skip them
                if "back to top" in text.lower():
                    current_footnote_id = None
                    continue
                # Otherwise, append paragraph text to current footnote
                footnotes[current_footnote_id].append(text)
            continue
            
        # We are in translation section
        if el.name in ["h1", "h2", "h3", "h4"]:
            if "chapter" not in text.lower() and "purana" not in text.lower():
                current_speaker = text
            continue
            
        # For paragraphs, check if it's a verse translation
        match = verse_pattern.match(text)
        if match:
            v_start = int(match.group(1))
            v_end = int(match.group(2)) if match.group(2) else v_start
            v_text = match.group(3).strip()
            
            # If there was a speaker, prepend it (e.g. "Śrī Śuka said: 1. In this way...")
            if current_speaker:
                v_text = f"{current_speaker}\n{v_text}"
                current_speaker = ""
                
            for v in range(v_start, v_end + 1):
                verse_translations[v] = v_text
        else:
            # Check if we should append to the last seen verse
            if verse_translations:
                last_v = max(verse_translations.keys())
                verse_translations[last_v] += "\n" + text
                
    # Now for each verse, map the footnotes referenced in its translation
    mapped_data = {}
    for v, trans in verse_translations.items():
        # Find all [K] references in trans
        refs = [int(r) for r in re.findall(r"\[(\d+)\]", trans)]
        # Gather footnote contents
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

# Test on 2.1
html_content = Path("test_english_page_2_1.html").read_text(encoding="utf-8")
res = parse_english_translation(html_content)

print(f"Parsed {len(res)} verse translations.")
# Print sample: verse 1, verse 27, verse 31, verse 37
for v in [1, 27, 31, 37]:
    if v in res:
        print(f"\n=== VERSE {v} ===")
        print("Translation:", res[v]["translation"][:300])
        print("Purport:", res[v]["purport"][:300])
