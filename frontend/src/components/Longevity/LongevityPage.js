import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BirthFormModal from '../BirthForm/BirthFormModal';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import SEOHead from '../SEO/SEOHead';
import { useAstrology } from '../../context/AstrologyContext';
import { longevityService } from '../../services/longevityService';
import './LongevityPage.css';

const TABS = [
  ['pillars', 'Pillars & Safeguards'],
  ['dossier', 'Maraka & Badhaka'],
  ['timeline', 'Crisis Time-Windows'],
];
const SUBJECTS = [['self', 'Native'], ['mother', 'Mother'], ['father', 'Father']];

const prettyDate = (value) => new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
  month: 'short', year: 'numeric',
});

function ScoreRing({ score = 0, level = 'low' }) {
  return (
    <div className={`longevity-score-ring longevity-score-ring--${level}`} style={{ '--score': score }}>
      <strong>{score}</strong><span>/ 100</span>
    </div>
  );
}

function Pillars({ items, safeguards }) {
  return <div className="longevity-pillars">
    {items.map((item, index) => <article className="longevity-panel" key={item.id}>
      <div className="longevity-panel__number">0{index + 1}</div>
      <div className="longevity-panel__heading"><div><p>{item.title}</p><h3>{item.verdict}</h3></div><span>{item.detail}</span></div>
      {item.pairs && <div className="longevity-pair-grid">
        {item.pairs.map((pair) => <div key={pair.label}>
          <b>{pair.label}</b><span>{pair.left.sign} ({pair.left.nature}) + {pair.right.sign} ({pair.right.nature})</span><em>{pair.verdict}</em>
        </div>)}
      </div>}
      {item.metrics && <div className="longevity-metrics">
        {Object.entries(item.metrics).filter(([, value]) => value !== null && typeof value !== 'object').map(([key, value]) => (
          <div key={key}><span>{key.replaceAll('_', ' ')}</span><b>{String(value)}</b></div>
        ))}
      </div>}
      {item.modifications?.rules?.length > 0 && <div className="longevity-pair-grid">
        {item.modifications.rules.map((rule) => <div key={rule.id}>
          <b>{rule.effect === 'vriddhi' ? 'Kakshya Vriddhi' : 'Kakshya Hrasa'}</b>
          <span>{rule.evidence}</span>
          <span><b>Requirement:</b> {rule.requirement}</span>
          <span>{rule.status_explanation}</span>
          {rule.calculated_effect && <span><b>Calculated effect:</b> {rule.calculated_effect}</span>}
          {rule.final_verdict_effect && <span><b>Final verdict:</b> {rule.final_verdict_effect}</span>}
          <em>{rule.applied ? rule.used_in_final_verdict === false ? 'Classically applied · excluded from final verdict' : 'Applied to final verdict' : rule.exception ? `Not applied · ${rule.exception.replaceAll('_', ' ')}` : 'Not applied'}</em>
        </div>)}
      </div>}
    </article>)}
    {safeguards && <article className="longevity-panel">
      <div className="longevity-panel__number">04</div>
      <div className="longevity-panel__heading"><div><p>Classical source audit</p><h3>{safeguards.title || 'BPHS early-life cancellation audit'}</h3></div><span>{safeguards.summary}</span></div>
      {safeguards.interpretation && <p className="longevity-safeguard-policy">{safeguards.interpretation}</p>}
      <div className="longevity-pair-grid">
        {safeguards.rules.map((rule) => <div key={rule.id}>
          <b>{rule.label || rule.id.replaceAll('_', ' ')}</b>
          <span>{rule.requirement || rule.evidence}</span>
          {rule.condition_checks?.map((check) => <span key={check.label}><b>{check.passed ? 'Passed:' : 'Failed:'}</b> {check.label}. {check.detail}</span>)}
          <em>{rule.status === 'partially_satisfied' ? 'Partially satisfied' : rule.applied ? 'Fully satisfied' : 'Not satisfied'}</em>
        </div>)}
      </div>
      {safeguards.classification_policy && <p className="longevity-safeguard-policy">{safeguards.classification_policy}</p>}
    </article>}
  </div>;
}

