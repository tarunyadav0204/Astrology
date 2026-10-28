import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import CreditsModal from '../Credits/CreditsModal';
import SEOHead from '../SEO/SEOHead';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import { apiErrorMessage, apiService } from '../../services/apiService';
import { generatePageSEO } from '../../config/seo.config';
import './NakshatraBlueprintPage.css';

const LIFE_AREA_TITLES = {
  identity: 'Identity', mind: 'Mind & emotions', family: 'Family & wealth', home: 'Home & roots',
  creativity: 'Creativity & children', work: 'Work & wellbeing', partnership: 'Partnership',
  transformation: 'Transformation', dharma: 'Dharma & learning', career: 'Career & purpose',
  gains: 'Gains & community', spirituality: 'Spirituality & rest',
};

const validBirthData = (birth) => Boolean(birth?.date && birth?.time && birth?.latitude != null && birth?.longitude != null);

const BLUEPRINT_FAQS = [
  ['What is a Nakshatra Blueprint?', 'Nakshatra Blueprint is a personalised natal reading that studies the Nakshatra and, where birth-time precision allows, the pada of every graha. It then brings the relevant patterns together by life area rather than offering a generic Sun-sign reading.'],
  ['Why do Nakshatras and padas matter?', 'In Vedic astrology, Nakshatras describe a graha’s instinctive style and motivation. Padas offer a finer layer of expression. They are read with the graha, rashi, house, aspects, strength, divisional charts and dasha context—not in isolation.'],
  ['What does the reading cover?', 'The Blueprint covers identity, mind and emotions, family and resources, home, creativity, work, partnership, transformation, learning, career, gains and spiritual rest. It also includes concise planetary Nakshatra signatures, practical alignment ideas and gentle remedies.'],
  ['How accurate must my birth time be?', 'A precise birth time is particularly important for the Ascendant, houses and Nakshatra padas. If the recorded time may vary, AstroRoshni lets you declare an accuracy range and clearly marks time-sensitive interpretation.'],
  ['Is Nakshatra Blueprint a prediction or a guarantee?', 'It is an interpretive natal consultation, not a guarantee of events or outcomes. It is designed to help you recognise chart patterns, strengths, tensions and practical ways to work with them.'],
];

