import React, { useState, useEffect } from 'react';
import { useAstrology } from '../../context/AstrologyContext';
import { DASHBOARD_CONFIG } from '../../config/dashboard.config';
import ChartWidget from '../Charts/ChartWidget';
import DashaWidget from '../DashaTable/DashaWidget';
import TransitControls from '../TransitControls/TransitControls';
import YogiWidget from '../YogiWidget/YogiWidget';
import PanchangWidget from '../PanchangWidget/PanchangWidget';
import EventPredictionWidget from '../EventPredictionWidget/EventPredictionWidget';
import NakshatrasTab from '../NakshatrasTab/NakshatrasTab';
import YogasTab from '../YogasTab/YogasTab';
import RelationshipsTab from '../RelationshipsTab/RelationshipsTab';
import HouseAnalysisTab from '../HouseAnalysisTab/HouseAnalysisTab';
import { DashboardContainer, Header, BackButton, Title, GridContainer, GridItem } from './Dashboard.styles';



const DivisionalChartSelector = ({ chartData, birthData }) => {
  const [selectedChart, setSelectedChart] = useState('navamsa');
  
  const divisionalCharts = [
    { value: 'navamsa', label: 'Navamsa (D9)', division: 9 },
    { value: 'dasamsa', label: 'Dasamsa (D10)', division: 10 },
    { value: 'dwadasamsa', label: 'Dwadasamsa (D12)', division: 12 },
    { value: 'shodasamsa', label: 'Shodasamsa (D16)', division: 16 },
    { value: 'vimshamsa', label: 'Vimshamsa (D20)', division: 20 },
    { value: 'chaturvimshamsa', label: 'Chaturvimshamsa (D24)', division: 24 },
    { value: 'saptavimshamsa', label: 'Saptavimshamsa (D27)', division: 27 },
    { value: 'trimshamsa', label: 'Trimshamsa (D30)', division: 30 },
    { value: 'khavedamsa', label: 'Khavedamsa (D40)', division: 40 },
    { value: 'akshavedamsa', label: 'Akshavedamsa (D45)', division: 45 },
    { value: 'shashtyamsa', label: 'Shashtyamsa (D60)', division: 60 }
  ];
  
  const titleWithDropdown = (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', width: '100%' }}>
      <span>Divisional Chart</span>
      <select 
        value={selectedChart} 
        onChange={(e) => setSelectedChart(e.target.value)}
        style={{
          padding: '0.2rem 0.4rem',
          border: '1px solid #ddd',
          borderRadius: '4px',
          fontSize: '0.7rem',
          background: 'white',
          minWidth: '120px'
        }}
      >
        {divisionalCharts.map(chart => (
          <option key={chart.value} value={chart.value}>
            {chart.label}
          </option>
        ))}
      </select>
    </div>
  );
  
  return (
    <ChartWidget
      title={titleWithDropdown}
      chartType="divisional"
      chartData={chartData}
      birthData={birthData}
      division={divisionalCharts.find(c => c.value === selectedChart)?.division || 9}
    />
  );
};

