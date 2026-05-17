from datetime import date, datetime

from fastapi import APIRouter
from fastapi.responses import Response
import os

from db import get_conn, execute

router = APIRouter()


def _lastmod_date(value) -> str:
    """Sitemap lastmod as YYYY-MM-DD; DB may return datetime, date, or string."""
    if value is None:
        return datetime.now().strftime("%Y-%m-%d")
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    s = str(value).strip()
    return s[:10] if len(s) >= 10 else s

@router.get("/sitemap.xml")
async def generate_sitemap():
    """Generate complete sitemap with static pages and blog posts"""
    
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT slug, updated_at
            FROM blog_posts
            WHERE status = 'published'
            ORDER BY updated_at DESC
            """,
        )
        posts = cur.fetchall() or []
    
    today = datetime.now().strftime('%Y-%m-%d')
    current_year = datetime.now().year

    nakshatras = ['ashwini', 'bharani', 'krittika', 'rohini', 'mrigashira', 'ardra', 'punarvasu', 'pushya', 'ashlesha', 'magha', 'purva-phalguni', 'uttara-phalguni', 'hasta', 'chitra', 'swati', 'vishakha', 'anuradha', 'jyeshtha', 'mula', 'purva-ashadha', 'uttara-ashadha', 'shravana', 'dhanishta', 'shatabhisha', 'purva-bhadrapada', 'uttara-bhadrapada', 'revati']

    static_pages = [
        ('/', 'daily', '1.0'),
        ('/panchang', 'daily', '0.9'),
        ('/muhurat-finder', 'daily', '0.8'),
        ('/monthly-panchang', 'weekly', '0.7'),
        ('/kundli-matching', 'weekly', '0.9'),
        ('/festivals', 'weekly', '0.7'),
        ('/festivals/monthly', 'weekly', '0.7'),
        ('/nakshatras', 'weekly', '0.8'),
        ('/karma-analysis', 'weekly', '0.9'),
        ('/chat', 'weekly', '0.9'),
        ('/blog', 'daily', '0.9'),
        ('/about', 'monthly', '0.5'),
        ('/contact', 'monthly', '0.5'),
        ('/policy', 'yearly', '0.3'),
        ('/calendar-2026', 'monthly', '0.7'),
        ('/tools/ashtakavarga', 'monthly', '0.7'),
        ('/astrovastu', 'monthly', '0.6'),
        ('/beginners-guide', 'monthly', '0.6'),
        ('/advanced-courses', 'monthly', '0.6'),
        ('/myths-vs-reality', 'monthly', '0.5'),
        ('/marriage-analysis', 'weekly', '0.9'),
        ('/career-guidance', 'weekly', '0.9'),
        ('/health-analysis', 'weekly', '0.8'),
        ('/wealth-analysis', 'weekly', '0.8'),
        ('/horoscope/daily', 'daily', '0.8'),
        ('/horoscope/weekly', 'weekly', '0.7'),
        ('/horoscope/monthly', 'monthly', '0.7'),
    ]
    
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

    for path, changefreq, priority in static_pages:
        loc = f"https://astroroshni.com{path if path != '/' else '/'}"
        sitemap_xml += f'''
  <url>
    <loc>{loc}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>'''

    for nakshatra in nakshatras:
        sitemap_xml += f'''
  <url>
    <loc>https://astroroshni.com/nakshatra/{nakshatra}/{current_year}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.7</priority>
  </url>'''
    
    # Add blog posts
    for post in posts:
        sitemap_xml += f'''
  <url>
    <loc>https://astroroshni.com/blog/{post[0]}</loc>
    <lastmod>{_lastmod_date(post[1])}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>'''
    
    sitemap_xml += '\n</urlset>'
    
    return Response(content=sitemap_xml, media_type="application/xml")