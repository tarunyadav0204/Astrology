from db import get_conn, execute


def init_blog_database():
    """Initialize blog tables in the main Postgres database."""
    with get_conn() as conn:
        # Blog posts table
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
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
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                published_at TIMESTAMPTZ,
                scheduled_for TIMESTAMPTZ
            )
            """,
        )

        # Media table
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS blog_media (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                gcs_path TEXT NOT NULL,
                public_url TEXT NOT NULL,
                original_name TEXT,
                file_size INTEGER,
                mime_type TEXT,
                alt_text TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )

        # Indexes
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_blog_posts_status ON blog_posts(status)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_blog_posts_published ON blog_posts(published_at DESC)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_blog_posts_slug ON blog_posts(slug)")

    print("Blog tables initialized successfully in Postgres!")


if __name__ == "__main__":
    init_blog_database()