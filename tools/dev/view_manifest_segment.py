import csv

manifest_path = "data/scraped/books_3_to_12_manifest.csv"
rows = []
with open(manifest_path, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        rows.append(row)

rows.sort(key=lambda r: int(r["doc_id"]))

found_idx = -1
for idx, r in enumerate(rows):
    if int(r["doc_id"]) >= 1245011:
        found_idx = idx
        break

if found_idx != -1:
    print("Entries after 1245011 in manifest:")
    for r in rows[found_idx:found_idx+15]:
        print(f"  doc_id={r['doc_id']}, ref={r['verse_ref']}, file={r['html_file']}")
