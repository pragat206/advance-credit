#!/usr/bin/env python3
"""
Deployment test script for Advance Credit
This script tests the basic functionality of the application
"""

import os
import sys
import subprocess
import time
import requests

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        from app.main import app
        from app.db import get_db, engine
        from app.models import Base
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database():
    """Test database connection and table creation"""
    print("Testing database...")
    try:
        from app.db import engine
        from app.models import Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_static_files():
    """Test if static files exist"""
    print("Testing static files...")
    static_dirs = [
        "app/static",
        "app/static/partners",
        "app/static/hero",
        "app/static/banners"
    ]
    
    for dir_path in static_dirs:
        if not os.path.exists(dir_path):
            print(f"❌ Static directory missing: {dir_path}")
            return False
    
    print("✅ Static files check passed")
    return True

def test_templates():
    """Test if templates exist"""
    print("Testing templates...")
    template_files = [
        "app/templates/home.html",
        "app/templates/about.html",
        "app/templates/products.html",
        "app/templates/services.html",
        "app/templates/partners.html",
        "app/templates/emi.html",
        "app/templates/navbar.html",
        "app/templates/footer.html"
    ]
    
    for template in template_files:
        if not os.path.exists(template):
            print(f"❌ Template missing: {template}")
            return False
    
    print("✅ Templates check passed")
    return True

def test_requirements():
    """Test if requirements.txt exists and is valid"""
    print("Testing requirements...")
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt missing")
        return False
    
    with open("requirements.txt", "r") as f:
        requirements = f.read()
        if "fastapi" not in requirements or "uvicorn" not in requirements:
            print("❌ Missing required packages in requirements.txt")
            return False
    
    print("✅ Requirements check passed")
    return True

def test_deployment_files():
    """Test if deployment files exist"""
    print("Testing deployment files...")
    deployment_files = [
        "Procfile",
        "runtime.txt",
        "build.sh"
    ]
    
    for file in deployment_files:
        if not os.path.exists(file):
            print(f"❌ Deployment file missing: {file}")
            return False
    
    print("✅ Deployment files check passed")
    return True

def main():
    """Run all deployment tests"""
    print("🚀 Advance Credit - Deployment Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database,
        test_static_files,
        test_templates,
        test_requirements,
        test_deployment_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Ready for deployment.")
        print("\n📋 Deployment Checklist:")
        print("1. ✅ Code is ready")
        print("2. ✅ Dependencies are specified")
        print("3. ✅ Database configuration is set")
        print("4. ✅ Static files are included")
        print("5. ✅ Templates are complete")
        print("6. ✅ Deployment files are ready")
        print("\n🚀 Ready to deploy on Render.com!")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 