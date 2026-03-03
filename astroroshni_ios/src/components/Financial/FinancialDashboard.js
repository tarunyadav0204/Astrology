import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../../utils/constants';

const SECTOR_ICONS = {
  'Banking & Finance': 'cash',
  'Technology & AI': 'hardware-chip',
  'Real Estate & Infrastructure': 'business',
  'Pharma & Healthcare': 'medical',
  'Auto & Luxury': 'car-sport',
  'Metals & Heavy Industry': 'construct',
  'Energy & Oil': 'flash',
  'FMCG & Consumer': 'cart',
  'Gold': 'diamond',
  'Silver': 'moon',
  'Copper': 'layers',
  'Iron & Steel': 'hammer'
};

const SectorCard = ({ sector, ruler, trend, intensity, onPress }) => {
  const getTrendColor = () => {
    if (trend === 'BULLISH') return ['#dcfce7', '#bbf7d0'];
    if (trend === 'BEARISH') return ['#fecaca', '#fca5a5'];
    return ['#fef3c7', '#fde68a'];
  };

  const getIconColor = () => {
    if (trend === 'BULLISH') return '#16a34a';
    if (trend === 'BEARISH') return '#dc2626';
    return '#d97706';
  };

  const getTrendIcon = () => {
    if (trend === 'BULLISH') return 'trending-up';
    if (trend === 'BEARISH') return 'trending-down';
    return 'remove';
  };

  return (
    <TouchableOpacity onPress={onPress} style={styles.sectorCard}>
      <LinearGradient colors={getTrendColor()} style={styles.sectorGradient}>
        <View style={styles.sectorHeader}>
          <Ionicons name={SECTOR_ICONS[sector] || 'briefcase'} size={24} color={getIconColor()} />
          <Ionicons name={getTrendIcon()} size={20} color={getIconColor()} />
        </View>
        <Text style={[styles.sectorName, { color: '#1f2937' }]}>{sector}</Text>
        <Text style={[styles.sectorRuler, { color: '#4b5563' }]}>♃ {ruler}</Text>
        <View style={styles.trendBadge}>
          <Text style={[styles.trendText, { color: '#1f2937' }]}>{trend}</Text>
          <Text style={[styles.intensityText, { color: '#6b7280' }]}>{intensity}</Text>
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );
};

const HotOpportunityCard = ({ opportunity, onPress }) => (
  <TouchableOpacity onPress={onPress} style={styles.hotCard}>
    <View style={styles.hotHeader}>
      <Ionicons name="flame" size={20} color="#ef4444" />
      <Text style={styles.hotSector}>{opportunity.sector}</Text>
    </View>
    <Text style={styles.hotDates}>
      {opportunity.start_date} → {opportunity.end_date}
    </Text>
    <Text style={styles.hotReason} numberOfLines={2}>{opportunity.reason}</Text>
    <View style={styles.hotFooter}>
      <Text style={styles.hotDuration}>{opportunity.duration_days} days</Text>
      <Ionicons name="arrow-forward" size={16} color="#6366f1" />
    </View>
  </TouchableOpacity>
);

