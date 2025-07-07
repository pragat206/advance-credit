import json
from datetime import datetime
from app.db import SessionLocal
from app.models import BankLoan

# --- Scraper stubs for each bank ---
def fetch_hdfc_loans():
    # TODO: Implement real scraping logic
    return [
        {
            'bank_name': 'HDFC Bank',
            'loan_type': 'personal',
            'interest_rate': '10.5%',
            'features': ['Fast approval', 'Flexible tenure', 'Minimal docs'],
            'url': 'https://www.hdfcbank.com/personal/loans/personal-loan'
        },
        {
            'bank_name': 'HDFC Bank',
            'loan_type': 'home',
            'interest_rate': '8.7%',
            'features': ['Low interest', 'Quick disbursal'],
            'url': 'https://www.hdfcbank.com/personal/loans/home-loan'
        }
    ]

def fetch_axis_loans():
    return [
        {
            'bank_name': 'Axis Bank',
            'loan_type': 'personal',
            'interest_rate': '10.99%',
            'features': ['No prepayment charges', 'Quick process'],
            'url': 'https://www.axisbank.com/retail/loans/personal-loan'
        }
    ]

def fetch_icici_loans():
    return [
        {
            'bank_name': 'ICICI Bank',
            'loan_type': 'car',
            'interest_rate': '9.25%',
            'features': ['Attractive rates', 'Flexible EMI'],
            'url': 'https://www.icicibank.com/loans/car-loan'
        }
    ]

def fetch_bajaj_loans():
    return [
        {
            'bank_name': 'Bajaj Finserv',
            'loan_type': 'business',
            'interest_rate': '17.5%',
            'features': ['Collateral free', 'Quick approval'],
            'url': 'https://www.bajajfinserv.in/business-loan'
        }
    ]

def fetch_tata_loans():
    return [
        {
            'bank_name': 'Tata Capital',
            'loan_type': 'home',
            'interest_rate': '8.75%',
            'features': ['Doorstep service', 'Minimal docs'],
            'url': 'https://www.tatacapital.com/loans/home-loan.html'
        }
    ]

def fetch_yesbank_loans():
    return [
        {
            'bank_name': 'Yes Bank',
            'loan_type': 'personal',
            'interest_rate': '10.99%',
            'features': ['Quick disbursal', 'Flexible tenure'],
            'url': 'https://www.yesbank.in/personal-banking/loans/personal-loan'
        }
    ]

# --- Sync logic ---
def sync_loans(loans, db):
    for loan in loans:
        existing = db.query(BankLoan).filter_by(bank_name=loan['bank_name'], loan_type=loan['loan_type']).first()
        features_json = json.dumps(loan['features'])
        if existing:
            if (existing.interest_rate == loan['interest_rate'] and existing.features == features_json):
                continue  # No change
            existing.interest_rate = loan['interest_rate']
            existing.features = features_json
            existing.url = loan.get('url')
            existing.last_updated = datetime.now()
            print(f"Updated: {loan['bank_name']} {loan['loan_type']}")
        else:
            new_loan = BankLoan(
                bank_name=loan['bank_name'],
                loan_type=loan['loan_type'],
                interest_rate=loan['interest_rate'],
                features=features_json,
                url=loan.get('url'),
                last_updated=datetime.now()
            )
            db.add(new_loan)
            print(f"Added: {loan['bank_name']} {loan['loan_type']}")
    db.commit()

if __name__ == '__main__':
    db = SessionLocal()
    all_loans = []
    all_loans += fetch_hdfc_loans()
    all_loans += fetch_axis_loans()
    all_loans += fetch_icici_loans()
    all_loans += fetch_bajaj_loans()
    all_loans += fetch_tata_loans()
    all_loans += fetch_yesbank_loans()
    sync_loans(all_loans, db)
    db.close()
    print("Bank loan data sync complete.") 