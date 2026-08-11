import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ModernNavigationHeader from '../../Shared/ModernNavigationHeader';
import SEOHead from '../../SEO/SEOHead';
import './LessonPage.css';

const PROGRESS_STORAGE_KEY = 'astroroshni-beginners-guide-progress';

const LESSONS = {
  1: {
    title: 'What is Astrology?',
    shortTitle: 'Astrology as a language',
    duration: '5 min read',
    level: 'Foundation',
    summary: 'Understand what astrology studies, how Vedic astrology differs from astronomy, and what an interpretation can—and cannot—claim.',
    objectives: ['Separate astronomical calculation from astrological interpretation', 'Recognise astrology as an interpretive tradition', 'Use astrological guidance without surrendering judgement'],
    sections: [
      { title: 'A map of a moment', paragraphs: ['A birth chart maps the positions of celestial bodies for a particular date, time, and place. The positions are astronomical data; the meanings assigned to them belong to an astrological tradition.', 'Jyotish, or Vedic astrology, relates grahas, rashis, houses, nakshatras, and timing systems to human experience. It is best approached as a symbolic and interpretive framework rather than a scientifically validated model of causation.'] },
      { title: 'Traditions and reference frames', paragraphs: ['Vedic astrology generally uses a sidereal zodiac adjusted through an ayanamsha. Most Western astrology uses the tropical zodiac anchored to the seasons. These systems begin from different coordinate conventions and have developed different interpretive priorities.'], bullets: ['Vedic practice emphasises nakshatras and dashas', 'Western practice often emphasises psychological symbolism and transits', 'Neither system is identical to the science of astronomy'] },
      { title: 'A responsible way to use it', paragraphs: ['An astrological reading can help organise questions, notice patterns, and consider timing. It should not promise certainty or replace evidence, agency, or qualified medical, legal, and financial advice.'] },
    ],
    practice: 'Write one question you hope astrology will answer. Then rewrite it so the question preserves your agency—for example, change “What will happen?” to “What conditions should I prepare for?”',
  },
  2: {
    title: 'The Zodiac Signs',
    shortTitle: 'The twelve rashis',
    duration: '8 min read',
    level: 'Foundation',
    summary: 'Learn how the twelve signs describe modes of expression through element, modality, and planetary rulership.',
    objectives: ['Name the four elements and three modalities', 'Understand that signs modify rather than act', 'Avoid reducing a chart to one Sun or Moon sign'],
    sections: [
      { title: 'Twelve equal divisions', paragraphs: ['The zodiac divides the ecliptic into twelve equal signs of thirty degrees each. In a chart, a sign describes the style or condition through which a planet and house operate; it does not act independently.'] },
      { title: 'Elements', paragraphs: ['The four elements offer a first vocabulary for how a sign engages experience.'], groups: [['Fire', 'Aries · Leo · Sagittarius', 'Initiating, expressive, purpose-driven'], ['Earth', 'Taurus · Virgo · Capricorn', 'Practical, material, stabilising'], ['Air', 'Gemini · Libra · Aquarius', 'Conceptual, relational, communicative'], ['Water', 'Cancer · Scorpio · Pisces', 'Receptive, emotional, adaptive']] },
      { title: 'Modalities', paragraphs: ['Each element appears in three modalities. Cardinal signs initiate, fixed signs sustain, and mutable signs adapt or redistribute. Combining element and modality gives every sign a distinct operating style.'], bullets: ['Cardinal: Aries, Cancer, Libra, Capricorn', 'Fixed: Taurus, Leo, Scorpio, Aquarius', 'Mutable: Gemini, Virgo, Sagittarius, Pisces'] },
      { title: 'Rulership gives context', paragraphs: ['Every sign has a planetary ruler. The condition and placement of that ruler connect the sign to another part of the chart. This is why sign descriptions alone are never a complete reading.'] },
    ],
    practice: 'Choose one planet in your chart. Describe its sign using element and modality before looking up any personality keywords.',
  },
  3: {
    title: 'Understanding Your Birth Chart',
    shortTitle: 'Reading the chart map',
    duration: '10 min read',
    level: 'Foundation',
    summary: 'See how ascendant, houses, signs, planets, and house lords combine into one chart rather than eight separate lists.',
    objectives: ['Identify the ascendant and twelve houses', 'Distinguish a house from the sign occupying it', 'Follow a house to its planetary lord'],
    sections: [
      { title: 'Start with the ascendant', paragraphs: ['The ascendant, or lagna, is the zodiac degree rising at the eastern horizon at the recorded birth time and place. It establishes the first house and determines which sign occupies every house.', 'Because the ascendant can change relatively quickly, birth-time accuracy matters—especially for house cusps, divisional charts, and fine timing.'] },
      { title: 'Four layers of one statement', groups: [['House', 'Where', 'The area of life being considered'], ['Sign', 'How', 'The style and conditions surrounding it'], ['Planet', 'What', 'The actor, function, or significator involved'], ['Lord', 'Connection', 'Where the house’s agenda is carried']] },
      { title: 'A disciplined reading order', paragraphs: ['Begin broad and add detail only when the earlier layer is clear. This reduces contradiction and prevents one striking placement from dominating the entire judgement.'], bullets: ['Confirm the ascendant and chart reference', 'Identify the house relevant to the question', 'Judge its lord, occupants, and aspects', 'Look for repetition from significators and divisional context', 'Use timing systems only after establishing natal promise'] },
    ],
    practice: 'Locate the first, fourth, seventh, and tenth houses in your chart. Note each house’s sign and where its lord is placed.',
  },
  4: {
    title: 'The Planets and Their Meanings',
    shortTitle: 'The nine grahas',
    duration: '12 min read',
    level: 'Foundation',
    summary: 'Meet the nine Vedic grahas as chart functions whose results depend on lordship, dignity, house placement, and relationship.',
    objectives: ['Recognise the core function of each graha', 'Separate natural nature from functional role', 'Judge a planet in context rather than by a fixed good-or-bad label'],
    sections: [
      { title: 'Grahas are not isolated characters', paragraphs: ['A graha represents a function within the chart, but its expression changes with sign dignity, house lordship, placement, aspects, conjunctions, and active timing. A naturally challenging planet can deliver constructive results; a naturally supportive planet can be constrained.'] },
      { title: 'The planetary vocabulary', groups: [['Sun', 'Identity and authority', 'Purpose, visibility, leadership'], ['Moon', 'Mind and responsiveness', 'Emotion, habit, nourishment'], ['Mars', 'Action and force', 'Courage, conflict, execution'], ['Mercury', 'Discrimination and exchange', 'Speech, analysis, trade'], ['Jupiter', 'Expansion and counsel', 'Knowledge, ethics, growth'], ['Venus', 'Value and relationship', 'Harmony, pleasure, agreement'], ['Saturn', 'Time and constraint', 'Duty, endurance, consequence'], ['Rahu', 'Amplification and appetite', 'Novelty, ambition, disruption'], ['Ketu', 'Separation and refinement', 'Release, inwardness, discontinuity']] },
      { title: 'Natural and functional roles', paragraphs: ['Natural benefic or malefic labels describe broad tendencies. Functional roles come from the houses a planet rules for a specific ascendant. Both layers matter, and neither should be read alone.'] },
    ],
    practice: 'Choose one graha. Record its sign, house, houses ruled, conjunctions, and major aspects before writing a one-sentence interpretation.',
  },
  5: {
    title: 'The 12 Houses Explained',
    shortTitle: 'Twelve fields of life',
    duration: '15 min read',
    level: 'Interpretation',
    summary: 'Understand the twelve bhavas as connected fields of experience, organised through angularity, purpose, and house relationships.',
    objectives: ['Associate each house with its core topics', 'Recognise angular, trinal, growth, and difficult houses', 'Read houses as relationships rather than isolated compartments'],
    sections: [
      { title: 'The house sequence', groups: [['1', 'Self and embodiment', 'Identity, vitality, approach'], ['2', 'Resources and speech', 'Family, values, accumulation'], ['3', 'Effort and skill', 'Courage, communication, siblings'], ['4', 'Home and foundation', 'Mother, property, inner security'], ['5', 'Intelligence and creation', 'Learning, children, authorship'], ['6', 'Work and obstacles', 'Service, conflict, illness'], ['7', 'Partnership and exchange', 'Marriage, contracts, public dealing'], ['8', 'Change and vulnerability', 'Joint resources, rupture, research'], ['9', 'Meaning and guidance', 'Dharma, teachers, long journeys'], ['10', 'Action and vocation', 'Career, authority, public role'], ['11', 'Gain and networks', 'Income, allies, fulfilment'], ['12', 'Release and distance', 'Expense, retreat, foreign places']] },
      { title: 'House families', paragraphs: ['Kendras anchor lived experience; trikonas support purpose and coherence; upachayas develop through effort and time; dusthanas describe friction, vulnerability, and transformation. These are overlapping frameworks, not simple rankings.'], bullets: ['Kendras: 1, 4, 7, 10', 'Trikonas: 1, 5, 9', 'Upachayas: 3, 6, 10, 11', 'Dusthanas: 6, 8, 12'] },
      { title: 'Read the whole chain', paragraphs: ['To judge a house, consider its sign, lord, occupants, aspects, natural significators, relevant divisional chart, and active periods. Repetition across these layers is more persuasive than one placement.'] },
    ],
    practice: 'Pick one life topic. Identify its primary house, the house lord, and one natural significator. Note where the three layers agree or disagree.',
  },
  6: {
    title: 'Aspects and Conjunctions',
    shortTitle: 'Planetary relationships',
    duration: '10 min read',
    level: 'Interpretation',
    summary: 'Learn how conjunctions and drishti connect planets and houses without treating every contact as an automatic result.',
    objectives: ['Distinguish conjunction from aspect', 'Recognise standard and special graha drishti', 'Judge relationship quality through context and repetition'],
    sections: [
      { title: 'Conjunction: sharing one sign', paragraphs: ['Planets in the same sign form a conjunction, but closeness matters. A wide conjunction may show shared territory; a close conjunction can blend, compete, or intensify the planets more directly.', 'Always consider dignity, degrees, combustion, planetary war where applicable, and house lordship before deciding which planet dominates.'] },
      { title: 'Drishti: directed influence', paragraphs: ['In Parashari practice, all planets cast a seventh-house aspect. Mars, Jupiter, and Saturn also have special full aspects. Different traditions may apply additional aspect frameworks, so name the method you are using.'], bullets: ['Mars: fourth, seventh, and eighth', 'Jupiter: fifth, seventh, and ninth', 'Saturn: third, seventh, and tenth'] },
      { title: 'From contact to judgement', paragraphs: ['An aspect does not guarantee an event. Ask what houses the planets rule, whether the relationship repeats through significators or divisional charts, and whether an appropriate dasha or transit activates it.'] },
    ],
    practice: 'Find one conjunction or major aspect in your chart. Write the houses ruled by both planets and identify the life areas their relationship connects.',
  },
  7: {
    title: 'Nakshatras — Lunar Mansions',
    shortTitle: 'The twenty-seven nakshatras',
    duration: '12 min read',
    level: 'Interpretation',
    summary: 'Understand how the twenty-seven nakshatras add a finer layer of symbolism and timing to the sidereal zodiac.',
    objectives: ['Understand the 27-fold lunar division', 'Recognise lord, deity, symbol, and pada as separate layers', 'Use nakshatra meaning without deterministic stereotyping'],
    sections: [
      { title: 'A finer division of the zodiac', paragraphs: ['The sidereal zodiac is divided into twenty-seven nakshatras of 13°20′ each. The Moon moves through roughly one nakshatra per day, which is why the system is closely connected with lunar timing and Vimshottari dasha.'] },
      { title: 'Four layers to record', groups: [['Nakshatra lord', 'Timing link', 'Connects the placement to the Vimshottari sequence'], ['Deity and symbol', 'Mythic language', 'Frames the traditional field of meaning'], ['Shakti', 'Capacity', 'Describes the action attributed to the nakshatra'], ['Pada', 'Quarter', 'Places the degree into a navamsha and refines expression']] },
      { title: 'Interpret placement, not stereotype', paragraphs: ['A nakshatra does not define an entire person. Judge which planet occupies it, the planet’s role in the chart, the nakshatra lord, house context, dignity, and relevant timing. Similar Moon nakshatras can express very differently in different charts.'] },
      { title: 'Use the dedicated calendar', paragraphs: ['AstroRoshni’s nakshatra pages provide yearly dates and reference material for all twenty-seven lunar mansions.'], link: { label: 'Explore all nakshatras', path: '/nakshatras' } },
    ],
    practice: 'Find your Moon’s nakshatra and pada. Then locate the nakshatra lord in the chart and note the house connection it creates.',
  },
  8: {
    title: 'Dasha Systems',
    shortTitle: 'Timing planetary periods',
    duration: '15 min read',
    level: 'Timing',
    summary: 'Learn why dashas organise time, how Vimshottari periods nest, and why timing must activate a promise already present in the chart.',
    objectives: ['Understand mahadasha and antardasha', 'Connect dasha results to natal promise', 'Combine periods with transits without double-counting evidence'],
    sections: [
      { title: 'A sequence of planetary periods', paragraphs: ['A dasha system assigns different spans of life to planetary rulers. Vimshottari dasha is a 120-year sequence derived from the Moon’s birth nakshatra and is one of the most widely used timing systems in Parashari astrology.'] },
      { title: 'Periods within periods', groups: [['Mahadasha', 'Primary period', 'Sets the broad chapter and dominant planetary agenda'], ['Antardasha', 'Sub-period', 'Narrows the active relationship and delivery mechanism'], ['Pratyantardasha', 'Finer sub-period', 'Refines shorter windows when birth time is reliable']] },
      { title: 'Promise before timing', paragraphs: ['A dasha does not manufacture a result that the natal chart cannot support. Judge the period lord’s house ownership, placement, dignity, relationships, significations, and divisional context before forecasting what it may activate.'] },
      { title: 'Add transits last', paragraphs: ['Transits can trigger or emphasise an active natal pattern. They are most useful after the natal promise and period lords are clear. Repeating the same factor through several techniques is corroboration; counting the same factor repeatedly is not.'], link: { label: 'Open charts and dashas', path: '/charts-dashas' } },
    ],
    practice: 'Identify your current mahadasha and antardasha lords. List the houses each rules and occupies, then note one transit that currently connects to those houses.',
  },
};

