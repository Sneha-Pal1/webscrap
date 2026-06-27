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

def test_chapter(book, chapter, start_url):
    english_dir = Path("data/scraped/english_chapters")
    english_dir.mkdir(parents=True, exist_ok=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    current_url = start_url
    part = 1
    
    print(f"\n--- Testing Book {book} Ch {chapter} starting at {start_url} ---")
    
    while True:
        if part == 1:
            target_path = english_dir / f"bhagavata_book{book}_ch{chapter}.html"
        else:
            target_path = english_dir / f"bhagavata_book{book}_ch{chapter}_part{part}.html"
            
        html_content = None
        if target_path.exists() and target_path.stat().st_size > 1000:
            print(f"  Part {part} already exists locally.")
            html_content = target_path.read_text(encoding="utf-8")
        else:
            print(f"  Fetching Part {part} from {current_url}...")
            req = urllib.request.Request(current_url, headers=headers)
            success = False
            for attempt in range(1, 4):
                try:
                    with urllib.request.urlopen(req, timeout=15) as response:
                        content = response.read()
                        target_path.write_bytes(content)
                        html_content = content.decode("utf-8", errors="replace")
                        success = True
                        break
                except urllib.error.HTTPError as e:
                    print(f"    Attempt {attempt} failed: HTTP Error {e.code}")
                    time.sleep(2)
                except Exception as e:
                    print(f"    Attempt {attempt} failed: {e}")
                    time.sleep(2)
            if not success:
                print(f"    Failed to download Part {part}")
                break
            time.sleep(1) # Polite delay
            
        soup = BeautifulSoup(html_content, "lxml")
        
        # Check Next link
        next_link = None
        for a in soup.find_all("a", href=True):
            if a.get_text().strip() == "Next >":
                next_link = a["href"]
                break
                
        if not next_link:
            print(f"  No 'Next >' link found in Part {part}. Stopping.")
            break
            
        next_url = f"https://www.wisdomlib.org{next_link}" if next_link.startswith("/") else next_link
        
        # Verify if next page belongs to same chapter. 
        # We need to fetch and check the next page.
        # Let us see if we can do this without downloading permanently first.
        print(f"  Checking next page at {next_url}...")
        req = urllib.request.Request(next_url, headers=headers)
        next_html = None
        next_path = english_dir / f"bhagavata_book{book}_ch{chapter}_part{part+1}.html"
        
        if next_path.exists() and next_path.stat().st_size > 1000:
            next_html = next_path.read_text(encoding="utf-8")
        else:
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    next_html = response.read().decode("utf-8", errors="replace")
            except Exception as e:
                print(f"    Failed to inspect next page: {e}")
                break
                
        next_soup = BeautifulSoup(next_html, "lxml")
        next_chapter_num = get_chapter_from_title_or_h1(next_soup)
        
        if next_chapter_num == chapter:
            print(f"    Next page is Chapter {next_chapter_num} (same). Continuing to Part {part+1}.")
            # Save it
            if not next_path.exists():
                next_path.write_text(next_html, encoding="utf-8")
            current_url = next_url
            part += 1
        else:
            print(f"    Next page is Chapter {next_chapter_num} (different). Stopping.")
            break

if __name__ == "__main__":
    # Test Book 10 Ch 80
    test_chapter(10, 80, "https://www.wisdomlib.org/hinduism/book/the-bhagavata-purana/d/doc1128958.html")
    # Test Book 12 Ch 6
    test_chapter(12, 6, "https://www.wisdomlib.org/hinduism/book/the-bhagavata-purana/d/doc1129010.html")
