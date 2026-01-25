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
      <h1 style={{ color: '#e91e63', marginBottom: '10px' }}>AstroRoshni Privacy Policy</h1>
      <p style={{ color: '#666', marginBottom: '30px' }}>Last Updated: January 24, 2026</p>
      
      <section style={{ marginBottom: '30px' }}>
        <h2>1. Introduction</h2>
        <p>Welcome to AstroRoshni. This Privacy Policy explains how we collect, use, and protect your personal data when you use our mobile application and website (astroroshni.com).</p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2>2. Data Controller</h2>
        <p>For the purposes of the General Data Protection Regulation (GDPR) and the Digital Personal Data Protection Act (DPDP India), the data controller is:</p>
        <p><strong>Amber Yadav</strong><br />Email: help@astroroshni.com</p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2>3. Information We Collect</h2>
        <p>We collect the following data to provide astrological services:</p>
        <ul>
          <li><strong>Personal Identifiers:</strong> Name, Email address, Phone Number.</li>
          <li><strong>Birth Data:</strong> Date of birth, Time of birth, Place of birth (Longitude/Latitude).</li>
          <li><strong>App Activity:</strong> Chat history, consultation logs, horoscopes, Vedic Life Analysis, and preferences.</li>
          <li><strong>Device Info:</strong> IP address, device model, and OS version (for security and crash reporting).</li>
          <li><strong>Cookies & Log Files:</strong> We collect browser type, screen resolution, and time spent on the website to analyze trends and improve our services. We track IP addresses to understand visitor demographics and geographic distribution.</li>
        </ul>
        <p><strong>Note:</strong> You do not have to provide personal information to browse our website. However, certain personalized services require registration.</p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2>4. How We Use Your Data</h2>
        <ul>
          <li><strong>Service Functionality:</strong> To calculate birth charts and generate predictions.</li>
          <li><strong>Personalization:</strong> To tailor AI insights to your specific planetary positions.</li>
          <li><strong>Account Management:</strong> To allow you to access your history across devices.</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2>5. Security & Confidentiality</h2>
        <div style={{ background: '#e8f5e8', padding: '15px', borderRadius: '8px', marginBottom: '15px', border: '2px solid #4caf50' }}>
          <p style={{ margin: '0 0 10px 0', fontWeight: 'bold', color: '#2e7d32' }}>🔒 All data is kept <strong>End-to-End Encrypted</strong>. Data is <strong>Encrypted in Transit</strong> (HTTPS/TLS) and <strong>Encrypted at Rest</strong> using industry-standard encryption protocols.</p>
          <p style={{ margin: '0', color: '#2e7d32' }}>We guarantee confidentiality of your identity, birth details, and predictions. No direct or indirect use will be made of your information except for the explicit purpose of generating and communicating your horoscope charts and predictions back to you.</p>
        </div>
        <p><strong>Payment Security:</strong> We DO NOT collect or store payment information on our servers. All payments are processed securely by third-party payment gateways (Stripe, PayPal, etc.) that comply with PCI-DSS standards.</p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2>6. AI Processing</h2>
        <div style={{ background: '#fff3e0', padding: '15px', borderRadius: '8px', border: '2px solid #ff9800' }}>
          <p style={{ margin: '0', fontWeight: 'bold', color: '#e65100' }}>🤖 We use Google Gemini API for astrological analysis. No personally identifiable information (Name/Email) is sent to the AI. Only birth coordinates and chat queries are processed.</p>
        </div>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2>7. Data Sharing</h2>
        <p><strong>We do not sell or rent your data.</strong> Data is only shared with:</p>
        <ul>
          <li><strong>Service Providers:</strong> Google Cloud/Firebase (Hosting) and Google Gemini (AI processing) under strict confidentiality.</li>
          <li><strong>Legal Necessity:</strong> Only if required by Indian Law.</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2>8. Your Rights & Data Deletion</h2>
        <p>You have the <strong>"Right to be Forgotten"</strong> and the following rights:</p>
        <ul>
          <li><strong>Access & Modify:</strong> You can access and update your profile information at any time through your account settings.</li>
          <li><strong>Delete Account:</strong> Request total deletion of your data via <strong>App Settings &gt; Delete Account</strong> or by emailing help@astroroshni.com. We will process deletions within 72 hours.</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2>9. Children's Privacy</h2>
        <p><strong>AstroRoshni is not intended for users under 18 years of age.</strong> We do not knowingly collect data from minors.</p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2>10. Third-Party Links</h2>
        <p>Our website and app may contain links to other websites. AstroRoshni is not responsible for the privacy practices of such external sites. We encourage you to read their privacy policies.</p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2>11. Changes to Privacy Policy</h2>
        <p>We may update this Privacy Policy from time to time. Any changes will be posted on this page with an updated "Last Updated" date. Your continued use of our services after changes constitutes acceptance of the updated policy.</p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2>12. Disclaimer</h2>
        <div style={{ background: '#f3e5f5', padding: '15px', borderRadius: '8px', border: '2px solid #9c27b0' }}>
          <p style={{ margin: '0', fontWeight: 'bold', color: '#6a1b9a' }}>⚖️ Astrology is for guidance and entertainment. We do not provide medical, legal, or financial advice.</p>
        </div>
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