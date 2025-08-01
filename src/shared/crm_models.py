from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Float, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# CRM Base
CRMBase = declarative_base()

class WebsiteLead(CRMBase):
    __tablename__ = "website_leads"
    lead_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    contact = Column(String(64), nullable=False)
    email = Column(String(128))
    message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class SocialMediaLead(CRMBase):
    __tablename__ = "social_media_leads"
    lead_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    contact = Column(String(64), nullable=False)
    city = Column(String(64))
    any_ongoing_loan = Column(String(16))
    loan_amount = Column(Float)
    platform_name = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())

class User(CRMBase):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    phone = Column(String(32), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(32), default="employee")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    employee = relationship("Employee", back_populates="user", uselist=False)

class Employee(CRMBase):
    __tablename__ = "employees"
    employee_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), unique=True, nullable=False)
    employee_code = Column(String(64), unique=True, nullable=False)
    designation = Column(String(64))
    department = Column(String(64))
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=True)
    salary = Column(Float, default=0.0)
    commission_rate = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    joining_date = Column(Date, server_default=func.current_date())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    user = relationship("User", back_populates="employee")
    team = relationship("Team", foreign_keys=[team_id], back_populates="members")
    managed_teams = relationship("Team", foreign_keys="Team.manager_id", back_populates="manager")
    assigned_leads = relationship("LeadAssignment", back_populates="employee")
    billings = relationship("Billing", back_populates="employee")
    commissions = relationship("Commission", back_populates="employee")

class Team(CRMBase):
    __tablename__ = "teams"
    team_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)
    manager_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    manager = relationship("Employee", foreign_keys=[manager_id], back_populates="managed_teams")
    members = relationship("Employee", foreign_keys="Employee.team_id", back_populates="team")

class LeadAssignment(CRMBase):
    __tablename__ = "lead_assignments"
    assignment_id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=False)
    lead_type = Column(String(32), nullable=False)  # 'website' or 'social'
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    assigned_at = Column(DateTime, server_default=func.now())
    notes = Column(Text)
    status = Column(String(32), default="assigned")  # 'assigned', 'converted', 'lost'
    
    employee = relationship("Employee", back_populates="assigned_leads")

class Billing(CRMBase):
    __tablename__ = "billing"
    billing_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    basic_salary = Column(Float, default=0.0)
    commission_earned = Column(Float, default=0.0)
    deductions = Column(Float, default=0.0)
    net_salary = Column(Float, default=0.0)
    payment_status = Column(String(32), default="pending")  # 'pending', 'paid', 'overdue'
    payment_date = Column(DateTime, nullable=True)
    generated_at = Column(DateTime, server_default=func.now())
    
    employee = relationship("Employee", back_populates="billings")

class Commission(CRMBase):
    __tablename__ = "commissions"
    commission_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    amount = Column(Float, default=0.0)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    employee = relationship("Employee", back_populates="commissions") 