"""
main.py — Entry point: process a folder of PDFs, deduplicate, export to Excel.

Usage:
    python main.py --input ./pdfs --output ./results/unique_records.xlsx --threshold 90
"""
import argparse
import sys
from pathlib import Path
from tqdm import tqdm
import pandas as pd

from pdf_extractor import extract_pdf
from deduplicator import deduplicate


def main():
    parser = argparse.ArgumentParser(description="PDF ledger deduplication pipeline")
    parser.add_argument("--input", required=True, help="Folder containing PDF files")
    parser.add_argument("--output", default="unique_records.xlsx", help="Output Excel path")
    parser.add_argument("--threshold", type=float, default=90.0,
                        help="Fuzzy similarity threshold 0-100 (default: 90)")
    args = parser.parse_args()

    pdf_dir = Path(args.input)
    if not pdf_dir.exists():
        print(f"ERROR: Input folder not found: {pdf_dir}")
        sys.exit(1)

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print("ERROR: No PDF files found in input folder.")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF files. Extracting tables...")
    all_rows: list[list[str]] = []

    for pdf_path in tqdm(pdf_files, unit="pdf"):
        try:
            rows = extract_pdf(str(pdf_path))
            all_rows.extend(rows)
        except Exception as e:
            print(f"  WARN: Failed to parse {pdf_path.name}: {e}")

    print(f"Total rows extracted (pre-dedup): {len(all_rows)}")

    df_unique = deduplicate(all_rows, threshold=args.threshold)
    print(f"Unique records after deduplication: {len(df_unique)}")
    print(f"Duplicate rows removed: {len(all_rows) - len(df_unique)}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_unique.to_excel(output_path, index=False)
    print(f"\nOutput saved: {output_path}")


if __name__ == "__main__":
    main()