const LessonPage = ({ user, onLogout, onAdminClick, onLogin }) => {
  const { lessonId } = useParams();
  const lessonNumber = Number.parseInt(lessonId, 10);
  const lesson = LESSONS[lessonNumber];
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

  useEffect(() => { window.scrollTo(0, 0); }, [lessonId]);

  const setLessonComplete = () => {
    setCompletedLessons((current) => {
      const next = new Set(current);
      if (next.has(lessonNumber)) next.delete(lessonNumber);
      else next.add(lessonNumber);
      return next;
    });
  };

  if (!lesson) {
    return (
      <div className="lesson-page">
        <SEOHead title="Lesson Not Found | AstroRoshni" description="This AstroRoshni lesson could not be found." canonical={`https://astroroshni.com/lesson/${lessonId}/`} noIndex />
        <ModernNavigationHeader sticky user={user} onLogin={onLogin} onLogout={onLogout} onAdminClick={onAdminClick} />
        <main className="lesson-not-found">
          <p className="lesson-page-eyebrow">Learning path</p><h1>That lesson is not in the syllabus.</h1>
          <p>Return to the beginner’s guide to choose one of the eight available lessons.</p>
          <Link to="/beginners-guide">View all lessons <span aria-hidden>↗</span></Link>
        </main>
      </div>
    );
  }

  const isComplete = completedLessons.has(lessonNumber);
  const previousLesson = lessonNumber > 1 ? LESSONS[lessonNumber - 1] : null;
  const nextLesson = lessonNumber < Object.keys(LESSONS).length ? LESSONS[lessonNumber + 1] : null;

  return (
    <div className="lesson-page">
      <SEOHead
        title={`${lesson.title} — Vedic Astrology Lesson ${lessonNumber} | AstroRoshni`}
        description={lesson.summary}
        keywords={`${lesson.title.toLowerCase()}, learn vedic astrology, jyotish lesson, astrology for beginners`}
        canonical={`https://astroroshni.com/lesson/${lessonNumber}/`}
        structuredData={{
          '@context': 'https://schema.org',
          '@type': 'LearningResource',
          name: lesson.title,
          description: lesson.summary,
          url: `https://astroroshni.com/lesson/${lessonNumber}/`,
          educationalLevel: lesson.level,
          learningResourceType: 'lesson',
          isAccessibleForFree: true,
          provider: { '@type': 'Organization', name: 'AstroRoshni', url: 'https://astroroshni.com/' },
          isPartOf: { '@type': 'Course', name: 'Beginner’s Guide to Vedic Astrology', url: 'https://astroroshni.com/beginners-guide/' },
        }}
      />
      <ModernNavigationHeader sticky user={user} onLogin={onLogin} onLogout={onLogout} onAdminClick={onAdminClick} />

      <main className="lesson-page-main">
        <header className="lesson-page-hero">
          <div className="lesson-page-hero__top">
            <Link to="/beginners-guide" className="lesson-page-back"><span aria-hidden>←</span> All lessons</Link>
            <span className="lesson-page-count">{String(lessonNumber).padStart(2, '0')} / {String(Object.keys(LESSONS).length).padStart(2, '0')}</span>
          </div>
          <div className="lesson-page-hero__body">
            <div>
              <p className="lesson-page-eyebrow">{lesson.level} · {lesson.duration}</p>
              <h1>{lesson.title}</h1>
              <p>{lesson.summary}</p>
            </div>
            <div className="lesson-page-hero__mark" aria-hidden><span>{String(lessonNumber).padStart(2, '0')}</span><small>Lesson</small></div>
          </div>
          <div className="lesson-page-objectives">
            {lesson.objectives.map((objective, index) => <div key={objective}><span>{String(index + 1).padStart(2, '0')}</span><p>{objective}</p></div>)}
          </div>
        </header>

        <div className="lesson-page-layout">
          <aside className="lesson-page-contents" aria-label="Lesson contents">
            <p>In this lesson</p>
            <nav>{lesson.sections.map((section, index) => <a key={section.title} href={`#section-${index + 1}`}><span>{String(index + 1).padStart(2, '0')}</span>{section.title}</a>)}</nav>
            <button type="button" aria-pressed={isComplete} onClick={setLessonComplete}><span aria-hidden>{isComplete ? '✓' : '+'}</span>{isComplete ? 'Lesson complete' : 'Mark as complete'}</button>
          </aside>

          <article className="lesson-page-article">
            {lesson.sections.map((section, index) => (
              <section id={`section-${index + 1}`} key={section.title}>
                <div className="lesson-page-section-number">{String(index + 1).padStart(2, '0')}</div>
                <h2>{section.title}</h2>
                {section.paragraphs?.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
                {section.bullets && <ul>{section.bullets.map((bullet) => <li key={bullet}>{bullet}</li>)}</ul>}
                {section.groups && <div className="lesson-page-groups">{section.groups.map(([title, subtitle, description]) => <div key={`${title}-${subtitle}`}><span>{title}</span><strong>{subtitle}</strong><p>{description}</p></div>)}</div>}
                {section.link && <Link className="lesson-page-inline-link" to={section.link.path}>{section.link.label} <span aria-hidden>↗</span></Link>}
              </section>
            ))}

            <section className="lesson-page-practice" aria-labelledby="practice-title">
              <p className="lesson-page-eyebrow">Put it into practice</p>
              <h2 id="practice-title">Use the idea on a real chart.</h2>
              <p>{lesson.practice}</p>
              <Link to="/ai-kundli-generator">Create or choose Kundli <span aria-hidden>↗</span></Link>
            </section>
          </article>
        </div>

        <nav className="lesson-page-navigation" aria-label="Lesson navigation">
          {previousLesson ? <Link to={`/lesson/${lessonNumber - 1}`}><small>Previous lesson</small><strong><span aria-hidden>←</span> {previousLesson.shortTitle}</strong></Link> : <span></span>}
          {nextLesson ? <Link to={`/lesson/${lessonNumber + 1}`}><small>Next lesson</small><strong>{nextLesson.shortTitle} <span aria-hidden>→</span></strong></Link> : <Link to="/advanced-courses"><small>Continue learning</small><strong>Advanced study paths <span aria-hidden>↗</span></strong></Link>}
        </nav>
      </main>
    </div>
  );
};

export default LessonPage;
