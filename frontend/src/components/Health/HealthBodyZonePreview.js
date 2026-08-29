import React from 'react';
import './HealthBodyZonePreview.css';

const FACTOR_LABELS = {
  sixth_house_sign: 'House 6 sign',
  sixth_lord_sign: '6th lord sign',
  sixth_lord_nakshatra: '6th lord nakshatra',
  sixth_lord_house: '6th lord house',
};

const DOSHA_ORDER = ['Vata', 'Pitta', 'Kapha'];

const HealthBodyZonePreview = ({ data, loading, compact = false }) => {
  const constitution = data?.constitution && !data.constitution.error ? data.constitution : null;
  const zones = data?.major_vulnerabilities || [];
  const limbs = data?.chain_limbs || [];
  const hasZones = zones.length > 0;

  if (loading && !constitution && !hasZones) {
    return (
      <section className={`health-body-zone-preview ${compact ? 'is-compact' : ''}`} aria-busy="true">
        <p className="health-body-zone-preview__status">
          Calculating constitution and sensitive body regions from your chart…
        </p>
      </section>
    );
  }

  if (!constitution && !hasZones) {
    return null;
  }

  const doshaBalance = constitution?.dosha_balance || {};

  return (
    <section className={`health-body-zone-preview ${compact ? 'is-compact' : ''}`}>
      {constitution && (
        <div className="health-constitution">
          <header className="health-body-zone-preview__header">
            <p className="health-body-zone-preview__eyebrow">From your birth chart</p>
            <h3>Constitution</h3>
            <p>
              Vata, Pitta, and Kapha from Lagna, Lagna lord, Moon, Sun, the
              6th house, and remaining grahas — graha dosha, sign element, and
              Moon nakshatra. An Ayurvedic tendency, not a medical prakriti diagnosis.
            </p>
          </header>
          <p className="health-constitution__label">{constitution.display || constitution.label}</p>
          <ul className="health-constitution__doshas">
            {DOSHA_ORDER.map((name) => {
              const value = Number(doshaBalance[name] || 0);
              return (
                <li key={name}>
                  <span className="health-constitution__name">{name}</span>
                  <span className="health-constitution__bar" aria-hidden>
                    <span style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
                  </span>
                  <span className="health-constitution__pct">{value.toFixed(0)}%</span>
                </li>
              );
            })}
          </ul>
          {constitution.summary && (
            <p className="health-constitution__summary">{constitution.summary}</p>
          )}
        </div>
      )}

      {hasZones && (
        <>
          <header className="health-body-zone-preview__header">
            {constitution
              ? <p className="health-body-zone-preview__eyebrow">Sensitive body regions</p>
              : <p className="health-body-zone-preview__eyebrow">From your birth chart</p>}
            <h3>{constitution ? 'Where the 6th-house chain points' : 'Sensitive body regions'}</h3>
            <p>
              These come from the 6th-house chain — House 6 sign, the 6th lord’s sign and
              nakshatra, and the house that lord occupies. They are chart susceptibilities
              for preventive attention, not a medical diagnosis.
            </p>
          </header>

          {limbs.length > 0 && (
            <ol className="health-body-zone-preview__chain">
              {limbs.map((limb) => (
                <li key={limb.factor}>
                  <span className="health-body-zone-preview__factor">
                    {limb.label || FACTOR_LABELS[limb.factor] || limb.factor}
                  </span>
                  <strong>{limb.anchor}</strong>
                  {limb.zones?.length > 0 && (
                    <span className="health-body-zone-preview__zones">
                      {limb.zones.join(', ')}
                    </span>
                  )}
                </li>
              ))}
            </ol>
          )}

          <ul className="health-body-zone-preview__regions">
            {zones.map((item, index) => {
              const reason = (item.primary_medical_reasons || item.why || [])[0];
              return (
                <li key={item.zone || index}>
                  <span className="health-body-zone-preview__rank">{index + 1}</span>
                  <div>
                    <h4>{item.zone}</h4>
                    {reason && <p>{reason}</p>}
                  </div>
                </li>
              );
            })}
          </ul>
        </>
      )}

      <p className="health-body-zone-preview__disclaimer">
        {[constitution?.disclaimer, data?.disclaimer].filter(Boolean).join(' ')}
      </p>
    </section>
  );
};

export default HealthBodyZonePreview;