const Dashboard = ({ onBack, currentView, setCurrentView }) => {
  const { birthData, chartData } = useAstrology();
  const [layouts, setLayouts] = useState(DASHBOARD_CONFIG.defaultLayout);
  const [transitDate, setTransitDate] = useState(new Date());
  const [transitData, setTransitData] = useState(null);
  const [selectedDashas, setSelectedDashas] = useState({});
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    // Load saved layout from localStorage
    const savedLayouts = localStorage.getItem('astrology-dashboard-layout');
    if (savedLayouts) {
      setLayouts(JSON.parse(savedLayouts));
    }
    // Load today's transit data on component mount
    handleTransitDateChange(new Date());
  }, []);

  const handleLayoutChange = (layout, layouts) => {
    setLayouts(layouts);
    localStorage.setItem('astrology-dashboard-layout', JSON.stringify(layouts));
  };

  const handleTransitDateChange = async (newDate) => {
    setTransitDate(newDate);
    setSelectedDashas({}); // Clear selected dashas to force recalculation
    try {
      const response = await fetch('http://localhost:8001/calculate-transits', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          birth_data: birthData,
          transit_date: newDate.toISOString().split('T')[0]
        })
      });
      const data = await response.json();
      setTransitData(data);
    } catch (error) {
      console.error('Error fetching transit data:', error);
    }
  };

  const handleDashaClick = (dashaDate) => {
    setTransitDate(new Date(dashaDate));
    handleTransitDateChange(new Date(dashaDate));
  };

  const handleDashaSelection = (dashaType, dasha) => {
    setSelectedDashas(prev => ({
      ...prev,
      [dashaType]: dasha
    }));
  };

  const resetToToday = () => {
    const today = new Date();
    setTransitDate(today);
    setSelectedDashas({});
    handleTransitDateChange(today);
  };

  if (!birthData || !chartData) {
    return <div>Loading...</div>;
  }

  return (
    <DashboardContainer>
      <Header>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1 }}>
          <BackButton onClick={onBack}>← Back</BackButton>
        </div>
        <Title style={{ flex: 2, textAlign: 'center', fontSize: '1rem' }}>{birthData.name} - Birth Chart Dashboard</Title>
        <TransitControls 
          date={transitDate} 
          onChange={handleTransitDateChange}
          onResetToToday={resetToToday}
        />
      </Header>

      {/* Tab Navigation */}
      <div style={{ 
        display: 'flex', 
        borderBottom: '3px solid #e91e63',
        marginBottom: '0.5rem',
        background: '#f8f9fa',
        borderRadius: '8px',
        padding: '0.3rem',
        margin: '0 1rem'
      }}>
        {[
          { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
          { id: 'nakshatras', label: '🌟 Nakshatras', icon: '🌟' },
          { id: 'houses', label: '🏠 House Analysis', icon: '🏠' },
          { id: 'relationships', label: '🤝 Relationships', icon: '🤝' },
          { id: 'strengths', label: '⚡ Strengths', icon: '⚡' },
          { id: 'yogas', label: '🔮 Yogas', icon: '🔮' },
          { id: 'timing', label: '📅 Timing', icon: '📅' },
          { id: 'predictions', label: '🔮 Predictions', icon: '🔮' },
          { id: 'remedies', label: '💎 Remedies', icon: '💎' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '0.5rem 1rem',
              background: activeTab === tab.id ? '#e91e63' : 'transparent',
              color: activeTab === tab.id ? 'white' : '#e91e63',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.8rem',
              fontWeight: '600',
              marginRight: '0.2rem'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'dashboard' && (
        <GridContainer>
          {/* First row - 4 charts */}
          <GridItem chart>
            <ChartWidget
              title="Lagna Chart"
              chartType="lagna"
              chartData={chartData}
              birthData={birthData}
            />
          </GridItem>
          
          <GridItem chart>
            <ChartWidget
              title="Navamsa Chart"
              chartType="navamsa"
              chartData={chartData}
              birthData={birthData}
            />
          </GridItem>
          
          <GridItem chart>
            <ChartWidget
              title="Transit Chart"
              chartType="transit"
              chartData={transitData || chartData}
              birthData={birthData}
              transitDate={transitDate}
            />
          </GridItem>
          
          <GridItem chart>
            <DivisionalChartSelector
              chartData={chartData}
              birthData={birthData}
            />
          </GridItem>
          
          {/* Second row - 7 items (5 dashas + yogi + panchang) */}
          <div style={{ gridColumn: '1 / -1', display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '0.3rem', height: '30vh' }}>
            <GridItem dasha>
              <DashaWidget
                title="Maha Dasha"
                dashaType="maha"
                birthData={birthData}
                onDashaClick={handleDashaClick}
                selectedDashas={selectedDashas}
                onDashaSelection={handleDashaSelection}
                transitDate={transitDate}
              />
            </GridItem>
            
            <GridItem dasha>
              <DashaWidget
                title="Antar Dasha"
                dashaType="antar"
                birthData={birthData}
                onDashaClick={handleDashaClick}
                selectedDashas={selectedDashas}
                onDashaSelection={handleDashaSelection}
                transitDate={transitDate}
              />
            </GridItem>
            
            <GridItem dasha>
              <DashaWidget
                title="Pratyantar Dasha"
                dashaType="pratyantar"
                birthData={birthData}
                onDashaClick={handleDashaClick}
                selectedDashas={selectedDashas}
                onDashaSelection={handleDashaSelection}
                transitDate={transitDate}
              />
            </GridItem>
            
            <GridItem dasha>
              <DashaWidget
                title="Sookshma Dasha"
                dashaType="sookshma"
                birthData={birthData}
                onDashaClick={handleDashaClick}
                selectedDashas={selectedDashas}
                onDashaSelection={handleDashaSelection}
                transitDate={transitDate}
              />
            </GridItem>
            
            <GridItem dasha>
              <DashaWidget
                title="Prana Dasha"
                dashaType="prana"
                birthData={birthData}
                onDashaClick={handleDashaClick}
                selectedDashas={selectedDashas}
                onDashaSelection={handleDashaSelection}
                transitDate={transitDate}
              />
            </GridItem>
            
            <GridItem dasha>
              <YogiWidget />
            </GridItem>
            
            <GridItem dasha>
              <PanchangWidget transitDate={transitDate} />
            </GridItem>
          </div>
        </GridContainer>
      )}
      
      {activeTab !== 'dashboard' && (
        <div style={{ 
          background: 'rgba(255,255,255,0.95)',
          borderRadius: '12px',
          padding: '1rem',
          margin: '0 1rem',
          minHeight: '70vh',
          boxShadow: '0 4px 16px rgba(0,0,0,0.1)'
        }}>
          {activeTab === 'nakshatras' && <NakshatrasTab chartData={chartData} birthData={birthData} />}
          {activeTab === 'houses' && <HouseAnalysisTab chartData={chartData} birthData={birthData} />}
          {activeTab === 'relationships' && <RelationshipsTab chartData={chartData} birthData={birthData} />}
          {activeTab === 'strengths' && <div>Strengths - Coming Soon</div>}
          {activeTab === 'yogas' && <YogasTab chartData={chartData} birthData={birthData} />}
          {activeTab === 'timing' && <div>Timing - Coming Soon</div>}
          {activeTab === 'predictions' && <div>Predictions - Coming Soon</div>}
          {activeTab === 'remedies' && <div>Remedies - Coming Soon</div>}
        </div>
      )}
    </DashboardContainer>
  );
};

export default Dashboard;