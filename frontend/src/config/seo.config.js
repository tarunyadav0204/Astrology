export const SEO_CONFIG = {
  site: {
    name: "AstroRoshni",
    url: "https://astroroshni.com",
    description: "Professional Vedic Astrology Services - Accurate predictions, birth chart analysis, horoscope matching and expert consultations",
    keywords: "vedic astrology, horoscope, kundli, birth chart, astrology predictions, marriage matching, daily horoscope, astrologer consultation, panchang, muhurat",
    author: "AstroRoshni",
    themeColor: "#e91e63",
    language: "en-IN",
    locale: "en_IN"
  },
  
  social: {
    facebook: "https://www.facebook.com/astroroshni",
    instagram: "https://www.instagram.com/astroroshni", 
    twitter: "https://twitter.com/astroroshni",
    youtube: "https://www.youtube.com/astroroshni"
  },
  
  images: {
    logo: "/images/astroroshni-logo.png",
    ogDefault: "/images/astroroshni-og-image.jpg",
    twitterDefault: "/images/astroroshni-twitter-image.jpg",
    favicon: "/favicon.ico"
  },
  
  pages: {
    home: {
      title: "AstroRoshni - Best Vedic Astrology & Horoscope Predictions Online",
      description: "Get accurate Vedic astrology predictions, free Kundli, horoscope matching, daily horoscopes & expert astrologer consultations. Trusted by 50,000+ users worldwide.",
      keywords: "vedic astrology, horoscope, kundli, birth chart, astrology predictions, marriage matching, daily horoscope, astrologer consultation, panchang, muhurat"
    },
    
    marriageAnalysis: {
      title: "Marriage Analysis Report - Vedic Astrology Compatibility | AstroRoshni",
      description: "Get detailed marriage analysis and compatibility report based on Vedic astrology. Discover spouse characteristics, marriage timing, and relationship insights.",
      keywords: "marriage analysis, horoscope matching, kundli matching, marriage compatibility, spouse prediction, marriage astrology, vedic marriage analysis"
    },
    
    careerGuidance: {
      title: "Career Guidance & Job Predictions - Vedic Astrology | AstroRoshni", 
      description: "Professional career guidance based on Vedic astrology. Get insights about job prospects, business success, and career growth opportunities.",
      keywords: "career astrology, job predictions, business astrology, career guidance, professional success, vedic career analysis"
    },
    
    healthAnalysis: {
      title: "Health Analysis & Medical Astrology Predictions | AstroRoshni",
      description: "Comprehensive health analysis using Vedic medical astrology. Get insights about health issues, remedies, and wellness guidance.",
      keywords: "medical astrology, health predictions, ayurvedic astrology, health analysis, wellness astrology, disease prediction"
    },
    
    wealthAnalysis: {
      title: "Wealth & Finance Analysis - Money Predictions | AstroRoshni",
      description: "Detailed wealth and finance analysis based on Vedic astrology. Discover money-making opportunities and financial growth prospects.",
      keywords: "wealth astrology, finance predictions, money astrology, financial analysis, prosperity predictions, wealth creation"
    },
    
    panchang: {
      title: "Daily Panchang - Hindu Calendar & Auspicious Times | AstroRoshni",
      description: "Get today's Panchang with Tithi, Nakshatra, Yoga, Karana and auspicious muhurat times. Complete Hindu calendar information.",
      keywords: "panchang, hindu calendar, tithi, nakshatra, muhurat times, auspicious times, vedic calendar"
    },
    
    muhuratFinder: {
      title: "Muhurat Finder - Auspicious Times Calculator | AstroRoshni", 
      description: "Find auspicious muhurat times for marriage, business, travel and other important events using Vedic astrology calculations.",
      keywords: "muhurat finder, auspicious times, marriage muhurat, business muhurat, travel muhurat, vedic muhurat"
    },
    
    dailyHoroscope: {
      title: "Daily Horoscope - Today's Predictions for All Zodiac Signs | AstroRoshni",
      description: "Read your daily horoscope predictions for love, career, health and finance. Accurate daily astrology forecasts for all 12 zodiac signs.",
      keywords: "daily horoscope, today horoscope, zodiac predictions, astrology forecast, daily predictions"
    }
  },
  
  structuredData: {
    organization: {
      "@context": "https://schema.org",
      "@type": "Organization",
      "name": "AstroRoshni",
      "url": "https://astroroshni.com",
      "logo": "https://astroroshni.com/images/astroroshni-logo.png",
      "description": "Professional Vedic Astrology Services - Accurate predictions, birth chart analysis, horoscope matching and expert consultations",
      "telephone": "+91-9999999999",
      "email": "info@astroroshni.com",
      "address": {
        "@type": "PostalAddress",
        "addressCountry": "IN",
        "addressRegion": "Delhi", 
        "addressLocality": "New Delhi"
      },
      "sameAs": [
        "https://www.facebook.com/astroroshni",
        "https://www.instagram.com/astroroshni",
        "https://twitter.com/astroroshni"
      ]
    },
    
    website: {
      "@context": "https://schema.org",
      "@type": "WebSite", 
      "name": "AstroRoshni",
      "url": "https://astroroshni.com",
      "potentialAction": {
        "@type": "SearchAction",
        "target": "https://astroroshni.com/search?q={search_term_string}",
        "query-input": "required name=search_term_string"
      }
    }
  }
};

export const generatePageSEO = (pageKey, customData = {}) => {
  const pageConfig = SEO_CONFIG.pages[pageKey] || SEO_CONFIG.pages.home;
  
  return {
    title: customData.title || pageConfig.title,
    description: customData.description || pageConfig.description,
    keywords: customData.keywords || pageConfig.keywords,
    canonical: customData.canonical || `${SEO_CONFIG.site.url}${customData.path || '/'}`,
    ogImage: customData.ogImage || `${SEO_CONFIG.site.url}${SEO_CONFIG.images.ogDefault}`,
    twitterImage: customData.twitterImage || `${SEO_CONFIG.site.url}${SEO_CONFIG.images.twitterDefault}`
  };
};