import React, { useState } from 'react';
import { locationService } from '../../services/locationService';
export default function MuhuratSetup({ initial = {}, onSubmit }) {
  const [draft, setDraft] = useState({ allowed_start: '08:00', allowed_end: '18:00', minimum_duration_minutes: 15, personalized: false, ...initial });
  const [query, setQuery] = useState(''), [places, setPlaces] = useState([]), [error, setError] = useState(''), [busy, setBusy] = useState(false);
  const update = (key, value) => setDraft(old => ({ ...old, [key]: value }));
  const search = async () => { setBusy(true); setError(''); try { setPlaces(await locationService.searchPlaces(query)); } catch (_) { setError('Unable to find this city. Please try again.'); } finally { setBusy(false); } };
  const submit = e => { e.preventDefault(); if (!draft.location || !draft.event_type || !draft.start_date || !draft.end_date || draft.end_date < draft.start_date || draft.allowed_end <= draft.allowed_start || (Date.parse(draft.end_date) - Date.parse(draft.start_date)) / 86400000 >= 60) { setError('Choose an activity, event city, 1–60 days and valid available hours.'); return; } onSubmit(draft); };
  return <form onSubmit={submit}><p>Choose when to begin an activity. Dates and hours stay within your selection; you can refine them after the search.</p>
    <label>Activity<select required value={draft.event_type || ''} onChange={e => update('event_type', e.target.value)}><option value="">Choose activity</option>{[['vehicle','Vehicle purchase'],['home','Griha Pravesh'],['gold','Gold purchase'],['business','Business opening']].map(([id,label]) => <option key={id} value={id}>{label}</option>)}{draft.event_type && !['vehicle','home','gold','business'].includes(draft.event_type) && <option value={draft.event_type}>{draft.event_type} · limited engine coverage</option>}</select></label>
    <label>Event city<input value={query} onChange={e => { setQuery(e.target.value); setPlaces([]); }} placeholder="Search where the activity will happen" /></label>
    <button type="button" disabled={busy || query.trim().length < 3} onClick={search}>{busy ? 'Searching…' : 'Find city'}</button>
    {places.map(place => <button type="button" key={place.id || place.name} onClick={() => { update('location', { name: place.name, latitude: Number(place.latitude), longitude: Number(place.longitude), timezone: String(place.timezone || 'UTC') }); setPlaces([]); }}>{place.name}</button>)}
    {draft.location && <p>Selected: {draft.location.name}</p>}
    {[['check_time','Fixed time to check (optional)','time'],['start_date','From','date'],['end_date','Through','date'],['allowed_start','Available from','time'],['allowed_end','Available until','time']].map(([key,label,type]) => <label key={key}>{label}<input required={key !== 'check_time'} type={type} value={draft[key] || ''} onChange={e => update(key,e.target.value)} /></label>)}
    <label>Minimum window (minutes)<input type="number" min="5" max="120" required value={draft.minimum_duration_minutes} onChange={e => update('minimum_duration_minutes',Number(e.target.value))} /></label>
    <label><input type="checkbox" checked={draft.personalized} onChange={e => update('personalized',e.target.checked)} /> Include the selected profile’s natal suitability where supported</label>
    <p>Daylight windows only. Marriage and other activities may require rules our current engine does not cover.</p>
    {error && <p role="alert">{error}</p>}<button type="submit">Check Muhurat</button></form>;
}
