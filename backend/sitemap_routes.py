from fastapi import APIRouter
from fastapi.responses import Response
import sqlite3
import os

router = APIRouter()

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'astrology.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/sitemap.xml")
async def generate_sitemap():
    """Generate complete sitemap with static pages and blog posts"""
    
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT slug, updated_at FROM blog_posts WHERE status = 'published' ORDER BY updated_at DESC"
    )
    posts = cursor.fetchall()
    conn.close()
    
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    nakshatras = ['ashwini', 'bharani', 'krittika', 'rohini', 'mrigashira', 'ardra', 'punarvasu', 'pushya', 'ashlesha', 'magha', 'purva-phalguni', 'uttara-phalguni', 'hasta', 'chitra', 'swati', 'vishakha', 'anuradha', 'jyeshtha', 'mula', 'purva-ashadha', 'uttara-ashadha', 'shravana', 'dhanishta', 'shatabhisha', 'purva-bhadrapada', 'uttara-bhadrapada', 'revati']
    
    sitemap_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://astroroshni.com/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/blog</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/marriage-analysis</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/career-guidance</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/health-analysis</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/wealth-analysis</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/panchang</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/muhurat-finder</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/horoscope/daily</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/horoscope/weekly</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/horoscope/monthly</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/beginners-guide</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/advanced-courses</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/myths-vs-reality</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>https://astroroshni.com/nakshatras</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>'''
    
    # Add all 27 nakshatras
    for nakshatra in nakshatras:
        sitemap_xml += f'''
  <url>
    <loc>https://astroroshni.com/nakshatra/{nakshatra}/2025</loc>
    <lastmod>{today}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.7</priority>
  </url>'''
    
    # Add blog posts
    for post in posts:
        sitemap_xml += f'''
  <url>
    <loc>https://astroroshni.com/blog/{post[0]}</loc>
    <lastmod>{post[1][:10]}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>'''
    
    sitemap_xml += '\n</urlset>'
    
    return Response(content=sitemap_xml, media_type="application/xml")