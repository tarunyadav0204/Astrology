import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  Alert,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { useAstrology } from '../context/AstrologyContext';
import { apiService } from '../services/apiService';

export default function ChartListScreen({ navigation }) {
  const { calculateChart } = useAstrology();
  const [charts, setCharts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadCharts();
  }, []);

  const loadCharts = async () => {
    try {
      setLoading(true);
      const response = await apiService.getExistingCharts(searchQuery);
      setCharts(response.charts || []);
    } catch (error) {
      console.error('Error loading charts:', error);
      Alert.alert('Error', 'Failed to load charts');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadCharts();
  };

  const selectChart = async (chart) => {
    try {
      const birthData = {
        name: chart.name,
        date: chart.date,
        time: chart.time,
        latitude: chart.latitude.toString(),
        longitude: chart.longitude.toString(),
        timezone: chart.timezone,
        place: `${chart.latitude}, ${chart.longitude}`
      };
      
      await calculateChart(birthData);
      navigation.navigate('Dashboard', { birthData });
    } catch (error) {
      Alert.alert('Error', 'Failed to load chart');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient
        colors={['#ff6b35', '#f7931e', '#ffcc80']}
        style={styles.gradient}
      >
        <ScrollView showsVerticalScrollIndicator={false}>
          <View style={styles.header}>
            <Text style={styles.title}>🌌 Welcome to Your Cosmic Journey</Text>
            <Text style={styles.subtitle}>Discover the secrets written in the stars</Text>
          </View>

          <View style={styles.searchContainer}>
            <TextInput
              style={styles.searchInput}
              placeholder="🔍 Search your charts..."
              value={searchQuery}
              onChangeText={setSearchQuery}
              onSubmitEditing={handleSearch}
            />
            <TouchableOpacity
              onPress={() => navigation.navigate('BirthForm')}
              style={styles.newChartButton}
            >
              <Text style={styles.newChartButtonText}>➕ Create New Chart</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.listContainer}>
            {loading ? (
              <View style={styles.loadingContainer}>
                <Text style={styles.loadingEmoji}>🔮</Text>
                <Text style={styles.loadingText}>Loading your charts...</Text>
              </View>
            ) : charts.length === 0 ? (
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyEmoji}>🌌</Text>
                <Text style={styles.emptyTitle}>Begin Your Cosmic Journey</Text>
                <Text style={styles.emptyText}>
                  {searchQuery ? 'Try a different search term to find your charts' : 'The stars are waiting to reveal your destiny. Create your first astrology chart and unlock the mysteries of your birth.'}
                </Text>
                <TouchableOpacity
                  onPress={() => navigation.navigate('BirthForm')}
                  style={styles.createFirstButton}
                >
                  <Text style={styles.createFirstButtonText}>🌟 Create Your Cosmic Blueprint</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <View style={styles.chartsGrid}>
                {charts.map(chart => (
                  <TouchableOpacity
                    key={chart.id}
                    style={styles.chartCard}
                    onPress={() => selectChart(chart)}
                  >
                    <View style={styles.chartInfo}>
                      <Text style={styles.chartName}>{chart.name}</Text>
                      <Text style={styles.chartDate}>📅 {new Date(chart.date).toLocaleDateString()}</Text>
                      <Text style={styles.chartTime}>🕐 {chart.time}</Text>
                      <Text style={styles.chartLocation}>📍 {chart.latitude.toFixed(2)}, {chart.longitude.toFixed(2)}</Text>
                    </View>
                    <View style={styles.viewButton}>
                      <Text style={styles.viewButtonText}>🔮 View Cosmic Insights</Text>
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>
        </ScrollView>
      </LinearGradient>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  header: {
    padding: 30,
    paddingTop: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    margin: 20,
    borderRadius: 20,
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ff6b35',
    textAlign: 'center',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  searchContainer: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  searchInput: {
    backgroundColor: 'white',
    borderRadius: 25,
    paddingHorizontal: 20,
    paddingVertical: 15,
    fontSize: 16,
    marginBottom: 15,
    borderWidth: 2,
    borderColor: '#ff6b35',
  },
  newChartButton: {
    backgroundColor: '#ff6b35',
    borderRadius: 25,
    paddingVertical: 15,
    alignItems: 'center',
  },
  newChartButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  listContainer: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  loadingContainer: {
    alignItems: 'center',
    padding: 50,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 20,
  },
  loadingEmoji: {
    fontSize: 40,
    marginBottom: 10,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 20,
  },
  emptyEmoji: {
    fontSize: 60,
    marginBottom: 20,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ff6b35',
    marginBottom: 15,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 30,
  },
  createFirstButton: {
    backgroundColor: '#ff6b35',
    borderRadius: 30,
    paddingVertical: 18,
    paddingHorizontal: 40,
  },
  createFirstButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  chartsGrid: {
    gap: 15,
  },
  chartCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 20,
    padding: 20,
    borderWidth: 2,
    borderColor: 'rgba(255, 107, 53, 0.3)',
  },
  chartInfo: {
    marginBottom: 15,
  },
  chartName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ff6b35',
    marginBottom: 8,
  },
  chartDate: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  chartTime: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  chartLocation: {
    fontSize: 14,
    color: '#666',
  },
  viewButton: {
    backgroundColor: 'rgba(255, 107, 53, 0.2)',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
  },
  viewButtonText: {
    color: '#ff6b35',
    fontSize: 14,
    fontWeight: '600',
  },
});