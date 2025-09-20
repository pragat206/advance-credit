print("CRM ROUTER LOADED")
from fastapi import APIRouter, Request, Form, Depends, status, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response
from src.shared.crm_models import CRMBase, User, Team, Employee, LeadAssignment, Billing, Commission, LeadComment, Lead, LeadActivity, Disbursement, CloseLead
from src.crm.lead_service import LeadService
from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker
import bcrypt
from fastapi.templating import Jinja2Templates
from typing import Optional
# import pandas as pd  # Temporarily disabled for deployment
import io
import os
from datetime import datetime, timedelta

router = APIRouter()

templates = Jinja2Templates(directory="src/crm/templates")

DATABASE_URL = os.getenv("CRM_DATABASE_URL", "sqlite:///./crm.db")

# Handle PostgreSQL URL conversion
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Enhanced Role-Based Access Control
def require_admin(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    return user

def require_manager_or_admin(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role not in ["admin", "manager"]:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    return user

def require_authenticated(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    return user

def get_current_employee(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(Employee).filter(Employee.user_id == user_id).first()

def can_manage_lead(assignment: LeadAssignment, current_employee: Employee, user_role: str) -> bool:
    """Check if current user can manage this lead"""
    if user_role == "admin":
        return True
    elif user_role == "manager":
        # Manager can manage leads assigned to their team members
        if assignment.employee.team_id and current_employee.team_id:
            return assignment.employee.team_id == current_employee.team_id
        return False
    else:
        # Employee can only manage their own leads
        return assignment.employee_id == current_employee.employee_id

# Lead Status Management
LEAD_STATUSES = {
    "assigned": "Assigned",
    "pd": "PD (Document Collection & Profile Check)",
    "login": "Login",
    "login_query": "Login Query",
    "underwriter": "Underwriter",
    "approved": "Approved",
    "rejected": "Rejected", 
    "closed": "Closed",
    "disbursed": "Disbursed"
}

def get_next_statuses(current_status: str) -> list:
    """Get possible next statuses based on current status"""
    status_flow = {
        "assigned": ["pd", "closed"],
        "pd": ["login", "closed"],
        "login": ["login_query", "closed"],
        "login_query": ["underwriter", "closed"],
        "underwriter": ["approved", "rejected", "closed"],
        "approved": ["disbursed", "closed"],
        "rejected": ["closed"],
        "closed": [],
        "disbursed": []
    }
    return status_flow.get(current_status, [])

@router.get("/unauthorized", response_class=HTMLResponse)
def unauthorized(request: Request):
    return templates.TemplateResponse("unauthorized.html", {"request": request})

# Registration routes removed - Only admins can create users through the admin panel

@router.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login", response_class=HTMLResponse)
def login_post(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    print(f"DEBUG: Login attempt for email: {email}")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"DEBUG: User not found for email: {email}")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials."})
    
    print(f"DEBUG: User found: {user.name} (Role: {user.role})")
    
    # Test password
    password_valid = bcrypt.checkpw(password.encode(), user.password_hash.encode())
    print(f"DEBUG: Password check result: {password_valid}")
    
    if not password_valid:
        print(f"DEBUG: Invalid password for user: {user.name}")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials."})
    
    # Get employee details
    employee = db.query(Employee).filter(Employee.user_id == user.user_id).first()
    if employee:
        print(f"DEBUG: Employee found: {employee.employee_code}")
    
    # Set session data
    request.session["user_id"] = user.user_id
    request.session["user_role"] = user.role
    request.session["user_name"] = user.name
    if employee:
        request.session["employee_id"] = employee.employee_id
        request.session["employee_code"] = employee.employee_code
    
    print(f"DEBUG: Session set - User ID: {user.user_id}, Role: {user.role}, Name: {user.name}")
    print(f"DEBUG: Redirecting to dashboard...")
    
    return RedirectResponse("/crm/dashboard", status_code=status.HTTP_302_FOUND)

# Manual Lead Creation Routes
@router.get("/leads/add-website", response_class=HTMLResponse)
def add_website_lead_get(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    user_role = request.session.get("user_role")
    # Only Admin and Manager can add leads
    if user_role not in ["admin", "manager"]:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    # Get employees for assignment (Admin sees all, Manager sees their team)
    if user_role == "admin":
        employees = db.query(Employee).filter(Employee.is_active == True).all()
    else:
        # Manager sees only their team members
        current_employee = db.query(Employee).filter(Employee.user_id == request.session.get("user_id")).first()
        if current_employee and current_employee.team_id:
            employees = db.query(Employee).filter(
                Employee.team_id == current_employee.team_id,
                Employee.is_active == True
            ).all()
        else:
            employees = []
    
    return templates.TemplateResponse("lead_new.html", {
        "request": request, 
        "error": None, 
        "lead_type": "website",
        "employees": employees
    })

@router.post("/leads/add-website", response_class=HTMLResponse)
def add_website_lead_post(
    request: Request, 
    name: str = Form(...), 
    contact: str = Form(...), 
    email: str = Form(None), 
    message: str = Form(None),
    assigned_employee_id: int = Form(None),
    db: Session = Depends(get_db)
):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    user_role = request.session.get("user_role")
    if user_role not in ["admin", "manager"]:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    try:
        # Create the unified lead
        lead = Lead(
            source="website",
            name=name,
            contact=contact,
            email=email,
            message=message,
            status="new"
        )
        db.add(lead)
        db.flush()  # Get the lead_id
        
        # Assign to employee if specified
        if assigned_employee_id:
            assignment = LeadAssignment(
                lead_id=lead.lead_id,
                employee_id=assigned_employee_id,
                status="assigned"
            )
            db.add(assignment)
        
        db.commit()
        return RedirectResponse("/crm/unified-leads", status_code=status.HTTP_302_FOUND)
    
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("lead_new.html", {
            "request": request, 
            "error": f"Error creating lead: {str(e)}", 
            "lead_type": "website",
            "employees": []
        })

@router.get("/leads/add-social", response_class=HTMLResponse)
def add_social_lead_get(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    user_role = request.session.get("user_role")
    if user_role not in ["admin", "manager"]:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    # Get employees for assignment
    if user_role == "admin":
        employees = db.query(Employee).filter(Employee.is_active == True).all()
    else:
        current_employee = db.query(Employee).filter(Employee.user_id == request.session.get("user_id")).first()
        if current_employee and current_employee.team_id:
            employees = db.query(Employee).filter(
                Employee.team_id == current_employee.team_id,
                Employee.is_active == True
            ).all()
        else:
            employees = []
    
    return templates.TemplateResponse("lead_new.html", {
        "request": request, 
        "error": None, 
        "lead_type": "social",
        "employees": employees
    })

@router.post("/leads/add-social", response_class=HTMLResponse)
def add_social_lead_post(
    request: Request, 
    name: str = Form(...), 
    contact: str = Form(...), 
    city: str = Form(None),
    any_ongoing_loan: str = Form("false"),
    loan_amount: float = Form(None),
    platform_name: str = Form(...),
    assigned_employee_id: int = Form(None),
    db: Session = Depends(get_db)
):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    user_role = request.session.get("user_role")
    if user_role not in ["admin", "manager"]:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    try:
        # Create the unified lead
        lead = Lead(
            source="social",
            name=name,
            contact=contact,
            city=city,
            any_ongoing_loan=any_ongoing_loan,
            loan_amount=loan_amount,
            platform_name=platform_name,
            status="new"
        )
        db.add(lead)
        db.flush()  # Get the lead_id
        
        # Assign to employee if specified
        if assigned_employee_id:
            assignment = LeadAssignment(
                lead_id=lead.lead_id,
                employee_id=assigned_employee_id,
                status="assigned"
            )
            db.add(assignment)
        
        db.commit()
        return RedirectResponse("/crm/unified-leads", status_code=status.HTTP_302_FOUND)
    
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("lead_new.html", {
            "request": request, 
            "error": f"Error creating lead: {str(e)}", 
            "lead_type": "social",
            "employees": []
        })

# Enhanced role-based dashboard with different personas
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    user_role = request.session.get("user_role")
    employee_id = request.session.get("employee_id")
    current_user = db.query(User).filter(User.user_id == request.session.get("user_id")).first()
    
    # Get current employee details
    current_employee = None
    if employee_id:
        current_employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    
    if user_role == "admin":
        # Admin sees all data and has full access
        website_leads_count = db.query(Lead).filter(Lead.source == "website").count()
        social_leads_count = db.query(Lead).filter(Lead.source == "social").count()
        total_leads = db.query(Lead).count()
        users_count = db.query(User).count()
        employees_count = db.query(Employee).count()
        teams_count = db.query(Team).count()
        
        # Get recent leads (unified)
        recent_leads = db.query(Lead).order_by(Lead.created_at.desc()).limit(5).all()
        
        # Get unassigned leads count (unified)
        assigned_leads = db.query(LeadAssignment).count()
        unassigned_leads = total_leads - assigned_leads
        
        # Get team performance
        teams = db.query(Team).all()
        team_performance = []
        for team in teams:
            team_members = db.query(Employee).filter(Employee.team_id == team.team_id).all()
            team_lead_count = 0
            for member in team_members:
                member_leads = db.query(LeadAssignment).filter(LeadAssignment.employee_id == member.employee_id).count()
                team_lead_count += member_leads
            team_performance.append({
                "team": team,
                "member_count": len(team_members),
                "lead_count": team_lead_count
            })
        
        # Get status summary for all leads
        status_summary = {}
        for assignment in db.query(LeadAssignment).all():
            status = assignment.status
            status_summary[status] = status_summary.get(status, 0) + 1
        
        dashboard_data = {
            "persona": "admin",
            "total_leads": total_leads,
            "website_leads_count": website_leads_count,
            "social_leads_count": social_leads_count,
            "unassigned_leads": unassigned_leads,
            "users_count": users_count,
            "employees_count": employees_count,
            "teams_count": teams_count,
            "recent_leads": recent_leads,
            "team_performance": team_performance,
            "status_summary": status_summary
        }
        
    elif user_role == "manager":
        # Manager sees team data and manages their team
        current_employee = db.query(Employee).filter(Employee.user_id == request.session.get("user_id")).first()
        
        if current_employee and current_employee.team_id:
            # Get team members
            team_members = db.query(Employee).filter(Employee.team_id == current_employee.team_id).all()
            team_member_ids = [member.employee_id for member in team_members]
            
            # Get team's assigned leads
            team_assignments = db.query(LeadAssignment).filter(
                LeadAssignment.employee_id.in_(team_member_ids)
            ).all()
            
            # Get unified leads for team
            team_lead_ids = [assignment.lead_id for assignment in team_assignments]
            team_leads = db.query(Lead).filter(Lead.lead_id.in_(team_lead_ids)).all()
            
            website_leads_count = sum(1 for lead in team_leads if lead.source == "website")
            social_leads_count = sum(1 for lead in team_leads if lead.source == "social")
            total_leads = len(team_leads)
            
            # Get team's recent leads (unified)
            recent_leads = db.query(Lead).filter(
                Lead.lead_id.in_(team_lead_ids)
            ).order_by(Lead.created_at.desc()).limit(5).all()
            
            # Get team member performance
            member_performance = []
            for member in team_members:
                member_leads = db.query(LeadAssignment).filter(LeadAssignment.employee_id == member.employee_id).count()
                member_performance.append({
                    "employee": member,
                    "lead_count": member_leads,
                    "user": db.query(User).filter(User.user_id == member.user_id).first()
                })
            
            # Get status summary for team leads
            status_summary = {}
            for assignment in team_assignments:
                status = assignment.status
                status_summary[status] = status_summary.get(status, 0) + 1
            
            dashboard_data = {
                "persona": "manager",
                "total_leads": total_leads,
                "website_leads_count": website_leads_count,
                "social_leads_count": social_leads_count,
                "team_members": team_members,
                "member_performance": member_performance,
                "recent_leads": recent_leads,
                "team": db.query(Team).filter(Team.team_id == current_employee.team_id).first(),
                "status_summary": status_summary
            }
        else:
            # Manager without team
            dashboard_data = {
                "persona": "manager",
                "total_leads": 0,
                "website_leads_count": 0,
                "social_leads_count": 0,
                "team_members": [],
                "member_performance": [],
                "recent_leads": [],
                "team": None,
                "status_summary": {}
            }
            
    else:
        # Employee sees only their data
        if employee_id:
            # Get assigned leads count (unified)
            employee_assignments = db.query(LeadAssignment).filter(
                LeadAssignment.employee_id == employee_id
            ).all()
            
            employee_lead_ids = [assignment.lead_id for assignment in employee_assignments]
            employee_leads = db.query(Lead).filter(Lead.lead_id.in_(employee_lead_ids)).all()
            
            website_leads_count = sum(1 for lead in employee_leads if lead.source == "website")
            social_leads_count = sum(1 for lead in employee_leads if lead.source == "social")
            total_leads = len(employee_leads)
            
            # Get employee's recent assigned leads (unified)
            recent_leads = db.query(Lead).filter(
                Lead.lead_id.in_(employee_lead_ids)
            ).order_by(Lead.created_at.desc()).limit(5).all()
            
            # Calculate assigned and pending leads count
            assigned_leads_count = len(employee_assignments)
            pending_leads_count = len([a for a in employee_assignments if a.status in ['assigned', 'pd', 'login', 'login_query']])
                
            # Get employee's team info
            team_info = None
            if current_employee and current_employee.team_id:
                team_info = db.query(Team).filter(Team.team_id == current_employee.team_id).first()
            
            # Get status summary for employee's leads
            status_summary = {}
            for assignment in employee_assignments:
                status = assignment.status
                status_summary[status] = status_summary.get(status, 0) + 1
            
            dashboard_data = {
                "persona": "employee",
                "total_leads": total_leads,
                "website_leads_count": website_leads_count,
                "social_leads_count": social_leads_count,
                "assigned_leads_count": assigned_leads_count,
                "pending_leads_count": pending_leads_count,
                "recent_leads": recent_leads,
                "team_info": team_info,
                "employee": current_employee,
                "status_summary": status_summary
            }
        else:
            dashboard_data = {
                "persona": "employee",
                "total_leads": 0,
                "website_leads_count": 0,
                "social_leads_count": 0,
                "assigned_leads_count": 0,
                "pending_leads_count": 0,
                "recent_leads": [],
                "team_info": None,
                "employee": None,
                "status_summary": {}
            }
    
    # Add common data
    dashboard_data.update({
        "request": request,
        "current_user": current_user,
        "user_role": user_role
    })
    
    return templates.TemplateResponse("dashboard.html", dashboard_data)

@router.get("/my-employment", response_class=HTMLResponse)
def my_employment(request: Request, db: Session = Depends(get_db)):
    """Employee's employment details page"""
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    user_role = request.session.get("user_role")
    if user_role != "employee":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user_id = request.session.get("user_id")
    employee = db.query(Employee).filter(Employee.user_id == user_id).first()
    
    if not employee:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    # Get employee's billing history
    billings = db.query(Billing).filter(
        Billing.employee_id == employee.employee_id
    ).order_by(Billing.year.desc(), Billing.month.desc()).all()
    
    # Get employee's commission history
    commissions = db.query(Commission).filter(
        Commission.employee_id == employee.employee_id
    ).order_by(Commission.year.desc(), Commission.month.desc()).all()
    
    # Get employee's lead assignments
    assignments = db.query(LeadAssignment).filter(
        LeadAssignment.employee_id == employee.employee_id
    ).order_by(LeadAssignment.assigned_at.desc()).all()
    
    # Calculate some statistics
    total_leads = len(assignments)
    converted_leads = len([a for a in assignments if a.status in ['approved', 'disbursed']])
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    return templates.TemplateResponse("my_employment.html", {
        "request": request,
        "employee": employee,
        "billings": billings,
        "commissions": commissions,
        "assignments": assignments,
        "total_leads": total_leads,
        "converted_leads": converted_leads,
        "conversion_rate": conversion_rate
    })

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)

# Website Leads Management
@router.get("/website-leads", response_class=HTMLResponse)
def website_leads_list(request: Request, db: Session = Depends(get_db)):
    # Redirect to unified leads since we're moving to the unified system
    return RedirectResponse("/crm/unified-leads", status_code=status.HTTP_302_FOUND)

@router.get("/website-leads/{lead_id}", response_class=HTMLResponse)
def website_lead_detail(request: Request, lead_id: int, db: Session = Depends(get_db)):
    """Redirect old website lead detail to unified lead detail"""
    # Try to find the corresponding unified lead
    unified_lead = db.query(Lead).filter(
        Lead.source == "website",
        Lead.additional_data.contains({"migrated_from": "website_leads", "original_id": lead_id})
    ).first()
    
    if unified_lead:
        return RedirectResponse(f"/crm/unified-leads/{unified_lead.lead_id}", status_code=status.HTTP_302_FOUND)
    else:
        # If not found, redirect to unified leads list
        return RedirectResponse("/crm/unified-leads", status_code=status.HTTP_302_FOUND)

# Social Media Leads Management
@router.get("/social-leads", response_class=HTMLResponse)
def social_leads_list(request: Request, db: Session = Depends(get_db)):
    # Redirect to unified leads since we're moving to the unified system
    return RedirectResponse("/crm/unified-leads", status_code=status.HTTP_302_FOUND)

# Bulk Upload for Social Media Leads
@router.get("/social-leads/bulk-upload", response_class=HTMLResponse)
def bulk_upload_get(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("bulk_upload.html", {"request": request, "error": None})

@router.post("/social-leads/bulk-upload", response_class=HTMLResponse)
async def bulk_upload_post(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    if not file.filename.endswith('.csv'):
        return templates.TemplateResponse("bulk_upload.html", {"request": request, "error": "Please upload a CSV file."})
    
    try:
        content = await file.read()
        # df = pd.read_csv(io.StringIO(content.decode('utf-8'))) # Temporarily disabled for deployment
        # for _, row in df.iterrows():
        #     lead = SocialMediaLead(
        #         name=row['name'],
        #         contact=row['contact'],
        #         city=row['city'],
        #         any_ongoing_loan=row.get('any_ongoing_loan', False),
        #         loan_amount=row.get('loan_amount'),
        #         platform_name=row['platform_name']
        #     )
        #     db.add(lead)
        
        # db.commit()
        return templates.TemplateResponse("bulk_upload.html", {"request": request, "error": None, "success": "Bulk upload functionality is temporarily disabled."})
    
    except Exception as e:
        return templates.TemplateResponse("bulk_upload.html", {"request": request, "error": f"Error processing file: {str(e)}"})

@router.get("/social-leads/bulk-upload/template.csv")
def download_csv_template():
    csv_content = "name,contact,city,any_ongoing_loan,loan_amount,platform_name\n"
    csv_content += "John Doe,9876543210,Mumbai,false,500000,Instagram\n"
    csv_content += "Jane Smith,9876543211,Delhi,true,750000,Facebook\n"
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=social_leads_template.csv"}
    )

@router.get("/social-leads/{lead_id}", response_class=HTMLResponse)
def social_lead_detail(request: Request, lead_id: int, db: Session = Depends(get_db)):
    """Redirect old social lead detail to unified lead detail"""
    # Try to find the corresponding unified lead
    unified_lead = db.query(Lead).filter(
        Lead.source == "social",
        Lead.additional_data.contains({"migrated_from": "social_media_leads", "original_id": lead_id})
    ).first()
    
    if unified_lead:
        return RedirectResponse(f"/crm/unified-leads/{unified_lead.lead_id}", status_code=status.HTTP_302_FOUND)
    else:
        # If not found, redirect to unified leads list
        return RedirectResponse("/crm/unified-leads", status_code=status.HTTP_302_FOUND)

# Users Management (Admin only)
@router.get("/users", response_class=HTMLResponse)
def users_list(request: Request, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

@router.get("/users/new", response_class=HTMLResponse)
def user_new_get(request: Request, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("user_new.html", {"request": request, "error": None})

@router.post("/users/new", response_class=HTMLResponse)
def user_new_post(request: Request, name: str = Form(...), email: str = Form(...), phone: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return templates.TemplateResponse("user_new.html", {"request": request, "error": "Email already registered."})
    
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_user = User(name=name, email=email, phone=phone, password_hash=hashed, role=role)
    db.add(new_user)
    db.flush()  # Get the user_id
    
    # Create employee record for the new user
    from datetime import date
    employee_code = f"EMP{new_user.user_id:04d}"
    employee = Employee(
        user_id=new_user.user_id,
        employee_code=employee_code,
        designation="Employee" if role == "employee" else role.title(),
        department="General",
        joining_date=date.today(),
        salary=0.0,
        commission_rate=0.0,
        is_active=True
    )
    db.add(employee)
    db.commit()
    return RedirectResponse("/crm/users", status_code=status.HTTP_302_FOUND)

@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
def user_edit_get(request: Request, user_id: int, db: Session = Depends(get_db)):
    # Manual authentication check
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    current_user = db.query(User).filter(User.user_id == current_user_id).first()
    if not current_user or current_user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("user_edit.html", {"request": request, "user": user, "error": None})

@router.post("/users/{user_id}/edit", response_class=HTMLResponse)
def user_edit_post(request: Request, user_id: int, name: str = Form(...), email: str = Form(...), phone: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    # Manual authentication check
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    current_user = db.query(User).filter(User.user_id == current_user_id).first()
    if not current_user or current_user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.name = name
    user.email = email
    user.phone = phone
    user.role = role
    db.commit()
    return RedirectResponse("/crm/users", status_code=status.HTTP_302_FOUND)

@router.get("/users/{user_id}/delete")
def user_delete(request: Request, user_id: int, db: Session = Depends(get_db)):
    # Manual authentication check
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    current_user = db.query(User).filter(User.user_id == current_user_id).first()
    if not current_user or current_user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    # Prevent self-deletion
    if current_user_id == user_id:
        return RedirectResponse("/crm/users?error=cannot_delete_self", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return RedirectResponse("/crm/users?error=user_not_found", status_code=status.HTTP_302_FOUND)
    
    try:
        # Check if user has associated employee record
        employee = db.query(Employee).filter(Employee.user_id == user_id).first()
        if employee:
            # Delete employee first (this will cascade to related records)
            db.delete(employee)
        
        # Delete the user
        db.delete(user)
        db.commit()
        
        return RedirectResponse("/crm/users?success=user_deleted", status_code=status.HTTP_302_FOUND)
        
    except Exception as e:
        db.rollback()
        print(f"Error deleting user: {e}")
        return RedirectResponse("/crm/users?error=delete_failed", status_code=status.HTTP_302_FOUND)

# Analytics Dashboard
@router.get("/analytics", response_class=HTMLResponse)
def analytics_dashboard(request: Request, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    try:
        # Get comprehensive analytics data
        analytics_data = get_analytics_data(db)
        
        return templates.TemplateResponse("analytics.html", {
            "request": request,
            **analytics_data
        })
    except Exception as e:
        print(f"Analytics error: {e}")
        # Return empty analytics data as fallback
        return templates.TemplateResponse("analytics.html", {
            "request": request,
            "website_leads_count": 0,
            "social_leads_count": 0,
            "total_leads": 0,
            "active_leads_count": 0,
            "converted_leads_count": 0,
            "lost_leads_count": 0,
            "pending_leads_count": 0,
            "conversion_rate": 0,
            "website_converted_count": 0,
            "social_converted_count": 0,
            "platform_labels": [],
            "platform_data": [],
            "monthly_labels": [],
            "website_monthly_data": [],
            "social_monthly_data": [],
            "team_labels": [],
            "team_data": [],
            "recent_activities": []
        })

def get_analytics_data(db: Session, time_filter: str = "all"):
    """Get comprehensive analytics data with optional time filtering using unified Lead model"""
    try:
        print("DEBUG: Starting analytics data collection")
        
        # Simple lead counts
        website_leads_count = db.query(Lead).filter(Lead.source == "website").count()
        social_leads_count = db.query(Lead).filter(Lead.source == "social").count()
        total_leads = db.query(Lead).count()
        
        print(f"DEBUG: Lead counts - Website: {website_leads_count}, Social: {social_leads_count}, Total: {total_leads}")
        
        # Simple assignment counts
        active_leads_count = db.query(LeadAssignment).filter(LeadAssignment.status.in_(["assigned", "pd", "login", "login_query", "underwriter"])).count()
        converted_leads_count = db.query(LeadAssignment).filter(LeadAssignment.status.in_(["approved", "disbursed"])).count()
        lost_leads_count = db.query(LeadAssignment).filter(LeadAssignment.status.in_(["rejected", "closed"])).count()
        pending_leads_count = db.query(LeadAssignment).filter(LeadAssignment.status == "assigned").count()
        
        print(f"DEBUG: Assignment counts - Active: {active_leads_count}, Converted: {converted_leads_count}, Lost: {lost_leads_count}, Pending: {pending_leads_count}")
        
        # Calculate conversion rate
        total_assigned = active_leads_count + converted_leads_count + lost_leads_count
        conversion_rate = (converted_leads_count / total_assigned * 100) if total_assigned > 0 else 0
        
        # Simple platform data
        platform_counts = db.query(
            Lead.platform_name,
            func.count(Lead.lead_id)
        ).filter(
            Lead.source == "social",
            Lead.platform_name.isnot(None)
        ).group_by(Lead.platform_name).all()
        
        platform_labels = [platform for platform, _ in platform_counts]
        platform_data = [count for _, count in platform_counts]
        
        print(f"DEBUG: Platform data - Labels: {platform_labels}, Data: {platform_data}")
        
        # Simple monthly data (last 6 months)
        monthly_labels = []
        website_monthly_data = []
        social_monthly_data = []
        
        for i in range(6):
            month_start = datetime.now() - timedelta(days=30 * (i + 1))
            month_end = datetime.now() - timedelta(days=30 * i)
            
            month_label = month_start.strftime("%b %Y")
            monthly_labels.insert(0, month_label)
            
            website_count = db.query(Lead).filter(
                Lead.source == "website",
                Lead.created_at >= month_start,
                Lead.created_at <= month_end
            ).count()
            website_monthly_data.insert(0, website_count)
            
            social_count = db.query(Lead).filter(
                Lead.source == "social",
                Lead.created_at >= month_start,
                Lead.created_at <= month_end
            ).count()
            social_monthly_data.insert(0, social_count)
        
        print(f"DEBUG: Monthly data collected")
        
        # Simple team data
        teams = db.query(Team).all()
        team_labels = [team.name for team in teams]
        team_data = []
        
        for team in teams:
            team_lead_count = db.query(LeadAssignment).join(
                Employee, LeadAssignment.employee_id == Employee.employee_id
            ).filter(Employee.team_id == team.team_id).count()
            team_data.append(team_lead_count)
        
        print(f"DEBUG: Team data collected")
        
        # Simple conversion counts
        website_converted_count = db.query(LeadAssignment).join(
            Lead, LeadAssignment.lead_id == Lead.lead_id
        ).filter(
            Lead.source == "website",
            LeadAssignment.status.in_(["approved", "disbursed"])
        ).count()
        
        social_converted_count = db.query(LeadAssignment).join(
            Lead, LeadAssignment.lead_id == Lead.lead_id
        ).filter(
            Lead.source == "social",
            LeadAssignment.status.in_(["approved", "disbursed"])
        ).count()
        
        print(f"DEBUG: Conversion counts - Website: {website_converted_count}, Social: {social_converted_count}")
        
        # Simple recent activities
        recent_activities = []
        
        # Recent leads
        recent_leads = db.query(Lead).order_by(Lead.created_at.desc()).limit(5).all()
        for lead in recent_leads:
            recent_activities.append({
                "type": lead.source,
                "title": f"New {lead.source.title()} Lead: {lead.name}",
                "description": f"Contact: {lead.contact}",
                "time": lead.created_at.strftime("%d %b %Y %H:%M")
            })
        
        print(f"DEBUG: Recent activities collected")
        
        return {
            "website_leads_count": website_leads_count,
            "social_leads_count": social_leads_count,
            "total_leads": total_leads,
            "active_leads_count": active_leads_count,
            "converted_leads_count": converted_leads_count,
            "lost_leads_count": lost_leads_count,
            "pending_leads_count": pending_leads_count,
            "conversion_rate": round(conversion_rate, 1),
            "website_converted_count": website_converted_count,
            "social_converted_count": social_converted_count,
            "platform_labels": platform_labels,
            "platform_data": platform_data,
            "monthly_labels": monthly_labels,
            "website_monthly_data": website_monthly_data,
            "social_monthly_data": social_monthly_data,
            "team_labels": team_labels,
            "team_data": team_data,
            "recent_activities": recent_activities
        }
    except Exception as e:
        print(f"Analytics error: {e}")
        import traceback
        traceback.print_exc()
        # Return empty data as fallback
        return {
            "website_leads_count": 0,
            "social_leads_count": 0,
            "total_leads": 0,
            "active_leads_count": 0,
            "converted_leads_count": 0,
            "lost_leads_count": 0,
            "pending_leads_count": 0,
            "conversion_rate": 0,
            "website_converted_count": 0,
            "social_converted_count": 0,
            "platform_labels": [],
            "platform_data": [],
            "monthly_labels": [],
            "website_monthly_data": [],
            "social_monthly_data": [],
            "team_labels": [],
            "team_data": [],
            "recent_activities": []
        }

def get_start_date_for_filter(time_filter: str):
    """Get start date based on time filter"""
    now = datetime.now()
    
    if time_filter == "this_month":
        return datetime(now.year, now.month, 1)
    elif time_filter == "last_month":
        last_month = now.replace(day=1) - timedelta(days=1)
        return datetime(last_month.year, last_month.month, 1)
    elif time_filter == "last_3_months":
        return now - timedelta(days=90)
    elif time_filter == "last_6_months":
        return now - timedelta(days=180)
    elif time_filter == "this_year":
        return datetime(now.year, 1, 1)
    elif time_filter == "last_year":
        return datetime(now.year - 1, 1, 1)
    else:  # all
        return None

def get_monthly_trends(db: Session, start_date=None):
    """Get monthly lead trends for the last 12 months"""
    now = datetime.now()
    labels = []
    website_data = []
    social_data = []
    
    for i in range(11, -1, -1):
        month_start = datetime(now.year, now.month, 1) - timedelta(days=30*i)
        month_end = (month_start.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        labels.append(month_start.strftime("%b %Y"))
        
        # Website leads for this month
        website_count = db.query(Lead).filter(
            Lead.source == "website",
            Lead.created_at >= month_start,
            Lead.created_at <= month_end
        ).count()
        website_data.append(website_count)
        
        # Social leads for this month
        social_count = db.query(Lead).filter(
            Lead.source == "social",
            Lead.created_at >= month_start,
            Lead.created_at <= month_end
        ).count()
        social_data.append(social_count)
    
    return {
        "labels": labels,
        "website": website_data,
        "social": social_data
    }

def get_team_performance(db: Session, start_date=None):
    """Get team performance data"""
    teams = db.query(Team).all()
    labels = []
    data = []
    
    for team in teams:
        # Count leads assigned to team members
        team_leads = db.query(LeadAssignment).join(
            Employee, LeadAssignment.employee_id == Employee.employee_id
        ).filter(
            Employee.team_id == team.team_id
        )
        
        if start_date:
            team_leads = team_leads.filter(LeadAssignment.assigned_at >= start_date)
        
        lead_count = team_leads.count()
        
        labels.append(team.name)
        data.append(lead_count)
    
    return {
        "labels": labels,
        "data": data
    }

def get_recent_activities(db: Session, limit: int = 10):
    """Get recent activities for timeline using unified Lead model"""
    activities = []
    
    # Recent website leads
    recent_website = db.query(Lead).filter(Lead.source == "website").order_by(Lead.created_at.desc()).limit(5).all()
    for lead in recent_website:
        activities.append({
            "type": "website",
            "title": f"New Website Lead: {lead.name}",
            "description": f"Contact: {lead.contact}",
            "time": lead.created_at.strftime("%d %b %Y %H:%M")
        })
    
    # Recent social leads
    recent_social = db.query(Lead).filter(Lead.source == "social").order_by(Lead.created_at.desc()).limit(5).all()
    for lead in recent_social:
        activities.append({
            "type": "social",
            "title": f"New Social Lead: {lead.name}",
            "description": f"Platform: {lead.platform_name or 'Unknown'}",
            "time": lead.created_at.strftime("%d %b %Y %H:%M")
        })
    
    # Recent conversions
    recent_conversions = db.query(LeadAssignment).join(Lead).filter(
        LeadAssignment.status.in_(["approved", "disbursed"])
    ).order_by(LeadAssignment.last_updated.desc()).limit(5).all()
    
    for conversion in recent_conversions:
        try:
            lead_source = conversion.lead.source if conversion.lead else "Unknown"
            activities.append({
                "type": "conversion",
                "title": f"Lead Converted",
                "description": f"Lead ID: {conversion.lead_id} ({lead_source})",
                "time": conversion.last_updated.strftime("%d %b %Y %H:%M") if conversion.last_updated else "N/A"
            })
        except Exception as e:
            print(f"Error processing conversion: {e}")
            activities.append({
                "type": "conversion",
                "title": f"Lead Converted",
                "description": f"Lead ID: {conversion.lead_id} (Unknown)",
                "time": "N/A"
            })
    
    # Sort by time and return top activities
    activities.sort(key=lambda x: x["time"], reverse=True)
    return activities[:limit]

@router.get("/analytics/data", response_class=JSONResponse)
def analytics_data_api(request: Request, filter: str = "all", db: Session = Depends(get_db)):
    """API endpoint for filtered analytics data"""
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    analytics_data = get_analytics_data(db, filter)
    return JSONResponse(analytics_data)

@router.get("/employees", response_class=HTMLResponse)
def employees_list(request: Request, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    # Get all employees with their user details and team info
    employees = db.query(Employee).join(User).outerjoin(Team, Employee.team_id == Team.team_id).all()
    
    # Calculate stats
    total_employees = len(employees)
    active_employees = len([e for e in employees if e.is_active])
    assigned_leads = db.query(LeadAssignment).count()
    total_salary = sum([e.salary for e in employees if e.is_active])
    
    return templates.TemplateResponse("employees.html", {
        "request": request,
        "employees": employees,
        "total_employees": total_employees,
        "active_employees": active_employees,
        "assigned_leads": assigned_leads,
        "total_salary": total_salary
    })

@router.get("/employees/new", response_class=HTMLResponse)
def employee_new_get(request: Request, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    teams = db.query(Team).all()
    print(f"DEBUG: Found {len(teams)} teams in employee_new_get route")
    for team in teams:
        print(f"DEBUG: Team - ID: {team.team_id}, Name: {team.name}")
    
    # Get users who are not already employees
    existing_employee_user_ids = db.query(Employee.user_id).all()
    existing_employee_user_ids = [user_id[0] for user_id in existing_employee_user_ids]
    users = db.query(User).filter(
        User.user_id.notin_(existing_employee_user_ids)
    ).all()
    return templates.TemplateResponse("employee_new.html", {
        "request": request,
        "teams": teams,
        "users": users
    })

@router.post("/employees/new", response_class=HTMLResponse)
def employee_new_post(request: Request, user_id: int = Form(...), employee_code: str = Form(...), designation: str = Form(...), department: str = Form(...), team_id: str = Form(""), joining_date: str = Form(...), salary: float = Form(...), commission_rate: float = Form(...), db: Session = Depends(get_db)):
    # Manual authentication check
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    current_user = db.query(User).filter(User.user_id == current_user_id).first()
    if not current_user or current_user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    # Check if employee code already exists
    existing_employee = db.query(Employee).filter(Employee.employee_code == employee_code).first()
    if existing_employee:
        teams = db.query(Team).all()
        existing_employee_user_ids = db.query(Employee.user_id).all()
        existing_employee_user_ids = [user_id[0] for user_id in existing_employee_user_ids]
        users = db.query(User).filter(
            User.user_id.notin_(existing_employee_user_ids)
        ).all()
        return templates.TemplateResponse("employee_new.html", {
            "request": request,
            "teams": teams,
            "users": users,
            "error": "Employee code already exists"
        })
    
    # Check if user is already an employee
    existing_employee_user = db.query(Employee).filter(Employee.user_id == user_id).first()
    if existing_employee_user:
        teams = db.query(Team).all()
        existing_employee_user_ids = db.query(Employee.user_id).all()
        existing_employee_user_ids = [user_id[0] for user_id in existing_employee_user_ids]
        users = db.query(User).filter(
            User.user_id.notin_(existing_employee_user_ids)
        ).all()
        return templates.TemplateResponse("employee_new.html", {
            "request": request,
            "teams": teams,
            "users": users,
            "error": "User is already an employee"
        })
    
    # Create employee
    from datetime import datetime
    joining_date_obj = datetime.strptime(joining_date, "%Y-%m-%d").date()
    
    employee = Employee(
        user_id=user_id,
        employee_code=employee_code,
        designation=designation,
        department=department,
        team_id=int(team_id) if team_id else None,
        joining_date=joining_date_obj,
        salary=salary,
        commission_rate=commission_rate,
        is_active=True
    )
    db.add(employee)
    db.commit()
    
    return RedirectResponse("/crm/employees", status_code=status.HTTP_302_FOUND)

@router.get("/employees/{employee_id}", response_class=HTMLResponse)
def employee_profile(request: Request, employee_id: int, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get assigned leads
    assigned_leads = db.query(LeadAssignment).filter(LeadAssignment.employee_id == employee_id).all()
    
    # Calculate stats
    total_assigned = len(assigned_leads)
    converted_leads = len([l for l in assigned_leads if l.status == "converted"])
    
    return templates.TemplateResponse("employee_profile.html", {
        "request": request,
        "employee": employee,
        "assigned_leads": assigned_leads,
        "total_assigned": total_assigned,
        "converted_leads": converted_leads
    })

@router.get("/employees/{employee_id}/edit", response_class=HTMLResponse)
def employee_edit_get(request: Request, employee_id: int, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    teams = db.query(Team).all()
    
    return templates.TemplateResponse("employee_edit.html", {
        "request": request,
        "employee": employee,
        "teams": teams
    })

@router.post("/employees/{employee_id}/edit", response_class=HTMLResponse)
def employee_edit_post(request: Request, employee_id: int, designation: str = Form(...), department: str = Form(...), team_id: str = Form(""), salary: float = Form(...), commission_rate: float = Form(...), db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    employee.designation = designation
    employee.department = department
    employee.team_id = int(team_id) if team_id and team_id.strip() else None
    employee.salary = salary
    employee.commission_rate = commission_rate
    
    db.commit()
    
    return RedirectResponse("/crm/employees", status_code=status.HTTP_302_FOUND)

@router.get("/employees/{employee_id}/profile", response_class=HTMLResponse)
def employee_profile_redirect(request: Request, employee_id: int):
    return RedirectResponse(f"/crm/employees/{employee_id}", status_code=status.HTTP_302_FOUND)

@router.get("/employees/{employee_id}/billing", response_class=HTMLResponse)
def employee_billing_redirect(request: Request, employee_id: int):
    return RedirectResponse("/crm/billing", status_code=status.HTTP_302_FOUND)

@router.get("/teams", response_class=HTMLResponse)
def teams_list(request: Request, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    # Get all teams with their members and managers
    teams = db.query(Team).outerjoin(Employee, Team.manager_id == Employee.employee_id).all()
    
    # Calculate team stats
    for team in teams:
        # Count team members
        member_count = db.query(Employee).filter(Employee.team_id == team.team_id).count()
        team.member_count = member_count
        
        # Count leads assigned to team members
        team_employee_ids = [e.employee_id for e in db.query(Employee).filter(Employee.team_id == team.team_id).all()]
        lead_count = db.query(LeadAssignment).filter(LeadAssignment.employee_id.in_(team_employee_ids)).count()
        team.lead_count = lead_count
        
        # Count converted leads
        converted_count = db.query(LeadAssignment).filter(
            LeadAssignment.employee_id.in_(team_employee_ids),
            LeadAssignment.status == "converted"
        ).count()
        team.converted_count = converted_count
    
    return templates.TemplateResponse("teams.html", {
        "request": request,
        "teams": teams
    })

@router.get("/teams/new", response_class=HTMLResponse)
def team_new_get(request: Request, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    # Get all employees who can be managers
    employees = db.query(Employee).join(User).filter(Employee.is_active == True).all()
    
    return templates.TemplateResponse("team_new.html", {
        "request": request,
        "employees": employees
    })

@router.post("/teams/new", response_class=HTMLResponse)
def team_new_post(request: Request, name: str = Form(...), manager_id: str = Form(""), db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    # Check if team name already exists
    existing_team = db.query(Team).filter(Team.name == name).first()
    if existing_team:
        employees = db.query(Employee).join(User).filter(Employee.is_active == True).all()
        return templates.TemplateResponse("team_new.html", {
            "request": request,
            "employees": employees,
            "error": "Team name already exists"
        })
    
    # Create new team (without description field since Team model doesn't have it)
    team = Team(
        name=name,
        manager_id=int(manager_id) if manager_id else None
    )
    db.add(team)
    db.commit()
    
    return RedirectResponse("/crm/teams", status_code=status.HTTP_302_FOUND)

@router.get("/teams/{team_id}/members", response_class=HTMLResponse)
def team_members(request: Request, team_id: int, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    members = db.query(Employee).filter(Employee.team_id == team_id).all()
    
    return templates.TemplateResponse("team_members.html", {
        "request": request,
        "team": team,
        "members": members
    })

@router.get("/teams/{team_id}/performance", response_class=HTMLResponse)
def team_performance(request: Request, team_id: int, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get team performance data
    leads_count = db.query(LeadAssignment).join(Employee, LeadAssignment.employee_id == Employee.employee_id).filter(Employee.team_id == team_id).count()
    converted_count = db.query(LeadAssignment).join(Employee, LeadAssignment.employee_id == Employee.employee_id).filter(
        Employee.team_id == team_id, 
        LeadAssignment.status == "converted"
    ).count()
    
    # Get team members count
    members_count = db.query(Employee).filter(Employee.team_id == team_id).count()
    
    conversion_rate = (converted_count / leads_count * 100) if leads_count > 0 else 0
    
    return templates.TemplateResponse("team_performance.html", {
        "request": request,
        "team": team,
        "leads_count": leads_count,
        "converted_count": converted_count,
        "conversion_rate": conversion_rate,
        "members_count": members_count
    })

@router.get("/teams/{team_id}/delete", response_class=HTMLResponse)
def delete_team(request: Request, team_id: int, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if team has members
    team_members = db.query(Employee).filter(Employee.team_id == team_id).count()
    if team_members > 0:
        # Get team members for display
        members = db.query(Employee).filter(Employee.team_id == team_id).all()
        return templates.TemplateResponse("teams.html", {
            "request": request,
            "teams": db.query(Team).all(),
            "error": f"Cannot delete team '{team.name}' because it has {team_members} member(s). Please reassign or remove members first.",
            "team_members": members,
            "team_to_delete": team
        })
    
    try:
        # Delete the team
        db.delete(team)
        db.commit()
        return RedirectResponse("/crm/teams", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("teams.html", {
            "request": request,
            "teams": db.query(Team).all(),
            "error": f"Error deleting team: {str(e)}"
        })

@router.get("/teams/{team_id}/force-delete", response_class=HTMLResponse)
def force_delete_team(request: Request, team_id: int, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    try:
        # Remove team assignments from all employees
        db.query(Employee).filter(Employee.team_id == team_id).update({"team_id": None})
        
        # Delete the team
        db.delete(team)
        db.commit()
        return RedirectResponse("/crm/teams", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("teams.html", {
            "request": request,
            "teams": db.query(Team).all(),
            "error": f"Error force deleting team: {str(e)}"
        })

@router.get("/billing", response_class=HTMLResponse)
def billing_list(request: Request, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    # Get all billing records with employee details
    billings = db.query(Billing).join(Employee).join(User).order_by(Billing.generated_at.desc()).all()
    
    # Calculate stats
    total_salary = sum([b.basic_salary for b in billings])
    total_commission = sum([b.commission_earned for b in billings])
    paid_bills = len([b for b in billings if b.payment_status == "paid"])
    pending_bills = len([b for b in billings if b.payment_status == "pending"])
    
    # Get paid and pending bills for display
    paid_bills_list = [b for b in billings if b.payment_status == "paid"]
    pending_bills_list = [b for b in billings if b.payment_status == "pending"]
    
    return templates.TemplateResponse("billing.html", {
        "request": request,
        "billings": billings,
        "total_salary": total_salary,
        "total_commission": total_commission,
        "paid_bills": paid_bills,
        "pending_bills": pending_bills,
        "paid_bills_list": paid_bills_list,
        "pending_bills_list": pending_bills_list
    })

@router.post("/billing/{billing_id}/mark-paid")
def mark_billing_paid(request: Request, billing_id: int, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    billing = db.query(Billing).filter(Billing.billing_id == billing_id).first()
    if not billing:
        raise HTTPException(status_code=404, detail="Billing record not found")
    
    billing.payment_status = "paid"
    billing.payment_date = datetime.utcnow()
    db.commit()
    
    return RedirectResponse("/crm/billing", status_code=status.HTTP_302_FOUND)

@router.get("/billing/generate", response_class=HTMLResponse)
def generate_billing_get(request: Request, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    # Get all active employees
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    
    from datetime import datetime
    current_year = datetime.now().year
    
    return templates.TemplateResponse("generate_billing.html", {
        "request": request,
        "employees": employees,
        "current_year": current_year
    })

@router.post("/billing/generate", response_class=HTMLResponse)
def generate_billing_post(request: Request, month: int = Form(...), year: int = Form(...), db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    # Get all active employees
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    
    # Check if billing already exists for this month/year
    existing_billing = db.query(Billing).filter(
        Billing.month == month,
        Billing.year == year
    ).first()
    
    if existing_billing:
        return templates.TemplateResponse("generate_billing.html", {
            "request": request,
            "employees": employees,
            "error": f"Billing for {month}/{year} already exists"
        })
    
    # Generate billing for each employee
    total_basic_salary = 0
    total_commission = 0
    total_net_salary = 0
    
    for employee in employees:
        # Calculate commission based on lead assignments
        commission_earned = 0.0
        lead_assignments = db.query(LeadAssignment).filter(
            LeadAssignment.employee_id == employee.employee_id,
            LeadAssignment.status == "converted"
        ).all()
        
        for assignment in lead_assignments:
            commission_earned += (employee.commission_rate / 100) * 10000  # Assuming 10k per conversion
        
        # Calculate net salary
        net_salary = employee.salary + commission_earned
        
        # Create billing record
        billing = Billing(
            employee_id=employee.employee_id,
            month=month,
            year=year,
            basic_salary=employee.salary,
            commission_earned=commission_earned,
            deductions=0.0,  # No deductions for now
            net_salary=net_salary,
            payment_status="pending"
        )
        
        db.add(billing)
        
        # Add to totals
        total_basic_salary += employee.salary
        total_commission += commission_earned
        total_net_salary += net_salary
    
    db.commit()
    
    # Redirect to invoice view
    return RedirectResponse(f"/crm/billing/invoice/{month}/{year}", status_code=status.HTTP_302_FOUND)

@router.get("/billing/invoice/{month}/{year}", response_class=HTMLResponse)
def billing_invoice(request: Request, month: int, year: int, db: Session = Depends(get_db)):
    # Manual authentication check
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    
    # Get all billing records for this month/year
    billing_records = db.query(Billing).filter(
        Billing.month == month,
        Billing.year == year
    ).join(Employee).join(User).all()
    
    if not billing_records:
        raise HTTPException(status_code=404, detail="No billing records found for this month/year")
    
    # Calculate totals
    total_basic_salary = sum(record.basic_salary for record in billing_records)
    total_commission = sum(record.commission_earned for record in billing_records)
    total_net_salary = sum(record.net_salary for record in billing_records)
    
    # Get month name
    month_names = {
        1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
        7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
    }
    month_name = month_names.get(month, f"Month {month}")
    
    # Get current date for invoice
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    return templates.TemplateResponse("billing_invoice.html", {
        "request": request,
        "billing_records": billing_records,
        "month": month,
        "year": year,
        "month_name": month_name,
        "total_basic_salary": total_basic_salary,
        "total_commission": total_commission,
        "total_net_salary": total_net_salary,
        "current_date": current_date
    })

@router.get("/profile", response_class=HTMLResponse)
def user_profile(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    user_id = request.session.get("user_id")
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user
    })

@router.get("/leads/{lead_type}/{lead_id}/assign", response_class=HTMLResponse)
def assign_lead_get(request: Request, lead_type: str, lead_id: int, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    # Try to find the corresponding unified lead
    unified_lead = db.query(Lead).filter(
        Lead.source == lead_type,
        Lead.additional_data.contains({"migrated_from": f"{lead_type}_leads", "original_id": lead_id})
    ).first()
    
    if unified_lead:
        return RedirectResponse(f"/crm/unified-leads/{unified_lead.lead_id}", status_code=status.HTTP_302_FOUND)
    else:
        # If not found, redirect to unified leads list
        return RedirectResponse("/crm/unified-leads", status_code=status.HTTP_302_FOUND)
    
    # Get all active employees
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    
    return templates.TemplateResponse("assign_lead.html", {
        "request": request,
        "lead": lead,
        "lead_type": lead_type,
        "lead_name": lead_name,
        "employees": employees
    })

@router.post("/leads/{lead_type}/{lead_id}/assign", response_class=HTMLResponse)
def assign_lead_post(request: Request, lead_type: str, lead_id: int, employee_id: int = Form(...), notes: str = Form(""), db: Session = Depends(get_db)):
    """Redirect old assignment route to unified system"""
    # Try to find the corresponding unified lead
    unified_lead = db.query(Lead).filter(
        Lead.source == lead_type,
        Lead.additional_data.contains({"migrated_from": f"{lead_type}_leads", "original_id": lead_id})
    ).first()
    
    if unified_lead:
        return RedirectResponse(f"/crm/unified-leads/{unified_lead.lead_id}", status_code=status.HTTP_302_FOUND)
    else:
        # If not found, redirect to unified leads list
        return RedirectResponse("/crm/unified-leads", status_code=status.HTTP_302_FOUND)

@router.get("/leads/{lead_type}/{lead_id}/unassign")
def unassign_lead(request: Request, lead_type: str, lead_id: int, db: Session = Depends(get_db)):
    """Redirect old unassign route to unified system"""
    # Try to find the corresponding unified lead
    unified_lead = db.query(Lead).filter(
        Lead.source == lead_type,
        Lead.additional_data.contains({"migrated_from": f"{lead_type}_leads", "original_id": lead_id})
    ).first()
    
    if unified_lead:
        return RedirectResponse(f"/crm/unified-leads/{unified_lead.lead_id}", status_code=status.HTTP_302_FOUND)
    else:
        # If not found, redirect to unified leads list
        return RedirectResponse("/crm/unified-leads", status_code=status.HTTP_302_FOUND)

# Lead Status and Comment Management
@router.post("/leads/{assignment_id}/update-status", response_class=JSONResponse)
def update_lead_status(
    assignment_id: int,
    request: Request,
    new_status: str = Form(...),
    comment: str = Form(None),
    db: Session = Depends(get_db)
):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_role = request.session.get("user_role")
    current_employee = get_current_employee(request, db)
    
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    # Get the assignment
    assignment = db.query(LeadAssignment).filter(LeadAssignment.assignment_id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Lead assignment not found")
    
    # Check if user can manage this lead
    if not can_manage_lead(assignment, current_employee, user_role):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate status transition
    if new_status not in LEAD_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    next_statuses = get_next_statuses(assignment.status)
    if new_status not in next_statuses and new_status != assignment.status:
        raise HTTPException(status_code=400, detail=f"Invalid status transition. Current: {assignment.status}, Allowed: {next_statuses}")
    
    try:
        # Update status
        assignment.status = new_status
        assignment.last_updated = datetime.now()
        
        # Add comment if provided
        if comment and comment.strip():
            lead_comment = LeadComment(
                assignment_id=assignment_id,
                employee_id=current_employee.employee_id,
                comment=comment.strip()
            )
            db.add(lead_comment)
        
        db.commit()
        
        return JSONResponse({
            "success": True,
            "message": f"Lead status updated to {LEAD_STATUSES[new_status]}",
            "new_status": new_status,
            "status_display": LEAD_STATUSES[new_status]
        })
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")

@router.post("/leads/{assignment_id}/add-comment", response_class=JSONResponse)
def add_lead_comment(
    assignment_id: int,
    request: Request,
    comment: str = Form(...),
    db: Session = Depends(get_db)
):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_role = request.session.get("user_role")
    current_employee = get_current_employee(request, db)
    
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    # Get the assignment
    assignment = db.query(LeadAssignment).filter(LeadAssignment.assignment_id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Lead assignment not found")
    
    # Check if user can manage this lead
    if not can_manage_lead(assignment, current_employee, user_role):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not comment or not comment.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty")
    
    try:
        lead_comment = LeadComment(
            assignment_id=assignment_id,
            employee_id=current_employee.employee_id,
            comment=comment.strip()
        )
        db.add(lead_comment)
        db.commit()
        
        return JSONResponse({
            "success": True,
            "message": "Comment added successfully",
            "comment": {
                "id": lead_comment.comment_id,
                "comment": lead_comment.comment,
                "created_at": lead_comment.created_at.strftime("%Y-%m-%d %H:%M"),
                "employee_name": current_employee.user.name
            }
        })
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding comment: {str(e)}")

@router.post("/leads/{assignment_id}/toggle-doable", response_class=JSONResponse)
def toggle_doable_flag(
    assignment_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Toggle the doable flag for a lead assignment"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_role = request.session.get("user_role")
    current_employee = get_current_employee(request, db)
    
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    # Get the assignment
    assignment = db.query(LeadAssignment).filter(LeadAssignment.assignment_id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Lead assignment not found")
    
    # Check if user can manage this lead
    if not can_manage_lead(assignment, current_employee, user_role):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Toggle the doable flag
        assignment.is_doable = not assignment.is_doable
        
        # If marked as not doable, automatically set status to closed
        if not assignment.is_doable:
            assignment.status = "closed"
        
        # Add a comment about the change
        status_text = "Not Doable" if not assignment.is_doable else "Doable"
        comment_text = f"Lead marked as {status_text}"
        if not assignment.is_doable:
            comment_text += " and automatically closed"
        
        new_comment = LeadComment(
            assignment_id=assignment_id,
            employee_id=current_employee.employee_id,
            comment=comment_text
        )
        db.add(new_comment)
        db.commit()
        
        return JSONResponse({
            "success": True,
            "message": f"Lead marked as {status_text}",
            "is_doable": assignment.is_doable,
            "status": assignment.status,
            "status_display": LEAD_STATUSES[assignment.status]
        })
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error toggling doable flag: {str(e)}")

@router.get("/leads/{assignment_id}/comments", response_class=JSONResponse)
def get_lead_comments(
    assignment_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_role = request.session.get("user_role")
    current_employee = get_current_employee(request, db)
    
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    # Get the assignment
    assignment = db.query(LeadAssignment).filter(LeadAssignment.assignment_id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Lead assignment not found")
    
    # Check if user can view this lead
    if not can_manage_lead(assignment, current_employee, user_role):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get comments with employee names
    comments = db.query(LeadComment, Employee, User).join(
        Employee, LeadComment.employee_id == Employee.employee_id
    ).join(
        User, Employee.user_id == User.user_id
    ).filter(
        LeadComment.assignment_id == assignment_id
    ).order_by(LeadComment.created_at.desc()).all()
    
    comments_data = []
    for comment, employee, user in comments:
        comments_data.append({
            "id": comment.comment_id,
            "comment": comment.comment,
            "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
            "employee_name": user.name,
            "employee_code": employee.employee_code
        })
    
    return JSONResponse({"comments": comments_data})

# Enhanced Lead Assignment with Role-Based Access (Redirect to Unified System)
@router.post("/leads/{lead_type}/{lead_id}/assign", response_class=JSONResponse)
def assign_lead(
    lead_type: str,
    lead_id: int,
    request: Request,
    employee_id: int = Form(...),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Redirect old assignment route to unified system"""
    # Try to find the corresponding unified lead
    unified_lead = db.query(Lead).filter(
        Lead.source == lead_type,
        Lead.additional_data.contains({"migrated_from": f"{lead_type}_leads", "original_id": lead_id})
    ).first()
    
    if unified_lead:
        # Use the unified assignment route
        return assign_unified_lead(request, unified_lead.lead_id, employee_id, notes, db)
    else:
        raise HTTPException(status_code=404, detail="Lead not found in unified system")

# ============================================================================
# UNIFIED LEAD MANAGEMENT ROUTES
# ============================================================================

@router.get("/unified-leads", response_class=HTMLResponse)
def unified_leads_list(request: Request, db: Session = Depends(get_db)):
    """Display all unified leads with filtering options"""
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    user_role = request.session.get("user_role")
    current_employee = get_current_employee(request, db)
    
    # Get filter parameters
    status_filter = request.query_params.get("status", "")
    source_filter = request.query_params.get("source", "")
    employee_filter = request.query_params.get("employee", "")
    
    # Build filters
    filters = {}
    if status_filter:
        filters['status'] = status_filter
    if source_filter:
        filters['source'] = source_filter
    if employee_filter and user_role in ["admin", "manager"]:
        filters['employee_id'] = int(employee_filter)
    elif user_role == "employee" and current_employee:
        filters['employee_id'] = current_employee.employee_id
    
    # Get leads with assignment information
    leads = LeadService.get_all_leads(db, filters)
    
    # Get assignment information for each lead
    for lead in leads:
        assignment = db.query(LeadAssignment).filter(LeadAssignment.lead_id == lead.lead_id).first()
        if assignment:
            lead.assignment = assignment
            # Get employee name for assignment
            employee = db.query(Employee).filter(Employee.employee_id == assignment.employee_id).first()
            if employee:
                user = db.query(User).filter(User.user_id == employee.user_id).first()
                lead.assignee_name = user.name if user else "Unknown"
            else:
                lead.assignee_name = "Unknown"
        else:
            lead.assignment = None
            lead.assignee_name = None
    
    # Get employees for filter dropdown (admin/manager only)
    employees = []
    if user_role in ["admin", "manager"]:
        employees = db.query(Employee).join(User).filter(Employee.is_active == True).all()
    
    return templates.TemplateResponse("unified_leads.html", {
        "request": request,
        "leads": leads,
        "employees": employees,
        "statuses": LeadService.LEAD_STATUSES,
        "current_filters": {
            "status": status_filter,
            "source": source_filter,
            "employee": employee_filter
        }
    })

@router.get("/unified-leads/{lead_id}", response_class=HTMLResponse)
def unified_lead_detail(request: Request, lead_id: int, db: Session = Depends(get_db)):
    """Display detailed view of a unified lead with timeline"""
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    
    
    # Get current assignment
    assignment = db.query(LeadAssignment).filter(LeadAssignment.lead_id == lead_id).first()
    
    # Get timeline
    timeline = LeadService.get_lead_timeline(db, lead_id)
    
    # Get comments for this lead
    comments = []
    if assignment:
        comments = db.query(LeadComment).filter(LeadComment.assignment_id == assignment.assignment_id).order_by(LeadComment.created_at.desc()).all()
    
    # Get next possible statuses
    if assignment:
        next_statuses = LeadService.get_next_possible_statuses(assignment.status)
    else:
        next_statuses = LeadService.get_next_possible_statuses(lead.status)
    
    # Get employees for assignment (admin/manager only)
    user_role = request.session.get("user_role")
    employees = []
    if user_role in ["admin", "manager"]:
        employees = db.query(Employee).join(User).filter(Employee.is_active == True).all()
    else:
        # For other users, still pass empty list to avoid template errors
        employees = []
    
    # Get workflow progress for visualization
    workflow_progress = LeadService.get_workflow_progress(lead, assignment)
    
    # Get current employee for permissions
    current_employee = get_current_employee(request, db)
    
    # Helper function for comment deletion permission
    def can_delete_comment(comment_employee_id):
        if not current_employee:
            return False
        user_role = request.session.get("user_role")
        return user_role in ['admin', 'manager'] or comment_employee_id == current_employee.employee_id
    
    # Helper function for lead update permission
    def can_update_lead():
        if not current_employee:
            return False
        user_role = request.session.get("user_role")
        return user_role in ['admin', 'manager'] or (assignment and assignment.employee_id == current_employee.employee_id)
    
    response = templates.TemplateResponse("unified_lead_detail.html", {
        "request": request,
        "lead": lead,
        "assignment": assignment,
        "timeline": timeline,
        "comments": comments,
        "next_statuses": next_statuses,
        "statuses": LeadService.LEAD_STATUSES,
        "status_descriptions": LeadService.STATUS_DESCRIPTIONS,
        "workflow_progress": workflow_progress,
        "employees": employees,
        "can_delete_comment": can_delete_comment,
        "can_update_lead": can_update_lead,
        "cache_buster": datetime.now().timestamp()  # Add cache buster
    })
    
    # Add cache-busting headers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    return response

@router.post("/unified-leads/{lead_id}/assign", response_class=JSONResponse)
def assign_unified_lead(request: Request, lead_id: int, employee_id: int = Form(...), notes: str = Form(None), db: Session = Depends(get_db)):
    """Assign a unified lead to an employee"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_role = request.session.get("user_role")
    current_employee = get_current_employee(request, db)
    
    if not current_employee or user_role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin and manager can assign leads")
    
    try:
        print(f"DEBUG: Attempting to assign lead {lead_id} to employee {employee_id}")
        
        # Check if lead exists
        lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()
        if not lead:
            print(f"DEBUG: Lead {lead_id} not found")
            raise HTTPException(status_code=404, detail="Lead not found")
        print(f"DEBUG: Found lead {lead_id} - {lead.name}")
        
        # Check if employee exists
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            print(f"DEBUG: Employee {employee_id} not found")
            raise HTTPException(status_code=404, detail="Employee not found")
        print(f"DEBUG: Found employee {employee_id} - {employee.user.name}")
        
        # Check if lead is already assigned
        existing_assignment = db.query(LeadAssignment).filter(LeadAssignment.lead_id == lead_id).first()
        if existing_assignment:
            print(f"DEBUG: Lead {lead_id} is already assigned")
            raise HTTPException(status_code=400, detail="Lead is already assigned")
        print(f"DEBUG: Lead {lead_id} is not already assigned")
        
        # Create assignment manually to avoid any service issues
        print(f"DEBUG: Creating assignment manually")
        assignment = LeadAssignment(
            lead_id=lead_id,
            employee_id=employee_id,
            assigned_by=current_employee.employee_id,
            notes=notes,
            status='assigned'
        )
        db.add(assignment)
        
        # Update lead status
        lead.status = 'assigned'
        
        db.commit()
        db.refresh(assignment)
        
        # Log activity
        LeadService.log_activity(
            db=db,
            lead_id=lead_id,
            employee_id=current_employee.employee_id,
            activity_type='assigned',
            description=f'Lead assigned to {employee.user.name}',
            activity_data={'assigned_to': employee_id, 'notes': notes}
        )
        
        print(f"DEBUG: Final commit successful")
        
        db.refresh(assignment)
        print(f"DEBUG: Assignment successful - ID: {assignment.assignment_id}")
        
        return JSONResponse({
            "success": True,
            "message": "Lead assigned successfully",
            "assignment_id": assignment.assignment_id
        })
    except HTTPException:
        raise
    except Exception as e:
        print(f"Assignment error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Assignment failed: {str(e)}")

@router.post("/unified-leads/{lead_id}/reassign", response_class=JSONResponse)
def reassign_unified_lead(request: Request, lead_id: int, employee_id: int = Form(...), notes: str = Form(None), db: Session = Depends(get_db)):
    """Reassign a unified lead to a different employee"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_role = request.session.get("user_role")
    current_employee = get_current_employee(request, db)
    
    if not current_employee or user_role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin and manager can reassign leads")
    
    try:
        # Check if lead exists
        lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Check if employee exists
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Check if lead is assigned
        existing_assignment = db.query(LeadAssignment).filter(LeadAssignment.lead_id == lead_id).first()
        if not existing_assignment:
            raise HTTPException(status_code=400, detail="Lead is not assigned yet")
        
        # Store old assignment info for logging
        old_employee_id = existing_assignment.employee_id
        old_employee = db.query(Employee).filter(Employee.employee_id == old_employee_id).first()
        
        # Update assignment
        existing_assignment.employee_id = employee_id
        existing_assignment.assigned_by = current_employee.employee_id
        existing_assignment.assigned_at = datetime.now()
        if notes:
            existing_assignment.notes = notes
        
        db.commit()
        
        # Log activity
        LeadService.log_activity(
            db=db,
            lead_id=lead_id,
            employee_id=current_employee.employee_id,
            activity_type='lead_reassigned',
            description=f'Lead reassigned from {old_employee.user.name} to {employee.user.name}',
            activity_data={
                'old_employee_id': old_employee_id,
                'new_employee_id': employee_id,
                'notes': notes
            }
        )
        
        return JSONResponse({
            "success": True,
            "message": "Lead reassigned successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Reassignment failed: {str(e)}")

@router.post("/unified-leads/assignment/{assignment_id}/update-status", response_class=JSONResponse)
def update_unified_lead_status(request: Request, assignment_id: int, new_status: str = Form(...), comment: str = Form(None), close_type: str = Form(None), db: Session = Depends(get_db)):
    """Update status of a unified lead assignment"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    try:
        print(f"DEBUG: Updating status for assignment {assignment_id} to {new_status}")
        success = LeadService.update_lead_status(db, assignment_id, new_status, current_employee.employee_id, comment, close_type=close_type)
        if success:
            message = "Status updated successfully"
            if new_status == 'closed' and close_type:
                message += f" - Closed as: {LeadService.CLOSE_TYPES.get(close_type, close_type)}"
            return JSONResponse({"success": True, "message": message})
        else:
            raise HTTPException(status_code=404, detail="Assignment not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating status: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")

@router.post("/unified-leads/assignment/{assignment_id}/toggle-doable", response_class=JSONResponse)
def toggle_unified_lead_doable(request: Request, assignment_id: int, is_doable: bool = Form(...), db: Session = Depends(get_db)):
    """Toggle doable status of a unified lead"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    try:
        success = LeadService.toggle_doable_status(db, assignment_id, current_employee.employee_id, is_doable)
        if success:
            return JSONResponse({"success": True, "message": "Doable status updated successfully"})
        else:
            raise HTTPException(status_code=404, detail="Assignment not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unified-leads/assignment/{assignment_id}/add-comment", response_class=JSONResponse)
def add_unified_lead_comment(request: Request, assignment_id: int, comment: str = Form(...), db: Session = Depends(get_db)):
    """Add a comment to a unified lead assignment"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    try:
        # Get the assignment to find the lead_id
        assignment = db.query(LeadAssignment).filter(LeadAssignment.assignment_id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        lead_comment = LeadService.add_comment(db, assignment.lead_id, current_employee.employee_id, comment)
        if lead_comment:
            return JSONResponse({"success": True, "message": "Comment added successfully", "comment_id": lead_comment.comment_id})
        else:
            raise HTTPException(status_code=500, detail="Failed to add comment")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding comment: {str(e)}")

@router.get("/unified-leads/{lead_id}/timeline", response_class=JSONResponse)
def get_unified_lead_timeline(request: Request, lead_id: int, db: Session = Depends(get_db)):
    """Get timeline for a unified lead"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        print(f"DEBUG: Getting timeline for lead {lead_id}")
        timeline = LeadService.get_lead_timeline(db, lead_id)
        print(f"DEBUG: Timeline data: {timeline}")
        
        # Additional JSON serialization check
        import json
        # Test if the timeline is JSON serializable
        json.dumps({"timeline": timeline})
        
        return JSONResponse({"timeline": timeline})
    except TypeError as e:
        # If there are still datetime objects, handle them
        print(f"JSON serialization error in timeline: {e}")
        # Return empty timeline as fallback
        return JSONResponse({"timeline": []})
    except Exception as e:
        print(f"Error getting timeline: {e}")
        return JSONResponse({"timeline": []})

@router.post("/unified-leads/create-manual", response_class=JSONResponse)
def create_manual_unified_lead(
    request: Request,
    name: str = Form(...),
    contact: str = Form(...),
    email: str = Form(None),
    city: str = Form(None),
    date_of_birth: str = Form(None),
    loan_amount: float = Form(None),
    loan_type: str = Form(None),
    occupation: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create a manual unified lead"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_role = request.session.get("user_role")
    if user_role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin and manager can create leads")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    try:
        lead = LeadService.create_manual_lead(
            db=db,
            name=name,
            contact=contact,
            email=email,
            city=city,
            date_of_birth=date_of_birth,
            loan_amount=loan_amount,
            loan_type=loan_type,
            occupation=occupation,
            created_by_employee_id=current_employee.employee_id
        )
        return JSONResponse({
            "success": True,
            "message": "Lead created successfully",
            "lead_id": lead.lead_id
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unified-leads/migrate", response_class=JSONResponse)
def migrate_existing_leads(request: Request, db: Session = Depends(get_db)):
    """Migrate existing leads to unified system"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_role = request.session.get("user_role")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can migrate leads")
    
    try:
        migrated_counts = LeadService.migrate_existing_leads(db)
        return JSONResponse({
            "success": True,
            "message": "Migration completed successfully",
            "migrated": migrated_counts
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unified-leads/bulk-upload", response_class=JSONResponse)
async def bulk_upload_unified_leads(request: Request, file: UploadFile = File(...), skip_duplicates: bool = Form(True), db: Session = Depends(get_db)):
    """Bulk upload leads from CSV file"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_role = request.session.get("user_role")
    if user_role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin and manager can bulk upload leads")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        content = await file.read()
        result = LeadService.bulk_import_leads(
            db=db,
            csv_content=content.decode('utf-8'),
            created_by_employee_id=current_employee.employee_id,
            skip_duplicates=skip_duplicates
        )
        
        return JSONResponse({
            "success": True,
            "message": "Bulk upload completed",
            "success_count": result["success_count"],
            "skipped_count": result["skipped_count"],
            "error_count": result["error_count"],
            "errors": result.get("errors", [])
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.get("/unified-leads/bulk-upload/template.csv")
def download_unified_leads_template():
    """Download CSV template for bulk upload"""
    csv_content = "name,contact,email,city,date_of_birth,loan_amount,loan_type,occupation,message\n"
    csv_content += "John Doe,9876543210,john@example.com,Mumbai,1990-01-15,500000,personal,Engineer,Interested in personal loan\n"
    csv_content += "Jane Smith,9876543211,jane@example.com,Delhi,1985-05-20,750000,business,Business Owner,Need business loan\n"
    csv_content += "Mike Johnson,9876543212,,Bangalore,1992-12-10,300000,personal,Teacher,Looking for quick loan\n"
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=unified_leads_template.csv"}
    )

# Loan Amount Tracking Routes
@router.post("/assignments/{assignment_id}/update-pd-amount", response_class=JSONResponse)
def update_pd_loan_amount(
    request: Request,
    assignment_id: int,
    loan_amount: float = Form(...),
    db: Session = Depends(get_db)
):
    """Update loan amount during PD stage"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    try:
        assignment = LeadService.update_pd_loan_amount(db, assignment_id, loan_amount, current_employee.employee_id)
        return JSONResponse({
            "success": True,
            "message": f"PD completed with loan amount: ₹{loan_amount:,.0f}",
            "assignment_id": assignment.assignment_id
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assignments/{assignment_id}/update-approved-amount", response_class=JSONResponse)
def update_approved_loan_amount(
    request: Request,
    assignment_id: int,
    loan_amount: float = Form(...),
    db: Session = Depends(get_db)
):
    """Update loan amount when approved"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    try:
        assignment = LeadService.update_approved_loan_amount(db, assignment_id, loan_amount, current_employee.employee_id)
        return JSONResponse({
            "success": True,
            "message": f"Loan approved with amount: ₹{loan_amount:,.0f}",
            "assignment_id": assignment.assignment_id
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Disbursement Routes
@router.post("/assignments/{assignment_id}/disburse", response_class=JSONResponse)
def create_disbursement(
    request: Request,
    assignment_id: int,
    amount: float = Form(...),
    disbursement_type: str = Form("full"),
    tranche_number: int = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create a disbursement record"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    try:
        disbursement = LeadService.create_disbursement(
            db=db,
            assignment_id=assignment_id,
            amount=amount,
            disbursement_type=disbursement_type,
            tranche_number=tranche_number,
            notes=notes,
            processed_by=current_employee.employee_id
        )
        return JSONResponse({
            "success": True,
            "message": f"Disbursement created: ₹{amount:,.0f}",
            "disbursement_id": disbursement.disbursement_id
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assignments/{assignment_id}/disbursements", response_class=JSONResponse)
def get_disbursements(request: Request, assignment_id: int, db: Session = Depends(get_db)):
    """Get all disbursements for an assignment"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        disbursements = LeadService.get_disbursements_for_assignment(db, assignment_id)
        total_amount = LeadService.get_total_disbursed_amount(db, assignment_id)
        
        disbursement_data = []
        for disbursement in disbursements:
            processor = db.query(Employee).filter(Employee.employee_id == disbursement.processed_by).first()
            processor_name = processor.user.name if processor and processor.user else "Unknown"
            
            disbursement_data.append({
                "disbursement_id": disbursement.disbursement_id,
                "amount": disbursement.amount,
                "disbursement_type": disbursement.disbursement_type,
                "tranche_number": disbursement.tranche_number,
                "notes": disbursement.notes,
                "processor_name": processor_name,
                "disbursement_date": disbursement.disbursement_date.isoformat() if disbursement.disbursement_date else None,
                "created_at": disbursement.created_at.isoformat() if disbursement.created_at else None
            })
        
        return JSONResponse({
            "disbursements": disbursement_data,
            "total_disbursed": total_amount
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Closed Leads Management
@router.get("/close-leads", response_class=HTMLResponse)
def close_leads_list(request: Request, db: Session = Depends(get_db)):
    """View closed leads"""
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    try:
        close_leads = LeadService.get_close_leads(db, limit=100)
        
        # Calculate stats
        success_count = sum(1 for lead in close_leads if 'Success' in lead['close_message'])
        not_doable_count = sum(1 for lead in close_leads if 'Not Doable' in lead['close_message'])
        total_amount = sum(lead['amount'] or 0 for lead in close_leads)
        
        return templates.TemplateResponse("close_leads.html", {
            "request": request,
            "close_leads": close_leads,
            "success_count": success_count,
            "not_doable_count": not_doable_count,
            "total_amount": total_amount
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/leads/{lead_id}/close", response_class=JSONResponse)
def close_lead(
    request: Request,
    lead_id: int,
    close_type: str = Form(...),  # 'success' or 'not_doable'
    close_reason: str = Form(...),
    db: Session = Depends(get_db)
):
    """Close a lead with two options: success or not doable"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    # Validate close type
    if close_type not in ['success', 'not_doable']:
        raise HTTPException(status_code=400, detail="Invalid close type. Must be 'success' or 'not_doable'")
    
    try:
        print(f"DEBUG: Closing lead {lead_id} with type: {close_type}")
        print(f"DEBUG: Close reason: {close_reason}")
        print(f"DEBUG: Employee ID: {current_employee.employee_id}")
        
        success = LeadService.close_lead(
            db=db,
            lead_id=lead_id,
            close_type=close_type,
            close_reason=close_reason,
            employee_id=current_employee.employee_id
        )
        
        print(f"DEBUG: Close lead result: {success}")
        
        if success:
            close_message = "Closed - Success" if close_type == 'success' else "Closed - Not Doable"
            return JSONResponse({
                "success": True,
                "message": f"Lead closed successfully: {close_message}"
            })
        else:
            raise HTTPException(status_code=404, detail="Lead not found")
    except Exception as e:
        print(f"DEBUG: Error closing lead: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Add Comment to Lead
@router.post("/unified-leads/{lead_id}/add-comment", response_class=JSONResponse)
def add_comment_to_lead(
    request: Request,
    lead_id: int,
    comment: str = Form(...),
    db: Session = Depends(get_db)
):
    """Add a comment to a lead"""
    print(f"DEBUG: Adding comment to lead {lead_id}")
    print(f"DEBUG: Comment: {comment}")
    
    if not request.session.get("user_id"):
        print("DEBUG: No user_id in session")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        print("DEBUG: No current employee found")
        raise HTTPException(status_code=401, detail="Employee not found")
    
    print(f"DEBUG: Current employee: {current_employee.employee_id}")
    
    try:
        # Check if lead exists
        lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()
        if not lead:
            print(f"DEBUG: Lead {lead_id} not found")
            raise HTTPException(status_code=404, detail="Lead not found")
        
        print(f"DEBUG: Found lead {lead_id} - {lead.name}")
        
        # Add comment
        lead_comment = LeadService.add_comment(
            db=db,
            lead_id=lead_id,
            employee_id=current_employee.employee_id,
            comment=comment
        )
        
        print(f"DEBUG: Comment added successfully with ID: {lead_comment.comment_id}")
        
        return JSONResponse({
            "success": True,
            "message": "Comment added successfully",
            "comment_id": lead_comment.comment_id
        })
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Error adding comment: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error adding comment: {str(e)}")

# Delete Comment
@router.post("/comments/{comment_id}/delete", response_class=JSONResponse)
def delete_comment(
    request: Request,
    comment_id: int,
    db: Session = Depends(get_db)
):
    """Delete a comment"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    user_role = request.session.get("user_role")
    
    try:
        success = LeadService.delete_comment(
            db=db,
            comment_id=comment_id,
            employee_id=current_employee.employee_id,
            user_role=user_role
        )
        
        if success:
            return JSONResponse({
                "success": True,
                "message": "Comment deleted successfully"
            })
        else:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update Lead Details (Form)
@router.post("/unified-leads/{lead_id}/update", response_class=JSONResponse)
def update_lead_details_form(
    request: Request,
    lead_id: int,
    name: str = Form(...),
    contact: str = Form(...),
    email: str = Form(None),
    city: str = Form(None),
    loan_amount: float = Form(None),
    loan_type: str = Form(None),
    occupation: str = Form(None),
    occupation_other: str = Form(None),
    any_ongoing_loan: str = Form(None),
    message: str = Form(None),
    other_details: str = Form(None),
    priority: str = Form(None),
    monthly_income: float = Form(None),
    credit_score: int = Form(None),
    employment_type: str = Form(None),
    preferred_contact_time: str = Form(None),
    source_details: str = Form(None),
    db: Session = Depends(get_db)
):
    """Update lead details from form"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    user_role = request.session.get("user_role")
    
    try:
        # Check if user can update this lead
        assignment = db.query(LeadAssignment).filter(LeadAssignment.lead_id == lead_id).first()
        if not LeadService.can_update_lead_info(user_role, assignment):
            raise HTTPException(status_code=403, detail="Not authorized to update this lead")
        
        # Prepare update data
        update_data = {
            'name': name,
            'contact': contact,
            'email': email,
            'city': city,
            'loan_amount': loan_amount,
            'loan_type': loan_type,
            'occupation': occupation,
            'occupation_other': occupation_other,
            'any_ongoing_loan': any_ongoing_loan,
            'message': message,
            'other_details': other_details,
            'priority': priority,
            'monthly_income': monthly_income,
            'credit_score': credit_score,
            'employment_type': employment_type,
            'preferred_contact_time': preferred_contact_time,
            'source_details': source_details
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        


        
        success = LeadService.update_lead_details(db, lead_id, **update_data)
        
        if success:
            # Log activity
            LeadService.log_activity(
                db=db,
                lead_id=lead_id,
                employee_id=current_employee.employee_id,
                activity_type='lead_details_updated',
                description=f'Lead details updated by {current_employee.user.name}',
                activity_data=update_data
            )
            
            return JSONResponse({
                "success": True,
                "message": "Lead updated successfully"
            })
        else:
            raise HTTPException(status_code=404, detail="Lead not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Lead Details Update
@router.post("/leads/{lead_id}/update-details", response_class=JSONResponse)
def update_lead_details(
    request: Request,
    lead_id: int,
    name: str = Form(...),
    contact: str = Form(...),
    email: str = Form(None),
    city: str = Form(None),
    loan_amount: float = Form(None),
    loan_type: str = Form(None),
    occupation: str = Form(None),
    occupation_other: str = Form(None),
    any_ongoing_loan: str = Form(None),
    message: str = Form(None),
    other_details: str = Form(None),
    priority: str = Form(None),
    monthly_income: float = Form(None),
    credit_score: int = Form(None),
    employment_type: str = Form(None),
    preferred_contact_time: str = Form(None),
    source_details: str = Form(None),
    db: Session = Depends(get_db)
):
    """Update lead details"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    user_role = request.session.get("user_role")
    
    # Check if user can update this lead
    assignment = db.query(LeadAssignment).filter(LeadAssignment.lead_id == lead_id).first()
    if not LeadService.can_update_lead_info(user_role, assignment):
        raise HTTPException(status_code=403, detail="Not authorized to update this lead")
    
    try:
        update_data = {
            'name': name,
            'contact': contact,
            'email': email,
            'city': city,
            'loan_amount': loan_amount,
            'loan_type': loan_type,
            'occupation': occupation,
            'occupation_other': occupation_other,
            'any_ongoing_loan': any_ongoing_loan,
            'message': message,
            'other_details': other_details,
            'priority': priority,
            'monthly_income': monthly_income,
            'credit_score': credit_score,
            'employment_type': employment_type,
            'preferred_contact_time': preferred_contact_time,
            'source_details': source_details
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        success = LeadService.update_lead_details(db, lead_id, **update_data)
        
        if success:
            # Log activity
            LeadService.log_activity(
                db=db,
                lead_id=lead_id,
                employee_id=current_employee.employee_id,
                activity_type='lead_details_updated',
                description=f'Lead details updated by {current_employee.user.name}',
                activity_data=update_data
            )
            
            return JSONResponse({
                "success": True,
                "message": "Lead details updated successfully"
            })
        else:
            raise HTTPException(status_code=404, detail="Lead not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update Other Details
@router.post("/unified-leads/{lead_id}/update-other-details", response_class=JSONResponse)
def update_other_details(
    request: Request,
    lead_id: int,
    other_details: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update other details for a lead"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    try:
        # Check if lead exists
        lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Update other details
        lead.other_details = other_details
        lead.updated_at = datetime.now()
        db.commit()
        
        # Log activity
        LeadService.log_activity(
            db=db,
            lead_id=lead_id,
            employee_id=current_employee.employee_id,
            activity_type='other_details_updated',
            description=f'Other details updated by {current_employee.user.name}',
            activity_data={'other_details': other_details}
        )
        
        return JSONResponse({
            "success": True,
            "message": "Other details updated successfully"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Workflow Progress API
@router.get("/leads/{lead_id}/workflow-progress", response_class=JSONResponse)
def get_workflow_progress(request: Request, lead_id: int, db: Session = Depends(get_db)):
    """Get workflow progress for visualization"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        assignment = db.query(LeadAssignment).filter(LeadAssignment.lead_id == lead_id).first()
        
        progress = LeadService.get_workflow_progress(lead, assignment)
        
        return JSONResponse({
            "success": True,
            "progress": progress,
            "current_status": assignment.status if assignment else lead.status
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Toggle Priority API
@router.post("/unified-leads/{lead_id}/toggle-priority", response_class=JSONResponse)
def toggle_priority(request: Request, lead_id: int, db: Session = Depends(get_db)):
    """Toggle priority between doable and not doable"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    current_employee = get_current_employee(request, db)
    if not current_employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    
    try:
        # Get request body
        try:
            body = request.json()
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON in request body")
        
        new_priority = body.get('priority')
        
        if not new_priority:
            raise HTTPException(status_code=400, detail="Priority field is required")
        
        if new_priority not in ['doable', 'not_doable']:
            raise HTTPException(status_code=400, detail="Invalid priority value. Must be 'doable' or 'not_doable'")
        
        # Check if lead exists
        lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Update priority
        old_priority = lead.priority
        print(f"DEBUG: Updating priority from {old_priority} to {new_priority}")
        lead.priority = new_priority
        lead.updated_at = datetime.now()
        db.commit()
        
        # Log activity
        LeadService.log_activity(
            db=db,
            lead_id=lead_id,
            employee_id=current_employee.employee_id,
            activity_type='priority_updated',
            description=f'Priority changed from {old_priority} to {new_priority} by {current_employee.user.name}',
            activity_data={'old_priority': old_priority, 'new_priority': new_priority}
        )
        
        return JSONResponse({
            "success": True,
            "message": f"Priority updated to {new_priority}",
            "priority": new_priority
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin Delete Lead Functionality
@router.post("/unified-leads/{lead_id}/delete", response_class=JSONResponse)
def delete_unified_lead(request: Request, lead_id: int, db: Session = Depends(get_db)):
    """Delete a lead (admin only)"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_role = request.session.get("user_role")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete leads")
    
    try:
        # Get the lead
        lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Get current employee for logging
        current_employee = get_current_employee(request, db)
        
        # Log the deletion before actually deleting
        if current_employee:
            LeadService.log_activity(
                db=db,
                lead_id=lead_id,
                employee_id=current_employee.employee_id,
                activity_type='lead_deleted',
                description=f'Lead deleted by admin',
                activity_data={'deleted_lead_name': lead.name, 'deleted_lead_contact': lead.contact}
            )
        
        # Delete related records first (due to foreign key constraints)
        # Delete comments
        if lead.assignments:
            for assignment in lead.assignments:
                db.query(LeadComment).filter(LeadComment.assignment_id == assignment.assignment_id).delete()
                db.query(Disbursement).filter(Disbursement.assignment_id == assignment.assignment_id).delete()
        
        # Delete assignments
        db.query(LeadAssignment).filter(LeadAssignment.lead_id == lead_id).delete()
        
        # Delete activities
        db.query(LeadActivity).filter(LeadActivity.lead_id == lead_id).delete()
        
        # Finally delete the lead
        db.delete(lead)
        db.commit()
        
        return JSONResponse({
            "success": True,
            "message": f"Lead {lead_id} deleted successfully"
        })
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Password Change Functionality
@router.get("/change-password", response_class=HTMLResponse)
def change_password_get(request: Request):
    """Display change password form"""
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("change_password.html", {"request": request})

@router.post("/change-password", response_class=JSONResponse)
def change_password_post(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Change user password"""
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_id = request.session.get("user_id")
    
    # Validate passwords
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters long")
    
    try:
        # Get user
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify current password
        import bcrypt
        if not bcrypt.checkpw(current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Hash new password
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update password
        user.password_hash = new_password_hash
        db.commit()
        
        return JSONResponse({
            "success": True,
            "message": "Password changed successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))