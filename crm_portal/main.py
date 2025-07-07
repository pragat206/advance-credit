print("MAIN.PY IS LOADED")
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common_models import Base, Employee, Lead, Partner
from starlette.middleware.sessions import SessionMiddleware
from crm_portal.routes import router as crm_router

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=os.getenv("CRM_SESSION_SECRET", "supersecretkey"))

app.mount("/static", StaticFiles(directory="crm_portal/static"), name="static")
templates = Jinja2Templates(directory="crm_portal/templates")

DATABASE_URL = os.getenv("CRM_DATABASE_URL", "sqlite:///../site.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse("/login")

app.include_router(crm_router)
