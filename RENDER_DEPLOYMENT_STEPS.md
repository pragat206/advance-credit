# 🚀 Render Deployment Steps

## You already have PostgreSQL databases set up! Here's how to deploy:

### **Step 1: Set Environment Variables in Render**

Go to your Render web service dashboard and add these environment variables:

```
SECRET_KEY=your-super-secure-random-key-here
DATABASE_URL=your-main-postgresql-url-from-render
CRM_DATABASE_URL=your-crm-postgresql-url-from-render
ADMIN_EMAIL=admin@advancecredit.com
ADMIN_PASSWORD=your-secure-admin-password
ENVIRONMENT=production
ALLOWED_HOSTS=your-app-name.onrender.com
ALLOWED_ORIGINS=https://your-app-name.onrender.com
```

### **Step 2: Generate Secure Keys**

Run these commands to generate secure keys:

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ADMIN_PASSWORD
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

### **Step 3: Deploy Your Code**

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Ready for Render deployment"
   git push origin main
   ```

2. **Render will automatically deploy** when it detects the push

### **Step 4: Run Database Setup Script**

After deployment, run this script to create all tables:

```bash
# In your local terminal (or Render shell)
python deploy_to_render.py
```

**This script will:**
- ✅ Test database connections
- ✅ Create all necessary tables safely
- ✅ Set up admin user
- ✅ Create default teams
- ✅ Verify everything is working

### **Step 5: Test Your Application**

1. **Health Check:**
   ```
   https://your-app-name.onrender.com/health
   ```

2. **Main Website:**
   ```
   https://your-app-name.onrender.com/
   ```

3. **CRM Login:**
   ```
   https://your-app-name.onrender.com/crm/login
   ```

### **Step 6: Verify Everything Works**

- [ ] Homepage loads correctly
- [ ] Contact form submits
- [ ] CRM login works
- [ ] Admin panel accessible
- [ ] Leads are saved to database

## 🔧 **Troubleshooting**

### **If deployment fails:**
1. Check Render logs in dashboard
2. Verify environment variables are set
3. Ensure PostgreSQL databases are running
4. Run the deployment script again

### **If database connection fails:**
1. Verify DATABASE_URL and CRM_DATABASE_URL are correct
2. Check if PostgreSQL databases are active
3. Ensure database credentials are correct

### **If tables aren't created:**
1. Run `python deploy_to_render.py` manually
2. Check the script output for errors
3. Verify database permissions

## 📊 **What the Deployment Script Does:**

### **Safely Creates Tables:**
- **Main Website:** `admin_users`
- **CRM System:** `users`, `teams`, `employees`, `website_leads`, `social_media_leads`, `lead_assignments`, `billing`

### **Sets Up Admin User:**
- Creates admin user with your credentials
- Uses environment variables for security

### **Creates Default Teams:**
- Operations team
- Sales team  
- Digital team

### **Verifies Everything:**
- Tests database connections
- Checks all tables exist
- Confirms admin user is created

## 🎯 **Success Indicators:**

✅ **Health check returns:** `{"status": "healthy", ...}`

✅ **CRM login works** with your admin credentials

✅ **Contact form saves leads** to database

✅ **All CRM features work** (leads, employees, billing, etc.)

---

**🚀 Your application will be fully functional on Render!** 