#!/usr/bin/env python3
"""
Simple SQLite browser for usage statistics

This script directly queries the SQLite database to show usage statistics
without needing the full backend setup.
"""

import sqlite3
import sys
from datetime import datetime, timedelta

import os
DB_PATH = os.path.join(os.path.dirname(__file__), 'backend', 'debabelizer_users.db')

def connect_db():
    """Connect to the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def show_users_summary():
    """Show summary of all users"""
    conn = connect_db()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        u.id as user_id,
        u.email,
        u.created_at as user_created,
        COALESCE(SUM(us.stt_words), 0) as total_stt_words,
        COALESCE(SUM(us.tts_words), 0) as total_tts_words,
        COALESCE(SUM(us.stt_requests), 0) as total_stt_requests,
        COALESCE(SUM(us.tts_requests), 0) as total_tts_requests,
        COUNT(DISTINCT us.date) as active_days,
        MIN(us.date) as first_usage,
        MAX(us.date) as last_usage
    FROM users u
    LEFT JOIN user_usage_stats us ON u.id = us.user_id
    WHERE u.is_active = 1
    GROUP BY u.id, u.email
    ORDER BY u.created_at DESC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print("=" * 100)
    print("USER USAGE SUMMARY")
    print("=" * 100)
    
    if not rows:
        print("No users found.")
        conn.close()
        return
    
    print(f"{'Email':<35} {'STT Words':<10} {'TTS Words':<10} {'STT Reqs':<8} {'TTS Reqs':<8} {'Days':<5} {'First Use':<12} {'Last Use':<12}")
    print("-" * 100)
    
    total_stt_words = 0
    total_tts_words = 0
    total_stt_requests = 0
    total_tts_requests = 0
    
    for row in rows:
        email = row['email'][:33] + '..' if len(row['email']) > 35 else row['email']
        stt_words = row['total_stt_words'] or 0
        tts_words = row['total_tts_words'] or 0
        stt_reqs = row['total_stt_requests'] or 0
        tts_reqs = row['total_tts_requests'] or 0
        active_days = row['active_days'] or 0
        first_use = row['first_usage'][:10] if row['first_usage'] else 'Never'
        last_use = row['last_usage'][:10] if row['last_usage'] else 'Never'
        
        print(f"{email:<35} {stt_words:<10} {tts_words:<10} {stt_reqs:<8} {tts_reqs:<8} {active_days:<5} {first_use:<12} {last_use:<12}")
        
        total_stt_words += stt_words
        total_tts_words += tts_words
        total_stt_requests += stt_reqs
        total_tts_requests += tts_reqs
    
    print("-" * 100)
    print(f"{'TOTALS':<35} {total_stt_words:<10} {total_tts_words:<10} {total_stt_requests:<8} {total_tts_requests:<8}")
    print()
    
    conn.close()

def show_user_details(email):
    """Show detailed stats for a specific user"""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Get user info
    cursor.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email.lower(),))
    user = cursor.fetchone()
    
    if not user:
        print(f"User '{email}' not found.")
        conn.close()
        return
    
    print("=" * 80)
    print(f"DETAILED USAGE FOR USER: {user['email']}")
    print("=" * 80)
    print(f"User ID: {user['id']}")
    print(f"Account Created: {user['created_at']}")
    print(f"Email Confirmed: {'Yes' if user['is_confirmed'] else 'No'}")
    print(f"Last Login: {user['last_login'] or 'Never'}")
    print()
    
    # Get usage stats
    cursor.execute("""
        SELECT * FROM user_usage_stats 
        WHERE user_id = ? 
        ORDER BY date DESC 
        LIMIT 30
    """, (user['id'],))
    
    stats = cursor.fetchall()
    
    if stats:
        print("DAILY USAGE (Last 30 entries):")
        print("-" * 80)
        print(f"{'Date':<12} {'STT Words':<10} {'TTS Words':<10} {'STT Reqs':<8} {'TTS Reqs':<8} {'Updated':<20}")
        print("-" * 80)
        
        total_stt = 0
        total_tts = 0
        
        for stat in stats:
            total_stt += stat['stt_words']
            total_tts += stat['tts_words']
            updated = stat['updated_at'][:19] if stat['updated_at'] else ''
            
            print(f"{stat['date']:<12} {stat['stt_words']:<10} {stat['tts_words']:<10} {stat['stt_requests']:<8} {stat['tts_requests']:<8} {updated:<20}")
        
        print("-" * 80)
        print(f"{'TOTALS':<12} {total_stt:<10} {total_tts:<10}")
    else:
        print("No usage data found for this user.")
    
    print()
    conn.close()

def show_recent_activity(days=7):
    """Show recent activity"""
    conn = connect_db()
    cursor = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    query = """
    SELECT 
        u.email,
        SUM(us.stt_words) as stt_words,
        SUM(us.tts_words) as tts_words,
        SUM(us.stt_requests) as stt_requests,
        SUM(us.tts_requests) as tts_requests,
        MAX(us.date) as last_activity
    FROM users u
    JOIN user_usage_stats us ON u.id = us.user_id
    WHERE us.date >= ? AND u.is_active = 1
    GROUP BY u.id, u.email
    HAVING (stt_words > 0 OR tts_words > 0)
    ORDER BY (stt_words + tts_words) DESC
    """
    
    cursor.execute(query, (start_date,))
    rows = cursor.fetchall()
    
    print("=" * 80)
    print(f"RECENT ACTIVITY (Last {days} days)")
    print("=" * 80)
    
    if not rows:
        print(f"No activity found in the last {days} days.")
        conn.close()
        return
    
    print(f"{'Email':<35} {'STT Words':<10} {'TTS Words':<10} {'Total':<10} {'Last Activity':<12}")
    print("-" * 80)
    
    for row in rows:
        email = row['email'][:33] + '..' if len(row['email']) > 35 else row['email']
        stt_words = row['stt_words'] or 0
        tts_words = row['tts_words'] or 0
        total_words = stt_words + tts_words
        last_activity = row['last_activity']
        
        print(f"{email:<35} {stt_words:<10} {tts_words:<10} {total_words:<10} {last_activity:<12}")
    
    print()
    conn.close()

def show_db_info():
    """Show database structure and info"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("DATABASE INFORMATION")
    print("=" * 60)
    
    # Count users
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
    user_count = cursor.fetchone()['count']
    
    # Count usage records
    cursor.execute("SELECT COUNT(*) as count FROM user_usage_stats")
    usage_count = cursor.fetchone()['count']
    
    # Date range of usage data
    cursor.execute("SELECT MIN(date) as first_date, MAX(date) as last_date FROM user_usage_stats")
    date_range = cursor.fetchone()
    
    print(f"Active Users: {user_count}")
    print(f"Usage Records: {usage_count}")
    print(f"Data Range: {date_range['first_date'] or 'No data'} to {date_range['last_date'] or 'No data'}")
    print()
    
    conn.close()

