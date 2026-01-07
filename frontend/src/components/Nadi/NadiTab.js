import React, { useState, useEffect } from 'react';
import ChartWidget from '../Charts/ChartWidget';
import DashaWidget from '../DashaTable/DashaWidget';
import CompactAspectsTable from './CompactAspectsTable';
import './NadiTab.css';

const NadiTab = ({ birthData, transitDate: propTransitDate, onTransitDateChange, selectedDashas: propSelectedDashas, onDashaSelection: propOnDashaSelection }) => {
  const [nadiData, setNadiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [transitDate, setTransitDate] = useState(propTransitDate || new Date());
  const [selectedDashas, setSelectedDashas] = useState({});
  const [cascadingDashaData, setCascadingDashaData] = useState(null);
  const [mobileTab, setMobileTab] = useState('charts');
  const [mobileChartTab, setMobileChartTab] = useState('rasi');

  useEffect(() => {
    fetchNadiAnalysis();
  }, [birthData, transitDate]);

  useEffect(() => {
    if (propSelectedDashas) {
      setSelectedDashas(propSelectedDashas);
    }
  }, [propSelectedDashas]);

  const fetchNadiAnalysis = async () => {
    try {
      setLoading(true);
      const { apiService } = await import('../../services/apiService');
      
      // Get chart data in the format existing components expect
      const chartData = await apiService.calculateChartOnly({
        name: birthData.name,
        date: birthData.date,
        time: birthData.time,
        latitude: birthData.latitude,
        longitude: birthData.longitude,
        place: birthData.place || ''
      });
      
      // Get transit data for current date
      const transitData = await apiService.calculateTransits({
        birth_data: birthData,
        transit_date: transitDate.toISOString().split('T')[0]
      });
      
      // Get cascading dasha data
      const dashaResponse = await fetch('/api/calculate-cascading-dashas', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          birth_data: birthData,
          target_date: transitDate.toISOString().split('T')[0]
        })
      });
      
      if (dashaResponse.ok) {
        const cascadingData = await dashaResponse.json();
        setCascadingDashaData(cascadingData);
      }
      
      const response = await fetch('/api/nadi-analysis', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ 
          birth_data: birthData,
          chart_data: chartData 
        })
      });
      
      if (!response.ok) {
        throw new Error(`Nadi API error: ${response.status}`);
      }
      
      const nadiAnalysis = await response.json();
      
      // Combine with existing chart data format
      setNadiData({
        ...nadiAnalysis,
        chart_data: chartData,
        transit_data: transitData
      });
    } catch (error) {
      console.error('Error fetching Nadi analysis:', error);
      setNadiData({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const handleTimelineClick = async (date) => {
    // Update transit date and refetch data
    const newDate = new Date(date);
    setTransitDate(newDate);
    setSelectedDashas({});
    
    // Refresh cascading dasha data for new date
    try {
      const dashaResponse = await fetch('/api/calculate-cascading-dashas', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          birth_data: birthData,
          target_date: newDate.toISOString().split('T')[0]
        })
      });
      
      if (dashaResponse.ok) {
        const cascadingData = await dashaResponse.json();
        setCascadingDashaData(cascadingData);
      }
    } catch (error) {
      console.error('Error refreshing cascading dasha data:', error);
    }
    
    onTransitDateChange(newDate);
  };

  const handleDashaClick = async (dashaDate) => {
    const newDate = new Date(dashaDate);
    setTransitDate(newDate);
    
    // Refresh cascading dasha data for new date
    try {
      const dashaResponse = await fetch('/api/calculate-cascading-dashas', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          birth_data: birthData,
          target_date: newDate.toISOString().split('T')[0]
        })
      });
      
      if (dashaResponse.ok) {
        const cascadingData = await dashaResponse.json();
        setCascadingDashaData(cascadingData);
      }
    } catch (error) {
      console.error('Error refreshing cascading dasha data:', error);
    }
    
    onTransitDateChange(newDate);
  };

  const handleDashaSelection = (dashaType, dasha) => {
    const newSelectedDashas = {
      ...selectedDashas,
      [dashaType]: dasha
    };
    setSelectedDashas(newSelectedDashas);
    if (propOnDashaSelection) {
      propOnDashaSelection(dashaType, dasha);
    }
  };

  if (loading) {
    return <div className="nadi-loading">Loading Nadi Analysis...</div>;
  }

  if (!nadiData) {
    return <div className="nadi-error">Failed to load Nadi analysis data</div>;
  }

  if (nadiData.error) {
    return <div className="nadi-error">Error: {nadiData.error}</div>;
  }

  if (!nadiData.chart_data || !nadiData.transit_data) {
    return <div className="nadi-error">Missing chart or transit data</div>;
  }

  const isMobile = window.innerWidth <= 768;

  if (isMobile) {
    return (
      <div className="nadi-mobile">
        {/* Main Content Area */}
        <div className="mobile-content">
          {mobileTab === 'charts' && (
            <div className="mobile-charts">
              {/* Chart Tab Navigation */}
              <div className="chart-tabs">
                {[
                  { id: 'rasi', label: 'Rasi', icon: '📊' },
                  { id: 'navamsa', label: 'Navamsa', icon: '🌙' },
                  { id: 'transit', label: 'Transit', icon: '🔄' }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setMobileChartTab(tab.id)}
                    className={`chart-tab ${mobileChartTab === tab.id ? 'active' : ''}`}
                  >
                    <span>{tab.icon}</span>
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>
              
              {/* Chart Content */}
              <div className="chart-content">
                {mobileChartTab === 'rasi' && (
                  <ChartWidget 
                    title="Rasi Chart"
                    chartType="lagna"
                    chartData={nadiData.chart_data}
                    birthData={birthData}
                    defaultStyle="north"
                  />
                )}
                {mobileChartTab === 'navamsa' && (
                  <ChartWidget 
                    title="Navamsa Chart"
                    chartType="navamsa"
                    chartData={nadiData.chart_data}
                    birthData={birthData}
                    defaultStyle="north"
                  />
                )}
                {mobileChartTab === 'transit' && (
                  <ChartWidget 
                    title="Transit Chart"
                    chartType="transit"
                    chartData={nadiData.transit_data}
                    birthData={birthData}
                    transitDate={transitDate}
                    defaultStyle="north"
                  />
                )}
              </div>
            </div>
          )}
          
          {mobileTab === 'aspects' && (
            <div className="mobile-aspects">
              {propSelectedDashas && Object.keys(propSelectedDashas).length > 0 && (
                <div style={{
                  background: 'linear-gradient(135deg, #e91e63 0%, #ff6f00 100%)',
                  color: 'white',
                  padding: '8px 12px',
                  fontSize: '0.7rem',
                  borderRadius: '6px',
                  marginBottom: '8px'
                }}>
                  {['maha', 'antar', 'pratyantar', 'sookshma', 'prana']
                    .filter(level => propSelectedDashas[level])
                    .map((level, index) => {
                      const dasha = propSelectedDashas[level];
                      const labels = { maha: 'M', antar: 'A', pratyantar: 'P', sookshma: 'S', prana: 'Pr' };
                      return (
                        <span key={level}>
                          {index > 0 && ' → '}
                          {labels[level]}:{dasha.planet}
                        </span>
                      );
                    })}
                </div>
              )}
              <CompactAspectsTable 
                aspects={nadiData.natal_aspects}
                natalPlanets={nadiData.natal_planets}
                onTimelineClick={handleTimelineClick}
                selectedDashas={propSelectedDashas || selectedDashas}
              />
            </div>
          )}
          
          {mobileTab === 'dashas' && (
            <div className="mobile-dashas">
              {propSelectedDashas && Object.keys(propSelectedDashas).length > 0 && (
                <div style={{
                  background: 'linear-gradient(135deg, #e91e63 0%, #ff6f00 100%)',
                  color: 'white',
                  padding: '8px 12px',
                  fontSize: '0.7rem',
                  borderRadius: '6px',
                  marginBottom: '8px'
                }}>
                  {['maha', 'antar', 'pratyantar', 'sookshma', 'prana']
                    .filter(level => propSelectedDashas[level])
                    .map((level, index) => {
                      const dasha = propSelectedDashas[level];
                      const labels = { maha: 'M', antar: 'A', pratyantar: 'P', sookshma: 'S', prana: 'Pr' };
                      return (
                        <span key={level}>
                          {index > 0 && ' → '}
                          {labels[level]}:{dasha.planet}
                        </span>
                      );
                    })}
                </div>
              )}
              <div className="dashas-grid">
                <DashaWidget 
                  title="Maha"
                  dashaType="maha" 
                  birthData={birthData}
                  onDashaClick={handleDashaClick}
                  selectedDashas={propSelectedDashas || selectedDashas}
                  onDashaSelection={propOnDashaSelection || handleDashaSelection}
                  transitDate={transitDate}
                  cascadingData={cascadingDashaData}
                />
                <DashaWidget 
                  title="Antar"
                  dashaType="antar" 
                  birthData={birthData}
                  onDashaClick={handleDashaClick}
                  selectedDashas={propSelectedDashas || selectedDashas}
                  onDashaSelection={propOnDashaSelection || handleDashaSelection}
                  transitDate={transitDate}
                  cascadingData={cascadingDashaData}
                />
                <DashaWidget 
                  title="Pratyantar"
                  dashaType="pratyantar" 
                  birthData={birthData}
                  onDashaClick={handleDashaClick}
                  selectedDashas={propSelectedDashas || selectedDashas}
                  onDashaSelection={propOnDashaSelection || handleDashaSelection}
                  transitDate={transitDate}
                  cascadingData={cascadingDashaData}
                />
                <DashaWidget 
                  title="Sookshma"
                  dashaType="sookshma" 
                  birthData={birthData}
                  onDashaClick={handleDashaClick}
                  selectedDashas={propSelectedDashas || selectedDashas}
                  onDashaSelection={propOnDashaSelection || handleDashaSelection}
                  transitDate={transitDate}
                  cascadingData={cascadingDashaData}
                />
                <DashaWidget 
                  title="Prana"
                  dashaType="prana" 
                  birthData={birthData}
                  onDashaClick={handleDashaClick}
                  selectedDashas={propSelectedDashas || selectedDashas}
                  onDashaSelection={propOnDashaSelection || handleDashaSelection}
                  transitDate={transitDate}
                  cascadingData={cascadingDashaData}
                />
              </div>
            </div>
          )}
        </div>
        
        {/* Bottom Tab Navigation */}
        <div className="mobile-bottom-tabs">
          {[
            { id: 'charts', label: 'Charts', icon: '📊' },
            { id: 'aspects', label: 'Aspects', icon: '🎯' },
            { id: 'dashas', label: 'Dashas', icon: '⏰' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setMobileTab(tab.id)}
              className={`mobile-tab ${mobileTab === tab.id ? 'active' : ''}`}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  // Desktop Layout
  return (
    <div className="nadi-dashboard">
      {/* Left Column - Charts and Aspects */}
      <div className="left-column">
        {/* Charts Section */}
        <div className="charts-section">
          <div className="chart-item">
            <ChartWidget 
              title="Rasi Chart"
              chartType="lagna"
              chartData={nadiData.chart_data}
              birthData={birthData}
              defaultStyle="north"
            />
          </div>
          
          <div className="chart-item">
            <ChartWidget 
              title="Navamsa Chart"
              chartType="navamsa"
              chartData={nadiData.chart_data}
              birthData={birthData}
              defaultStyle="north"
            />
          </div>
          
          <div className="chart-item">
            <ChartWidget 
              title="Transit Chart"
              chartType="transit"
              chartData={nadiData.transit_data}
              birthData={birthData}
              transitDate={transitDate}
              defaultStyle="north"
            />
          </div>
        </div>
        
        {/* Aspects Section */}
        <div className="aspects-section">
          <CompactAspectsTable 
            aspects={nadiData.natal_aspects}
            natalPlanets={nadiData.natal_planets}
            onTimelineClick={handleTimelineClick}
            selectedDashas={propSelectedDashas || selectedDashas}
          />
        </div>
      </div>

      {/* Right Column - All 5 Dashas */}
      <div className="right-column">
        <div className="dasha-item">
          <DashaWidget 
            title="Maha Dasha"
            dashaType="maha" 
            birthData={birthData}
            onDashaClick={handleDashaClick}
            selectedDashas={selectedDashas}
            onDashaSelection={handleDashaSelection}
            transitDate={transitDate}
            cascadingData={cascadingDashaData}
          />
        </div>
        
        <div className="dasha-item">
          <DashaWidget 
            title="Antar Dasha"
            dashaType="antar" 
            birthData={birthData}
            onDashaClick={handleDashaClick}
            selectedDashas={selectedDashas}
            onDashaSelection={handleDashaSelection}
            transitDate={transitDate}
            cascadingData={cascadingDashaData}
          />
        </div>
        
        <div className="dasha-item">
          <DashaWidget 
            title="Pratyantar Dasha"
            dashaType="pratyantar" 
            birthData={birthData}
            onDashaClick={handleDashaClick}
            selectedDashas={selectedDashas}
            onDashaSelection={handleDashaSelection}
            transitDate={transitDate}
            cascadingData={cascadingDashaData}
          />
        </div>
        
        <div className="dasha-item">
          <DashaWidget 
            title="Sookshma Dasha"
            dashaType="sookshma" 
            birthData={birthData}
            onDashaClick={handleDashaClick}
            selectedDashas={selectedDashas}
            onDashaSelection={handleDashaSelection}
            transitDate={transitDate}
            cascadingData={cascadingDashaData}
          />
        </div>
        
        <div className="dasha-item">
          <DashaWidget 
            title="Prana Dasha"
            dashaType="prana" 
            birthData={birthData}
            onDashaClick={handleDashaClick}
            selectedDashas={selectedDashas}
            onDashaSelection={handleDashaSelection}
            transitDate={transitDate}
            cascadingData={cascadingDashaData}
          />
        </div>
      </div>
    </div>
  );
};

export default NadiTab;