# 🏦 Advance Credit - Financial Services Platform

A comprehensive FastAPI application combining a public-facing financial services website with an integrated CRM system for lead management and employee operations.

## **🎯 Features**

### **🌐 Main Website**
- **Responsive Design**: Mobile, tablet, and desktop optimized
- **Lead Capture**: Contact forms, loan applications, debt consultation
- **Financial Calculators**: EMI calculator, debt relief calculator
- **Social Integration**: WhatsApp chat, Instagram links
- **Dynamic Content**: Partner logos, testimonials, team profiles

### **🔐 CRM Portal** (`/crm`)
- **Lead Management**: Website and social media leads
- **Employee Management**: Profiles, roles, teams, billing
- **Analytics Dashboard**: Performance metrics and insights
- **Role-Based Access**: Admin and employee permissions
- **Bulk Operations**: CSV upload, data export

## **🏗️ Project Structure**

```
news_slider/
├── app/                    # Main website application
│   ├── main.py            # FastAPI app with CRM integration
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
└── DEPLOYMENT_GUIDE.md   # Deployment instructions
```

## **🚀 Quick Start**

### **Local Development**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd news_slider
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

4. **Access the application**
   - Main Website: `http://localhost:8000`
   - CRM Portal: `http://localhost:8000/crm`

### **Production Deployment**

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

## **🔧 Environment Variables**

### **Required Variables**
```bash
# Security
SECRET_KEY=your-super-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@host:port/database
CRM_DATABASE_URL=postgresql://user:password@host:port/crm_database

# CRM Session
CRM_SESSION_SECRET=your-crm-session-secret
```

### **Optional Variables**
```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@advancecfa.com
TO_EMAIL=support@advancecfa.com
USE_TLS=True

# Admin Configuration
ADMIN_PASSWORD=secure-admin-password
```

## **🔐 Default Access**

### **CRM Admin**
- **URL**: `/crm`
- **Email**: `admin@advancecredit.com`
- **Password**: `admin123`

**⚠️ Important**: Change the default password immediately after deployment!

## **📱 Technology Stack**

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL/SQLite
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Authentication**: Session-based with role management
- **Deployment**: Render.com, Docker-ready
- **Database**: PostgreSQL (production), SQLite (development)

## **🔄 Database Setup**

The application automatically creates all necessary tables and seeds initial data:
- Default admin user
- Initial teams (Operations, Sales, Digital)
- Database schema for leads, employees, billing

## **📊 Features Overview**

### **Main Website**
- ✅ Responsive design across all devices
- ✅ Lead capture forms with validation
- ✅ Real-time EMI and debt relief calculators
- ✅ WhatsApp and Instagram integration
- ✅ Dynamic content management
- ✅ SEO optimized pages

### **CRM Portal**
- ✅ Unified login with role-based access
- ✅ Lead assignment and tracking
- ✅ Employee and team management
- ✅ Billing and commission tracking
- ✅ Analytics and reporting
- ✅ Bulk data operations
- ✅ Export functionality

## **🛠️ Development**

### **Adding New Features**
1. Update models in `common_models/__init__.py`
2. Add routes in `app/main.py` or `crm_portal/routes.py`
3. Create templates in respective `templates/` directories
4. Update static files as needed

### **Database Changes**
- Models are auto-created on startup
- For complex migrations, consider using Alembic

### **Styling**
- Main website: Bootstrap with custom CSS
- CRM: Glass-morphism design with modern UI

## **🔍 Testing**

### **Pre-Deployment Checklist**
- [ ] All forms submit successfully
- [ ] Calculators work correctly
- [ ] CRM login and navigation work
- [ ] Lead assignment functions
- [ ] Employee management works
- [ ] Responsive design on all devices
- [ ] Environment variables configured

## **📞 Support**

For technical support or feature requests, contact your development team.

---

**🎉 Ready for production deployment!** 