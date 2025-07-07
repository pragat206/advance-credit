import json
from app.db import SessionLocal
from passlib.hash import bcrypt
from app.models import AdminUser, FAQ, Product, Partner, Service, Banner, Testimonial, TeamMember

# Partner FAQs (from partners.html)
PARTNER_FAQS = [
    {
        "question": "How do you choose your lending partners?",
        "answer": "We select partners based on strict regulatory compliance, customer service, product innovation, and a proven track record of reliability.",
        "location": "partners"
    },
    {
        "question": "Can I apply for a loan directly with a partner?",
        "answer": "Yes, you can apply directly with any of our partners, but applying through Advance Credit gives you access to exclusive offers and personalized support.",
        "location": "partners"
    },
    {
        "question": "How can my institution become a partner?",
        "answer": "Simply contact our partnerships team using the button above. We'll guide you through our onboarding process.",
        "location": "partners"
    },
    {
        "question": "What are the benefits of partnering with Advance Credit?",
        "answer": "Our partners benefit from increased visibility, high-quality leads, digital tools, and co-branded marketing opportunities.",
        "location": "partners"
    }
]

PARTNERS = [
    {"name": "Axis Bank", "logo_url": "/static/partners/Axis_Bank_logo.png", "url": "https://www.axisbank.com/"},
    {"name": "ICICI Bank", "logo_url": "/static/partners/ICICI_Bank_Logo.png", "url": "https://www.icicibank.com/"},
    {"name": "Tata Capital", "logo_url": "/static/partners/tata_capital_logo.png", "url": "https://www.tatacapital.com/"},
    {"name": "HDFC Bank", "logo_url": "/static/partners/HDFC-Bank-logo.png", "url": "https://www.hdfcbank.com/personal/borrow/popular-loans"},
    {"name": "Yes Bank", "logo_url": "/static/partners/Yes_Bank.png", "url": "https://www.yesbank.in/yes-bank-loans"},
    {"name": "Bajaj Finserv", "logo_url": "/static/partners/Bajaj-Finance-logo.png", "url": "https://www.bajajfinserv.in/loans"}
]

LOAN_FILES = [
    ("Axis Bank", "app/static_data/axis_loans.json"),
    ("ICICI Bank", "app/static_data/icici_loans.json"),
    ("Tata Capital", "app/static_data/tata_loans.json"),
    ("HDFC Bank", "app/static_data/hdfc_loans.json"),
    ("Yes Bank", "app/static_data/yesbank_loans.json"),
    ("Bajaj Finserv", "app/static_data/bajajfinserv_loans.json")
]

SERVICES = [
    {"name": "Business Loan Planning", "description": "We help businesses organize and optimize their paperwork, making them eligible for future loan requirements. Our experts ensure your documentation and financials are always ready for the next big opportunity.", "icon": "briefcase-fill"},
    {"name": "Loans for MSMEs & SMEs", "description": "Specialized loan solutions for Micro, Small, and Medium Enterprises. Get working capital, machinery loans, and business expansion funding with flexible terms and expert support for your growing business.", "icon": "building"},
    {"name": "NRI Loans", "description": "Tailored loan products for Non-Resident Indians (NRIs) to invest in property, business, or personal needs in India. Enjoy seamless processing, attractive rates, and dedicated NRI support.", "icon": "globe"},
    {"name": "Debt Consolidation", "description": "Consolidate multiple small loans and EMIs into a single, structured loan. We help you restructure your debt, lower your monthly outgo, and manage your expenses better. Our experts will analyze your current liabilities and design a repayment plan that fits your budget, so you can regain control of your finances and reduce stress.", "icon": "arrow-repeat"},
    {"name": "Financial Consulting", "description": "Our consultants provide best practices and personalized strategies for a secure financial future. We guide you on budgeting, investments, and credit management to help you achieve your goals.", "icon": "bar-chart-fill"}
]

def seed_admin_user():
    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter_by(username="admin").first()
        if not admin:
            admin = AdminUser(username="admin", password_hash=bcrypt.hash("admin123"))
            db.add(admin)
            db.commit()
            print("Seeded default admin user: admin / admin123")
        else:
            # Force reset password
            admin.password_hash = bcrypt.hash("admin123")
            db.commit()
            print("Reset admin password to: admin123")
    finally:
        db.close()

