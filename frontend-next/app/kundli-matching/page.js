import KundliSiteHeader from '../../components/KundliSiteHeader';
import KundliMatchingLanding from '../../components/KundliMatchingLanding';
import { buildKundliStructuredData } from '../../lib/kundliSeoContent';

const KEYWORDS = [
  'kundli matching',
  'guna milan',
  'ashtakoot matching',
  'horoscope matching for marriage',
  'manglik dosha matching',
  'online kundli matching',
  'vedic compatibility analysis',
  'marriage matching by date of birth',
].join(', ');

export const metadata = {
  title: 'Kundli Matching — Ashtakoot Guna Milan & AI Report | AstroRoshni',
  description:
    'Match two Kundlis with Ashtakoot Guna Milan, Manglik analysis, Navamsa, timing climate, and AI-based marriage compatibility guidance.',
  keywords: KEYWORDS,
  alternates: {
    canonical: 'https://astroroshni.com/kundli-matching',
  },
  openGraph: {
    title: 'Kundli Matching | AstroRoshni',
    description:
      'Vedic Kundli matching with 36-point Guna Milan, Manglik checks, Navamsa, timing, and AI compatibility report.',
    url: 'https://astroroshni.com/kundli-matching',
    siteName: 'AstroRoshni',
    type: 'website',
    images: [{ url: 'https://astroroshni.com/images/astroroshni-og-image.jpg' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Kundli Matching | AstroRoshni',
    description: 'Ashtakoot Guna Milan, Manglik analysis, Navamsa, and AI-based compatibility guidance.',
    images: ['https://astroroshni.com/images/astroroshni-twitter-image.jpg'],
  },
};

export default function KundliMatchingPage() {
  const jsonLd = buildKundliStructuredData();

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <KundliSiteHeader />
      <div className="karma-page-wrap kundli-page-wrap">
        <KundliMatchingLanding />
      </div>
    </>
  );
}
