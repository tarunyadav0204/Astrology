/** Public copy + FAQ for /reports (indexed SEO layer). */

export const REPORTS_CANONICAL = 'https://astroroshni.com/reports/';

export const REPORT_TYPES = [
  {
    title: 'Partnership Report',
    status: 'Available now',
    desc: 'A premium 20+ page PDF for marriage, business, parent–child, or any two-person relationship study — with chart overlays, timing, strengths, friction points, remedies, and clear next steps.',
  },
  {
    title: 'Career Report',
    status: 'Coming soon',
    desc: 'A future report for work style, opportunity timing, and career direction from a single Vedic chart.',
  },
  {
    title: 'Wealth Report',
    status: 'Coming soon',
    desc: 'A future report for income flow, saving patterns, and wealth growth themes.',
  },
  {
    title: 'Health Report',
    status: 'Coming soon',
    desc: 'A future report for body constitution signals, care points, and wellness habits.',
  },
  {
    title: 'Progeny Report',
    status: 'Coming soon',
    desc: 'A future report for progeny timing and related chart indicators.',
  },
];

export const REPORT_STUDIO_STEPS = [
  {
    title: 'Choose the report type',
    desc: 'Start with Partnership Report for any two-person study. More report types are on the roadmap.',
  },
  {
    title: 'Select both charts',
    desc: 'Pick two saved birth charts or enter date, time, and place for each person.',
  },
  {
    title: 'Confirm language and generate',
    desc: 'Choose the AI narrative language, then generate a structured PDF you can open, download, and share.',
  },
];

export const REPORT_PDF_SECTIONS = [
  {
    title: 'Compatibility overview',
    desc: 'Headline verdict, overall tone, and a clear summary of how the two charts relate.',
  },
  {
    title: 'Ashtakoot and classic matching',
    desc: 'Guna Milan context, Manglik balance, and traditional signals explained in readable language.',
  },
  {
    title: 'Chart overlays and chemistry',
    desc: 'D1/D9 overlays, emotional fit, attraction patterns, and cross-chart relationship indicators.',
  },
  {
    title: 'Timing windows',
    desc: 'Joint readiness climate from dasha and transit context — when commitment or careful pacing makes sense.',
  },
  {
    title: 'Strengths and friction points',
    desc: 'What tends to support the bond, where pressure builds, and how those patterns may show up in real life.',
  },
  {
    title: 'Remedies and next steps',
    desc: 'Priority actions, practical guidance, and remedial direction to discuss with a qualified astrologer if needed.',
  },
];

export const REPORT_VS_OTHER_TOOLS = [
  {
    title: 'Reports Studio vs Kundli Matching',
    body: 'Kundli Matching gives a fast Ashtakoot score, Manglik check, and free compatibility snapshot. Reports Studio builds a much deeper premium PDF — chapter-level AI narrative, chart overlays, timing, remedies, and a shareable document for serious decisions.',
  },
  {
    title: 'Reports Studio vs AI Chat',
    body: 'Chat is best for follow-up questions and conversational exploration. A report is best when you want one polished, structured PDF covering the full partnership picture in one place.',
  },
  {
    title: 'Reports Studio vs single-chart analysis',
    body: 'Marriage, career, or wealth analysis pages study one chart in depth. Partnership Reports compare two charts together — the relationship itself is the subject.',
  },
];

