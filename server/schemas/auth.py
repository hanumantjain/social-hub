from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# Base User Schema
class UserBase(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    bio: Optional[str] = None

# User Creation Schema
class UserCreate(UserBase):
    password: str

# User Login Schema
class UserLogin(BaseModel):
    username: str
    password: str

# User Response Schema (what we return to client)
class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str

# Token Data Schema (for JWT payload)
class TokenData(BaseModel):
    username: Optional[str] = None

# User Update Schema (for future features)
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    bio: Optional[str] = None
