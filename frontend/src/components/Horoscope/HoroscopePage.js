import React, { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import SEOHead from '../SEO/SEOHead';
import { API_BASE_URL } from '../../config';
import './HoroscopePage.css';

const ZODIAC_SIGNS = [
  ['aries', '♈', 'Aries'], ['taurus', '♉', 'Taurus'], ['gemini', '♊', 'Gemini'],
  ['cancer', '♋', 'Cancer'], ['leo', '♌', 'Leo'], ['virgo', '♍', 'Virgo'],
  ['libra', '♎', 'Libra'], ['scorpio', '♏', 'Scorpio'], ['sagittarius', '♐', 'Sagittarius'],
  ['capricorn', '♑', 'Capricorn'], ['aquarius', '♒', 'Aquarius'], ['pisces', '♓', 'Pisces'],
].map(([name, symbol, displayName]) => ({ name, symbol: `${symbol}\uFE0E`, displayName }));

const PERIODS = [
  ['daily', 'Today'], ['weekly', 'This week'], ['monthly', 'This month'], ['yearly', 'This year'],
].map(([key, label]) => ({ key, label }));

const PERIOD_LABELS = { daily: 'Daily', weekly: 'Weekly', monthly: 'Monthly', yearly: 'Yearly' };
const VALID_PERIODS = new Set(PERIODS.map((period) => period.key));
const VALID_SIGNS = new Set(ZODIAC_SIGNS.map((sign) => sign.name));

const clampPercent = (value) => Math.max(0, Math.min(100, Number(value) || 0));

const MetricBar = ({ label, value }) => (
  <div className="horoscope-metric">
    <div><span>{label}</span><strong>{clampPercent(value)}%</strong></div>
    <div className="horoscope-metric__track"><span style={{ width: `${clampPercent(value)}%` }}></span></div>
  </div>
);

const HoroscopePage = ({ user, onLogin, onLogout, onAdminClick }) => {
  const { period: pathPeriod } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const query = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const period = VALID_PERIODS.has(pathPeriod) ? pathPeriod : 'daily';
  const querySign = query.get('sign');
  const selectedZodiac = VALID_SIGNS.has(querySign) ? querySign : 'aries';
  const currentZodiac = ZODIAC_SIGNS.find((sign) => sign.name === selectedZodiac) || ZODIAC_SIGNS[0];
  const [horoscopeData, setHoroscopeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const loadHoroscope = async () => {
      setLoading(true);
      setError('');
      setHoroscopeData(null);
      try {
        const response = await fetch(`${API_BASE_URL}/api/horoscope/${period}/${selectedZodiac}`, { signal: controller.signal });
        if (!response.ok) throw new Error(`Horoscope service returned ${response.status}`);
        setHoroscopeData(await response.json());
      } catch (requestError) {
        if (requestError.name !== 'AbortError') setError('The forecast could not be loaded right now.');
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    loadHoroscope();
    return () => controller.abort();
  }, [period, selectedZodiac, retryKey]);

  useEffect(() => { window.scrollTo(0, 0); }, [period]);

  const selectPeriod = (nextPeriod) => {
    navigate(`/horoscope/${nextPeriod}${selectedZodiac === 'aries' ? '' : `?sign=${selectedZodiac}`}`);
  };

  const selectSign = (nextSign) => {
    navigate(`/horoscope/${period}${nextSign === 'aries' ? '' : `?sign=${nextSign}`}`);
  };

  const periodLabel = PERIOD_LABELS[period];
  const canonical = `https://astroroshni.com/horoscope/${period}/`;
  const summary = horoscopeData?.daily_summary || horoscopeData?.weekly_summary || horoscopeData?.monthly_summary || horoscopeData?.yearly_summary;
  const prediction = horoscopeData?.prediction || {};

  const highlights = [
    ['Energy', horoscopeData?.todays_energy],
    ['Best time', horoscopeData?.best_time],
    ['Key focus', horoscopeData?.key_focus],
    ['Use care with', horoscopeData?.what_to_avoid],
    ['Supportive element', horoscopeData?.lucky_element],
    ['Moon phase', horoscopeData?.moon_timing && `${horoscopeData.moon_timing.phase}${horoscopeData.moon_timing.phase_meaning ? ` · ${horoscopeData.moon_timing.phase_meaning}` : ''}`],
  ].filter(([, value]) => value);

  const lifeAreas = [
    ['Relationships', prediction.love], ['Career & work', prediction.career], ['Health & wellbeing', prediction.health],
    ['Money & resources', prediction.finance], ['Learning', prediction.education], ['Inner life', prediction.spirituality],
  ].filter(([, value]) => value);

  const cosmicMetrics = horoscopeData?.cosmic_weather ? [
    ['Energy level', horoscopeData.cosmic_weather.energy_level],
    ['Manifestation power', horoscopeData.cosmic_weather.manifestation_power],
    ['Intuition strength', horoscopeData.cosmic_weather.intuition_strength],
    ['Relationship harmony', horoscopeData.cosmic_weather.relationship_harmony],
  ].filter(([, value]) => value !== undefined && value !== null) : [];

  const planetaryInfluences = prediction?.detailed_analysis?.planetary_influences || [];
  const challenges = prediction?.detailed_analysis?.challenges || [];
  const opportunities = prediction?.detailed_analysis?.opportunities || [];

  const actionItems = horoscopeData?.action_plan ? [
    ['Primary focus', horoscopeData.action_plan.primary_focus],
    ['Optimal timing', horoscopeData.action_plan.optimal_timing],
    ['Daily practices', horoscopeData.action_plan.daily_practices],
    ['Growth opportunities', horoscopeData.action_plan.growth_opportunities],
    ['Balance strategies', horoscopeData.action_plan.balance_strategies],
    ['Reflection practice', horoscopeData.action_plan.manifestation_techniques],
  ].filter(([, value]) => value) : [];

  return (
    <div className="horoscope-page">
      <SEOHead
        title={`${currentZodiac.displayName} ${periodLabel} Horoscope | AstroRoshni`}
        description={`Read the ${periodLabel.toLowerCase()} ${currentZodiac.displayName} tropical Sun-sign horoscope for relationships, work, wellbeing, money, timing, and practical focus.`}
        keywords={`${currentZodiac.displayName.toLowerCase()} horoscope, ${period} horoscope, tropical astrology forecast, sun sign horoscope`}
        canonical={canonical}
        structuredData={{
          '@context': 'https://schema.org',
          '@type': 'Article',
          headline: `${currentZodiac.displayName} ${periodLabel} Horoscope`,
          description: `${periodLabel} tropical Sun-sign forecast for ${currentZodiac.displayName}.`,
          mainEntityOfPage: canonical,
          author: { '@type': 'Organization', name: 'AstroRoshni' },
          publisher: { '@type': 'Organization', name: 'AstroRoshni', url: 'https://astroroshni.com/' },
        }}
      />

      <ModernNavigationHeader sticky user={user} onLogin={onLogin} onLogout={onLogout} onAdminClick={onAdminClick} />

      <main className="horoscope-main">
        <header className="horoscope-hero">
          <div className="horoscope-hero__copy">
            <p className="horoscope-eyebrow">Tropical Sun-sign forecast · {periodLabel}</p>
            <h1>{currentZodiac.displayName},<br /><em>meet the moment.</em></h1>
            <p className="horoscope-hero__lead">A broad forecast based on your tropical Sun sign and current planetary aspects. For chart-aware Vedic guidance, use your complete Kundli with Tara.</p>
          </div>
          <div className="horoscope-hero__sign" aria-hidden><span>{currentZodiac.symbol}</span><small>{currentZodiac.displayName}</small></div>
          <nav className="horoscope-periods" aria-label="Forecast period">
            {PERIODS.map((item) => <button key={item.key} type="button" aria-pressed={period === item.key} onClick={() => selectPeriod(item.key)}><span>{item.label}</span><small>{item.key}</small></button>)}
          </nav>
        </header>

        <section className="horoscope-sign-picker" aria-labelledby="choose-sign-title">
          <div><p className="horoscope-section-label">Choose a Sun sign</p><h2 id="choose-sign-title">Twelve signs,<br /><em>one current sky.</em></h2></div>
          <div className="horoscope-zodiac-grid">
            {ZODIAC_SIGNS.map((sign, index) => (
              <button key={sign.name} type="button" aria-pressed={selectedZodiac === sign.name} onClick={() => selectSign(sign.name)} title={`${sign.displayName} horoscope`}>
                <small>{String(index + 1).padStart(2, '0')}</small><span aria-hidden>{sign.symbol}</span><strong>{sign.displayName}</strong>
              </button>
            ))}
          </div>
        </section>

        {loading ? (
          <section className="horoscope-state" aria-live="polite"><span className="horoscope-state__spinner" aria-hidden></span><p>Reading the current planetary pattern…</p></section>
        ) : error ? (
          <section className="horoscope-state horoscope-state--error" role="alert"><p className="horoscope-section-label">Forecast unavailable</p><h2>The sky is still there.<br />The connection is not.</h2><p>{error} Please try again in a moment.</p><button type="button" onClick={() => setRetryKey((value) => value + 1)}>Try again <span aria-hidden>↻</span></button></section>
        ) : horoscopeData ? (
          <div className="horoscope-reading">
            <section className="horoscope-overview" aria-labelledby="forecast-title">
              <div className="horoscope-overview__heading">
                <p className="horoscope-section-label">{horoscopeData.date || periodLabel} · {horoscopeData.calculation_system === 'western_tropical_ephemeris' ? 'Western tropical ephemeris' : 'Tropical astrology'}</p>
                <h2 id="forecast-title">{summary?.theme || `${currentZodiac.displayName} ${periodLabel} outlook`}</h2>
                {summary?.essence && <p>{summary.essence}</p>}
              </div>
              <dl className="horoscope-overview__meta">
                <div><dt>Lucky number</dt><dd>{horoscopeData.lucky_number ?? '—'}</dd></div>
                <div><dt>Lucky colour</dt><dd>{horoscopeData.lucky_color || '—'}</dd></div>
                <div><dt>Forecast tone</dt><dd>{horoscopeData.rating ? `${horoscopeData.rating} / 5` : 'Balanced'}</dd></div>
              </dl>
              {prediction.overall && <blockquote>{prediction.overall}</blockquote>}
              {highlights.length > 0 && <div className="horoscope-highlights">{highlights.map(([label, value], index) => <article key={label}><span>{String(index + 1).padStart(2, '0')}</span><h3>{label}</h3><p>{value}</p></article>)}</div>}
            </section>

            {horoscopeData.daily_actions && (
              <section className="horoscope-actions" aria-labelledby="daily-actions-title">
                <div><p className="horoscope-section-label">Practical focus</p><h2 id="daily-actions-title">What to carry into the day.</h2></div>
                <div><ul>{horoscopeData.daily_actions.actions?.map((action) => <li key={action}>{action}</li>)}</ul>{horoscopeData.daily_actions.avoid && <p><strong>Use care with</strong>{horoscopeData.daily_actions.avoid}</p>}</div>
              </section>
            )}

            {horoscopeData.energy_forecast && (
              <section className="horoscope-energy" aria-labelledby="energy-title">
                <div><p className="horoscope-section-label">Energy rhythm</p><h2 id="energy-title">The day,<br /><em>in three movements.</em></h2><p>Peak indicated around {horoscopeData.energy_forecast.peak_time || 'the strongest part of the day'}.</p></div>
                <div><MetricBar label="Morning" value={horoscopeData.energy_forecast.morning} /><MetricBar label="Afternoon" value={horoscopeData.energy_forecast.afternoon} /><MetricBar label="Evening" value={horoscopeData.energy_forecast.evening} /></div>
              </section>
            )}

            {lifeAreas.length > 0 && (
              <section className="horoscope-life-areas" aria-labelledby="life-areas-title">
                <div className="horoscope-heading"><p className="horoscope-section-label">Across life</p><h2 id="life-areas-title">Where the pattern<br /><em>may be felt.</em></h2><p>Read each area as broad Sun-sign guidance rather than a personalised birth-chart judgement.</p></div>
                <div className="horoscope-life-grid">{lifeAreas.map(([title, value], index) => <article key={title}><span>{String(index + 1).padStart(2, '0')}</span><h3>{title}</h3><p>{value}</p></article>)}</div>
              </section>
            )}

            {(cosmicMetrics.length > 0 || planetaryInfluences.length > 0) && (
              <section className="horoscope-detail" aria-labelledby="detail-title">
                <div className="horoscope-heading horoscope-heading--inverse"><p className="horoscope-section-label">Under the forecast</p><h2 id="detail-title">The aspects shaping<br /><em>the reading.</em></h2></div>
                {cosmicMetrics.length > 0 && <div className="horoscope-detail__metrics">{cosmicMetrics.map(([label, value]) => <MetricBar key={label} label={label} value={value} />)}</div>}
                {planetaryInfluences.length > 0 && <div className="horoscope-planets">{planetaryInfluences.map((planet, index) => <article key={`${planet.planet}-${index}`}><div><span>{String(index + 1).padStart(2, '0')}</span><strong>{planet.planet}</strong><small>{planet.sign || planet.aspect || 'Current influence'}</small></div><p>{planet.influence || planet.effect}</p>{planet.strength !== undefined && <MetricBar label="Relative strength" value={planet.strength} />}</article>)}</div>}
                {(challenges.length > 0 || opportunities.length > 0) && <div className="horoscope-contrast">{challenges.length > 0 && <article><span>Navigate carefully</span><ul>{challenges.map((item) => <li key={item}>{item}</li>)}</ul></article>}{opportunities.length > 0 && <article><span>Use constructively</span><ul>{opportunities.map((item) => <li key={item}>{item}</li>)}</ul></article>}</div>}
              </section>
            )}

            {actionItems.length > 0 && (
              <section className="horoscope-plan" aria-labelledby="action-plan-title">
                <div className="horoscope-heading"><p className="horoscope-section-label">Action plan</p><h2 id="action-plan-title">Turn the forecast<br /><em>into a considered day.</em></h2></div>
                <div className="horoscope-plan__grid">{actionItems.map(([title, value], index) => <article key={title}><span>{String(index + 1).padStart(2, '0')}</span><h3>{title}</h3><p>{value}</p></article>)}</div>
              </section>
            )}
          </div>
        ) : null}

        <section className="horoscope-personal" aria-labelledby="personal-title">
          <div><p className="horoscope-section-label">Beyond the Sun sign</p><h2 id="personal-title">Your complete chart tells a different story.</h2><p>This page uses Western tropical Sun-sign astrology. Tara’s personalised readings use your saved Kundli and synthesize Parashari, Nadi, Jaimini, and KP astrology across 90+ calculation and interpretation layers.</p></div>
          <div><Link to="/ai-kundli-generator">Create or choose Kundli <span aria-hidden>↗</span></Link><Link to="/chat?app=1">Ask Tara <span aria-hidden>↗</span></Link></div>
        </section>
      </main>
    </div>
  );
};

export default HoroscopePage;
