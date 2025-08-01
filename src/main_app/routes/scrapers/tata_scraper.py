import requests
# from bs4 import BeautifulSoup  # Temporarily disabled for Python 3.13 compatibility
import json
from pathlib import Path

MAIN_PRODUCTS = [
    'Personal Loan', 'Home Loan', 'Business Loan', 'Vehicle Loan',
    'Loan Against Securities', 'Loan Against Property', 'Education Loan',
    'Credit Cards', 'Microfinance', 'Rural Individual Loan'
]

PRODUCT_KEYWORDS = [p.lower() for p in MAIN_PRODUCTS]

INTEREST_LABELS = {
    'Personal Loan': 'Personal loan starting',
    'Home Loan': 'Lowest interest rates starting',
}

STATIC_PATH = Path(__file__).parent / "static_data" / "tata_loans.json"

def fetch_tata_capital_loans():
    # Temporarily disabled for Python 3.13 compatibility
    return []
    
    # url = 'https://www.tatacapital.com/loans.html'
    # resp = requests.get(url, timeout=10)
    # resp.raise_for_status()
    # soup = BeautifulSoup(resp.text, 'html.parser')
    # products = []
    # found = set()
    # # Find all <li> and <a> tags that match main products
    # for tag in soup.find_all(['li', 'a']):
    #     text = tag.get_text(strip=True)
    #     for prod in MAIN_PRODUCTS:
    #         if prod.lower() in text.lower() and prod not in found:
    #         products.append({
    #             'name': prod,
    #             'interest': None,
    #             'features': [],
    #             'source': url
    #         })
    #         found.add(prod)
    # # Try to find interest rates for main products
    # for prod in products:
    #     label = INTEREST_LABELS.get(prod['name'])
    #     if label:
    #         rate_tag = soup.find(string=lambda t: t and label in t)
    #         if rate_tag:
    #             # Extract the rate (e.g., '@ 11.50% p.a' or 'at 8.75%*')
    #             after = rate_tag.split('starting')[-1].strip()
    #             prod['interest'] = after.split('\n')[0].strip()
    # return products

def save_tata_loans():
    data = fetch_tata_capital_loans()
    STATIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATIC_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    save_tata_loans()
    print(f"Saved Tata Capital loans to {STATIC_PATH}") 