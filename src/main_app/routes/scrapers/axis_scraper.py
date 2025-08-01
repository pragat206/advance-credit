import requests
# from bs4 import BeautifulSoup  # Temporarily disabled for Python 3.13 compatibility
import re
import json
from pathlib import Path

MAIN_PRODUCTS = [
    'Personal Loan', 'Home Loan', 'Car Loan', 'Business Loan', 'Loan Against Property',
]

PRODUCT_PATTERNS = {
    'Personal Loan': r'Personal.*?(\d+\.\d+%\s*(to|-)?\s*\d+\.\d+%|\d+\.\d+%|\d+%\s*(to|-)?\s*\d+%|\d+%)',
    'Home Loan': r'Home.*?(\d+\.\d+%\s*(to|-)?\s*\d+\.\d+%|\d+\.\d+%|\d+%\s*(to|-)?\s*\d+%|\d+%)',
    'Car Loan': r'Car.*?(\d+\.\d+%\s*(to|-)?\s*\d+\.\d+%|\d+\.\d+%|\d+%\s*(to|-)?\s*\d+%|\d+%)',
    'Business Loan': r'Business.*?(\d+\.\d+%\s*(to|-)?\s*\d+\.\d+%|\d+\.\d+%|\d+%\s*(to|-)?\s*\d+%|\d+%)',
    'Loan Against Property': r'Property.*?(\d+\.\d+%\s*(to|-)?\s*\d+\.\d+%|\d+\.\d+%|\d+%\s*(to|-)?\s*\d+%|\d+%)',
}

# Fallback: known rate ranges from Axis Bank as of June 2025
FALLBACK_RATES = {
    'Personal Loan': '9.99% to 22%',
    'Home Loan': '8.75% to 9.75%',
    'Car Loan': '9.45% to 14.05%',
    'Business Loan': None,
    'Loan Against Property': 'Up to 9.30%',
}

INTEREST_LABELS = {
    'Personal Loan': 'Personal',
    'Home Loan': 'Home',
    'Car Loan': 'Car',
    'Business Loan': 'Business',
    'Loan Against Property': 'Property',
}

STATIC_PATH = Path(__file__).parent / "static_data" / "axis_loans.json"

# Temporarily disabled for Python 3.13 compatibility
def fetch_axis_bank_loans():
    return []

def save_axis_loans():
    data = fetch_axis_bank_loans()
    # STATIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    # with open(STATIC_PATH, "w", encoding="utf-8") as f:
    #     json.dump(data, f, indent=2, ensure_ascii=False)
    pass

if __name__ == '__main__':
    save_axis_loans()
    print("Axis Bank scraper temporarily disabled") 