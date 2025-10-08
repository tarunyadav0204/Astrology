import React, { useState, useEffect, useRef } from 'react';
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
import ChartSearchDropdown from '../ChartSearchDropdown/ChartSearchDropdown';
import UnifiedHeader from '../UnifiedHeader/UnifiedHeader';
import RuleManager from '../RuleEngine/RuleManager';
import EventAnalyzer from '../RuleEngine/EventAnalyzer';
import UserSettings from '../UserSettings';
import TransitDateControls from '../TransitDateControls/TransitDateControls';
import { DashboardContainer, Header, BackButton, Title, GridContainer, GridItem } from './Dashboard.styles';



const DivisionalChartSelector = ({ chartData, birthData, defaultStyle }) => {
  const [selectedChart, setSelectedChart] = useState('navamsa');
  const [showDropdown, setShowDropdown] = useState(false);
  const isMobile = window.innerWidth <= 768;
  
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
  
  const currentChart = divisionalCharts.find(c => c.value === selectedChart);
  

  
  const titleWithDropdown = `Divisional Chart (D${currentChart?.division || 9})`;
  
  if (isMobile) {
    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '0.5rem', background: '#f8f9fa', borderBottom: '1px solid #ddd', position: 'relative' }}>
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            style={{
              padding: '0.3rem 0.5rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '0.8rem',
              background: 'white',
              width: '100%',
              textAlign: 'left',
              cursor: 'pointer',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <span>{currentChart?.label}</span>
            <span>▼</span>
          </button>
          {showDropdown && (
            <div style={{
              position: 'absolute',
              top: '100%',
              left: '0.5rem',
              right: '0.5rem',
              background: 'white',
              border: '1px solid #ddd',
              borderRadius: '4px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              zIndex: 1000,
              maxHeight: '200px',
              overflowY: 'auto'
            }}>
              {divisionalCharts.map(chart => (
                <button
                  key={chart.value}
                  onClick={() => {
                    setSelectedChart(chart.value);
                    setShowDropdown(false);
                  }}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    background: selectedChart === chart.value ? '#f0f0f0' : 'white',
                    border: 'none',
                    textAlign: 'left',
                    cursor: 'pointer',
                    fontSize: '0.8rem'
                  }}
                >
                  {chart.label}
                </button>
              ))}
            </div>
          )}
        </div>
        <div style={{ flex: 1 }}>
          <ChartWidget
            title={titleWithDropdown}
            chartType="divisional"
            chartData={chartData}
            birthData={birthData}
            division={currentChart?.division || 9}
            defaultStyle={defaultStyle}
          />
        </div>
      </div>
    );
  }
  
  // Desktop: Use original ChartWidget with title dropdown
  const titleWithDesktopDropdown = (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', width: '100%' }}>
      <span>Divisional</span>
      <select 
        value={selectedChart} 
        onChange={(e) => setSelectedChart(e.target.value)}
        style={{
          padding: '0.2rem',
          border: '1px solid #ddd',
          borderRadius: '4px',
          fontSize: '0.6rem',
          background: 'white',
          minWidth: '60px',
          maxWidth: '80px'
        }}
      >
        {divisionalCharts.map(chart => (
          <option key={chart.value} value={chart.value}>
            D{chart.division}
          </option>
        ))}
      </select>
    </div>
  );
  
  return (
    <ChartWidget
      title={titleWithDesktopDropdown}
      chartType="divisional"
      chartData={chartData}
      birthData={birthData}
      division={currentChart?.division || 9}
      defaultStyle={defaultStyle}
    />
  );
};

