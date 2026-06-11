import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import SEOHead from '../SEO/SEOHead';
import CreditsModal from '../Credits/CreditsModal';
import CompatibilityAnalysis from './CompatibilityAnalysis';
import { useAstrology } from '../../context/AstrologyContext';
import './KundliMatchingPage.css';

const faqItems = [
  {
    question: 'Is this Kundli matching free?',
    answer:
      'The first compatibility result is free and includes Ashtakoot Guna Milan, Manglik balance, an overall verdict, and timing climate. A detailed report is optional.'
  },
  {
    question: 'What birth details are needed for Kundli matching?',
    answer:
      'You need the birth date, exact birth time, and birth place for both people. Accurate time and place help calculate Moon nakshatra, houses, D9 Navamsa, and timing factors.'
  },
  {
    question: 'Does AstroRoshni only use 36 Gunas?',
    answer:
      'No. The result starts with traditional 36-point Ashtakoot matching and also considers Manglik status, D1/D9 marriage support, contradictions, and timing climate.'
  },
  {
    question: 'Can low Guna Milan still work?',
    answer:
      'Sometimes. A low score may be softened by stronger deeper chart support, timing, or specific exceptions. The report highlights both strengths and caution areas.'
  },
  {
    question: 'How accurate is online Kundli matching?',
    answer:
      'Accuracy depends on the birth details and the depth of analysis. AstroRoshni uses the classical Ashtakoot score as a foundation, then adds Manglik balance, D1/D9 marriage indicators, contradictions, and timing signals so the result is not based on one number alone.'
  },
  {
    question: 'What is a good Guna Milan score for marriage?',
    answer:
      'Traditionally 18 out of 36 is treated as the basic acceptable threshold, but a higher score does not automatically guarantee harmony. Nadi, Bhakoot, Gana, Manglik balance, seventh-house strength, Navamsa support, and the couple’s real-world maturity also matter.'
  },
  {
    question: 'Is Nadi Dosha always a deal breaker?',
    answer:
      'No. Nadi Dosha is important because it carries 8 points in Ashtakoot, but many charts have exceptions or compensating factors. The report treats it as a serious caution area and checks whether other compatibility signals reduce or increase the concern.'
  },
  {
    question: 'What does Bhakoot Dosha mean in Kundli matching?',
    answer:
      'Bhakoot compares the Moon sign relationship between two charts and can indicate emotional rhythm, family adjustment, and long-term support. A weak Bhakoot result should be read with the full chart instead of being judged in isolation.'
  },
  {
    question: 'Does Manglik Dosha cancel when both partners are Manglik?',
    answer:
      'It can be balanced in many cases, but the answer depends on placement, severity, house involved, and other protective factors. AstroRoshni checks pair-level Manglik compatibility instead of only marking each person as Manglik or non-Manglik.'
  },
  {
    question: 'Can Kundli matching help for love marriage?',
    answer:
      'Yes. For love marriage, Kundli matching is useful for understanding long-term adjustment, family pressure, emotional patterns, conflict style, and timing. It should support a practical decision, not replace the couple’s lived experience.'
  },
  {
    question: 'Can this be used before talking to an astrologer?',
    answer:
      'Yes. The free report gives a structured first view of the match, which can help you ask better questions if you later consult an astrologer. The detailed report adds a more complete interpretation for strengths, risks, and next steps.'
  },
  {
    question: 'Does the report suggest remedies?',
    answer:
      'The free result focuses on compatibility signals and caution areas. When a serious concern appears, the detailed report can explain the practical meaning and suggest the kind of remedial direction to discuss with a qualified astrologer.'
  },
  {
    question: 'Can I match saved birth charts?',
    answer:
      'Yes. Signed-in users can choose saved birth charts through the same birth detail picker used across the website, or enter fresh details for both partners.'
  },
  {
    question: 'Is my birth data private?',
    answer:
      'Your birth details are used to calculate the compatibility report and saved chart features. AstroRoshni does not show private birth details publicly on the Kundli matching page.'
  },
  {
    question: 'What is included in the detailed Kundli matching report?',
    answer:
      'The detailed report explains the match in clearer relationship language, including strengths, caution areas, timing, marriage support, emotional fit, and practical guidance beyond the free score summary.'
  }
];

