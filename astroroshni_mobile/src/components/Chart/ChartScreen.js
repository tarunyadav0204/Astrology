import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../../utils/constants';
import { storage } from '../../services/storage';
import { chartAPI } from '../../services/api';
import ChartWidget from './ChartWidget';

export default function ChartScreen({ visible, onClose }) {
  console.log('=== CHART SCREEN RENDER ===');
  console.log('visible:', visible);
  
  const [birthData, setBirthData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (visible) {
      loadBirthData();
    }
  }, [visible]);

  const loadBirthData = async () => {
    console.log('=== LOADING BIRTH DATA ===');
    try {
      setLoading(true);
      const data = await storage.getBirthDetails();
      console.log('Birth data loaded:', data);
      if (data) {
        setBirthData(data);
        await calculateChart(data);
      }
    } catch (error) {
      console.error('Error loading birth data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateChart = async (data) => {
    console.log('=== CALCULATING CHART ===');
    try {
      console.log('Birth data being sent:', JSON.stringify(data, null, 2));
      
      // Ensure proper date/time format
      const formattedData = {
        ...data,
        date: typeof data.date === 'string' ? data.date.split('T')[0] : data.date,
        time: typeof data.time === 'string' ? data.time.split('T')[1]?.slice(0, 5) || data.time : data.time,
        latitude: parseFloat(data.latitude),
        longitude: parseFloat(data.longitude),
        timezone: data.timezone || 'Asia/Kolkata'
      };
      
      console.log('Formatted data:', JSON.stringify(formattedData, null, 2));
      
      const response = await chartAPI.calculateChart(formattedData);
      console.log('=== CHART API RESPONSE ===');
      console.log('Chart response:', JSON.stringify(response.data, null, 2));
      setChartData(response.data);
    } catch (error) {
      console.error('=== CHART CALCULATION ERROR ===');
      console.error('Error calculating chart:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <LinearGradient colors={[COLORS.gradientStart, COLORS.gradientEnd]} style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Birth Chart</Text>
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <Ionicons name="close" size={24} color={COLORS.white} />
          </TouchableOpacity>
        </View>

        {loading ? (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Loading Chart...</Text>
          </View>
        ) : chartData && birthData ? (
          <ScrollView style={styles.chartContainer}>
            <ChartWidget 
              title="Lagna Chart"
              chartType="lagna"
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
              </View>
            )}
          </ScrollView>
        ) : (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>No birth data available</Text>
          </View>
        )}
      </LinearGradient>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    paddingTop: 50,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.white,
  },
  closeButton: {
    padding: 5,
  },
  chartContainer: {
    flex: 1,
    padding: 20,
  },
  chartInfo: {
    marginTop: 20,
    padding: 15,
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
    color: COLORS.white,
    fontSize: 16,
  },
});