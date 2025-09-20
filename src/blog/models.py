from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from src.main_app.database import Base

class BlogPost(Base):
    """Simple blog post model"""
    __tablename__ = 'blog_posts'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    slug = Column(String(350), unique=True, index=True, nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    featured_image = Column(String(500), nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
