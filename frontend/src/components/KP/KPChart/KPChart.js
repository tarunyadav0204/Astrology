import React, { useState } from 'react';
import NorthIndianChart from '../../Charts/NorthIndianChart';
import SouthIndianChart from '../../Charts/SouthIndianChart';
import './KPChart.css';

/** Which Placidus house a longitude falls in (1–12). */
function houseFromLongitude(longitude, houses) {
  const lon = ((Number(longitude) % 360) + 360) % 360;
  for (let i = 1; i <= 12; i += 1) {
    const currentCusp = Number(houses.find((h) => h.number === i)?.cusp_longitude) || 0;
    const nextHouse = i === 12 ? 1 : i + 1;
    const nextCusp = Number(houses.find((h) => h.number === nextHouse)?.cusp_longitude) || 0;

    if (currentCusp < nextCusp) {
      if (lon >= currentCusp && lon < nextCusp) return i;
    } else if (lon >= currentCusp || lon < nextCusp) {
      return i;
    }
  }
  return 1;
}

const KPChart = ({
  chartData,
  birthData,
  deskMode = false,
  chartStyle: controlledChartStyle,
  onChartStyleChange,
}) => {
  const [internalChartStyle, setInternalChartStyle] = useState('north');
  const chartStyle = controlledChartStyle ?? internalChartStyle;
  const toggleChartStyle = () => {
    const nextStyle = chartStyle === 'north' ? 'south' : 'north';
    if (onChartStyleChange) onChartStyleChange(nextStyle);
    else setInternalChartStyle(nextStyle);
  };
  
  if (!chartData || !chartData.houses || !chartData.planets) {
    return (
      <div className={deskMode ? 'kp-chart-empty kp-chart-empty--desk' : 'kp-chart-empty'}>
        Chart data not available
      </div>
    );
  }

  const ascendantLongitude = chartData.houses.find((h) => h.number === 1)?.cusp_longitude || 0;

  // Placidus houses can share a zodiac sign (and skip others). Planet glyphs must
  // be keyed by house number — never by sign — or they render in every house
  // whose cusp falls in that same sign.
  const transformedData = {
    planets: {},
    houses: [],
    ascendant: ascendantLongitude,
  };

  chartData.planets.forEach((planet) => {
    // Ascendant is shown via the ASC marker; skip the duplicate "As" glyph.
    if (planet.name === 'Ascendant') return;

    const longitude = Number(planet.longitude) || 0;
    const houseNumber = houseFromLongitude(longitude, chartData.houses);

    transformedData.planets[planet.name] = {
      longitude,
      // Real zodiac sign (for nakshatra/degree helpers)
      sign: Math.floor(longitude / 30) % 12,
      // Occupied Placidus house — North/South charts place by this when set
      house: houseNumber,
      degree: longitude % 30,
      retrograde: !!planet.retrograde,
    };
  });

  chartData.houses.forEach((house) => {
    transformedData.houses[house.number - 1] = {
      longitude: house.cusp_longitude,
      sign: Math.floor(house.cusp_longitude / 30) % 12,
      degree: house.cusp_longitude % 30,
    };
  });

  const chartEl = chartStyle === 'north' ? (
    <NorthIndianChart 
      chartData={transformedData}
      chartType="kp"
      birthData={birthData}
      showDegreeNakshatra={!deskMode}
      showFooterHint={false}
      deskMode={deskMode}
    />
  ) : (
    <SouthIndianChart 
      chartData={transformedData}
      chartType="kp"
      birthData={birthData}
      showDegreeNakshatra={!deskMode}
      showFooterHint={false}
      deskMode={deskMode}
    />
  );

  if (deskMode) {
    return (
      <div className="kp-chart-container kp-chart-container--desk">
        <button
          type="button"
          className="kp-chart-desk-toggle"
          onClick={toggleChartStyle}
          title="North / South Indian"
        >
          {chartStyle === 'north' ? 'N' : 'S'}
        </button>
        <div className="kp-chart-desk-canvas">
          {chartEl}
        </div>
      </div>
    );
  }

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '1rem',
      boxShadow: '0 4px 16px rgba(0,0,0,0.1)'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem',
        paddingBottom: '0.5rem',
        borderBottom: '2px solid #e91e63'
      }}>
        <div>
          <h3 style={{ margin: 0, color: '#e91e63' }}>KP Chart (Placidus Houses)</h3>
          <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.3rem' }}>
            KP Ayanamsa • Placidus House System
          </div>
        </div>
        <button
          onClick={toggleChartStyle}
          style={{
            padding: '8px 16px',
            fontSize: '12px',
            background: 'white',
            color: '#666',
            border: '1px solid #ddd',
            borderRadius: '20px',
            cursor: 'pointer',
            fontWeight: '500'
          }}
        >
          {chartStyle === 'north' ? 'N' : 'S'}
        </button>
      </div>
      
      {chartEl}
    </div>
  );
};

export default KPChart;
