import json
from pathlib import Path

STATIC_PATH = Path(__file__).parent / "static_data" / "hdfc_loans.json"

# TODO: Implement real scraping logic

def fetch_hdfc_loans():
    # Placeholder: return example data
    return [
        {"name": "Personal Loan", "interest": "10.5% to 21%", "features": ["Quick approval", "Minimal documentation"], "source": "https://www.hdfcbank.com/personal/borrow/popular-loans"},
        {"name": "Home Loan", "interest": "8.5% to 9.5%", "features": ["Flexible tenure", "Attractive rates"], "source": "https://www.hdfcbank.com/personal/borrow/popular-loans"},
    ]

def save_hdfc_loans():
    data = fetch_hdfc_loans()
    STATIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATIC_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    save_hdfc_loans()
    print(f"Saved HDFC Bank loans to {STATIC_PATH}") 