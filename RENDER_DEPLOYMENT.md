# 🚀 Render Deployment Guide

## Overview
This guide will help you deploy your Advance Credit website and CRM to Render.com

## 📋 Pre-Deployment Checklist

### 1. Repository Setup
- [ ] Code is pushed to GitHub
- [ ] All files are committed
- [ ] No sensitive data in code (passwords, keys)

### 2. Environment Variables (Set in Render Dashboard)
- [ ] `SECRET_KEY` - Secure random key
- [ ] `DATABASE_URL` - PostgreSQL database URL
- [ ] `CRM_DATABASE_URL` - CRM PostgreSQL database URL
- [ ] `ADMIN_EMAIL` - Admin email address
- [ ] `ADMIN_PASSWORD` - Secure admin password
- [ ] `ENVIRONMENT` - Set to "production"

## 🔧 Render Setup Steps

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Connect your GitHub repository

### Step 2: Create PostgreSQL Database
1. In Render dashboard, click "New +"
2. Select "PostgreSQL"
3. Choose a name (e.g., "advancecredit-main-db")
4. Select your region
5. Choose "Free" plan for testing
6. Click "Create Database"
7. **Copy the Internal Database URL**

### Step 3: Create Second PostgreSQL Database (for CRM)
1. Repeat Step 2 for CRM database
2. Name it "advancecredit-crm-db"
3. **Copy the Internal Database URL**

### Step 4: Create Web Service
1. In Render dashboard, click "New +"
2. Select "Web Service"
3. Connect your GitHub repository
4. Configure the service:

**Basic Settings:**
- **Name**: `advancecredit-website`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn main:app --bind 0.0.0.0:$PORT --worker-class uvicorn.workers.UvicornWorker`

**Environment Variables:**
```
SECRET_KEY=your-super-secure-random-key-here
DATABASE_URL=postgresql://user:pass@host:port/dbname
CRM_DATABASE_URL=postgresql://user:pass@host:port/crmdbname
ADMIN_EMAIL=admin@advancecredit.com
ADMIN_PASSWORD=your-secure-admin-password
ENVIRONMENT=production
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

## 🔒 Security Configuration

### Generate Secure Keys
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ADMIN_PASSWORD
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

### Environment Variables Checklist
- [ ] `SECRET_KEY` - 32+ character random string
- [ ] `ADMIN_PASSWORD` - 16+ character secure password
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `CRM_DATABASE_URL` - CRM PostgreSQL connection string
- [ ] `ENVIRONMENT` - Set to "production"
- [ ] `ALLOWED_HOSTS` - Your domain names
- [ ] `ALLOWED_ORIGINS` - Your domain URLs

## 🗄️ Database Setup

### Automatic Setup
The application will automatically:
1. Create database tables on first run
2. Create admin user with your credentials
3. Create default teams (Operations, Sales, Digital)

### Manual Setup (if needed)
```bash
# Run the production setup script
python setup_production.py
```

## 🌐 Custom Domain Setup

### 1. Add Custom Domain in Render
1. Go to your web service
2. Click "Settings"
3. Scroll to "Custom Domains"
4. Add your domain (e.g., `advancecredit.com`)

### 2. Update DNS Records
Add these DNS records to your domain provider:
```
Type: CNAME
Name: @
Value: your-app-name.onrender.com
```

### 3. Update Environment Variables
Update these in Render dashboard:
```
ALLOWED_HOSTS=advancecredit.com,www.advancecredit.com
ALLOWED_ORIGINS=https://advancecredit.com,https://www.advancecredit.com
```

## 🧪 Testing Deployment

### 1. Health Check
Visit: `https://your-app-name.onrender.com/health`
Should return: `{"status": "healthy", ...}`

### 2. Main Website
Visit: `https://your-app-name.onrender.com/`
Should show the homepage

### 3. CRM Access
Visit: `https://your-app-name.onrender.com/crm/login`
Login with your admin credentials

### 4. Form Testing
- Test contact form submission
- Check if leads appear in CRM
- Verify admin panel functionality

## 🔧 Troubleshooting

### Common Issues

**1. Build Failures**
- Check `requirements.txt` is up to date
- Verify Python version in `runtime.txt`
- Check build logs in Render dashboard

**2. Database Connection Issues**
- Verify `DATABASE_URL` and `CRM_DATABASE_URL` are correct
- Check if PostgreSQL databases are created
- Ensure database credentials are correct

**3. Static Files Not Loading**
- Verify static file paths in code
- Check if files are in correct directories
- Ensure `StaticFiles` middleware is configured

**4. Admin Login Issues**
- Verify `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set
- Check if admin user was created
- Try running setup script manually

### Debug Commands
```bash
# Check application logs
# In Render dashboard → Logs

# Test database connection
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
print('Database connection:', engine.execute('SELECT 1').fetchone())
"
```

## 📊 Monitoring

### Health Checks
- Render automatically monitors `/health` endpoint
- Service will restart if health check fails

### Logs
- View logs in Render dashboard
- Set up log forwarding if needed

### Performance
- Monitor response times
- Check database connection pool usage
- Monitor memory usage

## 🔄 Updates and Maintenance

### Code Updates
1. Push changes to GitHub
2. Render automatically redeploys
3. Check deployment logs
4. Test functionality

### Database Updates
1. Run migrations if needed
2. Backup database before major changes
3. Test in staging environment first

### Environment Variable Updates
1. Go to Render dashboard
2. Update environment variables
3. Redeploy service
4. Test functionality

## 🚨 Emergency Procedures

### Rollback
1. Go to Render dashboard
2. Click "Manual Deploy"
3. Select previous commit
4. Deploy

### Database Issues
1. Check database status in Render
2. Verify connection strings
3. Restart database if needed
4. Contact Render support

### Security Issues
1. Rotate `SECRET_KEY`
2. Change `ADMIN_PASSWORD`
3. Update environment variables
4. Redeploy service

---

**✅ Your application is now ready for production deployment on Render!** 