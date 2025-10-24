import React, { useState } from 'react';
import NorthIndianChart from '../../Charts/NorthIndianChart';
import SouthIndianChart from '../../Charts/SouthIndianChart';

const KPChart = ({ chartData, birthData }) => {
  const [chartStyle, setChartStyle] = useState('north');
  
  if (!chartData || !chartData.houses || !chartData.planets) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '200px',
        color: '#dc3545',
        fontSize: '1rem',
        background: 'white',
        borderRadius: '12px',
        boxShadow: '0 4px 16px rgba(0,0,0,0.1)'
      }}>
        Chart data not available
      </div>
    );
  }

  // Get ascendant sign from 1st house cusp
  const ascendantLongitude = chartData.houses.find(h => h.number === 1)?.cusp_longitude || 0;
  
  // Transform data for North/South Indian charts
  const transformedData = {
    planets: {},
    houses: {}
  };

  // Add planets based on house cusps (bhav chalit style)
  chartData.planets.forEach(planet => {
    const longitude = planet.longitude;
    
    // Find which house this planet falls into based on house cusps
    let houseNumber = 1;
    for (let i = 1; i <= 12; i++) {
      const currentCusp = chartData.houses.find(h => h.number === i)?.cusp_longitude || 0;
      const nextHouse = i === 12 ? 1 : i + 1;
      const nextCusp = chartData.houses.find(h => h.number === nextHouse)?.cusp_longitude || 0;
      
      // Check if planet falls in this house
      if (currentCusp < nextCusp) {
        if (longitude >= currentCusp && longitude < nextCusp) {
          houseNumber = i;
          break;
        }
      } else { // House crosses 0 degrees
        if (longitude >= currentCusp || longitude < nextCusp) {
          houseNumber = i;
          break;
        }
      }
    }
    
    // Place planet in the house it occupies, not its zodiac sign
    const ascendantSign = Math.floor(ascendantLongitude / 30);
    const planetHouseSign = (ascendantSign + houseNumber - 1) % 12;
    
    transformedData.planets[planet.name] = {
      longitude: longitude,
      sign: planetHouseSign, // Use house-based sign, not zodiac sign
      degree: longitude % 30,
      retrograde: false
    };
  });

  // Add houses as object with house numbers as keys
  chartData.houses.forEach(house => {
    transformedData.houses[house.number - 1] = {
      longitude: house.cusp_longitude,
      sign: Math.floor(house.cusp_longitude / 30),
      degree: house.cusp_longitude % 30
    };
  });

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
          onClick={() => setChartStyle(prev => prev === 'north' ? 'south' : 'north')}
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
      
      {chartStyle === 'north' ? (
        <NorthIndianChart 
          chartData={transformedData}
          chartType="kp"
          birthData={birthData}
          showDegreeNakshatra={true}
        />
      ) : (
        <SouthIndianChart 
          chartData={transformedData}
          chartType="kp"
          birthData={birthData}
          showDegreeNakshatra={true}
        />
      )}
    </div>
  );
};

export default KPChart;