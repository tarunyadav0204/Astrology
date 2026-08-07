import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../../services/apiService';
import './KpTodayHome.css';

const CACHE_PREFIX = 'kp_today_home_web_v1:';
const MAX_PAGES = 5;
const BULLETS_PER_PAGE = 4;

const TONE_LABELS = {
  supportive: 'Favourable',
  mixed: 'Mixed',
  challenging: 'Under pressure',
  neutral: 'Steady',
};

function formatLocalDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function formatLocalTime(d) {
  const h = String(d.getHours()).padStart(2, '0');
  const m = String(d.getMinutes()).padStart(2, '0');
  return `${h}:${m}`;
}

function formatShortDate(d) {
  try {
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  } catch (_) {
    return formatLocalDate(d);
  }
}

function birthId(birthDetails) {
  return birthDetails?.id || birthDetails?.birth_chart_id || birthDetails?.name || 'anon';
}

function cacheKey(birthDetails) {
  return `${CACHE_PREFIX}${birthId(birthDetails)}:${formatLocalDate(new Date())}`;
}

function isTechnicalLabel(label) {
  const s = String(label || '').trim();
  if (!s) return true;
  return /combined activated|life themes|fructif|significat|house\s*\d+/i.test(s);
}

function humanHeadline(selfTheme, quiet) {
  if (quiet) return 'A quieter day';
  const label = String(selfTheme?.label || '').trim();
  if (label && !isTechnicalLabel(label)) return label;
  const summary = String(selfTheme?.summary || '').trim();
  if (summary) {
    const first = summary.split(/[.!?]/)[0].trim();
    if (first.length >= 12 && first.length <= 72) return first;
    if (summary.length <= 72) return summary;
    return `${summary.slice(0, 69).trim()}…`;
  }
  return 'Your day is ready';
}

function buildReaderPages(todayBlock) {
  const houses = todayBlock?.houses_giving_results || [];
  const selfTheme = (todayBlock?.manifestations || []).find(
    (item) => (item.subject || 'self') === 'self'
  );
  const tone = selfTheme?.outcome_tone || houses[0]?.tone || 'neutral';
  const summary = String(selfTheme?.summary || '').trim();
  const possibilities = Array.isArray(selfTheme?.possibilities)
    ? selfTheme.possibilities.map((p) => String(p || '').trim()).filter(Boolean)
    : [];
  const quiet = !houses.length;
  const headline = humanHeadline(selfTheme, quiet);

  if (quiet) {
    return {
      quiet: true,
      tone: 'neutral',
      headline,
      teaser: 'Not much is lined up to give clear results today. You can still check finer timing in Activations.',
      pages: [
        {
          id: 'quiet',
          showSummary: true,
          summary:
            'Today looks quieter for clear, fructifying results. That can change through the day as ruling planets and fine dashas shift.',
          bullets: [
            'Check back later, or open Activations for sharper hour-level timing.',
            'A quiet day does not mean nothing happens — only that fewer houses are strongly confirmed right now.',
          ],
        },
      ],
    };
  }

  let bullets = [...possibilities];
  if (!bullets.length && summary) bullets = [summary];
  if (!bullets.length) {
    bullets = ['Several life themes look able to move today. Open Activations for timing detail.'];
  }

  const capped = bullets.slice(0, MAX_PAGES * BULLETS_PER_PAGE);
  const pages = [];
  for (let i = 0; i < capped.length && pages.length < MAX_PAGES; i += BULLETS_PER_PAGE) {
    pages.push({
      id: `page-${pages.length}`,
      showSummary: pages.length === 0 && !!summary,
      summary,
      bullets: capped.slice(i, i + BULLETS_PER_PAGE),
    });
  }

  return {
    quiet: false,
    tone,
    headline,
    teaser: summary || bullets[0] || 'Your predictions for today are ready.',
    pages,
  };
}

