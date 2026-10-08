# Link Extractor

A small Python script that reads a **saved HTML page** (a local file) and lists
every link found in it. Built for TechAbout task 1 (ZR-26-00754).

## What it does

Given a saved `.html` file, it reports, in document order, every:

- `<a href>` anchor link, with its visible link text
- `<link href>` stylesheet / icon reference
- `<img>`, `<script>`, `<iframe>`, `<video>`, `<audio>`, `<source>`,
  `<track>`, `<embed>`, `<object>` `src` / `data` references

Each entry shows the tag, the attribute, the original URL, the resolved URL
(when `--base` is given), the link text, and a classification:
`internal`, `external`, `relative`, `absolute`, or `skipped` (empty, `#`
fragments, `javascript:` / `mailto:` / `tel:` / `data:` links).

The script **never fetches anything from the internet**; it only parses the
file you hand it. No forms are submitted, no pages are crawled.

## Usage

```bash
python link_extractor.py page.html
python link_extractor.py page.html --base https://example.com
python link_extractor.py page.html --format csv --output links.csv
python link_extractor.py page.html --format json --output links.json
```

Output formats: `text` (default), `csv`, `json`.

## Sample output

`sample/` contains a saved copy of the public TechAbout homepage
(`techabout-homepage.html`, downloaded 2026-10-08) and the extractor output
in all three formats:

- `output.txt`: 186 links found (168 kept, 18 skipped)
- `output.csv`: spreadsheet-friendly table
- `output.json`: machine-readable result

## Tests

```bash
python test_link_extractor.py
```

12 tests covering tag coverage, document order, link-text collection,
relative-URL resolution, internal/external classification, skipped kinds,
and all three output formats.

## Files

| File | Purpose |
|---|---|
| `link_extractor.py` | The script |
| `test_link_extractor.py` | 12 unit tests |
| `sample/techabout-homepage.html` | Saved public page used for the demo |
| `sample/output.txt` / `.csv` / `.json` | Sample output in three formats |
