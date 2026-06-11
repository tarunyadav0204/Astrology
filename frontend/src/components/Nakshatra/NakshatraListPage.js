import React, { useMemo, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import SEOHead from '../SEO/SEOHead';
import { generatePageSEO } from '../../config/seo.config';
import './NakshatraListPage.css';

const FALLBACK_NAKSHATRAS = [
  ['Ashwini', 'Ketu', 'Ashwini Kumaras', 'Light/Swift', '0°00 Aries - 13°20 Aries', 'Horse head', 'Quick starts, healing ability, initiative, movement, and bold first steps.'],
  ['Bharani', 'Venus', 'Yama', 'Fierce/Ugra', '13°20 Aries - 26°40 Aries', 'Yoni', 'Responsibility, endurance, creativity, moral pressure, and transformation.'],
  ['Krittika', 'Sun', 'Agni', 'Mixed', '26°40 Aries - 10°00 Taurus', 'Blade', 'Purification, discernment, courage, protection, and sharp decision-making.'],
  ['Rohini', 'Moon', 'Brahma', 'Fixed/Dhruva', '10°00 Taurus - 23°20 Taurus', 'Chariot', 'Growth, beauty, fertility, comfort, material creation, and nourishment.'],
  ['Mrigashira', 'Mars', 'Soma', 'Soft/Mridu', '23°20 Taurus - 6°40 Gemini', 'Deer head', 'Curiosity, searching, learning, travel, sensitivity, and exploration.'],
  ['Ardra', 'Rahu', 'Rudra', 'Sharp/Tikshna', '6°40 Gemini - 20°00 Gemini', 'Teardrop', 'Intensity, research, storms, renewal, emotional cleansing, and breakthroughs.'],
  ['Punarvasu', 'Jupiter', 'Aditi', 'Movable/Chara', '20°00 Gemini - 3°20 Cancer', 'Quiver', 'Return, restoration, teaching, optimism, protection, and second chances.'],
  ['Pushya', 'Saturn', 'Brihaspati', 'Light/Laghu', '3°20 Cancer - 16°40 Cancer', 'Lotus', 'Nourishment, discipline, tradition, care, spiritual growth, and stability.'],
  ['Ashlesha', 'Mercury', 'Nagas', 'Sharp/Tikshna', '16°40 Cancer - 30°00 Cancer', 'Serpent', 'Strategy, intuition, hidden knowledge, psychological insight, and binding power.'],
  ['Magha', 'Ketu', 'Pitrs', 'Fierce/Ugra', '0°00 Leo - 13°20 Leo', 'Throne', 'Ancestry, authority, legacy, status, tradition, and inherited responsibility.'],
  ['Purva Phalguni', 'Venus', 'Bhaga', 'Fierce/Ugra', '13°20 Leo - 26°40 Leo', 'Hammock', 'Pleasure, creativity, attraction, rest, romance, and social enjoyment.'],
  ['Uttara Phalguni', 'Sun', 'Aryaman', 'Fixed/Dhruva', '26°40 Leo - 10°00 Virgo', 'Bed', 'Agreements, patronage, service, friendship, support, and lasting bonds.'],
  ['Hasta', 'Moon', 'Savitar', 'Light/Laghu', '10°00 Virgo - 23°20 Virgo', 'Hand', 'Skill, craft, dexterity, healing touch, wit, and practical manifestation.'],
  ['Chitra', 'Mars', 'Vishvakarma', 'Soft/Mridu', '23°20 Virgo - 6°40 Libra', 'Jewel', 'Design, beauty, structure, charisma, architecture, and refined creation.'],
  ['Swati', 'Rahu', 'Vayu', 'Movable/Chara', '6°40 Libra - 20°00 Libra', 'Young shoot', 'Independence, trade, flexibility, wind-like movement, and self-direction.'],
  ['Vishakha', 'Jupiter', 'Indragni', 'Mixed', '20°00 Libra - 3°20 Scorpio', 'Triumphal arch', 'Ambition, focus, ritual effort, branching paths, and determined growth.'],
  ['Anuradha', 'Saturn', 'Mitra', 'Soft/Mridu', '3°20 Scorpio - 16°40 Scorpio', 'Lotus', 'Friendship, devotion, discipline, success through loyalty, and emotional depth.'],
  ['Jyeshtha', 'Mercury', 'Indra', 'Sharp/Tikshna', '16°40 Scorpio - 30°00 Scorpio', 'Amulet', 'Seniority, protection, power, responsibility, strategy, and crisis control.'],
  ['Mula', 'Ketu', 'Nirriti', 'Sharp/Tikshna', '0°00 Sagittarius - 13°20 Sagittarius', 'Roots', 'Investigation, uprooting, truth-seeking, research, and deep transformation.'],
  ['Purva Ashadha', 'Venus', 'Apas', 'Fierce/Ugra', '13°20 Sagittarius - 26°40 Sagittarius', 'Fan', 'Purification, persuasion, confidence, invincibility, and emotional conviction.'],
  ['Uttara Ashadha', 'Sun', 'Vishvedevas', 'Fixed/Dhruva', '26°40 Sagittarius - 10°00 Capricorn', 'Elephant tusk', 'Victory, ethics, leadership, endurance, responsibility, and lasting achievement.'],
  ['Shravana', 'Moon', 'Vishnu', 'Movable/Chara', '10°00 Capricorn - 23°20 Capricorn', 'Ear', 'Listening, learning, transmission, pilgrimage, reputation, and disciplined study.'],
  ['Dhanishta', 'Mars', 'Vasus', 'Movable/Chara', '23°20 Capricorn - 6°40 Aquarius', 'Drum', 'Rhythm, wealth, community, performance, timing, and coordinated action.'],
  ['Shatabhisha', 'Rahu', 'Varuna', 'Movable/Chara', '6°40 Aquarius - 20°00 Aquarius', 'Circle', 'Healing, secrecy, research, systems, solitude, and unconventional insight.'],
  ['Purva Bhadrapada', 'Jupiter', 'Aja Ekapada', 'Fierce/Ugra', '20°00 Aquarius - 3°20 Pisces', 'Sword', 'Spiritual fire, intensity, austerity, ideals, and transformative commitment.'],
  ['Uttara Bhadrapada', 'Saturn', 'Ahir Budhnya', 'Fixed/Dhruva', '3°20 Pisces - 16°40 Pisces', 'Back legs of bed', 'Depth, patience, stability, inner wisdom, and emotional containment.'],
  ['Revati', 'Mercury', 'Pushan', 'Soft/Mridu', '16°40 Pisces - 30°00 Pisces', 'Fish', 'Completion, safe travel, nourishment, guidance, protection, and gentle prosperity.']
].map(([name, lord, deity, nature, degreeRange, symbol, description], index) => ({
  index: index + 1,
  name,
  lord,
  deity,
  nature,
  degree_range: degreeRange,
  symbol,
  description
}));

const SEO_FAQS = [
  {
    question: 'What are the 27 Nakshatras in Vedic astrology?',
    answer:
      'Nakshatras are the 27 lunar mansions used in Vedic astrology. Each nakshatra covers 13 degrees and 20 minutes of the zodiac and has its own ruling planet, deity, nature, symbol, and interpretive meaning.'
  },
  {
    question: 'How is a nakshatra different from a zodiac sign?',
    answer:
      'A zodiac sign divides the sky into 12 sections of 30 degrees, while a nakshatra divides it into 27 lunar mansions. Nakshatras give a more granular view of temperament, timing, muhurat, dasha, compatibility, and the Moon’s daily movement.'
  },
  {
    question: 'Why is Moon nakshatra important?',
    answer:
      'The Moon nakshatra, or Janma Nakshatra, is central to Vedic astrology because it describes the mind, emotional pattern, instinctive nature, dasha starting point, and many muhurat and compatibility calculations.'
  },
  {
    question: 'What can I see on each nakshatra calendar page?',
    answer:
      'Each nakshatra page shows the annual calendar for that nakshatra with begin and end timings, plus properties such as lord, deity, nature, description, traits, careers, and compatibility where available.'
  },
  {
    question: 'Can nakshatras be used for muhurat?',
    answer:
      'Yes. Nakshatras are widely used in muhurat selection. The nature of the nakshatra helps decide whether a period is better for travel, learning, healing, business, ceremonies, repair, discipline, or avoidance.'
  },
  {
    question: 'Are nakshatra interpretations guaranteed?',
    answer:
      'No. Nakshatra meanings are astrological guidance, not a guarantee. A full reading should also consider the Lagna, Moon, planets, houses, dashas, divisional charts, and real-life context.'
  }
];

function slugifyNakshatra(name) {
  return String(name || '')
    .trim()
    .toLowerCase()
    .replace(/\./g, '')
    .replace(/\s+/g, '-');
}

function normalizeNakshatra(item, index) {
  const fallback = FALLBACK_NAKSHATRAS[index] || {};
  return {
    ...fallback,
    ...item,
    index: Number(item?.index || fallback.index || index + 1),
    degree_range: item?.degree_range || fallback.degree_range,
    symbol: item?.symbol || fallback.symbol,
    description: item?.description || fallback.description
  };
}

const NakshatraListPage = () => {
  const navigate = useNavigate();
  const [nakshatras, setNakshatras] = useState(FALLBACK_NAKSHATRAS);
  const [loading, setLoading] = useState(true);
  const [apiNotice, setApiNotice] = useState('');
  const [user, setUser] = useState(null);
  const [activeLord, setActiveLord] = useState('All');
  const currentYear = new Date().getFullYear();
  const seoData = useMemo(() => generatePageSEO('nakshatrasList', { path: '/nakshatras' }), []);

  const lordFilters = useMemo(
    () => ['All', ...Array.from(new Set(FALLBACK_NAKSHATRAS.map((n) => n.lord)))],
    []
  );

  const visibleNakshatras = useMemo(
    () => activeLord === 'All' ? nakshatras : nakshatras.filter((n) => n.lord === activeLord),
    [activeLord, nakshatras]
  );

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        setUser(null);
      }
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const fetchNakshatras = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/nakshatras/list');
        if (!response.ok) throw new Error('Failed to fetch nakshatras');
        const data = await response.json();
        const apiNakshatras = Array.isArray(data?.nakshatras) ? data.nakshatras : [];
        if (!cancelled && apiNakshatras.length) {
          setNakshatras(apiNakshatras.map(normalizeNakshatra));
          setApiNotice('');
        }
      } catch {
        if (!cancelled) {
          setNakshatras(FALLBACK_NAKSHATRAS);
          setApiNotice('Showing the classical 27 nakshatra reference. Live calendar data opens on each nakshatra page.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchNakshatras();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleNakshatraClick = (nakshatraName) => {
    navigate(`/nakshatra/${slugifyNakshatra(nakshatraName)}/${currentYear}`);
  };

  return (
    <div
      className="nakshatra-list-page"
      style={{ '--nakshatra-hero-image': `url(${process.env.PUBLIC_URL || ''}/images/software/birth-chart.png)` }}
    >
      <SEOHead
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={{
          '@context': 'https://schema.org',
          '@graph': [
            {
              '@type': 'CollectionPage',
              name: '27 Nakshatras in Vedic Astrology',
              url: 'https://astroroshni.com/nakshatras',
              description: seoData.description,
              isPartOf: {
                '@type': 'WebSite',
                name: 'AstroRoshni',
                url: 'https://astroroshni.com'
              }
            },
            {
              '@type': 'ItemList',
              name: '27 Nakshatra Names and Lords',
              numberOfItems: 27,
              itemListElement: FALLBACK_NAKSHATRAS.map((nakshatra) => ({
                '@type': 'ListItem',
                position: nakshatra.index,
                name: `${nakshatra.name} Nakshatra`,
                url: `https://astroroshni.com/nakshatra/${slugifyNakshatra(nakshatra.name)}/${currentYear}`
              }))
            },
            {
              '@type': 'FAQPage',
              mainEntity: SEO_FAQS.map((item) => ({
                '@type': 'Question',
                name: item.question,
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: item.answer
                }
              }))
            }
          ]
        }}
      />
      <NavigationHeader
        compact
        user={user}
        onLogin={() => navigate('/')}
        onLogout={() => {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
          navigate('/');
        }}
      />

      <main className="nakshatra-list-main">
        <section className="nakshatra-hero">
          <div className="nakshatra-hero__copy">
            <p className="nakshatra-eyebrow">Vedic lunar mansions</p>
            <h1>27 Nakshatras in Vedic Astrology</h1>
            <p>
              Explore each nakshatra by lord, deity, zodiac span, nature, and yearly calendar. Use the list as a clean
              reference for Janma Nakshatra, muhurat selection, compatibility, dasha interpretation, and Moon-based timing.
            </p>
            <div className="nakshatra-hero__actions">
              <a href="#nakshatra-grid" className="nakshatra-primary-link">Browse all 27</a>
              <a href="#nakshatra-guide" className="nakshatra-secondary-link">Read the guide</a>
            </div>
          </div>
          <div className="nakshatra-hero__panel" aria-label="Nakshatra quick facts">
            <div>
              <strong>27</strong>
              <span>Lunar mansions</span>
            </div>
            <div>
              <strong>13°20'</strong>
              <span>Each nakshatra span</span>
            </div>
            <div>
              <strong>4</strong>
              <span>Padas per nakshatra</span>
            </div>
          </div>
        </section>

        <section className="nakshatra-controls" aria-label="Filter nakshatras by planetary lord">
          <div>
            <p className="nakshatra-controls__label">Filter by lord</p>
            <div className="nakshatra-filter-row">
              {lordFilters.map((lord) => (
                <button
                  key={lord}
                  type="button"
                  className={`nakshatra-filter ${activeLord === lord ? 'is-active' : ''}`}
                  onClick={() => setActiveLord(lord)}
                >
                  {lord}
                </button>
              ))}
            </div>
          </div>
          <p className="nakshatra-controls__meta">
            {loading ? 'Refreshing live nakshatra reference...' : `${visibleNakshatras.length} nakshatra${visibleNakshatras.length === 1 ? '' : 's'} shown`}
          </p>
        </section>

        {apiNotice && <p className="nakshatra-api-notice">{apiNotice}</p>}

        <section id="nakshatra-grid" className="nakshatras-grid" aria-label="All 27 nakshatras">
          {visibleNakshatras.map((nakshatra) => (
            <article key={nakshatra.name} className="nakshatra-card">
              <button type="button" onClick={() => handleNakshatraClick(nakshatra.name)}>
                <span className="nakshatra-card__number">{String(nakshatra.index).padStart(2, '0')}</span>
                <span className="nakshatra-card__topline">
                  <span>{nakshatra.lord}</span>
                  <span>{nakshatra.nature}</span>
                </span>
                <span className="nakshatra-card__name">{nakshatra.name}</span>
                <span className="nakshatra-card__symbol">{nakshatra.symbol}</span>
                <span className="nakshatra-card__description">{nakshatra.description}</span>
                <span className="nakshatra-card__facts">
                  <span>
                    <small>Deity</small>
                    {nakshatra.deity}
                  </span>
                  <span>
                    <small>Range</small>
                    {nakshatra.degree_range}
                  </span>
                </span>
                <span className="nakshatra-card__cta">View {currentYear} calendar</span>
              </button>
            </article>
          ))}
        </section>

        <section id="nakshatra-guide" className="nakshatra-guide" aria-label="Nakshatra SEO guide">
          <div className="nakshatra-guide__intro">
            <p className="nakshatra-eyebrow">Complete nakshatra guide</p>
            <h2>Nakshatra names, lords, deities, padas, and calendars</h2>
            <p>
              Nakshatras divide the zodiac into 27 Moon-based segments. They add precision to Vedic astrology by showing
              the texture of the mind, the quality of time, the dasha starting point, and the deeper pattern behind
              compatibility, muhurat, and predictions.
            </p>
          </div>
          <div className="nakshatra-guide__grid">
            <article>
              <h3>What a nakshatra shows</h3>
              <p>
                Each nakshatra carries a ruling planet, deity, symbol, nature, and four padas. Together they describe
                instinctive behavior, emotional patterning, talents, challenges, and timing quality.
              </p>
            </article>
            <article>
              <h3>How calendars help</h3>
              <p>
                The annual calendar pages show when each nakshatra is active during the year, helping you study Moon
                movement and choose better windows for rituals, learning, travel, reflection, or important work.
              </p>
            </article>
            <article>
              <h3>Why Janma Nakshatra matters</h3>
              <p>
                Your birth Moon nakshatra is used for Vimshottari dasha, compatibility matching, Tara Bala, naming
                syllables, temperament, and many traditional timing techniques.
              </p>
            </article>
          </div>
        </section>

        <section className="nakshatra-faq" aria-label="Nakshatra FAQ">
          <h2>Nakshatra FAQ</h2>
          <div className="nakshatra-faq__grid">
            {SEO_FAQS.map((item) => (
              <article key={item.question}>
                <h3>{item.question}</h3>
                <p>{item.answer}</p>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
};

export default NakshatraListPage;
