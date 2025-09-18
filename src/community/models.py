from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.main_app.database import Base

class CommunityUser(Base):
    """Community users table - separate from CRM users"""
    __tablename__ = 'community_users'
    
    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    profile_picture = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    reputation_score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    posts = relationship("CommunityPost", back_populates="author")
    comments = relationship("CommunityComment", back_populates="author")
    votes = relationship("CommunityVote", back_populates="user")
    company = relationship("CommunityCompany", back_populates="owner", uselist=False)

class CommunityCompany(Base):
    """Company pages in the community"""
    __tablename__ = 'community_companies'
    
    company_id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('community_users.user_id'), nullable=False)
    company_name = Column(String(200), nullable=False)
    company_slug = Column(String(200), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    logo = Column(String(500), nullable=True)
    website_url = Column(String(500), nullable=True)
    industry = Column(String(100), nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_badge = Column(String(100), nullable=True)  # e.g., "Verified Financial Advisor"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("CommunityUser", back_populates="company")
    posts = relationship("CommunityPost", back_populates="company")

class CommunityCategory(Base):
    """Post categories"""
    __tablename__ = 'community_categories'
    
    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    posts = relationship("CommunityPost", back_populates="category")

class CommunityPost(Base):
    """Community posts/blogs"""
    __tablename__ = 'community_posts'
    
    post_id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey('community_users.user_id'), nullable=False)
    company_id = Column(Integer, ForeignKey('community_companies.company_id'), nullable=True)
    category_id = Column(Integer, ForeignKey('community_categories.category_id'), nullable=False)
    title = Column(String(300), nullable=False)
    slug = Column(String(350), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    featured_image = Column(String(500), nullable=True)
    images = Column(JSON, nullable=True)  # Array of image URLs
    tags = Column(JSON, nullable=True)  # Array of tags
    meta_description = Column(String(160), nullable=True)
    meta_keywords = Column(String(200), nullable=True)
    view_count = Column(Integer, default=0)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    author = relationship("CommunityUser", back_populates="posts")
    company = relationship("CommunityCompany", back_populates="posts")
    category = relationship("CommunityCategory", back_populates="posts")
    comments = relationship("CommunityComment", back_populates="post", cascade="all, delete-orphan")
    votes = relationship("CommunityVote", back_populates="post", cascade="all, delete-orphan")

class CommunityComment(Base):
    """Comments on posts"""
    __tablename__ = 'community_comments'
    
    comment_id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('community_posts.post_id'), nullable=False)
    author_id = Column(Integer, ForeignKey('community_users.user_id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('community_comments.comment_id'), nullable=True)
    content = Column(Text, nullable=False)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    post = relationship("CommunityPost", back_populates="comments")
    author = relationship("CommunityUser", back_populates="comments")
    parent = relationship("CommunityComment", remote_side=[comment_id])
    replies = relationship("CommunityComment", back_populates="parent")
    votes = relationship("CommunityVote", back_populates="comment", cascade="all, delete-orphan")

class CommunityVote(Base):
    """Voting system for posts and comments"""
    __tablename__ = 'community_votes'
    
    vote_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('community_users.user_id'), nullable=False)
    post_id = Column(Integer, ForeignKey('community_posts.post_id'), nullable=True)
    comment_id = Column(Integer, ForeignKey('community_comments.comment_id'), nullable=True)
    vote_type = Column(String(10), nullable=False)  # 'upvote' or 'downvote'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("CommunityUser", back_populates="votes")
    post = relationship("CommunityPost", back_populates="votes")
    comment = relationship("CommunityComment", back_populates="votes")

class CommunityOTP(Base):
    """OTP verification for user registration"""
    __tablename__ = 'community_otps'
    
    otp_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    otp_code = Column(String(10), nullable=False)
    is_verified = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CommunityFAQ(Base):
    """Frequently Asked Questions"""
    __tablename__ = 'community_faqs'
    
    faq_id = Column(Integer, primary_key=True, index=True)
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)
    view_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CommunityTag(Base):
    """Tags for posts"""
    __tablename__ = 'community_tags'
    
    tag_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
