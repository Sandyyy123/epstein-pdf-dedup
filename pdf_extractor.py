"""
pdf_extractor.py — Layout-aware table extraction from ledger-format PDFs.
Tries digital text first (pdfplumber); falls back to OCR (Tesseract) for scanned pages.
"""
import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re
from pathlib import Path


def _clean_cell(text: str) -> str:
    """Normalize whitespace and strip control characters."""
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def extract_tables_pdfplumber(pdf_path: str) -> list[list[str]]:
    """Extract all table rows from a PDF using pdfplumber (digital text)."""
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        cleaned = [_clean_cell(cell) for cell in row]
                        if any(cleaned):  # skip fully empty rows
                            rows.append(cleaned)
            else:
                # Fallback: extract plain text lines if no table detected
                text = page.extract_text() or ""
                for line in text.split("\n"):
                    cols = [c.strip() for c in re.split(r"\s{2,}", line) if c.strip()]
                    if len(cols) >= 2:
                        rows.append(cols)
    return rows


def extract_tables_ocr(pdf_path: str, dpi: int = 300) -> list[list[str]]:
    """Extract table rows via OCR for scanned/image-only PDFs."""
    rows = []
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, config="--psm 6")
        for line in text.split("\n"):
            cols = [c.strip() for c in re.split(r"\s{2,}", line) if c.strip()]
            if len(cols) >= 2:
                rows.append(cols)
    doc.close()
    return rows


def is_scanned(pdf_path: str, sample_pages: int = 3) -> bool:
    """Heuristic: if first N pages have <50 chars of text, treat as scanned."""
    char_count = 0
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:sample_pages]:
            text = page.extract_text() or ""
            char_count += len(text.strip())
    return char_count < 50 * sample_pages


def extract_pdf(pdf_path: str) -> list[list[str]]:
    """Smart router: digital text or OCR depending on PDF type."""
    if is_scanned(pdf_path):
        return extract_tables_ocr(pdf_path)
    return extract_tables_pdfplumber(pdf_path)