function Dossier({ data }) {
  const pointLabels = {
    kharesh_22nd_drekkana: '22nd Drekkana · Kharesh', navamsha_64_moon: '64th Navamsha · Moon',
    navamsha_64_lagna: '64th Navamsha · Lagna', mrityu_pada_a8: 'Mrityu Pada · A8',
    maheshwara: 'Maheshwara Graha', rudra: 'Rudra Graha',
    badhaka: 'Badhaka', parental_eighth: 'Parental 8th', parental_third: 'Parental 3rd',
    derived_maraka_second: 'Derived Maraka · 2nd', derived_maraka_seventh: 'Derived Maraka · 7th',
    parent_karaka: 'Parent Karaka', d12_confirmation: 'D12 Confirmation',
  };
  return <div className="longevity-dossier-grid">
    <section className="longevity-panel longevity-ranking">
      <div className="longevity-section-heading"><div><p>Mrityu Sthana Strength</p><h2>Ranked crisis grahas</h2></div><span>Badhaka house {data.badhaka_house}</span></div>
      {data.ranked_planets.map((planet, index) => <details key={planet.planet} open={index < 3}>
        <summary><span className="longevity-rank">{index + 1}</span><b>{planet.planet}</b><span>{planet.sign} · H{planet.house}</span><strong>{planet.score}</strong></summary>
        <div className="longevity-rank-detail"><p>{planet.longitude}</p><ul>{planet.factors.map((factor) => <li key={factor}>{factor}</li>)}</ul></div>
      </details>)}
    </section>
    <section className="longevity-panel longevity-sensitive">
      <div className="longevity-section-heading"><div><p>Computed coordinates</p><h2>Sensitive points</h2></div></div>
      {Object.entries(data.sensitive_points).filter(([key]) => pointLabels[key]).map(([key, point]) => <div key={key}>
        <span>{pointLabels[key]}</span><b>{point.planet || point.lord} {point.sign ? `· ${point.sign}` : ''}</b><small>{point.derivation || (point.reference_karaka ? `8th from ${point.reference_karaka}` : '')}</small>
      </div>)}
    </section>
  </div>;
}

