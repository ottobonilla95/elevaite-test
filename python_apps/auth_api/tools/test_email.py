#!/usr/bin/env python3
"""
Simple script to test SMTP email configuration.

This script sends a test email using the email service from the auth API.
It's a lightweight alternative to using the admin_create_user.py script
for testing email functionality.

Usage:
    python test_email.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add the parent directory to sys.path to allow importing from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.email_service import send_email
from app.core.config import settings


async def send_test_email(recipient_email: str) -> bool:
    """
    Send a test email to verify SMTP configuration.
    
    Args:
        recipient_email: Email address to send the test to
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = "elevAIte SMTP Test"
    
    text_body = f"""
    Hello,
    
    This is a test email from the elevAIte system to verify that the SMTP configuration is working correctly.
    
    SMTP Settings:
    - Host: {settings.SMTP_HOST}
    - Port: {settings.SMTP_PORT}
    - TLS: {settings.SMTP_TLS}
    - From Email: {settings.EMAILS_FROM_EMAIL}
    - From Name: {settings.EMAILS_FROM_NAME}
    
    If you received this email, it means the SMTP configuration is working correctly.
    
    Time sent: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
    
    Best regards,
    The elevAIte Team
    """
    
    html_body = f"""
    <html>
    <body>
        <h2>elevAIte SMTP Test</h2>
        <p>Hello,</p>
        <p>This is a test email from the elevAIte system to verify that the SMTP configuration is working correctly.</p>
        
        <h3>SMTP Settings:</h3>
        <ul>
            <li><strong>Host:</strong> {settings.SMTP_HOST}</li>
            <li><strong>Port:</strong> {settings.SMTP_PORT}</li>
            <li><strong>TLS:</strong> {settings.SMTP_TLS}</li>
            <li><strong>From Email:</strong> {settings.EMAILS_FROM_EMAIL}</li>
            <li><strong>From Name:</strong> {settings.EMAILS_FROM_NAME}</li>
        </ul>
        
        <p>If you received this email, it means the SMTP configuration is working correctly.</p>
        <p>Time sent: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        
        <p>Best regards,<br>The elevAIte Team</p>
    </body>
    </html>
    """
    
    print(f"Sending test email to {recipient_email}...")
    print(f"Using SMTP settings:")
    print(f"  Host: {settings.SMTP_HOST}")
    print(f"  Port: {settings.SMTP_PORT}")
    print(f"  TLS: {settings.SMTP_TLS}")
    print(f"  User: {settings.SMTP_USER}")
    print(f"  From Email: {settings.EMAILS_FROM_EMAIL}")
    print(f"  From Name: {settings.EMAILS_FROM_NAME}")
    
    try:
        result = await send_email(
            recipient=recipient_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body
        )
        
        if result:
            print(f"Test email sent successfully to {recipient_email}")
        else:
            print(f"Failed to send test email to {recipient_email}")
        
        return result
    except Exception as e:
        print(f"Error sending test email: {str(e)}")
        return False


async def main():
    """Send a test email."""
    # Get recipient email
    recipient_email = input("Recipient email address: ")
    
    # Send the test email
    await send_test_email(recipient_email)


if __name__ == "__main__":
    asyncio.run(main())
