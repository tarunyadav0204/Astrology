import React, { useState, useEffect } from 'react';
import { selectedRitualValue, initializeMuhuratDraft } from '../../utils/festivalPujaSelection';
import festivalCatalog from '../../data/festivalPujaCatalog.json';
import { locationService } from '../../services/locationService';
export default function MuhuratSetup({ initial = {}, onSubmit }) {
  const [draft, setDraft] = useState(() => initializeMuhuratDraft(initial, festivalCatalog));
  const initialKey = JSON.stringify(initial);
  useEffect(() => { setDraft(initializeMuhuratDraft(JSON.parse(initialKey), festivalCatalog)); }, [initialKey]);
  const festival = draft.event_type === 'festival_puja' || Boolean(draft.festival_id);
  const selectedFestival = festivalCatalog.find(item => item.id === draft.festival_id);
  const ritualValue = selectedRitualValue(selectedFestival, draft.ritual);
  const ritualOptions = selectedFestival?.ritual_options || [];
  const [query, setQuery] = useState(''), [places, setPlaces] = useState([]), [error, setError] = useState(''), [busy, setBusy] = useState(false);
  const update = (key, value) => setDraft(old => ({ ...old, [key]: value }));
  const search = async () => { setBusy(true); setError(''); try { setPlaces(await locationService.searchPlaces(query)); } catch (_) { setError('Unable to find this city. Please try again.'); } finally { setBusy(false); } };
  const submit = e => { e.preventDefault(); if (!draft.location || !draft.event_type || !draft.start_date || !draft.end_date || draft.end_date < draft.start_date || draft.allowed_end <= draft.allowed_start || (Date.parse(draft.end_date) - Date.parse(draft.start_date)) / 86400000 >= (festival ? 366 : 60) || (festival && (!draft.festival_id || Number((draft.start_date || '').slice(0,4)) < 1900 || Number((draft.start_date || '').slice(0,4)) > 2100))) { setError(festival ? 'Choose a festival, event city and valid year (1900–2100).' : 'Choose an activity, event city, 1–60 days and valid available hours.'); return; } onSubmit(draft); };
  return <form onSubmit={submit}><p>{festival ? 'Confirm the festival, year and city where you will perform the puja. Its traditional time is calculated locally; kundli checks do not move the festival.' : 'Choose when to begin an activity. Dates and hours stay within your selection; you can refine them after the search.'}</p>
    <label>Activity<select required value={draft.event_type || ''} onChange={e => setDraft(old => ({ ...old, event_type:e.target.value, festival_id:null, ritual:null, ...(e.target.value === 'festival_puja' ? {allowed_start:'00:00', allowed_end:'23:59',festival_year:new Date().getFullYear(),start_date:`${new Date().getFullYear()}-01-01`,end_date:`${new Date().getFullYear()}-12-31`} : {}) }))}><option value="">Choose activity</option>{[['vehicle','Vehicle purchase'],['home','Griha Pravesh'],['gold','Gold purchase'],['business','Business opening'],['festival_puja','Festival puja / vrat']].map(([id,label]) => <option key={id} value={id}>{label}</option>)}{draft.event_type && !['vehicle','home','gold','business','festival_puja'].includes(draft.event_type) && <option value={draft.event_type}>{draft.event_type}</option>}</select></label>
    {festival && <><label>Festival<select required value={draft.festival_id || ''} onChange={e => setDraft(old => ({...old,festival_id:e.target.value,ritual:null}))}><option value="">Choose festival</option>{festivalCatalog.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label>Year<select aria-label="Year" required value={Number(draft.festival_year || (draft.start_date || '').slice(0,4)) || new Date().getFullYear()} onChange={e => { const year=Number(e.target.value); setDraft(old => ({...old,festival_year:year,start_date:`${year}-01-01`,end_date:`${year}-12-31`})); }}>
        {Array.from({length:201},(_,index)=>1900+index).map(year=><option key={year} value={year}>{year}</option>)}
      </select></label>
      {selectedFestival && !selectedFestival.ritual && <p>Puja timings for this festival aren’t available yet.</p>}
      <label>Ritual<select value={ritualValue} onChange={e => update('ritual',e.target.value || null)}>
        {!ritualOptions.length && <option value="">{selectedFestival ? 'No puja timings available' : 'Choose a festival first'}</option>}
        {ritualOptions.map(item => <option key={item.value} value={item.value} disabled={!item.supported}>{item.label}{item.supported ? '' : ' · timing not yet available'}</option>)}
        {ritualValue && !ritualOptions.some(item => item.value === ritualValue) && <option value={ritualValue}>{draft.ritual}</option>}
      </select></label></>}
    <label>Event city<input value={query} onChange={e => { setQuery(e.target.value); setPlaces([]); }} placeholder="Search where the activity will happen" /></label>
    <button type="button" disabled={busy || query.trim().length < 3} onClick={search}>{busy ? 'Searching…' : 'Find city'}</button>
    {places.map(place => <button type="button" key={place.id || place.name} onClick={() => { update('location', { name: place.name, latitude: Number(place.latitude), longitude: Number(place.longitude), timezone: String(place.timezone || 'UTC') }); setPlaces([]); }}>{place.name}</button>)}
    {draft.location && <p>Selected: {draft.location.name}</p>}
    {(!festival ? [['check_time','Fixed time to check (optional)','time'],['start_date','From','date'],['end_date','Through','date'],['allowed_start','Available from','time'],['allowed_end','Available until','time']] : []).map(([key,label,type]) => <label key={key}>{label}<input required={key !== 'check_time'} type={type} value={draft[key] || ''} onChange={e => update(key,e.target.value)} /></label>)}
    {!festival && <label>Minimum window (minutes)<input type="number" min="5" max="120" required value={draft.minimum_duration_minutes} onChange={e => update('minimum_duration_minutes',Number(e.target.value))} /></label>}
    <label><input type="checkbox" checked={draft.personalized} onChange={e => update('personalized',e.target.checked)} /> Include the selected profile’s natal suitability where supported</label>
    <p>{festival ? 'Choose the city where you will perform the puja. Timings are calculated for that location.' : 'Daylight windows only. Marriage and other activities may require rules our current engine does not cover.'}</p>
    {error && <p role="alert">{error}</p>}<button type="submit">Check Muhurat</button></form>;
}
