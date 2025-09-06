from fastapi import APIRouter, Request, Form, Depends, status, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from src.shared.crm_models import WebsiteLead, SocialMediaLead, LeadAssignment, Employee, User
from src.crm.routes import get_db
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/crm/templates")

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
        # Create the website lead
        lead = WebsiteLead(
            name=name,
            contact=contact,
            email=email,
            message=message
        )
        db.add(lead)
        db.flush()  # Get the lead_id
        
        # Assign to employee if specified
        if assigned_employee_id:
            assignment = LeadAssignment(
                lead_id=lead.lead_id,
                lead_type="website",
                employee_id=assigned_employee_id,
                status="assigned"
            )
            db.add(assignment)
        
        db.commit()
        return RedirectResponse("/crm/website-leads", status_code=status.HTTP_302_FOUND)
    
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
        # Create the social media lead
        lead = SocialMediaLead(
            name=name,
            contact=contact,
            city=city,
            any_ongoing_loan=any_ongoing_loan,
            loan_amount=loan_amount,
            platform_name=platform_name
        )
        db.add(lead)
        db.flush()  # Get the lead_id
        
        # Assign to employee if specified
        if assigned_employee_id:
            assignment = LeadAssignment(
                lead_id=lead.lead_id,
                lead_type="social",
                employee_id=assigned_employee_id,
                status="assigned"
            )
            db.add(assignment)
        
        db.commit()
        return RedirectResponse("/crm/social-leads", status_code=status.HTTP_302_FOUND)
    
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("lead_new.html", {
            "request": request, 
            "error": f"Error creating lead: {str(e)}", 
            "lead_type": "social",
            "employees": []
        })
