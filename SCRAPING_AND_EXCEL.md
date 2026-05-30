# Bhagavata Purana Morphology: Scrape → Text → Excel

This guide documents the workflow used for **Book 2, Chapter 1** on [wisdomlib.org](https://www.wisdomlib.org/hinduism/book/bhagavata-purana-sanskrit/d/doc1240138.html): fetch Sanskrit grammar analysis from the website, save it as plain text, then generate two Excel files (linear + structured).

---

## Overview

```
wisdomlib.org verse pages
        │
        ▼
  scrape_chapter.py          ← Playwright (live) or --from-html (saved files)
        │
        ▼
  data/scraped/chapter_N_raw.txt
        │
        ▼
  generate_sanskrit_excel.py
        │
        ├── bhagavata_book2_chN_linear.xlsx
        └── bhagavata_book2_chN_structured.xlsx
```

**Chapter 1 result (reference):**

| Item | Value |
|------|-------|
| Source | 39 HTML files (`2_1_1.html` … `2_1_39.html`) |
| Raw text | `data/scraped/chapter_1_raw.txt` |
| Verses | 39 (2.1.1 – 2.1.39) |
| Linear rows | 3,723 |
| Structured rows | 1,422 |
| Output | `bhagavata_book2_ch1_linear.xlsx`, `bhagavata_book2_ch1_structured.xlsx` |

---

## Prerequisites

From the project root (`~/Projects/webscrap`):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install openpyxl beautifulsoup4 lxml playwright
playwright install chromium   # only needed for live scraping
```

You also need **Google Chrome** installed on the system. The scraper launches Chrome via Playwright (`channel="chrome"`), not headless Chromium alone, because wisdomlib.org is protected by Cloudflare.

---

## Step 1 — Scrape morphology from wisdomlib.org

### Source URLs

Each verse has its own page. Book 2 Chapter 1 uses doc IDs **1003–1041**:

| Verse | URL pattern |
|-------|-------------|
| 2.1.1 | `https://www.wisdomlib.org/hinduism/book/bhagavata-purana-sanskrit/d/doc1241003.html` |
| 2.1.N | `doc1241002 + N` |
| 2.1.39 | `doc1241041.html` |

The scraper reads the **“Analysis of Sanskrit grammar”** section on each page and ignores everything after **“Other editions”**.

Verse-to-doc-ID mappings for other chapters are defined in `scrape_chapter.py` (`chapter_verse_urls()`). Add new chapters there before scraping.

### Option A — Live scrape (Playwright + Chrome)

Opens a real browser window, visits each verse URL, waits for Cloudflare, and saves HTML plus combined text:

```bash
cd ~/Projects/webscrap
.venv/bin/python scrape_chapter.py --chapter 1 --out-dir data/scraped
```

What it does:

1. Opens Chrome with a persistent profile at `data/scraped/.browser-profile`
2. For each verse, navigates to the page and waits for `Analysis of Sanskrit grammar`
3. Saves individual HTML: `data/scraped/2_1_1.html`, `2_1_2.html`, …
4. Writes combined morphology text: `data/scraped/chapter_1_raw.txt`

Useful flags (edit script or pass via defaults):

- `--chapter 1` — which chapter to scrape
- `--out-dir data/scraped` — output directory

**Note:** Live scraping is slow (~1.5 s delay between verses) and Cloudflare may block automated curl/headless requests. Chapter 1 was completed by saving HTML first, then re-parsing offline (Option B).

### Option B — Parse saved HTML (recommended, used for Chapter 1)

If you already have HTML files (from a browser session, manual save, or a partial scrape), skip the network step:

```bash
cd ~/Projects/webscrap
.venv/bin/python scrape_chapter.py --chapter 1 --from-html --out-dir data/scraped
```

This reads all `data/scraped/2_1_*.html` files, extracts morphology, and regenerates `data/scraped/chapter_1_raw.txt` without hitting the website.

### Option C — Paste text manually (when scraping is blocked)

If pages cannot be fetched automatically, copy the **Analysis of Sanskrit grammar** block from the browser and paste into a file (e.g. `chapter2.txt`). Then normalize headers if needed:

```bash
.venv/bin/python normalize_pasted_verse.py chapter2.txt data/scraped/chapter_2_raw.txt
```

`normalize_pasted_verse.py` converts `Verse 2.2.N` → `verse 2.2.N` and curly quotes → straight quotes. The Excel generator also accepts pasted format directly (case-insensitive `verse` headers and curly quotes).

---

## Step 2 — Verify the raw text format

The parser expects blocks like this (from `data/scraped/chapter_1_raw.txt`):

```
verse 2.1.1

Line 1: "śrīśuka uvāca "
śrīśuka* -
śrīśuka (noun, masculine)
[nominative single]
uvāca -
√vac (verb class 2)
[perfect active first single]
[perfect active third single]
Line 2: "varīyān eṣa te praśnaḥ kṛto lokahitaṃ nṛpa "
varīyān -
...
```

**Structure rules:**

| Line type | Example |
|-----------|---------|
| Verse header | `verse 2.1.1` (case-insensitive) |
| Verse line | `Line 1: "sanskrit text "` |
| Token | `śrīśuka* -` or `uvāca -` |
| Analysis | `śrīśuka (noun, masculine)` |
| Grammar tags | `[nominative single]` |
| Verb root | `√vac (verb class 2)` |
| Participle | `√naś -> naṣṭā (participle, feminine)` |
| Unresolved | `Cannot analyse xyz` |

Quick sanity check:

```bash
grep -c '^verse ' data/scraped/chapter_1_raw.txt   # should match verse count
```

---

## Step 3 — Generate Excel files

```bash
cd ~/Projects/webscrap
.venv/bin/python generate_sanskrit_excel.py \
  --input data/scraped/chapter_1_raw.txt \
  --output-prefix bhagavata_book2_ch1
```

Expected console output for Chapter 1:

```
Parsed 39 verses
Linear rows: 3723
Structured rows: 1422
Wrote: .../bhagavata_book2_ch1_linear.xlsx
Wrote: .../bhagavata_book2_ch1_structured.xlsx
```

### Output files

#### 1. `{prefix}_linear.xlsx`

Single sheet **“Linear Analysis”**, one row per text line — mirrors the website layout:

- Verse headers (blue background)
- Line headers (green background)
- Tokens in bold italic
- Analyses and grammar tags below each token

Good for human reading and side-by-side comparison with the source page.

#### 2. `{prefix}_structured.xlsx`

Two sheets:

**Morphology** — one row per analysis alternative:

| Column | Description |
|--------|-------------|
| Verse | e.g. `2.1.1` |
| Line # | Line number within verse |
| Verse Line | Full Sanskrit line text |
| Token | Surface form (e.g. `uvāca`) |
| Marked (*) | Whether token had `*` marker |
| Alt # | Rank when multiple analyses exist |
| Lemma / Root | Parsed lemma or `√root` |
| POS Category | noun, verb, participle, indeclinable, … |
| Grammar Tags | Semicolon-separated tags |
| Status | `resolved` or `unresolved` |

**LLM Training Pairs** — one row per token with instruction/input/target columns for fine-tuning.

---

## Full Chapter 1 command sequence

```bash
cd ~/Projects/webscrap

# 1. Scrape (or skip if HTML already in data/scraped/)
.venv/bin/python scrape_chapter.py --chapter 1 --out-dir data/scraped

# If HTML is already saved, use offline parse instead:
# .venv/bin/python scrape_chapter.py --chapter 1 --from-html --out-dir data/scraped

# 2. Generate Excel
.venv/bin/python generate_sanskrit_excel.py \
  --input data/scraped/chapter_1_raw.txt \
  --output-prefix bhagavata_book2_ch1
```

---

## Adding a new chapter

1. **Find doc IDs** — open the chapter index on wisdomlib.org and note the `doc124XXXX` ID for the first and last verse.
2. **Update `scrape_chapter.py`** — add a branch in `chapter_verse_urls()` with the correct verse range and doc ID formula.
3. **Scrape or paste** — run Option A, B, or C above.
4. **Generate Excel** — point `--input` at the raw txt and choose an `--output-prefix`.

Example for Chapter 2 (already configured in the scraper, verses 2.2.1–2.2.37 + colophon 2.2.38):

```bash
.venv/bin/python generate_sanskrit_excel.py \
  --input chapter2.txt \
  --output-prefix bhagavata_book2_ch2
```

---

## Project files

| File | Role |
|------|------|
| `scrape_chapter.py` | Fetch pages (Playwright) or parse saved HTML → raw txt |
| `generate_sanskrit_excel.py` | Raw txt → linear + structured Excel |
| `normalize_pasted_verse.py` | Normalize manually pasted text |
| `parse_snapshot.py` | Alternative: parse Cursor browser snapshot logs |
| `data/scraped/2_*_*.html` | Per-verse saved HTML |
| `data/scraped/chapter_N_raw.txt` | Combined morphology text |

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| “Just a moment…” / empty page | Cloudflare bot check | Use Playwright with system Chrome (`headless=False`); avoid curl/wget |
| Only 1 verse parsed | `Verse` vs `verse` or curly quotes | Run `normalize_pasted_verse.py`, or use current `generate_sanskrit_excel.py` (handles both) |
| `No analysis section` | HTML layout changed or wrong file | Re-save HTML from browser; check page has “Analysis of Sanskrit grammar” |
| Playwright Chromium download stuck | Large browser binary | Use `channel="chrome"` with installed Google Chrome instead |
| Missing tokens | Commentary mixed into paste | Edit txt to remove non-morphology lines before generating Excel |

---

## Data source

Morphology data comes from [Wisdom Library — Bhagavata Purana Sanskrit](https://www.wisdomlib.org/hinduism/book/bhagavata-purana-sanskrit/d/doc1240138.html). Respect the site’s terms of use and add delays between requests when live scraping.
