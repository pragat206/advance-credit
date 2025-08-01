import requests
from bs4 import BeautifulSoup
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

def fetch_axis_bank_loans():
    url = 'https://www.axisbank.com/retail/loans'
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    text = soup.get_text(" ", strip=True)
    products = []
    found = set()
    for prod in MAIN_PRODUCTS:
        pattern = PRODUCT_PATTERNS[prod]
        match = re.search(pattern, text, re.IGNORECASE)
        interest = None
        if match:
            # Filter out '100%' and similar non-rate numbers
            rate = match.group(1)
            if rate and not rate.startswith('100'):
                interest = rate
        if not interest:
            # Try to find a rate in the next 50 chars after product name
            idx = text.lower().find(prod.lower())
            if idx != -1:
                snippet = text[idx:idx+60]
                rates = re.findall(r'(\d+\.\d+%\s*(to|-)?\s*\d+\.\d+%|\d+\.\d+%|\d+%\s*(to|-)?\s*\d+%|\d+%)', snippet)
                for rate in rates:
                    if not rate.startswith('100'):
                        interest = rate
                        break
        if not interest:
            interest = FALLBACK_RATES[prod]
        products.append({
            'name': prod,
            'interest': interest,
            'features': [],
            'source': url
        })
    # Clean up interest rates for each product
    for prod in products:
        if prod['interest']:
            # Extract only the rate part, e.g., '8.75% to 9.75%' or '9.99% to 22%'
            match = re.search(r'(\d+\.\d+%\s*(to|-)?\s*\d+\.\d+%|\d+\.\d+%|\d+%\s*(to|-)?\s*\d+%|\d+%)', prod['interest'])
            if match:
                prod['interest'] = match.group(0)
    return products

def save_axis_loans():
    data = fetch_axis_bank_loans()
    STATIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATIC_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    save_axis_loans()
    print(f"Saved Axis Bank loans to {STATIC_PATH}") 