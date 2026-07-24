/**
 * Shared Markdown → HTML for public blog posts and admin preview.
 * Block-aware: tables/lists/headings are not wrapped in <p> or split by <br>.
 */

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function youtubeEmbed(id) {
  return `<div class="youtube-embed"><iframe width="560" height="315" src="https://www.youtube.com/embed/${id}" title="YouTube video" frameborder="0" allowfullscreen></iframe></div>`;
}

function inlineFormat(text) {
  let html = escapeHtml(text);

  html = html.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, '<img src="$2" alt="$1" class="content-image" />');
  html = html.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

  html = html.replace(
    /https:\/\/(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)(?:[&?][^\s&]*)*/g,
    (_, id) => youtubeEmbed(id)
  );
  html = html.replace(
    /https:\/\/youtu\.be\/([a-zA-Z0-9_-]+)(?:[?][^\s]*)*/g,
    (_, id) => youtubeEmbed(id)
  );

  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
  // Italic with single * / _ — avoid matching across words carelessly
  html = html.replace(/(^|[^\w*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>');
  html = html.replace(/(^|[^\w_])_([^_\n]+)_(?!_)/g, '$1<em>$2</em>');

  return html;
}

function isTableSeparator(line) {
  const trimmed = line.trim();
  if (!trimmed.includes('|')) return false;
  const inner = trimmed.replace(/^\|/, '').replace(/\|$/, '');
  return /^[\s:\-|]+$/.test(inner);
}

function parseTableRow(line) {
  let row = line.trim();
  if (row.startsWith('|')) row = row.slice(1);
  if (row.endsWith('|')) row = row.slice(0, -1);
  return row.split('|').map((cell) => cell.trim());
}

function renderTable(rows) {
  if (!rows.length) return '';
  const body = rows
    .map((cells, index) => {
      const tag = index === 0 ? 'th' : 'td';
      return `<tr>${cells.map((cell) => `<${tag}>${inlineFormat(cell)}</${tag}>`).join('')}</tr>`;
    })
    .join('');
  return `<table>${body}</table>`;
}

function renderList(items, ordered) {
  const tag = ordered ? 'ol' : 'ul';
  return `<${tag}>${items.map((item) => `<li>${inlineFormat(item)}</li>`).join('')}</${tag}>`;
}

/**
 * Convert blog Markdown to HTML for article rendering / editor preview.
 */
export function markdownToHtml(content, { emptyMessage = '' } = {}) {
  if (!content || !String(content).trim()) {
    return emptyMessage || '';
  }

  let text = String(content).replace(/\\n/g, '\n').replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  text = text.replace(/\n{3,}/g, '\n\n').trim();

  const lines = text.split('\n');
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const trimmed = lines[i].trim();

    if (!trimmed) {
      i += 1;
      continue;
    }

    // Table: header + separator + body rows
    if (trimmed.includes('|') && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      const rows = [parseTableRow(trimmed)];
      i += 2;
      while (i < lines.length && lines[i].trim().includes('|') && !isTableSeparator(lines[i])) {
        rows.push(parseTableRow(lines[i]));
        i += 1;
      }
      blocks.push(renderTable(rows));
      continue;
    }

    const heading = /^(#{1,4})\s+(.+)$/.exec(trimmed);
    if (heading) {
      const level = Math.min(heading[1].length + 1, 4); // # → h2 …
      blocks.push(`<h${level}>${inlineFormat(heading[2].trim())}</h${level}>`);
      i += 1;
      continue;
    }

    if (/^[-*+]\s+/.test(trimmed)) {
      const items = [];
      while (i < lines.length && /^[-*+]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*+]\s+/, ''));
        i += 1;
      }
      blocks.push(renderList(items, false));
      continue;
    }

    if (/^\d+\.\s+/.test(trimmed)) {
      const items = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+\.\s+/, ''));
        i += 1;
      }
      blocks.push(renderList(items, true));
      continue;
    }

    const paraLines = [];
    while (i < lines.length) {
      const t = lines[i].trim();
      if (!t) break;
      if (/^#{1,4}\s+/.test(t)) break;
      if (/^[-*+]\s+/.test(t)) break;
      if (/^\d+\.\s+/.test(t)) break;
      if (t.includes('|') && i + 1 < lines.length && isTableSeparator(lines[i + 1])) break;
      paraLines.push(t);
      i += 1;
    }

    const html = inlineFormat(paraLines.join(' '));
    // If paragraph is only an embed, don't wrap in <p>
    if (/^<div class="youtube-embed">[\s\S]*<\/div>$/.test(html.trim())) {
      blocks.push(html.trim());
    } else {
      blocks.push(`<p>${html}</p>`);
    }
  }

  return blocks.join('');
}

export default markdownToHtml;
