from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserRegistration(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=100, description="User's password (8-100 characters)")

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

class UserResponse(BaseModel):
    id: int
    email: str
    is_confirmed: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class LoginResponse(BaseModel):
    user: UserResponse
    session_token: str
    message: str

class EmailConfirmationRequest(BaseModel):
    token: str = Field(..., description="Email confirmation token")

class MessageResponse(BaseModel):
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    message: str
    success: bool = False