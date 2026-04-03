import React, { useState, useEffect, useRef } from 'react';
import { useAstrology } from '../../context/AstrologyContext';
import { DASHBOARD_CONFIG } from '../../config/dashboard.config';
import { getCurrentDomainConfig, ASTROROSHNI_OPEN_NATIVE_SELECTOR_SESSION_KEY } from '../../config/domains.config';
import ChartWidget from '../Charts/ChartWidget';
import DashaWidget from '../DashaTable/DashaWidget';
import DashaHierarchyBar from '../DashaHierarchyBar/DashaHierarchyBar';
import TransitControls from '../TransitControls/TransitControls';
import VedicTransitAspects from '../TransitAspects/VedicTransitAspects';
import EventPredictionWidget from '../EventPredictionWidget/EventPredictionWidget';
import NakshatrasTab from '../NakshatrasTab/NakshatrasTab';
import YogasTab from '../YogasTab/YogasTab';
import RelationshipsTab from '../RelationshipsTab/RelationshipsTab';
import HouseAnalysisTab from '../HouseAnalysisTab/HouseAnalysisTab';
import MarriageAnalysisTab from '../MarriageAnalysis/MarriageAnalysisTab';
import CompleteHealthAnalysisTab from '../Health/CompleteHealthAnalysisTab';
import NadiTab from '../Nadi/NadiTab';
import DashaBrowser from '../DashaBrowser/DashaBrowser';

import TransitAspectsPopup from '../TransitAspectsPopup/TransitAspectsPopup';
import ClassicalPrediction from '../ClassicalPrediction/ClassicalPrediction';
import UnifiedHeader from '../UnifiedHeader/UnifiedHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import UserSettings from '../UserSettings';
import AdminTab from '../AdminTab/AdminTab';
import TransitDateControls from '../TransitDateControls/TransitDateControls';
import { DashboardContainer, Header, BackButton, Title, GridContainer, GridItem } from './Dashboard.styles';



const DivisionalChartSelector = ({ chartData, birthData, defaultStyle, chartRefHighlight }) => {
  const [selectedChart, setSelectedChart] = useState('hora');
  const [showDropdown, setShowDropdown] = useState(false);
  const isMobile = window.innerWidth <= 768;
  
  const divisionalCharts = [
    { value: 'hora', label: 'Hora (D2)', division: 2 },
    { value: 'drekkana', label: 'Drekkana (D3)', division: 3 },
    { value: 'chaturthamsa', label: 'Chaturthamsa (D4)', division: 4 },
    { value: 'saptamsa', label: 'Saptamsa (D7)', division: 7 },
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
              zIndex: 10001,
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
            chartRefHighlight={chartRefHighlight}
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
      chartRefHighlight={chartRefHighlight}
    />
  );
};

