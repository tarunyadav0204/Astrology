import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';

import { COLORS } from '../../utils/constants';
import { storage } from '../../services/storage';
import { chartAPI } from '../../services/api';
import ChartWidget from './ChartWidget';
import CascadingDashaBrowser from '../Dasha/CascadingDashaBrowser';

export default function ChartScreen({ visible, onClose }) {
  const [birthData, setBirthData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDashaBrowser, setShowDashaBrowser] = useState(false);
  const chartWidgetRef = useRef(null);

  useEffect(() => {
    if (visible) {
      loadBirthData();
    }
  }, [visible]);

  const loadBirthData = async () => {
    try {
      setLoading(true);
      
      // Always use current birth data from storage (most up-to-date)
      const data = await storage.getBirthDetails();
      console.log('ChartScreen - Birth data from storage:', data);
      if (data && data.name) {
        setBirthData(data);
        await calculateChart(data);
      } else {
        console.log('ChartScreen - No valid birth data found');
      }
    } catch (error) {
      console.error('ChartScreen - Error loading birth data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateChart = async (data) => {
    try {
      console.log('ChartScreen - Calculating chart for:', data);
      
      // Format data properly for API
      const formattedData = {
        ...data,
        date: typeof data.date === 'string' ? data.date.split('T')[0] : data.date,
        time: typeof data.time === 'string' ? data.time.split('T')[1]?.slice(0, 5) || data.time : data.time,
        latitude: parseFloat(data.latitude),
        longitude: parseFloat(data.longitude),
        timezone: data.timezone || 'Asia/Kolkata'
      };
      
      console.log('ChartScreen - Formatted data:', formattedData);
      const response = await chartAPI.calculateChartOnly(formattedData);
      const chartResult = response.data;
      console.log('ChartScreen - Chart calculated successfully');
      
      setChartData(chartResult);
    } catch (error) {
      console.error('ChartScreen - Error calculating chart:', error);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <StatusBar barStyle="light-content" backgroundColor="#ff6f00" translucent={false} />
      <LinearGradient colors={[COLORS.gradientStart, COLORS.gradientEnd]} style={styles.container}>
        <LinearGradient 
          colors={['#FF6B35', '#FF8A65', '#FFAB91']} 
          style={styles.header}
          start={{x: 0, y: 0}} 
          end={{x: 1, y: 1}}
        >
          <View style={styles.headerContent}>
            <Text style={styles.headerTitle}>✨ Vedic Charts</Text>
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>
        </LinearGradient>

        {loading ? (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Loading Chart...</Text>
          </View>
        ) : chartData && birthData ? (
          <ScrollView style={styles.chartContainer}>
            <ChartWidget 
              ref={chartWidgetRef}
              chartData={chartData}
              birthData={birthData}
              defaultStyle="north"
            />
            
            {birthData && (
              <View style={styles.chartInfo}>
                <Text style={styles.chartTitle}>{birthData.name}</Text>
                <Text style={styles.chartDetails}>
                  {birthData.date} at {birthData.time}
                </Text>
                <Text style={styles.chartDetails}>{birthData.place}</Text>
                
                <View style={styles.buttonRow}>
                  <TouchableOpacity 
                    style={styles.actionButton}
                    onPress={() => setShowDashaBrowser(true)}
                  >
                    <Text style={styles.actionButtonText}>⏰ Dashas</Text>
                  </TouchableOpacity>
                  
                  <TouchableOpacity 
                    style={styles.actionButton}
                    onPress={() => chartWidgetRef.current?.navigateToTransit()}
                  >
                    <Text style={styles.actionButtonText}>🪐 Transit</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </ScrollView>
        ) : (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>No birth data available</Text>
          </View>
        )}
      </LinearGradient>
      
      <CascadingDashaBrowser 
        visible={showDashaBrowser} 
        onClose={() => setShowDashaBrowser(false)}
        birthData={birthData}
      />
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 15,
    paddingBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: 50,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.white,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  closeButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 20,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  closeButtonText: {
    fontSize: 18,
    color: COLORS.white,
    fontWeight: 'bold',
  },
  chartContainer: {
    flex: 1,
    paddingVertical: 20,
  },
  chartInfo: {
    marginTop: 20,
    paddingVertical: 15,
    paddingHorizontal: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 10,
    alignItems: 'center',
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.primary,
    marginBottom: 5,
  },
  chartDetails: {
    fontSize: 14,
    color: COLORS.gray,
    marginBottom: 2,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: COLORS.textPrimary,
    fontSize: 16,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
    marginTop: 15,
  },
  actionButton: {
    backgroundColor: COLORS.accent,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 25,
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 4,
    flex: 1,
    maxWidth: 160,
  },
  actionButtonText: {
    color: COLORS.white,
    fontSize: 15,
    fontWeight: '600',
    textAlign: 'center',
  },
});