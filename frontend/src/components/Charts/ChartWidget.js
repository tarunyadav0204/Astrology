import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { CHART_CONFIG } from '../../config/dashboard.config';
import NorthIndianChart from './NorthIndianChart';
import SouthIndianChart from './SouthIndianChart';
import { apiService } from '../../services/apiService';
import { WidgetContainer, WidgetHeader, WidgetTitle, StyleToggle, ChartContainer } from './ChartWidget.styles';
import AshtakavargaModal from '../Ashtakavarga/AshtakavargaModal';
import ShadbalaModal from '../Shadbala/ShadbalaModal';
import './ChartMaximizedModal.css';
import './ChartToolModal.css';
import { buildBhavChalitChart } from '../../utils/bhavChalitChart';

const ChartWidget = ({
  title,
  chartType,
  chartData,
  birthData,
  transitDate,
  division,
  defaultStyle,
  chartRefHighlight = null,
  /** Flat toolbar + square corners when embedded in Parashara dashboard (avoids stacked “headers”) */
  embedInDashboard = false,
  /** Parashari/KP desk: minimize chrome so the chart fills the cell */
  deskMode = false,
  showFooterHint = true,
  onHouseSelect = null,
  selectedHouseNumber = null,
  highlightedPlanets = null,
  highlightedHouseNumbers = null,
  activationHouseStates = null,
  chartStyle: controlledChartStyle,
  onChartStyleChange = null,
  calculationProfile = null,
}) => {
  const [internalChartStyle, setInternalChartStyle] = useState(defaultStyle || 'north');
  const chartStyle = controlledChartStyle ?? internalChartStyle;
  const [showAshtakavarga, setShowAshtakavarga] = useState(false);
  const supportsAshtakavarga = chartType === 'lagna' || chartType === 'transit';
  const [showMaximized, setShowMaximized] = useState(false);
  const [showDegreeNakshatra, setShowDegreeNakshatra] = useState(!deskMode);
  const [showSpecialPoints, setShowSpecialPoints] = useState(false);
  const [specialPointsData, setSpecialPointsData] = useState(null);
  const [showPlanetaryDignities, setShowPlanetaryDignities] = useState(false);
  const [dignitiesData, setDignitiesData] = useState(null);
  const [showCharaKarakas, setShowCharaKarakas] = useState(false);
  const [charaKarakasData, setCharaKarakasData] = useState(null);
  const [showShadbala, setShowShadbala] = useState(false);

  // Update chart style when defaultStyle prop changes
  useEffect(() => {
    if (defaultStyle && controlledChartStyle == null) {
      setInternalChartStyle(defaultStyle);
    }
  }, [defaultStyle, controlledChartStyle]);

  useEffect(() => {
    if (!showMaximized) return undefined;

    const previousOverflow = document.body.style.overflow;
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setShowMaximized(false);
    };

    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', closeOnEscape);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [showMaximized]);
  const [divisionalData, setDivisionalData] = useState(null);
  const [transitChartData, setTransitChartData] = useState(null);
  const [loading, setLoading] = useState(false);

  const toggleStyle = () => {
    const nextStyle = chartStyle === 'north' ? 'south' : 'north';
    if (onChartStyleChange) onChartStyleChange(nextStyle);
    else setInternalChartStyle(nextStyle);
  };
  
  // Fetch divisional chart data from backend when needed
  useEffect(() => {
    if ((chartType === 'navamsa' || chartType === 'divisional') && birthData && chartData) {
      setLoading(true);
      const divisionNum = chartType === 'navamsa' ? 9 : (division || 9);
      
      // Always use backend for all divisional charts
      apiService.calculateDivisionalChart(birthData, divisionNum, calculationProfile)
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
  }, [chartType, birthData, division, chartData, calculationProfile?.ayanamsha, calculationProfile?.node_type]);

  // Karkamsa / Swamsa (Jaimini) — need Atmakaraka then recast chart
  useEffect(() => {
    if ((chartType !== 'karkamsa' && chartType !== 'swamsa') || !chartData?.planets) {
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const karakas = await apiService.calculateCharaKarakas(chartData, birthData);
        const ak =
          karakas?.chara_karakas?.Atmakaraka?.planet
          || karakas?.chara_karakas?.AK?.planet
          || karakas?.atmakaraka
          || Object.entries(karakas?.chara_karakas || {}).find(([k]) => /atma/i.test(k))?.[1]?.planet;
        if (!ak) throw new Error('Atmakaraka not found');
        const res = chartType === 'karkamsa'
          ? await apiService.calculateKarkamsaChart(chartData, ak)
          : await apiService.calculateSwamsaChart(chartData, ak);
        const chart = chartType === 'karkamsa'
          ? res?.karkamsa?.karkamsa_chart
          : res?.swamsa?.swamsa_chart;
        if (cancelled) return;
        // Normalize houses array for NorthIndianChart (expects index-based sign)
        if (chart?.houses && Array.isArray(chart.houses)) {
          chart.houses = chart.houses.map((h, i) => ({
            ...h,
            sign: typeof h.sign === 'number' ? h.sign : (h.sign_index ?? i),
            longitude: h.longitude ?? ((typeof h.sign === 'number' ? h.sign : i) * 30),
          }));
        }
        setDivisionalData(chart || null);
      } catch (error) {
        console.error(`Failed to calculate ${chartType} chart:`, error);
        if (!cancelled) setDivisionalData(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [chartType, chartData, birthData]);

  useEffect(() => {
    if (chartType === 'transit' && birthData && transitDate) {
      setLoading(true);
      const transitDay = (() => {
        if (transitDate instanceof Date && !Number.isNaN(transitDate.getTime())) {
          const y = transitDate.getFullYear();
          const m = String(transitDate.getMonth() + 1).padStart(2, '0');
          const d = String(transitDate.getDate()).padStart(2, '0');
          return `${y}-${m}-${d}`;
        }
        return String(transitDate).split('T')[0];
      })();
      apiService.calculateTransits({
        birth_data: birthData,
        transit_date: transitDay,
        ...(calculationProfile ? { calculation_profile: calculationProfile } : {}),
      })
        .then((response) => {
          setTransitChartData(response);
        })
        .catch((error) => {
          console.error('Failed to calculate transit chart:', error);
          setTransitChartData(null);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [chartType, birthData, transitDate, calculationProfile?.ayanamsha, calculationProfile?.node_type]);

  const getChartData = () => {
    switch (chartType) {
      case 'lagna':
        return chartData;
      case 'bhav_chalit':
        return buildBhavChalitChart(chartData);
      case 'navamsa':
      case 'divisional':
      case 'karkamsa':
      case 'swamsa':
        return divisionalData || chartData;
      case 'transit':
        return transitChartData || chartData;
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
    <WidgetContainer $embedInDashboard={embedInDashboard} $deskMode={deskMode}>
      {!deskMode ? (
      <WidgetHeader $embedInDashboard={embedInDashboard}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0, flex: 1 }}>
          <WidgetTitle title={title} $embedInDashboard={embedInDashboard}>
            {title}
          </WidgetTitle>
          <span
            style={{
              fontSize: embedInDashboard ? '0.58rem' : '0.65rem',
              color: embedInDashboard ? '#6b6568' : '#8b5a3c',
              fontWeight: 500,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              lineHeight: 1.2,
            }}
          >
            Click or right-click a house for options
          </span>
        </div>
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
          {supportsAshtakavarga && (
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
          )}
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
      ) : null}
      
      <ChartContainer $embedInDashboard={embedInDashboard} $deskMode={deskMode} style={deskMode ? { position: 'relative' } : undefined}>
        {deskMode ? (
          <div
            className="chart-desk-mini-bar"
            style={{
              position: 'absolute',
              top: 2,
              right: 2,
              zIndex: 5,
              display: 'flex',
              gap: 4,
            }}
          >
            <StyleToggle onClick={toggleStyle} title="North / South Indian">
              {chartStyle === 'north' ? 'N' : 'S'}
            </StyleToggle>
            {!isMobile && (
              <button
                type="button"
                onClick={() => setShowMaximized(true)}
                style={{
                  padding: '2px 6px',
                  fontSize: '10px',
                  background: 'rgba(255,255,255,0.9)',
                  color: '#666',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  lineHeight: 1.2,
                }}
                title="Maximize chart"
              >
                ⛶
              </button>
            )}
          </div>
        ) : null}
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px', color: '#666' }}>
            Calculating divisional chart...
          </div>
        ) : ((chartType === 'bhav_chalit' && !processedData) || (!divisionalData && (chartType === 'navamsa' || chartType === 'divisional' || chartType === 'karkamsa' || chartType === 'swamsa'))) ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px', color: '#e91e63' }}>
            Failed to load chart
          </div>
        ) : chartStyle === 'north' ? (
          <NorthIndianChart 
            chartData={processedData}
            chartType={chartType}
            birthData={birthData}
            division={division}
            showDegreeNakshatra={showDegreeNakshatra}
            showFooterHint={showFooterHint}
            deskMode={deskMode}
            onHouseSelect={onHouseSelect}
            selectedHouseNumber={selectedHouseNumber}
            highlightedPlanets={highlightedPlanets}
            highlightedHouseNumbers={highlightedHouseNumbers}
            activationHouseStates={activationHouseStates}
          />
        ) : (
          <SouthIndianChart 
            chartData={processedData}
            chartType={chartType}
            birthData={birthData}
            division={division}
            showDegreeNakshatra={showDegreeNakshatra}
            showFooterHint={showFooterHint}
            deskMode={deskMode}
            onHouseSelect={onHouseSelect}
            selectedHouseNumber={selectedHouseNumber}
            highlightedPlanets={highlightedPlanets}
            highlightedHouseNumbers={highlightedHouseNumbers}
            activationHouseStates={activationHouseStates}
          />
        )}
      </ChartContainer>
      
      {supportsAshtakavarga ? (
        <AshtakavargaModal
          isOpen={showAshtakavarga}
          onClose={() => setShowAshtakavarga(false)}
          birthData={birthData}
          chartType={chartType}
          transitDate={transitDate}
        />
      ) : null}
      
      {showShadbala && (
        <ShadbalaModal
          chartData={getChartData()}
          birthData={birthData}
          onClose={() => setShowShadbala(false)}
        />
      )}
      
      {/* Special Points Modal */}
      {showSpecialPoints && createPortal(
        <div className="chart-tool-modal__backdrop" style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 100002,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }} onClick={() => setShowSpecialPoints(false)}>
          <div className="chart-tool-modal" style={{
            backgroundColor: 'white', borderRadius: '12px',
            maxWidth: '700px', width: '90%', maxHeight: '80vh',
            display: 'flex', flexDirection: 'column'
          }} onClick={e => e.stopPropagation()}>
            <div className="chart-tool-modal__header" style={{
              padding: '20px 20px 0 20px',
              borderBottom: '1px solid #e0e0e0',
              flexShrink: 0
            }}>
              <h3 style={{ color: '#9c27b0', margin: 0 }}>Special Astrological Points</h3>
            </div>
            <div className="chart-tool-modal__body" style={{
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
            <div className="chart-tool-modal__footer" style={{
              padding: '15px 20px',
              borderTop: '1px solid #e0e0e0',
              flexShrink: 0,
              display: 'flex',
              justifyContent: 'flex-end'
            }}>
              <button className="chart-tool-modal__close"
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
        <div className="chart-tool-modal__backdrop" style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 100002,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }} onClick={() => setShowCharaKarakas(false)}>
          <div className="chart-tool-modal chart-tool-modal--wide" style={{
            backgroundColor: 'white', borderRadius: '12px',
            maxWidth: '800px', width: '90%', maxHeight: '80vh',
            display: 'flex', flexDirection: 'column'
          }} onClick={e => e.stopPropagation()}>
            <div className="chart-tool-modal__header" style={{
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
            <div className="chart-tool-modal__body" style={{
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
            <div className="chart-tool-modal__footer" style={{
              padding: '15px 20px',
              borderTop: '1px solid #e0e0e0',
              flexShrink: 0,
              display: 'flex',
              justifyContent: 'flex-end'
            }}>
              <button className="chart-tool-modal__close"
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
        <div className="chart-tool-modal__backdrop" style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 100002,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }} onClick={() => setShowPlanetaryDignities(false)}>
          <div className="chart-tool-modal chart-tool-modal--wide" style={{
            backgroundColor: 'white', borderRadius: '12px',
            maxWidth: '800px', width: '90%', maxHeight: '80vh',
            display: 'flex', flexDirection: 'column'
          }} onClick={e => e.stopPropagation()}>
            <div className="chart-tool-modal__header" style={{
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
            <div className="chart-tool-modal__body" style={{
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
            <div className="chart-tool-modal__footer" style={{
              padding: '15px 20px',
              borderTop: '1px solid #e0e0e0',
              flexShrink: 0,
              display: 'flex',
              justifyContent: 'flex-end'
            }}>
              <button className="chart-tool-modal__close"
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
        <div
          className="chart-maximized-modal__backdrop"
          onClick={() => setShowMaximized(false)}
        >
          <section
            className="chart-maximized-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="chart-maximized-title"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="chart-maximized-modal__header">
              <div className="chart-maximized-modal__heading">
                <span className="chart-maximized-modal__eyebrow">Expanded chart</span>
                <h2 id="chart-maximized-title">{title}</h2>
              </div>
              <div className="chart-maximized-modal__header-actions">
                <span className="chart-maximized-modal__style-label">
                  {CHART_CONFIG.styles[chartStyle]}
                </span>
                <button
                  type="button"
                  className="chart-maximized-modal__close"
                  onClick={() => setShowMaximized(false)}
                  aria-label="Close expanded chart"
                  title="Close"
                >
                  <span aria-hidden="true">×</span>
                </button>
              </div>
            </header>

            <nav className="chart-maximized-modal__toolbar" aria-label="Chart tools">
              <div className="chart-maximized-modal__toolbar-scroll">
                <button
                  type="button"
                  onClick={() => setShowDegreeNakshatra(!showDegreeNakshatra)}
                  className={`chart-maximized-modal__tool${showDegreeNakshatra ? ' is-active' : ''}`}
                  title={showDegreeNakshatra ? 'Hide degree and nakshatra' : 'Show degree and nakshatra'}
                  aria-pressed={showDegreeNakshatra}
                >
                  {showDegreeNakshatra ? 'Details on' : 'Details'}
                </button>
                {chartType === 'lagna' && (
                  <button
                    type="button"
                    onClick={() => handleSpecialPoints()}
                    className="chart-maximized-modal__tool"
                    title="Show Dagdha Rasi, Tithi Shunya, Avayogi, Marka, Badhaka"
                  >
                    Special Points
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => handlePlanetaryDignities()}
                  className="chart-maximized-modal__tool"
                  title="Show Planetary Dignities & States"
                >
                  Dignities
                </button>
                {chartType === 'lagna' && (
                  <button
                    type="button"
                    onClick={() => handleCharaKarakas()}
                    className="chart-maximized-modal__tool"
                    title="Show Chara Karakas (Jaimini Significators)"
                  >
                    Karakas
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setShowShadbala(true)}
                  className="chart-maximized-modal__tool"
                >
                  Shadbala
                </button>
                {supportsAshtakavarga && (
                  <button
                    type="button"
                    onClick={() => setShowAshtakavarga(true)}
                    className="chart-maximized-modal__tool"
                  >
                    Ashtakavarga
                  </button>
                )}
                <button
                  type="button"
                  onClick={toggleStyle}
                  className="chart-maximized-modal__tool chart-maximized-modal__tool--style"
                  title="Switch chart style"
                >
                  <span aria-hidden="true">⇄</span>
                  {chartStyle === 'north' ? 'South Indian' : 'North Indian'}
                </button>
              </div>
            </nav>

            <div className="chart-maximized-modal__stage">
              {loading ? (
                <div className="chart-maximized-modal__state">
                  Calculating divisional chart...
                </div>
              ) : ((chartType === 'bhav_chalit' && !processedData) || (!divisionalData && (chartType === 'navamsa' || chartType === 'divisional' || chartType === 'karkamsa' || chartType === 'swamsa'))) ? (
                <div className="chart-maximized-modal__state chart-maximized-modal__state--error">
                  Failed to load chart
                </div>
              ) : chartStyle === 'north' ? (
                <div className="chart-maximized-modal__chart-frame">
                  <NorthIndianChart 
                    chartData={processedData}
                    chartType={chartType}
                    birthData={birthData}
                    division={division}
                    showDegreeNakshatra={showDegreeNakshatra}
                    chartRefHighlight={chartRefHighlight}
                    showFooterHint={showFooterHint}
                  />
                </div>
              ) : (
                <div className="chart-maximized-modal__chart-frame">
                  <SouthIndianChart 
                    chartData={processedData}
                    chartType={chartType}
                    birthData={birthData}
                    division={division}
                    showDegreeNakshatra={showDegreeNakshatra}
                    chartRefHighlight={chartRefHighlight}
                    showFooterHint={showFooterHint}
                  />
                </div>
              )}
            </div>
          </section>
        </div>,
        document.body
      )}
    </WidgetContainer>
  );
};

export default ChartWidget;
