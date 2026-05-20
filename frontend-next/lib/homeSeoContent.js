import { chatAppHref, kundliAppHref } from './navigation';

/** Crawlable tool cards and “how it works” copy for the static homepage (Next). */
export const HOME_METHOD_CARDS = [
  {
    title: 'How accurate is Tara AI astrology?',
    answer:
      'Tara improves prediction quality by reading the complete Vedic chart instead of only a Sun sign. It combines birth chart placements, divisional charts, dashas, transits, yogas, and Ashtakavarga strength into one synthesis.',
    links: [
      { label: 'Ask Tara', href: '/chat' },
      { label: 'Past-life karma analysis', href: '/karma-analysis' },
    ],
  },
  {
    title: 'What calculations does Tara use?',
    answer:
      'Tara uses Swiss Ephemeris precision for planetary positions, then applies Vedic layers such as Vimshottari Dasha, Jaimini Chara Dasha, Yogini Dasha, divisional charts, Ashtakavarga, yoga detection, and transit overlays.',
    links: [
      { label: 'Daily Panchang', href: '/panchang' },
      { label: 'AI chat guide', href: '/chat' },
    ],
  },
  {
    title: 'How is Tara different from generic horoscopes?',
    answer:
      'Generic horoscopes usually describe broad zodiac trends. Tara uses your date, exact time, and place of birth to calculate a personal Kundli, then answers questions against your own chart and current timing periods.',
    links: [
      { label: 'Create Kundli in chat', href: chatAppHref() },
      { label: 'Kundli matching', href: '/kundli-matching' },
    ],
  },
  {
    title: 'What birth details are required?',
    answer:
      'For the most accurate Kundli, enter date of birth, birth time, and birth place. Birth time sets the Lagna, houses, Moon nakshatra pada, dashas, and divisional chart details used in deeper predictions.',
    links: [
      { label: 'Open chat tool', href: chatAppHref() },
      { label: 'Match two Kundlis', href: kundliAppHref() },
    ],
  },
];

export const HOME_FEATURES = [
  {
    title: 'AI Vedic Astrologer Chat',
    body: 'Ask Tara career, marriage, health, wealth, dasha, transit, and timing questions from your real Janam Kundli.',
    href: '/chat',
  },
  {
    title: 'Kundli Matching',
    body: 'Compare two charts with Ashtakoot Guna Milan, Manglik checks, Navamsa context, and AI compatibility guidance.',
    href: '/kundli-matching',
  },
  {
    title: 'Past Life Karma Analysis',
    body: 'Study karmic patterns through D9, D60, the 12th house, Saturn, Rahu-Ketu, and chart-based interpretation.',
    href: '/karma-analysis',
  },
  {
    title: 'Daily Panchang',
    body: 'Check tithi, nakshatra, yoga, karana, vara, and daily Vedic timing signals for planning.',
    href: '/panchang',
  },
];
