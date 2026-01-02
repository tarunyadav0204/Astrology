from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BlogPostCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    meta_description: Optional[str] = None
    tags: Optional[List[str]] = []
    category: Optional[str] = None
    featured_image: Optional[str] = None
    status: str = "draft"
    scheduled_for: Optional[datetime] = None

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    meta_description: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    featured_image: Optional[str] = None
    status: Optional[str] = None
    scheduled_for: Optional[datetime] = None

class BlogPost(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: Optional[str]
    meta_description: Optional[str]
    tags: List[str]
    category: Optional[str]
    author: str
    status: str
    featured_image: Optional[str]
    view_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    scheduled_for: Optional[datetime]

class MediaUpload(BaseModel):
    filename: str
    gcs_path: str
    public_url: str
    original_name: str
    file_size: int
    mime_type: str
    alt_text: Optional[str] = None