import requests
from bs4 import BeautifulSoup
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

def fetch_icici_bank_loans():
    url = 'https://www.icicibank.com/personal-banking/loans'
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    text = soup.get_text(" ", strip=True)
    products = []
    for prod in MAIN_PRODUCTS:
        pattern = PRODUCT_PATTERNS[prod]
        match = re.search(pattern, text, re.IGNORECASE)
        interest = None
        if match:
            rate = match.group(1)
            if rate and not rate.startswith('100'):
                interest = rate
        if not interest:
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
    for prod in products:
        if prod['interest']:
            match = re.search(r'(\d+\.\d+%\s*(to|-)?\s*\d+\.\d+%|\d+\.\d+%|\d+%\s*(to|-)?\s*\d+%|\d+%)', prod['interest'])
            if match:
                prod['interest'] = match.group(0)
    return products

def save_icici_loans():
    data = fetch_icici_bank_loans()
    STATIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATIC_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    save_icici_loans()
    print(f"Saved ICICI Bank loans to {STATIC_PATH}") 