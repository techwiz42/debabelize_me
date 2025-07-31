import bcrypt
import secrets
import sendgrid
from sendgrid.helpers.mail import Mail, From, To, Subject, HtmlContent, PlainTextContent
from sendgrid import SendGridAPIClient
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging
import os
from app.database.database import Database
from app.models.auth import UserResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service for user management"""
    
    def __init__(self):
        # SendGrid configuration from settings
        self.sendgrid_api_key = settings.sendgrid_api_key or ""
        self.from_email = settings.from_email
        self.from_name = settings.from_name
        self.app_url = settings.app_url
        
        # Initialize SendGrid client
        if self.sendgrid_api_key:
            self.sendgrid_client = SendGridAPIClient(api_key=self.sendgrid_api_key)
            logger.info(f"SendGrid initialized with API key: {self.sendgrid_api_key[:10]}...")
        else:
            self.sendgrid_client = None
            logger.warning("SENDGRID_API_KEY not found - email functionality will be disabled")
        
        # Session configuration
        self.session_duration_days = settings.session_duration_days
        self.confirmation_token_hours = settings.confirmation_token_hours
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def generate_secure_token() -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(32)
    
    async def register_user(self, email: str, password: str) -> Tuple[bool, str, Optional[int]]:
        """
        Register a new user and send confirmation email
        Returns: (success, message, user_id)
        """
        try:
            # Check if user already exists
            existing_user = await Database.get_user_by_email(email)
            if existing_user:
                if existing_user['is_confirmed']:
                    return False, "User already exists and is confirmed", None
                else:
                    # User exists but not confirmed - resend confirmation
                    await self._send_confirmation_email(existing_user['id'], email)
                    return True, "User already exists. New confirmation email sent.", existing_user['id']
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Create user
            user_id = await Database.create_user(email, password_hash)
            if not user_id:
                return False, "Failed to create user", None
            
            # Send confirmation email
            confirmation_sent = await self._send_confirmation_email(user_id, email)
            if not confirmation_sent:
                logger.warning(f"User created but confirmation email failed for {email}")
                return True, "User created but confirmation email failed. Please contact support.", user_id
            
            return True, "User registered successfully. Please check your email for confirmation link.", user_id
            
        except Exception as e:
            logger.error(f"Error registering user {email}: {e}")
            return False, "Registration failed. Please try again.", None
    
    async def _send_confirmation_email(self, user_id: int, email: str) -> bool:
        """Send email confirmation link using SendGrid"""
        try:
            if not self.sendgrid_client:
                logger.warning("SendGrid not configured - skipping email send")
                return False
            
            # Generate confirmation token
            token = self.generate_secure_token()
            expires_at = datetime.utcnow() + timedelta(hours=self.confirmation_token_hours)
            
            # Store token in database
            token_created = await Database.create_confirmation_token(user_id, token, expires_at)
            if not token_created:
                return False
            
            # Create confirmation URL
            confirmation_url = f"{self.app_url}/auth/confirm-email?token={token}"
            
            # HTML email body
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Confirm Your Debabelizer Account</title>
            </head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 16px; color: white; text-align: center; margin-bottom: 30px;">
                    <div style="font-size: 3em; margin-bottom: 15px;">🗣️</div>
                    <h1 style="margin: 0; font-size: 28px; font-weight: 600;">
                        Welcome to Debabelizer!
                    </h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                        Universal Voice Processing Platform
                    </p>
                </div>
                
                <div style="background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                    <p style="color: #333; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                        Thank you for registering with Debabelizer! We're excited to help you break down language barriers with our advanced speech-to-text and text-to-speech technology.
                    </p>
                    
                    <p style="color: #333; font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                        To complete your registration and start using our voice processing services, please confirm your email address by clicking the button below:
                    </p>
                    
                    <div style="text-align: center; margin: 40px 0;">
                        <a href="{confirmation_url}" 
                           style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                  color: white; padding: 16px 32px; text-decoration: none; 
                                  border-radius: 8px; font-size: 16px; font-weight: 600; 
                                  display: inline-block; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                            ✉️ Confirm My Email Address
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.5; margin-bottom: 15px;">
                        If the button doesn't work, you can copy and paste this link into your browser:
                    </p>
                    <p style="color: #007bff; font-size: 14px; word-break: break-all; background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 30px;">
                        {confirmation_url}
                    </p>
                    
                    <div style="border-top: 1px solid #eee; padding-top: 30px; margin-top: 30px;">
                        <p style="color: #888; font-size: 12px; line-height: 1.5; margin-bottom: 10px;">
                            📋 <strong>By registering, you confirm that you have read and accepted our 
                            <a href="{self.app_url}/terms" style="color: #667eea; text-decoration: none;">Terms of Service</a>.</strong>
                        </p>
                        <p style="color: #888; font-size: 12px; line-height: 1.5; margin-bottom: 10px;">
                            ⏰ This confirmation link will expire in {self.confirmation_token_hours} hours for security.
                        </p>
                        <p style="color: #888; font-size: 12px; line-height: 1.5; margin-bottom: 10px;">
                            🛡️ If you didn't create an account with Debabelizer, you can safely ignore this email.
                        </p>
                        <p style="color: #888; font-size: 12px; line-height: 1.5;">
                            ❓ Questions? Contact us at support@debabelizer.com
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_body = f"""
Welcome to Debabelizer!

