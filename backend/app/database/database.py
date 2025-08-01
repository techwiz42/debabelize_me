import sqlite3
import aiosqlite
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path("debabelizer_users.db")

class Database:
    """SQLite database manager for user authentication"""
    
    @classmethod
    async def initialize(cls):
        """Initialize the SQLite database with required tables"""
        async with aiosqlite.connect(DB_PATH) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE
                )
            """)
            
            # Email confirmation tokens table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS confirmation_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            
            # Password reset tokens table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            
            # User sessions table (for tracking login sessions)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_agent TEXT,
                    ip_address TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            
            # User usage statistics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    stt_words INTEGER NOT NULL DEFAULT 0,
                    tts_words INTEGER NOT NULL DEFAULT 0,
                    stt_requests INTEGER NOT NULL DEFAULT 0,
                    tts_requests INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, date),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            
            # Create index for faster lookups
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_stats_user_date 
                ON user_usage_stats (user_id, date)
            """)
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    @classmethod
    async def create_user(cls, email: str, password_hash: str) -> Optional[int]:
        """Create a new user (unconfirmed)"""
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute(
                    "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                    (email.lower(), password_hash)
                )
                user_id = cursor.lastrowid
                await db.commit()
                logger.info(f"Created user with ID {user_id} for email {email}")
                return user_id
        except sqlite3.IntegrityError:
            logger.warning(f"Attempted to create duplicate user: {email}")
            return None
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            return None
    
    @classmethod
    async def get_user_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE email = ? AND is_active = TRUE",
                (email.lower(),)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    @classmethod
    async def get_user_by_id(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE id = ? AND is_active = TRUE",
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    @classmethod
    async def confirm_user_email(cls, user_id: int) -> bool:
        """Confirm user email address"""
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE users SET is_confirmed = TRUE WHERE id = ?",
                    (user_id,)
                )
                await db.commit()
                logger.info(f"Confirmed email for user ID {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error confirming user {user_id}: {e}")
            return False
    
    @classmethod
    async def update_last_login(cls, user_id: int) -> bool:
        """Update user's last login timestamp"""
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user_id,)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {e}")
            return False
    
    @classmethod
    async def create_confirmation_token(cls, user_id: int, token: str, expires_at: datetime) -> bool:
        """Create email confirmation token"""
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT INTO confirmation_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
                    (user_id, token, expires_at)
                )
                await db.commit()
                logger.info(f"Created confirmation token for user ID {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error creating confirmation token for user {user_id}: {e}")
            return False
    
    @classmethod
    async def get_confirmation_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """Get confirmation token details"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT ct.*, u.email, u.is_confirmed 
                FROM confirmation_tokens ct
                JOIN users u ON ct.user_id = u.id
                WHERE ct.token = ? AND ct.used = FALSE AND ct.expires_at > CURRENT_TIMESTAMP
            """, (token,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    @classmethod
    async def use_confirmation_token(cls, token: str, user_id: int) -> bool:
        """Mark confirmation token as used and confirm user"""
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                # Mark token as used
                await db.execute(
                    "UPDATE confirmation_tokens SET used = TRUE WHERE token = ? AND user_id = ?",
                    (token, user_id)
                )
                # Confirm user
                await db.execute(
                    "UPDATE users SET is_confirmed = TRUE WHERE id = ?",
                    (user_id,)
                )
                await db.commit()
                logger.info(f"Used confirmation token and confirmed user ID {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error using confirmation token for user {user_id}: {e}")
            return False
    
    @classmethod
    async def create_user_session(cls, user_id: int, session_token: str, expires_at: datetime, 
                                  user_agent: str = None, ip_address: str = None) -> bool:
        """Create user session"""
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("""
                    INSERT INTO user_sessions (user_id, session_token, expires_at, user_agent, ip_address)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, session_token, expires_at, user_agent, ip_address))
                await db.commit()
                logger.info(f"Created session for user ID {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error creating session for user {user_id}: {e}")
            return False
    
    @classmethod
    async def get_user_session(cls, session_token: str) -> Optional[Dict[str, Any]]:
        """Get user session by token"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT s.*, u.email, u.is_confirmed, u.is_active 
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP
            """, (session_token,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    @classmethod
    async def update_session_access(cls, session_token: str) -> bool:
        """Update session last accessed time"""
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE user_sessions SET last_accessed = CURRENT_TIMESTAMP WHERE session_token = ?",
                    (session_token,)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating session access: {e}")
            return False
    
    @classmethod
    async def delete_user_session(cls, session_token: str) -> bool:
        """Delete user session (logout)"""
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "DELETE FROM user_sessions WHERE session_token = ?",
                    (session_token,)
                )
                await db.commit()
                logger.info(f"Deleted session")
                return True
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    @classmethod
    async def cleanup_expired_tokens(cls) -> int:
        """Clean up expired tokens and sessions"""
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                # Clean up expired confirmation tokens
                cursor = await db.execute(
                    "DELETE FROM confirmation_tokens WHERE expires_at < CURRENT_TIMESTAMP"
                )
                confirmation_deleted = cursor.rowcount
                
                # Clean up expired password reset tokens
                cursor = await db.execute(
                    "DELETE FROM password_reset_tokens WHERE expires_at < CURRENT_TIMESTAMP"
                )
                reset_deleted = cursor.rowcount
                
                # Clean up expired sessions
                cursor = await db.execute(
                    "DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP"
                )
                session_deleted = cursor.rowcount
                
                await db.commit()
                total_deleted = confirmation_deleted + reset_deleted + session_deleted
                if total_deleted > 0:
                    logger.info(f"Cleaned up {total_deleted} expired tokens/sessions")
                return total_deleted
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            return 0
    
    @classmethod
    async def increment_usage_stats(cls, user_id: int, stt_words: int = 0, tts_words: int = 0) -> bool:
        """Increment usage statistics for a user for today"""
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                # Use date() function to get today's date in SQLite
                await db.execute("""
                    INSERT INTO user_usage_stats (user_id, date, stt_words, tts_words, stt_requests, tts_requests)
                    VALUES (?, date('now'), ?, ?, ?, ?)
                    ON CONFLICT(user_id, date) DO UPDATE SET
                        stt_words = stt_words + ?,
                        tts_words = tts_words + ?,
                        stt_requests = stt_requests + ?,
                        tts_requests = tts_requests + ?,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    user_id, 
                    stt_words, tts_words, 
                    1 if stt_words > 0 else 0, 
                    1 if tts_words > 0 else 0,
                    stt_words, tts_words,
                    1 if stt_words > 0 else 0, 
                    1 if tts_words > 0 else 0
                ))
                await db.commit()
                logger.info(f"Updated usage stats for user {user_id}: +{stt_words} STT words, +{tts_words} TTS words")
                return True
        except Exception as e:
            logger.error(f"Error updating usage stats for user {user_id}: {e}")
            return False
    
    @classmethod
    async def get_usage_stats(cls, user_id: int, start_date: str = None, end_date: str = None) -> list:
        """Get usage statistics for a user within date range"""
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                
                query = "SELECT * FROM user_usage_stats WHERE user_id = ?"
                params = [user_id]
                
                if start_date:
                    query += " AND date >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND date <= ?"
                    params.append(end_date)
                    
                query += " ORDER BY date DESC"
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting usage stats for user {user_id}: {e}")
            return []
    
    @classmethod
    async def get_all_users_usage_summary(cls) -> list:
        """Get usage summary for all users"""
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
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
                    WHERE u.is_active = TRUE
                    GROUP BY u.id, u.email
                    ORDER BY u.created_at DESC
                """)
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return []