#!/usr/bin/env python3
"""Test SendGrid configuration and diagnose issues"""

import os
import sys
sys.path.append('backend')

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
print(f"Loading .env from: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")
load_dotenv(env_path)

# Get SendGrid configuration
api_key = os.getenv('SENDGRID_API_KEY')
from_email = os.getenv('FROM_EMAIL', 'noreply@debabelize.me')
from_name = os.getenv('FROM_NAME', 'Debabelizer')

print(f"SendGrid API Key present: {bool(api_key)}")
print(f"API Key length: {len(api_key) if api_key else 0}")
print(f"API Key prefix: {api_key[:10] if api_key else 'None'}...")
print(f"From Email: {from_email}")
print(f"From Name: {from_name}")

if api_key:
    # Test the API key
    try:
        sg = SendGridAPIClient(api_key)
        
        # Create a simple test message
        message = Mail(
            from_email=from_email,
            to_emails='test@example.com',
            subject='Test SendGrid Configuration',
            plain_text_content='This is a test email to verify SendGrid configuration.'
        )
        
        # Try to send
        response = sg.send(message)
        print(f"\nSendGrid test result:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.body}")
        print(f"Response Headers: {dict(response.headers)}")
        
    except Exception as e:
        print(f"\nSendGrid test failed with error:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        if hasattr(e, 'body'):
            print(f"\nDetailed error from SendGrid:")
            print(f"Response body: {e.body}")
        if hasattr(e, 'headers'):
            print(f"Response headers: {e.headers}")
            
        # Try to get API key scopes
        print("\nTrying to check API key permissions...")
        try:
            import requests
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            # Check API key scopes
            scopes_response = requests.get('https://api.sendgrid.com/v3/scopes', headers=headers)
            print(f"API Key Scopes Status: {scopes_response.status_code}")
            if scopes_response.status_code == 200:
                print(f"API Key Scopes: {scopes_response.json()}")
            else:
                print(f"Scopes Error: {scopes_response.text}")
                
        except Exception as scope_error:
            print(f"Could not check scopes: {scope_error}")