import { CRA_HOME_ACCURACY_ITEMS, CRA_HOME_FAQS } from '../lib/craHomeSeo';
import { HOME_FEATURES, HOME_METHOD_CARDS } from '../lib/homeSeoContent';
import { chatAppHref } from '../lib/navigation';

export default function HomeLanding() {
  return (
    <main className="home-seo-page">
      <section className="home-hero" aria-labelledby="home-hero-heading">
        <div className="home-hero-copy">
          <p className="home-eyebrow">AI Vedic astrology · Kundli · Panchang · Ask Tara</p>
          <h1 id="home-hero-heading">AstroRoshni — Best Vedic Astrology and Horoscope Predictions Online</h1>
          <p className="home-lead">
            Get accurate Vedic astrology predictions, free Kundli, horoscope matching, daily horoscopes, and expert-style
            chart guidance with Tara. Ask career, marriage, health, wealth, dasha, transit, and timing questions from your
            Janam Kundli using dashas, divisional charts, Ashtakavarga, nakshatras, Panchang, and current transits.
          </p>
          <div className="home-hero-actions">
            <a className="home-primary-cta" href="/chat">
              Read about AI chat
            </a>
            <a className="home-secondary-cta" href={chatAppHref()}>
              Start Ask Tara
            </a>
          </div>
        </div>
        <div className="home-hero-media" aria-label="AstroRoshni mobile app preview">
          <img src="/images/AppHomepage.png" alt="AstroRoshni mobile app showing Vedic astrology tools" />
        </div>
      </section>

      <section className="home-editorial-section" aria-labelledby="home-editorial-heading">
        <h2 id="home-editorial-heading">Why AstroRoshni for Janam Kundli and Vedic timing</h2>
        <p>
          AstroRoshni combines traditional Parashari principles with modern computation: Swiss Ephemeris positions,
          Vimshottari and Jaimini dashas, Yogini Dasha, divisional charts (Vargas), Ashtakavarga, yoga and dosha detection,
          and gochar overlays. Whether you need{' '}
          <a href="/kundli-matching">Kundli matching for marriage</a>, a{' '}
          <a href="/panchang">daily Panchang</a> for muhurat planning, or a chart-grounded conversation in{' '}
          <a href="/chat">Ask Tara</a>, the same engine reads your saved birth data end to end.
        </p>
        <p>
          For relationship and longevity themes beyond Guna Milan, see{' '}
          <a href="/karma-analysis">past-life karma analysis</a> and the in-app life-path tools. Western Sun-sign style
          horoscopes are generic; Tara answers from <strong>your</strong> Lagna, houses, Moon nakshatra, and active
          planetary periods.
        </p>
      </section>

      <section className="home-tool-section" aria-labelledby="home-tools-heading">
        <div className="home-section-heading">
          <h2 id="home-tools-heading">Popular AstroRoshni tools</h2>
          <p>Start with a public guide, then open the signed-in app when you want a personal chart reading.</p>
        </div>
        <div className="home-tool-grid">
          {HOME_FEATURES.map((feature) => (
            <a className="home-tool-card" href={feature.href} key={feature.title}>
              <h3>{feature.title}</h3>
              <p>{feature.body}</p>
              <span>Open guide</span>
            </a>
          ))}
        </div>
      </section>

      <section className="home-accuracy-section" aria-labelledby="home-accuracy-heading">
        <div className="home-section-heading">
          <h2 id="home-accuracy-heading">Tara AI technical architecture and accuracy proofs</h2>
          <p>
            The same capability list appears in our structured data so search engines can associate this page with Tara’s
            calculation depth.
          </p>
        </div>
        <ol className="home-accuracy-list">
          {CRA_HOME_ACCURACY_ITEMS.map((item) => (
            <li key={item.name}>
              <h3>{item.name}</h3>
              <p>{item.description}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="home-method-section" aria-labelledby="home-method-heading">
        <div className="home-section-heading">
          <h2 id="home-method-heading">How Tara AI astrology works</h2>
          <p>Answer-first explanations for people comparing AI astrology, Kundli analysis, and generic horoscopes.</p>
        </div>
        <div className="home-method-grid">
          {HOME_METHOD_CARDS.map((item) => (
            <article className="home-method-card" key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.answer}</p>
              <div className="home-card-links">
                {item.links.map((link) => (
                  <a href={link.href} key={`${item.title}-${link.href}`}>
                    {link.label}
                  </a>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="home-proof-section" aria-labelledby="home-proof-heading">
        <div className="home-section-heading">
          <h2 id="home-proof-heading">Chart layers Tara reads</h2>
          <p>
            Tara is built around complete chart context: Lagna, houses, planets, nakshatras, Vimshottari Dasha, Jaimini
            Chara Dasha, Yogini Dasha, divisional charts, Ashtakavarga, yogas, doshas, and gochar transits.
          </p>
        </div>
        <div className="home-proof-grid">
          <div>
            <strong>Birth data</strong>
            <span>Date, accurate birth time, and birth place.</span>
          </div>
          <div>
            <strong>Prediction timing</strong>
            <span>Dasha periods, transit activations, and event windows.</span>
          </div>
          <div>
            <strong>Relationship context</strong>
            <span>Ashtakoot, Manglik, Navamsa, and cross-chart compatibility.</span>
          </div>
        </div>
      </section>

      <section className="home-play-section" aria-labelledby="home-play-heading">
        <div className="home-section-heading">
          <h2 id="home-play-heading">AstroRoshni on Google Play</h2>
          <p>
            AI Kundli, horoscope, kundali matching, and Ask Tara on Android — same structured data references this banner
            asset for rich results where eligible.
          </p>
        </div>
        <div className="home-play-banner">
          <a href="https://play.google.com/store/apps/details?id=com.astroroshni.mobile&pcampaignid=web_share">
            <img
              src="/images/homepage-life-path-banner.png"
              width={1200}
              height={656}
              alt="Discover your life path with AstroRoshni — AI Vedic astrology app for Kundli, daily horoscope, marriage matching, and live chat with an AI astrologer on Google Play"
            />
          </a>
        </div>
      </section>

      <section className="home-faq-section" aria-labelledby="home-faq-heading">
        <div className="home-section-heading">
          <h2 id="home-faq-heading">Frequently asked questions</h2>
          <p>Questions and answers match the FAQPage JSON-LD on this URL for consistent indexing.</p>
        </div>
        <div className="home-faq-list">
          {CRA_HOME_FAQS.map((faq) => (
            <details className="home-faq-item" key={faq.question}>
              <summary>{faq.question}</summary>
              <p>{faq.answer}</p>
            </details>
          ))}
        </div>
      </section>
    </main>
  );
}
