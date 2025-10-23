from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Base Response Schema
class BaseResponse(BaseModel):
    message: str
    success: bool = True

# Error Response Schema
class ErrorResponse(BaseModel):
    detail: str
    success: bool = False

# Pagination Schema (for future features)
class PaginationParams(BaseModel):
    page: int = 1
    size: int = 10
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

# Paginated Response Schema
class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(cls, items: list, total: int, page: int, size: int):
        pages = (total + size - 1) // size
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
