# Advance Credit - Financial Advisory Platform

A comprehensive financial advisory and debt consolidation platform built with FastAPI, Jinja2, and SQLite.

## Features

- **Debt Consolidation Services**: Help families combine multiple loans into manageable payments
- **Credit Building**: Expert guidance to improve credit scores
- **Financial Planning**: Comprehensive financial advisory services
- **Loan Products**: Integration with 50+ banks and NBFCs
- **EMI Calculator**: Interactive loan EMI calculator
- **Lead Management**: CRM system for managing leads and inquiries
- **Admin Portal**: Complete admin dashboard for managing content

## Tech Stack

- **Backend**: FastAPI, Python 3.12
- **Database**: SQLite (local), PostgreSQL (production)
- **Frontend**: Jinja2 Templates, Bootstrap 5, JavaScript
- **Email**: SMTP integration
- **Deployment**: Render.com ready

## Local Development

### Prerequisites

- Python 3.12+
- Poetry (recommended) or pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd news_slider
   ```

2. **Install dependencies**
   ```bash
   # Using Poetry (recommended)
   poetry install
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env_example.txt .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   # Using Poetry
   poetry run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or using uvicorn directly
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the application**
   - Main site: http://localhost:8000
   - Admin portal: http://localhost:8000/admin
   - Default admin credentials: admin / admin123

## Deployment on Render.com

### Prerequisites

1. **Render.com account**
2. **GitHub repository** with your code
3. **PostgreSQL database** (optional, SQLite works too)

### Deployment Steps

1. **Connect your repository to Render.com**
   - Go to Render.com dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure the web service**
   - **Name**: `advance-credit-web`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app.main:app --bind 0.0.0.0:$PORT --worker-class uvicorn.workers.UvicornWorker`

3. **Set environment variables**
   ```
   SECRET_KEY=your-super-secret-key-here
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

4. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Secret key for session management | Yes |
| `DATABASE_URL` | Database connection string | No (uses SQLite by default) |
| `SMTP_SERVER` | SMTP server for emails | No |
| `SMTP_PORT` | SMTP port | No |
| `SMTP_USERNAME` | SMTP username | No |
| `SMTP_PASSWORD` | SMTP password | No |
| `FROM_EMAIL` | From email address | No |
| `TO_EMAIL` | Default recipient email | No |
| `USE_TLS` | Use TLS for email | No |
| `ADMIN_PASSWORD` | Admin portal password | No |

## Project Structure

```
news_slider/
├── app/
│   ├── main.py              # FastAPI application
│   ├── db.py                # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── admin/               # Admin portal routes
│   ├── scrapers/            # Bank loan scrapers
│   ├── static/              # Static files (CSS, JS, images)
│   └── templates/           # Jinja2 templates
├── crm_portal/              # CRM system
├── requirements.txt          # Python dependencies
├── Procfile                 # Render.com deployment
├── build.sh                 # Build script
├── runtime.txt              # Python version
└── README.md               # This file
```

## Features Overview

### Main Website
- **Homepage**: Hero banner, services overview, debt calculator
- **Products**: Loan products from partner banks
- **Services**: Detailed service offerings
- **Partners**: Bank partnerships and logos
- **About**: Company information and team
- **EMI Calculator**: Interactive loan calculator

### Admin Portal
- **Dashboard**: Overview of leads and inquiries
- **Leads Management**: View and manage leads
- **Content Management**: FAQs, partners, products
- **Analytics**: Basic analytics and reports

### CRM System
- **Lead Tracking**: Capture and track leads
- **Employee Management**: Manage team members
- **Query Management**: Handle customer queries
- **Reminders**: Automated reminder system

## Database

The application uses two databases:
- **site.db**: Main application database
- **crm.db**: CRM system database

For production, you can use PostgreSQL by setting the `DATABASE_URL` environment variable.

## Email Configuration

The application supports email notifications for:
- Lead submissions
- Contact form submissions
- Admin notifications

Configure SMTP settings in environment variables for production use.

## Security

- Session management with secure secret keys
- Admin authentication
- Form validation
- SQL injection protection via SQLAlchemy

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is proprietary software for Advance Credit Pvt Ltd.

## Support

For support, contact:
- Email: vikas@advancecfa.com
- Website: https://advancecfa.com 