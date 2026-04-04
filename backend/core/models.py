from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from .database import Base
from sqlalchemy.sql import func

class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    fb_profile_link = Column(String, nullable=True)
    fb_username = Column(String, index=True, nullable=True)
    department = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

class PostHistory(Base):
    __tablename__ = "post_history"

    id = Column(Integer, primary_key=True, index=True)
    flyer_filename = Column(String)
    caption = Column(Text)
    status = Column(String, default="pending") # pending, posted, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    posted_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
