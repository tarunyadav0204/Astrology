import React from 'react';
import { Link } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import SEOHead from '../SEO/SEOHead';
import './AdvancedCourses.css';

const STUDY_TRACKS = [
  {
    id: '01',
    title: 'Predictive Timing',
    eyebrow: 'Dashas · Transits · Activation',
    level: 'Advanced',
    description: 'Move from isolated placements to time-bound judgement using planetary periods, transits, and activated houses.',
    topics: ['Vimshottari dasha', 'Transit synthesis', 'Event windows', 'Yoga activation'],
    path: '/charts-dashas/activations',
    action: 'Open activation desk',
  },
  {
    id: '02',
    title: 'Health & Vitality',
    eyebrow: 'Houses · Karakas · Periods',
    level: 'Specialist',
    description: 'Study health themes responsibly through house strength, planetary significators, timing, and the limits of astrological interpretation.',
    topics: ['Health significators', 'Sixth and eighth houses', 'Timing pressure', 'Responsible language'],
    path: '/health-analysis',
    action: 'Explore health analysis',
  },
  {
    id: '03',
    title: 'Relationship Judgement',
    eyebrow: 'Compatibility · Promise · Timing',
    level: 'Advanced',
    description: 'Learn to separate compatibility from marriage promise and timing, then synthesize both charts without reducing them to a single score.',
    topics: ['Seventh-house promise', 'Navamsha context', 'Dasha timing', 'Two-chart synthesis'],
    path: '/marriage-analysis',
    action: 'Explore marriage analysis',
  },
  {
    id: '04',
    title: 'Wealth & Vocation',
    eyebrow: 'Resources · Work · Recognition',
    level: 'Advanced',
    description: 'Connect dhana yogas, house lords, divisional context, and active periods to practical questions about income, work, and assets.',
    topics: ['Dhana combinations', 'Career houses', 'Dasha delivery', 'Asset timing'],
    path: '/wealth-analysis',
    action: 'Explore wealth analysis',
  },
  {
    id: '05',
    title: 'Remedies & Decision Support',
    eyebrow: 'Discernment · Practice · Ethics',
    level: 'Specialist',
    description: 'Build a careful framework for remedies: diagnose the chart first, distinguish support from superstition, and avoid one-size-fits-all prescriptions.',
    topics: ['Chart diagnosis', 'Remedy selection', 'Mantra and practice', 'Ethical boundaries'],
    path: '/chat?app=1',
    action: 'Discuss with Tara',
  },
  {
    id: '06',
    title: 'Multi-system Synthesis',
    eyebrow: 'Parashari · Nadi · Jaimini · KP',
    level: 'Mastery',
    description: 'Learn what each system contributes, where their evidence overlaps, and how to resolve conflicting indications without cherry-picking.',
    topics: ['Evidence hierarchy', 'System strengths', 'Contradiction handling', 'Final synthesis'],
    path: '/charts-dashas',
    action: 'Open chart workspace',
  },
];

const PRINCIPLES = [
  ['01', 'Promise before timing', 'First establish what the natal chart can support. Only then ask when it may become active.'],
  ['02', 'Synthesis before certainty', 'No single placement decides an outcome. Read corroborating and contradictory evidence together.'],
  ['03', 'Context before prescription', 'A useful interpretation considers the person, the question, and real-world choices—not only technique.'],
  ['04', 'Ethics before spectacle', 'Use careful language, acknowledge uncertainty, and never substitute astrology for medical or legal expertise.'],
];

