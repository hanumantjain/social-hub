# Import all models here so SQLAlchemy can discover them
from .user import User
from .post import Post

# This ensures all models are registered with SQLAlchemy
__all__ = ["User", "Post"]