const Dashboard = ({ onBack, onViewAllCharts, onNewChart, currentView, setCurrentView, onLogout, user }) => {
  const { birthData, chartData, setBirthData, setChartData } = useAstrology();
  const [layouts, setLayouts] = useState(DASHBOARD_CONFIG.defaultLayout);
  const [transitDate, setTransitDate] = useState(new Date());
  const [transitData, setTransitData] = useState(null);
  const [selectedDashas, setSelectedDashas] = useState({});
  const [cascadingDashaData, setCascadingDashaData] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [mobileSubTab, setMobileSubTab] = useState('lagna');
  const [userSettings, setUserSettings] = useState({ node_type: 'mean', default_chart_style: 'north' });
  const [chartRefHighlight, setChartRefHighlight] = useState(null);
  const [showTransitAspectsPopup, setShowTransitAspectsPopup] = useState(false);
  const [showBirthFormModal, setShowBirthFormModal] = useState(false);

  useEffect(() => {
    if (!birthData || !chartData) {
      const domainConfig = getCurrentDomainConfig();
      if (domainConfig.userType === 'general') {
        try {
          sessionStorage.setItem(ASTROROSHNI_OPEN_NATIVE_SELECTOR_SESSION_KEY, '1');
        } catch {
          /* ignore */
        }
        setCurrentView('astroroshnihomepage');
      } else {
        setCurrentView('selector');
      }
    }
  }, [birthData, chartData, setCurrentView]);

  useEffect(() => {
    if (!birthData || !chartData) return;
    // Load saved layout from localStorage
    const savedLayouts = localStorage.getItem('astrology-dashboard-layout');
    if (savedLayouts) {
      setLayouts(JSON.parse(savedLayouts));
    }
    // Load today's transit data and cascading dashas on component mount
    handleTransitDateChange(new Date());
    // Load user settings
    loadUserSettings();
  }, [birthData, chartData]);

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
      const chartData = await apiService.calculateChartOnly({
        name: birthData.name,
        date: birthData.date,
        time: birthData.time,
        latitude: birthData.latitude,
        longitude: birthData.longitude,
        place: birthData.place || ''
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

  const handleLayoutChange = (layout, layouts) => {
    setLayouts(layouts);
    localStorage.setItem('astrology-dashboard-layout', JSON.stringify(layouts));
  };

  const handleTransitDateChange = async (newDate) => {
    setTransitDate(newDate);
    setSelectedDashas({});
    
    try {
      const { apiService } = await import('../../services/apiService');
      
      // Calculate transits
      const transitData = await apiService.calculateTransits({
        birth_data: birthData,
        transit_date: newDate.toISOString().split('T')[0]
      });
      setTransitData(transitData);
      
      // Calculate cascading dashas
      const response = await fetch('/api/calculate-cascading-dashas', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          birth_data: birthData,
          target_date: newDate.toISOString().split('T')[0]
        })
      });
      
      if (response.ok) {
        const cascadingData = await response.json();
        setCascadingDashaData(cascadingData);
      }
    } catch (error) {
      console.error('Error fetching transit/dasha data:', error);
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
    const isAstroRoshni = getCurrentDomainConfig().userType === 'general';
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
        {isAstroRoshni ? 'Opening native selector…' : 'Opening chart selector…'}
      </div>
    );
  }

  return (
    <DashboardContainer style={{ overflow: 'visible' }}>
      <UnifiedHeader
        currentChart={birthData}
        onChangeNative={() => setShowBirthFormModal(true)}
        onViewAllCharts={onViewAllCharts}
        onNewChart={onNewChart || onBack}
        onLogout={onLogout}
        user={user}
        showTransitControls={window.innerWidth > 768}
        transitDate={transitDate}
        onTransitDateChange={handleTransitDateChange}
        onResetToToday={resetToToday}
        onSettings={() => setActiveTab('settings')}
      />

      <BirthFormModal
        isOpen={showBirthFormModal}
        onClose={() => setShowBirthFormModal(false)}
        onSubmit={() => {
          setTimeout(() => {
            setCascadingDashaData(null);
            handleTransitDateChange(transitDate);
          }, 0);
        }}
      />

      {/* Tab Navigation */}
      <div style={{ 
        display: 'flex', 
        borderBottom: '3px solid #e91e63',
        background: '#f8f9fa',
        borderRadius: window.innerWidth <= 768 ? '0' : '8px',
        padding: window.innerWidth <= 768 ? '0.3rem 0.35rem' : '0.45rem 0.6rem',
        minHeight: window.innerWidth <= 768 ? '42px' : '46px',
        marginTop: 0,
        marginBottom: window.innerWidth <= 768 ? '0.08rem' : '0.2rem',
        marginLeft: window.innerWidth <= 768 ? 0 : '0.5rem',
        marginRight: window.innerWidth <= 768 ? 0 : '0.5rem',
        overflowX: 'auto',
        scrollbarWidth: 'none',
        msOverflowStyle: 'none',
        WebkitOverflowScrolling: 'touch',
        '&::-webkit-scrollbar': {
          display: 'none'
        },
        position: window.innerWidth <= 768 ? 'fixed' : 'static',
        top: window.innerWidth <= 768 ? '60px' : 'auto',
        left: window.innerWidth <= 768 ? '0' : 'auto',
        right: window.innerWidth <= 768 ? '0' : 'auto',
        zIndex: window.innerWidth <= 768 ? 200 : 'auto',
        alignItems: 'center'
      }}>
        {[
          { id: 'dashboard', label: '🕉️ Parashara', icon: '🕉️' },
          { id: 'dashas', label: '⏰ Dasha Browser', icon: '⏰' },
          { id: 'nadi', label: '🔍 Nadi', icon: '🔍' },
          { id: 'marriage', label: '💍 Marriage', icon: '💍' },
          { id: 'health', label: '🏥 Health', icon: '🏥' },
          { id: 'nakshatras', label: '🌟 Nakshatras', icon: '🌟' },
          { id: 'houses', label: '🏠 House Analysis', icon: '🏠' },
          { id: 'relationships', label: '🤝 Relationships', icon: '🤝' },
          { id: 'yogas', label: '🔮 Yogas', icon: '🔮' },
          { id: 'settings', label: '⚙️ Settings', icon: '⚙️' },
          ...(user?.role === 'admin' ? [
            { id: 'admin', label: '🛠️ Admin', icon: '🛠️' }
          ] : [])
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: window.innerWidth <= 768 ? '0.4rem 0.65rem' : '0.6rem 1.2rem',
              background: activeTab === tab.id ? '#e91e63' : 'transparent',
              color: activeTab === tab.id ? 'white' : '#e91e63',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: window.innerWidth <= 768 ? '0.78rem' : '1rem',
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
            top: '128px',
            left: '0',
            right: '0',
            bottom: '80px',
            overflow: 'hidden'
          }}>
            {/* Main Content Area */}
            <div style={{ 
              flex: 1, 
              padding: '0.08rem 0.35rem 0.35rem', 
              overflow: 'hidden'
            }}>
              {mobileSubTab === 'lagna' && (
                <div style={{ height: '100%' }}>
                  <ChartWidget
                    title="Lagna Chart"
                    chartType="lagna"
                    chartData={chartData}
                    birthData={birthData}
                    defaultStyle={userSettings.default_chart_style}
                    chartRefHighlight={chartRefHighlight}
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
                    chartRefHighlight={chartRefHighlight}
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
                      chartRefHighlight={chartRefHighlight}
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
                    chartRefHighlight={chartRefHighlight}
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
                  <DashaHierarchyBar selectedDashas={selectedDashas} transitDate={transitDate} />
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
                      cascadingData={cascadingDashaData}
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
                      cascadingData={cascadingDashaData}
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
                      cascadingData={cascadingDashaData}
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
                      cascadingData={cascadingDashaData}
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
                      cascadingData={cascadingDashaData}
                    />
                  </div>
                </div>
                </div>
              )}
              {mobileSubTab === 'transit-aspects' && (
                <div style={{ height: '100%' }}>
                  <VedicTransitAspects 
                    birthData={birthData} 
                    onTimelineClick={handleTransitDateChange}
                    natalChart={chartData}
                  />
                </div>
              )}
            </div>
            
            {/* Bottom Tab Navigation */}
            <div style={{
              display: 'flex',
              background: 'rgba(255, 255, 255, 0.95)',
              borderTop: '2px solid #e91e63',
              padding: '0.3rem 0.15rem',
              gap: '0.2rem',
              overflowX: 'auto',
              scrollbarWidth: 'none',
              msOverflowStyle: 'none',
              WebkitOverflowScrolling: 'touch',
              '&::-webkit-scrollbar': {
                display: 'none'
              },
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
                { id: 'transit-aspects', label: '🎯 Aspects', icon: '🎯' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setMobileSubTab(tab.id)}
                  style={{
                    flex: 1,
                    padding: '0.4rem 0.1rem',
                    background: mobileSubTab === tab.id ? '#e91e63' : 'transparent',
                    color: mobileSubTab === tab.id ? 'white' : '#e91e63',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '0.5rem',
                    fontWeight: '600',
                    whiteSpace: 'nowrap',
                    minWidth: 'fit-content',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '0.1rem',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}
                >
                  <span style={{ fontSize: '0.7rem' }}>{tab.icon}</span>
                  <span style={{ fontSize: '0.5rem', maxWidth: '100%', overflow: 'hidden', textOverflow: 'ellipsis' }}>{tab.label.split(' ')[1]}</span>
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
                chartRefHighlight={chartRefHighlight}
              />
            </GridItem>
            
            <GridItem chart>
              <ChartWidget
                title="Navamsa Chart"
                chartType="navamsa"
                chartData={chartData}
                birthData={birthData}
                defaultStyle={userSettings.default_chart_style}
                chartRefHighlight={chartRefHighlight}
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
                chartRefHighlight={chartRefHighlight}
              />
            </GridItem>
            
            <GridItem chart>
              <DivisionalChartSelector
                chartData={chartData}
                birthData={birthData}
                defaultStyle={userSettings.default_chart_style}
                chartRefHighlight={chartRefHighlight}
              />
            </GridItem>
            
            <div style={{ 
              gridColumn: '1 / -1', 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center',
              padding: '0.3rem 0'
            }}>
              <DashaHierarchyBar selectedDashas={selectedDashas} transitDate={transitDate} />
            </div>
            
            <div style={{ 
              gridColumn: '1 / -1', 
              display: 'grid', 
              gridTemplateColumns: 'repeat(7, 1fr)', 
              gap: '0.3rem', 
              height: '26vh' 
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
                  cascadingData={cascadingDashaData}
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
                  cascadingData={cascadingDashaData}
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
                  cascadingData={cascadingDashaData}
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
                  cascadingData={cascadingDashaData}
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
                  cascadingData={cascadingDashaData}
                />
              </GridItem>
              
              <GridItem dasha style={{ gridColumn: 'span 2' }}>
                <div style={{
                  background: 'white',
                  borderRadius: '8px',
                  padding: '1rem',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '2px solid #e91e63'
                }}>
                  <h4 style={{ margin: '0 0 0.5rem 0', color: '#e91e63' }}>Transit Aspects</h4>
                  <button
                    onClick={() => setShowTransitAspectsPopup(true)}
                    style={{
                      background: '#e91e63',
                      color: 'white',
                      border: 'none',
                      borderRadius: '8px',
                      padding: '0.75rem 1.5rem',
                      fontSize: '1rem',
                      fontWeight: '600',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                  >
                    🎯 View Transit Aspects
                  </button>
                </div>
              </GridItem>
            </div>
          </GridContainer>
        )
      )}
      
      {activeTab !== 'dashboard' && (
        activeTab === 'nadi' && window.innerWidth <= 768 ? (
          <NadiTab birthData={birthData} transitDate={transitDate} onTransitDateChange={handleTransitDateChange} selectedDashas={selectedDashas} onDashaSelection={handleDashaSelection} />
        ) : (
          <div style={{ 
            background: 'rgba(255,255,255,0.95)',
            borderRadius: '12px',
            padding: window.innerWidth <= 768 ? '0.28rem 0.45rem 0.65rem' : '0.4rem 1rem 1rem',
            margin: window.innerWidth <= 768 ? '0 0.35rem' : '0 1rem',
            marginTop: window.innerWidth <= 768 ? '128px' : '0',
            minHeight: '70vh',
            boxShadow: '0 4px 16px rgba(0,0,0,0.1)'
          }}>
            {activeTab === 'classical' && <ClassicalPrediction birthData={birthData} />}
            {activeTab === 'dashas' && <DashaBrowser birthData={birthData} chartData={chartData} />}
            {activeTab === 'nadi' && <NadiTab birthData={birthData} transitDate={transitDate} onTransitDateChange={handleTransitDateChange} selectedDashas={selectedDashas} onDashaSelection={handleDashaSelection} />}
            {activeTab === 'marriage' && <MarriageAnalysisTab chartData={chartData} birthDetails={birthData} />}
            {activeTab === 'health' && <CompleteHealthAnalysisTab chartData={chartData} birthDetails={birthData} />}
            {activeTab === 'nakshatras' && <NakshatrasTab chartData={chartData} birthData={birthData} />}
            {activeTab === 'houses' && <HouseAnalysisTab chartData={chartData} birthData={birthData} />}
            {activeTab === 'relationships' && <RelationshipsTab chartData={chartData} birthData={birthData} />}
            {activeTab === 'yogas' && <YogasTab chartData={chartData} birthData={birthData} />}
            {activeTab === 'settings' && <UserSettings user={user} onSettingsUpdate={handleSettingsUpdate} />}
            {activeTab === 'admin' && user?.role === 'admin' && <AdminTab chartData={chartData} birthData={birthData} />}
          </div>
        )
      )}
      
      <TransitAspectsPopup
        isOpen={showTransitAspectsPopup}
        onClose={() => setShowTransitAspectsPopup(false)}
        birthData={birthData}
        natalChart={chartData}
        onTimelineClick={handleTransitDateChange}
      />
    </DashboardContainer>
  );
};

export default Dashboard;