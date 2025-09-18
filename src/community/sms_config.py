"""
SMS Configuration for CreditCare Community

This file contains configuration examples for different SMS services.
Copy the relevant section to your environment variables or .env file.
"""

# Example environment variables for different SMS services

# Twilio Configuration
TWILIO_CONFIG = """
# Twilio SMS Service
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
"""

# AWS SNS Configuration
AWS_SNS_CONFIG = """
# AWS SNS SMS Service
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
"""

# TextLocal Configuration (India-focused)
TEXTLOCAL_CONFIG = """
# TextLocal SMS Service (Good for India)
TEXTLOCAL_API_KEY=your_textlocal_api_key
TEXTLOCAL_SENDER_NAME=CREDIT
"""

# Fast2SMS Configuration (India-focused)
FAST2SMS_CONFIG = """
# Fast2SMS Service (India)
FAST2SMS_API_KEY=your_fast2sms_api_key
FAST2SMS_SENDER_ID=CREDIT
"""

# MSG91 Configuration (India-focused)
MSG91_CONFIG = """
# MSG91 SMS Service (India)
MSG91_AUTH_KEY=your_msg91_auth_key
MSG91_SENDER_ID=CREDIT
"""

# Example .env file content
ENV_FILE_EXAMPLE = """
# Email Configuration (already exists in main app)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
USE_TLS=True

# SMS Configuration - Choose one service
# Option 1: Twilio (International)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Option 2: TextLocal (India-focused)
# TEXTLOCAL_API_KEY=your_textlocal_api_key
# TEXTLOCAL_SENDER_NAME=CREDIT

# Option 3: Fast2SMS (India)
# FAST2SMS_API_KEY=your_fast2sms_api_key
# FAST2SMS_SENDER_ID=CREDIT

# Option 4: MSG91 (India)
# MSG91_AUTH_KEY=your_msg91_auth_key
# MSG91_SENDER_ID=CREDIT
"""

# Installation instructions
INSTALLATION_INSTRUCTIONS = """
# Install required packages for SMS services

# For Twilio
pip install twilio

# For AWS SNS
pip install boto3

# For TextLocal, Fast2SMS, MSG91
pip install requests

# All services
pip install twilio boto3 requests
"""

# Service comparison
SERVICE_COMPARISON = """
SMS Service Comparison:

1. Twilio
   - Pros: Reliable, international, good documentation
   - Cons: More expensive, requires credit card
   - Best for: International users, high volume

2. TextLocal
   - Pros: India-focused, cost-effective, easy setup
   - Cons: Limited to India, requires verification
   - Best for: India-only applications

3. Fast2SMS
   - Pros: Very cheap, India-focused, bulk SMS
   - Cons: Limited to India, requires verification
   - Best for: High volume India SMS

4. MSG91
   - Pros: Good for India, reasonable pricing
   - Cons: Limited to India, requires verification
   - Best for: Indian businesses

5. AWS SNS
   - Pros: Reliable, scalable, good for AWS users
   - Cons: Requires AWS account, more complex setup
   - Best for: AWS-based applications
"""

if __name__ == "__main__":
    print("SMS Configuration Examples")
    print("=" * 50)
    print(ENV_FILE_EXAMPLE)
    print("\nInstallation Instructions:")
    print(INSTALLATION_INSTRUCTIONS)
    print("\nService Comparison:")
    print(SERVICE_COMPARISON)
