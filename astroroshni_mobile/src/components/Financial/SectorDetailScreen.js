import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../../utils/constants';
import { LineChart } from 'react-native-chart-kit';

const PeriodCard = ({ period, index }) => {
  const getTrendColor = () => {
    if (period.trend === 'BULLISH') return ['#86efac', '#bbf7d0'];
    if (period.trend === 'BEARISH') return ['#fca5a5', '#fecaca'];
    return ['#fcd34d', '#fde68a'];
  };

  const getTrendIcon = () => {
    if (period.trend === 'BULLISH') return 'trending-up';
    if (period.trend === 'BEARISH') return 'trending-down';
    return 'remove';
  };

  return (
    <View style={styles.periodCard}>
      <LinearGradient colors={getTrendColor()} style={styles.periodGradient}>
        <View style={styles.periodHeader}>
          <View style={styles.periodBadge}>
            <Ionicons name={getTrendIcon()} size={16} color="#1f2937" />
            <Text style={styles.periodTrend}>{period.trend}</Text>
          </View>
          <Text style={styles.periodIntensity}>{period.intensity}</Text>
        </View>

        <View style={styles.periodDates}>
          <Text style={styles.periodDate}>{period.start_date}</Text>
          <Ionicons name="arrow-forward" size={16} color="rgba(31,41,55,0.5)" />
          <Text style={styles.periodDate}>{period.end_date}</Text>
        </View>

        <Text style={styles.periodDuration}>{period.duration_days} days</Text>

        <View style={styles.periodReason}>
          <Ionicons name="information-circle" size={16} color="rgba(31,41,55,0.7)" />
          <Text style={styles.periodReasonText}>{period.reason}</Text>
        </View>
      </LinearGradient>
    </View>
  );
};

