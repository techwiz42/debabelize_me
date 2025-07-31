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