import React from 'react';
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import SEOHead from '../SEO/SEOHead';
import ClassicalLifeReading from './ClassicalLifeReading';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import './ClassicalLifePage.css';

export default function ClassicalLifePage({ user, onLogin, onLogout, onAdminClick }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { birthData, chartData } = useAstrology();
  const { features, loading } = useCredits();
  const enabled = Boolean(features?.classical_life_tab_enabled);

  if (!loading && !enabled) return <Navigate to="/charts-dashas" replace />;

  return (
    <div className="classical-life-page">
      <SEOHead title="Classical Life Reading | AstroRoshni" description="A source-traceable natal life reading organised by house and life area." canonicalPath="/life-reading" noindex />
      <ModernNavigationHeader user={user} onLogin={onLogin} onLogout={onLogout} onAdminClick={onAdminClick} />
      <header className="classical-life-page__hero">
        <button type="button" onClick={() => navigate('/charts-dashas')}>← Chart workspace</button>
        <div><span>Life · Classical natal promise</span><h1>Your life,<br /><em>area by area.</em></h1><p>Read what the birth chart promises before timing is added. Every conclusion remains connected to its rule, chart evidence and source.</p></div>
        <aside><small>Reading for</small><strong>{birthData?.name || 'No chart selected'}</strong><button type="button" onClick={() => navigate('/charts-dashas')}>{birthData ? 'Change in chart workspace' : 'Select a chart'}</button></aside>
      </header>
      <main className="classical-life-page__content">
        {!user ? <div className="classical-life-page__gate"><h2>Sign in to read your chart</h2><p>The Life reading uses the selected saved birth chart.</p><button type="button" onClick={onLogin}>Sign in</button></div> : <ClassicalLifeReading birthData={birthData} chartData={chartData} variant="page" initialAreaKey={searchParams.get('area') || ''} />}
      </main>
    </div>
  );
}
