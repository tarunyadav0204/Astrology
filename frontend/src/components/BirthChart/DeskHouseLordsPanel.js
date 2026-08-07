import React, { useMemo } from 'react';
import { getPlanetDignity, houseLords } from '../../utils/planetAnalyzer';
import './DeskHouseLordsPanel.css';

const SIGN_ABBR = ['Ar', 'Ta', 'Ge', 'Cn', 'Le', 'Vi', 'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi'];
const PLANET_ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
  Gulika: 'Gu', Mandi: 'Md', InduLagna: 'IL',
};
const DIG_SHORT = { Exalted: 'Ex', Debilitated: 'Db', Own: 'Own', Neutral: '—' };
const TENANT_PLANETS = [
  'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu',
];

function houseOfPlanet(data, lagnaSign) {
  if (typeof data?.house === 'number') return data.house;
  if (typeof data?.sign !== 'number' || typeof lagnaSign !== 'number') return null;
  return ((data.sign - lagnaSign + 12) % 12) + 1;
}

/**
 * House → lord → seat → dignity → tenants. Core Parashari judgment map.
 */
export default function DeskHouseLordsPanel({ chartData }) {
  const rows = useMemo(() => {
    if (!chartData?.houses?.length && typeof chartData?.ascendant !== 'number') return [];
    const lagnaSign = chartData.houses?.[0]?.sign
      ?? (typeof chartData.ascendant === 'number' ? Math.floor((((chartData.ascendant % 360) + 360) % 360) / 30) : 0);

    const tenantsByHouse = {};
    TENANT_PLANETS.forEach((name) => {
      const data = chartData.planets?.[name];
      if (!data) return;
      const h = houseOfPlanet(data, lagnaSign);
      if (!h) return;
      if (!tenantsByHouse[h]) tenantsByHouse[h] = [];
      const mark = data.retrograde && name !== 'Rahu' && name !== 'Ketu' ? `${PLANET_ABBR[name]}(R)` : PLANET_ABBR[name];
      tenantsByHouse[h].push(mark);
    });

    return Array.from({ length: 12 }, (_, i) => {
      const house = i + 1;
      const sign = chartData.houses?.[i]?.sign ?? ((lagnaSign + i) % 12);
      const lord = houseLords[sign];
      const lordData = chartData.planets?.[lord];
      const lordHouse = houseOfPlanet(lordData, lagnaSign);
      const dig = lordData && typeof lordData.sign === 'number'
        ? getPlanetDignity(lord, lordData.sign)
        : 'Neutral';
      return {
        house,
        signAbbr: SIGN_ABBR[sign] || '—',
        lord: PLANET_ABBR[lord] || lord,
        lordFull: lord,
        lordHouse: lordHouse || '—',
        dig: DIG_SHORT[dig] || '—',
        digFull: dig,
        tenants: (tenantsByHouse[house] || []).join(' '),
      };
    });
  }, [chartData]);

  if (!rows.length) {
    return <div className="desk-lords desk-lords--status">No chart data</div>;
  }

  return (
    <div className="desk-lords" aria-label="House lord map">
      <table className="desk-lords__table">
        <thead>
          <tr>
            <th>H</th>
            <th>Sign</th>
            <th>Lord</th>
            <th>In</th>
            <th>Dig</th>
            <th>Tenants</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.house}
              className={row.digFull === 'Exalted' ? 'is-ex' : row.digFull === 'Debilitated' ? 'is-db' : undefined}
            >
              <td><strong>{row.house}</strong></td>
              <td>{row.signAbbr}</td>
              <td title={row.lordFull}>{row.lord}</td>
              <td>{row.lordHouse === '—' ? '—' : `H${row.lordHouse}`}</td>
              <td title={row.digFull}>{row.dig}</td>
              <td className="desk-lords__tenants">{row.tenants || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
