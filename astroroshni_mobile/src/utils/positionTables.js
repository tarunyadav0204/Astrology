const SIGN_NAMES = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
];

const SIGN_ABBR = ['Ar', 'Ta', 'Ge', 'Cn', 'Le', 'Vi', 'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi'];

const SIGN_LORDS = [
  'Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury',
  'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter',
];

const NAKSHATRAS = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
  'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
  'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
  'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
  'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
];

const NAK_ABBR = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
  'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'P.Phal', 'U.Phal',
  'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
  'Mula', 'P.Ashadha', 'U.Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
  'P.Bhadra', 'U.Bhadra', 'Revati',
];

const NAKSHATRA_LORDS = [
  'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
  'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
  'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
];

const PLANET_ORDER = [
  'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi',
];

const TENANT_PLANETS = [
  'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu',
];

const PLANET_ABBR = {
  Lagna: 'Lg',
  Sun: 'Su',
  Moon: 'Mo',
  Mars: 'Ma',
  Mercury: 'Me',
  Jupiter: 'Ju',
  Venus: 'Ve',
  Saturn: 'Sa',
  Rahu: 'Ra',
  Ketu: 'Ke',
  Gulika: 'Gu',
  Mandi: 'Md',
  InduLagna: 'IL',
};

const KARAKA_ABBR = {
  Atmakaraka: 'AK',
  Amatyakaraka: 'AmK',
  Bhratrukaraka: 'BK',
  Matrukaraka: 'MK',
  Pitrikaraka: 'PiK',
  Putrakaraka: 'PK',
  Gnatikaraka: 'GK',
  Darakaraka: 'DK',
};

const EXALTATION_SIGNS = { Sun: 0, Moon: 1, Mars: 9, Mercury: 5, Jupiter: 3, Venus: 11, Saturn: 6 };
const DEBILITATION_SIGNS = { Sun: 6, Moon: 7, Mars: 3, Mercury: 11, Jupiter: 9, Venus: 5, Saturn: 0 };
const OWN_SIGNS = {
  Sun: [4], Moon: [3], Mars: [0, 7], Mercury: [2, 5], Jupiter: [8, 11], Venus: [1, 6], Saturn: [9, 10],
};
const MOOLATRIKONA_RANGES = {
  Sun: { sign: 4, start: 0, end: 20 },
  Moon: { sign: 1, start: 4, end: 30 },
  Mars: { sign: 0, start: 0, end: 12 },
  Mercury: { sign: 5, start: 16, end: 20 },
  Jupiter: { sign: 8, start: 0, end: 10 },
  Venus: { sign: 6, start: 0, end: 15 },
  Saturn: { sign: 10, start: 0, end: 20 },
};

const COMBUSTION_ORBS = {
  Moon: 12,
  Mars: 17,
  Mercury: 14,
  Jupiter: 11,
  Venus: 10,
  Saturn: 15,
};

export function normLon(lon) {
  return ((Number(lon) % 360) + 360) % 360;
}

export function fmtDeg(deg) {
  const n = Number(deg);
  if (!Number.isFinite(n)) return '—';
  const wrapped = ((n % 30) + 30) % 30;
  const d = Math.floor(wrapped);
  const m = Math.floor((wrapped - d) * 60);
  return `${d}°${String(m).padStart(2, '0')}'`;
}

export function houseOf(sign, lagnaSign) {
  if (typeof sign !== 'number' || typeof lagnaSign !== 'number') return null;
  return ((sign - lagnaSign + 12) % 12) + 1;
}

export function nakshatraIndex(lon) {
  return Math.floor(normLon(lon) / (360 / 27)) % 27;
}

export function nakshatraOf(lon) {
  return NAKSHATRAS[nakshatraIndex(lon)] || '—';
}

export function nakshatraAbbr(lon) {
  return NAK_ABBR[nakshatraIndex(lon)] || '—';
}

export function padaOf(lon) {
  return Math.floor((normLon(lon) % (360 / 27)) / (360 / 108)) + 1;
}

export function nakshatraLordOf(lon) {
  return NAKSHATRA_LORDS[nakshatraIndex(lon)] || '—';
}

