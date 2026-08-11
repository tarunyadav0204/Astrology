import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import SEOHead from '../SEO/SEOHead';
import './BeginnersGuide.css';

const PROGRESS_STORAGE_KEY = 'astroroshni-beginners-guide-progress';

const LESSONS = [
  {
    id: 1,
    title: 'What is Astrology?',
    duration: '5 min read',
    level: 'Foundation',
    content: 'Understand what astrology studies, where the Vedic tradition begins, and how it differs from Western systems.',
    topics: ['Definition of astrology', 'Historical background', 'Vedic and Western systems', 'Core principles'],
  },
  {
    id: 2,
    title: 'The Zodiac Signs',
    duration: '8 min read',
    level: 'Foundation',
    content: 'Meet the twelve rashis through their elements, qualities, ruling planets, and characteristic ways of expression.',
    topics: ['Twelve zodiac signs', 'Four elements', 'Ruling planets', 'Sign characteristics'],
  },
  {
    id: 3,
    title: 'Understanding Your Birth Chart',
    duration: '10 min read',
    level: 'Foundation',
    content: 'Learn how signs, planets, houses, and the ascendant come together in the map of a single moment.',
    topics: ['Birth chart basics', 'Twelve houses', 'Planet positions', 'Ascendant and rising sign'],
  },
  {
    id: 4,
    title: 'The Planets and Their Meanings',
    duration: '12 min read',
    level: 'Foundation',
    content: 'Explore the nine grahas in Vedic astrology and the roles they play in temperament, experience, and timing.',
    topics: ['Sun, Moon, and Mars', 'Mercury, Jupiter, and Venus', 'Saturn, Rahu, and Ketu', 'Planetary influences'],
  },
  {
    id: 5,
    title: 'The 12 Houses Explained',
    duration: '15 min read',
    level: 'Interpretation',
    content: 'Connect each house to a distinct area of life, then see how house lords and planetary placements modify it.',
    topics: ['House meanings', 'Areas of life', 'House lords', 'Planetary placements'],
  },
  {
    id: 6,
    title: 'Aspects and Conjunctions',
    duration: '10 min read',
    level: 'Interpretation',
    content: 'See how planets influence one another through conjunctions and aspects, creating the chart’s relationships.',
    topics: ['Planetary aspects', 'Conjunctions', 'Support and pressure', 'Reading combinations'],
  },
  {
    id: 7,
    title: 'Nakshatras — Lunar Mansions',
    duration: '12 min read',
    level: 'Interpretation',
    content: 'Discover the twenty-seven nakshatras and the finer emotional, karmic, and timing detail they contribute.',
    topics: ['Twenty-seven nakshatras', 'Nakshatra lords', 'The pada system', 'Core characteristics'],
  },
  {
    id: 8,
    title: 'Dasha Systems',
    duration: '15 min read',
    level: 'Timing',
    content: 'Begin working with planetary periods and understand how dashas help place chart promises on a timeline.',
    topics: ['Vimshottari dasha', 'Planetary periods', 'Sub-periods', 'Timing events'],
  },
];

