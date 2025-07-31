from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import HTMLResponse
from typing import Optional
import logging
from app.models.auth import (
    UserRegistration, UserLogin, LoginResponse, EmailConfirmationRequest,
    MessageResponse, ErrorResponse, UserResponse
)
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_client_info(request: Request) -> tuple:
    """Extract client information from request"""
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host if request.client else ""
    return user_agent, ip_address

async def get_current_user(request: Request) -> Optional[UserResponse]:
    """Get current user from session token"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        return None
    return await auth_service.validate_session(session_token)

@router.post("/register", response_model=MessageResponse)
async def register(user_data: UserRegistration, request: Request):
    """Register a new user"""
    try:
        success, message, user_id = await auth_service.register_user(
            user_data.email, user_data.password
        )
        
        if success:
            logger.info(f"User registration successful: {user_data.email}")
            return MessageResponse(message=message, success=True)
        else:
            logger.warning(f"User registration failed: {user_data.email} - {message}")
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error for {user_data.email}: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=LoginResponse)
async def login(user_data: UserLogin, request: Request, response: Response):
    """Login user and create session"""
    try:
        user_agent, ip_address = get_client_info(request)
        
        success, message, session_token, user_response = await auth_service.login_user(
            user_data.email, user_data.password, user_agent, ip_address
        )
        
        if success and session_token and user_response:
            # Set secure HTTP-only cookie
            response.set_cookie(
                key="session_token",
                value=session_token,
                max_age=30 * 24 * 60 * 60,  # 30 days
                httponly=True,
                secure=True,  # HTTPS only
                samesite="lax"
            )
            
            logger.info(f"User login successful: {user_data.email}")
            return LoginResponse(
                user=user_response,
                session_token=session_token,
                message=message
            )
        else:
            logger.warning(f"User login failed: {user_data.email} - {message}")
            raise HTTPException(status_code=401, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {user_data.email}: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, response: Response):
    """Logout user and clear session"""
    try:
        session_token = request.cookies.get("session_token")
        if session_token:
            await auth_service.logout_user(session_token)
        
        # Clear cookie
        response.delete_cookie(key="session_token")
        
        return MessageResponse(message="Logout successful", success=True)
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.post("/confirm-email", response_model=MessageResponse)
async def confirm_email(confirmation_data: EmailConfirmationRequest):
    """Confirm user email with token"""
    try:
        success, message = await auth_service.confirm_email(confirmation_data.token)
        
        if success:
            logger.info(f"Email confirmation successful for token: {confirmation_data.token[:8]}...")
            return MessageResponse(message=message, success=True)
        else:
            logger.warning(f"Email confirmation failed for token: {confirmation_data.token[:8]}... - {message}")
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email confirmation error: {e}")
        raise HTTPException(status_code=500, detail="Email confirmation failed")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user

@router.get("/status")
async def auth_status(current_user: UserResponse = Depends(get_current_user)):
    """Check authentication status"""
    return {
        "authenticated": current_user is not None,
        "user": current_user if current_user else None
    }

# HTML Pages for authentication
@router.get("/register-page", response_class=HTMLResponse)
async def register_page():
    """Registration page"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Register - Debabelizer</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .auth-container {
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                padding: 40px;
                width: 100%;
                max-width: 400px;
                text-align: center;
            }
            
            .logo {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            h1 {
                color: #333;
                margin-bottom: 8px;
                font-size: 24px;
            }
            
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 14px;
            }
            
            .form-group {
                margin-bottom: 20px;
                text-align: left;
            }
            
            label {
                display: block;
                margin-bottom: 5px;
                color: #333;
                font-weight: 500;
                font-size: 14px;
            }
            
            input[type="email"], input[type="password"] {
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            
            input[type="email"]:focus, input[type="password"]:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .btn {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
                margin-bottom: 20px;
            }
            
            .btn:hover {
                transform: translateY(-2px);
            }
            
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .links {
                text-align: center;
                margin-top: 20px;
            }
            
            .links a {
                color: #667eea;
                text-decoration: none;
                font-size: 14px;
            }
            
            .links a:hover {
                text-decoration: underline;
            }
            
            .message {
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 20px;
                font-size: 14px;
            }
            
            .message.success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .message.error {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            
            .password-requirements {
                font-size: 12px;
                color: #666;
                margin-top: 5px;
                text-align: left;
            }
        </style>
    </head>
    <body>
        <div class="auth-container">
            <div class="logo">🗣️</div>
            <h1>Create Account</h1>
            <p class="subtitle">Join Debabelizer - Universal Voice Processing</p>
            
            <div id="message" class="message" style="display: none;"></div>
            
            <form id="registerForm">
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required minlength="8">
                    <div class="password-requirements">
                        Minimum 8 characters required
                    </div>
                </div>
                
                <button type="submit" class="btn" id="submitBtn">Create Account</button>
            </form>
            
            <div class="links">
                <a href="/auth/login-page">Already have an account? Sign in</a>
            </div>
        </div>
        
        <script>
            document.getElementById('registerForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const submitBtn = document.getElementById('submitBtn');
                const messageDiv = document.getElementById('message');
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                
                // Basic validation
                if (!email || !password) {
                    showMessage('Please fill in all fields', 'error');
                    return;
                }
                
                if (password.length < 8) {
                    showMessage('Password must be at least 8 characters long', 'error');
                    return;
                }
                
                // Submit registration
                submitBtn.disabled = true;
                submitBtn.textContent = 'Creating Account...';
                
                try {
                    const response = await fetch('/auth/register', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ email, password })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        showMessage(data.message, 'success');
                        document.getElementById('registerForm').reset();
                    } else {
                        showMessage(data.detail || 'Registration failed', 'error');
                    }
                } catch (error) {
                    showMessage('Network error. Please try again.', 'error');
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Create Account';
                }
            });
            
            function showMessage(text, type) {
                const messageDiv = document.getElementById('message');
                messageDiv.textContent = text;
                messageDiv.className = `message ${type}`;
                messageDiv.style.display = 'block';
                
                if (type === 'success') {
                    setTimeout(() => {
                        messageDiv.style.display = 'none';
                    }, 5000);
                }
            }
        </script>
    </body>
    </html>
    """

@router.get("/login-page", response_class=HTMLResponse)
async def login_page():
    """Login page"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - Debabelizer</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .auth-container {
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                padding: 40px;
                width: 100%;
                max-width: 400px;
                text-align: center;
            }
            
            .logo {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            h1 {
                color: #333;
                margin-bottom: 8px;
                font-size: 24px;
            }
            
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 14px;
            }
            
            .form-group {
                margin-bottom: 20px;
                text-align: left;
            }
            
            label {
                display: block;
                margin-bottom: 5px;
                color: #333;
                font-weight: 500;
                font-size: 14px;
            }
            
            input[type="email"], input[type="password"] {
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            
            input[type="email"]:focus, input[type="password"]:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .btn {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
                margin-bottom: 20px;
            }
            
            .btn:hover {
                transform: translateY(-2px);
            }
            
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .links {
                text-align: center;
                margin-top: 20px;
            }
            
            .links a {
                color: #667eea;
                text-decoration: none;
                font-size: 14px;
                margin: 0 10px;
            }
            
            .links a:hover {
                text-decoration: underline;
            }
            
            .message {
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 20px;
                font-size: 14px;
            }
            
            .message.success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .message.error {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
        </style>
    </head>
    <body>
        <div class="auth-container">
            <div class="logo">🗣️</div>
            <h1>Welcome Back</h1>
            <p class="subtitle">Sign in to your Debabelizer account</p>
            
            <div id="message" class="message" style="display: none;"></div>
            
            <form id="loginForm">
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <button type="submit" class="btn" id="submitBtn">Sign In</button>
            </form>
            
            <div class="links">
                <a href="/auth/register-page">Don't have an account? Sign up</a>
            </div>
        </div>
        
        <script>
            document.getElementById('loginForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const submitBtn = document.getElementById('submitBtn');
                const messageDiv = document.getElementById('message');
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                
                // Basic validation
                if (!email || !password) {
                    showMessage('Please fill in all fields', 'error');
                    return;
                }
                
                // Submit login
                submitBtn.disabled = true;
                submitBtn.textContent = 'Signing In...';
                
                try {
                    const response = await fetch('/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ email, password })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        showMessage('Login successful! Redirecting...', 'success');
                        setTimeout(() => {
                            window.location.href = '/';
                        }, 1500);
                    } else {
                        showMessage(data.detail || 'Login failed', 'error');
                    }
                } catch (error) {
                    showMessage('Network error. Please try again.', 'error');
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Sign In';
                }
            });
            
            function showMessage(text, type) {
                const messageDiv = document.getElementById('message');
                messageDiv.textContent = text;
                messageDiv.className = `message ${type}`;
                messageDiv.style.display = 'block';
            }
        </script>
    </body>
    </html>
    """

@router.get("/confirm-email", response_class=HTMLResponse)
async def confirm_email_page(token: str):
    """Email confirmation page"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Confirm Email - Debabelizer</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            
            .auth-container {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                padding: 40px;
                width: 100%;
                max-width: 400px;
                text-align: center;
            }}
            
            .logo {{
                font-size: 2.5em;
                margin-bottom: 10px;
            }}
            
            h1 {{
                color: #333;
                margin-bottom: 20px;
                font-size: 24px;
            }}
            
            .message {{
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 20px;
                font-size: 14px;
            }}
            
            .message.success {{
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            
            .message.error {{
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            
            .btn {{
                display: inline-block;
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                transition: transform 0.2s;
                margin-top: 20px;
            }}
            
            .btn:hover {{
                transform: translateY(-2px);
            }}
            
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }}
            
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="auth-container">
            <div class="logo">🗣️</div>
            <h1>Email Confirmation</h1>
            
            <div id="loading" style="display: block;">
                <div class="spinner"></div>
                <p>Confirming your email address...</p>
            </div>
            
            <div id="result" style="display: none;">
                <div id="message" class="message"></div>
                <a href="/auth/login-page" class="btn" id="loginBtn" style="display: none;">Continue to Login</a>
            </div>
        </div>
        
        <script>
            async function confirmEmail() {{
                try {{
                    const response = await fetch('/auth/confirm-email', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ token: '{token}' }})
                    }});
                    
                    const data = await response.json();
                    
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('result').style.display = 'block';
                    
                    if (response.ok) {{
                        document.getElementById('message').textContent = data.message;
                        document.getElementById('message').className = 'message success';
                        document.getElementById('loginBtn').style.display = 'inline-block';
                    }} else {{
                        document.getElementById('message').textContent = data.detail || 'Email confirmation failed';
                        document.getElementById('message').className = 'message error';
                    }}
                }} catch (error) {{
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('result').style.display = 'block';
                    document.getElementById('message').textContent = 'Network error. Please try again.';
                    document.getElementById('message').className = 'message error';
                }}
            }}
            
            // Auto-confirm when page loads
            confirmEmail();
        </script>
    </body>
    </html>
    """