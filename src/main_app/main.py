from fastapi import FastAPI, Request, Form, Query, Depends, HTTPException, status
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
# Scraper imports removed - using static data instead
import time
from starlette.middleware.sessions import SessionMiddleware
# Admin router removed - no admin functionality needed
from src.main_app.database import get_db, SessionLocal
from src.main_app.models import FAQ, Partner, Product, BankLoan
from sqlalchemy.orm import Session

# CRM Integration imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.shared.crm_models import WebsiteLead
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Include CRM routes with /crm prefix
from src.crm.routes import router as crm_router
from src.crm.manual_leads import router as manual_leads_router

# Production environment check
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

# Create FastAPI app
app = FastAPI(
    title="Advance Credit",
    description="Advance Credit Financial Services",
    version="1.0.0",
    debug=DEBUG
)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database tables and data on startup"""
    print("🚀 Starting Advance Credit application...")
    
    # Create database tables
    if create_tables():
        print("✅ Database tables initialized successfully")
        
        # Populate initial data
        if populate_initial_data():
            print("✅ Initial data populated successfully")
        else:
            print("⚠️ Warning: Failed to populate initial data")
    else:
        print("❌ Failed to initialize database tables")
    
    print("🎉 Application startup completed!")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "super-secret-key-change-this"))

# Include routers
app.include_router(crm_router, prefix="/crm")
app.include_router(manual_leads_router, prefix="/crm")

# Mount static files
app.mount("/static", StaticFiles(directory="src/main_app/static"), name="static")
app.mount("/crm/static", StaticFiles(directory="src/crm/static"), name="crm_static")

# Templates
templates = Jinja2Templates(directory="src/main_app/templates")

# Production security middleware
if ENVIRONMENT == "production":
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    
    # CORS Configuration
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "https://advancecredit.com,https://www.advancecredit.com").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Trusted Host Middleware - disabled for local testing
    # allowed_hosts = os.getenv("ALLOWED_HOSTS", "advancecredit.com,www.advancecredit.com").split(",")
    # Only add TrustedHost middleware if not running locally
    # if "localhost" not in allowed_hosts and "127.0.0.1" not in allowed_hosts:
    #     app.add_middleware(
    #         TrustedHostMiddleware,
    #         allowed_hosts=allowed_hosts
    #     )

# Database setup for production
if ENVIRONMENT == "production":
    # Use PostgreSQL for production
    DATABASE_URL = os.getenv("DATABASE_URL")
    CRM_DATABASE_URL = os.getenv("CRM_DATABASE_URL")
    
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    if CRM_DATABASE_URL and CRM_DATABASE_URL.startswith("postgres://"):
        CRM_DATABASE_URL = CRM_DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    # Use SQLite for development
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./site.db")
    CRM_DATABASE_URL = os.getenv("CRM_DATABASE_URL", "sqlite:///./crm.db")

# Create database engines
if "sqlite" in DATABASE_URL:
    main_engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    main_engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=0, pool_pre_ping=True)

if "sqlite" in CRM_DATABASE_URL:
    crm_engine = create_engine(CRM_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    crm_engine = create_engine(CRM_DATABASE_URL, pool_size=20, max_overflow=0, pool_pre_ping=True)

# Create session makers
CRMSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=crm_engine)

# Database initialization functions
def create_tables():
    """Create database tables if they don't exist"""
    try:
        # Import models to ensure they're registered
        from src.main_app.models import Base as MainBase
        from src.shared.crm_models import CRMBase
        
        # Create main app tables
        MainBase.metadata.create_all(bind=main_engine)
        print("✅ Main app database tables created")
        
        # Create CRM tables
        CRMBase.metadata.create_all(bind=crm_engine)
        print("✅ CRM database tables created")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False

