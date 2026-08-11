import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import SEOHead from '../SEO/SEOHead';
import { markdownToHtml } from '../../utils/blogMarkdown';
import './BlogPost.css';

const SITE_ORIGIN = 'https://astroroshni.com';

const ShareIcon = ({ type }) => {
    if (type === 'whatsapp') {
        return (
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path fill="currentColor" d="M17.47 14.38c-.28-.14-1.64-.81-1.9-.9-.25-.1-.44-.14-.62.14-.19.28-.72.9-.88 1.08-.16.19-.33.21-.61.07-.28-.14-1.18-.43-2.25-1.39-.83-.74-1.39-1.65-1.55-1.93-.16-.28-.02-.43.12-.57.13-.12.28-.33.42-.49.14-.16.19-.28.28-.47.1-.19.05-.35-.02-.49-.07-.14-.62-1.5-.85-2.05-.22-.53-.45-.46-.62-.47h-.53c-.19 0-.49.07-.74.35-.25.28-.97.95-.97 2.3s.99 2.67 1.13 2.85c.14.19 1.95 2.98 4.73 4.18.66.29 1.18.46 1.58.58.66.21 1.27.18 1.75.11.53-.08 1.64-.67 1.87-1.32.23-.65.23-1.2.16-1.32-.07-.11-.25-.18-.53-.32zM12.04 2C6.5 2 2 6.48 2 12c0 1.77.46 3.45 1.28 4.92L2 22l5.23-1.37A9.96 9.96 0 0 0 12.04 22C17.56 22 22 17.52 22 12S17.56 2 12.04 2z" />
            </svg>
        );
    }
    if (type === 'x') {
        return (
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path fill="currentColor" d="M18.24 2H21l-6.52 7.45L22 22h-6.17l-4.83-6.31L5.4 22H2.64l6.98-7.98L2 2h6.33l4.36 5.77L18.24 2zm-1.08 18.1h1.71L7 3.8H5.17l11.99 16.3z" />
            </svg>
        );
    }
    if (type === 'linkedin') {
        return (
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path fill="currentColor" d="M20.45 20.45h-3.55v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.12 20.45H3.55V9h3.57v11.45zM22 0H2C.9 0 0 .9 0 2v20c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V2c0-1.1-.9-2-2-2z" />
            </svg>
        );
    }
    return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path fill="currentColor" d="M22 12.07C22 6.48 17.52 2 11.93 2S1.86 6.48 1.86 12.07c0 5.02 3.66 9.18 8.44 9.93v-7.03H7.9v-2.9h2.4V9.85c0-2.37 1.41-3.68 3.57-3.68 1.03 0 2.12.18 2.12.18v2.33h-1.19c-1.18 0-1.54.73-1.54 1.48v1.78h2.63l-.42 2.9h-2.21V22c4.78-.75 8.44-4.91 8.44-9.93z" />
        </svg>
    );
};

