import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAstrology } from '../../context/AstrologyContext';
import { apiService } from '../../services/apiService';
import './BirthTimeRectificationPage.css';

const FALLBACK_EVENTS = [
  ['marriage', 'Marriage or formal commitment'],
  ['childbirth', 'Birth of a child'],
  ['career_change', 'First job or major job change'],
  ['promotion', 'Promotion or major status increase'],
  ['education', 'Admission, graduation or education milestone'],
  ['relocation', 'Major relocation or foreign move'],
  ['property_purchase', 'Property or home purchase'],
].map(([key, label]) => ({ key, label }));

const emptyEvent = () => ({
  event_type: 'marriage',
  date_start: '',
  date_end: '',
  precision: 'exact_day',
  source_reliability: 'confident_memory',
});

function displayError(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  return error?.message || 'Something went wrong. Please try again.';
}

function timeLabel(value) {
  if (!value) return '—';
  const [hour, minute] = String(value).split(':').map(Number);
  const suffix = hour >= 12 ? 'PM' : 'AM';
  const displayHour = hour % 12 || 12;
  return `${displayHour}:${String(minute).padStart(2, '0')} ${suffix}`;
}

function confidenceCopy(value) {
  return {
    clear_relative_leader: 'One window leads clearly and remains stable when events are rechecked.',
    moderate_relative_leader: 'One window leads, but alternatives still deserve review.',
    multiple_plausible_windows: 'More than one window fits the available events.',
    insufficient_evidence: 'Add at least four strong events before treating the leading window as meaningful.',
  }[value] || 'This is a relative astrological fit, not proof of an exact birth minute.';
}

