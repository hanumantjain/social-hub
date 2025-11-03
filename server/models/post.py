from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    caption = Column(String, nullable=True)
    tags = Column(String, nullable=True)  # Store as comma-separated string
    views = Column(Integer, default=0, nullable=False)
    downloads = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship to User
    user = relationship("User", back_populates="posts")

