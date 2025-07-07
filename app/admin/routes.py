print('DEBUG: Entering admin/routes.py')
from fastapi import APIRouter, Request, Form, Depends, Response, UploadFile, File
print('DEBUG: Imported FastAPI modules')
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from starlette.templating import Jinja2Templates
from app.db import get_db
print('DEBUG: Imported get_db')
from app.models import AdminUser, Banner, Product, Partner, FAQ, Testimonial, Service, TeamMember
print('DEBUG: Imported models')
from app.admin.auth import set_admin_session, clear_admin_session, is_admin_authenticated
print('DEBUG: Imported admin auth helpers')
import os
from uuid import uuid4

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

BANNERS_DIR = "app/static/banners/"
os.makedirs(BANNERS_DIR, exist_ok=True)

PARTNERS_DIR = "app/static/partners/"
os.makedirs(PARTNERS_DIR, exist_ok=True)

@router.get("/admin/login")
def admin_login_get(request: Request):
    print('DEBUG: In admin_login_get')
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})

@router.post("/admin/login")
def admin_login_post(request: Request, password: str = Form(...), db: Session = Depends(get_db)):
    print('DEBUG: In admin_login_post')
    admin = db.query(AdminUser).filter_by(username="admin").first()
    if admin and bcrypt.verify(password, admin.password_hash):
        redirect = RedirectResponse(url="/admin/dashboard", status_code=302)
        set_admin_session(redirect)
        return redirect
    else:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Invalid password."})

@router.get("/admin/logout")
def admin_logout(request: Request, response: Response):
    print('DEBUG: In admin_logout')
    clear_admin_session(response)
    return RedirectResponse(url="/admin/login", status_code=302)

# Dependency to require admin auth
def require_admin(request: Request):
    print('DEBUG: In require_admin')
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

@router.get("/admin/dashboard")
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    print('DEBUG: In admin_dashboard')
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    stats = {
        "banners": db.query(Banner).count(),
        "products": db.query(Product).count(),
        "partners": db.query(Partner).count(),
        "faqs": db.query(FAQ).count(),
        "testimonials": db.query(Testimonial).count(),
        "services": db.query(Service).count(),
        "team": db.query(TeamMember).count(),
    }
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "stats": stats})

