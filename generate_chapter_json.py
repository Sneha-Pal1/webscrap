#!/usr/bin/env python3
"""Generate simple per-chapter JSON files from saved Wisdomlib HTML."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

from generate_sanskrit_excel import parse_data
from scrape_chapter import extract_analysis_text

HTML_RE = re.compile(r"^(\d+)_(\d+)_(\d+)\.html$")


def devanagari_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    meta = soup.find("meta", attrs={"name": "description"})
    if not meta or not meta.get("content"):
        return ""
    content = re.sub(r"\s+", " ", meta["content"]).strip()
    return re.sub(r"^Verse\s+[\d.]+:\s*", "", content).strip()


def verse_json_from_html(path: Path, book: int, chapter: int, verse_num: int) -> dict:
    html = path.read_text(encoding="utf-8")
    verse_ref = f"{book}.{chapter}.{verse_num}"
    devanagari = devanagari_from_html(html)

    english_devnagari = ""
    verse_syn: list[str] = []
    try:
        analysis_text = extract_analysis_text(html, verse_ref)
        parsed = parse_data(analysis_text)
        if parsed:
            lines = parsed[0]["lines"]
            english_devnagari = "".join(line["line_text"].strip() for line in lines)
            for line in lines:
                for token in line["tokens"]:
                    verse_syn.append(token["surface"])
    except Exception:
        pass

    return {
        "verse": str(verse_num),
        "devanagari": devanagari,
        "english_devnagari": english_devnagari,
        "verse_Syn": verse_syn,
        "translation": "",
        "purport": "",
    }


def chapter_sort_key(item: tuple[tuple[int, int], list[tuple[int, Path]]]) -> tuple[int, int]:
    return item[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html-dir", type=Path, default=Path("data/scraped"))
    parser.add_argument("--out-dir", type=Path, default=Path("json"))
    parser.add_argument("--start-book", type=int, default=2)
    parser.add_argument("--end-book", type=int, default=12)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    grouped: dict[tuple[int, int], list[tuple[int, Path]]] = {}
    for path in args.html_dir.glob("*_*_*.html"):
        match = HTML_RE.match(path.name)
        if not match:
            continue
        book, chapter, verse_num = (int(part) for part in match.groups())
        if args.start_book <= book <= args.end_book:
            grouped.setdefault((book, chapter), []).append((verse_num, path))

    total_files = 0
    total_verses = 0
    for (book, chapter), verse_paths in sorted(grouped.items()):
        rows = [
            verse_json_from_html(path, book, chapter, verse_num)
            for verse_num, path in sorted(verse_paths)
        ]
        out_path = args.out_dir / f"bhagavata_book{book}_ch{chapter}.json"
        out_path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=4) + "\n",
            encoding="utf-8",
        )
        total_files += 1
        total_verses += len(rows)
        print(f"Wrote {out_path} ({len(rows)} verses)")

    print(f"JSON files: {total_files}")
    print(f"Verses: {total_verses}")


if __name__ == "__main__":
    main()
