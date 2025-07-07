from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Float
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False, default="employee")
    status = Column(String(32), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Partner(Base):
    __tablename__ = "partners"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    logo_url = Column(String(256))
    url = Column(String(256))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    name = Column(String(128), nullable=False)
    contact = Column(String(64), nullable=False)
    email = Column(String(128))
    message = Column(Text)
    
    # Form Source Information
    source = Column(String(32))  # homepage, products, services, about, debt-consultation
    form_type = Column(String(32))  # contact, debt-consultation, apply-loan, debt-calculator
    lead_type = Column(String(64))  # general contact us, applied for loan, priority action required, debt assessment
    
    # Debt Consultation Form Fields
    total_emi = Column(Float)  # Monthly EMI amount
    phone = Column(String(64))  # Alternative phone field for debt form
    
    # Loan Application Form Fields
    occupation = Column(String(64))  # Salaried, Business Owner, etc.
    loan_amount = Column(Float)  # Requested loan amount
    loan_type = Column(String(64))  # personal, home, car, business, etc.
    partner_name = Column(String(128))  # Bank/NBFC name
    
    # Debt Calculator Form Fields
    current_monthly_emi = Column(Float)  # Current EMI amount
    number_of_loans = Column(Integer)  # Number of active loans
    average_interest_rate = Column(Float)  # Average interest rate
    credit_score = Column(String(32))  # excellent, good, fair, poor
    
    # CRM Management Fields
    partner_id = Column(Integer, ForeignKey("partners.id"))
    assigned_to = Column(Integer, ForeignKey("employees.id"), nullable=True)
    status = Column(String(32), default="new")  # new, contacted, qualified, converted, lost
    is_verified = Column(Integer, default=0)  # 0 = unverified, 1 = verified
    documentation = Column(String(64), default="pending")  # pending, submitted, approved, rejected
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    partner = relationship("Partner")
    employee = relationship("Employee")

class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime, nullable=False)
    assigned_to = Column(Integer, ForeignKey("employees.id"), nullable=True)
    status = Column(String(32), default="pending")  # pending, done, overdue
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    employee = relationship("Employee")
