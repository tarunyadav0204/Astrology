import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { GestureHandlerRootView, PanGestureHandler } from 'react-native-gesture-handler';
import { chartAPI } from '../../services/api';

import { COLORS } from '../../utils/constants';
import NorthIndianChart from './NorthIndianChart';
import SouthIndianChart from './SouthIndianChart';

const ChartWidget = ({ title, chartType, chartData, birthData, defaultStyle = 'north' }) => {
  const [chartStyle, setChartStyle] = useState(defaultStyle);
  const [showDegreeNakshatra, setShowDegreeNakshatra] = useState(true);
  const [currentChartType, setCurrentChartType] = useState(chartType || 'lagna');
  const [currentChartData, setCurrentChartData] = useState(chartData);
  const [loading, setLoading] = useState(false);
  
  const chartTypes = ['lagna', 'navamsa', 'transit'];
  const chartTitles = {
    lagna: 'Birth Chart (Lagna)',
    navamsa: 'Navamsa Chart (D9)',
    transit: 'Transit Chart'
  };

  const toggleStyle = () => {
    setChartStyle(prev => prev === 'north' ? 'south' : 'north');
  };

  useEffect(() => {
    loadChartData(currentChartType);
  }, [currentChartType]);

  const loadChartData = async (type) => {
    if (type === 'lagna') {
      setCurrentChartData(chartData);
      return;
    }
    
    if (!birthData) return;
    
    try {
      setLoading(true);
      const formattedData = {
        ...birthData,
        date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
        time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'Asia/Kolkata'
      };
      
      let response;
      if (type === 'navamsa') {
        response = await chartAPI.calculateNavamsa(formattedData);
      } else if (type === 'transit') {
        response = await chartAPI.calculateTransit(formattedData);
      }
      
      if (response) {
        setCurrentChartData(response.data);
      }
    } catch (error) {
      console.error(`Error loading ${type} chart:`, error);
    } finally {
      setLoading(false);
    }
  };

  const onSwipeGesture = (event) => {
    const { translationX } = event.nativeEvent;
    
    if (Math.abs(translationX) > 50) {
      const currentIndex = chartTypes.indexOf(currentChartType);
      let newIndex;
      
      if (translationX > 0) {
        // Swipe right - previous chart
        newIndex = currentIndex > 0 ? currentIndex - 1 : chartTypes.length - 1;
      } else {
        // Swipe left - next chart
        newIndex = currentIndex < chartTypes.length - 1 ? currentIndex + 1 : 0;
      }
      
      setCurrentChartType(chartTypes[newIndex]);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{chartTitles[currentChartType] || title}</Text>
        <View style={styles.controls}>
          <TouchableOpacity
            onPress={() => setShowDegreeNakshatra(!showDegreeNakshatra)}
            style={[
              styles.controlButton,
              showDegreeNakshatra && styles.controlButtonActive
            ]}
          >
            <Text style={[
              styles.controlButtonText,
              showDegreeNakshatra && styles.controlButtonTextActive
            ]}>
              {showDegreeNakshatra ? 'Hide' : 'Show'}
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            onPress={toggleStyle}
            style={styles.styleToggle}
          >
            <Text style={styles.styleToggleText}>
              {chartStyle === 'north' ? 'N' : 'S'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
      
      <GestureHandlerRootView style={styles.chartContainer}>
        <PanGestureHandler onGestureEvent={onSwipeGesture}>
          <View style={styles.chartWrapper}>
            {loading ? (
              <View style={styles.loadingContainer}>
                <Text style={styles.loadingText}>Loading {chartTitles[currentChartType]}...</Text>
              </View>
            ) : currentChartData ? (
              chartStyle === 'north' ? (
                <NorthIndianChart 
                  chartData={currentChartData}
                  chartType={currentChartType}
                  birthData={birthData}
                  showDegreeNakshatra={showDegreeNakshatra}
                />
              ) : (
                <SouthIndianChart 
                  chartData={currentChartData}
                  chartType={currentChartType}
                  birthData={birthData}
                  showDegreeNakshatra={showDegreeNakshatra}
                />
              )
            ) : (
              <View style={styles.loadingContainer}>
                <Text style={styles.loadingText}>No chart data available</Text>
              </View>
            )}
          </View>
        </PanGestureHandler>
      </GestureHandlerRootView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 15,
    marginBottom: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  controlButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
    backgroundColor: COLORS.lightGray,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  controlButtonActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  controlButtonText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
  },
  controlButtonTextActive: {
    color: COLORS.white,
  },
  styleToggle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  styleToggleText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: 'bold',
  },
  chartContainer: {
    width: '100%',
    aspectRatio: 1,
  },
  chartWrapper: {
    flex: 1,
    width: '100%',
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
});

export default ChartWidget;