export const REPORTS_FAQ = [
  {
    question: 'What is AstroRoshni Reports Studio?',
    answer:
      'Reports Studio creates premium, structured Vedic astrology PDF reports. The first available type is the Partnership Report — a deep two-person study for marriage, business, parent–child, or other relationship contexts.',
  },
  {
    question: 'What is included in the Partnership Report PDF?',
    answer:
      'A typical Partnership Report is a 20+ page PDF with compatibility overview, Ashtakoot and Manglik context, chart overlays, emotional and practical chemistry, timing climate, strengths, friction points, remedies, and clear next steps.',
  },
  {
    question: 'How is this different from free Kundli matching?',
    answer:
      'Free Kundli matching focuses on a quick Guna Milan score and core compatibility signals. The Partnership Report goes further with multi-chapter AI interpretation, full PDF packaging, chart visuals, timing guidance, and remedy-oriented next steps.',
  },
  {
    question: 'Do I need exact birth time for both people?',
    answer:
      'Yes for best results. Accurate date, time, and place improve ascendant, houses, Navamsa (D9), Manglik assessment, and timing. Approximate times reduce reliability of house-based and divisional insights.',
  },
  {
    question: 'How many credits does a Partnership Report cost?',
    answer:
      'Partnership Reports use credits from your AstroRoshni balance. The exact cost is shown in Reports Studio before you confirm. Opening an already-generated report for the same pair and language does not charge again; regenerate does.',
  },
  {
    question: 'Can I reopen a report I already generated?',
    answer:
      'Yes. If a report already exists for the same two charts and language, Reports Studio shows Open instead of Generate, and reopening is free. Use Regenerate only when you want a fresh AI reading.',
  },
  {
    question: 'Which languages are supported?',
    answer:
      'The AI narrative inside the PDF can be generated in multiple languages supported by AstroRoshni (including English and Hindi). Choose the language in step 3 before generating.',
  },
  {
    question: 'How long does report generation take?',
    answer:
      'Most partnership reports finish within a few minutes. The studio shows progress while charts are read and chapters are assembled. Once ready, you can open the PDF in the browser.',
  },
  {
    question: 'Is my birth data private?',
    answer:
      'Birth details are used to calculate charts and generate your report. They are not published on the public SEO page. Use your account’s saved charts so you do not re-enter the same details every time.',
  },
  {
    question: 'Can astrology reports guarantee relationship outcomes?',
    answer:
      'No. Astrology highlights tendencies, strengths, and caution areas. Real outcomes also depend on maturity, communication, values, and free will. Treat the report as structured guidance for reflection, not a substitute for counselling or personal judgment.',
  },
  {
    question: 'Can I use the Partnership Report for business or parent–child relationships?',
    answer:
      'Yes. The same two-chart framework can illuminate business partnerships, parent–child dynamics, and other close relationships — not only marriage matching.',
  },
  {
    question: 'Will there be Career, Wealth, Health, and Progeny reports?',
    answer:
      'Yes. Those single-focus report types are planned in Reports Studio. Partnership Report is available now; the others appear as Coming soon until they ship.',
  },
];

export function buildReportsStructuredData() {
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebPage',
        '@id': `${REPORTS_CANONICAL}#webpage`,
        url: REPORTS_CANONICAL,
        name: 'Reports Studio — Premium Vedic Partnership PDF Reports | AstroRoshni',
        description:
          'Create premium Vedic astrology PDF reports. Partnership Report covers two charts with timing, strengths, remedies, and clear takeaways.',
        isPartOf: { '@type': 'WebSite', name: 'AstroRoshni', url: 'https://astroroshni.com' },
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://astroroshni.com/' },
          { '@type': 'ListItem', position: 2, name: 'Reports Studio', item: REPORTS_CANONICAL },
        ],
      },
      {
        '@type': 'WebApplication',
        name: 'AstroRoshni Reports Studio',
        url: REPORTS_CANONICAL,
        applicationCategory: 'LifestyleApplication',
        operatingSystem: 'Web',
        offers: {
          '@type': 'Offer',
          priceCurrency: 'INR',
          description: 'Partnership Report uses credits; reopen of an existing cached report is free',
        },
        description:
          'Premium Vedic partnership PDF reports with chart overlays, timing climate, strengths, friction points, and remedies.',
      },
      {
        '@type': 'FAQPage',
        mainEntity: REPORTS_FAQ.map((item) => ({
          '@type': 'Question',
          name: item.question,
          acceptedAnswer: { '@type': 'Answer', text: item.answer },
        })),
      },
    ],
  };
}