export default function BirthTimeRectificationPage({ user, onLogin }) {
  const navigate = useNavigate();
  const { birthData } = useAstrology();
  const chartId = birthData?.id || birthData?.birth_chart_id || birthData?.chart_id;
  const storageKey = chartId ? `astroroshni_rectification_case_${chartId}` : '';
  const [eventTypes, setEventTypes] = useState(FALLBACK_EVENTS);
  const [uncertainty, setUncertainty] = useState(30);
  const [caseData, setCaseData] = useState(null);
  const [eventDraft, setEventDraft] = useState(emptyEvent);
  const [run, setRun] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) return;
    apiService.getRectificationEventTypes()
      .then((payload) => setEventTypes(payload?.event_types?.length ? payload.event_types : FALLBACK_EVENTS))
      .catch(() => setEventTypes(FALLBACK_EVENTS));
  }, [user]);

  useEffect(() => {
    if (!user || !storageKey) return;
    const saved = window.localStorage.getItem(storageKey);
    if (!saved) return;
    apiService.getRectificationCase(saved)
      .then((payload) => {
        setCaseData(payload);
        if (payload?.active_run_id) {
          return apiService.getRectificationRun(payload.active_run_id);
        }
        return null;
      })
      .then((runPayload) => {
        if (runPayload) {
          setRun(runPayload);
          if (runPayload.status === 'completed') setResult(runPayload.result);
        }
      })
      .catch(() => window.localStorage.removeItem(storageKey));
  }, [storageKey, user]);

  useEffect(() => {
    if (!run?.id || !['pending', 'processing'].includes(run.status)) return undefined;
    const timer = window.setInterval(() => {
      apiService.getRectificationRun(run.id)
        .then((payload) => {
          setRun(payload);
          if (payload.status === 'completed') setResult(payload.result);
          if (payload.status === 'failed') setError(payload.error || 'The scan could not finish.');
        })
        .catch((pollError) => setError(displayError(pollError)));
    }, 1800);
    return () => window.clearInterval(timer);
  }, [run?.id, run?.status]);

  const progress = useMemo(() => {
    if (!run?.progress_total) return 0;
    return Math.min(100, Math.round((run.progress_current / run.progress_total) * 100));
  }, [run]);

  const createCase = async () => {
    if (!chartId) return;
    setBusy(true);
    setError('');
    try {
      const payload = await apiService.createRectificationCase({
        birth_chart_id: Number(chartId),
        uncertainty_minutes: uncertainty,
      });
      setCaseData(payload);
      setRun(null);
      setResult(null);
      window.localStorage.setItem(storageKey, payload.id);
    } catch (requestError) {
      setError(displayError(requestError));
    } finally {
      setBusy(false);
    }
  };

  const addEvent = async (event) => {
    event.preventDefault();
    if (!caseData?.id || !eventDraft.date_start) return;
    setBusy(true);
    setError('');
    try {
      await apiService.addRectificationEvent(caseData.id, {
        ...eventDraft,
        date_end: eventDraft.date_end || undefined,
      });
      const refreshed = await apiService.getRectificationCase(caseData.id);
      setCaseData(refreshed);
      setEventDraft(emptyEvent());
      setRun(null);
      setResult(null);
    } catch (requestError) {
      setError(displayError(requestError));
    } finally {
      setBusy(false);
    }
  };

  const startRun = async () => {
    setBusy(true);
    setError('');
    try {
      const payload = await apiService.startRectificationRun(caseData.id, 1);
      setRun(payload);
      setResult(payload.result || null);
    } catch (requestError) {
      setError(displayError(requestError));
    } finally {
      setBusy(false);
    }
  };

  const removeEvent = async (eventId) => {
    setBusy(true);
    setError('');
    try {
      await apiService.deleteRectificationEvent(eventId);
      const refreshed = await apiService.getRectificationCase(caseData.id);
      setCaseData(refreshed);
      setRun(null);
      setResult(null);
    } catch (requestError) {
      setError(displayError(requestError));
    } finally {
      setBusy(false);
    }
  };

  const startFreshCase = () => {
    if (storageKey) window.localStorage.removeItem(storageKey);
    setCaseData(null);
    setRun(null);
    setResult(null);
    setError('');
    setEventDraft(emptyEvent());
  };

  if (!user) {
    return (
      <main className="rectification-page rectification-empty">
        <h1>Birth-time rectification</h1>
        <p>Sign in to compare a saved chart with dated events from your life.</p>
        <button type="button" onClick={onLogin}>Sign in</button>
      </main>
    );
  }

  if (!chartId) {
    return (
      <main className="rectification-page rectification-empty">
        <h1>Birth-time rectification</h1>
        <p>Select a saved birth chart before starting this workbench.</p>
        <button type="button" onClick={() => navigate('/charts-dashas')}>Select chart</button>
      </main>
    );
  }

  return (
    <main className="rectification-page">
      <header className="rectification-hero">
        <button type="button" className="rectification-back" onClick={() => navigate('/charts-dashas')}>← Charts</button>
        <div>
          <span className="rectification-eyebrow">Evidence workbench</span>
          <h1>Birth-time rectification</h1>
          <p>
            Test nearby birth times against events that actually happened. AstroRoshni ranks supported
            windows; it does not pretend to prove an exact minute.
          </p>
        </div>
        <div className="rectification-native">
          <small>Selected chart</small>
          <strong>{birthData?.name || 'Native'}</strong>
          <span>{birthData?.date} · {birthData?.time}</span>
        </div>
      </header>

      {error ? <div className="rectification-error" role="alert">{error}</div> : null}

      {!caseData ? (
        <section className="rectification-card rectification-start">
          <span className="rectification-step">1</span>
          <div>
            <h2>How uncertain is the recorded time?</h2>
            <p>We will test every minute on either side of {timeLabel(birthData?.time)}.</p>
          </div>
          <div className="rectification-range-options" role="radiogroup" aria-label="Birth-time uncertainty">
            {[5, 15, 30, 60].map((minutes) => (
              <button
                type="button"
                role="radio"
                aria-checked={uncertainty === minutes}
                className={uncertainty === minutes ? 'is-active' : ''}
                onClick={() => setUncertainty(minutes)}
                key={minutes}
              >
                ±{minutes} min
              </button>
            ))}
          </div>
          <button type="button" className="rectification-primary" disabled={busy} onClick={createCase}>
            {busy ? 'Preparing…' : 'Create evidence case'}
          </button>
        </section>
      ) : (
        <>
          <section className="rectification-card">
            <div className="rectification-section-head">
              <div>
                <span className="rectification-step">2</span>
                <h2>Add dated life events</h2>
                <p>Documented exact dates carry more weight. Four or more independent events are recommended.</p>
              </div>
              <div className="rectification-case-actions">
                <strong>{caseData.events?.length || 0} events</strong>
                <button type="button" onClick={startFreshCase}>Start over</button>
              </div>
            </div>

            <div className="rectification-event-list">
              {(caseData.events || []).map((item) => (
                <article key={item.id}>
                  <span>{eventTypes.find((type) => type.key === item.event_type)?.label || item.event_type}</span>
                  <strong>{String(item.date_start)}{String(item.date_end) !== String(item.date_start) ? ` – ${String(item.date_end)}` : ''}</strong>
                  <small>{String(item.precision).replaceAll('_', ' ')} · {String(item.source_reliability).replaceAll('_', ' ')}</small>
                  <button type="button" disabled={busy} onClick={() => removeEvent(item.id)} aria-label={`Remove ${item.event_type} event`}>
                    Remove
                  </button>
                </article>
              ))}
            </div>

            <form className="rectification-event-form" onSubmit={addEvent}>
              <label>
                Event
                <select value={eventDraft.event_type} onChange={(e) => setEventDraft((old) => ({ ...old, event_type: e.target.value }))}>
                  {eventTypes.map((type) => <option key={type.key} value={type.key}>{type.label}</option>)}
                </select>
              </label>
              <label>
                Start date
                <input type="date" required value={eventDraft.date_start} onChange={(e) => setEventDraft((old) => ({ ...old, date_start: e.target.value }))} />
              </label>
              <label>
                End date <small>{eventDraft.precision === 'range' ? 'required' : 'optional'}</small>
                <input type="date" value={eventDraft.date_end} onChange={(e) => setEventDraft((old) => ({ ...old, date_end: e.target.value }))} />
              </label>
              <label>
                Date precision
                <select value={eventDraft.precision} onChange={(e) => setEventDraft((old) => ({ ...old, precision: e.target.value }))}>
                  <option value="exact_day">Exact day</option>
                  <option value="month">Month known</option>
                  <option value="year">Year known</option>
                  <option value="range">Approximate range</option>
                </select>
              </label>
              <label>
                Source
                <select value={eventDraft.source_reliability} onChange={(e) => setEventDraft((old) => ({ ...old, source_reliability: e.target.value }))}>
                  <option value="documented">Documented</option>
                  <option value="confident_memory">Confident memory</option>
                  <option value="approximate_memory">Approximate memory</option>
                </select>
              </label>
              <button
                type="submit"
                disabled={busy || !eventDraft.date_start || (eventDraft.precision === 'range' && !eventDraft.date_end)}
              >
                Add event
              </button>
            </form>
          </section>

          <section className="rectification-card rectification-run-card">
            <div>
              <span className="rectification-step">3</span>
              <h2>Compare candidate minutes</h2>
              <p>Four dated events are required. The scan compares Parashari promise, divisional charts, MD–AD–PD, transits and KP separately.</p>
            </div>
            <button
              type="button"
              className="rectification-primary"
              disabled={busy || (caseData.events?.length || 0) < 4 || ['pending', 'processing'].includes(run?.status)}
              onClick={startRun}
            >
              {['pending', 'processing'].includes(run?.status)
                ? 'Scanning evidence…'
                : (caseData.events?.length || 0) < 4
                  ? `Add ${4 - (caseData.events?.length || 0)} more event${4 - (caseData.events?.length || 0) === 1 ? '' : 's'}`
                  : 'Compare birth-time windows'}
            </button>
            {['pending', 'processing'].includes(run?.status) ? (
              <div className="rectification-progress" aria-label={`${progress}% complete`}>
                <span style={{ width: `${progress}%` }} />
                <small>{progress}% · {String(run.stage || '').replaceAll('_', ' ')}</small>
              </div>
            ) : null}
          </section>
        </>
      )}

      {result ? (
        <section className="rectification-results">
          <header>
            <span className="rectification-eyebrow">Research preview · leading supported window</span>
            <h2>{timeLabel(result.best_window?.start_local_time)} – {timeLabel(result.best_window?.end_local_time)}</h2>
            <p>{confidenceCopy(result.confidence_label)}</p>
            <div className="rectification-verdict-row">
              <span>Best minute <strong>{timeLabel(result.best_window?.best_local_time)}</strong></span>
              <span>Relative fit <strong>{Math.round(result.best_window?.relative_fit || 0)}/100</strong></span>
              <span>Events checked <strong>{result.event_count}</strong></span>
            </div>
          </header>

          <div className="rectification-landscape" aria-label="Candidate score landscape">
            {(result.score_landscape || []).map((point) => (
              <span key={point.local_time} title={`${timeLabel(point.local_time)} · ${Math.round(point.relative_fit)}`}>
                <i style={{ height: `${Math.max(4, point.relative_fit)}%` }} />
              </span>
            ))}
          </div>

          <div className="rectification-clusters">
            {(result.clusters || []).slice(0, 5).map((cluster) => (
              <details key={`${cluster.rank}-${cluster.start_local_time}`} open={cluster.rank === 1}>
                <summary>
                  <strong>#{cluster.rank} · {timeLabel(cluster.start_local_time)} – {timeLabel(cluster.end_local_time)}</strong>
                  <span>{Math.round(cluster.relative_fit)}/100 relative fit</span>
                </summary>
                <div className="rectification-evidence-grid">
                  {(cluster.best_candidate?.events || []).map((item) => (
                    <article key={item.event_id}>
                      <div><strong>{item.event_label}</strong><span className={`fit-${item.fit}`}>{item.fit}</span></div>
                      <small>{item.inspection_date} · event fit {Math.round(item.score)}/100</small>
                      <ul>
                        <li>Natal promise: {Math.round(item.structural_promise?.score || 0)}/10</li>
                        <li>Dasha delivery: {Math.round(item.dasha_delivery?.score || 0)}/40</li>
                        <li>{item.varga_confirmation?.chart}: {Math.round(item.varga_confirmation?.score || 0)}/20</li>
                        <li>Transit confirmation: {Math.round(item.transit_confirmation?.score || 0)}/15</li>
                        <li>KP confirmation: {Math.round(item.kp_confirmation?.score || 0)}/15</li>
                      </ul>
                    </article>
                  ))}
                </div>
              </details>
            ))}
          </div>

          <p className="rectification-disclaimer">{result.disclaimer} This is a validation preview, not a verified correction. Applying a rectified time to your saved chart is disabled.</p>
        </section>
      ) : null}
    </main>
  );
}
