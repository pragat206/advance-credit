"""
SMS Service for CreditCare Community OTP Verification

This module provides SMS functionality for sending OTP codes.
You can integrate with various SMS providers like Twilio, AWS SNS, etc.
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_sms_twilio(phone: str, message: str) -> bool:
    """
    Send SMS using Twilio service
    
    Requirements:
    - pip install twilio
    - Set environment variables:
      - TWILIO_ACCOUNT_SID
      - TWILIO_AUTH_TOKEN
      - TWILIO_PHONE_NUMBER
    """
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, from_number]):
            logger.warning("Twilio credentials not configured")
            return False
        
        client = Client(account_sid, auth_token)
        
        message_obj = client.messages.create(
            body=message,
            from_=from_number,
            to=phone
        )
        
        logger.info(f"SMS sent via Twilio to {phone}: {message_obj.sid}")
        return True
        
    except ImportError:
        logger.warning("Twilio package not installed. Run: pip install twilio")
        return False
    except Exception as e:
        logger.error(f"Twilio SMS error: {e}")
        return False

def send_sms_aws_sns(phone: str, message: str) -> bool:
    """
    Send SMS using AWS SNS service
    
    Requirements:
    - pip install boto3
    - Configure AWS credentials:
      - AWS_ACCESS_KEY_ID
      - AWS_SECRET_ACCESS_KEY
      - AWS_DEFAULT_REGION
    """
    try:
        import boto3
        
        sns = boto3.client('sns')
        
        response = sns.publish(
            PhoneNumber=phone,
            Message=message
        )
        
        logger.info(f"SMS sent via AWS SNS to {phone}: {response['MessageId']}")
        return True
        
    except ImportError:
        logger.warning("boto3 package not installed. Run: pip install boto3")
        return False
    except Exception as e:
        logger.error(f"AWS SNS SMS error: {e}")
        return False

def send_sms_textlocal(phone: str, message: str) -> bool:
    """
    Send SMS using TextLocal service (India-focused)
    
    Requirements:
    - pip install requests
    - Set environment variables:
      - TEXTLOCAL_API_KEY
      - TEXTLOCAL_SENDER_NAME
    """
    try:
        import requests
        
        api_key = os.getenv('TEXTLOCAL_API_KEY')
        sender_name = os.getenv('TEXTLOCAL_SENDER_NAME', 'CREDIT')
        
        if not api_key:
            logger.warning("TextLocal API key not configured")
            return False
        
        url = "https://api.textlocal.in/send/"
        data = {
            'apikey': api_key,
            'numbers': phone,
            'message': message,
            'sender': sender_name
        }
        
        response = requests.post(url, data=data)
        result = response.json()
        
        if result['status'] == 'success':
            logger.info(f"SMS sent via TextLocal to {phone}")
            return True
        else:
            logger.error(f"TextLocal SMS error: {result}")
            return False
            
    except ImportError:
        logger.warning("requests package not installed. Run: pip install requests")
        return False
    except Exception as e:
        logger.error(f"TextLocal SMS error: {e}")
        return False

def send_sms_simulation(phone: str, message: str) -> bool:
    """
    Simulate SMS sending for development/testing
    """
    logger.info(f"📱 [SMS SIMULATION] To: {phone}")
    logger.info(f"📱 [SMS SIMULATION] Message: {message}")
    logger.info("📱 [SMS SIMULATION] In production, this would be sent via SMS service")
    return True

def send_otp_sms(phone: str, otp: str) -> bool:
    """
    Send OTP via SMS using the best available service
    
    Priority:
    1. Twilio (if configured)
    2. AWS SNS (if configured)
    3. TextLocal (if configured)
    4. Simulation (for development)
    """
    message = f"Your CreditCare verification code is: {otp}. Valid for 10 minutes. Do not share this code."
    
    # Try different SMS services in order of preference
    services = [
        ("Twilio", lambda: send_sms_twilio(phone, message)),
        ("AWS SNS", lambda: send_sms_aws_sns(phone, message)),
        ("TextLocal", lambda: send_sms_textlocal(phone, message)),
        ("Simulation", lambda: send_sms_simulation(phone, message))
    ]
    
    for service_name, service_func in services:
        try:
            if service_func():
                logger.info(f"✅ SMS sent successfully via {service_name}")
                return True
        except Exception as e:
            logger.warning(f"❌ {service_name} failed: {e}")
            continue
    
    logger.error("❌ All SMS services failed")
    return False

# Example usage and configuration
if __name__ == "__main__":
    # Test SMS sending
    test_phone = "+919876543210"  # Replace with your test number
    test_otp = "123456"
    
    print("Testing SMS services...")
    send_otp_sms(test_phone, test_otp)
