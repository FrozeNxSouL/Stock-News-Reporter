"""
Pydantic models for user accounts and profiles.
"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
import re


class UserSignup(BaseModel):
    """Request body for user registration."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username must be alphanumeric (letters, numbers, underscores)")
        return v.lower()


class UserLogin(BaseModel):
    """Request body for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response containing JWT tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str


class UserProfileUpdate(BaseModel):
    """Fields the user can update on their profile."""
    username: Optional[str] = Field(None, min_length=3, max_length=30)
    watchlist: Optional[List[str]] = None  # list of ticker symbols to track

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username must be alphanumeric (letters, numbers, underscores)")
        return v.lower()


class UserInDB(BaseModel):
    """Full user document as stored in MongoDB (sensitive fields excluded in response)."""
    id: str = Field(alias="_id")
    email: str
    username: str
    hashed_password: str
    watchlist: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
        populate_by_name = True


class UserResponse(BaseModel):
    """Public user profile returned to clients (no password hash)."""
    id: str = Field(alias="_id")
    email: str
    username: str
    watchlist: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
