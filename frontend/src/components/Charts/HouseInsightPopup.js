import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../../services/apiService';
import { getHouseAspects } from '../../utils/grahaDrishti';
import './HouseInsightPopup.css';

const SIGN_LORDS = [
  'Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury',
  'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter',
];

const HOUSE_META = {
  1: { title: '1st House: Self & Personality', desc: 'Represents the self, physical body, appearance, and overall vitality.' },
  2: { title: '2nd House: Wealth & Family', desc: 'Governs wealth, family, speech, food, and accumulated resources.' },
  3: { title: '3rd House: Courage & Siblings', desc: 'Represents siblings, courage, communication, short journeys, and skills.' },
  4: { title: '4th House: Home & Mother', desc: 'Governs mother, home, property, education, and emotional foundation.' },
  5: { title: '5th House: Children & Creativity', desc: 'Represents children, creativity, intelligence, romance, and speculation.' },
  6: { title: '6th House: Health & Service', desc: 'Governs enemies, diseases, debts, service, and daily work.' },
  7: { title: '7th House: Marriage & Partnerships', desc: 'Represents spouse, partnerships, business, and public relations.' },
  8: { title: '8th House: Transformation & Longevity', desc: 'Governs longevity, transformation, occult, and shared resources.' },
  9: { title: '9th House: Fortune & Dharma', desc: 'Represents fortune, father, dharma, higher learning, and long journeys.' },
  10: { title: '10th House: Career & Status', desc: 'Governs career, status, public life, and professional achievements.' },
  11: { title: '11th House: Gains & Friends', desc: 'Represents fulfillment of desires, income, and social circles.' },
  12: { title: '12th House: Loss & Spirituality', desc: 'Governs isolation, expenses, foreign lands, and spiritual liberation.' },
};

const JUMP_LINKS = [
  { id: 'hi-reading', label: 'Reading' },
  { id: 'hi-lord', label: 'Lord' },
  { id: 'hi-occupants', label: 'Occupants' },
  { id: 'hi-argala', label: 'Argala' },
  { id: 'hi-timing', label: 'Timing' },
];

function prettyDignity(value) {
  if (!value) return '—';
  return String(value).replace(/_/g, ' ');
}

