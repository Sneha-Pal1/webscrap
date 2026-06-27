from pathlib import Path

excel_dir = Path("excel_sheets")
missing = [
    (5, 25), (5, 26),
    (7, 6), (7, 11), (7, 12), (7, 14),
    (8, 2), (8, 9), (8, 12), (8, 14), (8, 17), (8, 19), (8, 20), (8, 22), (8, 23), (8, 24)
]

found = []
not_found = []
for b, c in missing:
    p = excel_dir / f"bhagavata_book{b}_ch{c}_linear.xlsx"
    if p.exists():
        found.append((b, c))
    else:
        not_found.append((b, c))

print(f"Excel sheets found for {len(found)} of the 16 missing chapters.")
print("Found Excel sheets for:")
for b, c in found:
    print(f"  Book {b} Ch {c}")

if not_found:
    print("NOT found Excel sheets for:")
    for b, c in not_found:
        print(f"  Book {b} Ch {c}")
