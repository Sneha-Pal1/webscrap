#!/usr/bin/env python3
"""Normalize pasted wisdomlib morphology text into parser format."""

import re
import sys
from pathlib import Path

VERSE_HEADER = re.compile(r"^Verse\s+(2\.\d+\.\d+)\s*$", re.I)
LINE_RE = re.compile(r'^Line\s+(\d+):\s+[""](.+?)[""]\s*$')


def normalize(text: str) -> str:
    out: list[str] = []
    current_verse = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if current_verse and out and out[-1] != "":
                out.append("")
            continue

        m = VERSE_HEADER.match(line)
        if m:
            if current_verse:
                out.append("")
            current_verse = m.group(1)
            out.append(f"verse {current_verse}")
            out.append("")
            continue

        if line.startswith("Line "):
            m2 = LINE_RE.match(line) or re.match(r'^Line\s+(\d+):\s+[""](.+)[""]\s*$', line)
            if m2:
                out.append(f'Line {m2.group(1)}: "{m2.group(2).strip()} "')
            else:
                out.append(line)
            continue

        out.append(line)

    return "\n".join(out).strip() + "\n"


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/chapter_2_pasted.txt")
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/scraped/chapter_2_raw.txt")
    text = src.read_text(encoding="utf-8") if src.exists() else sys.stdin.read()
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(normalize(text), encoding="utf-8")
    print(f"Wrote {dst} ({dst.read_text().count('verse 2.2.')} verses)")


if __name__ == "__main__":
    main()
