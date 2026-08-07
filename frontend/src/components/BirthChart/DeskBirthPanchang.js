import React, { useEffect, useMemo, useState } from 'react';
import { apiService } from '../../services/apiService';
import './DeskBirthPanchang.css';

const PLANET_ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
};

function planetAbbr(name) {
  if (!name) return '';
  return PLANET_ABBR[name] || String(name).slice(0, 2);
}

function shortWeekday(name) {
  if (!name) return '—';
  const map = {
    Sunday: 'Sun', Monday: 'Mon', Tuesday: 'Tue', Wednesday: 'Wed',
    Thursday: 'Thu', Friday: 'Fri', Saturday: 'Sat',
  };
  return map[name] || String(name).slice(0, 3);
}

/**
 * Compact janma pañcāṅga strip for the Parashari desk (birth moment).
 */
export default function DeskBirthPanchang({ birthData }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!birthData?.date || birthData.latitude == null || birthData.longitude == null) {
      setData(null);
      return undefined;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await apiService.calculateBirthPanchang(birthData);
        if (!cancelled) {
          setData(res);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setData(null);
          setError(err?.response?.data?.detail || err.message || 'Failed to load birth panchang');
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [birthData]);

  const items = useMemo(() => {
    if (!data) return [];
    const list = [];
    const tithi = data.tithi;
    if (tithi?.name) {
      const paksha = tithi.paksha === 'Shukla' ? 'Śukla' : tithi.paksha === 'Krishna' ? 'Kṛṣṇa' : tithi.paksha;
      list.push({
        key: 'tithi',
        label: 'Tithi',
        value: `${tithi.name}${paksha ? ` · ${String(paksha).slice(0, 5)}` : ''}`,
        title: [
          tithi.name,
          paksha,
          tithi.lord ? `Lord ${tithi.lord}` : null,
          tithi.number != null ? `#${tithi.number}` : null,
        ].filter(Boolean).join(' · '),
        tone: 'tithi',
      });
    }
    const vara = data.vara;
    if (vara?.name) {
      list.push({
        key: 'vara',
        label: 'Vāra',
        value: `${shortWeekday(vara.name)}${vara.lord ? ` · ${planetAbbr(vara.lord)}` : ''}`,
        title: [vara.name, vara.lord ? `Lord ${vara.lord}` : null, vara.deity].filter(Boolean).join(' · '),
        tone: 'vara',
      });
    }
    const nak = data.nakshatra;
    if (nak?.name) {
      const shortNak = nak.name.length > 10 ? `${nak.name.slice(0, 8)}…` : nak.name;
      list.push({
        key: 'nak',
        label: 'Nak',
        value: `${shortNak}${nak.pada != null ? ` · P${nak.pada}` : ''}`,
        title: [
          nak.name,
          nak.pada != null ? `Pada ${nak.pada}` : null,
          nak.lord ? `Lord ${nak.lord}` : null,
        ].filter(Boolean).join(' · '),
        tone: 'nak',
      });
    }
    const yoga = data.yoga;
    if (yoga?.name) {
      const shortYoga = yoga.name.length > 10 ? `${yoga.name.slice(0, 8)}…` : yoga.name;
      list.push({
        key: 'yoga',
        label: 'Yoga',
        value: shortYoga,
        title: [yoga.name, yoga.quality, yoga.effect].filter(Boolean).join(' · '),
        tone: 'yoga',
      });
    }
    const karana = data.karana;
    if (karana?.name) {
      list.push({
        key: 'karana',
        label: 'Karaṇa',
        value: karana.name,
        title: [karana.name, karana.nature, karana.effect].filter(Boolean).join(' · '),
        tone: 'karana',
      });
    }
    return list;
  }, [data]);

  if (error) {
    return <div className="desk-bp desk-bp--strip desk-bp--error" title={String(error)}>Pañcāṅga</div>;
  }

  if (!items.length) {
    return (
      <div className="desk-bp desk-bp--strip desk-bp--empty" aria-hidden="true">
        <span className="desk-bp__strip-label">Birth</span>
      </div>
    );
  }

  return (
    <div className="desk-bp desk-bp--strip" aria-label="Birth panchanga">
      <span className="desk-bp__strip-label">Birth</span>
      <div className="desk-bp__chips">
        {items.map((item) => (
          <span
            key={item.key}
            className={`desk-bp__chip desk-bp__chip--${item.tone}`}
            title={item.title || `${item.label}: ${item.value}`}
          >
            <em>{item.label}</em>
            <strong>{item.value}</strong>
          </span>
        ))}
      </div>
    </div>
  );
}