const BLUEPRINT_AREAS = ['Identity and self-expression', 'Mind and emotional rhythm', 'Family, wealth and voice', 'Home and roots', 'Creativity and children', 'Work and wellbeing', 'Partnership', 'Transformation and shared resources', 'Dharma and learning', 'Career and purpose', 'Gains and community', 'Spirituality and rest'];

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
  const [progressPercent, setProgressPercent] = useState(0);
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
    setShowConfirm(false); setProgressPercent(0); setGenerating(true); setError('');
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
  useEffect(() => {
    if (!generating) { setProgressPercent(0); return undefined; }
    const startedAt = Date.now();
    const updateProgress = () => {
      const elapsed = Date.now() - startedAt;
      // Take a calm 40 seconds to reach 90%, then leave room for an unusually long response.
      const next = elapsed <= 40000
        ? 3 + (87 * elapsed / 40000)
        : 90 + Math.min(6, (elapsed - 40000) / 10000);
      setProgressPercent(Math.round(next));
    };
    updateProgress();
    const timer = window.setInterval(updateProgress, 250);
    return () => window.clearInterval(timer);
  }, [generating]);
  const reading = blueprint?.reading || {};
  const visualsByKey = useMemo(() => (blueprint?.visual_slots || []).reduce((all, visual) => ({ ...all, [visual?.key]: visual }), {}), [blueprint]);
  const lifeVisualKey = { identity: 'identity_foundation', mind: 'inner_nature', home: 'relationships_and_home', career: 'vocation_and_abundance' };
  const seoData = useMemo(() => generatePageSEO('nakshatraBlueprint', { path: '/nakshatra-blueprint' }), []);
  const structuredData = useMemo(() => ({
    '@context': 'https://schema.org', '@graph': [
      { '@type': 'WebPage', '@id': `${seoData.canonical}#webpage`, url: seoData.canonical, name: seoData.title, description: seoData.description, isPartOf: { '@type': 'WebSite', name: 'AstroRoshni', url: 'https://astroroshni.com/' }, about: [{ '@type': 'Thing', name: 'Nakshatra' }, { '@type': 'Thing', name: 'Vedic astrology' }] },
      { '@type': 'Service', name: 'Nakshatra Blueprint', url: seoData.canonical, description: seoData.description, provider: { '@type': 'Organization', name: 'AstroRoshni', url: 'https://astroroshni.com/' }, areaServed: 'Worldwide', serviceType: 'Personalised Vedic astrology natal reading' },
      { '@type': 'BreadcrumbList', itemListElement: [{ '@type': 'ListItem', position: 1, name: 'Home', item: 'https://astroroshni.com/' }, { '@type': 'ListItem', position: 2, name: 'Nakshatra Blueprint', item: seoData.canonical }] },
      { '@type': 'FAQPage', mainEntity: BLUEPRINT_FAQS.map(([question, answer]) => ({ '@type': 'Question', name: question, acceptedAnswer: { '@type': 'Answer', text: answer } })) },
    ],
  }), [seoData]);

  return <div className="nb-page">
    <SEOHead title={seoData.title} description={seoData.description} keywords={seoData.keywords} canonical={seoData.canonical} structuredData={structuredData} themeColor="#210b17" />
    <ModernNavigationHeader sticky user={user} onLogout={onLogout} onAdminClick={onAdminClick} onLogin={onLogin} />
    <main className="nb-shell">
      <button className="nb-back" type="button" onClick={() => navigate('/')}>← Home</button>
      <header className="nb-hero">
        <p>NEW · NATAL CONSULTATION</p><h1>Nakshatra Blueprint</h1>
        <span>{birthData?.name ? `A complete Nakshatra reading for ${birthData.name}.` : 'A complete natal reading through every graha’s Nakshatra and pada.'}</span>
      </header>
      {!user ? <><section className="nb-empty nb-seo-intro"><h2>Your stellar signature, in detail.</h2><p>Nakshatra Blueprint is a complete, personalised Vedic natal consultation. It reads every graha through its Nakshatra and pada, then connects those patterns to the parts of life where they are actually lived.</p><button className="nb-primary" type="button" onClick={onLogin}>Sign in to create your Blueprint</button></section><section className="nb-seo-section" aria-labelledby="nb-method"><p className="nb-seo-kicker">A Nakshatra-led natal reading</p><h2 id="nb-method">More than a Moon Nakshatra.</h2><p>Moon Nakshatra is important, but it is only one thread. A complete reading considers the Nakshatra nature of the Sun, Moon, Ascendant and all grahas—then uses rashi, house, aspects and chart context to understand where each pattern becomes meaningful. Pada-level detail is included when the supplied birth time supports it.</p><div className="nb-seo-grid"><article><strong>Every graha</strong><span>Concise Nakshatra signatures reveal the instinct each graha brings.</span></article><article><strong>Life first</strong><span>Deeper synthesis is organised around lived areas, not a list of placements.</span></article><article><strong>Practical guidance</strong><span>Each chapter includes an alignment practice and relevant gentle remedies.</span></article></div></section><section className="nb-seo-section" aria-labelledby="nb-areas"><p className="nb-seo-kicker">What your Blueprint explores</p><h2 id="nb-areas">Twelve connected life areas.</h2><p>Each chapter brings together the most relevant Nakshatra and pada patterns for that domain, so the reading feels like one coherent consultation.</p><ul className="nb-seo-areas">{BLUEPRINT_AREAS.map((area) => <li key={area}>{area}</li>)}</ul></section><section className="nb-seo-section nb-seo-section--accent" aria-labelledby="nb-precision"><p className="nb-seo-kicker">Birth-time precision</p><h2 id="nb-precision">Padas deserve care.</h2><p>Nakshatra padas can change near their boundaries. For that reason, the reading is transparent about the declared accuracy of the birth time and treats Ascendant and house-sensitive interpretation with appropriate care.</p></section><section className="nb-seo-section" aria-labelledby="nb-faq"><p className="nb-seo-kicker">Questions answered</p><h2 id="nb-faq">Nakshatra Blueprint FAQs</h2><div className="nb-faq">{BLUEPRINT_FAQS.map(([question, answer]) => <details key={question}><summary>{question}</summary><p>{answer}</p></details>)}</div></section></>
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
        {reading.presence_style?.reading && <article className="nb-card nb-presence"><p className="nb-seo-kicker">Presence, appearance & personal style</p><h3>{reading.presence_style.headline}</h3><p>{reading.presence_style.reading}</p>{reading.presence_style.style_direction && <aside><strong>Style direction</strong>{reading.presence_style.style_direction}</aside>}</article>}
        {(reading.core_patterns || []).length > 0 && <><h2 className="nb-section-title">The Nakshatra patterns that shape your life</h2><p className="nb-section-intro">These recurring dynamics connect your chart's placements into one story.</p><div className="nb-core-patterns">{reading.core_patterns.map((item, index) => <article className="nb-card" key={`${item.title}-${index}`}><h3>{item.title}</h3><p>{item.reading}</p></article>)}</div></>}
        <h2 className="nb-section-title">Your life areas</h2><div className="nb-life-list">{(reading.life_areas || []).map((item) => { const visual = visualsByKey[lifeVisualKey[item.key]]; return <article className={`nb-card nb-life-card${visual?.url ? ' nb-life-card--illustrated' : ''}`} key={item.key}><div><h3>{item.title || LIFE_AREA_TITLES[item.key] || item.key}</h3><p>{item.reading}</p>{item.application && <aside className="nb-application"><strong>In everyday life</strong>{item.application}</aside>}{!item.application && item.alignment && <aside><strong>Practical alignment</strong>{item.alignment}</aside>}</div>{visual?.url ? <figure className="nb-life-visual"><img src={visual.url} alt={visual.alt_text || `${item.title || item.key} illustration`} /></figure> : null}</article>; })}</div>
        <h2 className="nb-section-title">Planetary Nakshatra signatures</h2><p className="nb-section-intro">A concise reference for the instinct each graha brings to your life.</p><div className="nb-grid">{(reading.planet_readings || []).map((item) => <article className="nb-card" key={item.planet}><h3>{item.planet}</h3><p>{item.signature || item.behaviour}</p></article>)}</div>
        {(reading.nakshatra_remedies || []).length > 0 && <><h2 className="nb-section-title">Nakshatra remedies</h2><div className="nb-remedies">{reading.nakshatra_remedies.map((item, index) => <article className="nb-card" key={`${item.nakshatra}-${index}`}><em>{item.nakshatra}</em>{item.life_area && <b className="nb-supports">Supports: {item.life_area}</b>}<h3>{item.practice}</h3><p>{item.purpose}</p></article>)}</div></>}
      </section>}
      {user && !loading && !blueprint && validBirthData(birthData) ? <section className="nb-seo-section nb-seo-faq-for-user" aria-labelledby="nb-faq-signed-in"><p className="nb-seo-kicker">Before you begin</p><h2 id="nb-faq-signed-in">Nakshatra Blueprint FAQs</h2><div className="nb-faq">{BLUEPRINT_FAQS.map(([question, answer]) => <details key={question}><summary>{question}</summary><p>{answer}</p></details>)}</div></section> : null}
      {error && <p className="nb-error" role="alert">{error}</p>}
      {generating && <div className="nb-progress" role="status" aria-live="polite"><div className="nb-progress-track" role="progressbar" aria-label="Blueprint generation progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow={progressPercent}><span style={{ width: `${progressPercent}%` }} /></div><strong>Creating your Blueprint · {progressPercent}%</strong><p>{progress}</p></div>}
    </main>
    {showConfirm && <div className="nb-confirm" role="dialog" aria-modal="true"><div><p>CONFIRM GENERATION</p><h2>{forceRegenerate ? 'Create a fresh Blueprint?' : 'Create your Blueprint?'}</h2><span>This will use <strong>{selectedCost} credits</strong>. Your saved reading remains available.</span><footer><button type="button" onClick={() => setShowConfirm(false)}>Cancel</button><button className="nb-primary" type="button" onClick={generate}>Use {selectedCost} credits</button></footer></div></div>}
    <BirthFormModal isOpen={showBirthForm} onClose={() => setShowBirthForm(false)} onSubmit={() => { setShowBirthForm(false); load(); }} title="Birth details for Nakshatra Blueprint" description="Precise birth details are needed for Nakshatra and pada interpretation." />
    <CreditsModal isOpen={showCredits} onClose={() => setShowCredits(false)} />
  </div>;
}
