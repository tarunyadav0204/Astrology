import { API_BASE_URL } from '../utils/constants';
import locationCache from './locationCache';

const photonFallback = async (query) => {
  try {
    const url = `https://photon.komoot.io/api/?q=${encodeURIComponent(query)}&limit=10`;
    const response = await fetch(url);
    const json = await response.json();
    const data = json.features || [];
    const timestamp = Date.now();
    return data.map((item, index) => {
      const coords = item.geometry?.coordinates || [0, 0];
      const properties = item.properties || {};
      const parts = [];
      const city = properties.city || properties.name;
      const state = properties.state;
      const country = properties.country;
      if (city) parts.push(city);
      if (state && state !== city) parts.push(state);
      if (country) parts.push(country);
      return {
        id: `photon_${timestamp}_${index}`,
        name: parts.length > 0 ? parts.join(', ') : properties.name || 'Unknown',
        latitude: coords[1],
        longitude: coords[0],
        source: 'photon',
      };
    }).filter((place) => Number.isFinite(place.latitude) && Number.isFinite(place.longitude));
  } catch (error) {
    console.warn('Photon place search failed:', error?.message || error);
    return [];
  }
};

export async function searchPlaces(query) {
  const queryTrimmed = (query || '').trim();
  if (queryTrimmed.length < 2) return [];

  const [googleSuggestions, cacheResults] = await Promise.all([
    (async () => {
      try {
        const autocompleteUrl = `${API_BASE_URL}/api/places/autocomplete?q=${encodeURIComponent(queryTrimmed)}`;
        const res = await fetch(autocompleteUrl, { method: 'GET' });
        if (!res.ok) return [];
        const data = await res.json();
        const list = data.suggestions || [];
        const timestamp = Date.now();
        return list.map((suggestion, index) => ({
          id: `google_${timestamp}_${index}`,
          name: suggestion.description || '',
          place_id: suggestion.place_id,
          source: 'google',
          latitude: null,
          longitude: null,
        })).filter((place) => place.name);
      } catch (error) {
        console.warn('Places autocomplete failed:', error?.message || error);
        return [];
      }
    })(),
    locationCache.searchLocations(queryTrimmed, photonFallback),
  ]);

  const combined = [...googleSuggestions];
  for (const place of cacheResults) {
    if (!combined.some((item) => (item.name || '').trim() === (place.name || '').trim())) {
      combined.push({ ...place, source: place.source || 'cache' });
    }
    if (combined.length >= 15) break;
  }
  return combined.slice(0, 15);
}

export async function resolvePlace(place) {
  if (!place) return null;

  if (place.place_id && (place.latitude == null || place.longitude == null)) {
    try {
      const detailsUrl = `${API_BASE_URL}/api/places/details?place_id=${encodeURIComponent(place.place_id)}`;
      const res = await fetch(detailsUrl, { method: 'GET' });
      if (res.ok) {
        const data = await res.json();
        const latitude = parseFloat(data.latitude);
        const longitude = parseFloat(data.longitude);
        if (Number.isFinite(latitude) && Number.isFinite(longitude)) {
          return {
            name: data.name || data.formattedAddress || place.name,
            latitude,
            longitude,
            source: place.source || 'google',
          };
        }
      }
    } catch (error) {
      console.warn('Place details fetch failed:', error?.message || error);
    }
  }

  const latitude = parseFloat(place.latitude);
  const longitude = parseFloat(place.longitude);
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null;

  return {
    name: place.name,
    latitude,
    longitude,
    source: place.source || 'manual',
  };
}
