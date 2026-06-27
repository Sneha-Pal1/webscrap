import urllib.request
import urllib.error

url = "https://www.wisdomlib.org/hinduism/book/the-bhagavata-purana/d/doc1122471.html"
req = urllib.request.Request(
    url, 
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
)

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        html = response.read()
        print(f"Success! Read {len(html)} bytes.")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}")
except Exception as e:
    print(f"Other Error: {e}")
