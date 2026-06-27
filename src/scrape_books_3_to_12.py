#!/usr/bin/env python3
"""Scrape Wisdomlib Bhagavata Sanskrit Books 3-12 and write linear Excels.

This keeps the same source extraction method as ``scrape_chapter.py``:
save each Wisdomlib verse page as HTML, then parse the saved HTML locally.
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from generate_sanskrit_excel import build_linear_rows, parse_data, write_linear_excel
from scrape_chapter import extract_analysis_text

BASE_URL = "https://www.wisdomlib.org/hinduism/book/bhagavata-purana-sanskrit/d/doc{doc_id}.html"
VERSE_RE = re.compile(r"\bVerse\s+(\d+)\.(\d+)\.(\d+)\b", re.I)


def verse_ref_from_html(html: str) -> tuple[int, int, int] | None:
    soup = BeautifulSoup(html, "lxml")
    candidates = []
    if soup.title and soup.title.string:
        candidates.append(soup.title.string)
    h1 = soup.find("h1")
    if h1:
        candidates.append(h1.get_text(" ", strip=True))
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        candidates.append(meta["content"])

    for text in candidates:
        m = VERSE_RE.search(text)
        if m:
            return tuple(int(x) for x in m.groups())
    return None


def html_path(out_dir: Path, verse_ref: tuple[int, int, int]) -> Path:
    book, chapter, verse = verse_ref
    return out_dir / f"{book}_{chapter}_{verse}.html"


def write_manifest_row(manifest: Path, row: dict[str, str]) -> None:
    exists = manifest.exists()
    with manifest.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["doc_id", "verse_ref", "url", "html_file"])
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def latest_manifest_doc(manifest: Path) -> int | None:
    if not manifest.exists():
        return None
    latest: int | None = None
    with manifest.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                doc_id = int(row["doc_id"])
            except (KeyError, TypeError, ValueError):
                continue
            latest = doc_id if latest is None else max(latest, doc_id)
    return latest


def stable_page_content(page, attempts: int = 10, pause: float = 1.0) -> str:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            page.wait_for_load_state("domcontentloaded", timeout=5000)
            return page.content()
        except Exception as exc:
            last_error = exc
            time.sleep(pause)
    raise RuntimeError(f"Could not read stable page content: {last_error}")


def goto_with_recovery(page, url: str, doc_id: int, attempts: int = 3) -> bool:
    for attempt in range(1, attempts + 1):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=120000)
            return True
        except (PlaywrightTimeoutError, PlaywrightError) as exc:
            print(f"doc{doc_id}: navigation failed on attempt {attempt}: {exc}", flush=True)
            try:
                page.goto("about:blank", wait_until="domcontentloaded", timeout=10000)
            except Exception:
                pass
            time.sleep(5)
    return False


def fetch_books(
    start_doc: int,
    end_doc: int,
    out_dir: Path,
    profile_dir: Path,
    delay: float,
    stop_after_book12_misses: int,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "books_3_to_12_manifest.csv"
    misses_after_book12 = 0
    seen_book12 = False

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        for doc_id in range(start_doc, end_doc + 1):
            url = BASE_URL.format(doc_id=doc_id)
            print(f"doc{doc_id}: loading", flush=True)
            if not goto_with_recovery(page, url, doc_id):
                continue

            for _ in range(90):
                title = page.title()
                if title and "Just a moment" not in title:
                    break
                time.sleep(1)

            html = stable_page_content(page)
            verse_ref = verse_ref_from_html(html)
            if not verse_ref:
                if seen_book12:
                    misses_after_book12 += 1
                    if misses_after_book12 >= stop_after_book12_misses:
                        print("Stopping after sustained non-verse pages following Book 12.", flush=True)
                        break
                time.sleep(delay)
                continue

            book, chapter, verse = verse_ref
            if book < 3:
                time.sleep(delay)
                continue
            if book > 12:
                print(f"Stopping at Verse {book}.{chapter}.{verse}.", flush=True)
                break
            if book == 12:
                seen_book12 = True
                misses_after_book12 = 0

            path = html_path(out_dir, verse_ref)
            if path.exists():
                print(f"doc{doc_id}: Verse {book}.{chapter}.{verse} already saved", flush=True)
            else:
                path.write_text(html, encoding="utf-8")
                print(f"doc{doc_id}: saved Verse {book}.{chapter}.{verse}", flush=True)
                write_manifest_row(
                    manifest,
                    {
                        "doc_id": str(doc_id),
                        "verse_ref": f"{book}.{chapter}.{verse}",
                        "url": url,
                        "html_file": path.name,
                    },
                )
            time.sleep(delay)

        ctx.close()


def iter_saved_html(out_dir: Path, start_book: int, end_book: int) -> list[Path]:
    paths: list[tuple[tuple[int, int, int], Path]] = []
    pattern = re.compile(r"(\d+)_(\d+)_(\d+)\.html$")
    for path in out_dir.glob("*_*_*.html"):
        m = pattern.match(path.name)
        if not m:
            continue
        ref = tuple(int(x) for x in m.groups())
        if start_book <= ref[0] <= end_book:
            paths.append((ref, path))
    return [path for _ref, path in sorted(paths)]


def build_excels(out_dir: Path, excel_dir: Path, start_book: int, end_book: int) -> None:
    excel_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[tuple[int, int], list[tuple[tuple[int, int, int], str]]] = {}

    for path in iter_saved_html(out_dir, start_book, end_book):
        ref = tuple(int(x) for x in path.stem.split("_"))
        verse_ref = f"{ref[0]}.{ref[1]}.{ref[2]}"
        try:
            text = extract_analysis_text(path.read_text(encoding="utf-8"), verse_ref)
        except Exception as exc:
            print(f"WARN {path.name}: {exc}", flush=True)
            text = f"verse {verse_ref}\n\n# PARSE ERROR: {exc}\n"
        grouped.setdefault((ref[0], ref[1]), []).append((ref, text))

    for (book, chapter), chunks in sorted(grouped.items()):
        raw_path = out_dir / f"book{book}_chapter_{chapter}_raw.txt"
        raw_text = "\n".join(text for _ref, text in sorted(chunks))
        raw_path.write_text(raw_text, encoding="utf-8")

        verses = parse_data(raw_text)
        linear_rows = build_linear_rows(verses)
        excel_path = excel_dir / f"bhagavata_book{book}_ch{chapter}_linear.xlsx"
        write_linear_excel(linear_rows, excel_path)
        print(
            f"Book {book} Chapter {chapter}: {len(verses)} verses, "
            f"{len(linear_rows)} linear rows -> {excel_path}",
            flush=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-doc", type=int, default=1241414)
    parser.add_argument("--end-doc", type=int, default=1265000)
    parser.add_argument("--out-dir", type=Path, default=Path("data/scraped"))
    parser.add_argument("--excel-dir", type=Path, default=Path("excel_sheets"))
    parser.add_argument("--profile-dir", type=Path, default=Path("data/scraped/.browser-profile"))
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--start-book", type=int, default=3)
    parser.add_argument("--end-book", type=int, default=12)
    parser.add_argument("--parse-only", action="store_true")
    parser.add_argument("--fetch-only", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--stop-after-book12-misses", type=int, default=50)
    args = parser.parse_args()

    if args.resume:
        latest_doc = latest_manifest_doc(args.out_dir / "books_3_to_12_manifest.csv")
        if latest_doc is not None and latest_doc >= args.start_doc:
            args.start_doc = latest_doc + 1
            print(f"Resuming from doc{args.start_doc}", flush=True)

    if not args.parse_only:
        fetch_books(
            start_doc=args.start_doc,
            end_doc=args.end_doc,
            out_dir=args.out_dir,
            profile_dir=args.profile_dir,
            delay=args.delay,
            stop_after_book12_misses=args.stop_after_book12_misses,
        )

    if not args.fetch_only:
        build_excels(args.out_dir, args.excel_dir, args.start_book, args.end_book)


if __name__ == "__main__":
    main()