export default function FinancialDashboard({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [currentTrends, setCurrentTrends] = useState({});
  const [hotOpportunities, setHotOpportunities] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [startYear, setStartYear] = useState(new Date().getFullYear());
  const [endYear, setEndYear] = useState(new Date().getFullYear() + 5);
  const [showYearPicker, setShowYearPicker] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      
      // Fetch metadata first to get the forecast period
      const allRes = await fetch(`${API_BASE_URL}/api/financial/forecast/all`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const allData = await allRes.json();
      console.log('Metadata:', allData);
      setMetadata({ period: allData.period, generated_at: allData.generated_at });

      // Extract start year from period and use Jan 1 of that year for current trends
      const startYear = allData.period?.split(' - ')[0] || new Date().getFullYear();
      const forecastDate = `${startYear}-01-01`;
      console.log('Using forecast date:', forecastDate);
      
      // Fetch current trends using the forecast start date
      const trendsRes = await fetch(`${API_BASE_URL}/api/financial/current-trends?date=${forecastDate}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const trendsData = await trendsRes.json();
      console.log('Current Trends Response:', trendsData);
      console.log('Trends keys:', Object.keys(trendsData.trends || {}));
      setCurrentTrends(trendsData.trends || {});

      // Fetch hot opportunities
      const hotRes = await fetch(`${API_BASE_URL}/api/financial/hot-opportunities?intensity=High`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const hotData = await hotRes.json();
      console.log('Hot Opportunities:', hotData.opportunities?.length || 0);
      setHotOpportunities(hotData.opportunities.slice(0, 5));

    } catch (error) {
      console.error('Error fetching financial data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <LinearGradient colors={['#0f0c29', '#302b63']} style={styles.bg}>
          <SafeAreaView style={styles.safeArea}>
            <ActivityIndicator size="large" color="#10b981" />
            <Text style={styles.loadingText}>Loading Market Insights...</Text>
          </SafeAreaView>
        </LinearGradient>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#0f0c29', '#302b63', '#24243e']} style={styles.bg}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Ionicons name="arrow-back" size={24} color="#fff" />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Market Astrology</Text>
            <TouchableOpacity onPress={fetchData}>
              <Ionicons name="refresh" size={24} color="#fff" />
            </TouchableOpacity>
          </View>

          <ScrollView showsVerticalScrollIndicator={false}>
            {/* Hero Section */}
            <View style={styles.heroSection}>
              <Text style={styles.heroTitle}>📈 Vedic Market Insights</Text>
              <TouchableOpacity 
                style={styles.yearSelector}
                onPress={() => setShowYearPicker(true)}
              >
                <Text style={styles.heroSubtitle}>
                  {metadata?.period || `${startYear}-${endYear}`}
                </Text>
                <Ionicons name="chevron-down" size={20} color="#10b981" />
              </TouchableOpacity>
              <Text style={styles.heroDate}>
                Updated: {metadata?.generated_at ? new Date(metadata.generated_at).toLocaleDateString() : 'Today'}
              </Text>
            </View>

            {/* Hot Opportunities */}
            {hotOpportunities.length > 0 && (
              <View style={styles.section}>
                <View style={styles.sectionHeader}>
                  <Ionicons name="flame" size={20} color="#ef4444" />
                  <Text style={styles.sectionTitle}>Hot Opportunities</Text>
                </View>
                <ScrollView 
                  horizontal 
                  showsHorizontalScrollIndicator={false} 
                  contentContainerStyle={styles.hotScroll}
                >
                  {hotOpportunities.map((opp, idx) => (
                    <HotOpportunityCard
                      key={idx}
                      opportunity={opp}
                      onPress={() => navigation.navigate('SectorDetail', { sector: opp.sector })}
                    />
                  ))}
                </ScrollView>
              </View>
            )}

            {/* All Sectors Grid */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>All Sectors</Text>
              {Object.keys(currentTrends).length === 0 ? (
                <View style={styles.emptyState}>
                  <Ionicons name="analytics-outline" size={48} color="#666" />
                  <Text style={styles.emptyText}>No forecast data available</Text>
                  <Text style={styles.emptySubtext}>Tap the year selector above to generate forecast</Text>
                </View>
              ) : (
                <View style={styles.sectorsGrid}>
                  {Object.entries(currentTrends).map(([sector, data]) => (
                    <SectorCard
                      key={sector}
                      sector={sector}
                      ruler={data.ruler || 'Unknown'}
                      trend={data.trend}
                      intensity={data.intensity}
                      onPress={() => navigation.navigate('SectorDetail', { sector })}
                    />
                  ))}
                </View>
              )}
            </View>

            {/* View All Button */}
            <TouchableOpacity
              style={styles.viewAllButton}
              onPress={() => navigation.navigate('AllOpportunities')}
            >
              <Text style={styles.viewAllText}>View All Opportunities</Text>
              <Ionicons name="arrow-forward" size={20} color="#fff" />
            </TouchableOpacity>

          </ScrollView>

          {/* Year Picker Modal */}
          {showYearPicker && (
            <View style={styles.modalOverlay}>
              <View style={styles.yearPickerModal}>
                <Text style={styles.modalTitle}>Select Year Range</Text>
                
                <View style={styles.yearRangeContainer}>
                  <View style={styles.yearColumn}>
                    <Text style={styles.columnLabel}>Start Year</Text>
                    <ScrollView style={styles.yearList}>
                      {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() + i).map(year => (
                        <TouchableOpacity
                          key={year}
                          style={[styles.yearOption, year === startYear && styles.yearOptionSelected]}
                          onPress={() => {
                            setStartYear(year);
                            if (year > endYear) {
                              setEndYear(year);
                            }
                          }}
                        >
                          <Text style={[styles.yearText, year === startYear && styles.yearTextSelected]}>
                            {year}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </ScrollView>
                  </View>
                  
                  <View style={styles.yearColumn}>
                    <Text style={styles.columnLabel}>End Year</Text>
                    <ScrollView style={styles.yearList}>
                      {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() + i).map(year => (
                        <TouchableOpacity
                          key={year}
                          style={[
                            styles.yearOption, 
                            year === endYear && styles.yearOptionSelected,
                            year < startYear && styles.yearOptionDisabled
                          ]}
                          disabled={year < startYear}
                          onPress={() => setEndYear(year)}
                        >
                          <Text style={[
                            styles.yearText, 
                            year === endYear && styles.yearTextSelected,
                            year < startYear && styles.yearTextDisabled
                          ]}>
                            {year}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </ScrollView>
                  </View>
                </View>
                
                {startYear > endYear && (
                  <Text style={styles.errorText}>Start year cannot be greater than end year</Text>
                )}
                
                <View style={styles.buttonRow}>
                  <TouchableOpacity
                    style={[styles.actionButton, styles.cancelButton]}
                    onPress={() => setShowYearPicker(false)}
                  >
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.actionButton, styles.generateButton, startYear > endYear && styles.buttonDisabled]}
                    disabled={startYear > endYear}
                    onPress={async () => {
                      setShowYearPicker(false);
                      setLoading(true);
                      try {
                        const token = await AsyncStorage.getItem('authToken');
                        const response = await fetch(
                          `${API_BASE_URL}/api/financial/admin/regenerate?start_year=${startYear}&end_year=${endYear}`,
                          {
                            method: 'POST',
                            headers: { 'Authorization': `Bearer ${token}` }
                          }
                        );
                        
                        if (!response.ok) {
                          const error = await response.json();
                          Alert.alert('Error', error.detail || 'Failed to generate forecast');
                        } else {
                          const result = await response.json();
                          // Update metadata immediately with generated period
                          setMetadata({ 
                            period: `${result.start_year} - ${result.end_year}`,
                            generated_at: new Date().toISOString()
                          });
                          await fetchData();
                        }
                      } catch (error) {
                        console.error('Error regenerating forecast:', error);
                        Alert.alert('Error', 'Failed to generate forecast');
                      } finally {
                        setLoading(false);
                      }
                    }}
                  >
                    <Text style={styles.generateButtonText}>Generate</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          )}

        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  bg: { flex: 1, width: '100%', height: '100%' },
  safeArea: { flex: 1 },
  centerContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { color: '#fff', marginTop: 16, fontSize: 16 },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
  },
  headerTitle: { color: '#fff', fontSize: 20, fontWeight: 'bold' },

  heroSection: {
    alignItems: 'center',
    paddingVertical: 20,
    paddingHorizontal: 20,
  },
  heroTitle: { color: '#fff', fontSize: 24, fontWeight: 'bold', marginBottom: 8 },
  yearSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  heroSubtitle: { color: '#10b981', fontSize: 16, fontWeight: '600' },
  heroDate: { color: '#888', fontSize: 12, marginTop: 4 },

  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  yearPickerModal: {
    backgroundColor: '#1a1a2e',
    borderRadius: 16,
    padding: 20,
    width: '90%',
    maxHeight: '70%',
  },
  modalTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center',
  },
  yearRangeContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  yearColumn: {
    flex: 1,
  },
  columnLabel: {
    color: '#10b981',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  yearList: {
    maxHeight: 250,
  },
  yearOption: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 6,
    backgroundColor: 'rgba(255,255,255,0.05)',
  },
  yearOptionSelected: {
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    borderWidth: 1,
    borderColor: '#10b981',
  },
  yearOptionDisabled: {
    opacity: 0.3,
  },
  yearText: {
    color: '#fff',
    fontSize: 14,
    textAlign: 'center',
  },
  yearTextSelected: {
    color: '#10b981',
    fontWeight: 'bold',
  },
  yearTextDisabled: {
    color: '#666',
  },
  errorText: {
    color: '#ef4444',
    fontSize: 12,
    textAlign: 'center',
    marginBottom: 12,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#666',
  },
  cancelButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  generateButton: {
    backgroundColor: '#10b981',
  },
  generateButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  buttonDisabled: {
    opacity: 0.5,
  },

  section: { marginBottom: 24 },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    paddingHorizontal: 20,
    marginBottom: 12,
  },

  hotScroll: { paddingLeft: 20, paddingRight: 20 },
  hotCard: {
    width: 280,
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.3)',
    marginRight: 12,
  },
  hotHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  hotSector: { color: '#fff', fontSize: 16, fontWeight: 'bold', flex: 1 },
  hotDates: { color: '#10b981', fontSize: 14, marginBottom: 8 },
  hotReason: { color: '#ccc', fontSize: 13, lineHeight: 18, marginBottom: 12 },
  hotFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  hotDuration: { color: '#888', fontSize: 12 },

  sectorsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 12,
    gap: 12,
  },
  sectorCard: {
    width: '47%',
    borderRadius: 16,
    overflow: 'hidden',
  },
  sectorGradient: {
    padding: 16,
    minHeight: 140,
  },
  sectorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  sectorName: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  sectorRuler: { color: 'rgba(255,255,255,0.8)', fontSize: 12, marginBottom: 8 },
  trendBadge: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 8,
    padding: 6,
    marginTop: 'auto',
  },
  trendText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  intensityText: { color: 'rgba(255,255,255,0.8)', fontSize: 10 },

  viewAllButton: {
    marginHorizontal: 20,
    marginBottom: 30,
    backgroundColor: '#6366f1',
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  viewAllText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },

  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
    paddingHorizontal: 20,
  },
  emptyText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 16,
    textAlign: 'center',
  },
  emptySubtext: {
    color: '#888',
    fontSize: 14,
    marginTop: 8,
    textAlign: 'center',
  },
});
