#!/usr/bin/env python3
"""
Test script to check if leads are being saved to the database
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the current directory to Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.shared.crm_models import WebsiteLead

# Database URL (use the same as in your application)
DATABASE_URL = "postgresql://advancecredit_user:wJVDdYJ2bRbakoiyDcmkWsOjb2UmnLke@dpg-d26cobnfte5s73enhjm0-a.ohio-postgres.render.com/advancecredit"

def test_database():
    """Test if leads are in the database"""
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Query all website leads
        leads = db.query(WebsiteLead).all()
        
        print(f"✅ Found {len(leads)} leads in database:")
        for lead in leads:
            print(f"  - {lead.name} ({lead.contact}) - {lead.email}")
            print(f"    Message: {lead.message}")
            print(f"    Created: {lead.created_at}")
            print()
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking database for leads...")
    test_database() 