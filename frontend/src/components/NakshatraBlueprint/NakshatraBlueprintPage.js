import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import CreditsModal from '../Credits/CreditsModal';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import { apiErrorMessage, apiService } from '../../services/apiService';
import './NakshatraBlueprintPage.css';

const LIFE_AREA_TITLES = {
  identity: 'Identity', mind: 'Mind & emotions', family: 'Family & wealth', home: 'Home & roots',
  creativity: 'Creativity & children', work: 'Work & wellbeing', partnership: 'Partnership',
  transformation: 'Transformation', dharma: 'Dharma & learning', career: 'Career & purpose',
  gains: 'Gains & community', spirituality: 'Spirituality & rest',
};

const validBirthData = (birth) => Boolean(birth?.date && birth?.time && birth?.latitude != null && birth?.longitude != null);

export default function NakshatraBlueprintPage({ user, onLogout, onAdminClick, onLogin }) {
  const navigate = useNavigate();
  const { birthData } = useAstrology();
  const { credits, fetchBalance } = useCredits();
  const [pricing, setPricing] = useState(null);
  const [blueprint, setBlueprint] = useState(null);
  const [includeImages, setIncludeImages] = useState(false);
  const [accuracy, setAccuracy] = useState(15);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [forceRegenerate, setForceRegenerate] = useState(false);
  const [showBirthForm, setShowBirthForm] = useState(false);
  const [showCredits, setShowCredits] = useState(false);
  const [error, setError] = useState('');

  const request = useCallback((extra = {}) => ({
    birth_data: birthData,
    language: 'english',
    include_images: includeImages,
    birth_time_accuracy_minutes: accuracy,
    force_regenerate: false,
    ...extra,
  }), [accuracy, birthData, includeImages]);

  const load = useCallback(async () => {
    if (!user || !validBirthData(birthData)) { setLoading(false); return; }
    setLoading(true); setError(''); setBlueprint(null); setForceRegenerate(false);
    try {
      const [price, existing] = await Promise.all([
        apiService.getNakshatraBlueprintPricing(),
        apiService.getLatestNakshatraBlueprint(request()),
      ]);
      setPricing(price);
      if (existing?.exists) {
        setBlueprint(existing.payload);
        setIncludeImages(Boolean(existing.payload?.include_images));
        setAccuracy(existing.payload?.precision?.declared_accuracy_minutes ?? 15);
      }
    } catch (loadError) { setError(apiErrorMessage(loadError, 'Could not open your saved Blueprint.')); }
    finally { setLoading(false); }
  }, [birthData, request, user]);

  useEffect(() => { load(); }, [load]);

  const selectedCost = includeImages ? pricing?.illustrated_cost : pricing?.text_cost;
  const checkBeforePurchase = async () => {
    if (!user) { onLogin?.(); return; }
    if (!validBirthData(birthData)) { setShowBirthForm(true); return; }
    if (forceRegenerate) { setShowConfirm(true); return; }
    setChecking(true); setError('');
    try {
      const existing = await apiService.findNakshatraBlueprint(request());
      if (existing?.exists) { setBlueprint(existing.payload); return; }
      if (Number(credits) < Number(selectedCost || 0)) { setShowCredits(true); return; }
      setShowConfirm(true);
    } catch (checkError) { setError(apiErrorMessage(checkError)); }
    finally { setChecking(false); }
  };

  const generate = async () => {
    setShowConfirm(false); setGenerating(true); setError('');
    try {
      const result = await apiService.generateNakshatraBlueprint(request({ force_regenerate: forceRegenerate }));
      setBlueprint(result?.payload || null);
      setForceRegenerate(false);
      fetchBalance?.();
    } catch (generationError) { setError(apiErrorMessage(generationError, 'Could not create the Blueprint. No credits were used if it did not complete.')); }
    finally { setGenerating(false); }
  };

  const regenerate = () => {
    setIncludeImages(Boolean(blueprint?.include_images));
    setAccuracy(blueprint?.precision?.declared_accuracy_minutes ?? 15);
    setBlueprint(null); setForceRegenerate(true); setError('');
  };

  const progress = useMemo(() => generating ? 'The reading is being composed. This usually takes under a minute.' : '', [generating]);
  const reading = blueprint?.reading || {};
  const visualsByKey = useMemo(() => (blueprint?.visual_slots || []).reduce((all, visual) => ({ ...all, [visual?.key]: visual }), {}), [blueprint]);
  const lifeVisualKey = { identity: 'identity_foundation', mind: 'inner_nature', home: 'relationships_and_home', career: 'vocation_and_abundance' };

  return <div className="nb-page">
    <ModernNavigationHeader sticky user={user} onLogout={onLogout} onAdminClick={onAdminClick} onLogin={onLogin} />
    <main className="nb-shell">
      <button className="nb-back" type="button" onClick={() => navigate('/')}>← Home</button>
      <header className="nb-hero">
        <p>NEW · NATAL CONSULTATION</p><h1>Nakshatra Blueprint</h1>
        <span>{birthData?.name ? `A complete Nakshatra reading for ${birthData.name}.` : 'A complete natal reading through every graha’s Nakshatra and pada.'}</span>
      </header>
      {!user ? <section className="nb-empty"><h2>Your stellar signature, in detail.</h2><p>Sign in and select a saved birth chart to begin.</p><button className="nb-primary" type="button" onClick={onLogin}>Sign in to begin</button></section>
      : loading ? <section className="nb-empty"><span className="nb-spinner" /><p>Opening your saved Blueprint…</p></section>
      : !validBirthData(birthData) ? <section className="nb-empty"><h2>Add birth details first</h2><p>A precise birth date, time and place are needed for a Nakshatra and pada reading.</p><button className="nb-primary" type="button" onClick={() => setShowBirthForm(true)}>Add birth details</button></section>
      : !blueprint ? <section className="nb-config">
        <h2>{forceRegenerate ? 'Regenerate your Blueprint' : 'Choose your Blueprint'}</h2>
        <p>{forceRegenerate ? 'A fresh reading is charged again at the displayed price.' : 'A saved Blueprint is always restored free. A new edition is charged once.'}</p>
        <label className="nb-option"><input type="checkbox" checked={includeImages} onChange={(event) => setIncludeImages(event.target.checked)} /><span><strong>Illustrated Blueprint</strong><small>Adds four celestial life-scene artworks to the written reading.</small></span><b>{includeImages ? `${pricing?.illustrated_cost ?? '—'} credits total` : `+${pricing?.images_addon_cost ?? '—'} credits`}</b></label>
        <fieldset><legend>Birth-time accuracy</legend><div className="nb-choices">{[0, 15, 60].map((minutes) => <button key={minutes} type="button" className={accuracy === minutes ? 'is-selected' : ''} onClick={() => setAccuracy(minutes)}>{minutes === 0 ? 'Exact' : `±${minutes} min`}</button>)}</div></fieldset>
        <button className="nb-primary" type="button" disabled={checking || generating || !pricing} onClick={checkBeforePurchase}>{checking ? 'Checking your saved Blueprint…' : `${forceRegenerate ? 'Regenerate' : 'Generate'}${includeImages ? ' illustrated' : ''} Blueprint · ${selectedCost ?? '—'} credits`}</button>
      </section> : <section className="nb-reading">
        <div className="nb-reading-actions"><span>{blueprint.native_name || birthData?.name}</span><button type="button" onClick={() => window.print()}>Save as PDF</button><button type="button" onClick={regenerate}>Regenerate · {blueprint.credits_charged ?? selectedCost} credits</button></div>
        <article className="nb-opening"><h2>{reading.headline}</h2><p>{reading.opening}</p><small>{blueprint.precision?.message}</small></article>
        <h2 className="nb-section-title">Your life areas</h2><div className="nb-life-list">{(reading.life_areas || []).map((item) => { const visual = visualsByKey[lifeVisualKey[item.key]]; return <article className={`nb-card nb-life-card${visual?.url ? ' nb-life-card--illustrated' : ''}`} key={item.key}><div><h3>{item.title || LIFE_AREA_TITLES[item.key] || item.key}</h3><p>{item.reading}</p>{item.alignment && <aside><strong>Practical alignment</strong>{item.alignment}</aside>}</div>{visual?.url ? <figure className="nb-life-visual"><img src={visual.url} alt={visual.alt_text || `${item.title || item.key} illustration`} /></figure> : null}</article>; })}</div>
        <h2 className="nb-section-title">Planetary Nakshatra signatures</h2><p className="nb-section-intro">A concise reference for the instinct each graha brings to your life.</p><div className="nb-grid">{(reading.planet_readings || []).map((item) => <article className="nb-card" key={item.planet}><h3>{item.planet}</h3><p>{item.signature || item.behaviour}</p></article>)}</div>
        {(reading.nakshatra_remedies || []).length > 0 && <><h2 className="nb-section-title">Nakshatra remedies</h2><div className="nb-remedies">{reading.nakshatra_remedies.map((item, index) => <article className="nb-card" key={`${item.nakshatra}-${index}`}><em>{item.nakshatra}</em>{item.life_area && <b className="nb-supports">Supports: {item.life_area}</b>}<h3>{item.practice}</h3><p>{item.purpose}</p></article>)}</div></>}
      </section>}
      {error && <p className="nb-error" role="alert">{error}</p>}
      {generating && <div className="nb-progress" role="status"><span /><strong>Creating your Blueprint</strong><p>{progress}</p></div>}
    </main>
    {showConfirm && <div className="nb-confirm" role="dialog" aria-modal="true"><div><p>CONFIRM GENERATION</p><h2>{forceRegenerate ? 'Create a fresh Blueprint?' : 'Create your Blueprint?'}</h2><span>This will use <strong>{selectedCost} credits</strong>. Your saved reading remains available.</span><footer><button type="button" onClick={() => setShowConfirm(false)}>Cancel</button><button className="nb-primary" type="button" onClick={generate}>Use {selectedCost} credits</button></footer></div></div>}
    <BirthFormModal isOpen={showBirthForm} onClose={() => setShowBirthForm(false)} onSubmit={() => { setShowBirthForm(false); load(); }} title="Birth details for Nakshatra Blueprint" description="Precise birth details are needed for Nakshatra and pada interpretation." />
    <CreditsModal isOpen={showCredits} onClose={() => setShowCredits(false)} />
  </div>;
}
