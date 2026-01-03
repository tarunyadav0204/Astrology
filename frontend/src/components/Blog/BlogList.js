import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import './BlogList.css';

const BlogList = () => {
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState('');

    useEffect(() => {
        fetchPosts();
        fetchCategories();
    }, [selectedCategory]);

    const fetchPosts = async () => {
        try {
            const params = {
                status: 'published',
                ...(selectedCategory && { category: selectedCategory })
            };
            const response = await axios.get('/api/blog/posts', { params });
            setPosts(response.data);
        } catch (error) {
            console.error('Error fetching posts:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchCategories = async () => {
        try {
            const response = await axios.get('/api/blog/categories');
            setCategories(Array.isArray(response.data) ? response.data : []);
        } catch (error) {
            console.error('Error fetching categories:', error);
            setCategories([]); // Set empty array on error
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    const truncateText = (text, maxLength = 150) => {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    };

    if (loading) {
        return (
            <div className="blog-list-container">
                <div className="loading">Loading blog posts...</div>
            </div>
        );
    }

    return (
        <div className="blog-list-container">
            <div className="blog-header">
                <h1>AstroRoshni Blog</h1>
                <p>Discover the wisdom of Vedic astrology and cosmic insights</p>
            </div>

            <div className="blog-filters">
                <button 
                    className={selectedCategory === '' ? 'active' : ''}
                    onClick={() => setSelectedCategory('')}
                >
                    All Posts
                </button>
                {Array.isArray(categories) && categories.map(category => (
                    <button
                        key={category}
                        className={selectedCategory === category ? 'active' : ''}
                        onClick={() => setSelectedCategory(category)}
                    >
                        {category}
                    </button>
                ))}
            </div>

            {posts.length === 0 ? (
                <div className="no-posts">
                    <h3>No posts found</h3>
                    <p>Check back soon for new astrological insights!</p>
                </div>
            ) : (
                <div className="blog-grid">
                    {posts.map(post => (
                        <article key={post.id} className="blog-card">
                            {post.featured_image && (
                                <div className="blog-card-image">
                                    <img src={post.featured_image} alt={post.title} />
                                </div>
                            )}
                            <div className="blog-card-content">
                                <div className="blog-card-meta">
                                    <span className="blog-date">{formatDate(post.created_at)}</span>
                                    {post.category && (
                                        <span className="blog-category">{post.category}</span>
                                    )}
                                </div>
                                <h2 className="blog-card-title">
                                    <Link to={`/blog/${post.slug}`}>{post.title}</Link>
                                </h2>
                                <p className="blog-card-excerpt">
                                    {post.excerpt || post.content.replace(/[#*\[\]()]/g, '').substring(0, 150) + '...'}
                                </p>
                                <div className="blog-card-footer">
                                    <Link to={`/blog/${post.slug}`} className="read-more">
                                        Read More →
                                    </Link>
                                    {post.tags && post.tags.length > 0 && (
                                        <div className="blog-tags">
                                            {post.tags.slice(0, 3).map(tag => (
                                                <span key={tag} className="blog-tag">
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </article>
                    ))}
                </div>
            )}
        </div>
    );
};

export default BlogList;