from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List, Optional
import sqlite3
import json
import os
from datetime import datetime
from .models import BlogPost, BlogPostCreate, BlogPostUpdate, MediaUpload
try:
    from .storage import storage_manager
except Exception as e:
    print(f"GCP Storage not available: {e}")
    from .local_storage import storage_manager
import re

router = APIRouter(prefix="/api/blog", tags=["blog"])

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'blog_database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def create_slug(title: str) -> str:
    """Create URL-friendly slug from title"""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

@router.get("/posts", response_model=List[BlogPost])
async def get_posts(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    """Get blog posts with filtering"""
    conn = get_db_connection()
    
    query = "SELECT * FROM blog_posts WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor = conn.execute(query, params)
    posts = cursor.fetchall()
    conn.close()
    
    # Convert to Pydantic models
    result = []
    for post in posts:
        post_dict = dict(post)
        post_dict['tags'] = json.loads(post_dict['tags']) if post_dict['tags'] else []
        result.append(BlogPost(**post_dict))
    
    return result

@router.post("/posts", response_model=BlogPost)
async def create_post(post: BlogPostCreate):
    """Create new blog post"""
    conn = get_db_connection()
    
    # Generate slug
    slug = create_slug(post.title)
    
    # Check if slug exists
    cursor = conn.execute("SELECT id FROM blog_posts WHERE slug = ?", (slug,))
    if cursor.fetchone():
        # Add timestamp to make unique
        slug = f"{slug}-{int(datetime.now().timestamp())}"
    
    # Insert post
    cursor = conn.execute('''
        INSERT INTO blog_posts 
        (title, slug, content, excerpt, meta_description, tags, category, 
         featured_image, status, scheduled_for, published_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        post.title, slug, post.content, post.excerpt, post.meta_description,
        json.dumps(post.tags), post.category, post.featured_image, post.status,
        post.scheduled_for, datetime.now() if post.status == 'published' else None
    ))
    
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Return created post
    return await get_post_by_id(post_id)

@router.get("/posts/{post_id}", response_model=BlogPost)
async def get_post_by_id(post_id: int):
    """Get single blog post by ID"""
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM blog_posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    conn.close()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post_dict = dict(post)
    post_dict['tags'] = json.loads(post_dict['tags']) if post_dict['tags'] else []
    return BlogPost(**post_dict)

@router.get("/posts/slug/{slug}", response_model=BlogPost)
async def get_post_by_slug(slug: str):
    """Get single blog post by slug"""
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM blog_posts WHERE slug = ?", (slug,))
    post = cursor.fetchone()
    
    if post:
        # Increment view count
        conn.execute("UPDATE blog_posts SET view_count = view_count + 1 WHERE slug = ?", (slug,))
        conn.commit()
    
    conn.close()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post_dict = dict(post)
    post_dict['tags'] = json.loads(post_dict['tags']) if post_dict['tags'] else []
    return BlogPost(**post_dict)

@router.put("/posts/{post_id}", response_model=BlogPost)
async def update_post(post_id: int, post_update: BlogPostUpdate):
    """Update blog post"""
    conn = get_db_connection()
    
    # Build update query dynamically
    update_fields = []
    params = []
    
    for field, value in post_update.dict(exclude_unset=True).items():
        if field == 'tags':
            value = json.dumps(value)
        update_fields.append(f"{field} = ?")
        params.append(value)
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Add updated_at
    update_fields.append("updated_at = ?")
    params.append(datetime.now())
    
    # Add published_at if status changed to published
    if post_update.status == 'published':
        update_fields.append("published_at = ?")
        params.append(datetime.now())
    
    params.append(post_id)
    
    query = f"UPDATE blog_posts SET {', '.join(update_fields)} WHERE id = ?"
    cursor = conn.execute(query, params)
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")
    
    conn.commit()
    conn.close()
    
    return await get_post_by_id(post_id)

@router.delete("/posts/{post_id}")
async def delete_post(post_id: int):
    """Delete blog post"""
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM blog_posts WHERE id = ?", (post_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Post deleted successfully"}

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), alt_text: str = ""):
    """Upload image to Cloud Storage"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read file content
    content = await file.read()
    
    # Upload to Cloud Storage
    upload_result = storage_manager.upload_image(
        content, file.filename, file.content_type
    )
    
    # Save to database
    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO blog_media 
        (filename, gcs_path, public_url, original_name, file_size, mime_type, alt_text)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        upload_result['filename'], upload_result['gcs_path'], upload_result['public_url'],
        file.filename, len(content), file.content_type, alt_text
    ))
    
    media_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": media_id,
        "url": upload_result['public_url'],
        "filename": upload_result['filename']
    }

@router.get("/storage-status")
async def get_storage_status():
    """Check which storage system is being used"""
    try:
        from .storage import storage_manager
        if hasattr(storage_manager, 'images_bucket'):
            return {
                "storage_type": "Google Cloud Storage",
                "images_bucket": "astroroshni-blog-images",
                "charts_bucket": "astroroshni-blog-charts",
                "status": "active"
            }
        else:
            return {
                "storage_type": "Local Storage",
                "upload_dir": storage_manager.upload_dir,
                "status": "fallback"
            }
    except Exception as e:
        return {
            "storage_type": "Local Storage (fallback)",
            "error": str(e),
            "status": "error"
        }

@router.get("/categories")
async def get_categories():
    """Get all blog categories"""
    conn = get_db_connection()
    cursor = conn.execute("SELECT DISTINCT category FROM blog_posts WHERE category IS NOT NULL")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return categories