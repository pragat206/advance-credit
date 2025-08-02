print("CRM ROUTER LOADED")
from fastapi import APIRouter, Request, Form, Depends, status, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response
from src.shared.crm_models import CRMBase, WebsiteLead, SocialMediaLead, User, Team, Employee, LeadAssignment, Billing, Commission
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

def require_admin(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/crm/unauthorized", status_code=status.HTTP_302_FOUND)
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "admin":
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

@router.get("/unauthorized", response_class=HTMLResponse)
def unauthorized(request: Request):
    return templates.TemplateResponse("unauthorized.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@router.post("/register", response_class=HTMLResponse)
def register_post(request: Request, name: str = Form(...), email: str = Form(...), phone: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email already registered."})
    
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(name=name, email=email, phone=phone, password_hash=hashed, role="employee")
    db.add(user)
    db.flush()  # Get the user_id
    
    # Create employee record for the registered user
    from datetime import date
    employee_code = f"EMP{user.user_id:04d}"
    employee = Employee(
        user_id=user.user_id,
        employee_code=employee_code,
        designation="Employee",
        department="General",
        joining_date=date.today(),
        salary=0.0,
        commission_rate=0.0
    )
    db.add(employee)
    db.commit()
    
    return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)

@router.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login", response_class=HTMLResponse)
def login_post(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials."})
    
    # Get employee record if exists
    employee = db.query(Employee).filter(Employee.user_id == user.user_id).first()
    
    request.session["user_id"] = user.user_id
    request.session["user_name"] = user.name
    request.session["user_role"] = user.role
    if employee:
        request.session["employee_id"] = employee.employee_id
        request.session["employee_code"] = employee.employee_code
    else:
        request.session["employee_id"] = None
        request.session["employee_code"] = None
    
    return RedirectResponse("/crm/dashboard", status_code=status.HTTP_302_FOUND)

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    user_role = request.session.get("user_role")
    employee_id = request.session.get("employee_id")
    
    if user_role == "admin":
        # Admin sees all data
        website_leads_count = db.query(WebsiteLead).count()
        social_leads_count = db.query(SocialMediaLead).count()
        total_leads = website_leads_count + social_leads_count
        users_count = db.query(User).count()
        employees_count = db.query(Employee).count()
        teams_count = db.query(Team).count()
        
        # Get recent leads
        recent_website_leads = db.query(WebsiteLead).order_by(WebsiteLead.created_at.desc()).limit(5).all()
        recent_social_leads = db.query(SocialMediaLead).order_by(SocialMediaLead.created_at.desc()).limit(5).all()
    else:
        # Employee sees only their data
        if employee_id:
            # Get assigned leads count
            website_assignments = db.query(LeadAssignment).filter(
                LeadAssignment.employee_id == employee_id,
                LeadAssignment.lead_type == "website"
            ).count()
            social_assignments = db.query(LeadAssignment).filter(
                LeadAssignment.employee_id == employee_id,
                LeadAssignment.lead_type == "social"
            ).count()
            
            website_leads_count = website_assignments
            social_leads_count = social_assignments
            total_leads = website_leads_count + social_leads_count
            
            # Get employee's recent assigned leads
            website_lead_ids = db.query(LeadAssignment.lead_id).filter(
                LeadAssignment.employee_id == employee_id,
                LeadAssignment.lead_type == "website"
            ).all()
            social_lead_ids = db.query(LeadAssignment.lead_id).filter(
                LeadAssignment.employee_id == employee_id,
                LeadAssignment.lead_type == "social"
            ).all()
            
            if website_lead_ids:
                recent_website_leads = db.query(WebsiteLead).filter(
                    WebsiteLead.lead_id.in_([id[0] for id in website_lead_ids])
                ).order_by(WebsiteLead.created_at.desc()).limit(5).all()
            else:
                recent_website_leads = []
                
            if social_lead_ids:
                recent_social_leads = db.query(SocialMediaLead).filter(
                    SocialMediaLead.lead_id.in_([id[0] for id in social_lead_ids])
                ).order_by(SocialMediaLead.created_at.desc()).limit(5).all()
            else:
                recent_social_leads = []
        else:
            website_leads_count = 0
            social_leads_count = 0
            total_leads = 0
            recent_website_leads = []
            recent_social_leads = []
        
        users_count = 0  # Employees don't see user count
        employees_count = 0  # Employees don't see employee count
        teams_count = 0  # Employees don't see team count
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_leads": total_leads,
        "website_leads_count": website_leads_count,
        "social_leads_count": social_leads_count,
        "users_count": users_count,
        "employees_count": employees_count,
        "teams_count": teams_count,
        "recent_website_leads": recent_website_leads,
        "recent_social_leads": recent_social_leads
    })

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)

