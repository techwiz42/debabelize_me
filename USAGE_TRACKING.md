# Usage Tracking for Debabelize Me

This implementation tracks STT (Speech-to-Text) and TTS (Text-to-Speech) usage per user, counting words processed and requests made.

## Database Schema

The system adds a `user_usage_stats` table with the following columns:
- `user_id` - Links to the users table
- `date` - Date of usage (YYYY-MM-DD)
- `stt_words` - Number of words transcribed via STT
- `tts_words` - Number of words synthesized via TTS
- `stt_requests` - Number of STT requests made
- `tts_requests` - Number of TTS requests made
- `created_at` / `updated_at` - Timestamps

## How It Works

### STT Word Counting
- Tracks words in **final** transcription results only (avoids double-counting interim results)
- Works with all STT providers: Deepgram, Soniox, OpenAI Whisper
- WebSocket STT requires session token in query parameters for user authentication
- Example: `wss://debabelize.me/api/ws/stt?session_token=abc123`

### TTS Word Counting  
- Tracks words in text sent to TTS synthesis
- Counts words before sending to TTS provider
- Requires user authentication via session cookie

### Authentication
- **REST endpoints**: Use session cookies for authentication (standard FastAPI Depends)
- **WebSocket endpoints**: Pass session token as query parameter
- Only authenticated users have their usage tracked
- Anonymous usage is not tracked

## Scripts for Reading Statistics

Two scripts are provided for reading usage data:

### 1. `read_usage_stats.py` (Full-featured)
Uses the backend database module with async support.

```bash
# Show all users summary + recent activity
python read_usage_stats.py

# Show detailed stats for specific user
python read_usage_stats.py user@example.com

# Show recent activity (default: 7 days)
python read_usage_stats.py --recent

# Show recent activity for specific number of days
python read_usage_stats.py --recent 14

# Show only users summary
python read_usage_stats.py --summary

# Show help
python read_usage_stats.py --help
```

### 2. `browse_usage_db.py` (Simple SQLite browser)
Direct SQLite queries, no backend dependencies.

```bash
# Show DB info, summary, and recent activity
python browse_usage_db.py

# Show detailed stats for specific user
python browse_usage_db.py user@example.com

# Show recent activity
python browse_usage_db.py --recent

# Show recent activity for specific days
python browse_usage_db.py --recent 30

# Show only users summary
python browse_usage_db.py --summary

# Show only database info
python browse_usage_db.py --info

# Show help
python browse_usage_db.py --help
```

## Example Output

```
================================================================================
USER USAGE SUMMARY
================================================================================
Email                          STT Words    TTS Words    STT Reqs   TTS Reqs   Days   First Use    Last Use    
--------------------------------------------------------------------------------
user@example.com               1,250        890          45         23         12     2025-07-20   2025-08-01
admin@company.com              500          1,200        15         35         8      2025-07-25   2025-08-01
--------------------------------------------------------------------------------
TOTALS                         1,750        2,090        60         58
```

## Implementation Details

### Word Counting Algorithm
- Uses regex pattern `\b\w+\b` to count words
- Handles multiple whitespace, punctuation, and special characters
- Returns 0 for empty or null text

### Database Updates
- Uses SQLite `ON CONFLICT` clause for atomic upserts
- Daily aggregation by user (one record per user per day)
- Automatic timestamp management

### Error Handling
- Graceful handling of unauthenticated users (no tracking)
- Database errors are logged but don't break functionality
- Scripts handle missing data gracefully

## Privacy & Security
- Only tracks usage statistics, not content
- Requires user authentication
- No personal data beyond email is tracked
- Anonymous usage is not tracked

## Performance
- Minimal overhead on STT/TTS operations
- Database indexed on `(user_id, date)` for fast queries
- Atomic upsert operations prevent race conditions
- Daily aggregation keeps database size manageable