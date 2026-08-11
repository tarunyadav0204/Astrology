import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import SEOHead from '../SEO/SEOHead';
import './MythsVsReality.css';

const MYTHS = [
  {
    id: 1,
    category: 'Foundations',
    title: 'Astrology and astronomy are the same discipline',
    claim: 'Both study planets, so astrology is simply another branch of astronomy.',
    reading: 'Astronomy is a physical science. Astrology is an interpretive tradition that assigns meaning to celestial positions.',
    explanation: 'The two share historical roots and astronomical calculations, but they ask different questions and use different standards of evidence. AstroRoshni uses astronomical position data to construct charts; the interpretation of those charts belongs to Vedic astrological tradition, not modern astronomy.',
  },
  {
    id: 2,
    category: 'Technique',
    title: 'Precession makes every Vedic zodiac sign wrong',
    claim: 'Because Earth’s axis shifts, all signs are displaced and every astrological chart is obsolete.',
    reading: 'Sidereal astrology explicitly applies an ayanamsha to account for precession; tropical astrology uses a seasonal reference frame.',
    explanation: 'The criticism often mixes two zodiac frameworks. Vedic practice generally uses a sidereal zodiac with a chosen ayanamsha, while most Western practice uses the tropical zodiac anchored to the equinoxes. They are different coordinate conventions, not an unnoticed calculation error.',
  },
  {
    id: 3,
    category: 'Philosophy',
    title: 'A birth chart removes free will',
    claim: 'If a chart describes the future, every event must be fixed and personal choice is meaningless.',
    reading: 'Responsible practice treats a chart as a framework of tendencies, constraints, and timing—not an instruction to surrender agency.',
    explanation: 'Astrological traditions differ on fate and choice, but a useful reading should widen decision-making rather than close it. Predictions should be expressed with uncertainty, alternatives, and practical context. A chart cannot make a decision on someone’s behalf.',
  },
  {
    id: 4,
    category: 'Questions',
    title: 'Twins must live identical lives',
    claim: 'If twins have nearly identical charts, astrology requires their personalities and life events to match exactly.',
    reading: 'A chart is not a complete model of a person. Biology, relationships, environment, opportunity, and individual choices also shape a life.',
    explanation: 'Small birth-time differences can affect some timing factors, but that cannot honestly be used to explain every divergence. Twin cases are a useful reminder that astrology is interpretive and contextual; it should never claim that the birth chart is the only cause operating in a life.',
  },
  {
    id: 5,
    category: 'Evidence',
    title: 'Astrology is scientifically proven',
    claim: 'Long use, personal accuracy, or a few correlations establish astrology as a validated predictive science.',
    reading: 'Astrology has not achieved scientific validation as a reliable predictive model under controlled testing.',
    explanation: 'Astrology can be meaningful as a cultural, spiritual, or reflective practice without being presented as established science. Individual experiences and selective correlations do not replace reproducible evidence. AstroRoshni should be used as interpretive guidance, not scientific proof of future events.',
  },
  {
    id: 6,
    category: 'Wellbeing',
    title: 'Astrology can diagnose or treat mental health conditions',
    claim: 'A chart can identify a psychiatric condition and prescribe the treatment a person needs.',
    reading: 'Astrology is not a diagnostic tool and must not replace qualified mental-health or medical care.',
    explanation: 'A reading may support reflection or help someone articulate a concern, but diagnosis and treatment require licensed professionals. Urgent or persistent distress belongs with appropriate clinical support. Astrological language should never create fear, stigma, or dependency.',
  },
  {
    id: 7,
    category: 'Evidence',
    title: 'A reading that feels accurate proves every claim',
    claim: 'Personal recognition is enough to establish that an interpretation is objectively correct.',
    reading: 'Confirmation bias, selective memory, and broadly applicable statements can all influence perceived accuracy.',
    explanation: 'A compelling reading may still be personally valuable, but confidence should not outrun evidence. Prefer specific, testable statements; record predictions before outcomes; notice misses as carefully as hits; and avoid retrofitting every event to the chart.',
  },
  {
    id: 8,
    category: 'Foundations',
    title: 'A Sun-sign horoscope is a complete reading',
    claim: 'Knowing one zodiac sign is enough to describe personality, relationships, career, and timing.',
    reading: 'A personalised Vedic reading considers the full birth chart, including ascendant, Moon, houses, nakshatras, divisional context, and timing.',
    explanation: 'Generic horoscopes simplify astrology for a broad audience. A complete chart uses accurate date, time, and place data and still requires synthesis rather than one-factor conclusions. Even a detailed chart should be read as guidance, not certainty.',
  },
];

