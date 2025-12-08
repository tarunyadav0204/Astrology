import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAstrology } from '../context/AstrologyContext';
import { apiService } from '../services/apiService';
import ChartWidget from '../components/ChartWidget';
import DashaWidget from '../components/DashaWidget';
import YogiWidget from '../components/YogiWidget';
import PanchangWidget from '../components/PanchangWidget';
import TransitDateControls from '../components/TransitDateControls';
import UnifiedHeader from '../components/UnifiedHeader';
import NakshatrasTab from '../components/NakshatrasTab';
import YogasTab from '../components/YogasTab';
import RelationshipsTab from '../components/RelationshipsTab';
import HouseAnalysisTab from '../components/HouseAnalysisTab';
import SettingsTab from '../components/SettingsTab';
import DateNavigationControls from '../components/DateNavigationControls';

const { width } = Dimensions.get('window');

const DivisionalChartSelector = ({ chartData, birthData, defaultStyle }) => {
  const [selectedChart, setSelectedChart] = useState('navamsa');
  const [showDropdown, setShowDropdown] = useState(false);
  
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
  
  return (
    <View style={styles.divisionalContainer}>
      <View style={styles.divisionalHeader}>
        <TouchableOpacity
          onPress={() => setShowDropdown(!showDropdown)}
          style={styles.divisionalButton}
        >
          <Text style={styles.divisionalButtonText}>{currentChart?.label}</Text>
          <Text style={styles.divisionalArrow}>▼</Text>
        </TouchableOpacity>
        {showDropdown && (
          <View style={styles.divisionalDropdown}>
            <ScrollView style={styles.divisionalList}>
              {divisionalCharts.map(chart => (
                <TouchableOpacity
                  key={chart.value}
                  onPress={() => {
                    setSelectedChart(chart.value);
                    setShowDropdown(false);
                  }}
                  style={[
                    styles.divisionalOption,
                    selectedChart === chart.value && styles.selectedDivisionalOption
                  ]}
                >
                  <Text style={styles.divisionalOptionText}>{chart.label}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}
      </View>
      <View style={styles.divisionalChart}>
        <ChartWidget
          title={`Divisional Chart (D${currentChart?.division || 9})`}
          chartType="divisional"
          chartData={chartData}
          birthData={birthData}
          division={currentChart?.division || 9}
          defaultStyle={defaultStyle}
        />
      </View>
    </View>
  );
};

export default function DashboardScreen({ navigation }) {
  const { user, setUser, birthData, setBirthData, chartData, setChartData } = useAstrology();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [mobileSubTab, setMobileSubTab] = useState('lagna');
  const [transitDate, setTransitDate] = useState(new Date());
  const [transitData, setTransitData] = useState(null);
  const [selectedDashas, setSelectedDashas] = useState({});
  const [showMenu, setShowMenu] = useState(false);
  const [userSettings, setUserSettings] = useState({ 
    node_type: 'mean', 
    default_chart_style: 'north' 
  });

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'nakshatras', label: 'Nakshatras', icon: '⭐' },
    { id: 'houses', label: 'Houses', icon: '🏠' },
    { id: 'relationships', label: 'Relations', icon: '🤝' },
    { id: 'yogas', label: 'Yogas', icon: '🔮' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ];



  useEffect(() => {
    loadUserData();
    loadDemoChart();
    handleTransitDateChange(new Date());
  }, []);

  useEffect(() => {
    // Handle route params for birth data
    const routeParams = navigation.getState()?.routes?.find(r => r.name === 'Dashboard')?.params;
    if (routeParams?.birthData && !birthData) {
      setBirthData(routeParams.birthData);
      loadChartData(routeParams.birthData);
    }
  }, [navigation]);

  const loadChartData = async (data) => {
    try {
      const { calculateChart } = useAstrology();
      await calculateChart(data);
    } catch (error) {
      console.error('Error loading chart data:', error);
      if (error.response?.status === 401) {
        handleLogout();
      }
    }
  };

  const loadUserData = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const user = JSON.parse(userData);
        setUser(user);
        // Load user settings
        if (user.phone) {
          const settings = await apiService.getUserSettings(user.phone);
          setUserSettings(settings);
        }
      }
    } catch (error) {
      console.error('Error loading user data:', error);
      if (error.response?.status === 401) {
        handleLogout();
      }
    }
  };

  const loadDemoChart = () => {
    // Skip demo chart loading - let user enter birth data
  };

  const handleLogout = async () => {
    try {
      await AsyncStorage.removeItem('userToken');
      await AsyncStorage.removeItem('userData');
      setUser(null);
      navigation.reset({
        index: 0,
        routes: [{ name: 'Landing' }],
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const handleTransitDateChange = async (newDate) => {
    setTransitDate(newDate);
    setSelectedDashas({});
    setTransitData(chartData);
  };

  const handleDashaClick = (dashaDate) => {
    setTransitDate(new Date(dashaDate));
    handleTransitDateChange(new Date(dashaDate));
  };

  const handleDashaSelection = (dashaType, dasha) => {
    // console.log('📝 DASHBOARD DASHA SELECTION:', {
      dashaType,
      selectedPlanet: dasha?.planet,
      currentSelectedDashas: selectedDashas
    });
    
    setSelectedDashas(prev => {
      const newSelection = { ...prev, [dashaType]: dasha };
      
      // Clear child dashas when parent changes
      if (dashaType === 'maha') {
        delete newSelection.antar;
        delete newSelection.pratyantar;
        delete newSelection.sookshma;
        delete newSelection.prana;
      } else if (dashaType === 'antar') {
        delete newSelection.pratyantar;
        delete newSelection.sookshma;
        delete newSelection.prana;
      } else if (dashaType === 'pratyantar') {
        delete newSelection.sookshma;
        delete newSelection.prana;
      } else if (dashaType === 'sookshma') {
        delete newSelection.prana;
      }
      
      // console.log('📝 NEW SELECTED DASHAS:', newSelection);
      return newSelection;
    });
  };

  const resetToToday = () => {
    const today = new Date();
    setTransitDate(today);
    setSelectedDashas({});
    handleTransitDateChange(today);
  };

  const selectExistingChart = () => {};
  const onViewAllCharts = () => {};
  const onNewChart = () => {};

  if (!birthData || !chartData) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <LinearGradient
      colors={['#fffbf0', '#fff8e1', '#fff3c4']}
      style={styles.container}
    >
    <SafeAreaView style={styles.transparentContainer} pointerEvents="auto">
      <View style={styles.mobileHeader}>
        <TouchableOpacity 
          style={styles.hamburgerButton} 
          onPress={() => setShowMenu(!showMenu)}
          activeOpacity={0.7}
        >
          <Text style={styles.hamburgerIcon}>☰</Text>
        </TouchableOpacity>
        
        <View style={styles.headerCenter}>
          <Text style={styles.appTitle}>🔮 AstroGPT</Text>
          {birthData && (
            <Text style={styles.chartInfo}>
              {birthData.name} • {birthData.date}
            </Text>
          )}
        </View>
        
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutButtonText}>Logout</Text>
        </TouchableOpacity>
      </View>

      {/* Top Navigation */}
      <View style={styles.topNavContainer}>
        <ScrollView 
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.topNavContent}
        >
          {tabs.map(tab => (
            <TouchableOpacity
              key={tab.id}
              onPress={() => setActiveTab(tab.id)}
              style={styles.topNavTab}
            >
              <View style={styles.topNavContent}>
                <Text style={styles.topNavIcon}>{tab.icon}</Text>
                <Text style={[
                  styles.topNavText,
                  activeTab === tab.id && styles.activeTopNavText
                ]}>
                  {tab.label}
                </Text>
              </View>
              {activeTab === tab.id && <View style={styles.topNavIndicator} />}
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Tab Content - Chart moved to top */}
      <View style={styles.tabContentContainer}>
        {activeTab === 'dashboard' && (
        <View style={styles.dashboardContainer}>
          {/* Main Content Area */}
          <View style={styles.mainContent}>
          {/* Chart at Top */}
          {mobileSubTab === 'lagna' && (
            <View style={styles.topChartContainer}>
              <ChartWidget
                title="Lagna Chart"
                chartType="lagna"
                chartData={chartData}
                birthData={birthData}
                defaultStyle={userSettings.default_chart_style}
              />
            </View>
          )}
          {mobileSubTab === 'navamsa' && (
            <View style={styles.topChartContainer}>
              <ChartWidget
                title="Navamsa Chart"
                chartType="navamsa"
                chartData={chartData}
                birthData={birthData}
                defaultStyle={userSettings.default_chart_style}
              />
            </View>
          )}
          {mobileSubTab === 'transit' && (
            <View style={styles.topChartContainer}>
              <DateNavigationControls
                transitDate={transitDate}
                onTransitDateChange={handleTransitDateChange}
                onResetToToday={resetToToday}
              />
              <View style={styles.chartWrapper}>
                <ChartWidget
                  title="Transit Chart"
                  chartType="transit"
                  chartData={transitData || chartData}
                  birthData={birthData}
                  transitDate={transitDate}
                  defaultStyle={userSettings.default_chart_style}
                />
              </View>
            </View>
          )}
          {mobileSubTab === 'divisional' && (
            <View style={styles.topChartContainer}>
              <DivisionalChartSelector
                chartData={chartData}
                birthData={birthData}
                defaultStyle={userSettings.default_chart_style}
              />
            </View>
          )}
            {mobileSubTab === 'dashas' && (
              <ScrollView style={styles.dashaScrollContainer} showsVerticalScrollIndicator={false}>
                <DateNavigationControls
                  transitDate={transitDate}
                  onTransitDateChange={handleTransitDateChange}
                  onResetToToday={resetToToday}
                />
                {/* Dasha Hierarchy Header */}
                {Object.keys(selectedDashas).length > 0 && (
                  <View style={styles.dashaHierarchyHeader}>
                    <Text style={styles.dashaHierarchyText}>
                      {[
                        selectedDashas.maha?.planet,
                        selectedDashas.antar?.planet,
                        selectedDashas.pratyantar?.planet,
                        selectedDashas.sookshma?.planet,
                        selectedDashas.prana?.planet
                      ].filter(Boolean).join(' → ')}
                    </Text>
                  </View>
                )}
                <View style={styles.dashaGrid}>
                  <View style={styles.dashaRow}>
                    <DashaWidget
                      key="maha-widget"
                      title="Maha"
                      dashaType="maha"
                      birthData={birthData}
                      onDashaClick={handleDashaClick}
                      selectedDashas={selectedDashas}
                      onDashaSelection={handleDashaSelection}
                      transitDate={transitDate}
                    />
                    <DashaWidget
                      key="antar-widget"
                      title="Antar"
                      dashaType="antar"
                      birthData={birthData}
                      onDashaClick={handleDashaClick}
                      selectedDashas={selectedDashas}
                      onDashaSelection={handleDashaSelection}
                      transitDate={transitDate}
                    />
                  </View>
                  <View style={styles.dashaRow}>
                    <DashaWidget
                      key="pratyantar-widget"
                      title="Pratyantar"
                      dashaType="pratyantar"
                      birthData={birthData}
                      onDashaClick={handleDashaClick}
                      selectedDashas={selectedDashas}
                      onDashaSelection={handleDashaSelection}
                      transitDate={transitDate}
                    />
                    <DashaWidget
                      key="sookshma-widget"
                      title="Sookshma"
                      dashaType="sookshma"
                      birthData={birthData}
                      onDashaClick={handleDashaClick}
                      selectedDashas={selectedDashas}
                      onDashaSelection={handleDashaSelection}
                      transitDate={transitDate}
                    />
                  </View>
                  <View style={styles.dashaRow}>
                    <DashaWidget
                      key="prana-widget"
                      title="Prana"
                      dashaType="prana"
                      birthData={birthData}
                      onDashaClick={handleDashaClick}
                      selectedDashas={selectedDashas}
                      onDashaSelection={handleDashaSelection}
                      transitDate={transitDate}
                    />
                  </View>
                </View>
              </ScrollView>
            )}
            {mobileSubTab === 'yogi' && (
              <View style={styles.chartContainer}>
                <YogiWidget />
              </View>
            )}
            {mobileSubTab === 'panchang' && (
              <View style={styles.chartContainer}>
                <PanchangWidget transitDate={transitDate} />
              </View>
            )}
          </View>
          
          {/* Bottom Navigation - Fixed */}
          <View style={styles.bottomNavigation}>
            {[
              { id: 'lagna', label: 'Lagna', icon: '📊' },
              { id: 'navamsa', label: 'Navamsa', icon: '🌙' },
              { id: 'transit', label: 'Transit', icon: '🔄' },
              { id: 'divisional', label: 'Divisional', icon: '📈' },
              { id: 'dashas', label: 'Dashas', icon: '⏰' }
            ].map(tab => (
              <TouchableOpacity
                key={tab.id}
                onPress={() => setMobileSubTab(tab.id)}
                style={styles.bottomNavTab}
              >
                {mobileSubTab === tab.id && <View style={styles.bottomNavIndicator} />}
                <Text style={styles.bottomNavIcon}>{tab.icon}</Text>
                <Text style={[
                  styles.bottomNavText,
                  mobileSubTab === tab.id && styles.activeBottomNavText
                ]}>
                  {tab.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}
      
        {activeTab !== 'dashboard' && (
          <View style={[styles.nonScrollableTabContent, {position: 'absolute', top: 0, left: 0, right: 0, bottom: 0}]}>
            {activeTab === 'nakshatras' && <NakshatrasTab chartData={chartData} birthData={birthData} />}
            {activeTab === 'houses' && <HouseAnalysisTab chartData={chartData} birthData={birthData} />}
            {activeTab === 'relationships' && <RelationshipsTab chartData={chartData} birthData={birthData} />}
            {activeTab === 'strengths' && <Text style={styles.comingSoon}>Strengths - Coming Soon</Text>}
            {activeTab === 'yogas' && <YogasTab chartData={chartData} birthData={birthData} />}
            {activeTab === 'timing' && <Text style={styles.comingSoon}>Timing - Coming Soon</Text>}
            {activeTab === 'predictions' && <Text style={styles.comingSoon}>Predictions - Coming Soon</Text>}
            {activeTab === 'remedies' && <Text style={styles.comingSoon}>Remedies - Coming Soon</Text>}
            {activeTab === 'settings' && <SettingsTab user={user} onSettingsUpdate={loadUserData} />}
          </View>
        )}
      </View>
      {showMenu && (
        <>
          <TouchableOpacity 
            style={styles.overlay} 
            onPress={() => setShowMenu(false)}
            activeOpacity={1}
          />
          <View style={styles.dropdownMenu}>
            <TouchableOpacity
              style={styles.menuItem}
              onPress={() => {
                navigation.navigate('ChartList');
                setShowMenu(false);
              }}
            >
              <Text style={styles.menuItemText}>🏠 Home</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.menuItem}
              onPress={() => {
                navigation.navigate('BirthForm');
                setShowMenu(false);
              }}
            >
              <Text style={styles.menuItemText}>➕ New Chart</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.menuItem}
              onPress={() => {
                setActiveTab('settings');
                setShowMenu(false);
              }}
            >
              <Text style={styles.menuItemText}>⚙️ Settings</Text>
            </TouchableOpacity>
            <View style={styles.menuDivider}>
              <Text style={styles.profileText}>👤 {user?.name || 'Profile'}</Text>
            </View>
            <TouchableOpacity
              style={[styles.menuItem, styles.logoutMenuItem]}
              onPress={() => {
                handleLogout();
                setShowMenu(false);
              }}
            >
              <Text style={styles.logoutMenuText}>🚪 Logout</Text>
            </TouchableOpacity>
          </View>
        </>
      )}
    </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  transparentContainer: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
  },
  topNavContainer: {
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  topNavContent: {
    paddingHorizontal: 16,
  },
  topNavTab: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    position: 'relative',
  },
  topNavContent: {
    alignItems: 'center',
    gap: 4,
  },
  topNavIcon: {
    fontSize: 16,
  },
  topNavText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '600',
  },
  activeTopNavText: {
    color: '#e91e63',
    fontWeight: '700',
  },
  topNavIndicator: {
    position: 'absolute',
    bottom: 0,
    left: 20,
    right: 20,
    height: 3,
    backgroundColor: '#e91e63',
    borderRadius: 2,
  },
  dashboardContainer: {
    flex: 1,
    position: 'relative',
  },
  mainContent: {
    flex: 1,
    paddingBottom: 70,
  },
  topChartContainer: {
    height: 500,
    marginVertical: 12,
    marginHorizontal: 12,
    backgroundColor: 'white',
    borderRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 16,
    elevation: 12,
  },
  chartWrapper: {
    flex: 1,
  },
  chartContainer: {
    flex: 1,
    margin: 8,
  },
  transitContainer: {
    flex: 1,
  },
  dashaScrollContainer: {
    flex: 1,
    maxHeight: '100%',
  },
  dashaHierarchyHeader: {
    backgroundColor: 'rgba(233, 30, 99, 0.1)',
    marginHorizontal: 12,
    marginTop: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(233, 30, 99, 0.2)',
  },
  dashaHierarchyText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#e91e63',
    textAlign: 'center',
  },
  dashaGrid: {
    padding: 6,
    paddingBottom: 10,
    overflow: 'hidden',
    gap: 15,
  },
  dashaRow: {
    flexDirection: 'row',
    marginBottom: 20,
    height: 160,
    flexShrink: 0,
  },
  divisionalContainer: {
    flex: 1,
  },
  divisionalHeader: {
    padding: 8,
    backgroundColor: '#f8f9fa',
    borderBottomWidth: 1,
    borderBottomColor: '#ddd',
    position: 'relative',
  },
  divisionalButton: {
    padding: 8,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 4,
    backgroundColor: 'white',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  divisionalButtonText: {
    fontSize: 14,
  },
  divisionalArrow: {
    fontSize: 12,
  },
  divisionalDropdown: {
    position: 'absolute',
    top: '100%',
    left: 8,
    right: 8,
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 4,
    zIndex: 1000,
    maxHeight: 200,
  },
  divisionalList: {
    maxHeight: 200,
  },
  divisionalOption: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  selectedDivisionalOption: {
    backgroundColor: '#f0f0f0',
  },
  divisionalOptionText: {
    fontSize: 14,
  },
  divisionalChart: {
    flex: 1,
  },

  tabContentContainer: {
    flex: 1,
  },
  tabContent: {
    flex: 1,
    backgroundColor: 'white',
    borderRadius: 20,
    margin: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    elevation: 8,
    overflow: 'hidden',
  },
  nonScrollableTabContent: {
    flex: 1,
    backgroundColor: 'white',
    borderRadius: 20,
    margin: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    elevation: 8,
    overflow: 'hidden',
  },
  comingSoon: {
    textAlign: 'center',
    fontSize: 18,
    color: '#666',
    marginTop: 50,
    fontWeight: '600',
  },
  mobileHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#ff6f00',
    paddingHorizontal: 15,
    paddingVertical: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 8,
  },

  hamburgerButton: {
    padding: 8,
    minWidth: 44,
    minHeight: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  dropdownMenu: {
    position: 'absolute',
    top: 60,
    left: 10,
    backgroundColor: 'white',
    borderWidth: 2,
    borderColor: '#e91e63',
    borderRadius: 15,
    minWidth: 180,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.2,
    shadowRadius: 20,
    elevation: 1000,
    zIndex: 99999,
  },
  menuItem: {
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  menuItemText: {
    fontSize: 16,
    color: '#333',
    fontWeight: '600',
  },
  menuDivider: {
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
    backgroundColor: 'rgba(233, 30, 99, 0.05)',
  },
  profileText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
  },
  logoutMenuItem: {
    borderBottomWidth: 0,
  },
  logoutMenuText: {
    fontSize: 16,
    color: '#dc3545',
    fontWeight: '700',
  },
  hamburgerIcon: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  appTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
  },
  chartInfo: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  logoutButton: {
    backgroundColor: 'rgba(255,255,255,0.3)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 4,
  },
  logoutButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'transparent',
    zIndex: 998,
  },
  bottomNavigation: {
    flexDirection: 'row',
    backgroundColor: 'white',
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 70,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    zIndex: 1000,
  },
  bottomNavTab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    position: 'relative',
  },
  bottomNavIcon: {
    fontSize: 16,
    marginBottom: 4,
  },
  bottomNavText: {
    fontSize: 10,
    color: '#666',
    fontWeight: '600',
  },
  activeBottomNavText: {
    color: '#e91e63',
    fontWeight: '700',
  },
  bottomNavIndicator: {
    position: 'absolute',
    top: 0,
    left: 16,
    right: 16,
    height: 3,
    backgroundColor: '#e91e63',
    borderRadius: 2,
  },
});