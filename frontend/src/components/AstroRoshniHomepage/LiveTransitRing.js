import React, { useEffect, useMemo, useRef, useState } from 'react';
import { HOUSE_POLYGONS, layoutWebHouse } from '../Charts/northChartPlacement';
import { apiService } from '../../services/apiService';

const RASHIS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
];

const LAGNA_SHORT = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'];

const NAKSHATRAS = [
  ['Ashwini', 'Ash'], ['Bharani', 'Bha'], ['Krittika', 'Kri'], ['Rohini', 'Roh'],
  ['Mrigashira', 'Mri'], ['Ardra', 'Ard'], ['Punarvasu', 'Pun'], ['Pushya', 'Pus'],
  ['Ashlesha', 'Asl'], ['Magha', 'Mag'], ['Purva Phalguni', 'PPh'], ['Uttara Phalguni', 'UPh'],
  ['Hasta', 'Has'], ['Chitra', 'Chi'], ['Swati', 'Swa'], ['Vishakha', 'Vis'],
  ['Anuradha', 'Anu'], ['Jyeshtha', 'Jye'], ['Mula', 'Mul'], ['Purva Ashadha', 'PAs'],
  ['Uttara Ashadha', 'UAs'], ['Shravana', 'Shr'], ['Dhanishta', 'Dha'], ['Shatabhisha', 'Sha'],
  ['Purva Bhadrapada', 'PBh'], ['Uttara Bhadrapada', 'UBh'], ['Revati', 'Rev'],
];

const PLANET_RADII = {
  Sun: 27,
  Moon: 31,
  Mars: 24,
  Mercury: 33,
  Jupiter: 27,
  Venus: 21,
  Saturn: 31,
  Rahu: 24,
  Ketu: 24,
};

const GRAHAS = [
  ['Sun', 'SU', 'Su'],
  ['Moon', 'MO', 'Mo'],
  ['Mars', 'MA', 'Ma'],
  ['Mercury', 'ME', 'Me'],
  ['Jupiter', 'JU', 'Ju'],
  ['Venus', 'VE', 'Ve'],
  ['Saturn', 'SA', 'Sa'],
  ['Rahu', 'RA', 'Ra'],
  ['Ketu', 'KE', 'Ke'],
];

const CHART_VIEWS = [
  { id: 'natal-north', label: 'Natal North Indian' },
  { id: 'transit-north', label: 'Transit North Indian' },
  { id: 'natal-circular', label: 'Natal Circular' },
  { id: 'transit-circular', label: 'Transit Circular' },
];

const SIGN_NUMBER_POSITIONS = {
  1: { x: 200, y: 165 },
  2: { x: 100, y: 88 },
  3: { x: 75, y: 110 },
  4: { x: 150, y: 205 },
  5: { x: 75, y: 290 },
  6: { x: 100, y: 318 },
  7: { x: 200, y: 250 },
  8: { x: 300, y: 318 },
  9: { x: 325, y: 290 },
  10: { x: 250, y: 205 },
  11: { x: 325, y: 110 },
  12: { x: 300, y: 88 },
};

const NORTH_HOUSE_PATHS = {
  1: 'M200,0 L300,100 L200,200 L100,100 Z',
  2: 'M0,0 L200,0 L100,100 Z',
  3: 'M0,0 L100,100 L0,200 Z',
  4: 'M0,200 L100,100 L200,200 L100,300 Z',
  5: 'M0,200 L100,300 L0,400 Z',
  6: 'M0,400 L100,300 L200,400 Z',
  7: 'M200,200 L300,300 L200,400 L100,300 Z',
  8: 'M200,400 L300,300 L400,400 Z',
  9: 'M300,300 L400,200 L400,400 Z',
  10: 'M200,200 L300,100 L400,200 L300,300 Z',
  11: 'M300,100 L400,0 L400,200 Z',
  12: 'M200,0 L400,0 L300,100 Z',
};

const pointOnRing = (longitude, radius) => {
  const radians = ((Number(longitude || 0) - 90) * Math.PI) / 180;
  return {
    x: 50 + radius * Math.cos(radians),
    y: 50 + radius * Math.sin(radians),
  };
};

const formatDegree = (degree) => {
  const totalMinutes = Math.min(1799, Math.max(0, Math.round(Number(degree || 0) * 60)));
  return `${Math.floor(totalMinutes / 60)}° ${String(totalMinutes % 60).padStart(2, '0')}′`;
};

