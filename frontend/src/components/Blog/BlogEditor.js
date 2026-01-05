import React, { useState, useEffect } from 'react';
import axios from 'axios';
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
            // Convert tags array to comma-separated string for editing
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
            // Auto-generate slug from title if slug is empty
            const autoSlug = value.toLowerCase()
                .replace(/[^\w\s-]/g, '')
                .replace(/[-\s]+/g, '-')
                .trim('-');
            setPost(prev => ({ ...prev, [name]: value, slug: autoSlug }));
        } else {
            setPost(prev => ({ ...prev, [name]: value }));
        }
    };

    const handleImageUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setImageUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('alt_text', imageAltText.trim() || 'Image');

        try {
            const response = await axios.post('/api/blog/upload-image', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            
            const imageUrl = response.data.url;
            setPost(prev => ({ ...prev, featured_image: imageUrl }));
            
            // Insert image into content at cursor position with alt text
            const textarea = document.getElementById('content-editor');
            const cursorPos = textarea.selectionStart;
            const textBefore = post.content.substring(0, cursorPos);
            const textAfter = post.content.substring(cursorPos);
            const altText = imageAltText.trim() || 'Image';
            const imageMarkdown = `\n![${altText}](${imageUrl})\n`;
            
            setPost(prev => ({
                ...prev,
                content: textBefore + imageMarkdown + textAfter
            }));
            
            // Clear alt text after successful upload
            setImageAltText('');
        } catch (error) {
            console.error('Error uploading image:', error);
            alert('Failed to upload image');
        } finally {
            setImageUploading(false);
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
                    <label>Image Upload</label>
                    <div className="image-upload">
                        <div className="alt-text-input">
                            <input
                                type="text"
                                value={imageAltText}
                                onChange={(e) => setImageAltText(e.target.value)}
                                placeholder="Enter alt text for the image (optional)"
                                className="alt-text-field"
                            />
                        </div>
                        <input
                            type="file"
                            accept="image/*"
                            onChange={handleImageUpload}
                            disabled={imageUploading}
                        />
                        {imageUploading && <span>Uploading...</span>}
                        {post.featured_image && (
                            <img src={post.featured_image} alt="Featured" className="featured-preview" />
                        )}
                        <small className="help-text">
                            Enter descriptive alt text for better accessibility and SEO (optional).
                        </small>
                    </div>
                </div>

                <div className="form-group">
                    <label>Content</label>
                    <textarea
                        id="content-editor"
                        name="content"
                        value={post.content}
                        onChange={handleInputChange}
                        placeholder="Write your blog post content here. You can use Markdown formatting."
                        rows="20"
                        className="content-editor"
                    />
                    <div className="editor-help">
                        <small>
                            Markdown supported: **bold**, *italic*, [link](url), ![image](url)
                        </small>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BlogEditor;