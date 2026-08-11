import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import SEOHead from '../SEO/SEOHead';
import ColorLegend from './ColorLegend';
import './NakshatraPage.css';

const SITE_ORIGIN = 'https://astroroshni.com';

const slugifyNakshatra = (name) => String(name || '').trim().toLowerCase().replace(/\s+/g, '-');
const titleizeNakshatra = (name) => String(name || '').replace(/[-_]+/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

const NakshatraPage = ({ user, onLogin, onLogout, onAdminClick }) => {
  const { nakshatraName, year } = useParams();
  const navigate = useNavigate();
  const currentYear = new Date().getFullYear();
  const yearFromUrl = parseInt(year, 10);
  const [nakshatraData, setNakshatraData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedYear, setSelectedYear] = useState(Number.isFinite(yearFromUrl) ? yearFromUrl : currentYear);

  const canonicalYear = Number.isFinite(yearFromUrl) && yearFromUrl < currentYear ? currentYear : selectedYear;
  const canonicalSlug = slugifyNakshatra(nakshatraData?.slug || nakshatraName);
  const displayName = nakshatraData?.nakshatra || titleizeNakshatra(nakshatraName);
  const canonicalUrl = `${SITE_ORIGIN}/nakshatra/${canonicalSlug}/${canonicalYear}/`;

  useEffect(() => {
    if (Number.isFinite(yearFromUrl) && yearFromUrl < currentYear) {
      navigate(`/nakshatra/${nakshatraName}/${currentYear}/`, { replace: true });
    }
  }, [yearFromUrl, currentYear, nakshatraName, navigate]);

  useEffect(() => {
    if (Number.isFinite(yearFromUrl) && yearFromUrl < currentYear) return undefined;

    let cancelled = false;
    const fetchNakshatraData = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`/api/nakshatra/${encodeURIComponent(nakshatraName)}/${selectedYear}`);
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Failed to fetch nakshatra data');
        }
        const data = await response.json();
        if (!cancelled) setNakshatraData(data);
      } catch (fetchError) {
        if (!cancelled) setError(fetchError.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchNakshatraData();
    return () => { cancelled = true; };
  }, [nakshatraName, selectedYear, yearFromUrl, currentYear]);

  const handleYearChange = (newYear) => {
    const yearNum = parseInt(newYear, 10);
    setSelectedYear(yearNum);
    navigate(`/nakshatra/${nakshatraName}/${yearNum}/`);
  };

  const seoStructuredData = useMemo(() => ({
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Article',
        headline: `${displayName} Nakshatra ${selectedYear} calendar`,
        description: nakshatraData?.seo?.description || `${displayName} nakshatra dates, timings and Vedic properties for ${selectedYear}.`,
        url: canonicalUrl,
        isPartOf: { '@type': 'WebSite', name: 'AstroRoshni', url: SITE_ORIGIN }
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: `${SITE_ORIGIN}/` },
          { '@type': 'ListItem', position: 2, name: '27 Nakshatras', item: `${SITE_ORIGIN}/nakshatras` },
          { '@type': 'ListItem', position: 3, name: `${displayName} ${selectedYear}`, item: canonicalUrl }
        ]
      }
    ]
  }), [displayName, selectedYear, canonicalUrl, nakshatraData]);

  const sharedSeo = (
    <SEOHead
      title={nakshatraData?.seo?.title || `${displayName} Nakshatra ${selectedYear} | AstroRoshni`}
      description={nakshatraData?.seo?.description || `${displayName} nakshatra calendar and Vedic insights for ${selectedYear}.`}
      keywords={nakshatraData?.seo?.keywords}
      canonical={canonicalUrl}
      themeColor="#210b17"
      structuredData={seoStructuredData}
    />
  );

  if (loading || error || !nakshatraData) {
    return (
      <div className="nakshatra-page nakshatra-page--themed">
        {sharedSeo}
        <ModernNavigationHeader sticky user={user} onLogin={onLogin} onLogout={onLogout} onAdminClick={onAdminClick} />
        <main className="nakshatra-state" role={error ? 'alert' : 'status'}>
          <span className="nakshatra-state__orbit" aria-hidden="true" />
          <p>{error ? 'Calendar unavailable' : 'Reading the lunar calendar'}</p>
          <h1>{error ? 'The sky could not be loaded.' : `${displayName} · ${selectedYear}`}</h1>
          <span>{error || (!nakshatraData && !loading ? 'No data found.' : 'Calculating every begin and end time…')}</span>
          {error && <button type="button" onClick={() => window.location.reload()}>Try again</button>}
        </main>
      </div>
    );
  }

  const properties = nakshatraData.properties || {};
  const navigation = nakshatraData.navigation || {};
  const periods = nakshatraData.periods || [];

  return (
    <div className="nakshatra-page nakshatra-page--themed">
      {sharedSeo}
      <ModernNavigationHeader sticky user={user} onLogin={onLogin} onLogout={onLogout} onAdminClick={onAdminClick} />

      <main>
        <section className="nakshatra-detail-hero">
          <div className="nakshatra-detail-hero__copy">
            <button type="button" className="nakshatra-detail-back" onClick={() => navigate('/nakshatras')}>
              <span aria-hidden>←</span> All 27 Nakshatras
            </button>
            <p className="nakshatra-detail-eyebrow">Lunar mansion · {selectedYear}</p>
            <h1>{nakshatraData.nakshatra}<br /><em>Nakshatra.</em></h1>
            <p>{properties.description || 'An ancient lunar mansion with its own planetary ruler, deity, nature and quality of time.'}</p>
          </div>

          <div className="nakshatra-detail-hero__sigil" aria-label={`${nakshatraData.nakshatra} symbol ${properties.symbol || ''}`}>
            <div>
              <span>{properties.symbol || 'Lunar mansion'}</span>
              <strong>{String(periods.length).padStart(2, '0')}</strong>
              <small>transit windows</small>
            </div>
          </div>

          <div className="nakshatra-detail-hero__facts" aria-label="Nakshatra properties">
            <span><small>Lord</small><strong>{properties.lord || '—'}</strong></span>
            <span><small>Deity</small><strong>{properties.deity || '—'}</strong></span>
            <span><small>Nature</small><strong>{properties.nature || '—'}</strong></span>
            <span><small>Guna</small><strong>{properties.guna || '—'}</strong></span>
          </div>
        </section>

        <nav className="nakshatra-sibling-nav" aria-label="Previous and next nakshatra">
          <button type="button" onClick={() => navigate(`/nakshatra/${navigation.previous_slug || slugifyNakshatra(navigation.previous)}/${selectedYear}/`)}>
            <small>Previous mansion</small><strong><span aria-hidden>←</span> {navigation.previous}</strong>
          </button>
          <button type="button" onClick={() => navigate(`/nakshatra/${navigation.next_slug || slugifyNakshatra(navigation.next)}/${selectedYear}/`)}>
            <small>Next mansion</small><strong>{navigation.next} <span aria-hidden>→</span></strong>
          </button>
        </nav>

        <section className="nakshatra-calendar" aria-labelledby="nakshatra-calendar-title">
          <header className="nakshatra-calendar__header">
            <div>
              <p className="nakshatra-detail-eyebrow">Annual lunar calendar</p>
              <h2 id="nakshatra-calendar-title">Every {nakshatraData.nakshatra}<br /><em>window in {selectedYear}.</em></h2>
              <p>Begin and end times are calculated for {nakshatraData.location?.name || 'New Delhi, India'}.</p>
            </div>
            <div className="year-navigation" aria-label="Choose calendar year">
              <button
                type="button"
                onClick={() => handleYearChange(selectedYear - 1)}
                disabled={selectedYear <= currentYear}
                aria-label={selectedYear <= currentYear ? 'Earlier archived years redirect to the current calendar' : `View ${selectedYear - 1}`}
              >←</button>
              <span><small>Calendar year</small><strong>{selectedYear}</strong></span>
              <button type="button" onClick={() => handleYearChange(selectedYear + 1)} disabled={selectedYear >= currentYear + 5} aria-label={`View ${selectedYear + 1}`}>→</button>
            </div>
          </header>

          <ColorLegend />

          {periods.length === 0 ? (
            <div className="no-periods">No {nakshatraData.nakshatra} periods were found for {selectedYear}.</div>
          ) : (
            <div className="periods-list">
              {periods.map((period, index) => (
                <article key={`${period.start_datetime || period.start_date}-${index}`} className={`period-card ${period.auspiciousness || 'neutral'}`}>
                  <div className="period-card__index">{String(index + 1).padStart(2, '0')}</div>
                  <time className="period-date" dateTime={period.start_date}>
                    <strong>{period.day_number || new Date(period.start_datetime).getDate()}</strong>
                    <span>{period.month_name || new Date(period.start_datetime).toLocaleDateString('en-US', { month: 'short' })}</span>
                    <small>{period.weekday}</small>
                  </time>
                  <div className="period-content">
                    <div className="period-title">{nakshatraData.nakshatra} is active</div>
                    <div className="period-timing">
                      <span><small>Begins</small><strong>{period.start_time}</strong><em>{period.start_date}</em></span>
                      <i aria-hidden>→</i>
                      <span><small>Ends</small><strong>{period.end_time}</strong><em>{period.end_date}</em></span>
                    </div>
                  </div>
                  <span className="period-quality">{period.auspiciousness || 'Neutral'}</span>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="nakshatra-details" aria-labelledby="nakshatra-meaning-title">
          <div className="nakshatra-details__heading">
            <p className="nakshatra-detail-eyebrow">Character & expression</p>
            <h2 id="nakshatra-meaning-title">The meaning of<br /><em>{nakshatraData.nakshatra}.</em></h2>
          </div>
          <div className="characteristics-grid">
            <article className="char-card"><span>01</span><h3>Description</h3><p>{properties.description || 'Ancient lunar mansion with deep spiritual significance.'}</p></article>
            {properties.characteristics && <article className="char-card"><span>02</span><h3>Characteristics</h3><p>{properties.characteristics}</p></article>}
            {properties.positive_traits && <article className="char-card positive"><span>03</span><h3>Strengths</h3><p>{properties.positive_traits}</p></article>}
            {properties.negative_traits && <article className="char-card negative"><span>04</span><h3>Challenges</h3><p>{properties.negative_traits}</p></article>}
            {properties.careers && <article className="char-card"><span>05</span><h3>Career fields</h3><p>{properties.careers}</p></article>}
            {properties.compatibility && <article className="char-card"><span>06</span><h3>Compatibility</h3><p>{properties.compatibility}</p></article>}
          </div>
        </section>

        <aside className="footer-note">
          <strong>Timing reference</strong>
          <p>All timings use 12-hour local time for {nakshatraData.location?.name || 'the selected location'}, including daylight-saving adjustment where applicable. In Panchang, the day begins and ends at sunrise.</p>
        </aside>
      </main>
    </div>
  );
};

export default NakshatraPage;
