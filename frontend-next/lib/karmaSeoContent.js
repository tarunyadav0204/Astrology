/** Public copy + FAQ for /karma-analysis (indexed layer). */

export const KARMA_CANONICAL = 'https://astroroshni.com/karma-analysis';

export const KARMA_REPORT_SECTIONS = [
  { icon: '🕉️', title: 'Introduction', desc: 'Overview of your soul journey and karmic themes from the chart.' },
  { icon: '🌟', title: 'Past-life impressions', desc: 'Patterns carried from previous incarnations visible in divisional charts.' },
  { icon: '🎯', title: 'Current-life purpose', desc: 'Why certain lessons repeat and what you are here to complete.' },
  { icon: '⚖️', title: 'Karmic debts & balances', desc: 'Areas of excess, deficiency, and reconciliation in this lifetime.' },
  { icon: '💎', title: 'Spiritual strengths', desc: 'Gifts and dharmic support shown by benefic placements.' },
  { icon: '🔱', title: 'Challenges & shadow themes', desc: 'Rahu–Ketu axis, Saturn, and 12th-house indications.' },
  { icon: '👪', title: 'Relationship karma', desc: 'Family, partnership, and ancestral threads in the chart.' },
  { icon: '🙏', title: 'Remedies & practices', desc: 'Traditional-aligned suggestions for balance (not medical advice).' },
];

export const KARMA_FAQ = [
  {
    question: 'What is past life karma in Vedic astrology?',
    answer:
      'In Jyotish, karma is the accumulated impression of past actions (sanchita) and what is active now (prarabdha). Past-life themes are read through the Navamsa (D9), Shashtiamsa (D60), the 12th house, nodes (Rahu–Ketu), and Saturn—not through guesswork, but through the birth chart calculated for your date, time, and place of birth.',
  },
  {
    question: 'Which divisional chart is used for past life—D9 or D60?',
    answer:
      'Both matter. Navamsa (D9) is widely used for the soul’s deeper direction and dharma. Shashtiamsa (D60) is emphasised in classical texts for subtler karmic residue and past-life tone. AstroRoshni’s karma analysis weighs D9 and D60 together with the radix chart, dashas, and node positions.',
  },
  {
    question: 'Can Vedic astrology show karmic debt?',
    answer:
      'Astrology can highlight areas of repeated struggle, obligation, or “unfinished business”—often linked to Saturn, the 12th house, certain nakshatras, and D60 placements. This is symbolic and interpretive guidance, not a literal ledger of debts. It helps you understand patterns, not replace professional counselling or medical care.',
  },
  {
    question: 'What does the 12th house indicate about past lives?',
    answer:
      'The 12th house relates to liberation (moksha), loss, isolation, foreign lands, sleep, and the subconscious. Strong 12th-house themes can point to past-life withdrawal, service, or expenses of energy that still echo in this life. Context always comes from the full chart, not one house alone.',
  },
  {
    question: 'How are Rahu and Ketu linked to past-life karma?',
    answer:
      'Rahu and Ketu are the lunar nodes—points where the Moon’s path crosses the ecliptic. They often describe obsessive growth (Rahu) and release or mastery (Ketu). Many traditions associate them with sudden karmic acceleration: talents from past effort (Ketu) and desires still pulling you forward (Rahu).',
  },
  {
    question: 'Do I need an exact birth time for karma analysis?',
    answer:
      'An accurate birth time improves house cusps, ascendant, and divisional charts. If your time is approximate, results may be less precise for house-based factors; still, many node and planetary-sign themes remain useful. Enter the most accurate time you have from a birth certificate or family record.',
  },
  {
    question: 'How is AstroRoshni’s karma analysis different from a psychic past-life reading?',
    answer:
      'Our report is generated from your Vedic birth chart (Parashari-style calculations plus D9/D60) and AI-assisted interpretation trained on traditional frameworks. It is structured, chart-based, and reproducible for the same birth data—not a spontaneous psychic narrative.',
  },
  {
    question: 'Is the personalised karma report free?',
    answer:
      'The educational guide on this page is free to read. The full personalised karma analysis uses credits on your AstroRoshni account after you sign in and save a birth chart. Pricing is shown before you confirm.',
  },
  {
    question: 'Will my birth details and report be private?',
    answer:
      'Your chart is tied to your account. We do not publish individual reports as public web pages. See our Privacy Policy for how data is stored and used.',
  },
  {
    question: 'Can I run karma analysis for another person’s chart?',
    answer:
      'Yes. After signing in, create or select a saved birth chart for that person (with their consent), then start the analysis from the tool below.',
  },
];

export const KARMA_SAMPLE_EXCERPT =
  'A chart with Ketu influencing the 12th house while Saturn aspects the Moon may suggest a soul that has spent many lives in service, retreat, or responsibility for others—sometimes at the cost of personal rest. In this incarnation, the lesson is not to abandon service, but to balance it with boundaries. Rahu in an angular house can pull attention toward worldly achievement; the karmic task is to pursue goals without repeating old patterns of exhaustion. This is illustrative only; your report is built from your exact birth data.';

export function buildKarmaStructuredData() {
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebPage',
        '@id': `${KARMA_CANONICAL}#webpage`,
        url: KARMA_CANONICAL,
        name: 'Past Life Karma Analysis — Vedic Birth Chart | AstroRoshni',
        description:
          'Vedic past-life and karmic pattern analysis using D9, D60, 12th house, and lunar nodes. Free guide plus personalised report from your birth chart.',
        isPartOf: { '@type': 'WebSite', name: 'AstroRoshni', url: 'https://astroroshni.com' },
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://astroroshni.com/' },
          { '@type': 'ListItem', position: 2, name: 'Past Life Karma Analysis', item: KARMA_CANONICAL },
        ],
      },
      {
        '@type': 'WebApplication',
        name: 'AstroRoshni Past Life Karma Analysis',
        url: KARMA_CANONICAL,
        applicationCategory: 'LifestyleApplication',
        operatingSystem: 'Web',
        offers: {
          '@type': 'Offer',
          price: '0',
          priceCurrency: 'INR',
          description: 'Free educational guide; personalised report uses credits',
        },
        description:
          'Personalised Vedic karma and past-life themes from your birth chart, including Navamsa and Shashtiamsa.',
      },
      {
        '@type': 'FAQPage',
        mainEntity: KARMA_FAQ.map((item) => ({
          '@type': 'Question',
          name: item.question,
          acceptedAnswer: { '@type': 'Answer', text: item.answer },
        })),
      },
    ],
  };
}
