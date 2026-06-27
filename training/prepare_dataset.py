#!/usr/bin/env python3
"""Convert Bhagavata JSON chapter files into SFT training data."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

INSTRUCTION_MORPH = (
    "Given a Sanskrit verse line and a token, list all valid morphological analyses "
    "including lemma, part of speech, and grammatical tags."
)
INSTRUCTION_TRANSLATE = "Translate this Sanskrit verse to English."


def format_analyses(analyses: list[dict]) -> str:
    lines = []
    for analysis in analyses:
        lemma = analysis.get("base_word_", "")
        pos = analysis.get("lexical_category") or analysis.get("lex_catg", "")
        tags = (
            analysis.get("morphological_and_syntactical_analysis")
            or analysis.get("morph_synt_analysis", "")
        )
        lines.append(f"{lemma} ({pos}) {tags}")
    return "\n".join(lines)


def iter_morphology_rows(json_dir: Path):
    for path in sorted(json_dir.glob("bhagavata_*.json")):
        chapter = path.stem
        for verse in json.loads(path.read_text(encoding="utf-8")):
            line = verse.get("english_devnagari") or verse.get("devanagari", "")
            verse_num = verse.get("verse", "")
            for item in verse.get("verse_Syn", []):
                if not isinstance(item, dict) or "analyses" not in item:
                    continue
                yield {
                    "task": "morphology",
                    "chapter": chapter,
                    "verse": verse_num,
                    "instruction": INSTRUCTION_MORPH,
                    "input": f"Verse line: {line}\nToken: {item['word']}",
                    "output": format_analyses(item["analyses"]),
                }


def iter_translation_rows(json_dir: Path):
    for path in sorted(json_dir.glob("bhagavata_*.json")):
        chapter = path.stem
        for verse in json.loads(path.read_text(encoding="utf-8")):
            text = verse.get("english_devnagari") or verse.get("devanagari", "")
            translation = (verse.get("translation") or "").strip()
            if not text or not translation:
                continue
            yield {
                "task": "translation",
                "chapter": chapter,
                "verse": verse.get("verse", ""),
                "instruction": INSTRUCTION_TRANSLATE,
                "input": text,
                "output": translation,
            }


def split_by_chapter(rows: list[dict], val_ratio: float, seed: int):
    chapters = sorted({row["chapter"] for row in rows})
    rng = random.Random(seed)
    rng.shuffle(chapters)
    val_count = max(1, int(len(chapters) * val_ratio))
    val_chapters = set(chapters[:val_count])
    train = [row for row in rows if row["chapter"] not in val_chapters]
    val = [row for row in rows if row["chapter"] in val_chapters]
    return train, val


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-dir", type=Path, default=Path("data/json"))
    parser.add_argument("--out-dir", type=Path, default=Path("training/data"))
    parser.add_argument(
        "--task",
        choices=("morphology", "translation"),
        default="morphology",
    )
    parser.add_argument("--max-rows", type=int, default=0, help="0 = use all rows")
    parser.add_argument("--val-ratio", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.task == "morphology":
        rows = list(iter_morphology_rows(args.json_dir))
    else:
        rows = list(iter_translation_rows(args.json_dir))

    if not rows:
        raise SystemExit(f"No training rows found in {args.json_dir}")

    rng = random.Random(args.seed)
    rng.shuffle(rows)
    if args.max_rows > 0:
        rows = rows[: args.max_rows]

    train, val = split_by_chapter(rows, args.val_ratio, args.seed)
    prefix = f"{args.task}"
    if args.max_rows > 0:
        prefix += f"_n{len(rows)}"

    write_jsonl(args.out_dir / f"{prefix}_train.jsonl", train)
    write_jsonl(args.out_dir / f"{prefix}_val.jsonl", val)

    print(f"task={args.task}")
    print(f"rows={len(rows)} train={len(train)} val={len(val)}")
    print(f"wrote {args.out_dir / f'{prefix}_train.jsonl'}")
    print(f"wrote {args.out_dir / f'{prefix}_val.jsonl'}")


if __name__ == "__main__":
    main()
