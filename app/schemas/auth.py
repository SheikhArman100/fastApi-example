from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

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
