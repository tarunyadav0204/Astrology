import React from 'react';
import { Helmet } from 'react-helmet-async';

const SEOHead = ({
  title = "AstroRoshni - Best Vedic Astrology & Horoscope Predictions Online",
  description = "Get accurate Vedic astrology predictions, free Kundli, horoscope matching, daily horoscopes & expert astrologer consultations. Trusted by 50,000+ users worldwide.",
  keywords = "vedic astrology, horoscope, kundli, birth chart, astrology predictions, marriage matching, daily horoscope, astrologer consultation, panchang, muhurat",
  canonical = "https://astroroshni.com/",
  ogImage = "https://astroroshni.com/images/astroroshni-og-image.jpg",
  twitterImage = "https://astroroshni.com/images/astroroshni-twitter-image.jpg",
  structuredData = null,
  noIndex = false
}) => {
  const defaultStructuredData = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": title,
    "description": description,
    "url": canonical,
    "isPartOf": {
      "@type": "WebSite",
      "name": "AstroRoshni",
      "url": "https://astroroshni.com"
    }
  };

  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      
      {/* Robots */}
      <meta name="robots" content={noIndex ? "noindex, nofollow" : "index, follow"} />
      <meta name="author" content="AstroRoshni" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta name="theme-color" content="#e91e63" />
      <link rel="canonical" href={canonical} />
      
      {/* Open Graph / Facebook */}
      <meta property="og:type" content="website" />
      <meta property="og:url" content={canonical} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={ogImage} />
      <meta property="og:site_name" content="AstroRoshni" />
      
      {/* Twitter */}
      <meta property="twitter:card" content="summary_large_image" />
      <meta property="twitter:url" content={canonical} />
      <meta property="twitter:title" content={title} />
      <meta property="twitter:description" content={description} />
      <meta property="twitter:image" content={twitterImage} />
      
      {/* Structured Data */}
      <script type="application/ld+json">
        {JSON.stringify(structuredData || defaultStructuredData)}
      </script>
    </Helmet>
  );
};

export default SEOHead;