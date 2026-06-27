# Bhagavata Purana Morphology Dataset & Toolkit

A reproducible pipeline for building a **word-level Sanskrit morphology dataset** from the
[Bhagavata Purana](https://en.wikipedia.org/wiki/Bhagavata_Purana), together with the scraping,
processing, and fine-tuning tooling used to produce it.

For every verse the dataset captures the Devanāgarī text, IAST transliteration, English
translation, commentary (purport), and — most importantly — a **per-word grammatical analysis**
(lemma/root, lexical category, and morphological tags). The morphology is sourced from the
"Analysis of Sanskrit grammar" sections on [wisdomlib.org](https://www.wisdomlib.org/hinduism/book/bhagavata-purana-sanskrit).

> **Status:** ~300 chapters across Books 2–12, **12,679 verses** parsed into JSON and Excel.

---

## Why this exists

High-quality, machine-readable Sanskrit morphology data is scarce. This project turns scattered
HTML grammar tables into a clean, structured corpus suitable for:

- Training/evaluating **Sanskrit morphological analyzers** (verse line + token → lemma/POS/tags)
- Building lookup tools and study aids
- Linguistics and digital-humanities research on the Bhagavata Purana

A ready-to-train LoRA fine-tuning setup is included under [`training/`](training/).

---

## Repository layout

```
.
├── src/                 # Core pipeline (run from the repo root)
│   ├── scrape_chapter.py            # Fetch verse pages (Playwright) or parse saved HTML → raw txt
│   ├── scrape_books_3_to_12.py      # Bulk scraper for Books 3–12
│   ├── generate_sanskrit_excel.py   # raw txt → linear + structured Excel
│   ├── generate_chapter_json.py     # saved HTML → per-chapter JSON dataset
│   ├── normalize_pasted_verse.py    # Normalize manually pasted morphology text
│   └── ...                          # English-translation fetch/parse helpers
│
├── data/
│   ├── scraped/         # Raw scraped HTML + intermediate txt (HTML is gitignored)
│   ├── json/            # 📦 The dataset: one JSON file per chapter
│   └── excel/           # Linear + structured spreadsheets per chapter
│
├── training/            # LoRA fine-tuning (data prep, train, inference, Colab notebook)
├── examples/            # Small sample outputs (example.json, sample.xlsx, ch1_example.json)
├── tools/dev/           # One-off inspection / sanity-check scripts (not part of the pipeline)
├── docs/                # Extended docs and supplementary reports
│   └── SCRAPING_AND_EXCEL.md        # Detailed scrape → text → Excel walkthrough
├── requirements.txt
└── LICENSE              # Apache-2.0 (code). See "Data & licensing" for the dataset.
```

---

## Dataset

Each chapter is a JSON array of verse objects: [`data/json/bhagavata_book{B}_ch{C}.json`](data/json).
A trimmed example record:

```jsonc
{
  "verse": "1",
  "devanagari": "श्रीशुक उवाच । वरीयान् एष ते प्रश्नः ...",
  "english_devnagari": "śrīśuka uvāca varīyān eṣa te praśnaḥ ...",  // IAST transliteration
  "translation": "Śrī Śuka said: Oh king! ...",
  "purport": "Footnote [1]: para—(i) Within the range of senses ...",
  "verse_Syn": [
    {
      "word": "uvāca",
      "analyses": [
        {
          "base_word_": "√ vac",
          "lexical_category": "verb class 2",
          "morphological_and_syntactical_analysis": "[perfect active first single], [perfect active third single]"
        }
      ]
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `verse` | Verse number within the chapter |
| `devanagari` | Original Devanāgarī text |
| `english_devnagari` | IAST transliteration |
| `translation` | English translation |
| `purport` | Commentary / footnotes |
| `verse_Syn` | List of tokens, each with one or more `analyses` (lemma/root, lexical category, morphological tags) |

The same content is also exported to Excel in [`data/excel/`](data/excel): a human-readable
**linear** sheet (mirrors the website layout) and a **structured** sheet (one row per analysis,
plus an LLM-training-pairs sheet). See [docs/SCRAPING_AND_EXCEL.md](docs/SCRAPING_AND_EXCEL.md)
for column-by-column details.

**Coverage:** Books 2 (10 ch), 3 (33), 4 (31), 5 (24), 6 (19), 7 (11), 8 (14), 9 (24), 10 (90),
11 (31), 12 (13).

---

## Installation

```bash
git clone <repo-url>
cd webscrap

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Only needed for *live* scraping (offline parsing of saved HTML does not need this):
playwright install chromium
```

Live scraping also requires **Google Chrome** installed system-wide — wisdomlib.org is behind
Cloudflare, so the scraper drives real Chrome via Playwright (`channel="chrome"`) rather than
headless Chromium.

> All commands below assume you run them **from the repo root** so the default
> `data/...` paths resolve correctly.

---

## Usage

### 1. Generate Excel from morphology text

```bash
python src/generate_sanskrit_excel.py \
  --input data/scraped/chapter_1_raw.txt \
  --output-prefix bhagavata_book2_ch1
# → bhagavata_book2_ch1_linear.xlsx, bhagavata_book2_ch1_structured.xlsx
```

### 2. Build the JSON dataset from saved HTML

```bash
python src/generate_chapter_json.py --book 2 --chapter 1
# → data/json/bhagavata_book2_ch1.json
```

### 3. Scrape new chapters

```bash
# Live scrape a single chapter (opens Chrome)
python src/scrape_chapter.py --chapter 1 --out-dir data/scraped

# Re-parse already-saved HTML offline (no network)
python src/scrape_chapter.py --chapter 1 --from-html --out-dir data/scraped

# Bulk scrape Books 3–12
python src/scrape_books_3_to_12.py --excel-dir data/excel
```

The full scrape → text → Excel walkthrough, including how to add a new chapter and troubleshoot
Cloudflare blocks, lives in **[docs/SCRAPING_AND_EXCEL.md](docs/SCRAPING_AND_EXCEL.md)**.

### 4. Fine-tune a model on the morphology task

```bash
# Prepare train/val JSONL from the JSON dataset
python training/prepare_dataset.py --task morphology --max-rows 8000

# Train (needs an NVIDIA GPU) or use the Colab notebook
pip install -r training/requirements-training.txt
python training/finetune.py
python training/test_inference.py
```

See [training/README.md](training/README.md) for the one-click free-GPU Colab path.

---

## Licensing

This repository has **two different licensing regimes** — they are not the same, and the
distinction matters:

### Code — Apache License 2.0

All **source code** (everything under `src/`, `tools/`, `training/`, and the build/config files)
is licensed under the [Apache License 2.0](LICENSE). You may use, modify, and redistribute the
code freely under those terms.

### Data — third-party content, NOT licensed by this project

The contents of `data/json/`, `data/excel/`, and the bundled examples are **derived from
third-party material** and are **not** covered by the Apache license above. See
[DATA_LICENSE.md](DATA_LICENSE.md) and [NOTICE](NOTICE) for the full statement. In short:

- The Devanāgarī mūla text is in the **public domain**.
- The **English translation and purport (commentary)** fields are drawn from a **published,
  copyrighted edition** (G. V. Tagare et al., *The Bhāgavata Purāṇa*, AITM series,
  **Motilal Banarsidass**), as hosted on [wisdomlib.org](https://www.wisdomlib.org). The
  maintainers of this repository **claim no ownership** of that text and **grant no license** to
  it — we cannot, because we do not hold the rights.
- The dataset is shared **only for non-commercial research and educational use**, with attribution
  to the original publishers and to Wisdom Library as the upstream source.

> **Disclaimer.** This project is an independent, unofficial work. It is **not affiliated with,
> authorized, or endorsed by** Wisdom Library, Motilal Banarsidass, or any rights holder. The data
> is provided "as is," without warranty, and you are responsible for ensuring your own use complies
> with applicable copyright law.

> **Takedown / rights holders.** If you are a rights holder (or their representative) and believe
> any content here infringes your copyright, please open an issue or contact the maintainer and the
> material will be **removed promptly**. See [NOTICE](NOTICE) for contact details.

---

## Contributing

Contributions — new chapters, parsing fixes, schema improvements — are welcome. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the workflow and conventions.
