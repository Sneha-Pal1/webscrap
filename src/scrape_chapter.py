#!/usr/bin/env python3
"""Scrape wisdomlib verse morphology via Playwright (system Chrome)."""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE = "https://www.wisdomlib.org/hinduism/book/bhagavata-purana-sanskrit/d/doc124{doc_id}.html"

CHAPTERS = {
    1: (1003, 1041),  # verses 2.1.1 - 2.1.39
    2: (1043, 1079),  # approximate; verify from index
    3: (1083, 1108),  # verses 2.3.1 - 2.3.26
    4: (1110, 1135),  # verses 2.4.1 - 2.4.26
    5: (1137, 1179),  # verses 2.5.1 - 2.5.42 + colophon 2.5.43
    6: (1181, 1226),  # verses 2.6.1 - 2.6.45 + colophon 2.6.46
    7: (1228, 1281),  # verses 2.7.1 - 2.7.52 + colophon 2.7.53-54
    8: (1283, 1312),  # verses 2.8.1 - 2.8.29 + colophon 2.8.30
    9: (1314, 1359),  # verses 2.9.1 - 2.9.45 + colophon 2.9.46
    10: (1361, 1412),  # verses 2.10.1 - 2.10.51 + colophon 2.10.52
}


def chapter_verse_urls(chapter: int) -> list[tuple[str, str]]:
    if chapter == 1:
        return [
            (f"2.1.{n}", BASE.format(doc_id=1002 + n))
            for n in range(1, 40)
        ]
    if chapter == 2:
        return [
            (f"2.2.{n}", BASE.format(doc_id=1043 + n))
            for n in range(1, 38)
        ]
    if chapter == 3:
        return [
            (f"2.3.{n}", BASE.format(doc_id=1082 + n))
            for n in range(1, 27)
        ]
    if chapter == 4:
        return [
            (f"2.4.{n}", BASE.format(doc_id=1109 + n))
            for n in range(1, 27)
        ]
    if chapter == 5:
        return [
            (f"2.5.{n}", BASE.format(doc_id=1136 + n))
            for n in range(1, 44)
        ]
    if chapter == 6:
        return [
            (f"2.6.{n}", BASE.format(doc_id=1180 + n))
            for n in range(1, 47)
        ]
    if chapter == 7:
        return [
            (f"2.7.{n}", BASE.format(doc_id=1227 + n))
            for n in range(1, 55)
        ]
    if chapter == 8:
        return [
            (f"2.8.{n}", BASE.format(doc_id=1282 + n))
            for n in range(1, 31)
        ]
    if chapter == 9:
        return [
            (f"2.9.{n}", BASE.format(doc_id=1313 + n))
            for n in range(1, 47)
        ]
    if chapter == 10:
        return [
            (f"2.10.{n}", BASE.format(doc_id=1360 + n))
            for n in range(1, 53)
        ]
    raise ValueError(f"Chapter {chapter} mapping not configured")


def normalize_morph_line(line: str) -> str:
    line = re.sub(r"√\s+", "√", line)
    line = re.sub(r"from √\s+", "from √", line)
    return re.sub(r"\s+", " ", line).strip()


