import React from 'react';
import './TrustBanner.css';

const TrustBanner = () => {
  return (
    <section className="trust-banner">
      <div className="container">
        <div className="trust-header">
          <div className="main-shield">🛡️</div>
          <h2>The AstroRoshni Trust Protocol</h2>
          <p>Deterministic Astrology based on the "Root-to-Fruit" Synthesis</p>
        </div>

        <div className="logic-grid">
          <div className="logic-card">
            <div className="logic-icon-wrapper">🔍</div>
            <h3>1. The Root (D1)</h3>
            <p>We analyze your <strong>Physical Birth Chart (D1)</strong> to identify the initial karmic "promise" of your life.</p>
          </div>

          <div className="logic-connector">→</div>

          <div className="logic-card">
            <div className="logic-icon-wrapper">🎯</div>
            <h3>2. The Fruit (D9)</h3>
            <p>We verify that promise against your <strong>Navamsa (D9)</strong>. If the "Fruit" is strong, the "Root" will manifest success.</p>
          </div>

          <div className="logic-connector">→</div>

          <div className="logic-card">
            <div className="logic-icon-wrapper">📊</div>
            <h3>3. The Trigger</h3>
            <p>Using <strong>Real-Time Transits</strong>, we pin-point the exact month when your 84+ calculators align for a "Life Pivot."</p>
          </div>
        </div>

        <div className="trust-disclaimer">
          <p>
            <strong>Our Ethical Guarantee:</strong> AstroRoshni does not predict death dates. 
            Instead, we use <strong>Sniper Points & Mrityu Bhaga</strong> logic to highlight periods of 
            vulnerability, allowing for proactive remedies and care.
          </p>
        </div>
      </div>
    </section>
  );
};

export default TrustBanner;