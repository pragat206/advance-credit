print("CRM ROUTER LOADED")
from fastapi import APIRouter, Request, Form, Depends, status, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response
from common_models import Base, Employee, Lead, Partner, Reminder
from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker
import bcrypt
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import joinedload
from typing import Optional
import pandas as pd
import io
import os
from datetime import datetime

router = APIRouter()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

DATABASE_URL = "sqlite:////Users/pragattiwari/news_slider/crm.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Add a session for the main website's site.db
SITE_DATABASE_URL = "sqlite:////Users/pragattiwari/news_slider/site.db"
site_engine = create_engine(SITE_DATABASE_URL, connect_args={"check_same_thread": False})
SiteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=site_engine)

# Minimal model for leads table in crm.db (for queries section)
SiteBase = declarative_base()
class SiteLead(SiteBase):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    contact = Column(String(64), nullable=False)
    email = Column(String(128))
    message = Column(Text)
    source = Column(String(32))
    created_at = Column(DateTime)
    lead_type = Column(String)
    assigned_to = Column(Integer)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_site_db():
    db = SiteSessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_admin(request: Request, db: Session = Depends(get_db)):
    emp_id = request.session.get("employee_id")
    if not emp_id:
        raise HTTPException(status_code=403, detail="Not authenticated")
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp or emp.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return emp

