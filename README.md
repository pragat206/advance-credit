# Advance Credit - Financial Advisory Platform

A comprehensive financial advisory platform built with FastAPI, featuring a modern website and integrated CRM system for debt consolidation and loan management.

## 🚀 Features

### Website Features
- **Modern Landing Page** with hero banners and value propositions
- **Loan Products** showcase with detailed information
- **Financial Services** overview and consultation booking
- **About Us** with team information and company achievements
- **Contact Form** with lead capture
- **EMI Calculator** for debt consolidation calculations
- **Partner Showcase** with banking partners

### CRM System
- **Lead Management** with unified lead tracking
- **Employee Management** with role-based access
- **Team Management** with performance tracking
- **Analytics Dashboard** with key metrics
- **Billing System** for commission tracking
- **Activity Logs** with JIRA-style interface
- **Bulk Lead Import** via CSV upload
- **Progress Tracking** with visual workflow

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.12+
- **Database**: PostgreSQL (Production), SQLite (Development)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication**: JWT tokens with bcrypt
- **ORM**: SQLAlchemy 2.0+
- **Server**: Uvicorn/Gunicorn

## 📦 Installation

### Prerequisites
- Python 3.12+
- PostgreSQL (for production)
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd advance-credit
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   uvicorn src.main_app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Production Deployment

1. **Set environment variables**
   - `DATABASE_URL`: PostgreSQL connection string
   - `CRM_DATABASE_URL`: CRM database connection string
   - `SECRET_KEY`: JWT secret key
   - `ENVIRONMENT`: Set to "production"

2. **Deploy with Gunicorn**
   ```bash
   gunicorn src.main_app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

## 🗄️ Database Schema

### Main Tables
- **Users**: User authentication and profiles
- **Leads**: Unified lead management
- **Lead Assignments**: Lead assignment and tracking
- **Employees**: Employee management
- **Teams**: Team organization
- **Activities**: Activity logging and timeline

### Key Features
- **Unified Lead System**: All leads (website, social, manual) in one place
- **Workflow Tracking**: Visual progress tree with status management
- **Activity Logging**: Comprehensive audit trail
- **Role-based Access**: Admin, Manager, Employee roles

## 🔧 Configuration

### Environment Variables
```env
# Database
DATABASE_URL=postgresql://adv_cred_usr_prd:iZHC0gRJoBRkpoHULM7ZovXZ2HeH9eAj@dpg-d2u6t57fte5s73asjovg-a/advancecred_prd
CRM_DATABASE_URL=postgresql://adv_cred_usr_prd:iZHC0gRJoBRkpoHULM7ZovXZ2HeH9eAj@dpg-d2u6t57fte5s73asjovg-a/advancecred_prd

# Security
SECRET_KEY=your-secret-key-here
ENVIRONMENT=production

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 📱 Usage

### Website
- Visit the homepage for loan products and services
- Use the EMI calculator for debt consolidation estimates
- Submit contact forms for consultation requests
- Browse partner information and team details

### CRM System
- Access at `/crm/login` with employee credentials
- Manage leads in the unified leads section
- Track progress with visual workflow trees
- Generate reports and analytics
- Manage team members and assignments

## 🚀 Deployment

### Render.com Deployment
1. Connect your GitHub repository to Render
2. Create a PostgreSQL database service
3. Set environment variables in Render dashboard
4. Deploy as a web service with the following settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn src.main_app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

### Environment Variables for Render
```
DATABASE_URL=postgresql://adv_cred_usr_prd:iZHC0gRJoBRkpoHULM7ZovXZ2HeH9eAj@dpg-d2u6t57fte5s73asjovg-a/advancecred_prd
CRM_DATABASE_URL=postgresql://adv_cred_usr_prd:iZHC0gRJoBRkpoHULM7ZovXZ2HeH9eAj@dpg-d2u6t57fte5s73asjovg-a/advancecred_prd
SECRET_KEY=your-secret-key
ENVIRONMENT=production
```

## 📊 Key Metrics

The platform tracks:
- **500+ Families Helped**
- **₹500Cr+ Debt Consolidated**
- **1000+ Disbursements**
- **50+ Bank Partners**
- **4.8/5 Customer Rating**

## 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control
- SQL injection protection
- XSS protection
- CSRF protection

## 📈 Performance

- Optimized database queries
- Efficient caching strategies
- Responsive design for all devices
- Fast page load times
- Scalable architecture

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is proprietary software. All rights reserved.

## 📞 Support

For support and inquiries:
- Email: support@advancecfa.com
- Phone: +91-XXXX-XXXX
- Website: https://advancecfa.com

---

**Advance Credit** - Your trusted partner in financial transformation.