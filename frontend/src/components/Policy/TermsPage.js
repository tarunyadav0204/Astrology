import React from 'react';
import { Link } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import './TermsPage.css';

const TERMS_NAV = [
  ['definitions', 'Important definitions'],
  ['eligibility', 'Eligibility'],
  ['account', 'Account security'],
  ['ai-content', 'AI content'],
  ['payments', 'Payments & refunds'],
  ['conduct', 'User conduct'],
  ['warranties', 'Warranties'],
  ['liability', 'Liability'],
  ['intellectual-property', 'Intellectual property'],
  ['privacy', 'Privacy & DPDP'],
  ['indemnification', 'Indemnification'],
  ['governing-law', 'Governing law'],
  ['support', 'Contact & support'],
];

const TermsPage = ({ user, onLogout, onLogin, onAdminClick }) => {
  return (
    <div className="terms-page">
      <ModernNavigationHeader
        sticky
        user={user}
        onLogout={onLogout}
        onLogin={onLogin}
        onAdminClick={onAdminClick}
      />

      <main className="terms-main">
        <header className="terms-hero">
          <p className="terms-eyebrow">Legal · AstroRoshni</p>
          <div className="terms-hero__body">
            <div>
              <h1>Terms &amp;<br /><em>conditions.</em></h1>
              <p>
                The rules that govern access to AstroRoshni’s website, mobile applications,
                AI-generated guidance, reports, wallet, and associated services.
              </p>
            </div>
            <dl className="terms-hero__meta">
              <div><dt>Last updated</dt><dd>June 7, 2026</dd></div>
              <div><dt>Operated by</dt><dd>Apeiron Logic LLP</dd></div>
              <div><dt>Jurisdiction</dt><dd>India</dd></div>
            </dl>
          </div>
        </header>

        <div className="terms-layout">
          <aside className="terms-index" aria-label="Terms contents">
            <p>On this page</p>
            <nav>
              {TERMS_NAV.map(([id, label], index) => (
                <a key={id} href={`#${id}`}>
                  <span>{String(index + 1).padStart(2, '0')}</span>{label}
                </a>
              ))}
            </nav>
          </aside>

          <article className="terms-document">
            <section className="terms-introduction" aria-labelledby="terms-introduction-title">
              <p className="terms-section-label">Agreement</p>
              <h2 id="terms-introduction-title">Before you use AstroRoshni</h2>
              <p>
                Welcome to <strong>AstroRoshni</strong>. These Terms and Conditions
                (&quot;Terms&quot;, &quot;Agreement&quot;) govern your access to and use of the
                AstroRoshni website, mobile applications, and all associated services
                (collectively referred to as the &quot;Platform&quot;). The Platform is owned and
                operated by <strong>Apeiron Logic LLP</strong> (&quot;Company&quot;).
              </p>
              <p>
                By accessing, browsing, downloading, or using the Platform, you
                (&quot;User&quot;, &quot;Member&quot;, &quot;Customer&quot;) agree to be bound by these Terms.
                If you do not agree with any part of these Terms, you must immediately cease
                using the Platform.
              </p>
            </section>

            <section id="definitions">
              <p className="terms-section-label">01</p>
              <h2>Important definitions</h2>
              <ul>
                <li><strong>&quot;AstroRoshni&quot; / &quot;We&quot; / &quot;Us&quot; / &quot;Our&quot;:</strong> Refers to Apeiron Logic LLP, the AstroRoshni platform, its artificial intelligence (AI) architecture, owners, directors, and employees.</li>
                <li><strong>&quot;User&quot; / &quot;You&quot;:</strong> Any person who accesses the Platform.</li>
                <li><strong>&quot;Services&quot;:</strong> The AI-generated astrological content, reports, data, and interactive AI sessions provided on the Platform.</li>
              </ul>
            </section>

            <section id="eligibility">
              <p className="terms-section-label">02</p>
              <h2>Eligibility</h2>
              <p>By using the Platform, you represent and warrant that you are at least 18 years of age and legally competent to form a binding contract under the Indian Contract Act, 1872.</p>
            </section>

            <section id="account">
              <p className="terms-section-label">03</p>
              <h2>Account registration and security</h2>
              <ul>
                <li><strong>Accurate Information:</strong> You agree to provide accurate, current, and complete birth data to ensure precise AI analysis.</li>
                <li><strong>Account Security:</strong> You are solely responsible for maintaining the confidentiality of your account credentials.</li>
              </ul>
            </section>

            <section id="ai-content" className="terms-section--emphasis">
              <p className="terms-section-label">04</p>
              <h2>Description of services &amp; “AI Content” acknowledgement</h2>
              <ul>
                <li><strong>Purely AI Platform:</strong> AstroRoshni provides high-precision astrological calculations and analysis exclusively through artificial intelligence. <strong>AstroRoshni is purely an AI platform with no human astrologers on board and does not operate as an astrologer marketplace.</strong></li>
                <li><strong>Nature of AI &amp; Astrology:</strong> While our platform utilizes advanced computational algorithms to ensure the mathematical precision of astrological charts, astrology itself does not possess standardized scientific consensus. Therefore, the interpretive reports and AI interactions are provided strictly for entertainment, personal reflection, and spiritual guidance.</li>
                <li><strong>Automated Generation:</strong> Because the content is dynamically generated by AI, AstroRoshni does not guarantee that the text will be entirely free of algorithmic anomalies or &quot;hallucinations.&quot;</li>
              </ul>
            </section>

            <section id="payments">
              <p className="terms-section-label">05</p>
              <h2>Payments, wallet, and fair refund policy</h2>
              <p>All Paid Services on AstroRoshni operate on a prepaid &quot;Wallet&quot; or pay-per-report model.</p>
              <ul>
                <li><strong>Wallet Recharges:</strong> Wallet balances are non-transferable and cannot be withdrawn to bank accounts.</li>
                <li><strong>General Refund Policy:</strong> Due to the digital nature of the service, once an AI interaction is completed or a report is successfully delivered based on the data you provided, refunds will not be issued based on disagreement with the astrological interpretation.</li>
                <li>
                  <strong>Deficiency in Service (Exceptions for Refund):</strong> A refund or wallet credit <em>will</em> be provided if you experience a technical deficiency, including:
                  <ul>
                    <li>System crashes or network failures that deduct wallet balance without delivering the service.</li>
                    <li>The AI generates heavily corrupted, garbled, or entirely irrelevant text (algorithmic failure).</li>
                  </ul>
                </li>
                <li>To claim a refund under these conditions, you must open a ticket in the Support Section or write to <a href="mailto:help@astroroshni.com">help@astroroshni.com</a> within 48 hours of the incident.</li>
              </ul>
            </section>

            <section id="conduct">
              <p className="terms-section-label">06</p>
              <h2>User conduct and AI guardrails</h2>
              <p>The AstroRoshni AI is strictly programmed with safety guardrails to refuse certain topics. You agree <strong>NOT</strong> to:</p>
              <ul>
                <li>Attempt to reverse-engineer, &quot;jailbreak,&quot; or manipulate the AI prompts to bypass safety protocols.</li>
                <li>Use the Platform to seek medical diagnoses, financial investment advice, or legal counsel.</li>
                <li>Ask questions relating to the gender determination of a fetus, which is strictly prohibited under the Pre-Conception and Pre-Natal Diagnostic Techniques (PCPNDT) Act, 1994.</li>
              </ul>
              <p>If a User intentionally manipulates the AI to produce prohibited content, the User bears sole legal responsibility for that output, and their account will be terminated.</p>
            </section>

            <section id="warranties" className="terms-section--warning">
              <p className="terms-section-label">07</p>
              <h2>Strict disclaimer of warranties</h2>
              <ul>
                <li><strong>Specialist advice is strongly advocated</strong> for all questions asked on the AstroRoshni platform. The AI-generated astrological advice or insights are <strong>not</strong> a substitute for professional, legal, financial, medical, or psychological advice.</li>
                <li><strong>Medical &amp; Mental Health:</strong> If you are facing severe mental distress, depression, or suicidal thoughts, please consult a qualified medical professional or a suicide prevention helpline immediately. Do not rely on AI-generated predictions for mental health crises.</li>
              </ul>
            </section>

            <section id="liability">
              <p className="terms-section-label">08</p>
              <h2>Limitation of liability and financial cap</h2>
              <p>To the maximum extent permitted by applicable Indian law, Apeiron Logic LLP shall not be liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of profits, revenues, data, or emotional distress resulting from your reliance on the AI Services.</p>
              <ul>
                <li><strong>Strict Liability Cap:</strong> In no event shall the total, aggregate liability of AstroRoshni and Apeiron Logic LLP for any claim arising out of or relating to these Terms or the Services exceed the actual INR amount paid by the User for the specific report or interactive session giving rise to the dispute.</li>
              </ul>
            </section>

            <section id="intellectual-property">
              <p className="terms-section-label">09</p>
              <h2>Intellectual property rights</h2>
              <p>All content on the Platform, including AI models, algorithms, codebase, graphics, and generated reports, is the exclusive property of Apeiron Logic LLP and is protected by copyright and trademark laws.</p>
            </section>

            <section id="privacy">
              <p className="terms-section-label">10</p>
              <h2>Privacy policy and DPDP compliance</h2>
              <p>Your use of the Platform involves the processing of personal and astrological data. By accepting these Terms, you explicitly consent to our data processing practices as outlined in our <Link to="/policy">Privacy Policy</Link>, which is compliant with the Digital Personal Data Protection (DPDP) Act, 2023.</p>
            </section>

            <section id="indemnification">
              <p className="terms-section-label">11</p>
              <h2>Indemnification</h2>
              <p>You agree to indemnify and hold harmless Apeiron Logic LLP, its directors, and employees from any claims, damages, or legal expenses arising out of your violation of these Terms, particularly regarding the intentional misuse of the AI to generate prohibited content.</p>
            </section>

            <section id="governing-law">
              <p className="terms-section-label">12</p>
              <h2>Governing law and dispute resolution</h2>
              <ul>
                <li><strong>Jurisdiction:</strong> These Terms shall be governed by the laws of India.</li>
                <li><strong>Dispute Resolution:</strong> Any disputes arising out of these Terms shall be subject to the exclusive jurisdiction of the courts located in New Delhi, India.</li>
              </ul>
            </section>

            <section id="support">
              <p className="terms-section-label">13</p>
              <h2>Contact and support</h2>
              <p>For any questions, grievances, technical issues, or support:</p>
              <ul>
                <li><strong>Support Tickets:</strong> Support can be obtained by opening a ticket in the Support Section of the platform.</li>
                <li><strong>Email:</strong> You may also write to us at <a href="mailto:help@astroroshni.com">help@astroroshni.com</a>.</li>
                <li><strong>Entity:</strong> Apeiron Logic LLP</li>
                <li><strong>Address:</strong> S1-41, Vatika Signature Vill, Narsinghpur, Kherki Daula Police Station, Narsinghpur, Gurgaon- 122004, Haryana, India</li>
              </ul>
            </section>

            <footer className="terms-document__footer">
              <span>Related document</span>
              <Link to="/policy">Read the Privacy Policy <b aria-hidden>↗</b></Link>
              <Link to="/contact">Contact AstroRoshni <b aria-hidden>↗</b></Link>
            </footer>
          </article>
        </div>
      </main>
    </div>
  );
};

export default TermsPage;
