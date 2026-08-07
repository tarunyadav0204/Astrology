import React, { useEffect, useMemo, useState } from 'react';
import { apiService } from '../../services/apiService';
import './DeskYogasPanel.css';

const CATEGORY_LABELS = {
  raj_yogas: 'Raja',
  dhana_yogas: 'Dhana',
  mahapurusha_yogas: 'Mahāpuruṣa',
  neecha_bhanga_yogas: 'Neecha Bhaṅga',
  gaja_kesari_yogas: 'Gaja Kesari',
  amala_yogas: 'Amala',
  viparita_raja_yogas: 'Viparīta Raja',
  dharma_karma_yogas: 'Dharma-Karma',
  nabhasa_yogas: 'Nābhasa',
  chandra_yogas: 'Chandra',
  surya_yogas: 'Sūrya',
  career_specific_yogas: 'Career',
  health_yogas: 'Health',
  education_yogas: 'Education',
  marriage_yogas: 'Marriage',
  major_doshas: 'Doṣa',
};

function flattenYogas(payload) {
  if (!payload || typeof payload !== 'object') return [];
  const rows = [];
  Object.entries(payload).forEach(([key, value]) => {
    if (key === 'parivartana_yogas' && value && typeof value === 'object' && !Array.isArray(value)) {
      Object.entries(value).forEach(([subKey, list]) => {
        if (!Array.isArray(list)) return;
        list.forEach((yoga, idx) => {
          rows.push({
            id: `${subKey}-${idx}-${yoga.name || yoga.yoga_name || 'y'}`,
            category: 'Parivartana',
            name: yoga.name || yoga.yoga_name || subKey,
            strength: yoga.strength || yoga.intensity || yoga.grade || '',
            description: yoga.description || yoga.effects || yoga.effect || yoga.meaning || '',
            planets: yoga.planets || yoga.involved_planets || [],
          });
        });
      });
      return;
    }
    if (!Array.isArray(value)) return;
    value.forEach((yoga, idx) => {
      if (!yoga) return;
      // Skip false/empty markers
      if (yoga.present === false) return;
      rows.push({
        id: `${key}-${idx}-${yoga.name || yoga.yoga_name || 'y'}`,
        category: CATEGORY_LABELS[key] || key.replace(/_/g, ' '),
        name: yoga.name || yoga.yoga_name || yoga.type || CATEGORY_LABELS[key] || 'Yoga',
        strength: yoga.strength || yoga.intensity || yoga.grade || '',
        description: yoga.description || yoga.effects || yoga.effect || yoga.meaning || yoga.note || '',
        planets: yoga.planets || yoga.involved_planets || [],
      });
    });
  });
  return rows;
}

/**
 * Compact yogas list for Parashari desk (backend YogaCalculator).
 */
export default function DeskYogasPanel({ birthData }) {
  const [raw, setRaw] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    if (!birthData?.date || !birthData?.time) {
      setRaw(null);
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    setError('');
    apiService
      .getYogas(birthData)
      .then((data) => {
        if (!cancelled) setRaw(data?.yogas || data || null);
      })
      .catch((err) => {
        if (!cancelled) {
          setRaw(null);
          setError(err?.response?.data?.detail || err.message || 'Failed to load yogas');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [birthData]);

  const rows = useMemo(() => flattenYogas(raw), [raw]);
  const categories = useMemo(() => {
    const set = new Set(rows.map((r) => r.category));
    return ['all', ...Array.from(set)];
  }, [rows]);

  const visible = filter === 'all' ? rows : rows.filter((r) => r.category === filter);

  if (loading) return <div className="desk-yogas desk-yogas--status">Loading yogas…</div>;
  if (error) return <div className="desk-yogas desk-yogas--status desk-yogas--err">{error}</div>;
  if (!rows.length) return <div className="desk-yogas desk-yogas--status">No classical yogas flagged</div>;

  return (
    <div className="desk-yogas" aria-label="Classical yogas">
      <div className="desk-yogas__filters">
        {categories.map((cat) => (
          <button
            key={cat}
            type="button"
            className={filter === cat ? 'is-active' : ''}
            onClick={() => setFilter(cat)}
          >
            {cat === 'all' ? `All (${rows.length})` : cat}
          </button>
        ))}
      </div>
      <ul className="desk-yogas__list">
        {visible.map((yoga) => (
          <li key={yoga.id}>
            <div className="desk-yogas__row">
              <strong>{yoga.name}</strong>
              <span className="desk-yogas__cat">{yoga.category}</span>
              {yoga.strength ? <em>{yoga.strength}</em> : null}
            </div>
            {yoga.planets?.length ? (
              <div className="desk-yogas__planets">
                {(Array.isArray(yoga.planets) ? yoga.planets : [yoga.planets]).map((p) => (
                  <span key={String(p)}>{typeof p === 'string' ? p : p.name || p.planet}</span>
                ))}
              </div>
            ) : null}
            {yoga.description ? <p>{String(yoga.description).slice(0, 160)}</p> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
