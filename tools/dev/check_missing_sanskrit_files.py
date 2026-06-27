from pathlib import Path

html_dir = Path("data/scraped")

expected = [
    (2, 3), (2, 4),
    (5, 25), (5, 26),
    (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7), (6, 8), (6, 9), (6, 18), (6, 19),
]

# Add all of books 7, 8, 9
# Book 7 has 15 chapters
for c in range(1, 16):
    expected.append((7, c))
# Book 8 has 24 chapters
for c in range(1, 25):
    expected.append((8, c))
# Book 9 has 24 chapters
for c in range(1, 25):
    expected.append((9, c))

missing = []
for book, ch in expected:
    files = list(html_dir.glob(f"{book}_{ch}_*.html"))
    if not files:
        missing.append((book, ch))

print(f"Checked {len(expected)} book/chapter combinations.")
print(f"Missing Sanskrit HTML files for: {len(missing)} chapters")
if missing:
    for book, ch in missing[:20]:
        print(f"  Missing: Book {book} Chapter {ch}")
    if len(missing) > 20:
        print("  ...")
else:
    print("All required Sanskrit HTML files are present!")
