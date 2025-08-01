# 🚀 Advance Credit - Deployment Guide

## **📋 Project Overview**
This is a unified FastAPI application containing:
- **Main Website**: Public-facing website with lead capture forms
- **CRM Portal**: Internal management system for leads and employees
- **Unified Access**: Single domain with `/crm` prefix for CRM access

## **🏗️ Project Structure**
```
news_slider/
├── app/                    # Main website application
│   ├── main.py            # Main FastAPI app with CRM integration
│   ├── models.py          # Database models
│   ├── db.py              # Database configuration
│   ├── admin/             # Admin routes
│   ├── scrapers/          # Bank loan scrapers
│   ├── templates/         # Website templates
│   └── static/            # Website assets
├── crm_portal/            # CRM application
│   ├── routes.py          # CRM routes
│   ├── templates/         # CRM templates
│   └── static/            # CRM assets
├── common_models/         # Shared database models
├── deploy_crm.py          # CRM deployment script
├── crm_main.py           # CRM standalone entry point
├── crm_requirements.txt   # CRM dependencies
├── requirements.txt       # Main app dependencies
├── Procfile              # Render deployment config
├── runtime.txt           # Python version
└── README.md            # Project documentation
```

## **🔧 Environment Variables**

### **Main Application**
```bash
# Security
SECRET_KEY=your-super-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Email (optional - forms use file logging)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@advancecfa.com
TO_EMAIL=support@advancecfa.com
USE_TLS=True

# Admin
ADMIN_PASSWORD=secure-admin-password
```

### **CRM Application**
```bash
# CRM Database
CRM_DATABASE_URL=postgresql://user:password@host:port/crm_database

# CRM Session
CRM_SESSION_SECRET=your-crm-session-secret

# CRM Base URL (for future integration)
CRM_BASE_URL=https://your-crm-app.onrender.com
```

## **🚀 Deployment Options**

### **Option 1: Single Application (Recommended)**
Deploy both main website and CRM on the same domain:

**Render.com Setup:**
1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables
5. Deploy

**Access:**
- Main Website: `https://your-app.onrender.com`
- CRM Portal: `https://your-app.onrender.com/crm`

### **Option 2: Separate Applications**
Deploy main website and CRM as separate applications:

**Main Website (Render.com):**
1. Build command: `pip install -r requirements.txt`
2. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**CRM Portal (Render.com):**
1. Build command: `pip install -r crm_requirements.txt`
2. Start command: `uvicorn crm_main:app --host 0.0.0.0 --port $PORT`

## **🗄️ Database Setup**

### **PostgreSQL (Recommended for Production)**
1. Create PostgreSQL database on Render.com or external provider
2. Set `DATABASE_URL` and `CRM_DATABASE_URL` environment variables
3. Tables will be created automatically on first run

### **SQLite (Development)**
- Default fallback for local development
- Files: `site.db` and `crm.db` (created automatically)

## **🔐 Initial Setup**

### **CRM Admin Access**
After deployment, the CRM will have a default admin user:
- **Email**: `admin@advancecredit.com`
- **Password**: `admin123`

**⚠️ Important**: Change the admin password immediately after first login!

### **Database Seeding**
The application automatically creates:
- Default admin user
- Initial teams (Operations, Sales, Digital)
- Basic database structure

## **📱 Features**

### **Main Website**
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Lead capture forms
- ✅ EMI calculators
- ✅ Debt relief calculator
- ✅ Contact forms
- ✅ WhatsApp integration
- ✅ Instagram integration

### **CRM Portal**
- ✅ Lead management (website & social media)
- ✅ Employee management
- ✅ Team management
- ✅ Billing system
- ✅ Analytics dashboard
- ✅ Role-based access control
- ✅ Bulk data upload

## **🔍 Testing Checklist**

### **Main Website**
- [ ] Homepage loads correctly
- [ ] All forms submit successfully
- [ ] Calculators work properly
- [ ] WhatsApp button opens chat
- [ ] Instagram link works
- [ ] Responsive on mobile/tablet

### **CRM Portal**
- [ ] Login page accessible at `/crm`
- [ ] Admin can log in with default credentials
- [ ] All pages load without errors
- [ ] Lead assignment works
- [ ] Employee management functions
- [ ] Billing generation works
- [ ] Analytics dashboard displays data

## **🛠️ Troubleshooting**

### **Common Issues**

**1. Database Connection Errors**
- Check environment variables
- Ensure database URL is correct
- Verify database permissions

**2. Static Files Not Loading**
- Check file paths in templates
- Verify static file mounting

**3. CRM Access Issues**
- Ensure `/crm` prefix is working
- Check session middleware configuration
- Verify admin credentials

**4. Form Submission Errors**
- Check database connectivity
- Verify form validation
- Check file permissions for logging

### **Logs**
- Check Render.com logs for errors
- Monitor application startup
- Verify database migrations

## **📞 Support**
For deployment issues or questions, contact your development team or refer to the FastAPI documentation.

---

**🎉 Your application is now clean and ready for deployment!** 