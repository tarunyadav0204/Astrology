import React, { useCallback, useMemo, useRef, useState } from 'react';
import { markdownToHtml } from '../../utils/blogMarkdown';

function wrapSelection(value, start, end, before, after = before) {
  const selected = value.slice(start, end) || 'text';
  const next = value.slice(0, start) + before + selected + after + value.slice(end);
  return {
    value: next,
    selectionStart: start + before.length,
    selectionEnd: start + before.length + selected.length,
  };
}

function prefixLines(value, start, end, prefix) {
  const lineStart = value.lastIndexOf('\n', start - 1) + 1;
  const lineEnd = (() => {
    const idx = value.indexOf('\n', end);
    return idx === -1 ? value.length : idx;
  })();
  const block = value.slice(lineStart, lineEnd);
  const nextBlock = block
    .split('\n')
    .map((line) => (line.startsWith(prefix) ? line : `${prefix}${line || ''}`))
    .join('\n');
  const next = value.slice(0, lineStart) + nextBlock + value.slice(lineEnd);
  return {
    value: next,
    selectionStart: lineStart,
    selectionEnd: lineStart + nextBlock.length,
  };
}

const TOOLBAR = [
  { id: 'h2', label: 'H2', title: 'Heading 2', run: (v, s, e) => prefixLines(v, s, e, '## ') },
  { id: 'h3', label: 'H3', title: 'Heading 3', run: (v, s, e) => prefixLines(v, s, e, '### ') },
  { id: 'bold', label: 'B', title: 'Bold', run: (v, s, e) => wrapSelection(v, s, e, '**') },
  { id: 'italic', label: 'I', title: 'Italic', run: (v, s, e) => wrapSelection(v, s, e, '*') },
  { id: 'ul', label: '• List', title: 'Bullet list', run: (v, s, e) => prefixLines(v, s, e, '- ') },
  { id: 'ol', label: '1. List', title: 'Numbered list', run: (v, s, e) => prefixLines(v, s, e, '1. ') },
  {
    id: 'quote',
    label: '“ ”',
    title: 'Quote',
    run: (v, s, e) => prefixLines(v, s, e, '> '),
  },
  {
    id: 'link',
    label: 'Link',
    title: 'Insert link',
    run: (v, s, e) => {
      const selected = v.slice(s, e) || 'link text';
      const before = '[';
      const after = '](https://)';
      const next = v.slice(0, s) + before + selected + after + v.slice(e);
      return {
        value: next,
        selectionStart: s + before.length + selected.length + 2,
        selectionEnd: s + before.length + selected.length + after.length - 1,
      };
    },
  },
  {
    id: 'image',
    label: 'Image',
    title: 'Insert image URL',
    run: (v, s, e) => {
      const selected = v.slice(s, e) || 'Image';
      const snippet = `![${selected}](https://)`;
      const next = v.slice(0, s) + snippet + v.slice(e);
      const urlStart = s + selected.length + 4;
      return {
        value: next,
        selectionStart: urlStart,
        selectionEnd: urlStart + 'https://'.length,
      };
    },
  },
];

/**
 * Markdown editor with formatting toolbar + live preview.
 * Keeps Markdown string output for existing blog storage/render path.
 */
const BlogMarkdownEditor = ({
  value = '',
  onChange,
  onUploadImage,
  imageUploading = false,
  placeholder = 'Write your blog post…',
}) => {
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const [mode, setMode] = useState('split'); // write | split | preview

  const previewHtml = useMemo(
    () => markdownToHtml(value, { emptyMessage: '<p class="md-preview-empty">Nothing to preview yet. Start writing on the left.</p>' }),
    [value]
  );

  const applyEdit = useCallback((result) => {
    onChange(result.value);
    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (!el) return;
      el.focus();
      el.setSelectionRange(result.selectionStart, result.selectionEnd);
    });
  }, [onChange]);

  const runToolbar = (item) => {
    const el = textareaRef.current;
    if (!el) return;
    applyEdit(item.run(value, el.selectionStart, el.selectionEnd));
  };

  const insertAtCursor = (snippet) => {
    const el = textareaRef.current;
    const start = el ? el.selectionStart : value.length;
    const end = el ? el.selectionEnd : value.length;
    const next = `${value.slice(0, start)}${snippet}${value.slice(end)}`;
    onChange(next);
    requestAnimationFrame(() => {
      if (!el) return;
      const pos = start + snippet.length;
      el.focus();
      el.setSelectionRange(pos, pos);
    });
  };

  const handleUploadClick = () => {
    if (!onUploadImage || imageUploading) return;
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file || !onUploadImage) return;
    const url = await onUploadImage(file);
    if (!url) return;
    insertAtCursor(`\n![Image](${url})\n`);
  };

  return (
    <div className={`blog-md-editor blog-md-editor--${mode}`}>
      <div className="blog-md-toolbar">
        <div className="blog-md-toolbar-group" role="toolbar" aria-label="Formatting">
          {TOOLBAR.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`blog-md-tool${item.id === 'bold' ? ' blog-md-tool--bold' : ''}${item.id === 'italic' ? ' blog-md-tool--italic' : ''}`}
              title={item.title}
              onClick={() => runToolbar(item)}
            >
              {item.label}
            </button>
          ))}
          {onUploadImage && (
            <button
              type="button"
              className="blog-md-tool blog-md-tool--upload"
              title="Upload & insert image"
              onClick={handleUploadClick}
              disabled={imageUploading}
            >
              {imageUploading ? 'Uploading…' : 'Upload image'}
            </button>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="blog-md-file-input"
            onChange={handleFileChange}
          />
        </div>
        <div className="blog-md-mode-toggle" role="group" aria-label="Editor view">
          <button type="button" className={mode === 'write' ? 'active' : ''} onClick={() => setMode('write')}>Write</button>
          <button type="button" className={mode === 'split' ? 'active' : ''} onClick={() => setMode('split')}>Split</button>
          <button type="button" className={mode === 'preview' ? 'active' : ''} onClick={() => setMode('preview')}>Preview</button>
        </div>
      </div>

      <div className="blog-md-panes">
        {mode !== 'preview' && (
          <div className="blog-md-write">
            <textarea
              ref={textareaRef}
              id="content-editor"
              className="blog-md-textarea"
              value={value}
              onChange={(e) => onChange(e.target.value)}
              placeholder={placeholder}
              spellCheck
            />
          </div>
        )}
        {mode !== 'write' && (
          <div className="blog-md-preview post-content">
            <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
          </div>
        )}
      </div>
    </div>
  );
};

export default BlogMarkdownEditor;
