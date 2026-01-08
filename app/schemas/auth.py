from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re

class LoginRequest(BaseModel):
    """Request model for user login"""
    email: EmailStr = Field(
        ...,
        description="Valid email address"
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User password"
    )

class TokenResponse(BaseModel):
    """Response model containing access token and user info"""
    access_token: str = Field(..., description="JWT access token")
    user: dict = Field(..., description="User information")

class RefreshTokenResponse(BaseModel):
    """Response model for token refresh"""
    access_token: str = Field(..., description="New JWT access token")
    role: str = Field(..., description="User role")

class AuthUserResponse(BaseModel):
    """User information in auth responses"""
    id: int
    name: str
    email: str
    role: str

class ChangePasswordRequest(BaseModel):
    """Request model for changing password"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password must be 8-128 characters"
    )

    @field_validator('new_password')
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        """Validate new password strength requirements"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class ForgetPasswordRequest(BaseModel):
    """Request model for forget password"""
    email: EmailStr = Field(..., description="User email address")

class ResetPasswordRequest(BaseModel):
    """Request model for resetting password with token"""
    token: str = Field(..., description="Forget password token")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password must be 8-128 characters"
    )

    @field_validator('new_password')
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        """Validate new password strength requirements"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
