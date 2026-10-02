import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { useNavigate } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import CreditsModal from '../Credits/CreditsModal';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import { apiService } from '../../services/apiService';
import sampleMale from '../../assets/partner-portrait/sample-example.jpg';
import sampleFemale from '../../assets/partner-portrait/sample-woman-pair.jpg';
import generatingPreview from '../../assets/partner-portrait/generating-preview.jpg';
import './PartnerPortraitPage.css';

const AGES = ['25-34', '35-44', '45-54', '55+'];
const CLOTHING = [
  ['contemporary', 'Contemporary'],
  ['traditional_regional', 'Traditional'],
  ['modern_formal', 'Modern formal'],
];
const PROGRESS = [
  ['reading_chart', 'Reading the relationship pattern in your Kundli'],
  ['creating_portrait', 'Shaping a coherent face and expression'],
  ['creating_full_body', 'Completing the full-body portrait'],
];
const PROGRESS_RANK = { queued: 0, reading_chart: 0, creating_portrait: 1, creating_full_body: 2, ready: 3 };

const words = (value = '') => String(value).replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
const appearanceWords = (item) => {
  if (!item || typeof item !== 'object') return words(item);
  const value = words(item.value || item.trait || item.label || '');
  const attribute = words(item.attribute || '');
  return attribute && value ? `${attribute}: ${value}` : value || attribute;
};
const personalityWords = (item) => {
  if (!item || typeof item !== 'object') return words(item);
  return words(item.trait || item.value || item.label || '');
};
const consolidatedFactorReadings = (readings = []) => {
  const grouped = new Map();
  readings.forEach((reading) => {
    const key = `${reading?.factor_type || 'factor'}:${reading?.factor || ''}`;
    if (!reading?.factor) return;
    if (!grouped.has(key)) {
      grouped.set(key, {
        factor: reading.factor,
        factor_type: reading.factor_type,
        channels: [],
        appearance: [],
        personality: [],
        references: [],
      });
    }
    const entry = grouped.get(key);
    if (reading.channel && !entry.channels.includes(reading.channel)) entry.channels.push(reading.channel);
    (reading.appearance || []).forEach((item) => {
      const label = appearanceWords(item);
      if (label && !entry.appearance.includes(label)) entry.appearance.push(label);
    });
    (reading.personality || []).forEach((item) => {
      const label = personalityWords(item);
      if (label && !entry.personality.includes(label)) entry.personality.push(label);
    });
    const references = reading.references?.length
      ? reading.references
      : [{ source_id: reading.source_id, verse: reading.verse }];
    references.forEach((reference) => {
      const label = reference?.verse || reference?.source_id;
      if (label && !entry.references.includes(label)) entry.references.push(label);
    });
  });
  return [...grouped.values()];
};
const chartId = (chart) => Number(chart?.birth_chart_id || chart?.id || 0);
const partnerIsFeminine = (gender) => !['female', 'woman', 'f', 'girl'].includes(String(gender || '').trim().toLowerCase());
const errorDetail = (error) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string') return { message: detail };
  if (detail && typeof detail === 'object') return { code: detail.code, message: detail.message || detail.detail };
  return { message: error?.message || 'Something went wrong. Please try again.' };
};
const uniqueId = () => (globalThis.crypto?.randomUUID?.() || `portrait-${Date.now()}-${Math.random().toString(36).slice(2)}`);

