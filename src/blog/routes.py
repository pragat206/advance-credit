from fastapi import APIRouter, Depends, HTTPException, Request, Form, File, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
import os
import uuid
import re

from src.main_app.database import get_db
from src.blog.models import BlogPost

# Templates
templates = Jinja2Templates(directory="src/blog/templates")

router = APIRouter()

# Utility functions
def create_slug(text):
    """Create URL-friendly slug from text"""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

# Blog Homepage - Display all posts as cards
@router.get("/", response_class=HTMLResponse)
async def blog_home(request: Request, db: Session = Depends(get_db)):
    """Blog homepage with all posts displayed as cards"""
    posts = db.query(BlogPost).filter(BlogPost.is_published == True).order_by(desc(BlogPost.created_at)).all()
    return templates.TemplateResponse("blog/home.html", {
        "request": request,
        "posts": posts
    })

# View individual post
@router.get("/post/{slug}", response_class=HTMLResponse)
async def view_post(request: Request, slug: str, db: Session = Depends(get_db)):
    """View a specific blog post"""
    post = db.query(BlogPost).filter(
        BlogPost.slug == slug,
        BlogPost.is_published == True
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return templates.TemplateResponse("blog/post_detail.html", {
        "request": request,
        "post": post
    })

# Admin Panel - List all posts
@router.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    """Admin panel to manage blog posts"""
    posts = db.query(BlogPost).order_by(desc(BlogPost.created_at)).all()
    return templates.TemplateResponse("blog/admin.html", {
        "request": request,
        "posts": posts
    })

# Admin Panel - Create new post
@router.get("/admin/create", response_class=HTMLResponse)
async def create_post_page(request: Request):
    """Create new post page"""
    return templates.TemplateResponse("blog/create_post.html", {
        "request": request
    })

@router.post("/admin/create", response_class=JSONResponse)
async def create_post(
    request: Request,
    title: str = Form(...),
    summary: str = Form(""),
    content: str = Form(...),
    featured_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """Create a new blog post"""
    
    # Create slug
    slug = create_slug(title)
    base_slug = slug
    counter = 1
    while db.query(BlogPost).filter(BlogPost.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Handle file upload
    featured_image_url = None
    if featured_image:
        # Save featured image
        filename = f"{uuid.uuid4()}_{featured_image.filename}"
        file_path = f"src/blog/static/uploads/{filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            content_data = await featured_image.read()
            buffer.write(content_data)
        featured_image_url = f"/blog/static/uploads/{filename}"
    
    # Create post
    post = BlogPost(
        title=title,
        slug=slug,
        summary=summary,
        content=content,
        featured_image=featured_image_url
    )
    
    db.add(post)
    db.commit()
    
    return JSONResponse({
        "success": True,
        "message": "Post created successfully",
        "post_id": post.id,
        "slug": post.slug
    })

# Admin Panel - Edit post
@router.get("/admin/edit/{post_id}", response_class=HTMLResponse)
async def edit_post_page(request: Request, post_id: int, db: Session = Depends(get_db)):
    """Edit post page"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return templates.TemplateResponse("blog/edit_post.html", {
        "request": request,
        "post": post
    })

@router.post("/admin/edit/{post_id}", response_class=JSONResponse)
async def edit_post(
    request: Request,
    post_id: int,
    title: str = Form(...),
    summary: str = Form(""),
    content: str = Form(...),
    featured_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """Edit a blog post"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Update fields
    post.title = title
    post.summary = summary
    post.content = content
    
    # Handle file upload if new image provided
    if featured_image:
        # Save featured image
        filename = f"{uuid.uuid4()}_{featured_image.filename}"
        file_path = f"src/blog/static/uploads/{filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            content_data = await featured_image.read()
            buffer.write(content_data)
        post.featured_image = f"/blog/static/uploads/{filename}"
    
    # Update slug if title changed
    new_slug = create_slug(title)
    if new_slug != post.slug:
        base_slug = new_slug
        counter = 1
        while db.query(BlogPost).filter(BlogPost.slug == new_slug, BlogPost.id != post_id).first():
            new_slug = f"{base_slug}-{counter}"
            counter += 1
        post.slug = new_slug
    
    db.commit()
    
    return JSONResponse({
        "success": True,
        "message": "Post updated successfully",
        "post_id": post.id,
        "slug": post.slug
    })

# Admin Panel - Delete post
@router.post("/admin/delete/{post_id}", response_class=JSONResponse)
async def delete_post(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db)
):
    """Delete a blog post"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Delete featured image file if exists
    if post.featured_image:
        image_path = post.featured_image.replace("/blog/static/uploads/", "src/blog/static/uploads/")
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.delete(post)
    db.commit()
    
    return JSONResponse({
        "success": True,
        "message": "Post deleted successfully"
    })

# Admin Panel - Toggle post status
@router.post("/admin/toggle/{post_id}", response_class=JSONResponse)
async def toggle_post_status(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db)
):
    """Toggle post published status"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.is_published = not post.is_published
    db.commit()
    
    return JSONResponse({
        "success": True,
        "message": f"Post {'published' if post.is_published else 'unpublished'} successfully",
        "is_published": post.is_published
    })