def seed_faqs():
    db = SessionLocal()
    try:
        # Seed home FAQs from faqs.json
        with open("app/faqs.json", "r", encoding="utf-8") as f:
            faqs = json.load(f)
        for faq in faqs:
            exists = db.query(FAQ).filter_by(question=faq["question"], location="home").first()
            if not exists:
                db.add(FAQ(question=faq["question"], answer=faq["answer"], location="home"))
        # Seed partner FAQs
        for faq in PARTNER_FAQS:
            exists = db.query(FAQ).filter_by(question=faq["question"], location="partners").first()
            if not exists:
                db.add(FAQ(question=faq["question"], answer=faq["answer"], location="partners"))
        db.commit()
        print("Seeded FAQs for home and partners.")
    finally:
        db.close()

def seed_partners():
    db = SessionLocal()
    try:
        for p in PARTNERS:
            exists = db.query(Partner).filter_by(name=p["name"]).first()
            if not exists:
                db.add(Partner(name=p["name"], logo_url=p["logo_url"], url=p["url"]))
        db.commit()
        print("Seeded partners.")
    finally:
        db.close()

def seed_products():
    db = SessionLocal()
    try:
        for partner_name, file_path in LOAN_FILES:
            partner = db.query(Partner).filter_by(name=partner_name).first()
            if not partner:
                continue
            with open(file_path, "r", encoding="utf-8") as f:
                loans = json.load(f)
            for loan in loans:
                exists = db.query(Product).filter_by(name=loan["name"], partner_id=partner.id).first()
                if not exists:
                    db.add(Product(
                        name=loan["name"],
                        type=loan.get("type", None),
                        description=None,
                        interest=loan.get("interest", None),
                        features=", ".join(loan.get("features", [])) if loan.get("features") else None,
                        partner_id=partner.id
                    ))
        db.commit()
        print("Seeded products/loans.")
    finally:
        db.close()

def seed_services():
    db = SessionLocal()
    try:
        for s in SERVICES:
            exists = db.query(Service).filter_by(name=s["name"]).first()
            if not exists:
                db.add(Service(name=s["name"], description=s["description"], icon=s["icon"]))
        db.commit()
        print("Seeded services.")
    finally:
        db.close()

def seed_banners():
    db = SessionLocal()
    try:
        banners = [
            {
                "title": "Get fast and easy access to loans with a click!",
                "image_url": "/static/hero/hero_banner_1.png",
                "caption": "Let's find the perfect loan for you. Whether you need personal advice or are ready to apply, our team is here to assist you.",
                "order": 1
            },
            {
                "title": "Your trusted partner for financial growth.",
                "image_url": "/static/hero/hero_banner_2.png",
                "caption": "Apply for loans from top banks & NBFCs. Simple, transparent, and secure borrowing.",
                "order": 2
            }
        ]
        for b in banners:
            exists = db.query(Banner).filter_by(title=b["title"]).first()
            if not exists:
                db.add(Banner(**b))
        db.commit()
        print("Seeded banners.")
    finally:
        db.close()

def seed_testimonials():
    db = SessionLocal()
    try:
        testimonials = [
            {"author": "Priya S.", "content": "Advance Credit made my home loan process seamless and fast. Highly recommended!"},
            {"author": "Rahul M.", "content": "I could compare all offers and got the best deal for my car loan. Thank you!"},
            {"author": "Anjali T.", "content": "Superb service and support. The team was with me at every step."}
        ]
        for t in testimonials:
            exists = db.query(Testimonial).filter_by(author=t["author"], content=t["content"]).first()
            if not exists:
                db.add(Testimonial(**t))
        db.commit()
        print("Seeded testimonials.")
    finally:
        db.close()

def seed_team():
    db = SessionLocal()
    try:
        team = [
            {
                "name": "Vikas Tiwari",
                "role": "Founder & CEO",
                "bio": "Vikas is a seasoned financial advisor with 15+ years of experience helping clients achieve their financial goals. He leads Advance Credit with a vision for transparency and customer-first service.",
                "image_url": None
            }
        ]
        for m in team:
            exists = db.query(TeamMember).filter_by(name=m["name"]).first()
            if not exists:
                db.add(TeamMember(**m))
        db.commit()
        print("Seeded team members.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin_user()
    seed_faqs()
    seed_partners()
    seed_products()
    seed_services()
    seed_banners()
    seed_testimonials()
    seed_team() 