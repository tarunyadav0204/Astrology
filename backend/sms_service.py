import os
from twilio.rest import Client

class SMSService:
    def __init__(self):
        # Twilio credentials from environment variables
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            print("Warning: Twilio credentials not found. SMS will be disabled.")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)
    
    def send_reset_code(self, phone_number: str, code: str) -> bool:
        """Send password reset code via SMS"""
        if not self.client:
            print(f"SMS disabled - would send code {code} to {phone_number}")
            return False
        
        try:
            # Format phone number for international format
            if not phone_number.startswith('+'):
                # Assume Indian number if no country code
                phone_number = f'+91{phone_number}'
            
            message = self.client.messages.create(
                body=f"Your AstroGPT password reset code is: {code}. Valid for 10 minutes.",
                from_=self.from_number,
                to=phone_number
            )
            
            print(f"SMS sent successfully. SID: {message.sid}")
            return True
            
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")
            return False

# Global SMS service instance
sms_service = SMSService()