function Timeline({ windows }) {
  return <section className="longevity-panel longevity-timeline">
    <div className="longevity-section-heading"><div><p>Vimshottari × Shoola × Transit</p><h2>Vulnerability timeline</h2></div><span>Next 12 years</span></div>
    <div className="longevity-timeline__legend"><span className="low">Lower</span><span className="moderate">Moderate</span><span className="critical">Critical vigilance</span></div>
    {windows.map((window) => <details key={`${window.start_date}-${window.antardasha}`}>
      <summary>
        <span className={`longevity-risk-dot longevity-risk-dot--${window.level}`} />
        <div><b>{prettyDate(window.start_date)} — {prettyDate(window.end_date)}</b><span>{window.mahadasha}–{window.antardasha} · {window.label}</span></div>
        <strong>{window.convergence?.confirmed_systems ?? 0}/3</strong>
      </summary>
      <div className="longevity-window-detail">
        <div>{Object.entries(window.components).map(([key, value]) => <span key={key}>{key}<b>{value}</b></span>)}</div>
        {window.khanda_boundary && <p>{window.khanda_boundary.status === 'not_applicable' ? window.khanda_boundary.policy : <>Khanda boundary: <b>{window.khanda_boundary.status}</b> · midpoint age {window.khanda_boundary.age_at_midpoint}</>}</p>}
        <ul>{window.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
      </div>
    </details>)}
  </section>;
}

export default function LongevityPage({ user, onLogout, onAdminClick, onLogin }) {
  const navigate = useNavigate();
  const { birthData, chartData } = useAstrology();
  const [activeTab, setActiveTab] = useState('pillars');
  const [subject, setSubject] = useState('self');
  const [showBirthModal, setShowBirthModal] = useState(!birthData || !chartData);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const identity = useMemo(() => [birthData?.date, birthData?.time, birthData?.latitude, birthData?.longitude, chartData?.ascendant].join('|'), [birthData, chartData]);
  useEffect(() => {
    if (!birthData || !chartData) return;
    let cancelled = false;
    setLoading(true); setError('');
    longevityService.calculate(birthData, chartData, 12, subject)
      .then((payload) => { if (!cancelled) setResult(payload); })
      .catch((requestError) => {
        if (cancelled) return;
        const detail = requestError?.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : detail?.message || 'The longevity calculator could not be completed.');
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [identity, subject]);

  const verdict = result?.verdict;
  return <div className="longevity-page">
    <SEOHead title="Vedic Longevity Calculator | AstroRoshni" description="Explore Ayurdaya pillars, Maraka and Badhaka factors, sensitive points and preventive vigilance windows from your Vedic birth chart." canonical="https://astroroshni.com/longevity" noIndex />
    <ModernNavigationHeader user={user} onLogout={onLogout} onAdminClick={onAdminClick} onLogin={onLogin} />
    <main>
      <header className="longevity-hero">
        <button onClick={() => navigate('/')} className="longevity-back">← Back</button>
        <div><p className="longevity-eyebrow">Ayurdaya · Deterministic calculator</p><h1>Longevity & Vitality Inspector</h1><p>A high-level verdict first, with the mathematical evidence available below.</p></div>
      </header>

      {birthData && chartData && <section className="longevity-subject" aria-label="Select longevity view">
        <div><b>Read from this native chart</b><span>Parent views rotate the same chart to the classical parental house and confirm it in D12.</span></div>
        <div className="longevity-subject__buttons">{SUBJECTS.map(([id, label]) => <button type="button" key={id} className={subject === id ? 'active' : ''} aria-pressed={subject === id} onClick={() => { setSubject(id); setActiveTab('pillars'); }}>{label}</button>)}</div>
      </section>}

      {!birthData || !chartData ? <section className="longevity-empty longevity-panel"><span>✦</span><h2>Your chart is the starting point</h2><p>Enter an accurate birth date, time and place to calculate the three Ayurdaya pillars.</p><button onClick={() => setShowBirthModal(true)}>Enter birth details</button></section>
      : loading ? <section className="longevity-empty longevity-panel"><div className="longevity-loader" /><h2>Calculating classical factors…</h2><p>Resolving D3, D9, Shadbala, Ashtakavarga and dasha intersections.</p></section>
      : error ? <section className="longevity-empty longevity-panel"><h2>Calculator unavailable</h2><p>{error}</p><button onClick={() => setShowBirthModal(true)}>Review birth details</button></section>
      : result && <>
        <section className="longevity-verdict">
          <div className="longevity-verdict__main">
            <p>{subject === 'self' ? 'Calculated lifespan compartment' : `Derived ${result.subject.label} vitality support`}</p><h2>{verdict.compartment.label}</h2><span>{subject === 'self' ? `${verdict.compartment.range} years · baseline ${verdict.compartment.baseline_window.join('–')}` : verdict.compartment.interpretation}</span>
            <div className="longevity-confidence"><b>{verdict.compartment.confidence} {subject === 'self' ? 'agreement' : 'technical agreement'}</b><span>{verdict.compartment.agreement} · {verdict.compartment.adjustment}</span></div>
            {verdict.compartment.age_validation?.reconciled && <div className="longevity-confidence"><b>Attained-age reconciliation</b><span>{verdict.compartment.age_validation.reason}</span></div>}
          </div>
          <div className="longevity-verdict__threat"><p>{result.subject.label} threat vector</p><h3>{verdict.primary_threat.planet}</h3><span>{verdict.primary_threat.summary}</span><div className="longevity-threat-score">MPS {verdict.primary_threat.score}</div></div>
          <div className="longevity-verdict__current"><p>Current {result.subject.label.toLowerCase()} vulnerability</p><ScoreRing score={verdict.current_vulnerability.score} level={verdict.current_vulnerability.level} /><h3>{verdict.current_vulnerability.label}</h3></div>
        </section>
        <nav className="longevity-tabs" aria-label="Longevity report sections">{TABS.map(([id, label]) => <button className={activeTab === id ? 'active' : ''} onClick={() => setActiveTab(id)} key={id}>{label}</button>)}</nav>
        {activeTab === 'pillars' && <Pillars items={result.pillars} safeguards={result.safeguards} />}
        {activeTab === 'dossier' && <Dossier data={result.maraka_dossier} />}
        {activeTab === 'timeline' && <Timeline windows={result.crisis_windows} />}
        <aside className="longevity-disclaimer"><b>Use as a vigilance tool—not a fate verdict.</b><span>{result.disclaimer}</span></aside>
      </>}
    </main>
    <BirthFormModal isOpen={showBirthModal} onClose={() => setShowBirthModal(false)} onSubmit={() => setShowBirthModal(false)} title="Longevity Calculator — Birth Details" description="Accurate birth time is essential for D3, D9 and dasha calculations." />
  </div>;
}