const BlogPost = ({ user, onLogin, onLogout, onAdminClick }) => {
    const { slug } = useParams();
    const [post, setPost] = useState(null);
    const [recentPosts, setRecentPosts] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [readingProgress, setReadingProgress] = useState(0);

    useEffect(() => {
        const updateReadingProgress = () => {
            const article = document.querySelector('.blog-post');
            if (!article) return setReadingProgress(0);
            const start = article.offsetTop;
            const distance = Math.max(1, article.offsetHeight - window.innerHeight);
            setReadingProgress(Math.min(100, Math.max(0, ((window.scrollY - start) / distance) * 100)));
        };
        window.addEventListener('scroll', updateReadingProgress, { passive: true });
        window.addEventListener('resize', updateReadingProgress);
        updateReadingProgress();
        return () => {
            window.removeEventListener('scroll', updateReadingProgress);
            window.removeEventListener('resize', updateReadingProgress);
        };
    }, [post]);

    useEffect(() => {
        fetchPost();
        fetchSidebarData();
    }, [slug]);

    const fetchPost = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get(`/api/blog/posts/slug/${slug}`);
            setPost(response.data);
        } catch (err) {
            console.error('Error fetching post:', err);
            setError('Post not found');
        } finally {
            setLoading(false);
        }
    };

    const fetchSidebarData = async () => {
        try {
            const [postsRes, categoriesRes] = await Promise.all([
                axios.get('/api/blog/posts', { params: { status: 'published', limit: 8 } }),
                axios.get('/api/blog/categories'),
            ]);
            setRecentPosts(Array.isArray(postsRes.data) ? postsRes.data : []);
            setCategories(Array.isArray(categoriesRes.data) ? categoriesRes.data : []);
        } catch (err) {
            console.error('Error fetching blog sidebar data:', err);
            setRecentPosts([]);
            setCategories([]);
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    const shareUrl = useMemo(() => {
        if (!post?.slug) return SITE_ORIGIN;
        if (typeof window !== 'undefined' && window.location?.origin) {
            return `${window.location.origin}/blog/${post.slug}`;
        }
        return `${SITE_ORIGIN}/blog/${post.slug}`;
    }, [post?.slug]);

    const shareLinks = useMemo(() => {
        if (!post) return [];
        const text = post.title || 'AstroRoshni Blog';
        const encodedUrl = encodeURIComponent(shareUrl);
        const encodedText = encodeURIComponent(text);
        return [
            {
                type: 'whatsapp',
                label: 'Share on WhatsApp',
                href: `https://wa.me/?text=${encodeURIComponent(`${text} ${shareUrl}`)}`,
                className: 'share-whatsapp',
            },
            {
                type: 'x',
                label: 'Share on X',
                href: `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedText}`,
                className: 'share-x',
            },
            {
                type: 'linkedin',
                label: 'Share on LinkedIn',
                href: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`,
                className: 'share-linkedin',
            },
            {
                type: 'facebook',
                label: 'Share on Facebook',
                href: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`,
                className: 'share-facebook',
            },
        ];
    }, [post, shareUrl]);

    const relatedPosts = useMemo(() => {
        if (!post) return [];
        const others = recentPosts.filter((item) => item.slug !== post.slug);
        const sameCategory = others.filter((item) => post.category && item.category === post.category);
        const rest = others.filter((item) => !post.category || item.category !== post.category);
        return [...sameCategory, ...rest].slice(0, 6);
    }, [recentPosts, post]);

    const renderedHtml = useMemo(
        () => (post?.content ? markdownToHtml(post.content) : ''),
        [post?.content]
    );

    const readingMinutes = useMemo(() => {
        const words = String(post?.content || '').replace(/<[^>]*>/g, ' ').trim().split(/\s+/).filter(Boolean).length;
        return Math.max(1, Math.ceil(words / 220));
    }, [post?.content]);

    if (loading) {
        return (
            <>
                <ModernNavigationHeader sticky user={user} onLogin={onLogin} onLogout={onLogout} onAdminClick={onAdminClick} />
                <main className="blog-post-state" aria-live="polite"><i aria-hidden /><p>Opening the journal…</p></main>
            </>
        );
    }

    if (error || !post) {
        return (
            <>
                <ModernNavigationHeader sticky user={user} onLogin={onLogin} onLogout={onLogout} onAdminClick={onAdminClick} />
                <main className="blog-post-state" role="alert">
                <div>
                    <p>Journal</p>
                    <h2>Post Not Found</h2>
                    <p>The blog post you're looking for doesn't exist.</p>
                    <Link to="/blog" className="back-link">← Back to Blog</Link>
                </div>
                </main>
            </>
        );
    }

    return (
        <>
            <div className="blog-post-page">
            <SEOHead
                title={`${post.title} | AstroRoshni Blog`}
                description={post.excerpt || post.content.substring(0, 160)}
                keywords={post.tags ? post.tags.join(', ') : 'vedic astrology, astrology blog'}
                canonical={`https://astroroshni.com/blog/${post.slug}/`}
                ogImage={post.featured_image || 'https://astroroshni.com/og-image.jpg'}
                themeColor="#210b17"
                structuredData={{
                    '@context': 'https://schema.org',
                    '@graph': [
                        {
                            '@type': 'BlogPosting',
                            headline: post.title,
                            description: post.excerpt || post.content.substring(0, 160),
                            ...(post.featured_image && { image: post.featured_image }),
                            datePublished: post.created_at,
                            dateModified: post.updated_at || post.created_at,
                            mainEntityOfPage: `https://astroroshni.com/blog/${post.slug}/`,
                            author: { '@type': 'Organization', name: 'AstroRoshni', url: SITE_ORIGIN },
                            publisher: {
                                '@type': 'Organization', name: 'AstroRoshni', url: SITE_ORIGIN,
                                logo: { '@type': 'ImageObject', url: 'https://astroroshni.com/logo.png' }
                            }
                        },
                        {
                            '@type': 'BreadcrumbList',
                            itemListElement: [
                                { '@type': 'ListItem', position: 1, name: 'Home', item: `${SITE_ORIGIN}/` },
                                { '@type': 'ListItem', position: 2, name: 'Journal', item: `${SITE_ORIGIN}/blog/` },
                                { '@type': 'ListItem', position: 3, name: post.title, item: `${SITE_ORIGIN}/blog/${post.slug}/` }
                            ]
                        }
                    ]
                }}
            />
            <ModernNavigationHeader sticky user={user} onLogin={onLogin} onLogout={onLogout} onAdminClick={onAdminClick} />
            <div className="blog-reading-progress" aria-hidden="true"><span style={{ width: `${readingProgress}%` }} /></div>
            <main className="blog-post-container">
            <div className="blog-post-layout">
            <article className="blog-post">
                <header className="post-header">
                    <Link to="/blog" className="back-link">← Back to Blog</Link>
                    
                    <div className="post-meta">
                        <time className="post-date" dateTime={post.created_at}>{formatDate(post.created_at)}</time>
                        {post.category && (
                            <Link to={`/blog?category=${encodeURIComponent(post.category)}`} className="post-category">
                                {post.category}
                            </Link>
                        )}
                        <span className="post-read-time">{readingMinutes} min read</span>
                    </div>
                    
                    <h1 className="post-title">{post.title}</h1>
                    
                    {post.excerpt && (
                        <p className="post-excerpt">{post.excerpt}</p>
                    )}
                    
                    {post.featured_image && (
                        <div className="post-featured-image">
                            <img src={post.featured_image} alt={post.title} />
                        </div>
                    )}
                </header>

                <div className="post-share-bar" aria-label="Share this article">
                    <span className="post-share-label">Share</span>
                    <div className="post-share-links">
                        {shareLinks.map((link) => (
                            <a
                                key={link.type}
                                href={link.href}
                                className={`post-share-btn ${link.className}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                aria-label={link.label}
                                title={link.label}
                            >
                                <ShareIcon type={link.type} />
                            </a>
                        ))}
                    </div>
                </div>

                <div className="post-content">
                    <div 
                        dangerouslySetInnerHTML={{ 
                            __html: renderedHtml
                        }}
                    />
                </div>

                {post.tags && post.tags.length > 0 && (
                    <footer className="post-footer">
                        <div className="post-tags">
                            <span className="tags-label">Tags:</span>
                            {post.tags.map(tag => (
                                <span key={tag} className="post-tag">
                                    {tag}
                                </span>
                            ))}
                        </div>
                    </footer>
                )}
            </article>

            <aside className="blog-post-sidebar" aria-label="Blog sidebar">
                <section className="blog-sidebar-widget">
                    <h2 className="blog-sidebar-title">Related Blog</h2>
                    {relatedPosts.length > 0 ? (
                        <ul className="blog-sidebar-list">
                            {relatedPosts.map((item) => (
                                <li key={item.id || item.slug}>
                                    <Link to={`/blog/${item.slug}`}>{item.title}</Link>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="blog-sidebar-empty">More posts coming soon.</p>
                    )}
                </section>

                <section className="blog-sidebar-widget">
                    <h2 className="blog-sidebar-title">Categories</h2>
                    {categories.length > 0 ? (
                        <ul className="blog-sidebar-list blog-sidebar-categories">
                            <li>
                                <Link to="/blog">All Posts</Link>
                            </li>
                            {categories.filter(Boolean).map((category) => (
                                <li key={category}>
                                    <Link to={`/blog?category=${encodeURIComponent(category)}`}>
                                        {category}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="blog-sidebar-empty">No categories yet.</p>
                    )}
                </section>

                <section className="blog-sidebar-widget blog-sidebar-share">
                    <h2 className="blog-sidebar-title">Share</h2>
                    <div className="post-share-links">
                        {shareLinks.map((link) => (
                            <a
                                key={`side-${link.type}`}
                                href={link.href}
                                className={`post-share-btn ${link.className}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                aria-label={link.label}
                                title={link.label}
                            >
                                <ShareIcon type={link.type} />
                            </a>
                        ))}
                    </div>
                </section>
            </aside>
            </div>

            <div className="post-navigation">
                <Link to="/blog" className="nav-button">
                    View All Posts
                </Link>
            </div>
            </main>
            </div>
        </>
    );
};

export default BlogPost;
