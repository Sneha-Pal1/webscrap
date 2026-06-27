import urllib.request
import urllib.error
from bs4 import BeautifulSoup

url = "https://www.wisdomlib.org/hinduism/book/bhagavata-purana-sanskrit/d/doc1246146.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}
req = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        html = response.read().decode("utf-8")
        soup = BeautifulSoup(html, "lxml")
        print("Title:", soup.title.string if soup.title else "No title")
        h1 = soup.find("h1")
        print("H1:", h1.get_text() if h1 else "No H1")
        meta = soup.find("meta", attrs={"name": "description"})
        print("Meta description:", meta["content"] if meta else "No meta description")
except Exception as e:
    print("Error:", e)