def main():
    """Main function"""
    if len(sys.argv) == 1:
        show_db_info()
        show_users_summary()
        show_recent_activity()
    
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        
        if arg in ['-h', '--help']:
            print("Simple SQLite Usage Statistics Browser")
            print()
            print("Usage:")
            print("  python browse_usage_db.py                    # Show DB info, summary, and recent activity")
            print("  python browse_usage_db.py user@example.com   # Show detailed stats for specific user")
            print("  python browse_usage_db.py --recent [days]    # Show recent activity (default: 7 days)")
            print("  python browse_usage_db.py --summary          # Show only users summary")
            print("  python browse_usage_db.py --info             # Show only database info")
            print("  python browse_usage_db.py --help             # Show this help")
        
        elif arg == '--summary':
            show_users_summary()
        
        elif arg == '--recent':
            show_recent_activity()
        
        elif arg == '--info':
            show_db_info()
        
        elif '@' in arg:
            show_user_details(arg)
        
        else:
            print(f"Unknown argument: {arg}")
            print("Use --help for usage information.")
    
    elif len(sys.argv) == 3:
        if sys.argv[1] == '--recent':
            try:
                days = int(sys.argv[2])
                show_recent_activity(days)
            except ValueError:
                print("Error: Days must be a number")
        else:
            print("Invalid arguments. Use --help for usage information.")
    
    else:
        print("Too many arguments. Use --help for usage information.")

if __name__ == "__main__":
    main()