export function getPlanetDignity(planet, sign, degree) {
  if (EXALTATION_SIGNS[planet] === sign) return { key: 'ex', label: 'Exalted', short: 'Ex' };
  if (DEBILITATION_SIGNS[planet] === sign) return { key: 'db', label: 'Debilitated', short: 'Db' };
  const moola = MOOLATRIKONA_RANGES[planet];
  if (
    moola
    && sign === moola.sign
    && degree != null
    && Number.isFinite(Number(degree))
    && Number(degree) >= moola.start
    && Number(degree) <= moola.end
  ) {
    return { key: 'mt', label: 'Moolatrikona', short: 'MT' };
  }
  if (OWN_SIGNS[planet]?.includes(sign)) return { key: 'own', label: 'Own', short: 'Own' };
  return null;
}

export function navamsaSign(longitude) {
  const lon = normLon(longitude);
  const sign = Math.floor(lon / 30);
  const navamsaPart = Math.floor((lon % 30) / (30 / 9));
  if ([0, 3, 6, 9].includes(sign)) return (sign + navamsaPart) % 12;
  if ([1, 4, 7, 10].includes(sign)) return ((sign + 8) + navamsaPart) % 12;
  return ((sign + 4) + navamsaPart) % 12;
}

export function isVargottama(sign, longitude) {
  if (typeof sign !== 'number' || !Number.isFinite(Number(longitude))) return false;
  return sign === navamsaSign(longitude);
}

export function isMooltrikona(planet, sign, degree) {
  const range = MOOLATRIKONA_RANGES[planet];
  return Boolean(
    range
    && sign === range.sign
    && degree != null
    && Number.isFinite(Number(degree))
    && Number(degree) >= range.start
    && Number(degree) <= range.end
  );
}

function angularDistance(a, b) {
  let distance = Math.abs(normLon(a) - normLon(b));
  if (distance > 180) distance = 360 - distance;
  return distance;
}

export function combustSet(chartData) {
  const sunLon = longitudeOf(chartData?.planets?.Sun);
  if (sunLon == null) return new Set();
  const set = new Set();
  Object.entries(chartData?.planets || {}).forEach(([planet, data]) => {
    const orb = COMBUSTION_ORBS[planet];
    if (!orb) return;
    const lon = longitudeOf(data);
    if (lon == null) return;
    if (angularDistance(lon, sunLon) <= orb) set.add(planet);
  });
  return set;
}

export function longitudeOf(data) {
  if (data == null) return null;
  if (typeof data === 'number' && Number.isFinite(data)) return data;
  if (typeof data.longitude === 'number' && Number.isFinite(data.longitude)) return data.longitude;
  if (typeof data.sign === 'number' && Number.isFinite(Number(data.degree))) {
    return data.sign * 30 + Number(data.degree);
  }
  return null;
}

export function lagnaSignOf(chartData) {
  if (typeof chartData?.houses?.[0]?.sign === 'number') return chartData.houses[0].sign;
  const asc = longitudeOf(chartData?.ascendant) ?? longitudeOf(chartData?.houses?.[0]);
  if (asc == null) return 0;
  return Math.floor(normLon(asc) / 30) % 12;
}

export function karakaByPlanet(karakas) {
  const map = {};
  if (!karakas || typeof karakas !== 'object') return map;
  Object.entries(karakas).forEach(([karaka, value]) => {
    const planet = typeof value === 'string' ? value : value?.planet || value?.name;
    if (planet) map[planet] = KARAKA_ABBR[karaka] || karaka;
  });
  return map;
}

function planetAbbr(name) {
  return PLANET_ABBR[name] || String(name).slice(0, 2);
}

function lordAbbr(lord) {
  return PLANET_ABBR[lord] || String(lord).slice(0, 2);
}