@router.get("/admin/banners")
def admin_banners(request: Request, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    banners = db.query(Banner).order_by(Banner.order).all()
    return templates.TemplateResponse("admin_banners.html", {"request": request, "banners": banners})

@router.post("/admin/banners")
def admin_add_banner(request: Request, title: str = Form(...), caption: str = Form(None), order: int = Form(0), image: UploadFile = File(...), db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    # Save image
    ext = os.path.splitext(image.filename)[1]
    filename = f"{uuid4().hex}{ext}"
    path = os.path.join(BANNERS_DIR, filename)
    with open(path, "wb") as f:
        f.write(image.file.read())
    image_url = f"/static/banners/{filename}"
    banner = Banner(title=title, caption=caption, order=order, image_url=image_url)
    db.add(banner)
    db.commit()
    return RedirectResponse(url="/admin/banners", status_code=302)

@router.get("/admin/banners/{banner_id}/edit")
def admin_edit_banner_get(request: Request, banner_id: int, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    banner = db.query(Banner).filter_by(id=banner_id).first()
    if not banner:
        return RedirectResponse(url="/admin/banners", status_code=302)
    return templates.TemplateResponse("admin_banners.html", {"request": request, "edit_banner": banner})

@router.post("/admin/banners/{banner_id}/edit")
def admin_edit_banner_post(request: Request, banner_id: int, title: str = Form(...), caption: str = Form(None), order: int = Form(0), image: UploadFile = File(None), db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    banner = db.query(Banner).filter_by(id=banner_id).first()
    if not banner:
        return RedirectResponse(url="/admin/banners", status_code=302)
    banner.title = title
    banner.caption = caption
    banner.order = order
    if image:
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid4().hex}{ext}"
        path = os.path.join(BANNERS_DIR, filename)
        with open(path, "wb") as f:
            f.write(image.file.read())
        banner.image_url = f"/static/banners/{filename}"
    db.commit()
    return RedirectResponse(url="/admin/banners", status_code=302)

@router.post("/admin/banners/{banner_id}/delete")
def admin_delete_banner(request: Request, banner_id: int, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    banner = db.query(Banner).filter_by(id=banner_id).first()
    if banner:
        db.delete(banner)
        db.commit()
    return RedirectResponse(url="/admin/banners", status_code=302)

@router.get("/admin/partners")
def admin_partners(request: Request, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    partners = db.query(Partner).order_by(Partner.name).all()
    return templates.TemplateResponse("admin_partners.html", {"request": request, "partners": partners})

@router.post("/admin/partners")
def admin_add_partner(request: Request, name: str = Form(...), url: str = Form(None), logo: UploadFile = File(...), db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    ext = os.path.splitext(logo.filename)[1]
    filename = f"{uuid4().hex}{ext}"
    path = os.path.join(PARTNERS_DIR, filename)
    with open(path, "wb") as f:
        f.write(logo.file.read())
    logo_url = f"/static/partners/{filename}"
    partner = Partner(name=name, url=url, logo_url=logo_url)
    db.add(partner)
    db.commit()
    return RedirectResponse(url="/admin/partners", status_code=302)

@router.get("/admin/partners/{partner_id}/edit")
def admin_edit_partner_get(request: Request, partner_id: int, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    partner = db.query(Partner).filter_by(id=partner_id).first()
    if not partner:
        return RedirectResponse(url="/admin/partners", status_code=302)
    return templates.TemplateResponse("admin_partners.html", {"request": request, "edit_partner": partner})

@router.post("/admin/partners/{partner_id}/edit")
def admin_edit_partner_post(request: Request, partner_id: int, name: str = Form(...), url: str = Form(None), logo: UploadFile = File(None), db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    partner = db.query(Partner).filter_by(id=partner_id).first()
    if not partner:
        return RedirectResponse(url="/admin/partners", status_code=302)
    partner.name = name
    partner.url = url
    if logo:
        ext = os.path.splitext(logo.filename)[1]
        filename = f"{uuid4().hex}{ext}"
        path = os.path.join(PARTNERS_DIR, filename)
        with open(path, "wb") as f:
            f.write(logo.file.read())
        partner.logo_url = f"/static/partners/{filename}"
    db.commit()
    return RedirectResponse(url="/admin/partners", status_code=302)

@router.post("/admin/partners/{partner_id}/delete")
def admin_delete_partner(request: Request, partner_id: int, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    partner = db.query(Partner).filter_by(id=partner_id).first()
    if partner:
        db.delete(partner)
        db.commit()
    return RedirectResponse(url="/admin/partners", status_code=302)

@router.get("/admin/faqs")
def admin_faqs(request: Request, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    faqs = db.query(FAQ).order_by(FAQ.id).all()
    return templates.TemplateResponse("admin_faqs.html", {"request": request, "faqs": faqs})

@router.post("/admin/faqs")
def admin_add_faq(request: Request, question: str = Form(...), answer: str = Form(...), db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    faq = FAQ(question=question, answer=answer)
    db.add(faq)
    db.commit()
    return RedirectResponse(url="/admin/faqs", status_code=302)

@router.get("/admin/faqs/{faq_id}/edit")
def admin_edit_faq_get(request: Request, faq_id: int, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    faq = db.query(FAQ).filter_by(id=faq_id).first()
    if not faq:
        return RedirectResponse(url="/admin/faqs", status_code=302)
    return templates.TemplateResponse("admin_faqs.html", {"request": request, "edit_faq": faq})

@router.post("/admin/faqs/{faq_id}/edit")
def admin_edit_faq_post(request: Request, faq_id: int, question: str = Form(...), answer: str = Form(...), db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    faq = db.query(FAQ).filter_by(id=faq_id).first()
    if not faq:
        return RedirectResponse(url="/admin/faqs", status_code=302)
    faq.question = question
    faq.answer = answer
    db.commit()
    return RedirectResponse(url="/admin/faqs", status_code=302)

@router.post("/admin/faqs/{faq_id}/delete")
def admin_delete_faq(request: Request, faq_id: int, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    faq = db.query(FAQ).filter_by(id=faq_id).first()
    if faq:
        db.delete(faq)
        db.commit()
    return RedirectResponse(url="/admin/faqs", status_code=302)

@router.get("/admin/products")
def admin_products(request: Request, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    products = db.query(Product).order_by(Product.id).all()
    return templates.TemplateResponse("admin_products.html", {"request": request, "products": products})

@router.post("/admin/products")
def admin_add_product(request: Request, name: str = Form(...), description: str = Form(None), price: float = Form(...), image: UploadFile = File(...), db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    ext = os.path.splitext(image.filename)[1]
    filename = f"{uuid4().hex}{ext}"
    path = os.path.join(BANNERS_DIR, filename)
    with open(path, "wb") as f:
        f.write(image.file.read())
    image_url = f"/static/banners/{filename}"
    product = Product(name=name, description=description, price=price, image_url=image_url)
    db.add(product)
    db.commit()
    return RedirectResponse(url="/admin/products", status_code=302)

@router.get("/admin/products/{product_id}/edit")
def admin_edit_product_get(request: Request, product_id: int, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    product = db.query(Product).filter_by(id=product_id).first()
    if not product:
        return RedirectResponse(url="/admin/products", status_code=302)
    return templates.TemplateResponse("admin_products.html", {"request": request, "edit_product": product})

@router.post("/admin/products/{product_id}/edit")
def admin_edit_product_post(request: Request, product_id: int, name: str = Form(...), description: str = Form(None), price: float = Form(...), image: UploadFile = File(None), db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    product = db.query(Product).filter_by(id=product_id).first()
    if not product:
        return RedirectResponse(url="/admin/products", status_code=302)
    product.name = name
    product.description = description
    product.price = price
    if image:
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid4().hex}{ext}"
        path = os.path.join(BANNERS_DIR, filename)
        with open(path, "wb") as f:
            f.write(image.file.read())
        product.image_url = f"/static/banners/{filename}"
    db.commit()
    return RedirectResponse(url="/admin/products", status_code=302)

@router.post("/admin/products/{product_id}/delete")
def admin_delete_product(request: Request, product_id: int, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    product = db.query(Product).filter_by(id=product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse(url="/admin/products", status_code=302)

@router.get("/admin/testimonials")
def admin_testimonials(request: Request, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    testimonials = db.query(Testimonial).order_by(Testimonial.id).all()
    return templates.TemplateResponse("admin_testimonials.html", {"request": request, "testimonials": testimonials})

@router.post("/admin/testimonials")
def admin_add_testimonial(request: Request, name: str = Form(...), testimonial: str = Form(...), db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    testimonial = Testimonial(name=name, testimonial=testimonial)
    db.add(testimonial)
    db.commit()
    return RedirectResponse(url="/admin/testimonials", status_code=302)

@router.get("/admin/testimonials/{testimonial_id}/edit")
def admin_edit_testimonial_get(request: Request, testimonial_id: int, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    testimonial = db.query(Testimonial).filter_by(id=testimonial_id).first()
    if not testimonial:
        return RedirectResponse(url="/admin/testimonials", status_code=302)
    return templates.TemplateResponse("admin_testimonials.html", {"request": request, "edit_testimonial": testimonial})

@router.post("/admin/testimonials/{testimonial_id}/edit")
def admin_edit_testimonial_post(request: Request, testimonial_id: int, name: str = Form(...), testimonial: str = Form(...), db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    testimonial = db.query(Testimonial).filter_by(id=testimonial_id).first()
    if not testimonial:
        return RedirectResponse(url="/admin/testimonials", status_code=302)
    testimonial.name = name
    testimonial.testimonial = testimonial
    db.commit()
    return RedirectResponse(url="/admin/testimonials", status_code=302)

@router.post("/admin/testimonials/{testimonial_id}/delete")
def admin_delete_testimonial(request: Request, testimonial_id: int, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    testimonial = db.query(Testimonial).filter_by(id=testimonial_id).first()
    if testimonial:
        db.delete(testimonial)
        db.commit()
    return RedirectResponse(url="/admin/testimonials", status_code=302)

@router.get("/admin/services")
def admin_services(request: Request, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    services = db.query(Service).order_by(Service.id).all()
    return templates.TemplateResponse("admin_services.html", {"request": request, "services": services})

@router.post("/admin/services")
def admin_add_service(request: Request, name: str = Form(...), description: str = Form(None), db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    service = Service(name=name, description=description)
    db.add(service)
    db.commit()
    return RedirectResponse(url="/admin/services", status_code=302)

@router.get("/admin/services/{service_id}/edit")
def admin_edit_service_get(request: Request, service_id: int, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    service = db.query(Service).filter_by(id=service_id).first()
    if not service:
        return RedirectResponse(url="/admin/services", status_code=302)
    return RedirectResponse(url="/admin/partners", status_code=302)

@router.get("/admin/team")
def admin_team(request: Request, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    team = db.query(TeamMember).order_by(TeamMember.id).all()
    return templates.TemplateResponse("admin_team.html", {"request": request, "team": team})

@router.post("/admin/team")
def admin_add_team(request: Request, name: str = Form(...), role: str = Form(None), bio: str = Form(None), image_url: str = Form(None), db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    member = TeamMember(name=name, role=role, bio=bio, image_url=image_url)
    db.add(member)
    db.commit()
    return RedirectResponse(url="/admin/team", status_code=302)

@router.get("/admin/team/{member_id}/edit")
def admin_edit_team_get(request: Request, member_id: int, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    member = db.query(TeamMember).filter_by(id=member_id).first()
    if not member:
        return RedirectResponse(url="/admin/team", status_code=302)
    team = db.query(TeamMember).order_by(TeamMember.id).all()
    return templates.TemplateResponse("admin_team.html", {"request": request, "team": team, "edit_member": member})

@router.post("/admin/team/{member_id}/edit")
def admin_edit_team_post(request: Request, member_id: int, name: str = Form(...), role: str = Form(None), bio: str = Form(None), image_url: str = Form(None), db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    member = db.query(TeamMember).filter_by(id=member_id).first()
    if not member:
        return RedirectResponse(url="/admin/team", status_code=302)
    member.name = name
    member.role = role
    member.bio = bio
    member.image_url = image_url
    db.commit()
    return RedirectResponse(url="/admin/team", status_code=302)

@router.post("/admin/team/{member_id}/delete")
def admin_delete_team(request: Request, member_id: int, db: Session = Depends(get_db)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    member = db.query(TeamMember).filter_by(id=member_id).first()
    if member:
        db.delete(member)
        db.commit()
    return RedirectResponse(url="/admin/team", status_code=302)

@router.get("/admin/settings")
def admin_settings(request: Request):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    return templates.TemplateResponse("admin_settings.html", {"request": request}) 