#!/usr/bin/env python3
"""Check verified senders in SendGrid"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
load_dotenv(env_path)

api_key = os.getenv('SENDGRID_API_KEY')

if api_key:
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print("Checking SendGrid verified senders...\n")
    
    # Check verified senders
    senders_response = requests.get('https://api.sendgrid.com/v3/verified_senders', headers=headers)
    if senders_response.status_code == 200:
        senders = senders_response.json()
        print("Verified Senders:")
        if senders.get('results'):
            for sender in senders['results']:
                print(f"  - {sender.get('from_email')} ({sender.get('from_name', 'No name')})")
                print(f"    Status: {sender.get('verified', {}).get('status', 'Unknown')}")
        else:
            print("  No verified senders found")
    else:
        print(f"Error checking senders: {senders_response.status_code}")
        print(senders_response.text)
    
    # Check domain authentication
    print("\nChecking authenticated domains...")
    domains_response = requests.get('https://api.sendgrid.com/v3/whitelabel/domains', headers=headers)
    if domains_response.status_code == 200:
        domains = domains_response.json()
        if domains:
            for domain in domains:
                print(f"  - {domain.get('domain')} (Valid: {domain.get('valid')})")
        else:
            print("  No authenticated domains found")
    else:
        print(f"Error checking domains: {domains_response.status_code}")