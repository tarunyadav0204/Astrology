import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Modal } from 'react-native';
import { apiService } from '../services/apiService';

export default function AshtakavargaModal({ visible, onClose, birthData, chartType }) {
  const [ashtakavargaData, setAshtakavargaData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('sarva');

  const signNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

  useEffect(() => {
    if (visible && birthData) {
      fetchAshtakavarga();
    }
  }, [visible, birthData, chartType]);

  const fetchAshtakavarga = async () => {
    setLoading(true);
    try {
      const response = await apiService.calculateAshtakavarga({
        birth_data: birthData,
        chart_type: chartType
      });
      setAshtakavargaData(response);
    } catch (error) {
      console.error('Error fetching Ashtakavarga:', error);
      setAshtakavargaData(null);
    } finally {
      setLoading(false);
    }
  };

  const getTabsForChartType = () => {
    const baseTabs = [
      { id: 'sarva', label: 'Sarvashtakavarga' },
      { id: 'individual', label: 'Individual Charts' }
    ];

    if (chartType === 'lagna') {
      return [...baseTabs, { id: 'analysis', label: 'Life Analysis' }];
    } else if (chartType === 'navamsa') {
      return [...baseTabs, { id: 'analysis', label: 'Marriage Analysis' }];
    } else if (chartType === 'transit') {
      return [...baseTabs, { id: 'analysis', label: 'Timing Analysis' }];
    }
    
    return [...baseTabs, { id: 'analysis', label: 'General Analysis' }];
  };

  const renderSarvashtakavarga = () => {
    if (!ashtakavargaData) return null;

    const { sarvashtakavarga, total_bindus } = ashtakavargaData.ashtakavarga;

    return (
      <View style={styles.sarvaChart}>
        <Text style={styles.sectionTitle}>Sarvashtakavarga ({total_bindus} total bindus)</Text>
        <View style={styles.binduGrid}>
          {signNames.map((sign, index) => {
            const bindus = sarvashtakavarga[index];
            let cellStyle = styles.binduCell;
            if (bindus >= 30) cellStyle = [styles.binduCell, styles.strongCell];
            else if (bindus <= 25) cellStyle = [styles.binduCell, styles.weakCell];
            else cellStyle = [styles.binduCell, styles.averageCell];

            return (
              <View key={index} style={cellStyle}>
                <Text style={styles.signName}>{sign}</Text>
                <Text style={styles.binduCount}>{bindus}</Text>
              </View>
            );
          })}
        </View>
      </View>
    );
  };

  const renderIndividualCharts = () => {
    if (!ashtakavargaData) return null;

    const { individual_charts } = ashtakavargaData.ashtakavarga;

    return (
      <ScrollView style={styles.individualCharts}>
        <Text style={styles.sectionTitle}>Individual Planet Charts</Text>
        {Object.entries(individual_charts).map(([planet, data]) => (
          <View key={planet} style={styles.planetChart}>
            <Text style={styles.planetTitle}>{planet} ({data.total} bindus)</Text>
            <View style={styles.binduRow}>
              {signNames.map((sign, index) => {
                const count = data.bindus[index];
                let cellStyle = styles.miniBindu;
                if (count >= 4) cellStyle = [styles.miniBindu, styles.highBindu];
                else if (count >= 2) cellStyle = [styles.miniBindu, styles.mediumBindu];
                else cellStyle = [styles.miniBindu, styles.lowBindu];
                
                return (
                  <View key={index} style={cellStyle}>
                    <Text style={styles.miniSign}>{sign.slice(0, 3)}</Text>
                    <Text style={styles.miniCount}>{count}</Text>
                  </View>
                );
              })}
            </View>
          </View>
        ))}
      </ScrollView>
    );
  };

  const renderAnalysis = () => {
    if (!ashtakavargaData) return null;

    const { analysis } = ashtakavargaData;

    return (
      <ScrollView style={styles.analysisContent} showsVerticalScrollIndicator={false}>
        {/* Header Section */}
        <View style={styles.analysisHeader}>
          <Text style={styles.analysisTitle}>🔮 Life Analysis</Text>
          <Text style={styles.analysisSubtitle}>Based on Ashtakavarga Calculations</Text>
        </View>

        {/* Strength Analysis Cards */}
        {analysis.strongest_sign && (
          <View style={styles.strengthCards}>
            <View style={styles.strengthCard}>
              <View style={styles.cardIcon}>
                <Text style={styles.iconText}>💪</Text>
              </View>
              <View style={styles.cardContent}>
                <Text style={styles.cardTitle}>Strongest Sign</Text>
                <Text style={styles.cardValue}>{analysis.strongest_sign.name}</Text>
                <Text style={styles.cardBindus}>{analysis.strongest_sign.bindus} bindus</Text>
              </View>
              <View style={styles.strengthIndicator}>
                <View style={[styles.strengthBar, styles.strongBar]} />
              </View>
            </View>
            
            <View style={styles.strengthCard}>
              <View style={styles.cardIcon}>
                <Text style={styles.iconText}>⚠️</Text>
              </View>
              <View style={styles.cardContent}>
                <Text style={styles.cardTitle}>Weakest Sign</Text>
                <Text style={styles.cardValue}>{analysis.weakest_sign.name}</Text>
                <Text style={styles.cardBindus}>{analysis.weakest_sign.bindus} bindus</Text>
              </View>
              <View style={styles.strengthIndicator}>
                <View style={[styles.strengthBar, styles.weakBar]} />
              </View>
            </View>
          </View>
        )}
        
        {/* Focus Area Section */}
        {analysis.focus && (
          <View style={styles.focusSection}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionIcon}>🎯</Text>
              <Text style={styles.sectionTitleText}>Focus Area</Text>
            </View>
            <View style={styles.focusCard}>
              <Text style={styles.focusTitle}>{analysis.focus}</Text>
              <Text style={styles.focusDescription}>{analysis.analysis}</Text>
            </View>
          </View>
        )}

        {/* Recommendations Section */}
        {analysis.recommendations && (
          <View style={styles.recommendationsSection}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionIcon}>💡</Text>
              <Text style={styles.sectionTitleText}>Recommendations</Text>
            </View>
            <View style={styles.recommendationsGrid}>
              {analysis.recommendations.map((rec, index) => (
                <View key={index} style={styles.recommendationCard}>
                  <View style={styles.recommendationNumber}>
                    <Text style={styles.recommendationNumberText}>{index + 1}</Text>
                  </View>
                  <Text style={styles.recommendationText}>{rec}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Life Insights Section */}
        <View style={styles.insightsSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionIcon}>✨</Text>
            <Text style={styles.sectionTitleText}>Life Insights</Text>
          </View>
          <View style={styles.insightCard}>
            <Text style={styles.insightText}>
              Your Ashtakavarga reveals the cosmic blueprint of your life's journey. 
              The distribution of bindus across signs indicates periods of strength and challenge, 
              guiding you toward optimal timing for important decisions.
            </Text>
          </View>
        </View>

        <View style={styles.bottomPadding} />
      </ScrollView>
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>
            Ashtakavarga Analysis - {chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart
          </Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Text style={styles.closeButtonText}>×</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.tabContainer}>
          {getTabsForChartType().map(tab => (
            <TouchableOpacity
              key={tab.id}
              style={[styles.tab, activeTab === tab.id && styles.activeTab]}
              onPress={() => setActiveTab(tab.id)}
            >
              <Text style={[styles.tabText, activeTab === tab.id && styles.activeTabText]}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.modalContent}>
          {loading ? (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>Calculating Ashtakavarga...</Text>
            </View>
          ) : !ashtakavargaData ? (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>Failed to load Ashtakavarga data. Please try again.</Text>
            </View>
          ) : (
            <>
              {activeTab === 'sarva' && renderSarvashtakavarga()}
              {activeTab === 'individual' && renderIndividualCharts()}
              {activeTab === 'analysis' && renderAnalysis()}
            </>
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalContainer: {
    flex: 1,
    backgroundColor: 'white',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e91e63',
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#e91e63',
    flex: 1,
  },
  closeButton: {
    padding: 8,
    backgroundColor: '#e91e63',
    borderRadius: 4,
  },
  closeButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  tabContainer: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#e91e63',
  },
  tabText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#e91e63',
    fontWeight: '600',
  },
  modalContent: {
    flex: 1,
    padding: 16,
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorText: {
    fontSize: 16,
    color: '#e91e63',
    textAlign: 'center',
  },
  sarvaChart: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 16,
    textAlign: 'center',
  },
  binduGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  binduCell: {
    width: '23%',
    aspectRatio: 1,
    marginBottom: 8,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  strongCell: {
    backgroundColor: '#d1fae5',
    borderColor: '#10b981',
  },
  averageCell: {
    backgroundColor: '#fef3c7',
    borderColor: '#f59e0b',
  },
  weakCell: {
    backgroundColor: '#fee2e2',
    borderColor: '#ef4444',
  },
  signName: {
    fontSize: 10,
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
  },
  binduCount: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 4,
  },
  individualCharts: {
    flex: 1,
  },
  planetChart: {
    marginBottom: 16,
  },
  planetTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  binduRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
  },
  miniBindu: {
    width: '15%',
    aspectRatio: 1,
    borderRadius: 4,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  highBindu: {
    backgroundColor: '#d1fae5',
    borderColor: '#10b981',
  },
  mediumBindu: {
    backgroundColor: '#fef3c7',
    borderColor: '#f59e0b',
  },
  lowBindu: {
    backgroundColor: '#fee2e2',
    borderColor: '#ef4444',
  },
  miniSign: {
    fontSize: 8,
    fontWeight: '600',
    color: '#333',
  },
  miniCount: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#333',
  },
  analysisContent: {
    flex: 1,
  },
  analysisHeader: {
    alignItems: 'center',
    marginBottom: 24,
    paddingVertical: 16,
    backgroundColor: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    borderRadius: 16,
    backgroundColor: '#f8f9ff',
  },
  analysisTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#4c51bf',
    marginBottom: 4,
  },
  analysisSubtitle: {
    fontSize: 12,
    color: '#6b7280',
    fontStyle: 'italic',
  },
  strengthCards: {
    marginBottom: 24,
  },
  strengthCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
    borderLeftWidth: 4,
    borderLeftColor: '#e91e63',
  },
  cardIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  iconText: {
    fontSize: 20,
  },
  cardContent: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  cardValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 2,
  },
  cardBindus: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 2,
  },
  strengthIndicator: {
    width: 4,
    height: 40,
    borderRadius: 2,
    overflow: 'hidden',
  },
  strengthBar: {
    flex: 1,
    borderRadius: 2,
  },
  strongBar: {
    backgroundColor: '#10b981',
  },
  weakBar: {
    backgroundColor: '#ef4444',
  },
  focusSection: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  sectionTitleText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  focusCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
    borderLeftWidth: 4,
    borderLeftColor: '#f59e0b',
  },
  focusTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 8,
  },
  focusDescription: {
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 20,
  },
  recommendationsSection: {
    marginBottom: 24,
  },
  recommendationsGrid: {
    gap: 12,
  },
  recommendationCard: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
    borderLeftWidth: 4,
    borderLeftColor: '#8b5cf6',
  },
  recommendationNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#8b5cf6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    marginTop: 2,
  },
  recommendationNumberText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: 'white',
  },
  recommendationText: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  insightsSection: {
    marginBottom: 24,
  },
  insightCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  insightText: {
    fontSize: 14,
    color: '#4b5563',
    lineHeight: 22,
    textAlign: 'justify',
    fontStyle: 'italic',
  },
  bottomPadding: {
    height: 32,
  },
});