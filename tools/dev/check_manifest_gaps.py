import csv

manifest_path = "data/scraped/books_3_to_12_manifest.csv"
doc_ids = []
with open(manifest_path, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        doc_ids.append(int(row["doc_id"]))

doc_ids.sort()
print(f"Total entries in manifest: {len(doc_ids)}")
print(f"Min doc_id: {doc_ids[0]}")
print(f"Max doc_id: {doc_ids[-1]}")

gaps = []
for i in range(len(doc_ids) - 1):
    diff = doc_ids[i+1] - doc_ids[i]
    if diff > 1:
        gaps.append((doc_ids[i], doc_ids[i+1]))

print(f"Found {len(gaps)} gaps in doc_ids:")
for start, end in gaps[:20]:
    print(f"  Gap from {start} to {end} (size {end - start - 1})")
if len(gaps) > 20:
    print("  ...")