function HouseInsightPopup({
  isOpen,
  onClose,
  houseNumber,
  signName,
  rashiIndex,
  chartData,
  birthData,
  chartId = 'lagna',
  planetsInHouse = [],
  onMakeAscendant,
  transitDate,
}) {
  const navigate = useNavigate();
  const [insight, setInsight] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mudakku, setMudakku] = useState(null);
  const [gandanta, setGandanta] = useState(null);
  const [error, setError] = useState('');
  const bodyRef = useRef(null);

  const meta = HOUSE_META[houseNumber] || { title: `House ${houseNumber}`, desc: '' };
  const houseLord = SIGN_LORDS[rashiIndex] || insight?.house_lord || '—';

  const aspects = useMemo(() => {
    if (!chartData || rashiIndex == null || !houseNumber) return [];
    return getHouseAspects(chartData, houseNumber, rashiIndex);
  }, [chartData, houseNumber, rashiIndex]);

  useEffect(() => {
    if (!isOpen || !birthData || !houseNumber) {
      setInsight(null);
      setError('');
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    setError('');
    apiService
      .getHouseInsight({ birthData, houseNum: houseNumber, chartId, transitDate })
      .then((data) => {
        if (!cancelled) setInsight(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setInsight(null);
          setError(err?.response?.data?.detail || err.message || 'Failed to load house insight');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [isOpen, birthData, houseNumber, chartId, transitDate]);

  useEffect(() => {
    if (!isOpen || !chartData) {
      setMudakku(null);
      setGandanta(null);
      return undefined;
    }
    let cancelled = false;
    Promise.all([
      apiService.calculateMudakkuAnalysis(chartData).catch(() => null),
      apiService.calculateGandantaAnalysis(chartData).catch(() => null),
    ]).then(([mud, gan]) => {
      if (cancelled) return;
      setMudakku(mud?.mudakku_analysis || mud?.data?.mudakku_analysis || mud || null);
      setGandanta(gan?.gandanta_analysis || gan?.data?.gandanta_analysis || gan || null);
    });
    return () => {
      cancelled = true;
    };
  }, [isOpen, chartData]);

  if (!isOpen || !houseNumber) return null;

  const ava = insight?.raw?.ashtakavarga;
  const lordSheet = insight?.lord_worksheet;
  const argala = insight?.argala;
  const savGivers = insight?.sav_givers?.givers || ava?.givers || [];
  const pointsInHouse = insight?.points_in_house || [];
  const karakasHere = insight?.chara_karakas_here || [];
  const naturalKarakas = insight?.natural_karakas || [];
  const relatedVarga = insight?.related_varga;
  const timing = insight?.timing || {};
  const scrollToSection = (id) => {
    bodyRef.current?.querySelector(`#${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
  const mudakkuHere = mudakku?.mudakku_point?.sign === rashiIndex;
  const planetaryGandanta = gandanta?.planetary_gandanta
    || gandanta?.planets_in_gandanta
    || gandanta?.planets
    || [];
  const gandantaPlanets = planetaryGandanta.filter((p) => {
    const name = typeof p.planet === 'string' ? p.planet : (p.planet?.name || p.name);
    if (!name) return false;
    const info = p.gandanta_info || (p.is_gandanta ? p : null);
    if (!info && !p.is_gandanta) return false;
    return planetsInHouse.some((occ) => occ.name === name);
  });
  const lagnaGandanta = houseNumber === 1 && (gandanta?.lagna_gandanta?.is_gandanta);

  const askPrompt = `Analyze the ${houseNumber} house in my ${chartId === 'lagna' ? 'D1 Lagna' : chartId} chart. It has ${signName} sign and ${planetsInHouse.length ? planetsInHouse.map((p) => p.name).join(', ') : 'no planets'}.`;

  return createPortal(
    <div className="house-insight-overlay" onClick={onClose} role="presentation">
      <aside
        className="house-insight-panel"
        role="dialog"
        aria-modal="true"
        aria-label={`House ${houseNumber} insights`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="house-insight-handle" />
        <header className="house-insight-head">
          <span className="house-insight-badge">{houseNumber}</span>
          <div>
            <h2>{meta.title}</h2>
            <p>{signName}</p>
          </div>
          <button type="button" className="house-insight-close" onClick={onClose} aria-label="Close">×</button>
        </header>
        <nav className="house-insight-jump" aria-label="Jump to section">
          {JUMP_LINKS.map((link) => (
            <button key={link.id} type="button" onClick={() => scrollToSection(link.id)}>
              {link.label}
            </button>
          ))}
        </nav>

        <div className="house-insight-body" ref={bodyRef}>
          <section className="house-insight-sec">
            <h3>Significance</h3>
            <p>{insight?.significance || meta.desc}</p>
          </section>

          {mudakkuHere && mudakku ? (
            <section className="house-insight-sec house-insight-sec--warn">
              <h3>Mudakku / Modakku</h3>
              <p>This house contains the Mudakku point for your chart.</p>
              <div className="house-insight-grid">
                <div>
                  <em>Sun Nakshatra</em>
                  <strong>{mudakku.sun_nakshatra?.name || '—'}</strong>
                </div>
                <div>
                  <em>Count to Mula</em>
                  <strong>{mudakku.count_to_mula ?? '—'}</strong>
                </div>
              </div>
              <p className="house-insight-note">
                Landing: {mudakku.mudakku_nakshatra?.name || '—'} · {mudakku.mudakku_rashi || '—'}
                {mudakku.is_split_nakshatra ? ' · Split nakshatra rule' : ' · Single sign landing'}
              </p>
            </section>
          ) : null}

          {(gandantaPlanets.length > 0 || lagnaGandanta) ? (
            <section className="house-insight-sec house-insight-sec--danger">
              <h3>Gandamoola (Gandanta)</h3>
              <p>
                {lagnaGandanta
                  ? `This is a Gandanta Lagna house (${gandanta?.lagna_gandanta?.gandanta_info?.gandanta_name || 'junction'}).`
                  : 'This house contains one or more planets in Gandanta.'}
              </p>
              {gandantaPlanets.map((row, idx) => {
                const info = row.gandanta_info || row;
                const name = typeof row.planet === 'string' ? row.planet : (row.planet?.name || row.name || 'Planet');
                return (
                  <div key={`${name}-${idx}`} className="house-insight-chip-row">
                    <strong>{name}</strong>
                    <span>
                      {info.gandanta_name || 'Gandanta'}
                      {info.intensity ? ` · ${info.intensity}` : ''}
                      {info.distance_from_junction != null ? ` · ${info.distance_from_junction}°` : ''}
                    </span>
                  </div>
                );
              })}
            </section>
          ) : null}

          {loading ? <div className="house-insight-status">Loading chart reading…</div> : null}
          {error ? <div className="house-insight-status house-insight-status--err">{error}</div> : null}

          {insight ? (
            <section className="house-insight-sec house-insight-sec--read" id="hi-reading">
              <div className="house-insight-verdict-row">
                <h3>Chart reading</h3>
                <em className={`verdict-${insight.verdict?.key || 'quiet'}`}>{insight.verdict?.label || '—'}</em>
              </div>
              <p>{insight.interpretation}</p>
            </section>
          ) : null}

          {insight?.support_factors?.length ? (
            <section className="house-insight-sec">
              <h3>What supports this house</h3>
              <ul>
                {insight.support_factors.map((item) => (
                  <li key={item.label || item}>{item.label || item}</li>
                ))}
              </ul>
            </section>
          ) : null}

          {insight?.stress_factors?.length ? (
            <section className="house-insight-sec">
              <h3>What adds pressure</h3>
              <ul>
                {insight.stress_factors.map((item) => (
                  <li key={item.label || item}>{item.label || item}</li>
                ))}
              </ul>
            </section>
          ) : null}

          {insight?.activation_factors?.length ? (
            <section className="house-insight-sec">
              <h3>What is activating it now</h3>
              <ul>
                {insight.activation_factors.map((item) => (
                  <li key={item.label || item}>{item.label || item}</li>
                ))}
              </ul>
            </section>
          ) : null}

          {(ava?.sav || savGivers.length) ? (
            <section className="house-insight-sec">
              <h3>Ashtakavarga</h3>
              <div className="house-insight-grid">
                <div>
                  <em>SAV</em>
                  <strong>
                    {ava?.sav?.house_points ?? insight?.sav_givers?.total ?? '—'}
                    {ava?.sav?.classification ? ` · ${ava.sav.classification}` : ''}
                  </strong>
                </div>
                {ava?.lord_bav ? (
                  <div>
                    <em>{ava.lord_bav.planet} BAV</em>
                    <strong>{ava.lord_bav.house_points ?? '—'} · {ava.lord_bav.classification || '—'}</strong>
                  </div>
                ) : null}
              </div>
              {ava.lord_bav?.strongest_houses?.length ? (
                <p className="house-insight-note">
                  Strongest {ava.lord_bav.planet} BAV houses: {ava.lord_bav.strongest_houses.join(', ')}
                </p>
              ) : null}
              {ava.lord_bav?.weakest_houses?.length ? (
                <p className="house-insight-note">
                  Weakest {ava.lord_bav.planet} BAV houses: {ava.lord_bav.weakest_houses.join(', ')}
                </p>
              ) : null}
              {savGivers.length ? (
                <div className="house-insight-givers">
                  {savGivers.map((row) => (
                    <span key={row.planet}>
                      {row.planet === 'Lagna' ? 'Lg' : row.planet.slice(0, 2)} {row.bindus}
                    </span>
                  ))}
                </div>
              ) : null}
            </section>
          ) : null}

          <section className="house-insight-sec" id="hi-occupants">
            <h3>Occupant planets</h3>
            {planetsInHouse.length ? (
              planetsInHouse.map((planet) => {
                const roles = insight?.raw?.occupant_roles?.[planet.name] || [];
                const retro = planet.retrograde && planet.name !== 'Rahu' && planet.name !== 'Ketu';
                return (
                  <div key={planet.name} className="house-insight-occupant">
                    <strong>{planet.symbol || planet.name.slice(0, 2)}</strong>
                    <div>
                      <b>
                        {planet.name}
                        {retro ? <i>Retrograde</i> : null}
                        {roles.map((role) => <i key={role}>{role}</i>)}
                      </b>
                      <span>
                        {planet.formattedDegree || planet.degree}
                        {planet.nakshatra ? ` in ${planet.nakshatra}` : ''}
                        {planet.pada != null ? ` · Pada ${planet.pada}` : ''}
                      </span>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="house-insight-empty">No planets occupy this house.</p>
            )}
          </section>

          <section className="house-insight-sec">
            <h3>Graha drishti</h3>
            {aspects.length ? (
              aspects.map((row) => (
                <div key={`${row.planetName}-${row.planetHouse}`} className="house-insight-chip-row">
                  <strong>
                    {row.planetName}
                    {row.planetHouse != null ? ` · H${row.planetHouse}` : ''}
                  </strong>
                  <span>{row.aspectKinds} aspect</span>
                </div>
              ))
            ) : (
              <p className="house-insight-empty">No graha drishti from other houses.</p>
            )}
          </section>

          <section className="house-insight-sec" id="hi-lord">
            <h3>House lord</h3>
            {lordSheet ? (
              <>
                <p>
                  {lordSheet.planet} in {lordSheet.sign_name || signName}
                  {lordSheet.house != null ? ` · H${lordSheet.house}` : ''}
                  {lordSheet.dignity ? ` · ${prettyDignity(lordSheet.dignity)}` : ''}
                </p>
                <div className="house-insight-grid">
                  <div>
                    <em>Nakshatra</em>
                    <strong>
                      {lordSheet.nakshatra || '—'}
                      {lordSheet.nakshatra_lord ? ` · ${lordSheet.nakshatra_lord}` : ''}
                    </strong>
                  </div>
                  <div>
                    <em>Shadbala</em>
                    <strong>
                      {lordSheet.shadbala_rupas != null ? `${lordSheet.shadbala_rupas} / ${lordSheet.required_rupas ?? '—'} rupas` : '—'}
                      {lordSheet.meets_minimum === false ? ' · below' : lordSheet.meets_minimum ? ' · meets' : ''}
                    </strong>
                  </div>
                  <div>
                    <em>Condition</em>
                    <strong>
                      {[
                        lordSheet.retrograde ? 'Retrograde' : null,
                        lordSheet.combust ? 'Combust' : null,
                        lordSheet.cazimi ? 'Cazimi' : null,
                      ].filter(Boolean).join(' · ') || 'Direct'}
                    </strong>
                  </div>
                  <div>
                    <em>Also lords</em>
                    <strong>
                      {(lordSheet.other_lordships || []).length
                        ? lordSheet.other_lordships.map((h) => `H${h}`).join(', ')
                        : '—'}
                    </strong>
                  </div>
                </div>
                {(lordSheet.special_roles || []).length ? (
                  <p className="house-insight-note">{lordSheet.special_roles.join(' · ')}</p>
                ) : null}
              </>
            ) : (
              <p>Lord of {signName} is {houseLord}.</p>
            )}
          </section>

          <section className="house-insight-sec" id="hi-argala">
            <h3>Argala</h3>
            {argala && (argala.support?.length || argala.obstruction?.length) ? (
              <>
                <p className="house-insight-note">{argala.grade}</p>
                {argala.support?.map((row) => (
                  <div key={`a-${row.planet}-${row.from_house}`} className="house-insight-chip-row">
                    <strong>{row.planet}</strong>
                    <span>Argala from H{row.from_house} ({row.label})</span>
                  </div>
                ))}
                {argala.obstruction?.map((row) => (
                  <div key={`v-${row.planet}-${row.from_house}`} className="house-insight-chip-row">
                    <strong>{row.planet}</strong>
                    <span>Virodha from H{row.from_house} ({row.label})</span>
                  </div>
                ))}
              </>
            ) : (
              <p className="house-insight-empty">No argala or virodha from occupied houses.</p>
            )}
          </section>

          {(pointsInHouse.length || karakasHere.length) ? (
            <section className="house-insight-sec">
              <h3>Points in this house</h3>
              {pointsInHouse.map((point) => (
                <div key={point.key} className="house-insight-chip-row">
                  <strong>{point.label}</strong>
                  <span>
                    {point.sign_name}
                    {point.detail ? ` · ${point.detail}` : ''}
                  </span>
                </div>
              ))}
              {karakasHere.map((row) => (
                <div key={row.karaka} className="house-insight-chip-row">
                  <strong>{row.abbr}</strong>
                  <span>{row.planet} · {row.title}</span>
                </div>
              ))}
            </section>
          ) : null}

          <details className="house-insight-sec house-insight-sec--fold" id="hi-timing">
            <summary>Timing, karaka, related varga</summary>
            {timing.current_transits?.length ? (
              <p>Transiting here now: {timing.current_transits.join(', ')}</p>
            ) : (
              <p className="house-insight-empty">No natal-sign transits flagged for the as-of date.</p>
            )}
            {timing.windows?.length ? (
              timing.windows.map((row) => (
                <div key={`${row.mahadasha}-${row.antardasha}-${row.start}`} className="house-insight-chip-row">
                  <strong>{row.current ? 'Now' : 'Next'}</strong>
                  <span>
                    {row.mahadasha}/{row.antardasha}
                    {row.start ? ` · ${row.start}` : ''}
                    {row.end ? `–${row.end}` : ''}
                    {row.why ? ` · ${row.why}` : ''}
                  </span>
                </div>
              ))
            ) : (
              <p className="house-insight-empty">No upcoming MD/AD of the lord, occupants, or aspectors in the current cycle.</p>
            )}
            {naturalKarakas.length ? (
              <>
                <h3>Natural karaka</h3>
                {naturalKarakas.map((row) => (
                  <div key={row.planet} className="house-insight-chip-row">
                    <strong>{row.planet}</strong>
                    <span>
                      {row.sign_name || '—'}
                      {row.house != null ? ` · H${row.house}` : ''}
                      {row.retrograde ? ' · R' : ''}
                    </span>
                  </div>
                ))}
              </>
            ) : null}
            {relatedVarga ? (
              <>
                <h3>Related varga</h3>
                <p>
                  {relatedVarga.name}: same house is {relatedVarga.sign_name || '—'}, lord {relatedVarga.lord || '—'}
                  {relatedVarga.lord_house != null ? ` in H${relatedVarga.lord_house}` : ''}
                  {relatedVarga.occupants?.length ? ` · occupants ${relatedVarga.occupants.join(', ')}` : ' · empty'}
                </p>
              </>
            ) : null}
          </details>
        </div>

        <footer className="house-insight-actions">
          {onMakeAscendant ? (
            <button
              type="button"
              className="house-insight-actions__primary"
              onClick={() => {
                onMakeAscendant(houseNumber, signName);
                onClose();
              }}
            >
              Make Ascendant
            </button>
          ) : null}
          <button
            type="button"
            onClick={() => {
              onClose();
              navigate('/chat?app=1', { state: { initialMessage: askPrompt } });
            }}
          >
            Ask
          </button>
        </footer>
      </aside>
    </div>,
    document.body
  );
}

export default HouseInsightPopup;
