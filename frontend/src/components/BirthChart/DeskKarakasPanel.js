import React, { useEffect, useMemo, useState } from 'react';
import { apiService } from '../../services/apiService';
import './DeskKarakasPanel.css';

const PLANET_ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
};

const KARAKA_ORDER = [
  { key: 'Atmakaraka', abbr: 'AK', tone: 'ak' },
  { key: 'Amatyakaraka', abbr: 'AmK', tone: 'amk' },
  { key: 'Bhratrukaraka', abbr: 'BK', tone: 'bk' },
  { key: 'Matrukaraka', abbr: 'MK', tone: 'mk' },
  { key: 'Pitrikaraka', abbr: 'PiK', tone: 'pik' },
  { key: 'Putrakaraka', abbr: 'PK', tone: 'pk' },
  { key: 'Gnatikaraka', abbr: 'GK', tone: 'gk' },
  { key: 'Darakaraka', abbr: 'DK', tone: 'dk' },
];

function planetAbbr(name) {
  if (!name) return '—';
  return PLANET_ABBR[name] || String(name).slice(0, 2);
}

function innerKarakas(payload) {
  if (!payload || typeof payload !== 'object') return {};
  if (payload.chara_karakas && typeof payload.chara_karakas === 'object') {
    return payload.chara_karakas;
  }
  return payload;
}

/**
 * Jaimini Chara Karaka strip for the Parashari desk.
 */
export default function DeskKarakasPanel({ birthData, chartData, onOpenTool }) {
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!birthData?.date || !chartData?.planets) {
      setPayload(null);
      return undefined;
    }
    let cancelled = false;
    apiService.calculateCharaKarakas(chartData, birthData)
      .then((data) => {
        if (!cancelled) {
          setPayload(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setPayload(null);
          setError(err?.response?.data?.detail || err.message || 'Failed');
        }
      });
    return () => {
      cancelled = true;
    };
  }, [birthData, chartData]);

  const items = useMemo(() => {
    const rows = innerKarakas(payload);
    return KARAKA_ORDER
      .map((meta) => {
        const info = rows[meta.key];
        if (!info?.planet) return null;
        const house = info.house != null ? Number(info.house) : null;
        return {
          ...meta,
          planet: info.planet,
          value: `${planetAbbr(info.planet)}${house ? ` · H${house}` : ''}`,
          title: [
            meta.key,
            info.title,
            info.planet,
            house ? `House ${house}` : null,
            info.degree_in_sign != null ? `${Number(info.degree_in_sign).toFixed(1)}° in sign` : null,
          ].filter(Boolean).join(' · '),
        };
      })
      .filter(Boolean);
  }, [payload]);

  if (error && !items.length) {
    return <div className="desk-ck desk-ck--strip desk-ck--error" title={String(error)}>Karakas</div>;
  }

  if (!items.length) {
    return (
      <div className="desk-ck desk-ck--strip desk-ck--empty" aria-hidden="true">
        <span className="desk-ck__label">Karakas</span>
      </div>
    );
  }

  return (
    <div className="desk-ck desk-ck--strip" aria-label="Jaimini Chara Karakas">
      <span className="desk-ck__label">Karakas</span>
      <div className="desk-ck__chips">
        {items.map((item) => {
          const Chip = onOpenTool ? 'button' : 'span';
          return (
            <Chip
              key={item.key}
              type={onOpenTool ? 'button' : undefined}
              className={`desk-ck__chip desk-ck__chip--${item.tone}`}
              title={item.title}
              onClick={onOpenTool ? () => onOpenTool('karakas') : undefined}
            >
              <em>{item.abbr}</em>
              <strong>{item.value}</strong>
            </Chip>
          );
        })}
      </div>
    </div>
  );
}
