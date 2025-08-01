import requests
# from bs4 import BeautifulSoup  # Temporarily disabled for Python 3.13 compatibility
import re
import json
from pathlib import Path

STATIC_PATH = Path(__file__).parent / "static_data" / "icici_loans.json"

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

# Fallback: known rate ranges from ICICI Bank as of June 2025
FALLBACK_RATES = {
    'Personal Loan': '10.50% to 19%',
    'Home Loan': '8.75% to 9.85%',
    'Car Loan': '8.75% to 13.75%',
    'Business Loan': None,
    'Loan Against Property': '9.00% to 10.85%',
}

# Temporarily disabled for Python 3.13 compatibility
def fetch_icici_bank_loans():
    return []

def save_icici_loans():
    data = fetch_icici_bank_loans()
    # STATIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    # with open(STATIC_PATH, "w", encoding="utf-8") as f:
    #     json.dump(data, f, indent=2, ensure_ascii=False)
    pass

if __name__ == '__main__':
    save_icici_loans()
    print("ICICI Bank scraper temporarily disabled") 