const CATEGORIES = ['All', ...new Set(MYTHS.map((item) => item.category))];

const MythsVsReality = ({ user, onLogout, onAdminClick, onLogin }) => {
  const [selectedCategory, setSelectedCategory] = useState('All');
  const filteredMyths = useMemo(
    () => selectedCategory === 'All' ? MYTHS : MYTHS.filter((item) => item.category === selectedCategory),
    [selectedCategory]
  );

  return (
    <div className="myths-reality-page">
      <SEOHead
        title="Astrology Myths vs Reality - Facts About Vedic Astrology | AstroRoshni"
        description="A careful guide to common astrology myths: astronomy, precession, free will, scientific evidence, confirmation bias, mental health, twins, and Sun-sign horoscopes."
        keywords="astrology myths, astrology facts, vedic astrology truth, astrology science, zodiac myths, astrology misconceptions, sidereal zodiac precession"
        canonical="https://astroroshni.com/myths-vs-reality/"
        structuredData={{
          '@context': 'https://schema.org',
          '@graph': [
            {
              '@type': 'Article',
              '@id': 'https://astroroshni.com/myths-vs-reality/#article',
              headline: 'Astrology Myths vs Reality: A Careful Guide to Vedic Astrology Claims',
              description: 'A clear distinction between astrological tradition, astronomical calculation, scientific evidence, and responsible personal use.',
              mainEntityOfPage: 'https://astroroshni.com/myths-vs-reality/',
              author: { '@type': 'Organization', name: 'AstroRoshni' },
              publisher: { '@type': 'Organization', name: 'AstroRoshni', url: 'https://astroroshni.com/' },
            },
            {
              '@type': 'FAQPage',
              mainEntity: MYTHS.map((item) => ({
                '@type': 'Question',
                name: item.title,
                acceptedAnswer: { '@type': 'Answer', text: `${item.reading} ${item.explanation}` },
              })),
            },
          ],
        }}
      />

      <ModernNavigationHeader
        sticky
        user={user}
        onLogin={onLogin}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
      />

      <main className="myths-reality-main">
        <header className="myths-reality-hero">
          <div className="myths-reality-hero__copy">
            <p className="myths-reality-eyebrow">Claims · Context · Clearer judgement</p>
            <h1>Keep the wonder.<br /><em>Lose the certainty.</em></h1>
            <p className="myths-reality-hero__lead">
              A more honest guide to what astrology is, what it is not, and how to use Vedic interpretation without confusing tradition, evidence, and personal meaning.
            </p>
            <div className="myths-reality-hero__actions">
              <a href="#myth-index" className="myths-reality-primary">Read the eight claims <span aria-hidden>↓</span></a>
              <Link to="/beginners-guide" className="myths-reality-secondary">Learn the foundations <span aria-hidden>↗</span></Link>
            </div>
          </div>

          <div className="myths-reality-lens" aria-hidden="true">
            <span className="myths-reality-lens__orbit"></span>
            <div className="myths-reality-lens__claim">Claim</div>
            <div className="myths-reality-lens__context">Context</div>
            <div className="myths-reality-lens__centre"><strong>Judgement</strong><small>with proportion</small></div>
          </div>

          <dl className="myths-reality-hero__facts">
            <div><dt>Claims examined</dt><dd>{String(MYTHS.length).padStart(2, '0')}</dd></div>
            <div><dt>Scientific status</dt><dd>Not validated</dd></div>
            <div><dt>Best use</dt><dd>Reflection &amp; guidance</dd></div>
          </dl>
        </header>

        <section className="myths-reality-position" aria-labelledby="position-title">
          <div>
            <p className="myths-reality-section-label">Our position</p>
            <h2 id="position-title">AstroRoshni is an interpretive astrology platform—not a scientific, medical, legal, or financial authority.</h2>
          </div>
          <p>We calculate chart factors and combine Vedic systems to produce astrological interpretations. Those interpretations may support reflection and planning, but they do not prove causation, guarantee outcomes, or replace qualified professional advice.</p>
        </section>

        <section className="myths-reality-index" id="myth-index" aria-labelledby="myth-index-title">
          <div className="myths-reality-heading">
            <p className="myths-reality-section-label">Myth index</p>
            <h2 id="myth-index-title">Eight common claims.<br /><em>A more careful reading.</em></h2>
            <p>Filter by subject or read in order. Each entry separates the popular claim from the narrower conclusion the available context can actually support.</p>
          </div>

          <div className="myths-reality-filters" role="group" aria-label="Filter myths by category">
            {CATEGORIES.map((category) => (
              <button
                key={category}
                type="button"
                aria-pressed={selectedCategory === category}
                onClick={() => setSelectedCategory(category)}
              >
                {category}<span>{category === 'All' ? MYTHS.length : MYTHS.filter((item) => item.category === category).length}</span>
              </button>
            ))}
          </div>

          <div className="myths-reality-list" aria-live="polite">
            {filteredMyths.map((item) => (
              <article className="myths-reality-article" key={item.id}>
                <div className="myths-reality-article__number">{String(item.id).padStart(2, '0')}</div>
                <div className="myths-reality-article__body">
                  <span className="myths-reality-article__category">{item.category}</span>
                  <h3>{item.title}</h3>
                  <div className="myths-reality-comparison">
                    <div className="myths-reality-comparison__claim"><span>The claim</span><p>{item.claim}</p></div>
                    <div className="myths-reality-comparison__reading"><span>The careful reading</span><p>{item.reading}</p></div>
                  </div>
                  <details className="myths-reality-explanation">
                    <summary>Why the distinction matters <span aria-hidden>+</span></summary>
                    <p>{item.explanation}</p>
                  </details>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="myths-reality-framework" aria-labelledby="framework-title">
          <div className="myths-reality-heading myths-reality-heading--inverse">
            <p className="myths-reality-section-label">A better reading habit</p>
            <h2 id="framework-title">Ask three questions<br /><em>before believing a claim.</em></h2>
          </div>
          <div className="myths-reality-framework__grid">
            <article><span>01</span><h3>What is being claimed?</h3><p>Is it a symbolic interpretation, a factual statement, a prediction, or professional advice? Different claims require different standards.</p></article>
            <article><span>02</span><h3>What could change the conclusion?</h3><p>Look for missing birth data, alternative interpretations, contradictory factors, and real-world context.</p></article>
            <article><span>03</span><h3>What decision follows?</h3><p>Prefer interpretations that preserve agency. High-stakes decisions deserve qualified evidence and professional support.</p></article>
          </div>
        </section>

        <section className="myths-reality-sources" aria-labelledby="sources-title">
          <div className="myths-reality-heading">
            <p className="myths-reality-section-label">Study with context</p>
            <h2 id="sources-title">Tradition, method,<br />and responsible limits.</h2>
          </div>
          <div className="myths-reality-sources__grid">
            <article><span>01</span><h3>Classical tradition</h3><ul><li><cite>Brihat Parashara Hora Shastra</cite></li><li><cite>Jaimini Sutras</cite></li><li><cite>Phaladeepika</cite></li><li><cite>Saravali</cite></li></ul></article>
            <article><span>02</span><h3>Analytical discipline</h3><ul><li>Record predictions before outcomes</li><li>Count misses as carefully as hits</li><li>Separate calculation from interpretation</li><li>State uncertainty explicitly</li></ul></article>
            <article><span>03</span><h3>Responsible boundaries</h3><ul><li>No medical diagnosis</li><li>No guaranteed financial outcome</li><li>No fear-based prediction</li><li>No substitute for professional care</li></ul></article>
          </div>
        </section>

        <section className="myths-reality-next" aria-labelledby="myths-next-title">
          <div><p className="myths-reality-section-label">Continue with clarity</p><h2 id="myths-next-title">Learn how a complete chart is actually assembled.</h2></div>
          <Link to="/beginners-guide">Open the beginner’s guide <span aria-hidden>↗</span></Link>
        </section>
      </main>
    </div>
  );
};

export default MythsVsReality;
