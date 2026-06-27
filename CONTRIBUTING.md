# Contributing

Thanks for your interest in improving the Bhagavata Purana Morphology Dataset & Toolkit!

## Getting set up

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # only for live scraping
```

Always run scripts **from the repo root** so the default `data/...` paths resolve.

## Project conventions

- **`src/`** holds the core, supported pipeline. Keep these scripts runnable from the repo root.
  `scrape_books_3_to_12.py` imports `scrape_chapter` and `generate_sanskrit_excel` as siblings, so
  the core scripts must stay in the same flat directory.
- **`tools/dev/`** is for throwaway inspection / sanity-check helpers. Don't add pipeline logic here.
- **`data/json/`** is the canonical dataset; **`data/excel/`** is the spreadsheet export.
- Raw scraped HTML under `data/scraped/` is gitignored — it is a regenerable cache, not source.

## Adding a new chapter

1. Find the wisdomlib.org doc IDs for the chapter's first and last verse.
2. Add the verse range / doc-ID formula in `chapter_verse_urls()` in `src/scrape_chapter.py`.
3. Scrape (or paste) the morphology — see [docs/SCRAPING_AND_EXCEL.md](docs/SCRAPING_AND_EXCEL.md).
4. Generate outputs:
   ```bash
   python src/generate_chapter_json.py --book B --chapter C
   python src/generate_sanskrit_excel.py --input data/scraped/chapter_C_raw.txt \
       --output-prefix bhagavata_bookB_chC
   ```
5. Verify the JSON parses and the verse count matches the source page.

## Pull requests

- Keep changes focused; describe what was scraped/changed and how you verified it.
- Run `python -m py_compile src/*.py` before submitting.
- For dataset additions, note the source URLs in the PR description.

## Data source, licensing & ethics

The data comes from [Wisdom Library](https://www.wisdomlib.org). Note that the **data and the code
are licensed differently**: code is Apache-2.0 ([LICENSE](LICENSE)), but the dataset's
`translation`/`purport` fields are third-party copyrighted content and are **not** open-licensed —
see [DATA_LICENSE.md](DATA_LICENSE.md) and [NOTICE](NOTICE).

When contributing:

- Scrape at modest request rates with the provided delays.
- Preserve attribution to Wisdom Library (upstream) and to the original publisher
  (Motilal Banarsidass) for translation/commentary.
- Do not relabel or relicense the dataset as freely reusable or public domain.
- Keep additions within non-commercial research/educational scope.