# Website Leads Management
@router.get("/website-leads", response_class=HTMLResponse)
def website_leads_list(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    user_role = request.session.get("user_role")
    employee_id = request.session.get("employee_id")
    
    if user_role == "admin":
        # Admin sees all leads
        leads = db.query(WebsiteLead).order_by(WebsiteLead.created_at.desc()).all()
    else:
        # Employee sees only their assigned leads
        if employee_id:
            assigned_leads = db.query(LeadAssignment).filter(
                LeadAssignment.employee_id == employee_id,
                LeadAssignment.lead_type == "website"
            ).all()
            lead_ids = [assignment.lead_id for assignment in assigned_leads]
            leads = db.query(WebsiteLead).filter(WebsiteLead.lead_id.in_(lead_ids)).order_by(WebsiteLead.created_at.desc()).all()
        else:
            leads = []
    
    # Get assignment information for each lead
    for lead in leads:
        assignment = db.query(LeadAssignment).filter(
            LeadAssignment.lead_type == "website",
            LeadAssignment.lead_id == lead.lead_id
        ).first()
        lead.assignment = assignment
    
    return templates.TemplateResponse("website_leads.html", {"request": request, "leads": leads})

@router.get("/website-leads/{lead_id}", response_class=HTMLResponse)
def website_lead_detail(request: Request, lead_id: int, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    lead = db.query(WebsiteLead).filter(WebsiteLead.lead_id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return templates.TemplateResponse("website_lead_detail.html", {"request": request, "lead": lead})

# Social Media Leads Management
@router.get("/social-leads", response_class=HTMLResponse)
def social_leads_list(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    user_role = request.session.get("user_role")
    employee_id = request.session.get("employee_id")
    
    if user_role == "admin":
        # Admin sees all leads
        leads = db.query(SocialMediaLead).order_by(SocialMediaLead.created_at.desc()).all()
    else:
        # Employee sees only their assigned leads
        if employee_id:
            assigned_leads = db.query(LeadAssignment).filter(
                LeadAssignment.employee_id == employee_id,
                LeadAssignment.lead_type == "social"
            ).all()
            lead_ids = [assignment.lead_id for assignment in assigned_leads]
            leads = db.query(SocialMediaLead).filter(SocialMediaLead.lead_id.in_(lead_ids)).order_by(SocialMediaLead.created_at.desc()).all()
        else:
            leads = []
    
    # Get assignment information for each lead
    for lead in leads:
        assignment = db.query(LeadAssignment).filter(
            LeadAssignment.lead_type == "social",
            LeadAssignment.lead_id == lead.lead_id
        ).first()
        lead.assignment = assignment
    
    return templates.TemplateResponse("social_leads.html", {"request": request, "leads": leads})

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
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    lead = db.query(SocialMediaLead).filter(SocialMediaLead.lead_id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return templates.TemplateResponse("social_lead_detail.html", {"request": request, "lead": lead})

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
    user = User(name=name, email=email, phone=phone, password_hash=hashed, role=role)
    db.add(user)
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
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return RedirectResponse("/crm/users", status_code=status.HTTP_302_FOUND)

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
    
    # Get lead counts by platform
    website_leads_count = db.query(WebsiteLead).count()
    social_leads_count = db.query(SocialMediaLead).count()
    
    # Get platform breakdown for social leads
    platform_counts = db.query(
        SocialMediaLead.platform_name,
        func.count(SocialMediaLead.lead_id)
    ).group_by(SocialMediaLead.platform_name).all()
    
    # Get leads by date (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_website_leads_count = db.query(WebsiteLead).filter(WebsiteLead.created_at >= thirty_days_ago).count()
    recent_social_leads_count = db.query(SocialMediaLead).filter(SocialMediaLead.created_at >= thirty_days_ago).count()
    
    # Get recent leads for display
    recent_website_leads = db.query(WebsiteLead).order_by(WebsiteLead.created_at.desc()).limit(5).all()
    recent_social_leads = db.query(SocialMediaLead).order_by(SocialMediaLead.created_at.desc()).limit(5).all()
    
    # Calculate total leads and platform breakdown
    total_leads = website_leads_count + social_leads_count
    platform_breakdown = {platform: count for platform, count in platform_counts}
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "website_leads_count": website_leads_count,
        "social_leads_count": social_leads_count,
        "total_leads": total_leads,
        "platform_breakdown": platform_breakdown,
        "recent_website_leads_count": recent_website_leads_count,
        "recent_social_leads_count": recent_social_leads_count,
        "recent_website_leads": recent_website_leads,
        "recent_social_leads": recent_social_leads
    })

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
    
    conversion_rate = (converted_count / leads_count * 100) if leads_count > 0 else 0
    
    return templates.TemplateResponse("team_performance.html", {
        "request": request,
        "team": team,
        "leads_count": leads_count,
        "converted_count": converted_count,
        "conversion_rate": conversion_rate
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
    
    # Get the lead based on type
    if lead_type == "website":
        lead = db.query(WebsiteLead).filter(WebsiteLead.lead_id == lead_id).first()
        lead_name = lead.name if lead else "Unknown"
    elif lead_type == "social":
        lead = db.query(SocialMediaLead).filter(SocialMediaLead.lead_id == lead_id).first()
        lead_name = lead.name if lead else "Unknown"
    else:
        return RedirectResponse("/crm/dashboard", status_code=status.HTTP_302_FOUND)
    
    if not lead:
        return RedirectResponse("/crm/dashboard", status_code=status.HTTP_302_FOUND)
    
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
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    # Check if assignment already exists
    existing_assignment = db.query(LeadAssignment).filter(
        LeadAssignment.lead_type == lead_type,
        LeadAssignment.lead_id == lead_id
    ).first()
    
    if existing_assignment:
        return templates.TemplateResponse("assign_lead.html", {
            "request": request,
            "lead": None,
            "lead_type": lead_type,
            "lead_name": "Unknown",
            "employees": db.query(Employee).filter(Employee.is_active == True).all(),
            "error": "This lead is already assigned to an employee"
        })
    
    # Create new assignment
    assignment = LeadAssignment(
        employee_id=employee_id,
        lead_type=lead_type,
        lead_id=lead_id,
        status="assigned",
        notes=notes
    )
    
    db.add(assignment)
    db.commit()
    
    # Redirect based on lead type
    if lead_type == "website":
        return RedirectResponse("/crm/website-leads", status_code=status.HTTP_302_FOUND)
    else:
        return RedirectResponse("/crm/social-leads", status_code=status.HTTP_302_FOUND)

@router.get("/leads/{lead_type}/{lead_id}/unassign")
def unassign_lead(request: Request, lead_type: str, lead_id: int, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/crm/login", status_code=status.HTTP_302_FOUND)
    
    # Find and delete the assignment
    assignment = db.query(LeadAssignment).filter(
        LeadAssignment.lead_type == lead_type,
        LeadAssignment.lead_id == lead_id
    ).first()
    
    if assignment:
        db.delete(assignment)
        db.commit()
    
    # Redirect based on lead type
    if lead_type == "website":
        return RedirectResponse("/crm/website-leads", status_code=status.HTTP_302_FOUND)
    else:
        return RedirectResponse("/crm/social-leads", status_code=status.HTTP_302_FOUND)
