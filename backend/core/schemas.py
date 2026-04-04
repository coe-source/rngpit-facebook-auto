from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FacultyBase(BaseModel):
    name: str
    fb_profile_link: Optional[str] = None
    fb_username: Optional[str] = None
    department: Optional[str] = None
    is_active: bool = True

class FacultyCreate(FacultyBase):
    pass

class Faculty(FacultyBase):
    id: int

    class Config:
        from_attributes = True

class PostHistoryBase(BaseModel):
    flyer_filename: str
    caption: str
    status: str = "pending"

class PostHistoryCreate(PostHistoryBase):
    pass

class PostHistory(PostHistoryBase):
    id: int
    created_at: datetime
    posted_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
