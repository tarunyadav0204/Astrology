import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import NorthIndianChart from './NorthIndianChart';
import SouthIndianChart from './SouthIndianChart';
import AshtakavargaModal from './AshtakavargaModal';
import { apiService } from '../services/apiService';

export default function ChartWidget({ 
  title, 
  chartType, 
  chartData, 
  birthData, 
  defaultStyle = 'north',
  transitDate,
  division 
}) {
  const [chartStyle, setChartStyle] = useState(defaultStyle || 'north');
  const [showAshtakavarga, setShowAshtakavarga] = useState(false);
  const [divisionalData, setDivisionalData] = useState(null);
  const [transitChartData, setTransitChartData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (defaultStyle) {
      setChartStyle(defaultStyle);
    }
  }, [defaultStyle]);

  const toggleStyle = () => {
    setChartStyle(prev => prev === 'north' ? 'south' : 'north');
  };

  const handleAshtakavarga = () => {
    setShowAshtakavarga(true);
  };

  useEffect(() => {
    if ((chartType === 'navamsa' || chartType === 'divisional') && birthData && chartData) {
      setLoading(true);
      const divisionNum = chartType === 'navamsa' ? 9 : (division || 9);
      
      setTimeout(() => {
        setDivisionalData(chartData);
        setLoading(false);
      }, 500);
    }
  }, [chartType, birthData, division, chartData]);
  
  useEffect(() => {
    if (chartType === 'transit' && transitDate && birthData) {
      fetchTransitData();
    }
  }, [chartType, transitDate, birthData]);
  
  const fetchTransitData = async () => {
    try {
      setLoading(true);
      const transitData = await apiService.calculateTransits(
        birthData,
        transitDate.toISOString().split('T')[0]
      );
      setTransitChartData(transitData);
    } catch (error) {
      console.error('Error fetching transit data:', error);
      setTransitChartData(chartData); // Fallback to birth chart
    } finally {
      setLoading(false);
    }
  };

  const getChartData = () => {
    switch (chartType) {
      case 'lagna':
        return chartData;
      case 'navamsa':
      case 'divisional':
        return divisionalData || chartData;
      case 'transit':
        return transitChartData || chartData;
      default:
        return chartData;
    }
  };

  const processedData = getChartData();
  
  if (chartData && chartData.planets && !processedData?.planets?.Gulika && chartData.planets.Gulika) {
    processedData.planets = processedData.planets || {};
    processedData.planets.Gulika = chartData.planets.Gulika;
    processedData.planets.Mandi = chartData.planets.Mandi;
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{title}</Text>
        <View style={styles.controls}>
          <TouchableOpacity 
            onPress={handleAshtakavarga}
            style={styles.ashtakavargaButton}
          >
            <Text style={styles.ashtakavargaButtonText}>Ashtakavarga</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={toggleStyle} style={styles.styleToggle}>
            <Text style={styles.styleToggleText}>
              {chartStyle === 'north' ? 'N' : 'S'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
      
      <View style={styles.chartContainer}>
        {loading ? (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Calculating divisional chart...</Text>
          </View>
        ) : !divisionalData && (chartType === 'navamsa' || chartType === 'divisional') ? (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>Failed to load divisional chart</Text>
          </View>
        ) : (
          chartStyle === 'north' ? (
            <NorthIndianChart 
              chartData={processedData}
              chartType={chartType}
              birthData={birthData}
            />
          ) : (
            <SouthIndianChart 
              chartData={processedData}
              chartType={chartType}
              birthData={birthData}
            />
          )
        )}
      </View>
      
      <AshtakavargaModal
        visible={showAshtakavarga}
        onClose={() => setShowAshtakavarga(false)}
        birthData={birthData}
        chartType={chartType}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'white',
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  controls: {
    flexDirection: 'row',
    gap: 8,
  },
  ashtakavargaButton: {
    backgroundColor: '#e91e63',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  ashtakavargaButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  styleToggle: {
    backgroundColor: '#ff6f00',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    minWidth: 24,
    alignItems: 'center',
  },
  styleToggleText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  chartContainer: {
    flex: 1,
    paddingVertical: 2,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#666',
    fontSize: 14,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    color: '#e91e63',
    fontSize: 14,
  },
});