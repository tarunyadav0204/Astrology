/**
 * CRA homepage SEO parity: same meta targets as `frontend/src/config/seo.config.js`
 * and the same JSON-LD payloads the CRA homepage injects via react-helmet-async.
 * FAQ + accuracy list text is the single source for visible `<details>` and FAQPage schema.
 */

const SITE_URL = 'https://astroroshni.com';
const PAGE_URL = `${SITE_URL}/`;

/** Four capability bullets — same copy as CRA `buildHomeAccuracyProofStructuredData` ItemList. */
export const CRA_HOME_ACCURACY_ITEMS = [
  {
    name: '50+ Astrological Calculation Systems',
    description:
      'Tara processes over 50 astrological calculation systems simultaneously. By executing Sudarshana Chakra analysis, complete Ashtakavarga analysis, and Nadi Astrology links in real-time, the engine delivers unmatched accuracy through multi-layered synthesis.',
  },
  {
    name: 'NASA-Grade Swiss Ephemeris',
    description:
      'Calculations are powered by Swiss Ephemeris precision, ensuring planetary alignments, planetary war (Graha Yuddha) calculations, and Neecha Bhanga analysis are astronomically accurate to the exact arc-second.',
  },
  {
    name: 'Comprehensive Dasha Processing',
    description:
      'The predictive model computes a precise 5-level Vimshottari Dasha system alongside Jaimini Chara Dasha and Yogini Dasha, rigorously back-tested against hundreds of thousands of birth charts to refine predictive timing.',
  },
  {
    name: 'Expert Astrologer Validation',
    description:
      "Tara's real-time transit activations and karmic trigger detection models are continuously audited by certified Vedic astrologers to ensure modern computational technology strictly adheres to traditional astrological rules.",
  },
];

/** FAQ answers must match FAQPage `acceptedAnswer.text` exactly (CRA `buildHomeAccuracyProofStructuredData`). */
export const CRA_HOME_FAQS = [
  {
    question: 'Is Tara AI astrology accurate?',
    answer:
      'Tara achieves unprecedented accuracy by processing over 50+ astrological calculation systems simultaneously. Powered by NASA-grade Swiss Ephemeris precision, Tara cross-references traditional Vedic texts with complex real-time variables like planetary war calculations, Neecha Bhanga analysis, and comprehensive yoga detection.',
  },
  {
    question: 'How is Tara different from generic horoscopes?',
    answer:
      'Unlike generalized Sun-sign horoscopes, Tara acts as an advanced Digital Astrologer. It generates hyper-personalized predictions by calculating complete Ashtakavarga, Nadi Astrology links, and Sudarshana Chakra analysis specific to your exact birth time and coordinates, delivering multi-layered synthesis rather than one-dimensional forecasts.',
  },
  {
    question: 'Can Kundli predict the future accurately?',
    answer:
      'It reveals tendencies, possibilities, and specific planetary periods. Tara maps your future using a precise 5-level Vimshottari Dasha system alongside Jaimini Chara Dasha and Yogini Dasha. Combined with real-time transit activations and karmic trigger detection, Tara pinpoints exactly when major life events are most likely to unfold.',
  },
  {
    question: 'What is a divisional chart (Varga)?',
    answer:
      'Divisional charts are derived charts that zoom into specific life areas. While most platforms calculate only a few, Tara computes all 16 Divisional Charts (from D1 to D60). This allows the engine to analyze the deepest layers of your destiny, from your primary life path down to highly specific areas like career, partnerships, and spiritual growth.',
  },
  {
    question: 'What is a Kundali (Birth Chart)?',
    answer:
      'A Kundali is an astrological chart mapping the celestial bodies at your exact birth moment. Tara maps the placement of 9 planets across 12 houses and applies comprehensive yoga detection to analyze personality traits, life events, and complex relationship dynamics.',
  },
  {
    question: 'What information do I need to create my Kundli?',
    answer:
      'To generate an accurate Kundli, you need your date of birth, precise time of birth, and place of birth. Tara uses this exact data with Swiss Ephemeris precision to map your celestial coordinates without mathematical rounding errors.',
  },
  {
    question: 'Why is birth time important for Kundli?',
    answer:
      "Birth time determines your Ascendant (Lagna), which changes every two hours. Even a difference of a few minutes shifts the Moon's Nakshatra pada, which fundamentally alters how Tara calculates your 5-level Vimshottari Dasha system and subsequent predictions.",
  },
  {
    question: 'What is Lagna (Ascendant)?',
    answer:
      'The Lagna is the zodiac sign rising on the eastern horizon at your exact time of birth. It represents your physical body, personality, and serves as the baseline from which Tara conducts its multi-layered synthesis.',
  },
  {
    question: 'What are the 12 houses in a Kundli?',
    answer:
      'The 12 houses represent different life areas: 1st (Self), 2nd (Wealth), 3rd (Siblings), 4th (Home), 5th (Children/Education), 6th (Health), 7th (Marriage), 8th (Longevity), 9th (Fortune), 10th (Career), 11th (Gains), and 12th (Losses).',
  },
  {
    question: 'Why do twins have different lives?',
    answer:
      'Even minutes apart, twins can have a different Lagna or Nakshatra Pada. Furthermore, Tara tracks how subtle minute variations impact the deeper higher-level Divisional Charts (up to D60) and Nadi Astrology links, revealing entirely different karmic triggers.',
  },
  {
    question: "How accurate is Tara's Kundali matching?",
    answer:
      "Tara's matching system strictly analyzes all 36 Gunas as per traditional Vedic astrology. It simultaneously executes complex planetary alignments to check for planetary war (Graha Yuddha) and specific doshas, providing definitive, highly synthesized compatibility scores.",
  },
  {
    question: 'Is my birth data secure with AstroRoshni?',
    answer:
      "Yes. AstroRoshni secures your data using bank-grade 256-bit encryption. We are fully compliant with GDPR and India's IT Act. Your personal data is never sold to third parties, and you can request complete deletion at any time.",
  },
  {
    question: 'Do astrological remedies really work?',
    answer:
      "Remedies function through psychological, behavioral, and spiritual mechanisms to create positive vibrations. Their effectiveness is highly tied to the user's consistency when applying the specific timings calculated by Tara's real-time transit activations.",
  },
  {
    question: 'What are common remedies for weak planets?',
    answer:
      "Standard Vedic remedies include wearing specific gemstones, chanting mantras, performing charity on specific days, fasting, and utilizing energized Yantras aligned with an individual's planetary afflictions.",
  },
];

