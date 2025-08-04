"""Authentication schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored in JWT token."""
    email: Optional[str] = None
    user_id: Optional[int] = None
    business_id: Optional[int] = None


class LoginRequest(BaseModel):
    """Login request data."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class RegisterBusinessRequest(BaseModel):
    """Register new business with admin user."""
    # Business info
    business_name: str = Field(..., min_length=2, max_length=255)
    business_slug: str = Field(..., min_length=2, max_length=255, pattern="^[a-z0-9-]+$")
    
    # Admin user info
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    admin_name: str = Field(..., min_length=2, max_length=255)
    
    class Config:
        json_schema_extra = {
            "example": {
                "business_name": "Sunrise Cafe",
                "business_slug": "sunrise-cafe",
                "admin_email": "owner@sunrisecafe.com",
                "admin_password": "securePassword123!",
                "admin_name": "John Doe"
            }
        }