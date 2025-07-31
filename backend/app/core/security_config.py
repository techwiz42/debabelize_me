from pydantic_settings import BaseSettings
from typing import List

class SecuritySettings(BaseSettings):
    # Rate limiting configuration
    rate_limit_requests: int = 30
    rate_limit_window_minutes: int = 1
    
    # Input validation
    max_input_length: int = 10000
    max_conversation_length: int = 50  # Max messages in a conversation
    
    # Session security
    session_timeout_hours: int = 24
    max_sessions_per_ip: int = 10
    
    # Content filtering
    enable_content_filtering: bool = True
    log_injection_attempts: bool = True
    
    # CORS settings
    allowed_origins: List[str] = ["http://localhost:3005", "http://127.0.0.1:3005"]
    
    class Config:
        env_prefix = "SECURITY_"

security_settings = SecuritySettings()