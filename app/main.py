from fastapi import FastAPI, Request, Form, Query, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import status
import uvicorn
import json
from pathlib import Path
import smtplib
from email.message import EmailMessage
import os
from app.scrapers.tata_scraper import fetch_tata_capital_loans
from app.scrapers.axis_scraper import fetch_axis_bank_loans
from app.scrapers.icici_scraper import fetch_icici_bank_loans
import time
from starlette.middleware.sessions import SessionMiddleware
from app.admin.routes import router as admin_router
from app.db import get_db, CRM_SessionLocal, SessionLocal
from app.models import FAQ, Lead, Partner, Product, BankLoan
from sqlalchemy.orm import Session

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "super-secret-key-change-this"))
app.include_router(admin_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Email Configuration
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'localhost'),
    'smtp_port': int(os.getenv('SMTP_PORT', '25')),
    'smtp_username': os.getenv('SMTP_USERNAME', ''),
    'smtp_password': os.getenv('SMTP_PASSWORD', ''),
    'from_email': os.getenv('FROM_EMAIL', 'noreply@advancecfa.com'),
    'to_email': os.getenv('TO_EMAIL', 'vikas@advancecfa.com'),
    'use_tls': os.getenv('USE_TLS', 'False').lower() == 'true'
}

def send_email(subject, body, to_email=None):
    """Send email using configured SMTP settings"""
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_CONFIG['from_email']
        msg["To"] = to_email or EMAIL_CONFIG['to_email']
        msg.set_content(body)
        
        # For localhost testing, if no SMTP server is available, simulate email sending
        if EMAIL_CONFIG['smtp_server'] == 'localhost':
            try:
                # Try to connect to local SMTP server
                smtp = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
                smtp.send_message(msg)
                smtp.quit()
                print(f"✅ Email sent via localhost SMTP: {subject}")
                return True, None
            except ConnectionRefusedError:
                # If no local SMTP server, simulate email sending for testing
                print(f"📧 [MOCK] Email would be sent: {subject}")
                print(f"📧 [MOCK] From: {EMAIL_CONFIG['from_email']}")
                print(f"📧 [MOCK] To: {to_email or EMAIL_CONFIG['to_email']}")
                print(f"📧 [MOCK] Body: {body[:200]}...")
                print("📧 [MOCK] Note: No local SMTP server found. This is a simulation for testing.")
                return True, None
        elif EMAIL_CONFIG['use_tls']:
            smtp = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            smtp.starttls()
        else:
            smtp = smtplib.SMTP_SSL(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        
        # Login if credentials are provided (skip for localhost)
        if EMAIL_CONFIG['smtp_username'] and EMAIL_CONFIG['smtp_password'] and EMAIL_CONFIG['smtp_server'] != 'localhost':
            smtp.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
        
        smtp.send_message(msg)
        smtp.quit()
        return True, None
    except Exception as e:
        print(f"Email send failed: {e}")
        return False, str(e)

# Dummy loan products
dummy_products = [
    {"name": "Personal Loan", "type": "Personal Loan", "description": "Quick personal loans with minimal documentation.", "interest": "10.5% p.a.", "features": ["Minimal documentation", "Quick approval", "Flexible tenure"]},
    {"name": "Home Loan", "type": "Home Loan", "description": "Affordable home loans for your dream house.", "interest": "8.2% p.a.", "features": ["Low interest rates", "Long tenure", "Easy balance transfer"]},
    {"name": "Car Loan", "type": "Car Loan", "description": "Drive your dream car with easy car loans.", "interest": "9.0% p.a.", "features": ["Up to 100% funding", "Quick disbursal", "Attractive interest rates"]},
    {"name": "Business Loan", "type": "Business Loan", "description": "Grow your business with flexible business loans.", "interest": "12.0% p.a.", "features": ["Collateral-free", "Flexible repayment", "High loan amount"]},
]

ADMIN_PASSWORD = "admin123"  # Change this to a secure password in production
FAQS_PATH = Path("app/faqs.json")

STATIC_DATA_PATH = Path(__file__).parent / "static_data"

# Custom fallback features for each partner and loan type
PARTNER_LOAN_FEATURES = {
    ("Axis Bank", "Personal Loan"): [
        "Quick personal loans with minimal Axis Bank paperwork",
        "Attractive rates and fast disbursal from Axis Bank"
    ],
    ("Axis Bank", "Home Loan"): [
        "Axis Bank home loans for your dream house",
        "Flexible tenure and doorstep service"
    ],
    ("Axis Bank", "Car Loan"): [
        "Finance your new car with Axis Bank",
        "Up to 100% on-road funding, quick approval"
    ],
    ("Axis Bank", "Business Loan"): [
        "Grow your business with Axis Bank's collateral-free loans",
        "Flexible repayment and high loan amounts"
    ],
    ("Axis Bank", "Loan Against Property"): [
        "Unlock property value with Axis Bank",
        "Competitive rates and easy processing"
    ],
    ("ICICI Bank", "Personal Loan"): [
        "ICICI Bank personal loans for all your needs",
        "Minimal documentation, fast approval"
    ],
    ("ICICI Bank", "Home Loan"): [
        "ICICI Bank home loans at attractive rates",
        "Flexible tenure and balance transfer facility"
    ],
    ("ICICI Bank", "Car Loan"): [
        "Drive home your dream car with ICICI Bank",
        "Quick disbursal and up to 100% funding"
    ],
    ("ICICI Bank", "Business Loan"): [
        "Expand your business with ICICI Bank loans",
        "Collateral-free, flexible repayment options"
    ],
    ("ICICI Bank", "Loan Against Property"): [
        "Leverage your property with ICICI Bank",
        "Attractive rates and fast processing"
    ],
    ("Tata Capital", "Personal Loan"): [
        "Tata Capital personal loans for every occasion",
        "Quick approval and flexible tenure"
    ],
    ("Tata Capital", "Home Loan"): [
        "Affordable Tata Capital home loans",
        "Easy balance transfer and top-up options"
    ],
    ("Tata Capital", "Business Loan"): [
        "Empower your business with Tata Capital",
        "Simple process, competitive rates"
    ],
    ("Tata Capital", "Vehicle Loan"): [
        "Finance your vehicle with Tata Capital",
        "Attractive rates and fast approval"
    ],
    ("Tata Capital", "Loan Against Property"): [
        "Unlock funds with Tata Capital property loans",
        "Flexible tenure and quick disbursal"
    ],
    ("Tata Capital", "Education Loan"): [
        "Tata Capital education loans for your future",
        "Flexible repayment after course completion"
    ],
    ("Tata Capital", "Credit Cards"): [
        "Tata Capital credit cards for every lifestyle",
        "Exciting rewards and offers"
    ],
    ("Tata Capital", "Microfinance"): [
        "Microfinance solutions by Tata Capital",
        "Empowering small businesses and individuals"
    ],
    ("Tata Capital", "Rural Individual Loan"): [
        "Loans for rural individuals by Tata Capital",
        "Simple process and quick approval"
    ],
    ("Tata Capital", "Loan Against Securities"): [
        "Leverage your investments with Tata Capital",
        "Instant funds and flexible tenure"
    ],
    ("HDFC Bank", "Personal Loan"): [
        "HDFC Bank personal loans with quick approval",
        "Minimal documentation and flexible tenure"
    ],
    ("HDFC Bank", "Home Loan"): [
        "HDFC Bank home loans at attractive rates",
        "Long tenure and easy balance transfer"
    ],
    ("Yes Bank", "Personal Loan"): [
        "Yes Bank personal loans for your needs",
        "Quick disbursal and flexible repayment"
    ],
    ("Yes Bank", "Home Loan"): [
        "Yes Bank home loans with attractive rates",
        "Easy documentation and fast approval"
    ],
    ("Bajaj Finserv", "Personal Loan"): [
        "Bajaj Finserv instant personal loans",
        "Minimal paperwork and fast approval"
    ],
    ("Bajaj Finserv", "Home Loan"): [
        "Bajaj Finserv home loans at low rates",
        "Flexible repayment and quick processing"
    ],
}

def load_faqs():
    if FAQS_PATH.exists():
        with open(FAQS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_faqs(faqs):
    with open(FAQS_PATH, "w", encoding="utf-8") as f:
        json.dump(faqs, f, indent=2, ensure_ascii=False)

def get_cached_partner_loans(partner):
    now = time.time()
    entry = PARTNER_CACHE[partner]
    if entry['data'] is not None and now - entry['ts'] < CACHE_TTL:
        return entry['data']
    # Fetch fresh data
    if partner == 'axis':
        data = fetch_axis_bank_loans()
    elif partner == 'icici':
        data = fetch_icici_bank_loans()
    elif partner == 'tata':
        data = fetch_tata_capital_loans()
    else:
        data = []
    PARTNER_CACHE[partner] = {'data': data, 'ts': now}
    return data

def ensure_loan_features(loans, partner_name=None):
    for loan in loans:
        # Use partner-specific fallback if features are missing or too short
        if not loan.get("features") or len(loan["features"]) < 2:
            key = (partner_name, loan["name"])
            default = PARTNER_LOAN_FEATURES.get(key)
            if default:
                loan["features"] = default
            else:
                loan["features"] = ["Flexible terms and fast approval", "Trusted by thousands of customers"]
    return loans

# Helper functions to load partner loan data from static files
def load_axis_loans():
    try:
        with open(STATIC_DATA_PATH / "axis_loans.json", "r", encoding="utf-8") as f:
            loans = json.load(f)
            return ensure_loan_features(loans, partner_name="Axis Bank")
    except Exception:
        return []

def load_icici_loans():
    try:
        with open(STATIC_DATA_PATH / "icici_loans.json", "r", encoding="utf-8") as f:
            loans = json.load(f)
            return ensure_loan_features(loans, partner_name="ICICI Bank")
    except Exception:
        return []

def load_tata_loans():
    try:
        with open(STATIC_DATA_PATH / "tata_loans.json", "r", encoding="utf-8") as f:
            loans = json.load(f)
            return ensure_loan_features(loans, partner_name="Tata Capital")
    except Exception:
        return []

def load_hdfc_loans():
    try:
        with open(STATIC_DATA_PATH / "hdfc_loans.json", "r", encoding="utf-8") as f:
            loans = json.load(f)
            return ensure_loan_features(loans, partner_name="HDFC Bank")
    except Exception:
        return []

def load_yesbank_loans():
    try:
        with open(STATIC_DATA_PATH / "yesbank_loans.json", "r", encoding="utf-8") as f:
            loans = json.load(f)
            return ensure_loan_features(loans, partner_name="Yes Bank")
    except Exception:
        return []

def load_bajajfinserv_loans():
    try:
        with open(STATIC_DATA_PATH / "bajajfinserv_loans.json", "r", encoding="utf-8") as f:
            loans = json.load(f)
            return ensure_loan_features(loans, partner_name="Bajaj Finserv")
    except Exception:
        return []

@app.get("/", response_class=HTMLResponse)
def home(request: Request, faq_success: str = Query(None), db: Session = Depends(get_db)):
    faqs = db.query(FAQ).filter_by(location="home").order_by(FAQ.id).all()
    return templates.TemplateResponse("home.html", {"request": request, "faqs": faqs, "faq_success": faq_success})

@app.get("/products", response_class=HTMLResponse)
def products(request: Request, db: Session = Depends(get_db)):
    partners = db.query(Partner).all()
    partners_data = []
    for partner in partners:
        loans = db.query(Product).filter_by(partner_id=partner.id).all()
        partners_data.append({
            'name': partner.name,
            'logo': partner.logo_url,
            'url': partner.url,
            'loans': [
                {
                    'name': loan.name,
                    'interest': loan.interest,
                    'features': loan.features,
                } for loan in loans
            ]
        })
    return templates.TemplateResponse("products.html", {"request": request, "partners": partners_data})

@app.get("/emi", response_class=HTMLResponse)
def emi_get(request: Request):
    return templates.TemplateResponse("emi.html", {"request": request, "result": None})

@app.post("/emi")
async def emi_post(request: Request, 
             loan_amount: float = Form(...), 
             tenure: int = Form(...), 
             interest_rate: float = Form(...)):
    # EMI calculation
    monthly_rate = interest_rate / (12 * 100)
    total_months = tenure
    
    if monthly_rate == 0:
        emi = loan_amount / total_months
    else:
        emi = loan_amount * (monthly_rate * (1 + monthly_rate)**total_months) / ((1 + monthly_rate)**total_months - 1)
    
    total_payment = emi * total_months
    total_interest = total_payment - loan_amount
    
    # No database interaction for EMI calculator
    result = {
        "loan_amount": f"{loan_amount:,.0f}",
        "tenure": tenure,
        "interest_rate": interest_rate,
        "emi": f"{emi:,.0f}",
        "total_payment": f"{total_payment:,.0f}",
        "total_interest": f"{total_interest:,.0f}"
    }
    
    return templates.TemplateResponse("emi.html", {"request": request, "result": result})

@app.get("/partners", response_class=HTMLResponse)
def partners(request: Request, db: Session = Depends(get_db)):
    partners = [
        {
            'name': 'Axis Bank',
            'logo': '/static/partners/Axis_Bank_logo.png',
            'url': 'https://www.axisbank.com/',
            'type': 'Bank',
            'tagline': "India's Leading Private Bank",
            'description': "Axis Bank is one of India's largest private sector banks, offering a wide range of financial products and services to individuals and businesses.",
            'loans': load_axis_loans()
        },
        {
            'name': 'ICICI Bank',
            'logo': '/static/partners/ICICI_Bank_Logo.png',
            'url': 'https://www.icicibank.com/',
            'type': 'Bank',
            'tagline': "Trusted Financial Partner",
            'description': "ICICI Bank is a leading private sector bank in India, known for its innovative products and customer-centric approach.",
            'loans': load_icici_loans()
        },
        {
            'name': 'Tata Capital',
            'logo': '/static/partners/tata_capital_logo.png',
            'url': 'https://www.tatacapital.com/',
            'type': 'NBFC',
            'tagline': "Empowering Your Dreams",
            'description': "Tata Capital is a leading non-banking financial company (NBFC) in India, providing a variety of loan and investment solutions.",
            'loans': load_tata_loans()
        },
        {
            'name': 'HDFC Bank',
            'logo': '/static/partners/HDFC-Bank-logo.png',
            'url': 'https://www.hdfcbank.com/personal/borrow/popular-loans',
            'type': 'Bank',
            'tagline': "India's Most Valuable Bank",
            'description': "HDFC Bank is India's largest private sector lender by assets, offering a full suite of financial products and services.",
            'loans': load_hdfc_loans()
        },
        {
            'name': 'Yes Bank',
            'logo': '/static/partners/Yes_Bank.png',
            'url': 'https://www.yesbank.in/yes-bank-loans',
            'type': 'Bank',
            'tagline': "Progressive Banking",
            'description': "Yes Bank is a high-quality, customer-centric, and service-driven bank in India, offering a wide range of banking and financial products.",
            'loans': load_yesbank_loans()
        },
        {
            'name': 'Bajaj Finserv',
            'logo': '/static/partners/Bajaj-Finance-logo.png',
            'url': 'https://www.bajajfinserv.in/loans',
            'type': 'NBFC',
            'tagline': "Innovative Lending Solutions",
            'description': "Bajaj Finserv is a leading NBFC in India, providing a wide range of financial products including loans, insurance, and investments.",
            'loans': load_bajajfinserv_loans()
        }
    ]
    # Compute unique product names for filters
    all_products = set()
    for partner in partners:
        for loan in partner['loans']:
            all_products.add(loan['name'])
    all_products = sorted(all_products)
    faqs = db.query(FAQ).filter_by(location="partners").order_by(FAQ.id).all()
    return templates.TemplateResponse(
        "partners.html",
        {"request": request, "partners": partners, "faqs": faqs, "all_products": all_products}
    )

@app.get("/services", response_class=HTMLResponse)
def services(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})

@app.post("/contact")
async def contact(
    name: str = Form(...),
    contact: str = Form(...),
    email: str = Form(None),
    query: str = Form(...),
    source: str = Form("homepage")
):
    # Save to CRM leads table
    crm_db = CRM_SessionLocal()
    try:
        lead = Lead(
            name=name, 
            contact=contact, 
            email=email, 
            message=query, 
            source=source, 
            form_type="contact",
            lead_type="general contact us"
        )
        crm_db.add(lead)
        crm_db.commit()
    finally:
        crm_db.close()
    # Send the email using the configured SMTP settings
    subject = f"New Contact Query from {name} (Advance Credit Website)"
    body = f"""
Name: {name}
Contact: {contact}
Email: {email or 'Not provided'}
Query:
{query}

---
This email was sent from the Advance Credit website contact form.
"""
    success, error = send_email(subject, body)
    # Always return a simple HTML message
    return HTMLResponse("<div style='text-align:center;padding:2em;'><h2>Successfully submitted your request.</h2></div>")

@app.post("/apply-loan")
async def apply_loan(
    name: str = Form(...),
    email: str = Form(None),
    contact: str = Form(...),
    occupation: str = Form(...),
    amount: str = Form(...),
    partner: str = Form(None),
    loan_type: str = Form(None),
    source: str = Form('apply')
):
    crm_db = CRM_SessionLocal()
    try:
        msg = f"Occupation: {occupation}\nLoan Type: {loan_type}\nAmount: {amount}"
        lead = Lead(
            name=name, 
            contact=contact, 
            email=email, 
            message=msg, 
            source=source, 
            form_type="apply-loan",
            lead_type="applied for loan",
            occupation=occupation,
            loan_amount=float(amount) if amount else None,
            loan_type=loan_type,
            partner_name=partner
        )
        crm_db.add(lead)
        crm_db.commit()
    finally:
        crm_db.close()
    subject = f"New Loan Application from {name} - {loan_type}"
    body = f"""
New Loan Application Received

Applicant Details:
Name: {name}
Email: {email or 'Not provided'}
Contact: {contact}
Occupation: {occupation}

Loan Details:
Loan Type: {loan_type}
Amount: {amount}
Partner: {partner}

---
This application was submitted through the Advance Credit website.
Please contact the applicant within 24 hours.
"""
    success, error = send_email(subject, body)
    return HTMLResponse("<div style='text-align:center;padding:2em;'><h2>Successfully submitted your request.</h2></div>")

@app.post("/debt-consultation")
async def debt_consultation(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(None),
    total_emi: str = Form(None)
):
    crm_db = CRM_SessionLocal()
    try:
        msg = "Debt Consolidation Consultation Request"
        lead = Lead(
            name=name, 
            contact=phone, 
            email=email, 
            message=msg, 
            source="debt-consultation", 
            form_type="debt-consultation",
            lead_type="priority action required",
            phone=phone,
            total_emi=float(total_emi) if total_emi else None
        )
        crm_db.add(lead)
        crm_db.commit()
    finally:
        crm_db.close()
    subject = f"Debt Consolidation Consultation Request from {name}"
    body = f"""
New Debt Consolidation Consultation Request

Client Details:
Name: {name}
Phone: {phone}
Email: {email}
Total Monthly EMI: {total_emi or 'Not provided'}

Service Requested: Debt Consolidation Consultation

---
This request was submitted through the Advance Credit website debt consolidation section.
Please call the client within 30 minutes as promised on the website.
"""
    success, error = send_email(subject, body)
    return HTMLResponse("<div style='text-align:center;padding:2em;'><h2>Successfully submitted your request.</h2></div>")

@app.post("/debt-calculator")
async def debt_calculator(
    name: str = Form(None),
    contact: str = Form(None),
    email: str = Form(None),
    current_emi: str = Form(None),
    loan_count: str = Form(None),
    interest_rate: str = Form(None),
    credit_score: str = Form(None),
    source: str = Form("debt-calculator")
):
    crm_db = CRM_SessionLocal()
    try:
        msg = "Debt Calculator Assessment Request"
        lead = Lead(
            name=name, 
            contact=contact, 
            email=email, 
            message=msg, 
            source=source, 
            form_type="debt-calculator",
            lead_type="debt assessment",
            current_monthly_emi=float(current_emi) if current_emi else None,
            number_of_loans=int(loan_count) if loan_count else None,
            average_interest_rate=float(interest_rate) if interest_rate else None,
            credit_score=credit_score
        )
        crm_db.add(lead)
        crm_db.commit()
    finally:
        crm_db.close()
    
    # Calculate approximate savings
    if current_emi and loan_count and interest_rate:
        try:
            current_emi_val = float(current_emi)
            loan_count_val = int(loan_count)
            interest_rate_val = float(interest_rate)
            
            # Simple calculation for demonstration
            # In reality, this would be more complex based on credit score and other factors
            if credit_score == "excellent":
                new_rate = interest_rate_val * 0.7  # 30% reduction
            elif credit_score == "good":
                new_rate = interest_rate_val * 0.8  # 20% reduction
            elif credit_score == "fair":
                new_rate = interest_rate_val * 0.9  # 10% reduction
            else:
                new_rate = interest_rate_val * 0.95  # 5% reduction
            
            monthly_savings = current_emi_val * (interest_rate_val - new_rate) / 100
            annual_savings = monthly_savings * 12
            
            return JSONResponse({
                "success": True,
                "monthly_savings": round(monthly_savings, 2),
                "annual_savings": round(annual_savings, 2),
                "new_emi": round(current_emi_val - monthly_savings, 2)
            })
        except:
            pass
    
    return JSONResponse({"success": True, "message": "Assessment submitted successfully"})

@app.get("/api/partner-loans/tata-capital")
def api_tata_capital_loans():
    return fetch_tata_capital_loans()

@app.get("/api/partner-loans/axis-bank")
def api_axis_bank_loans():
    return fetch_axis_bank_loans()

@app.get("/api/partner-loans/icici-bank")
def api_icici_bank_loans():
    return fetch_icici_bank_loans()

@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get('/api/bank-loans')
def get_bank_loans():
    db = SessionLocal()
    loans = db.query(BankLoan).all()
    result = []
    for loan in loans:
        result.append({
            'bank_name': loan.bank_name,
            'loan_type': loan.loan_type,
            'interest_rate': loan.interest_rate,
            'features': json.loads(loan.features) if loan.features else [],
            'url': loan.url,
            'last_updated': loan.last_updated.isoformat() if loan.last_updated else None
        })
    db.close()
    return JSONResponse(result)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 