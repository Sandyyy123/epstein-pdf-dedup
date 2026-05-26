"""
deduplicator.py — Content-level deduplication using RapidFuzz fuzzy matching.
Designed for ledger-format records where structural repetition (headers, page numbers)
must be stripped before similarity comparison.
"""
import pandas as pd
from rapidfuzz import fuzz
from collections import defaultdict


HEADER_KEYWORDS = {
    "name", "date", "address", "phone", "entry", "record", "no.", "#",
    "page", "total", "header", "item", "description", "amount"
}


def row_to_string(row: list[str]) -> str:
    """Flatten a row to a single comparable string."""
    return " | ".join(str(c).strip().lower() for c in row if str(c).strip())


def is_header_row(row: list[str]) -> bool:
    """Detect structural header/footer rows to exclude from dedup."""
    text = " ".join(str(c).lower() for c in row)
    matches = sum(1 for kw in HEADER_KEYWORDS if kw in text)
    return matches >= 2


def deduplicate(rows: list[list[str]], threshold: float = 90.0) -> pd.DataFrame:
    """
    Remove duplicate rows using fuzzy token_sort_ratio.
    threshold: 0-100; rows scoring >= threshold against an already-seen row are dropped.
    Returns a DataFrame of unique rows.
    """
    # Filter header/footer rows first
    data_rows = [r for r in rows if not is_header_row(r)]

    # Pad rows to uniform column count
    max_cols = max((len(r) for r in data_rows), default=1)
    padded = [r + [""] * (max_cols - len(r)) for r in data_rows]

    seen_strings: list[str] = []
    unique_rows: list[list[str]] = []

    for row in padded:
        candidate = row_to_string(row)
        if not candidate:
            continue
        is_dup = False
        for seen in seen_strings:
            score = fuzz.token_sort_ratio(candidate, seen)
            if score >= threshold:
                is_dup = True
                break
        if not is_dup:
            seen_strings.append(candidate)
            unique_rows.append(row)

    col_names = [f"col_{i+1}" for i in range(max_cols)]
    return pd.DataFrame(unique_rows, columns=col_names)
