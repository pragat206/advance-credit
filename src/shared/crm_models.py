from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Float, Boolean, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# CRM Base
CRMBase = declarative_base()

# Unified Lead Model - Combines all lead sources
class Lead(CRMBase):
    __tablename__ = "leads"
    lead_id = Column(Integer, primary_key=True, index=True)
    source = Column(String(32), nullable=False)  # 'website', 'social', 'manual', 'referral', 'walk_in'
    name = Column(String(128), nullable=False)
    contact = Column(String(64), nullable=False)
    email = Column(String(128))
    city = Column(String(64))
    loan_amount = Column(Float)
    loan_type = Column(String(64))  # 'personal', 'home', 'business', 'car', 'property'
    occupation = Column(String(64))
    any_ongoing_loan = Column(String(16))
    platform_name = Column(String(64))  # For social media leads
    message = Column(Text)  # For website leads
    additional_data = Column(JSON)  # Store any additional source-specific data
    status = Column(String(32), default="new")  # 'new', 'assigned', 'pd', 'documentation', 'login', 'underwriter', 'approved', 'rejected', 'disbursed'
    state = Column(String(16), default="open")  # 'open', 'closed'
    other_details = Column(Text)  # For detailed information about leads
    is_doable = Column(Boolean, default=True)
    priority = Column(String(16), default="not_doable")  # 'doable', 'not_doable', 'low', 'medium', 'high', 'urgent'
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    assignments = relationship("LeadAssignment", back_populates="lead", cascade="all, delete-orphan")
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")

# Comprehensive Activity Log Model
class LeadActivity(CRMBase):
    __tablename__ = "lead_activities"
    activity_id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.lead_id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)  # Can be null for system activities
    activity_type = Column(String(64), nullable=False)  # 'created', 'assigned', 'status_changed', 'comment_added', 'doable_toggled', 'contacted', 'document_uploaded', 'follow_up'
    activity_data = Column(JSON)  # Store additional data like old_status, new_status, comment_text, etc.
    description = Column(Text, nullable=False)  # Human-readable description
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    lead = relationship("Lead", back_populates="activities")
    employee = relationship("Employee")

# Keep existing models for backward compatibility
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
    role = Column(String(32), default="employee")  # 'employee', 'manager', 'admin'
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
    assigned_leads = relationship("LeadAssignment", foreign_keys="LeadAssignment.employee_id", back_populates="employee")
    billings = relationship("Billing", back_populates="employee")
    commissions = relationship("Commission", back_populates="employee")
    activities = relationship("LeadActivity", back_populates="employee")

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
    lead_id = Column(Integer, ForeignKey("leads.lead_id"), nullable=False)  # Updated to reference unified Lead
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    assigned_at = Column(DateTime, server_default=func.now())
    notes = Column(Text)
    status = Column(String(32), default="assigned")  # 'assigned', 'pd', 'login', 'login_query', 'underwriter', 'approved', 'rejected', 'closed', 'disbursed'
    is_doable = Column(Boolean, default=True)  # Flag to mark if lead is doable or not
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    assigned_by = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)  # Who assigned this lead
    pd_loan_amount = Column(Float, nullable=True)  # Loan amount captured during PD stage
    approved_loan_amount = Column(Float, nullable=True)  # Loan amount when approved
    close_type = Column(String(32), nullable=True)  # 'approved', 'rejected', 'not_doable' - reason for closure
    
    # Relationships
    lead = relationship("Lead", back_populates="assignments")
    employee = relationship("Employee", back_populates="assigned_leads", foreign_keys=[employee_id])
    assigned_by_employee = relationship("Employee", foreign_keys=[assigned_by])
    comments = relationship("LeadComment", back_populates="assignment", cascade="all, delete-orphan")
    disbursements = relationship("Disbursement", back_populates="assignment", cascade="all, delete-orphan")

class LeadComment(CRMBase):
    __tablename__ = "lead_comments"
    comment_id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("lead_assignments.assignment_id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    assignment = relationship("LeadAssignment", back_populates="comments")
    employee = relationship("Employee")

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

class Disbursement(CRMBase):
    __tablename__ = "disbursements"
    disbursement_id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("lead_assignments.assignment_id"), nullable=False)
    amount = Column(Float, nullable=False)  # Disbursed amount
    disbursement_date = Column(DateTime, server_default=func.now())
    disbursement_type = Column(String(32), default="full")  # 'full', 'partial', 'tranche'
    tranche_number = Column(Integer, nullable=True)  # For partial disbursements
    notes = Column(Text)
    processed_by = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    assignment = relationship("LeadAssignment", back_populates="disbursements")
    processor = relationship("Employee") 

# Closed Leads Model - For tracking closed cases
class CloseLead(CRMBase):
    __tablename__ = "close_leads"
    close_id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=False)  # Reference to original lead
    name = Column(String(128), nullable=False)
    contact = Column(String(64), nullable=False)
    amount = Column(Float)
    close_message = Column(String(32), nullable=False)  # 'rejected' or 'disbursed'
    close_reason = Column(Text)  # Detailed reason for closure
    closed_by = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    closed_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    employee = relationship("Employee") 