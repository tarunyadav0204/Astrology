import React, { useEffect, useMemo, useState } from 'react';
import { apiService } from '../../services/apiService';
import './DeskSpecialLagnas.css';

const SIGN_ABBR = {
  Aries: 'Ar', Taurus: 'Ta', Gemini: 'Ge', Cancer: 'Cn',
  Leo: 'Le', Virgo: 'Vi', Libra: 'Li', Scorpio: 'Sc',
  Sagittarius: 'Sg', Capricorn: 'Cp', Aquarius: 'Aq', Pisces: 'Pi',
};

const SIGN_NAMES = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
];

function signAbbr(v) {
  if (v == null) return '—';
  if (typeof v === 'number') return SIGN_ABBR[SIGN_NAMES[v]] || '—';
  return SIGN_ABBR[v] || String(v).slice(0, 2);
}

function houseFromSign(sign, lagnaSign) {
  if (typeof sign !== 'number' || typeof lagnaSign !== 'number') return null;
  return ((sign - lagnaSign + 12) % 12) + 1;
}

function resolveAk(karakas) {
  return (
    karakas?.chara_karakas?.Atmakaraka?.planet
    || karakas?.chara_karakas?.AK?.planet
    || karakas?.atmakaraka
    || Object.entries(karakas?.chara_karakas || {}).find(([k]) => /atma/i.test(k))?.[1]?.planet
  );
}

/**
 * AL / UL / A7 / Indu strip for marriage & career judgment.
 */
export default function DeskSpecialLagnas({ birthData, chartData }) {
  const [lagnas, setLagnas] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!birthData?.date || !chartData?.planets) {
      setLagnas(null);
      return undefined;
    }
    let cancelled = false;
    (async () => {
      try {
        const karakas = await apiService.calculateCharaKarakas(chartData, birthData);
        const ak = resolveAk(karakas);
        if (!ak) throw new Error('Atmakaraka not found');
        const res = await apiService.calculateJaiminiSpecialLagnas(chartData, ak);
        if (!cancelled) {
          setLagnas(res?.jaimini_lagnas || res || null);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setLagnas(null);
          setError(err?.response?.data?.detail || err.message || 'Failed');
        }
      }
    })();
    return () => { cancelled = true; };
  }, [birthData, chartData]);

  const items = useMemo(() => {
    const list = [];
    const lagnaSign = chartData?.houses?.[0]?.sign
      ?? (typeof chartData?.ascendant === 'number'
        ? Math.floor((((chartData.ascendant % 360) + 360) % 360) / 30)
        : null);

    const pushLagna = (key, label, point, tone) => {
      if (!point) return;
      const sign = typeof point.sign_id === 'number'
        ? point.sign_id
        : (typeof point.sign === 'number' ? point.sign : null);
      const signName = point.sign_name || (sign != null ? SIGN_NAMES[sign] : null);
      const house = point.house != null
        ? point.house
        : houseFromSign(sign, lagnaSign);
      list.push({
        key,
        label,
        value: `${signAbbr(signName || sign)}${house != null ? ` · H${house}` : ''}`,
        title: [label, signName, house != null ? `House ${house}` : null, point.description].filter(Boolean).join(' · '),
        tone,
      });
    };

    pushLagna('al', 'AL', lagnas?.arudha_lagna, 'al');
    pushLagna('ul', 'UL', lagnas?.upapada_lagna, 'ul');
    pushLagna('a7', 'A7', lagnas?.darapada, 'a7');

    const indu = chartData?.planets?.InduLagna;
    if (indu && typeof indu.sign === 'number') {
      const h = houseFromSign(indu.sign, lagnaSign);
      list.push({
        key: 'indu',
        label: 'Indu',
        value: `${signAbbr(indu.sign)}${h != null ? ` · H${h}` : ''}`,
        title: `Indu Lagna · ${SIGN_NAMES[indu.sign]}${h != null ? ` · House ${h}` : ''}`,
        tone: 'indu',
      });
    }

    return list;
  }, [lagnas, chartData]);

  if (error && !items.length) {
    return <div className="desk-lag desk-lag--strip desk-lag--error" title={String(error)}>Lagnas</div>;
  }

  if (!items.length) {
    return (
      <div className="desk-lag desk-lag--strip desk-lag--empty" aria-hidden="true">
        <span className="desk-lag__label">Lagnas</span>
      </div>
    );
  }

  return (
    <div className="desk-lag desk-lag--strip" aria-label="Special lagnas">
      <span className="desk-lag__label">Lagnas</span>
      <div className="desk-lag__chips">
        {items.map((item) => (
          <span
            key={item.key}
            className={`desk-lag__chip desk-lag__chip--${item.tone}`}
            title={item.title}
          >
            <em>{item.label}</em>
            <strong>{item.value}</strong>
          </span>
        ))}
      </div>
    </div>
  );
}
