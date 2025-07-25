# -*- coding: utf-8 -*-
"""
ner_extractor_spacy.py

Extracts structured fields from loan agreements using a spaCy NER model trained in Doccano.
Supports PDF (native or OCR) and DOCX input formats with a Tkinter GUI for testing.
"""

import os
import re
import spacy
import pdfplumber
import pytesseract
from docx import Document
from pdf2image import convert_from_path
from tkinter import Tk, filedialog

# === CONFIGURATION ===
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler\Library\bin"
SPACY_MODEL_PATH = r"./scanner/trained_transfer_model"

# === Load spaCy NER Model ===
print(f"Loading spaCy NER model from '{SPACY_MODEL_PATH}'...")
nlp = spacy.load(SPACY_MODEL_PATH)
print("NER model loaded. Labels:", nlp.get_pipe('ner').labels)

# === Text Extraction ===
def extract_text_from_pdf(path: str) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or '' for page in pdf.pages)

def ocr_pdf_to_text(path: str) -> str:
    images = convert_from_path(path, dpi=300, poppler_path=POPPLER_PATH)
    return "\n".join(pytesseract.image_to_string(img, config='--psm 6') for img in images)

def extract_text_from_docx(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

# === Trimming & Normalization ===
def trim_entity_text(label: str, text: str) -> str:
    text = text.strip()
    if label.lower() in {"lender", "borrower"}:
        for sep in [",", " (", " and ", ";", "\n"]:
            if sep in text:
                return text.split(sep)[0].strip()
    return text

def normalize_value(raw: str, label: str) -> str:
    text = raw.strip()
    lbl = label.lower()

    if "date" in lbl:
        # Match DD Month YYYY (e.g., "04 November 2009")
        m = re.search(r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})", text)
        if m:
            day, month_str, year = m.groups()
            month_map = {
                "January": 1, "February": 2, "March": 3, "April": 4,
                "May": 5, "June": 6, "July": 7, "August": 8,
                "September": 9, "October": 10, "November": 11, "December": 12
            }
            month = month_map[month_str]
            return f"{int(year):04d}/{month:02d}/{int(day):02d}"

        # Fallback: 31/12/2020 or 2020-12-31
        m2 = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", text)
        if m2:
            day, month, year = m2.groups()
            if len(year) == 2:
                year = "20" + year
            return f"{int(day):02d}/{int(month):02d}/{int(year):04d}"

        return text

    elif "rate" in lbl:
        m = re.search(r"\d+(\.\d+)?%", text)
        return m.group(0) if m else text

    elif "principal" in lbl:
        digits = re.sub(r"[^\d]", "", text)
        return digits

    return text

# === Entity Extraction ===
def extract_entities(text: str) -> dict:
    results = {}
    doc = nlp(text)

    for ent in doc.ents:
        if ent.label_ not in results:
            clean = trim_entity_text(ent.label_, ent.text)
            results[ent.label_] = {
                "raw": ent.text.strip(),
                "value": normalize_value(clean, ent.label_)
            }

    # Attempt to recover borrower from nearby text if missing
    if "borrower" not in results and "lender" in results:
        lender_text = results["lender"]["raw"]
        lender_end = text.find(lender_text) + len(lender_text)
        nearby_text = text[lender_end:lender_end + 300]
        borrower_match = re.search(r"\b([A-Z][\w\s,&.-]+?)\s+\(.*?Borrower.*?\)", nearby_text)
        if borrower_match:
            borrower_name = borrower_match.group(1).strip()
            results["borrower"] = {
                "raw": borrower_match.group(0),
                "value": trim_entity_text("borrower", borrower_name)
            }

    return results

# === Main Processing ===
def extract_agreement_data(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        text = extract_text_from_pdf(path)
        if not text.strip():
            print("No native PDF text found; using OCR.")
            text = ocr_pdf_to_text(path)
    elif ext == ".docx":
        text = extract_text_from_docx(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    return extract_entities(text)

# === GUI Entry Point ===
if __name__ == "__main__":
    Tk().withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Agreement (.pdf/.docx)",
        filetypes=[("PDF and DOCX files", "*.pdf *.docx")]
    )
    if not file_path:
        print("No file selected.")
    else:
        print(f"Processing: {file_path}")
        data = extract_agreement_data(file_path)
        print("\n=== Extracted Fields ===")
        if not data:
            print("No fields extracted.")
        for label, info in data.items():
            print(f"{label}: {info['value']} (raw: '{info['raw']}')")
