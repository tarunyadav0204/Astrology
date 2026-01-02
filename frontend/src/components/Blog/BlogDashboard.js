import React, { useState, useEffect } from 'react';
import axios from 'axios';
import BlogEditor from './BlogEditor';
import './BlogDashboard.css';

const BlogDashboard = () => {
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showEditor, setShowEditor] = useState(false);
    const [editingPost, setEditingPost] = useState(null);
    const [filter, setFilter] = useState('all');

    useEffect(() => {
        fetchPosts();
    }, []);

    const fetchPosts = async () => {
        try {
            const response = await axios.get('/api/blog/posts');
            setPosts(response.data);
        } catch (error) {
            console.error('Error fetching posts:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreatePost = () => {
        setEditingPost(null);
        setShowEditor(true);
    };

    const handleEditPost = (post) => {
        setEditingPost(post.id);
        setShowEditor(true);
    };

    const handleDeletePost = async (postId) => {
        if (!window.confirm('Are you sure you want to delete this post?')) return;
        
        try {
            await axios.delete(`/api/blog/posts/${postId}`);
            fetchPosts();
        } catch (error) {
            console.error('Error deleting post:', error);
            alert('Failed to delete post');
        }
    };

    const handleEditorSave = () => {
        setShowEditor(false);
        setEditingPost(null);
        fetchPosts();
    };

    const handleEditorCancel = () => {
        setShowEditor(false);
        setEditingPost(null);
    };

    const filteredPosts = posts.filter(post => {
        if (filter === 'all') return true;
        return post.status === filter;
    });

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    if (showEditor) {
        return (
            <BlogEditor
                postId={editingPost}
                onSave={handleEditorSave}
                onCancel={handleEditorCancel}
            />
        );
    }

    return (
        <div className="blog-dashboard">
            <div className="dashboard-header">
                <h1>Blog Management</h1>
                <button onClick={handleCreatePost} className="btn-create">
                    Create New Post
                </button>
            </div>

            <div className="dashboard-filters">
                <button 
                    className={filter === 'all' ? 'active' : ''}
                    onClick={() => setFilter('all')}
                >
                    All Posts ({posts.length})
                </button>
                <button 
                    className={filter === 'published' ? 'active' : ''}
                    onClick={() => setFilter('published')}
                >
                    Published ({posts.filter(p => p.status === 'published').length})
                </button>
                <button 
                    className={filter === 'draft' ? 'active' : ''}
                    onClick={() => setFilter('draft')}
                >
                    Drafts ({posts.filter(p => p.status === 'draft').length})
                </button>
            </div>

            {loading ? (
                <div className="loading">Loading posts...</div>
            ) : (
                <div className="posts-table">
                    {filteredPosts.length === 0 ? (
                        <div className="no-posts">
                            <p>No posts found. Create your first blog post!</p>
                        </div>
                    ) : (
                        <table>
                            <thead>
                                <tr>
                                    <th>Title</th>
                                    <th>Category</th>
                                    <th>Status</th>
                                    <th>Created</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredPosts.map(post => (
                                    <tr key={post.id}>
                                        <td>
                                            <div className="post-title">
                                                <strong>{post.title}</strong>
                                                {post.excerpt && (
                                                    <div className="post-excerpt">
                                                        {post.excerpt.substring(0, 100)}...
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td>
                                            <span className="category-tag">
                                                {post.category || 'Uncategorized'}
                                            </span>
                                        </td>
                                        <td>
                                            <span className={`status-badge ${post.status}`}>
                                                {post.status}
                                            </span>
                                        </td>
                                        <td>{formatDate(post.created_at)}</td>
                                        <td>
                                            <div className="post-actions">
                                                <button 
                                                    onClick={() => handleEditPost(post)}
                                                    className="btn-edit"
                                                >
                                                    Edit
                                                </button>
                                                <button 
                                                    onClick={() => handleDeletePost(post.id)}
                                                    className="btn-delete"
                                                >
                                                    Delete
                                                </button>
                                                {post.status === 'published' && (
                                                    <a 
                                                        href={`/blog/${post.slug}`}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="btn-view"
                                                    >
                                                        View
                                                    </a>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            )}
        </div>
    );
};

export default BlogDashboard;