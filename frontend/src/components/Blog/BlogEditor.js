import React, { useState, useEffect } from 'react';
import axios from 'axios';
import BlogMarkdownEditor from './BlogMarkdownEditor';
import './BlogEditor.css';

const BlogEditor = ({ postId, onSave, onCancel }) => {
    const [post, setPost] = useState({
        title: '',
        slug: '',
        content: '',
        excerpt: '',
        category: '',
        tags: '',
        meta_description: '',
        featured_image: '',
        status: 'draft'
    });
    const [loading, setLoading] = useState(false);
    const [imageUploading, setImageUploading] = useState(false);
    const [featuredUploading, setFeaturedUploading] = useState(false);
    const [imageAltText, setImageAltText] = useState('');

    useEffect(() => {
        if (postId) {
            fetchPost();
        }
    }, [postId]);

    const fetchPost = async () => {
        try {
            const response = await axios.get(`/api/blog/posts/${postId}`);
            const postData = response.data;
            setPost({
                ...postData,
                tags: Array.isArray(postData.tags) ? postData.tags.join(', ') : postData.tags || ''
            });
        } catch (error) {
            console.error('Error fetching post:', error);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        if (name === 'title' && !post.slug) {
            const autoSlug = value.toLowerCase()
                .replace(/[^\w\s-]/g, '')
                .replace(/[-\s]+/g, '-')
                .trim('-');
            setPost(prev => ({ ...prev, [name]: value, slug: autoSlug }));
        } else {
            setPost(prev => ({ ...prev, [name]: value }));
        }
    };

    const uploadImageFile = async (file, altText = 'Image') => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('alt_text', altText);
        const response = await axios.post('/api/blog/upload-image', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data.url;
    };

    const handleContentImageUpload = async (file) => {
        setImageUploading(true);
        try {
            return await uploadImageFile(file, imageAltText.trim() || 'Image');
        } catch (error) {
            console.error('Error uploading image:', error);
            alert('Failed to upload image');
            return null;
        } finally {
            setImageUploading(false);
        }
    };

    const handleFeaturedImageUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setFeaturedUploading(true);
        try {
            const imageUrl = await uploadImageFile(file, imageAltText.trim() || 'Featured image');
            setPost(prev => ({ ...prev, featured_image: imageUrl }));
            setImageAltText('');
        } catch (error) {
            console.error('Error uploading featured image:', error);
            alert('Failed to upload featured image');
        } finally {
            setFeaturedUploading(false);
        }
    };

    const handleSave = async () => {
        setLoading(true);
        try {
            const postData = {
                ...post,
                tags: typeof post.tags === 'string'
                    ? post.tags.split(',').map(tag => tag.trim()).filter(tag => tag)
                    : post.tags || []
            };

            if (postId) {
                await axios.put(`/api/blog/posts/${postId}`, postData);
            } else {
                await axios.post('/api/blog/posts', postData);
            }

            onSave && onSave();
        } catch (error) {
            console.error('Error saving post:', error);
            alert('Failed to save post');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="blog-editor">
            <div className="editor-header">
                <h2>{postId ? 'Edit Post' : 'Create New Post'}</h2>
                <div className="editor-actions">
                    <button onClick={onCancel} className="btn-cancel">Cancel</button>
                    <button onClick={handleSave} disabled={loading} className="btn-save">
                        {loading ? 'Saving...' : 'Save'}
                    </button>
                </div>
            </div>

            <div className="editor-form">
                <div className="form-group">
                    <label>Title</label>
                    <input
                        type="text"
                        name="title"
                        value={post.title}
                        onChange={handleInputChange}
                        placeholder="Enter post title"
                    />
                </div>

                <div className="form-group">
                    <label>URL Slug</label>
                    <input
                        type="text"
                        name="slug"
                        value={post.slug}
                        onChange={handleInputChange}
                        placeholder="url-friendly-slug"
                    />
                    <small className="help-text">
                        URL will be: /blog/{post.slug || 'your-slug-here'}
                    </small>
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label>Category</label>
                        <input
                            type="text"
                            name="category"
                            value={post.category}
                            onChange={handleInputChange}
                            placeholder="e.g., Vedic Astrology"
                        />
                    </div>
                    <div className="form-group">
                        <label>Status</label>
                        <select name="status" value={post.status} onChange={handleInputChange}>
                            <option value="draft">Draft</option>
                            <option value="published">Published</option>
                        </select>
                    </div>
                </div>

                <div className="form-group">
                    <label>Tags (comma separated)</label>
                    <input
                        type="text"
                        name="tags"
                        value={post.tags}
                        onChange={handleInputChange}
                        placeholder="astrology, horoscope, predictions"
                    />
                </div>

                <div className="form-group">
                    <label>Excerpt</label>
                    <textarea
                        name="excerpt"
                        value={post.excerpt}
                        onChange={handleInputChange}
                        placeholder="Brief description of the post"
                        rows="3"
                    />
                </div>

                <div className="form-group">
                    <label>Meta Description (SEO)</label>
                    <textarea
                        name="meta_description"
                        value={post.meta_description}
                        onChange={handleInputChange}
                        placeholder="SEO description for search engines"
                        rows="2"
                    />
                </div>

                <div className="form-group">
                    <label>Featured Image</label>
                    <div className="image-upload">
                        <div className="alt-text-input">
                            <input
                                type="text"
                                value={imageAltText}
                                onChange={(e) => setImageAltText(e.target.value)}
                                placeholder="Alt text for uploaded images (optional)"
                                className="alt-text-field"
                            />
                        </div>
                        <input
                            type="file"
                            accept="image/*"
                            onChange={handleFeaturedImageUpload}
                            disabled={featuredUploading}
                        />
                        {featuredUploading && <span>Uploading featured image...</span>}
                        {post.featured_image && (
                            <img src={post.featured_image} alt="Featured" className="featured-preview" />
                        )}
                        <small className="help-text">
                            Cover image for the post card and social share preview. Use the content editor toolbar to insert inline images.
                        </small>
                    </div>
                </div>

                <div className="form-group">
                    <label>Content</label>
                    <BlogMarkdownEditor
                        value={post.content}
                        onChange={(content) => setPost((prev) => ({ ...prev, content }))}
                        onUploadImage={handleContentImageUpload}
                        imageUploading={imageUploading}
                        placeholder="Write your blog post. Use the toolbar for headings, lists, links, and images."
                    />
                </div>
            </div>
        </div>
    );
};

export default BlogEditor;
