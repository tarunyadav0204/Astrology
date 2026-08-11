import React, { useEffect, useMemo, useRef, useState } from 'react';

const RASHIS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
];

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

export default function LiveTransitRing() {
  const [sky, setSky] = useState(null);
  const [status, setStatus] = useState('loading');
  const [activePlanetName, setActivePlanetName] = useState('Moon');
  const hasSky = useRef(false);

  useEffect(() => {
    let cancelled = false;

    const loadSky = async () => {
      try {
        const response = await fetch('/api/public/current-sky', { headers: { Accept: 'application/json' } });
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
    const refreshTimer = window.setInterval(loadSky, 5 * 60 * 1000);
    return () => {
      cancelled = true;
      window.clearInterval(refreshTimer);
    };
  }, []);

  const planets = sky?.planets || [];
  const activePlanet = useMemo(
    () => planets.find((planet) => planet.name === activePlanetName) || planets[0] || null,
    [activePlanetName, planets]
  );

  const statusLabel = status === 'ready'
    ? 'Live positions'
    : status === 'stale'
      ? 'Last known positions'
      : status === 'error'
        ? 'Sky temporarily unavailable'
        : 'Calculating positions';

  return (
    <div className={`mh-chart-shell mh-transit-shell mh-transit-shell--${status}`}>
      <div className="mh-chart-meta">
        <span>THE SIDEREAL SKY NOW</span>
        <span className="mh-chart-meta__status"><i></i>{statusLabel}</span>
      </div>

      <div className="mh-transit-ring" role="group" aria-label="Current Lahiri sidereal transit positions">
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

        {Array.from({ length: 27 }, (_, index) => {
          const longitude = index * (360 / 27);
          const point = pointOnRing(longitude, 46.2);
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
          const point = pointOnRing(longitude, 43.4);
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
          return (
            <span
              className="mh-transit-rashi-label"
              style={{ '--transit-x': `${point.x}%`, '--transit-y': `${point.y}%` }}
              key={rashi}
              aria-hidden
            >
              {rashi}
            </span>
          );
        })}

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

        <div className="mh-transit-ring__core" aria-hidden>
          <strong>NOW</strong>
          <span>SIDEREAL · LAHIRI</span>
          <small>{formatUpdatedAt(sky?.calculated_at)}</small>
        </div>

        {planets.length === 0 ? (
          <div className="mh-transit-ring__empty" aria-live="polite">
            <span>{status === 'error' ? 'Live sky unavailable' : 'Reading the sky'}</span>
          </div>
        ) : null}
      </div>

      <div className="mh-chart-readout" aria-live="polite">
        <div>
          <span>{activePlanet ? activePlanet.name : 'Current transit'}</span>
          <strong>
            {activePlanet
              ? `${activePlanet.rashi} ${formatDegree(activePlanet.degree_in_rashi)} · ${activePlanet.nakshatra} P${activePlanet.pada}`
              : 'Awaiting precise positions'}
          </strong>
        </div>
        <div>
          <span>Motion & reference</span>
          <strong>{activePlanet ? (activePlanet.retrograde ? 'Retrograde · Lahiri' : 'Direct · Lahiri') : '— · Lahiri'}</strong>
        </div>
      </div>
    </div>
  );
}
