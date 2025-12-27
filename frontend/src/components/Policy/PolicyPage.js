import React from 'react';
import NavigationHeader from '../Shared/NavigationHeader';

const PolicyPage = () => {
  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 50%, #dee2e6 100%)',
      fontFamily: 'Arial, sans-serif'
    }}>
      <NavigationHeader />
      <div style={{ padding: '220px 20px 60px 20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ color: '#e91e63', marginBottom: '30px' }}>Privacy Policy & Terms</h1>
      
      <section style={{ marginBottom: '30px' }}>
        <h2>Privacy Policy</h2>
        <div style={{ background: '#e8f5e8', padding: '15px', borderRadius: '8px', marginBottom: '20px', border: '2px solid #4caf50' }}>
          <h3 style={{ color: '#2e7d32', margin: '0 0 10px 0' }}>🔒 End-to-End Encryption</h3>
          <p style={{ margin: '0', fontWeight: 'bold', color: '#2e7d32' }}>ALL data we collect is protected with end-to-end encryption. Your personal information, birth details, and chat messages are encrypted and secure.</p>
        </div>
        <p>We collect birth details for astrological calculations and protect your personal information with appropriate security measures.</p>
        
        <h3>Information We Collect</h3>
        <ul>
          <li>Birth details (date, time, place)</li>
          <li>Contact information (name, email)</li>
          <li>Chat messages and consultation history</li>
        </ul>
        
        <h3>AI Processing Disclosure</h3>
        <div style={{ background: '#fff3e0', padding: '15px', borderRadius: '8px', marginBottom: '20px', border: '2px solid #ff9800' }}>
          <p style={{ margin: '0', fontWeight: 'bold', color: '#e65100' }}>🤖 We use advanced Artificial Intelligence (AI) models to analyze your astrological data. While your data is encrypted, it is processed through secure API channels to generate insights. No personal identifiers (like your name) are shared with the AI models.</p>
        </div>
        
        <h3>How We Use Information</h3>
        <ul>
          <li>Provide astrological services</li>
          <li>Generate personalized reports</li>
          <li>Improve user experience</li>
        </ul>
        
        <h3>Data Deletion & Right to be Forgotten</h3>
        <p>Users have the right to request the total deletion of their birth profile, chat history, and account data at any time via the settings menu or by contacting support.</p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2>Terms of Service</h2>
        <p>AstroRoshni provides astrological services for entertainment and guidance purposes.</p>
        
        <h3>Age Restriction</h3>
        <p><strong>Users must be 18 years of age or older to use the consultation and chat services.</strong></p>
        
        <h3>User Responsibilities</h3>
        <ul>
          <li>Provide accurate information</li>
          <li>Use services lawfully</li>
          <li>Respect intellectual property</li>
        </ul>
        
        <h3>Fate vs. Freewill Clause</h3>
        <div style={{ background: '#f3e5f5', padding: '15px', borderRadius: '8px', marginBottom: '20px', border: '2px solid #9c27b0' }}>
          <p style={{ margin: '0', fontWeight: 'bold', color: '#6a1b9a' }}>⚖️ Astrology provides indicators of cosmic energy, not deterministic outcomes. Users retain absolute freewill. AstroRoshni is not responsible for any actions taken or not taken by the user based on the information provided.</p>
        </div>
        
        <h3>Ethical Boundaries & Prohibited Topics</h3>
        <p>Our services strictly prohibit and will not provide predictions related to:</p>
        <ul>
          <li>Determining the exact time or date of death</li>
          <li>Specific medical diagnoses or treatment outcomes</li>
          <li>Illegal activities or gambling advice</li>
          <li>Paternity or sensitive family disputes</li>
        </ul>
        
        <h3>Disclaimer</h3>
        <p>Services are for entertainment purposes. Not professional advice for medical, legal, financial, or mental health decisions. In case of emergency, contact appropriate emergency services.</p>
      </section>

      <section>
        <h2>Contact</h2>
        <p>Email: help@astroroshni.com</p>
      </section>
      </div>
    </div>
  );
};

export default PolicyPage;