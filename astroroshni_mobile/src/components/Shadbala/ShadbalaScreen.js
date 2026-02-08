import React, { useState, useEffect, useMemo } from 'react';
import { View, Text, ScrollView, StyleSheet, ActivityIndicator, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import api, { chartAPI } from '../../services/api';
import { getEndpoint } from '../../utils/constants';

const ShadbalaScreen = ({ route, navigation }) => {
  const { birthData } = route.params;
  const { theme, colors } = useTheme();
  const [loading, setLoading] = useState(true);
  const [shadbalaData, setData] = useState(null);
  const [selectedPlanet, setSelectedPlanet] = useState(null);
  const [hasFetched, setHasFetched] = useState(false);

  useEffect(() => {
    if (!hasFetched) {
      fetchShadbala();
      setHasFetched(true);
    }
  }, [hasFetched]);

  const fetchShadbala = async () => {
    try {
      const chartResponse = await chartAPI.calculateChartOnly(birthData);
      const response = await api.post(getEndpoint('/calculate-classical-shadbala'), {
        birth_data: birthData,
        chart_data: chartResponse.data
      });
      
      // Deep clone to prevent mutations
      const clonedData = JSON.parse(JSON.stringify(response.data));
      setData(clonedData);
      
      if (clonedData.shadbala) {
        const firstPlanet = Object.keys(clonedData.shadbala)[0];
        setSelectedPlanet(firstPlanet);
      }
    } catch (error) {
      console.error('Shadbala fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (grade) => {
    if (grade === 'Excellent') return colors.success;
    if (grade === 'Good') return '#8BC34A';
    if (grade === 'Average') return colors.warning;
    return colors.error;
  };

  const getPlanetIcon = (planet) => {
    const icons = {
      Sun: '☉', Moon: '☽', Mars: '♂', Mercury: '☿',
      Jupiter: '♃', Venus: '♀', Saturn: '♄',
      Rahu: '☊', Ketu: '☋'
    };
    return icons[planet] || '●';
  };

  const planetData = shadbalaData?.shadbala || {};
  
  const filteredPlanetData = useMemo(() => {
    const validPlanets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
    return Object.keys(planetData)
      .filter(planet => validPlanets.includes(planet))
      .reduce((obj, key) => {
        obj[key] = planetData[key];
        return obj;
      }, {});
  }, [planetData]);
  
  const selected = useMemo(() => {
    return selectedPlanet ? filteredPlanetData[selectedPlanet] : null;
  }, [selectedPlanet, filteredPlanetData]);

  if (loading) {
    return (
      <LinearGradient colors={[colors.gradientStart, colors.gradientMid]} style={styles.container}>
        <ActivityIndicator size="large" color={colors.primary} />
      </LinearGradient>
    );
  }


  return (
    <LinearGradient colors={[colors.gradientStart, colors.gradientMid, colors.gradientEnd]} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.closeButton, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(249, 115, 22, 0.25)' }]}>
            <Ionicons name="close" size={20} color={colors.text} />
          </TouchableOpacity>
        </View>
        <ScrollView showsVerticalScrollIndicator={false}>
          <Text style={[styles.title, { color: colors.text }]}>Shadbala Analysis</Text>
          <Text style={[styles.subtitle, { color: colors.textSecondary }]}>Classical Planetary Strength (7 Visible Planets)</Text>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pillContainer}>
          {Object.keys(filteredPlanetData).map(planet => (
            <TouchableOpacity
              key={planet}
              onPress={() => setSelectedPlanet(planet)}
              style={[
                styles.pill,
                { backgroundColor: colors.surface, borderColor: colors.cardBorder },
                selectedPlanet === planet && { backgroundColor: colors.primary + '40', borderColor: colors.primary }
              ]}>
              <Text style={[styles.pillIcon, { color: colors.text }]}>{getPlanetIcon(planet)}</Text>
              <Text style={[styles.pillText, { color: colors.text }]}>{planet}</Text>
              <View style={[styles.pillBadge, { backgroundColor: getGradeColor(filteredPlanetData[planet].grade) }]}>
                <Text style={styles.pillBadgeText}>{filteredPlanetData[planet].total_rupas.toFixed(1)}</Text>
              </View>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {selected && (
          <>
            <View style={[styles.card, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
              <View style={styles.cardHeader}>
                <Text style={[styles.planetIcon, { color: colors.text }]}>{getPlanetIcon(selectedPlanet)}</Text>
                <View style={styles.cardHeaderText}>
                  <Text style={[styles.planetName, { color: colors.text }]}>{selectedPlanet}</Text>
                  <Text style={[styles.grade, { color: getGradeColor(selected.grade) }]}>
                    {selected.grade}
                  </Text>
                </View>
              </View>
              
              <View style={styles.strengthRow}>
                <View style={styles.strengthItem}>
                  <Text style={[styles.strengthValue, { color: colors.text }]}>{selected.total_rupas.toFixed(2)}</Text>
                  <Text style={[styles.strengthLabel, { color: colors.textSecondary }]}>Rupas</Text>
                </View>
                <View style={[styles.strengthDivider, { backgroundColor: colors.cardBorder }]} />
                <View style={styles.strengthItem}>
                  <Text style={[styles.strengthValue, { color: colors.text }]}>{selected.total_points.toFixed(0)}</Text>
                  <Text style={[styles.strengthLabel, { color: colors.textSecondary }]}>Points</Text>
                </View>
              </View>

              <View style={styles.progressContainer}>
                <View style={[styles.progressBar, { backgroundColor: colors.surface }]}>
                  <LinearGradient
                    colors={[getGradeColor(selected.grade), getGradeColor(selected.grade) + '80']}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                    style={[styles.progressFill, { width: `${Math.min((selected.total_rupas / 10) * 100, 100)}%` }]}
                  />
                </View>
                <View style={styles.progressLabels}>
                  <Text style={[styles.progressLabel, { color: colors.textTertiary }]}>0</Text>
                  <Text style={[styles.progressLabel, { color: colors.textTertiary }]}>5</Text>
                  <Text style={[styles.progressLabel, { color: colors.textTertiary }]}>10</Text>
                </View>
              </View>
            </View>

            <View style={[styles.card, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>Strength Components</Text>
              {Object.entries(selected.components).map(([key, value]) => (
                <View key={key} style={[styles.componentRow, { borderBottomColor: colors.cardBorder }]}>
                  <Text style={[styles.componentName, { color: colors.textSecondary }]}>{formatComponentName(key)}</Text>
                  <Text style={[styles.componentValue, { color: colors.text }]}>{value.toFixed(1)}</Text>
                </View>
              ))}
            </View>

            {selected.detailed_breakdown && (
              <>
                <View style={[styles.card, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
                  <Text style={[styles.sectionTitle, { color: colors.text }]}>Sthana Bala Breakdown</Text>
                  {Object.entries(selected.detailed_breakdown.sthana_components).map(([key, value]) => (
                    <View key={key} style={styles.detailRow}>
                      <Text style={[styles.detailName, { color: colors.textSecondary }]}>{formatComponentName(key)}</Text>
                      <Text style={[styles.detailValue, { color: colors.text }]}>{value.toFixed(1)}</Text>
                    </View>
                  ))}
                </View>

                <View style={[styles.card, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
                  <Text style={[styles.sectionTitle, { color: colors.text }]}>Kala Bala Breakdown</Text>
                  {Object.entries(selected.detailed_breakdown.kala_components).map(([key, value]) => (
                    <View key={key} style={styles.detailRow}>
                      <Text style={[styles.detailName, { color: colors.textSecondary }]}>{formatComponentName(key)}</Text>
                      <Text style={[styles.detailValue, { color: colors.text }]}>{value.toFixed(1)}</Text>
                    </View>
                  ))}
                </View>
              </>
            )}
          </>
        )}
      </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
};

const formatComponentName = (name) => {
  return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  header: { paddingHorizontal: 15, paddingVertical: 10 },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: { fontSize: 28, fontWeight: 'bold', textAlign: 'center', marginTop: 10 },
  subtitle: { fontSize: 14, textAlign: 'center', marginBottom: 20 },
  pillContainer: { paddingHorizontal: 15, marginBottom: 20 },
  pill: {
    flexDirection: 'row', alignItems: 'center', borderRadius: 25,
    paddingHorizontal: 15, paddingVertical: 10, marginRight: 10, borderWidth: 1
  },
  pillIcon: { fontSize: 20, marginRight: 8 },
  pillText: { fontSize: 14, fontWeight: '600', marginRight: 8 },
  pillBadge: { borderRadius: 12, paddingHorizontal: 8, paddingVertical: 2 },
  pillBadgeText: { fontSize: 12, color: '#fff', fontWeight: 'bold' },
  card: {
    borderRadius: 15, padding: 20, marginHorizontal: 15, marginBottom: 15, borderWidth: 1
  },
  cardHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 20 },
  planetIcon: { fontSize: 48, marginRight: 15 },
  cardHeaderText: { flex: 1 },
  planetName: { fontSize: 24, fontWeight: 'bold' },
  grade: { fontSize: 16, fontWeight: '600', marginTop: 4 },
  strengthRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 20 },
  strengthItem: { alignItems: 'center' },
  strengthValue: { fontSize: 32, fontWeight: 'bold' },
  strengthLabel: { fontSize: 12, marginTop: 4 },
  strengthDivider: { width: 1 },
  progressContainer: { marginTop: 10 },
  progressBar: { height: 8, borderRadius: 4, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 4 },
  progressLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 5 },
  progressLabel: { fontSize: 10 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 15 },
  componentRow: {
    flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 12,
    borderBottomWidth: 1
  },
  componentName: { fontSize: 14, flex: 1 },
  componentValue: { fontSize: 16, fontWeight: '600' },
  detailRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8 },
  detailName: { fontSize: 13, flex: 1 },
  detailValue: { fontSize: 14, fontWeight: '500' }
});

export default ShadbalaScreen;
