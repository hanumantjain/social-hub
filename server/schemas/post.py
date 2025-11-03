from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Base Post Schema
class PostBase(BaseModel):
    title: Optional[str] = None
    caption: Optional[str] = None
    tags: Optional[str] = None

# Post Creation Schema
class PostCreate(PostBase):
    image_url: str

# Post Response Schema
class PostResponse(PostBase):
    id: int
    user_id: int
    image_url: str
    views: int = 0
    downloads: int = 0
    created_at: datetime
    updated_at: datetime
    
    # User info
    username: Optional[str] = None
    user_full_name: Optional[str] = None
    
    class Config:
        from_attributes = True

