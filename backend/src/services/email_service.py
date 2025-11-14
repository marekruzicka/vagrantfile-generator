"""
Email Service.

Handles email delivery via Mailgun API for OTP authentication.
"""

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Mailgun."""
    
    def __init__(self):
        """Initialize email service with Mailgun credentials."""
        self.api_key = os.getenv("MAILGUN_API_KEY")
        self.domain = os.getenv("MAILGUN_DOMAIN")
        self.from_email = os.getenv("MAILGUN_FROM_EMAIL", f"noreply@{self.domain}")
        self.base_url = f"https://api.mailgun.net/v3/{self.domain}/messages"
    
    def is_configured(self) -> bool:
        """
        Check if Mailgun is properly configured.
        
        Returns:
            bool: True if API key and domain are set, False otherwise
        """
        return bool(self.api_key and self.domain)
    
    def send_otp_email(self, to_email: str, otp_code: str) -> bool:
        """
        Send OTP code via email using Mailgun.
        
        Args:
            to_email: Recipient email address
            otp_code: 6-digit OTP code to send
            
        Returns:
            bool: True if email sent successfully, False otherwise
            
        Raises:
            ValueError: If Mailgun is not configured
            RuntimeError: If email delivery fails
        """
        if not self.is_configured():
            raise ValueError(
                "Mailgun is not configured. "
                "Please set MAILGUN_API_KEY and MAILGUN_DOMAIN environment variables."
            )
        
        subject = "Your Vagrantfile Generator Login Code"
        text_body = f"""
Hello,

Your login code is: {otp_code}

This code will expire in 15 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Vagrantfile Generator Team
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Login Code</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #333;">Your Login Code</h2>
    <p>Hello,</p>
    <p>Your login code is:</p>
    <div style="background-color: #f5f5f5; padding: 15px; text-align: center; margin: 20px 0;">
        <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #2563eb;">{otp_code}</span>
    </div>
    <p>This code will expire in <strong>15 minutes</strong>.</p>
    <p style="color: #666; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
    <p style="color: #999; font-size: 12px;">Vagrantfile Generator Team</p>
</body>
</html>
        """.strip()
        
        try:
            response = requests.post(
                self.base_url,
                auth=("api", self.api_key),
                data={
                    "from": self.from_email,
                    "to": to_email,
                    "subject": subject,
                    "text": text_body,
                    "html": html_body
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"OTP email sent successfully to {to_email}")
                return True
            else:
                error_msg = f"Mailgun API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)


# Global email service instance
email_service = EmailService()