def populate_initial_data():
    """Populate database with initial data if tables are empty"""
    try:
        db = SessionLocal()
        
        # Check if partners table is empty
        partner_count = db.query(Partner).count()
        if partner_count == 0:
            # Add sample partners
            partners_data = [
                {
                    "name": "Axis Bank",
                    "logo_url": "/static/partners/Axis_Bank_logo.png",
                    "url": "https://www.axisbank.com/",
                    "description": "India's Leading Private Bank",
                    "is_active": True
                },
                {
                    "name": "ICICI Bank", 
                    "logo_url": "/static/partners/ICICI_Bank_Logo.png",
                    "url": "https://www.icicibank.com/",
                    "description": "Trusted Financial Partner",
                    "is_active": True
                },
                {
                    "name": "Tata Capital",
                    "logo_url": "/static/partners/tata_capital_logo.png", 
                    "url": "https://www.tatacapital.com/",
                    "description": "Empowering Your Dreams",
                    "is_active": True
                },
                {
                    "name": "HDFC Bank",
                    "logo_url": "/static/partners/HDFC-Bank-logo.png",
                    "url": "https://www.hdfcbank.com/",
                    "description": "India's Most Valuable Bank", 
                    "is_active": True
                },
                {
                    "name": "Yes Bank",
                    "logo_url": "/static/partners/Yes_Bank.png",
                    "url": "https://www.yesbank.in/",
                    "description": "Progressive Banking",
                    "is_active": True
                },
                {
                    "name": "Bajaj Finserv",
                    "logo_url": "/static/partners/Bajaj-Finance-logo.png",
                    "url": "https://www.bajajfinserv.in/",
                    "description": "Innovative Lending Solutions",
                    "is_active": True
                }
            ]
            
            for partner_data in partners_data:
                partner = Partner(**partner_data)
                db.add(partner)
            
            db.commit()
            print("✅ Initial partners data populated")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error populating initial data: {e}")
        return False

def get_crm_db():
    db = CRMSessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_lead_to_crm(name, contact, email, message, source="website"):
    """Save lead to CRM database using unified lead service"""
    db = None
    try:
        db = CRMSessionLocal()
        
        # Import the lead service
        from src.crm.lead_service import LeadService
        
        # Create unified lead
        lead = LeadService.create_lead_from_website(db, name, contact, email, message)
        print(f"✅ Lead saved to unified CRM: {name} - {contact} (Lead ID: {lead.lead_id})")
        return True
    except Exception as e:
        print(f"❌ Error saving lead to CRM: {e}")
        return False
    finally:
        if db:
            db.close()

# Email Configuration
# Note: For Gmail, you need to use an App Password instead of your regular password
# Generate an App Password at: https://myaccount.google.com/apppasswords
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
    'smtp_username': os.getenv('SMTP_USERNAME', 'support@advancecfa.com'),
    'smtp_password': os.getenv('SMTP_PASSWORD', 'YOUR_APP_PASSWORD_HERE'),  # Replace with App Password
    'from_email': os.getenv('FROM_EMAIL', 'support@advancecfa.com'),
    'to_email': os.getenv('TO_EMAIL', 'support@advancecfa.com'),
    'use_tls': os.getenv('USE_TLS', 'True').lower() == 'true'
}

# Alternative email configuration for testing
# You can use your personal Gmail account for testing
TEST_EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'smtp_username': 'your-personal-gmail@gmail.com',  # Replace with your Gmail
    'smtp_password': 'your-app-password',  # Replace with your App Password
    'from_email': 'your-personal-gmail@gmail.com',
    'to_email': 'support@advancecfa.com',
    'use_tls': True
}

def send_simple_email(subject, data, form_type):
    """Send a simple email without HTML formatting for testing"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_CONFIG['from_email']
        msg['To'] = EMAIL_CONFIG['to_email']
        
        # Create plain text content
        text_content = f"""
{subject}

New Lead Information:
"""
        for key, value in data.items():
            if value and key not in ['source', 'form_type']:
                label = key.replace('_', ' ').title()
                text_content += f"{label}: {value}\n"
        
        text_content += f"""
Source: {data.get('source', 'Unknown')}
Form Type: {form_type}

⚠️ ACTION REQUIRED: This is a new lead that requires immediate attention. 
Please contact the customer within 30 minutes as promised on the website.

