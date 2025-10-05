import React, { useState } from 'react';
import { CHART_CONFIG } from '../../config/dashboard.config';
import NorthIndianChart from './NorthIndianChart';
import SouthIndianChart from './SouthIndianChart';
import { WidgetContainer, WidgetHeader, WidgetTitle, StyleToggle, ChartContainer } from './ChartWidget.styles';

const ChartWidget = ({ title, chartType, chartData, birthData, transitDate, division }) => {
  const [chartStyle, setChartStyle] = useState('north');

  const toggleStyle = () => {
    setChartStyle(prev => prev === 'north' ? 'south' : 'north');
  };

  const getChartData = () => {
    switch (chartType) {
      case 'lagna':
        return chartData;
      case 'navamsa':
        return calculateDivisionalChart(chartData, 9);
      case 'divisional':
        return calculateDivisionalChart(chartData, division || 9);
      case 'transit':
        return chartData;
      default:
        return chartData;
    }
  };

  const calculateDivisionalChart = (data, divisionNumber) => {
    const divisionalData = { ...data };
    
    // Calculate divisional ascendant first
    const ascendantLongitude = data.ascendant;
    const ascendantSign = Math.floor(ascendantLongitude / 30);
    const ascendantDegreeInSign = ascendantLongitude % 30;
    
    let divisionalAscendantSign = getDivisionalSign(ascendantSign, ascendantDegreeInSign, divisionNumber);
    const divisionalAscendant = divisionalAscendantSign * 30 + (ascendantDegreeInSign % (30/divisionNumber)) * divisionNumber;
    
    // Update ascendant
    divisionalData.ascendant = divisionalAscendant;
    
    // Recalculate houses based on new ascendant
    divisionalData.houses = [];
    for (let i = 0; i < 12; i++) {
      const houseSign = (divisionalAscendantSign + i) % 12;
      divisionalData.houses.push({
        longitude: (houseSign * 30) % 360,
        sign: houseSign
      });
    }
    
    // Calculate divisional positions for planets (including Gulika and Mandi)
    if (data.planets) {
      divisionalData.planets = {};
      Object.keys(data.planets).forEach(planet => {
        const longitude = data.planets[planet].longitude;
        const sign = Math.floor(longitude / 30);
        const degreeInSign = longitude % 30;
        
        const divisionalSign = getDivisionalSign(sign, degreeInSign, divisionNumber);
        const divisionalLongitude = divisionalSign * 30 + (degreeInSign % (30/divisionNumber)) * divisionNumber;
        
        divisionalData.planets[planet] = {
          ...data.planets[planet],
          longitude: divisionalLongitude,
          sign: divisionalSign,
          degree: divisionalLongitude % 30
        };
      });
    }
    return divisionalData;
  };
  
  const getDivisionalSign = (sign, degreeInSign, divisionNumber) => {
    const part = Math.floor(degreeInSign / (30/divisionNumber));
    
    switch (divisionNumber) {
      case 9: // Navamsa (D9)
        const navamsaStarts = [0, 0, 8, 8, 4, 4, 0, 0, 8, 8, 4, 4];
        return (navamsaStarts[sign] + part) % 12;
      
      case 10: // Dasamsa (D10)
        return sign % 2 === 1 ? (sign + part) % 12 : ((sign + 8) + part) % 12;
      
      case 12: // Dwadasamsa (D12)
        return (sign + part) % 12;
      
      case 16: // Shodasamsa (D16)
        return sign % 2 === 1 ? (sign + part) % 12 : ((sign + 8) + part) % 12;
      
      case 20: // Vimsamsa (D20)
        return sign % 2 === 1 ? (sign + part) % 12 : ((sign + 8) + part) % 12;
      
      case 24: // Chaturvimsamsa (D24)
        return sign % 2 === 1 ? ((sign + 4) + part) % 12 : ((sign + 8) + part) % 12;
      
      case 27: // Nakshatramsa (D27)
        const d27Starts = [0, 3, 6, 9, 0, 3, 6, 9, 0, 3, 6, 9];
        return (d27Starts[sign] + part) % 12;
      
      case 30: // Trimsamsa (D30)
        if (sign % 2 === 1) { // Odd signs
          if (part < 5) return 3; // Mars
          else if (part < 10) return 6; // Saturn  
          else if (part < 18) return 4; // Jupiter
          else if (part < 25) return 1; // Mercury
          else return 2; // Venus
        } else { // Even signs
          if (part < 5) return 2; // Venus
          else if (part < 12) return 1; // Mercury
          else if (part < 20) return 4; // Jupiter
          else if (part < 25) return 6; // Saturn
          else return 3; // Mars
        }
      
      case 40: // Khavedamsa (D40)
        return sign % 2 === 1 ? (sign + part) % 12 : ((sign + 8) + part) % 12;
      
      case 45: // Akshavedamsa (D45)
        return sign % 2 === 1 ? (sign + part) % 12 : ((sign + 8) + part) % 12;
      
      case 60: // Shashtyamsa (D60)
        return sign % 2 === 1 ? (sign + part) % 12 : ((sign + 8) + part) % 12;
      
      default:
        return (sign + part) % 12;
    }
  };

  const processedData = getChartData();
  
  // Ensure Gulika and Mandi are included in all chart types
  if (chartData && chartData.planets && !processedData.planets?.Gulika && chartData.planets.Gulika) {
    processedData.planets = processedData.planets || {};
    processedData.planets.Gulika = chartData.planets.Gulika;
    processedData.planets.Mandi = chartData.planets.Mandi;
  }

  return (
    <WidgetContainer>
      <WidgetHeader>
        <WidgetTitle>{title}</WidgetTitle>
        <StyleToggle onClick={toggleStyle}>
          {CHART_CONFIG.styles[chartStyle]}
        </StyleToggle>
      </WidgetHeader>
      
      <ChartContainer>
        {chartStyle === 'north' ? (
          <NorthIndianChart 
            chartData={processedData}
            chartType={chartType}
            birthData={birthData}
          />
        ) : (
          <SouthIndianChart 
            chartData={processedData}
            chartType={chartType}
            birthData={birthData}
          />
        )}
      </ChartContainer>
    </WidgetContainer>
  );
};

export default ChartWidget;