const formatUpdatedAt = (value) => {
  if (!value) return 'Calculating now';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Updated now';
  return new Intl.DateTimeFormat(undefined, {
    day: 'numeric',
    month: 'short',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date);
};

const localDateKey = (value = new Date()) => {
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${value.getFullYear()}-${month}-${day}`;
};

const middayInstant = (dateKey) => new Date(`${dateKey}T12:00:00`).toISOString();

const formatTransitDay = (dateKey) => {
  const [year, month, day] = dateKey.split('-').map(Number);
  const date = new Date(year, (month || 1) - 1, day || 1);
  const sameYear = date.getFullYear() === new Date().getFullYear();
  return new Intl.DateTimeFormat(undefined, {
    day: 'numeric',
    month: 'short',
    year: sameYear ? undefined : 'numeric',
  }).format(date);
};

const birthKey = (birthData) => [
  birthData?.name,
  birthData?.date,
  birthData?.time,
  birthData?.latitude,
  birthData?.longitude,
].join('|');

const ascendantLongitude = (chart) => {
  const raw = typeof chart?.ascendant === 'number' ? chart.ascendant : chart?.houses?.[0]?.longitude;
  if (typeof raw !== 'number' || Number.isNaN(raw)) return null;
  return ((raw % 360) + 360) % 360;
};

const pointOutside = (longitude, radius, nudge = 0) => {
  const radians = ((Number(longitude || 0) - 90) * Math.PI) / 180;
  const cos = Math.cos(radians);
  const sin = Math.sin(radians);
  return {
    x: 50 + radius * cos - nudge * sin,
    y: 50 + radius * sin + nudge * cos,
  };
};

const planetsFromChart = (chart) => {
  if (!chart?.planets) return [];
  return GRAHAS.map(([name, code, symbol]) => {
    const data = chart.planets[name];
    if (!data) return null;
    const longitude = typeof data.longitude === 'number'
      ? ((data.longitude % 360) + 360) % 360
      : (((data.sign || 0) * 30) + (Number(data.degree) || 0));
    const signIndex = typeof data.sign === 'number' ? data.sign : Math.floor(longitude / 30);
    const nakshatraIndex = Math.min(26, Math.floor(longitude / (360 / 27)));
    const pada = Math.min(4, Math.floor((longitude % (360 / 27)) / (360 / 108)) + 1);
    return {
      name,
      code,
      symbol: data.retrograde ? `${symbol}(R)` : symbol,
      longitude,
      rashi_index: signIndex,
      rashi: RASHIS[signIndex],
      degree_in_rashi: typeof data.degree === 'number' ? data.degree : longitude % 30,
      nakshatra: NAKSHATRAS[nakshatraIndex][0],
      pada,
      retrograde: !!data.retrograde,
    };
  }).filter(Boolean);
};

const planetsFromSky = (skyPlanets) => (skyPlanets || []).map((planet) => {
  const graha = GRAHAS.find(([name]) => name === planet.name);
  const symbol = graha ? graha[2] : String(planet.code || planet.name || '').slice(0, 2);
  return {
    ...planet,
    symbol: planet.retrograde ? `${symbol}(R)` : symbol,
    rashi_index: planet.rashi_index,
  };
});

const layoutNorthHouses = (planets, ascSign) => {
  const layouts = {};
  for (let house = 1; house <= 12; house += 1) {
    const sign = (ascSign + house - 1) % 12;
    layouts[house] = layoutWebHouse({
      polygon: HOUSE_POLYGONS[house],
      sign: SIGN_NUMBER_POSITIONS[house],
      signLabel: String(sign + 1),
      showDegree: false,
      planets: planets
        .filter((planet) => planet.rashi_index === sign)
        .map((planet) => ({ symbol: planet.symbol })),
    });
  }
  return layouts;
};

export default function LiveTransitRing({ birthData = null, chartData = null }) {
  const [sky, setSky] = useState(null);
  const [status, setStatus] = useState('loading');
  const [activePlanetName, setActivePlanetName] = useState('Moon');
  const [transitDate, setTransitDate] = useState(localDateKey);
  const hasSky = useRef(false);
  const isLiveTransit = transitDate === localDateKey();

  useEffect(() => {
    let cancelled = false;
    const live = transitDate === localDateKey();

    const loadSky = async () => {
      try {
        const url = live
          ? '/api/public/current-sky'
          : `/api/public/current-sky?at=${encodeURIComponent(middayInstant(transitDate))}`;
        const response = await fetch(url, { headers: { Accept: 'application/json' } });
        if (!response.ok) throw new Error('Current sky unavailable');
        const payload = await response.json();
        if (!cancelled && Array.isArray(payload?.planets) && payload.planets.length > 0) {
          hasSky.current = true;
          setSky(payload);
          setStatus('ready');
        } else if (!cancelled) {
          throw new Error('Current sky response was incomplete');
        }
      } catch (_) {
        if (!cancelled) setStatus(hasSky.current ? 'stale' : 'error');
      }
    };

    loadSky();
    if (!live) {
      return () => {
        cancelled = true;
      };
    }
    const refreshTimer = window.setInterval(loadSky, 5 * 60 * 1000);
    return () => {
      cancelled = true;
      window.clearInterval(refreshTimer);
    };
  }, [transitDate]);

  const [view, setView] = useState('transit-circular');
  const [natalChart, setNatalChart] = useState(birthData?.date && chartData?.planets ? chartData : null);
  const [natalStatus, setNatalStatus] = useState(birthData?.date && chartData?.planets ? 'ready' : 'idle');
  const nativeKey = birthKey(birthData);
  const isNatal = view.startsWith('natal');
  const isNorth = view.endsWith('north');

  useEffect(() => {
    if (!birthData?.date) {
      setNatalChart(null);
      setNatalStatus('missing');
      return undefined;
    }
    if (chartData?.planets) {
      setNatalChart(chartData);
      setNatalStatus('ready');
      return undefined;
    }
    let cancelled = false;
    setNatalStatus('loading');
    apiService.calculateChartOnly(birthData)
      .then((payload) => {
        if (cancelled) return;
        setNatalChart(payload?.planets ? payload : null);
        setNatalStatus(payload?.planets ? 'ready' : 'error');
      })
      .catch(() => {
        if (!cancelled) {
          setNatalChart(null);
          setNatalStatus('error');
        }
      });
    return () => {
      cancelled = true;
    };
  }, [chartData, nativeKey, birthData]);

  const transitPlanets = useMemo(() => planetsFromSky(sky?.planets || []), [sky]);
  const natalPlanets = useMemo(() => planetsFromChart(natalChart), [natalChart]);
  const planets = isNatal ? natalPlanets : transitPlanets;
  const ascLongitude = ascendantLongitude(natalChart);
  const ascSign = ascLongitude == null ? null : Math.floor(ascLongitude / 30);
  const ascLabelPoint = ascLongitude == null ? null : pointOutside(
    ascLongitude,
    47.4,
    (ascLongitude % 30) < 8 ? 3.4 : (ascLongitude % 30) > 22 ? -3.4 : 0
  );
  const activePlanet = useMemo(
    () => planets.find((planet) => planet.name === activePlanetName) || planets[0] || null,
    [activePlanetName, planets]
  );
  const northLayouts = useMemo(
    () => (isNorth && planets.length ? layoutNorthHouses(planets, isNatal ? (ascSign ?? 0) : 0) : null),
    [ascSign, isNatal, isNorth, planets]
  );

  const statusLabel = isNatal
    ? (birthData?.name || 'Selected native')
    : !isLiveTransit
      ? formatTransitDay(transitDate)
      : status === 'ready'
      ? 'Live positions'
      : status === 'stale'
        ? 'Last known positions'
        : status === 'error'
          ? 'Sky temporarily unavailable'
          : 'Calculating positions';

  const title = isNatal
    ? (isNorth ? 'NATAL · NORTH INDIAN' : 'NATAL · CIRCULAR')
    : (isNorth ? 'TRANSIT · NORTH INDIAN' : 'THE SIDEREAL SKY NOW');

  const natalPrompt = !birthData?.date
    ? 'Select a native to see the birth chart'
    : natalStatus === 'error'
      ? 'Birth chart unavailable'
      : 'Reading the birth chart';

  return (
    <div className={`mh-chart-shell mh-transit-shell mh-transit-shell--${status}`}>
      <div className="mh-chart-meta">
        <span>{title}</span>
        <span className="mh-chart-meta__status"><i></i>{statusLabel}</span>
      </div>

      {isNorth ? (
        <div className="mh-transit-ring mh-north-frame" role="group" aria-label={isNatal ? 'Natal North Indian chart' : 'Transit North Indian chart'}>
          {planets.length > 0 && northLayouts ? (
            <svg className="mh-north-chart" viewBox="0 0 400 400" role="img">
              <rect className="mh-north-surface" x="0" y="0" width="400" height="400" />
              <polygon className="mh-north-line" points="200,0 400,200 200,400 0,200" />
              <line className="mh-north-line" x1="0" y1="0" x2="400" y2="400" />
              <line className="mh-north-line" x1="400" y1="0" x2="0" y2="400" />
              {Array.from({ length: 12 }, (_, index) => {
                const house = index + 1;
                const sign = ((isNatal ? (ascSign ?? 0) : 0) + index) % 12;
                const spot = SIGN_NUMBER_POSITIONS[house];
                const layout = northLayouts[house];
                const housePlanets = planets.filter((planet) => planet.rashi_index === sign);
                return (
                  <g key={house}>
                    <path className="mh-north-house" d={NORTH_HOUSE_PATHS[house]} />
                    <text className="mh-north-sign" x={spot.x} y={spot.y} textAnchor="middle">{sign + 1}</text>
                    {housePlanets.map((planet, index) => {
                      const slot = layout?.planets?.[index];
                      if (!slot) return null;
                      return (
                        <text
                          key={`${house}-${planet.name}`}
                          className={`mh-north-planet mh-north-planet--${planet.name.toLowerCase()}${activePlanet?.name === planet.name ? ' is-active' : ''}`}
                          x={slot.x}
                          y={slot.y}
                          fontSize={slot.symbolFont}
                          textAnchor="middle"
                          onMouseEnter={() => setActivePlanetName(planet.name)}
                          onClick={() => setActivePlanetName(planet.name)}
                        >
                          {planet.symbol}
                        </text>
                      );
                    })}
                  </g>
                );
              })}
            </svg>
          ) : (
            <div className="mh-chart-prompt" aria-live="polite">
              <span>{isNatal ? natalPrompt : (status === 'error' ? 'Live sky unavailable' : 'Reading the sky')}</span>
            </div>
          )}
        </div>
      ) : (
      <div className="mh-transit-ring" role="group" aria-label={isNatal ? 'Natal circular chart' : 'Current Lahiri sidereal transit positions'}>
        <div className="mh-transit-ring__glow" aria-hidden></div>
        <div className="mh-transit-ring__circle mh-transit-ring__circle--outer" aria-hidden></div>
        <div className="mh-transit-ring__circle mh-transit-ring__circle--nakshatra" aria-hidden></div>
        <div className="mh-transit-ring__circle mh-transit-ring__circle--planet" aria-hidden></div>

        {Array.from({ length: 12 }, (_, index) => (
          <i
            className="mh-transit-rashi-axis"
            style={{ '--transit-angle': `${index * 30 - 90}deg` }}
            key={`rashi-axis-${index}`}
            aria-hidden
          ></i>
        ))}

        {Array.from({ length: 12 }, (_, index) => {
          const point = pointOnRing(index * 30, 47.4);
          return (
            <span
              className="mh-transit-cusp"
              style={{ '--transit-x': `${point.x}%`, '--transit-y': `${point.y}%` }}
              key={`cusp-${index}`}
              aria-hidden
            >
              {index * 30}°
            </span>
          );
        })}

        {Array.from({ length: 27 }, (_, index) => {
          const longitude = index * (360 / 27);
          const point = pointOnRing(longitude, 43.6);
          return (
            <i
              className="mh-transit-nakshatra-tick"
              style={{
                '--transit-x': `${point.x}%`,
                '--transit-y': `${point.y}%`,
                '--transit-angle': `${longitude}deg`,
              }}
              key={`nakshatra-tick-${index}`}
              aria-hidden
            ></i>
          );
        })}

        {NAKSHATRAS.map(([name, abbreviation], index) => {
          const longitude = (index + 0.5) * (360 / 27);
          const point = pointOnRing(longitude, 41.2);
          return (
            <abbr
              className="mh-transit-nakshatra-label"
              style={{ '--transit-x': `${point.x}%`, '--transit-y': `${point.y}%` }}
              title={name}
              key={name}
              aria-label={name}
            >
              {abbreviation}
            </abbr>
          );
        })}

        {RASHIS.map((rashi, index) => {
          const point = pointOnRing(index * 30 + 15, 36.7);
          const houseNumber = ascSign == null ? null : ((index - ascSign + 12) % 12) + 1;
          return (
            <span
              className="mh-transit-rashi-label"
              style={{ '--transit-x': `${point.x}%`, '--transit-y': `${point.y}%` }}
              key={rashi}
              aria-hidden
            >
              {rashi}
              {isNatal && houseNumber ? (
                <b className={houseNumber === 1 ? 'is-lagna' : ''} aria-label={`House ${houseNumber}`}>{houseNumber}</b>
              ) : null}
            </span>
          );
        })}

        {isNatal && ascLongitude != null ? (
          <>
            <i
              className="mh-transit-asc"
              style={{ '--transit-angle': `${ascLongitude - 90}deg` }}
              aria-hidden
            />
            <span
              className="mh-transit-asc-label"
              style={{ '--transit-x': `${ascLabelPoint.x}%`, '--transit-y': `${ascLabelPoint.y}%` }}
              aria-hidden
            >
              Asc
              <small>{formatDegree(ascLongitude % 30)}</small>
            </span>
          </>
        ) : null}

        {planets.map((planet) => (
          <i
            className={`mh-transit-degree mh-transit-degree--${planet.name.toLowerCase()}${activePlanet?.name === planet.name ? ' is-active' : ''}`}
            style={{ '--transit-angle': `${planet.longitude - 90}deg` }}
            key={`degree-${planet.name}`}
            aria-hidden
          />
        ))}

        {planets.map((planet, index) => {
          const point = pointOnRing(planet.longitude, PLANET_RADII[planet.name] || 30);
          const isActive = activePlanet?.name === planet.name;
          return (
            <button
              type="button"
              className={`mh-transit-planet mh-transit-planet--${planet.name.toLowerCase()}${isActive ? ' is-active' : ''}`}
              style={{
                '--transit-x': `${point.x}%`,
                '--transit-y': `${point.y}%`,
                '--planet-order': index,
              }}
              key={planet.name}
              onMouseEnter={() => setActivePlanetName(planet.name)}
              onFocus={() => setActivePlanetName(planet.name)}
              onClick={() => setActivePlanetName(planet.name)}
              aria-pressed={isActive}
              aria-label={`${planet.name}: ${planet.rashi} ${formatDegree(planet.degree_in_rashi)}, ${planet.nakshatra}, Pada ${planet.pada}${planet.retrograde ? ', retrograde' : ''}`}
            >
              <span>{planet.code}</span>
              {planet.retrograde ? <sup>R</sup> : null}
            </button>
          );
        })}

        {planets.length > 0 ? (
          <div className="mh-transit-ring__core" aria-hidden>
            <strong>{isNatal ? (ascSign == null ? 'NATAL' : LAGNA_SHORT[ascSign]) : (isLiveTransit ? 'NOW' : formatTransitDay(transitDate))}</strong>
            <span>{isNatal ? 'LAGNA · LAHIRI' : 'SIDEREAL · LAHIRI'}</span>
            <small>{isNatal ? (birthData?.name || 'Selected native') : (isLiveTransit ? formatUpdatedAt(sky?.calculated_at) : 'Midday positions')}</small>
          </div>
        ) : null}

        {planets.length === 0 ? (
          <div className={isNatal ? 'mh-chart-prompt' : 'mh-transit-ring__empty'} aria-live="polite">
            <span>{isNatal ? natalPrompt : (status === 'error' ? 'Live sky unavailable' : 'Reading the sky')}</span>
          </div>
        ) : null}
      </div>
      )}

      <div className="mh-chart-readout" aria-live="polite">
        <div>
          <span>{activePlanet ? activePlanet.name : 'Current transit'}</span>
          <strong>
            {activePlanet
              ? `${activePlanet.rashi} ${formatDegree(activePlanet.degree_in_rashi)} · ${activePlanet.nakshatra} P${activePlanet.pada}`
              : 'Awaiting precise positions'}
          </strong>
        </div>
        <strong>{activePlanet ? (activePlanet.retrograde ? 'Retrograde · Lahiri' : 'Direct · Lahiri') : 'Lahiri'}</strong>
      </div>

      <div className="mh-chart-controls">
        {isNatal ? null : (
          <label className="mh-chart-date">
            <span>Date</span>
            <input
              type="date"
              value={transitDate}
              max="2100-12-31"
              min="1800-01-01"
              aria-label="Transit date"
              onChange={(event) => {
                if (event.target.value) setTransitDate(event.target.value);
              }}
            />
          </label>
        )}
        <nav className="mh-chart-switch" aria-label="Chart views">
          {CHART_VIEWS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={view === item.id ? 'is-active' : ''}
              aria-pressed={view === item.id}
              onClick={() => setView(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </div>
    </div>
  );
}
