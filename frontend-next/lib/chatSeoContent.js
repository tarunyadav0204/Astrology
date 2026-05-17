/** Public copy + FAQ for /chat (indexed layer). */

export const CHAT_CANONICAL = 'https://astroroshni.com/chat';

export const CHAT_MODES = [
  {
    id: 'single',
    title: 'Single Chart',
    icon: '✨',
    subtitle: 'Your birth chart + personal life guidance',
    body:
      'Ask career, marriage, health, finance, dasha, transit, yoga, dosha, and timing questions grounded in your Janam Kundli. Every reply uses your saved date, time, and place of birth—not generic sun-sign text.',
  },
  {
    id: 'partnership',
    title: 'Partnership',
    icon: '💞',
    subtitle: 'Two charts + relationship context',
    body:
      'Select two birth charts and a relationship type (spouse, partner, parent–child, business, etc.). Get synastry-style guidance on chemistry, friction, commitment timing, and practical conversation topics.',
  },
  {
    id: 'mundane',
    title: 'Mundane',
    icon: '🌍',
    subtitle: 'Global events + trend dynamics',
    body:
      'Explore collective trends, elections, markets, geopolitics, and event categories by country or region. Mundane mode uses location and timing context rather than a personal natal chart.',
  },
];

export const CHAT_CAPABILITIES = [
  {
    title: 'Chart-native answers',
    desc: 'Responses reference your Lagna, houses, planetary strengths, aspects, and divisional context instead of generic horoscope paragraphs.',
  },
  {
    title: 'Dasha & timing',
    desc: 'Mahadasha, Antardasha, and Pratyantardasha periods are interpreted for when themes are likely to activate—not vague “soon” predictions.',
  },
  {
    title: 'Transit correlation',
    desc: 'Current Gochar (transits) are mapped to your birth chart for event windows, mood shifts, and opportunity phases.',
  },
  {
    title: 'Yoga & dosha detection',
    desc: 'Identifies combinations like Raja, Dhana, Gaja Kesari yogas and doshas that shape life trajectory, with plain-language meaning.',
  },
  {
    title: 'Nakshatra depth',
    desc: 'Moon nakshatra themes, padas, and karmic undertones for personality, habits, and life purpose.',
  },
  {
    title: 'Event period finder',
    desc: 'Discover high-probability periods when a chosen life area (career move, marriage, relocation, etc.) may peak across a selected year.',
  },
  {
    title: 'Enhanced deep analysis',
    desc: 'Optional deeper pass with multi-layered chart synthesis, house lordships, and richer remedial context when you need more detail.',
  },
  {
    title: 'Remedial guidance',
    desc: 'Personalised mantra, gemstone, and ritual suggestions aligned to planetary strengths and weaknesses in your chart.',
  },
  {
    title: 'Instant concise mode',
    desc: 'Faster, shorter replies when you want a quick chart check without a long narrative.',
  },
  {
    title: 'Voice chat with Tara',
    desc: 'Hands-free speech conversation with the same chart context—ideal when you are away from the keyboard.',
  },
  {
    title: 'Listen as podcast',
    desc: 'Turn a written answer into an audio-style podcast summary you can replay on the go.',
  },
  {
    title: 'Saved charts workflow',
    desc: 'Pick from saved profiles so you do not re-enter birth details for every session.',
  },
];

export const CHAT_TOPIC_AREAS = [
  'Career, business, and professional direction',
  'Marriage, love, and relationship decisions',
  'Health tendencies and supportive lifestyle timing',
  'Wealth, property, and financial cycles',
  'Education, exams, and skill-building phases',
  'Family, children, and progeny themes',
  'Relocation, travel, and foreign connections',
  'Spiritual growth, remedies, and karmic patterns',
  'Legal matters, disputes, and conflict windows',
  'General life overview and yearly focus',
];

export const CHAT_HOW_STEPS = [
  {
    title: 'Choose your mode',
    desc: 'Single chart for personal questions, Partnership for two people, or Mundane for collective/global topics.',
  },
  {
    title: 'Set up birth data',
    desc: 'Select a saved chart or enter date, accurate birth time, and place. Partnership mode walks you through both charts and relationship type.',
  },
  {
    title: 'Ask in plain English',
    desc: 'Type naturally—no need to know Sanskrit terms. The system maps your question to relevant houses, dashas, and transits.',
  },
  {
    title: 'Read chart-aware replies',
    desc: 'Answers stream in real time with optional chart context, follow-up suggestions, and deeper analysis when you need it.',
  },
];

