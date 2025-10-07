import React, { useState, useEffect } from 'react';
import { CHART_CONFIG } from '../../config/dashboard.config';
import NorthIndianChart from './NorthIndianChart';
import SouthIndianChart from './SouthIndianChart';
import { apiService } from '../../services/apiService';
import { WidgetContainer, WidgetHeader, WidgetTitle, StyleToggle, ChartContainer } from './ChartWidget.styles';
import AshtakavargaModal from '../Ashtakavarga/AshtakavargaModal';

const ChartWidget = ({ title, chartType, chartData, birthData, transitDate, division, defaultStyle }) => {
  const [chartStyle, setChartStyle] = useState(defaultStyle || 'north');
  const [showAshtakavarga, setShowAshtakavarga] = useState(false);

  // Update chart style when defaultStyle prop changes
  useEffect(() => {
    if (defaultStyle) {
      setChartStyle(defaultStyle);
    }
  }, [defaultStyle]);
  const [divisionalData, setDivisionalData] = useState(null);
  const [loading, setLoading] = useState(false);

  const toggleStyle = () => {
    setChartStyle(prev => prev === 'north' ? 'south' : 'north');
  };
  
  // Fetch divisional chart data from backend when needed
  useEffect(() => {
    if ((chartType === 'navamsa' || chartType === 'divisional') && birthData && chartData) {
      setLoading(true);
      const divisionNum = chartType === 'navamsa' ? 9 : (division || 9);
      
      // Always use backend for all divisional charts
      apiService.calculateDivisionalChart(birthData, divisionNum)
        .then(response => {
          setDivisionalData(response.divisional_chart);
        })
        .catch(error => {
          console.error('Failed to calculate divisional chart:', error);
          setDivisionalData(null);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [chartType, birthData, division, chartData]);

  const getChartData = () => {
    switch (chartType) {
      case 'lagna':
        return chartData;
      case 'navamsa':
      case 'divisional':
        return divisionalData || chartData;
      case 'transit':
        return chartData;
      default:
        return chartData;
    }
  };



  const processedData = getChartData();
  
  // Ensure Gulika and Mandi are included in all charts
  if (chartData && chartData.planets && !processedData.planets?.Gulika && chartData.planets.Gulika) {
    processedData.planets = processedData.planets || {};
    processedData.planets.Gulika = chartData.planets.Gulika;
    processedData.planets.Mandi = chartData.planets.Mandi;
  }

  const isMobile = window.innerWidth <= 768;
  
  return (
    <WidgetContainer>
      <WidgetHeader>
        <WidgetTitle>{title}</WidgetTitle>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={() => setShowAshtakavarga(true)}
            style={{
              padding: '4px 8px',
              fontSize: '12px',
              background: '#e91e63',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Ashtakavarga
          </button>
          <StyleToggle onClick={toggleStyle}>
            {isMobile ? (chartStyle === 'north' ? 'N' : 'S') : CHART_CONFIG.styles[chartStyle]}
          </StyleToggle>
        </div>
      </WidgetHeader>
      
      <ChartContainer>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px', color: '#666' }}>
            Calculating divisional chart...
          </div>
        ) : !divisionalData && (chartType === 'navamsa' || chartType === 'divisional') ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px', color: '#e91e63' }}>
            Failed to load divisional chart
          </div>
        ) : chartStyle === 'north' ? (
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
      
      <AshtakavargaModal 
        isOpen={showAshtakavarga}
        onClose={() => setShowAshtakavarga(false)}
        birthData={birthData}
        chartType={chartType}
      />
    </WidgetContainer>
  );
};

export default ChartWidget;