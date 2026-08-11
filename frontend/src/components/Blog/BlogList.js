import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import SEOHead from '../SEO/SEOHead';
import './BlogList.css';

const SITE_ORIGIN = 'https://astroroshni.com';

const formatDate = (dateString) => new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric'
});

const plainText = (value = '') => String(value)
    .replace(/<[^>]*>/g, ' ')
    .replace(/[#*_`>[\]()!-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const excerptFor = (post, maxLength = 190) => {
    const text = plainText(post?.excerpt || post?.content || '');
    return text.length > maxLength ? `${text.slice(0, maxLength).trim()}…` : text;
};

const readTimeFor = (post) => Math.max(1, Math.ceil(plainText(post?.content).split(/\s+/).filter(Boolean).length / 220));

const BlogList = ({ user, onLogin, onLogout, onAdminClick }) => {
    const [searchParams, setSearchParams] = useSearchParams();
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [categories, setCategories] = useState([]);
    const [error, setError] = useState('');
    const selectedCategory = searchParams.get('category') || '';

    useEffect(() => {
        let cancelled = false;
        const loadBlog = async () => {
            setLoading(true);
            setError('');
            try {
                const params = { status: 'published', ...(selectedCategory && { category: selectedCategory }) };
                const [postsResponse, categoriesResponse] = await Promise.all([
                    axios.get('/api/blog/posts', { params }),
                    axios.get('/api/blog/categories')
                ]);
                if (!cancelled) {
                    setPosts(Array.isArray(postsResponse.data) ? postsResponse.data : []);
                    setCategories(Array.isArray(categoriesResponse.data) ? categoriesResponse.data.filter(Boolean) : []);
                }
            } catch (loadError) {
                console.error('Error fetching blog:', loadError);
                if (!cancelled) {
                    setPosts([]);
                    setError('The journal could not be refreshed right now.');
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        };
        loadBlog();
        return () => { cancelled = true; };
    }, [selectedCategory]);

    const featuredPost = posts[0];
    const morePosts = posts.slice(1);
    const canonical = selectedCategory
        ? `${SITE_ORIGIN}/blog/?category=${encodeURIComponent(selectedCategory)}`
        : `${SITE_ORIGIN}/blog/`;

    const structuredData = useMemo(() => ({
        '@context': 'https://schema.org',
        '@graph': [
            {
                '@type': 'Blog',
                name: selectedCategory ? `${selectedCategory} articles | AstroRoshni Journal` : 'AstroRoshni Journal',
                description: 'Vedic astrology articles, practical guides, planetary timing and chart interpretation.',
                url: canonical,
                publisher: { '@type': 'Organization', name: 'AstroRoshni', url: SITE_ORIGIN }
            },
            {
                '@type': 'ItemList',
                numberOfItems: posts.length,
                itemListElement: posts.map((post, index) => ({
                    '@type': 'ListItem',
                    position: index + 1,
                    name: post.title,
                    url: `${SITE_ORIGIN}/blog/${post.slug}/`
                }))
            }
        ]
    }), [posts, selectedCategory, canonical]);

    const selectCategory = (category) => setSearchParams(category ? { category } : {});

    return (
        <div className="blog-list-page">
            <SEOHead
                title={selectedCategory ? `${selectedCategory} Astrology Articles | AstroRoshni Journal` : 'Vedic Astrology Blog - Insights & Predictions | AstroRoshni'}
                description="Explore thoughtful Vedic astrology articles, practical guides, planetary timing, nakshatras and chart interpretation from AstroRoshni."
                keywords="astrology blog, vedic astrology articles, astrology insights, planetary transits, nakshatra articles, astrology predictions"
                canonical={canonical}
                themeColor="#210b17"
                structuredData={structuredData}
            />
            <ModernNavigationHeader sticky user={user} onLogin={onLogin} onLogout={onLogout} onAdminClick={onAdminClick} />

            <main className="blog-list-main">
                <section className="blog-list-hero">
                    <div className="blog-list-hero__copy">
                        <p className="blog-list-eyebrow"><span /> The AstroRoshni journal</p>
                        <h1>Ideas for a life<br /><em>read in context.</em></h1>
                        <p>Vedic knowledge, translated into clear thinking about timing, relationships, work and the patterns shaping everyday life.</p>
                    </div>
                    <div className="blog-list-hero__mark" aria-hidden="true">
                        <span>AR</span><i /><i /><i />
                    </div>
                    <div className="blog-list-hero__proof">
                        <span><strong>{posts.length || '—'}</strong>Published essays</span>
                        <span><strong>{categories.length || '—'}</strong>Fields of study</span>
                        <span><strong>4</strong>Vedic systems</span>
                    </div>
                </section>

                <section className="blog-filters" aria-label="Filter journal by category">
                    <div>
                        <p>Browse by subject</p>
                        <div className="blog-filter-row">
                            <button type="button" className={!selectedCategory ? 'active' : ''} onClick={() => selectCategory('')}>All articles</button>
                            {categories.map((category) => (
                                <button type="button" key={category} className={selectedCategory === category ? 'active' : ''} onClick={() => selectCategory(category)}>{category}</button>
                            ))}
                        </div>
                    </div>
                    <span>{loading ? 'Refreshing journal…' : `${posts.length} article${posts.length === 1 ? '' : 's'}`}</span>
                </section>

                {loading ? (
                    <section className="blog-list-state" aria-live="polite">
                        <i aria-hidden /><p>Opening the journal…</p>
                    </section>
                ) : error ? (
                    <section className="blog-list-state" role="alert">
                        <p>{error}</p><button type="button" onClick={() => window.location.reload()}>Try again</button>
                    </section>
                ) : posts.length === 0 ? (
                    <section className="blog-list-state">
                        <p>No articles are filed under {selectedCategory || 'this subject'} yet.</p>
                        {selectedCategory && <button type="button" onClick={() => selectCategory('')}>View all articles</button>}
                    </section>
                ) : (
                    <>
                        <article className={`blog-feature ${featuredPost.featured_image ? '' : 'blog-feature--without-image'}`}>
                            <Link className="blog-feature__image" to={`/blog/${featuredPost.slug}`} aria-label={`Read ${featuredPost.title}`}>
                                {featuredPost.featured_image ? <img src={featuredPost.featured_image} alt="" /> : <span aria-hidden>Latest<br />thinking.</span>}
                            </Link>
                            <div className="blog-feature__copy">
                                <div className="blog-card-meta">
                                    <span>{featuredPost.category || 'Vedic astrology'}</span>
                                    <time dateTime={featuredPost.created_at}>{formatDate(featuredPost.created_at)}</time>
                                </div>
                                <p className="blog-feature__label">Featured reading</p>
                                <h2><Link to={`/blog/${featuredPost.slug}`}>{featuredPost.title}</Link></h2>
                                <p>{excerptFor(featuredPost, 260)}</p>
                                <div className="blog-feature__footer">
                                    <Link to={`/blog/${featuredPost.slug}`}>Read the article <span aria-hidden>↗</span></Link>
                                    <span>{readTimeFor(featuredPost)} min read</span>
                                </div>
                            </div>
                        </article>

                        {morePosts.length > 0 && (
                            <section className="blog-archive" aria-labelledby="blog-archive-title">
                                <header>
                                    <p className="blog-list-eyebrow"><span /> From the archive</p>
                                    <h2 id="blog-archive-title">More to explore.</h2>
                                </header>
                                <div className="blog-grid">
                                    {morePosts.map((post, index) => (
                                        <article key={post.id || post.slug} className="blog-card">
                                            <Link className="blog-card-image" to={`/blog/${post.slug}`} aria-label={`Read ${post.title}`}>
                                                {post.featured_image ? <img src={post.featured_image} alt="" loading="lazy" /> : <span>{String(index + 2).padStart(2, '0')}</span>}
                                            </Link>
                                            <div className="blog-card-content">
                                                <div className="blog-card-meta"><span>{post.category || 'Journal'}</span><time dateTime={post.created_at}>{formatDate(post.created_at)}</time></div>
                                                <h3><Link to={`/blog/${post.slug}`}>{post.title}</Link></h3>
                                                <p>{excerptFor(post)}</p>
                                                <footer><span>{readTimeFor(post)} min read</span><Link to={`/blog/${post.slug}`} aria-label={`Read ${post.title}`}>↗</Link></footer>
                                            </div>
                                        </article>
                                    ))}
                                </div>
                            </section>
                        )}
                    </>
                )}
            </main>
        </div>
    );
};

export default BlogList;
