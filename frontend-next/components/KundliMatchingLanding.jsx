import KundliGetStartedButton from '@/components/KundliGetStartedButton';
import { craHref, kundliAppHref } from '@/lib/navigation';
import {
  ASHTAKOOTA_KOOTS,
  KUNDLI_ANALYSIS_STEPS,
  KUNDLI_CANONICAL,
  KUNDLI_DEEP_TOPICS,
  KUNDLI_FAQ,
  KUNDLI_REPORT_SECTIONS,
  KUNDLI_SCORE_BANDS,
  KUNDLI_SAMPLE_EXCERPT,
} from '@/lib/kundliSeoContent';

export default function KundliMatchingLanding() {
  return (
    <article className="karma-landing kundli-landing" id="kundli-guide">
      <header className="karma-landing-hero kundli-landing-hero">
        <p className="karma-landing-eyebrow">Vedic astrology · Marriage compatibility · AI report</p>
        <h1 className="karma-landing-h1">Kundli Matching by Date, Time and Place of Birth</h1>
        <p className="karma-landing-lead">
          Compare two Vedic birth charts with Ashtakoot Guna Milan, Manglik analysis, D9/Navamsa support,
          relationship indicators, marriage timing climate, and an AI-assisted compatibility report in plain language.
        </p>
        <KundliGetStartedButton />
        <p className="karma-landing-cta-note">
          Sign in, select saved charts or enter both birth details, then run free matching.{' '}
          <a href={kundliAppHref()}>Open the matching tool</a>
        </p>
      </header>

      <section className="karma-landing-section" aria-labelledby="kundli-what-heading">
        <h2 id="kundli-what-heading">What is Kundli matching?</h2>
        <p>
          Kundli matching, also known as horoscope matching or Guna Milan, compares two Janam Kundlis to understand
          how a relationship may function in marriage. The traditional starting point is <strong>Ashtakoot Milan</strong>,
          a 36-point system based mainly on the Moon sign and Nakshatra of both partners.
        </p>
        <p>
          A useful reading does not stop at the total score. AstroRoshni also checks <strong>Manglik compatibility</strong>,
          chart-level marriage support, D9/Navamsa indications, cross-chart chemistry, contradictions, and current timing
          windows. This gives a more realistic view than a simple pass/fail score.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="kundli-how-heading">
        <h2 id="kundli-how-heading">How online Kundli matching works</h2>
        <p>
          For accurate marriage compatibility, both charts need the date of birth, time of birth, and place of birth.
          AstroRoshni calculates the birth charts first, then compares traditional Guna Milan with deeper relationship
          indicators. This helps logged-out visitors understand the method before they sign in or enter private details.
        </p>
        <ol className="karma-landing-steps kundli-process-list">
          {KUNDLI_ANALYSIS_STEPS.map((step) => (
            <li key={step.title}>
              <strong>{step.title}</strong> — {step.desc}
            </li>
          ))}
        </ol>
      </section>

      <section className="karma-landing-section" aria-labelledby="kundli-ashtakoot-heading">
        <h2 id="kundli-ashtakoot-heading">Ashtakoot Guna Milan: 8 koots and 36 points</h2>
        <p>
          The Ashtakoot system divides compatibility into eight factors. Each factor has a maximum point value, and
          the combined score is shown out of 36. Traditionally, 18+ is treated as workable, but exceptions and full-chart
          context matter a lot.
        </p>
        <ul className="karma-landing-report-grid kundli-koot-grid">
          {ASHTAKOOTA_KOOTS.map((item) => (
            <li key={item.name}>
              <span className="kundli-koot-points" aria-label={`${item.points} points`}>
                {item.points}
              </span>
              <div>
                <h3>{item.name}</h3>
                <p>{item.desc}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="karma-landing-section" aria-labelledby="kundli-score-heading">
        <h2 id="kundli-score-heading">How to read the Kundli matching score</h2>
        <p>
          The Guna score is a useful starting point, but it should be read as a diagnostic signal, not a final verdict.
          Two charts with the same score can have very different relationship realities depending on which koots are weak,
          whether doshas are cancelled, and how the full charts support marriage.
        </p>
        <div className="kundli-score-table" role="table" aria-label="Kundli matching score interpretation">
          {KUNDLI_SCORE_BANDS.map((band) => (
            <div className="kundli-score-row" role="row" key={band.score}>
              <div className="kundli-score-cell kundli-score-value" role="cell">{band.score}</div>
              <div className="kundli-score-cell" role="cell">
                <strong>{band.title}</strong>
                <p>{band.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="karma-landing-section" aria-labelledby="kundli-deep-heading">
        <h2 id="kundli-deep-heading">What AstroRoshni checks beyond basic Guna Milan</h2>
        <p>
          Many online Kundli matching calculators only show a number. A serious marriage compatibility reading should
          explain why the number is high or low, where the pair has natural support, and what topics need conscious work.
        </p>
        <div className="kundli-topic-stack">
          {KUNDLI_DEEP_TOPICS.map((topic) => (
            <section className="kundli-topic" key={topic.title} aria-label={topic.title}>
              <h3>{topic.title}</h3>
              <p>{topic.body}</p>
            </section>
          ))}
        </div>
      </section>

      <section className="karma-landing-section" aria-labelledby="kundli-ai-heading">
        <h2 id="kundli-ai-heading">AI-based Kundli matching on AstroRoshni</h2>
        <p>
          The free matching result gives you a structured compatibility score and chart indicators. The premium AI
          report explains the same evidence as a readable relationship guidance report: where the pair feels naturally
          supportive, where adjustment is needed, and what practical conversations should happen before commitment.
        </p>
        <ul className="karma-landing-report-grid">
          {KUNDLI_REPORT_SECTIONS.map((item) => (
            <li key={item.title}>
              <span className="karma-landing-report-icon" aria-hidden="true">
                •
              </span>
              <div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="karma-landing-section" aria-labelledby="kundli-beyond-heading">
        <h2 id="kundli-beyond-heading">Why the Guna score alone is not enough</h2>
        <p>
          A high Guna score can still hide friction if Manglik imbalance, weak 7th-house support, difficult Venus-Mars
          exchange, or challenging timing is present. A moderate score can still be workable when the deeper chart shows
          emotional maturity, shared values, and strong D9 support.
        </p>
        <p>
          That is why AstroRoshni combines traditional matching with chart synthesis. The goal is not fear-based rejection;
          it is to understand compatibility clearly enough to make grounded decisions.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="kundli-use-cases-heading">
        <h2 id="kundli-use-cases-heading">Who can use this Kundli matching tool?</h2>
        <p>
          The tool is designed for arranged marriage discussions, love marriage compatibility, families comparing charts,
          and couples who want a structured Vedic view of long-term relationship dynamics. It can be used before a formal
          proposal, during engagement conversations, or when a couple wants to understand recurring emotional patterns.
        </p>
        <p>
          You can run matching with freshly entered birth details or select saved charts from your AstroRoshni account.
          The public guide stays visible for everyone; personal chart data and AI reports remain inside the logged-in app.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="kundli-related-heading">
        <h2 id="kundli-related-heading">Related Vedic astrology tools</h2>
        <p>
          Kundli matching is strongest when read with the broader life context. You may also want to explore{' '}
          <a href={craHref('/marriage-analysis')}>personal marriage analysis</a>,{' '}
          <a href={craHref('/karma-analysis')}>karma analysis</a>, <a href={craHref('/panchang')}>daily Panchang</a>,{' '}
          <a href={craHref('/muhurat-finder')}>muhurat finder</a>, and{' '}
          <a href={craHref('/nakshatras')}>Nakshatra meanings</a>.
        </p>
      </section>

      <section className="karma-landing-section karma-landing-sample" aria-labelledby="kundli-sample-heading">
        <h2 id="kundli-sample-heading">Sample interpretation style</h2>
        <blockquote cite={KUNDLI_CANONICAL}>
          <p>{KUNDLI_SAMPLE_EXCERPT}</p>
        </blockquote>
        <p className="karma-landing-disclaimer">
          This is illustrative only. Your report is generated from the exact birth details of both people.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="kundli-faq-heading">
        <h2 id="kundli-faq-heading">Frequently asked questions</h2>
        <dl className="karma-landing-faq">
          {KUNDLI_FAQ.map((item) => (
            <div key={item.question} className="karma-faq-entry">
              <dt>{item.question}</dt>
              <dd>{item.answer}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="karma-landing-section karma-landing-trust">
        <h2>Trust & limitations</h2>
        <p>
          Kundli matching is spiritual and astrological guidance for reflection. It is not a guarantee of marriage
          success and should not replace personal judgment, communication, family context, or professional counselling.
          Analysis quality depends on accurate birth time and location for both partners.
        </p>
        <p>
          <a href={craHref('/about')}>About AstroRoshni</a> · <a href={craHref('/policy')}>Privacy Policy</a> ·{' '}
          <a href={craHref('/contact')}>Contact</a>
        </p>
      </section>
    </article>
  );
}