function KpTodayReaderModal({ open, reader, loading, onClose, onOpenFull }) {
  const [pageIndex, setPageIndex] = useState(0);
  const [animKey, setAnimKey] = useState(0);
  const dialogRef = useRef(null);
  const pages = reader?.pages || [];
  const tone = reader?.tone || 'neutral';

  useEffect(() => {
    if (open) {
      setPageIndex(0);
      setAnimKey((k) => k + 1);
    }
  }, [open, reader?.headline]);

  useEffect(() => {
    if (!open) return undefined;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
      if (e.key === 'ArrowRight' && pageIndex < pages.length - 1) {
        setPageIndex((i) => i + 1);
        setAnimKey((k) => k + 1);
      }
      if (e.key === 'ArrowLeft' && pageIndex > 0) {
        setPageIndex((i) => i - 1);
        setAnimKey((k) => k + 1);
      }
    };
    window.addEventListener('keydown', onKey);
    dialogRef.current?.focus?.();
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener('keydown', onKey);
    };
  }, [open, onClose, pageIndex, pages.length]);

  if (!open) return null;

  const page = pages[pageIndex] || pages[0];
  const go = (next) => {
    const clamped = Math.max(0, Math.min(pages.length - 1, next));
    if (clamped === pageIndex) return;
    setPageIndex(clamped);
    setAnimKey((k) => k + 1);
  };

  return createPortal(
    <div className="kp-today-modal" role="presentation" onClick={onClose}>
      <div
        className={`kp-today-dialog kp-today-dialog--${tone}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="kp-today-dialog-title"
        tabIndex={-1}
        ref={dialogRef}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="kp-today-dialog__top">
          <div className="kp-today-dialog__meta">
            <span className="kp-today-dialog__eyebrow">Today · {formatShortDate(new Date())}</span>
            <h2 id="kp-today-dialog-title" className="kp-today-dialog__title">
              {reader?.headline || 'Your day is ready'}
            </h2>
          </div>
          <span className={`kp-today-tone kp-today-tone--${tone}`}>
            {TONE_LABELS[tone] || 'Steady'}
          </span>
          <button type="button" className="kp-today-dialog__close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="kp-today-dialog__body">
          {loading && !pages.length ? (
            <div className="kp-today-dialog__loading">
              <div className="kp-today-spinner" aria-hidden="true" />
              <p>Writing today’s predictions…</p>
            </div>
          ) : (
            <div key={animKey} className="kp-today-page">
              {page?.showSummary && page?.summary ? (
                <p className="kp-today-page__summary">{page.summary}</p>
              ) : null}
              <p className="kp-today-page__label">What may unfold</p>
              <ul className="kp-today-page__bullets">
                {(page?.bullets || []).map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
              {pages.length > 1 ? (
                <p className="kp-today-page__count">
                  {pageIndex + 1} of {pages.length}
                </p>
              ) : null}
            </div>
          )}
        </div>

        {pages.length > 1 ? (
          <div className="kp-today-nav">
            <button
              type="button"
              className="kp-today-nav__btn"
              onClick={() => go(pageIndex - 1)}
              disabled={pageIndex === 0}
              aria-label="Previous"
            >
              ←
            </button>
            <div className="kp-today-dots" role="tablist" aria-label="Prediction pages">
              {pages.map((p, i) => (
                <button
                  key={p.id}
                  type="button"
                  className={`kp-today-dot${i === pageIndex ? ' is-active' : ''}`}
                  aria-label={`Page ${i + 1}`}
                  aria-current={i === pageIndex ? 'true' : undefined}
                  onClick={() => go(i)}
                />
              ))}
            </div>
            <button
              type="button"
              className="kp-today-nav__btn"
              onClick={() => go(pageIndex + 1)}
              disabled={pageIndex >= pages.length - 1}
              aria-label="Next"
            >
              →
            </button>
          </div>
        ) : null}

        <div className="kp-today-dialog__footer">
          <button type="button" className="kp-today-dialog__cta" onClick={onOpenFull}>
            Open full timing
            <span aria-hidden="true">→</span>
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}

/**
 * Homepage daily KP predictions — teaser card + centered reader (not a swipe carousel).
 */
export default function KpTodayHome({ user, birthData, onLogin, onNeedBirth }) {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(false);
  const requestIdRef = useRef(0);
  const hasDataRef = useRef(false);
  const birthDetailsRef = useRef(birthData);
  birthDetailsRef.current = birthData;

  const birthKey = useMemo(() => {
    if (!birthData) return '';
    return [
      birthId(birthData),
      String(birthData.date || ''),
      String(birthData.time || ''),
      String(birthData.latitude ?? ''),
      String(birthData.longitude ?? ''),
    ].join('|');
  }, [
    birthData?.id,
    birthData?.birth_chart_id,
    birthData?.name,
    birthData?.date,
    birthData?.time,
    birthData?.latitude,
    birthData?.longitude,
  ]);

  const load = useCallback(async () => {
    const details = birthDetailsRef.current;
    if (!details?.date || !details?.time || details.latitude == null || details.longitude == null) {
      setLoading(false);
      setError(null);
      setData(null);
      return;
    }

    const requestId = ++requestIdRef.current;
    const key = cacheKey(details);

    try {
      const cachedRaw = localStorage.getItem(key);
      if (cachedRaw && requestId === requestIdRef.current) {
        const cached = JSON.parse(cachedRaw);
        if (cached?.today) {
          setData(cached);
          hasDataRef.current = true;
          setLoading(false);
          setError(null);
        }
      }
    } catch (_) {
      /* ignore */
    }

    if (!hasDataRef.current) setLoading(true);
    try {
      const now = new Date();
      const birthDate = String(details.date).split('T')[0];
      let birthTime = String(details.time);
      if (birthTime.includes('T')) birthTime = birthTime.split('T')[1];
      birthTime = birthTime.slice(0, 5);

      const response = await apiService.getKpFructification({
        birth_date: birthDate,
        birth_time: birthTime,
        latitude: details.latitude,
        longitude: details.longitude,
        timezone: details.timezone || '',
        as_of_date: formatLocalDate(now),
        as_of_time: formatLocalTime(now),
        language: 'en',
        synthesize: true,
      });

      if (requestId !== requestIdRef.current) return;
      if (response?.success && response?.data) {
        const payload = response.data;
        setData(payload);
        hasDataRef.current = true;
        setError(null);
        try {
          localStorage.setItem(key, JSON.stringify(payload));
        } catch (_) {
          /* ignore */
        }
      } else if (!hasDataRef.current) {
        setError(response?.detail || 'Could not load today’s predictions.');
      }
    } catch (e) {
      if (requestId !== requestIdRef.current) return;
      if (!hasDataRef.current) {
        setError(e?.response?.data?.detail || e.message || 'Could not load today’s predictions.');
      }
    } finally {
      if (requestId === requestIdRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user || !birthKey) {
      setData(null);
      hasDataRef.current = false;
      return undefined;
    }
    hasDataRef.current = false;
    setData(null);
    setError(null);
    load();
    return () => {
      requestIdRef.current += 1;
    };
  }, [user, birthKey, load]);

  const reader = useMemo(() => buildReaderPages(data?.today), [data?.today]);
  const tone = reader.tone || 'neutral';
  const ready = Boolean(user && birthData?.date && birthData?.time);

  const openReader = () => {
    if (!user) {
      onLogin?.();
      return;
    }
    if (!birthData?.date) {
      onNeedBirth?.();
      return;
    }
    if (error && !data) {
      load();
      return;
    }
    setOpen(true);
  };

  const openFull = () => {
    setOpen(false);
    navigate('/charts-dashas/activations');
  };

  if (!user) {
    return (
      <button type="button" className="kp-today-teaser kp-today-teaser--guest" onClick={onLogin}>
        <span className="kp-today-teaser__accent" aria-hidden="true" />
        <div className="kp-today-teaser__copy">
          <span className="kp-today-teaser__eyebrow">Daily KP</span>
          <h3 className="kp-today-teaser__title">Your day is waiting</h3>
          <p className="kp-today-teaser__text">
            Sign in with your birth chart to see today’s fructifying themes — written for this moment.
          </p>
          <span className="kp-today-teaser__cta">
            Sign in to read <span aria-hidden="true">→</span>
          </span>
        </div>
      </button>
    );
  }

  if (!birthData?.date) {
    return (
      <button type="button" className="kp-today-teaser kp-today-teaser--guest" onClick={onNeedBirth}>
        <span className="kp-today-teaser__accent" aria-hidden="true" />
        <div className="kp-today-teaser__copy">
          <span className="kp-today-teaser__eyebrow">Daily KP</span>
          <h3 className="kp-today-teaser__title">Select a native</h3>
          <p className="kp-today-teaser__text">
            Choose a birth chart to unlock today’s predictions for that person.
          </p>
          <span className="kp-today-teaser__cta">
            Select native <span aria-hidden="true">→</span>
          </span>
        </div>
      </button>
    );
  }

  if (!ready) return null;

  return (
    <>
      <button
        type="button"
        className={`kp-today-teaser kp-today-teaser--${tone}`}
        onClick={openReader}
        disabled={loading && !data}
      >
        <span className="kp-today-teaser__accent" aria-hidden="true" />
        <div className="kp-today-teaser__copy">
          <div className="kp-today-teaser__row">
            <span className="kp-today-teaser__eyebrow">Today · {formatShortDate(new Date())}</span>
            {!loading || data ? (
              <span className={`kp-today-tone kp-today-tone--${tone}`}>
                {TONE_LABELS[tone] || 'Steady'}
              </span>
            ) : null}
          </div>
          <h3 className="kp-today-teaser__title">
            {loading && !data ? 'Preparing your day…' : reader.quiet ? 'A quieter day' : 'Your day is ready'}
          </h3>
          {error && !data ? (
            <p className="kp-today-teaser__text kp-today-teaser__text--error">{error}</p>
          ) : (
            <p className="kp-today-teaser__text">
              {loading && !data
                ? 'Pulling today’s KP themes for your chart.'
                : reader.teaser}
            </p>
          )}
          <span className="kp-today-teaser__cta">
            {error && !data ? 'Retry' : 'Read today’s predictions'}
            <span aria-hidden="true">→</span>
          </span>
        </div>
      </button>

      <KpTodayReaderModal
        open={open}
        reader={reader}
        loading={loading}
        onClose={() => setOpen(false)}
        onOpenFull={openFull}
      />
    </>
  );
}
