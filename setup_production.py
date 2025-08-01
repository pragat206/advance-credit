#!/usr/bin/env python3
"""
Production Setup Script for Render
This script sets up the database and initializes the application for production deployment.
"""

import os
import sys
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.shared.crm_models import Base, User, Team, WebsiteLead, SocialMediaLead
from src.shared.models import Base as MainBase, AdminUser

def setup_production_database():
    """Setup production database with PostgreSQL"""
    
    # Get database URLs from environment
    DATABASE_URL = os.getenv("DATABASE_URL")
    CRM_DATABASE_URL = os.getenv("CRM_DATABASE_URL")
    
    if not DATABASE_URL or not CRM_DATABASE_URL:
        print("❌ DATABASE_URL and CRM_DATABASE_URL must be set in environment")
        return False
    
    # Fix PostgreSQL URLs for newer SQLAlchemy
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    if CRM_DATABASE_URL.startswith("postgres://"):
        CRM_DATABASE_URL = CRM_DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    try:
        # Setup main database
        main_engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=0, pool_pre_ping=True)
        MainBase.metadata.create_all(bind=main_engine)
        print("✅ Main database setup completed")
        
        # Setup CRM database
        crm_engine = create_engine(CRM_DATABASE_URL, pool_size=20, max_overflow=0, pool_pre_ping=True)
        Base.metadata.create_all(bind=crm_engine)
        print("✅ CRM database setup completed")
        
        # Create admin user
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=crm_engine)
        db = SessionLocal()
        
        try:
            # Check if admin user already exists
            admin_email = os.getenv("ADMIN_EMAIL", "admin@advancecredit.com")
            admin_user = db.query(User).filter(User.email == admin_email).first()
            
            if not admin_user:
                # Create admin user with secure password
                admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
                admin_password_hash = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()).decode()
                
                admin_user = User(
                    name="Admin User",
                    email=admin_email,
                    phone="9987763779",
                    password_hash=admin_password_hash,
                    role="admin",
                    is_active=True
                )
                db.add(admin_user)
                print(f"✅ Admin user created: {admin_email}")
            else:
                print(f"✅ Admin user already exists: {admin_email}")
            
            # Create default teams
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
            print("✅ Production setup completed successfully")
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.rollback()
            return False
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up databases: {e}")
        return False

def main():
    """Main production setup function"""
    print("🚀 Starting production setup for Render...")
    
    # Check environment variables
    required_vars = ['DATABASE_URL', 'CRM_DATABASE_URL', 'SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your Render environment variables")
        return False
    
    # Setup database
    if not setup_production_database():
        return False
    
    print("✅ Production setup completed successfully!")
    print("🌐 Your application is ready for production deployment on Render")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 