# 🚀 Production Deployment Guide

## Overview
This guide will help you deploy your Advance Credit website and CRM system to production.

## 📋 Pre-Deployment Checklist

### 1. Security Configuration
- [ ] Generate secure SECRET_KEY
- [ ] Set secure ADMIN_PASSWORD
- [ ] Configure database URLs
- [ ] Set up environment variables

### 2. Database Setup
- [ ] Set up PostgreSQL database
- [ ] Configure database connection pooling
- [ ] Set up database backups

### 3. Domain & SSL
- [ ] Configure domain name
- [ ] Set up SSL certificate
- [ ] Configure DNS settings

## 🔧 Environment Setup

### 1. Create Environment File
```bash
# Copy the example file
cp env.example .env

# Edit with your production values
nano .env
```

### 2. Required Environment Variables
```bash
# Security
SECRET_KEY=your-super-secure-random-key-here
CRM_SESSION_SECRET=another-secure-random-key

# Database URLs (Use PostgreSQL for production)
DATABASE_URL=postgresql://username:password@host:port/database_name
CRM_DATABASE_URL=postgresql://username:password@host:port/crm_database_name

# Admin Credentials
ADMIN_EMAIL=admin@advancecredit.com
ADMIN_PASSWORD=secure-production-password

# Application Settings
DEBUG=False
ENVIRONMENT=production
ALLOWED_HOSTS=advancecredit.com,www.advancecredit.com
```

## 🗄️ Database Setup

### PostgreSQL Setup
1. **Create Database**
   ```sql
   CREATE DATABASE advancecredit_main;
   CREATE DATABASE advancecredit_crm;
   ```

2. **Install PostgreSQL Driver**
   ```bash
   pip install psycopg2-binary
   ```

3. **Run Database Setup**
   ```bash
   python deployment/scripts/setup_production.py
   ```

## 🚀 Deployment Options

### Option 1: Render.com (Recommended)
1. **Connect Repository**
   - Link your GitHub repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Environment Variables**
   - Add all variables from `.env` file
   - Set `ENVIRONMENT=production`

3. **Database**
   - Create PostgreSQL database on Render
   - Use provided database URLs

### Option 2: Railway
1. **Deploy from GitHub**
2. **Add PostgreSQL addon**
3. **Configure environment variables**

### Option 3: DigitalOcean App Platform
1. **Connect GitHub repository**
2. **Add PostgreSQL database**
3. **Configure environment variables**

## 🔒 Security Checklist

### 1. Environment Variables
- [ ] SECRET_KEY is secure and random
- [ ] Database passwords are strong
- [ ] Admin password is secure
- [ ] No hardcoded credentials

### 2. Database Security
- [ ] PostgreSQL with SSL
- [ ] Strong database passwords
- [ ] Connection pooling enabled
- [ ] Regular backups configured

### 3. Application Security
- [ ] HTTPS enabled
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Security headers set

## 📊 Monitoring & Maintenance

### 1. Health Checks
- [ ] `/health` endpoint working
- [ ] Database connectivity
- [ ] Form submissions working

### 2. Logging
- [ ] Application logs configured
- [ ] Error tracking setup
- [ ] Performance monitoring

### 3. Backups
- [ ] Database backups scheduled
- [ ] File backups configured
- [ ] Recovery procedures documented

## 🧪 Testing Checklist

### 1. Functionality Tests
- [ ] Homepage loads correctly
- [ ] Contact form submits
- [ ] CRM login works
- [ ] Lead capture functional
- [ ] Admin panel accessible

### 2. Security Tests
- [ ] No hardcoded passwords
- [ ] HTTPS redirects working
- [ ] CORS properly configured
- [ ] Rate limiting active

### 3. Performance Tests
- [ ] Page load times < 3 seconds
- [ ] Database queries optimized
- [ ] Static files cached
- [ ] Mobile responsive

## 🚨 Emergency Procedures

### 1. Database Issues
```bash
# Check database connectivity
python -c "from src.main_app.database import engine; print(engine.execute('SELECT 1').fetchone())"
```

### 2. Application Issues
```bash
# Check application logs
tail -f /var/log/application.log

# Restart application
sudo systemctl restart your-app
```

### 3. Security Breach
1. **Immediate Actions**
   - Change all passwords
   - Review access logs
   - Update security keys

2. **Investigation**
   - Check application logs
   - Review database access
   - Audit user accounts

## 📞 Support Contacts

- **Technical Issues**: Your development team
- **Hosting Support**: Your hosting provider
- **Domain Issues**: Your domain registrar

## 🔄 Update Procedures

### 1. Code Updates
```bash
# Pull latest changes
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Restart application
sudo systemctl restart your-app
```

### 2. Database Migrations
```bash
# Run migration scripts
python deployment/scripts/setup_production.py
```

### 3. Configuration Updates
- Update environment variables
- Restart application
- Test functionality

---

**⚠️ Important Notes:**
- Always test in staging environment first
- Keep backups before major updates
- Monitor application after deployment
- Document any custom configurations 