const structuredData = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'WebApplication',
      name: 'AstroRoshni Kundli Matching',
      url: 'https://astroroshni.com/kundli-matching',
      applicationCategory: 'LifestyleApplication',
      operatingSystem: 'Web',
      description:
        'Free Kundli matching tool with Ashtakoot Guna Milan, Manglik compatibility, marriage support, timing climate, and optional AI relationship guidance.',
      offers: {
        '@type': 'Offer',
        price: '0',
        priceCurrency: 'INR'
      },
      publisher: {
        '@type': 'Organization',
        name: 'AstroRoshni',
        url: 'https://astroroshni.com'
      }
    },
    {
      '@type': 'FAQPage',
      mainEntity: faqItems.map((item) => ({
        '@type': 'Question',
        name: item.question,
        acceptedAnswer: {
          '@type': 'Answer',
          text: item.answer
        }
      }))
    },
    {
      '@type': 'BreadcrumbList',
      itemListElement: [
        {
          '@type': 'ListItem',
          position: 1,
          name: 'Home',
          item: 'https://astroroshni.com/'
        },
        {
          '@type': 'ListItem',
          position: 2,
          name: 'Kundli Matching',
          item: 'https://astroroshni.com/kundli-matching'
        }
      ]
    }
  ]
};

const KundliMatchingPage = ({
  user,
  onLogout,
  onAdminClick,
  onLogin,
  showLoginButton = true
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { birthData } = useAstrology();
  const [showCreditsModal, setShowCreditsModal] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(location.search || '');
    const shouldOpenLogin = location.state?.openLogin || params.get('login') === '1';
    if (!user && shouldOpenLogin && onLogin) {
      onLogin();
      params.delete('login');
      const search = params.toString();
      navigate(`${location.pathname}${search ? `?${search}` : ''}`, { replace: true, state: {} });
    }
  }, [user, location.state?.openLogin, location.search, onLogin, navigate, location.pathname]);

  const handleAdmin = () => {
    if (onAdminClick) onAdminClick();
  };

  return (
    <div className="kundli-matching-page">
      <SEOHead
        title="Free Kundli Matching by Date of Birth | Ashtakoot Guna Milan | AstroRoshni"
        description="Match two Kundlis with free Ashtakoot Guna Milan, Manglik compatibility, D1/D9 marriage support, timing climate, strengths, caution areas, and an optional detailed report."
        keywords="kundli matching, free kundli matching, horoscope matching, guna milan, ashtakoot matching, manglik matching, marriage compatibility, kundali milan, birth chart compatibility"
        canonical="https://astroroshni.com/kundli-matching"
        structuredData={structuredData}
      />
      <NavigationHeader
        compact
        showZodiacSelector={false}
        user={user}
        onAdminClick={handleAdmin}
        onLogout={onLogout}
        birthData={birthData}
        onChangeNative={() => navigate('/')}
        onCreditsClick={() => setShowCreditsModal(true)}
        onLogin={onLogin}
        showLoginButton={showLoginButton}
      />
      <main className="kundli-matching-main">
        <header className="kundli-matching-hero" id="kundli-matching-tool">
          <button type="button" className="kundli-matching-back" onClick={() => navigate(-1)}>
            ← Back
          </button>
          <div
            className="kundli-matching-hero-grid"
            style={{ '--kundli-hero-image': `url(${process.env.PUBLIC_URL || ''}/images/software/birth-chart.png)` }}
          >
            <div className="kundli-matching-hero-copy">
              <p className="kundli-matching-eyebrow">Free Kundli matching</p>
              <h1>AstroRoshni Kundli Matching</h1>
              <p className="kundli-matching-sub">
                Compare two birth charts with Ashtakoot Guna Milan, Manglik balance, deeper D1/D9 marriage support,
                and current timing climate before unlocking the detailed report.
              </p>
              <div className="kundli-matching-hero-actions">
                <a href="#kundli-match-form" className="kundli-matching-primary-link">Start free match</a>
                <a href="#kundli-matching-method" className="kundli-matching-secondary-link">See method</a>
              </div>
            </div>

            <div className="kundli-matching-proof" aria-label="Kundli matching coverage">
              <div>
                <strong>36</strong>
                <span>Guna Milan points</span>
              </div>
              <div>
                <strong>D1/D9</strong>
                <span>Marriage support</span>
              </div>
              <div>
                <strong>Timing</strong>
                <span>Current climate</span>
              </div>
            </div>
          </div>
        </header>
        <section className="kundli-matching-trust-spine" aria-label="What the free Kundli matching checks">
          {[
            ['Ashtakoot', 'Traditional 8-koot score with Nadi, Bhakoot, Gana, Tara, Yoni, and Graha Maitri.'],
            ['Manglik', 'Pair-level Manglik compatibility, not only one-person labels.'],
            ['Marriage Support', 'D1 seventh-house and D9 Navamsa signals for long-term stability.'],
            ['Timing Climate', 'Current and upcoming windows for commitment readiness.']
          ].map(([title, body]) => (
            <article key={title} className="kundli-matching-trust-card">
              <h2>{title}</h2>
              <p>{body}</p>
            </article>
          ))}
        </section>

        <section className="kundli-matching-panel" id="kundli-match-form" aria-label="Free Kundli matching form">
          <CompatibilityAnalysis user={user} onLogin={onLogin} onBuyCredits={() => setShowCreditsModal(true)} />
        </section>

        <section className="kundli-matching-seo" id="kundli-matching-method">
          <div className="kundli-matching-seo-header">
            <p className="kundli-matching-eyebrow">Classical matching, clearer decisions</p>
            <h2>What this Kundli matching report includes</h2>
            <p>
              AstroRoshni gives a real free compatibility result first. The score is only the starting point; the page also shows
              why the match looks supportive, where caution is needed, and whether the present timing favors commitment.
            </p>
          </div>
          <div className="kundli-matching-seo-grid">
            <article>
              <h3>Ashtakoot Guna Milan</h3>
              <p>
                The report calculates the traditional 36-point system across Varna, Vashya, Tara, Yoni, Graha Maitri,
                Gana, Bhakoot, and Nadi, with plain-language interpretations for each koot.
              </p>
            </article>
            <article>
              <h3>Manglik compatibility</h3>
              <p>
                Instead of treating Manglik as a simple yes/no fear label, the match checks severity and pair-level balance
                so the result is more useful for real relationship decisions.
              </p>
            </article>
            <article>
              <h3>D1 and D9 marriage support</h3>
              <p>
                Deeper chart support can explain why a match feels stronger or weaker than the raw Guna score suggests,
                especially when the seventh house or Navamsa tells a different story.
              </p>
            </article>
            <article>
              <h3>Timing guidance</h3>
              <p>
                Relationship readiness changes with dasha and transit climate. The free report highlights the current climate
                and visible favorable windows before the optional premium interpretation.
              </p>
            </article>
          </div>
        </section>

        <section className="kundli-matching-faq" aria-label="Kundli matching FAQ">
          <h2>Kundli Matching FAQ</h2>
          <div className="kundli-matching-faq-grid">
            {faqItems.map((item) => (
              <article key={item.question}>
                <h3>{item.question}</h3>
                <p>{item.answer}</p>
              </article>
            ))}
          </div>
        </section>
      </main>
      <CreditsModal isOpen={showCreditsModal} onClose={() => setShowCreditsModal(false)} onLogin={onLogin} />
    </div>
  );
};

export default KundliMatchingPage;
