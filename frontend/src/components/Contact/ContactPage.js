import React from 'react';
import NavigationHeader from '../Shared/NavigationHeader';
import ContactSupportForm from './ContactSupportForm';
import './ContactPage.css';

const ContactPage = () => {
  return (
    <div className="contact-page">
      <NavigationHeader />
      <div className="contact-page-shell">
        <div className="contact-page-card">
          <div className="contact-page-hero">
            <div className="contact-page-hero-icon" aria-hidden="true">
              ✨
            </div>
            <h1>Contact AstroRoshni</h1>
            <p>Connect with us for your cosmic journey</p>
          </div>

          <div className="contact-page-grid">
            <div className="contact-page-tile">
              <div className="contact-page-tile-icon" aria-hidden="true">
                📧
              </div>
              <h3 style={{ color: '#e91e63' }}>Email Support</h3>
              <p>Get help with your account, billing, or technical issues</p>
              <a href="mailto:help@astroroshni.com" className="contact-page-email-btn">
                help@astroroshni.com
              </a>
            </div>

            <div className="contact-page-tile">
              <div className="contact-page-tile-icon" aria-hidden="true">
                💼
              </div>
              <h3 style={{ color: '#9c27b0' }}>Business Inquiries</h3>
              <p>Partnerships, collaborations, and business opportunities</p>
              <div className="contact-page-badge">Coming Soon</div>
            </div>
          </div>

          <ContactSupportForm />

          <div className="contact-page-social">
            <h3>🌟 Follow Our Cosmic Journey</h3>
            <div className="contact-page-social-links">
              <a href="https://x.com/astroroshni" target="_blank" rel="noopener noreferrer">
                🐦 Twitter
              </a>
              <a href="https://instagram.com/astroroshniai" target="_blank" rel="noopener noreferrer">
                📷 Instagram
              </a>
              <a href="https://facebook.com/astroroshniai" target="_blank" rel="noopener noreferrer">
                📘 Facebook
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactPage;
