import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import ConsultationHistory from './ConsultationHistory';
import CreditLedger from './CreditLedger';
import './ProfilePage.css';

const ProfilePage = ({ user, onLogout, onAdminClick }) => {
  const navigate = useNavigate();
  const { birthData } = useAstrology();
  const { credits, loading: creditsLoading } = useCredits();
  const [activeTab, setActiveTab] = useState('consultations');

  const accountName = user?.name || birthData?.name || user?.email || user?.phone || 'AstroRoshni member';
  const accountContact = user?.email || user?.phone || 'Signed-in account';
  const initial = accountName.trim().charAt(0).toUpperCase() || 'A';
  const chartDate = birthData?.date ? new Date(`${String(birthData.date).split('T')[0]}T00:00:00`).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric'
  }) : null;

  return (
    <div className="profile-page">
      <ModernNavigationHeader
        sticky
        user={user}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
      />

      <main className="profile-main">
        <section className="profile-hero" aria-labelledby="profile-title">
          <div className="profile-hero__identity">
            <span className="profile-eyebrow">Your AstroRoshni</span>
            <div className="profile-hero__name-row">
              <div className="profile-avatar" aria-hidden>{initial}</div>
              <div>
                <h1 id="profile-title">{accountName}</h1>
                <p>{accountContact}</p>
              </div>
            </div>
          </div>

          <div className="profile-hero__balance">
            <span>Available balance</span>
            <strong>{creditsLoading ? '—' : credits}</strong>
            <small>AstroRoshni credits</small>
            <button type="button" onClick={() => navigate('/subscription')}>Credits & membership <span aria-hidden>↗</span></button>
          </div>
        </section>

        <section className="profile-overview" aria-label="Account overview">
          <article className="profile-chart-card">
            <div className="profile-card-heading">
              <span>Current Kundli</span>
              <strong>{birthData ? 'Active' : 'Not selected'}</strong>
            </div>
            {birthData ? (
              <>
                <h2>{birthData.name || 'Selected birth chart'}</h2>
                <p>{[chartDate, birthData.time, birthData.place].filter(Boolean).join(' · ')}</p>
                <div className="profile-card-actions">
                  <button type="button" onClick={() => navigate('/charts-dashas')}>Open chart</button>
                  <button type="button" onClick={() => navigate('/chat?app=1')}>Ask Tara</button>
                </div>
              </>
            ) : (
              <>
                <h2>Begin with your birth chart.</h2>
                <p>Add accurate date, time and place once to personalize every reading.</p>
                <div className="profile-card-actions">
                  <button type="button" onClick={() => navigate('/ai-kundli-generator')}>Create Kundli</button>
                </div>
              </>
            )}
          </article>

          <nav className="profile-quick-links" aria-label="Profile shortcuts">
            <button type="button" onClick={() => navigate('/chat?app=1')}>
              <span><small>Consultation</small><strong>Ask Tara</strong></span><i aria-hidden>↗</i>
            </button>
            <button type="button" onClick={() => navigate('/subscription')}>
              <span><small>Plan and balance</small><strong>Membership</strong></span><i aria-hidden>↗</i>
            </button>
            <button type="button" onClick={() => navigate('/order-management')}>
              <span><small>Purchases</small><strong>Orders & billing</strong></span><i aria-hidden>↗</i>
            </button>
          </nav>
        </section>

        <section className="profile-records" aria-labelledby="profile-records-title">
          <header className="profile-records__header">
            <div>
              <span className="profile-eyebrow">Your records</span>
              <h2 id="profile-records-title">A private archive of your journey.</h2>
            </div>
            <div className="profile-tabs" role="tablist" aria-label="Profile records">
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'consultations'}
                className={activeTab === 'consultations' ? 'active' : ''}
                onClick={() => setActiveTab('consultations')}
              >Consultations</button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'credits'}
                className={activeTab === 'credits' ? 'active' : ''}
                onClick={() => setActiveTab('credits')}
              >Credit ledger</button>
            </div>
          </header>

          <div className="profile-tab-content" role="tabpanel">
            {activeTab === 'consultations' && (
              <ConsultationHistory user={user} onStartConsultation={() => navigate('/chat?app=1')} />
            )}
            {activeTab === 'credits' && <CreditLedger user={user} />}
          </div>
        </section>

        <footer className="profile-account-footer">
          <div><span>Account</span><p>Manage billing or permanently remove your AstroRoshni data.</p></div>
          <div>
            <button type="button" onClick={() => navigate('/order-management')}>Billing history</button>
            <button type="button" className="profile-account-footer__danger" onClick={() => navigate('/account/delete')}>Delete account</button>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default ProfilePage;