/** Same object as CRA `SEO_CONFIG.structuredData.organization`. */
export const organizationLd = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'AstroRoshni',
  url: SITE_URL,
  logo: `${SITE_URL}/images/astroroshni-icon.png`,
  description:
    'Professional Vedic Astrology Services - Accurate predictions, birth chart analysis, horoscope matching and expert consultations',
  telephone: '+91-9999999999',
  email: 'info@astroroshni.com',
  address: {
    '@type': 'PostalAddress',
    addressCountry: 'IN',
    addressRegion: 'Delhi',
    addressLocality: 'New Delhi',
  },
  sameAs: [
    'https://www.facebook.com/astroroshni',
    'https://www.instagram.com/astroroshni',
    'https://twitter.com/astroroshni',
  ],
};

/** Same object as CRA `SEO_CONFIG.structuredData.website`. */
export const websiteLd = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'AstroRoshni',
  url: SITE_URL,
  potentialAction: {
    '@type': 'SearchAction',
    target: `${SITE_URL}/search?q={search_term_string}`,
    'query-input': 'required name=search_term_string',
  },
};

/** Same graph as CRA `buildHomeAccuracyProofStructuredData()`. */
export function buildHomeAccuracyProofStructuredData() {
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Organization',
        '@id': `${SITE_URL}/#organization`,
        name: 'Apeiron Logic LLP',
        url: PAGE_URL,
        logo: `${SITE_URL}/images/astroroshni-icon.png`,
        description: "Creators of Tara, the world's most advanced AI Predictive Astrology Engine.",
        sameAs: ['https://play.google.com/store/apps/details?id=com.astroroshni.mobile'],
      },
      {
        '@type': 'WebPage',
        '@id': `${SITE_URL}/#accuracy-proof`,
        name: 'Tara AI Technical Architecture and Accuracy Proofs',
        mainEntity: {
          '@type': 'ItemList',
          name: 'Tara Predictive Synthesis Capabilities',
          itemListElement: CRA_HOME_ACCURACY_ITEMS.map((item, index) => ({
            '@type': 'ListItem',
            position: index + 1,
            name: item.name,
            description: item.description,
          })),
        },
      },
      {
        '@type': 'FAQPage',
        '@id': `${SITE_URL}/#faq`,
        mainEntity: CRA_HOME_FAQS.map((faq) => ({
          '@type': 'Question',
          name: faq.question,
          acceptedAnswer: {
            '@type': 'Answer',
            text: faq.answer,
          },
        })),
      },
    ],
  };
}

const PLAY_STORE_URL =
  'https://play.google.com/store/apps/details?id=com.astroroshni.mobile&pcampaignid=web_share';
const HOME_BANNER_PATH = '/images/homepage-life-path-banner.png';
const HOME_BANNER = {
  width: 1200,
  height: 656,
  caption:
    'Promotional banner: unlock your destiny with best-in-class Vedic astrology. Get the AstroRoshni Android app for free Kundli, predictions, and AI astrologer chat.',
};

/** Same graph as CRA `buildHomePlayStoreBannerStructuredData()`. */
export function buildHomePlayStoreBannerStructuredData() {
  const imageUrl = `${SITE_URL}${HOME_BANNER_PATH}`;

  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'ImageObject',
        '@id': `${PAGE_URL}#homepage-life-path-banner`,
        contentUrl: imageUrl,
        url: imageUrl,
        name: 'Discover Your Life Path — AstroRoshni Vedic Astrology',
        description: HOME_BANNER.caption,
        width: HOME_BANNER.width,
        height: HOME_BANNER.height,
        encodingFormat: 'image/png',
        inLanguage: 'en-IN',
        isPartOf: { '@type': 'WebPage', '@id': PAGE_URL },
        mainEntityOfPage: PAGE_URL,
      },
      {
        '@type': 'SoftwareApplication',
        '@id': `${PAGE_URL}#astroroshni-android-app`,
        name: 'AstroRoshni: AI Kundli & Chat',
        operatingSystem: 'Android',
        applicationCategory: 'LifestyleApplication',
        description:
          'AI-powered Vedic astrology app: instant Kundli, horoscope, kundali matching, past life karma analysis, and live chat with an AI astrologer.',
        image: imageUrl,
        installUrl: PLAY_STORE_URL,
        downloadUrl: PLAY_STORE_URL,
        offers: {
          '@type': 'Offer',
          price: '0',
          priceCurrency: 'INR',
          availability: 'https://schema.org/InStock',
        },
        publisher: {
          '@type': 'Organization',
          name: 'AstroRoshni',
          url: SITE_URL,
        },
      },
    ],
  };
}
