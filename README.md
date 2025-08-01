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
├── src/                          # Main source code
│   ├── main_app/                 # Main website application
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── models.py            # Database models
│   │   ├── database.py          # Database configuration
│   │   ├── routes/              # Route modules
│   │   │   ├── __init__.py
│   │   │   ├── admin/           # Admin routes
│   │   │   └── scrapers/        # Bank scrapers
│   │   ├── templates/           # Website templates
│   │   └── static/              # Website assets
│   ├── crm/                     # CRM application
│   │   ├── __init__.py
│   │   ├── routes.py            # CRM routes
│   │   ├── templates/           # CRM templates
│   │   └── static/              # CRM assets
│   └── shared/                  # Shared components
│       ├── __init__.py
│       └── models.py            # Shared database models
├── deployment/                   # Deployment files
│   ├── scripts/
│   │   ├── deploy_crm.py        # CRM deployment script
│   │   └── setup_database.py    # Database setup
│   ├── requirements/
│   │   ├── main.txt             # Main app requirements
│   │   └── crm.txt              # CRM requirements
│   └── config/
│       ├── Procfile             # Render deployment
│       ├── runtime.txt          # Python version
│       └── build.sh             # Build script
├── docs/                        # Documentation
│   ├── README.md                # Main documentation
│   ├── DEPLOYMENT_GUIDE.md      # Deployment guide
│   └── API_DOCS.md              # API documentation
├── tests/                       # Test files
│   ├── __init__.py
│   ├── test_main_app.py
│   └── test_crm.py
├── main.py                      # Application entry point
├── requirements.txt              # Main dependencies
├── .gitignore
├── pyproject.toml
└── poetry.lock
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
   python main.py
   # or
   uvicorn main:app --reload --port 8000
   ```

4. **Access the application**
   - Main Website: `http://localhost:8000`
   - CRM Portal: `http://localhost:8000/crm`

### **Production Deployment**

See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

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
1. Update models in `src/shared/models.py`
2. Add routes in `src/main_app/main.py` or `src/crm/routes.py`
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