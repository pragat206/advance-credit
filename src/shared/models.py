from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import json

Base = declarative_base()

class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Banner(Base):
    __tablename__ = "banners"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128), nullable=False)
    image_url = Column(String(256), nullable=False)
    caption = Column(Text)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Partner(Base):
    __tablename__ = "partners"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    logo_url = Column(String(256))
    url = Column(String(256))
    products = relationship("Product", back_populates="partner")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    type = Column(String(64))
    description = Column(Text)
    interest = Column(String(32))
    features = Column(Text)  # JSON or comma-separated
    partner_id = Column(Integer, ForeignKey("partners.id"))
    partner = relationship("Partner", back_populates="products")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class FAQ(Base):
    __tablename__ = "faqs"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    location = Column(String(32), nullable=False, default="home")  # 'home', 'partners', etc.
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Testimonial(Base):
    __tablename__ = "testimonials"
    id = Column(Integer, primary_key=True, index=True)
    author = Column(String(128))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    icon = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    role = Column(String(128))
    bio = Column(Text)
    image_url = Column(String(256))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    contact = Column(String(64), nullable=False)
    email = Column(String(128))
    message = Column(Text)
    source = Column(String(32))  # 'contact' or 'apply' or 'debt'
    lead_type = Column(String(64))  # 'general contact us', 'applied for loan', 'priority action required'
    created_at = Column(DateTime, server_default=func.now())

class BankLoan(Base):
    __tablename__ = 'bank_loans'
    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String(64), nullable=False)
    loan_type = Column(String(32), nullable=False)
    interest_rate = Column(String(32), nullable=False)
    features = Column(Text)  # JSON-encoded list of features
    url = Column(String(256))
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now()) 