def extract_analysis_text(html: str, verse_ref: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    heading = soup.find(
        lambda tag: tag.name in ("h2", "h3", "h4")
        and tag.get_text(strip=True).lower().startswith("analysis of sanskrit grammar")
    )
    if not heading:
        raise ValueError(f"No analysis section for {verse_ref}")

    lines: list[str] = [f"verse {verse_ref}", ""]
    ul = heading.find_next("ul")
    if not ul:
        raise ValueError(f"No analysis list for {verse_ref}")

    for el in ul.find_all("li", recursive=True):
        if el.find_parent("li") is not el.parent and el.parent.name == "li":
            continue
        classes = el.get("class") or []
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        if "heading" in classes:
            m = re.search(r'Line \d+: “(.+?)”', text)
            if m:
                line_num = re.match(r"Line (\d+):", text)
                line_text = re.sub(r"\s+", " ", m.group(1)).strip()
                lines.append(f'Line {line_num.group(1)}: "{line_text} "')
            continue
        if "segment" in classes and text.endswith("-"):
            token = normalize_morph_line(text)
            lines.append(token.replace(" * -", "* -"))
            continue
        if "list" in classes:
            for row in el.select(".words-group"):
                lemma_part = row.select_one(".col-5")
                grammar_part = row.select_one(".deriv-list")
                if not lemma_part:
                    continue
                lemma_text = normalize_morph_line(lemma_part.get_text(" ", strip=True))
                grammar_text = grammar_part.get_text(" ", strip=True) if grammar_part else ""
                if lemma_text.lower().startswith("cannot analyse"):
                    lines.append(lemma_text)
                    continue
                lines.append(lemma_text)
                if grammar_text:
                    for g in re.findall(r"\[[^\]]+\]", grammar_text):
                        lines.append(normalize_morph_line(g))
            if text.lower().startswith("cannot analyse"):
                lines.append(normalize_morph_line(text))
            continue

    # Stop at Other editions heading
    cleaned: list[str] = []
    for line in lines:
        if line.lower().startswith("other editions"):
            break
        cleaned.append(line)
    return "\n".join(cleaned) + "\n"


def split_analysis_line(text: str) -> list[str]:
    """Split list items that bundle multiple analyses onto one line."""
    parts = re.split(r"(?=√\s*\S+\s+\(verb|\√\S+ ->)", text)
    if len(parts) <= 1:
        return [text]
    out: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Separate trailing bracket groups after lemma lines
        m = re.match(
            r"^(.+?\((?:noun|verb|participle|indeclinable|pronoun|Preverb|adverb)[^)]*\))\s*(.*)$",
            part,
            re.I,
        )
        if m:
            out.append(m.group(1).strip())
            rest = m.group(2).strip()
            if rest:
                for g in re.findall(r"\[[^\]]+\]", rest):
                    out.append(g)
                for sub in re.split(r"(?=√\s*\S+|\√\S+ ->)", rest):
                    sub = sub.strip()
                    if sub and not sub.startswith("["):
                        out.extend(split_analysis_line(sub))
        else:
            out.append(part)
    return out


def scrape_chapter(chapter: int, out_dir: Path, delay: float = 1.5) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    combined = out_dir / f"chapter_{chapter}_raw.txt"
    urls = chapter_verse_urls(chapter)
    chunks: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(out_dir / ".browser-profile"),
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        for i, (verse_ref, url) in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {verse_ref} ...", flush=True)
            success = False
            for attempt in range(1, 4):
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    success = True
                    break
                except Exception as exc:
                    print(f"  WARN: Navigation failed on attempt {attempt}: {exc}", flush=True)
                    time.sleep(5)
            if not success:
                print(f"  ERROR: Failed to load {url} after 3 attempts", flush=True)
                chunks.append(f"verse {verse_ref}\n\n# SCRAPE ERROR: Failed to load page\n")
                continue

            for _ in range(45):
                title = page.title()
                if title and "Verse" in title and "Just a moment" not in title:
                    break
                time.sleep(1)
            
            try:
                page.wait_for_selector("text=Analysis of Sanskrit grammar", timeout=60000)
            except Exception as exc:
                print(f"  WARN: wait_for_selector failed: {exc}", flush=True)

            html = page.content()
            try:
                text = extract_analysis_text(html, verse_ref)
                chunks.append(text)
                (out_dir / f"{verse_ref.replace('.', '_')}.html").write_text(html, encoding="utf-8")
            except Exception as exc:
                print(f"  WARN: {exc}", flush=True)
                chunks.append(f"verse {verse_ref}\n\n# SCRAPE ERROR: {exc}\n")
            time.sleep(delay)

        ctx.close()

    combined.write_text("\n".join(chunks), encoding="utf-8")
    return combined


def parse_html_dir(html_dir: Path, chapter: int) -> Path:
    combined = html_dir / f"chapter_{chapter}_raw.txt"
    chunks: list[str] = []
    pattern = re.compile(r"2_(\d+)_(\d+)\.html$")
    files = sorted(html_dir.glob("2_*.html"), key=lambda p: p.name)
    for path in files:
        m = pattern.match(path.name)
        if not m:
            continue
        book, verse_num = m.groups()
        if book != str(chapter):
            continue
        verse_ref = f"2.{book}.{verse_num}"
        html = path.read_text(encoding="utf-8")
        try:
            chunks.append(extract_analysis_text(html, verse_ref))
        except Exception as exc:
            chunks.append(f"verse {verse_ref}\n\n# PARSE ERROR: {exc}\n")
    combined.write_text("\n".join(chunks), encoding="utf-8")
    return combined


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", type=int, default=1)
    parser.add_argument("--out-dir", type=Path, default=Path("data/scraped"))
    parser.add_argument(
        "--from-html",
        action="store_true",
        help="Parse saved HTML files instead of live scraping",
    )
    args = parser.parse_args()
    if args.from_html:
        path = parse_html_dir(args.out_dir, args.chapter)
    else:
        path = scrape_chapter(args.chapter, args.out_dir)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