const BeginnersGuide = ({ user, onLogout, onAdminClick, onLogin }) => {
  const [completedLessons, setCompletedLessons] = useState(() => {
    try {
      const saved = JSON.parse(window.localStorage.getItem(PROGRESS_STORAGE_KEY) || '[]');
      return new Set(Array.isArray(saved) ? saved : []);
    } catch {
      return new Set();
    }
  });

  useEffect(() => {
    window.localStorage.setItem(PROGRESS_STORAGE_KEY, JSON.stringify([...completedLessons]));
  }, [completedLessons]);

  const totalMinutes = useMemo(
    () => LESSONS.reduce((total, lesson) => total + Number.parseInt(lesson.duration, 10), 0),
    []
  );
  const progressPercentage = Math.round((completedLessons.size / LESSONS.length) * 100);

  const toggleLessonComplete = (lessonId) => {
    setCompletedLessons((current) => {
      const next = new Set(current);
      if (next.has(lessonId)) next.delete(lessonId);
      else next.add(lessonId);
      return next;
    });
  };

  return (
    <div className="beginners-guide-page">
      <SEOHead
        title="Beginner's Guide to Astrology - Learn Vedic Astrology Basics | AstroRoshni"
        description="Complete beginner's guide to astrology with step-by-step lessons. Learn zodiac signs, birth charts, planets, houses and Vedic astrology fundamentals."
        keywords="astrology for beginners, learn astrology, vedic astrology basics, zodiac signs guide, birth chart tutorial, astrology lessons"
        canonical="https://astroroshni.com/beginners-guide/"
        structuredData={{
          '@context': 'https://schema.org',
          '@type': 'Course',
          name: "Beginner's Guide to Vedic Astrology",
          description: 'A free, step-by-step introduction to zodiac signs, birth charts, planets, houses, nakshatras, and dasha timing.',
          provider: { '@type': 'Organization', name: 'AstroRoshni', url: 'https://astroroshni.com/' },
          courseMode: 'online',
          educationalLevel: 'Beginner',
          isAccessibleForFree: true,
          numberOfCredits: LESSONS.length,
        }}
      />

      <ModernNavigationHeader
        sticky
        user={user}
        onLogin={onLogin}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
      />

      <main className="beginners-guide-main">
        <header className="beginners-guide-hero">
          <div className="beginners-guide-hero__copy">
            <p className="beginners-guide-eyebrow">Vedic astrology · Start here</p>
            <h1>Learn the sky.<br /><em>Read the pattern.</em></h1>
            <p className="beginners-guide-hero__lead">
              A calm, structured introduction to signs, planets, houses, nakshatras, and timing—built to help you understand a chart rather than memorise jargon.
            </p>
            <div className="beginners-guide-hero__actions">
              <a href="#curriculum" className="beginners-guide-primary">Begin with lesson one <span aria-hidden>↓</span></a>
              <Link to="/ai-kundli-generator" className="beginners-guide-secondary">Create your chart <span aria-hidden>↗</span></Link>
            </div>
          </div>

          <div className="beginners-guide-orbit" aria-hidden="true">
            <span className="beginners-guide-orbit__ring beginners-guide-orbit__ring--outer"></span>
            <span className="beginners-guide-orbit__ring beginners-guide-orbit__ring--inner"></span>
            <span className="beginners-guide-orbit__center">आरम्भ<small>Begin</small></span>
            <i className="beginners-guide-orbit__planet beginners-guide-orbit__planet--one"></i>
            <i className="beginners-guide-orbit__planet beginners-guide-orbit__planet--two"></i>
          </div>

          <dl className="beginners-guide-hero__facts">
            <div><dt>Lessons</dt><dd>{String(LESSONS.length).padStart(2, '0')}</dd></div>
            <div><dt>Reading time</dt><dd>{totalMinutes} min</dd></div>
            <div><dt>Level</dt><dd>First principles</dd></div>
          </dl>
        </header>

        <section className="beginners-guide-progress" aria-labelledby="learning-progress-title">
          <div>
            <p className="beginners-guide-section-label">Your path</p>
            <h2 id="learning-progress-title">Learning progress</h2>
          </div>
          <div className="beginners-guide-progress__status">
            <span>{completedLessons.size} of {LESSONS.length} lessons complete</span>
            <strong>{progressPercentage}%</strong>
          </div>
          <div
            className="beginners-guide-progress__track"
            role="progressbar"
            aria-valuemin="0"
            aria-valuemax="100"
            aria-valuenow={progressPercentage}
            aria-label={`${progressPercentage}% complete`}
          >
            <span style={{ width: `${progressPercentage}%` }}></span>
          </div>
          <p>Your progress is saved on this device.</p>
        </section>

        <section className="beginners-guide-curriculum" id="curriculum" aria-labelledby="curriculum-title">
          <div className="beginners-guide-heading">
            <p className="beginners-guide-section-label">The curriculum</p>
            <h2 id="curriculum-title">Eight ideas.<br /><em>One connected system.</em></h2>
            <p>Move in order for a strong foundation, or open the idea you need today. Each lesson ends with concepts you can locate in a real chart.</p>
          </div>

          <div className="beginners-guide-lessons">
            {LESSONS.map((lesson) => {
              const isCompleted = completedLessons.has(lesson.id);
              return (
                <article key={lesson.id} className={`beginners-guide-lesson${isCompleted ? ' is-complete' : ''}`}>
                  <div className="beginners-guide-lesson__index">{String(lesson.id).padStart(2, '0')}</div>
                  <div className="beginners-guide-lesson__body">
                    <div className="beginners-guide-lesson__meta">
                      <span>{lesson.level}</span><span>{lesson.duration}</span>
                    </div>
                    <h3>{lesson.title}</h3>
                    <p>{lesson.content}</p>
                    <ul aria-label={`Topics in ${lesson.title}`}>
                      {lesson.topics.map((topic) => <li key={topic}>{topic}</li>)}
                    </ul>
                  </div>
                  <div className="beginners-guide-lesson__actions">
                    <Link className="beginners-guide-lesson__open" to={`/lesson/${lesson.id}`}>
                      {isCompleted ? 'Review lesson' : 'Open lesson'} <span aria-hidden>↗</span>
                    </Link>
                    <button
                      type="button"
                      className="beginners-guide-lesson__complete"
                      aria-pressed={isCompleted}
                      onClick={() => toggleLessonComplete(lesson.id)}
                    >
                      <span aria-hidden>{isCompleted ? '✓' : '+'}</span>{isCompleted ? 'Completed' : 'Mark complete'}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className="beginners-guide-practice" aria-labelledby="practice-title">
          <div className="beginners-guide-heading beginners-guide-heading--inverse">
            <p className="beginners-guide-section-label">Turn theory into recognition</p>
            <h2 id="practice-title">Study your own chart<br /><em>as you learn.</em></h2>
            <p>Astrology becomes clearer when every new idea has somewhere real to land. Use a saved Kundli to identify placements, then ask Tara how the pieces combine.</p>
          </div>
          <div className="beginners-guide-practice__actions">
            <Link to="/ai-kundli-generator">Create or choose Kundli <span aria-hidden>↗</span></Link>
            <Link to="/chat?app=1">Ask Tara about my chart <span aria-hidden>↗</span></Link>
          </div>
        </section>

        <section className="beginners-guide-resources" aria-labelledby="resources-title">
          <div className="beginners-guide-heading">
            <p className="beginners-guide-section-label">Keep beside you</p>
            <h2 id="resources-title">A learner’s toolkit</h2>
          </div>
          <div className="beginners-guide-resources__grid">
            <article>
              <span>01</span><h3>Essential vocabulary</h3>
              <dl><div><dt>Ascendant</dt><dd>Your rising sign</dd></div><div><dt>Conjunction</dt><dd>Planets placed closely together</dd></div><div><dt>Transit</dt><dd>Current planetary movement</dd></div><div><dt>Retrograde</dt><dd>Apparent backward motion</dd></div></dl>
            </article>
            <article>
              <span>02</span><h3>Practice prompts</h3>
              <ul><li>Identify your Sun, Moon, and rising sign</li><li>Locate every graha in your birth chart</li><li>Connect each house to an area of life</li><li>Find your current dasha period</li></ul>
            </article>
            <article>
              <span>03</span><h3>Reference shelf</h3>
              <ul><li><cite>Light on Life</cite> · Hart de Fouw</li><li><cite>Astrology for the Soul</cite> · Jan Spiller</li><li><cite>The Only Astrology Book You’ll Ever Need</cite></li><li><cite>Vedic Astrology</cite> · David Frawley</li></ul>
            </article>
          </div>
        </section>

        <section className="beginners-guide-next" aria-labelledby="next-title">
          <div>
            <p className="beginners-guide-section-label">Continue learning</p>
            <h2 id="next-title">Ready to go deeper?</h2>
          </div>
          <Link to="/advanced-courses">Explore advanced courses <span aria-hidden>↗</span></Link>
        </section>
      </main>
    </div>
  );
};

export default BeginnersGuide;
