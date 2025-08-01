import json
from pathlib import Path

STATIC_PATH = Path(__file__).parent / "static_data" / "bajajfinserv_loans.json"

# TODO: Implement real scraping logic

def fetch_bajajfinserv_loans():
    # Placeholder: return example data
    return [
        {"name": "Personal Loan", "interest": "11% onwards", "features": ["Instant approval", "Minimal paperwork"], "source": "https://www.bajajfinserv.in/loans"},
        {"name": "Home Loan", "interest": "8.50% onwards", "features": ["Flexible repayment", "Quick processing"], "source": "https://www.bajajfinserv.in/loans"},
    ]

def save_bajajfinserv_loans():
    data = fetch_bajajfinserv_loans()
    STATIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATIC_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    save_bajajfinserv_loans()
    print(f"Saved Bajaj Finserv loans to {STATIC_PATH}") 