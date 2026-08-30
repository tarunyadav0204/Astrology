import React from 'react';
import { View, Text, StyleSheet, StatusBar, TouchableOpacity, ActivityIndicator, Platform } from 'react-native';
import { ScrollView as GHScrollView } from 'react-native-gesture-handler';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { DISPLAY_FONT_FAMILY } from '../../theme/tokens';

const PlanetaryPositionsScreen = ({ navigation, route }) => {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const { chartData, birthData } = route.params || {};
  React.useEffect(() => {
    if (!birthData?.name) {
      navigation.replace('BirthProfileIntro', { returnTo: 'PlanetaryPositions' });
    }
  }, [birthData, navigation]);

  const [activeTab, setActiveTab] = React.useState('planets');
  const [karakas, setKarakas] = React.useState(null);
  const [jaiminiLagnas, setJaiminiLagnas] = React.useState(null);
  const [yogiPoints, setYogiPoints] = React.useState(null);
  const [sniperPoints, setSniperPoints] = React.useState(null);
  const [pushkaraData, setPushkaraData] = React.useState(null);
  const [mudakkuData, setMudakkuData] = React.useState(null);
  const [gandantaData, setGandantaData] = React.useState(null);
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
      const [yogiResponse, sniperResponse, pushkaraResponse, mudakkuResponse, gandantaResponse] = await Promise.all([
        chartAPI.calculateYogiPoints(birthData),
        chartAPI.calculateSniperPoints(chartData),
        chartAPI.calculatePushkaraNavamsha(chartData, d9Chart),
        chartAPI.calculateMudakkuAnalysis(chartData),
        chartAPI.calculateGandantaAnalysis(chartData),
      ]);
      setYogiPoints(yogiResponse.data.yogi_points);
      setSniperPoints(sniperResponse.data.sniper_points);
      setPushkaraData(pushkaraResponse.data.pushkara_analysis);
      setMudakkuData(mudakkuResponse?.data?.mudakku_analysis);
      setGandantaData(gandantaResponse?.data?.gandanta_analysis);
    } catch (error) {
      console.error('Error loading special points:', error);
    } finally {
      setSpecialLoading(false);
      setSpecialLoaded(true);
    }
  };

  if (!birthData?.name) return null;

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

  const planetsPayload = chartData && typeof chartData === 'object' ? chartData.planets : null;

  const planets = planetsPayload && typeof planetsPayload === 'object'
    ? planetOrder
        .filter((name) => planetsPayload[name])
        .map((name) => ({
          name,
          ...planetsPayload[name],
          nakshatra: getNakshatra(planetsPayload[name].longitude),
          pada: getNakshatraPada(planetsPayload[name].longitude),
        }))
    : [];

  const ascendantLon = (() => {
    const asc = chartData?.ascendant;
    if (typeof asc === 'number' && !Number.isNaN(asc)) return asc;
    if (asc != null && asc !== '') {
      const n = parseFloat(String(asc));
      if (!Number.isNaN(n)) return n;
    }
    return null;
  })();

  // Lagnas data (needs ascendant + chart payload)
  const lagnas = [];
  if (ascendantLon != null) {
    lagnas.push({
      name: 'Ascendant (Lagna)',
      longitude: ascendantLon,
      sign: Math.floor(ascendantLon / 30),
      degree: ascendantLon % 30,
      house: 1,
      nakshatra: getNakshatra(ascendantLon),
      pada: getNakshatraPada(ascendantLon),
      description: 'Self, Personality, Physical Body',
    });
  }

  if (planetsPayload?.InduLagna) {
    lagnas.push({
      name: 'Indu Lagna',
      ...planetsPayload.InduLagna,
      nakshatra: getNakshatra(planetsPayload.InduLagna.longitude),
      pada: getNakshatraPada(planetsPayload.InduLagna.longitude),
      description: 'Wealth Indicator',
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
          house:
            ascendantLon != null
              ? ((signId - Math.floor(ascendantLon / 30) + 12) % 12) + 1
              : 1,
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
        {
          backgroundColor: active ? colors.selectionSurface : colors.surfaceRaised,
          borderColor: active ? colors.selectionBorder : colors.cardBorder,
        },
        active && styles.tabButtonActive,
      ]}
      onPress={() => setActiveTab(value)}
    >
      <Text style={[styles.tabEmoji, active && styles.tabEmojiActive]}>{emoji}</Text>
      <Text style={[styles.tabLabel, { color: active ? colors.selectionText : colors.textSecondary }, active && styles.tabLabelActive]}>{label}</Text>
    </TouchableOpacity>
  );

  // Planet Card Component
  const PlanetCard = ({ planet }) => (
    <View style={[styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
        <View style={styles.cardHeader}>
          <View style={styles.planetInfo}>
            <View style={[styles.planetSeal, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
              <Text style={[styles.planetEmoji, { color: colors.selectionText }]}>{planetEmojis[planet.name]}</Text>
            </View>
            <View>
              <Text style={[styles.planetName, { color: colors.text }]}>{planet.name}</Text>
              {planet.retrograde && <Text style={[styles.retrogradeTag, { color: colors.error }]}>{t('premiumUi.planetaryPositions.retrograde', 'Retrograde')}</Text>}
            </View>
          </View>
          <View style={[styles.houseTag, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
            <Text style={[styles.houseText, { color: colors.selectionText }]}>{t('premiumUi.planetaryPositions.house', 'House {{number}}', { number: planet.house })}</Text>
          </View>
        </View>
        <View style={[styles.divider, { backgroundColor: colors.cardBorder }]} />
        <View style={styles.detailsGrid}>
          <View style={styles.detailItem}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.rashi', 'Rashi')}</Text>
            <View style={styles.rashiContainer}>
              <Text style={styles.rashiIcon}>{rashiIcons[planet.sign]}</Text>
              <Text style={[styles.detailValue, { color: colors.text }]}>{rashiNames[planet.sign]}</Text>
            </View>
          </View>
          <View style={styles.detailItem}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.degree', 'Degree')}</Text>
            <Text style={[styles.detailValue, { color: colors.text }]}>{planet.degree.toFixed(2)}°</Text>
          </View>
          <View style={styles.detailItemFull}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.nakshatra', 'Nakshatra')}</Text>
            <Text style={[styles.detailValue, styles.detailValueWide, { color: colors.text }]}>{planet.nakshatra} · {t('premiumUi.planetaryPositions.pada', 'Pada {{number}}', { number: planet.pada })}</Text>
          </View>
        </View>
    </View>
  );

  // Lagna Card Component
  const LagnaCard = ({ lagna }) => (
    <View style={[styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
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
          <View style={[styles.houseTag, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
            <Text style={[styles.houseText, { color: colors.selectionText }]}>{t('premiumUi.planetaryPositions.house', 'House {{number}}', { number: lagna.house })}</Text>
          </View>
        </View>
        <View style={[styles.divider, { backgroundColor: colors.cardBorder }]} />
        <View style={styles.detailsGrid}>
          <View style={styles.detailItem}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.rashi', 'Rashi')}</Text>
            <View style={styles.rashiContainer}>
              <Text style={styles.rashiIcon}>{rashiIcons[lagna.sign]}</Text>
              <Text style={[styles.detailValue, { color: colors.text }]}>{rashiNames[lagna.sign]}</Text>
            </View>
          </View>
          {!lagna.isJaimini && (
            <>
              <View style={styles.detailItem}>
                <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.degree', 'Degree')}</Text>
                <Text style={[styles.detailValue, { color: colors.text }]}>{lagna.degree.toFixed(2)}°</Text>
              </View>
              <View style={styles.detailItemFull}>
                <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.nakshatra', 'Nakshatra')}</Text>
                <Text style={[styles.detailValue, styles.detailValueWide, { color: colors.text }]}>{lagna.nakshatra} · {t('premiumUi.planetaryPositions.pada', 'Pada {{number}}', { number: lagna.pada })}</Text>
              </View>
            </>
          )}
        </View>
    </View>
  );

  // Render Tab Content
  const renderTabContent = () => {
    if (activeTab === 'planets') {
      if (!planetsPayload || planets.length === 0) {
        return (
          <View style={styles.loadingContainer}>
            <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
              Chart data is still loading or unavailable. Open your chart first, then try again.
            </Text>
          </View>
        );
      }
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
              <View key={karaka} style={[styles.karakaCard, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
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

      const specialCardBg = colors.surfaceRaised;
      const specialCardBorder = colors.cardBorder;
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

          {/* Mudakku / Modakku */}
          {mudakkuData && (
            <View style={styles.specialSection}>
              <Text style={[styles.specialSectionTitle, { color: colors.text }]}>🧩 Mudakku / Modakku</Text>
              <View style={[styles.specialCard, { backgroundColor: specialCardBg, borderColor: specialCardBorder }]}>
                <Text style={[styles.specialPointName, { color: colors.text }]}>
                  {mudakkuData.sun_nakshatra?.name || mudakkuData.method?.count_from || 'Sun Nakshatra'}
                </Text>
                <Text style={[styles.specialPointValue, { color: colors.primary }]}>
                  Count to Mula: {mudakkuData.count_to_mula}
                </Text>
                <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                  Mudakku Nakshatra: {mudakkuData.mudakku_nakshatra?.name}
                  {'\n'}
                  Mudakku Rashi: {mudakkuData.mudakku_rashi} • Lord: {mudakkuData.mudakku_rashi_lord}
                  {'\n'}
                  {mudakkuData.is_split_nakshatra ? 'Split nakshatra rule applied.' : 'Single sign landing.'}
                </Text>
              </View>
            </View>
          )}

          {/* Gandanta */}
          {gandantaData && (
            <View style={styles.specialSection}>
              <Text style={[styles.specialSectionTitle, { color: colors.text }]}>🧶 Gandamoola (Gandanta)</Text>
              <View style={[styles.specialCard, { backgroundColor: specialCardBg, borderColor: specialCardBorder }]}>
                <Text style={[styles.specialPointName, { color: colors.text }]}>
                  {gandantaData.lagna_gandanta?.is_gandanta
                    ? `Lagna: ${gandantaData.lagna_gandanta?.gandanta_info?.gandanta_name || 'Gandanta'}`
                    : gandantaData.moon_gandanta?.is_gandanta
                      ? `Moon: ${gandantaData.moon_gandanta?.gandanta_info?.gandanta_name || 'Gandanta'}`
                      : 'Chart Gandanta'}
                </Text>
                <Text style={[styles.specialPointValue, { color: colors.primary }]}>
                  Planets in Gandanta: {gandantaData.planets_in_gandanta?.length || 0}
                </Text>
                <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                  {gandantaData.lagna_gandanta?.is_gandanta ? `Lagna is in ${gandantaData.lagna_gandanta?.gandanta_info?.gandanta_name}.` : 'Lagna is not in Gandanta.'}
                  {'\n'}
                  {gandantaData.moon_gandanta?.is_gandanta ? `Moon is in ${gandantaData.moon_gandanta?.gandanta_info?.gandanta_name}.` : 'Moon is not in Gandanta.'}
                  {gandantaData.planets_in_gandanta?.length
                    ? `\n${gandantaData.planets_in_gandanta.map((item) => `${item.planet} (${item.gandanta_info?.gandanta_name || 'Gandanta'})`).join(', ')}`
                    : '\nNo planets are in Gandanta.'}
                </Text>
              </View>
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

          {!yogiPoints && !sniperPoints && !pushkaraData && !mudakkuData && !gandantaData && (
            <Text style={[styles.emptyText, { color: colors.textSecondary }]}>No special points data available</Text>
          )}
        </View>
      );
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} translucent={false} />
        <SafeAreaView edges={['top']} style={[styles.safeArea, { backgroundColor: colors.headerSurface }]}>
          <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine }]}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.backButton, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}>
              <Ionicons name="arrow-back" size={22} color={colors.textInverse} />
            </TouchableOpacity>
            <View style={styles.headerCopy}>
              <Text style={[styles.headerTitle, { color: colors.textInverse }]}>{t('premiumUi.planetaryPositions.title', 'Planetary Positions')}</Text>
              <Text style={[styles.headerSubtitle, { color: colors.textInverseMuted }]} numberOfLines={1}>{birthData?.name || t('premiumUi.planetaryPositions.selectedChart', 'Selected chart')}</Text>
            </View>
            <View style={styles.placeholder} />
          </View>
        </SafeAreaView>

          <View style={[styles.tabBar, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}>
            <GHScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabScrollContent}>
              <TabButton label={t('premiumUi.planetaryPositions.tabs.planets', 'Planets')} emoji="🪐" value="planets" active={activeTab === 'planets'} />
              <TabButton label={t('premiumUi.planetaryPositions.tabs.karakas', 'Karakas')} emoji="🔱" value="karakas" active={activeTab === 'karakas'} />
              <TabButton label={t('premiumUi.planetaryPositions.tabs.lagnas', 'Lagnas')} emoji="🎯" value="lagnas" active={activeTab === 'lagnas'} />
              <TabButton label={t('premiumUi.planetaryPositions.tabs.special', 'Special')} emoji="✨" value="special" active={activeTab === 'special'} />
            </GHScrollView>
          </View>

          <GHScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
            <View style={[styles.hero, { backgroundColor: colors.surfaceInverse, borderColor: colors.cosmicLine }]}>
              <View pointerEvents="none" style={styles.heroLinework}>
                <View style={[styles.heroOrbit, styles.heroOrbitLarge, { borderColor: colors.onSurfaceInverseMuted }]} />
                <View style={[styles.heroOrbit, styles.heroOrbitSmall, { borderColor: colors.onSurfaceInverseMuted }]} />
              </View>
              <Text style={[styles.heroEyebrow, { color: colors.onSurfaceInverseMuted }]}>{t('premiumUi.planetaryPositions.skyMap', 'YOUR CELESTIAL MAP')}</Text>
              <Text style={[styles.heroTitle, { color: colors.onSurfaceInverse }]}>{t('premiumUi.planetaryPositions.heroTitle', 'The sky at your birth.')}</Text>
              <Text style={[styles.heroBody, { color: colors.onSurfaceInverseMuted }]}>{t('premiumUi.planetaryPositions.heroBody', 'Read each planet through its sign, house, exact degree and nakshatra placement.')}</Text>
              <View style={[styles.heroMeta, { borderTopColor: colors.onSurfaceInverseMuted }]}>
                <Text style={[styles.heroMetaText, { color: colors.onSurfaceInverse }]}>{t('premiumUi.planetaryPositions.positionCount', '{{count}} planetary positions', { count: planets.length })}</Text>
                <Text style={[styles.heroMetaText, { color: colors.onSurfaceInverseMuted }]}>{t('premiumUi.planetaryPositions.sidereal', 'Sidereal · Lahiri')}</Text>
              </View>
            </View>
            {renderTabContent()}
            <View style={{ height: 32 }} />
          </GHScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: {},
  header: {
    minHeight: 72,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 18,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerCopy: { flex: 1, alignItems: 'center', paddingHorizontal: 10 },
  headerTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 21, lineHeight: 25 },
  headerSubtitle: { fontSize: 11, lineHeight: 15, marginTop: 2, fontWeight: '600' },
  placeholder: { width: 40 },
  hero: { minHeight: 190, marginBottom: 16, padding: 22, borderWidth: 1, borderRadius: 26, overflow: 'hidden' },
  heroLinework: { ...StyleSheet.absoluteFillObject, opacity: 0.25 },
  heroOrbit: { position: 'absolute', borderWidth: 1 },
  heroOrbitLarge: { width: 190, height: 190, borderRadius: 95, right: -70, top: -92 },
  heroOrbitSmall: { width: 116, height: 116, borderRadius: 58, right: -18, top: -48 },
  heroEyebrow: { fontSize: 10, lineHeight: 14, fontWeight: '800', letterSpacing: 1.5, marginBottom: 10 },
  heroTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 31, lineHeight: 35, maxWidth: '82%' },
  heroBody: { fontSize: 13, lineHeight: 19, fontWeight: '500', maxWidth: '88%', marginTop: 10 },
  heroMeta: { marginTop: 18, paddingTop: 12, borderTopWidth: StyleSheet.hairlineWidth, flexDirection: 'row', justifyContent: 'space-between', gap: 10 },
  heroMetaText: { fontSize: 10, lineHeight: 14, fontWeight: '700', letterSpacing: 0.4 },
  tabBar: {
    marginHorizontal: 18,
    marginTop: 14,
    padding: 5,
    borderWidth: 1,
    borderRadius: 18,
  },
  tabScrollContent: {
    gap: 8,
  },
  tabButton: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 42,
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 14,
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
    fontSize: 12,
    fontWeight: '800',
  },
  tabLabelActive: {},

  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 18,
    paddingTop: 16,
  },
  card: {
    marginBottom: 11,
    borderRadius: 20,
    borderWidth: 1,
    padding: 15,
    overflow: 'hidden',
    ...Platform.select({
      ios: { shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.08, shadowRadius: 12 },
      android: { elevation: 1 },
      default: { boxShadow: '0 5px 18px rgba(0,0,0,0.06)' },
    }),
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
  planetSeal: { width: 44, height: 44, borderRadius: 15, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  planetEmoji: { fontSize: 24 },
  planetName: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 21, lineHeight: 25 },
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
    paddingVertical: 7,
    borderRadius: 999,
    borderWidth: 1,
  },
  houseText: {
    fontSize: 12,
    fontWeight: '700',
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
    textAlign: 'right',
  },
  detailValueWide: { flex: 1, marginLeft: 18 },
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