const TimelineChart = ({ timeline, period }) => {
  if (!timeline || timeline.length === 0) return null;

  console.log('Timeline data:', timeline.length, 'periods');
  console.log('First period:', timeline[0]?.start_date);
  console.log('Last period:', timeline[timeline.length - 1]?.start_date);

  // Convert timeline to chart data
  const chartData = timeline.map(p => {
    if (p.trend === 'BULLISH') return 1;
    if (p.trend === 'BEARISH') return -1;
    return 0;
  });

  // Use start dates as labels with month/day format
  const labels = timeline.map(p => {
    const date = new Date(p.start_date);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    return `${month}/${day}`;
  });

  console.log('Chart data points:', chartData.length);
  console.log('Labels:', labels);

  const screenWidth = Dimensions.get('window').width;
  // Dynamic calculation: fit all periods in screen if <= 8, otherwise use 35px per period
  const periodWidth = timeline.length <= 8 ? (screenWidth - 60) / timeline.length : 35;
  const chartWidth = Math.max(screenWidth - 40, timeline.length * periodWidth);

  return (
    <View style={styles.timelineContainer}>
      <Text style={styles.timelineTitle}>{period || 'Timeline'}</Text>
      <Text style={styles.chartSubtitle}>{timeline.length} forecast periods</Text>
      <View style={styles.chartWrapper}>
        <ScrollView horizontal showsHorizontalScrollIndicator={true} contentContainerStyle={{ paddingRight: 20 }}>
          <LineChart
            data={{
              labels: labels,
              datasets: [{ 
                data: chartData,
                strokeWidth: 3
              }]
            }}
            width={chartWidth}
            height={200}
            yAxisInterval={1}
            chartConfig={{
              backgroundColor: '#1a1a2e',
              backgroundGradientFrom: '#1a1a2e',
              backgroundGradientTo: '#1a1a2e',
              decimalPlaces: 0,
              color: (opacity = 1) => `rgba(134, 239, 172, ${opacity})`,
              labelColor: (opacity = 1) => `rgba(136, 136, 136, ${opacity})`,
              style: { borderRadius: 16 },
              propsForDots: {
                r: '4',
                strokeWidth: '2',
              },
              propsForBackgroundLines: {
                strokeDasharray: '',
                stroke: 'rgba(255,255,255,0.1)'
              },
              propsForLabels: {
                fontSize: 8
              }
            }}
            bezier
            style={styles.chart}
            segments={2}
            withVerticalLines={true}
            withHorizontalLines={true}
            withInnerLines={true}
            withOuterLines={true}
            formatXLabel={(value, index) => labels[index] || value}
            getDotColor={(dataPoint, dataPointIndex) => {
              const trend = timeline[dataPointIndex]?.trend;
              if (trend === 'BULLISH') return '#86efac';
              if (trend === 'BEARISH') return '#fca5a5';
              return '#fcd34d';
            }}
          />
        </ScrollView>
      </View>
      <View style={styles.timelineLegend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#86efac' }]} />
          <Text style={styles.legendText}>Bullish</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#fca5a5' }]} />
          <Text style={styles.legendText}>Bearish</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#fcd34d' }]} />
          <Text style={styles.legendText}>Neutral</Text>
        </View>
      </View>
    </View>
  );
};

export default function SectorDetailScreen({ route, navigation }) {
  const { sector } = route.params;
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchSectorData();
  }, []);

  const fetchSectorData = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(
        `${API_BASE_URL}/api/financial/forecast/${encodeURIComponent(sector)}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      const json = await response.json();
      setData(json);
    } catch (error) {
      console.error('Error fetching sector data:', error);
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
            <Text style={styles.loadingText}>Loading {sector}...</Text>
          </SafeAreaView>
        </LinearGradient>
      </View>
    );
  }

  if (!data) {
    return (
      <View style={styles.centerContainer}>
        <LinearGradient colors={['#0f0c29', '#302b63']} style={styles.bg}>
          <SafeAreaView style={styles.safeArea}>
            <Text style={styles.errorText}>Failed to load sector data</Text>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
              <Text style={styles.backButtonText}>Go Back</Text>
            </TouchableOpacity>
          </SafeAreaView>
        </LinearGradient>
      </View>
    );
  }

  const { summary, timeline, ruler, period } = data;

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#0f0c29', '#302b63', '#24243e']} style={styles.bg}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Ionicons name="arrow-back" size={24} color="#fff" />
            </TouchableOpacity>
            <Text style={styles.headerTitle} numberOfLines={1}>{sector}</Text>
            <View style={{ width: 24 }} />
          </View>

          <ScrollView showsVerticalScrollIndicator={false}>
            {/* Sector Info */}
            <View style={styles.infoSection}>
              <Text style={styles.sectorName}>{sector}</Text>
              <Text style={styles.rulerText}>Ruled by ♃ {ruler}</Text>
              
              <View style={styles.statsRow}>
                <View style={styles.statBox}>
                  <Text style={styles.statValue}>{summary.total_periods}</Text>
                  <Text style={styles.statLabel}>Total Periods</Text>
                </View>
                <View style={[styles.statBox, { borderColor: '#10b981' }]}>
                  <Text style={[styles.statValue, { color: '#10b981' }]}>{summary.bullish_count}</Text>
                  <Text style={styles.statLabel}>Bullish</Text>
                </View>
                <View style={[styles.statBox, { borderColor: '#ef4444' }]}>
                  <Text style={[styles.statValue, { color: '#ef4444' }]}>{summary.bearish_count}</Text>
                  <Text style={styles.statLabel}>Bearish</Text>
                </View>
              </View>
            </View>

            {/* Timeline Visualization */}
            <TimelineChart timeline={timeline} period={period} />

            {/* All Periods */}
            <View style={styles.periodsSection}>
              <Text style={styles.sectionTitle}>Forecast Periods</Text>
              {timeline.map((period, idx) => (
                <PeriodCard key={idx} period={period} index={idx} />
              ))}
            </View>
          </ScrollView>
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
  errorText: { color: '#fff', fontSize: 16, marginBottom: 20 },
  backButton: { backgroundColor: '#6366f1', padding: 12, borderRadius: 8 },
  backButtonText: { color: '#fff', fontWeight: 'bold' },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
  },
  headerTitle: { color: '#fff', fontSize: 18, fontWeight: 'bold', flex: 1, textAlign: 'center' },

  infoSection: {
    padding: 20,
    alignItems: 'center',
  },
  sectorName: { color: '#fff', fontSize: 24, fontWeight: 'bold', marginBottom: 8, textAlign: 'center' },
  rulerText: { color: '#10b981', fontSize: 16, marginBottom: 20 },
  
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  statBox: {
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  statValue: { color: '#fff', fontSize: 24, fontWeight: 'bold', marginBottom: 4 },
  statLabel: { color: '#888', fontSize: 12 },

  timelineContainer: {
    marginVertical: 20,
    paddingHorizontal: 20,
  },
  timelineTitle: { color: '#fff', fontSize: 16, fontWeight: 'bold', marginBottom: 4 },
  chartSubtitle: { color: '#888', fontSize: 12, marginBottom: 12 },
  chartWrapper: {
    marginLeft: -20,
    marginRight: -20,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  timelineLegend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    marginTop: 8,
  },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legendDot: { width: 12, height: 12, borderRadius: 6 },
  legendText: { color: '#888', fontSize: 12 },

  periodsSection: {
    padding: 20,
  },
  sectionTitle: { color: '#fff', fontSize: 18, fontWeight: 'bold', marginBottom: 16 },

  periodCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  periodGradient: {
    padding: 16,
  },
  periodHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  periodBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(31,41,55,0.15)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  periodTrend: { color: '#1f2937', fontSize: 14, fontWeight: 'bold' },
  periodIntensity: { color: 'rgba(31,41,55,0.7)', fontSize: 12 },
  
  periodDates: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  periodDate: { color: '#1f2937', fontSize: 14, fontWeight: '600' },
  periodDuration: { color: 'rgba(31,41,55,0.6)', fontSize: 12, marginBottom: 12 },
  
  periodReason: {
    flexDirection: 'row',
    gap: 8,
    backgroundColor: 'rgba(31,41,55,0.1)',
    padding: 12,
    borderRadius: 8,
  },
  periodReasonText: { color: 'rgba(31,41,55,0.8)', fontSize: 13, lineHeight: 18, flex: 1 },
});
