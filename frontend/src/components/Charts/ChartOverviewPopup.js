import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { apiService } from '../../services/apiService';
import './HouseInsightPopup.css';
import './ChartOverviewPopup.css';

const JUMP_LINKS = [
  { id: 'co-houses', label: 'Houses' },
  { id: 'co-pillars', label: 'Pillars' },
  { id: 'co-now', label: 'Now' },
  { id: 'co-marks', label: 'Marks' },
];

function prettyDignity(value) {
  if (!value) return '—';
  return String(value).replace(/_/g, ' ');
}

function ChartOverviewPopup({
  isOpen,
  onClose,
  birthData,
  chartId = 'lagna',
  transitDate,
  onOpenHouse,
  onOpenYogas,
}) {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const bodyRef = useRef(null);

  useEffect(() => {
    if (!isOpen || !birthData) {
      setOverview(null);
      setError('');
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    setError('');
    apiService
      .getChartOverview({ birthData, chartId, transitDate })
      .then((data) => {
        if (!cancelled) setOverview(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setOverview(null);
          setError(err?.response?.data?.detail || err.message || 'Failed to load chart overview');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [isOpen, birthData, chartId, transitDate]);

  if (!isOpen) return null;

  const scrollToSection = (id) => {
    bodyRef.current?.querySelector(`#${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const openHouse = (houseNumber) => {
    onOpenHouse?.(houseNumber);
  };

  const now = overview?.now || {};
  const houses = overview?.houses || [];
  const pillars = overview?.pillars || [];
  const marks = overview?.special_marks || [];

  return createPortal(
    <div className="house-insight-overlay" onClick={onClose} role="presentation">
      <aside
        className="house-insight-panel chart-overview-panel"
        role="dialog"
        aria-modal="true"
        aria-label="Chart overview"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="house-insight-handle" />
        <header className="house-insight-head">
          <span className="house-insight-badge">D1</span>
          <div>
            <h2>Chart reading</h2>
            <p>{overview?.lagna_sign ? `${overview.lagna_sign} lagna` : 'Whole kundli'}</p>
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
          {loading ? <div className="house-insight-status">Comparing the twelve houses…</div> : null}
          {error ? <div className="house-insight-status house-insight-status--err">{error}</div> : null}

          {overview?.summary ? (
            <section className="house-insight-sec">
              <h3>Verdict</h3>
              <p>{overview.summary}</p>
            </section>
          ) : null}

          <section className="house-insight-sec" id="co-houses">
            <h3>Houses</h3>
            <p className="house-insight-note">Tap a house for the full reading.</p>
            <div className="chart-overview-houses">
              {houses.map((row) => (
                <button
                  key={row.house}
                  type="button"
                  className={`chart-overview-house chart-overview-house--${row.tone || 'quiet'}${row.active ? ' is-active' : ''}`}
                  onClick={() => openHouse(row.house)}
                >
                  <em>H{row.house}</em>
                  <strong>{row.sign_name || '—'}</strong>
                  <span>{row.verdict?.label || '—'}</span>
                  {row.marks?.length ? <i>{row.marks.join(' · ')}</i> : null}
                </button>
              ))}
            </div>
          </section>

          <section className="house-insight-sec" id="co-pillars">
            <h3>Pillars</h3>
            <div className="chart-overview-pillars">
              {pillars.map((row) => (
                <button
                  key={`${row.role}-${row.planet}`}
                  type="button"
                  className="chart-overview-pillar"
                  onClick={() => row.house && openHouse(row.house)}
                >
                  <em>{row.role}</em>
                  <strong>{row.planet}</strong>
                  <span>
                    {[
                      row.sign_name,
                      row.house != null ? `H${row.house}` : null,
                      prettyDignity(row.dignity),
                    ].filter(Boolean).join(' · ')}
                  </span>
                  <span>
                    {row.shadbala_rupas != null
                      ? `${row.shadbala_rupas} / ${row.required_rupas ?? '—'} rupas`
                      : 'Shadbala pending'}
                    {row.meets_minimum === false ? ' · below' : row.meets_minimum ? ' · meets' : ''}
                    {row.retrograde ? ' · R' : ''}
                    {row.combust ? ' · combust' : ''}
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section className="house-insight-sec" id="co-now">
            <h3>Now</h3>
            <div className="house-insight-grid">
              <div>
                <em>Mahadasha</em>
                <strong>{now.mahadasha || '—'}</strong>
              </div>
              <div>
                <em>Antardasha</em>
                <strong>{now.antardasha || '—'}</strong>
              </div>
            </div>
            {now.houses?.length ? (
              <p className="house-insight-note">
                Lighting {now.houses.map((house) => `H${house}`).join(' · ')}
              </p>
            ) : null}
            <div className="chart-overview-now-houses">
              {(now.houses || []).map((house) => (
                <button key={house} type="button" onClick={() => openHouse(house)}>
                  H{house}
                </button>
              ))}
            </div>
            {(now.transits || []).length ? (
              <p className="house-insight-note">
                Transits on those houses: {now.transits.map((row) => `${row.planet} H${row.house}`).join(' · ')}
              </p>
            ) : null}
          </section>

          {marks.length ? (
            <section className="house-insight-sec" id="co-marks">
              <h3>Special marks</h3>
              <div className="chart-overview-marks">
                {marks.map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    className={`chart-overview-mark chart-overview-mark--${item.tone || 'point'}`}
                    title={item.title}
                    onClick={() => item.house && openHouse(item.house)}
                  >
                    <em>{item.label}</em>
                    <strong>{item.value}</strong>
                  </button>
                ))}
              </div>
            </section>
          ) : (
            <section className="house-insight-sec" id="co-marks">
              <h3>Special marks</h3>
              <p>No yogi, gandanta, mūlatrikona, or special-point hits are marked in this kundli.</p>
            </section>
          )}

          {onOpenYogas ? (
            <section className="house-insight-sec">
              <h3>Yogas</h3>
              <p className="house-insight-note">The full categorized list lives on the Yogas screen, not in this glance.</p>
              <button type="button" className="chart-overview-yoga-cta" onClick={onOpenYogas}>
                Open Yogas
              </button>
            </section>
          ) : null}
        </div>
      </aside>
    </div>
  );
}

export default ChartOverviewPopup;
