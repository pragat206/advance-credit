# Email Setup Guide for Advance Credit Website

This guide will help you configure email functionality for the Advance Credit website.

## Overview

The website now supports email notifications for:
- Contact form submissions
- Loan applications
- Debt consolidation consultation requests

## Email Configuration

### 1. Environment Variables

Set the following environment variables in your system or `.env` file:

```bash
# SMTP Server Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
USE_TLS=True

# Email Credentials
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Email Addresses
FROM_EMAIL=noreply@advancecfa.com
TO_EMAIL=vikas@advancecfa.com
```

### 2. Gmail Setup (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App Passwords
   - Generate a new app password for "Mail"
   - Use the 16-character password as `SMTP_PASSWORD`

3. **Use your full Gmail address** as `SMTP_USERNAME`

### 3. Other Email Providers

#### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
USE_TLS=True
```

#### Yahoo
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
USE_TLS=True
```

#### Custom Domain
Use your email provider's SMTP settings.

## Testing Email Functionality

### 1. Run the Test Script

```bash
python test_email.py
```

This script will:
- Check your email configuration
- Attempt to send a test email
- Provide detailed error messages if something fails

### 2. Test Website Forms

1. **Contact Form**: Go to `/services` and submit the contact form
2. **Loan Application**: Go to `/products` and apply for a loan
3. **Debt Consultation**: Go to homepage and submit the debt consolidation form

## Email Templates

### Contact Form Email
```
Subject: New Contact Query from [Name] (Advance Credit Website)

Name: [Name]
Contact: [Contact]
Email: [Email or 'Not provided']
Query: [User's query]

---
This email was sent from the Advance Credit website contact form.
```

### Loan Application Email
```
Subject: New Loan Application from [Name] - [Loan Type]

New Loan Application Received

Applicant Details:
Name: [Name]
Email: [Email or 'Not provided']
Contact: [Contact]
Occupation: [Occupation]

Loan Details:
Loan Type: [Loan Type]
Amount: [Amount]

---
This application was submitted through the Advance Credit website.
Please contact the applicant within 24 hours.
```

### Debt Consultation Email
```
Subject: Debt Consolidation Consultation Request from [Name]

New Debt Consolidation Consultation Request

Client Details:
Name: [Name]
Phone: [Phone]
Email: [Email]

Service Requested: Debt Consolidation Consultation

---
This request was submitted through the Advance Credit website debt consolidation section.
Please call the client within 30 minutes as promised on the website.
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Ensure you're using an App Password (not regular password) for Gmail
   - Check that 2-Factor Authentication is enabled
   - Verify your email address is correct

2. **Connection Refused**
   - Check if the SMTP server and port are correct
   - Ensure your firewall allows outbound connections on the SMTP port

3. **TLS/SSL Errors**
   - Try setting `USE_TLS=False` for some providers
   - Use port 465 with SSL instead of 587 with TLS

4. **Email Not Received**
   - Check spam/junk folder
   - Verify the `TO_EMAIL` address is correct
   - Check if your email provider has sending limits

### Debug Mode

To see detailed email logs, check the console output when running the FastAPI server. Failed email attempts will be logged with error details.

## Security Notes

1. **Never commit email credentials** to version control
2. **Use environment variables** for all sensitive information
3. **Regularly rotate** your app passwords
4. **Monitor email logs** for suspicious activity

## Production Deployment

For production deployment:

1. **Use a dedicated email service** like SendGrid, Mailgun, or AWS SES
2. **Set up proper DNS records** (SPF, DKIM, DMARC)
3. **Monitor email delivery rates**
4. **Implement rate limiting** to prevent spam
5. **Use environment-specific configurations**

## Support

If you encounter issues:

1. Run the test script first: `python test_email.py`
2. Check the console logs for error messages
3. Verify your email provider's SMTP settings
4. Test with a different email provider if needed 