from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import BankLoan, Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./site.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# CRM database for leads
CRM_DATABASE_URL = "sqlite:///./crm.db"
crm_engine = create_engine(CRM_DATABASE_URL, connect_args={"check_same_thread": False})
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

Base.metadata.create_all(engine) 