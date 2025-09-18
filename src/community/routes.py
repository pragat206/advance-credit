from fastapi import APIRouter, Depends, HTTPException, Request, Form, File, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from typing import Optional, List
import os
import uuid
import random
import string
from datetime import datetime, timedelta
import re

from src.main_app.database import get_db
from src.community.models import (
    CommunityUser, CommunityCompany, CommunityPost, CommunityComment, 
    CommunityVote, CommunityOTP, CommunityCategory, CommunityTag, CommunityFAQ
)

# Templates
templates = Jinja2Templates(directory="src/community/templates")

router = APIRouter()

# Utility functions
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def create_slug(text):
    """Create URL-friendly slug from text"""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def send_otp_email(email: str, otp: str):
    """Send OTP via email using existing email infrastructure"""
    try:
        # Import email functions from main app
        import sys
        import os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from src.main_app.main import send_email
        
        subject = "CreditCare Community - Verification Code"
        
        # Create professional HTML email template
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CreditCare Verification Code</title>
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8fafc;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 24px;
            font-weight: 700;
            color: #1e40af;
            margin-bottom: 10px;
        }}
        .otp-code {{
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            font-size: 32px;
            font-weight: 700;
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            margin: 30px 0;
            letter-spacing: 4px;
        }}
        .warning {{
            background: #fef3c7;
            border: 1px solid #f59e0b;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            color: #92400e;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🛡️ CreditCare</div>
            <h1>Verification Code</h1>
        </div>
        
        <p>Hello!</p>
        
        <p>You're almost ready to join the CreditCare community. Use the verification code below to complete your registration:</p>
        
        <div class="otp-code">{otp}</div>
        
        <div class="warning">
            <strong>⚠️ Important:</strong> This code will expire in 10 minutes. If you didn't request this code, please ignore this email.
        </div>
        
        <p>Once verified, you'll have access to:</p>
        <ul>
            <li>Expert financial advice from verified professionals</li>
            <li>Community discussions on loans, debt consolidation, and more</li>
            <li>Educational content to improve your financial health</li>
            <li>Direct access to Advance Credit Finance Advisory services</li>
        </ul>
        
        <div class="footer">
            <p><strong>CreditCare Team</strong><br>
            Advance Credit Finance Advisory</p>
            <p>This is an automated message. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Plain text version for email clients that don't support HTML
        plain_body = f"""
CreditCare Community - Verification Code

Hello!

You're almost ready to join the CreditCare community. Use the verification code below to complete your registration:

{otp}

IMPORTANT: This code will expire in 10 minutes. If you didn't request this code, please ignore this email.

Once verified, you'll have access to:
- Expert financial advice from verified professionals
- Community discussions on loans, debt consolidation, and more
- Educational content to improve your financial health
- Direct access to Advance Credit Finance Advisory services

Best regards,
CreditCare Team
Advance Credit Finance Advisory

This is an automated message. Please do not reply to this email.
        """
        
        success, error = send_email(subject, plain_body, email)
        if success:
            print(f"✅ OTP email sent to {email}")
            return True
        else:
            print(f"❌ Failed to send OTP email to {email}: {error}")
            # Fallback: print to console for development
            print(f"📧 [FALLBACK] OTP for {email}: {otp}")
            return True  # Return True to continue the flow
    except Exception as e:
        print(f"❌ Error sending OTP email to {email}: {e}")
        # Fallback: print to console for development
        print(f"📧 [FALLBACK] OTP for {email}: {otp}")
        return True  # Return True to continue the flow

def send_otp_sms(phone: str, otp: str):
    """Send OTP via SMS using SMS service module"""
    try:
        # Import SMS service
        from src.community.sms_service import send_otp_sms as sms_service_send
        
        success = sms_service_send(phone, otp)
        if success:
            print(f"✅ OTP SMS sent to {phone}")
            return True
        else:
            print(f"❌ Failed to send OTP SMS to {phone}")
            # Fallback: print to console for development
            print(f"📱 [FALLBACK] OTP for {phone}: {otp}")
            return True  # Return True to continue the flow
            
    except Exception as e:
        print(f"❌ Error sending OTP SMS to {phone}: {e}")
        # Fallback: print to console for development
        print(f"📱 [FALLBACK] OTP for {phone}: {otp}")
        return True  # Return True to continue the flow

# Community Homepage
@router.get("/", response_class=HTMLResponse)
async def community_home(request: Request, db: Session = Depends(get_db)):
    """CreditCare Community Homepage - Comprehensive Financial Blog"""
    # This is now a comprehensive single-page community with all financial blogs
    # No need to query database for posts since we're using static content
    return templates.TemplateResponse("community/home.html", {
        "request": request
    })

# User Registration
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """User registration page"""
    return templates.TemplateResponse("community/register.html", {"request": request})

@router.post("/register", response_class=JSONResponse)
async def register_user(
    request: Request,
    email: str = Form(None),
    phone: str = Form(None),
    username: str = Form(...),
    full_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """Register a new community user"""
    if not email and not phone:
        raise HTTPException(status_code=400, detail="Either email or phone is required")
    
    # Check if user already exists
    existing_user = None
    if email:
        existing_user = db.query(CommunityUser).filter(CommunityUser.email == email).first()
    if phone and not existing_user:
        existing_user = db.query(CommunityUser).filter(CommunityUser.phone == phone).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Check username availability
    if db.query(CommunityUser).filter(CommunityUser.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Generate OTP
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Save OTP
    otp_record = CommunityOTP(
        email=email,
        phone=phone,
        otp_code=otp_code,
        expires_at=expires_at
    )
    db.add(otp_record)
    db.commit()
    
    # Send OTP
    if email:
        send_otp_email(email, otp_code)
    if phone:
        send_otp_sms(phone, otp_code)
    
    return JSONResponse({
        "success": True,
        "message": "OTP sent successfully",
        "otp_id": otp_record.otp_id
    })

# OTP Verification Page
@router.get("/verify-otp", response_class=HTMLResponse)
async def verify_otp_page(request: Request):
    """OTP verification page"""
    return templates.TemplateResponse("community/verify_otp.html", {"request": request})

# OTP Verification
@router.post("/verify-otp", response_class=JSONResponse)
async def verify_otp(
    request: Request,
    otp_id: int = Form(...),
    otp_code: str = Form(...),
    email: str = Form(None),
    phone: str = Form(None),
    email_or_phone: str = Form(None),
    username: str = Form(None),
    full_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """Verify OTP and create user account or login"""
    # Get OTP record
    otp_record = db.query(CommunityOTP).filter(
        CommunityOTP.otp_id == otp_id,
        CommunityOTP.otp_code == otp_code,
        CommunityOTP.is_verified == False,
        CommunityOTP.expires_at > datetime.utcnow()
    ).first()
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Mark OTP as verified
    otp_record.is_verified = True
    db.commit()
    
    # If username and full_name are provided, this is registration
    if username and full_name:
        # Create new user account
        user = CommunityUser(
            email=email or otp_record.email,
            phone=phone or otp_record.phone,
            username=username,
            full_name=full_name,
            is_verified=True
        )
        db.add(user)
        db.commit()
        
        message = "Account created successfully"
    else:
        # This is login - find existing user
        user_email = email or otp_record.email
        user_phone = phone or otp_record.phone
        
        user = None
        if user_email:
            user = db.query(CommunityUser).filter(CommunityUser.email == user_email).first()
        if user_phone and not user:
            user = db.query(CommunityUser).filter(CommunityUser.phone == user_phone).first()
        
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        message = "Login successful"
    
    # Set session
    request.session["community_user_id"] = user.user_id
    request.session["community_username"] = user.username
    
    return JSONResponse({
        "success": True,
        "message": message,
        "user_id": user.user_id
    })

# Resend OTP
@router.post("/resend-otp", response_class=JSONResponse)
async def resend_otp(
    request: Request,
    otp_id: int = Form(...),
    email: str = Form(None),
    phone: str = Form(None),
    email_or_phone: str = Form(None),
    username: str = Form(None),
    full_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """Resend OTP for verification"""
    # Get existing OTP record
    otp_record = db.query(CommunityOTP).filter(CommunityOTP.otp_id == otp_id).first()
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid OTP request")
    
    # Generate new OTP
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Update OTP record
    otp_record.otp_code = otp_code
    otp_record.expires_at = expires_at
    otp_record.is_verified = False
    db.commit()
    
    # Send OTP - use existing email/phone from OTP record or new values
    send_email = email or otp_record.email
    send_phone = phone or otp_record.phone
    
    if send_email:
        send_otp_email(send_email, otp_code)
    if send_phone:
        send_otp_sms(send_phone, otp_code)
    
    return JSONResponse({
        "success": True,
        "message": "New OTP sent successfully"
    })

# User Login
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """User login page"""
    return templates.TemplateResponse("community/login.html", {"request": request})

@router.post("/login", response_class=JSONResponse)
async def login_user(
    request: Request,
    email_or_phone: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login user (OTP-based authentication)"""
    if not email_or_phone:
        raise HTTPException(status_code=400, detail="Email or phone number is required")
    
    # Determine if input is email or phone
    email = None
    phone = None
    
    if "@" in email_or_phone:
        email = email_or_phone
    else:
        phone = email_or_phone
    
    # Find user
    user = None
    if email:
        user = db.query(CommunityUser).filter(CommunityUser.email == email).first()
    if phone and not user:
        user = db.query(CommunityUser).filter(CommunityUser.phone == phone).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="User not found. Please register first.")
    
    # Generate OTP for login
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Save OTP
    otp_record = CommunityOTP(
        email=email,
        phone=phone,
        otp_code=otp_code,
        expires_at=expires_at
    )
    db.add(otp_record)
    db.commit()
    
    # Send OTP
    if email:
        send_otp_email(email, otp_code)
    if phone:
        send_otp_sms(phone, otp_code)
    
    return JSONResponse({
        "success": True,
        "message": "OTP sent for login",
        "otp_id": otp_record.otp_id
    })

# Post Creation
@router.get("/create-post", response_class=HTMLResponse)
async def create_post_page(request: Request, db: Session = Depends(get_db)):
    """Create new post page"""
    if not request.session.get("community_user_id"):
        return RedirectResponse("/community/login", status_code=302)
    
    categories = db.query(CommunityCategory).filter(CommunityCategory.is_active == True).all()
    return templates.TemplateResponse("community/create_post.html", {
        "request": request,
        "categories": categories
    })

@router.post("/create-post", response_class=JSONResponse)
async def create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    category_id: int = Form(...),
    tags: str = Form(""),
    featured_image: UploadFile = File(None),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db)
):
    """Create a new post"""
    user_id = request.session.get("community_user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(CommunityUser).filter(CommunityUser.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create slug
    slug = create_slug(title)
    base_slug = slug
    counter = 1
    while db.query(CommunityPost).filter(CommunityPost.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Handle file uploads
    featured_image_url = None
    if featured_image:
        # Save featured image
        filename = f"{uuid.uuid4()}_{featured_image.filename}"
        file_path = f"static/uploads/community/{filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            content = await featured_image.read()
            buffer.write(content)
        featured_image_url = f"/static/uploads/community/{filename}"
    
    # Handle multiple images
    image_urls = []
    for image in images:
        if image:
            filename = f"{uuid.uuid4()}_{image.filename}"
            file_path = f"static/uploads/community/{filename}"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as buffer:
                content = await image.read()
                buffer.write(content)
            image_urls.append(f"/static/uploads/community/{filename}")
    
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    # Create post
    post = CommunityPost(
        author_id=user_id,
        category_id=category_id,
        title=title,
        slug=slug,
        content=content,
        excerpt=content[:200] + "..." if len(content) > 200 else content,
        featured_image=featured_image_url,
        images=image_urls,
        tags=tag_list,
        meta_description=content[:160] if len(content) > 160 else content,
        meta_keywords=",".join(tag_list[:5])
    )
    
    db.add(post)
    db.commit()
    
    return JSONResponse({
        "success": True,
        "message": "Post created successfully",
        "post_id": post.post_id,
        "slug": post.slug
    })

# View Post
@router.get("/post/{slug}", response_class=HTMLResponse)
async def view_post(request: Request, slug: str, db: Session = Depends(get_db)):
    """View a specific post"""
    post = db.query(CommunityPost).filter(
        CommunityPost.slug == slug,
        CommunityPost.is_published == True
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Increment view count
    post.view_count += 1
    db.commit()
    
    # Get comments
    comments = db.query(CommunityComment).filter(
        CommunityComment.post_id == post.post_id,
        CommunityComment.is_approved == True
    ).order_by(desc(CommunityComment.created_at)).all()
    
    # Get related posts
    related_posts = db.query(CommunityPost).filter(
        CommunityPost.category_id == post.category_id,
        CommunityPost.post_id != post.post_id,
        CommunityPost.is_published == True
    ).order_by(desc(CommunityPost.published_at)).limit(5).all()
    
    return templates.TemplateResponse("community/post_detail.html", {
        "request": request,
        "post": post,
        "comments": comments,
        "related_posts": related_posts
    })

# Vote on Post
@router.post("/vote/{post_id}", response_class=JSONResponse)
async def vote_post(
    request: Request,
    post_id: int,
    vote_type: str = Form(...),  # 'upvote' or 'downvote'
    db: Session = Depends(get_db)
):
    """Vote on a post"""
    user_id = request.session.get("community_user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    post = db.query(CommunityPost).filter(CommunityPost.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user already voted
    existing_vote = db.query(CommunityVote).filter(
        CommunityVote.user_id == user_id,
        CommunityVote.post_id == post_id
    ).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            # Remove vote
            db.delete(existing_vote)
            if vote_type == 'upvote':
                post.upvotes -= 1
            else:
                post.downvotes -= 1
        else:
            # Change vote
            existing_vote.vote_type = vote_type
            if vote_type == 'upvote':
                post.upvotes += 1
                post.downvotes -= 1
            else:
                post.upvotes -= 1
                post.downvotes += 1
    else:
        # Create new vote
        vote = CommunityVote(
            user_id=user_id,
            post_id=post_id,
            vote_type=vote_type
        )
        db.add(vote)
        
        if vote_type == 'upvote':
            post.upvotes += 1
        else:
            post.downvotes += 1
    
    db.commit()
    
    return JSONResponse({
        "success": True,
        "upvotes": post.upvotes,
        "downvotes": post.downvotes
    })

# Company Pages
@router.get("/company/{slug}", response_class=HTMLResponse)
async def view_company(request: Request, slug: str, db: Session = Depends(get_db)):
    """View company page"""
    company = db.query(CommunityCompany).filter(
        CommunityCompany.company_slug == slug,
        CommunityCompany.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company posts
    posts = db.query(CommunityPost).filter(
        CommunityPost.company_id == company.company_id,
        CommunityPost.is_published == True
    ).order_by(desc(CommunityPost.published_at)).limit(10).all()
    
    return templates.TemplateResponse("community/company_page.html", {
        "request": request,
        "company": company,
        "posts": posts
    })

# Search
@router.get("/search", response_class=HTMLResponse)
async def search_posts(request: Request, q: str = "", db: Session = Depends(get_db)):
    """Search posts"""
    posts = []
    if q:
        posts = db.query(CommunityPost).filter(
            CommunityPost.is_published == True,
            or_(
                CommunityPost.title.ilike(f"%{q}%"),
                CommunityPost.content.ilike(f"%{q}%"),
                CommunityPost.tags.contains([q])
            )
        ).order_by(desc(CommunityPost.published_at)).limit(20).all()
    
    return templates.TemplateResponse("community/search.html", {
        "request": request,
        "query": q,
        "posts": posts
    })

# Add Comment
@router.post("/comment", response_class=JSONResponse)
async def add_comment(
    request: Request,
    post_id: int = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    """Add a comment to a post"""
    user_id = request.session.get("community_user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(CommunityUser).filter(CommunityUser.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    post = db.query(CommunityPost).filter(CommunityPost.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Create comment
    comment = CommunityComment(
        post_id=post_id,
        author_id=user_id,
        content=content,
        is_approved=True  # Auto-approve for now
    )
    db.add(comment)
    db.commit()
    
    return JSONResponse({
        "success": True,
        "message": "Comment added successfully",
        "comment_id": comment.comment_id
    })

# Delete Comment
@router.post("/comment/{comment_id}/delete", response_class=JSONResponse)
async def delete_comment(
    request: Request,
    comment_id: int,
    db: Session = Depends(get_db)
):
    """Delete a comment"""
    user_id = request.session.get("community_user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    comment = db.query(CommunityComment).filter(
        CommunityComment.comment_id == comment_id,
        CommunityComment.author_id == user_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    db.delete(comment)
    db.commit()
    
    return JSONResponse({
        "success": True,
        "message": "Comment deleted successfully"
    })

# Follow Company
@router.post("/company/{slug}/follow", response_class=JSONResponse)
async def follow_company(
    request: Request,
    slug: str,
    db: Session = Depends(get_db)
):
    """Follow/unfollow a company"""
    user_id = request.session.get("community_user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    company = db.query(CommunityCompany).filter(
        CommunityCompany.company_slug == slug,
        CommunityCompany.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # For now, just increment followers count
    company.followers_count = (company.followers_count or 0) + 1
    db.commit()
    
    return JSONResponse({
        "success": True,
        "message": "Company followed successfully",
        "followers_count": company.followers_count
    })

# Logout
@router.get("/logout", response_class=RedirectResponse)
async def logout(request: Request):
    """Logout user"""
    request.session.clear()
    return RedirectResponse("/community/", status_code=302)
