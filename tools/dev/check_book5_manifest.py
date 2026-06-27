import csv

manifest_path = "data/scraped/books_3_to_12_manifest.csv"
book5_entries = []
with open(manifest_path, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ref = row["verse_ref"]
        parts = ref.split(".")
        if len(parts) == 3 and parts[0] == "5":
            book5_entries.append((int(parts[1]), int(parts[2]), int(row["doc_id"])))

book5_entries.sort()
print(f"Book 5 entries in manifest: {len(book5_entries)}")
chapters = set()
for ch, v, doc_id in book5_entries:
    chapters.add(ch)

print(f"Chapters present in manifest for Book 5: {sorted(list(chapters))}")
if book5_entries:
    print(f"Book 5 chapter 24 last verse: {book5_entries[-1]}")
