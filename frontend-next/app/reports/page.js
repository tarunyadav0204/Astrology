import ReportsSiteHeader from '../../components/ReportsSiteHeader';
import ReportsLanding from '../../components/ReportsLanding';
import { buildReportsStructuredData } from '../../lib/reportsSeoContent';
import './reports.css';

const KEYWORDS = [
  'vedic partnership report',
  'marriage compatibility PDF',
  'premium kundli report',
  'two chart astrology report',
  'partnership astrology PDF',
  'ashtakoot detailed report',
  'online vedic relationship report',
  'astoroshni reports studio',
].join(', ');

export const metadata = {
  title: 'Reports Studio — Premium Vedic Partnership PDF Reports | AstroRoshni',
  description:
    'Create premium Vedic partnership PDF reports from two birth charts. Chart overlays, timing, strengths, remedies, and clear takeaways in a shareable 20+ page report.',
  keywords: KEYWORDS,
  alternates: {
    canonical: 'https://astroroshni.com/reports/',
  },
  openGraph: {
    title: 'Reports Studio | AstroRoshni',
    description:
      'Premium Vedic partnership PDF reports with timing climate, strengths, friction points, and remedies.',
    url: 'https://astroroshni.com/reports/',
    siteName: 'AstroRoshni',
    type: 'website',
    images: [{ url: 'https://astroroshni.com/images/astroroshni-og-image.jpg' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Reports Studio | AstroRoshni',
    description: 'Deepest two-chart Vedic analysis as a polished PDF report.',
    images: ['https://astroroshni.com/images/astroroshni-twitter-image.jpg'],
  },
};

export default function ReportsPage() {
  const jsonLd = buildReportsStructuredData();

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <ReportsSiteHeader />
      <div className="karma-page-wrap reports-page-wrap">
        <ReportsLanding />
      </div>
    </>
  );
}
