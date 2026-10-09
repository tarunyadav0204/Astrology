import React, { useState } from 'react';
import { locationService } from '../../services/locationService';
export default function PrashnaSetup({ onSelect }) {
  const [query, setQuery] = useState(''), [places, setPlaces] = useState([]), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const search = async () => {
    setBusy(true); setError('');
    try { setPlaces(await locationService.searchPlaces(query)); }
    catch (_) { setError('Unable to find this city. Please try again.'); }
    finally { setBusy(false); }
  };
  return <div><p>Start with Parashari. KP and Tajika are available when useful. The question chart is fixed when you send your question.</p>
    <p>Choose the city where you are asking the question.</p>
    <label>Current city<input value={query} onChange={e => { setQuery(e.target.value); setPlaces([]); }} placeholder="Search your current city" /></label>
    <button disabled={busy || query.trim().length < 3} onClick={search}>{busy ? 'Searching…' : 'Find city'}</button>
    {error && <p role="alert">{error}</p>}
    {places.map(place => <button key={place.id} className="chat-memory-fact" onClick={() => onSelect(place)}>{place.name}</button>)}
  </div>;
}
