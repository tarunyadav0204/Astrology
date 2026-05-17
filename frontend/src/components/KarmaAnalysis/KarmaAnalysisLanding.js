import React from 'react';
import { Link } from 'react-router-dom';
import {
  KARMA_CANONICAL,
  KARMA_FAQ,
  KARMA_REPORT_SECTIONS,
  KARMA_SAMPLE_EXCERPT,
} from './karmaSeoContent';

/**
 * Always-visible public content for SEO and guests (Layer 1).
 * Personalised report UI lives below in #karma-tool.
 */
const KarmaAnalysisLanding = ({ onGetStarted }) => {
  return (
    <article className="karma-landing" id="karma-guide">
      <header className="karma-landing-hero">
        <p className="karma-landing-eyebrow">Vedic astrology · Past life · Karmic patterns</p>
        <h1 className="karma-landing-h1">Past Life Karma Analysis from Your Birth Chart</h1>
        <p className="karma-landing-lead">
          Understand past-life themes, karmic debts, and spiritual lessons using classical Jyotish—Navamsa (D9),
          Shashtiamsa (D60), the 12th house, Saturn, and Rahu–Ketu—calculated for your exact date, time, and place
          of birth. Read the guide below, then get your personalised AI-assisted report on AstroRoshni.
        </p>
        <button type="button" className="karma-landing-cta" onClick={onGetStarted}>
          Get your personalised karma report
        </button>
        <p className="karma-landing-cta-note">
          Sign in, save your birth chart, and run the analysis in the tool below.{' '}
          <a href="#karma-tool">Jump to tool ↓</a>
        </p>
      </header>

      <section className="karma-landing-section" aria-labelledby="karma-what-heading">
        <h2 id="karma-what-heading">What is past life karma in Vedic astrology?</h2>
        <p>
          Karma in Sanskrit means action and its consequences. Vedic astrology (Jyotish) does not claim to show a
          cinematic replay of a previous incarnation; instead it maps <strong>karmic patterns</strong>—tendencies,
          obligations, talents, and repeating lessons—through the birth chart and divisional charts computed at birth.
        </p>
        <p>
          Practitioners look at the radix (D1) chart for life themes, <strong>Navamsa (D9)</strong> for the soul’s
          deeper direction, and <strong>Shashtiamsa (D60)</strong> for subtler residue from past cycles. The{' '}
          <strong>12th house</strong> relates to moksha, loss, and the subconscious; <strong>Saturn</strong> often
          marks discipline and debts; <strong>Rahu and Ketu</strong> (lunar nodes) describe obsession and release.
          Together they form a coherent picture of what you are working through in this life.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="karma-how-heading">
        <h2 id="karma-how-heading">How AstroRoshni analyses your karma</h2>
        <ol className="karma-landing-steps">
          <li>
            <strong>Accurate chart calculation</strong> — Your birth data is converted to sidereal positions using
            standard Vedic methods (ayanamsa and house system as used across the app).
          </li>
          <li>
            <strong>Divisional focus</strong> — D9 and D60 are computed and interpreted alongside the birth chart and
            current dasha periods where available.
          </li>
          <li>
            <strong>Structured AI interpretation</strong> — A multi-section report explains themes in plain language,
            grounded in chart factors—not random psychic claims.
          </li>
          <li>
            <strong>Private to your account</strong> — Reports are stored for your chart; they are not published as
            public pages.
          </li>
        </ol>
        <p>
          Explore related tools:{' '}
          <Link to="/panchang">daily Panchang</Link>,{' '}
          <Link to="/kundli-matching">Kundli matching</Link>,{' '}
          <Link to="/nakshatras">27 Nakshatras</Link>, and{' '}
          <Link to="/beginners-guide">Vedic astrology for beginners</Link>.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="karma-report-heading">
        <h2 id="karma-report-heading">What your personalised report includes</h2>
        <ul className="karma-landing-report-grid">
          {KARMA_REPORT_SECTIONS.map((item) => (
            <li key={item.title}>
              <span className="karma-landing-report-icon" aria-hidden="true">
                {item.icon}
              </span>
              <div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="karma-landing-section karma-landing-sample" aria-labelledby="karma-sample-heading">
        <h2 id="karma-sample-heading">Sample tone of interpretation (illustrative)</h2>
        <blockquote cite={KARMA_CANONICAL}>
          <p>{KARMA_SAMPLE_EXCERPT}</p>
        </blockquote>
        <p className="karma-landing-disclaimer">
          This excerpt is for illustration only. Your report is generated from your unique chart.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="karma-faq-heading">
        <h2 id="karma-faq-heading">Frequently asked questions</h2>
        <dl className="karma-landing-faq">
          {KARMA_FAQ.map((item) => (
            <React.Fragment key={item.question}>
              <dt>{item.question}</dt>
              <dd>{item.answer}</dd>
            </React.Fragment>
          ))}
        </dl>
      </section>

      <section className="karma-landing-section karma-landing-trust">
        <h2>Trust & limitations</h2>
        <p>
          AstroRoshni provides spiritual and astrological guidance for reflection and education. It is not medical,
          legal, or financial advice. For serious mental health or life decisions, consult qualified professionals.
          Analysis quality depends on accurate birth time and location.
        </p>
        <p>
          <Link to="/about">About AstroRoshni</Link> · <Link to="/policy">Privacy Policy</Link> ·{' '}
          <Link to="/contact">Contact</Link>
        </p>
      </section>
    </article>
  );
};

export default KarmaAnalysisLanding;
