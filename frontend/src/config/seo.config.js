export const SEO_CONFIG = {
  site: {
    name: "AstroRoshni",
    url: "https://astroroshni.com",
    description: "Professional Vedic Astrology Services - Accurate predictions, birth chart analysis, horoscope matching and expert consultations",
    keywords: "vedic astrology, horoscope, kundli, birth chart, astrology predictions, marriage matching, daily horoscope, astrologer consultation, panchang, muhurat",
    author: "AstroRoshni",
    themeColor: "#961b48",
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
    /** 96px raster + WebP — header logo displays ~22–44px; avoids multi‑MB 1024² PNG. */
    logo: "/images/astroroshni-icon-96.webp",
    logoPngFallback: "/images/astroroshni-icon-96.png",
    ogDefault: "/images/astroroshni-og-image.jpg",
    twitterDefault: "/images/astroroshni-twitter-image.jpg",
    favicon: "/favicon.ico",
    /** Responsive WebP built from source banner; PNG fallbacks for non‑WebP browsers. */
    homeLifePathBanner: "/images/homepage-life-path-banner-1200.webp",
    homeLifePathBannerSrcSetWebp:
      "/images/homepage-life-path-banner-800.webp 800w, /images/homepage-life-path-banner-1200.webp 1200w",
    homeLifePathBannerFallback: "/images/homepage-life-path-banner-1200.png",
  },

  /** Google Play listing — homepage life-path banner CTA */
  mobileApp: {
    name: "AstroRoshni: AI Kundli & Chat",
    playStoreUrl:
      "https://play.google.com/store/apps/details?id=com.astroroshni.mobile&pcampaignid=web_share",
    homeBanner: {
      width: 1200,
      height: 485,
      alt:
        "Discover Your Life Path -AstroRoshni Vedic Astrology",
      title:
        "Discover Your Life Path -AstroRoshni Vedic Astrology",
      caption:
        "Promotional banner: unlock your destiny with best-in-class Vedic astrology. Get the AstroRoshni Android app for free Kundli, predictions, and AI astrologer chat.",
    },
  },
  
  pages: {
    home: {
      title: "AI Powered Vedic Astrology & Daily Horoscope Prediction | AstroRoshni",
      description: "Get personalized Vedic astrology insights with AI-powered horoscope analysis, daily predictions, and accurate astrology guidance tailored to your birth details.",
      keywords: "daily horoscope prediction, personalized vedic astrology, AI powered horoscope, personalized astrology guidance, vedic horoscope analysis, AI astrology assistant, AI powered astrology, AI based vedic astrology"
    },
    
    marriageAnalysis: {
      title: "AI Powered Marriage Astrology | Marriage Prediction by date of birth",
      description: "Get AI-powered marriage astrology insights and marriage prediction by date of birth with personalized horoscope analysis and Vedic guidance.",
      keywords: "AI marriage prediction, AI powered marriage astrology, marriage horoscope analysis, marriage prediction by date of birth, marriage prediction astrology"
    },
    
    careerGuidance: {
      title: "AI Career Astrology & Career Prediction by Date of Birth | AstroRoshni",
      description: "Explore AI-powered career guidance astrology with personalized birth chart analysis to understand your career path, growth opportunities, and professional potential.",
      keywords: "AI career astrology, career guidance astrology, career prediction by date of birth"
    },
    
    healthAnalysis: {
      title: "AI Powered Health Astrology | Health Prediction by Date of Birth",
      description: "Get AI-powered health astrology insights and health horoscope predictions based on your date of birth with personalized Vedic astrology analysis.",
      keywords: "AI powered health astrology, health astrology by date of birth, health horoscope prediction, health prediction by date of birth"
    },
    
    wealthAnalysis: {
      title: "AI Powered Wealth Astrology & Wealth Analysis by Kundli | AstroRoshni",
      description: "Explore AI wealth analysis with detailed Kundli insights to understand your wealth potential, financial opportunities, and prosperity patterns.",
      keywords: "wealth astrology, AI powered wealth astrology, wealth analysis by kundli, AI wealth analysis"
    },

    educationAnalysis: {
      title: "AI Powered Education Astrology & Education Prediction by Date of Birth",
      description: "Get AI-powered education astrology insights and education predictions by date of birth. Discover your learning strengths, academic path, and Vedic guidance.",
      keywords: "education astrology, AI powered education astrology, AI education prediction, education astrology by date of birth, Vedic education astrology"
    },

    lifeEvents: {
      title: "Life Events Timeline by Date of Birth | Yearly & Monthly Vedic Predictions | AstroRoshni",
      description: "Get a Vedic life events timeline by date of birth with yearly predictions, monthly chapters, one-month deep dives, dasha timing, transits, Parashari, Nadi, and Jaimini methods.",
      keywords: "life events timeline by date of birth, life events astrology, yearly predictions astrology, monthly predictions astrology, vedic timeline, dasha events, transit predictions, Parashari timing, Nadi astrology timeline, Jaimini timing, major life events prediction, birth chart event timing"
    },
    
    panchang: {
      title: "Today Panchang | Tithi, Nakshatra, Rahu Kaal & Muhurat Timings | AstroRoshni",
      description: "Check today's Panchang by location with tithi, nakshatra, yoga, karana, sunrise, sunset, Rahu Kaal, Yamaganda, Choghadiya, Hora and auspicious muhurat timings.",
      keywords: "today panchang, daily panchang, hindu calendar, tithi today, nakshatra today, rahu kaal today, choghadiya today, hora today, muhurat timings, vedic calendar, panchang by location"
    },
    
    muhuratFinder: {
      title: "Shubh Muhurat Finder for Important Events | AstroRoshni", 
      description: "Find the right Shubh Muhurat for marriage, griha pravesh, vehicle, travel, property, and special occasions with personalized Vedic astrology guidance and auspicious timings.",
      keywords: "shubh muhurat finder"
    },
    
    dailyHoroscope: {
      title: "Daily Horoscope - Today's Predictions for All Zodiac Signs | AstroRoshni",
      description: "Read your daily horoscope predictions for love, career, health and finance. Accurate daily astrology forecasts for all 12 zodiac signs.",
      keywords: "daily horoscope, today horoscope, zodiac predictions, astrology forecast, daily predictions"
    },

    kundliMatching: {
      title: "Smart Kundli Matching for Marriage | Kundli Matching by Name",
      description: "Get smart Kundli matching for marriage with AI-powered analysis, Guna Milan insights, and personalized compatibility reports based on birth details.",
      keywords: "kundli matching for marriage, marriage kundli analysis, smart kundli matching, kundli matching by name"
    },

    reportsStudio: {
      title: "Reports Studio — Premium Vedic PDF Reports | AstroRoshni",
      description: "Create premium Vedic PDF reports in AstroRoshni Reports Studio: Partnership compatibility and Wealth timing reports with charts, dasha windows, remedies, and clear takeaways. Career, Health, and Progeny coming soon.",
      keywords: "vedic reports studio, partnership compatibility PDF, wealth astrology report, kundli PDF report, dasha timing report, marriage matching report, vedic wealth report, premium kundli report"
    },

    birthChartCreation: {
      title: "AI Kundli Generator | Free Janam Kundli Online & Accurate Kundli Prediction | AstroRoshni",
      description: "Use AstroRoshni's AI Kundli Generator to create your free Janam Kundli online with date, time, and place of birth. Get instant Vedic Kundli analysis, horoscope and Kundli insights, dosha analysis, and accurate AI-backed Kundli prediction.",
      keywords: "Free Janam Kundli Generator, Instant Kundli Report Generator, Free Horoscope and Kundli, Online Kundli by Date of Birth, Horoscope and kundli, Free Janam Kundli online, AI Kundli Prediction, Accurate kundli prediction, Kundli maker, Instant Kundli Report, Vedic Kundli Analysis, AI Janam Kundli, Kundli Dosha Analysis",
    },

    chartsDashasWorkspace: {
      title: "Charts & Dashas Workspace | Lagna, Divisional Charts and Dasha Timeline | AstroRoshni",
      description: "Open your AstroRoshni charts and dashas workspace to explore Lagna, divisional charts, transit chart views, and major dasha systems from one saved birth chart.",
      keywords: "charts and dashas, lagna chart, divisional charts, vimshottari dasha, transit chart, navamsa chart, dasha timeline, vedic astrology dashboard, kundli charts workspace, astrology charts online",
    },

    monthlyPanchang: {
      title: "Monthly Panchang — Hindu Calendar by Month | AstroRoshni",
      description: "View monthly Panchang with tithi, nakshatra, festivals, and auspicious days for any month and location.",
      keywords: "monthly panchang, hindu calendar month, tithi calendar, vedic calendar"
    },

    festivals: {
      title: "Hindu Festivals Calendar | Today’s Vrat, Tithi & Panchang Dates | AstroRoshni",
      description: "Check today’s Hindu festivals and vrats by date and location with Panchang context, tithi, nakshatra, parana timing, rituals, and festival significance.",
      keywords: "hindu festivals calendar, today hindu festival, vrat today, tithi festival dates, panchang festivals, ekadashi vrat, pradosh vrat, hindu calendar, indian festivals, festival significance, parana time"
    },

    festivalsMonthly: {
      title: "Monthly Hindu Festivals Calendar | Vrat Dates, Ekadashi & Panchang | AstroRoshni",
      description: "Browse monthly Hindu festivals and vrats with location-aware dates, Ekadashi, Pradosh, Purnima, Amavasya, tithi details, parana timing, and observance guidance.",
      keywords: "monthly hindu festivals, hindu festival calendar month, vrat dates this month, ekadashi dates, pradosh dates, purnima amavasya calendar, panchang monthly festivals, indian festival calendar, hindu calendar month"
    },

    nakshatrasList: {
      title: "27 Nakshatras in Vedic Astrology | Names, Lords, Deities & Calendar | AstroRoshni",
      description: "Explore the complete 27 Nakshatras list with names, planetary lords, deities, nature, zodiac ranges, padas, meanings, Janma Nakshatra guidance, and yearly nakshatra calendars.",
      keywords: "27 nakshatras, nakshatra list, nakshatra names, nakshatra lord, nakshatra deity, Janma Nakshatra, nakshatra padas, lunar mansions, Vedic astrology nakshatra, nakshatra calendar, Moon nakshatra"
    },

    nakshatraDetail: {
      title: "Nakshatra Calendar & Predictions | AstroRoshni",
      description: "Yearly nakshatra calendar with auspicious dates and Vedic insights.",
      keywords: "nakshatra calendar, nakshatra predictions, vedic astrology"
    },

    karmaAnalysis: {
      title: "Past Life Karma Analysis — Vedic Birth Chart Reading | AstroRoshni",
      description: "Discover past-life themes and karmic patterns from your Vedic chart (D9, D60, 12th house, Rahu–Ketu). Free guide plus personalised karma report on AstroRoshni.",
      keywords: "past life karma analysis, vedic past life astrology, karmic patterns birth chart, D60 shashtiamsa, past life reading by date of birth, 12th house past life, Rahu Ketu karma, karmic debt astrology"
    },

    chatAstrologer: {
      title: "AI Vedic Astrologer Chat — Ask Tara About Your Kundli | AstroRoshni",
      description: "Chart-aware Vedic astrology chat: single chart, partnership, and mundane modes with dasha, transit, yoga, event periods, voice chat, and podcast summaries.",
      keywords: "ai astrologer chat, vedic astrology chat online, birth chart questions, ask astrologer online, kundli chat, horoscope chat bot, jyotish ai, partnership astrology chat, dasha prediction chat, online vedic astrologer"
    },

    blogList: {
      title: "AstroRoshni Blog — Vedic Astrology Articles & Guides",
      description: "Expert articles on Vedic astrology, remedies, Panchang, matching, and life guidance.",
      keywords: "astrology blog, vedic astrology articles, horoscope blog, jyotish"
    },

    blogPost: {
      title: "Blog | AstroRoshni",
      description: "Vedic astrology articles and guides from AstroRoshni.",
      keywords: "vedic astrology, astrology article"
    },

    about: {
      title: "About AstroRoshni — Authentic Vedic Astrology Platform",
      description: "Learn about AstroRoshni's mission to deliver accurate Vedic astrology, Kundli, and personalized guidance.",
      keywords: "about astroroshni, vedic astrology platform, online astrologer"
    },

    contact: {
      title: "Contact AstroRoshni — Support & Inquiries",
      description: "Get in touch with the AstroRoshni team for support, partnerships, or astrology questions.",
      keywords: "contact astroroshni, astrology support, customer service"
    },

    policy: {
      title: "Privacy Policy | AstroRoshni",
      description: "AstroRoshni privacy policy — how we collect, use, and protect your personal and birth chart data.",
      keywords: "privacy policy, data protection, astrology app privacy"
    },

    terms: {
      title: "Terms and Conditions | AstroRoshni",
      description: "Terms of use for AstroRoshni — AI astrology platform, wallet, refunds, conduct, liability, and DPDP-aligned data consent.",
      keywords: "terms and conditions, terms of service, astroroshni legal, user agreement"
    },

    calendar2026: {
      title: "Hindu Calendar 2026 — Festivals, Panchang & Muhurat | AstroRoshni",
      description: "Complete 2026 Hindu calendar with festivals, ekadashi, amavasya, and auspicious muhurat dates.",
      keywords: "hindu calendar 2026, festival calendar 2026, panchang 2026"
    },

    beginnersGuide: {
      title: "Vedic Astrology for Beginners — Free Guide | AstroRoshni",
      description: "Start learning Vedic astrology: houses, planets, signs, and how to read your birth chart.",
      keywords: "learn vedic astrology, astrology for beginners, jyotish basics"
    },

    advancedCourses: {
      title: "Advanced Vedic Astrology Courses | AstroRoshni",
      description: "Deep-dive courses on dashas, divisional charts, prediction techniques, and professional Jyotish.",
      keywords: "advanced astrology course, vedic astrology training, jyotish course"
    },

    mythsVsReality: {
      title: "Astrology Myths vs Reality — Facts About Jyotish | AstroRoshni",
      description: "Separate fact from fiction in Vedic astrology with evidence-based explanations.",
      keywords: "astrology myths, vedic astrology facts, jyotish science"
    },

    ashtakavarga: {
      title: "Ashtakavarga Calculator | Sarvashtakavarga & Bhinna Ashtakavarga Analysis | AstroRoshni",
      description: "Use AstroRoshni's Ashtakavarga Calculator to study Sarvashtakavarga totals, Bhinna Ashtakavarga bindus, house strength, and transit support from your Vedic birth chart.",
      keywords: "Ashtakavarga Calculator, Sarvashtakavarga, Bhinna Ashtakavarga, Ashtakavarga bindus, house strength astrology, Vedic chart strength, transit support astrology, bindu analysis, Ashtakavarga in Vedic astrology, Sarvashtakavarga calculator"
    },

    astroVastu: {
      title: "Astro-Vastu — Home Direction & Planetary Remedies | AstroRoshni",
      description: "Combine Vedic astrology with Vastu principles for home layout and directional remedies.",
      keywords: "astro vastu, vastu shastra, home remedies astrology"
    },

    subscription: {
      title: "Subscription & Plans — AstroRoshni",
      description: "AstroRoshni subscription plans, credits, and premium Vedic astrology features.",
      keywords: "astroroshni subscription, astrology plans, premium kundli"
    },

    progenyAnalysis: {
      title: "AI Powered Progeny Astrology & Children Prediction Analysis | AstroRoshni",
      description: "Get AI-powered progeny astrology insights and children prediction analysis based on Vedic astrology, birth details, and personalized horoscope guidance.",
      keywords: "progeny astrology, AI powered progeny astrology, AI progeny analysis, children prediction astrology"
    }
  },
  
  structuredData: {
    /** Single canonical Organization (legal entity + consumer brand). Referenced elsewhere via @id. */
    organization: {
      "@context": "https://schema.org",
      "@type": "Organization",
      "@id": "https://astroroshni.com/#organization",
      name: "Apeiron Logic LLP",
      alternateName: "AstroRoshni",
      url: "https://astroroshni.com",
      logo: "https://astroroshni.com/images/astroroshni-icon-96.webp",
      description:
        "Professional Vedic Astrology Services & Creators of Tara, the world's most advanced AI Predictive Astrology Engine.",
      telephone: "+91-9560214006",
      email: "help@astroroshni.com",
      address: {
        "@type": "PostalAddress",
        addressCountry: "IN",
        addressRegion: "Gurgaon",
        addressLocality: "Haryana",
      },
      sameAs: [
        "https://www.facebook.com/astroroshni",
        "https://www.instagram.com/astroroshniai",
        "https://twitter.com/astroroshni",
        "https://play.google.com/store/apps/details?id=com.astroroshni.mobile",
      ],
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

/** JSON-LD for homepage technical architecture, accuracy proof, and FAQ content. */
export const buildHomeAccuracyProofStructuredData = () => ({
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebPage",
      "@id": "https://astroroshni.com/#accuracy-proof",
      "name": "Tara AI Technical Architecture and Accuracy Proofs",
      "mainEntity": {
        "@type": "ItemList",
        "name": "Tara Predictive Synthesis Capabilities",
        "itemListElement": [
          {
            "@type": "ListItem",
            "position": 1,
            "name": "50+ Astrological Calculation Systems",
            "description": "Tara processes over 50 astrological calculation systems simultaneously. By executing Sudarshana Chakra analysis, complete Ashtakavarga analysis, and Nadi Astrology links in real-time, the engine delivers unmatched accuracy through multi-layered synthesis."
          },
          {
            "@type": "ListItem",
            "position": 2,
            "name": "NASA-Grade Swiss Ephemeris",
            "description": "Calculations are powered by Swiss Ephemeris precision, ensuring planetary alignments, planetary war (Graha Yuddha) calculations, and Neecha Bhanga analysis are astronomically accurate to the exact arc-second."
          },
          {
            "@type": "ListItem",
            "position": 3,
            "name": "Comprehensive Dasha Processing",
            "description": "The predictive model computes a precise 5-level Vimshottari Dasha system alongside Jaimini Chara Dasha and Yogini Dasha, rigorously back-tested against hundreds of thousands of birth charts to refine predictive timing."
          },
          {
            "@type": "ListItem",
            "position": 4,
            "name": "Expert Astrologer Validation",
            "description": "Tara's real-time transit activations and karmic trigger detection models are continuously audited by certified Vedic astrologers to ensure modern computational technology strictly adheres to traditional astrological rules."
          }
        ]
      }
    },
    {
      "@type": "FAQPage",
      "@id": "https://astroroshni.com/#faq",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "Is Tara AI astrology accurate?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Tara achieves unprecedented accuracy by processing over 50+ astrological calculation systems simultaneously. Powered by NASA-grade Swiss Ephemeris precision, Tara cross-references traditional Vedic texts with complex real-time variables like planetary war calculations, Neecha Bhanga analysis, and comprehensive yoga detection."
          }
        },
        {
          "@type": "Question",
          "name": "How is Tara different from generic horoscopes?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Unlike generalized Sun-sign horoscopes, Tara acts as an advanced Digital Astrologer. It generates hyper-personalized predictions by calculating complete Ashtakavarga, Nadi Astrology links, and Sudarshana Chakra analysis specific to your exact birth time and coordinates, delivering multi-layered synthesis rather than one-dimensional forecasts."
          }
        },
        {
          "@type": "Question",
          "name": "Can Kundli predict the future accurately?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "It reveals tendencies, possibilities, and specific planetary periods. Tara maps your future using a precise 5-level Vimshottari Dasha system alongside Jaimini Chara Dasha and Yogini Dasha. Combined with real-time transit activations and karmic trigger detection, Tara pinpoints exactly when major life events are most likely to unfold."
          }
        },
        {
          "@type": "Question",
          "name": "What is a divisional chart (Varga)?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Divisional charts are derived charts that zoom into specific life areas. While most platforms calculate only a few, Tara computes all 16 Divisional Charts (from D1 to D60). This allows the engine to analyze the deepest layers of your destiny, from your primary life path down to highly specific areas like career, partnerships, and spiritual growth."
          }
        },
        {
          "@type": "Question",
          "name": "What is a Kundali (Birth Chart)?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "A Kundali is an astrological chart mapping the celestial bodies at your exact birth moment. Tara maps the placement of 9 planets across 12 houses and applies comprehensive yoga detection to analyze personality traits, life events, and complex relationship dynamics."
          }
        },
        {
          "@type": "Question",
          "name": "What information do I need to create my Kundli?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "To generate an accurate Kundli, you need your date of birth, precise time of birth, and place of birth. Tara uses this exact data with Swiss Ephemeris precision to map your celestial coordinates without mathematical rounding errors."
          }
        },
        {
          "@type": "Question",
          "name": "Why is birth time important for Kundli?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Birth time determines your Ascendant (Lagna), which changes every two hours. Even a difference of a few minutes shifts the Moon's Nakshatra pada, which fundamentally alters how Tara calculates your 5-level Vimshottari Dasha system and subsequent predictions."
          }
        },
        {
          "@type": "Question",
          "name": "What is Lagna (Ascendant)?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "The Lagna is the zodiac sign rising on the eastern horizon at your exact time of birth. It represents your physical body, personality, and serves as the baseline from which Tara conducts its multi-layered synthesis."
          }
        },
        {
          "@type": "Question",
          "name": "What are the 12 houses in a Kundli?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "The 12 houses represent different life areas: 1st (Self), 2nd (Wealth), 3rd (Siblings), 4th (Home), 5th (Children/Education), 6th (Health), 7th (Marriage), 8th (Longevity), 9th (Fortune), 10th (Career), 11th (Gains), and 12th (Losses)."
          }
        },
        {
          "@type": "Question",
          "name": "Why do twins have different lives?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Even minutes apart, twins can have a different Lagna or Nakshatra Pada. Furthermore, Tara tracks how subtle minute variations impact the deeper higher-level Divisional Charts (up to D60) and Nadi Astrology links, revealing entirely different karmic triggers."
          }
        },
        {
          "@type": "Question",
          "name": "How accurate is Tara's Kundali matching?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Tara's matching system strictly analyzes all 36 Gunas as per traditional Vedic astrology. It simultaneously executes complex planetary alignments to check for planetary war (Graha Yuddha) and specific doshas, providing definitive, highly synthesized compatibility scores."
          }
        },
        {
          "@type": "Question",
          "name": "Is my birth data secure with AstroRoshni?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Yes. AstroRoshni secures your data using bank-grade 256-bit encryption. We are fully compliant with GDPR and India's IT Act. Your personal data is never sold to third parties, and you can request complete deletion at any time."
          }
        },
        {
          "@type": "Question",
          "name": "Do astrological remedies really work?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Remedies function through psychological, behavioral, and spiritual mechanisms to create positive vibrations. Their effectiveness is highly tied to the user's consistency when applying the specific timings calculated by Tara's real-time transit activations."
          }
        },
        {
          "@type": "Question",
          "name": "What are common remedies for weak planets?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Standard Vedic remedies include wearing specific gemstones, chanting mantras, performing charity on specific days, fasting, and utilizing energized Yantras aligned with an individual's planetary afflictions."
          }
        }
      ]
    }
  ]
});