export const CHAT_SAMPLE_EXCERPT =
  'Your Venus Mahadasha with Jupiter Antardasha suggests a window where partnership and creative collaboration strengthen, especially while transiting Jupiter aspects your 7th lord. If marriage is the focus, compare this period with Navamsa support and any Manglik considerations before fixing a date—not every “good” dasha means immediate action without chart balance.';

export const CHAT_FAQ = [
  {
    question: 'What is AstroRoshni AI astrologer chat?',
    answer:
      'It is a Vedic astrology chat that reads your real birth chart (Janam Kundli) and answers in plain language. Unlike generic horoscope bots, replies use houses, dashas, transits, yogas, and divisional context calculated from your date, time, and place of birth.',
  },
  {
    question: 'Do I need to log in to read about the chat features?',
    answer:
      'No. This page explains everything the chat offers—modes, topics, credits, and limitations—without sign-in. To start a live session with your chart, sign in and open the chat tool.',
  },
  {
    question: 'What birth details are required?',
    answer:
      'For Single Chart and Partnership modes you need date of birth, as accurate a birth time as possible, and place of birth. Better timing improves ascendant, houses, dasha, and event-period accuracy. Mundane mode uses country/region and event context instead of a personal chart.',
  },
  {
    question: 'What is the difference between Single Chart and Partnership chat?',
    answer:
      'Single Chart focuses on one person’s life themes. Partnership mode loads two charts plus a relationship label so answers address compatibility, dynamics, and timing between those two people—not just one horoscope in isolation.',
  },
  {
    question: 'What is Mundane chat used for?',
    answer:
      'Mundane mode is for collective questions: geopolitical trends, elections, markets, natural events, or category-based forecasts tied to a country or region. It is not a substitute for personal life guidance from your natal chart.',
  },
  {
    question: 'Can I ask about career, marriage, and health in one session?',
    answer:
      'Yes. You can ask follow-up questions in the same thread. For a structured scan of when a specific event type may peak, use the event period finder flow from the greeting options.',
  },
  {
    question: 'Is there a free question?',
    answer:
      'Eligible accounts may receive a free first question in standard single-chart chat. Partnership, mundane, instant, enhanced, voice, and podcast features may use credits according to your plan and current pricing in the app.',
  },
  {
    question: 'What is instant chat vs detailed replies?',
    answer:
      'Instant mode returns concise, faster answers suited to quick checks. Detailed mode provides longer narrative interpretations with richer chart synthesis. You can switch approaches within a session depending on what you need.',
  },
  {
    question: 'What is voice chat with Tara?',
    answer:
      'Speech chat lets you talk to the AI astrologer using your voice while keeping the same chart setup. It is helpful when you want hands-free guidance after your birth chart is configured.',
  },
  {
    question: 'How accurate is AI Vedic astrology chat?',
    answer:
      'Quality depends on accurate birth time, clear questions, and classical chart calculation. AstroRoshni is guidance for reflection and planning—not a guarantee of outcomes and not a replacement for professional medical, legal, or financial advice.',
  },
];

export function buildChatStructuredData() {
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebPage',
        '@id': `${CHAT_CANONICAL}#webpage`,
        url: CHAT_CANONICAL,
        name: 'AI Vedic Astrologer Chat — Ask Tara | AstroRoshni',
        description:
          'Chart-aware Vedic astrology chat: single chart, partnership, and mundane modes with dasha, transit, yoga, and timing guidance.',
        isPartOf: { '@type': 'WebSite', name: 'AstroRoshni', url: 'https://astroroshni.com' },
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://astroroshni.com/' },
          { '@type': 'ListItem', position: 2, name: 'AI Astrologer Chat', item: CHAT_CANONICAL },
        ],
      },
      {
        '@type': 'WebApplication',
        name: 'AstroRoshni AI Astrologer Chat',
        url: CHAT_CANONICAL,
        applicationCategory: 'LifestyleApplication',
        operatingSystem: 'Web',
        offers: {
          '@type': 'Offer',
          price: '0',
          priceCurrency: 'INR',
          description: 'Free guide on this page; live chat may include a free first question and credit-based premium features',
        },
        description:
          'Vedic birth-chart chat with single chart, partnership, mundane modes, dasha timing, transits, yogas, event periods, voice chat, and podcast summaries.',
      },
      {
        '@type': 'FAQPage',
        mainEntity: CHAT_FAQ.map((item) => ({
          '@type': 'Question',
          name: item.question,
          acceptedAnswer: { '@type': 'Answer', text: item.answer },
        })),
      },
    ],
  };
}