function SampleExperience({ onStart, signedIn, gender }) {
  const image = partnerIsFeminine(gender) ? sampleFemale : sampleMale;
  return (
    <section className="pp-sample" aria-labelledby="partner-portrait-title">
      <div className="pp-sample__copy">
        <p className="pp-kicker">A portrait guided by your Kundli</p>
        <h1 id="partner-portrait-title">Meet the person your chart describes.</h1>
        <p className="pp-lead">Tara studies the seventh house, its lord, spouse significators, Navamsha and Darakaraka, resolves conflicting indications, and turns the final synthesis into two original portraits.</p>
        <button className="pp-primary" type="button" onClick={onStart}>{signedIn ? 'Create my partner’s portrait' : 'Sign in to create my partner’s portrait'} <span>→</span></button>
        <div className="pp-proof-grid">
          <div><strong>01</strong><span>Face portrait</span></div>
          <div><strong>02</strong><span>Full-body portrait</span></div>
          <div><strong>03</strong><span>Appearance and personality</span></div>
          <div><strong>04</strong><span>Classical reasoning</span></div>
        </div>
        <p className="pp-fine">An artistic interpretation of classical chart indications, not the identity of a specific person.</p>
      </div>
      <figure className="pp-sample__visual">
        <img src={image} alt="Watermarked sample of a Partner Portrait experience" />
        <span className="pp-watermark">SAMPLE</span>
        <figcaption><strong>What the finished experience includes</strong><span>Portrait, personality and the chart logic behind both.</span></figcaption>
      </figure>
    </section>
  );
}

function WorkingExperience({ stage, startedAt }) {
  const active = Math.max(0, PROGRESS_RANK[stage] ?? 0);
  const elapsed = Math.max(0, Math.floor((Date.now() - (startedAt || Date.now())) / 1000));
  return (
    <section className="pp-working" aria-live="polite">
      <div className="pp-working__visual">
        <img src={generatingPreview} alt="A softly blurred portrait taking shape" />
        <div className="pp-working__veil"><span></span><i></i></div>
      </div>
      <div className="pp-working__copy">
        <p className="pp-kicker">Tara is creating your portrait</p>
        <h2>A person is taking shape from the chart.</h2>
        <p>The work continues safely if you leave this page. Return at any time and we will reconnect you to the same portrait.</p>
        <ol className="pp-progress">
          {PROGRESS.map(([key, label], index) => (
            <li key={key} className={index < active ? 'is-done' : index === active ? 'is-active' : ''}>
              <span>{index < active ? '✓' : index + 1}</span><div><strong>{label}</strong>{index === active && <small>In progress · {elapsed}s</small>}</div>
            </li>
          ))}
        </ol>
        <p className="pp-fine">Detailed image creation can take a few minutes. Please do not submit another purchase.</p>
      </div>
    </section>
  );
}