const AdvancedCourses = ({ user, onLogout, onAdminClick, onLogin }) => (
  <div className="advanced-courses-page">
    <SEOHead
      title="Advanced Vedic Astrology Courses | AstroRoshni"
      description="Study advanced Vedic astrology through structured learning paths in dashas, transits, relationships, health, wealth, remedies, and multi-system chart synthesis."
      keywords="advanced astrology course, vedic astrology training, jyotish course, dasha course, predictive astrology, chart synthesis"
      canonical="https://astroroshni.com/advanced-courses/"
      structuredData={{
        '@context': 'https://schema.org',
        '@graph': [
          {
            '@type': 'CollectionPage',
            '@id': 'https://astroroshni.com/advanced-courses/#page',
            name: 'Advanced Vedic Astrology Learning Paths',
            description: 'Structured advanced study paths for predictive timing, relationships, health, wealth, remedies, and multi-system Vedic astrology synthesis.',
            url: 'https://astroroshni.com/advanced-courses/',
            isPartOf: { '@type': 'WebSite', name: 'AstroRoshni', url: 'https://astroroshni.com/' },
          },
          {
            '@type': 'ItemList',
            name: 'Advanced Vedic Astrology Study Tracks',
            numberOfItems: STUDY_TRACKS.length,
            itemListElement: STUDY_TRACKS.map((track, index) => ({
              '@type': 'ListItem',
              position: index + 1,
              name: track.title,
              description: track.description,
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

    <main className="advanced-courses-main">
      <header className="advanced-courses-hero">
        <div className="advanced-courses-hero__copy">
          <p className="advanced-courses-eyebrow">Advanced study · Beyond isolated rules</p>
          <h1>Judge the chart.<br /><em>Then judge the time.</em></h1>
          <p className="advanced-courses-hero__lead">
            Six focused learning paths for moving from technique to synthesis—grounded in Parashari, Nadi, Jaimini, and KP perspectives.
          </p>
          <div className="advanced-courses-hero__actions">
            <a href="#study-tracks" className="advanced-courses-primary">Explore study tracks <span aria-hidden>↓</span></a>
            <Link to="/beginners-guide" className="advanced-courses-secondary">Review foundations <span aria-hidden>↗</span></Link>
          </div>
        </div>

        <div className="advanced-courses-synthesis" aria-label="Four systems synthesized into one judgement">
          <span className="advanced-courses-synthesis__system advanced-courses-synthesis__system--one">Parashari</span>
          <span className="advanced-courses-synthesis__system advanced-courses-synthesis__system--two">Nadi</span>
          <span className="advanced-courses-synthesis__system advanced-courses-synthesis__system--three">Jaimini</span>
          <span className="advanced-courses-synthesis__system advanced-courses-synthesis__system--four">KP</span>
          <div><strong>Synthesis</strong><small>One considered judgement</small></div>
        </div>

        <dl className="advanced-courses-hero__facts">
          <div><dt>Study tracks</dt><dd>{String(STUDY_TRACKS.length).padStart(2, '0')}</dd></div>
          <div><dt>Methods combined</dt><dd>04</dd></div>
          <div><dt>Core discipline</dt><dd>Corroboration</dd></div>
        </dl>
      </header>

      <section className="advanced-courses-foundation" aria-labelledby="foundation-check-title">
        <div>
          <p className="advanced-courses-section-label">Before you begin</p>
          <h2 id="foundation-check-title">Strong foundations make advanced work useful.</h2>
        </div>
        <p>You should already be comfortable with signs, grahas, houses, house lordship, basic aspects, nakshatras, and the purpose of dashas.</p>
        <Link to="/beginners-guide">Check the beginner path <span aria-hidden>↗</span></Link>
      </section>

      <section className="advanced-courses-tracks" id="study-tracks" aria-labelledby="study-tracks-title">
        <div className="advanced-courses-heading">
          <p className="advanced-courses-section-label">Choose your direction</p>
          <h2 id="study-tracks-title">Six paths into<br /><em>deeper judgement.</em></h2>
          <p>Each track names the reasoning skills to build and leads into a working AstroRoshni surface where you can examine the ideas using a real chart.</p>
        </div>

        <div className="advanced-courses-track-list">
          {STUDY_TRACKS.map((track) => (
            <article className="advanced-courses-track" key={track.id}>
              <div className="advanced-courses-track__number">{track.id}</div>
              <div className="advanced-courses-track__body">
                <div className="advanced-courses-track__meta"><span>{track.level}</span><span>{track.eyebrow}</span></div>
                <h3>{track.title}</h3>
                <p>{track.description}</p>
                <ul>{track.topics.map((topic) => <li key={topic}>{topic}</li>)}</ul>
              </div>
              <Link className="advanced-courses-track__link" to={track.path}>{track.action} <span aria-hidden>↗</span></Link>
            </article>
          ))}
        </div>
      </section>

      <section className="advanced-courses-method" aria-labelledby="method-title">
        <div className="advanced-courses-heading advanced-courses-heading--inverse">
          <p className="advanced-courses-section-label">The advanced method</p>
          <h2 id="method-title">What separates analysis<br /><em>from pattern collecting.</em></h2>
        </div>
        <div className="advanced-courses-principles">
          {PRINCIPLES.map(([number, title, description]) => (
            <article key={number}><span>{number}</span><h3>{title}</h3><p>{description}</p></article>
          ))}
        </div>
      </section>

      <section className="advanced-courses-workbench" aria-labelledby="workbench-title">
        <div>
          <p className="advanced-courses-section-label">Learn by doing</p>
          <h2 id="workbench-title">Bring a chart to the workbench.</h2>
          <p>Open the chart workspace to compare Parashari, KP, Nadi, dasha, and activation evidence side by side.</p>
        </div>
        <div className="advanced-courses-workbench__actions">
          <Link to="/charts-dashas">Open chart workspace <span aria-hidden>↗</span></Link>
          <Link to="/chat?app=1">Ask Tara a focused question <span aria-hidden>↗</span></Link>
        </div>
      </section>

      <section className="advanced-courses-guidance" aria-labelledby="guidance-title">
        <div>
          <p className="advanced-courses-section-label">Need a route through the material?</p>
          <h2 id="guidance-title">Tell us what you want to learn.</h2>
        </div>
        <p>We can help you choose a study sequence based on your current knowledge and the kind of questions you want to answer.</p>
        <Link to="/contact">Contact AstroRoshni <span aria-hidden>↗</span></Link>
      </section>
    </main>
  </div>
);

export default AdvancedCourses;
