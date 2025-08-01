#!/usr/bin/env python3
"""
Usage Statistics Reader for Debabelize Me

This script reads and displays STT/TTS usage statistics from the database.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Optional

# Add the backend path to sys.path to import database module
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Change to backend directory for correct database path
os.chdir(backend_path)

from app.database.database import Database

async def display_all_users_summary():
    """Display usage summary for all users"""
    print("=" * 80)
    print("USER USAGE SUMMARY")
    print("=" * 80)
    
    users = await Database.get_all_users_usage_summary()
    
    if not users:
        print("No users found in the database.")
        return
    
    # Header
    print(f"{'Email':<30} {'STT Words':<12} {'TTS Words':<12} {'STT Reqs':<10} {'TTS Reqs':<10} {'Days':<6} {'First Use':<12} {'Last Use':<12}")
    print("-" * 80)
    
    total_stt_words = 0
    total_tts_words = 0
    total_stt_requests = 0
    total_tts_requests = 0
    
    for user in users:
        email = user['email'][:28] + '..' if len(user['email']) > 30 else user['email']
        stt_words = user['total_stt_words'] or 0
        tts_words = user['total_tts_words'] or 0
        stt_reqs = user['total_stt_requests'] or 0
        tts_reqs = user['total_tts_requests'] or 0
        active_days = user['active_days'] or 0
        first_use = user['first_usage'][:10] if user['first_usage'] else 'Never'
        last_use = user['last_usage'][:10] if user['last_usage'] else 'Never'
        
        print(f"{email:<30} {stt_words:<12} {tts_words:<12} {stt_reqs:<10} {tts_reqs:<10} {active_days:<6} {first_use:<12} {last_use:<12}")
        
        total_stt_words += stt_words
        total_tts_words += tts_words
        total_stt_requests += stt_reqs
        total_tts_requests += tts_reqs
    
    print("-" * 80)
    print(f"{'TOTALS':<30} {total_stt_words:<12} {total_tts_words:<12} {total_stt_requests:<10} {total_tts_requests:<10}")
    print()

async def display_user_details(email: str, days: int = 30):
    """Display detailed usage for a specific user"""
    # First get the user by email
    users = await Database.get_all_users_usage_summary()
    user = next((u for u in users if u['email'].lower() == email.lower()), None)
    
    if not user:
        print(f"User '{email}' not found.")
        return
    
    print("=" * 80)
    print(f"DETAILED USAGE FOR USER: {user['email']}")
    print("=" * 80)
    print(f"User ID: {user['user_id']}")
    print(f"Account Created: {user['user_created']}")
    print(f"Total STT Words: {user['total_stt_words'] or 0}")
    print(f"Total TTS Words: {user['total_tts_words'] or 0}")
    print(f"Total STT Requests: {user['total_stt_requests'] or 0}")
    print(f"Total TTS Requests: {user['total_tts_requests'] or 0}")
    print(f"Active Days: {user['active_days'] or 0}")
    print()
    
    # Get daily breakdown
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    daily_stats = await Database.get_usage_stats(
        user_id=user['user_id'],
        start_date=start_date
    )
    
    if daily_stats:
        print(f"DAILY BREAKDOWN (Last {days} days):")
        print("-" * 80)
        print(f"{'Date':<12} {'STT Words':<12} {'TTS Words':<12} {'STT Reqs':<10} {'TTS Reqs':<10}")
        print("-" * 80)
        
        for day in daily_stats:
            print(f"{day['date']:<12} {day['stt_words']:<12} {day['tts_words']:<12} {day['stt_requests']:<10} {day['tts_requests']:<10}")
    else:
        print(f"No usage data found for the last {days} days.")
    
    print()

async def display_recent_activity(days: int = 7):
    """Display recent activity across all users"""
    print("=" * 80)
    print(f"RECENT ACTIVITY (Last {days} days)")
    print("=" * 80)
    
    # Get all users and their recent stats
    users = await Database.get_all_users_usage_summary()
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    recent_activity = []
    
    for user in users:
        daily_stats = await Database.get_usage_stats(
            user_id=user['user_id'],
            start_date=start_date
        )
        
        if daily_stats:
            total_stt = sum(day['stt_words'] for day in daily_stats)
            total_tts = sum(day['tts_words'] for day in daily_stats)
            
            if total_stt > 0 or total_tts > 0:
                recent_activity.append({
                    'email': user['email'],
                    'stt_words': total_stt,
                    'tts_words': total_tts,
                    'total_words': total_stt + total_tts
                })
    
    if not recent_activity:
        print(f"No activity found in the last {days} days.")
        return
    
    # Sort by total activity
    recent_activity.sort(key=lambda x: x['total_words'], reverse=True)
    
    print(f"{'Email':<30} {'STT Words':<12} {'TTS Words':<12} {'Total Words':<12}")
    print("-" * 80)
    
    for activity in recent_activity:
        email = activity['email'][:28] + '..' if len(activity['email']) > 30 else activity['email']
        print(f"{email:<30} {activity['stt_words']:<12} {activity['tts_words']:<12} {activity['total_words']:<12}")
    
    print()

async def main():
    """Main function to handle command line arguments and display stats"""
    
    # Initialize database
    await Database.initialize()
    
    if len(sys.argv) == 1:
        # No arguments - show summary and recent activity
        await display_all_users_summary()
        await display_recent_activity()
    
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        
        if arg in ['-h', '--help']:
            print("Usage Statistics Reader for Debabelize Me")
            print()
            print("Usage:")
            print("  python read_usage_stats.py                    # Show all users summary + recent activity")
            print("  python read_usage_stats.py user@example.com   # Show detailed stats for specific user")
            print("  python read_usage_stats.py --recent [days]    # Show recent activity (default: 7 days)")
            print("  python read_usage_stats.py --summary          # Show only users summary")
            print("  python read_usage_stats.py --help             # Show this help")
            return
        
        elif arg == '--summary':
            await display_all_users_summary()
        
        elif arg == '--recent':
            await display_recent_activity()
        
        elif '@' in arg:
            # Email address - show detailed user stats
            await display_user_details(arg)
        
        else:
            print(f"Unknown argument: {arg}")
            print("Use --help for usage information.")
    
    elif len(sys.argv) == 3:
        command = sys.argv[1]
        
        if command == '--recent':
            try:
                days = int(sys.argv[2])
                await display_recent_activity(days)
            except ValueError:
                print("Error: Days must be a number")
        
        elif '@' in command:
            # Email with days
            try:
                days = int(sys.argv[2])
                await display_user_details(command, days)
            except ValueError:
                print("Error: Days must be a number")
        
        else:
            print("Invalid arguments. Use --help for usage information.")
    
    else:
        print("Too many arguments. Use --help for usage information.")

if __name__ == "__main__":
    asyncio.run(main())