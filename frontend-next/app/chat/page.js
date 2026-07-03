import ChatSiteHeader from '../../components/ChatSiteHeader';
import ChatLanding from '../../components/ChatLanding';
import { buildChatStructuredData } from '../../lib/chatSeoContent';
import './chat.css';

const KEYWORDS = [
  'ai astrologer chat',
  'vedic astrology chat online',
  'birth chart questions',
  'ask astrologer online',
  'kundli chat',
  'horoscope chat bot',
  'jyotish ai',
  'partnership astrology chat',
  'dasha prediction chat',
  'online vedic astrologer',
  'ai kundli reading chat',
  'astroroshni ask tara',
].join(', ');

export const metadata = {
  title: 'AI Vedic Astrologer Chat — Ask Tara About Your Kundli | AstroRoshni',
  description:
    'Chart-aware Vedic astrology chat: single chart, partnership, and mundane modes with dasha, transit, yoga, event periods, voice chat, and podcast summaries.',
  keywords: KEYWORDS,
  alternates: {
    canonical: 'https://astroroshni.com/chat/',
  },
  openGraph: {
    title: 'AI Vedic Astrologer Chat | AstroRoshni',
    description:
      'Ask Tara anything about your Janam Kundli—career, marriage, dasha, transits, yogas, and timing—with real chart calculation.',
    url: 'https://astroroshni.com/chat/',
    siteName: 'AstroRoshni',
    type: 'website',
    images: [{ url: 'https://astroroshni.com/images/astroroshni-og-image.jpg' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AI Vedic Astrologer Chat | AstroRoshni',
    description:
      'Birth-chart AI chat with single, partnership, and mundane modes—dasha, transits, yogas, and timing guidance.',
    images: ['https://astroroshni.com/images/astroroshni-twitter-image.jpg'],
  },
};

export default function ChatPage() {
  const jsonLd = buildChatStructuredData();

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <ChatSiteHeader />
      <div className="karma-page-wrap chat-page-wrap">
        <ChatLanding />
      </div>
    </>
  );
}
