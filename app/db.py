import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import BankLoan, Base

# Use environment variable for database URL, fallback to local SQLite
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./site.db")

# Handle PostgreSQL URL from Render.com (convert to SQLAlchemy format)
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# CRM database for leads
CRM_DATABASE_URL = os.getenv("CRM_DATABASE_URL", "sqlite:///./crm.db")
if CRM_DATABASE_URL.startswith("postgres://"):
    CRM_DATABASE_URL = CRM_DATABASE_URL.replace("postgres://", "postgresql://", 1)

crm_engine = create_engine(
    CRM_DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in CRM_DATABASE_URL else {}
)
CRM_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=crm_engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def seed_admin_user():
    db = SessionLocal()
    try:
        if not db.query(AdminUser).filter_by(username="admin").first():
            admin = AdminUser(username="admin", password_hash=bcrypt.hash("admin123"))
            db.add(admin)
            db.commit()
            print("Seeded default admin user: admin / admin123")
    finally:
        db.close()

# Create tables if they don't exist
Base.metadata.create_all(engine) 