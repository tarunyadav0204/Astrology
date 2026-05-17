import React, { useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { resolveSeoForPathname } from '../../config/publicRoutes.seo';
import SEOHead from './SEOHead';

/**
 * App-wide SEO fallback for public routes. Child pages with their own SEOHead override these tags.
 */
const RouteSEO = () => {
  const { pathname } = useLocation();

  const seo = useMemo(() => resolveSeoForPathname(pathname), [pathname]);

  if (!seo) {
    return null;
  }
  if (!seo.title && !seo.noIndex) {
    return null;
  }

  return (
    <SEOHead
      title={seo.title}
      description={seo.description}
      keywords={seo.keywords}
      canonical={seo.canonical}
      ogImage={seo.ogImage}
      twitterImage={seo.twitterImage}
      noIndex={seo.noIndex}
    />
  );
};

export default RouteSEO;
