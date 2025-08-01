#!/usr/bin/env python3
"""
CRM Deployment Script for Render
This script sets up the database and seeds initial data for production deployment.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt
from datetime import datetime, date

# Add the current directory to Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from common_models import Base, User, Team, Employee, WebsiteLead, SocialMediaLead

def setup_database():
    """Set up the database and create initial data"""
    
    # Database configuration for production
    DATABASE_URL = os.getenv("CRM_DATABASE_URL", "sqlite:///./crm.db")
    
    # Create database engine
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == "admin@advancecredit.com").first()
        if not admin_user:
            # Create admin user
            admin_password = bcrypt.hashpw(os.getenv("ADMIN_PASSWORD", "admin123").encode(), bcrypt.gensalt()).decode()
            admin_user = User(
                name="Admin User",
                email="admin@advancecredit.com",
                phone="9987763779",
                password_hash=admin_password,
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("✅ Admin user created successfully")
        else:
            print("✅ Admin user already exists")
        
        # Create teams if they don't exist
        teams_data = [
            {"name": "Operations", "description": "Operations team handling customer service"},
            {"name": "Sales", "description": "Sales team for lead conversion"},
            {"name": "Digital", "description": "Digital marketing and online presence"}
        ]
        
        for team_data in teams_data:
            team = db.query(Team).filter(Team.name == team_data["name"]).first()
            if not team:
                team = Team(**team_data)
                db.add(team)
                print(f"✅ Team '{team_data['name']}' created")
        
        db.commit()
        print("✅ Database setup completed successfully")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting CRM deployment setup...")
    setup_database()
    print("✅ CRM deployment setup completed!") 