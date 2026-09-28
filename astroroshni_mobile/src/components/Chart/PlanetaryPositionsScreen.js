import React from 'react';
import { View, Text, StyleSheet, StatusBar, TouchableOpacity, ActivityIndicator, Linking, Modal, Pressable, Platform, useWindowDimensions } from 'react-native';
import { ScrollView as GHScrollView } from 'react-native-gesture-handler';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { DISPLAY_FONT_FAMILY } from '../../theme/tokens';

const isSpecialPoint = (value) => (
  Boolean(value)
  && typeof value === 'object'
  && !Array.isArray(value)
  && typeof value.sign_name === 'string'
);

const formatPointDegrees = (value) => {
  const degree = Number(value);
  return Number.isFinite(degree) ? `${degree.toFixed(2)}°` : '';
};

const PlanetaryPositionsScreen = ({ navigation, route }) => {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const { width: windowWidth } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const { chartData, birthData, conditionChartData } = route.params || {};
  const isTablet = windowWidth >= 768;
  const planetDockRef = React.useRef(null);
  const nakshatraDockRef = React.useRef(null);
  const jaiminiRequestRef = React.useRef(0);
  const specialPointsRequestRef = React.useRef(0);
  const natalPromiseRequestRef = React.useRef(0);
  const lastChartKeyRef = React.useRef(null);
  const chartKey = `${birthData?.id || birthData?.name || ''}|${birthData?.date || ''}|${birthData?.time || ''}`;
  React.useEffect(() => {
    if (!birthData?.name) {
      navigation.replace('BirthProfileIntro', { returnTo: 'PlanetaryPositions' });
    }
  }, [birthData, navigation]);

  const [activeTab, setActiveTab] = React.useState('planets');
  const [karakas, setKarakas] = React.useState(null);
  const [planetaryDignities, setPlanetaryDignities] = React.useState({});
  const [canonicalPositions, setCanonicalPositions] = React.useState(null);
  const [professionalJaimini, setProfessionalJaimini] = React.useState(null);
  const [jaiminiLoading, setJaiminiLoading] = React.useState(false);
  const [jaiminiLoaded, setJaiminiLoaded] = React.useState(false);
  const [jaiminiError, setJaiminiError] = React.useState(null);
  const [jaiminiScheme, setJaiminiScheme] = React.useState('seven');
  const [natalPromise, setNatalPromise] = React.useState(null);
  const [natalPromiseLoading, setNatalPromiseLoading] = React.useState(false);
  const [natalPromiseLoaded, setNatalPromiseLoaded] = React.useState(false);
  const [natalPromiseError, setNatalPromiseError] = React.useState(null);
  const [selectedPromiseHouse, setSelectedPromiseHouse] = React.useState(1);
  const [showPromiseEvidence, setShowPromiseEvidence] = React.useState(false);
  const [promiseAreaPickerOpen, setPromiseAreaPickerOpen] = React.useState(false);
  const [selectedPromiseSubject, setSelectedPromiseSubject] = React.useState('all');
  const [promiseSubjectPickerOpen, setPromiseSubjectPickerOpen] = React.useState(false);
  const [yogiPoints, setYogiPoints] = React.useState(null);
  const [sniperPoints, setSniperPoints] = React.useState(null);
  const [pushkaraData, setPushkaraData] = React.useState(null);
  const [mudakkuData, setMudakkuData] = React.useState(null);
  const [gandantaData, setGandantaData] = React.useState(null);
  const [professionalSpecialPoints, setProfessionalSpecialPoints] = React.useState(null);
  const [professionalSpecialLoaded, setProfessionalSpecialLoaded] = React.useState(false);
  const [professionalSpecialError, setProfessionalSpecialError] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [specialLoading, setSpecialLoading] = React.useState(false);
  const [specialLoaded, setSpecialLoaded] = React.useState(false);
  const [specialFailures, setSpecialFailures] = React.useState([]);
  const [expandedPlanets, setExpandedPlanets] = React.useState({});
  const [expandedHouses, setExpandedHouses] = React.useState({});
  const [expandedLagnas, setExpandedLagnas] = React.useState({});
  const [selectedPlanetName, setSelectedPlanetName] = React.useState(route.params?.selectedPlanetName || null);
  const [selectedHouseNumber, setSelectedHouseNumber] = React.useState(route.params?.selectedHouseNumber || null);
  const [selectedNakshatraSubject, setSelectedNakshatraSubject] = React.useState(null);

  React.useEffect(() => {
    loadInitialPlanetData();
  }, [chartData, conditionChartData, birthData]);

  React.useEffect(() => {
    if (activeTab === 'jaimini' && !jaiminiLoaded) {
      loadProfessionalJaimini();
    }
  }, [activeTab, jaiminiLoaded]);

  React.useEffect(() => {
    if (activeTab === 'promise' && !natalPromiseLoaded) loadNatalPromise();
  }, [activeTab, natalPromiseLoaded]);

  React.useEffect(() => {
    if (activeTab === 'special' && !specialLoaded) {
      loadSpecialPoints();
    }
  }, [activeTab, specialLoaded]);

  React.useEffect(() => {
    if (['lagnas', 'nakshatras'].includes(activeTab) && !professionalSpecialLoaded) {
      loadProfessionalSpecialPoints();
    }
  }, [activeTab, professionalSpecialLoaded]);

  const loadInitialPlanetData = async () => {
    setLoading(true);
    setCanonicalPositions(null);
    setPlanetaryDignities({});
    try {
      const { chartAPI } = require('../../services/api');
      const [karakaResult, dignityResult] = await Promise.allSettled([
        chartAPI.calculateCharaKarakas(chartData, birthData),
        chartAPI.calculatePlanetaryDignities(chartData, conditionChartData || chartData, birthData),
      ]);
      if (karakaResult.status === 'fulfilled') {
        const response = karakaResult.value;
        setKarakas(response.data.karakas || response.data.chara_karakas || response.data);
      } else {
        console.error('Error loading karakas:', karakaResult.reason);
      }
      if (dignityResult.status === 'fulfilled') {
        setPlanetaryDignities(dignityResult.value?.data?.dignities || {});
        setCanonicalPositions(dignityResult.value?.data?.positions || null);
      } else {
        console.error('Error loading canonical positions:', dignityResult.reason);
      }
    } catch (error) {
      console.error('Error loading planet details:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadProfessionalJaimini = async () => {
    const requestId = ++jaiminiRequestRef.current;
    setJaiminiLoading(true);
    setJaiminiError(null);
    try {
      const { chartAPI } = require('../../services/api');
      const d9Chart = route.params?.d9Chart || {};
      const response = await chartAPI.calculateProfessionalJaimini(chartData, d9Chart);
      const payload = response?.data?.professional_jaimini;
      if (!payload) throw new Error('Professional Jaimini response is empty');
      if (requestId === jaiminiRequestRef.current) setProfessionalJaimini(payload);
    } catch (error) {
      console.error('Error loading professional Jaimini worksheet:', error);
      if (requestId === jaiminiRequestRef.current) {
        setJaiminiError(error?.response?.data?.detail?.message || error?.response?.data?.detail || error.message);
      }
    } finally {
      if (requestId === jaiminiRequestRef.current) {
        setJaiminiLoading(false);
        setJaiminiLoaded(true);
      }
    }
  };

  const loadNatalPromise = async () => {
    const requestId = ++natalPromiseRequestRef.current;
    setNatalPromiseLoading(true);
    setNatalPromiseError(null);
    try {
      const { chartAPI } = require('../../services/api');
      const response = await chartAPI.calculateClassicalReading(chartData, birthData);
      const payload = response?.data?.classical_reading;
      if (!payload?.areas?.length) throw new Error('Classical reading response is empty');
      if (requestId === natalPromiseRequestRef.current) {
        setNatalPromise(payload);
        setSelectedPromiseHouse((current) => payload.areas.some((row) => row.house === current) ? current : payload.areas[0].house);
      }
    } catch (error) {
      console.error('Error loading classical natal promise:', error);
      if (requestId === natalPromiseRequestRef.current) {
        setNatalPromiseError(error?.response?.data?.detail?.message || error?.response?.data?.detail || error.message);
      }
    } finally {
      if (requestId === natalPromiseRequestRef.current) {
        setNatalPromiseLoading(false);
        setNatalPromiseLoaded(true);
      }
    }
  };

  const loadProfessionalSpecialPoints = async () => {
    const requestId = ++specialPointsRequestRef.current;
    setProfessionalSpecialError(null);
    try {
      const { chartAPI } = require('../../services/api');
      const d9Chart = route.params?.d9Chart || {};
      const response = await chartAPI.calculateProfessionalSpecialPoints(chartData, birthData, d9Chart);
      if (requestId === specialPointsRequestRef.current) {
        setProfessionalSpecialPoints(response?.data?.professional_special_points || null);
      }
    } catch (error) {
      console.error('Error loading classical special points:', error);
      if (requestId === specialPointsRequestRef.current) {
        setProfessionalSpecialError(error?.response?.data?.detail?.message || error?.response?.data?.detail || error.message);
      }
    } finally {
      if (requestId === specialPointsRequestRef.current) setProfessionalSpecialLoaded(true);
    }
  };

  const loadSpecialPoints = async () => {
    setSpecialLoading(true);
    setSpecialFailures([]);
    try {
      const { chartAPI } = require('../../services/api');
      const d9Chart = route.params?.d9Chart || {};
      const results = await Promise.allSettled([
        chartAPI.calculateYogiPoints(birthData),
        chartAPI.calculateSniperPoints(chartData),
        chartAPI.calculatePushkaraNavamsha(chartData, d9Chart),
        chartAPI.calculateMudakkuAnalysis(chartData),
        chartAPI.calculateGandantaAnalysis(chartData),
        professionalSpecialPoints
          ? Promise.resolve({ data: { professional_special_points: professionalSpecialPoints } })
          : chartAPI.calculateProfessionalSpecialPoints(chartData, birthData, d9Chart),
      ]);
      const [yogiResult, sniperResult, pushkaraResult, mudakkuResult, gandantaResult, professionalResult] = results;
      const sourceKeys = ['lunarConditions', 'sensitivePoints', 'fortifyingPlacements', 'mudakku', 'gandanta', 'classicalPoints'];
      const payloads = [
        yogiResult.status === 'fulfilled' ? yogiResult.value?.data?.yogi_points : null,
        sniperResult.status === 'fulfilled' ? sniperResult.value?.data?.sniper_points : null,
        pushkaraResult.status === 'fulfilled' ? pushkaraResult.value?.data?.pushkara_analysis : null,
        mudakkuResult.status === 'fulfilled' ? mudakkuResult.value?.data?.mudakku_analysis : null,
        gandantaResult.status === 'fulfilled' ? gandantaResult.value?.data?.gandanta_analysis : null,
        professionalResult.status === 'fulfilled' ? professionalResult.value?.data?.professional_special_points : null,
      ];
      setYogiPoints(payloads[0] || null);
      setSniperPoints(payloads[1] || null);
      setPushkaraData(payloads[2] || null);
      setMudakkuData(payloads[3] || null);
      setGandantaData(payloads[4] || null);
      setProfessionalSpecialPoints(payloads[5] || null);
      setProfessionalSpecialLoaded(true);
      const failures = [];
      results.forEach((result, index) => {
        if (result.status === 'rejected' || !payloads[index]) {
          console.error(`Error loading special point source ${index + 1}:`, result.reason);
          failures.push(sourceKeys[index]);
        }
      });
      setSpecialFailures(failures);
    } catch (error) {
      console.error('Error loading special points:', error);
      setSpecialFailures(['lunarConditions', 'sensitivePoints', 'fortifyingPlacements', 'mudakku', 'gandanta', 'classicalPoints']);
    } finally {
      setSpecialLoading(false);
      setSpecialLoaded(true);
    }
  };

  const planetRows = React.useMemo(
    () => (canonicalPositions?.planets || []).map((row) => ({
      ...row,
      signName: row.sign_name,
      signAbbr: row.sign_abbr,
      lord: row.sign_lord,
      lordAbbr: row.sign_lord_abbr,
      signLordRelationship: row.sign_lord_relationship,
      nakLord: row.nakshatra_lord,
      nakLordRelationship: row.nakshatra_lord_relationship,
      retro: row.retrograde,
      neechaBhanga: row.neecha_bhanga,
      combustion: row.combustion ? {
        applicable: row.combustion.applicable !== false,
        isCombust: row.combustion.is_combust,
        distance: row.combustion.angular_distance,
        threshold: row.combustion.threshold,
        motion: row.combustion.motion,
      } : null,
    })),
    [canonicalPositions],
  );
  const houseRows = React.useMemo(
    () => (canonicalPositions?.houses || []).map((row) => ({
      ...row,
      signName: row.sign_name,
      signAbbr: row.sign_abbr,
      lordAbbr: row.lord_abbr,
      lordHouse: row.lord_house ?? '—',
      dignity: row.lord_dignity,
      lordCombust: row.lord_combust,
      occupantList: row.occupants || [],
    })),
    [canonicalPositions],
  );
  const nakshatraPlacements = React.useMemo(
    () => canonicalPositions?.nakshatra_placements || [],
    [canonicalPositions],
  );

  React.useEffect(() => {
    if (lastChartKeyRef.current === null) {
      lastChartKeyRef.current = chartKey;
      return;
    }
    if (lastChartKeyRef.current !== chartKey) {
      lastChartKeyRef.current = chartKey;
      jaiminiRequestRef.current += 1;
      specialPointsRequestRef.current += 1;
      natalPromiseRequestRef.current += 1;
      setSelectedPlanetName(null);
      setExpandedPlanets({});
      setSelectedHouseNumber(null);
      setExpandedHouses({});
      setExpandedLagnas({});
      setSelectedNakshatraSubject(null);
      setProfessionalJaimini(null);
      setJaiminiLoaded(false);
      setJaiminiError(null);
      setJaiminiScheme('seven');
      setNatalPromise(null);
      setNatalPromiseLoaded(false);
      setNatalPromiseError(null);
      setSelectedPromiseHouse(1);
      setShowPromiseEvidence(false);
      setPromiseAreaPickerOpen(false);
      setSelectedPromiseSubject('all');
      setPromiseSubjectPickerOpen(false);
      setYogiPoints(null);
      setSniperPoints(null);
      setPushkaraData(null);
      setMudakkuData(null);
      setGandantaData(null);
      setProfessionalSpecialPoints(null);
      setProfessionalSpecialLoaded(false);
      setProfessionalSpecialError(null);
      setSpecialFailures([]);
      setSpecialLoaded(false);
    }
  }, [chartKey]);

  React.useEffect(() => {
    const available = (canonicalPositions?.planets || [])
      .map((row) => row.name)
      .filter((name) => ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'].includes(name));
    if (!available.length) return;
    if (!selectedPlanetName || available.includes(selectedPlanetName)) return;
    setSelectedPlanetName(null);
  }, [canonicalPositions, selectedPlanetName]);

  React.useEffect(() => {
    if (!selectedNakshatraSubject) return;
    if (!nakshatraPlacements.some((row) => row.name === selectedNakshatraSubject)) {
      setSelectedNakshatraSubject(null);
    }
  }, [nakshatraPlacements, selectedNakshatraSubject]);

  const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                      'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

  const rashiIcons = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];

  const planetEmojis = {
    'Lagna': '⬆', 'Sun': '☉', 'Moon': '☽', 'Mars': '♂', 'Mercury': '☿',
    'Jupiter': '♃', 'Venus': '♀', 'Saturn': '♄',
    'Rahu': '☊', 'Ketu': '☋', 'Gulika': '🌑', 'Mandi': '⚫',
    'Indu Lagna': '🌙', 'Bhava Lagna': '🏠', 'Hora Lagna': '💰',
    'Ascendant (Lagna)': '⬆️', 'Arudha Lagna': '🎭', 'Upapada Lagna': '💑',
    'Karkamsa Lagna': '🎯', 'Swamsa Lagna': '🕉️', 'Ghatika Lagna': '👑',
    'Darapada': '🤝'
  };

  const planetsPayload = chartData && typeof chartData === 'object' ? chartData.planets : null;
  const planets = planetRows.filter((row) => (
    ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'].includes(row.name)
  )).map((row) => ({
    name: row.name,
    sign: row.sign,
    degree: row.degree,
    longitude: row.longitude,
    house: row.house,
    retrograde: row.retrograde,
    nakshatra: row.nakshatra,
    pada: row.pada,
  }));
  const selectedPlanet = selectedPlanetName
    ? planets.find((planet) => planet.name === selectedPlanetName) || null
    : null;
  const selectedHouse = selectedHouseNumber
    ? houseRows.find((row) => row.house === Number(selectedHouseNumber)) || null
    : null;
  const planetDockOptionCount = planets.length + 1;
  const dockItemWidth = isTablet
    ? Math.max(68, (windowWidth - 16 - (Math.max(planetDockOptionCount - 1, 0) * 3)) / Math.max(planetDockOptionCount, 1))
    : 76;
  const nakshatraDockOptionCount = nakshatraPlacements.length + 1;
  const nakshatraDockItemWidth = isTablet
    ? Math.max(62, (windowWidth - 16 - (Math.max(nakshatraDockOptionCount - 1, 0) * 3)) / Math.max(nakshatraDockOptionCount, 1))
    : 76;

  React.useEffect(() => {
    if (isTablet || !planetDockRef.current) return;
    const planetIndex = planets.findIndex((planet) => planet.name === selectedPlanetName);
    const index = selectedPlanetName && planetIndex >= 0 ? planetIndex + 1 : 0;
    const x = Math.max(0, (index * dockItemWidth) - ((windowWidth - dockItemWidth) / 2));
    requestAnimationFrame(() => planetDockRef.current?.scrollTo?.({ x, animated: true }));
  }, [selectedPlanetName, isTablet, dockItemWidth, windowWidth, planets.length]);

  React.useEffect(() => {
    if (isTablet || !nakshatraDockRef.current) return;
    const placementIndex = nakshatraPlacements.findIndex((row) => row.name === selectedNakshatraSubject);
    const index = selectedNakshatraSubject && placementIndex >= 0 ? placementIndex + 1 : 0;
    const x = Math.max(0, (index * nakshatraDockItemWidth) - ((windowWidth - nakshatraDockItemWidth) / 2));
    requestAnimationFrame(() => nakshatraDockRef.current?.scrollTo?.({ x, animated: true }));
  }, [selectedNakshatraSubject, isTablet, nakshatraDockItemWidth, windowWidth, nakshatraPlacements.length]);

  React.useEffect(() => {
    if (!selectedPlanetName || !planets.some((planet) => planet.name === selectedPlanetName)) return;
    setExpandedPlanets((current) => (
      current[selectedPlanetName] === undefined
        ? { ...current, [selectedPlanetName]: true }
        : current
    ));
  }, [selectedPlanetName, planets.length]);

  React.useEffect(() => {
    if (!selectedHouseNumber || !houseRows.some((row) => row.house === Number(selectedHouseNumber))) return;
    setExpandedHouses((current) => (
      current[selectedHouseNumber] === undefined
        ? { ...current, [selectedHouseNumber]: true }
        : current
    ));
  }, [selectedHouseNumber, houseRows.length]);

  if (!birthData?.name) return null;

  const lagnas = professionalSpecialPoints?.special_lagnas?.points || [];

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

  const selectPlanet = (planetName) => {
    setSelectedPlanetName(planetName);
    setExpandedPlanets((current) => (
      planetName ? { ...current, [planetName]: true } : {}
    ));
    navigation.setParams?.({ selectedPlanetName: planetName || null });
  };

  const PlanetDock = () => (
    <View
      style={[
        styles.planetDock,
        {
          backgroundColor: colors.surfaceRaised,
          borderTopColor: colors.cardBorder,
          paddingBottom: Math.max(insets.bottom, 8),
        },
      ]}
      accessibilityLabel={t('premiumUi.planetaryPositions.planetSelector', 'Select a planet')}
    >
      <GHScrollView
        ref={planetDockRef}
        horizontal
        scrollEnabled={!isTablet}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={[styles.planetDockContent, isTablet && styles.planetDockContentTablet]}
      >
        <TouchableOpacity
          key="planet-dock-all"
          style={[
            styles.planetDockItem,
            { width: dockItemWidth },
            !selectedPlanetName && {
              backgroundColor: colors.selectionSurface,
              borderColor: colors.selectionBorder,
            },
          ]}
          onPress={() => selectPlanet(null)}
          accessibilityRole="tab"
          accessibilityState={{ selected: !selectedPlanetName }}
          accessibilityLabel={t('premiumUi.planetaryPositions.allPlanets', 'All planets')}
        >
          <Ionicons
            name="apps-outline"
            size={19}
            color={!selectedPlanetName ? colors.selectionText : colors.textSecondary}
          />
          <Text
            style={[styles.planetDockName, { color: !selectedPlanetName ? colors.selectionText : colors.textSecondary }]}
            numberOfLines={1}
          >
            {t('premiumUi.planetaryPositions.all', 'All')}
          </Text>
        </TouchableOpacity>
        {planets.map((planet) => {
          const selected = planet.name === selectedPlanetName;
          return (
            <TouchableOpacity
              key={`planet-dock-${planet.name}`}
              style={[
                styles.planetDockItem,
                { width: dockItemWidth },
                selected && {
                  backgroundColor: colors.selectionSurface,
                  borderColor: colors.selectionBorder,
                },
              ]}
              onPress={() => selectPlanet(planet.name)}
              accessibilityRole="tab"
              accessibilityState={{ selected }}
              accessibilityLabel={planet.name}
            >
              <Text style={[styles.planetDockSymbol, { color: selected ? colors.selectionText : colors.textSecondary }]}>
                {planetEmojis[planet.name]}
              </Text>
              <Text
                style={[styles.planetDockName, { color: selected ? colors.selectionText : colors.textSecondary }]}
                numberOfLines={1}
              >
                {planet.name}
              </Text>
            </TouchableOpacity>
          );
        })}
      </GHScrollView>
    </View>
  );

  const selectHouse = (houseNumber) => {
    setSelectedHouseNumber(houseNumber);
    setExpandedHouses((current) => (
      houseNumber ? { ...current, [houseNumber]: true } : {}
    ));
    navigation.setParams?.({ selectedHouseNumber: houseNumber || null });
  };

  const HouseDock = () => (
    <View
      style={[
        styles.planetDock,
        {
          backgroundColor: colors.surfaceRaised,
          borderTopColor: colors.cardBorder,
          paddingBottom: Math.max(insets.bottom, 8),
        },
      ]}
      accessibilityLabel={t('premiumUi.planetaryPositions.houseSelector', 'Select a house')}
    >
      <GHScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.planetDockContent}
      >
        <TouchableOpacity
          style={[
            styles.houseDockItem,
            !selectedHouseNumber && {
              backgroundColor: colors.selectionSurface,
              borderColor: colors.selectionBorder,
            },
          ]}
          onPress={() => selectHouse(null)}
          accessibilityRole="tab"
          accessibilityState={{ selected: !selectedHouseNumber }}
          accessibilityLabel={t('premiumUi.planetaryPositions.allHouses', 'All houses')}
        >
          <Ionicons name="grid-outline" size={18} color={!selectedHouseNumber ? colors.selectionText : colors.textSecondary} />
          <Text style={[styles.planetDockName, { color: !selectedHouseNumber ? colors.selectionText : colors.textSecondary }]}>
            {t('premiumUi.planetaryPositions.all', 'All')}
          </Text>
        </TouchableOpacity>
        {houseRows.map((row) => {
          const selected = row.house === Number(selectedHouseNumber);
          return (
            <TouchableOpacity
              key={`house-dock-${row.house}`}
              style={[
                styles.houseDockItem,
                selected && {
                  backgroundColor: colors.selectionSurface,
                  borderColor: colors.selectionBorder,
                },
              ]}
              onPress={() => selectHouse(row.house)}
              accessibilityRole="tab"
              accessibilityState={{ selected }}
              accessibilityLabel={t('premiumUi.planetaryPositions.house', 'House {{number}}', { number: row.house })}
            >
              <Text style={[styles.houseDockNumber, { color: selected ? colors.selectionText : colors.textSecondary }]}>H{row.house}</Text>
              <Text style={[styles.planetDockName, { color: selected ? colors.selectionText : colors.textSecondary }]} numberOfLines={1}>
                {row.signAbbr}
              </Text>
            </TouchableOpacity>
          );
        })}
      </GHScrollView>
    </View>
  );

  const selectNakshatraSubject = (name) => {
    setSelectedNakshatraSubject(name);
  };

  const NakshatraDock = () => (
    <View
      style={[
        styles.planetDock,
        {
          backgroundColor: colors.surfaceRaised,
          borderTopColor: colors.cardBorder,
          paddingBottom: Math.max(insets.bottom, 8),
        },
      ]}
      accessibilityLabel={t('premiumUi.planetaryPositions.nakshatraPlacementSelector', 'Select a chart placement')}
    >
      <GHScrollView
        ref={nakshatraDockRef}
        horizontal
        scrollEnabled={!isTablet}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={[styles.planetDockContent, isTablet && styles.planetDockContentTablet]}
      >
        <TouchableOpacity
          style={[
            styles.planetDockItem,
            { width: nakshatraDockItemWidth },
            !selectedNakshatraSubject && { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder },
          ]}
          onPress={() => selectNakshatraSubject(null)}
          accessibilityRole="tab"
          accessibilityState={{ selected: !selectedNakshatraSubject }}
        >
          <Ionicons name="apps-outline" size={19} color={!selectedNakshatraSubject ? colors.selectionText : colors.textSecondary} />
          <Text style={[styles.planetDockName, { color: !selectedNakshatraSubject ? colors.selectionText : colors.textSecondary }]}>
            {t('premiumUi.planetaryPositions.all', 'All')}
          </Text>
        </TouchableOpacity>
        {nakshatraPlacements.map((placement) => {
          const selected = placement.name === selectedNakshatraSubject;
          return (
            <TouchableOpacity
              key={`nakshatra-dock-${placement.name}`}
              style={[
                styles.planetDockItem,
                { width: nakshatraDockItemWidth },
                selected && { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder },
              ]}
              onPress={() => selectNakshatraSubject(placement.name)}
              accessibilityRole="tab"
              accessibilityState={{ selected }}
            >
              <Text style={[styles.planetDockSymbol, { color: selected ? colors.selectionText : colors.textSecondary }]}>
                {planetEmojis[placement.name] || '⭐'}
              </Text>
              <Text style={[styles.planetDockName, { color: selected ? colors.selectionText : colors.textSecondary }]} numberOfLines={1}>
                {placement.name === 'Lagna' ? t('premiumUi.planetaryPositions.lagna', 'Lagna') : placement.name}
              </Text>
            </TouchableOpacity>
          );
        })}
      </GHScrollView>
    </View>
  );

  const karakaNameFor = (planetName) => {
    if (!karakas || typeof karakas !== 'object') return null;
    const found = Object.entries(karakas).find(([, value]) => {
      const planet = typeof value === 'string' ? value : value?.planet || value?.name;
      return planet === planetName;
    });
    return found ? found[0] : null;
  };

  const degreeText = (value, fallback) => {
    const number = Number(value);
    if (Number.isFinite(number)) return `${number.toFixed(2)}°`;
    return fallback || '—';
  };

  const dignityText = (dignity) => {
    if (!dignity) return t('premiumUi.planetaryPositions.dignities.notGraded', 'Not classically graded');
    return t(
      `premiumUi.planetaryPositions.dignities.${dignity.labelKey || 'notGraded'}`,
      dignity.label || 'Not classically graded',
    );
  };

  const relationshipText = (relationship) => {
    if (!relationship) return '—';
    return t(
      `premiumUi.planetaryPositions.relationships.${relationship.labelKey || 'traditionDependent'}`,
      relationship.label || 'Tradition-dependent',
    );
  };

  const relationshipColor = (relationship) => {
    if (['friend', 'greatFriend', 'self', 'temporaryFriend'].includes(relationship?.key)) return colors.success;
    if (['enemy', 'greatEnemy', 'temporaryEnemy'].includes(relationship?.key)) return colors.error;
    return colors.textSecondary;
  };

  const professionalValue = (label, value, color = colors.text) => (
    <View style={styles.professionalRow}>
      <Text style={[styles.professionalLabel, { color: colors.textSecondary }]}>{label}</Text>
      <Text style={[styles.professionalValue, { color }]}>{value || '—'}</Text>
    </View>
  );

  const combustionEvidenceText = (combustion) => {
    if (!combustion?.applicable || !Number.isFinite(Number(combustion.distance))) return null;
    const motion = combustion.motion === 'retrograde'
      ? t('premiumUi.planetaryPositions.retrograde', 'Retrograde')
      : t('premiumUi.planetaryPositions.direct', 'Direct');
    const status = combustion.isCombust
      ? t('premiumUi.planetaryPositions.notes.combustFull', 'Combust')
      : t('premiumUi.planetaryPositions.clearOfCombustion', 'Clear');
    return t(
      'premiumUi.planetaryPositions.combustionEvidence',
      '{{distance}}° from Sun · {{threshold}}° limit · {{motion}} · {{status}}',
      {
        distance: Number(combustion.distance).toFixed(2),
        threshold: Number(combustion.threshold).toFixed(0),
        motion,
        status,
      },
    );
  };

  const PlanetCard = ({ planet }) => {
    const row = planetRows.find((item) => item.name === planet.name);
    const dignityResult = planetaryDignities?.[planet.name];
    const functional = dignityResult?.functional_nature_details;
    const natural = dignityResult?.natural_nature_details;
    const delivery = (
      conditionChartData?.planet_result_delivery?.planets?.[planet.name]
      || chartData?.planet_result_delivery?.planets?.[planet.name]
    );
    const retrograde = !!(planet.retrograde && planet.name !== 'Rahu' && planet.name !== 'Ketu');
    const notes = [];
    if (row?.combust) notes.push(t('premiumUi.planetaryPositions.notes.combustFull', 'Combust'));
    if (row?.neechaBhanga) notes.push(t('premiumUi.planetaryPositions.notes.neechaBhangaFull', 'Neecha Bhanga'));
    if (row?.vargottama) notes.push(t('premiumUi.planetaryPositions.notes.vargottamaFull', 'Vargottama'));
    const karaka = karakaNameFor(planet.name);
    const expanded = !!expandedPlanets[planet.name];
    const advanced = row || {};
    const signFriendship = advanced.friendships?.sign_lord;
    const nakFriendship = advanced.friendships?.nakshatra_lord;
    const aspectsCast = (advanced.aspects?.cast || []).map((item) => (
      t('premiumUi.planetaryPositions.aspectCastValue', '{{number}}th → H{{house}}{{planets}}', {
        number: item.aspect_number,
        house: item.target_house,
        planets: item.planets?.length ? ` (${item.planets.join(', ')})` : '',
      })
    )).join(' · ');
    const aspectsReceived = (advanced.aspects?.received || []).map((item) => (
      `${item.planet} (${item.aspect_numbers.join('/')})`
    )).join(' · ');
    const conjunctions = (advanced.conjunctions || []).map((item) => (
      `${item.planet} · ${Number(item.separation_degrees).toFixed(2)}°`
    )).join(' · ');
    const repetitions = advanced.varga_strength?.repetitions || {};
    const naturalRoleText = planet.name === 'Moon' && natural?.phase === 'waxing'
      ? t('premiumUi.planetaryPositions.waxingMoonBenefic', 'Waxing Moon · natural benefic')
      : planet.name === 'Moon' && natural?.phase === 'waning_or_dark'
        ? t('premiumUi.planetaryPositions.waningMoonMalefic', 'Waning or dark Moon · natural malefic')
        : t(
          `premiumUi.planetaryPositions.naturalNature.${natural?.nature}`,
          natural?.nature === 'benefic' ? 'Natural benefic' : natural?.nature === 'malefic' ? 'Natural malefic' : 'Context-dependent',
        );
    const functionalRoleText = t(
      `premiumUi.planetaryPositions.functionalNature.${functional?.functional_nature}`,
      functional?.functional_nature === 'benefic'
        ? 'Functional benefic'
        : functional?.functional_nature === 'malefic'
          ? 'Functional malefic'
          : 'Neutral or qualified',
    );
    const naturalRoleColor = natural?.nature === 'benefic'
      ? colors.success
      : natural?.nature === 'malefic' ? colors.error : colors.textSecondary;
    const functionalRoleColor = functional?.functional_nature === 'benefic'
      ? colors.success
      : functional?.functional_nature === 'malefic' ? colors.error : colors.textSecondary;
    return (
      <View style={[styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
        <View style={styles.cardHeader}>
          <View style={styles.planetInfo}>
            <View style={[styles.planetSeal, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
              <Text style={[styles.planetEmoji, { color: colors.selectionText }]}>{planetEmojis[planet.name]}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.planetName, { color: colors.text }]}>{planet.name}</Text>
              {retrograde ? (
                <Text style={[styles.retrogradeTag, { color: colors.error }]}>
                  {t('premiumUi.planetaryPositions.retrograde', 'Retrograde')}
                </Text>
              ) : null}
              {notes.length > 0 ? (
                <Text style={[styles.lagnaDescription, { color: colors.textSecondary }]}>{notes.join(' · ')}</Text>
              ) : null}
            </View>
          </View>
          <View style={[styles.houseTag, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
            <Text style={[styles.houseText, { color: colors.selectionText }]}>
              {t('premiumUi.planetaryPositions.house', 'House {{number}}', { number: planet.house })}
            </Text>
          </View>
        </View>
        <View style={[styles.divider, { backgroundColor: colors.cardBorder }]} />
        <View style={styles.detailsGrid}>
          <View style={styles.detailItem}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.rashi', 'Rashi')}</Text>
            <View style={styles.rashiContainer}>
              <Text style={styles.rashiIcon}>{rashiIcons[planet.sign]}</Text>
              <Text style={[styles.detailValue, { color: colors.text }]}>{rashiNames[planet.sign] || row?.signName}</Text>
            </View>
          </View>
          {combustionEvidenceText(row?.combustion) ? (
            <View style={styles.detailItemFull}>
              <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.solarDistance', 'Solar distance')}</Text>
              <Text style={[
                styles.detailValue,
                styles.detailValueWide,
                { color: row?.combustion?.isCombust ? colors.error : colors.textSecondary },
              ]}>
                {combustionEvidenceText(row.combustion)}
              </Text>
            </View>
          ) : null}
          <View style={styles.detailItem}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.degree', 'Degree')}</Text>
            <Text style={[styles.detailValue, { color: colors.text }]}>{degreeText(planet.degree, row?.degree)}</Text>
          </View>
          <View style={styles.detailItemFull}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.dignity', 'Dignity')}</Text>
            <Text style={[
              styles.detailValue,
              styles.detailValueWide,
              { color: row?.dignity?.key === 'db' || row?.dignity?.key === 'enemy' ? colors.error : colors.text },
            ]}>
              {dignityText(row?.dignity)}
            </Text>
          </View>
          {row?.lord ? (
            <View style={styles.detailItemFull}>
              <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.rashiLord', 'Rashi lord')}</Text>
              <Text style={[styles.detailValue, styles.detailValueWide, { color: colors.text }]}>
                {row.lord} · <Text style={{ color: relationshipColor(row.signLordRelationship) }}>{relationshipText(row.signLordRelationship)}</Text>
              </Text>
            </View>
          ) : null}
          <View style={styles.detailItemFull}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.nakshatra', 'Nakshatra')}</Text>
            <Text style={[styles.detailValue, styles.detailValueWide, { color: colors.text }]}>
              {planet.nakshatra} · {t('premiumUi.planetaryPositions.pada', 'Pada {{number}}', { number: planet.pada })}
            </Text>
          </View>
          {row?.nakLord ? (
            <View style={styles.detailItemFull}>
              <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.nakshatraLord', 'Nakshatra lord')}</Text>
              <Text style={[styles.detailValue, styles.detailValueWide, { color: colors.text }]}>
                {row.nakLord} · <Text style={{ color: relationshipColor(row.nakLordRelationship) }}>{relationshipText(row.nakLordRelationship)}</Text>
              </Text>
            </View>
          ) : null}
          {karaka ? (
            <View style={styles.detailItem}>
              <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.charaKaraka', 'Chara karaka')}</Text>
              <Text style={[styles.detailValue, { color: colors.text }]}>{karaka}</Text>
            </View>
          ) : null}
        </View>
        {natural?.applicable || functional?.applicable ? (
          <View style={[styles.roleSummaryCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
            <View style={styles.roleSummaryTitleRow}>
              <Ionicons name="git-branch-outline" size={18} color={colors.primaryStrong} />
              <Text style={[styles.roleSummaryTitle, { color: colors.text }]}>
                {t('premiumUi.planetaryPositions.roleInChart', 'Role in this chart')}
              </Text>
            </View>
            {natural?.applicable ? (
              <View style={styles.roleSummaryRow}>
                <Text style={[styles.roleSummaryLabel, { color: colors.textSecondary }]}>
                  {t('premiumUi.planetaryPositions.naturalRole', 'Natural nature')}
                </Text>
                <Text style={[styles.roleSummaryValue, { color: naturalRoleColor }]}>{naturalRoleText}</Text>
              </View>
            ) : null}
            {functional?.applicable ? (
              <View style={styles.roleSummaryRow}>
                <Text style={[styles.roleSummaryLabel, { color: colors.textSecondary }]}>
                  {t('premiumUi.planetaryPositions.functionalRole', 'Role for this Lagna')}
                </Text>
                <Text style={[styles.roleSummaryValue, { color: functionalRoleColor }]}>{functionalRoleText}</Text>
              </View>
            ) : null}
            {functional?.applicable ? (
              <Text style={[styles.roleSummaryReason, { color: colors.textSecondary, borderTopColor: colors.cardBorder }]}>
                {t('premiumUi.planetaryPositions.rulesHouses', 'Rules House(s) {{houses}}', {
                  houses: (functional.ruled_houses || []).join(', ') || '—',
                })}
              </Text>
            ) : null}
            {functional?.is_yogakaraka ? (
              <Text style={[styles.roleSummaryCondition, { color: colors.success }]}>
                {t('premiumUi.planetaryPositions.yogakarakaRole', 'Yogakaraka: owns both a Kendra and a Trikona')}
              </Text>
            ) : null}
            {functional?.is_maraka_lord ? (
              <Text style={[styles.roleSummaryCondition, { color: colors.textSecondary }]}>
                {t('premiumUi.planetaryPositions.marakaRole', 'Maraka lordship: House(s) {{houses}}', {
                  houses: (functional.maraka_houses || []).join(', '),
                })}
              </Text>
            ) : null}
          </View>
        ) : null}
        <View style={[styles.professionalAccordion, { borderColor: colors.cardBorder, backgroundColor: colors.surfaceMuted }]}>
          <TouchableOpacity
            style={styles.professionalToggle}
            onPress={() => setExpandedPlanets((current) => ({ ...current, [planet.name]: !current[planet.name] }))}
            accessibilityRole="button"
          >
            <View style={{ flex: 1 }}>
              <Text style={[styles.professionalToggleTitle, { color: colors.text }]}>
                {t('premiumUi.planetaryPositions.professionalDetails', 'Professional details')}
              </Text>
              <Text style={[styles.professionalToggleHint, { color: colors.textSecondary }]}>
                {t('premiumUi.planetaryPositions.professionalDetailsHint', 'Strength, motion, aspects, dispositors and special states')}
              </Text>
            </View>
            <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={20} color={colors.primaryStrong} />
          </TouchableOpacity>
          {expanded ? (
          <View style={[styles.professionalPanel, { borderTopColor: colors.cardBorder }]}>
            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.precisePlacement', 'Precise placement')}
            </Text>
            {professionalValue(t('premiumUi.planetaryPositions.exactLongitude', 'Exact longitude'), `${Number(advanced.longitude).toFixed(6)}° · ${advanced.degree_dms?.text || '—'}`)}
            {professionalValue(t('premiumUi.planetaryPositions.houseComparison', 'Rashi / Bhava Chalit house'), `H${advanced.rashi_house || planet.house} / ${advanced.bhava_chalit_house ? `H${advanced.bhava_chalit_house}` : '—'}`)}
            {professionalValue(t('premiumUi.planetaryPositions.motion', 'Motion'), t(`premiumUi.planetaryPositions.motionStates.${advanced.motion?.key || 'unknown'}`, advanced.motion?.key || '—') + (advanced.motion?.speed_degrees_per_day != null && Number.isFinite(Number(advanced.motion.speed_degrees_per_day)) ? ` · ${Number(advanced.motion.speed_degrees_per_day).toFixed(6)}°/${t('premiumUi.planetaryPositions.day', 'day')}` : ''))}
            {advanced.deep_point ? professionalValue(t('premiumUi.planetaryPositions.deepPoint', 'Exact dignity point'), t('premiumUi.planetaryPositions.deepPointValue', '{{type}} at {{degree}}° · {{distance}}° away', { type: t(`premiumUi.planetaryPositions.deepPointTypes.${advanced.deep_point.type}`, advanced.deep_point.type), degree: advanced.deep_point.exact_degree, distance: Number(advanced.deep_point.distance_degrees).toFixed(2) })) : null}
            {professionalValue(t('premiumUi.planetaryPositions.boundaries', 'Nearest boundaries'), t('premiumUi.planetaryPositions.boundaryValue', 'Rashi {{rashi}}° · Nakshatra {{nakshatra}}°', { rashi: Number(advanced.boundary_proximity?.rashi_degrees).toFixed(2), nakshatra: Number(advanced.boundary_proximity?.nakshatra_degrees).toFixed(2) }))}

            {natural?.applicable || functional?.applicable ? (
              <>
                <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
                  {t('premiumUi.planetaryPositions.roleReasoning', 'Role reasoning')}
                </Text>
                {natural?.applicable ? professionalValue(t('premiumUi.planetaryPositions.naturalRole', 'Natural nature'), naturalRoleText, naturalRoleColor) : null}
                {planet.name === 'Moon' && Number.isFinite(Number(natural?.elongation)) ? professionalValue(
                  t('premiumUi.planetaryPositions.moonPhaseEvidence', 'Moon phase evidence'),
                  t('premiumUi.planetaryPositions.moonElongation', '{{degrees}}° ahead of the Sun', { degrees: Number(natural.elongation).toFixed(2) }),
                ) : null}
                {functional?.applicable ? professionalValue(t('premiumUi.planetaryPositions.functionalRole', 'Role for this Lagna'), functionalRoleText, functionalRoleColor) : null}
                {functional?.applicable ? professionalValue(t('premiumUi.planetaryPositions.houseOwnership', 'House ownership'), t('premiumUi.planetaryPositions.rulesHouses', 'Rules House(s) {{houses}}', { houses: (functional.ruled_houses || []).join(', ') || '—' })) : null}
                {functional?.applicable ? professionalValue(
                  t('premiumUi.planetaryPositions.classicalReference', 'Classical reference'),
                  t('premiumUi.planetaryPositions.functionalReference', 'Classical basis: Brihat Parashara Hora Shastra · {{verses}}', { verses: functional.stated_verses || 'Chapter 34' }),
                ) : null}
              </>
            ) : null}

            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.friendshipsAndDispositors', 'Friendships and dispositors')}
            </Text>
            {signFriendship ? professionalValue(t('premiumUi.planetaryPositions.rashiLord', 'Rashi lord'), `${advanced.lord} · ${relationshipText(signFriendship.natural)} · ${relationshipText(signFriendship.temporary)} · ${relationshipText(signFriendship.compound)}`, relationshipColor(signFriendship.compound)) : null}
            {nakFriendship ? professionalValue(t('premiumUi.planetaryPositions.nakshatraLord', 'Nakshatra lord'), `${advanced.nakLord} · ${relationshipText(nakFriendship.natural)} · ${relationshipText(nakFriendship.temporary)} · ${relationshipText(nakFriendship.compound)}`, relationshipColor(nakFriendship.compound)) : null}
            {professionalValue(t('premiumUi.planetaryPositions.signDispositor', 'Sign dispositor'), advanced.dispositors?.sign?.available ? `${advanced.dispositors.sign.planet} · H${advanced.dispositors.sign.house} · ${dignityText(advanced.dispositors.sign.dignity)}${advanced.dispositors.sign.shadbala ? ` · ${advanced.dispositors.sign.shadbala.required_percent}% ${t('premiumUi.planetaryPositions.shadbala', 'Shadbala')}` : ''}${advanced.dispositors.sign.aspects_received?.length ? ` · ${advanced.dispositors.sign.aspects_received.length} ${t('premiumUi.planetaryPositions.aspectsReceived', 'aspects received')}` : ''}${advanced.dispositors.sign.combust ? ` · ${t('premiumUi.planetaryPositions.notes.combustFull', 'Combust')}` : ''}` : '—')}
            {professionalValue(t('premiumUi.planetaryPositions.nakshatraDispositor', 'Nakshatra dispositor'), advanced.dispositors?.nakshatra?.available ? `${advanced.dispositors.nakshatra.planet} · H${advanced.dispositors.nakshatra.house} · ${dignityText(advanced.dispositors.nakshatra.dignity)}${advanced.dispositors.nakshatra.shadbala ? ` · ${advanced.dispositors.nakshatra.shadbala.required_percent}% ${t('premiumUi.planetaryPositions.shadbala', 'Shadbala')}` : ''}${advanced.dispositors.nakshatra.aspects_received?.length ? ` · ${advanced.dispositors.nakshatra.aspects_received.length} ${t('premiumUi.planetaryPositions.aspectsReceived', 'aspects received')}` : ''}${advanced.dispositors.nakshatra.combust ? ` · ${t('premiumUi.planetaryPositions.notes.combustFull', 'Combust')}` : ''}` : '—')}

            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.connections', 'Connections')}
            </Text>
            {professionalValue(t('premiumUi.planetaryPositions.aspectsCast', 'Aspects cast'), aspectsCast || t('premiumUi.planetaryPositions.none', 'None'))}
            {professionalValue(t('premiumUi.planetaryPositions.aspectsReceived', 'Aspects received'), aspectsReceived || t('premiumUi.planetaryPositions.none', 'None'))}
            {professionalValue(t('premiumUi.planetaryPositions.conjunctions', 'Same-sign conjunctions'), conjunctions || t('premiumUi.planetaryPositions.none', 'None'))}
            {advanced.graha_yuddha ? professionalValue(t('premiumUi.planetaryPositions.grahaYuddha', 'Graha Yuddha'), t('premiumUi.planetaryPositions.grahaYuddhaValue', 'Eligible close conjunction with {{planet}} · {{distance}}° · winner not graded', { planet: advanced.graha_yuddha.planet_1 === planet.name ? advanced.graha_yuddha.planet_2 : advanced.graha_yuddha.planet_1, distance: Number(advanced.graha_yuddha.separation_degrees).toFixed(3) }), colors.warning) : null}

            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.strengthAndSpecialStates', 'Strength and special states')}
            </Text>
            {advanced.baladi_avastha ? professionalValue(t('premiumUi.planetaryPositions.baladiAvastha', 'Baladi Avastha'), `${t(`premiumUi.planetaryPositions.avasthas.${advanced.baladi_avastha.key}`, advanced.baladi_avastha.key)} · ${advanced.baladi_avastha.strength_percent}%`) : null}
            {advanced.shadbala ? professionalValue(t('premiumUi.planetaryPositions.shadbala', 'Shadbala'), t('premiumUi.planetaryPositions.shadbalaValue', '{{rupas}} Rupas · requires {{required}} · {{percent}}%', { rupas: advanced.shadbala.total_rupas, required: advanced.shadbala.minimum_required_rupas, percent: advanced.shadbala.required_percent }), advanced.shadbala.meets_minimum ? colors.success : colors.error) : null}
            {advanced.shadbala?.strongest_component ? professionalValue(t('premiumUi.planetaryPositions.shadbalaComponents', 'Shadbala components'), t('premiumUi.planetaryPositions.shadbalaComponentsValue', 'Strongest: {{strongest}} · weakest: {{weakest}}', { strongest: t(`premiumUi.planetaryPositions.shadbalaComponentNames.${advanced.shadbala.strongest_component.key}`, advanced.shadbala.strongest_component.key), weakest: t(`premiumUi.planetaryPositions.shadbalaComponentNames.${advanced.shadbala.weakest_component?.key}`, advanced.shadbala.weakest_component?.key || '—') })) : null}
            {!advanced.shadbala && canonicalPositions?.shadbala_status?.status === 'unavailable' ? professionalValue(t('premiumUi.planetaryPositions.shadbala', 'Shadbala'), t('premiumUi.planetaryPositions.strengthUnavailable', 'Strength worksheet unavailable'), colors.warning) : null}
            {advanced.ishta_kashta ? professionalValue(t('premiumUi.planetaryPositions.ishtaKashta', 'Ishta / Kashta Phala'), `${advanced.ishta_kashta.ishta_phala} / ${advanced.ishta_kashta.kashta_phala}`) : null}
            {advanced.varga_strength ? professionalValue(t('premiumUi.planetaryPositions.vargaStrength', 'Varga strength'), t('premiumUi.planetaryPositions.vargaStrengthValue', 'D9 {{sign}} · {{dignity}} · Vimshopaka {{vimshopaka}}/20 · exalted {{exalted}} · own {{own}} · debilitated {{debilitated}}', { sign: advanced.varga_strength.d9_sign_name || '—', dignity: dignityText(advanced.varga_strength.d9_dignity), vimshopaka: advanced.varga_strength.vimshopaka_bala?.score ?? '—', exalted: (repetitions.exalted || []).length, own: (repetitions.own_sign || []).length, debilitated: (repetitions.debilitated || []).length })) : null}
            {advanced.gandanta?.is_gandanta ? professionalValue(t('premiumUi.planetaryPositions.gandanta', 'Gandanta'), t('premiumUi.planetaryPositions.gandantaValue', '{{junction}} · {{distance}}° from junction', { junction: t(`premiumUi.planetaryPositions.gandantaJunctions.${advanced.gandanta.junction_key}`, advanced.gandanta.junction_key), distance: Number(advanced.gandanta.distance_degrees).toFixed(2) }), colors.warning) : null}
            {advanced.pushkara?.is_pushkara_navamsa || advanced.pushkara?.is_pushkara_bhaga ? professionalValue(t('premiumUi.planetaryPositions.pushkara', 'Pushkara'), [advanced.pushkara.is_pushkara_navamsa ? t('premiumUi.planetaryPositions.pushkaraNavamsha', 'Pushkara Navamsha') : null, advanced.pushkara.is_pushkara_bhaga ? t('premiumUi.planetaryPositions.pushkaraBhaga', 'Pushkara Bhaga') : null].filter(Boolean).join(' · '), colors.success) : null}
            {advanced.navatara ? professionalValue(t('premiumUi.planetaryPositions.navatara', 'Navatara from natal Moon'), t(`premiumUi.planetaryPositions.navataraValues.${advanced.navatara.key}`, advanced.navatara.key)) : null}
            <Text style={[styles.methodDisclosure, { color: colors.textSecondary, borderTopColor: colors.cardBorder }]}>
              {t('premiumUi.planetaryPositions.professionalMethodNote', 'Parashari whole-sign aspects are used. Rahu and Ketu use only the 7th aspect here. Exact separations are shown without Western aspect orbs.')}
            </Text>
          </View>
          ) : null}
        </View>
        {delivery?.relevant ? (
          <View style={[styles.deliveryCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
            <View style={styles.deliveryTitleRow}>
              <Ionicons name="navigate-circle-outline" size={19} color={colors.primaryStrong} />
              <Text style={[styles.deliveryTitle, { color: colors.text }]}>
                {t('premiumUi.planetResultDelivery.title', 'Where this planet can deliver results')}
              </Text>
            </View>

            {delivery.conditions?.neecha_bhanga ? (
              <Text style={[styles.deliveryExplanation, { color: colors.textSecondary }]}>
                {t('premiumUi.planetResultDelivery.neechaBhanga')}
              </Text>
            ) : delivery.conditions?.debilitated ? (
              <Text style={[styles.deliveryExplanation, { color: colors.textSecondary }]}>
                {t('premiumUi.planetResultDelivery.debilitated')}
              </Text>
            ) : null}
            {delivery.conditions?.retrograde ? (
              <Text style={[styles.deliveryExplanation, { color: colors.textSecondary }]}>
                {t('premiumUi.planetResultDelivery.retrograde')}
              </Text>
            ) : null}
            {delivery.conditions?.combust ? (
              <Text style={[styles.deliveryExplanation, { color: colors.textSecondary }]}>
                {t('premiumUi.planetResultDelivery.combust')}
              </Text>
            ) : null}

            <Text style={[styles.deliverySectionLabel, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetResultDelivery.houseChannels', 'House channels')}
            </Text>
            <View style={styles.deliveryChannels}>
              {(delivery.channels || []).map((channel) => {
                const roleLabels = (channel.roles || []).map((role) => {
                  if (role !== 'aspected') return t(`premiumUi.planetResultDelivery.${role}`, role);
                  const aspects = (channel.aspect_numbers || []).map((number) => (
                    t('premiumUi.planetResultDelivery.aspect', '{{number}}th aspect', { number })
                  ));
                  return aspects.length ? aspects.join(', ') : t('premiumUi.planetResultDelivery.aspected', 'Aspects');
                });
                return (
                  <View key={`${planet.name}-delivery-${channel.house}`} style={[styles.deliveryChannel, { borderColor: colors.cardBorder, backgroundColor: colors.surfaceRaised }]}>
                    <View style={[styles.deliveryHouseBadge, { backgroundColor: colors.selectionSurface }]}>
                      <Text style={[styles.deliveryHouseBadgeText, { color: colors.selectionText }]}>H{channel.house}</Text>
                    </View>
                    <View style={styles.deliveryChannelCopy}>
                      <Text style={[styles.deliveryHouseArea, { color: colors.text }]}>
                        {t(`premiumUi.home.houseAreas.${channel.house}`, `House ${channel.house}`)}
                      </Text>
                      <Text style={[styles.deliveryRoles, { color: colors.textSecondary }]}>{roleLabels.join(' · ')}</Text>
                    </View>
                  </View>
                );
              })}
            </View>
            <Text style={[styles.deliverySectionLabel, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetResultDelivery.timingTitle', 'When this matters')}
            </Text>
            <Text style={[styles.deliveryExplanation, { color: colors.textSecondary }]}>
              {t('premiumUi.planetResultDelivery.timing')}
            </Text>
            <Text style={[styles.deliveryBoundary, { color: colors.textSecondary, borderTopColor: colors.cardBorder }]}>
              {t('premiumUi.planetResultDelivery.boundary')}
            </Text>
          </View>
        ) : null}
        {row?.neechaBhanga ? (
          <TouchableOpacity
            style={[styles.yogaLink, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}
            onPress={() => navigation.navigate('Yogas')}
            accessibilityRole="button"
          >
            <Ionicons name="library-outline" size={16} color={colors.selectionText} />
            <Text style={[styles.yogaLinkText, { color: colors.selectionText }]}>
              {t('premiumUi.planetaryPositions.openNeechaBhanga', 'See the classical Neecha Bhanga rule')}
            </Text>
            <Ionicons name="chevron-forward" size={16} color={colors.selectionText} />
          </TouchableOpacity>
        ) : null}
      </View>
    );
  };

  const HouseCard = ({ row }) => {
    const people = row.occupantList || [];
    const expanded = !!expandedHouses[row.house];
    const occupantText = people.length
      ? people.map((person) => {
        const states = [
          (person.retrograde || person.retro) ? t('premiumUi.planetaryPositions.retrograde', 'Retrograde') : null,
          person.combust ? t('premiumUi.planetaryPositions.notes.combustFull', 'Combust') : null,
        ].filter(Boolean);
        const name = t(`planets.${person.name}`, person.name);
        return states.length ? `${name} (${states.join(', ')})` : name;
      }).join(', ')
      : t('premiumUi.planetaryPositions.none', 'None');
    const lordText = row.lordHouse === '—'
      ? t(`planets.${row.lord}`, row.lord)
      : `${t(`planets.${row.lord}`, row.lord)} · ${t('premiumUi.planetaryPositions.house', 'House {{number}}', { number: row.lordHouse })}`;
    const lordState = row.lord_state;
    const lordConditions = [
      lordState?.dignity ? dignityText(lordState.dignity) : null,
      lordState?.retrograde ? t('premiumUi.planetaryPositions.retrograde', 'Retrograde') : null,
      lordState?.combust ? t('premiumUi.planetaryPositions.notes.combustFull', 'Combust') : null,
      lordState?.neecha_bhanga ? t('premiumUi.planetaryPositions.notes.neechaBhangaFull', 'Neecha Bhanga') : null,
      lordState?.vargottama ? t('premiumUi.planetaryPositions.notes.vargottamaFull', 'Vargottama') : null,
    ].filter(Boolean);
    const classificationText = (row.classifications || []).map((key) => (
      t(`premiumUi.planetaryPositions.houseClassifications.${key}`, key)
    ));
    const houseArea = t(`premiumUi.home.houseAreas.${row.house}`, `House ${row.house}`);
    return (
      <View style={[styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
        <TouchableOpacity
          style={styles.cardHeader}
          onPress={() => setExpandedHouses((current) => ({ ...current, [row.house]: !current[row.house] }))}
          accessibilityRole="button"
          accessibilityState={{ expanded }}
        >
          <View style={styles.planetInfo}>
            <View style={[styles.houseSeal, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
              <Text style={[styles.houseSealText, { color: colors.selectionText }]}>H{row.house}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.planetName, { color: colors.text }]}>
                {t('premiumUi.planetaryPositions.house', 'House {{number}}', { number: row.house })}
              </Text>
              <Text style={[styles.lagnaDescription, { color: colors.textSecondary }]} numberOfLines={2}>{houseArea}</Text>
            </View>
          </View>
          <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={19} color={colors.textSecondary} />
        </TouchableOpacity>
        <View style={[styles.divider, { backgroundColor: colors.cardBorder }]} />
        <View style={styles.detailsGrid}>
          <View style={styles.detailItem}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.rashi', 'Rashi')}</Text>
            <View style={styles.rashiContainer}>
              <Text style={styles.rashiIcon}>{rashiIcons[row.sign]}</Text>
              <Text style={[styles.detailValue, { color: colors.text }]}>{row.signName}</Text>
            </View>
          </View>
          <View style={styles.detailItem}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.cols.lord', 'Lord')}</Text>
            <Text style={[styles.detailValue, styles.detailValueWide, { color: colors.text }]}>{lordText}</Text>
          </View>
          <View style={styles.detailItemFull}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.cols.occupants', 'Planets')}</Text>
            <Text style={[styles.detailValue, styles.detailValueWide, { color: colors.text }]}>{occupantText}</Text>
          </View>
        </View>
        {expanded ? (
          <View style={[styles.houseProfessionalPanel, { borderTopColor: colors.cardBorder }]}>
            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.houseNature', 'House nature')}
            </Text>
            <View style={styles.houseClassificationRow}>
              {classificationText.length ? classificationText.map((label, index) => (
                <View key={`${row.house}-class-${index}`} style={[styles.houseClassificationChip, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                  <Text style={[styles.houseClassificationText, { color: colors.text }]}>{label}</Text>
                </View>
              )) : (
                <Text style={[styles.professionalValue, { color: colors.textSecondary }]}>
                  {t('premiumUi.planetaryPositions.noSpecialHouseGroup', 'No additional classical group')}
                </Text>
              )}
            </View>

            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.houseLordCondition', 'House lord and its condition')}
            </Text>
            {professionalValue(t('premiumUi.planetaryPositions.cols.lord', 'Lord'), lordText)}
            {professionalValue(
              t('premiumUi.planetaryPositions.condition', 'Condition'),
              lordConditions.length ? lordConditions.join(' · ') : t('premiumUi.planetaryPositions.dignities.ordinary', 'Ordinary'),
              lordState?.dignity?.key === 'db' || lordState?.dignity?.key === 'enemy' || lordState?.combust ? colors.error : colors.text,
            )}
            {lordState?.friendships?.sign_lord ? professionalValue(
              t('premiumUi.planetaryPositions.rashi', 'Rashi'),
              `${lordState.sign_name} · ${relationshipText(lordState.friendships.sign_lord.compound)}`,
              relationshipColor(lordState.friendships.sign_lord.compound),
            ) : null}
            {lordState?.nakshatra ? professionalValue(
              t('premiumUi.planetaryPositions.nakshatra', 'Nakshatra'),
              `${lordState.nakshatra} · ${t('premiumUi.planetaryPositions.nakshatraLord', 'Nakshatra lord')}: ${t(`planets.${lordState.nakshatra_lord}`, lordState.nakshatra_lord)}${lordState.friendships?.nakshatra_lord ? ` · ${relationshipText(lordState.friendships.nakshatra_lord.compound)}` : ''}`,
              relationshipColor(lordState.friendships?.nakshatra_lord?.compound),
            ) : null}

            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.planetsInHouse', 'Planets placed in this house')}
            </Text>
            {(row.occupant_details || []).length ? row.occupant_details.map((person) => {
              const conditions = [
                person.dignity ? dignityText(person.dignity) : null,
                person.retrograde ? t('premiumUi.planetaryPositions.retrograde', 'Retrograde') : null,
                person.combust ? t('premiumUi.planetaryPositions.notes.combustFull', 'Combust') : null,
                person.neecha_bhanga ? t('premiumUi.planetaryPositions.notes.neechaBhangaFull', 'Neecha Bhanga') : null,
                person.vargottama ? t('premiumUi.planetaryPositions.notes.vargottamaFull', 'Vargottama') : null,
              ].filter(Boolean);
              return professionalValue(
                t(`planets.${person.name}`, person.name),
                conditions.length ? conditions.join(' · ') : t('premiumUi.planetaryPositions.dignities.ordinary', 'Ordinary'),
              );
            }) : professionalValue(
              t('premiumUi.planetaryPositions.planetsInHouse', 'Planets placed in this house'),
              t('premiumUi.planetaryPositions.none', 'None'),
            )}

            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.aspectsToHouse', 'Aspects received by this house')}
            </Text>
            {(row.aspects_received || []).length ? row.aspects_received.map((aspect) => {
              const aspectConditions = [
                aspect.dignity ? dignityText(aspect.dignity) : null,
                aspect.retrograde ? t('premiumUi.planetaryPositions.retrograde', 'Retrograde') : null,
                aspect.combust ? t('premiumUi.planetaryPositions.notes.combustFull', 'Combust') : null,
              ].filter(Boolean);
              return professionalValue(
                t(`planets.${aspect.planet}`, aspect.planet),
                `${t('premiumUi.planetResultDelivery.aspect', '{{number}}th aspect', { number: aspect.aspect_number })} · ${t('premiumUi.planetaryPositions.fromHouse', 'from House {{number}}', { number: aspect.from_house })}${aspectConditions.length ? ` · ${aspectConditions.join(' · ')}` : ''}`,
              );
            }) : professionalValue(
              t('premiumUi.planetaryPositions.aspectsToHouse', 'Aspects received by this house'),
              t('premiumUi.planetaryPositions.none', 'None'),
            )}

            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.bhavaChalitChanges', 'Rashi and Bhava Chalit changes')}
            </Text>
            {row.bhava_chalit?.status === 'available' && row.bhava_chalit?.changes?.length ? row.bhava_chalit.changes.map((change) => professionalValue(
              t(`planets.${change.planet}`, change.planet),
              `H${change.rashi_house} → H${change.bhava_chalit_house}`,
            )) : professionalValue(
              t('premiumUi.planetaryPositions.bhavaChalitChanges', 'Rashi and Bhava Chalit changes'),
              row.bhava_chalit?.status === 'available'
                ? t('premiumUi.planetaryPositions.noBhavaChalitChange', 'No planet moves into or out of this house')
                : t('premiumUi.planetaryPositions.bhavaChalitUnavailable', 'Bhava Chalit data unavailable'),
            )}
          </View>
        ) : null}
      </View>
    );
  };

  const NakshatraPlacementCard = ({ row, detailed = false }) => {
    const meta = row.nakshatra_metadata || {};
    const pada = row.pada_details || {};
    const lord = row.nakshatra_lord_state || {};
    const specialStates = [
      row.gandanta?.is_gandanta ? t('premiumUi.planetaryPositions.gandanta', 'Gandanta') : null,
      row.boundary_proximity?.near_nakshatra_boundary ? t('premiumUi.planetaryPositions.nakshatraSandhi', 'Near Nakshatra boundary') : null,
      row.pushkara?.is_pushkara_navamsa ? t('premiumUi.planetaryPositions.pushkaraNavamsha', 'Pushkara Navamsha') : null,
      row.pushkara?.is_pushkara_bhaga ? t('premiumUi.planetaryPositions.pushkaraBhaga', 'Pushkara Bhaga') : null,
      row.vargottama ? t('premiumUi.planetaryPositions.notes.vargottamaFull', 'Vargottama') : null,
      row.combust ? t('premiumUi.planetaryPositions.notes.combustFull', 'Combust') : null,
      row.retrograde ? t('premiumUi.planetaryPositions.retrograde', 'Retrograde') : null,
      ...(row.special_roles || []).map((role) => t(
        `premiumUi.planetaryPositions.specialNakshatraRoles.${role}`,
        role === 'yogi' ? 'Yogi lord' : role === 'duplicate_yogi' ? 'Duplicate Yogi' : 'Avayogi lord',
      )),
    ].filter(Boolean);
    const ownedHouses = (lord.houses_owned || []).map((house) => `H${house}`).join(', ');
    const subject = row.name === 'Lagna' ? t('premiumUi.planetaryPositions.lagna', 'Lagna') : row.name;
    const deliveryText = lord.available
      ? t(
        'premiumUi.planetaryPositions.nakshatraDeliverySummary',
        '{{subject}} is placed in {{nakshatra}}, ruled by {{lord}}. {{lord}} is in {{sign}}, House {{house}}, and carries the result through House(s) {{houses}}.',
        { subject, nakshatra: row.nakshatra, lord: row.nakshatra_lord, sign: lord.sign_name, house: lord.house, houses: ownedHouses || '—' },
      )
      : t(
        'premiumUi.planetaryPositions.nakshatraDeliveryUnavailable',
        '{{subject}} is placed in {{nakshatra}}, ruled by {{lord}}. The lord’s placement is unavailable in this chart.',
        { subject, nakshatra: row.nakshatra, lord: row.nakshatra_lord },
      );
    return (
      <View style={[styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
        <TouchableOpacity
          style={styles.cardHeader}
          onPress={() => selectNakshatraSubject(detailed ? null : row.name)}
          accessibilityRole="button"
        >
          <View style={styles.planetInfo}>
            <View style={[styles.planetSeal, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
              <Text style={[styles.planetEmoji, { color: colors.selectionText }]}>{planetEmojis[row.name] || '⭐'}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.planetName, { color: colors.text }]}>{subject}</Text>
              <Text style={[styles.nakshatraHeadline, { color: colors.textSecondary }]}>
                {row.nakshatra} · {t('premiumUi.planetaryPositions.pada', 'Pada {{number}}', { number: row.pada })}
              </Text>
            </View>
          </View>
          <Ionicons name={detailed ? 'close' : 'chevron-forward'} size={20} color={colors.primaryStrong} />
        </TouchableOpacity>

        <View style={[styles.nakshatraQuickGrid, { borderTopColor: colors.cardBorder }]}>
          <View style={styles.nakshatraQuickItem}>
            <Text numberOfLines={3} style={[styles.detailLabel, styles.nakshatraQuickLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.degreeInNakshatra', 'Position in Nakshatra')}</Text>
            <Text style={[styles.detailValue, styles.nakshatraQuickValue, { color: colors.text }]}>{row.degree_in_nakshatra_dms?.text || '—'}</Text>
          </View>
          <View style={styles.nakshatraQuickItem}>
            <Text numberOfLines={3} style={[styles.detailLabel, styles.nakshatraQuickLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.nakshatraLord', 'Nakshatra lord')}</Text>
            <Text style={[styles.detailValue, styles.nakshatraQuickValue, { color: colors.text }]}>{row.nakshatra_lord}</Text>
          </View>
          <View style={styles.nakshatraQuickItem}>
            <Text numberOfLines={3} style={[styles.detailLabel, styles.nakshatraQuickLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.navamsa', 'Navamsa')}</Text>
            <Text style={[styles.detailValue, styles.nakshatraQuickValue, { color: colors.text }]}>{pada.navamsa_sign_name || '—'}</Text>
          </View>
        </View>

        {specialStates.length ? (
          <View style={styles.nakshatraChipRow}>
            {specialStates.map((state) => (
              <View key={state} style={[styles.nakshatraStateChip, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                <Text style={[styles.nakshatraStateText, { color: colors.textSecondary }]}>{state}</Text>
              </View>
            ))}
          </View>
        ) : null}

        {detailed ? (
          <View style={[styles.professionalPanel, styles.nakshatraDetailPanel, { borderTopColor: colors.cardBorder }]}>
            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.placementAndPada', 'Placement and Pada')}
            </Text>
            {professionalValue(t('premiumUi.planetaryPositions.rashiAndHouse', 'Rashi and house'), `${row.sign_name} · H${row.house}`)}
            {professionalValue(t('premiumUi.planetaryPositions.exactLongitude', 'Exact longitude'), `${Number(row.longitude).toFixed(6)}°`)}
            {professionalValue(t('premiumUi.planetaryPositions.padaSpan', 'Pada span within Nakshatra'), `${Number(pada.start_degree_in_nakshatra).toFixed(2)}°–${Number(pada.end_degree_in_nakshatra).toFixed(2)}°`)}
            {professionalValue(t('premiumUi.planetaryPositions.navamsaAndLord', 'Navamsa and lord'), `${pada.navamsa_sign_name || '—'} · ${pada.navamsa_lord || '—'}`)}
            {professionalValue(t('premiumUi.planetaryPositions.padaPurpose', 'Pada orientation'), t(`premiumUi.planetaryPositions.purusharthas.${pada.purushartha}`, pada.purushartha || '—'))}
            {professionalValue(
              t('premiumUi.planetaryPositions.boundaryDistance', 'Nakshatra boundaries'),
              t(
                'premiumUi.planetaryPositions.boundaryDistanceValue',
                '{{fromStart}}° from the start · {{toEnd}}° to {{next}}',
                {
                  fromStart: Number(row.boundary_proximity?.degrees_from_nakshatra_start).toFixed(2),
                  toEnd: Number(row.boundary_proximity?.degrees_to_nakshatra_end).toFixed(2),
                  next: row.boundary_proximity?.next_nakshatra || '—',
                },
              ),
            )}

            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.resultDeliveryChain', 'Result delivery chain')}
            </Text>
            <Text style={[styles.nakshatraExplanation, { color: colors.text }]}>{deliveryText}</Text>
            {lord.available ? professionalValue(t('premiumUi.planetaryPositions.lordCondition', 'Nakshatra lord condition'), [
              dignityText(lord.dignity),
              lord.retrograde ? t('premiumUi.planetaryPositions.retrograde', 'Retrograde') : null,
              lord.combust ? t('premiumUi.planetaryPositions.notes.combustFull', 'Combust') : null,
              lord.neecha_bhanga ? t('premiumUi.planetaryPositions.notes.neechaBhangaFull', 'Neecha Bhanga') : null,
              lord.vargottama ? t('premiumUi.planetaryPositions.notes.vargottamaFull', 'Vargottama') : null,
            ].filter(Boolean).join(' · ')) : null}
            {lord.available ? professionalValue(t('premiumUi.planetaryPositions.lordOwnsHouses', 'Nakshatra lord owns'), ownedHouses || '—') : null}
            {lord.friendships?.sign_lord ? professionalValue(
              t('premiumUi.planetaryPositions.lordSignRelationship', 'Lord’s relation with its Rashi lord'),
              relationshipText(lord.friendships.sign_lord.compound || lord.friendships.sign_lord.natural),
              relationshipColor(lord.friendships.sign_lord.compound || lord.friendships.sign_lord.natural),
            ) : null}
            {lord.conjunctions?.length ? professionalValue(
              t('premiumUi.planetaryPositions.lordConjunctions', 'Planets joined with the lord'),
              lord.conjunctions.map((item) => item.planet).join(', '),
            ) : null}
            {lord.aspects_received?.length ? professionalValue(
              t('premiumUi.planetaryPositions.lordAspectsReceived', 'Aspects received by the lord'),
              lord.aspects_received.map((item) => `${item.planet} (${item.aspect_numbers.join('/')})`).join(' · '),
            ) : null}
            {row.nakshatra_lord_relationship ? professionalValue(
              t('premiumUi.planetaryPositions.subjectLordRelationship', 'Planet’s relation with Nakshatra lord'),
              relationshipText(row.nakshatra_lord_relationship),
              relationshipColor(row.nakshatra_lord_relationship),
            ) : null}

            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.classicalNakshatraIdentity', 'Classical Nakshatra identity')}
            </Text>
            {professionalValue(t('premiumUi.planetaryPositions.deity', 'Deity'), meta.deity)}
            {professionalValue(t('premiumUi.planetaryPositions.symbol', 'Symbol'), meta.symbol)}
            {professionalValue(t('premiumUi.planetaryPositions.shakti', 'Shakti'), meta.shakti)}
            {professionalValue(t('premiumUi.planetaryPositions.actionClass', 'Action class'), t(`premiumUi.planetaryPositions.natureClasses.${meta.nature_class}`, meta.nature_class))}
            {professionalValue(t('premiumUi.planetaryPositions.nakshatraPurpose', 'Nakshatra orientation'), t(`premiumUi.planetaryPositions.purusharthas.${meta.purushartha}`, meta.purushartha))}

            {row.navatara ? (
              <>
                <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
                  {t('premiumUi.planetaryPositions.navataraSection', 'Navatara from the natal Moon')}
                </Text>
                {professionalValue(t('premiumUi.planetaryPositions.tara', 'Tara'), t(`premiumUi.planetaryPositions.navataraValues.${row.navatara.key}`, row.navatara.key))}
                {professionalValue(t('premiumUi.planetaryPositions.taraCount', 'Count and cycle'), t('premiumUi.planetaryPositions.taraCountValue', '{{count}} from Janma Nakshatra · cycle {{cycle}}', { count: row.navatara.count_from_birth_nakshatra, cycle: row.navatara.cycle }))}
              </>
            ) : null}

            {row.vimshottari_birth_balance ? (
              <>
                <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
                  {t('premiumUi.planetaryPositions.moonDashaStart', 'Moon’s Vimshottari starting period')}
                </Text>
                {professionalValue(t('premiumUi.planetaryPositions.startingMahadasha', 'Starting Mahadasha'), row.vimshottari_birth_balance.starting_lord)}
                {professionalValue(t('premiumUi.planetaryPositions.balanceAtBirth', 'Approximate balance at birth'), t('premiumUi.planetaryPositions.balanceYears', '{{years}} years', { years: Number(row.vimshottari_birth_balance.remaining_years).toFixed(2) }))}
              </>
            ) : null}

            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.compatibilityAttributes', 'Compatibility attributes')}
            </Text>
            {professionalValue(t('premiumUi.planetaryPositions.gana', 'Gana'), meta.gana)}
            {professionalValue(t('premiumUi.planetaryPositions.nadi', 'Nadi'), meta.nadi)}
            {professionalValue(t('premiumUi.planetaryPositions.yoni', 'Yoni'), meta.yoni)}
            <Text style={[styles.methodDisclosure, { color: colors.textSecondary, borderTopColor: colors.cardBorder }]}>
              {t('premiumUi.planetaryPositions.nakshatraSources', 'Method: 27 equal Nakshatras in the Lahiri sidereal zodiac. Deities, action classes and Ashtakoota attributes are displayed as separate traditional data families; KP sub-lords are not mixed into this table.')}
            </Text>
          </View>
        ) : null}
      </View>
    );
  };

  // Canonical special-Lagna card. Exact and sign-only points are deliberately
  // presented differently so a plotting anchor can never look like a degree.
  const LagnaCard = ({ lagna }) => {
    const expanded = !!expandedLagnas[lagna.key];
    const basis = lagna.calculation_basis || {};
    const houseGroups = (lagna.planet_houses || []).reduce((groups, row) => {
      const house = Number(row.house_from_reference);
      groups[house] = [...(groups[house] || []), row.planet];
      return groups;
    }, {});
    const name = t(`premiumUi.planetaryPositions.lagnaWorksheet.names.${lagna.key}`, lagna.name);
    const description = t(`premiumUi.planetaryPositions.lagnaWorksheet.descriptions.${lagna.key}`, '');
    const icon = {
      natal_lagna: '⬆', bhava_lagna: '🏠', hora_lagna: '💰', ghatika_lagna: '👑',
      pranapada_lagna: '〽', indu_lagna: '🌙',
    }[lagna.key] || '⭐';
    return (
      <View style={[styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
        <TouchableOpacity
          style={styles.cardHeader}
          onPress={() => setExpandedLagnas((current) => ({ ...current, [lagna.key]: !current[lagna.key] }))}
          accessibilityRole="button"
          accessibilityState={{ expanded }}
        >
          <View style={styles.planetInfo}>
            <View style={[styles.planetSeal, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
              <Text style={[styles.planetEmoji, { color: colors.selectionText }]}>{icon}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.planetName, { color: colors.text }]}>{name}</Text>
              {description ? (
                <Text style={[styles.lagnaDescription, { color: colors.textSecondary }]}>{description}</Text>
              ) : null}
            </View>
          </View>
          <View style={styles.lagnaHeaderRight}>
            <View style={[styles.houseTag, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
              <Text style={[styles.houseText, { color: colors.selectionText }]}>{t('premiumUi.planetaryPositions.house', 'House {{number}}', { number: lagna.house })}</Text>
            </View>
            <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={18} color={colors.textSecondary} />
          </View>
        </TouchableOpacity>
        <View style={[styles.divider, { backgroundColor: colors.cardBorder }]} />
        <View style={styles.detailsGrid}>
          <View style={styles.detailItem}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.rashi', 'Rashi')}</Text>
            <View style={styles.rashiContainer}>
              <Text style={styles.rashiIcon}>{rashiIcons[lagna.sign]}</Text>
              <Text style={[styles.detailValue, { color: colors.text }]}>{rashiNames[lagna.sign]}</Text>
            </View>
          </View>
          {lagna.precision !== 'sign_only' ? (
            <>
              <View style={styles.detailItem}>
                <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.degree', 'Degree')}</Text>
                <Text style={[styles.detailValue, { color: colors.text }]}>{formatPointDegrees(lagna.degree)}</Text>
              </View>
              {lagna.nakshatra ? <View style={styles.detailItemFull}>
                <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.nakshatra', 'Nakshatra')}</Text>
                <Text style={[styles.detailValue, styles.detailValueWide, { color: colors.text }]}>{lagna.nakshatra} · {t('premiumUi.planetaryPositions.pada', 'Pada {{number}}', { number: lagna.pada })}</Text>
              </View> : null}
            </>
          ) : (
            <View style={styles.detailItem}>
              <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.lagnaWorksheet.precision', 'Precision')}</Text>
              <Text style={[styles.detailValue, { color: colors.text }]}>{t('premiumUi.planetaryPositions.lagnaWorksheet.signOnly', 'Sign only')}</Text>
            </View>
          )}
        </View>
        {expanded ? (
          <View style={[styles.lagnaExpanded, { borderTopColor: colors.cardBorder }]}>
            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.lagnaWorksheet.calculation', 'How it is calculated')}
            </Text>
            {professionalValue(
              t('premiumUi.planetaryPositions.lagnaWorksheet.formula', 'Formula'),
              t(`premiumUi.planetaryPositions.lagnaWorksheet.formulas.${lagna.key}`, basis.formula),
            )}
            {basis.applicable_sunrise_local ? professionalValue(
              t('premiumUi.planetaryPositions.lagnaWorksheet.sunrise', 'Applicable sunrise'),
              basis.applicable_sunrise_local.replace('T', ' '),
            ) : null}
            {Number.isFinite(Number(basis.sun_longitude_at_sunrise)) ? professionalValue(
              t('premiumUi.planetaryPositions.lagnaWorksheet.sunAtSunrise', 'Sun at sunrise'),
              `${Number(basis.sun_longitude_at_sunrise).toFixed(4)}°`,
            ) : null}
            {Number.isFinite(Number(basis.elapsed_ghatis)) ? professionalValue(
              t('premiumUi.planetaryPositions.lagnaWorksheet.elapsedGhatis', 'Elapsed ghatis'),
              Number(basis.elapsed_ghatis).toFixed(4),
            ) : null}
            {Number.isFinite(Number(basis.ghatis_per_sign)) ? professionalValue(
              t('premiumUi.planetaryPositions.lagnaWorksheet.rate', 'Rate'),
              t('premiumUi.planetaryPositions.lagnaWorksheet.rateValue', '1 sign per {{count}} ghatis', { count: basis.ghatis_per_sign }),
            ) : null}

            <Text style={[styles.professionalSectionTitle, { color: colors.primaryStrong }]}>
              {t('premiumUi.planetaryPositions.lagnaWorksheet.planetsFromHere', 'Planets from this Lagna')}
            </Text>
            <View style={styles.jaiminiChipWrap}>
              {Object.entries(houseGroups).sort(([a], [b]) => Number(a) - Number(b)).map(([house, occupants]) => (
                <View key={`${lagna.key}-h${house}`} style={[styles.jaiminiDataChip, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                  <Text style={[styles.jaiminiDataChipTitle, { color: colors.text }]}>H{house}</Text>
                  <Text style={[styles.jaiminiDataChipBody, { color: colors.textSecondary }]}>{occupants.join(', ')}</Text>
                </View>
              ))}
            </View>
            <Text style={[styles.methodDisclosure, { color: colors.textSecondary, borderTopColor: colors.cardBorder }]}>
              {basis.reference || professionalSpecialPoints?.special_lagnas?.calculation_basis?.reference}
            </Text>
          </View>
        ) : null}
      </View>
    );
  };

  const renderJaiminiTab = () => {
    if (jaiminiLoading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
            {t('premiumUi.planetaryPositions.jaimini.loading', 'Calculating the Jaimini worksheet…')}
          </Text>
        </View>
      );
    }
    if (jaiminiError || !professionalJaimini) {
      return (
        <View style={[styles.jaiminiErrorCard, { backgroundColor: colors.surfaceRaised, borderColor: colors.error }]}>
          <Ionicons name="alert-circle-outline" size={22} color={colors.error} />
          <View style={styles.jaiminiErrorCopy}>
            <Text style={[styles.jaiminiSectionTitle, { color: colors.text }]}>
              {t('premiumUi.planetaryPositions.jaimini.unavailable', 'Jaimini calculation is unavailable')}
            </Text>
            <Text style={[styles.jaiminiBody, { color: colors.textSecondary }]}>{String(jaiminiError || '—')}</Text>
            <TouchableOpacity style={[styles.jaiminiRetry, { borderColor: colors.selectionBorder }]} onPress={loadProfessionalJaimini}>
              <Text style={[styles.jaiminiRetryText, { color: colors.primary }]}>{t('premiumUi.common.retry', 'Try again')}</Text>
            </TouchableOpacity>
          </View>
        </View>
      );
    }

    const scheme = professionalJaimini.karaka_schemes?.[jaiminiScheme];
    const reference = professionalJaimini.svamsha_karakamsha?.[jaiminiScheme];
    const padas = professionalJaimini.arudha_padas || [];
    const principalPadas = professionalJaimini.principal_padas || {};
    const drishtiRows = professionalJaimini.rashi_drishti || [];
    const occupiedRows = (rows = []) => rows.filter((row) => row.occupants?.length);
    const roleLabel = (row) => t(`premiumUi.planetaryPositions.jaimini.roles.${row.karaka_code}`, row.karaka_name);

    const Section = ({ title, subtitle, children }) => (
      <View style={[styles.jaiminiSection, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
        <Text style={[styles.jaiminiSectionTitle, { color: colors.text }]}>{title}</Text>
        {subtitle ? <Text style={[styles.jaiminiSectionSubtitle, { color: colors.textSecondary }]}>{subtitle}</Text> : null}
        <View style={[styles.jaiminiDivider, { backgroundColor: colors.cardBorder }]} />
        {children}
      </View>
    );

    return (
      <View>
        <View style={[styles.methodNote, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
          <Ionicons name="book-outline" size={17} color={colors.primary} />
          <Text style={[styles.methodNoteText, { color: colors.textSecondary }]}>
            {t('premiumUi.planetaryPositions.jaimini.intro', 'A structural Jaimini worksheet. Seven- and eight-karaka schemes remain separate, and every Pada shows its calculation. No Parashari graha aspects are mixed into Rashi Drishti.')}
          </Text>
        </View>

        <View style={[styles.jaiminiSchemeSelector, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
          {['seven', 'eight'].map((value) => {
            const selected = jaiminiScheme === value;
            return (
              <TouchableOpacity
                key={value}
                style={[styles.jaiminiSchemeButton, selected && { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}
                onPress={() => setJaiminiScheme(value)}
                accessibilityRole="tab"
                accessibilityState={{ selected }}
              >
                <Text style={[styles.jaiminiSchemeLabel, { color: selected ? colors.selectionText : colors.textSecondary }]}>
                  {value === 'seven'
                    ? t('premiumUi.planetaryPositions.jaimini.sevenKaraka', '7 Karakas')
                    : t('premiumUi.planetaryPositions.jaimini.eightKaraka', '8 Karakas · Rahu')}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <Section
          title={t('premiumUi.planetaryPositions.jaimini.charaKarakas', 'Chara Karakas')}
          subtitle={jaiminiScheme === 'seven'
            ? t('premiumUi.planetaryPositions.jaimini.sevenMethod', 'Seven visible grahas ranked by their degree within the sign.')
            : t('premiumUi.planetaryPositions.jaimini.eightMethod', 'Seven visible grahas plus Rahu, whose progress is measured in reverse from 30°.')}
        >
          {scheme?.tie_groups?.length ? (
            <View style={[styles.jaiminiNotice, { backgroundColor: colors.surfaceMuted, borderColor: colors.warning }]}>
              <Ionicons name="warning-outline" size={18} color={colors.warning} />
              <Text style={[styles.jaiminiNoticeText, { color: colors.textSecondary }]}>
                {t('premiumUi.planetaryPositions.jaimini.degreeTie', 'A degree tie was found. Its resolution depends on the selected commentary, so the ambiguity is shown.')}
              </Text>
            </View>
          ) : null}
          {(scheme?.rows || []).map((row) => (
            <View key={`${jaiminiScheme}-${row.karaka_code}`} style={[styles.jaiminiKarakaRow, { borderBottomColor: colors.cardBorder }]}>
              <View style={[styles.jaiminiCodeBadge, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
                <Text style={[styles.jaiminiCode, { color: colors.selectionText }]}>{row.karaka_code}</Text>
                <Text style={[styles.jaiminiRank, { color: colors.textSecondary }]}>{row.rank}</Text>
              </View>
              <View style={styles.jaiminiKarakaCopy}>
                <Text style={[styles.jaiminiKarakaRole, { color: colors.textSecondary }]}>{roleLabel(row)}</Text>
                <Text style={[styles.jaiminiKarakaPlanet, { color: colors.text }]}>{planetEmojis[row.planet] || '⭐'} {row.planet} · {row.degree_text}</Text>
                <Text style={[styles.jaiminiMeta, { color: colors.textSecondary }]}>
                  {t('premiumUi.planetaryPositions.jaimini.d1Placement', 'D1 {{sign}} · H{{house}}', { sign: row.sign_name, house: row.house })}
                  {'  ·  '}
                  {t('premiumUi.planetaryPositions.jaimini.d9Placement', 'D9 {{sign}}', { sign: row.d9_sign_name || '—' })}
                </Text>
                {row.measured_in_reverse ? (
                  <Text style={[styles.jaiminiReverse, { color: colors.primary }]}>
                    {t('premiumUi.planetaryPositions.jaimini.rahuReverse', 'Rahu ranking measure: {{degree}}', { degree: row.ranking_degree_text })}
                  </Text>
                ) : null}
              </View>
            </View>
          ))}
          <Text style={[styles.methodDisclosure, { color: colors.textSecondary, borderTopColor: colors.cardBorder }]}>{professionalJaimini.calculation_basis?.karakas?.reference}</Text>
        </Section>

        <Section
          title={t('premiumUi.planetaryPositions.jaimini.svamshaKarakamsha', 'Swamsha and Karakamsha')}
          subtitle={t('premiumUi.planetaryPositions.jaimini.svamshaIntro', 'This screen calls the Atmakaraka’s Navamsha sign Swamsha and uses the same sign as the Karakamsha reference in D1. Commentarial terminology varies.')}
        >
          <View style={styles.jaiminiReferenceHeader}>
            <View style={[styles.jaiminiSignSeal, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
              <Text style={styles.jaiminiSignIcon}>{rashiIcons[reference?.sign_id] || '◇'}</Text>
            </View>
            <View style={styles.jaiminiReferenceCopy}>
              <Text style={[styles.jaiminiReferenceSign, { color: colors.text }]}>{reference?.sign_name || '—'}</Text>
              <Text style={[styles.jaiminiMeta, { color: colors.textSecondary }]}>
                {t('premiumUi.planetaryPositions.jaimini.akInD9', '{{planet}} is Atmakaraka and occupies this sign in D9.', { planet: reference?.atmakaraka || '—' })}
              </Text>
            </View>
          </View>
          <Text style={[styles.jaiminiSubheading, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.jaimini.d1FromKarakamsha', 'D1 planets from Karakamsha')}</Text>
          <View style={styles.jaiminiChipWrap}>
            {occupiedRows(reference?.d1_reference_houses).map((row) => (
              <View key={`d1-${row.house}`} style={[styles.jaiminiDataChip, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
                <Text style={[styles.jaiminiDataChipTitle, { color: colors.text }]}>H{row.house} · {row.sign_name}</Text>
                <Text style={[styles.jaiminiDataChipBody, { color: colors.textSecondary }]}>{row.occupants.join(', ')}</Text>
              </View>
            ))}
          </View>
          <Text style={[styles.jaiminiSubheading, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.jaimini.d9FromSwamsha', 'D9 planets from Swamsha')}</Text>
          <View style={styles.jaiminiChipWrap}>
            {occupiedRows(reference?.d9_reference_houses).map((row) => (
              <View key={`d9-${row.house}`} style={[styles.jaiminiDataChip, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
                <Text style={[styles.jaiminiDataChipTitle, { color: colors.text }]}>H{row.house} · {row.sign_name}</Text>
                <Text style={[styles.jaiminiDataChipBody, { color: colors.textSecondary }]}>{row.occupants.join(', ')}</Text>
              </View>
            ))}
          </View>
          <Text style={[styles.methodDisclosure, { color: colors.textSecondary, borderTopColor: colors.cardBorder }]}>{professionalJaimini.calculation_basis?.svamsha?.reference}</Text>
        </Section>

        <Section
          title={t('premiumUi.planetaryPositions.jaimini.principalPadas', 'Principal Arudha Padas')}
          subtitle={t('premiumUi.planetaryPositions.jaimini.principalPadasIntro', 'The three most frequently consulted Padas are shown first; the complete A1–A12 worksheet follows.')}
        >
          <View style={styles.jaiminiPrincipalGrid}>
            {[
              ['AL', principalPadas.arudha_lagna, t('premiumUi.planetaryPositions.jaimini.arudhaLagna', 'Arudha Lagna')],
              ['A7', principalPadas.darapada, t('premiumUi.planetaryPositions.jaimini.darapada', 'Darapada')],
              ['UL', principalPadas.upapada, t('premiumUi.planetaryPositions.jaimini.upapada', 'Upapada')],
            ].map(([code, row, label]) => row ? (
              <View key={code} style={[styles.jaiminiPrincipalCard, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
                <Text style={[styles.jaiminiPrincipalCode, { color: colors.primary }]}>{code}</Text>
                <Text style={[styles.jaiminiPrincipalSign, { color: colors.text }]}>{row.sign_name}</Text>
                <Text style={[styles.jaiminiMeta, { color: colors.textSecondary }]}>{label} · H{row.house_from_lagna}</Text>
              </View>
            ) : null)}
          </View>
        </Section>

        <Section
          title={t('premiumUi.planetaryPositions.jaimini.allPadas', 'A1–A12 calculation table')}
          subtitle={t('premiumUi.planetaryPositions.jaimini.allPadasIntro', 'Each row shows the source sign, its lord’s placement, and the resulting Pada.')}
        >
          {padas.map((row) => (
            <View key={row.code} style={[styles.jaiminiPadaRow, { borderBottomColor: colors.cardBorder }]}>
              <View style={[styles.jaiminiPadaCode, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
                <Text style={[styles.jaiminiCode, { color: colors.selectionText }]}>{row.code}</Text>
              </View>
              <View style={styles.jaiminiPadaCopy}>
                <Text style={[styles.jaiminiPadaResult, { color: colors.text }]}>{row.sign_name} · H{row.house_from_lagna}</Text>
                <Text style={[styles.jaiminiMeta, { color: colors.textSecondary }]}>
                  {t('premiumUi.planetaryPositions.jaimini.padaDerivation', '{{source}} → lord {{lord}} in {{lordSign}} · count {{count}} signs → {{result}}', { source: row.source_sign_name, lord: row.lord, lordSign: row.lord_sign_name, count: row.distance_signs, result: row.sign_name })}
                </Text>
                {row.exception_applied ? (
                  <Text style={[styles.jaiminiException, { color: colors.primary }]}>
                    {row.exception === 'lord_in_1_or_7_take_10'
                      ? t('premiumUi.planetaryPositions.jaimini.tenthException', 'Exception: lord in 1st/7th; the 10th from the source is used.')
                      : t('premiumUi.planetaryPositions.jaimini.fourthException', 'Exception: lord in 4th/10th; the 4th from the source is used.')}
                  </Text>
                ) : null}
              </View>
            </View>
          ))}
          <Text style={[styles.methodDisclosure, { color: colors.textSecondary, borderTopColor: colors.cardBorder }]}>
            {professionalJaimini.calculation_basis?.arudha?.reference}{'\n'}
            {t('premiumUi.planetaryPositions.jaimini.lordshipConvention', 'Classical seven-graha lordship is used: Mars rules Scorpio and Saturn rules Aquarius; nodes are not used as co-lords.')}
          </Text>
        </Section>

        <Section
          title={t('premiumUi.planetaryPositions.jaimini.rashiDrishti', 'Rashi Drishti')}
          subtitle={t('premiumUi.planetaryPositions.jaimini.rashiDrishtiIntro', 'These are sign aspects. Every planet in the source sign shares that sign’s Rashi Drishti.')}
        >
          {drishtiRows.map((row) => (
            <View key={row.sign_id} style={[styles.jaiminiDrishtiRow, { borderBottomColor: colors.cardBorder }]}>
              <View style={styles.jaiminiDrishtiSource}>
                <Text style={[styles.jaiminiDrishtiSign, { color: colors.text }]}>{rashiIcons[row.sign_id]} {row.sign_name}</Text>
                <Text style={[styles.jaiminiMeta, { color: colors.textSecondary }]}>
                  {t(`premiumUi.planetaryPositions.jaimini.modalities.${row.modality}`, row.modality)}{row.occupants?.length ? ` · ${row.occupants.join(', ')}` : ''}
                </Text>
              </View>
              <Ionicons name="arrow-forward" size={16} color={colors.primary} />
              <Text style={[styles.jaiminiDrishtiTargets, { color: colors.textSecondary }]}>
                {row.aspected_signs.map((target) => `${target.sign_name}${target.occupants?.length ? ` (${target.occupants.join(', ')})` : ''}`).join(' · ')}
              </Text>
            </View>
          ))}
          <Text style={[styles.methodDisclosure, { color: colors.textSecondary, borderTopColor: colors.cardBorder }]}>{professionalJaimini.calculation_basis?.rashi_drishti?.reference}</Text>
        </Section>
      </View>
    );
  };

  const renderNatalPromiseTab = () => {
    if (natalPromiseLoading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
            {t('premiumUi.planetaryPositions.natalPromise.loading', 'Reading the published classical rules…')}
          </Text>
        </View>
      );
    }
    if (natalPromiseError || !natalPromise?.areas?.length) {
      return (
        <View style={[styles.methodNote, { backgroundColor: colors.surfaceMuted, borderColor: colors.warning }]}>
          <Ionicons name="alert-circle-outline" size={18} color={colors.warning} />
          <View style={{ flex: 1 }}>
            <Text style={[styles.methodNoteText, { color: colors.textSecondary }]}>
              {natalPromiseError || t('premiumUi.planetaryPositions.natalPromise.unavailable', 'The classical natal reading is unavailable for this chart.')}
            </Text>
            <TouchableOpacity onPress={() => { setNatalPromiseLoaded(false); }} style={styles.promiseRetry}>
              <Text style={[styles.promiseRetryText, { color: colors.primary }]}>{t('premiumUi.common.tryAgain', 'Try again')}</Text>
            </TouchableOpacity>
          </View>
        </View>
      );
    }
    const selected = natalPromise.areas.find((row) => row.house === selectedPromiseHouse) || natalPromise.areas[0];
    const allSelectedInsights = selected.insights || [];
    const subjects = selected.subjects || [];
    const activeSubject = selectedPromiseSubject === 'all' || subjects.some((subject) => subject.key === selectedPromiseSubject)
      ? selectedPromiseSubject
      : 'all';
    const selectedInsights = activeSubject === 'all'
      ? allSelectedInsights
      : allSelectedInsights.filter((insight) => insight.subject?.key === activeSubject);
    const visibleSupports = [...new Set(selectedInsights.flatMap((insight) => insight.supports || []))];
    const visiblePressures = [...new Set(selectedInsights.flatMap((insight) => insight.pressures || []))];
    const conditionKey = visibleSupports.length && visiblePressures.length
      ? 'mixed'
      : visibleSupports.length ? 'supported' : visiblePressures.length ? 'under_pressure' : 'unqualified';
    const visibleSources = selectedInsights
      .flatMap((insight) => insight.sources || [])
      .filter((source, index, rows) => rows.findIndex((row) => row.rule_key === source.rule_key && row.reference === source.reference) === index);
    const conditionLabels = {
      supported: t('premiumUi.planetaryPositions.natalPromise.supported', 'Supported'),
      mixed: t('premiumUi.planetaryPositions.natalPromise.mixed', 'Support and pressure'),
      under_pressure: t('premiumUi.planetaryPositions.natalPromise.underPressure', 'Under pressure'),
      unqualified: t('premiumUi.planetaryPositions.natalPromise.unqualified', 'No strong modifier'),
    };
    const conditionColor = conditionKey === 'supported' ? colors.success : conditionKey === 'under_pressure' ? colors.warning : colors.primary;
    const insightReading = (insight) => (insight.statements || [])
      .map((statement) => t(statement.key, statement.text || '', statement.parameters || {}))
      .filter(Boolean)
      .map((outcome) => `${outcome.charAt(0).toUpperCase()}${outcome.slice(1).replace(/[.!?]+$/, '')}.`)
      .join(' ');
    return (
      <View>
        <View style={[styles.methodNote, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
          <Ionicons name="book-outline" size={18} color={colors.primary} />
          <Text style={[styles.methodNoteText, { color: colors.textSecondary }]}>
            {t('premiumUi.planetaryPositions.natalPromise.intro', 'This natal reading brings together every published classical indication for the selected area. It describes tendencies in the birth chart; timing is evaluated separately.')}
          </Text>
        </View>

        <Text style={[styles.promiseSelectorLabel, { color: colors.textSecondary }]}>
          {t('premiumUi.planetaryPositions.natalPromise.currentArea', 'Life area')}
        </Text>
        <TouchableOpacity
          style={[styles.promiseSelector, { backgroundColor: colors.surface, borderColor: colors.selectionBorder }]}
          onPress={() => setPromiseAreaPickerOpen(true)}
          accessibilityRole="button"
          accessibilityLabel={t('premiumUi.planetaryPositions.natalPromise.lifeOverview', 'Choose an area of life')}
        >
          <View style={[styles.promiseSelectorHouse, { backgroundColor: colors.selectionBackground }]}>
            <Text style={[styles.promiseSelectorHouseText, { color: colors.primary }]}>H{selected.house}</Text>
          </View>
          <Text numberOfLines={2} style={[styles.promiseSelectorValue, { color: colors.text }]}>
            {t(`premiumUi.planetaryPositions.natalPromise.areas.${selected.house}`, selected.label)}
          </Text>
          <Ionicons name="chevron-down" size={20} color={colors.primary} />
        </TouchableOpacity>

        <Modal
          visible={promiseAreaPickerOpen}
          transparent
          animationType="slide"
          statusBarTranslucent
          onRequestClose={() => setPromiseAreaPickerOpen(false)}
        >
          <View style={styles.promiseModalRoot}>
            <Pressable
              style={styles.promiseModalBackdrop}
              onPress={() => setPromiseAreaPickerOpen(false)}
              accessibilityRole="button"
              accessibilityLabel={t('premiumUi.common.close', 'Close')}
            />
            <View
              style={[
                styles.promiseSheet,
                {
                  backgroundColor: colors.background,
                  borderColor: colors.cardBorder,
                  paddingBottom: Math.max(insets.bottom, 16),
                },
              ]}
            >
              <View style={[styles.promiseSheetGrabber, { backgroundColor: colors.cardBorder }]} />
              <View style={styles.promiseSheetHeader}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.promiseSheetTitle, { color: colors.text }]}>
                    {t('premiumUi.planetaryPositions.natalPromise.lifeOverview', 'Choose an area of life')}
                  </Text>
                  <Text style={[styles.promiseSheetSubtitle, { color: colors.textSecondary }]}>
                    {t('premiumUi.planetaryPositions.natalPromise.pickerHint', 'The reading below will change to the area you select.')}
                  </Text>
                </View>
                <TouchableOpacity
                  onPress={() => setPromiseAreaPickerOpen(false)}
                  style={[styles.promiseSheetClose, { backgroundColor: colors.surfaceMuted }]}
                  accessibilityRole="button"
                  accessibilityLabel={t('premiumUi.common.close', 'Close')}
                >
                  <Ionicons name="close" size={21} color={colors.text} />
                </TouchableOpacity>
              </View>
              <GHScrollView
                style={styles.promiseSheetList}
                contentContainerStyle={styles.promiseSheetListContent}
                showsVerticalScrollIndicator={false}
              >
                {natalPromise.areas.map((row) => {
                  const active = row.house === selected.house;
                  return (
                    <TouchableOpacity
                      key={row.key}
                      onPress={() => {
                        setSelectedPromiseHouse(row.house);
                        setShowPromiseEvidence(false);
                        setSelectedPromiseSubject('all');
                        setPromiseAreaPickerOpen(false);
                      }}
                      style={[
                        styles.promiseSheetRow,
                        {
                          backgroundColor: active ? colors.selectionBackground : colors.surface,
                          borderColor: active ? colors.selectionBorder : colors.cardBorder,
                        },
                      ]}
                      accessibilityRole="button"
                      accessibilityState={{ selected: active }}
                    >
                      <View style={[styles.promiseSheetHouse, { backgroundColor: active ? colors.primary : colors.surfaceMuted }]}>
                        <Text style={[styles.promiseSheetHouseText, { color: active ? colors.onPrimary : colors.textSecondary }]}>H{row.house}</Text>
                      </View>
                      <Text style={[styles.promiseSheetRowTitle, { color: colors.text }]}>
                        {t(`premiumUi.planetaryPositions.natalPromise.areas.${row.house}`, row.label)}
                      </Text>
                      {active ? <Ionicons name="checkmark-circle" size={21} color={colors.primary} /> : null}
                    </TouchableOpacity>
                  );
                })}
              </GHScrollView>
            </View>
          </View>
        </Modal>

        {subjects.length > 1 ? (
          <>
            <Text style={[styles.promiseSelectorLabel, { color: colors.textSecondary }]}>
              {t('premiumUi.planetaryPositions.natalPromise.currentTopic', 'Topic')}
            </Text>
            <TouchableOpacity
              style={[styles.promiseTopicSelector, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}
              onPress={() => setPromiseSubjectPickerOpen(true)}
              accessibilityRole="button"
              accessibilityLabel={t('premiumUi.planetaryPositions.natalPromise.chooseTopic', 'Choose a topic')}
            >
              <Ionicons name="layers-outline" size={19} color={colors.primary} />
              <Text style={[styles.promiseTopicValue, { color: colors.text }]}>
                {activeSubject === 'all'
                  ? t('premiumUi.planetaryPositions.natalPromise.allTopics', 'All indications')
                  : t(
                    subjects.find((subject) => subject.key === activeSubject)?.label_key,
                    subjects.find((subject) => subject.key === activeSubject)?.label,
                  )}
              </Text>
              <Ionicons name="chevron-down" size={18} color={colors.primary} />
            </TouchableOpacity>
            <Modal
              visible={promiseSubjectPickerOpen}
              transparent
              animationType="slide"
              statusBarTranslucent
              onRequestClose={() => setPromiseSubjectPickerOpen(false)}
            >
              <View style={styles.promiseModalRoot}>
                <Pressable style={styles.promiseModalBackdrop} onPress={() => setPromiseSubjectPickerOpen(false)} />
                <View
                  style={[
                    styles.promiseSheet,
                    {
                      backgroundColor: colors.background,
                      borderColor: colors.cardBorder,
                      paddingBottom: Math.max(insets.bottom, 16),
                    },
                  ]}
                >
                  <View style={[styles.promiseSheetGrabber, { backgroundColor: colors.cardBorder }]} />
                  <View style={styles.promiseSheetHeader}>
                    <Text style={[styles.promiseSheetTitle, { color: colors.text, flex: 1 }]}>
                      {t('premiumUi.planetaryPositions.natalPromise.chooseTopic', 'Choose a topic')}
                    </Text>
                    <TouchableOpacity
                      onPress={() => setPromiseSubjectPickerOpen(false)}
                      style={[styles.promiseSheetClose, { backgroundColor: colors.surfaceMuted }]}
                    >
                      <Ionicons name="close" size={21} color={colors.text} />
                    </TouchableOpacity>
                  </View>
                  <GHScrollView style={styles.promiseSheetList} contentContainerStyle={styles.promiseSheetListContent}>
                    {[
                      {
                        key: 'all',
                        label: t('premiumUi.planetaryPositions.natalPromise.allTopics', 'All indications'),
                        count: allSelectedInsights.length,
                      },
                      ...subjects.map((subject) => ({
                        key: subject.key,
                        label: t(subject.label_key, subject.label),
                        count: subject.insight_ids?.length || 0,
                      })),
                    ].map((subject) => {
                      const active = subject.key === activeSubject;
                      return (
                        <TouchableOpacity
                          key={subject.key}
                          onPress={() => {
                            setSelectedPromiseSubject(subject.key);
                            setShowPromiseEvidence(false);
                            setPromiseSubjectPickerOpen(false);
                          }}
                          style={[
                            styles.promiseSheetRow,
                            {
                              backgroundColor: active ? colors.selectionBackground : colors.surface,
                              borderColor: active ? colors.selectionBorder : colors.cardBorder,
                            },
                          ]}
                          accessibilityRole="button"
                          accessibilityState={{ selected: active }}
                        >
                          <Text style={[styles.promiseSheetRowTitle, { color: colors.text }]}>{subject.label}</Text>
                          <Text style={[styles.promiseTopicCount, { color: colors.textSecondary }]}>{subject.count}</Text>
                          {active ? <Ionicons name="checkmark-circle" size={21} color={colors.primary} /> : null}
                        </TouchableOpacity>
                      );
                    })}
                  </GHScrollView>
                </View>
              </View>
            </Modal>
          </>
        ) : null}

        <View style={[styles.promiseCard, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
          <Text style={[styles.promiseEyebrow, { color: colors.primary }]}>
            {t(`premiumUi.planetaryPositions.natalPromise.areas.${selected.house}`, selected.label)}
          </Text>
          <Text style={[styles.promiseReadingLabel, { color: colors.textSecondary }]}>
            {t('premiumUi.planetaryPositions.natalPromise.yourReading', 'Your reading')}
          </Text>
          <View style={styles.promiseReadingStack}>
            {selectedInsights.map((insight) => (
              <View key={insight.insight_id}>
                {selectedInsights.length > 1 ? (
                  <Text style={[styles.promiseInsightSubject, { color: colors.primary }]}>
                    {t(insight.subject?.label_key, insight.subject?.label)}
                  </Text>
                ) : null}
                <Text style={[styles.promiseReading, { color: colors.text }]}>{insightReading(insight)}</Text>
              </View>
            ))}
          </View>
          <View style={[styles.promiseCondition, { backgroundColor: colors.surfaceMuted, borderColor: conditionColor }]}>
            <Text style={[styles.promiseConditionLabel, { color: conditionColor }]}>{conditionLabels[conditionKey]}</Text>
          </View>

          {(visibleSupports.length || visiblePressures.length) ? (
            <View style={styles.promiseBalanceGrid}>
              {visibleSupports.length ? (
                <View style={[styles.promiseBalanceCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.success }]}>
                  <Text style={[styles.promiseBalanceTitle, { color: colors.success }]}>{t('premiumUi.planetaryPositions.natalPromise.supportTitle', 'What supports this area')}</Text>
                  <Text style={[styles.promiseBalanceText, { color: colors.textSecondary }]}>{visibleSupports.join(' · ')}</Text>
                </View>
              ) : null}
              {visiblePressures.length ? (
                <View style={[styles.promiseBalanceCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.warning }]}>
                  <Text style={[styles.promiseBalanceTitle, { color: colors.warning }]}>{t('premiumUi.planetaryPositions.natalPromise.effortTitle', 'What may require effort')}</Text>
                  <Text style={[styles.promiseBalanceText, { color: colors.textSecondary }]}>{visiblePressures.join(' · ')}</Text>
                </View>
              ) : null}
            </View>
          ) : null}

          <TouchableOpacity
            style={[styles.promiseBasisLink, { borderTopColor: colors.cardBorder }]}
            onPress={() => setShowPromiseEvidence((open) => !open)}
            accessibilityRole="button"
          >
            <View style={{ flex: 1 }}>
              <Text style={[styles.promiseBasisTitle, { color: colors.primary }]}>
                {t('premiumUi.planetaryPositions.natalPromise.classicalBasisCount', 'Classical basis · {{count}} indication', {
                  count: selectedInsights.length,
                })}
              </Text>
              <Text style={[styles.promiseBasisReference, { color: colors.textSecondary }]}>
                {visibleSources.map((source) => source.reference).filter(Boolean).join(' · ')}
              </Text>
            </View>
            <Ionicons name={showPromiseEvidence ? 'chevron-up' : 'chevron-down'} size={18} color={colors.primary} />
          </TouchableOpacity>

          {showPromiseEvidence ? (
            <View style={[styles.promiseBasisPanel, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
              {selectedInsights.map((insight, insightIndex) => (
                <View
                  key={insight.insight_id}
                  style={[
                    styles.promiseInsightEvidence,
                    insightIndex > 0 ? { borderTopColor: colors.cardBorder, borderTopWidth: StyleSheet.hairlineWidth, marginTop: 5, paddingTop: 12 } : null,
                  ]}
                >
                  {selectedInsights.length > 1 ? (
                    <Text style={[styles.promiseSectionTitle, { color: colors.text }]}>
                      {t(insight.subject?.label_key, insight.subject?.label)}
                    </Text>
                  ) : null}
                  {(insight.contributions || []).map((contribution) => {
                    const evidence = contribution.evidence || {};
                    return (
                      <View key={`${insight.insight_id}-${contribution.work_key}-${contribution.chapter}`} style={styles.promiseContribution}>
                        <Text style={[styles.promiseBasisPlacement, { color: colors.text }]}>
                          {t(evidence.summary?.key, evidence.summary?.text, evidence.summary?.parameters || {})}
                        </Text>
                        {(evidence.facts || []).map((fact) => (
                          <Text
                            key={fact.key}
                            style={[
                              styles.promiseEvidenceText,
                              {
                                color: fact.state === 'support'
                                  ? colors.success
                                  : fact.state === 'pressure' ? colors.warning : colors.textSecondary,
                              },
                            ]}
                          >
                            {fact.label}: {fact.value}
                          </Text>
                        ))}
                        {(contribution.sources || []).map((source) => (
                          <TouchableOpacity
                            key={`${source.rule_key}-${source.reference}`}
                            onPress={() => Linking.openURL(source.witness_url)}
                            disabled={!source.witness_url}
                          >
                            <Text style={[styles.promiseSourceLink, { color: colors.primary }]}>
                              {t('premiumUi.planetaryPositions.natalPromise.openSource', 'Open source witness')} · {source.reference}
                            </Text>
                          </TouchableOpacity>
                        ))}
                      </View>
                    );
                  })}
                  {(insight.controls || []).map((control) => (
                    <Text key={control.key} style={[styles.promiseEvidenceText, { color: colors.textSecondary }]}>
                      {control.reference}: {t(control.key, control.text)}
                    </Text>
                  ))}
                </View>
              ))}
            </View>
          ) : null}

          <Text style={[styles.promiseBoundary, { color: colors.textSecondary, borderTopColor: colors.cardBorder }]}>
            {t('premiumUi.planetaryPositions.natalPromise.notCertainty', 'A natal tendency is not a guaranteed event; timing is not evaluated here.')}
          </Text>
        </View>
      </View>
    );
  };

  const chartUnavailable = (
    <View style={styles.loadingContainer}>
      <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
        Chart data is still loading or unavailable. Open your chart first, then try again.
      </Text>
    </View>
  );

  // Render Tab Content
  const renderTabContent = () => {
    if (loading && ['planets', 'houses', 'nakshatras'].includes(activeTab)) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('premiumUi.common.loading', 'Loading…')}</Text>
        </View>
      );
    }
    if (activeTab === 'planets') {
      if (!planetsPayload || planets.length === 0) return chartUnavailable;
      return (
        <View>
          <View style={[styles.methodNote, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
            <Ionicons name="book-outline" size={17} color={colors.primary} />
            <Text style={[styles.methodNoteText, { color: colors.textSecondary }]}>
              {t(
                'premiumUi.planetaryPositions.combustionReference',
                'Combustion: BPHS 7.28–29; direct/retrograde limits from R. Santhanam, Vol. I, pp. 99–100.',
              )}
            </Text>
          </View>
          {selectedPlanet
            ? <PlanetCard key={selectedPlanet.name} planet={selectedPlanet} />
            : planets.map((planet) => <PlanetCard key={planet.name} planet={planet} />)}
        </View>
      );
    }

    if (activeTab === 'houses') {
      if (!planetsPayload || houseRows.length === 0) return chartUnavailable;
      return (
        <View>
          <View style={[styles.methodNote, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
            <Ionicons name="book-outline" size={17} color={colors.primary} />
            <Text style={[styles.methodNoteText, { color: colors.textSecondary }]}>
              {t(
                'premiumUi.planetaryPositions.houseMethodNote',
                'Whole-sign houses and classical Parashari graha aspects are shown. Rahu and Ketu use only the 7th aspect.',
              )}
            </Text>
          </View>
          {selectedHouse
            ? <HouseCard key={selectedHouse.house} row={selectedHouse} />
            : houseRows.map((row) => <HouseCard key={row.house} row={row} />)}
        </View>
      );
    }

    if (activeTab === 'nakshatras') {
      if (!planetsPayload || planets.length === 0) return chartUnavailable;
      if (nakshatraPlacements.length === 0) {
        return <Text style={[styles.emptyText, { color: colors.textSecondary }]}>—</Text>;
      }
      const selected = selectedNakshatraSubject
        ? nakshatraPlacements.find((row) => row.name === selectedNakshatraSubject)
        : null;
      return (
        <View>
          <View style={[styles.methodNote, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
            <Ionicons name="star-outline" size={17} color={colors.primary} />
            <Text style={[styles.methodNoteText, { color: colors.textSecondary }]}>
              {t(
                'premiumUi.planetaryPositions.nakshatraMethodNote',
                'Read the planet first, then its Nakshatra and Pada, and finally the condition of the Nakshatra lord that delivers its results.',
              )}
            </Text>
          </View>
          {professionalSpecialPoints?.abhukta_mula ? (
            <View style={[styles.specialCard, { backgroundColor: colors.surfaceRaised, borderColor: professionalSpecialPoints.abhukta_mula.is_active ? colors.warning : colors.cardBorder }]}>
              <Text style={[styles.specialPointName, { color: colors.text }]}>
                {t('premiumUi.planetaryPositions.specialPoints.abhuktaMula', 'Abhukta Mula')}
              </Text>
              <Text style={[styles.specialPointValue, { color: professionalSpecialPoints.abhukta_mula.is_active ? colors.warning : colors.success }]}>
                {professionalSpecialPoints.abhukta_mula.is_active
                  ? t('premiumUi.planetaryPositions.specialPoints.abhuktaMulaPresent', 'Present at birth')
                  : t('premiumUi.planetaryPositions.specialPoints.abhuktaMulaAbsent', 'Not present at birth')}
              </Text>
              <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                {t('premiumUi.planetaryPositions.specialPoints.abhuktaMulaWindow', 'Classical window: {{start}} to {{end}}', {
                  start: professionalSpecialPoints.abhukta_mula.window_start_local,
                  end: professionalSpecialPoints.abhukta_mula.window_end_local,
                })}
              </Text>
              <Text style={[styles.methodDisclosure, { color: colors.textSecondary, borderTopColor: colors.cardBorder }]}>
                {professionalSpecialPoints.abhukta_mula.calculation_basis?.reference}
              </Text>
            </View>
          ) : null}
          {selected
            ? <NakshatraPlacementCard key={selected.name} row={selected} detailed />
            : nakshatraPlacements.map((row) => <NakshatraPlacementCard key={row.name} row={row} />)}
        </View>
      );
    }

    if (activeTab === 'jaimini') return renderJaiminiTab();

    if (activeTab === 'promise') return renderNatalPromiseTab();

    if (activeTab === 'lagnas') {
      if (!professionalSpecialLoaded) {
        return (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('premiumUi.common.loading', 'Loading…')}</Text>
          </View>
        );
      }
      if (professionalSpecialError || !lagnas.length) {
        return (
          <View style={[styles.methodNote, { backgroundColor: colors.surfaceMuted, borderColor: colors.warning }]}>
            <Ionicons name="alert-circle-outline" size={18} color={colors.warning} />
            <Text style={[styles.methodNoteText, { color: colors.textSecondary }]}>
              {professionalSpecialError || t('premiumUi.planetaryPositions.lagnaWorksheet.unavailable', 'The special-Lagna calculation is unavailable for this chart.')}
            </Text>
          </View>
        );
      }
      return (
        <View>
          <View style={[styles.methodNote, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
            <Ionicons name="sunny-outline" size={18} color={colors.primary} />
            <Text style={[styles.methodNoteText, { color: colors.textSecondary }]}>
              {t('premiumUi.planetaryPositions.lagnaWorksheet.intro', 'Bhava, Hora and Ghatika Lagna are calculated from the applicable local sunrise and the Sun’s longitude at that sunrise. Open a card to inspect the exact derivation and the chart counted from that reference.')}
            </Text>
          </View>
          {lagnas.map((lagna) => <LagnaCard key={lagna.key} lagna={lagna} />)}
          <Text style={[styles.methodDisclosure, { color: colors.textSecondary, borderTopColor: colors.cardBorder }]}>
            {t('premiumUi.planetaryPositions.lagnaWorksheet.sunriseRule', 'For births before local sunrise, elapsed time is counted from the previous local sunrise.')}
          </Text>
        </View>
      );
    }

    if (activeTab === 'special') {
      if (specialLoading) {
        return (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
              {t('premiumUi.planetaryPositions.specialPoints.loading', 'Loading special conditions…')}
            </Text>
          </View>
        );
      }

      const specialCardBg = colors.surfaceRaised;
      const specialCardBorder = colors.cardBorder;
      const yogiPoint = isSpecialPoint(yogiPoints?.yogi) ? yogiPoints.yogi : null;
      const duplicateYogi = isSpecialPoint(yogiPoints?.duplicate_yogi) ? yogiPoints.duplicate_yogi : null;
      const avayogiPoint = isSpecialPoint(yogiPoints?.avayogi) ? yogiPoints.avayogi : null;
      const tithiDagdhaRashis = Array.isArray(yogiPoints?.tithi_dagdha_rashis)
        ? yogiPoints.tithi_dagdha_rashis.filter(isSpecialPoint)
        : [];
      const duplicateAvayogiOverlap = Boolean(
        yogiPoints?.duplicate_yogi_avayogi_overlap?.is_active
        || (duplicateYogi?.lord && avayogiPoint?.lord && duplicateYogi.lord === avayogiPoint.lord),
      );
      const bhriguBindu = sniperPoints?.bhrigu_bindu && !sniperPoints.bhrigu_bindu.error
        ? sniperPoints.bhrigu_bindu
        : null;
      const kharesh = sniperPoints?.kharesh && !sniperPoints.kharesh.error ? sniperPoints.kharesh : null;
      const mrityuBhaga = sniperPoints?.mrityu_bhaga && !sniperPoints.mrityu_bhaga.error
        ? sniperPoints.mrityu_bhaga
        : null;
      const solarUpagrahas = professionalSpecialPoints?.solar_upagrahas;
      const timeUpagrahas = professionalSpecialPoints?.time_upagrahas;
      const navamsa64References = professionalSpecialPoints?.navamsa_64?.references || [];
      const gandantaEntries = [];
      if (gandantaData?.lagna_gandanta?.is_gandanta) {
        gandantaEntries.push({ subject: t('premiumUi.planetaryPositions.specialPoints.lagna', 'Lagna'), ...gandantaData.lagna_gandanta.gandanta_info });
      }
      (gandantaData?.planets_in_gandanta || []).forEach((item) => {
        gandantaEntries.push({ subject: item.planet, ...(item.gandanta_info || {}) });
      });
      const failedLabel = (key) => t(`premiumUi.planetaryPositions.specialPoints.sources.${key}`, key);

      const SpecialGroup = ({ icon, title, description, source, children }) => (
        <View style={[styles.specialGroup, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
          <View style={styles.specialGroupHeader}>
            <View style={[styles.specialGroupIcon, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
              <Ionicons name={icon} size={18} color={colors.primary} />
            </View>
            <View style={styles.specialGroupHeading}>
              <Text style={[styles.specialGroupTitle, { color: colors.text }]}>{title}</Text>
              <Text style={[styles.specialGroupDescription, { color: colors.textSecondary }]}>{description}</Text>
            </View>
          </View>
          <View style={[styles.specialGroupRule, { backgroundColor: colors.cardBorder }]} />
          {children}
          <Text style={[styles.specialSource, { color: colors.textMuted || colors.textSecondary }]}>{source}</Text>
        </View>
      );

      const SpecialField = ({ label, value, valueColor }) => {
        if (value === undefined || value === null || value === '') return null;
        return (
          <View style={styles.specialFieldRow}>
            <Text style={[styles.specialFieldLabel, { color: colors.textSecondary }]}>{label}</Text>
            <Text style={[styles.specialFieldValue, { color: valueColor || colors.text }]}>{String(value)}</Text>
          </View>
        );
      };

      const SpecialCard = ({ title, value, children, tone }) => (
        <View style={[styles.specialCard, { backgroundColor: specialCardBg, borderColor: tone || specialCardBorder }]}>
          <Text style={[styles.specialPointName, { color: colors.text }]}>{title}</Text>
          {value ? <Text style={[styles.specialPointValue, { color: colors.primary }]}>{value}</Text> : null}
          {children}
        </View>
      );

      const renderYogiPoint = ({ key, title, point, role }) => {
        if (!point) return null;
        return (
          <SpecialCard key={key} title={title} value={`${point.sign_name} ${formatPointDegrees(point.degree)}`}>
            <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.nakshatra', 'Nakshatra')} value={point.nakshatra_name || '—'} />
            <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.rulingPlanet', 'Ruling planet')} value={point.lord || '—'} />
            <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>{role}</Text>
          </SpecialCard>
        );
      };

      const hasAnySpecialData = Boolean(yogiPoints || sniperPoints || pushkaraData || mudakkuData || gandantaData || professionalSpecialPoints);

      return (
        <View>
          <View style={[styles.methodNote, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
            <Ionicons name="information-circle-outline" size={18} color={colors.primary} />
            <View style={styles.specialIntroCopy}>
              <Text style={[styles.specialIntroTitle, { color: colors.text }]}>
                {t('premiumUi.planetaryPositions.specialPoints.screenTitle', 'Special conditions and calculated points')}
              </Text>
              <Text style={[styles.specialIntroText, { color: colors.textSecondary }]}>
                {t('premiumUi.planetaryPositions.specialPoints.screenIntro', 'These calculations come from different traditions. Each group shows its own method so they are not read as one combined system.')}
              </Text>
            </View>
          </View>

          {specialFailures.length > 0 ? (
            <View style={[styles.specialFailureCard, { backgroundColor: colors.surfaceRaised, borderColor: colors.error }]}>
              <Ionicons name="alert-circle-outline" size={20} color={colors.error} />
              <View style={styles.specialFailureCopy}>
                <Text style={[styles.specialFailureTitle, { color: colors.text }]}>
                  {t('premiumUi.planetaryPositions.specialPoints.incompleteTitle', 'Some calculations could not be loaded')}
                </Text>
                <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                  {t('premiumUi.planetaryPositions.specialPoints.incompleteBody', 'Unavailable: {{sources}}. The missing sections are shown explicitly instead of being replaced with local estimates.', { sources: specialFailures.map(failedLabel).join(', ') })}
                </Text>
              </View>
            </View>
          ) : null}

          {yogiPoints ? (
            <SpecialGroup
              icon="moon-outline"
              title={t('premiumUi.planetaryPositions.specialPoints.lunarConditions', 'Lunar and tithi conditions')}
              description={t('premiumUi.planetaryPositions.specialPoints.lunarConditionsDesc', 'Yogi and Avayogi come from the Sun–Moon sum. Tithi Dagdha signs come from the birth tithi table and remain a separate calculation.')}
              source={t('premiumUi.planetaryPositions.specialPoints.yogiMethod', 'Method: Yogi = Sun + Moon + 93°20′; Avayogi = Yogi + 66°40′. Dagdha table: Seshadri Iyer tradition.')}
            >
              {renderYogiPoint({
                key: 'yogi',
                title: t('premiumUi.planetaryPositions.specialPoints.yogi', 'Yogi'),
                point: yogiPoint,
                role: t('premiumUi.planetaryPositions.specialPoints.yogiExplanation', 'The lord of the nakshatra containing the Yogi point.'),
              })}
              {renderYogiPoint({
                key: 'duplicate-yogi',
                title: t('premiumUi.planetaryPositions.specialPoints.duplicateYogi', 'Duplicate Yogi'),
                point: duplicateYogi,
                role: t('premiumUi.planetaryPositions.specialPoints.duplicateYogiExplanation', 'The lord of the zodiac sign containing the Yogi point.'),
              })}
              {renderYogiPoint({
                key: 'avayogi',
                title: t('premiumUi.planetaryPositions.specialPoints.avayogi', 'Avayogi'),
                point: avayogiPoint,
                role: t('premiumUi.planetaryPositions.specialPoints.avayogiExplanation', 'The lord of the nakshatra containing the Avayogi point.'),
              })}
              {duplicateAvayogiOverlap ? (
                <SpecialCard title={t('premiumUi.planetaryPositions.specialPoints.dualRoleTitle', 'One planet, two separate roles')} tone={colors.warning}>
                  <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                    {t('premiumUi.planetaryPositions.specialPoints.dualRoleBody', '{{planet}} is Duplicate Yogi because it rules the Yogi point’s sign, and Avayogi because it rules the Avayogi point’s nakshatra. These roles come from separate calculations and must be read together as an overlap.', { planet: duplicateYogi.lord })}
                  </Text>
                </SpecialCard>
              ) : null}
              <SpecialCard
                title={t('premiumUi.planetaryPositions.specialPoints.tithiDagdhaRashis', 'Tithi Dagdha Rashis')}
                value={t('premiumUi.planetaryPositions.specialPoints.birthTithiValue', 'Birth tithi {{number}}', { number: yogiPoints.paksha_tithi_number || '—' })}
              >
                {tithiDagdhaRashis.length > 0 ? (
                  <View style={styles.specialChipWrap}>
                    {tithiDagdhaRashis.map((row) => (
                      <View key={`dagdha-${row.sign}`} style={[styles.specialChip, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
                        <Text style={[styles.specialChipText, { color: colors.selectionText }]}>{row.sign_name} · {row.lord}</Text>
                      </View>
                    ))}
                  </View>
                ) : (
                  <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                    {t('premiumUi.planetaryPositions.specialPoints.noneForTithiBody', 'Purnima and Amavasya have no Tithi Dagdha Rashi in the selected table.')}
                  </Text>
                )}
              </SpecialCard>
            </SpecialGroup>
          ) : null}

          {gandantaData || sniperPoints || navamsa64References.length > 0 ? (
            <SpecialGroup
              icon="locate-outline"
              title={t('premiumUi.planetaryPositions.specialPoints.sensitivePoints', 'Sensitive degrees and junctions')}
              description={t('premiumUi.planetaryPositions.specialPoints.sensitivePointsDesc', 'Exact junctions and derived chart points are shown separately. Their presence marks an area for closer judgment; it does not predict an event by itself.')}
              source={t('premiumUi.planetaryPositions.specialPoints.sensitiveMethod', 'Methods shown: water-to-fire Gandanta zones, Moon–Rahu midpoint, 22nd Drekkana, 64th Navamsha and the configured Mrityu Bhaga table.')}
            >
              {gandantaData ? (
                <SpecialCard
                  title={t('premiumUi.planetaryPositions.specialPoints.gandanta', 'Gandanta')}
                  value={t('premiumUi.planetaryPositions.specialPoints.gandantaCount', '{{count}} placements in Gandanta', { count: gandantaEntries.length })}
                >
                  {gandantaEntries.length > 0 ? gandantaEntries.map((item, index) => (
                    <View key={`${item.subject}-${index}`} style={styles.specialListItem}>
                      <Text style={[styles.specialListTitle, { color: colors.text }]}>{item.subject} · {item.gandanta_name}</Text>
                      <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                        {t('premiumUi.planetaryPositions.specialPoints.distanceFromJunction', '{{distance}}° from the exact junction · {{intensity}}', { distance: item.distance_from_junction, intensity: item.intensity })}
                      </Text>
                    </View>
                  )) : (
                    <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                      {t('premiumUi.planetaryPositions.specialPoints.noGandanta', 'No planet or Lagna falls within the configured Gandanta range.')}
                    </Text>
                  )}
                </SpecialCard>
              ) : null}
              {bhriguBindu ? (
                <SpecialCard title={t('premiumUi.planetaryPositions.specialPoints.bhriguBindu', 'Bhrigu Bindu')} value={bhriguBindu.formatted}>
                  <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.derivation', 'Derivation')} value={t('premiumUi.planetaryPositions.specialPoints.moonRahuMidpoint', 'Midpoint of the Moon and Rahu')} />
                  <SpecialField label={t('premiumUi.planetaryPositions.nakshatra', 'Nakshatra')} value={bhriguBindu.nakshatra ? `${bhriguBindu.nakshatra} · ${t('premiumUi.planetaryPositions.pada', 'Pada {{number}}', { number: bhriguBindu.pada })}` : null} />
                  <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.lordLabel', 'Sign lord')} value={bhriguBindu.lord} />
                </SpecialCard>
              ) : null}
              {kharesh ? (
                <SpecialCard title={t('premiumUi.planetaryPositions.specialPoints.kharesh', '22nd Drekkana lord')} value={`${kharesh.danger_sign} · ${kharesh.kharesh_lord}`}>
                  <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.derivation', 'Derivation')} value={t('premiumUi.planetaryPositions.specialPoints.khareshDerivation', 'Eighth sign from the D3 ascendant')} />
                  <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.d3Ascendant', 'D3 ascendant')} value={kharesh.d3_ascendant_sign} />
                </SpecialCard>
              ) : null}
              {navamsa64References.length > 0 ? (
                <SpecialCard title={t('premiumUi.planetaryPositions.specialPoints.navamsa64', '64th Navamsha')}>
                  {navamsa64References.map((row) => (
                    <View key={`navamsa64-${row.reference}`} style={styles.specialListItem}>
                      <Text style={[styles.specialListTitle, { color: colors.text }]}>
                        {row.reference} · {row.sensitive_sign_name} · {row.sensitive_sign_lord}
                      </Text>
                      <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                        {t('premiumUi.planetaryPositions.specialPoints.navamsa64ReferenceDerivation', 'Fourth sign from {{sign}} in D9', { sign: row.d9_reference_sign_name })}
                      </Text>
                    </View>
                  ))}
                </SpecialCard>
              ) : null}
              {mrityuBhaga ? (
                <SpecialCard
                  title={t('premiumUi.planetaryPositions.specialPoints.mrityuBhaga', 'Mrityu Bhaga')}
                  value={mrityuBhaga.has_affliction
                    ? t('premiumUi.planetaryPositions.specialPoints.mrityuFound', '{{count}} qualifying placements', { count: mrityuBhaga.afflicted_points?.length || 0 })
                    : t('premiumUi.planetaryPositions.specialPoints.noneFound', 'No qualifying placement')}
                >
                  {(mrityuBhaga.afflicted_points || []).map((item) => (
                    <View key={`${item.planet || item.point}-${item.house}`} style={styles.specialListItem}>
                      <Text style={[styles.specialListTitle, { color: colors.text }]}>{item.planet || item.point} · H{item.house}</Text>
                      <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                        {t('premiumUi.planetaryPositions.specialPoints.mrityuSpan', '{{degree}}° · traditional {{target}}th degree ({{start}}°–{{end}}°)', { degree: item.degree, target: item.mb_degree, start: item.degree_span_start, end: item.degree_span_end })}
                      </Text>
                    </View>
                  ))}
                  <Text style={[styles.methodDisclosure, { color: colors.textSecondary, borderTopColor: colors.cardBorder }]}>
                    {mrityuBhaga.source} · {mrityuBhaga.degree_semantics}
                  </Text>
                </SpecialCard>
              ) : null}
            </SpecialGroup>
          ) : null}

          {solarUpagrahas ? (
            <SpecialGroup
              icon="sunny-outline"
              title={t('premiumUi.planetaryPositions.specialPoints.solarUpagrahas', 'Solar-derived Upagrahas')}
              description={t('premiumUi.planetaryPositions.specialPoints.solarUpagrahasDesc', 'Five non-luminous points derived in sequence from the Sun. Each point shows its exact formula and placement.')}
              source={solarUpagrahas.calculation_basis?.reference || 'BPHS 3.61–65'}
            >
              {(solarUpagrahas.points || []).map((point) => (
                <SpecialCard key={`solar-${point.name}`} title={point.name} value={`${point.sign_name} ${formatPointDegrees(point.degree)} · H${point.house}`}>
                  <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.formula', 'Formula')} value={point.formula} />
                  <SpecialField label={t('premiumUi.planetaryPositions.nakshatra', 'Nakshatra')} value={`${point.nakshatra} · ${t('premiumUi.planetaryPositions.pada', 'Pada {{number}}', { number: point.pada })}`} />
                  <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.signLord', 'Sign lord')} value={point.sign_lord} />
                </SpecialCard>
              ))}
            </SpecialGroup>
          ) : null}

          {timeUpagrahas ? (
            <SpecialGroup
              icon="time-outline"
              title={t('premiumUi.planetaryPositions.specialPoints.timeUpagrahas', 'Day and night Upagrahas')}
              description={t('premiumUi.planetaryPositions.specialPoints.timeUpagrahasDesc', 'The actual local day or night is divided into eight equal parts. These are ascendants at the applicable planetary segment.')}
              source={timeUpagrahas.calculation_basis?.reference || 'BPHS 3.66–70'}
            >
              <SpecialCard
                title={timeUpagrahas.day_night_frame?.is_day_birth
                  ? t('premiumUi.planetaryPositions.specialPoints.dayBirth', 'Day birth calculation')
                  : t('premiumUi.planetaryPositions.specialPoints.nightBirth', 'Night birth calculation')}
                value={`${timeUpagrahas.day_night_frame?.weekday || '—'} · ${timeUpagrahas.day_night_frame?.segment_duration_minutes || '—'} min`}
              >
                <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.periodStart', 'Period begins')} value={timeUpagrahas.day_night_frame?.period_start_local} />
                <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.periodEnd', 'Period ends')} value={timeUpagrahas.day_night_frame?.period_end_local} />
              </SpecialCard>
              {(timeUpagrahas.points || []).map((point) => (
                <SpecialCard key={`time-${point.name}`} title={point.name} value={`${point.sign_name} ${formatPointDegrees(point.degree)} · H${point.house}`}>
                  <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.planetarySegment', 'Planetary segment')} value={`${point.segment_lord} · ${point.segment_start_local}`} />
                  <SpecialField label={t('premiumUi.planetaryPositions.nakshatra', 'Nakshatra')} value={`${point.nakshatra} · ${t('premiumUi.planetaryPositions.pada', 'Pada {{number}}', { number: point.pada })}`} />
                  {point.name === 'Mandi' ? (
                    <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                      {t('premiumUi.planetaryPositions.specialPoints.mandiConvention', 'BPHS identifies Mandi with Gulika, so both names show the ascendant at the start of Saturn’s segment. Later differing conventions are not mixed here.')}
                    </Text>
                  ) : null}
                </SpecialCard>
              ))}
            </SpecialGroup>
          ) : null}

          {pushkaraData ? (
            <SpecialGroup
              icon="diamond-outline"
              title={t('premiumUi.planetaryPositions.specialPoints.fortifyingPlacements', 'Fortifying placements')}
              description={t('premiumUi.planetaryPositions.specialPoints.fortifyingPlacementsDesc', 'Pushkara status is a strengthening degree condition. It modifies a planet’s capacity but does not erase its lordship, dignity or afflictions.')}
              source={t('premiumUi.planetaryPositions.specialPoints.pushkaraMethod', 'Method: two Pushkara Navamshas per sign and the configured sign-specific Pushkara Bhaga degrees.')}
            >
              {(pushkaraData.pushkara_planets || []).length > 0 ? pushkaraData.pushkara_planets.map((data) => (
                <SpecialCard key={data.planet} title={data.planet} value={`${formatPointDegrees(data.degree_in_sign)} · ${t('premiumUi.planetaryPositions.specialPoints.navamsaNumber', 'Navamsha {{number}}', { number: data.navamsa_no })}`}>
                  <View style={styles.specialChipWrap}>
                    {data.is_pushkara_navamsa ? (
                      <View style={[styles.specialChip, { backgroundColor: colors.selectionSurface, borderColor: colors.success }]}>
                        <Text style={[styles.specialChipText, { color: colors.success }]}>{t('premiumUi.planetaryPositions.pushkaraNavamsha', 'Pushkara Navamsha')}</Text>
                      </View>
                    ) : null}
                    {data.is_pushkara_bhaga ? (
                      <View style={[styles.specialChip, { backgroundColor: colors.selectionSurface, borderColor: colors.success }]}>
                        <Text style={[styles.specialChipText, { color: colors.success }]}>{t('premiumUi.planetaryPositions.pushkaraBhaga', 'Pushkara Bhaga')}</Text>
                      </View>
                    ) : null}
                  </View>
                  {data.ruled_houses?.length ? <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.rulesHouses', 'Rules houses')} value={data.ruled_houses.map((house) => `H${house}`).join(', ')} /> : null}
                </SpecialCard>
              )) : (
                <SpecialCard title={t('premiumUi.planetaryPositions.specialPoints.noneFound', 'No qualifying placement')}>
                  <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                    {t('premiumUi.planetaryPositions.specialPoints.noPushkara', 'No planet qualifies for Pushkara Navamsha or the configured Pushkara Bhaga proximity in this chart.')}
                  </Text>
                </SpecialCard>
              )}
            </SpecialGroup>
          ) : null}

          {mudakkuData ? (
            <SpecialGroup
              icon="git-compare-outline"
              title={t('premiumUi.planetaryPositions.specialPoints.traditionSpecific', 'Tradition-specific conditions')}
              description={t('premiumUi.planetaryPositions.specialPoints.traditionSpecificDesc', 'These calculations belong to a named regional or textual method and should be judged within that method.')}
              source={t('premiumUi.planetaryPositions.specialPoints.mudakkuMethod', 'Tamil Mudakku method: count inclusively from the Sun’s nakshatra to Mula, then repeat that count from Purvashada.')}
            >
              <SpecialCard title={t('premiumUi.planetaryPositions.specialPoints.mudakku', 'Mudakku / Modakku')} value={`${mudakkuData.mudakku_nakshatra?.name || '—'} · ${mudakkuData.mudakku_rashi || '—'}`}>
                <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.sunNakshatra', 'Sun’s nakshatra')} value={mudakkuData.sun_nakshatra?.name} />
                <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.inclusiveCount', 'Inclusive count to Mula')} value={mudakkuData.count_to_mula} />
                <SpecialField label={t('premiumUi.planetaryPositions.specialPoints.rulingPlanet', 'Ruling planet')} value={mudakkuData.mudakku_rashi_lord} />
                {mudakkuData.is_split_nakshatra ? (
                  <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                    {t('premiumUi.planetaryPositions.specialPoints.splitNakshatra', 'The landing nakshatra crosses two signs; the first pada and first sign are used by this method.')}
                  </Text>
                ) : null}
              </SpecialCard>
            </SpecialGroup>
          ) : null}

          {!hasAnySpecialData ? (
            <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
              {t('premiumUi.planetaryPositions.specialPoints.noData', 'No special-condition data is available for this chart.')}
            </Text>
          ) : null}
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
              <TabButton label={t('premiumUi.planetaryPositions.tabs.houses', 'Houses')} emoji="🏠" value="houses" active={activeTab === 'houses'} />
              <TabButton label={t('premiumUi.planetaryPositions.tabs.promise', 'Life')} emoji="📜" value="promise" active={activeTab === 'promise'} />
              <TabButton label={t('premiumUi.planetaryPositions.tabs.nakshatras', 'Nakshatras')} emoji="⭐" value="nakshatras" active={activeTab === 'nakshatras'} />
              <TabButton label={t('premiumUi.planetaryPositions.tabs.jaimini', 'Jaimini')} emoji="🔱" value="jaimini" active={activeTab === 'jaimini'} />
              <TabButton label={t('premiumUi.planetaryPositions.tabs.lagnas', 'Lagnas')} emoji="🎯" value="lagnas" active={activeTab === 'lagnas'} />
              <TabButton label={t('premiumUi.planetaryPositions.tabs.special', 'Special')} emoji="✨" value="special" active={activeTab === 'special'} />
            </GHScrollView>
          </View>

          <GHScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false} nestedScrollEnabled>
            <View style={[styles.hero, { backgroundColor: colors.surfaceInverse, borderColor: colors.cosmicLine }]}>
              <View pointerEvents="none" style={styles.heroLinework}>
                <View style={[styles.heroOrbit, styles.heroOrbitLarge, { borderColor: colors.onSurfaceInverseMuted }]} />
                <View style={[styles.heroOrbit, styles.heroOrbitSmall, { borderColor: colors.onSurfaceInverseMuted }]} />
              </View>
              <Text style={[styles.heroEyebrow, { color: colors.onSurfaceInverseMuted }]}>{t('premiumUi.planetaryPositions.skyMap', 'YOUR CELESTIAL MAP')}</Text>
              <Text style={[styles.heroTitle, { color: colors.onSurfaceInverse }]}>{t('premiumUi.planetaryPositions.heroTitle', 'The sky at your birth.')}</Text>
              <Text style={[styles.heroBody, { color: colors.onSurfaceInverseMuted }]}>{t('premiumUi.planetaryPositions.heroBody', 'Scan planet, house, and nakshatra tables the way a desk astrologer would.')}</Text>
              <View style={[styles.heroMeta, { borderTopColor: colors.onSurfaceInverseMuted }]}>
                <Text style={[styles.heroMetaText, { color: colors.onSurfaceInverse }]}>{t('premiumUi.planetaryPositions.positionCount', '{{count}} planetary positions', { count: planets.length })}</Text>
                <Text style={[styles.heroMetaText, { color: colors.onSurfaceInverseMuted }]}>{t('premiumUi.planetaryPositions.sidereal', 'Sidereal · Lahiri')}</Text>
              </View>
            </View>
            {renderTabContent()}
            <View style={{ height: ['planets', 'houses', 'nakshatras'].includes(activeTab) ? Math.max(insets.bottom, 8) + 68 : 32 }} />
          </GHScrollView>
          {activeTab === 'planets' && !loading && planets.length > 0 ? <PlanetDock /> : null}
          {activeTab === 'houses' && !loading && houseRows.length > 0 ? <HouseDock /> : null}
          {activeTab === 'nakshatras' && !loading && nakshatraPlacements.length > 0 ? <NakshatraDock /> : null}
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

  planetDock: {
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingTop: 7,
    ...Platform.select({
      ios: { shadowColor: '#000', shadowOffset: { width: 0, height: -3 }, shadowOpacity: 0.08, shadowRadius: 10 },
      android: { elevation: 8 },
      default: { boxShadow: '0 -4px 14px rgba(0,0,0,0.07)' },
    }),
  },
  planetDockContent: { paddingHorizontal: 8, gap: 3 },
  planetDockContentTablet: { flexGrow: 1, justifyContent: 'space-between' },
  planetDockItem: {
    minHeight: 52,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'transparent',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
    paddingVertical: 5,
  },
  planetDockSymbol: { fontSize: 19, lineHeight: 22, fontWeight: '700' },
  planetDockName: { fontSize: 9, lineHeight: 12, fontWeight: '800', marginTop: 1 },
  houseDockItem: {
    width: 62,
    minHeight: 52,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'transparent',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
    paddingVertical: 5,
  },
  houseDockNumber: { fontSize: 16, lineHeight: 20, fontWeight: '900' },

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
  houseSeal: { width: 44, height: 44, borderRadius: 15, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  houseSealText: { fontSize: 15, lineHeight: 20, fontWeight: '900' },
  houseProfessionalPanel: { borderTopWidth: StyleSheet.hairlineWidth, marginTop: 14, paddingTop: 5 },
  houseClassificationRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginBottom: 3 },
  houseClassificationChip: { borderWidth: 1, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 6 },
  houseClassificationText: { fontSize: 10, lineHeight: 14, fontWeight: '800' },
  retrogradeTag: {
    fontSize: 10,
    fontWeight: '600',
    marginTop: 2,
  },
  yogaLink: { marginTop: 14, borderWidth: 1, borderRadius: 13, paddingHorizontal: 12, paddingVertical: 10, flexDirection: 'row', alignItems: 'center', gap: 8 },
  yogaLinkText: { flex: 1, fontSize: 12, lineHeight: 17, fontWeight: '700' },
  roleSummaryCard: { marginTop: 14, borderWidth: 1, borderRadius: 15, padding: 13, gap: 8 },
  roleSummaryTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 2 },
  roleSummaryTitle: { flex: 1, fontFamily: DISPLAY_FONT_FAMILY, fontSize: 17, lineHeight: 21 },
  roleSummaryRow: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 },
  roleSummaryLabel: { flex: 0.42, fontSize: 11, lineHeight: 16, fontWeight: '700' },
  roleSummaryValue: { flex: 0.58, fontSize: 12, lineHeight: 17, fontWeight: '800', textAlign: 'right' },
  roleSummaryReason: { borderTopWidth: StyleSheet.hairlineWidth, paddingTop: 8, fontSize: 11, lineHeight: 16, fontWeight: '600' },
  roleSummaryCondition: { fontSize: 11, lineHeight: 16, fontWeight: '700' },
  professionalAccordion: { marginTop: 14, borderWidth: 1, borderRadius: 15, overflow: 'hidden' },
  professionalToggle: { paddingHorizontal: 13, paddingVertical: 11, flexDirection: 'row', alignItems: 'center', gap: 10 },
  professionalToggleTitle: { fontSize: 13, lineHeight: 18, fontWeight: '800' },
  professionalToggleHint: { fontSize: 10, lineHeight: 14, fontWeight: '500', marginTop: 2 },
  professionalPanel: { borderTopWidth: StyleSheet.hairlineWidth, paddingHorizontal: 13, paddingTop: 4, paddingBottom: 13 },
  professionalSectionTitle: { fontSize: 10, lineHeight: 14, fontWeight: '900', letterSpacing: 0.9, textTransform: 'uppercase', marginTop: 9, marginBottom: 5 },
  professionalRow: { paddingVertical: 7, gap: 3 },
  professionalLabel: { fontSize: 10, lineHeight: 14, fontWeight: '700' },
  professionalValue: { fontSize: 12, lineHeight: 18, fontWeight: '600' },
  nakshatraHeadline: { fontSize: 12, lineHeight: 17, fontWeight: '700', marginTop: 2 },
  nakshatraQuickGrid: {
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingTop: 12,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    alignItems: 'stretch',
  },
  nakshatraQuickItem: { flex: 1, flexBasis: 0, minWidth: 0, gap: 3 },
  nakshatraQuickLabel: { height: 42 },
  nakshatraQuickValue: { marginTop: 0, textAlign: 'left', alignSelf: 'stretch', lineHeight: 20 },
  nakshatraChipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginTop: 12 },
  nakshatraStateChip: { borderWidth: 1, borderRadius: 999, paddingHorizontal: 9, paddingVertical: 5 },
  nakshatraStateText: { fontSize: 9, lineHeight: 12, fontWeight: '800' },
  nakshatraDetailPanel: { borderTopWidth: StyleSheet.hairlineWidth, marginTop: 14, paddingHorizontal: 0 },
  nakshatraExplanation: { fontSize: 12, lineHeight: 19, fontWeight: '600', paddingVertical: 7 },
  methodDisclosure: { borderTopWidth: StyleSheet.hairlineWidth, marginTop: 10, paddingTop: 10, fontSize: 10, lineHeight: 15, fontStyle: 'italic' },
  deliveryCard: { marginTop: 14, borderWidth: 1, borderRadius: 15, padding: 13 },
  deliveryTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 7 },
  deliveryTitle: { flex: 1, fontFamily: DISPLAY_FONT_FAMILY, fontSize: 17, lineHeight: 21 },
  deliveryExplanation: { fontSize: 12, lineHeight: 18, fontWeight: '500', marginBottom: 7 },
  deliverySectionLabel: { fontSize: 10, lineHeight: 14, fontWeight: '800', letterSpacing: 1, marginTop: 5, marginBottom: 7, textTransform: 'uppercase' },
  deliveryChannels: { gap: 7 },
  deliveryChannel: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderRadius: 12, padding: 9, gap: 9 },
  deliveryHouseBadge: { minWidth: 38, height: 32, borderRadius: 10, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 7 },
  deliveryHouseBadgeText: { fontSize: 12, fontWeight: '900' },
  deliveryChannelCopy: { flex: 1 },
  deliveryHouseArea: { fontSize: 12, lineHeight: 16, fontWeight: '800' },
  deliveryRoles: { fontSize: 10, lineHeight: 14, fontWeight: '600', marginTop: 2 },
  deliveryBoundary: { borderTopWidth: StyleSheet.hairlineWidth, paddingTop: 9, marginTop: 3, fontSize: 10, lineHeight: 15, fontStyle: 'italic' },
  methodNote: { marginBottom: 12, borderWidth: 1, borderRadius: 14, padding: 12, flexDirection: 'row', alignItems: 'flex-start', gap: 9 },
  methodNoteText: { flex: 1, fontSize: 11, lineHeight: 16, fontWeight: '600' },
  promiseRetry: { alignSelf: 'flex-start', marginTop: 9, paddingVertical: 5 },
  promiseRetryText: { fontSize: 12, lineHeight: 16, fontWeight: '800' },
  promiseSelectorLabel: { fontSize: 10, lineHeight: 14, fontWeight: '900', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 6 },
  promiseSelector: { minHeight: 64, borderWidth: 1.5, borderRadius: 17, paddingHorizontal: 12, paddingVertical: 10, marginBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 11 },
  promiseSelectorHouse: { width: 42, height: 42, borderRadius: 13, alignItems: 'center', justifyContent: 'center' },
  promiseSelectorHouseText: { fontSize: 12, lineHeight: 16, fontWeight: '900' },
  promiseSelectorValue: { flex: 1, fontFamily: DISPLAY_FONT_FAMILY, fontSize: 17, lineHeight: 22 },
  promiseTopicSelector: { minHeight: 52, borderWidth: 1, borderRadius: 15, paddingHorizontal: 13, paddingVertical: 9, marginBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 10 },
  promiseTopicValue: { flex: 1, fontSize: 13, lineHeight: 18, fontWeight: '800' },
  promiseTopicCount: { fontSize: 11, lineHeight: 15, fontWeight: '900' },
  promiseModalRoot: { flex: 1, justifyContent: 'flex-end' },
  promiseModalBackdrop: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(20, 7, 14, 0.55)' },
  promiseSheet: { width: '100%', maxWidth: 680, maxHeight: '78%', alignSelf: 'center', borderWidth: 1, borderTopLeftRadius: 26, borderTopRightRadius: 26, paddingHorizontal: 16, paddingTop: 9 },
  promiseSheetGrabber: { width: 42, height: 4, borderRadius: 2, alignSelf: 'center', marginBottom: 13 },
  promiseSheetHeader: { flexDirection: 'row', alignItems: 'flex-start', gap: 12, marginBottom: 13 },
  promiseSheetTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 22, lineHeight: 28 },
  promiseSheetSubtitle: { fontSize: 11, lineHeight: 16, fontWeight: '600', marginTop: 3 },
  promiseSheetClose: { width: 38, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center' },
  promiseSheetList: { flexGrow: 0, flexShrink: 1 },
  promiseSheetListContent: { gap: 8, paddingBottom: 4 },
  promiseSheetRow: { minHeight: 58, borderWidth: 1, borderRadius: 15, paddingHorizontal: 11, paddingVertical: 8, flexDirection: 'row', alignItems: 'center', gap: 11 },
  promiseSheetHouse: { width: 39, height: 39, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  promiseSheetHouseText: { fontSize: 11, lineHeight: 15, fontWeight: '900' },
  promiseSheetRowTitle: { flex: 1, fontSize: 13, lineHeight: 18, fontWeight: '800' },
  promiseCard: { borderWidth: 1, borderRadius: 20, padding: 16, marginBottom: 12 },
  promiseEyebrow: { fontSize: 10, lineHeight: 14, fontWeight: '900', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 5 },
  promiseTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 22, lineHeight: 28 },
  promiseReadingLabel: { fontSize: 10, lineHeight: 14, fontWeight: '900', letterSpacing: 1, textTransform: 'uppercase', marginTop: 8, marginBottom: 6 },
  promiseReadingStack: { gap: 13 },
  promiseInsightSubject: { fontSize: 11, lineHeight: 15, fontWeight: '900', marginBottom: 4 },
  promiseReading: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 19, lineHeight: 29 },
  promiseCondition: { borderWidth: 1, borderRadius: 13, paddingHorizontal: 11, paddingVertical: 9, marginTop: 12 },
  promiseConditionLabel: { fontSize: 11, lineHeight: 15, fontWeight: '900' },
  promiseConditionMeta: { fontSize: 10, lineHeight: 14, fontWeight: '600', marginTop: 2, textTransform: 'capitalize' },
  promiseSectionTitle: { fontSize: 12, lineHeight: 17, fontWeight: '900', marginTop: 15, marginBottom: 8 },
  promiseBulletRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 9, marginBottom: 8 },
  promiseBullet: { width: 5, height: 5, borderRadius: 3, marginTop: 7 },
  promiseBulletText: { flex: 1, fontSize: 12, lineHeight: 19, fontWeight: '600' },
  promiseEvidence: { borderTopWidth: StyleSheet.hairlineWidth, marginTop: 10, paddingTop: 2, gap: 6 },
  promiseEvidenceText: { fontSize: 10, lineHeight: 16, fontWeight: '700' },
  promiseBalanceGrid: { gap: 8, marginTop: 13 },
  promiseBalanceCard: { borderWidth: 1, borderRadius: 13, paddingHorizontal: 11, paddingVertical: 10 },
  promiseBalanceTitle: { fontSize: 10, lineHeight: 14, fontWeight: '900', marginBottom: 4 },
  promiseBalanceText: { fontSize: 11, lineHeight: 17, fontWeight: '600' },
  promiseBasisLink: { borderTopWidth: StyleSheet.hairlineWidth, marginTop: 15, paddingTop: 13, paddingBottom: 5, flexDirection: 'row', alignItems: 'center', gap: 10 },
  promiseBasisTitle: { fontSize: 12, lineHeight: 17, fontWeight: '900' },
  promiseBasisReference: { fontSize: 9, lineHeight: 13, fontWeight: '600', marginTop: 2 },
  promiseBasisPanel: { borderWidth: 1, borderRadius: 14, padding: 12, marginTop: 8, gap: 8 },
  promiseInsightEvidence: { gap: 8, paddingVertical: 5 },
  promiseContribution: { gap: 5 },
  promiseBasisPlacement: { fontSize: 13, lineHeight: 19, fontWeight: '900' },
  promiseSourceLink: { fontSize: 11, lineHeight: 16, fontWeight: '900', paddingVertical: 4 },
  promiseBoundary: { borderTopWidth: StyleSheet.hairlineWidth, marginTop: 13, paddingTop: 11, fontSize: 9, lineHeight: 14, fontWeight: '500' },
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

  jaiminiSchemeSelector: { flexDirection: 'row', borderWidth: 1, borderRadius: 16, padding: 4, gap: 4, marginBottom: 12 },
  jaiminiSchemeButton: { flex: 1, minHeight: 40, borderWidth: 1, borderColor: 'transparent', borderRadius: 12, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 8 },
  jaiminiSchemeLabel: { fontSize: 12, lineHeight: 16, fontWeight: '800', textAlign: 'center' },
  jaiminiSection: { borderWidth: 1, borderRadius: 20, padding: 15, marginBottom: 12 },
  jaiminiSectionTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 20, lineHeight: 25 },
  jaiminiSectionSubtitle: { fontSize: 11, lineHeight: 17, fontWeight: '600', marginTop: 4 },
  jaiminiDivider: { height: StyleSheet.hairlineWidth, marginVertical: 12 },
  jaiminiBody: { fontSize: 12, lineHeight: 18, marginTop: 4 },
  jaiminiErrorCard: { borderWidth: 1, borderRadius: 18, padding: 15, flexDirection: 'row', alignItems: 'flex-start', gap: 11 },
  jaiminiErrorCopy: { flex: 1 },
  jaiminiRetry: { borderWidth: 1, borderRadius: 10, alignSelf: 'flex-start', paddingHorizontal: 12, paddingVertical: 8, marginTop: 10 },
  jaiminiRetryText: { fontSize: 11, lineHeight: 15, fontWeight: '800' },
  jaiminiNotice: { borderWidth: 1, borderRadius: 12, padding: 10, flexDirection: 'row', alignItems: 'flex-start', gap: 8, marginBottom: 8 },
  jaiminiNoticeText: { flex: 1, fontSize: 10, lineHeight: 15, fontWeight: '600' },
  jaiminiKarakaRow: { flexDirection: 'row', alignItems: 'flex-start', paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, gap: 11 },
  jaiminiCodeBadge: { width: 46, minHeight: 46, borderWidth: 1, borderRadius: 13, alignItems: 'center', justifyContent: 'center', padding: 4 },
  jaiminiCode: { fontSize: 12, lineHeight: 16, fontWeight: '900' },
  jaiminiRank: { fontSize: 9, lineHeight: 12, fontWeight: '700' },
  jaiminiKarakaCopy: { flex: 1 },
  jaiminiKarakaRole: { fontSize: 10, lineHeight: 14, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.5 },
  jaiminiKarakaPlanet: { fontSize: 15, lineHeight: 21, fontWeight: '800', marginTop: 1 },
  jaiminiMeta: { fontSize: 10, lineHeight: 15, fontWeight: '600', marginTop: 2 },
  jaiminiReverse: { fontSize: 10, lineHeight: 15, fontWeight: '800', marginTop: 2 },
  jaiminiReferenceHeader: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 12 },
  jaiminiSignSeal: { width: 54, height: 54, borderRadius: 16, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  jaiminiSignIcon: { fontSize: 26 },
  jaiminiReferenceCopy: { flex: 1 },
  jaiminiReferenceSign: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 23, lineHeight: 28 },
  jaiminiSubheading: { fontSize: 10, lineHeight: 14, fontWeight: '900', letterSpacing: 0.8, textTransform: 'uppercase', marginTop: 8, marginBottom: 7 },
  jaiminiChipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  jaiminiDataChip: { minWidth: '31%', flexGrow: 1, borderWidth: 1, borderRadius: 11, paddingHorizontal: 9, paddingVertical: 7 },
  jaiminiDataChipTitle: { fontSize: 10, lineHeight: 14, fontWeight: '800' },
  jaiminiDataChipBody: { fontSize: 9, lineHeight: 13, fontWeight: '600', marginTop: 2 },
  jaiminiPrincipalGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  jaiminiPrincipalCard: { flex: 1, minWidth: 105, borderWidth: 1, borderRadius: 13, padding: 11 },
  jaiminiPrincipalCode: { fontSize: 10, lineHeight: 14, fontWeight: '900', letterSpacing: 0.8 },
  jaiminiPrincipalSign: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 17, lineHeight: 22, marginTop: 3 },
  jaiminiPadaRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, paddingVertical: 9, borderBottomWidth: StyleSheet.hairlineWidth },
  jaiminiPadaCode: { width: 42, minHeight: 38, borderWidth: 1, borderRadius: 11, alignItems: 'center', justifyContent: 'center' },
  jaiminiPadaCopy: { flex: 1 },
  jaiminiPadaResult: { fontSize: 13, lineHeight: 18, fontWeight: '800' },
  jaiminiException: { fontSize: 9, lineHeight: 14, fontWeight: '800', marginTop: 3 },
  jaiminiDrishtiRow: { flexDirection: 'row', alignItems: 'center', gap: 9, paddingVertical: 9, borderBottomWidth: StyleSheet.hairlineWidth },
  jaiminiDrishtiSource: { width: 112 },
  jaiminiDrishtiSign: { fontSize: 12, lineHeight: 17, fontWeight: '800' },
  jaiminiDrishtiTargets: { flex: 1, fontSize: 10, lineHeight: 15, fontWeight: '600' },
  lagnaHeaderRight: { alignItems: 'flex-end', justifyContent: 'center', gap: 7 },
  lagnaExpanded: { borderTopWidth: StyleSheet.hairlineWidth, marginTop: 4, paddingTop: 13 },

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
  tableSection: {
    marginBottom: 22,
  },
  tableTitle: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 20,
    lineHeight: 24,
    marginBottom: 10,
  },
  tableLegend: {
    fontSize: 10,
    lineHeight: 14,
    fontWeight: '600',
    marginTop: 8,
  },
  tableCard: {
    borderWidth: 1,
    borderRadius: 16,
    overflow: 'hidden',
    alignSelf: 'flex-start',
    minWidth: '100%',
  },
  tableCardFull: {
    alignSelf: 'stretch',
    width: '100%',
  },
  tableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 36,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  tableHeadingRow: {
    minHeight: 34,
  },
  tableCellWrap: {
    paddingHorizontal: 8,
    paddingVertical: 8,
    borderRightWidth: StyleSheet.hairlineWidth,
    justifyContent: 'center',
  },
  tableCellFlex: {
    flex: 1,
    paddingHorizontal: 8,
    paddingVertical: 8,
    justifyContent: 'center',
  },
  tableHeader: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.4,
    textTransform: 'uppercase',
  },
  tableCell: {
    fontSize: 12,
    fontWeight: '600',
  },
  tableCellStrong: {
    fontSize: 12,
    fontWeight: '800',
  },

  // Special Points Styles
  specialGroup: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
    marginBottom: 16,
  },
  specialIntroCopy: {
    flex: 1,
  },
  specialIntroTitle: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '800',
  },
  specialIntroText: {
    fontSize: 11,
    lineHeight: 16,
    fontWeight: '600',
    marginTop: 3,
  },
  specialGroupHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  specialGroupIcon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  specialGroupHeading: {
    flex: 1,
  },
  specialGroupTitle: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 19,
    lineHeight: 23,
  },
  specialGroupDescription: {
    fontSize: 12,
    lineHeight: 17,
    marginTop: 3,
  },
  specialGroupRule: {
    height: StyleSheet.hairlineWidth,
    marginVertical: 13,
  },
  specialSource: {
    fontSize: 10,
    lineHeight: 15,
    fontWeight: '600',
    marginTop: 4,
  },
  specialFailureCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    borderWidth: 1,
    borderRadius: 14,
    padding: 13,
    marginBottom: 16,
  },
  specialFailureCopy: {
    flex: 1,
  },
  specialFailureTitle: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '800',
  },
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
  specialFieldRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 12,
    marginTop: 6,
  },
  specialFieldLabel: {
    flex: 1,
    fontSize: 11,
    lineHeight: 16,
    fontWeight: '600',
  },
  specialFieldValue: {
    flex: 1.25,
    fontSize: 11,
    lineHeight: 16,
    fontWeight: '800',
    textAlign: 'right',
  },
  specialPointDesc: {
    fontSize: 11,
    marginTop: 4,
    lineHeight: 16,
  },
  specialChipWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 8,
  },
  specialChip: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 9,
    paddingVertical: 5,
  },
  specialChipText: {
    fontSize: 10,
    lineHeight: 13,
    fontWeight: '800',
  },
  specialListItem: {
    marginTop: 8,
  },
  specialListTitle: {
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '800',
  },
});

export default PlanetaryPositionsScreen;
