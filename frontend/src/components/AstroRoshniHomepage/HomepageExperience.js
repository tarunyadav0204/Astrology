import React, { lazy, useEffect, useState } from 'react';
import { SEO_CONFIG } from '../../config/seo.config';
import './HomepageExperience.css';

const LegacyHomepage = lazy(() => import('./AstroRoshniHomepage'));
const ModernHomepage = lazy(() => import('./ModernAstroRoshniHomepage'));

const getPreviewOverride = () => {
  if (typeof window === 'undefined') return null;
  const value = new URLSearchParams(window.location.search).get('homepage');
  if (value === 'modern' || value === 'legacy') return value;
  return null;
};

/**
 * Fail-closed homepage switcher.
 *
 * The legacy homepage remains the fallback whenever the public config request
 * fails or the admin flag is disabled. `?homepage=modern` and
 * `?homepage=legacy` are intentionally available for production-safe QA.
 */
const HomepageExperience = (props) => {
  const previewOverride = getPreviewOverride();
  const [experience, setExperience] = useState(
    previewOverride || (process.env.REACT_APP_MODERN_HOMEPAGE === 'true' ? 'modern' : null)
  );

  useEffect(() => {
    if (previewOverride) return undefined;

    let mounted = true;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 2000);
    fetch('/api/app/config', { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error('Homepage config unavailable');
        return response.json();
      })
      .then((config) => {
        if (mounted) setExperience(config.modern_homepage_enabled ? 'modern' : 'legacy');
      })
      .catch(() => {
        if (mounted) setExperience('legacy');
      });

    return () => {
      mounted = false;
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [previewOverride]);

  if (!experience) {
    return (
      <div className="homepage-experience-loading" role="status" aria-label="Loading AstroRoshni">
        <img src={SEO_CONFIG.images.logo} width="42" height="42" alt="" />
        <span>AstroRoshni</span>
      </div>
    );
  }

  return experience === 'modern' ? <ModernHomepage {...props} /> : <LegacyHomepage {...props} />;
};

export default HomepageExperience;
