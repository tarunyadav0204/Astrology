import React from 'react';
import { CHART_CONFIG } from '../../config/dashboard.config';

const SouthIndianChart = ({ chartData }) => {
  const { signs, planets } = CHART_CONFIG;
  
  // South Indian chart house positions (square grid)
  const housePositions = [
    { x: 75, y: 75, width: 75, height: 75 },   // House 1
    { x: 150, y: 75, width: 75, height: 75 },  // House 2
    { x: 225, y: 75, width: 75, height: 75 },  // House 3
    { x: 225, y: 150, width: 75, height: 75 }, // House 4
    { x: 225, y: 225, width: 75, height: 75 }, // House 5
    { x: 150, y: 225, width: 75, height: 75 }, // House 6
    { x: 75, y: 225, width: 75, height: 75 },  // House 7
    { x: 0, y: 225, width: 75, height: 75 },   // House 8
    { x: 0, y: 150, width: 75, height: 75 },   // House 9
    { x: 0, y: 75, width: 75, height: 75 },    // House 10
    { x: 0, y: 0, width: 75, height: 75 },     // House 11
    { x: 75, y: 0, width: 75, height: 75 }     // House 12
  ];

  const getHouseNumber = (houseIndex) => {
    if (!chartData.houses || !chartData.houses[0]) return 1;
    const ascendantSign = Math.floor(chartData.houses[0].longitude / 30);
    return ((houseIndex + ascendantSign) % 12) + 1;
  };

  const getPlanetsInHouse = (houseNum) => {
    if (!chartData.planets) return [];
    
    return Object.entries(chartData.planets)
      .filter(([name, data]) => {
        const planetHouse = ((data.sign - Math.floor(chartData.houses[0].longitude / 30) + 12) % 12) + 1;
        return planetHouse === houseNum;
      })
      .map(([name]) => {
        const planetNames = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi'];
        const planetIndex = planetNames.indexOf(name);
        return planets[planetIndex] || name.substring(0, 2);
      });
  };

  return (
    <svg width="300" height="300" viewBox="0 0 300 300">
      {/* Chart grid */}
      <rect x="0" y="0" width="300" height="300" 
            fill="none" stroke="#333" strokeWidth="2"/>
      
      {/* Grid lines */}
      <line x1="75" y1="0" x2="75" y2="300" stroke="#333" strokeWidth="1"/>
      <line x1="150" y1="0" x2="150" y2="300" stroke="#333" strokeWidth="1"/>
      <line x1="225" y1="0" x2="225" y2="300" stroke="#333" strokeWidth="1"/>
      <line x1="0" y1="75" x2="300" y2="75" stroke="#333" strokeWidth="1"/>
      <line x1="0" y1="150" x2="300" y2="150" stroke="#333" strokeWidth="1"/>
      <line x1="0" y1="225" x2="300" y2="225" stroke="#333" strokeWidth="1"/>

      {/* Houses */}
      {housePositions.map((pos, index) => {
        const houseNum = getHouseNumber(index);
        const planetsInHouse = getPlanetsInHouse(houseNum);
        
        return (
          <g key={index}>
            {/* House number */}
            <text x={pos.x + 8} y={pos.y + 18} 
                  fontSize="14" fill="#666" fontWeight="bold">
              {houseNum}
            </text>
            
            {/* Sign */}
            <text x={pos.x + pos.width - 20} y={pos.y + 20} 
                  fontSize="14" fill="#666"
                  textAnchor="middle">
              {signs[index]}
            </text>
            
            {/* Planets */}
            {planetsInHouse.map((planet, pIndex) => {
              const totalPlanets = planetsInHouse.length;
              let planetX, planetY;
              
              if (totalPlanets === 1) {
                planetX = pos.x + pos.width / 2;
                planetY = pos.y + pos.height / 2 + 5;
              } else if (totalPlanets === 2) {
                planetX = pos.x + pos.width / 2 + (pIndex === 0 ? -18 : 18);
                planetY = pos.y + pos.height / 2 + 5;
              } else if (totalPlanets === 3) {
                const positions = [-22, 0, 22];
                planetX = pos.x + pos.width / 2 + positions[pIndex];
                planetY = pos.y + pos.height / 2 + 5;
              } else if (totalPlanets === 4) {
                const positions = [[-18, -8], [18, -8], [-18, 8], [18, 8]];
                planetX = pos.x + pos.width / 2 + positions[pIndex][0];
                planetY = pos.y + pos.height / 2 + positions[pIndex][1];
              } else {
                // Compact grid for 5+ planets
                const cols = Math.min(3, totalPlanets);
                const row = Math.floor(pIndex / cols);
                const col = pIndex % cols;
                
                const spacing = totalPlanets > 6 ? 15 : 20;
                planetX = pos.x + pos.width / 2 + (col - Math.floor(cols/2)) * spacing;
                planetY = pos.y + pos.height / 2 - 5 + (row * 12);
              }
              
              return (
                <text key={pIndex} 
                      x={planetX} 
                      y={planetY} 
                      fontSize={totalPlanets > 4 ? "13" : "16"} 
                      fill="#0066cc" 
                      fontWeight="bold"
                      textAnchor="middle">
                  {planet}
                </text>
              );
            })}
          </g>
        );
      })}
    </svg>
  );
};

export default SouthIndianChart;