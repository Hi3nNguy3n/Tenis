# backend/app/schemas/post.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

# Shared properties
class PostBase(BaseModel):
    title: str = Field(..., max_length=255, description="Tiêu đề bài viết")
    summary: Optional[str] = None
    content: Optional[str] = None
    post_type: str = Field(default="news", max_length=30)
    category_id: Optional[int] = None
    category: Optional[str] = "Thông báo"
    thumbnail_url: Optional[str] = None
    media_url: Optional[str] = None
    status: str = Field(default="draft", max_length=20) # draft, pending, published, rejected
    is_breaking_news: bool = False
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    tags: Optional[List[str]] = [] # Pydantic List -> JSONB trong SQLAlchemy

# Properties to receive on item creation
class PostCreate(PostBase):
    pass # Author ID sẽ được lấy tự động từ Token người dùng

# Properties to receive on item update
class PostUpdate(PostBase):
    title: Optional[str] = None
    status: Optional[str] = None

# Properties to return to client
class PostResponse(PostBase):
    id: int
    slug: str
    author_id: int
    owner_user_id: Optional[int] = None
    publish_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Cho phép parse dữ liệu từ SQLAlchemy Model
    class Config:
        from_attributes = True