import React from 'react';
import { Link } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import ContactSupportForm from './ContactSupportForm';
import './ContactPage.css';

const ContactPage = ({ user, onLogout, onLogin, onAdminClick }) => {
  return (
    <div className="contact-page">
      <ModernNavigationHeader sticky user={user} onLogout={onLogout} onLogin={onLogin} onAdminClick={onAdminClick} />
      <div className="contact-page-shell">
        <div className="contact-page-card">
          <div className="contact-page-hero">
            <p className="contact-page-eyebrow">Contact & support</p>
            <h1>We’re here when<br /><em>you need clarity.</em></h1>
            <p>Choose the quickest route for account help, billing questions, or business enquiries.</p>
          </div>

          <div className="contact-page-grid">
            <div className="contact-page-tile">
              <div className="contact-page-tile-icon" aria-hidden="true">01</div>
              <h3>Email support</h3>
              <p>Get help with your account, billing, or technical issues</p>
              <a href="mailto:help@astroroshni.com" className="contact-page-email-btn">
                help@astroroshni.com
              </a>
            </div>

            <div className="contact-page-tile">
              <div className="contact-page-tile-icon" aria-hidden="true">02</div>
              <h3>Orders & billing</h3>
              <p>View purchases, payment references, refund requests, and billing support tickets</p>
              <Link to="/order-management" className="contact-page-order-btn">
                Manage orders
              </Link>
            </div>

            <div className="contact-page-tile">
              <div className="contact-page-tile-icon" aria-hidden="true">03</div>
              <h3>Business inquiries</h3>
              <p>Partnerships, collaborations, and business opportunities</p>
              <div className="contact-page-badge">Coming Soon</div>
            </div>
          </div>

          <ContactSupportForm />

          <div className="contact-page-social">
            <h3>Follow AstroRoshni</h3>
            <div className="contact-page-social-links">
              <a href="https://x.com/astroroshni" target="_blank" rel="noopener noreferrer">
                X / Twitter
              </a>
              <a href="https://instagram.com/astroroshniai" target="_blank" rel="noopener noreferrer">
                Instagram
              </a>
              <a href="https://www.facebook.com/AstroRoshni/" target="_blank" rel="noopener noreferrer">
                Facebook
              </a>
              <a href="https://www.linkedin.com/company/astroroshni" target="_blank" rel="noopener noreferrer">
                LinkedIn
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactPage;