---
Advance Credit Financial Advisory
support@advancecfa.com
Transform your financial future with expert debt consolidation
"""
        
        # Attach text content
        text_part = MIMEText(text_content, 'plain')
        msg.attach(text_part)
        
        # Try to send email with detailed error handling
        try:
            print(f"🔧 Attempting to send email to {EMAIL_CONFIG['to_email']}")
            print(f"🔧 Using SMTP: {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}")
            print(f"🔧 Username: {EMAIL_CONFIG['smtp_username']}")
            
            if EMAIL_CONFIG['use_tls']:
                server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
                print("🔧 Starting TLS...")
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            
            print("🔧 Attempting login...")
            server.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
            print("🔧 Login successful!")
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent successfully: {subject}")
            return True, None
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication failed: {e}")
            print("💡 Solution: Check username/password or enable App Passwords in Gmail")
            return False, "SMTP Authentication failed - check username/password"
        except smtplib.SMTPException as e:
            print(f"❌ SMTP Error: {e}")
            return False, f"SMTP Error: {e}"
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            return False, str(e)
            
    except Exception as e:
        print(f"❌ Email configuration error: {e}")
        return False, str(e)

def send_test_email(subject, data, form_type):
    """Send email using test configuration for debugging"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        # Create simple text message
        text_content = f"""
{subject}

New Lead Information:
"""
        for key, value in data.items():
            if value and key not in ['source', 'form_type']:
                label = key.replace('_', ' ').title()
                text_content += f"{label}: {value}\n"
        
        text_content += f"""
Source: {data.get('source', 'Unknown')}
Form Type: {form_type}

⚠️ ACTION REQUIRED: This is a new lead that requires immediate attention.

---
Advance Credit Financial Advisory
"""
        
        msg = MIMEText(text_content)
        msg['Subject'] = subject
        msg['From'] = TEST_EMAIL_CONFIG['from_email']
        msg['To'] = TEST_EMAIL_CONFIG['to_email']
        
        # Try to send using test config
        try:
            print(f"🧪 Testing email with: {TEST_EMAIL_CONFIG['smtp_username']}")
            
            server = smtplib.SMTP(TEST_EMAIL_CONFIG['smtp_server'], TEST_EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(TEST_EMAIL_CONFIG['smtp_username'], TEST_EMAIL_CONFIG['smtp_password'])
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Test email sent successfully!")
            return True, None
            
        except Exception as e:
            print(f"❌ Test email failed: {e}")
            return False, str(e)
            
    except Exception as e:
        print(f"❌ Test email configuration error: {e}")
        return False, str(e)

def create_html_email_template(subject, data, form_type):
    """Create a nicely formatted HTML email template"""
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{subject}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            .email-container {{
                background-color: #ffffff;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
                color: white;
                padding: 20px;
                border-radius: 8px 8px 0 0;
                margin: -30px -30px 30px -30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }}
            .form-type-badge {{
                background-color: #10b981;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                display: inline-block;
                margin-top: 10px;
            }}
            .data-section {{
                background-color: #f8fafc;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }}
            .data-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 0;
                border-bottom: 1px solid #e2e8f0;
            }}
            .data-row:last-child {{
                border-bottom: none;
            }}
            .data-label {{
                font-weight: 600;
                color: #374151;
                min-width: 120px;
            }}
            .data-value {{
                color: #1f2937;
                text-align: right;
                flex: 1;
                margin-left: 20px;
            }}
            .footer {{
                background-color: #f1f5f9;
                padding: 20px;
                border-radius: 8px;
                margin-top: 30px;
                text-align: center;
                color: #64748b;
                font-size: 14px;
            }}
            .company-info {{
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid #e2e8f0;
            }}
            .urgent-notice {{
                background-color: #fef3c7;
                border: 1px solid #f59e0b;
                border-radius: 6px;
                padding: 15px;
                margin: 20px 0;
                color: #92400e;
            }}
            .urgent-notice strong {{
                color: #d97706;
            }}
            @media (max-width: 600px) {{
                body {{
                    padding: 10px;
                }}
                .email-container {{
                    padding: 20px;
                }}
                .data-row {{
                    flex-direction: column;
                    align-items: flex-start;
                }}
                .data-value {{
                    text-align: left;
                    margin-left: 0;
                    margin-top: 5px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>Advance Credit - New Lead</h1>
                <div class="form-type-badge">{form_type.replace('-', ' ').title()}</div>
            </div>
            
            <div class="data-section">
                <h3 style="margin-top: 0; color: #1e3a8a;">Lead Information</h3>
    """
    
    # Add data rows
    for key, value in data.items():
        if value and key not in ['source', 'form_type']:
            label = key.replace('_', ' ').title()
            html_template += f"""
                <div class="data-row">
                    <div class="data-label">{label}:</div>
                    <div class="data-value">{value}</div>
                </div>
            """
    
    # Add source information
    if 'source' in data:
        html_template += f"""
                <div class="data-row">
                    <div class="data-label">Source:</div>
                    <div class="data-value">{data['source'].title()}</div>
                </div>
        """
    
    html_template += """
            </div>
            
            <div class="urgent-notice">
                <strong>⚠️ Action Required:</strong> This is a new lead that requires immediate attention. Please contact the customer within 30 minutes as promised on the website.
            </div>
            
            <div class="footer">
                <p><strong>Advance Credit Financial Advisory</strong></p>
                <div class="company-info">
                    <p>📧 support@advancecfa.com | 📞 24/7 Support</p>
                    <p>Transform your financial future with expert debt consolidation</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_template

def send_html_email(subject, data, form_type):
    """Send nicely formatted HTML email"""
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_CONFIG['from_email']
        msg["To"] = EMAIL_CONFIG['to_email']
        
        # Create HTML content
        html_content = create_html_email_template(subject, data, form_type)
        
        # Create plain text version
        plain_text = f"""
{subject}

Lead Information:
"""
        for key, value in data.items():
            if value and key not in ['source', 'form_type']:
                label = key.replace('_', ' ').title()
                plain_text += f"{label}: {value}\n"
        
        plain_text += f"""
Source: {data.get('source', 'Unknown')}
Form Type: {form_type}

⚠️ Action Required: This is a new lead that requires immediate attention. Please contact the customer within 30 minutes as promised on the website.

---
Advance Credit Financial Advisory
support@advancecfa.com
Transform your financial future with expert debt consolidation
"""
        
        # Set the plain text as the main content
        msg.set_content(plain_text)
        
        # Add HTML as alternative
        msg.add_alternative(html_content, subtype='html')
        
        # Send email
        if EMAIL_CONFIG['use_tls']:
            smtp = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            smtp.starttls()
        else:
            smtp = smtplib.SMTP_SSL(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        
        # Login
        smtp.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
        
        smtp.send_message(msg)
        smtp.quit()
        print(f"✅ HTML Email sent: {subject}")
        return True, None
    except Exception as e:
        print(f"Email send failed: {e}")
        return False, str(e)

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

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # Use environment variable
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

# Partner loan caching removed - using static data instead

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

@app.get("/health")
async def health_check():
    """Health check endpoint for Render monitoring"""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": ENVIRONMENT,
        "version": "1.0.0"
    }

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/crm")
async def crm_redirect():
    """Redirect /crm to /crm/login for seamless access"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/crm/login", status_code=302)

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
             interest_rate: float = Form(...),
             tenure_unit: str = Form("years")):
    # EMI calculation
    monthly_rate = interest_rate / (12 * 100)
    
    # Convert tenure to months based on unit
    if tenure_unit.lower() == "years":
        total_months = tenure * 12
    else:
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
        "tenure": total_months,  # Always return in months for display
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

@app.get("/contact", response_class=HTMLResponse)
def contact_get(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.post("/contact")
async def contact(
    name: str = Form(...),
    contact: str = Form(...),
    email: str = Form(None),
    query: str = Form(...),
    source: str = Form("homepage")
):
    # Save directly to CRM database (no file logging)
    message = f"Query: {query}\nSource: {source}"
    save_lead_to_crm(name, contact, email, message, source)
    
    # Return success message with nice styling
    success_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Success - Advance Credit</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .success-container {
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .success-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                max-width: 500px;
                width: 100%;
                padding: 40px;
                text-align: center;
            }
            .success-icon {
                font-size: 4rem;
                color: #28a745;
                margin-bottom: 20px;
            }
            .success-title {
                color: #2c3e50;
                font-weight: 700;
                font-size: 2rem;
                margin-bottom: 15px;
            }
            .success-message {
                color: #7f8c8d;
                font-size: 1.1rem;
                margin-bottom: 30px;
            }
            .btn-back {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                border-radius: 12px;
                padding: 12px 30px;
                font-weight: 600;
                color: white;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .btn-back:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="success-container">
            <div class="success-card">
                <div class="success-icon">
                    <i class="bi bi-check-circle"></i>
                </div>
                <h1 class="success-title">Message Sent Successfully!</h1>
                <p class="success-message">
                    Thank you for contacting us. We'll get back to you within 24 hours.
                </p>
                <a href="/" class="btn btn-back">
                    <i class="bi bi-house me-2"></i>Back to Home
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=success_html)

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
    # Save directly to CRM database (no file logging)
    message = f"Occupation: {occupation}\nLoan Amount: ₹{amount}\nLoan Type: {loan_type or 'Personal Loan'}\nPartner: {partner or 'Not specified'}\nSource: {source}"
    save_lead_to_crm(name, contact, email, message, source)
    
    # Return success message with nice styling
    success_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Success - Advance Credit</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .success-container {
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .success-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                max-width: 500px;
                width: 100%;
                padding: 40px;
                text-align: center;
            }
            .success-icon {
                font-size: 4rem;
                color: #28a745;
                margin-bottom: 20px;
            }
            .success-title {
                color: #2c3e50;
                font-weight: 700;
                font-size: 2rem;
                margin-bottom: 15px;
            }
            .success-message {
                color: #7f8c8d;
                font-size: 1.1rem;
                margin-bottom: 30px;
            }
            .btn-back {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                border-radius: 12px;
                padding: 12px 30px;
                font-weight: 600;
                color: white;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .btn-back:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="success-container">
            <div class="success-card">
                <div class="success-icon">
                    <i class="bi bi-check-circle"></i>
                </div>
                <h1 class="success-title">Application Submitted!</h1>
                <p class="success-message">
                    Thank you for your loan application. We have received your details and will contact you within 24 hours to discuss your requirements.
                </p>
                <a href="/" class="btn btn-back">
                    <i class="bi bi-house me-2"></i>Back to Home
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=success_html)

@app.post("/debt-consultation")
async def debt_consultation(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(None),
    total_emi: str = Form(None)
):
    # Save directly to CRM database (no file logging)
    message = f"Total EMI: ₹{total_emi or 'Not specified'}\nSource: debt-consultation"
    save_lead_to_crm(name, phone, email, message, "debt-consultation")
    
    # Return success message with nice styling
    success_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Success - Advance Credit</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .success-container {
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .success-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                max-width: 500px;
                width: 100%;
                padding: 40px;
                text-align: center;
            }
            .success-icon {
                font-size: 4rem;
                color: #28a745;
                margin-bottom: 20px;
            }
            .success-title {
                color: #2c3e50;
                font-weight: 700;
                font-size: 2rem;
                margin-bottom: 15px;
            }
            .success-message {
                color: #7f8c8d;
                font-size: 1.1rem;
                margin-bottom: 30px;
            }
            .btn-back {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                border-radius: 12px;
                padding: 12px 30px;
                font-weight: 600;
                color: white;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .btn-back:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="success-container">
            <div class="success-card">
                <div class="success-icon">
                    <i class="bi bi-check-circle"></i>
                </div>
                <h1 class="success-title">Consultation Requested!</h1>
                <p class="success-message">
                    Thank you for requesting a debt consultation. Our experts will analyze your situation and contact you within 24 hours with personalized solutions.
                </p>
                <a href="/" class="btn btn-back">
                    <i class="bi bi-house me-2"></i>Back to Home
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=success_html)

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
    # Only log to file if name and contact are provided (no CRM integration for calculators)
    if name and contact:
        email_data = {
            'name': name,
            'contact': contact,
            'email': email,
            'current_emi': current_emi,
            'loan_count': loan_count,
            'interest_rate': interest_rate,
            'credit_score': credit_score,
            'source': source
        }
        
        subject = f"Debt Calculator Assessment Request from {name}"
        # The log_email_to_file function is removed, so this part of the code is now effectively a no-op
        # if we were to re-introduce it, it would need to be re-implemented or removed.
        # For now, we'll just print a message indicating the simulation.
        print(f"📧 [MOCK] Email would be sent: {subject}")
        print(f"📧 [MOCK] From: {EMAIL_CONFIG['from_email']}")
        print(f"📧 [MOCK] To: {email_data.get('email', EMAIL_CONFIG['to_email'])}")
        print(f"📧 [MOCK] Body: {email_data}")
        print("📧 [MOCK] Note: No local SMTP server found. This is a simulation for testing.")
    
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

# API endpoints for partner loans removed - using static data instead

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