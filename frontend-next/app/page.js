import HomeLanding from '../components/HomeLanding';
import {
  buildHomeAccuracyProofStructuredData,
  buildHomePlayStoreBannerStructuredData,
  organizationLd,
  websiteLd,
} from '../lib/craHomeSeo';
import './home.css';

const KEYWORDS = [
  'vedic astrology',
  'horoscope',
  'kundli',
  'birth chart',
  'astrology predictions',
  'marriage matching',
  'daily horoscope',
  'astrologer consultation',
  'panchang',
  'muhurat',
  'ai astrologer',
  'ask tara',
  'janam kundli',
].join(', ');

/** Aligned with CRA `generatePageSEO('home')` / `SEO_CONFIG.pages.home`. */
export const metadata = {
  title: 'AstroRoshni - Best Vedic Astrology & Horoscope Predictions Online',
  description:
    'Get accurate Vedic astrology predictions, free Kundli, horoscope matching, daily horoscopes & expert astrologer consultations. Trusted by 50,000+ users worldwide.',
  keywords: KEYWORDS,
  alternates: {
    canonical: '/',
  },
  openGraph: {
    title: 'AstroRoshni - Best Vedic Astrology & Horoscope Predictions Online',
    description:
      'Get accurate Vedic astrology predictions, free Kundli, horoscope matching, daily horoscopes & expert astrologer consultations. Trusted by 50,000+ users worldwide.',
    url: 'https://astroroshni.com/',
    siteName: 'AstroRoshni',
    type: 'website',
    images: [{ url: 'https://astroroshni.com/images/astroroshni-og-image.jpg' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AstroRoshni - Best Vedic Astrology & Horoscope Predictions Online',
    description:
      'Get accurate Vedic astrology predictions, free Kundli, horoscope matching, daily horoscopes & expert astrologer consultations. Trusted by 50,000+ users worldwide.',
    images: ['https://astroroshni.com/images/astroroshni-twitter-image.jpg'],
  },
};

export default function HomePage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(buildHomeAccuracyProofStructuredData()) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(buildHomePlayStoreBannerStructuredData()) }}
      />
      <header className="karma-site-header">
        <div className="karma-site-header-inner">
          <a href="/" className="karma-site-logo">
            AstroRoshni
          </a>
          <nav className="karma-site-nav" aria-label="Main">
            <a href="/panchang">Panchang</a>
            <a href="/chat">AI chat</a>
            <a href="/kundli-matching">Kundli matching</a>
            <a href="/karma-analysis">Karma analysis</a>
            <a href="/">Open app</a>
          </nav>
        </div>
      </header>
      <HomeLanding />
    </>
  );
}