Thank you for registering with Debabelizer - your universal voice processing platform.

To complete your registration and start using our speech-to-text and text-to-speech services, 
please confirm your email address by visiting this link:

{confirmation_url}

This confirmation link will expire in {self.confirmation_token_hours} hours for security.

If you didn't create an account with Debabelizer, you can safely ignore this email.

Questions? Contact us at support@debabelizer.com

Best regards,
The Debabelizer Team
            """
            
            # Create SendGrid mail object
            mail = Mail()
            mail.from_email = From(email=self.from_email, name=self.from_name)
            mail.to = To(email=email)
            mail.subject = Subject("Confirm Your Debabelizer Account 🗣️")
            mail.content = [
                PlainTextContent(text_body),
                HtmlContent(html_body)
            ]
            
            # Send email
            response = self.sendgrid_client.send(mail)
            
            if response.status_code == 202:
                logger.info(f"Confirmation email sent to {email} via SendGrid")
                return True
            else:
                logger.error(f"SendGrid email failed with status {response.status_code}: {response.body}")
                logger.error(f"SendGrid headers: {response.headers}")
                return False
            
        except Exception as e:
            logger.error(f"Error sending confirmation email to {email}: {e}")
            return False
    
    async def confirm_email(self, token: str) -> Tuple[bool, str]:
        """Confirm user email with token"""
        try:
            # Get token details
            token_data = await Database.get_confirmation_token(token)
            if not token_data:
                return False, "Invalid or expired confirmation link"
            
            if token_data['is_confirmed']:
                return True, "Email already confirmed. You can now log in."
            
            # Use token and confirm user
            success = await Database.use_confirmation_token(token, token_data['user_id'])
            if success:
                return True, "Email confirmed successfully! You can now log in."
            else:
                return False, "Failed to confirm email. Please try again."
                
        except Exception as e:
            logger.error(f"Error confirming email with token {token}: {e}")
            return False, "Email confirmation failed. Please try again."
    
    async def login_user(self, email: str, password: str, user_agent: str = None, 
                        ip_address: str = None) -> Tuple[bool, str, Optional[str], Optional[UserResponse]]:
        """
        Authenticate user and create session
        Returns: (success, message, session_token, user_data)
        """
        try:
            # Get user by email
            user = await Database.get_user_by_email(email)
            if not user:
                return False, "Invalid email or password", None, None
            
            # Check if user is confirmed
            if not user['is_confirmed']:
                return False, "Please confirm your email address before logging in", None, None
            
            # Verify password
            if not self.verify_password(password, user['password_hash']):
                return False, "Invalid email or password", None, None
            
            # Generate session token
            session_token = self.generate_secure_token()
            expires_at = datetime.utcnow() + timedelta(days=self.session_duration_days)
            
            # Create session
            session_created = await Database.create_user_session(
                user['id'], session_token, expires_at, user_agent, ip_address
            )
            
            if not session_created:
                return False, "Failed to create session", None, None
            
            # Update last login
            await Database.update_last_login(user['id'])
            
            # Create user response
            user_response = UserResponse(
                id=user['id'],
                email=user['email'],
                is_confirmed=user['is_confirmed'],
                created_at=user['created_at'],
                last_login=user['last_login']
            )
            
            return True, "Login successful", session_token, user_response
            
        except Exception as e:
            logger.error(f"Error logging in user {email}: {e}")
            return False, "Login failed. Please try again.", None, None
    
    async def validate_session(self, session_token: str) -> Optional[UserResponse]:
        """Validate session token and return user data"""
        try:
            session_data = await Database.get_user_session(session_token)
            if not session_data:
                return None
            
            if not session_data['is_active'] or not session_data['is_confirmed']:
                return None
            
            # Update session access time
            await Database.update_session_access(session_token)
            
            return UserResponse(
                id=session_data['user_id'],
                email=session_data['email'],
                is_confirmed=session_data['is_confirmed'],
                created_at=session_data['created_at'],
                last_login=session_data['last_accessed']
            )
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    async def logout_user(self, session_token: str) -> bool:
        """Logout user by deleting session"""
        try:
            return await Database.delete_user_session(session_token)
        except Exception as e:
            logger.error(f"Error logging out user: {e}")
            return False
    
    async def cleanup_expired_data(self) -> int:
        """Clean up expired tokens and sessions"""
        return await Database.cleanup_expired_tokens()

# Global auth service instance
auth_service = AuthService()