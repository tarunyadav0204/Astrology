import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { apiService } from '../../services/apiService';
import AshtakavargaModal from '../Ashtakavarga/AshtakavargaModal';
import ShadbalaModal from '../Shadbala/ShadbalaModal';
import './DeskToolModals.css';

/**
 * Desk-level strength/insight modals: Shadbala, Ashtakavarga, Chara Karakas, Dignities.
 */
export default function DeskToolModals({
  birthData,
  chartData,
  activeTool,
  onClose,
}) {
  const [dignitiesData, setDignitiesData] = useState(null);
  const [karakasData, setKarakasData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!activeTool || !birthData || !chartData) return undefined;
    if (activeTool !== 'dignities' && activeTool !== 'karakas') return undefined;
    let cancelled = false;
    setLoading(true);
    setError('');
    const req = activeTool === 'dignities'
      ? apiService.calculatePlanetaryDignities(chartData, birthData)
      : apiService.calculateCharaKarakas(chartData, birthData);
    req
      .then((data) => {
        if (cancelled) return;
        if (activeTool === 'dignities') setDignitiesData(data);
        else setKarakasData(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err?.response?.data?.detail || err.message || 'Failed to load');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeTool, birthData, chartData]);

  if (!activeTool) return null;

  if (activeTool === 'shadbala') {
    return <ShadbalaModal chartData={chartData} birthData={birthData} onClose={onClose} />;
  }

  if (activeTool === 'ashtakavarga') {
    return (
      <AshtakavargaModal
        isOpen
        onClose={onClose}
        birthData={birthData}
        chartType="lagna"
      />
    );
  }

  const title = activeTool === 'dignities' ? 'Planetary dignities' : 'Chara Karakas';

  return createPortal(
    <div className="desk-tool-overlay" onClick={onClose} role="presentation">
      <div className="desk-tool-modal" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <header className="desk-tool-modal__head">
          <h3>{title}</h3>
          <button type="button" onClick={onClose} aria-label="Close">×</button>
        </header>
        <div className="desk-tool-modal__body">
          {loading ? <p className="desk-tool-modal__status">Loading…</p> : null}
          {error ? <p className="desk-tool-modal__status desk-tool-modal__status--err">{error}</p> : null}

          {activeTool === 'dignities' && dignitiesData ? (
            <>
              {dignitiesData.summary ? (
                <div className="desk-tool-summary">
                  {dignitiesData.summary.exalted_planets?.length ? (
                    <div><em>Exalted</em><strong>{dignitiesData.summary.exalted_planets.join(', ')}</strong></div>
                  ) : null}
                  {dignitiesData.summary.debilitated_planets?.length ? (
                    <div><em>Debilitated</em><strong>{dignitiesData.summary.debilitated_planets.join(', ')}</strong></div>
                  ) : null}
                  {dignitiesData.summary.combust_planets?.length ? (
                    <div><em>Combust</em><strong>{dignitiesData.summary.combust_planets.join(', ')}</strong></div>
                  ) : null}
                  {dignitiesData.summary.retrograde_planets?.length ? (
                    <div><em>Retrograde</em><strong>{dignitiesData.summary.retrograde_planets.join(', ')}</strong></div>
                  ) : null}
                </div>
              ) : null}
              <div className="desk-tool-grid">
                {Object.entries(dignitiesData.dignities || {}).map(([planet, info]) => (
                  <div key={planet} className="desk-tool-card">
                    <strong>{planet}</strong>
                    <span>{info.dignity || info.state || info.status || '—'}</span>
                    {info.sign_name || info.sign != null ? (
                      <em>{info.sign_name || `Sign ${Number(info.sign) + 1}`}</em>
                    ) : null}
                  </div>
                ))}
              </div>
            </>
          ) : null}

          {activeTool === 'karakas' && karakasData ? (
            <>
              <p className="desk-tool-modal__meta">
                {karakasData.calculation_method || 'Jaimini'} · {karakasData.system || 'Chara Karakas'}
              </p>
              <div className="desk-tool-grid">
                {Object.entries(karakasData.chara_karakas || {}).map(([karaka, info]) => (
                  <div key={karaka} className="desk-tool-card desk-tool-card--karaka">
                    <strong>{karaka}</strong>
                    <span>{info.planet}</span>
                    <em>{info.title || (typeof info.description === 'string' ? info.description.slice(0, 80) : '') || `H${info.house ?? '—'}`}</em>
                  </div>
                ))}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>,
    document.body
  );
}
