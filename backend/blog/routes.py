from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form
from typing import List, Optional
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

from db import get_conn, execute

router = APIRouter(prefix="/api/blog", tags=["blog"])

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
    query = "SELECT * FROM blog_posts WHERE 1=1"
    params: list = []

    if status:
        query += " AND status = %s"
        params.append(status)

    if category:
        query += " AND category = %s"
        params.append(category)

    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with get_conn() as conn:
        cur = execute(conn, query, tuple(params))
        rows = cur.fetchall() or []
        colnames = [d[0] for d in cur.description] if cur.description else []

    result: List[BlogPost] = []
    for row in rows:
        data = dict(zip(colnames, row)) if colnames else {}
        tags_raw = data.get("tags")
        data["tags"] = json.loads(tags_raw) if tags_raw else []
        result.append(BlogPost(**data))

    return result

@router.post("/posts", response_model=BlogPost)
async def create_post(post: BlogPostCreate):
    """Create new blog post"""
    # Use provided slug or generate from title
    slug = post.slug or create_slug(post.title)

    with get_conn() as conn:
        cur = execute(conn, "SELECT id FROM blog_posts WHERE slug = %s", (slug,))
        if cur.fetchone():
            slug = f"{slug}-{int(datetime.now().timestamp())}"

        cur = execute(
            conn,
            """
            INSERT INTO blog_posts
                (title, slug, content, excerpt, meta_description, tags, category,
                 featured_image, status, scheduled_for, published_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                post.title,
                slug,
                post.content,
                post.excerpt,
                post.meta_description,
                json.dumps(post.tags),
                post.category,
                post.featured_image,
                post.status,
                post.scheduled_for,
                datetime.now() if post.status == "published" else None,
            ),
        )
        row = cur.fetchone()
        post_id = row[0] if row else None

    if post_id is None:
        raise HTTPException(status_code=500, detail="Failed to create post")

    return await get_post_by_id(post_id)

@router.get("/posts/{post_id}", response_model=BlogPost)
async def get_post_by_id(post_id: int):
    """Get single blog post by ID"""
    with get_conn() as conn:
        cur = execute(conn, "SELECT * FROM blog_posts WHERE id = %s", (post_id,))
        row = cur.fetchone()
        colnames = [d[0] for d in cur.description] if cur.description else []

    if not row:
        raise HTTPException(status_code=404, detail="Post not found")

    data = dict(zip(colnames, row)) if colnames else {}
    tags_raw = data.get("tags")
    data["tags"] = json.loads(tags_raw) if tags_raw else []
    return BlogPost(**data)

@router.get("/posts/slug/{slug}", response_model=BlogPost)
async def get_post_by_slug(slug: str):
    """Get single blog post by slug"""
    with get_conn() as conn:
        cur = execute(conn, "SELECT * FROM blog_posts WHERE slug = %s", (slug,))
        row = cur.fetchone()
        colnames = [d[0] for d in cur.description] if cur.description else []

        if row:
            execute(
                conn,
                "UPDATE blog_posts SET view_count = view_count + 1 WHERE slug = %s",
                (slug,),
            )

    if not row:
        raise HTTPException(status_code=404, detail="Post not found")

    data = dict(zip(colnames, row)) if colnames else {}
    tags_raw = data.get("tags")
    data["tags"] = json.loads(tags_raw) if tags_raw else []
    return BlogPost(**data)

@router.put("/posts/{post_id}", response_model=BlogPost)
async def update_post(post_id: int, post_update: BlogPostUpdate):
    """Update blog post"""
    # Build update query dynamically
    update_fields = []
    params: list = []

    for field, value in post_update.dict(exclude_unset=True).items():
        if field == "tags":
            value = json.dumps(value)
        update_fields.append(f"{field} = %s")
        params.append(value)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_fields.append("updated_at = %s")
    params.append(datetime.now())

    if post_update.status == "published":
        update_fields.append("published_at = %s")
        params.append(datetime.now())

    params.append(post_id)

    query = f"UPDATE blog_posts SET {', '.join(update_fields)} WHERE id = %s"

    with get_conn() as conn:
        cur = execute(conn, query, tuple(params))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Post not found")

    return await get_post_by_id(post_id)

@router.delete("/posts/{post_id}")
async def delete_post(post_id: int):
    """Delete blog post"""
    with get_conn() as conn:
        cur = execute(conn, "DELETE FROM blog_posts WHERE id = %s", (post_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Post not found")

    return {"message": "Post deleted successfully"}

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), alt_text: str = Form("")):
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
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            INSERT INTO blog_media
                (filename, gcs_path, public_url, original_name, file_size, mime_type, alt_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                upload_result["filename"],
                upload_result["gcs_path"],
                upload_result["public_url"],
                file.filename,
                len(content),
                file.content_type,
                alt_text,
            ),
        )
        row = cur.fetchone()
        media_id = row[0] if row else None

    if media_id is None:
        raise HTTPException(status_code=500, detail="Failed to save media record")

    return {
        "id": media_id,
        "url": upload_result['public_url'],
        "filename": upload_result['filename'],
        "alt_text": alt_text
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
    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT DISTINCT category FROM blog_posts WHERE category IS NOT NULL",
        )
        rows = cur.fetchall() or []
    return [row[0] for row in rows]

@router.get("/media")
async def get_media(limit: int = 20, offset: int = 0):
    """Get uploaded media files with alt text"""
    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT * FROM blog_media ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
        rows = cur.fetchall() or []
        colnames = [d[0] for d in cur.description] if cur.description else []

    return [dict(zip(colnames, row)) for row in rows]

# Legacy sitemap code removed (endpoint now served at root-level sitemap)