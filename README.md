# epstein-pdf-dedup

Layout-aware PDF extraction and content-level fuzzy deduplication pipeline.

Built for ledger-format PDFs with 10-entry-per-page tabular structures where
standard file-level deduplication (MD5 hashing) fails because the same records
repeat across many files with identical layout but different page positions.

## Architecture

```
PDF Folder (2,000 files)
        |
        v
pdf_extractor.py
  - pdfplumber  (digital text PDFs)
  - Tesseract OCR  (scanned/image PDFs, auto-detected)
        |
        v
All rows (raw, ~20,000+ rows)
        |
        v
deduplicator.py
  - Strip header/footer rows
  - RapidFuzz token_sort_ratio (default threshold: 90)
  - Return unique DataFrame
        |
        v
unique_records.xlsx  (~200 unique records)
```

## Setup

```bash
pip install -r requirements.txt
# For OCR support, also install Tesseract:
# Ubuntu: sudo apt install tesseract-ocr
# macOS:  brew install tesseract
```

## Usage

```bash
python main.py --input ./pdfs --output ./results/unique_records.xlsx --threshold 90
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | required | Folder containing PDF files |
| `--output` | `unique_records.xlsx` | Output Excel path |
| `--threshold` | `90` | Fuzzy similarity 0-100; lower = more aggressive dedup |

## How deduplication works

Each extracted row is flattened to a normalized string.
RapidFuzz `token_sort_ratio` compares every candidate against all previously
seen unique rows. If similarity >= threshold, the row is classified as a duplicate.

`token_sort_ratio` handles common OCR artifacts (word reordering, minor character
substitutions) that would fool exact matching.

## Adjusting the threshold

- `95+` - conservative; only near-identical rows removed
- `90` - recommended default for ledger data with consistent formatting
- `80-85` - aggressive; use if OCR quality is poor

## Output

Excel file with one row per unique record, columns named `col_1`, `col_2`, etc.
(rename to match your schema once column count is confirmed).
