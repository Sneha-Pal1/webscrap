#!/usr/bin/env python3
"""Parse wisdomlib browser snapshot logs into morphology text format."""

import re
from pathlib import Path

LINE_RE = re.compile(r'^Line \d+:')
TOKEN_RE = re.compile(r".+\s-\s*$")
CANNOT_RE = re.compile(r"^Cannot analyse", re.I)


def parse_snapshot_file(path: Path) -> tuple[str, list[str]]:
    text = path.read_text(encoding="utf-8")
    verse_ref = None
    m = re.search(r"name: Verse (2\.\d+\.\d+)", text)
    if m:
        verse_ref = m.group(1)

    in_analysis = False
    rows: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if "Analysis of Sanskrit grammar" in line:
            in_analysis = True
            continue
        if not in_analysis:
            continue
        if "Other editions" in line:
            break
        if not line.startswith("name:"):
            continue
        content = line.split("name:", 1)[1].strip().strip('"')
        if not content or content.startswith("Note:"):
            continue
        rows.extend(normalize_snapshot_row(content))

    return verse_ref or "unknown", rows


def normalize_snapshot_row(content: str) -> list[str]:
    content = re.sub(r"\s+", " ", content).strip()
    if LINE_RE.match(content):
        return [content]
    if TOKEN_RE.match(content) or content.endswith(" -"):
        return [content.replace(" * -", "* -").replace(" -", " -")]
    if CANNOT_RE.match(content):
        return [content]

    # "lemma (pos) [grammar]" combined
    m = re.match(r"^(.+?\([^)]+\))\s*(\[.+\])$", content)
    if m:
        return [m.group(1).strip(), m.group(2).strip()]

    # Multiple √ verb analyses on one line
    if "√" in content:
        out: list[str] = []
        parts = re.split(r"(?=√\s*\S+)", content)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            subparts = re.split(r"(?<=\])\s*(?=√)", part)
            for sp in subparts:
                sp = sp.strip()
                if not sp:
                    continue
                m2 = re.match(r"^(.+?\([^)]+\))\s*(\[.+\])$", sp)
                if m2:
                    out.append(m2.group(1).strip())
                    for g in re.findall(r"\[[^\]]+\]", m2.group(2)):
                        out.append(g)
                elif sp.startswith("["):
                    out.extend(re.findall(r"\[[^\]]+\]", sp))
                else:
                    out.append(sp)
        return out

    if content.startswith("["):
        return re.findall(r"\[[^\]]+\]", content)

    return [content]


def snapshot_dir_to_text(snapshot_dir: Path, out_file: Path) -> None:
    chunks: list[str] = []
    for path in sorted(snapshot_dir.glob("snapshot-*.log")):
        verse_ref, rows = parse_snapshot_file(path)
        if not rows:
            continue
        chunks.append(f"verse {verse_ref}\n")
        chunks.extend(rows)
        chunks.append("")
    out_file.write_text("\n".join(chunks), encoding="utf-8")


if __name__ == "__main__":
    import sys

    src = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/archilect/.cursor/browser-logs")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "data/scraped/chapter_1_raw.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    snapshot_dir_to_text(src, out)
    print(f"Wrote {out}")
