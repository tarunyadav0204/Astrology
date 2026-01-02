import sqlite3
import os
from datetime import datetime

def init_blog_database():
    """Initialize blog database with required tables"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'blog_database.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Blog posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            excerpt TEXT,
            meta_description TEXT,
            tags TEXT,
            category TEXT,
            author TEXT DEFAULT 'AstroRoshni',
            status TEXT DEFAULT 'draft',
            featured_image TEXT,
            view_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP,
            scheduled_for TIMESTAMP
        )
    ''')
    
    # Media table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blog_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            gcs_path TEXT NOT NULL,
            public_url TEXT NOT NULL,
            original_name TEXT,
            file_size INTEGER,
            mime_type TEXT,
            alt_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_blog_posts_status ON blog_posts(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_blog_posts_published ON blog_posts(published_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_blog_posts_slug ON blog_posts(slug)')
    
    conn.commit()
    conn.close()
    print("Blog database initialized successfully!")

if __name__ == "__main__":
    init_blog_database()