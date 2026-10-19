import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { apiService } from '../../services/apiService';
import './MrityuBhagaWorkspace.css';
import ChartWidget from '../Charts/ChartWidget';
import { printMrityuBhagaReport, ordinal } from '../../utils/mrityuBhagaExport';
import { buildBhriguBinduReport } from '../../utils/bhriguBinduExport';
const focuses = ['general', 'career', 'marriage', 'family', 'finances', 'education', 'property', 'health', 'travel'];
const orbLabel = v => Number(v) === 5/3 ? 'Patel ±1°40′ (100 arcminutes)' : `±${v}°`;
const focusLinks = rows => rows.map(c => `${{mahadasha:'MD',antardasha:'AD',pratyantardasha:'PD'}[c.level]}: ${c.lord} (natal houses ${c.houses.join(', ')})`).join(' · ');
const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};
const plus = (value, days) => {
  const d = new Date(`${value}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
};
const moment = (value, utc) => new Date(value).toLocaleString('en-GB', {
  dateStyle: 'medium',
  timeStyle: 'medium',
  ...(utc ? {
    timeZone: 'UTC'
  } : {})
});
const label = point => point === 'Ascendant' ? 'Lagna' : point === 'Mandi' ? 'Gulika / Mandi' : point;
const strength = value => value ? `${value.total_rupas ?? (value.total_points / 60).toFixed(2)} rupas · ${value.required_percent}% of required strength` : 'Not applicable';
const links = rows => rows.map(r => `${{mahadasha:'MD',antardasha:'AD',pratyantardasha:'PD'}[r.level]}: ${r.lord} (${(r.roles || []).map(role => role.replaceAll('_', ' ')).join(', ')})`).join(' · ');
const foldCalendarLine = line => {
  let current = '',
    bytes = 0;
  const rows = [];
  for (const char of line) {
    const code = char.codePointAt(0);
    const length = code > 65535 ? 4 : code > 2047 ? 3 : code > 127 ? 2 : 1;
    if (bytes + length > 73) {
      rows.push(current);
      current = ' ';
      bytes = 1;
    }
    current += char;
    bytes += length;
  }
  rows.push(current);
  return rows.join('\r\n');
};
const kind = row => row.aspect_number === 1 ? 'Passes over the Bhrigu Bindu' : `${ordinal(row.aspect_number)} aspect to the Bhrigu Bindu`;
function download(name, content, type = 'text/plain') {
  const url = URL.createObjectURL(new Blob([content], {
    type
  }));
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
const icsDate = value => new Date(value).toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z/, 'Z');
export function makeCalendar(events) {
  return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//AstroRoshni//Bhrigu Bindu//EN', 'CALSCALE:GREGORIAN', ...events.flatMap(r => ['BEGIN:VEVENT', `UID:${r.id}:${r.start_at}@astroroshni.com`, `DTSTAMP:${icsDate(new Date())}`, `DTSTART:${icsDate(r.start_at)}`, `DTEND:${icsDate(r.end_at)}`, `SUMMARY:${r.planet} - ${label(r.point)} - ${kind(r)}`, 'DESCRIPTION:Potential activation evidence. Review natal conditions and dasha connections in AstroRoshni.', 'END:VEVENT']), 'END:VCALENDAR'].map(foldCalendarLine).join('\r\n');
}
export default function BhriguBinduWorkspace({
  birthData,
  onAsk,
  onHighlight
}) {
  const [open, setOpen] = useState(false);
  return <><button type="button" className="parashari-desk-chip" onClick={() => setOpen(true)}>Bhrigu Bindu</button>{open && createPortal(<Workspace key={JSON.stringify(birthData)} birthData={birthData} onClose={() => {
      setOpen(false);
      onHighlight?.(null);
    }} onAsk={onAsk} onHighlight={onHighlight} />, document.body)}</>;
}
export function Workspace({
  birthData,
  onClose,
  onAsk,
  onHighlight
}) {
  const [tab, setTab] = useState('natal'),
    [data, setData] = useState(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  const [exporting, setExporting] = useState(false);
  const [start, setStart] = useState(today),
    [end, setEnd] = useState(() => plus(today(), 89)),
    [fast, setFast] = useState(false),
    [aspects, setAspects] = useState(false),
    [orb, setOrb] = useState(String(5/3)),
    [customOrb, setCustomOrb] = useState(false),
    [focus, setFocus] = useState('general'),
    [relevantOnly, setRelevantOnly] = useState(false),
    [preview, setPreview] = useState(null),
    [previewId, setPreviewId] = useState(null),
    [previewBusy, setPreviewBusy] = useState(false);
  const [type, setType] = useState('all'),
    [multiple, setMultiple] = useState(false),
    [utc, setUtc] = useState(false),
    [sensitivity, setSensitivity] = useState(0);
  const [exportIds, setExportIds] = useState(new Set());
  const [showChart, setShowChart] = useState(() => window.innerWidth > 900);
  const noteKey = `bb-notes-v1:${JSON.stringify([birthData.date, birthData.time, birthData.latitude, birthData.longitude, birthData.calculation_profile])}`;
  const [notes, setNotes] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(noteKey) || '{}');
    } catch {
      return {};
    }
  });
  const [noteError, setNoteError] = useState('');
  const [visibleCount, setVisibleCount] = useState(40);
  useEffect(() => setVisibleCount(40), [type, multiple, relevantOnly, data]);
  const previewController = useRef(null);
  const controller = useRef(null),
    dialog = useRef(null),
    lastFocus = useRef(null);
  const content = useRef(null);
  useEffect(() => {
    content.current?.scrollTo?.({
      top: 0
    });
  }, [tab]);
  async function load(calendar = false, comparison = sensitivity) {
    if (!Number.isFinite(Number(orb)) || Number(orb) < 0.1 || Number(orb) > 3) {
      setError('Choose a contact distance between 0.1° and 3°.');
      return;
    }
    controller.current?.abort();
    previewController.current?.abort();
    setPreview(null);
    setPreviewBusy(false);
    const request = new AbortController();
    controller.current = request;
    setBusy(true);
    setError('');
    setExportIds(new Set());
    try {
      const result = await apiService.getBhriguBinduWorkspace(birthData, {
        start_date: start,
        end_date: end,
        calendar,
        include_fast: fast,
        include_aspects: aspects,
        orb_degrees: Number(orb),
        birth_time_minutes: comparison,
        focus
      }, request.signal);
      if (!request.signal.aborted) setData(result);
    } catch (e) {
      if (!request.signal.aborted) setError(e.response?.data?.detail || e.message || 'Calculation unavailable.');
    } finally {
      if (!request.signal.aborted) setBusy(false);
    }
  }
  useEffect(() => {
    load(false);
    return () => {controller.current?.abort(); previewController.current?.abort();};
  }, []); // Mounted per birth/profile; calendar is explicitly recalculated.
  useEffect(() => {
    lastFocus.current = document.activeElement;
    dialog.current?.focus();
    const key = e => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'Tab') {
        const items = [...dialog.current.querySelectorAll('button,input,select,textarea,[tabindex="0"]')].filter(el => !el.disabled);
        const first = items[0],
          last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener('keydown', key);
    const old = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', key);
      document.body.style.overflow = old;
      lastFocus.current?.focus();
    };
  }, [onClose]);
  const updateNote = (key, value) => {
    const next = {
      ...notes,
      [key]: value
    };
    setNotes(next);
    try {
      localStorage.setItem(noteKey, JSON.stringify(next));
      setNoteError('');
    } catch {
      setNoteError('Notes could not be saved on this device.');
    }
  };
  async function openTransit(event, at) {
    previewController.current?.abort();
    const request = new AbortController();
    previewController.current = request;
    setPreview(null);
    setPreviewId(event.id);
    setPreviewBusy(true);
    setError('');
    try {
      const result = await apiService.getBhriguBinduWorkspace(birthData, {start_date:start,end_date:end,calendar:false,focus,orb_degrees:Number(orb),chart_at:at}, request.signal);
      if (!request.signal.aborted) setPreview(result.selected_transit);
    } catch (e) {
      if (!request.signal.aborted) setError(typeof e.response?.data?.detail === 'string' ? e.response.data.detail : e.message || 'Transit chart unavailable.');
    } finally {
      if (!request.signal.aborted) setPreviewBusy(false);
    }
  }
  const invalidate = fn => {
    controller.current?.abort();
    previewController.current?.abort();
    setPreview(null);
    setPreviewBusy(false);
    setBusy(false);
    setData(previous => previous ? {
      ...previous,
      calendar_calculated: false,
      events: [],
      dasha_activations: []
    } : previous);
    fn();
  };
  const events = (data?.events || []).filter(r => (!multiple || r.concurrent_transits?.length) && (!relevantOnly || focus === 'general' || r.focus_evidence?.length) && (type === 'all' || (type === 'conjunction' ? r.aspect_number === 1 : r.aspect_number !== 1)));
  const dashas = data?.dasha_activations || [];
  const savePdf = async () => {
    if (exporting) return;
    setExporting(true);
    try {
      await printMrityuBhagaReport(buildBhriguBinduReport(data, birthData, notes, events));
    } catch (e) {
      setError(`PDF export unavailable: ${e.message}`);
    } finally {
      setExporting(false);
    }
  };
  return <div className="mb-backdrop"><section className="mb-workspace" role="dialog" aria-modal="true" aria-labelledby="mb-title" ref={dialog} tabIndex={-1}>
    <header className="mb-header"><div><small>ASTROROSHNI · ASTROLOGER WORKSPACE</small><h2 id="mb-title">Bhrigu Bindu</h2><p>{birthData.name} · Natal assessment & activation calendar</p></div><button onClick={onClose} aria-label="Close Bhrigu Bindu">✕</button></header>
    <nav className="mb-tabs" aria-label="Workspace views">{['natal', 'calendar', 'audit'].map(t => <button key={t} aria-pressed={tab === t} onClick={() => setTab(t)}>{t === 'natal' ? 'Natal assessment' : t === 'calendar' ? 'Activation calendar' : 'Calculation audit'}</button>)}</nav>
    <div ref={content} className="mb-scroll">
      {error && <div role="alert" className="mb-error">{String(error)} <button onClick={() => load(tab === 'calendar')}>Retry</button></div>}
      {busy && <p role="status">{tab === 'calendar' ? 'Resolving transit crossings, stations and dasha overlaps…' : 'Calculating the natal assessment…'}</p>}
      {data?.natal.unavailable_points?.map(p => <p role="alert" className="mb-error" key={p.point}>Assessment incomplete: {p.point} could not be checked. {p.reason} Its absence is not a negative finding.</p>)}
      {data && tab === 'natal' && <>{data.natal.points.map(p => <article className="mb-card" key={p.point}>
        <h3>Bhrigu Bindu · House {p.house}</h3><p className="mb-note">C. S. Patel: Rahu → Moon arc</p><p className="mb-position">{p.position}</p>
        <p>{p.nakshatra} · Pada {p.pada} · Nakshatra ruler: {p.nakshatra_lord}</p>
        <p><strong>House themes:</strong> {(p.house_themes || []).join(', ')}. These describe areas to examine, rather than a promised event.</p><p>A calculated sensitive point between Rahu and Moon. Read its house and ruler alongside the rest of the chart.</p>
        <dl><dt>Moon</dt><dd>{p.moon_position}</dd><dt>Rahu</dt><dd>{p.rahu_position}</dd><dt>How it is calculated</dt><dd>Move forward from Rahu to Moon through the zodiac and take half that distance ({p.forward_arc_degrees.toFixed(4)}° ÷ 2).</dd>
        <dt>Sign ruler</dt><dd>{p.dispositor} · {p.dispositor_position} · {p.dispositor_dignity || 'Unspecified'} · {strength(p.dispositor_strength)}{p.dispositor_retrograde ? ' · Retrograde' : ''}{p.dispositor_combustion?.is_combust ? ' · Combust' : ''}</dd>
        <dt>Planet connections</dt><dd>{p.relationships.map(r => `${r.planet}: ${r.relation === 'same_sign' ? `same sign (${r.separation_degrees.toFixed(2)}° apart)` : `${ordinal(r.aspect_number)} whole-sign aspect`}`).join(' · ') || 'None'}</dd></dl>
        <p className="mb-note">Dasha context at range start: {data.dasha_activations.filter(r => r.start_at === data.range.start_at).map(r => links(r.connections)).join(' · ') || 'No linked period'}. These are contextual links, not a separate Bhrigu Bindu dasha.</p>
        <button onClick={() => setShowChart(!showChart)}>{showChart ? 'Hide linked chart' : 'Show linked chart'}</button>
        {showChart && <ChartWidget chartData={data.natal_chart} birthData={birthData} chartType="lagna" highlightedPlanets={['Moon', 'Rahu', p.dispositor]} selectedHouseNumber={p.house} deskMode />}
        <div className="mb-actions"><button onClick={() => setTab('calendar')}>View activation dates</button>{onAsk && <button onClick={() => { onAsk(`Analyze Bhrigu Bindu at ${p.position}, house ${p.house}, calculated using the forward Rahu-to-Moon midpoint. Discuss house themes, sign ruler ${p.dispositor}, nakshatra ruler ${p.nakshatra_lord}, natal connections and transit/dasha context. Consultation focus: ${focus}. Separate calculated facts from interpretation.`); onClose(); }}>Ask Tara</button>}</div>
        <label className="mb-note-input">Astrologer notes · saved on this device<textarea value={notes[p.point] || ''} onChange={e => updateNote(p.point, e.target.value)} /></label>
      </article>)}<label>Check nearby birth times <select value={sensitivity} onChange={e => { setSensitivity(Number(e.target.value)); load(false, Number(e.target.value)); }}><option value={0}>Recorded time only</option>{[5,10,15].map(n => <option key={n} value={n}>{n} min earlier / later</option>)}</select></label>{data.birth_time_comparison.map(r => <p key={r.offset_minutes}>{r.offset_minutes > 0 ? '+' : ''}{r.offset_minutes} min: {r.position} · House {r.house} · {r.nakshatra}</p>)}{!!sensitivity && <p className="mb-note">Only the recorded time and selected endpoints are checked. Times between them are not checked.</p>}</>}
      {tab === 'calendar' && <><label>Consultation focus <select value={focus} onChange={e => invalidate(() => {setFocus(e.target.value); setRelevantOnly(false);})}>{focuses.map(v => <option key={v} value={v}>{v[0].toUpperCase()+v.slice(1)}</option>)}</select></label><p className="mb-note">Focus explains connections to the selected topic. All contacts remain visible unless you choose to filter them.</p><form className="mb-controls" onSubmit={e => {
            e.preventDefault();
            load(true);
          }}><label>From<input type="date" required value={start} onChange={e => invalidate(() => setStart(e.target.value))} /></label><label>Through<input type="date" required min={start} value={end} onChange={e => invalidate(() => setEnd(e.target.value))} /></label><label>Contact distance<select value={customOrb ? 'custom' : orb} onChange={e => invalidate(() => {setCustomOrb(e.target.value === 'custom'); setOrb(e.target.value === 'custom' ? '1' : e.target.value);})}>{['0.5', '1', String(5/3), '2', '3'].map(v => <option key={v} value={v}>{orbLabel(v)}</option>)}<option value="custom">Custom distance</option></select></label>{customOrb && <label>Custom distance (degrees)<input type="number" required min="0.1" max="3" step="any" value={orb} onChange={e => invalidate(() => setOrb(e.target.value))} /></label>}<button disabled={busy}>Calculate calendar</button></form>
        <div className="mb-actions">{[30, 90, 365].map(n => <button key={n} onClick={() => invalidate(() => setEnd(plus(start, n - 1)))}>{n} days</button>)}<label><input type="checkbox" checked={fast} onChange={e => invalidate(() => setFast(e.target.checked))} />Include Sun, Moon, Mercury, Venus</label><label><input type="checkbox" checked={aspects} onChange={e => invalidate(() => setAspects(e.target.checked))} />Include aspect degree contacts</label></div>
        <p className="mb-note">Dates use the birth timezone ({data?.range.timezone || birthData.timezone}). Times below use {utc ? 'UTC' : 'your device timezone'}. Calendar contacts use the distance selected above. Conjunctions and optional aspect contacts are shown separately.</p>
        {data?.calendar_calculated && <><div className="mb-actions">{focus !== 'general' && <label><input type="checkbox" checked={relevantOnly} onChange={e => setRelevantOnly(e.target.checked)} />Only contacts with {focus} connections</label>}<label>Evidence<select value={type} onChange={e => setType(e.target.value)}><option value="all">All transit evidence</option><option value="conjunction">Conjunctions</option><option value="aspect">Aspects</option></select></label><label><input type="checkbox" checked={multiple} onChange={e => setMultiple(e.target.checked)} />Show overlapping transits</label><label><input type="checkbox" checked={utc} onChange={e => setUtc(e.target.checked)} />UTC</label></div>
          <h3>Dasha context · {dashas.length} intervals</h3>{dashas.map((r, i) => <article className="mb-card mb-card--small" key={`${r.point}-${i}`}><strong>{label(r.point)}</strong><p>{moment(r.start_at, utc)} → {moment(r.end_at, utc)}</p><p>{links(r.connections)}</p></article>)}{!dashas.length && <p>No matching dasha period in the selected dates.</p>}
          <h3>Potential transit windows · {events.length}</h3>{!events.length && <p>No matching contacts in the selected range and filters. This does not assess other astrological factors.</p>}
          {events.slice(0, visibleCount).map(r => <article className="mb-card" key={r.id}><div className="mb-card-title"><h4>{r.planet} → {label(r.point)}</h4><label><input type="checkbox" aria-label={`Export ${r.planet} ${r.point} ${r.kind}`} checked={exportIds.has(r.id)} onChange={e => setExportIds(previous => {
                    const n = new Set(previous);
                    e.target.checked ? n.add(r.id) : n.delete(r.id);
                    return n;
                  })} /> Export</label></div><p>{kind(r)}</p>{r.current_contact && <p className="mb-note">As of {moment(r.current_contact.as_of, utc)}: {r.current_contact.distance_degrees.toFixed(3)}° from this contact target · {r.current_contact.direction} · {r.current_contact.motion}{r.current_contact.within_selected_orb ? ' · Within selected distance' : ''}</p>}{focus !== 'general' && <div><strong>{focus[0].toUpperCase()+focus.slice(1)} connections</strong>{r.focus_evidence?.length ? r.focus_evidence.map(text => <p key={text}>{text}</p>) : <p>No direct house links under this focus rule. The contact remains available for review.</p>}{r.focus_dasha_overlaps?.map((d,i) => <p className="mb-note" key={i}>{moment(d.start_at,utc)} → {moment(d.end_at,utc)} · {focusLinks(d.connections)}</p>)}</div>}
            <div className="mb-actions">{onAsk && <button onClick={() => {onAsk(`Review this Bhrigu Bindu contact for ${focus}: ${r.planet}, aspect ${r.aspect_number}, window ${r.start_at} to ${r.end_at}. Exact passes: ${r.exact_passes.map(p => `${p.at} ${p.motion}`).join('; ') || 'none in this window'}. Natal BB: ${data.natal.points[0].position}, house ${data.natal.points[0].house}. Chart links: ${(r.focus_evidence || []).join('; ')}. Treat the contact as timing evidence and explain the actual chart connections.`);onClose();}}>Ask Tara about this contact</button>}<button onClick={() => openTransit(r,r.start_at)}>Open chart at window start</button>{r.exact_passes.map((pass,i) => <button key={pass.at} onClick={() => openTransit(r,pass.at)}>Open exact contact {i+1}</button>)}</div>
            {previewId === r.id && previewBusy && <p role="status">Calculating transit chart…</p>}{previewId === r.id && preview && <div><h4>Transit planets · {moment(preview.at,utc)}</h4><p className="mb-note">{preview.frame}. Bhrigu Bindu remains at {preview.bb_position}, house {preview.bb_house}.</p><div style={{maxWidth:420}}><ChartWidget key={preview.at} chartData={preview.chart} chartType="transit" highlightedPlanets={[r.planet]} selectedHouseNumber={preview.bb_house} deskMode /></div><button onClick={() => {setPreview(null);setPreviewId(null);}}>Close transit chart</button></div>}
<p className="mb-note">Sequence observed in this range: {r.sequence_motion} · Window {r.sequence_window_number} of {r.sequence_window_count}</p><p>{r.clipped_start ? 'Active at range start · ' : ''}{moment(r.start_at, utc)} → {moment(r.end_at, utc)}{r.clipped_end ? ' · Reaches range end' : ''}</p>
            {r.exact_passes.map((p, i) => <p key={p.at}>{r.midpoint_only ? 'Span midpoint' : 'Exact contact'} {i + 1}: {moment(p.at, utc)} · {p.motion}</p>)}{!r.exact_passes.length && <p>No exact {r.midpoint_only ? 'midpoint' : 'contact'} in this window; near-pass or clipped interval.</p>}
            <p className="mb-note">Other bodies contacting this point during part of the window: {r.concurrent_transits?.join(', ') || 'None'}. Each body is counted once.</p><p>{r.dasha_overlaps.length ? `${r.dasha_overlaps.length} dasha overlaps` : 'No linked dasha period'}</p>{r.dasha_overlaps.map((d, i) => <p className="mb-note" key={i}>{moment(d.start_at, utc)} → {moment(d.end_at, utc)} · {links(d.connections)}</p>)}
            <label className="mb-note-input">Observation / event review<textarea placeholder="Record an observation, including no notable event" value={notes[r.id] || ''} onChange={e => updateNote(r.id, e.target.value)} /></label>
          </article>)}
          {events.length > visibleCount && <button onClick={() => setVisibleCount(n => n + 40)}>Show more windows ({visibleCount} of {events.length} shown)</button>}
          <button disabled={!exportIds.size} onClick={() => download('AstroRoshni-BB.ics', makeCalendar((data.events || []).filter(r => exportIds.has(r.id))), 'text/calendar')}>Export selected windows ({exportIds.size})</button>
        </>}{!data?.calendar_calculated && !busy && <p>Calculate the calendar to resolve exact windows for these settings.</p>}
      </>}
      {data && tab === 'audit' && <><h3>Calculation audit</h3><dl>{Object.entries(data.audit).filter(([key]) => !['sources', 'limits'].includes(key)).map(([key, value]) => <React.Fragment key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{Array.isArray(value) ? value.join(', ') : String(value)}</dd></React.Fragment>)}</dl><p>{data.natal.source} · {data.natal.degree_semantics}</p>{data.audit.sources.map(s => <p key={s.url}><a href={s.url} target="_blank" rel="noreferrer">{s.title}</a></p>)}{data.audit.limits.map(text => <p key={text}>{text}</p>)}<p>Calculation version: {data.schema_version}. No medical or mortality grade is generated.</p></>}
      {noteError && <p role="alert">{noteError}</p>}
    </div>{data && <footer className="mb-footer"><button disabled={exporting} onClick={savePdf}>{exporting ? 'Preparing PDF…' : 'Save assessment PDF'}</button><button onClick={() => download('AstroRoshni-BB-audit.json', JSON.stringify(data, null, 2), 'application/json')}>Calculation data</button></footer>}
  </section></div>;
}
