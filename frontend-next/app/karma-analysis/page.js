import KarmaSiteHeader from '../../components/KarmaSiteHeader';
import KarmaAnalysisLanding from '../../components/KarmaAnalysisLanding';
import KarmaTool from '../../components/KarmaTool';
import { buildKarmaStructuredData } from '../../lib/karmaSeoContent';

const KEYWORDS = [
  'past life karma analysis',
  'vedic past life astrology',
  'karmic patterns birth chart',
  'D60 shashtiamsa',
  'past life reading by date of birth',
  '12th house past life',
  'Rahu Ketu karma',
  'karmic debt astrology',
].join(', ');

export const metadata = {
  title: 'Past Life Karma Analysis — Vedic Birth Chart Reading | AstroRoshni',
  description:
    'Discover past-life themes and karmic patterns from your Vedic chart (D9, D60, 12th house, Rahu–Ketu). Free guide plus personalised karma report on AstroRoshni.',
  keywords: KEYWORDS,
  alternates: {
    canonical: 'https://astroroshni.com/karma-analysis/',
  },
  openGraph: {
    title: 'Past Life Karma Analysis | AstroRoshni',
    description:
      'Vedic past-life & karmic pattern analysis from your birth chart. Free guide + personalised report.',
    url: 'https://astroroshni.com/karma-analysis/',
    siteName: 'AstroRoshni',
    type: 'website',
    images: [{ url: 'https://astroroshni.com/images/astroroshni-og-image.jpg' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Past Life Karma Analysis | AstroRoshni',
    description: 'Karmic patterns from D9, D60, 12th house & lunar nodes — Vedic birth chart reading.',
    images: ['https://astroroshni.com/images/astroroshni-twitter-image.jpg'],
  },
};

export default function KarmaAnalysisPage() {
  const jsonLd = buildKarmaStructuredData();

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <KarmaSiteHeader />
      <div className="karma-page-wrap">
        <KarmaAnalysisLanding />
        <KarmaTool />
      </div>
    </>
  );
}
