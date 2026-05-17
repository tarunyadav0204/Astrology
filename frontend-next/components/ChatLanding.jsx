import ChatGetStartedButton from '@/components/ChatGetStartedButton';
import { chatAppHref, craHref } from '@/lib/navigation';
import {
  CHAT_CANONICAL,
  CHAT_CAPABILITIES,
  CHAT_FAQ,
  CHAT_HOW_STEPS,
  CHAT_MODES,
  CHAT_SAMPLE_EXCERPT,
  CHAT_TOPIC_AREAS,
} from '@/lib/chatSeoContent';

export default function ChatLanding() {
  return (
    <article className="karma-landing chat-landing" id="chat-guide">
      <header className="karma-landing-hero chat-landing-hero">
        <p className="karma-landing-eyebrow">Vedic astrology · AI astrologer · Birth chart chat</p>
        <h1 className="karma-landing-h1">AI Vedic Astrologer Chat — Ask Tara About Your Kundli</h1>
        <p className="karma-landing-lead">
          Talk to a chart-aware AI astrologer trained on classical Jyotish. Ask career, marriage, health, dasha,
          transit, yoga, and timing questions from your real Janam Kundli—not generic sun-sign text. Choose single
          chart, partnership, or mundane mode, then get streaming answers grounded in houses, divisional charts, and
          current Gochar.
        </p>
        <ChatGetStartedButton />
        <p className="karma-landing-cta-note">
          Sign in, save your birth chart, and start a live session.{' '}
          <a href={chatAppHref()}>Open the chat tool</a>
        </p>
      </header>

      <section className="karma-landing-section" aria-labelledby="chat-what-heading">
        <h2 id="chat-what-heading">What is AstroRoshni AI astrologer chat?</h2>
        <p>
          AstroRoshni chat (Ask Tara) is an online Vedic astrology conversation tied to calculated birth charts. When
          you ask a question, the system does not guess from your zodiac sign alone—it evaluates{' '}
          <strong>Lagna and houses</strong>, <strong>Vimshottari dasha</strong>, <strong>transits</strong>,{' '}
          <strong>yogas and doshas</strong>, and relevant divisional context, then explains the result in clear
          English or Hindi-friendly phrasing.
        </p>
        <p>
          This public guide describes every mode and feature without login. Your private chart data, message history,
          and credit usage stay inside the signed-in app.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="chat-modes-heading">
        <h2 id="chat-modes-heading">Three chat modes for different questions</h2>
        <p>
          Pick the mode that matches your intent before you type. Each mode changes how charts are loaded and how
          answers are framed.
        </p>
        <ul className="karma-landing-report-grid chat-mode-grid">
          {CHAT_MODES.map((mode) => (
            <li key={mode.id}>
              <span className="karma-landing-report-icon" aria-hidden="true">
                {mode.icon}
              </span>
              <div>
                <h3>{mode.title}</h3>
                <p className="chat-mode-subtitle">{mode.subtitle}</p>
                <p>{mode.body}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="karma-landing-section" aria-labelledby="chat-how-heading">
        <h2 id="chat-how-heading">How online Vedic astrology chat works</h2>
        <p>
          Accurate answers start with accurate birth data. For personal questions, use the most precise birth time
          you have; for partnership, configure both charts; for mundane topics, set country and event context.
        </p>
        <ol className="karma-landing-steps">
          {CHAT_HOW_STEPS.map((step) => (
            <li key={step.title}>
              <strong>{step.title}</strong> — {step.desc}
            </li>
          ))}
        </ol>
      </section>

      <section className="karma-landing-section" aria-labelledby="chat-capabilities-heading">
        <h2 id="chat-capabilities-heading">What you can ask and what the chat checks</h2>
        <p>
          The assistant is built for depth, not one-line fortune cookies. Below are the main analysis layers used
          across sessions.
        </p>
        <ul className="karma-landing-report-grid">
          {CHAT_CAPABILITIES.map((item) => (
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

      <section className="karma-landing-section" aria-labelledby="chat-topics-heading">
        <h2 id="chat-topics-heading">Popular topics people ask in chat</h2>
        <p>
          You can ask open-ended questions or use guided flows such as <strong>Find Event Periods</strong> to scan
          when a theme may peak in a selected year. Common areas include:
        </p>
        <ul className="karma-landing-steps chat-topic-list">
          {CHAT_TOPIC_AREAS.map((topic) => (
            <li key={topic}>{topic}</li>
          ))}
        </ul>
      </section>

      <section className="karma-landing-section" aria-labelledby="chat-partnership-heading">
        <h2 id="chat-partnership-heading">Partnership chat for two birth charts</h2>
        <p>
          Partnership mode walks you through selecting two saved or new charts, then choosing a relationship type
          (spouse, romantic partner, parent, child, sibling, business partner, or custom). Suggested starter questions
          appear based on that relationship so you are not staring at a blank box.
        </p>
        <p>
          Answers weigh <strong>synastry-style chemistry</strong>, house overlays, Venus–Mars dynamics, 7th-house
          themes, and timing windows relevant to commitment, communication, or conflict—useful alongside formal{' '}
          <a href={craHref('/kundli-matching')}>Kundli matching</a> when you want a conversational deep dive.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="chat-mundane-heading">
        <h2 id="chat-mundane-heading">Mundane chat for global and collective trends</h2>
        <p>
          Mundane mode is for questions about countries, elections, markets, geopolitical phases, or event categories
          rather than an individual life path. You configure region, year, and optional event timing, then ask about
          trend dynamics and likely phases.
        </p>
        <p>
          Use personal single-chart chat for marriage timing on your own chart; use mundane mode when the subject is
          collective, not natal.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="chat-premium-heading">
        <h2 id="chat-premium-heading">Instant answers, voice, podcast, and credits</h2>
        <p>
          Standard chat streams detailed interpretations. <strong>Instant mode</strong> trades length for speed when
          you need a quick chart check. <strong>Voice chat with Tara</strong> keeps the same setup but lets you speak
          your question. After a strong written answer, you can optionally generate a <strong>podcast-style audio</strong>{' '}
          summary to listen later.
        </p>
        <p>
          Many accounts receive a <strong>free first question</strong> in single-chart mode; partnership, mundane,
          enhanced deep analysis, instant, voice, and podcast features may consume credits according to current app
          pricing. Top up credits from your account when needed.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="chat-vs-heading">
        <h2 id="chat-vs-heading">How this differs from generic AI horoscope bots</h2>
        <p>
          Generic chatbots often invent placements or rely on sun-sign tropes. AstroRoshni computes sidereal
          positions from your birth data, attaches them to the session, and grounds replies in Jyotish structure:
          house lords, dasha periods, transits, and yogas. You can also open chart context during streaming replies
          when the assistant is synthesising a complex answer.
        </p>
        <p>
          It is still software guidance—not a human pundit on video call—and it should be read alongside your own
          judgment, family context, and professional advice where relevant.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="chat-related-heading">
        <h2 id="chat-related-heading">Related AstroRoshni tools</h2>
        <p>
          Chat works best next to structured reports. Explore{' '}
          <a href={craHref('/kundli-matching')}>Kundli matching</a>,{' '}
          <a href={craHref('/karma-analysis')}>past life karma analysis</a>,{' '}
          <a href={craHref('/marriage-analysis')}>marriage analysis</a>,{' '}
          <a href={craHref('/career-guidance')}>career guidance</a>,{' '}
          <a href={craHref('/panchang')}>daily Panchang</a>, and{' '}
          <a href={craHref('/nakshatras')}>27 Nakshatras</a>.
        </p>
      </section>

      <section className="karma-landing-section karma-landing-sample" aria-labelledby="chat-sample-heading">
        <h2 id="chat-sample-heading">Sample interpretation style</h2>
        <blockquote cite={CHAT_CANONICAL}>
          <p>{CHAT_SAMPLE_EXCERPT}</p>
        </blockquote>
        <p className="karma-landing-disclaimer">
          Illustrative only. Your session uses your exact chart, dasha, and transits at question time.
        </p>
      </section>

      <section className="karma-landing-section" aria-labelledby="chat-faq-heading">
        <h2 id="chat-faq-heading">Frequently asked questions</h2>
        <dl className="karma-landing-faq">
          {CHAT_FAQ.map((item) => (
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
          Vedic astrology chat is spiritual and reflective guidance. It does not guarantee outcomes and is not medical,
          legal, or financial advice. Accuracy depends on birth time quality and how clearly you frame your question.
        </p>
        <p>
          <a href={craHref('/about')}>About AstroRoshni</a> · <a href={craHref('/policy')}>Privacy Policy</a> ·{' '}
          <a href={craHref('/contact')}>Contact</a>
        </p>
        <ChatGetStartedButton>Sign in and start chat</ChatGetStartedButton>
      </section>
    </article>
  );
}
