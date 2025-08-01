#!/usr/bin/env python3
"""
Production Setup Script
This script sets up the application for production deployment.
"""

import os
import sys
import secrets
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.shared.crm_models import Base, User, Team, WebsiteLead, SocialMediaLead
from src.shared.models import Base as MainBase

def generate_secure_key():
    """Generate a secure random key"""
    return secrets.token_urlsafe(32)

def setup_production_environment():
    """Setup production environment variables"""
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("📝 Please create a .env file with the following variables:")
        print("   - Copy from env.example and fill in your values")
        return False
    
    # Validate required environment variables
    required_vars = [
        'SECRET_KEY',
        'CRM_DATABASE_URL', 
        'DATABASE_URL',
        'ADMIN_EMAIL',
        'ADMIN_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment variables validated")
    return True

def setup_databases():
    """Setup production databases"""
    
    # Main website database
    main_db_url = os.getenv("DATABASE_URL")
    if not main_db_url:
        print("❌ DATABASE_URL not set")
        return False
    
    try:
        main_engine = create_engine(main_db_url)
        MainBase.metadata.create_all(bind=main_engine)
        print("✅ Main website database setup completed")
    except Exception as e:
        print(f"❌ Error setting up main database: {e}")
        return False
    
    # CRM database
    crm_db_url = os.getenv("CRM_DATABASE_URL")
    if not crm_db_url:
        print("❌ CRM_DATABASE_URL not set")
        return False
    
    try:
        crm_engine = create_engine(crm_db_url)
        Base.metadata.create_all(bind=crm_engine)
        print("✅ CRM database setup completed")
    except Exception as e:
        print(f"❌ Error setting up CRM database: {e}")
        return False
    
    return True

def create_admin_user():
    """Create admin user for production"""
    
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if not admin_email or not admin_password:
        print("❌ ADMIN_EMAIL or ADMIN_PASSWORD not set")
        return False
    
    crm_db_url = os.getenv("CRM_DATABASE_URL")
    engine = create_engine(crm_db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == admin_email).first()
        if not admin_user:
            # Create admin user with secure password
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
            db.commit()
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

def main():
    """Main production setup function"""
    print("🚀 Starting production setup...")
    
    # Step 1: Validate environment
    if not setup_production_environment():
        return False
    
    # Step 2: Setup databases
    if not setup_databases():
        return False
    
    # Step 3: Create admin user
    if not create_admin_user():
        return False
    
    print("✅ Production setup completed successfully!")
    print("🔐 Please ensure your environment variables are secure")
    print("🌐 Your application is ready for production deployment")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 