/** JSON-LD for homepage Play Store promo banner (ImageObject + SoftwareApplication). */
export const buildHomePlayStoreBannerStructuredData = () => {
  const { site, images, mobileApp } = SEO_CONFIG;
  const imageUrl = `${site.url}${images.homeLifePathBanner}`;
  const pageUrl = `${site.url}/`;

  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "ImageObject",
        "@id": `${pageUrl}#homepage-life-path-banner`,
        contentUrl: imageUrl,
        url: imageUrl,
        name: "Discover Your Life Path — AstroRoshni Vedic Astrology",
        description: mobileApp.homeBanner.caption,
        width: mobileApp.homeBanner.width,
        height: mobileApp.homeBanner.height,
        encodingFormat: "image/png",
        inLanguage: site.language,
        isPartOf: { "@type": "WebPage", "@id": pageUrl },
        mainEntityOfPage: pageUrl,
      },
      {
        "@type": "SoftwareApplication",
        "@id": `${pageUrl}#astroroshni-android-app`,
        name: mobileApp.name,
        operatingSystem: "Android",
        applicationCategory: "LifestyleApplication",
        description:
          "AI-powered Vedic astrology app: instant Kundli, horoscope, kundali matching, past life karma analysis, and live chat with an AI astrologer.",
        image: imageUrl,
        installUrl: mobileApp.playStoreUrl,
        downloadUrl: mobileApp.playStoreUrl,
        offers: {
          "@type": "Offer",
          price: "0",
          priceCurrency: "INR",
          availability: "https://schema.org/InStock",
        },
        publisher: {
          "@id": `${site.url}/#organization`,
        },
      },
    ],
  };
};
