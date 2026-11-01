"""User profile Pydantic schemas."""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserProfile(BaseModel):
    id: str = Field(alias="_id")
    full_name: str
    email: EmailStr
    mobile_number: str
    role: str = "user"
    farm_name: str | None = None
    location: str | None = None
    avatar_url: str | None = None
    created_at: datetime | None = None


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=100)
    mobile_number: str | None = Field(None, min_length=8, max_length=20)
    farm_name: str | None = None
    location: str | None = None
    avatar_url: str | None = None


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    mobile_number: str
    role: str
    is_active: bool
    farm_name: str | None = None
    location: str | None = None
    created_at: datetime | None = None
