import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { matchesQuery, SEARCH_DATA } from './SearchBar';
import './ModernSiteSearch.css';

const QUICK_LINKS = [
  ['/ai-kundli-generator', 'Create Kundli'],
  ['/chat?app=1', 'Ask Tara'],
  ['/panchang', 'Today’s Panchang'],
  ['/kundli-matching', 'Kundli Matching'],
  ['/horoscope/daily', 'Daily Horoscope'],
];

const ModernSiteSearch = ({ isOpen, onClose, user, onLogin }) => {
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);

  const results = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return [];
    return SEARCH_DATA
      .filter((item) => matchesQuery(item, normalized))
      .map((item, sourceIndex) => {
        const title = item.title.toLowerCase();
        const keywordStarts = item.keywords.some((keyword) => keyword.toLowerCase().startsWith(normalized));
        const score = title === normalized ? 5 : title.startsWith(normalized) ? 4 : title.includes(normalized) ? 3 : keywordStarts ? 2 : 1;
        return { item, score, sourceIndex };
      })
      .sort((a, b) => b.score - a.score || a.sourceIndex - b.sourceIndex)
      .slice(0, 8)
      .map(({ item }) => item);
  }, [query]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    setQuery('');
    setActiveIndex(0);
    const focusTimer = window.setTimeout(() => inputRef.current?.focus(), 40);
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') onClose?.();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      window.clearTimeout(focusTimer);
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  useEffect(() => { setActiveIndex(0); }, [query]);

  if (!isOpen) return null;

  const openResult = (result) => {
    if (!user && !result.public) {
      onClose?.();
      onLogin?.();
      return;
    }
    onClose?.();
    navigate(result.path);
  };

  const openQuickLink = (path) => {
    const result = SEARCH_DATA.find((item) => item.path === path) || { path, public: path !== '/chat?app=1' };
    openResult(result);
  };

  const handleInputKeyDown = (event) => {
    if (!results.length) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActiveIndex((index) => (index + 1) % results.length);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex((index) => (index - 1 + results.length) % results.length);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      openResult(results[activeIndex]);
    }
  };

  return createPortal(
    <div className="modern-search-overlay" role="presentation" onMouseDown={onClose}>
      <section className="modern-search-dialog" role="dialog" aria-modal="true" aria-labelledby="modern-search-title" onMouseDown={(event) => event.stopPropagation()}>
        <header className="modern-search-header">
          <div>
            <p>Explore AstroRoshni</p>
            <h2 id="modern-search-title">What are you looking for?</h2>
          </div>
          <button type="button" onClick={onClose} aria-label="Close search"><span aria-hidden>×</span></button>
        </header>

        <div className="modern-search-input-wrap">
          <svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="6.7"></circle><path d="m16 16 4.2 4.2"></path></svg>
          <input
            ref={inputRef}
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={handleInputKeyDown}
            placeholder="Search Kundli, career, Panchang, reports…"
            aria-label="Search AstroRoshni"
            aria-controls="modern-search-results"
            aria-activedescendant={results.length ? `modern-search-result-${activeIndex}` : undefined}
          />
          {query && <button type="button" onClick={() => setQuery('')} aria-label="Clear search">Clear</button>}
        </div>

        <div className="modern-search-content" id="modern-search-results" aria-live="polite">
          {!query.trim() ? (
            <div className="modern-search-quick">
              <span>Popular paths</span>
              <div>{QUICK_LINKS.map(([path, label]) => <button type="button" key={path} onClick={() => openQuickLink(path)}>{label}<i aria-hidden>↗</i></button>)}</div>
            </div>
          ) : results.length ? (
            <div className="modern-search-results" role="listbox" aria-label="Search results">
              <div className="modern-search-results__meta"><span>{results.length} result{results.length === 1 ? '' : 's'}</span><small>↑ ↓ to move · Enter to open</small></div>
              {results.map((result, index) => (
                <button
                  id={`modern-search-result-${index}`}
                  type="button"
                  role="option"
                  aria-selected={activeIndex === index}
                  className={activeIndex === index ? 'is-active' : ''}
                  key={`${result.path}-${result.title}`}
                  onMouseEnter={() => setActiveIndex(index)}
                  onClick={() => openResult(result)}
                >
                  <span>{String(index + 1).padStart(2, '0')}</span>
                  <strong>{result.title}</strong>
                  {!user && !result.public && <small>Sign in</small>}
                  <i aria-hidden>↗</i>
                </button>
              ))}
            </div>
          ) : (
            <div className="modern-search-empty"><span>NO MATCH</span><h3>Try a broader phrase.</h3><p>Search for a life area, astrology tool, report, or learning topic.</p></div>
          )}
        </div>

        <footer className="modern-search-footer"><span>Search all AstroRoshni pages</span><small>Esc to close</small></footer>
      </section>
    </div>,
    document.body
  );
};

export default ModernSiteSearch;