const Dashboard = ({ onBack, onViewAllCharts, currentView, setCurrentView, onLogout, user }) => {
  const { birthData, chartData, setBirthData, setChartData } = useAstrology();
  const [layouts, setLayouts] = useState(DASHBOARD_CONFIG.defaultLayout);
  const [transitDate, setTransitDate] = useState(new Date());
  const [transitData, setTransitData] = useState(null);
  const [selectedDashas, setSelectedDashas] = useState({});
  const [activeTab, setActiveTab] = useState('dashboard');
  const [mobileSubTab, setMobileSubTab] = useState('lagna');
  const [userSettings, setUserSettings] = useState({ node_type: 'mean', default_chart_style: 'north' });

  useEffect(() => {
    // Load saved layout from localStorage
    const savedLayouts = localStorage.getItem('astrology-dashboard-layout');
    if (savedLayouts) {
      setLayouts(JSON.parse(savedLayouts));
    }
    // Load today's transit data on component mount
    handleTransitDateChange(new Date());
    // Load user settings
    loadUserSettings();
  }, []);

  const loadUserSettings = async () => {
    if (!user?.phone) return;
    try {
      const { apiService } = await import('../../services/apiService');
      const settings = await apiService.getUserSettings(user.phone);
      setUserSettings(settings);
    } catch (error) {
      console.log('Using default settings');
    }
  };

  const refreshChartWithSettings = async () => {
    if (!birthData) return;
    try {
      const { apiService } = await import('../../services/apiService');
      const chartData = await apiService.calculateChart({
        name: birthData.name,
        date: birthData.date,
        time: birthData.time,
        latitude: birthData.latitude,
        longitude: birthData.longitude,
        timezone: birthData.timezone
      }, userSettings.node_type);
      
      setChartData(chartData);
      handleTransitDateChange(transitDate);
    } catch (error) {
      console.error('Failed to refresh chart:', error);
    }
  };

  const handleSettingsUpdate = async () => {
    await loadUserSettings();
    await refreshChartWithSettings();
  };



  const selectExistingChart = async (chart) => {
    try {
      const { apiService } = await import('../../services/apiService');
      
      const chartData = await apiService.calculateChart({
        name: chart.name,
        date: chart.date,
        time: chart.time,
        latitude: chart.latitude,
        longitude: chart.longitude,
        timezone: chart.timezone
      }, userSettings.node_type);
      
      setBirthData({
        name: chart.name,
        date: chart.date,
        time: chart.time,
        place: `${chart.latitude}, ${chart.longitude}`,
        latitude: chart.latitude,
        longitude: chart.longitude,
        timezone: chart.timezone
      });
      
      setChartData(chartData);
      handleTransitDateChange(new Date());
    } catch (error) {
      console.error('Failed to load chart:', error);
    }
  };

  const handleLayoutChange = (layout, layouts) => {
    setLayouts(layouts);
    localStorage.setItem('astrology-dashboard-layout', JSON.stringify(layouts));
  };

  const handleTransitDateChange = async (newDate) => {
    setTransitDate(newDate);
    setSelectedDashas({}); // Clear selected dashas to force recalculation
    try {
      const { apiService } = await import('../../services/apiService');
      const data = await apiService.calculateTransits({
        birth_data: birthData,
        transit_date: newDate.toISOString().split('T')[0]
      });
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
      <UnifiedHeader
        currentChart={birthData}
        onSelectChart={selectExistingChart}
        onViewAllCharts={onViewAllCharts}
        onNewChart={onBack}
        onLogout={onLogout}
        user={user}
        showTransitControls={window.innerWidth > 768}
        transitDate={transitDate}
        onTransitDateChange={handleTransitDateChange}
        onResetToToday={resetToToday}
        onSettings={() => setActiveTab('settings')}
      />

      {/* Tab Navigation */}
      <div style={{ 
        display: 'flex', 
        borderBottom: '3px solid #e91e63',
        marginBottom: '0.5rem',
        background: '#f8f9fa',
        borderRadius: window.innerWidth <= 768 ? '0' : '8px',
        padding: '0.3rem',
        margin: window.innerWidth <= 768 ? '0' : '0 0.5rem',
        overflowX: 'auto',
        scrollbarWidth: 'none',
        msOverflowStyle: 'none',
        WebkitOverflowScrolling: 'touch',
        position: window.innerWidth <= 768 ? 'fixed' : 'static',
        top: window.innerWidth <= 768 ? '60px' : 'auto',
        left: window.innerWidth <= 768 ? '0' : 'auto',
        right: window.innerWidth <= 768 ? '0' : 'auto',
        zIndex: window.innerWidth <= 768 ? 200 : 'auto'
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
          { id: 'remedies', label: '💎 Remedies', icon: '💎' },
          { id: 'settings', label: '⚙️ Settings', icon: '⚙️' },
          ...(user?.role === 'admin' ? [
            { id: 'rule-engine', label: '⚙️ Rule Engine', icon: '⚙️' },
            { id: 'event-analyzer', label: '🔍 Event Analyzer', icon: '🔍' }
          ] : [])
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: window.innerWidth <= 768 ? '0.4rem 0.8rem' : '0.5rem 1rem',
              background: activeTab === tab.id ? '#e91e63' : 'transparent',
              color: activeTab === tab.id ? 'white' : '#e91e63',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: window.innerWidth <= 768 ? '0.65rem' : '0.8rem',
              fontWeight: '600',
              marginRight: '0.2rem',
              whiteSpace: 'nowrap',
              minWidth: 'fit-content',
              flexShrink: 0
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'dashboard' && (
        window.innerWidth <= 768 ? (
          // Mobile Layout - Bottom Tabs
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            position: 'fixed',
            top: '120px',
            left: '0',
            right: '0',
            bottom: '0'
          }}>
            {/* Main Content Area */}
            <div style={{ 
              flex: 1, 
              padding: '0.5rem', 
              overflow: 'hidden',
              marginBottom: '80px'
            }}>
              {mobileSubTab === 'lagna' && (
                <div style={{ height: '100%' }}>
                  <ChartWidget
                    title="Lagna Chart"
                    chartType="lagna"
                    chartData={chartData}
                    birthData={birthData}
                    defaultStyle={userSettings.default_chart_style}
                  />
                </div>
              )}
              {mobileSubTab === 'navamsa' && (
                <div style={{ height: '100%' }}>
                  <ChartWidget
                    title="Navamsa Chart"
                    chartType="navamsa"
                    chartData={chartData}
                    birthData={birthData}
                    defaultStyle={userSettings.default_chart_style}
                  />
                </div>
              )}
              {mobileSubTab === 'transit' && (
                <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <TransitDateControls
                    transitDate={transitDate}
                    onTransitDateChange={handleTransitDateChange}
                    onResetToToday={resetToToday}
                  />
                  <div style={{ flex: 1 }}>
                    <ChartWidget
                      title="Transit Chart"
                      chartType="transit"
                      chartData={transitData || chartData}
                      birthData={birthData}
                      transitDate={transitDate}
                      defaultStyle={userSettings.default_chart_style}
                    />
                  </div>
                </div>
              )}
              {mobileSubTab === 'divisional' && (
                <div style={{ height: '100%' }}>
                  <DivisionalChartSelector
                    chartData={chartData}
                    birthData={birthData}
                    defaultStyle={userSettings.default_chart_style}
                  />
                </div>
              )}
              {mobileSubTab === 'dashas' && (
                <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <TransitDateControls
                    transitDate={transitDate}
                    onTransitDateChange={handleTransitDateChange}
                    onResetToToday={resetToToday}
                  />
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: '1fr 1fr', 
                    gridTemplateRows: 'repeat(3, 1fr)',
                    gap: '0.5rem', 
                    flex: 1, 
                    overflow: 'auto' 
                  }}>
                  <div>
                    <DashaWidget
                      title="Maha"
                      dashaType="maha"
                      birthData={birthData}
                      onDashaClick={handleDashaClick}
                      selectedDashas={selectedDashas}
                      onDashaSelection={handleDashaSelection}
                      transitDate={transitDate}
                    />
                  </div>
                  <div>
                    <DashaWidget
                      title="Antar"
                      dashaType="antar"
                      birthData={birthData}
                      onDashaClick={handleDashaClick}
                      selectedDashas={selectedDashas}
                      onDashaSelection={handleDashaSelection}
                      transitDate={transitDate}
                    />
                  </div>
                  <div>
                    <DashaWidget
                      title="Pratyantar"
                      dashaType="pratyantar"
                      birthData={birthData}
                      onDashaClick={handleDashaClick}
                      selectedDashas={selectedDashas}
                      onDashaSelection={handleDashaSelection}
                      transitDate={transitDate}
                    />
                  </div>
                  <div>
                    <DashaWidget
                      title="Sookshma"
                      dashaType="sookshma"
                      birthData={birthData}
                      onDashaClick={handleDashaClick}
                      selectedDashas={selectedDashas}
                      onDashaSelection={handleDashaSelection}
                      transitDate={transitDate}
                    />
                  </div>
                  <div>
                    <DashaWidget
                      title="Prana"
                      dashaType="prana"
                      birthData={birthData}
                      onDashaClick={handleDashaClick}
                      selectedDashas={selectedDashas}
                      onDashaSelection={handleDashaSelection}
                      transitDate={transitDate}
                    />
                  </div>
                </div>
                </div>
              )}
              {mobileSubTab === 'yogi' && (
                <div style={{ height: '100%' }}>
                  <YogiWidget />
                </div>
              )}
              {mobileSubTab === 'panchang' && (
                <div style={{ height: '100%' }}>
                  <PanchangWidget transitDate={transitDate} />
                </div>
              )}
            </div>
            
            {/* Bottom Tab Navigation */}
            <div style={{
              display: 'flex',
              background: 'rgba(255, 255, 255, 0.95)',
              borderTop: '2px solid #e91e63',
              padding: '0.5rem 0.25rem',
              gap: '0.25rem',
              overflowX: 'auto',
              scrollbarWidth: 'none',
              msOverflowStyle: 'none',
              WebkitOverflowScrolling: 'touch',
              position: 'fixed',
              bottom: '0',
              left: '0',
              right: '0',
              zIndex: 1000,
              width: '100%'
            }}>
              {[
                { id: 'lagna', label: '📊 Lagna', icon: '📊' },
                { id: 'navamsa', label: '🌙 Navamsa', icon: '🌙' },
                { id: 'transit', label: '🔄 Transit', icon: '🔄' },
                { id: 'divisional', label: '📈 Divisional', icon: '📈' },
                { id: 'dashas', label: '⏰ Dashas', icon: '⏰' },
                { id: 'yogi', label: '🧘 Yogi', icon: '🧘' },
                { id: 'panchang', label: '📅 Panchang', icon: '📅' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setMobileSubTab(tab.id)}
                  style={{
                    flex: 1,
                    padding: '0.5rem 0.25rem',
                    background: mobileSubTab === tab.id ? '#e91e63' : 'transparent',
                    color: mobileSubTab === tab.id ? 'white' : '#e91e63',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '0.6rem',
                    fontWeight: '600',
                    whiteSpace: 'nowrap',
                    minWidth: 'fit-content',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '0.1rem'
                  }}
                >
                  <span style={{ fontSize: '0.8rem' }}>{tab.icon}</span>
                  <span>{tab.label.split(' ')[1]}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          // Desktop Layout - Grid
          <GridContainer>
            <GridItem chart>
              <ChartWidget
                title="Lagna Chart"
                chartType="lagna"
                chartData={chartData}
                birthData={birthData}
                defaultStyle={userSettings.default_chart_style}
              />
            </GridItem>
            
            <GridItem chart>
              <ChartWidget
                title="Navamsa Chart"
                chartType="navamsa"
                chartData={chartData}
                birthData={birthData}
                defaultStyle={userSettings.default_chart_style}
              />
            </GridItem>
            
            <GridItem chart>
              <ChartWidget
                title="Transit Chart"
                chartType="transit"
                chartData={transitData || chartData}
                birthData={birthData}
                transitDate={transitDate}
                defaultStyle={userSettings.default_chart_style}
              />
            </GridItem>
            
            <GridItem chart>
              <DivisionalChartSelector
                chartData={chartData}
                birthData={birthData}
                defaultStyle={userSettings.default_chart_style}
              />
            </GridItem>
            
            <div style={{ 
              gridColumn: '1 / -1', 
              display: 'grid', 
              gridTemplateColumns: 'repeat(7, 1fr)', 
              gap: '0.3rem', 
              height: '30vh' 
            }}>
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
        )
      )}
      
      {activeTab !== 'dashboard' && (
        <div style={{ 
          background: 'rgba(255,255,255,0.95)',
          borderRadius: '12px',
          padding: '1rem',
          margin: window.innerWidth <= 768 ? '0 0.5rem' : '0 1rem',
          marginTop: window.innerWidth <= 768 ? '110px' : '0',
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
          {activeTab === 'settings' && <UserSettings user={user} onSettingsUpdate={handleSettingsUpdate} />}
          {activeTab === 'rule-engine' && user?.role === 'admin' && <RuleManager />}
          {activeTab === 'event-analyzer' && user?.role === 'admin' && <EventAnalyzer birthChart={chartData} />}

        </div>
      )}
    </DashboardContainer>
  );
};

export default Dashboard;