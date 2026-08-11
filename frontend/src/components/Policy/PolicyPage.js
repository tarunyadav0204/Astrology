import React from 'react';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import './TermsPage.css';
import './PolicyPage.css';

const POLICY_NAV = [
  ['introduction', 'Introduction'],
  ['processing', 'Data & AI processing'],
  ['controller', 'Data controller'],
  ['collection', 'Information collected'],
  ['use', 'How data is used'],
  ['security', 'Security'],
  ['ai-processing', 'AI processing'],
  ['sharing', 'Data sharing'],
  ['rights', 'Your rights'],
  ['children', 'Children’s privacy'],
  ['third-party-links', 'Third-party links'],
  ['changes', 'Policy changes'],
  ['disclaimer', 'Disclaimer'],
  ['contact', 'Contact'],
];

const PolicyPage = ({ user, onLogout, onLogin, onAdminClick }) => {
  return (
    <div className="terms-page policy-page">
      <ModernNavigationHeader
        sticky
        user={user}
        onLogout={onLogout}
        onLogin={onLogin}
        onAdminClick={onAdminClick}
      />

      <main className="terms-main">
        <header className="terms-hero policy-hero">
          <p className="terms-eyebrow">Privacy · AstroRoshni</p>
          <div className="terms-hero__body">
            <div>
              <h1>Privacy,<br /><em>plainly stated.</em></h1>
              <p>
                How AstroRoshni collects, processes, protects, and deletes personal and
                astrological data across its website and mobile application.
              </p>
            </div>
            <dl className="terms-hero__meta">
              <div><dt>Last updated</dt><dd>June 7, 2026</dd></div>
              <div><dt>Operated by</dt><dd>Apeiron Logic LLP</dd></div>
              <div><dt>Frameworks</dt><dd>DPDP · GDPR</dd></div>
            </dl>
          </div>
        </header>

        <div className="terms-layout">
          <aside className="terms-index" aria-label="Privacy policy contents">
            <p>On this page</p>
            <nav>
              {POLICY_NAV.map(([id, label], index) => (
                <a key={id} href={`#${id}`}>
                  <span>{String(index + 1).padStart(2, '0')}</span>{label}
                </a>
              ))}
            </nav>
          </aside>

          <article className="terms-document policy-document">
            <section id="introduction" className="terms-introduction">
              <p className="terms-section-label">01</p>
              <h2>Introduction</h2>
              <p>Welcome to AstroRoshni. This Privacy Policy explains how we collect, use, and protect your personal data when you use our mobile application and website (astroroshni.com).</p>
            </section>

            <section id="processing" className="policy-section--processing">
              <p className="terms-section-label">02</p>
              <h2>Data processing and AI integration</h2>
              <p className="policy-section-note">Under the Digital Personal Data Protection Act, 2023</p>
              <p>To provide you with high-precision AI-generated astrological insights, AstroRoshni (operated by <strong>Apeiron Logic LLP</strong>) collects specific personal data, including your Name, Date of Birth, Time of Birth, and Place of Birth (collectively, &quot;Astrological Data&quot;).</p>
              <p><strong>By using our Services, you provide explicit, unconditional consent for the following:</strong></p>
              <ol>
                <li><strong>Automated Processing:</strong> Your Astrological Data will be processed by our proprietary artificial intelligence algorithms to generate personalized reports and interactive responses.</li>
                <li><strong>Third-Party AI Processors:</strong> To deliver our interactive chat and complex analytical features, your Astrological Data may be securely transmitted to and processed by third-party Large Language Model (LLM) providers via API. We do not permit these third-party providers to use your personal data to train their public models.</li>
                <li><strong>Data Minimization:</strong> We only process the exact data required to calculate astrological charts and generate your specific requested report.</li>
                <li><strong>Right to Erasure:</strong> You have the right to withdraw your consent at any time. Upon your request to <a href="mailto:help@astroroshni.com">help@astroroshni.com</a>, we will permanently delete your Astrological Data and user account from our active databases and third-party processing logs, except where retention is required by Indian law.</li>
              </ol>
            </section>

            <section id="controller">
              <p className="terms-section-label">03</p>
              <h2>Data controller</h2>
              <p>For the purposes of the General Data Protection Regulation (GDPR) and the Digital Personal Data Protection Act (DPDP India), the data controller is:</p>
              <p><strong>Aradhana Asnani</strong><br />Email: <a href="mailto:help@astroroshni.com">help@astroroshni.com</a></p>
            </section>

            <section id="collection">
              <p className="terms-section-label">04</p>
              <h2>Information we collect</h2>
              <p>We collect the following data to provide astrological services:</p>
              <ul>
                <li><strong>Personal Identifiers:</strong> Name, Email address, Phone Number.</li>
                <li><strong>Birth Data:</strong> Date of birth, Time of birth, Place of birth (Longitude/Latitude).</li>
                <li><strong>App Activity:</strong> Chat history, consultation logs, horoscopes, Vedic Life Analysis, and preferences.</li>
                <li><strong>Device Info:</strong> IP address, device model, and OS version (for security and crash reporting).</li>
                <li><strong>Cookies &amp; Log Files:</strong> We collect browser type, screen resolution, and time spent on the website to analyze trends and improve our services. We track IP addresses to understand visitor demographics and geographic distribution.</li>
              </ul>
              <p><strong>Note:</strong> You do not have to provide personal information to browse our website. However, certain personalized services require registration.</p>
            </section>

            <section id="use">
              <p className="terms-section-label">05</p>
              <h2>How we use your data</h2>
              <ul>
                <li><strong>Service Functionality:</strong> To calculate birth charts and generate predictions.</li>
                <li><strong>Personalization:</strong> To tailor AI insights to your specific planetary positions.</li>
                <li><strong>Account Management:</strong> To allow you to access your history across devices.</li>
                <li><strong>Analytics &amp; Improvements:</strong> To understand how users interact with our app and to improve performance, reliability, and features.</li>
              </ul>
            </section>

            <section id="security" className="policy-section--secure">
              <p className="terms-section-label">06</p>
              <h2>Security &amp; confidentiality</h2>
              <div className="policy-callout">
                <strong>Encrypted in transit and at rest</strong>
                <p>All data is encrypted in transit (HTTPS/TLS) and encrypted at rest using industry-standard encryption protocols.</p>
                <p>We guarantee confidentiality of your identity, birth details, and predictions. No direct or indirect use will be made of your information except for the explicit purpose of generating and communicating your horoscope charts and predictions back to you.</p>
              </div>
              <p><strong>Payment Security:</strong> We DO NOT collect or store payment information on our servers. All payments are processed securely by third-party payment gateways (Stripe, PayPal, etc.) that comply with PCI-DSS standards.</p>
            </section>

            <section id="ai-processing" className="policy-section--ai">
              <p className="terms-section-label">07</p>
              <h2>AI processing</h2>
              <div className="policy-callout">
                <strong>Only the context needed for analysis</strong>
                <p>We use the Google Gemini API for astrological analysis. We do not intentionally send personally identifiable information (such as your name or email) to the AI provider. We primarily send birth coordinates and chat queries needed for astrological analysis, which may be processed on servers outside your country in accordance with the provider&apos;s privacy and data handling practices.</p>
              </div>
            </section>

            <section id="sharing">
              <p className="terms-section-label">08</p>
              <h2>Data sharing</h2>
              <p><strong>We do not sell or rent your data.</strong> Data is only shared with:</p>
              <ul>
                <li><strong>Service Providers:</strong> Google Cloud/Firebase (Hosting) and Google Gemini (AI processing) under strict confidentiality.</li>
                <li><strong>Legal Necessity:</strong> Only if required by Indian Law.</li>
              </ul>
            </section>

            <section id="rights" className="policy-section--rights">
              <p className="terms-section-label">09</p>
              <h2>Your rights &amp; data deletion</h2>
              <p>You have the <strong>&quot;Right to be Forgotten&quot;</strong> and the following rights:</p>
              <ul>
                <li><strong>Access &amp; Modify:</strong> You can access and update your profile information at any time through your account settings.</li>
                <li><strong>Delete Account In-App:</strong> You can permanently delete your account and associated data directly from the AstroRoshni mobile app by going to <strong>Profile &gt; Delete Account &amp; Data</strong>.</li>
                <li><strong>Delete Account via Email:</strong> You can also request deletion by emailing <a href="mailto:help@astroroshni.com">help@astroroshni.com</a> with the subject line <em>&quot;Delete my AstroRoshni account&quot;</em>. We will process verified deletion requests within 72 hours.</li>
              </ul>
            </section>

            <section id="children">
              <p className="terms-section-label">10</p>
              <h2>Children&apos;s privacy</h2>
              <p><strong>AstroRoshni is not intended for users under 18 years of age.</strong> We do not knowingly collect data from minors.</p>
            </section>

            <section id="third-party-links">
              <p className="terms-section-label">11</p>
              <h2>Third-party links</h2>
              <p>Our website and app may contain links to other websites. AstroRoshni is not responsible for the privacy practices of such external sites. We encourage you to read their privacy policies.</p>
            </section>

            <section id="changes">
              <p className="terms-section-label">12</p>
              <h2>Changes to this privacy policy</h2>
              <p>We may update this Privacy Policy from time to time. Any changes will be posted on this page with an updated &quot;Last Updated&quot; date. Your continued use of our services after changes constitutes acceptance of the updated policy.</p>
            </section>

            <section id="disclaimer" className="terms-section--warning">
              <p className="terms-section-label">13</p>
              <h2>Disclaimer</h2>
              <p><strong>Astrology is for guidance and entertainment.</strong> We do not provide medical, legal, or financial advice.</p>
            </section>

            <section id="contact">
              <p className="terms-section-label">Contact</p>
              <h2>Privacy questions</h2>
              <p>Email: <a href="mailto:help@astroroshni.com">help@astroroshni.com</a></p>
            </section>

            <footer className="terms-document__footer">
              <span>Related documents</span>
              <a href="/terms">Read the Terms &amp; Conditions <b aria-hidden>↗</b></a>
              <a href="/account/delete">Delete your account <b aria-hidden>↗</b></a>
            </footer>
          </article>
        </div>
      </main>
    </div>
  );
};

export default PolicyPage;
