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
  const [birthData, setBirthData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (visible) {
      loadBirthData();
    }
  }, [visible]);

  const loadBirthData = async () => {
    try {
      setLoading(true);
      
      // First try to get fresh data from database
      try {
        const response = await chartAPI.getExistingCharts('');
        const charts = response.data.charts || [];
        if (charts.length > 0) {
          // Use the most recent chart from database
          const latestChart = charts[0];
          const freshData = {
            name: latestChart.name,
            date: latestChart.date,
            time: latestChart.time,
            latitude: latestChart.latitude,
            longitude: latestChart.longitude,
            timezone: latestChart.timezone,
            place: latestChart.place || '',
            gender: latestChart.gender || ''
          };
          setBirthData(freshData);
          await calculateChart(freshData);
          return;
        }
      } catch (dbError) {
      }
      
      // Fallback to local storage if database fetch fails
      const data = await storage.getBirthDetails();
      if (data) {
        setBirthData(data);
        await calculateChart(data);
      }
    } catch (error) {
      // Error loading birth data
    } finally {
      setLoading(false);
    }
  };

  const calculateChart = async (data) => {
    try {
      
      // Ensure proper date/time format
      let formattedDate = data.date;
      let formattedTime = data.time;
      
      // Fix date format
      if (typeof data.date === 'string' && data.date.includes('T')) {
        formattedDate = data.date.split('T')[0];
      }
      
      // Fix time format - extract HH:MM from various formats
      if (typeof data.time === 'string') {
        if (data.time.includes('T')) {
          // Extract time from datetime string like "1970-01-01T09:25:00.000Z"
          const timePart = data.time.split('T')[1];
          if (timePart) {
            formattedTime = timePart.slice(0, 5); // Get HH:MM
          }
        } else if (data.time.includes(':')) {
          // Already in HH:MM format
          formattedTime = data.time.slice(0, 5);
        }
      }
      
      const formattedData = {
        ...data,
        date: formattedDate,
        time: formattedTime,
        latitude: parseFloat(data.latitude),
        longitude: parseFloat(data.longitude),
        timezone: 'Asia/Kolkata' // Always use proper timezone
      };
      
      // Get auth token for authenticated request
      const token = await storage.getAuthToken();
      
      // Clear any cached chart data to ensure fresh calculation
      await storage.clearChartData();
      
      // Always calculate fresh chart data without saving to database
      const response = await chartAPI.calculateChartOnly(formattedData);
      
      const chartResult = response.data;
      
      // Store chart data for future use
      await storage.setChartData({
        birthData: formattedData,
        chartData: chartResult
      });
      
      setChartData(chartResult);
    } catch (error) {
      // Error calculating chart
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <LinearGradient colors={[COLORS.gradientStart, COLORS.gradientEnd]} style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Vedic Charts</Text>
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <Ionicons name="close" size={24} color={COLORS.accent} />
          </TouchableOpacity>
        </View>

        {loading ? (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Loading Chart...</Text>
          </View>
        ) : chartData && birthData ? (
          <ScrollView style={styles.chartContainer}>
            <ChartWidget 
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
    color: COLORS.textPrimary,
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
    color: COLORS.textPrimary,
    fontSize: 16,
  },
});