export function buildPlanetRows(chartData, karakas) {
  const planets = chartData?.planets;
  if (!planets) return [];
  const lagnaSign = lagnaSignOf(chartData);
  const ck = karakaByPlanet(karakas);
  const combust = combustSet(chartData);
  const rows = [];

  const ascLon = longitudeOf(chartData?.ascendant) ?? longitudeOf(chartData?.houses?.[0]);
  if (ascLon != null) {
    const sign = Math.floor(normLon(ascLon) / 30) % 12;
    rows.push({
      name: 'Lagna',
      abbr: 'Lg',
      ck: '—',
      sign,
      signAbbr: SIGN_ABBR[sign],
      signName: SIGN_NAMES[sign],
      lord: SIGN_LORDS[sign],
      lordAbbr: lordAbbr(SIGN_LORDS[sign]),
      house: 1,
      degree: fmtDeg(normLon(ascLon) % 30),
      nakshatra: nakshatraOf(ascLon),
      nakAbbr: nakshatraAbbr(ascLon),
      pada: padaOf(ascLon),
      nakLord: nakshatraLordOf(ascLon),
      longitude: normLon(ascLon),
      retro: false,
      combust: false,
      vargottama: isVargottama(sign, ascLon),
      dignity: null,
    });
  }

  PLANET_ORDER.forEach((name) => {
    const data = planets[name];
    if (!data || typeof data.sign !== 'number') return;
    const lon = longitudeOf(data);
    const degree = typeof data.degree === 'number' ? data.degree : (lon != null ? normLon(lon) % 30 : null);
    rows.push({
      name,
      abbr: planetAbbr(name),
      ck: ck[name] || '—',
      sign: data.sign,
      signAbbr: SIGN_ABBR[data.sign] || '—',
      signName: SIGN_NAMES[data.sign] || '—',
      lord: SIGN_LORDS[data.sign],
      lordAbbr: lordAbbr(SIGN_LORDS[data.sign]),
      house: typeof data.house === 'number' ? data.house : houseOf(data.sign, lagnaSign),
      degree: fmtDeg(degree),
      nakshatra: lon != null ? nakshatraOf(lon) : '—',
      nakAbbr: lon != null ? nakshatraAbbr(lon) : '—',
      pada: lon != null ? padaOf(lon) : '—',
      nakLord: lon != null ? nakshatraLordOf(lon) : '—',
      longitude: lon,
      retro: !!data.retrograde && name !== 'Rahu' && name !== 'Ketu',
      combust: combust.has(name),
      vargottama: lon != null && isVargottama(data.sign, lon),
      dignity: getPlanetDignity(name, data.sign, degree),
    });
  });

  return rows;
}

export function buildHouseRows(chartData) {
  const lagnaSign = lagnaSignOf(chartData);
  const tenantsByHouse = {};
  TENANT_PLANETS.forEach((name) => {
    const data = chartData?.planets?.[name];
    if (!data) return;
    const h = typeof data.house === 'number' ? data.house : houseOf(data.sign, lagnaSign);
    if (!h) return;
    if (!tenantsByHouse[h]) tenantsByHouse[h] = [];
    const retro = !!(data.retrograde && name !== 'Rahu' && name !== 'Ketu');
    tenantsByHouse[h].push({
      name,
      retro,
      mark: retro ? `${planetAbbr(name)}(R)` : planetAbbr(name),
    });
  });

  return Array.from({ length: 12 }, (_, i) => {
    const house = i + 1;
    const sign = chartData?.houses?.[i]?.sign ?? ((lagnaSign + i) % 12);
    const lord = SIGN_LORDS[sign];
    const lordData = chartData?.planets?.[lord];
    const lordHouse = lordData
      ? (typeof lordData.house === 'number' ? lordData.house : houseOf(lordData.sign, lagnaSign))
      : null;
    const lordDegree = typeof lordData?.degree === 'number'
      ? lordData.degree
      : (longitudeOf(lordData) != null ? normLon(longitudeOf(lordData)) % 30 : null);
    const dignity = lordData && typeof lordData.sign === 'number'
      ? getPlanetDignity(lord, lordData.sign, lordDegree)
      : null;
    return {
      house,
      sign,
      signAbbr: SIGN_ABBR[sign] || '—',
      signName: SIGN_NAMES[sign] || '—',
      lord,
      lordAbbr: lordAbbr(lord),
      lordHouse: lordHouse || '—',
      dignity,
      occupants: (tenantsByHouse[house] || []).map((person) => person.mark).join(' '),
      occupantList: tenantsByHouse[house] || [],
    };
  });
}

export function buildNakshatraRows(planetRows) {
  const grouped = new Map();
  planetRows.forEach((row) => {
    if (row.nakshatra === '—' || row.pada === '—') return;
    const key = nakshatraIndex(row.longitude);
    if (!grouped.has(key)) {
      grouped.set(key, {
        index: key,
        nakshatra: NAKSHATRAS[key],
        nakAbbr: NAK_ABBR[key],
        lord: NAKSHATRA_LORDS[key],
        lordAbbr: lordAbbr(NAKSHATRA_LORDS[key]),
        occupants: [],
        people: [],
      });
    }
    const mark = `${row.abbr}·${row.pada}${row.retro ? 'R' : ''}`;
    grouped.get(key).occupants.push(mark);
    grouped.get(key).people.push({
      name: row.name,
      pada: row.pada,
      retro: row.retro,
    });
  });
  return Array.from(grouped.values()).sort((a, b) => a.index - b.index);
}

export {
  SIGN_NAMES,
  SIGN_ABBR,
  PLANET_ABBR,
  PLANET_ORDER,
};
