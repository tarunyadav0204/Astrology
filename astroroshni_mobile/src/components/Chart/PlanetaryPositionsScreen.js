import React from 'react';
import { View, Text, StyleSheet, ScrollView, StatusBar, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../utils/constants';

const PlanetaryPositionsScreen = ({ navigation, route }) => {
  const { chartData } = route.params;

  const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                      'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
  
  const rashiIcons = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];

  const planetEmojis = {
    'Sun': '☉', 'Moon': '☽', 'Mars': '♂', 'Mercury': '☿',
    'Jupiter': '♃', 'Venus': '♀', 'Saturn': '♄',
    'Rahu': '☊', 'Ketu': '☋'
  };

  const getNakshatra = (longitude) => {
    const nakshatras = [
      'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
      'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
      'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
      'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
      'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
    ];
    const nakshatraIndex = Math.floor(longitude / 13.333333);
    return nakshatras[nakshatraIndex] || 'Unknown';
  };

  const getNakshatraPada = (longitude) => {
    const degreeInNakshatra = longitude % 13.333333;
    return Math.floor(degreeInNakshatra / 3.333333) + 1;
  };

  const planetOrder = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
  
  const planets = planetOrder
    .filter(name => chartData.planets[name])
    .map(name => ({
      name,
      ...chartData.planets[name],
      nakshatra: getNakshatra(chartData.planets[name].longitude),
      pada: getNakshatraPada(chartData.planets[name].longitude)
    }));

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={COLORS.background} />
      <LinearGradient
        colors={[COLORS.gradientStart, COLORS.gradientEnd]}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={COLORS.primary} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Planetary Positions</Text>
            <View style={styles.placeholder} />
          </View>

          <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
            {planets.map((planet, index) => (
              <View key={planet.name} style={styles.card}>
                <LinearGradient
                  colors={['#ffffff', '#fef7f0']}
                  style={styles.cardGradient}
                >
                  <View style={styles.cardHeader}>
                    <View style={styles.planetInfo}>
                      <Text style={styles.planetEmoji}>{planetEmojis[planet.name]}</Text>
                      <View>
                        <Text style={styles.planetName}>{planet.name}</Text>
                        {planet.retrograde && (
                          <Text style={styles.retrogradeTag}>Retrograde</Text>
                        )}
                      </View>
                    </View>
                    <View style={styles.houseTag}>
                      <Text style={styles.houseText}>House {planet.house}</Text>
                    </View>
                  </View>

                  <View style={styles.divider} />

                  <View style={styles.detailsGrid}>
                    <View style={styles.detailItem}>
                      <Text style={styles.detailLabel}>Rashi</Text>
                      <View style={styles.rashiContainer}>
                        <Text style={styles.rashiIcon}>{rashiIcons[planet.sign]}</Text>
                        <Text style={styles.detailValue}>{rashiNames[planet.sign]}</Text>
                      </View>
                    </View>

                    <View style={styles.detailItem}>
                      <Text style={styles.detailLabel}>Degree</Text>
                      <Text style={styles.detailValue}>{planet.degree.toFixed(2)}°</Text>
                    </View>

                    <View style={styles.detailItemFull}>
                      <Text style={styles.detailLabel}>Nakshatra</Text>
                      <Text style={styles.detailValue}>{planet.nakshatra} - Pada {planet.pada}</Text>
                    </View>
                  </View>
                </LinearGradient>
              </View>
            ))}
          </ScrollView>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.white,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  placeholder: { width: 40 },
  scrollView: {
    flex: 1,
    paddingHorizontal: 20,
  },
  card: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  cardGradient: {
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  planetInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  planetEmoji: {
    fontSize: 32,
  },
  planetName: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  retrogradeTag: {
    fontSize: 10,
    color: COLORS.error,
    fontWeight: '600',
    marginTop: 2,
  },
  houseTag: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  houseText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.white,
  },
  divider: {
    height: 1,
    backgroundColor: COLORS.border,
    marginVertical: 12,
  },
  detailsGrid: {
    gap: 12,
  },
  detailItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailItemFull: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 14,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  detailValue: {
    fontSize: 14,
    color: COLORS.textPrimary,
    fontWeight: '700',
  },
  rashiContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  rashiIcon: {
    fontSize: 16,
  },
});

export default PlanetaryPositionsScreen;
