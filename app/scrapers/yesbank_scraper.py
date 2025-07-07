import json
from pathlib import Path

STATIC_PATH = Path(__file__).parent / "static_data" / "yesbank_loans.json"

# TODO: Implement real scraping logic

def fetch_yesbank_loans():
    # Placeholder: return example data
    return [
        {"name": "Personal Loan", "interest": "10.99% onwards", "features": ["Quick disbursal", "Flexible tenure"], "source": "https://www.yesbank.in/yes-bank-loans"},
        {"name": "Home Loan", "interest": "9.15% onwards", "features": ["Attractive rates", "Easy documentation"], "source": "https://www.yesbank.in/yes-bank-loans"},
    ]

def save_yesbank_loans():
    data = fetch_yesbank_loans()
    STATIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATIC_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    save_yesbank_loans()
    print(f"Saved Yes Bank loans to {STATIC_PATH}") 