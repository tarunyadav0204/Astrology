import React from 'react';
import { View, Text, StyleSheet, ScrollView, StatusBar, TouchableOpacity, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';

const PlanetaryPositionsScreen = ({ navigation, route }) => {
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const { chartData, birthData } = route.params;
  const screenGradient = isDark
    ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd]
    : [colors.gradientStart, colors.gradientMid, colors.gradientEnd];
  const [activeTab, setActiveTab] = React.useState('planets');
  const [karakas, setKarakas] = React.useState(null);
  const [jaiminiLagnas, setJaiminiLagnas] = React.useState(null);
  const [yogiPoints, setYogiPoints] = React.useState(null);
  const [sniperPoints, setSniperPoints] = React.useState(null);
  const [pushkaraData, setPushkaraData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [lagnasLoading, setLagnasLoading] = React.useState(false);
  const [specialLoading, setSpecialLoading] = React.useState(false);
  const [specialLoaded, setSpecialLoaded] = React.useState(false);

  React.useEffect(() => {
    loadKarakas();
  }, []);

  React.useEffect(() => {
    if (activeTab === 'lagnas' && !jaiminiLagnas) {
      loadJaiminiLagnas();
    }
  }, [activeTab]);

  React.useEffect(() => {
    if (activeTab === 'special' && !specialLoaded) {
      loadSpecialPoints();
    }
  }, [activeTab]);

  const loadKarakas = async () => {
    try {
      const { chartAPI } = require('../../services/api');
      const response = await chartAPI.calculateCharaKarakas(chartData, birthData);
      setKarakas(response.data.karakas || response.data.chara_karakas || response.data);
    } catch (error) {
      console.error('Error loading karakas:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadJaiminiLagnas = async () => {
    setLagnasLoading(true);
    try {
      const { chartAPI } = require('../../services/api');
      
      if (!karakas?.Atmakaraka?.planet) {
        console.error('Atmakaraka not available, cannot load Jaimini lagnas');
        setLagnasLoading(false);
        return;
      }
      
      const atmakaraka = karakas.Atmakaraka.planet;
      const d9Chart = route.params?.d9Chart || {};
      const response = await chartAPI.calculateJaiminiLagnas(chartData, d9Chart, atmakaraka);
      setJaiminiLagnas(response.data.jaimini_lagnas);
    } catch (error) {
      console.error('Error loading Jaimini lagnas:', error);
      console.error('Error details:', error.response?.data);
    } finally {
      setLagnasLoading(false);
    }
  };

  const loadSpecialPoints = async () => {
    setSpecialLoading(true);
    try {
      const { chartAPI } = require('../../services/api');
      const d9Chart = route.params?.d9Chart || {};
      const [yogiResponse, sniperResponse, pushkaraResponse] = await Promise.all([
        chartAPI.calculateYogiPoints(birthData),
        chartAPI.calculateSniperPoints(chartData),
        chartAPI.calculatePushkaraNavamsha(chartData, d9Chart)
      ]);
      setYogiPoints(yogiResponse.data.yogi_points);
      setSniperPoints(sniperResponse.data.sniper_points);
      setPushkaraData(pushkaraResponse.data.pushkara_analysis);
    } catch (error) {
      console.error('Error loading special points:', error);
    } finally {
      setSpecialLoading(false);
      setSpecialLoaded(true);
    }
  };

  const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                      'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
  
  const rashiIcons = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];

  const planetEmojis = {
    'Sun': '☉', 'Moon': '☽', 'Mars': '♂', 'Mercury': '☿',
    'Jupiter': '♃', 'Venus': '♀', 'Saturn': '♄',
    'Rahu': '☊', 'Ketu': '☋', 'Gulika': '🌑', 'Mandi': '⚫',
    'Indu Lagna': '🌙', 'Bhava Lagna': '🏠', 'Hora Lagna': '💰',
    'Ascendant (Lagna)': '⬆️', 'Arudha Lagna': '🎭', 'Upapada Lagna': '💑',
    'Karkamsa Lagna': '🎯', 'Swamsa Lagna': '🕉️', 'Ghatika Lagna': '👑',
    'Darapada': '🤝'
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

  const planetOrder = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi'];
  
  const planets = planetOrder
    .filter(name => chartData.planets[name])
    .map(name => ({
      name,
      ...chartData.planets[name],
      nakshatra: getNakshatra(chartData.planets[name].longitude),
      pada: getNakshatraPada(chartData.planets[name].longitude)
    }));

  // Lagnas data
  const lagnas = [
    {
      name: 'Ascendant (Lagna)',
      longitude: chartData.ascendant,
      sign: Math.floor(chartData.ascendant / 30),
      degree: chartData.ascendant % 30,
      house: 1,
      nakshatra: getNakshatra(chartData.ascendant),
      pada: getNakshatraPada(chartData.ascendant),
      description: 'Self, Personality, Physical Body'
    }
  ];
  
  if (chartData.planets?.InduLagna) {
    lagnas.push({
      name: 'Indu Lagna',
      ...chartData.planets.InduLagna,
      nakshatra: getNakshatra(chartData.planets.InduLagna.longitude),
      pada: getNakshatraPada(chartData.planets.InduLagna.longitude),
      description: 'Wealth Indicator'
    });
  }

  // Add Jaimini Lagnas if loaded
  if (jaiminiLagnas) {
    const jaiminiLagnasList = [
      { key: 'arudha_lagna', name: 'Arudha Lagna' },
      { key: 'upapada_lagna', name: 'Upapada Lagna' },
      { key: 'darapada', name: 'Darapada' },
      { key: 'karkamsa_lagna', name: 'Karkamsa Lagna' },
      { key: 'swamsa_lagna', name: 'Swamsa Lagna' },
      { key: 'hora_lagna', name: 'Hora Lagna' },
      { key: 'ghatika_lagna', name: 'Ghatika Lagna' }
    ];

    jaiminiLagnasList.forEach(({ key, name }) => {
      const lagnaData = jaiminiLagnas[key];
      if (lagnaData) {
        const signId = lagnaData.sign_id;
        lagnas.push({
          name: name,
          sign: signId,
          house: ((signId - Math.floor(chartData.ascendant / 30) + 12) % 12) + 1,
          description: lagnaData.description,
          isJaimini: true
        });
      }
    });
  }

  // Tab Button Component
  const TabButton = ({ label, emoji, value, active }) => (
    <TouchableOpacity
      style={[
        styles.tabButton,
        { backgroundColor: active ? colors.primary : (isDark ? colors.surface : colors.cardBackground), borderColor: active ? colors.primary : colors.cardBorder },
        active && styles.tabButtonActive,
      ]}
      onPress={() => setActiveTab(value)}
    >
      <Text style={[styles.tabEmoji, active && styles.tabEmojiActive]}>{emoji}</Text>
      <Text style={[styles.tabLabel, { color: active ? '#fff' : colors.text }, active && styles.tabLabelActive]}>{label}</Text>
    </TouchableOpacity>
  );

  // Planet Card Component
  const planetCardGradient = isDark ? [colors.cardBackground, colors.surface] : [colors.cardBackground, colors.backgroundSecondary];
  const PlanetCard = ({ planet }) => (
    <View style={styles.card}>
      <LinearGradient colors={planetCardGradient} style={[styles.cardGradient, { borderColor: colors.cardBorder }]}>
        <View style={styles.cardHeader}>
          <View style={styles.planetInfo}>
            <Text style={styles.planetEmoji}>{planetEmojis[planet.name]}</Text>
            <View>
              <Text style={[styles.planetName, { color: colors.text }]}>{planet.name}</Text>
              {planet.retrograde && <Text style={[styles.retrogradeTag, { color: colors.error }]}>Retrograde</Text>}
            </View>
          </View>
          <View style={[styles.houseTag, { backgroundColor: colors.primary }]}>
            <Text style={styles.houseText}>House {planet.house}</Text>
          </View>
        </View>
        <View style={[styles.divider, { backgroundColor: colors.cardBorder }]} />
        <View style={styles.detailsGrid}>
          <View style={styles.detailItem}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>Rashi</Text>
            <View style={styles.rashiContainer}>
              <Text style={styles.rashiIcon}>{rashiIcons[planet.sign]}</Text>
              <Text style={[styles.detailValue, { color: colors.text }]}>{rashiNames[planet.sign]}</Text>
            </View>
          </View>
          <View style={styles.detailItem}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>Degree</Text>
            <Text style={[styles.detailValue, { color: colors.text }]}>{planet.degree.toFixed(2)}°</Text>
          </View>
          <View style={styles.detailItemFull}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>Nakshatra</Text>
            <Text style={[styles.detailValue, { color: colors.text }]}>{planet.nakshatra} - Pada {planet.pada}</Text>
          </View>
        </View>
      </LinearGradient>
    </View>
  );

  // Lagna Card Component
  const lagnaCardGradient = isDark ? [colors.backgroundSecondary, colors.cardBackground] : [colors.backgroundSecondary, colors.cardBackground];
  const LagnaCard = ({ lagna }) => (
    <View style={styles.card}>
      <LinearGradient colors={lagnaCardGradient} style={[styles.cardGradient, { borderColor: colors.cardBorder }]}>
        <View style={styles.cardHeader}>
          <View style={styles.planetInfo}>
            <Text style={styles.planetEmoji}>{planetEmojis[lagna.name] || '⭐'}</Text>
            <View style={{ flex: 1 }}>
              <Text style={[styles.planetName, { color: colors.text }]}>{lagna.name}</Text>
              {lagna.description && (
                <Text style={[styles.lagnaDescription, { color: colors.textSecondary }]}>{lagna.description}</Text>
              )}
            </View>
          </View>
          <View style={[styles.houseTag, { backgroundColor: colors.primary }]}>
            <Text style={styles.houseText}>House {lagna.house}</Text>
          </View>
        </View>
        <View style={[styles.divider, { backgroundColor: colors.cardBorder }]} />
        <View style={styles.detailsGrid}>
          <View style={styles.detailItem}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>Rashi</Text>
            <View style={styles.rashiContainer}>
              <Text style={styles.rashiIcon}>{rashiIcons[lagna.sign]}</Text>
              <Text style={[styles.detailValue, { color: colors.text }]}>{rashiNames[lagna.sign]}</Text>
            </View>
          </View>
          {!lagna.isJaimini && (
            <>
              <View style={styles.detailItem}>
                <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>Degree</Text>
                <Text style={[styles.detailValue, { color: colors.text }]}>{lagna.degree.toFixed(2)}°</Text>
              </View>
              <View style={styles.detailItemFull}>
                <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>Nakshatra</Text>
                <Text style={[styles.detailValue, { color: colors.text }]}>{lagna.nakshatra} - Pada {lagna.pada}</Text>
              </View>
            </>
          )}
        </View>
      </LinearGradient>
    </View>
  );

  // Render Tab Content
  const renderTabContent = () => {
    if (activeTab === 'planets') {
      return planets.map((planet) => <PlanetCard key={planet.name} planet={planet} />);
    }

    if (activeTab === 'karakas') {
      if (loading) {
        return (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={[styles.loadingText, { color: colors.textSecondary }]}>Loading Karakas...</Text>
          </View>
        );
      }
      if (!karakas) {
        return <Text style={[styles.emptyText, { color: colors.textSecondary }]}>No Karaka data available</Text>;
      }
      return (
        <View style={styles.karakasGrid}>
          {Object.entries(karakas).map(([karaka, value]) => {
            let displayName = 'Unknown';
            if (typeof value === 'string') {
              displayName = value;
            } else if (value && typeof value === 'object') {
              displayName = value.planet || value.name || 'Unknown';
            }
            return (
              <View key={karaka} style={[styles.karakaCard, { backgroundColor: isDark ? 'rgba(249, 115, 22, 0.1)' : 'rgba(234, 88, 12, 0.08)', borderColor: isDark ? 'rgba(249, 115, 22, 0.3)' : colors.cardBorder }]}>
                <Text style={[styles.karakaName, { color: colors.textSecondary }]}>{karaka}</Text>
                <Text style={[styles.karakaPlanet, { color: colors.text }]}>{planetEmojis[displayName] || '⭐'} {displayName}</Text>
              </View>
            );
          })}
        </View>
      );
    }

    if (activeTab === 'lagnas') {
      if (lagnasLoading) {
        return (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={[styles.loadingText, { color: colors.textSecondary }]}>Loading Jaimini Lagnas...</Text>
          </View>
        );
      }
      return lagnas.map((lagna, index) => <LagnaCard key={index} lagna={lagna} />);
    }

    if (activeTab === 'special') {
      if (specialLoading) {
        return (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={[styles.loadingText, { color: colors.textSecondary }]}>Loading Special Points...</Text>
          </View>
        );
      }

      const specialCardBg = isDark ? 'rgba(236, 72, 153, 0.08)' : 'rgba(219, 39, 119, 0.08)';
      const specialCardBorder = isDark ? 'rgba(236, 72, 153, 0.2)' : colors.cardBorder;
      return (
        <View>
          {/* Yogi Points */}
          {yogiPoints && (
            <View style={styles.specialSection}>
              <Text style={[styles.specialSectionTitle, { color: colors.text }]}>Yogi Points</Text>
              {Object.entries(yogiPoints).map(([key, point]) => (
                <View key={key} style={[styles.specialCard, { backgroundColor: specialCardBg, borderColor: specialCardBorder }]}>
                  <Text style={[styles.specialPointName, { color: colors.text }]}>{key.replace('_', ' ').toUpperCase()}</Text>
                  <Text style={[styles.specialPointValue, { color: colors.primary }]}>
                    {point.sign_name} {point.degree?.toFixed(2)}°
                  </Text>
                  <Text style={[styles.specialPointLord, { color: colors.textSecondary }]}>Lord: {point.lord}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Bhrigu Bindu */}
          {sniperPoints?.bhrigu_bindu && !sniperPoints.bhrigu_bindu.error && (
            <View style={styles.specialSection}>
              <Text style={[styles.specialSectionTitle, { color: colors.text }]}>🎯 Bhrigu Bindu</Text>
              <View style={[styles.specialCard, { backgroundColor: specialCardBg, borderColor: specialCardBorder }]}>
                <Text style={[styles.specialPointName, { color: colors.text }]}>Destiny Point</Text>
                <Text style={[styles.specialPointValue, { color: colors.primary }]}>
                  {sniperPoints.bhrigu_bindu.formatted}
                </Text>
                <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                  {sniperPoints.bhrigu_bindu.significance}
                </Text>
              </View>
            </View>
          )}

          {/* Pushkara Navamsha */}
          {pushkaraData?.pushkara_planets && pushkaraData.pushkara_planets.length > 0 && (
            <View style={styles.specialSection}>
              <Text style={[styles.specialSectionTitle, { color: colors.text }]}>💎 Pushkara Navamsha</Text>
              {pushkaraData.pushkara_planets.map((data, index) => (
                <View key={index} style={[styles.specialCard, { backgroundColor: specialCardBg, borderColor: specialCardBorder }]}>
                  <Text style={[styles.specialPointName, { color: colors.text }]}>{data.planet}</Text>
                  <Text style={[styles.specialPointValue, { color: colors.primary }]}>
                    Navamsa {data.navamsa_no} • {data.degree_in_sign?.toFixed(2)}°
                  </Text>
                  <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                    {data.description} ({data.intensity})
                  </Text>
                </View>
              ))}
            </View>
          )}

          {!yogiPoints && !sniperPoints && !pushkaraData && (
            <Text style={[styles.emptyText, { color: colors.textSecondary }]}>No special points data available</Text>
          )}
        </View>
      );
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} />
      <LinearGradient colors={screenGradient} style={styles.gradient}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={colors.primary} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]}>Planetary Positions</Text>
            <View style={styles.placeholder} />
          </View>

          {/* Tab Bar */}
          <View style={[styles.tabBar, { borderBottomColor: colors.cardBorder }]}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabScrollContent}>
              <TabButton label="Planets" emoji="🪐" value="planets" active={activeTab === 'planets'} />
              <TabButton label="Karakas" emoji="🔱" value="karakas" active={activeTab === 'karakas'} />
              <TabButton label="Lagnas" emoji="🎯" value="lagnas" active={activeTab === 'lagnas'} />
              <TabButton label="Special" emoji="✨" value="special" active={activeTab === 'special'} />
            </ScrollView>
          </View>

          {/* Tab Content */}
          <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
            {renderTabContent()}
            <View style={{ height: 20 }} />
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
    backgroundColor: 'transparent',
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
  },
  placeholder: { width: 40 },
  
  // Tab Bar Styles
  tabBar: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  tabScrollContent: {
    gap: 8,
  },
  tabButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    gap: 6,
  },
  tabButtonActive: {},
  tabEmoji: {
    fontSize: 16,
  },
  tabEmojiActive: {
    fontSize: 16,
  },
  tabLabel: {
    fontSize: 14,
    fontWeight: '600',
  },
  tabLabelActive: {},

  scrollView: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 16,
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
    flex: 1,
  },
  planetEmoji: {
    fontSize: 32,
  },
  planetName: {
    fontSize: 18,
    fontWeight: '700',
  },
  retrogradeTag: {
    fontSize: 10,
    fontWeight: '600',
    marginTop: 2,
  },
  lagnaDescription: {
    fontSize: 11,
    marginTop: 2,
  },
  houseTag: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  houseText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#ffffff',
  },
  divider: {
    height: 1,
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
    fontWeight: '600',
  },
  detailValue: {
    fontSize: 14,
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
  
  // Karakas Grid
  karakasGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  karakaCard: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    minWidth: '48%',
    flexGrow: 1,
  },
  karakaName: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
  },
  karakaPlanet: {
    fontSize: 16,
    fontWeight: '700',
  },

  // Loading & Empty States
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
  },
  emptyText: {
    textAlign: 'center',
    fontSize: 14,
    paddingVertical: 40,
  },
  comingSoonContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 80,
  },
  comingSoonEmoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  comingSoonText: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 8,
  },
  comingSoonSubtext: {
    fontSize: 14,
    textAlign: 'center',
    paddingHorizontal: 40,
  },

  // Special Points Styles
  specialSection: {
    marginBottom: 24,
  },
  specialSectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
  },
  specialCard: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
  },
  specialPointName: {
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 4,
    textTransform: 'capitalize',
  },
  specialPointValue: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 4,
  },
  specialPointLord: {
    fontSize: 12,
  },
  specialPointDesc: {
    fontSize: 11,
    marginTop: 4,
    lineHeight: 16,
  },
});

export default PlanetaryPositionsScreen;
