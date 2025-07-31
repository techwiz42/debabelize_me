from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from typing import Dict, List
import hashlib
from app.services.security_service import security_service

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.ip_request_history: Dict[str, List[datetime]] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self.block_duration = timedelta(hours=1)
        self.suspicious_patterns = [
            "/../", "/..", 
            "<script", "</script>",
            "javascript:", 
            "onerror=",
            "eval(",
            "exec(",
            "__import__",
        ]
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            if datetime.now() < self.blocked_ips[client_ip]:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "IP temporarily blocked due to suspicious activity"}
                )
            else:
                # Unblock if duration has passed
                del self.blocked_ips[client_ip]
        
        # Check for suspicious patterns in URL
        if any(pattern in str(request.url).lower() for pattern in self.suspicious_patterns):
            self.blocked_ips[client_ip] = datetime.now() + self.block_duration
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid request"}
            )
        
        # Add security headers
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        
        return response

class RequestSizeLimit(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > self.max_size:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request entity too large"}
                )
        
        response = await call_next(request)
        return response