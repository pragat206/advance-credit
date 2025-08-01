import os
import sys
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from starlette.middleware.sessions import SessionMiddleware
from crm_portal.routes import router as crm_router

# Add the current directory to Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from common_models import Base

# Database configuration for production
DATABASE_URL = os.getenv("CRM_DATABASE_URL", "sqlite:///./crm.db")

# Create database engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# Create tables
Base.metadata.create_all(bind=engine)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="Advance Credit CRM", version="1.0.0")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-here")

# Mount static files
app.mount("/static", StaticFiles(directory="crm_portal/static"), name="static")

# Templates
templates = Jinja2Templates(directory="crm_portal/templates")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Include CRM routes
app.include_router(crm_router)

# Custom exception handler for 403 errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 403:
        return templates.TemplateResponse("unauthorized.html", {"request": request})
    return HTMLResponse(f"<h1>Error {exc.status_code}</h1><p>{exc.detail}</p>")

# Root redirect to login
@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port) 