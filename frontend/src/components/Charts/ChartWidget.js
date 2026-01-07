import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { CHART_CONFIG } from '../../config/dashboard.config';
import NorthIndianChart from './NorthIndianChart';
import SouthIndianChart from './SouthIndianChart';
import { apiService } from '../../services/apiService';
import { WidgetContainer, WidgetHeader, WidgetTitle, StyleToggle, ChartContainer } from './ChartWidget.styles';
import AshtakavargaModal from '../Ashtakavarga/AshtakavargaModal';
import ShadbalaModal from '../Shadbala/ShadbalaModal';

const ChartWidget = ({ title, chartType, chartData, birthData, transitDate, division, defaultStyle, chartRefHighlight = null }) => {
  const [chartStyle, setChartStyle] = useState(defaultStyle || 'north');
  const [showAshtakavarga, setShowAshtakavarga] = useState(false);
  const [showMaximized, setShowMaximized] = useState(false);
  const [showDegreeNakshatra, setShowDegreeNakshatra] = useState(true);
  const [showSpecialPoints, setShowSpecialPoints] = useState(false);
  const [specialPointsData, setSpecialPointsData] = useState(null);
  const [showPlanetaryDignities, setShowPlanetaryDignities] = useState(false);
  const [dignitiesData, setDignitiesData] = useState(null);
  const [showCharaKarakas, setShowCharaKarakas] = useState(false);
  const [charaKarakasData, setCharaKarakasData] = useState(null);
  const [showShadbala, setShowShadbala] = useState(false);

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
      
      console.log('🌐 [WEB] Requesting divisional chart:', {
        chartType,
        division: divisionNum,
        birthData: {
          name: birthData.name,
          date: birthData.date,
          time: birthData.time,
          latitude: birthData.latitude,
          longitude: birthData.longitude,
          timezone: birthData.timezone
        }
      });
      
      // Always use backend for all divisional charts
      apiService.calculateDivisionalChart(birthData, divisionNum)
        .then(response => {
          console.log('✅ [WEB] Received divisional chart:', {
            division: divisionNum,
            ascendant: response.divisional_chart?.ascendant,
            ascendant_sign: Math.floor(response.divisional_chart?.ascendant / 30),
            houses: response.divisional_chart?.houses?.map(h => ({ house: h.house_number, sign: h.sign }))
          });
          setDivisionalData(response.divisional_chart);
        })
        .catch(error => {
          console.error('❌ [WEB] Failed to calculate divisional chart:', error);
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
  
  const handlePlanetaryDignities = async () => {
    if (!birthData) return;
    
    try {
      // Use the processed chart data (which includes divisional charts)
      const currentChartData = getChartData();
      if (!currentChartData) return;
      
      const response = await apiService.calculatePlanetaryDignities(currentChartData, birthData);
      setDignitiesData(response);
      setShowPlanetaryDignities(true);
    } catch (error) {
      console.error('Failed to fetch planetary dignities:', error);
    }
  };
  
  const handleCharaKarakas = async () => {
    if (!birthData) return;
    
    try {
      // Use the processed chart data
      const currentChartData = getChartData();
      if (!currentChartData) return;
      
      const response = await apiService.calculateCharaKarakas(currentChartData, birthData);
      setCharaKarakasData(response);
      setShowCharaKarakas(true);
    } catch (error) {
      console.error('Failed to fetch Chara Karakas:', error);
    }
  };
  
  return (
    <WidgetContainer>
      <WidgetHeader>
        <WidgetTitle title={title}>{title}</WidgetTitle>
        <div style={{ display: 'flex', gap: '4px', alignItems: 'center', flexShrink: 0, flexWrap: 'nowrap', overflow: 'hidden' }}>
          <button
            onClick={() => setShowDegreeNakshatra(!showDegreeNakshatra)}
            style={{
              padding: '4px 8px',
              fontSize: '10px',
              background: 'white',
              color: showDegreeNakshatra ? '#e91e63' : '#666',
              border: `1px solid ${showDegreeNakshatra ? '#e91e63' : '#ddd'}`,
              borderRadius: '12px',
              cursor: 'pointer',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
            title={showDegreeNakshatra ? 'Hide degree and nakshatra' : 'Show degree and nakshatra'}
          >
            {isMobile ? (showDegreeNakshatra ? 'H' : 'S') : (showDegreeNakshatra ? 'Hide' : 'Show')}
          </button>
          {chartType === 'lagna' && (
            <button 
              onClick={() => handleSpecialPoints()}
              style={{
                padding: '4px 8px',
                fontSize: '10px',
                background: 'white',
                color: '#666',
                border: '1px solid #ddd',
                borderRadius: '12px',
                cursor: 'pointer',
                fontWeight: '500',
                transition: 'all 0.2s ease'
              }}
              title="Show Dagdha Rasi, Tithi Shunya, Avayogi, Marka, Badhaka"
            >
              {isMobile ? 'SP' : 'Special'}
            </button>
          )}
          <button 
            onClick={() => handlePlanetaryDignities()}
            style={{
              padding: '4px 8px',
              fontSize: '10px',
              background: 'white',
              color: '#666',
              border: '1px solid #ddd',
              borderRadius: '12px',
              cursor: 'pointer',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
            title="Show Planetary Dignities & States"
          >
            {isMobile ? 'PD' : 'Dignities'}
          </button>
          {chartType === 'lagna' && (
            <button 
              onClick={() => handleCharaKarakas()}
              style={{
                padding: '4px 8px',
                fontSize: '10px',
                background: 'white',
                color: '#666',
                border: '1px solid #ddd',
                borderRadius: '12px',
                cursor: 'pointer',
                fontWeight: '500',
                transition: 'all 0.2s ease'
              }}
              title="Show Chara Karakas (Jaimini Significators)"
            >
              {isMobile ? 'CK' : 'Karakas'}
            </button>
          )}
          <button 
            onClick={() => setShowShadbala(true)}
            style={{
              padding: '4px 8px',
              fontSize: '10px',
              background: 'white',
              color: '#666',
              border: '1px solid #ddd',
              borderRadius: '12px',
              cursor: 'pointer',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
            title="Show Shadbala (Planetary Strength)"
          >
            {isMobile ? 'SB' : 'Shadbala'}
          </button>
          <button 
            onClick={() => setShowAshtakavarga(true)}
            style={{
              padding: '4px 8px',
              fontSize: '10px',
              background: 'white',
              color: '#666',
              border: '1px solid #ddd',
              borderRadius: '12px',
              cursor: 'pointer',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
          >
            {isMobile ? 'AV' : 'Ashtak'}
          </button>
          <StyleToggle onClick={toggleStyle}>
            {chartStyle === 'north' ? 'N' : 'S'}
          </StyleToggle>
          {!isMobile && (
            <button 
              onClick={() => setShowMaximized(true)}
              style={{
                padding: '4px 8px',
                fontSize: '10px',
                background: 'white',
                color: '#666',
                border: '1px solid #ddd',
                borderRadius: '12px',
                cursor: 'pointer',
                fontWeight: '500',
                transition: 'all 0.2s ease'
              }}
              title="Maximize chart"
            >
              ⛶
            </button>
          )}
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
      
      {showShadbala && (
        <ShadbalaModal
          chartData={getChartData()}
          birthData={birthData}
          onClose={() => setShowShadbala(false)}
        />
      )}
      
      {/* Special Points Modal */}
      {showSpecialPoints && createPortal(
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 100002,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }} onClick={() => setShowSpecialPoints(false)}>
          <div style={{
            backgroundColor: 'white', borderRadius: '12px',
            maxWidth: '700px', width: '90%', maxHeight: '80vh',
            display: 'flex', flexDirection: 'column'
          }} onClick={e => e.stopPropagation()}>
            <div style={{
              padding: '20px 20px 0 20px',
              borderBottom: '1px solid #e0e0e0',
              flexShrink: 0
            }}>
              <h3 style={{ color: '#9c27b0', margin: 0 }}>Special Astrological Points</h3>
            </div>
            <div style={{
              padding: '20px',
              overflow: 'auto',
              flex: 1
            }}>
              {specialPointsData?.yogi && (
                <div style={{ marginBottom: '25px' }}>
                  <h4 style={{ color: '#e91e63', marginBottom: '15px', fontSize: '16px', borderBottom: '2px solid #e91e63', paddingBottom: '5px' }}>Yogi & Related Points</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '15px' }}>
                    <div style={{
                      padding: '12px',
                      border: '1px solid #e91e63',
                      borderRadius: '8px',
                      backgroundColor: '#fef7f7'
                    }}>
                      <div style={{ fontWeight: 'bold', color: '#e91e63', marginBottom: '5px' }}>Yogi Point</div>
                      <div style={{ fontSize: '14px' }}>{specialPointsData.yogi.yogi.sign_name} {specialPointsData.yogi.yogi.degree}°</div>
                      <div style={{ fontSize: '12px', color: '#666', marginTop: '3px' }}>Beneficial point for spiritual growth</div>
                    </div>
                    <div style={{
                      padding: '12px',
                      border: '1px solid #ff9800',
                      borderRadius: '8px',
                      backgroundColor: '#fff8f0'
                    }}>
                      <div style={{ fontWeight: 'bold', color: '#ff9800', marginBottom: '5px' }}>Avayogi Point</div>
                      <div style={{ fontSize: '14px' }}>{specialPointsData.yogi.avayogi.sign_name} {specialPointsData.yogi.avayogi.degree}°</div>
                      <div style={{ fontSize: '12px', color: '#666', marginTop: '3px' }}>Point of obstacles and challenges</div>
                    </div>
                    <div style={{
                      padding: '12px',
                      border: '1px solid #f44336',
                      borderRadius: '8px',
                      backgroundColor: '#fef5f5'
                    }}>
                      <div style={{ fontWeight: 'bold', color: '#f44336', marginBottom: '5px' }}>Dagdha Rashi</div>
                      <div style={{ fontSize: '14px' }}>{specialPointsData.yogi.dagdha_rashi.sign_name} {specialPointsData.yogi.dagdha_rashi.degree}°</div>
                      <div style={{ fontSize: '12px', color: '#666', marginTop: '3px' }}>Burnt/afflicted sign to avoid</div>
                    </div>
                    <div style={{
                      padding: '12px',
                      border: '1px solid #9c27b0',
                      borderRadius: '8px',
                      backgroundColor: '#f8f5f9'
                    }}>
                      <div style={{ fontWeight: 'bold', color: '#9c27b0', marginBottom: '5px' }}>Tithi Shunya</div>
                      <div style={{ fontSize: '14px' }}>{specialPointsData.yogi.tithi_shunya_rashi.sign_name} {specialPointsData.yogi.tithi_shunya_rashi.degree}°</div>
                      <div style={{ fontSize: '12px', color: '#666', marginTop: '3px' }}>Void sign based on birth Tithi</div>
                    </div>
                  </div>
                </div>
              )}
              
              {specialPointsData?.badhaka && specialPointsData.badhaka.success && (
                <div style={{ marginBottom: '20px' }}>
                  <h4 style={{ color: '#e91e63', marginBottom: '15px', fontSize: '16px', borderBottom: '2px solid #e91e63', paddingBottom: '5px' }}>Badhaka & Maraka Analysis</h4>
                  <div style={{
                    padding: '15px',
                    border: '1px solid #e0e0e0',
                    borderRadius: '8px',
                    backgroundColor: '#fafafa'
                  }}>
                    {specialPointsData.badhaka.chart_analysis && (
                      <div>
                        <div style={{ marginBottom: '15px', padding: '8px', backgroundColor: '#e3f2fd', borderRadius: '4px' }}>
                          <strong style={{ color: '#1976d2' }}>Rasi Type:</strong> <span style={{ marginLeft: '8px' }}>{specialPointsData.badhaka.chart_analysis.rasi_type}</span>
                        </div>
                        
                        {specialPointsData.badhaka.chart_analysis.badhaka && (
                          <div style={{ marginBottom: '15px', padding: '10px', border: '1px solid #ff9800', borderRadius: '6px', backgroundColor: '#fff8f0' }}>
                            <div style={{ fontWeight: 'bold', color: '#ff9800', marginBottom: '8px' }}>Badhaka (Obstacle) Analysis</div>
                            <div style={{ fontSize: '14px', marginBottom: '5px' }}>
                              <strong>House:</strong> {specialPointsData.badhaka.chart_analysis.badhaka.house} | 
                              <strong style={{ marginLeft: '10px' }}>Lord:</strong> {specialPointsData.badhaka.chart_analysis.badhaka.lord}
                            </div>
                            {specialPointsData.badhaka.chart_analysis.badhaka.effects?.description && (
                              <div style={{ fontSize: '13px', color: '#666', fontStyle: 'italic', marginTop: '8px', lineHeight: '1.4' }}>
                                {specialPointsData.badhaka.chart_analysis.badhaka.effects.description}
                              </div>
                            )}
                          </div>
                        )}
                        
                        {specialPointsData.badhaka.chart_analysis.maraka && (
                          <div style={{ padding: '10px', border: '1px solid #f44336', borderRadius: '6px', backgroundColor: '#fef5f5' }}>
                            <div style={{ fontWeight: 'bold', color: '#f44336', marginBottom: '8px' }}>Maraka (Death-inflicting) Lords</div>
                            {specialPointsData.badhaka.chart_analysis.maraka.lords?.map((lord, idx) => (
                              <div key={idx} style={{
                                padding: '6px 10px',
                                margin: '4px 0',
                                backgroundColor: 'white',
                                borderRadius: '4px',
                                fontSize: '13px',
                                border: '1px solid #ffcdd2'
                              }}>
                                <strong>{lord.planet}</strong> - House {lord.house} ({lord.type})
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
            <div style={{
              padding: '15px 20px',
              borderTop: '1px solid #e0e0e0',
              flexShrink: 0,
              display: 'flex',
              justifyContent: 'flex-end'
            }}>
              <button 
                onClick={() => setShowSpecialPoints(false)}
                style={{ 
                  padding: '8px 16px', 
                  backgroundColor: '#9c27b0', color: 'white', 
                  border: 'none', borderRadius: '6px', cursor: 'pointer' 
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
      
      {/* Chara Karakas Modal */}
      {showCharaKarakas && createPortal(
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 100002,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }} onClick={() => setShowCharaKarakas(false)}>
          <div style={{
            backgroundColor: 'white', borderRadius: '12px',
            maxWidth: '800px', width: '90%', maxHeight: '80vh',
            display: 'flex', flexDirection: 'column'
          }} onClick={e => e.stopPropagation()}>
            <div style={{
              padding: '20px 20px 0 20px',
              borderBottom: '1px solid #e0e0e0',
              flexShrink: 0
            }}>
              <h3 style={{ color: '#9c27b0', margin: 0 }}>
                Chara Karakas (Jaimini Significators)
                {chartType !== 'lagna' && (
                  <span style={{ fontSize: '14px', fontWeight: 'normal', color: '#666', marginLeft: '10px' }}>
                    ({chartType === 'navamsa' ? 'Navamsa (D9)' : 
                      chartType === 'divisional' ? `D${division || 9}` : 
                      chartType === 'transit' ? 'Transit' : title})
                  </span>
                )}
              </h3>
            </div>
            <div style={{
              padding: '20px',
              overflow: 'auto',
              flex: 1
            }}>
              {charaKarakasData && (
                <div>
                  <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#f0f8ff', borderRadius: '6px', fontSize: '13px' }}>
                    <strong>Calculation Method:</strong> {charaKarakasData.calculation_method}<br/>
                    <strong>System:</strong> {charaKarakasData.system}
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '15px' }}>
                    {Object.entries(charaKarakasData.chara_karakas || {}).map(([karaka, info]) => (
                      <div key={karaka} style={{
                        border: '2px solid #e91e63',
                        borderRadius: '10px',
                        padding: '15px',
                        backgroundColor: '#fafafa'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                          <h4 style={{ margin: 0, color: '#e91e63', fontSize: '16px' }}>{karaka}</h4>
                          <span style={{
                            padding: '4px 10px',
                            borderRadius: '15px',
                            fontSize: '12px',
                            fontWeight: 'bold',
                            backgroundColor: '#e91e63',
                            color: 'white'
                          }}>
                            {info.planet}
                          </span>
                        </div>
                        
                        <div style={{ fontSize: '13px', marginBottom: '10px' }}>
                          <strong>{info.title}</strong>
                        </div>
                        
                        <div style={{ fontSize: '12px', color: '#666', marginBottom: '10px', lineHeight: '1.4' }}>
                          {info.description}
                        </div>
                        
                        <div style={{ fontSize: '12px', marginBottom: '10px' }}>
                          <strong>Position:</strong> {info.degree_in_sign}° in House {info.house} (Sign {info.sign + 1})
                        </div>
                        
                        <div style={{ fontSize: '12px' }}>
                          <strong>Life Areas:</strong>
                          <div style={{ marginTop: '5px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                            {info.life_areas?.map((area, idx) => (
                              <span key={idx} style={{
                                padding: '2px 6px',
                                borderRadius: '8px',
                                fontSize: '10px',
                                backgroundColor: '#e3f2fd',
                                color: '#1976d2',
                                border: '1px solid #bbdefb'
                              }}>
                                {area}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div style={{
              padding: '15px 20px',
              borderTop: '1px solid #e0e0e0',
              flexShrink: 0,
              display: 'flex',
              justifyContent: 'flex-end'
            }}>
              <button 
                onClick={() => setShowCharaKarakas(false)}
                style={{ 
                  padding: '8px 16px', 
                  backgroundColor: '#9c27b0', color: 'white', 
                  border: 'none', borderRadius: '6px', cursor: 'pointer' 
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
      
      {/* Planetary Dignities Modal */}
      {showPlanetaryDignities && createPortal(
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 100002,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }} onClick={() => setShowPlanetaryDignities(false)}>
          <div style={{
            backgroundColor: 'white', borderRadius: '12px',
            maxWidth: '800px', width: '90%', maxHeight: '80vh',
            display: 'flex', flexDirection: 'column'
          }} onClick={e => e.stopPropagation()}>
            <div style={{
              padding: '20px 20px 0 20px',
              borderBottom: '1px solid #e0e0e0',
              flexShrink: 0
            }}>
              <h3 style={{ color: '#9c27b0', margin: 0 }}>
                Planetary Dignities & States
                {chartType !== 'lagna' && (
                  <span style={{ fontSize: '14px', fontWeight: 'normal', color: '#666', marginLeft: '10px' }}>
                    ({chartType === 'navamsa' ? 'Navamsa (D9)' : 
                      chartType === 'divisional' ? `D${division || 9}` : 
                      chartType === 'transit' ? 'Transit' : title})
                  </span>
                )}
              </h3>
            </div>
            <div style={{
              padding: '20px',
              overflow: 'auto',
              flex: 1
            }}>
            
            {dignitiesData && (
              <div>
                {/* Summary Section */}
                {dignitiesData.summary && (
                  <div style={{ marginBottom: '25px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                    <h4 style={{ color: '#e91e63', marginBottom: '15px' }}>Summary</h4>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', fontSize: '13px' }}>
                      {dignitiesData.summary.strongest_planets?.length > 0 && (
                        <div><strong>Strongest:</strong> {dignitiesData.summary.strongest_planets.join(', ')}</div>
                      )}
                      {dignitiesData.summary.exalted_planets?.length > 0 && (
                        <div><strong>Exalted:</strong> {dignitiesData.summary.exalted_planets.join(', ')}</div>
                      )}
                      {dignitiesData.summary.debilitated_planets?.length > 0 && (
                        <div><strong>Debilitated:</strong> {dignitiesData.summary.debilitated_planets.join(', ')}</div>
                      )}
                      {dignitiesData.summary.combust_planets?.length > 0 && (
                        <div><strong>Combust:</strong> {dignitiesData.summary.combust_planets.join(', ')}</div>
                      )}
                      {dignitiesData.summary.retrograde_planets?.length > 0 && (
                        <div><strong>Retrograde:</strong> {dignitiesData.summary.retrograde_planets.join(', ')}</div>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Detailed Dignities */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '15px' }}>
                  {Object.entries(dignitiesData.dignities || {}).map(([planet, info]) => (
                    <div key={planet} style={{
                      border: '1px solid #e0e0e0',
                      borderRadius: '8px',
                      padding: '15px',
                      backgroundColor: info.strength_multiplier > 1.2 ? '#e8f5e8' : info.strength_multiplier < 0.8 ? '#ffeaea' : '#ffffff'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                        <h5 style={{ margin: 0, color: '#e91e63', fontSize: '16px' }}>{planet}</h5>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '11px',
                          fontWeight: 'bold',
                          backgroundColor: info.strength_multiplier > 1.2 ? '#4caf50' : info.strength_multiplier < 0.8 ? '#f44336' : '#ff9800',
                          color: 'white',
                          cursor: 'pointer'
                        }}
                        title={info.strength_breakdown ? info.strength_breakdown.join(' • ') : 'Strength calculation'}
                        >
                          {info.strength_multiplier}x
                        </span>
                      </div>
                      
                      <div style={{ fontSize: '13px', lineHeight: '1.4' }}>
                        <div style={{ marginBottom: '5px' }}>
                          <strong>Position:</strong> {info.degree}° in sign {info.sign + 1}
                        </div>
                        
                        <div style={{ marginBottom: '5px' }}>
                          <strong>Dignity:</strong> 
                          <span style={{
                            marginLeft: '5px',
                            padding: '1px 6px',
                            borderRadius: '10px',
                            fontSize: '11px',
                            backgroundColor: info.dignity === 'exalted' ? '#4caf50' : 
                                           info.dignity === 'debilitated' ? '#f44336' :
                                           info.dignity === 'moolatrikona' ? '#ff9800' :
                                           info.dignity === 'own_sign' ? '#2196f3' : '#9e9e9e',
                            color: 'white'
                          }}>
                            {info.dignity.replace('_', ' ').toUpperCase()}
                          </span>
                        </div>
                        
                        <div style={{ marginBottom: '5px' }}>
                          <strong>Functional:</strong> 
                          <span style={{
                            marginLeft: '5px',
                            padding: '1px 6px',
                            borderRadius: '10px',
                            fontSize: '11px',
                            backgroundColor: info.functional_nature === 'benefic' ? '#4caf50' : 
                                           info.functional_nature === 'malefic' ? '#f44336' : '#9e9e9e',
                            color: 'white'
                          }}>
                            {info.functional_nature.toUpperCase()}
                          </span>
                        </div>
                        
                        {info.states && info.states.length > 0 && (
                          <div style={{ marginTop: '8px' }}>
                            <strong>States:</strong>
                            <div style={{ marginTop: '4px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                              {info.states.map((state, idx) => (
                                <span key={idx} style={{
                                  padding: '2px 6px',
                                  borderRadius: '8px',
                                  fontSize: '10px',
                                  backgroundColor: '#e3f2fd',
                                  color: '#1976d2',
                                  border: '1px solid #bbdefb'
                                }}>
                                  {state}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {info.strength_breakdown && info.strength_breakdown.length > 0 && (
                          <div style={{ marginTop: '8px', padding: '6px', backgroundColor: '#f8f9fa', borderRadius: '4px', border: '1px solid #e9ecef' }}>
                            <strong style={{ fontSize: '11px', color: '#666' }}>Strength Calculation:</strong>
                            <div style={{ marginTop: '2px', fontSize: '10px', color: '#555' }}>
                              {info.strength_breakdown.map((factor, idx) => (
                                <div key={idx} style={{ marginBottom: '1px' }}>• {factor}</div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            </div>
            <div style={{
              padding: '15px 20px',
              borderTop: '1px solid #e0e0e0',
              flexShrink: 0,
              display: 'flex',
              justifyContent: 'flex-end'
            }}>
              <button 
                onClick={() => setShowPlanetaryDignities(false)}
                style={{ 
                  padding: '8px 16px', 
                  backgroundColor: '#9c27b0', color: 'white', 
                  border: 'none', borderRadius: '6px', cursor: 'pointer' 
                }}
              >
                Close
              </button>
            </div>
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
                {chartType === 'lagna' && (
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
                )}
                <button 
                  onClick={() => handlePlanetaryDignities()}
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
                  title="Show Planetary Dignities & States"
                >
                  Dignities
                </button>
                {chartType === 'lagna' && (
                  <button 
                    onClick={() => handleCharaKarakas()}
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
                    title="Show Chara Karakas (Jaimini Significators)"
                  >
                    Karakas
                  </button>
                )}
                <button 
                  onClick={() => setShowShadbala(true)}
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
                  Shadbala
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
                    chartRefHighlight={chartRefHighlight}
                  />
                </div>
              ) : (
                <div style={{ width: '100%', height: '100%', minHeight: '600px' }}>
                  <SouthIndianChart 
                    chartData={processedData}
                    chartType={chartType}
                    birthData={birthData}
                    showDegreeNakshatra={showDegreeNakshatra}
                    chartRefHighlight={chartRefHighlight}
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