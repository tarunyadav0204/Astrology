import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import NorthIndianChart from '../components/NorthIndianChart';

export default function ChartsScreen() {
  const [selectedChart, setSelectedChart] = useState('lagna');

  const chartTypes = [
    { id: 'lagna', name: 'Lagna (D1)', description: 'Birth Chart' },
    { id: 'navamsa', name: 'Navamsa (D9)', description: 'Marriage & Spirituality' },
    { id: 'dasamsa', name: 'Dasamsa (D10)', description: 'Career & Profession' },
    { id: 'dwadasamsa', name: 'Dwadasamsa (D12)', description: 'Parents & Ancestry' },
  ];

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

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.title}>Divisional Charts</Text>
        
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false}
          style={styles.chartSelector}
        >
          {chartTypes.map((chart) => (
            <TouchableOpacity
              key={chart.id}
              style={[
                styles.chartTab,
                selectedChart === chart.id && styles.activeChartTab
              ]}
              onPress={() => setSelectedChart(chart.id)}
            >
              <Text style={[
                styles.chartTabText,
                selectedChart === chart.id && styles.activeChartTabText
              ]}>
                {chart.name}
              </Text>
              <Text style={[
                styles.chartTabDescription,
                selectedChart === chart.id && styles.activeChartTabDescription
              ]}>
                {chart.description}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <NorthIndianChart 
          chartData={mockChartData}
          onHousePress={(house) => console.log(`House ${house} pressed`)}
        />

        <View style={styles.chartInfo}>
          <Text style={styles.infoTitle}>
            {chartTypes.find(c => c.id === selectedChart)?.name}
          </Text>
          <Text style={styles.infoDescription}>
            {chartTypes.find(c => c.id === selectedChart)?.description}
          </Text>
          
          <View style={styles.planetList}>
            <Text style={styles.planetListTitle}>Planetary Positions:</Text>
            {Object.entries(mockChartData.planets).map(([planet, data]) => (
              <View key={planet} style={styles.planetRow}>
                <Text style={styles.planetName}>{planet}</Text>
                <Text style={styles.planetDetails}>
                  House {data.house} • {data.degree}°
                </Text>
              </View>
            ))}
          </View>
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
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#e91e63',
    textAlign: 'center',
    marginBottom: 20,
  },
  chartSelector: {
    marginBottom: 20,
  },
  chartTab: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 15,
    marginRight: 10,
    minWidth: 120,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  activeChartTab: {
    backgroundColor: '#e91e63',
  },
  chartTabText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
  },
  activeChartTabText: {
    color: 'white',
  },
  chartTabDescription: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginTop: 4,
  },
  activeChartTabDescription: {
    color: 'rgba(255,255,255,0.8)',
  },
  chartInfo: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    marginTop: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#e91e63',
    marginBottom: 5,
  },
  infoDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 15,
  },
  planetList: {
    marginTop: 10,
  },
  planetListTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  planetRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  planetName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  planetDetails: {
    fontSize: 14,
    color: '#666',
  },
});