@router.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@router.post("/register", response_class=HTMLResponse)
def register_post(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(Employee).filter(Employee.email == email).first()
    if existing:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email already registered."})
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    employee = Employee(name=name, email=email, password_hash=hashed, role="employee")
    db.add(employee)
    db.commit()
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

@router.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login", response_class=HTMLResponse)
def login_post(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.email == email).first()
    if not employee or not bcrypt.checkpw(password.encode(), employee.password_hash.encode()):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials."})
    request.session["employee_id"] = employee.id
    request.session["employee_name"] = employee.name
    request.session["employee_role"] = employee.role
    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    if not request.session.get("employee_id"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("dashboard.html", {"request": request, "employee_name": request.session.get("employee_name")})

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

@router.get("/leads", response_class=HTMLResponse)
def leads_list(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("employee_id"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    employees = db.query(Employee).all()
    partners = db.query(Partner).all()
    return templates.TemplateResponse("leads.html", {"request": request, "leads": leads, "employees": employees, "partners": partners})

@router.get("/leads/new", response_class=HTMLResponse)
def lead_new_get(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("employee_id"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    employees = db.query(Employee).all()
    partners = db.query(Partner).all()
    return templates.TemplateResponse("lead_new.html", {"request": request, "employees": employees, "partners": partners, "error": None})

@router.post("/leads/new", response_class=HTMLResponse)
async def lead_new_post(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("employee_id"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    form = await request.form()
    name = form.get("name")
    email = form.get("email", "")
    contact = form.get("contact")
    partner_id = form.get("partner_id") or None
    assigned_to = form.get("assigned_to") or None
    message = form.get("message", "")
    status_ = form.get("status", "new")
    is_verified = int(form.get("is_verified", 0))
    source = form.get("source", "contact")
    documentation = form.get("documentation", "pending")
    if not name or not contact:
        return HTMLResponse("Missing required fields", status_code=400)
    try:
        partner_id = int(partner_id) if partner_id else None
    except Exception:
        partner_id = None
    try:
        assigned_to = int(assigned_to) if assigned_to else None
    except Exception:
        assigned_to = None
    lead = Lead(
        name=name,
        email=email,
        contact=contact,
        partner_id=partner_id,
        assigned_to=assigned_to,
        message=message,
        status=status_,
        is_verified=is_verified,
        source=source,
        documentation=documentation
    )
    db.add(lead)
    db.commit()
    return RedirectResponse("/leads", status_code=302)

@router.get("/leads/{lead_id}", response_class=HTMLResponse)
def lead_detail(request: Request, lead_id: int, db: Session = Depends(get_db)):
    if not request.session.get("employee_id"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    employees = db.query(Employee).all()
    partners = db.query(Partner).all()
    if not lead:
        return RedirectResponse("/leads", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("lead_detail.html", {"request": request, "lead": lead, "employees": employees, "partners": partners, "success": None, "error": None})

@router.post("/leads/{lead_id}", response_class=HTMLResponse)
def lead_update(request: Request, lead_id: int, status_: str = Form(...), assigned_to: int = Form(None), notes: str = Form(""), db: Session = Depends(get_db)):
    if not request.session.get("employee_id"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    employees = db.query(Employee).all()
    partners = db.query(Partner).all()
    if not lead:
        return RedirectResponse("/leads", status_code=status.HTTP_302_FOUND)
    lead.status = status_
    lead.assigned_to = assigned_to
    lead.notes = notes
    db.commit()
    db.refresh(lead)
    return templates.TemplateResponse("lead_detail.html", {"request": request, "lead": lead, "employees": employees, "partners": partners, "success": "Lead updated successfully!", "error": None})

@router.get("/employees", response_class=HTMLResponse)
def employees_list(request: Request, db: Session = Depends(get_db), admin: Employee = Depends(require_admin)):
    employees = db.query(Employee).all()
    return templates.TemplateResponse("employees.html", {"request": request, "employees": employees})

@router.get("/employees/new", response_class=HTMLResponse)
def employee_new_get(request: Request, db: Session = Depends(get_db), admin: Employee = Depends(require_admin)):
    return templates.TemplateResponse("employee_new.html", {"request": request, "error": None})

@router.post("/employees/new", response_class=HTMLResponse)
def employee_new_post(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db), admin: Employee = Depends(require_admin)):
    existing = db.query(Employee).filter(Employee.email == email).first()
    if existing:
        return templates.TemplateResponse("employee_new.html", {"request": request, "error": "Email already exists."})
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    emp = Employee(name=name, email=email, password_hash=hashed, role=role)
    db.add(emp)
    db.commit()
    return RedirectResponse("/employees", status_code=status.HTTP_302_FOUND)

@router.get("/employees/{emp_id}/edit", response_class=HTMLResponse)
def employee_edit_get(request: Request, emp_id: int, db: Session = Depends(get_db), admin: Employee = Depends(require_admin)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        return RedirectResponse("/employees", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("employee_edit.html", {"request": request, "emp": emp, "error": None})

@router.post("/employees/{emp_id}/edit", response_class=HTMLResponse)
def employee_edit_post(request: Request, emp_id: int, name: str = Form(...), email: str = Form(...), role: str = Form(...), db: Session = Depends(get_db), admin: Employee = Depends(require_admin)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        return RedirectResponse("/employees", status_code=status.HTTP_302_FOUND)
    emp.name = name
    emp.email = email
    emp.role = role
    db.commit()
    return RedirectResponse("/employees", status_code=status.HTTP_302_FOUND)

@router.get("/employees/{emp_id}/delete")
def employee_delete(request: Request, emp_id: int, db: Session = Depends(get_db), admin: Employee = Depends(require_admin)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if emp:
        db.delete(emp)
        db.commit()
    return RedirectResponse("/employees", status_code=status.HTTP_302_FOUND)

@router.get("/analytics", response_class=HTMLResponse)
def analytics_dashboard(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("employee_id"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    # Total leads
    total_leads = db.query(func.count(Lead.id)).scalar()
    # Leads by status
    status_counts = db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
    # Leads by partner
    partner_counts = db.query(Partner.name, func.count(Lead.id)).join(Lead, Lead.partner_id == Partner.id, isouter=True).group_by(Partner.name).all()
    # Leads by assignee
    assignee_counts = db.query(Employee.name, func.count(Lead.id)).join(Lead, Lead.assigned_to == Employee.id, isouter=True).group_by(Employee.name).all()
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "total_leads": total_leads,
        "status_counts": status_counts,
        "partner_counts": partner_counts,
        "assignee_counts": assignee_counts
    })

@router.get("/analytics/data")
def analytics_data(request: Request, status: str = '', partner_id: str = '', assigned_to: str = '', start_date: str = '', end_date: str = '', db: Session = Depends(get_db)):
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    if partner_id:
        query = query.join(Partner).filter(Partner.name == partner_id)
    if assigned_to:
        query = query.join(Employee).filter(Employee.name == assigned_to)
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Lead.created_at >= start)
        except Exception:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Lead.created_at <= end)
        except Exception:
            pass
    leads = query.all()
    # KPIs
    total_leads = len(leads)
    new_leads = sum(1 for l in leads if l.status == 'new')
    closed_leads = sum(1 for l in leads if l.status == 'closed')
    conversion = int((closed_leads / total_leads) * 100) if total_leads else 0
    # By status
    status_counts = {}
    for l in leads:
        status_counts[l.status] = status_counts.get(l.status, 0) + 1
    # By partner
    partner_counts = {}
    for l in leads:
        pname = l.partner.name if l.partner else 'Unassigned'
        partner_counts[pname] = partner_counts.get(pname, 0) + 1
    # By assignee
    assignee_counts = {}
    for l in leads:
        aname = l.employee.name if hasattr(l, 'employee') and l.employee else 'Unassigned'
        assignee_counts[aname] = assignee_counts.get(aname, 0) + 1
    # Over time (by day)
    time_counts = {}
    for l in leads:
        if l.created_at:
            day = l.created_at.strftime('%Y-%m-%d')
            time_counts[day] = time_counts.get(day, 0) + 1
    time_labels = sorted(time_counts.keys())
    time_data = [time_counts[d] for d in time_labels]
    return JSONResponse({
        "kpiTotalLeads": total_leads,
        "kpiNewLeads": new_leads,
        "kpiClosedLeads": closed_leads,
        "kpiConversion": conversion,
        "statusLabels": list(status_counts.keys()),
        "statusData": list(status_counts.values()),
        "partnerLabels": list(partner_counts.keys()),
        "partnerData": list(partner_counts.values()),
        "assigneeLabels": list(assignee_counts.keys()),
        "assigneeData": list(assignee_counts.values()),
        "timeLabels": time_labels,
        "timeData": time_data
    })

@router.get("/my-queries", response_class=HTMLResponse)
def my_queries(request: Request, db: Session = Depends(get_site_db)):
    emp_id = request.session.get("employee_id")
    if not emp_id:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    # Only queries/enquiries assigned to this employee
    queries = db.query(SiteLead).filter(
        ((SiteLead.source == 'contact') | (SiteLead.lead_type == 'general contact us')) & (SiteLead.assigned_to == emp_id)
    ).order_by(SiteLead.created_at.desc()).all()
    return templates.TemplateResponse("my_queries.html", {"request": request, "queries": queries})

@router.get("/admin/queries", response_class=HTMLResponse)
def admin_queries(request: Request, db: Session = Depends(get_site_db)):
    emp_id = request.session.get("employee_id")
    role = request.session.get("employee_role")
    if not emp_id or role not in ["admin", "manager"]:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    # Get all employees for assignment dropdown
    employees = db.query(Employee).all()
    # Get all queries/enquiries
    queries = db.query(SiteLead).filter(
        (SiteLead.source == 'contact') | (SiteLead.lead_type == 'general contact us')
    ).order_by(SiteLead.created_at.desc()).all()
    return templates.TemplateResponse("admin_queries.html", {"request": request, "queries": queries, "employees": employees})

@router.post("/admin/queries/assign", response_class=HTMLResponse)
async def assign_query(request: Request, db: Session = Depends(get_site_db)):
    emp_id = request.session.get("employee_id")
    role = request.session.get("employee_role")
    if not emp_id or role not in ["admin", "manager"]:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    form = await request.form()
    query_id = int(form.get("query_id"))
    assigned_to = int(form.get("assigned_to"))
    query = db.query(SiteLead).filter(SiteLead.id == query_id).first()
    if query:
        query.assigned_to = assigned_to
        db.commit()
    return RedirectResponse("/admin/queries", status_code=status.HTTP_302_FOUND)

@router.get("/admin/employees", response_class=HTMLResponse)
def admin_employees(request: Request, db: Session = Depends(get_db)):
    emp_id = request.session.get("employee_id")
    role = request.session.get("employee_role")
    if not emp_id or role not in ["admin", "manager"]:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    employees = db.query(Employee).all()
    return templates.TemplateResponse("admin_employees.html", {"request": request, "employees": employees})

@router.post("/admin/employees/update", response_class=HTMLResponse)
async def update_employee(request: Request, db: Session = Depends(get_db)):
    emp_id = request.session.get("employee_id")
    role = request.session.get("employee_role")
    if not emp_id or role not in ["admin", "manager"]:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    form = await request.form()
    employee_id = int(form.get("employee_id"))
    new_role = form.get("role")
    new_status = form.get("status")
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if emp:
        emp.role = new_role
        emp.status = new_status
        db.commit()
    return RedirectResponse("/admin/employees", status_code=status.HTTP_302_FOUND)

@router.get("/leads/bulk-upload", response_class=HTMLResponse)
def bulk_upload_get(request: Request):
    if not request.session.get("employee_id"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("bulk_upload.html", {"request": request, "error": None, "success": None})

@router.post("/leads/bulk-upload", response_class=HTMLResponse)
async def bulk_upload_post(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not request.session.get("employee_id"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    try:
        filename = file.filename.lower()
        if filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(file.file)
        else:
            return templates.TemplateResponse("bulk_upload.html", {"request": request, "error": "File must be .csv or .xlsx/.xls", "success": None})
        required_cols = {"name", "contact"}
        if not required_cols.issubset(df.columns):
            return templates.TemplateResponse("bulk_upload.html", {"request": request, "error": "File must include at least 'name' and 'contact' columns.", "success": None})
        for _, row in df.iterrows():
            lead = Lead(
                name=row.get("name"),
                contact=row.get("contact"),
                email=row.get("email", ""),
                partner_id=row.get("partner_id") if pd.notna(row.get("partner_id")) else None,
                assigned_to=row.get("assigned_to") if pd.notna(row.get("assigned_to")) else None,
                message=row.get("message", ""),
                status=row.get("status", "new"),
                is_verified=int(row.get("is_verified", 0)) if pd.notna(row.get("is_verified")) else 0,
                source=row.get("source", "contact"),
                documentation=row.get("documentation", "pending")
            )
            db.add(lead)
        db.commit()
        return templates.TemplateResponse("bulk_upload.html", {"request": request, "error": None, "success": "Leads uploaded successfully!"})
    except Exception as e:
        return templates.TemplateResponse("bulk_upload.html", {"request": request, "error": f"Error: {e}", "success": None})

@router.get("/leads/bulk-upload/template.csv")
def download_csv_template():
    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name","contact","email","partner_id","assigned_to","message","status","is_verified","source","documentation"])
    writer.writerow(["John Doe","1234567890","john@example.com","1","2","Test message","new","1","contact","pending"])
    writer.writerow(["Jane Smith","9876543210","jane@example.com","","","Another message","in_progress","0","apply","received"])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=leads_template.csv"})

@router.get("/leads/bulk-upload/template.xlsx")
def download_xlsx_template():
    import pandas as pd
    output = io.BytesIO()
    df = pd.DataFrame([
        {"name": "John Doe", "contact": "1234567890", "email": "john@example.com", "partner_id": 1, "assigned_to": 2, "message": "Test message", "status": "new", "is_verified": 1, "source": "contact", "documentation": "pending"},
        {"name": "Jane Smith", "contact": "9876543210", "email": "jane@example.com", "partner_id": "", "assigned_to": "", "message": "Another message", "status": "in_progress", "is_verified": 0, "source": "apply", "documentation": "received"}
    ])
    df.to_excel(output, index=False)
    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=leads_template.xlsx"})

@router.get("/reminders", response_class=HTMLResponse)
def reminders_list(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("employee_id"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    emp_id = request.session.get("employee_id")
    reminders = db.query(Reminder).filter(Reminder.assigned_to == emp_id).order_by(Reminder.due_date.asc()).all()
    employees = db.query(Employee).all()
    return templates.TemplateResponse("reminders.html", {"request": request, "reminders": reminders, "employees": employees})

@router.post("/reminders/new", response_class=HTMLResponse)
def reminders_new(request: Request, title: str = Form(...), description: str = Form(""), due_date: str = Form(...), assigned_to: int = Form(None), db: Session = Depends(get_db)):
    if not request.session.get("employee_id"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    try:
        due_date_parsed = datetime.strptime(due_date, "%Y-%m-%d")
    except Exception:
        return HTMLResponse("Invalid date format", status_code=400)
    reminder = Reminder(
        title=title,
        description=description,
        due_date=due_date_parsed,
        assigned_to=assigned_to or request.session.get("employee_id"),
        status="pending"
    )
    db.add(reminder)
    db.commit()
    return RedirectResponse("/reminders", status_code=302)

@router.post("/reminders/{reminder_id}/edit", response_class=HTMLResponse)
def reminders_edit(request: Request, reminder_id: int, title: str = Form(...), description: str = Form(""), due_date: str = Form(...), status: str = Form(...), db: Session = Depends(get_db)):
    if not request.session.get("employee_id"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        return HTMLResponse("Reminder not found", status_code=404)
    try:
        reminder.title = title
        reminder.description = description
        reminder.due_date = datetime.strptime(due_date, "%Y-%m-%d")
        reminder.status = status
        db.commit()
    except Exception:
        return HTMLResponse("Invalid data", status_code=400)
    return RedirectResponse("/reminders", status_code=302)

@router.post("/reminders/{reminder_id}/delete", response_class=HTMLResponse)
def reminders_delete(request: Request, reminder_id: int, db: Session = Depends(get_db)):
    if not request.session.get("employee_id"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if reminder:
        db.delete(reminder)
        db.commit()
    return RedirectResponse("/reminders", status_code=302)