function ResultExperience({ result, jobId, cost, onAnother, onPartnership, onAsk, onMarriage, onCompatibility }) {
  const [assetKind, setAssetKind] = useState('portrait');
  const [previewUrl, setPreviewUrl] = useState('');
  const [shareOpen, setShareOpen] = useState(false);
  const [shareFile, setShareFile] = useState(null);
  const [assetAction, setAssetAction] = useState('');
  const [assetMessage, setAssetMessage] = useState('');
  const profile = result?.profile || {};
  const summary = profile.resolved_summary || {};
  const assets = result?.assets || [];
  const selected = assets.find((item) => item.kind === assetKind) || assets[0];
  const appearance = summary.appearance || [];
  const personality = summary.personality || [];
  const factors = summary.dominant_factors || [];
  const factorReadings = useMemo(
    () => consolidatedFactorReadings(profile.factor_readings || []),
    [profile.factor_readings],
  );
  useEffect(() => () => {
    if (previewUrl?.startsWith('blob:')) URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);
  const loadAssetFile = async () => {
    if (!jobId || !selected?.kind) throw new Error('Portrait file is unavailable');
    const blob = await apiService.getPartnerPortraitAsset(jobId, selected.kind);
    const extension = blob.type === 'image/png' ? 'png' : blob.type === 'image/jpeg' ? 'jpg' : 'webp';
    return new File([blob], `astroroshni-partner-${selected.kind.replace('_', '-')}.${extension}`, { type: blob.type || 'image/webp' });
  };
  const downloadFile = (file) => {
    const url = URL.createObjectURL(file);
    const link = document.createElement('a');
    link.href = url; link.download = file.name; document.body.appendChild(link); link.click(); link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  useEffect(() => {
    setShareFile(null);
    if (!shareOpen || !jobId || !selected?.kind) return undefined;
    let cancelled = false;
    setAssetAction('share'); setAssetMessage('Preparing the image…');
    loadAssetFile().then((file) => {
      if (!cancelled) { setShareFile(file); setAssetMessage('Choose how you want to continue.'); }
    }).catch(() => {
      if (!cancelled) setAssetMessage('The image could not be prepared. Please try again.');
    }).finally(() => { if (!cancelled) setAssetAction(''); });
    return () => { cancelled = true; };
  }, [shareOpen, jobId, selected?.kind]);
  const sharePreparedFile = async () => {
    if (!shareFile || assetAction) return;
    const payload = { files: [shareFile], title: 'My AstroRoshni Partner Portrait', text: 'See the partner my Kundli describes.' };
    const nativeFileShare = navigator.share && (!navigator.canShare || navigator.canShare(payload));
    if (!nativeFileShare) {
      downloadFile(shareFile); setAssetMessage('Image downloaded. Attach it to the app or message where you want to share it.'); return;
    }
    try {
      await navigator.share(payload);
      setShareOpen(false);
    } catch (error) {
      if (error?.name !== 'AbortError') setAssetMessage('Sharing was not available. You can download the image instead.');
    }
  };
  const downloadPreparedFile = () => {
    if (!shareFile) return;
    downloadFile(shareFile);
    setAssetMessage('Image downloaded. Attach it wherever you want to share it.');
  };
  return (
    <>
      <section className="pp-result-hero">
        <div className="pp-result-visual">
          <div className="pp-image-tabs" role="tablist" aria-label="Portrait view">
            <button className={assetKind === 'portrait' ? 'is-active' : ''} onClick={() => setAssetKind('portrait')} type="button">Portrait</button>
            <button className={assetKind === 'full_body' ? 'is-active' : ''} onClick={() => setAssetKind('full_body')} type="button">Full body</button>
          </div>
          {selected?.url && <img src={selected.url} alt="Astrology-guided artistic portrait of a potential partner archetype" />}
          <div className="pp-image-actions">
            <button type="button" onClick={() => { setAssetMessage(''); setShareOpen(true); }}>Share</button>
            <button type="button" onClick={() => { setAssetMessage(''); setPreviewUrl(selected?.url || ''); }}>Open image</button>
          </div>
        </div>
        <div className="pp-result-intro">
          <p className="pp-kicker">Your Kundli’s partner archetype</p>
          <h1>Meet the person your chart describes.</h1>
          <p className="pp-lead">Tara has combined the strongest repeated indications into one coherent appearance and temperament.</p>
        </div>
      </section>
      {assetMessage && <p className="pp-asset-message" role="status">{assetMessage}</p>}
      {previewUrl && <div className="pp-image-viewer" role="dialog" aria-modal="true" aria-label="Partner portrait image viewer" onClick={() => setPreviewUrl('')}>
        <button type="button" aria-label="Close image viewer" onClick={() => setPreviewUrl('')}>×</button>
        <img src={previewUrl} alt="Astrology-guided artistic portrait of a potential partner archetype" onClick={(event) => event.stopPropagation()} />
      </div>}
      {shareOpen && <div className="pp-share-sheet" role="dialog" aria-modal="true" aria-label="Share Partner Portrait" onClick={() => setShareOpen(false)}>
        <div className="pp-share-sheet__card" onClick={(event) => event.stopPropagation()}>
          <button className="pp-share-sheet__close" type="button" aria-label="Close share options" onClick={() => setShareOpen(false)}>×</button>
          <img src={selected?.url} alt="Partner portrait ready to share" />
          <p className="pp-kicker">Share your portrait</p>
          <h2>Your image is ready.</h2>
          <p>{assetMessage || 'Preparing the image…'}</p>
          <div className="pp-share-sheet__actions">
            <button className="pp-primary" type="button" disabled={!shareFile} onClick={sharePreparedFile}>{shareFile && navigator.share && (!navigator.canShare || navigator.canShare({ files: [shareFile] })) ? 'Share image' : 'Download to share'} <span>→</span></button>
            <button className="pp-secondary" type="button" disabled={!shareFile} onClick={downloadPreparedFile}>Download image</button>
          </div>
        </div>
      </div>}

      <section className="pp-glance">
        <div className="pp-section-heading"><p className="pp-kicker">Your partner at a glance</p><h2>The clearest qualities in the chart</h2></div>
        <div className="pp-glance__grid">
          <article><span>Appearance</span><ul>{appearance.slice(0, 6).map((item) => <li key={`${item.attribute}-${item.value}`}><strong>{words(item.attribute)}</strong>{words(item.value)}</li>)}</ul></article>
          <article><span>Personality</span><ul>{personality.slice(0, 6).map((item) => <li key={item.trait}>{words(item.trait)}</li>)}</ul></article>
        </div>
      </section>

      <section className="pp-synthesis">
        <div className="pp-section-heading"><p className="pp-kicker">How Tara formed one clear picture</p><h2>Strong signals lead. Supporting signals add nuance.</h2></div>
        <div className="pp-factor-grid">
          {factors.map((factor, index) => <article key={`${factor.factor}-${index}`}><span>{index === 0 ? 'Dominant influence' : 'Supporting influence'}</span><h3>{factor.factor}</h3><p>{[...(factor.appearance || []).map((x) => words(x.value)), ...(factor.personality || []).map(words)].slice(0, 4).join(' · ')}</p></article>)}
        </div>
        {(summary.conflicts_resolved || []).length > 0 && <details className="pp-details"><summary>How conflicting indications were resolved <span>＋</span></summary><div>{summary.conflicts_resolved.map((item) => <p key={item.attribute}><strong>{words(item.attribute)}:</strong> {words(item.selected)} was repeated more strongly than {words(item.alternative)}.</p>)}</div></details>}
      </section>

      <div className="pp-result-lower-grid">
      <section className="pp-evidence">
        <div className="pp-section-heading"><p className="pp-kicker">Why Tara created this portrait</p><h2>The chart factors behind the result</h2></div>
        {factorReadings.map((reading) => (
          <details className="pp-details" key={`${reading.factor_type}-${reading.factor}`}>
            <summary><span><b>{reading.factor}</b><small>{reading.channels.map(words).join(' · ')}</small></span><i>＋</i></summary>
            <div>
              {reading.appearance.length > 0 && <p><strong>Appearance:</strong> {reading.appearance.join(', ')}</p>}
              {reading.personality.length > 0 && <p><strong>Personality:</strong> {reading.personality.join(', ')}</p>}
              {reading.references.length > 0 && <small className="pp-source">{reading.references.join(' · ')}</small>}
            </div>
          </details>
        ))}
      </section>

      <section className="pp-classics">
        <div><p className="pp-kicker">Classical basis</p><h2>Traceable sources, clearly separated from the artwork.</h2></div>
        <div>{(profile.references || []).map((ref, index) => <p key={`${ref.source_id}-${index}`}><strong>{ref.title || words(ref.source_id)}</strong><span>{ref.verse || ref.reference || ''}</span></p>)}</div>
        {profile.method_note && <small>{profile.method_note}</small>}
      </section>

      <section className="pp-beyond">
        <div className="pp-section-heading"><p className="pp-kicker">Go beyond the portrait</p><h2>Understand the relationship, not only the face.</h2></div>
        <div className="pp-beyond__grid">
          <button type="button" className="is-featured" onClick={onPartnership}><span>Best next step</span><strong>Analyse your partnership</strong><small>Bring both Kundlis together in Ask Tara.</small><i>→</i></button>
          <button type="button" onClick={onAsk}><strong>Ask Tara about your future partner</strong><small>Explore personality, meeting circumstances and relationship themes.</small><i>→</i></button>
          <button type="button" onClick={onMarriage}><strong>Marriage analysis</strong><small>Read promise, patterns and timing from your Kundli.</small><i>→</i></button>
          <button type="button" onClick={onCompatibility}><strong>Kundli matching</strong><small>Compare two known charts in depth.</small><i>→</i></button>
        </div>
      </section>

      <section className="pp-variation-card">
        <div className="pp-variation-card__mark" aria-hidden="true">◇</div>
        <div>
          <p className="pp-kicker">Another interpretation</p>
          <h2>Want to explore another possible look?</h2>
          <p>The same chart indications can create more than one coherent visual interpretation. Generate a different face and matching full-body portrait from the same astrological profile.</p>
          <button className="pp-secondary" type="button" onClick={onAnother}>Create another look · {cost} credits <span>→</span></button>
          <small>Your current portrait stays saved. You will review the options before credits are used.</small>
        </div>
      </section>
      </div>
    </>
  );
}

export default function PartnerPortraitPage({ user, onLogin, onLogout, onAdminClick }) {
  const navigate = useNavigate();
  const { birthData, setBirthData } = useAstrology();
  const { credits, features, partnerPortraitCost, fetchBalance, loading: creditsLoading } = useCredits();
  const [charts, setCharts] = useState([]);
  const [selectedId, setSelectedId] = useState(chartId(birthData));
  const [direction, setDirection] = useState(null);
  const [directionIssue, setDirectionIssue] = useState(null);
  const [cost, setCost] = useState(null);
  const [available, setAvailable] = useState(true);
  const [ageBand, setAgeBand] = useState('25-34');
  const [clothing, setClothing] = useState('contemporary');
  const [state, setState] = useState(user ? 'loading' : 'guest');
  const [stage, setStage] = useState('reading_chart');
  const [startedAt, setStartedAt] = useState(null);
  const [result, setResult] = useState(null);
  const [resultJobId, setResultJobId] = useState('');
  const [creatingVariation, setCreatingVariation] = useState(false);
  const [error, setError] = useState('');
  const [showCredits, setShowCredits] = useState(false);
  const pollRef = useRef(null);
  const selected = charts.find((item) => chartId(item) === selectedId) || birthData;
  const effectiveCost = Number(cost ?? partnerPortraitCost ?? 44);
  const featureEnabled = features?.partner_portrait_enabled === true;

  const stopPolling = useCallback(() => { if (pollRef.current) window.clearTimeout(pollRef.current); pollRef.current = null; }, []);
  const poll = useCallback(async (jobId) => {
    try {
      const payload = await apiService.getPartnerPortraitStatus(jobId);
      if (payload.chart_matches_current_version === false) {
        stopPolling(); setResult(null); setResultJobId(''); setState('setup'); return;
      }
      if (payload.status === 'completed') {
        stopPolling(); setResult(payload.data); setResultJobId(jobId); setCreatingVariation(false); setState('result'); setStage('ready'); fetchBalance(); return;
      }
      if (payload.status === 'failed') {
        stopPolling(); setError(payload.credits_refunded ? `${payload.error}. Your credits were returned.` : payload.error); setState('error'); fetchBalance(); return;
      }
      const reported = payload.progress_stage || (payload.status === 'processing' ? 'creating_portrait' : 'reading_chart');
      setStage((current) => (PROGRESS_RANK[reported] >= PROGRESS_RANK[current] ? reported : current));
      pollRef.current = window.setTimeout(() => poll(jobId), 3500);
    } catch (_) { pollRef.current = window.setTimeout(() => poll(jobId), 5000); }
  }, [fetchBalance, stopPolling]);

  const loadForChart = useCallback(async (id) => {
    if (!id) { setState('setup'); return; }
    stopPolling(); setDirection(null); setDirectionIssue(null); setResultJobId(''); setCreatingVariation(false); setError(''); setState('loading');
    try {
      const [config, directionData, history] = await Promise.all([
        apiService.getPartnerPortraitConfig(), apiService.getPartnerPortraitDirection(id), apiService.getPartnerPortraitHistory(),
      ]);
      setCost(Number(config.cost)); setAvailable(config.available !== false); setDirection(directionData);
      const chartHistory = (history.items || []).filter((item) => (
        Number(item.birth_chart_id) === Number(id) && item.matches_current_chart !== false
      ));
      const active = chartHistory.find((item) => ['pending', 'processing'].includes(item.status));
      const completedHistory = chartHistory.find((item) => item.status === 'completed');
      if (active) {
        setState('working'); setStartedAt(Date.now()); poll(active.job_id);
      } else if (completedHistory) {
        const completed = await apiService.getPartnerPortraitStatus(completedHistory.job_id);
        if (completed.chart_matches_current_version === false) {
          setResult(null); setResultJobId(''); setState('setup');
        } else {
          setResult(completed.data); setResultJobId(completedHistory.job_id); setState('result');
        }
      } else { setResult(null); setResultJobId(''); setCreatingVariation(false); setState('setup'); }
    } catch (requestError) {
      const detail = errorDetail(requestError);
      if (detail.code === 'GENDER_REQUIRED') { setDirectionIssue('GENDER_REQUIRED'); setState('setup'); }
      else { setError(detail.message); setState('error'); }
    }
  }, [poll, stopPolling]);

  useEffect(() => {
    if (!user) { setState('guest'); return undefined; }
    if (creditsLoading || !featureEnabled) return undefined;
    let cancelled = false;
    apiService.getExistingCharts('', 100, 0).then((chartResponse) => {
      if (cancelled) return;
      const list = chartResponse.charts || chartResponse.items || [];
      setCharts(list);
      const preferred = list.find((item) => chartId(item) === chartId(birthData)) || list[0];
      const id = chartId(preferred);
      setSelectedId(id);
      if (preferred) setBirthData(preferred);
      if (id) loadForChart(id); else setState('setup');
    }).catch((requestError) => { if (!cancelled) { setError(errorDetail(requestError).message); setState('error'); } });
    return () => { cancelled = true; stopPolling(); };
  }, [creditsLoading, featureEnabled, user]);

  useEffect(() => {
    if (!creditsLoading && !featureEnabled) navigate('/', { replace: true });
  }, [creditsLoading, featureEnabled, navigate]);

  const chooseChart = (event) => {
    const id = Number(event.target.value); const next = charts.find((item) => chartId(item) === id);
    setSelectedId(id); if (next) setBirthData(next); loadForChart(id);
  };
  const generate = async () => {
    if (!user) return onLogin?.();
    if (!selectedId || directionIssue) return;
    if (credits < effectiveCost) { setShowCredits(true); return; }
    setError(''); setState('working'); setStage('reading_chart'); setStartedAt(Date.now());
    try {
      const job = await apiService.generatePartnerPortrait({ birth_chart_id: selectedId, age_band: ageBand, clothing_style: clothing, idempotency_key: uniqueId() });
      setResultJobId(job.job_id); fetchBalance(); poll(job.job_id);
    } catch (requestError) {
      const detail = errorDetail(requestError);
      if (requestError?.response?.status === 402) setShowCredits(true);
      else { setError(detail.message); setState('error'); }
      fetchBalance();
    }
  };

  const pageProps = { user, onLogin, onLogout, onAdminClick, showNativeBar: false };
  return (
    <div className="partner-portrait-page">
      <Helmet><title>Partner Portrait from Your Kundli | AstroRoshni</title><meta name="description" content="Create an artistic portrait and personality profile of the partner archetype described by your Vedic birth chart." /></Helmet>
      <ModernNavigationHeader {...pageProps} />
      {user && featureEnabled && <div className="pp-toolbar"><div><span>Reading for</span><select value={selectedId || ''} onChange={chooseChart} aria-label="Select birth chart"><option value="" disabled>Select a Kundli</option>{charts.map((chart) => <option key={chartId(chart)} value={chartId(chart)}>{chart.name}</option>)}</select></div><button type="button" onClick={() => navigate('/charts-dashas')}>Open Kundli ↗</button></div>}
      <main className="pp-main">
        {creditsLoading && <div className="pp-loading"><span></span><h2>Opening Partner Portrait…</h2></div>}
        {!creditsLoading && state === 'guest' && <SampleExperience signedIn={false} onStart={onLogin} />}
        {!creditsLoading && state === 'loading' && <div className="pp-loading"><span></span><h2>Opening your saved portrait experience…</h2></div>}
        {state === 'setup' && <>
          {!creatingVariation && <SampleExperience signedIn gender={selected?.gender} onStart={() => document.getElementById('create-partner-portrait')?.scrollIntoView({ behavior: 'smooth' })} />}
          <section className="pp-create-panel" id="create-partner-portrait">
            <div>
              <p className="pp-kicker">{creatingVariation ? 'Another interpretation' : 'Create yours'}</p>
              <h2>{creatingVariation ? 'Create another possible look' : `A distinct portrait for ${selected?.name || 'your Kundli'}`}</h2>
              <p>{creatingVariation ? 'This deliberately creates a different face from the same chart indications. Your current portrait remains saved until the new one is complete.' : 'The chart decides the partner presentation and cultural context from saved gender and birth coordinates. You choose only the age and clothing style.'}</p>
              {creatingVariation && <button className="pp-keep-current" type="button" onClick={() => { setCreatingVariation(false); setState('result'); }}>← Keep my current portrait</button>}
            </div>
            {charts.length === 0 ? <div className="pp-callout"><strong>A saved Kundli is needed</strong><p>Create or save a birth chart before generating the portrait.</p><button className="pp-primary" type="button" onClick={() => navigate('/ai-kundli-generator')}>Create Kundli →</button></div> : directionIssue === 'GENDER_REQUIRED' ? <div className="pp-callout pp-callout--warning"><strong>Add gender to this Kundli</strong><p>Partner presentation is derived from the selected native. Add gender in the saved chart before continuing.</p><button className="pp-secondary" type="button" onClick={() => navigate('/profile')}>Update saved Kundli</button></div> : <div className="pp-form">
              <label><span>Partner age in the artwork</span><div className="pp-choice-row">{AGES.map((age) => <button type="button" className={ageBand === age ? 'is-active' : ''} onClick={() => setAgeBand(age)} key={age}>{age}</button>)}</div></label>
              <label><span>Portrait style</span><div className="pp-choice-row">{CLOTHING.map(([key, label]) => <button type="button" className={clothing === key ? 'is-active' : ''} onClick={() => setClothing(key)} key={key}>{label}</button>)}</div></label>
              {direction && <p className="pp-derived">Tara will create a <strong>{direction.presentation}</strong> partner portrait with <strong>{words(direction.visual_context)}</strong> visual context, derived from this saved chart.</p>}
              <div className="pp-purchase"><div><small>Your balance</small><strong>{credits} credits</strong></div><div><small>One complete experience</small><strong>{effectiveCost} credits</strong></div></div>
              <button className="pp-primary" type="button" onClick={generate} disabled={!available || !direction || !Number.isFinite(effectiveCost)}>{!available ? 'Temporarily unavailable' : credits < effectiveCost ? 'Get credits to create portrait' : creatingVariation ? `Create another possible look · ${effectiveCost} credits` : `Create my partner’s portrait · ${effectiveCost} credits`} <span>→</span></button>
            </div>}
          </section>
        </>}
        {state === 'working' && <WorkingExperience stage={stage} startedAt={startedAt} />}
        {state === 'result' && <ResultExperience result={result} jobId={resultJobId} cost={effectiveCost} onAnother={() => { setCreatingVariation(true); setState('setup'); window.setTimeout(() => document.getElementById('create-partner-portrait')?.scrollIntoView({ behavior: 'smooth' }), 50); }} onPartnership={() => navigate('/chat', { state: { startPartnership: true, birthData: selected } })} onAsk={() => navigate('/chat', { state: { openSingleChartChat: true, birthData: selected, followUpQuestion: 'What does my Kundli show about my future partner and the circumstances in which we may meet?' } })} onMarriage={() => navigate('/marriage-analysis')} onCompatibility={() => navigate('/kundli-matching')} />}
        {state === 'error' && <section className="pp-error"><p className="pp-kicker">We could not open this experience</p><h1>Your purchase is protected.</h1><p>{error}</p><button className="pp-primary" type="button" onClick={() => loadForChart(selectedId)}>Try again →</button></section>}
      </main>
      <CreditsModal isOpen={showCredits} onClose={() => setShowCredits(false)} onLogin={onLogin} />
    </div>
  );
}
