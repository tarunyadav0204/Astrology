import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { apiService } from '../../services/apiService';
import './MrityuBhagaWorkspace.css';
import ChartWidget from '../Charts/ChartWidget';
import { buildMrityuBhagaReport, printMrityuBhagaReport, ordinal } from '../../utils/mrityuBhagaExport';
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
const links = rows => rows.map(r => `${{
  mahadasha: 'MD',
  antardasha: 'AD',
  pratyantardasha: 'PD'
}[r.level]}: ${r.lord} (${r.relation === 'direct' ? 'own period' : 'sign ruler'})`).join(' · ');
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
const kind = row => row.kind === 'natal_mb_span' ? 'Passes through the Mrityu Bhaga range' : row.aspect_number === 1 ? 'Passes over the birth position' : `${ordinal(row.aspect_number)} aspect to the birth position`;
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
  return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//AstroRoshni//Mrityu Bhaga//EN', 'CALSCALE:GREGORIAN', ...events.flatMap(r => ['BEGIN:VEVENT', `UID:${r.id}:${r.start_at}@astroroshni.com`, `DTSTAMP:${icsDate(new Date())}`, `DTSTART:${icsDate(r.start_at)}`, `DTEND:${icsDate(r.end_at)}`, `SUMMARY:${r.planet} - ${label(r.point)} - ${kind(r)}`, 'DESCRIPTION:Potential activation evidence. Review natal conditions and dasha connections in AstroRoshni.', 'END:VEVENT']), 'END:VCALENDAR'].map(foldCalendarLine).join('\r\n');
}
export default function MrityuBhagaWorkspace({
  birthData,
  onAsk,
  onHighlight
}) {
  const [open, setOpen] = useState(false);
  return <><button type="button" className="parashari-desk-chip" onClick={() => setOpen(true)}>Mrityu Bhaga</button>{open && createPortal(<Workspace key={JSON.stringify(birthData)} birthData={birthData} onClose={() => {
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
    [orb, setOrb] = useState('1');
  const [filter, setFilter] = useState('all'),
    [type, setType] = useState('all'),
    [multiple, setMultiple] = useState(false),
    [direct, setDirect] = useState(false),
    [utc, setUtc] = useState(false),
    [sensitivity, setSensitivity] = useState(0),
    [checked, setChecked] = useState(false),
    [selected, setSelected] = useState(null);
  const [exportIds, setExportIds] = useState(new Set());
  const [showChart, setShowChart] = useState(() => window.innerWidth > 900);
  const noteKey = `mb-notes-v1:${JSON.stringify([birthData.date, birthData.time, birthData.latitude, birthData.longitude, birthData.calculation_profile])}`;
  const [notes, setNotes] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(noteKey) || '{}');
    } catch {
      return {};
    }
  });
  const [noteError, setNoteError] = useState('');
  const [visibleCount, setVisibleCount] = useState(40);
  useEffect(() => setVisibleCount(40), [filter, type, direct, multiple, data]);
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
    controller.current?.abort();
    const request = new AbortController();
    controller.current = request;
    setBusy(true);
    setError('');
    setExportIds(new Set());
    try {
      const result = await apiService.getMrityuBhagaWorkspace(birthData, {
        start_date: start,
        end_date: end,
        calendar,
        include_fast: fast,
        include_aspects: aspects,
        orb_degrees: Number(orb),
        birth_time_minutes: comparison
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
    return () => controller.current?.abort();
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
  const invalidate = fn => {
    controller.current?.abort();
    setBusy(false);
    setData(previous => previous ? {
      ...previous,
      calendar_calculated: false,
      events: [],
      dasha_activations: []
    } : previous);
    fn();
  };
  const events = (data?.events || []).filter(r => (!multiple || r.concurrent_transits?.length) && (filter === 'all' || r.point === filter) && (type === 'all' || r.kind === type) && (!direct || r.dasha_overlaps.some(d => d.connections.some(c => c.relation === 'direct'))));
  const dashas = (data?.dasha_activations || []).filter(r => (filter === 'all' || r.point === filter) && (!direct || r.connections.some(c => c.relation === 'direct')));
  const savePdf = async () => {
    if (exporting) return;
    setExporting(true);
    try {
      await printMrityuBhagaReport(buildMrityuBhagaReport(data, birthData, notes, events));
    } catch (e) {
      setError(`PDF export unavailable: ${e.message}`);
    } finally {
      setExporting(false);
    }
  };
  return <div className="mb-backdrop"><section className="mb-workspace" role="dialog" aria-modal="true" aria-labelledby="mb-title" ref={dialog} tabIndex={-1}>
    <header className="mb-header"><div><small>ASTROROSHNI · ASTROLOGER WORKSPACE</small><h2 id="mb-title">Mrityu Bhaga</h2><p>{birthData.name} · Natal assessment & activation calendar</p></div><button onClick={onClose} aria-label="Close Mrityu Bhaga">✕</button></header>
    <nav className="mb-tabs" aria-label="Workspace views">{['natal', 'calendar', 'audit'].map(t => <button key={t} aria-pressed={tab === t} onClick={() => setTab(t)}>{t === 'natal' ? 'Natal assessment' : t === 'calendar' ? 'Activation calendar' : 'Calculation audit'}</button>)}</nav>
    <div ref={content} className={`mb-scroll${tab === 'natal' && showChart ? ' mb-scroll--chart' : ''}`}>
      {error && <div role="alert" className="mb-error">{String(error)} <button onClick={() => load(tab === 'calendar')}>Retry</button></div>}
      {busy && <p role="status">{tab === 'calendar' ? 'Resolving transit crossings, stations and dasha overlaps…' : 'Calculating the natal assessment…'}</p>}
      {data?.natal.unavailable_points?.map(p => <p role="alert" className="mb-error" key={p.point}>Assessment incomplete: {p.point} could not be checked. {p.reason} Its absence is not a negative finding.</p>)}
      {data && tab === 'natal' && <><div className="mb-summary"><strong>{data.natal.affected_count ? `${data.natal.points.filter(p => p.is_mrityu_bhaga).map(p => label(p.point)).join(', ')} ${data.natal.affected_count === 1 ? 'is' : 'are'} in Mrityu Bhaga` : 'No Mrityu Bhaga found'}</strong><span>{data.natal.affected_count ? 'See the Mrityu Bhaga range and birth position below.' : 'None of the checked positions is inside its Mrityu Bhaga range.'}</span></div>
        <div className="mb-birth-review"><label>Check nearby birth times <select value={sensitivity} onChange={e => {
                setSensitivity(Number(e.target.value));
                load(false, Number(e.target.value));
              }}><option value={0}>Recorded time only</option>{[5, 10, 15].map(n => <option key={n} value={n}>{n} min earlier / later</option>)}</select></label>{data.birth_time_comparison?.map(r => <p key={r.offset_minutes}>{r.offset_minutes > 0 ? '+' : ''}{r.offset_minutes} min: {r.affected_points.map(label).join(', ') || 'No Mrityu Bhaga found'}<small> · Lagna {r.lagna_position} · Gulika {r.gulika_position}</small></p>)}<p className="mb-note">{sensitivity ? `Checks the recorded time, ${sensitivity} minutes earlier and ${sensitivity} minutes later. Times in between are not checked.` : 'Choose an earlier and later birth time to see whether the result changes.'}</p></div><button className="mb-chart-toggle" onClick={() => setShowChart(!showChart)}>{showChart ? 'Hide linked chart' : 'Show linked chart'}</button>{showChart && <div className="mb-chart-preview"><ChartWidget chartData={data.natal_chart} birthData={birthData} chartType="lagna" highlightedPlanets={selected ? [selected, data.natal.points.find(p => p.point === selected)?.dispositor].filter(Boolean) : data.natal.points.filter(p => p.is_mrityu_bhaga).map(p => p.point)} selectedHouseNumber={data.natal.points.find(p => p.point === selected)?.house} deskMode /></div>}{data.natal.affected_count === 0 && <p>None of the checked planets or points is in Mrityu Bhaga, so there are no Mrityu Bhaga dates to show.</p>}
        {data.natal.points.filter(p => p.is_mrityu_bhaga).map(p => <article className={`mb-card${selected === p.point ? ' is-selected' : ''}`} key={p.point}>
          <h3><button className="mb-text-button" onClick={() => {
                setSelected(p.point);
                onHighlight?.(p.point === 'Ascendant' ? [p.dispositor] : [p.point, p.dispositor]);
              }}>{label(p.point)} is in Mrityu Bhaga</button> <small>House {p.house}</small></h3><p>Mrityu Bhaga range: <strong>{p.degree_span_start}°–{p.degree_span_end}° {p.sign_name}</strong></p><p className="mb-position">{label(p.point)}’s position: {p.position}</p><p>Houses ruled: {p.houses_ruled.join(', ') || 'None'}</p>
          <dl><dt>Sign condition & motion</dt><dd>{p.dignity || 'Not applicable'}{p.retrograde === true ? ' · Retrograde' : p.retrograde === false ? ' · Direct' : ''}</dd><dt>Planet strength (Shadbala)</dt><dd>{strength(p.strength)}</dd><dt>Combustion</dt><dd>{p.combustion.applicable ? p.combustion.is_combust ? 'Combust' : 'Not combust' : 'Not applicable'}</dd><dt>Sign ruler</dt><dd>{p.dispositor} · {p.dispositor_position} · {p.dispositor_dignity || 'Unspecified'}<br />{strength(p.dispositor_strength)}</dd><dt>Nakshatra</dt><dd>{p.nakshatra || 'Unavailable'}{p.nakshatra_lord ? ` · ${p.nakshatra_lord}` : ''}</dd><dt>Planet connections</dt><dd>{p.relationships.map(r => `${r.planet}: ${r.relation === 'same_sign' ? 'in the same sign' : `${ordinal(r.aspect_number)} aspect`}`).join(' · ') || 'None'}</dd><dt>Other charts</dt><dd>{Object.entries(p.divisional_placements).map(([d, v]) => `${d}: ${v.sign}, H${v.house}`).join(' · ')}</dd></dl>
          {p.birth_time_sensitive && <p className="mb-note">A small change in birth time can change this result. Please check the birth time.</p>}
          <p className="mb-note">Dasha at the selected start date: {data.dasha_activations.filter(r => r.point === p.point && r.start_at === data.range.start_at).map(r => links(r.connections)).join(' · ') || 'No matching dasha period'}</p>
          <div className="mb-actions"><button onClick={() => {
                setFilter(p.point);
                setTab('calendar');
              }}>View activation dates</button>{onAsk && <button onClick={() => {
                onAsk(`Analyze ${label(p.point)} in natal Mrityu Bhaga at ${p.position}, H${p.house}. Assess its dispositor ${p.dispositor}, strength, aspects and dasha activation, separating calculated facts from interpretation.`);
                onClose();
              }}>Ask Tara about this finding</button>}</div>
          <label className="mb-note-input">Astrologer notes · saved on this device<textarea value={notes[p.point] || ''} onChange={e => updateNote(p.point, e.target.value)} /></label>
        </article>)}
        <button className="mb-all-points" onClick={() => setChecked(!checked)} aria-expanded={checked}>All {data.natal.points.length} points checked</button>{checked && <div className="mb-table-wrap"><table><thead><tr><th>Point</th><th>Birth position</th><th>Mrityu Bhaga range</th><th>Result</th></tr></thead><tbody>{data.natal.points.map(p => <tr key={p.point}><td>{label(p.point)}</td><td>{p.position}</td><td>{p.degree_span_start}°–{p.degree_span_end}°</td><td>{p.is_mrityu_bhaga ? 'In Mrityu Bhaga' : 'Not in Mrityu Bhaga'}</td></tr>)}</tbody></table></div>}
      </>}
      {tab === 'calendar' && <><form className="mb-controls" onSubmit={e => {
            e.preventDefault();
            load(true);
          }}><label>From<input type="date" required value={start} onChange={e => invalidate(() => setStart(e.target.value))} /></label><label>Through<input type="date" required min={start} value={end} onChange={e => invalidate(() => setEnd(e.target.value))} /></label><label>Contact distance<select value={orb} onChange={e => invalidate(() => setOrb(e.target.value))}>{['0.5', '1', '2', '3'].map(v => <option key={v} value={v}>±{v}°</option>)}</select></label><button disabled={busy}>Calculate calendar</button></form>
        <div className="mb-actions">{[30, 90, 365].map(n => <button key={n} onClick={() => invalidate(() => setEnd(plus(start, n - 1)))}>{n} days</button>)}<label><input type="checkbox" checked={fast} onChange={e => invalidate(() => setFast(e.target.checked))} />Include Sun, Moon, Mercury, Venus</label><label><input type="checkbox" checked={aspects} onChange={e => invalidate(() => setAspects(e.target.checked))} />Include aspect degree contacts</label></div>
        <p className="mb-note">Dates use the birth timezone ({data?.range.timezone || birthData.timezone}). Times below use {utc ? 'UTC' : 'your device timezone'}. Birth positions are checked against the exact Mrityu Bhaga range. Calendar contacts use the distance selected above.</p>
        {data?.calendar_calculated && <><div className="mb-actions"><label>Point<select value={filter} onChange={e => setFilter(e.target.value)}><option value="all">All affected points</option>{data.natal.points.filter(p => p.is_mrityu_bhaga).map(p => <option key={p.point}>{p.point}</option>)}</select></label><label>Evidence<select value={type} onChange={e => setType(e.target.value)}><option value="all">All transit evidence</option><option value="natal_contact">Birth-position contacts</option><option value="natal_mb_span">Mrityu Bhaga range crossings</option></select></label><label><input type="checkbox" checked={multiple} onChange={e => setMultiple(e.target.checked)} />Show overlapping transits</label><label><input type="checkbox" checked={direct} onChange={e => setDirect(e.target.checked)} />Only during the planet’s own dasha</label><label><input type="checkbox" checked={utc} onChange={e => setUtc(e.target.checked)} />UTC</label></div>
          <h3>Dasha activation · {dashas.length} intervals</h3>{dashas.map((r, i) => <article className="mb-card mb-card--small" key={`${r.point}-${i}`}><strong>{label(r.point)}</strong><p>{moment(r.start_at, utc)} → {moment(r.end_at, utc)}</p><p>{links(r.connections)}</p></article>)}{!dashas.length && <p>No matching dasha period in the selected dates.</p>}
          <h3>Potential transit windows · {events.length}</h3>{!events.length && <p>No matching contacts in the selected range and filters. This does not assess other astrological factors.</p>}
          {events.slice(0, visibleCount).map(r => <article className="mb-card" key={r.id}><div className="mb-card-title"><h4>{r.planet} → {label(r.point)}</h4><label><input type="checkbox" aria-label={`Export ${r.planet} ${r.point} ${r.kind}`} checked={exportIds.has(r.id)} onChange={e => setExportIds(previous => {
                    const n = new Set(previous);
                    e.target.checked ? n.add(r.id) : n.delete(r.id);
                    return n;
                  })} /> Export</label></div><p>{kind(r)}</p><p className="mb-note">Sequence observed in this range: {r.sequence_motion} · Window {r.sequence_window_number} of {r.sequence_window_count}</p><p>{r.clipped_start ? 'Active at range start · ' : ''}{moment(r.start_at, utc)} → {moment(r.end_at, utc)}{r.clipped_end ? ' · Reaches range end' : ''}</p>
            {r.exact_passes.map((p, i) => <p key={p.at}>{r.midpoint_only ? 'Span midpoint' : 'Exact contact'} {i + 1}: {moment(p.at, utc)} · {p.motion}</p>)}{!r.exact_passes.length && <p>No exact {r.midpoint_only ? 'midpoint' : 'contact'} in this window; near-pass or clipped interval.</p>}
            <p className="mb-note">Other bodies contacting this point during part of the window: {r.concurrent_transits?.join(', ') || 'None'}. Same-body span and longitude rows count once.</p><p>{r.dasha_overlaps.length ? `${r.dasha_overlaps.length} dasha overlaps` : 'No direct/dispositor dasha overlap'}</p>{r.dasha_overlaps.map((d, i) => <p className="mb-note" key={i}>{moment(d.start_at, utc)} → {moment(d.end_at, utc)} · {links(d.connections)}</p>)}
            <label className="mb-note-input">Observation / event review<textarea placeholder="Record an observation, including no notable event" value={notes[r.id] || ''} onChange={e => updateNote(r.id, e.target.value)} /></label>
          </article>)}
          {events.length > visibleCount && <button onClick={() => setVisibleCount(n => n + 40)}>Show more windows ({visibleCount} of {events.length} shown)</button>}
          <button disabled={!exportIds.size} onClick={() => download('AstroRoshni-MB.ics', makeCalendar((data.events || []).filter(r => exportIds.has(r.id))), 'text/calendar')}>Export selected windows ({exportIds.size})</button>
        </>}{!data?.calendar_calculated && !busy && <p>Calculate the calendar to resolve exact windows for these settings.</p>}
      </>}
      {data && tab === 'audit' && <><h3>Calculation audit</h3><dl>{Object.entries(data.audit).filter(([key]) => !['sources', 'limits'].includes(key)).map(([key, value]) => <React.Fragment key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{Array.isArray(value) ? value.join(', ') : String(value)}</dd></React.Fragment>)}</dl><p>{data.natal.source} · {data.natal.degree_semantics}</p>{data.audit.sources.map(s => <p key={s.url}><a href={s.url} target="_blank" rel="noreferrer">{s.title}</a></p>)}{data.audit.limits.map(text => <p key={text}>{text}</p>)}<p>Calculation version: {data.schema_version}. No medical or mortality grade is generated.</p></>}
      {noteError && <p role="alert">{noteError}</p>}
    </div>{data && <footer className="mb-footer"><button disabled={exporting} onClick={savePdf}>{exporting ? 'Preparing PDF…' : 'Save assessment PDF'}</button><button onClick={() => download('AstroRoshni-MB-audit.json', JSON.stringify(data, null, 2), 'application/json')}>Calculation data</button></footer>}
  </section></div>;
}
