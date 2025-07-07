# 🚀 Render.com Deployment Guide

## Quick Deployment Steps

### 1. Prepare Your Repository
- ✅ All files are ready for deployment
- ✅ Dependencies are specified in `requirements.txt`
- ✅ Database configuration supports both SQLite and PostgreSQL
- ✅ Environment variables are properly configured

### 2. Deploy on Render.com

#### Step 1: Connect Repository
1. Go to [Render.com](https://render.com)
2. Sign up/Login with your GitHub account
3. Click "New +" → "Web Service"
4. Connect your GitHub repository

#### Step 2: Configure Web Service
- **Name**: `advance-credit-web` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `main` (or your default branch)

#### Step 3: Build & Start Commands
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app.main:app --bind 0.0.0.0:$PORT --worker-class uvicorn.workers.UvicornWorker`

#### Step 4: Environment Variables
Add these environment variables in Render.com dashboard:

```
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=postgresql://user:password@host:port/database
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@advancecfa.com
TO_EMAIL=vikas@advancecfa.com
USE_TLS=True
ADMIN_PASSWORD=your-secure-admin-password
```

#### Step 5: Deploy
- Click "Create Web Service"
- Render will automatically build and deploy your application
- Wait for the build to complete (usually 2-5 minutes)

### 3. Post-Deployment

#### Verify Deployment
- Your app will be available at: `https://your-app-name.onrender.com`
- Test all main pages:
  - Homepage: `/`
  - About: `/about`
  - Products: `/products`
  - Services: `/services`
  - Partners: `/partners`
  - EMI Calculator: `/emi`
  - Admin Portal: `/admin`

#### Database Setup (Optional)
If you want to use PostgreSQL instead of SQLite:
1. Create a PostgreSQL database in Render.com
2. Update the `DATABASE_URL` environment variable
3. Redeploy the application

## File Structure for Deployment

```
news_slider/
├── app/
│   ├── main.py              # FastAPI application
│   ├── db.py                # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── admin/               # Admin portal
│   ├── scrapers/            # Bank scrapers
│   ├── static/              # Static files
│   └── templates/           # HTML templates
├── requirements.txt          # Python dependencies
├── Procfile                 # Render.com deployment
├── runtime.txt              # Python version
├── build.sh                 # Build script
├── .gitignore               # Git ignore rules
└── README.md               # Documentation
```

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Session secret key | `super-secret-key-change-this` | Yes |
| `DATABASE_URL` | Database connection | SQLite local | No |
| `SMTP_SERVER` | Email server | `localhost` | No |
| `SMTP_PORT` | Email port | `25` | No |
| `SMTP_USERNAME` | Email username | Empty | No |
| `SMTP_PASSWORD` | Email password | Empty | No |
| `FROM_EMAIL` | From email | `noreply@advancecfa.com` | No |
| `TO_EMAIL` | Default recipient | `vikas@advancecfa.com` | No |
| `USE_TLS` | Use TLS for email | `False` | No |
| `ADMIN_PASSWORD` | Admin password | `admin123` | No |

## Troubleshooting

### Common Issues

#### 1. Build Fails
- Check that `requirements.txt` exists and is valid
- Ensure all dependencies are compatible
- Check Python version in `runtime.txt`

#### 2. Application Won't Start
- Verify the start command in Procfile
- Check environment variables are set correctly
- Review logs in Render.com dashboard

#### 3. Database Issues
- Ensure `DATABASE_URL` is set correctly
- For PostgreSQL, check connection string format
- Verify database permissions

#### 4. Static Files Not Loading
- Check that static files are in `app/static/`
- Verify StaticFiles mounting in `main.py`
- Clear browser cache

### Debug Commands

```bash
# Test locally before deploying
poetry run python deploy_test.py

# Run locally with production settings
poetry run python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT

# Check application logs
# Use Render.com dashboard → Logs tab
```

## Security Checklist

- [ ] Change default admin password
- [ ] Set a strong SECRET_KEY
- [ ] Configure proper SMTP settings
- [ ] Use HTTPS (automatic on Render.com)
- [ ] Set up proper environment variables
- [ ] Review and update admin credentials

## Performance Optimization

- [ ] Enable caching for static files
- [ ] Optimize database queries
- [ ] Use CDN for static assets (optional)
- [ ] Monitor application performance
- [ ] Set up proper logging

## Monitoring

- **Render.com Dashboard**: Monitor logs, performance, and errors
- **Application Logs**: Check for errors and warnings
- **Database**: Monitor connection and query performance
- **Email**: Verify email functionality works

## Support

If you encounter issues:
1. Check Render.com logs
2. Review application logs
3. Test locally with `deploy_test.py`
4. Contact support with specific error messages

## Next Steps

After successful deployment:
1. Set up custom domain (optional)
2. Configure email notifications
3. Set up monitoring and alerts
4. Create backup strategy
5. Plan for scaling

---

**Ready to deploy!** 🚀

Your Advance Credit application is now ready for deployment on Render.com. Follow the steps above and your financial advisory platform will be live on the internet. 