from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal, Dict, Any
from datetime import datetime
import re

class UserCreateRequest(BaseModel):
    """Request model for creating a new user"""
    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="User's full name"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be 8-128 characters"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name contains only letters and spaces"""
        if not re.match(r'^[a-zA-Z\s]+$', v):
            raise ValueError('Name must contain only letters and spaces')
        return v.strip().title()  # Clean and title case

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength requirements"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name contains only letters and spaces"""
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z\s]+$', v):
            raise ValueError('Name must contain only letters and spaces')
        return v.strip().title()

class ChangePasswordRequest(BaseModel):
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

class UserFiltersQuery(BaseModel):
    """Query parameters for user filtering"""
    search_term: Optional[str] = Field(None, description="Search across name and email")
    role: Optional[str] = Field(None, description="Filter by role (admin, user)")
    email: Optional[str] = Field(None, description="Filter by email")
    is_active: Optional[bool] = Field(None, description="Filter by active status")

class UserPaginationQuery(BaseModel):
    """Query parameters for user pagination"""
    page: int = Field(1, ge=1, description="Page number (starts from 1)")
    limit: int = Field(10, ge=1, le=100, description="Items per page (1-100)")
    order_by: str = Field("created_at", description="Sort field")
    order_direction: Literal["asc", "desc"] = Field("desc", description="Sort direction")

class UserListResponse(BaseModel):
    """Response model for user list endpoint"""
    data: list[dict]
    meta: dict

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    role: str
    profile_image_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
