import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { CHART_CONFIG } from '../../config/dashboard.config';
import NorthIndianChart from './NorthIndianChart';
import SouthIndianChart from './SouthIndianChart';
import { apiService } from '../../services/apiService';
import { WidgetContainer, WidgetHeader, WidgetTitle, StyleToggle, ChartContainer } from './ChartWidget.styles';
import AshtakavargaModal from '../Ashtakavarga/AshtakavargaModal';

const ChartWidget = ({ title, chartType, chartData, birthData, transitDate, division, defaultStyle }) => {
  const [chartStyle, setChartStyle] = useState(defaultStyle || 'north');
  const [showAshtakavarga, setShowAshtakavarga] = useState(false);
  const [showMaximized, setShowMaximized] = useState(false);
  const [showDegreeNakshatra, setShowDegreeNakshatra] = useState(true);
  const [showSpecialPoints, setShowSpecialPoints] = useState(false);
  const [specialPointsData, setSpecialPointsData] = useState(null);

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
  
  const handleSpecialPoints = async () => {
    if (!birthData) return;
    
    try {
      // Fetch Yogi data (includes Dagdha, Tithi Shunya, Avayogi)
      const yogiResponse = await apiService.calculateYogi(birthData);
      
      // Fetch Badhaka-Maraka data
      let badhakaResponse = null;
      try {
        badhakaResponse = await apiService.calculateBadhakaMaraka(chartData);
      } catch (error) {
        console.log('Badhaka-Maraka API not available:', error.message);
      }
      
      setSpecialPointsData({
        yogi: yogiResponse,
        badhaka: badhakaResponse
      });
      setShowSpecialPoints(true);
    } catch (error) {
      console.error('Failed to fetch special points:', error);
    }
  };
  
  return (
    <WidgetContainer>
      <WidgetHeader>
        <WidgetTitle>{title}</WidgetTitle>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <button
            onClick={() => setShowDegreeNakshatra(!showDegreeNakshatra)}
            style={{
              padding: '6px 10px',
              fontSize: '11px',
              background: 'white',
              color: showDegreeNakshatra ? '#e91e63' : '#666',
              border: `1px solid ${showDegreeNakshatra ? '#e91e63' : '#ddd'}`,
              borderRadius: '16px',
              cursor: 'pointer',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
            title={showDegreeNakshatra ? 'Hide degree and nakshatra' : 'Show degree and nakshatra'}
          >
            {isMobile ? (showDegreeNakshatra ? 'H' : 'S') : (showDegreeNakshatra ? 'Hide' : 'Show')}
          </button>
          <button 
            onClick={() => handleSpecialPoints()}
            style={{
              padding: '6px 10px',
              fontSize: '11px',
              background: 'white',
              color: '#666',
              border: '1px solid #ddd',
              borderRadius: '16px',
              cursor: 'pointer',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
            title="Show Dagdha Rasi, Tithi Shunya, Avayogi, Marka, Badhaka"
          >
            {isMobile ? 'SP' : 'Special'}
          </button>
          <button 
            onClick={() => setShowAshtakavarga(true)}
            style={{
              padding: '6px 10px',
              fontSize: '11px',
              background: 'white',
              color: '#666',
              border: '1px solid #ddd',
              borderRadius: '16px',
              cursor: 'pointer',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
          >
            {isMobile ? 'AV' : 'Ashtak'}
          </button>
          <StyleToggle onClick={toggleStyle}>
            {isMobile ? (chartStyle === 'north' ? 'N' : 'S') : CHART_CONFIG.styles[chartStyle]}
          </StyleToggle>
          <button 
            onClick={() => setShowMaximized(true)}
            style={{
              padding: '6px 10px',
              fontSize: '11px',
              background: 'white',
              color: '#666',
              border: '1px solid #ddd',
              borderRadius: '16px',
              cursor: 'pointer',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
            title="Maximize chart"
          >
            ⛶
          </button>
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
            showDegreeNakshatra={showDegreeNakshatra}
          />
        ) : (
          <SouthIndianChart 
            chartData={processedData}
            chartType={chartType}
            birthData={birthData}
            showDegreeNakshatra={showDegreeNakshatra}
          />
        )}
      </ChartContainer>
      
      <AshtakavargaModal 
        isOpen={showAshtakavarga}
        onClose={() => setShowAshtakavarga(false)}
        birthData={birthData}
        chartType={chartType}
        transitDate={transitDate}
      />
      
      {/* Special Points Modal */}
      {showSpecialPoints && createPortal(
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 20000,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }} onClick={() => setShowSpecialPoints(false)}>
          <div style={{
            backgroundColor: 'white', borderRadius: '12px', padding: '20px',
            maxWidth: '600px', width: '90%', maxHeight: '80vh', overflow: 'auto'
          }} onClick={e => e.stopPropagation()}>
            <h3 style={{ color: '#9c27b0', marginBottom: '20px' }}>Special Astrological Points</h3>
            
            {specialPointsData?.yogi && (
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ color: '#e91e63' }}>Yogi & Related Points</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', fontSize: '14px' }}>
                  <div>
                    <strong>Yogi:</strong> {specialPointsData.yogi.yogi.sign_name} {specialPointsData.yogi.yogi.degree}°
                  </div>
                  <div>
                    <strong>Avayogi:</strong> {specialPointsData.yogi.avayogi.sign_name} {specialPointsData.yogi.avayogi.degree}°
                  </div>
                  <div>
                    <strong>Dagdha Rashi:</strong> {specialPointsData.yogi.dagdha_rashi.sign_name} {specialPointsData.yogi.dagdha_rashi.degree}°
                  </div>
                  <div>
                    <strong>Tithi Shunya:</strong> {specialPointsData.yogi.tithi_shunya_rashi.sign_name} {specialPointsData.yogi.tithi_shunya_rashi.degree}°
                  </div>
                </div>
              </div>
            )}
            
            {specialPointsData?.badhaka && specialPointsData.badhaka.success && (
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ color: '#e91e63' }}>Badhaka & Maraka Analysis</h4>
                <div style={{ fontSize: '14px' }}>
                  {specialPointsData.badhaka.chart_analysis && (
                    <div>
                      <div style={{ marginBottom: '15px' }}>
                        <strong>Rasi Type:</strong> {specialPointsData.badhaka.chart_analysis.rasi_type}
                      </div>
                      
                      {specialPointsData.badhaka.chart_analysis.badhaka && (
                        <div style={{ marginBottom: '15px' }}>
                          <strong>Badhaka:</strong> House {specialPointsData.badhaka.chart_analysis.badhaka.house} (Lord: {specialPointsData.badhaka.chart_analysis.badhaka.lord})
                          <br />
                          <em>{specialPointsData.badhaka.chart_analysis.badhaka.effects?.description}</em>
                        </div>
                      )}
                      
                      {specialPointsData.badhaka.chart_analysis.maraka && (
                        <div>
                          <strong>Maraka Lords:</strong>
                          {specialPointsData.badhaka.chart_analysis.maraka.lords?.map((lord, idx) => (
                            <div key={idx} style={{ marginLeft: '10px' }}>
                              • {lord.planet} (House {lord.house}) - {lord.type}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
            

            
            <button 
              onClick={() => setShowSpecialPoints(false)}
              style={{ 
                marginTop: '15px', padding: '8px 16px', 
                backgroundColor: '#9c27b0', color: 'white', 
                border: 'none', borderRadius: '6px', cursor: 'pointer' 
              }}
            >
              Close
            </button>
          </div>
        </div>,
        document.body
      )}
      
      {/* Maximized Chart Modal - Rendered outside widget container */}
      {showMaximized && createPortal(
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.8)',
          zIndex: 10000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }} onClick={() => setShowMaximized(false)}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '20px',
            maxWidth: '90vw',
            maxHeight: '90vh',
            width: '800px',
            height: '800px',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
          }} onClick={e => e.stopPropagation()}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '20px',
              borderBottom: '2px solid #e91e63',
              paddingBottom: '10px'
            }}>
              <h3 style={{ margin: 0, color: '#e91e63' }}>{title}</h3>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <button
                  onClick={() => setShowDegreeNakshatra(!showDegreeNakshatra)}
                  style={{
                    padding: '8px 16px',
                    fontSize: '13px',
                    background: 'white',
                    color: showDegreeNakshatra ? '#e91e63' : '#666',
                    border: `1px solid ${showDegreeNakshatra ? '#e91e63' : '#ddd'}`,
                    borderRadius: '20px',
                    cursor: 'pointer',
                    fontWeight: '500',
                    transition: 'all 0.2s ease'
                  }}
                  title={showDegreeNakshatra ? 'Hide degree and nakshatra' : 'Show degree and nakshatra'}
                >
                  {showDegreeNakshatra ? 'Hide Details' : 'Show Details'}
                </button>
                <button 
                  onClick={() => handleSpecialPoints()}
                  style={{
                    padding: '8px 16px',
                    fontSize: '13px',
                    background: 'white',
                    color: '#666',
                    border: '1px solid #ddd',
                    borderRadius: '20px',
                    cursor: 'pointer',
                    fontWeight: '500',
                    transition: 'all 0.2s ease'
                  }}
                  title="Show Dagdha Rasi, Tithi Shunya, Avayogi, Marka, Badhaka"
                >
                  Special Points
                </button>
                <button 
                  onClick={() => setShowAshtakavarga(true)}
                  style={{
                    padding: '8px 16px',
                    fontSize: '13px',
                    background: 'white',
                    color: '#666',
                    border: '1px solid #ddd',
                    borderRadius: '20px',
                    cursor: 'pointer',
                    fontWeight: '500',
                    transition: 'all 0.2s ease'
                  }}
                >
                  Ashtakavarga
                </button>
                <button 
                  onClick={toggleStyle}
                  style={{
                    padding: '8px 16px',
                    fontSize: '13px',
                    background: 'white',
                    color: '#666',
                    border: '1px solid #ddd',
                    borderRadius: '20px',
                    cursor: 'pointer',
                    fontWeight: '500',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {CHART_CONFIG.styles[chartStyle]}
                </button>
                <button 
                  onClick={() => setShowMaximized(false)}
                  style={{
                    padding: '8px 16px',
                    fontSize: '16px',
                    background: '#e91e63',
                    color: 'white',
                    border: '1px solid #e91e63',
                    borderRadius: '20px',
                    cursor: 'pointer',
                    fontWeight: '500',
                    transition: 'all 0.2s ease'
                  }}
                >
                  ×
                </button>
              </div>
            </div>
            <div style={{ flex: 1, overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {loading ? (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: '#666' }}>
                  Calculating divisional chart...
                </div>
              ) : !divisionalData && (chartType === 'navamsa' || chartType === 'divisional') ? (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: '#e91e63' }}>
                  Failed to load divisional chart
                </div>
              ) : chartStyle === 'north' ? (
                <div style={{ width: '100%', height: '100%', minHeight: '600px' }}>
                  <NorthIndianChart 
                    chartData={processedData}
                    chartType={chartType}
                    birthData={birthData}
                    showDegreeNakshatra={showDegreeNakshatra}
                  />
                </div>
              ) : (
                <div style={{ width: '100%', height: '100%', minHeight: '600px' }}>
                  <SouthIndianChart 
                    chartData={processedData}
                    chartType={chartType}
                    birthData={birthData}
                    showDegreeNakshatra={showDegreeNakshatra}
                  />
                </div>
              )}
            </div>
          </div>
        </div>,
        document.body
      )}
    </WidgetContainer>
  );
};

export default ChartWidget;