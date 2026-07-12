import ReportsGetStartedButton from './ReportsGetStartedButton';
import { craHref, reportsAppHref } from '../lib/navigation';
import {
  REPORT_PDF_SECTIONS,
  REPORT_STUDIO_STEPS,
  REPORT_TYPES,
  REPORT_VS_OTHER_TOOLS,
  REPORTS_FAQ,
} from '../lib/reportsSeoContent';

export default function ReportsLanding() {
  return (
    <article className="karma-landing reports-landing" id="reports-guide">
      <header className="karma-landing-hero reports-landing-hero">
        <p className="karma-landing-eyebrow">Vedic astrology · Premium PDF · Partnership report</p>
        <h1 className="karma-landing-h1">Reports Studio — Deepest Chart Analysis as a Polished PDF</h1>
        <p className="karma-landing-lead">
          Create a premium Vedic partnership report from two birth charts: structured chapters, timing climate,
          strengths, friction points, remedies, and clear takeaways in a shareable 20+ page PDF.
        </p>
        <ReportsGetStartedButton />
        <p className="karma-landing-cta-note">
          Sign in, choose both charts and a language, then generate or reopen your report.{' '}
          <a href={reportsAppHref()}>Open Reports Studio</a>
        </p>
      </header>

      <section className="karma-landing-section" aria-labelledby="reports-what-heading">
        <h2 id="reports-what-heading">What is Reports Studio?</h2>
        <p>
          Reports Studio is AstroRoshni’s home for <strong>full structured PDF reports</strong> — deeper than a free
          score card, and more polished than a long chat thread. The first live report type is the{' '}
          <strong>Partnership Report</strong>, built for marriage, business partnerships, parent–child dynamics, or
          any two-person relationship study.
        </p>
        <p>
          Each report combines classical Vedic signals (Ashtakoot context, Manglik balance, D1/D9 overlays, timing)
          with chapter-level AI narrative so the PDF is readable for families and decision-makers — not only for
          astrology practitioners.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="reports-types-heading">
        <h2 id="reports-types-heading">Report types</h2>
        <ul className="karma-landing-report-grid">
          {REPORT_TYPES.map((item) => (
            <li key={item.title}>
              <h3>{item.title}</h3>
              <p className="reports-type-status">{item.status}</p>
              <p>{item.desc}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="karma-landing-section" aria-labelledby="reports-how-heading">
        <h2 id="reports-how-heading">How Reports Studio works</h2>
        <p>
          The studio follows a simple three-step flow. You stay in control of which charts and language are used,
          and you see credit cost before confirming a fresh generate.
        </p>
        <ol className="karma-landing-steps">
          {REPORT_STUDIO_STEPS.map((step) => (
            <li key={step.title}>
              <strong>{step.title}</strong> — {step.desc}
            </li>
          ))}
        </ol>
      </section>

      <section className="karma-landing-section" aria-labelledby="reports-pdf-heading">
        <h2 id="reports-pdf-heading">What is inside a Partnership Report PDF?</h2>
        <p>
          A Partnership Report is designed as a complete reading you can revisit later — not a one-line verdict.
          Typical sections include:
        </p>
        <ul className="karma-landing-report-grid">
          {REPORT_PDF_SECTIONS.map((item) => (
            <li key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.desc}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="karma-landing-section" aria-labelledby="reports-compare-heading">
        <h2 id="reports-compare-heading">How Reports Studio compares to other AstroRoshni tools</h2>
        {REPORT_VS_OTHER_TOOLS.map((item) => (
          <div key={item.title} className="reports-compare-block">
            <h3>{item.title}</h3>
            <p>{item.body}</p>
          </div>
        ))}
        <p>
          Prefer a quick score first? Try{' '}
          <a href={craHref('/kundli-matching')}>Kundli Matching</a>. Prefer questions as they come up? Open{' '}
          <a href={craHref('/chat')}>AI Chat</a>.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="reports-credits-heading">
        <h2 id="reports-credits-heading">Credits, reopen, and regenerate</h2>
        <p>
          Generating a new Partnership Report uses credits. If you already generated a report for the same pair and
          language, Reports Studio offers <strong>Open report</strong> at no extra charge. Choose{' '}
          <strong>Regenerate</strong> only when you want a fresh AI reading — that uses credits again.
        </p>
        <p>
          This keeps serious reports affordable to revisit while still covering the cost of deep multi-chapter
          generation.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="reports-faq-heading">
        <h2 id="reports-faq-heading">Frequently asked questions</h2>
        <dl className="karma-landing-faq">
          {REPORTS_FAQ.map((item) => (
            <div key={item.question} className="karma-faq-entry">
              <dt>{item.question}</dt>
              <dd>{item.answer}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="karma-landing-section reports-landing-closing" aria-labelledby="reports-cta-heading">
        <h2 id="reports-cta-heading">Ready for the deepest two-chart reading?</h2>
        <p>
          Open Reports Studio, select both charts, confirm language, and generate a premium Partnership Report PDF
          you can keep and share.
        </p>
        <ReportsGetStartedButton>Create your Partnership Report</ReportsGetStartedButton>
      </section>
    </article>
  );
}
