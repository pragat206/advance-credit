#!/usr/bin/env python3
"""
Render Deployment Script
This script safely creates all necessary tables on Render PostgreSQL database
"""

import os
import sys
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.shared.crm_models import CRMBase, User, Team, Employee, WebsiteLead, SocialMediaLead, LeadAssignment, Billing
from src.shared.models import Base as MainBase, AdminUser

def test_database_connection(database_url, name):
    """Test database connection"""
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✅ {name} database connection successful")
            return True
    except Exception as e:
        print(f"❌ {name} database connection failed: {e}")
        return False

def create_tables_safely(database_url, base, name):
    """Safely create tables without dropping existing data"""
    try:
        engine = create_engine(database_url)
        
        # Check if tables already exist
        inspector = engine.dialect.inspector(engine)
        existing_tables = inspector.get_table_names()
        
        print(f"📊 Existing tables in {name}: {existing_tables}")
        
        # Create tables (SQLAlchemy will skip if they exist)
        base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        inspector = engine.dialect.inspector(engine)
        new_tables = inspector.get_table_names()
        print(f"✅ {name} tables created/verified: {new_tables}")
        
        return True
    except Exception as e:
        print(f"❌ Error creating {name} tables: {e}")
        return False

def setup_admin_user(database_url):
    """Setup admin user if it doesn't exist"""
    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
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
            db.commit()
            print(f"✅ Admin user created: {admin_email}")
        else:
            print(f"✅ Admin user already exists: {admin_email}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def setup_default_teams(database_url):
    """Setup default teams if they don't exist"""
    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        teams_data = [
            {"name": "Operations"},
            {"name": "Sales"},
            {"name": "Digital"}
        ]
        
        for team_data in teams_data:
            team = db.query(Team).filter(Team.name == team_data["name"]).first()
            if not team:
                team = Team(**team_data)
                db.add(team)
                print(f"✅ Team '{team_data['name']}' created")
            else:
                print(f"✅ Team '{team_data['name']}' already exists")
        
        db.commit()
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating teams: {e}")
        return False

def verify_database_structure(database_url, name):
    """Verify that all required tables exist"""
    try:
        engine = create_engine(database_url)
        inspector = engine.dialect.inspector(engine)
        tables = inspector.get_table_names()
        
        print(f"📋 {name} database tables: {tables}")
        
        # Check for required tables
        if name == "CRM":
            required_tables = ["users", "teams", "employees", "website_leads", "social_media_leads", "lead_assignments", "billing"]
        else:
            required_tables = ["admin_users"]
        
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"⚠️ Missing tables in {name}: {missing_tables}")
            return False
        else:
            print(f"✅ All required tables exist in {name}")
            return True
            
    except Exception as e:
        print(f"❌ Error verifying {name} database: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Starting Render deployment...")
    print("=" * 50)
    
    # Get database URLs from environment
    DATABASE_URL = os.getenv("DATABASE_URL")
    CRM_DATABASE_URL = os.getenv("CRM_DATABASE_URL")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set in environment")
        return False
    
    if not CRM_DATABASE_URL:
        print("❌ CRM_DATABASE_URL not set in environment")
        return False
    
    # Fix PostgreSQL URLs for newer SQLAlchemy
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    if CRM_DATABASE_URL.startswith("postgres://"):
        CRM_DATABASE_URL = CRM_DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    print(f"📊 Main Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Local'}")
    print(f"📊 CRM Database URL: {CRM_DATABASE_URL.split('@')[1] if '@' in CRM_DATABASE_URL else 'Local'}")
    print("=" * 50)
    
    # Step 1: Test database connections
    print("\n🔗 Testing database connections...")
    if not test_database_connection(DATABASE_URL, "Main"):
        return False
    
    if not test_database_connection(CRM_DATABASE_URL, "CRM"):
        return False
    
    # Step 2: Create main website tables
    print("\n🗄️ Creating main website tables...")
    if not create_tables_safely(DATABASE_URL, MainBase, "Main website"):
        return False
    
    # Step 3: Create CRM tables
    print("\n🗄️ Creating CRM tables...")
    if not create_tables_safely(CRM_DATABASE_URL, CRMBase, "CRM"):
        return False
    
    # Step 4: Setup admin user
    print("\n👤 Setting up admin user...")
    if not setup_admin_user(CRM_DATABASE_URL):
        return False
    
    # Step 5: Setup default teams
    print("\n👥 Setting up default teams...")
    if not setup_default_teams(CRM_DATABASE_URL):
        return False
    
    # Step 6: Verify database structure
    print("\n✅ Verifying database structure...")
    if not verify_database_structure(DATABASE_URL, "Main website"):
        return False
    
    if not verify_database_structure(CRM_DATABASE_URL, "CRM"):
        return False
    
    print("\n" + "=" * 50)
    print("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print("✅ All tables created safely")
    print("✅ Admin user configured")
    print("✅ Default teams created")
    print("✅ Database structure verified")
    print("\n🌐 Your application is ready to use!")
    print(f"📧 Admin Email: {os.getenv('ADMIN_EMAIL', 'admin@advancecredit.com')}")
    print(f"🔑 Admin Password: {os.getenv('ADMIN_PASSWORD', 'admin123')}")
    print("\n🔗 Access your application:")
    print("- Main Website: Your Render URL")
    print("- CRM System: Your Render URL/crm")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 