from locale import currency
from .agreement_ner_extractor_spacy import extract_agreement_data

def run_scanner_script(file_path: str) -> dict:
    raw_data = extract_agreement_data(file_path)

    return {
        "original_date": raw_data.get("original_date", {}).get("value",""),
        "lender": raw_data.get("lender", {}).get("value",""),
        "borrower": raw_data.get("borrower", {}).get("value",""),
        "principal": raw_data.get("principal", {}).get("value",""),
        "currency": raw_data.get("currency", {}).get("value",""),
        "interest_rate": raw_data.get("interest_rate",{}).get("value",""),
        "maturity_date": raw_data.get("maturity_date",{}).get("value", "")
    }
