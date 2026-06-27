import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from bs4 import BeautifulSoup

def get_chapter_from_title_or_h1(soup):
    # Try H1 first
    h1 = soup.find("h1")
    if h1:
        text = h1.get_text().strip()
        m = re.search(r"Chapter\s+(\d+)", text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    
    # Try Title
    title = soup.title.string if soup.title else ""
    m = re.search(r"Chapter\s+(\d+)", title, re.IGNORECASE)
    if m:
        return int(m.group(1))
        
    return None

def is_split_page(soup):
    h1 = soup.find("h1")
    h1_text = h1.get_text() if h1 else ""
    title = soup.title.string if soup.title else ""
    text = f"{h1_text} {title}".lower()
    # Check if title or H1 has indicators of split chapter (e.g. Chapter 80(a), Chapter 6(a), part, introductory)
    return bool(re.search(r'\(\s*[a-z]\s*\)|part|introductory|continued', text))

def main():
    html_dir = Path("data/scraped")
    english_dir = html_dir / "english_chapters"
    english_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Gather all first-verse files to locate English links
    first_verse_files = sorted(
        html_dir.glob("*_*_1.html"),
        key=lambda p: [int(x) for x in p.stem.split("_")]
    )
    
    print(f"Found {len(first_verse_files)} chapters to check/download.")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    success_count = 0
    skipped_count = 0
    failed_count = 0
    
    for i, path in enumerate(first_verse_files, 1):
        parts = path.stem.split("_")
        book = int(parts[0])
        chapter = int(parts[1])
        
        # Parse the Sanskrit page to find the first English link
        try:
            soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "lxml")
        except Exception as e:
            print(f"[{i}/{len(first_verse_files)}] Book {book} Ch {chapter} - Parse Error reading local HTML: {e}")
            failed_count += 1
            continue
            
        english_link = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/book/the-bhagavata-purana/" in href or "the-bhagavata-purana" in href:
                english_link = href
                break
                
        if not english_link:
            print(f"[{i}/{len(first_verse_files)}] Book {book} Ch {chapter} - Warning: No English link found in local Sanskrit HTML")
            failed_count += 1
            continue
            
        if english_link.startswith("/"):
            url = f"https://www.wisdomlib.org{english_link}"
        else:
            url = english_link
            
        # Recursive parts downloader
        part = 1
        current_url = url
        
        while True:
            if part == 1:
                target_path = english_dir / f"bhagavata_book{book}_ch{chapter}.html"
            else:
                target_path = english_dir / f"bhagavata_book{book}_ch{chapter}_part{part}.html"
                
            html_content = None
            if target_path.exists() and target_path.stat().st_size > 1000:
                html_content = target_path.read_text(encoding="utf-8", errors="replace")
                skipped_count += 1
            else:
                print(f"[{i}/{len(first_verse_files)}] Fetching Book {book} Ch {chapter} Part {part} from {current_url}...")
                req = urllib.request.Request(current_url, headers=headers)
                attempt_success = False
                for attempt in range(1, 4):
                    try:
                        with urllib.request.urlopen(req, timeout=15) as response:
                            content = response.read()
                            target_path.write_bytes(content)
                            html_content = content.decode("utf-8", errors="replace")
                            attempt_success = True
                            success_count += 1
                            break
                    except urllib.error.HTTPError as e:
                        print(f"  Attempt {attempt} failed: HTTP Error {e.code} - {e.reason}")
                        time.sleep(2)
                    except Exception as e:
                        print(f"  Attempt {attempt} failed: {e}")
                        time.sleep(2)
                        
                if not attempt_success:
                    print(f"  ERROR: Failed to download Book {book} Ch {chapter} Part {part}")
                    failed_count += 1
                    break
                    
                time.sleep(0.3) # Polite delay
                
            if not html_content:
                break
                
            soup_part = BeautifulSoup(html_content, "lxml")
            
            # Optimization: only check for next part if this page indicates it is split
            if not is_split_page(soup_part):
                break
            
            # Find Next link
            next_link = None
            for a in soup_part.find_all("a", href=True):
                if a.get_text().strip() == "Next >":
                    next_link = a["href"]
                    break
                    
            if not next_link:
                break
                
            next_url = f"https://www.wisdomlib.org{next_link}" if next_link.startswith("/") else next_link
            
            # Look ahead: check if the next page belongs to the same chapter.
            # We fetch it temporarily to check its title/H1.
            next_path = english_dir / f"bhagavata_book{book}_ch{chapter}_part{part+1}.html"
            next_html = None
            if next_path.exists() and next_path.stat().st_size > 1000:
                next_html = next_path.read_text(encoding="utf-8", errors="replace")
            else:
                req_next = urllib.request.Request(next_url, headers=headers)
                try:
                    with urllib.request.urlopen(req_next, timeout=15) as response:
                        next_html = response.read().decode("utf-8", errors="replace")
                except Exception as e:
                    print(f"  Warning: Failed to inspect next page {next_url}: {e}")
                    break
                    
            next_soup = BeautifulSoup(next_html, "lxml")
            next_chapter_num = get_chapter_from_title_or_h1(next_soup)
            
            if next_chapter_num == chapter:
                # Yes, it is the same chapter. We will save it on the next loop iteration or now
                if not next_path.exists():
                    next_path.write_text(next_html, encoding="utf-8")
                    print(f"  Found and pre-cached Part {part+1} for Book {book} Ch {chapter}")
                current_url = next_url
                part += 1
            else:
                # Different chapter, stop traversing
                break
        
    print(f"\nDownload finished. Success: {success_count}, Skipped (Already cached): {skipped_count}, Failed: {failed_count}")

if __name__ == "__main__":
    main()
