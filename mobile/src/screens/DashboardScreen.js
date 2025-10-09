import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import NorthIndianChart from '../components/NorthIndianChart';

export default function DashboardScreen({ route }) {
  const [birthData, setBirthData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (route.params?.birthData) {
      setBirthData(route.params.birthData);
      calculateChart(route.params.birthData);
    }
  }, [route.params]);

  const calculateChart = async (data) => {
    setLoading(true);
    try {
      // Mock chart data for now - replace with actual API call
      const mockChartData = {
        planets: {
          Sun: { house: 1, degree: 15.5, sign: 0 },
          Moon: { house: 4, degree: 22.3, sign: 3 },
          Mars: { house: 7, degree: 8.7, sign: 6 },
          Mercury: { house: 1, degree: 25.1, sign: 0 },
          Jupiter: { house: 10, degree: 12.9, sign: 9 },
          Venus: { house: 2, degree: 18.4, sign: 1 },
          Saturn: { house: 8, degree: 5.2, sign: 7 },
          Rahu: { house: 6, degree: 14.8, sign: 5 },
          Ketu: { house: 12, degree: 14.8, sign: 11 },
        }
      };
      setChartData(mockChartData);
    } catch (error) {
      Alert.alert('Error', 'Failed to calculate chart');
    } finally {
      setLoading(false);
    }
  };

  const handleHousePress = (houseNumber) => {
    Alert.alert(
      `House ${houseNumber}`,
      `Analysis for House ${houseNumber} will be shown here`,
      [{ text: 'OK' }]
    );
  };

  if (!birthData) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.errorText}>No birth data available</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.title}>Birth Chart</Text>
          <Text style={styles.subtitle}>{birthData.name}</Text>
          <Text style={styles.details}>
            {birthData.date} at {birthData.time}
          </Text>
          <Text style={styles.details}>{birthData.place}</Text>
        </View>

        {loading ? (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Calculating chart...</Text>
          </View>
        ) : (
          <NorthIndianChart 
            chartData={chartData} 
            onHousePress={handleHousePress}
          />
        )}

        <View style={styles.infoCards}>
          <View style={styles.infoCard}>
            <Text style={styles.cardTitle}>Lagna</Text>
            <Text style={styles.cardValue}>Aries</Text>
          </View>
          
          <View style={styles.infoCard}>
            <Text style={styles.cardTitle}>Rashi</Text>
            <Text style={styles.cardValue}>Cancer</Text>
          </View>
          
          <View style={styles.infoCard}>
            <Text style={styles.cardTitle}>Nakshatra</Text>
            <Text style={styles.cardValue}>Pushya</Text>
          </View>
        </View>

        <View style={styles.actionButtons}>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionButtonText}>View Navamsa</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionButtonText}>Dasha Periods</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionButtonText}>Transits</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollContent: {
    padding: 10,
  },
  header: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    marginBottom: 10,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#e91e63',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 5,
  },
  details: {
    fontSize: 14,
    color: '#666',
    marginBottom: 2,
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
  },
  errorText: {
    fontSize: 16,
    color: '#e91e63',
    textAlign: 'center',
    marginTop: 50,
  },
  infoCards: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 10,
  },
  infoCard: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 15,
    flex: 1,
    marginHorizontal: 5,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
  },
  cardValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#e91e63',
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
  },
  actionButton: {
    backgroundColor: '#e91e63',
    borderRadius: 8,
    padding: 12,
    flex: 1,
    marginHorizontal: 5,
    alignItems: 'center',
  },
  actionButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
});