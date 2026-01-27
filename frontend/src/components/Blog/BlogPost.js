import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import NavigationHeader from '../Shared/NavigationHeader';
import SEOHead from '../SEO/SEOHead';
import './BlogPost.css';

const BlogPost = () => {
    const { slug } = useParams();
    const [post, setPost] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchPost();
    }, [slug]);

    const fetchPost = async () => {
        try {
            const response = await axios.get(`/api/blog/posts/slug/${slug}`);
            setPost(response.data);
        } catch (error) {
            console.error('Error fetching post:', error);
            setError('Post not found');
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    const renderContent = (content) => {
        if (!content) return '';
        
        // First, convert literal \n to actual newlines
        let processedContent = content.replace(/\\n/g, '\n');
        
        let html = processedContent
            // Headers - start from H2 since post title is H1
            .replace(/^### (.*$)/gim, '<h4>$1</h4>')
            .replace(/^## (.*$)/gim, '<h3>$1</h3>')
            .replace(/^# (.*$)/gim, '<h2>$1</h2>')
            // YouTube embeds - handle markdown image format and plain URLs
            .replace(/\[!\[[^\]]*\]\(https:\/\/(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)(?:[&?][^\s]*)*\)\]/g, 
                '<div class="youtube-embed"><iframe width="560" height="315" src="https://www.youtube.com/embed/$1" frameborder="0" allowfullscreen></iframe></div>')
            .replace(/\[!\[[^\]]*\]\(https:\/\/youtu\.be\/([a-zA-Z0-9_-]+)(?:[?][^\s]*)*\)\]/g, 
                '<div class="youtube-embed"><iframe width="560" height="315" src="https://www.youtube.com/embed/$1" frameborder="0" allowfullscreen></iframe></div>')
            .replace(/https:\/\/(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)(?:[&?][^\s]*)*/g, 
                '<div class="youtube-embed"><iframe width="560" height="315" src="https://www.youtube.com/embed/$1" frameborder="0" allowfullscreen></iframe></div>')
            .replace(/https:\/\/youtu\.be\/([a-zA-Z0-9_-]+)(?:[?][^\s]*)*/g, 
                '<div class="youtube-embed"><iframe width="560" height="315" src="https://www.youtube.com/embed/$1" frameborder="0" allowfullscreen></iframe></div>')
            // Tables
            .replace(/\|(.+)\|/g, (match, content) => {
                // Skip separator rows (containing only dashes and pipes)
                if (content.match(/^[\s\-\|]+$/)) return '';
                const cells = content.split('|').map(cell => cell.trim());
                return '<tr>' + cells.map(cell => `<td>${cell}</td>`).join('') + '</tr>';
            })
            .replace(/(<tr>.*<\/tr>)/gs, '<table>$1</table>')
            // Bold and italic
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Links and images - handle edge cases
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
            .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="content-image" />')
            .replace(/!\[([^\]]*)\]\(\s*\)/g, '') // Remove images with empty URLs
            .replace(/!Image/g, '') // Remove standalone !Image text
            // Lists
            .replace(/^- (.+)$/gm, '<li>$1</li>')
            .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
            // Convert double newlines to paragraph breaks
            .replace(/\n\n/g, '</p><p>')
            // Convert single newlines to line breaks
            .replace(/\n/g, '<br>');
            
        // Clean up and wrap in paragraphs
        html = `<p>${html}</p>`;
        
        // Remove excessive spacing before tables - more aggressive approach
        html = html
            .replace(/<\/p><p><table/g, '</p><table')
            .replace(/<\/table><\/p><p>/g, '</table><p>')
            .replace(/<p>(<br>\s*)*<table/g, '<table')
            .replace(/(<br>\s*)*<table/g, '<table')
            .replace(/<p><\/p><table/g, '<table')
            .replace(/(<br>){2,}/g, '<br>');
            
        return html;
    };

    if (loading) {
        return (
            <>
                <NavigationHeader compact={true} />
                <div className="blog-post-container" style={{paddingTop: '80px'}}>
                <div className="loading">Loading post...</div>
            </div>
        </>
        );
    }

    if (error || !post) {
        return (
            <>
                <NavigationHeader compact={true} />
                <div className="blog-post-container" style={{paddingTop: '80px'}}>
                <div className="error">
                    <h2>Post Not Found</h2>
                    <p>The blog post you're looking for doesn't exist.</p>
                    <Link to="/blog" className="back-link">← Back to Blog</Link>
                </div>
            </div>
        </>
        );
    }

    return (
        <>
            <SEOHead 
                title={`${post.title} | AstroRoshni Blog`}
                description={post.excerpt || post.content.substring(0, 160)}
                keywords={post.tags ? post.tags.join(', ') : 'vedic astrology, astrology blog'}
                canonical={`https://astroroshni.com/blog/${post.slug}`}
                ogImage={post.featured_image || 'https://astroroshni.com/og-image.jpg'}
                structuredData={{
                    "@context": "https://schema.org",
                    "@type": "BlogPosting",
                    "headline": post.title,
                    "description": post.excerpt,
                    "image": post.featured_image,
                    "datePublished": post.created_at,
                    "dateModified": post.updated_at,
                    "author": {
                        "@type": "Organization",
                        "name": "AstroRoshni"
                    },
                    "publisher": {
                        "@type": "Organization",
                        "name": "AstroRoshni",
                        "logo": {
                            "@type": "ImageObject",
                            "url": "https://astroroshni.com/logo.png"
                        }
                    }
                }}
            />
            <NavigationHeader compact={true} />
            <div className="blog-post-container" style={{paddingTop: '80px'}}>
            <article className="blog-post">
                <header className="post-header">
                    <Link to="/blog" className="back-link">← Back to Blog</Link>
                    
                    <div className="post-meta">
                        <time className="post-date">{formatDate(post.created_at)}</time>
                        {post.category && (
                            <span className="post-category">{post.category}</span>
                        )}
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

                <div className="post-content">
                    <div 
                        dangerouslySetInnerHTML={{ 
                            __html: renderContent(post.content)
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

            <div className="post-navigation">
                <Link to="/blog" className="nav-button">
                    View All Posts
                </Link>
            </div>
            </div>
        </>
    );
};

export default BlogPost;