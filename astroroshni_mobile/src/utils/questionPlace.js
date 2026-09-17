import AsyncStorage from '@react-native-async-storage/async-storage';

const PLACE_KEY = 'prashna_question_place';

const asPlace = (latitude, longitude, name, source) => {
  const lat = parseFloat(latitude);
  const lon = parseFloat(longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
  return {
    latitude: lat,
    longitude: lon,
    name: String(name || 'Current location').trim() || 'Current location',
    source,
  };
};

const shortAddress = (address = {}, displayName = '') => {
  const city = address.city || address.town || address.village || address.municipality || address.county;
  const parts = [city, address.state, address.country].filter(Boolean);
  if (parts.length) return parts.join(', ');
  return displayName.split(',').slice(0, 3).join(',').trim() || 'Current location';
};

export async function loadSavedQuestionPlace() {
  try {
    const raw = await AsyncStorage.getItem(PLACE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return asPlace(parsed.latitude, parsed.longitude, parsed.name, parsed.source || 'saved');
  } catch {
    return null;
  }
}

export async function saveQuestionPlace(place) {
  const next = asPlace(place?.latitude, place?.longitude, place?.name, place?.source || 'manual');
  if (!next) return;
  try {
    await AsyncStorage.setItem(PLACE_KEY, JSON.stringify(next));
  } catch {
    // Ignore storage failures; the in-memory place still works for this session.
  }
}

async function reverseGeocode(latitude, longitude) {
  const response = await fetch(
    `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`,
    { headers: { 'User-Agent': 'AstroRoshni/1.0' } },
  );
  if (!response.ok) throw new Error('reverse-geocode');
  const data = await response.json();
  return asPlace(latitude, longitude, shortAddress(data.address, data.display_name), 'gps');
}

function getGpsCoords() {
  return new Promise((resolve, reject) => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      reject(new Error('unavailable'));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({
        latitude: pos.coords.latitude,
        longitude: pos.coords.longitude,
      }),
      reject,
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 120000 },
    );
  });
}

async function detectByGps() {
  const coords = await getGpsCoords();
  try {
    return await reverseGeocode(coords.latitude, coords.longitude);
  } catch {
    return asPlace(coords.latitude, coords.longitude, 'Current location', 'gps');
  }
}

async function detectByIp() {
  const response = await fetch('https://ipwho.is/');
  if (!response.ok) throw new Error('ip');
  const data = await response.json();
  if (data?.success === false) throw new Error('ip');
  const name = [data.city, data.region, data.country].filter(Boolean).join(', ');
  return asPlace(data.latitude, data.longitude, name, 'ip');
}

export async function detectQuestionPlace() {
  try {
    return await detectByGps();
  } catch {
    // GPS is often unavailable in the native app; city-level IP location is still
    // the place of asking, not the natal chart.
  }
  try {
    return await detectByIp();
  } catch {
    return null;
  }
}
