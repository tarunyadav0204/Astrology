import React from 'react';
import { View, Text, StyleSheet, StatusBar, TouchableOpacity, ActivityIndicator, Platform, useWindowDimensions } from 'react-native';
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
  const [expandedPlanets, setExpandedPlanets] = React.useState({});
  const [selectedPlanetName, setSelectedPlanetName] = React.useState(route.params?.selectedPlanetName || null);

  React.useEffect(() => {
    loadInitialPlanetData();
  }, [chartData, conditionChartData, birthData]);

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
      const results = await Promise.allSettled([
        chartAPI.calculateYogiPoints(birthData),
        chartAPI.calculateSniperPoints(chartData),
        chartAPI.calculatePushkaraNavamsha(chartData, d9Chart),
        chartAPI.calculateMudakkuAnalysis(chartData),
        chartAPI.calculateGandantaAnalysis(chartData),
      ]);
      const [yogiResult, sniperResult, pushkaraResult, mudakkuResult, gandantaResult] = results;
      if (yogiResult.status === 'fulfilled') setYogiPoints(yogiResult.value?.data?.yogi_points || null);
      if (sniperResult.status === 'fulfilled') setSniperPoints(sniperResult.value?.data?.sniper_points || null);
      if (pushkaraResult.status === 'fulfilled') setPushkaraData(pushkaraResult.value?.data?.pushkara_analysis || null);
      if (mudakkuResult.status === 'fulfilled') setMudakkuData(mudakkuResult.value?.data?.mudakku_analysis || null);
      if (gandantaResult.status === 'fulfilled') setGandantaData(gandantaResult.value?.data?.gandanta_analysis || null);
      results.forEach((result, index) => {
        if (result.status === 'rejected') {
          console.error(`Error loading special point source ${index + 1}:`, result.reason);
        }
      });
    } catch (error) {
      console.error('Error loading special points:', error);
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
  const nakshatraRows = React.useMemo(
    () => (canonicalPositions?.nakshatras || []).map((row) => ({
      ...row,
      people: row.people || [],
    })),
    [canonicalPositions],
  );

  React.useEffect(() => {
    if (lastChartKeyRef.current === null) {
      lastChartKeyRef.current = chartKey;
      return;
    }
    if (lastChartKeyRef.current !== chartKey) {
      lastChartKeyRef.current = chartKey;
      setSelectedPlanetName(null);
      setExpandedPlanets({});
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
  const planetDockOptionCount = planets.length + 1;
  const dockItemWidth = isTablet
    ? Math.max(68, (windowWidth - 16 - (Math.max(planetDockOptionCount - 1, 0) * 3)) / Math.max(planetDockOptionCount, 1))
    : 76;

  React.useEffect(() => {
    if (isTablet || !planetDockRef.current) return;
    const planetIndex = planets.findIndex((planet) => planet.name === selectedPlanetName);
    const index = selectedPlanetName && planetIndex >= 0 ? planetIndex + 1 : 0;
    const x = Math.max(0, (index * dockItemWidth) - ((windowWidth - dockItemWidth) / 2));
    requestAnimationFrame(() => planetDockRef.current?.scrollTo?.({ x, animated: true }));
  }, [selectedPlanetName, isTablet, dockItemWidth, windowWidth, planets.length]);

  React.useEffect(() => {
    if (!selectedPlanetName || !planets.some((planet) => planet.name === selectedPlanetName)) return;
    setExpandedPlanets((current) => (
      current[selectedPlanetName] === undefined
        ? { ...current, [selectedPlanetName]: true }
        : current
    ));
  }, [selectedPlanetName, planets.length]);

  if (!birthData?.name) return null;

  const ascendantLon = (() => {
    const asc = canonicalPositions?.ascendant?.longitude;
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
    const ascendant = canonicalPositions.ascendant;
    lagnas.push({
      name: 'Ascendant (Lagna)',
      longitude: ascendant.longitude,
      sign: ascendant.sign,
      degree: ascendant.degree,
      house: 1,
      nakshatra: ascendant.nakshatra,
      pada: ascendant.pada,
      description: 'Self, Personality, Physical Body',
    });
  }

  if (canonicalPositions?.indu_lagna) {
    const indu = canonicalPositions.indu_lagna;
    lagnas.push({
      name: 'Indu Lagna',
      longitude: indu.longitude,
      sign: indu.sign,
      degree: indu.degree,
      house: indu.house,
      nakshatra: indu.nakshatra,
      pada: indu.pada,
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
    const occupantText = people.length
      ? people.map((person) => {
        const states = [
          person.retro ? t('premiumUi.planetaryPositions.retrograde', 'Retrograde') : null,
          person.combust ? t('premiumUi.planetaryPositions.notes.combustFull', 'Combust') : null,
        ].filter(Boolean);
        return states.length ? `${person.name} (${states.join(', ')})` : person.name;
      }).join(', ')
      : t('premiumUi.planetaryPositions.none', 'None');
    const lordText = row.lordHouse === '—'
      ? row.lord
      : `${row.lord} · ${t('premiumUi.planetaryPositions.house', 'House {{number}}', { number: row.lordHouse })}`;
    return (
      <View style={[styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
        <View style={styles.cardHeader}>
          <View style={styles.planetInfo}>
            <View>
              <Text style={[styles.planetName, { color: colors.text }]}>
                {t('premiumUi.planetaryPositions.house', 'House {{number}}', { number: row.house })}
              </Text>
              {row.dignity ? (
                <Text style={[styles.lagnaDescription, { color: row.dignity.key === 'db' || row.dignity.key === 'enemy' ? colors.error : colors.textSecondary }]}>
                  {dignityText(row.dignity)}
                </Text>
              ) : null}
              {row.lordCombust ? (
                <Text style={[styles.lagnaDescription, { color: colors.warning }]}>
                  {t('premiumUi.planetaryPositions.notes.combustFull', 'Combust')}
                </Text>
              ) : null}
            </View>
          </View>
        </View>
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
      </View>
    );
  };

  const NakshatraCard = ({ row }) => {
    const people = row.people || [];
    const occupantText = people.map((person) => {
      const pada = t('premiumUi.planetaryPositions.pada', 'Pada {{number}}', { number: person.pada });
      const retro = person.retro ? ` (${t('premiumUi.planetaryPositions.retrograde', 'Retrograde')})` : '';
      const combust = person.combust ? ` (${t('premiumUi.planetaryPositions.notes.combustFull', 'Combust')})` : '';
      return `${person.name} · ${pada}${retro}${combust}`;
    }).join(', ');
    return (
      <View style={[styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
        <View style={styles.cardHeader}>
          <Text style={[styles.planetName, { color: colors.text, flex: 1 }]}>{row.nakshatra}</Text>
        </View>
        <View style={[styles.divider, { backgroundColor: colors.cardBorder }]} />
        <View style={styles.detailsGrid}>
          <View style={styles.detailItem}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.nakshatraLord', 'Nakshatra lord')}</Text>
            <Text style={[styles.detailValue, { color: colors.text }]}>{row.lord}</Text>
          </View>
          <View style={styles.detailItemFull}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.cols.occupants', 'Planets')}</Text>
            <Text style={[styles.detailValue, styles.detailValueWide, { color: colors.text }]}>{occupantText || '—'}</Text>
          </View>
        </View>
      </View>
    );
  };

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
      return houseRows.map((row) => <HouseCard key={row.house} row={row} />);
    }

    if (activeTab === 'nakshatras') {
      if (!planetsPayload || planets.length === 0) return chartUnavailable;
      if (nakshatraRows.length === 0) {
        return <Text style={[styles.emptyText, { color: colors.textSecondary }]}>—</Text>;
      }
      return nakshatraRows.map((row) => <NakshatraCard key={row.nakshatra} row={row} />);
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
      const yogiPoint = isSpecialPoint(yogiPoints?.yogi) ? yogiPoints.yogi : null;
      const duplicateYogi = isSpecialPoint(yogiPoints?.duplicate_yogi) ? yogiPoints.duplicate_yogi : null;
      const avayogiPoint = isSpecialPoint(yogiPoints?.avayogi) ? yogiPoints.avayogi : null;
      const tithiDagdhaRashis = Array.isArray(yogiPoints?.tithi_dagdha_rashis)
        ? yogiPoints.tithi_dagdha_rashis.filter(isSpecialPoint)
        : [];
      const duplicateAvayogiOverlap = Boolean(
        yogiPoints?.duplicate_yogi_avayogi_overlap?.is_active
        || (
          duplicateYogi?.lord
          && avayogiPoint?.lord
          && duplicateYogi.lord === avayogiPoint.lord
        ),
      );

      const renderYogiPoint = ({ key, title, point, explanation }) => {
        if (!point) return null;
        return (
          <View key={key} style={[styles.specialCard, { backgroundColor: specialCardBg, borderColor: specialCardBorder }]}>
            <Text style={[styles.specialPointName, { color: colors.text }]}>{title}</Text>
            <Text style={[styles.specialPointValue, { color: colors.primary }]}>
              {point.sign_name} {formatPointDegrees(point.degree)}
            </Text>
            <Text style={[styles.specialPointLord, { color: colors.textSecondary }]}>
              {t('premiumUi.planetaryPositions.specialPoints.lord', 'Lord: {{planet}}', { planet: point.lord || '—' })}
            </Text>
            {point.nakshatra_name ? (
              <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                {t('premiumUi.planetaryPositions.specialPoints.nakshatra', 'Nakshatra: {{name}}', { name: point.nakshatra_name })}
              </Text>
            ) : null}
            <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>{explanation}</Text>
          </View>
        );
      };

      return (
        <View>
          {/* Yogi Points */}
          {yogiPoints && (
            <View style={styles.specialSection}>
              <Text style={[styles.specialSectionTitle, { color: colors.text }]}>{t('premiumUi.planetaryPositions.specialPoints.yogiPoints', 'Yogi points')}</Text>
              {renderYogiPoint({
                key: 'yogi',
                title: t('premiumUi.planetaryPositions.specialPoints.yogi', 'Yogi'),
                point: yogiPoint,
                explanation: t('premiumUi.planetaryPositions.specialPoints.yogiExplanation', 'The lord of the nakshatra containing the Yogi point.'),
              })}
              {renderYogiPoint({
                key: 'duplicate-yogi',
                title: t('premiumUi.planetaryPositions.specialPoints.duplicateYogi', 'Duplicate Yogi'),
                point: duplicateYogi,
                explanation: t('premiumUi.planetaryPositions.specialPoints.duplicateYogiExplanation', 'The lord of the zodiac sign containing the Yogi point.'),
              })}
              {renderYogiPoint({
                key: 'avayogi',
                title: t('premiumUi.planetaryPositions.specialPoints.avayogi', 'Avayogi'),
                point: avayogiPoint,
                explanation: t('premiumUi.planetaryPositions.specialPoints.avayogiExplanation', 'The lord of the nakshatra containing the Avayogi point.'),
              })}
              {duplicateAvayogiOverlap ? (
                <View style={[styles.specialCard, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
                  <Text style={[styles.specialPointName, { color: colors.text }]}>{t('premiumUi.planetaryPositions.specialPoints.dualRoleTitle', 'One planet, two separate roles')}</Text>
                  <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>
                    {t('premiumUi.planetaryPositions.specialPoints.dualRoleBody', '{{planet}} is Duplicate Yogi because it rules the Yogi point’s sign, and Avayogi because it rules the Avayogi point’s nakshatra. These roles come from separate calculations and must be read together as an overlap.', { planet: duplicateYogi.lord })}
                  </Text>
                </View>
              ) : null}
              <Text style={[styles.specialSectionTitle, { color: colors.text }]}>{t('premiumUi.planetaryPositions.specialPoints.tithiDagdhaRashis', 'Tithi Dagdha Rashis')}</Text>
              {tithiDagdhaRashis.length > 0 ? tithiDagdhaRashis.map((row) => (
                <View key={`dagdha-${row.sign}`} style={[styles.specialCard, { backgroundColor: specialCardBg, borderColor: specialCardBorder }]}>
                  <Text style={[styles.specialPointName, { color: colors.text }]}>{row.sign_name}</Text>
                  <Text style={[styles.specialPointLord, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.specialPoints.lord', 'Lord: {{planet}}', { planet: row.lord || '—' })}</Text>
                </View>
              )) : (
                <View style={[styles.specialCard, { backgroundColor: specialCardBg, borderColor: specialCardBorder }]}>
                  <Text style={[styles.specialPointName, { color: colors.text }]}>{t('premiumUi.planetaryPositions.specialPoints.noneForTithi', 'None for this tithi')}</Text>
                  <Text style={[styles.specialPointDesc, { color: colors.textSecondary }]}>{t('premiumUi.planetaryPositions.specialPoints.noneForTithiBody', 'Purnima and Amavasya have no Tithi Dagdha Rashi in the selected table.')}</Text>
                </View>
              )}
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
              <TabButton label={t('premiumUi.planetaryPositions.tabs.houses', 'Houses')} emoji="🏠" value="houses" active={activeTab === 'houses'} />
              <TabButton label={t('premiumUi.planetaryPositions.tabs.nakshatras', 'Nakshatras')} emoji="⭐" value="nakshatras" active={activeTab === 'nakshatras'} />
              <TabButton label={t('premiumUi.planetaryPositions.tabs.karakas', 'Karakas')} emoji="🔱" value="karakas" active={activeTab === 'karakas'} />
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
            <View style={{ height: 32 }} />
          </GHScrollView>
          {activeTab === 'planets' && !loading && planets.length > 0 ? <PlanetDock /> : null}
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
