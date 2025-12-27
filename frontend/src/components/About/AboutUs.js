import React from 'react';
import NavigationHeader from '../Shared/NavigationHeader';
import './AboutUs.css';

const AboutUs = ({ user, onLogout, onLogin }) => {
  const stats = [
    { label: 'Specialized Calculators', value: '84+' },
    { label: 'Analytical Systems', value: '75+' },
    { label: 'Calculation Accuracy', value: '99.9%' },
    { label: 'Active Users', value: '50k+' },
  ];

  const corePillars = [
    {
      icon: '🔬',
      title: "The Vedic Physics Engine",
      desc: "Unlike standard apps, AstroRoshni uses a proprietary synthesis engine that processes 84+ specialized calculators simultaneously, including Shodashvarga (D1-D60) and Nadi links."
    },
    {
      icon: '🛡️',
      title: "Root-to-Fruit Logic",
      desc: "Our 'Double Confirmation' protocol cross-references physical potential (D1) with internal strength (D9), ensuring predictions are mathematically derived, not just generated."
    },
    {
      icon: '⚡',
      title: "Real-Time Transit Triggers",
      desc: "We track planetary transits within 0.1° of your natal placements to identify the exact month of 'Life Pivot Points' and karmic activations."
    },
    {
      icon: '📊',
      title: "Ashtakavarga Oracle System",
      desc: "Advanced Sarvashtakavarga and Bhinnashtakavarga calculations filter transit predictions through house strength analysis, preventing false promises of 'great years' that turn mediocre."
    },
    {
      icon: '🎯',
      title: "Sniper Points Technology",
      desc: "Proprietary Mrityu Bhaga calculator identifies exact degrees of vulnerability in D1, D3, and D9 charts, enabling month-level precision for health and crisis timing."
    },
    {
      icon: '🔄',
      title: "Multi-Dasha Synthesis",
      desc: "Simultaneous analysis of Vimshottari, Chara, Yogini, Kalachakra, and Shoola dashas creates nuanced predictions where other systems disagree, revealing complex life patterns."
    },
    {
      icon: '🌟',
      title: "Jaimini Full System",
      desc: "Complete Rashi Drishti analysis with Atmakaraka-Amatyakaraka yogas, Arudha Lagna calculations, and sign-based aspects that reveal hidden connections missed by planetary aspects alone."
    },
    {
      icon: '💎',
      title: "Nadi Linkage Matrix",
      desc: "Bhrigu Nandi Nadi connections between planets define the exact nature of events - Saturn+Mars links indicate technical careers, Venus+Ketu shows delayed but spiritual marriages."
    },
    {
      icon: '🔮',
      title: "Sudarshana Triple View",
      desc: "Every prediction is verified from Lagna (body), Moon (mind), and Sun (soul) perspectives using the ancient Sudarshana Chakra method for 360-degree accuracy."
    }
  ];

  return (
    <div className="about-page">
      <NavigationHeader 
        user={user}
        onLogout={onLogout}
        onLogin={onLogin}
        showLoginButton={!user}
      />
      {/* Hero Section */}
      <section className="about-hero">
        <div className="container">
          <h1>The Science Behind <span className="highlight">AstroRoshni</span></h1>
          <p className="hero-subtitle">
            World's first high-precision analytical engine for Vedic Astrology, 
            driven by 84+ deterministic algorithms.
          </p>
        </div>
      </section>

      {/* Stats Ribbon */}
      <section className="stats-ribbon">
        <div className="container stats-grid">
          {stats.map((stat, i) => (
            <div key={i} className="stat-card">
              <h3>{stat.value}</h3>
              <p>{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Philosophy Section */}
      <section className="philosophy-section">
        <div className="container">
          <div className="philosophy-grid">
            <div className="philosophy-text">
              <h2>Beyond "General" Predictions</h2>
              <p>
                In a digital landscape filled with generic sun-sign horoscopes, 
                AstroRoshni was built to restore the mathematical integrity of Jyotish. 
                Our engine, <strong>Tara</strong>, doesn't just chat—she calculates.
              </p>
              <p>
                By integrating Parashari, Jaimini, Nadi, and Financial systems, 
                we provide a 360-degree view of your karma, health, and wealth 
                from three simultaneous perspectives: the Ascendant, Moon, and Sun.
              </p>
            </div>
            <div className="philosophy-visual">
              <div className="engine-placeholder">84+ Calculators Active</div>
            </div>
          </div>
        </div>
      </section>

      {/* Core Technology Pillars */}
      <section className="pillars-section">
        <div className="container">
          <h2 className="section-title">Why We Are Different</h2>
          <div className="pillars-grid">
            {corePillars.map((pillar, i) => (
              <div key={i} className="pillar-card">
                <div className="icon-wrapper">{pillar.icon}</div>
                <h3>{pillar.title}</h3>
                <p>{pillar.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust & Transparency Section */}
      <section className="trust-transparency">
        <div className="container">
          <div className="trust-card">
            <div className="trust-badge">🔒</div>
            <h2>Trust & Transparency</h2>
            <p>
              AstroRoshni is committed to ethical astrology and complete privacy. We never predict exact 
              death dates or provide medical diagnoses. Instead, we use our <strong>Sniper Points 
              & Mrityu Bhaga</strong> logic to highlight periods of high physical 
              vulnerability, empowering you to take proactive care.
            </p>
            <p>
              <strong>Your Privacy is Sacred:</strong> All birth details and chat messages are protected with 
              end-to-end encryption. Your conversations with Tara remain completely private - 
              no human ever sees your personal questions or astrological data. What you share stays between you and our AI.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default AboutUs;