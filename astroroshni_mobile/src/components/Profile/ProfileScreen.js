import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView as RNScrollView,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
  StatusBar,
  Alert,
  Modal,
  Linking,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ScrollView as GHScrollView } from 'react-native-gesture-handler';
import Svg, { Rect, Line, Polygon } from 'react-native-svg';
import { COLORS, LANGUAGES } from '../../utils/constants';
import { parseCalendarDateInput, formatBirthDateForDisplay } from '../../utils/birthDateUtils';
import { storage } from '../../services/storage';
import { useCredits } from '../../credits/CreditContext';
import { useAuthGate } from '../../auth/AuthGateContext';
import { useTheme } from '../../context/ThemeContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useTranslation } from 'react-i18next';
import i18n from '../../locales/i18n';
import CascadingDashaBrowser from '../Dasha/CascadingDashaBrowser';
import ThemePicker from '../Common/ThemePicker';
import { DISPLAY_FONT_FAMILY } from '../../theme/tokens';

const { width } = Dimensions.get('window');

const FAMILY_RELATION_ORDER = ['self', 'father', 'mother', 'spouse', 'child', 'sibling', 'friend', 'shared', 'other'];

const normalizeRelation = (value) => String(value || 'other').trim().toLowerCase();

const relationRank = (profile) => {
  const relation = normalizeRelation(profile?.relation);
  const rank = FAMILY_RELATION_ORDER.indexOf(relation);
  return rank >= 0 ? rank : FAMILY_RELATION_ORDER.length;
};

const getRelationLabel = (profile) => {
  const relation = normalizeRelation(profile?.relation);
  if (profile?.relation_label) return profile.relation_label;
  if (relation === 'self') return 'You';
  if (relation === 'father') return 'Father';
  if (relation === 'mother') return 'Mother';
  if (relation === 'spouse') return 'Spouse';
  if (relation === 'child') {
    const order = Number(profile?.relation_order);
    if (order === 1) return '1st child';
    if (order === 2) return '2nd child';
    if (order === 3) return '3rd child';
    return 'Child';
  }
  if (relation === 'sibling') {
    const order = Number(profile?.relation_order);
    if (order < 0) return 'Elder sibling';
    if (order > 0) return 'Younger sibling';
    return 'Sibling';
  }
  if (relation === 'friend') return 'Friend';
  if (relation === 'shared') return 'Shared';
  return 'Other';
};

export default function ProfileScreen({ navigation, route }) {
  const { t } = useTranslation();
  useAnalytics('ProfileScreen');
  const {
    colors,
    isPanditMode,
    enterPanditMode,
    exitPanditMode,
  } = useTheme();
  const { credits } = useCredits();
  const { requireAuthForPaid, isGuest, refreshAuthState } = useAuthGate();
  const [userData, setUserData] = useState(null);
  const [birthData, setBirthData] = useState(null);
  const [stats, setStats] = useState({ totalChats: 0, chartsViewed: 0, podcastsCount: 0 });
  const [chartData, setChartData] = useState(null);
  const [loadingChart, setLoadingChart] = useState(false);
  const [showDashaBrowser, setShowDashaBrowser] = useState(false);
  const [dashaData, setDashaData] = useState(null);
  const [loadingDashas, setLoadingDashas] = useState(false);
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [language, setLanguage] = useState(i18n.language);
  const [pushSyncing, setPushSyncing] = useState(false);
  const [familyCharts, setFamilyCharts] = useState([]);
  const [selectedFamilyChart, setSelectedFamilyChart] = useState(null);

  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    loadUserData();
    const stopAnimations = startAnimations();
    const loadLanguage = async () => {
      const savedLanguage = await storage.getLanguage();
      if (savedLanguage) {
        setLanguage(savedLanguage);
        i18n.changeLanguage(savedLanguage);
      }
    }
    loadLanguage();

    // Add focus listener to reload data when returning to screen
    const unsubscribe = navigation.addListener('focus', () => {
      loadUserData();
    });

    return () => {
      stopAnimations?.();
      unsubscribe();
    };
  }, [navigation]);

  useEffect(() => {
    if (!route.params?.reopenDashaBrowser) return;
    const selectedBirthData = route.params?.birthData || route.params?.birthDetails;
    navigation.setParams({
      reopenDashaBrowser: undefined,
      birthData: undefined,
      birthDetails: undefined,
      birthChartId: undefined,
    });
    if (selectedBirthData?.name) {
      setBirthData(selectedBirthData);
    }
    setTimeout(() => setShowDashaBrowser(true), 100);
  }, [navigation, route.params?.reopenDashaBrowser]);

  const startAnimations = () => {
    const entranceAnimation = Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 8,
        useNativeDriver: true,
      }),
    ]);
    entranceAnimation.start();
    return () => entranceAnimation.stop();
  };

  const loadUserData = async () => {
    try {
      const user = await storage.getUserData();
      setUserData(user);
      const token = await storage.getAuthToken();

      if (!token) {
        const localBirth = await storage.getBirthDetails();
        setBirthData(localBirth);
        if (localBirth) {
          loadChartData(localBirth);
          loadDashaData(localBirth);
        }
        setStats({ totalChats: 0, chartsViewed: 0, podcastsCount: 0 });
        return;
      }

      // Fetch user's self birth chart from API
      const { authAPI, chatAPI } = require('../../services/api');
      const response = await authAPI.getSelfBirthChart();


      if (response.data.has_self_chart) {
        const birthDataWithId = {
          ...response.data,
          id: response.data.birth_chart_id // Ensure id is included
        };
        setBirthData(birthDataWithId);
        loadChartData(birthDataWithId);
        loadDashaData(birthDataWithId);
      } else {
        const localBirth = await storage.getBirthDetails();
        setBirthData(localBirth);
        if (localBirth) {
          loadChartData(localBirth);
          loadDashaData(localBirth);
        }
      }
      // Load real profile stats (chats, charts, days)
      const statsRes = await authAPI.getUserStats();
      let podcastsCount = 0;
      try {
        const podcastHistoryRes = await chatAPI.getPodcastHistory();
        const podcasts = podcastHistoryRes?.data?.podcasts;
        podcastsCount = Array.isArray(podcasts) ? podcasts.length : 0;
      } catch (_) {}
      if (statsRes.data) {
        setStats({
          totalChats: statsRes.data.total_chat_sessions ?? 0,
          chartsViewed: statsRes.data.total_birth_charts ?? 0,
          podcastsCount,
        });
      }
      loadFamilyCharts();
    } catch (error) {
      setBirthData(null);
      // Still try to load stats on error (e.g. no self chart but user exists)
      try {
        const { authAPI, chatAPI } = require('../../services/api');
        const statsRes = await authAPI.getUserStats();
        let podcastsCount = 0;
        try {
          const podcastHistoryRes = await chatAPI.getPodcastHistory();
          const podcasts = podcastHistoryRes?.data?.podcasts;
          podcastsCount = Array.isArray(podcasts) ? podcasts.length : 0;
        } catch (_) {}
        if (statsRes.data) {
          setStats({
            totalChats: statsRes.data.total_chat_sessions ?? 0,
            chartsViewed: statsRes.data.total_birth_charts ?? 0,
            podcastsCount,
          });
        }
      } catch (_) {}
      loadFamilyCharts();
    }
  };

  const loadFamilyCharts = async () => {
    try {
      const { chartAPI } = require('../../services/api');
      const response = await chartAPI.getExistingCharts('', 100, 0);
      const charts = Array.isArray(response?.data?.charts) ? response.data.charts : [];
      const sortedCharts = [...charts].sort((a, b) => {
        const rankDiff = relationRank(a) - relationRank(b);
        if (rankDiff !== 0) return rankDiff;
        const orderDiff = (Number(a.relation_order) || 0) - (Number(b.relation_order) || 0);
        if (orderDiff !== 0) return orderDiff;
        return String(a.name || '').localeCompare(String(b.name || ''));
      });
      setFamilyCharts(sortedCharts);
    } catch (_) {
      setFamilyCharts([]);
    }
  };

  const loadChartData = async (birth) => {
    try {
      setLoadingChart(true);
      const formattedData = {
        ...birth,
        date: typeof birth.date === 'string' ? birth.date.split('T')[0] : birth.date,
        time: typeof birth.time === 'string' ? birth.time.split('T')[1]?.slice(0, 5) || birth.time : birth.time,
        latitude: parseFloat(birth.latitude),
        longitude: parseFloat(birth.longitude),
      };

      const { chartAPI } = require('../../services/api');
      const response = await chartAPI.calculateChartOnly(formattedData);
      setChartData(response.data);
    } catch (error) {
      // Chart data loading failed
    } finally {
      setLoadingChart(false);
    }
  };

  const ZODIAC_KEYS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio',
    'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
  ];

  const getSignName = (signNumber) => {
    if (signNumber === undefined || signNumber === null || signNumber === '') {
      return null;
    }
    const en = ZODIAC_KEYS[signNumber];
    if (en == null) return null;
    return t(`signs.${en}`, en);
  };

  const formatSignLabel = (signNumber) => {
    const name = getSignName(signNumber);
    if (!name) return t('profile.signUnavailable', '—');
    return `${getSignIcon(signNumber)} ${name}`;
  };

  const getDashaPlanetLabel = (planet) => {
    if (!planet) return '...';
    return t(`home.planet_names.${planet}`, planet);
  };

  const getSignIcon = (signNumber) => {
    const icons = {
      0: '♈', 1: '♉', 2: '♊', 3: '♋',
      4: '♌', 5: '♍', 6: '♎', 7: '♏',
      8: '♐', 9: '♑', 10: '♒', 11: '♓'
    };
    return icons[signNumber] || '⭐';
  };

  const loadDashaData = async (birth) => {
    try {
      setLoadingDashas(true);
      const targetDate = new Date().toISOString().split('T')[0];

      const formattedBirthData = {
        name: birth.name,
        date: birth.date.includes('T') ? birth.date.split('T')[0] : birth.date,
        time: birth.time.includes('T') ? new Date(birth.time).toTimeString().slice(0, 5) : birth.time,
        latitude: parseFloat(birth.latitude),
        longitude: parseFloat(birth.longitude),
        location: birth.place || 'Unknown'
      };

      const { chartAPI } = require('../../services/api');
      const response = await chartAPI.calculateCascadingDashas(formattedBirthData, targetDate);

      if (response.data && !response.data.error) {
        setDashaData(response.data);
      }
    } catch (error) {
      // Dasha data loading failed
    } finally {
      setLoadingDashas(false);
    }
  };

  const handleLanguageChange = async (newLanguage) => {
    i18n.changeLanguage(newLanguage);
    setLanguage(newLanguage);
    await storage.setLanguage(newLanguage);
    setShowLanguageModal(false);
  };

  const openChartsHub = (chart = birthData) => {
    if (chart) {
      navigation.navigate('ChartsHub', { birthData: chart });
      return;
    }
    navigation.navigate('BirthForm', { returnTo: 'Profile' });
  };

  const openDashaBrowser = () => {
    if (birthData) {
      setShowDashaBrowser(true);
      return;
    }
    Alert.alert(
      t('profile.birthDataRequired', 'Birth Data Required'),
      t('profile.dashasAlert', 'Please connect your birth chart to view dashas.'),
    );
  };

  const getZodiacSign = (date) => {
    if (!date) return '♈';
    const d = parseCalendarDateInput(date);
    if (!d) return '♈';
    const month = d.getMonth() + 1;
    const day = d.getDate();

    if ((month === 3 && day >= 21) || (month === 4 && day <= 19)) return '♈';
    if ((month === 4 && day >= 20) || (month === 5 && day <= 20)) return '♉';
    if ((month === 5 && day >= 21) || (month === 6 && day <= 20)) return '♊';
    if ((month === 6 && day >= 21) || (month === 7 && day <= 22)) return '♋';
    if ((month === 7 && day >= 23) || (month === 8 && day <= 22)) return '♌';
    if ((month === 8 && day >= 23) || (month === 9 && day <= 22)) return '♍';
    if ((month === 9 && day >= 23) || (month === 10 && day <= 22)) return '♎';
    if ((month === 10 && day >= 23) || (month === 11 && day <= 21)) return '♏';
    if ((month === 11 && day >= 22) || (month === 12 && day <= 21)) return '♐';
    if ((month === 12 && day >= 22) || (month === 1 && day <= 19)) return '♑';
    if ((month === 1 && day >= 20) || (month === 2 && day <= 18)) return '♒';
    return '♓';
  };

  const ChartIconSvg = ({ color = colors.primary, size = 32 }) => (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Rect x="2" y="2" width="44" height="44" fill="none" stroke={color} strokeWidth="2" />
      <Polygon points="24,2 46,24 24,46 2,24" fill="none" stroke={color} strokeWidth="1.5" opacity={0.9} />
      <Line x1="2" y1="2" x2="46" y2="46" stroke={color} strokeWidth="1" opacity={0.7} />
      <Line x1="46" y1="2" x2="2" y2="46" stroke={color} strokeWidth="1" opacity={0.7} />
    </Svg>
  );

  const StatCard = ({ icon, iconElement, value, label, onPress }) => (
    <TouchableOpacity
      activeOpacity={0.85}
      onPress={onPress}
      disabled={!onPress}
      style={{ flex: 1 }}
    >
      <Animated.View
        style={[
          styles.statCard,
          { opacity: fadeAnim, transform: [{ translateY: slideAnim }], backgroundColor: colors.surface, borderColor: colors.cardBorder },
        ]}
      >
        <View style={styles.statGradient}>
          {iconElement != null ? (
            <View style={styles.statIconWrap}>{iconElement}</View>
          ) : (
            <Text style={[styles.statIcon, { color: colors.primary }]}>{icon}</Text>
          )}
          <Text style={[styles.statValue, { color: colors.text }]}>{value}</Text>
          <Text style={[styles.statLabel, { color: colors.textSecondary }]}>{label}</Text>
        </View>
      </Animated.View>
    </TouchableOpacity>
  );

  const ActionButton = ({ icon, label, onPress }) => (
    <TouchableOpacity
      style={[styles.actionButton, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}
      onPress={onPress}
      activeOpacity={0.82}
    >
      <View style={styles.actionGradient}>
        <View style={styles.actionContent}>
          <View style={[styles.actionIcon, { backgroundColor: colors.selectionSurface }]}>
            <Ionicons name={icon} size={19} color={colors.primary} />
          </View>
          <Text style={[styles.actionLabel, { color: colors.text }]}>{label}</Text>
          <Ionicons name="arrow-forward" size={16} color={colors.textTertiary} />
        </View>
      </View>
    </TouchableOpacity>
  );

  const FamilyChartChip = ({ chart }) => {
    const relation = getRelationLabel(chart);
    return (
      <TouchableOpacity
        style={[
          styles.familyChip,
          {
            backgroundColor: colors.surface,
            borderColor: colors.cardBorder,
          },
        ]}
        onPress={() => setSelectedFamilyChart(chart)}
      >
        <Text style={[styles.familyChipRelation, { color: colors.primary }]} numberOfLines={1}>
          {relation}
        </Text>
        <Text style={[styles.familyChipName, { color: colors.text }]} numberOfLines={1}>
          {chart.name || t('profile.unnamedChart', 'Unnamed')}
        </Text>
      </TouchableOpacity>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} translucent={false} />
      <LinearGradient
        colors={[colors.background, colors.backgroundSecondary, colors.background]}
        style={styles.gradient}
      >
        <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.headerSurface }]}>
          <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine }]}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.backButton, { backgroundColor: colors.cosmicRaised }]}>
              <Ionicons name="arrow-back" size={22} color={colors.textInverse} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.textInverse }]}>
              {t('profile.myProfile', 'Your space')}
            </Text>
            <TouchableOpacity
              style={[styles.editButton, { backgroundColor: colors.cosmicRaised }]}
              onPress={() => navigation.navigate('BirthForm', { editProfile: birthData })}
              accessibilityLabel={t('profile.editBirthDetails', 'Edit birth details')}
            >
              <Ionicons name="create-outline" size={19} color={colors.textInverse} />
            </TouchableOpacity>
          </View>

          <GHScrollView
            style={[styles.scrollView, { backgroundColor: colors.background }]}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
            nestedScrollEnabled
            directionalLockEnabled
          >
            {isGuest ? (
              <TouchableOpacity
                activeOpacity={0.9}
                onPress={() => navigation.navigate('Login')}
                style={[styles.guestCard, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}
              >
                <Text style={{ color: colors.text, fontWeight: '800', fontSize: 15 }}>
                  {t('profile.guestSignInTitle', 'Exploring as guest')}
                </Text>
                <Text style={{ color: colors.textSecondary, marginTop: 4, fontSize: 13 }}>
                  {t(
                    'profile.guestSignInBody',
                    'Sign in to save charts to your account, buy credits, and unlock paid insights.',
                  )}
                </Text>
              </TouchableOpacity>
            ) : null}
            <Animated.View
              style={[
                styles.profileHeader,
                { opacity: fadeAnim, backgroundColor: colors.headerSurface, borderColor: colors.cosmicLine },
              ]}
            >
              <View pointerEvents="none" style={styles.heroLinework}>
                <View style={[styles.heroOrbitOuter, { borderColor: colors.cosmicLine }]} />
                <View style={[styles.heroOrbitInner, { borderColor: colors.accent }]} />
                <View style={[styles.heroGoldRule, { backgroundColor: colors.accent }]} />
                <View style={[styles.heroGoldDot, { backgroundColor: colors.accent }]} />
              </View>
              <View style={styles.avatarContainer}>
                <View style={[styles.avatar, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}>
                  <Text style={[styles.avatarText, { color: colors.accent }]}>
                    {chartData ? (() => {
                      const signIndex = chartData?.houses?.[0]?.sign || 0;
                      return getSignIcon(signIndex);
                    })() : (loadingChart ? '⏳' : getZodiacSign(birthData?.date))}
                  </Text>
                </View>
              </View>
              <Text style={[styles.profileEyebrow, { color: colors.accent }]}>{t('premiumUi.profile.yourAstroRoshni')}</Text>
              <Text style={[styles.userName, { color: colors.textInverse }]}>
                {userData?.name || t('profile.user', 'User')}
              </Text>
              <Text style={[styles.userSubtitle, { color: colors.textInverseMuted }]}>
                {birthData?.date
                  ? formatBirthDateForDisplay(birthData.date, {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric',
                    })
                  : t('profile.birthDateNotSet', 'Birth date not set')}
              </Text>
              {birthData?.time && (
                <Text style={[styles.userSubtitle, { color: colors.textInverseMuted }]}>🕐 {birthData.time}</Text>
              )}
              {!birthData?.date && (
                <TouchableOpacity
                  style={styles.connectChartButton}
                  onPress={() => navigation.navigate('SelectNative', { fromProfile: true })}
                >
                  <View style={[styles.connectChartGradient, { backgroundColor: colors.accent }]}>
                    <Text style={[styles.connectChartText, { color: colors.onAccent }]}>
                      {`📊 ${t('profile.connectChart', 'Connect Chart to Profile')}`}
                    </Text>
                  </View>
                </TouchableOpacity>
              )}
              {birthData?.place && (
                <Text style={[styles.userLocation, { color: colors.textInverseMuted }]}>📍 {birthData.place}</Text>
              )}
            </Animated.View>

            <Animated.View style={[styles.creditsCard, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
              <LinearGradient
                colors={[colors.surfaceInverse, colors.cosmicRaised]}
                style={styles.creditsGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <View style={styles.creditsContent}>
                  <View>
                    <Text style={[styles.creditsLabel, { color: colors.textInverseMuted }]}>
                      {t('profile.availableCredits', 'Available Credits')}
                    </Text>
                    <Text style={[styles.creditsValue, { color: colors.textInverse }]}>{credits}</Text>
                  </View>
                  <TouchableOpacity
                    style={[styles.addCreditsButton, { backgroundColor: colors.accent, borderColor: colors.accent }]}
                    onPress={async () => {
                      const authOk = await requireAuthForPaid({
                        feature: t('authGate.featureCredits'),
                        message: t('authGate.messageCredits'),
                        resume: { resumeRoute: 'Credits', resumeParams: {} },
                      });
                      if (!authOk) return;
                      navigation.navigate('Credits');
                    }}
                  >
                    <Text style={[styles.addCreditsText, { color: colors.onAccent }]}>{t('profile.add', 'Add credits')}</Text>
                  </TouchableOpacity>
                </View>
              </LinearGradient>
            </Animated.View>

            <View style={styles.statsGrid}>
              <StatCard
                icon="💬"
                value={stats.totalChats}
                label={t('profile.chats', 'Chats')}
                onPress={() => navigation.navigate('ChatHistory')}
              />
              <StatCard
                iconElement={<ChartIconSvg color={colors.primary} size={28} />}
                value={stats.chartsViewed}
                label={t('profile.charts', 'Charts')}
                onPress={() => navigation.navigate('SelectNative', { fromProfile: true })}
              />
              <StatCard
                icon="🎙️"
                value={stats.podcastsCount}
                label={t('profile.podcasts', 'Podcasts')}
                onPress={() => navigation.navigate('PodcastHistory')}
              />
            </View>

            <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
              <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{t('premiumUi.profile.savedPeople')}</Text>
              <View style={styles.familySectionHeader}>
                <Text style={[styles.sectionTitle, styles.familySectionTitle, { color: colors.text }]}>
                  {t('profile.familyCharts', 'Birth chart library')}
                </Text>
                <TouchableOpacity
                  style={[
                    styles.familyAddButton,
                    { backgroundColor: colors.selectionSurface },
                  ]}
                  onPress={() => navigation.navigate('BirthForm', { returnTo: 'Profile' })}
                >
                  <Ionicons name="add" size={16} color={colors.primary} />
                  <Text style={[styles.familyAddText, { color: colors.primary }]}>
                    {t('common.add', 'Add')}
                  </Text>
                </TouchableOpacity>
              </View>
              {familyCharts.length > 0 ? (
                <GHScrollView
                  horizontal
                  nestedScrollEnabled
                  directionalLockEnabled
                  alwaysBounceHorizontal
                  showsHorizontalScrollIndicator={false}
                  style={styles.familyChipsScroll}
                  contentContainerStyle={styles.familyChipRow}
                >
                  {familyCharts.map((chart) => (
                    <FamilyChartChip key={chart.id} chart={chart} />
                  ))}
                </GHScrollView>
              ) : (
                <TouchableOpacity
                  style={[
                    styles.familyEmptyCard,
                    {
                      backgroundColor: colors.surface,
                      borderColor: colors.cardBorder,
                    },
                  ]}
                  onPress={() => navigation.navigate('BirthForm', { returnTo: 'Profile' })}
                >
                  <Ionicons name="people-outline" size={22} color={colors.primary} />
                  <Text style={[styles.familyEmptyText, { color: colors.text }]}>
                    {t('profile.addFamilyChartsPrompt', 'Add family charts to organize relatives in one place.')}
                  </Text>
                </TouchableOpacity>
              )}
            </Animated.View>

            <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
              <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{t('premiumUi.profile.currentSky')}</Text>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                {t('profile.birthChartEssence', 'Birth chart essence')}
              </Text>
              <View style={[styles.chartSummaryCard, { borderColor: colors.cardBorder }]}>
                <LinearGradient
                  colors={[colors.surface, colors.surfaceRaised]}
                  style={styles.chartSummaryGradient}
                >
                  <TouchableOpacity
                    style={styles.essenceHeader}
                    onPress={() => openChartsHub()}
                    activeOpacity={0.82}
                  >
                    <View style={[styles.essenceChartIcon, { backgroundColor: colors.selectionSurface }]}>
                      <Svg width="50" height="50" viewBox="0 0 48 48">
                        <Rect x="2" y="2" width="44" height="44" fill="none" stroke={colors.primary} strokeWidth="2" />
                        <Polygon points="24,2 46,24 24,46 2,24" fill="none" stroke={colors.chartLineStrong} strokeWidth="1.7" />
                        <Line x1="2" y1="2" x2="46" y2="46" stroke={colors.chartLine} strokeWidth="1" />
                        <Line x1="46" y1="2" x2="2" y2="46" stroke={colors.chartLine} strokeWidth="1" />
                      </Svg>
                    </View>
                    <View style={styles.essenceHeaderCopy}>
                      <Text style={[styles.essenceLabel, { color: colors.primary }]}>{t('premiumUi.profile.natalFoundation')}</Text>
                      <Text style={[styles.essenceName, { color: colors.text }]} numberOfLines={1}>
                        {birthData?.name || userData?.name || t('profile.user', 'Your chart')}
                      </Text>
                      <Text style={[styles.essenceMeta, { color: colors.textSecondary }]}>
                        {t('profile.viewFullChart', 'Open the complete chart workbench')}
                      </Text>
                    </View>
                    <View style={[styles.essenceArrow, { borderColor: colors.cardBorder }]}>
                      <Ionicons name="arrow-forward" size={18} color={colors.primary} />
                    </View>
                  </TouchableOpacity>

                  <View style={[styles.bigThreeGrid, { borderColor: colors.cardBorder }]}>
                    {[
                      [t('profile.ascendant', 'Ascendant'), chartData?.houses?.[0]?.sign],
                      [t('profile.moonSign', 'Moon'), chartData?.planets?.Moon?.sign],
                      [t('profile.sunSign', 'Sun'), chartData?.planets?.Sun?.sign],
                    ].map(([label, sign], index) => (
                      <View
                        key={label}
                        style={[styles.bigThreeItem, index < 2 && { borderRightWidth: 1, borderRightColor: colors.cardBorder }]}
                      >
                        <Text style={[styles.bigThreeLabel, { color: colors.textTertiary }]}>{label}</Text>
                        <Text style={[styles.bigThreeValue, { color: colors.text }]} numberOfLines={1}>
                          {loadingChart ? '…' : formatSignLabel(sign)}
                        </Text>
                      </View>
                    ))}
                  </View>

                  <TouchableOpacity
                    style={[styles.dashaPanel, { backgroundColor: colors.surfaceInverse, borderColor: colors.cosmicLine }]}
                    onPress={openDashaBrowser}
                    activeOpacity={0.84}
                  >
                    <View style={styles.dashaPanelHeader}>
                      <View>
                        <Text style={[styles.dashaPanelEyebrow, { color: colors.accent }]}>{t('premiumUi.profile.currentTimingCycle')}</Text>
                        <Text style={[styles.dashaPanelTitle, { color: colors.onSurfaceInverse }]}>{t('premiumUi.profile.vimshottariDasha')}</Text>
                      </View>
                      <Ionicons name="arrow-forward" size={19} color={colors.accent} />
                    </View>
                    <View style={styles.dashaPanelChain}>
                      {loadingDashas ? (
                        <Text style={[styles.dashasLoading, { color: colors.onSurfaceInverseMuted }]}>
                          {t('profile.loading', 'Loading...')}
                        </Text>
                      ) : (
                        [
                          { level: 'Maha', data: dashaData?.maha_dashas?.find(d => d.current) },
                          { level: 'Antar', data: dashaData?.antar_dashas?.find(d => d.current) },
                          { level: 'Pratyantar', data: dashaData?.pratyantar_dashas?.find(d => d.current) },
                        ].map((dasha, index) => (
                          <React.Fragment key={dasha.level}>
                            <View style={styles.dashaChainItem}>
                              <Text style={[styles.dashaLevel, { color: colors.onSurfaceInverseMuted }]}>
                                {t(`profile.dashaLevels.${dasha.level}`, dasha.level)}
                              </Text>
                              <Text style={[styles.dashaPlanet, { color: colors.onSurfaceInverse }]} numberOfLines={1}>
                                {getDashaPlanetLabel(dasha.data?.planet)}
                              </Text>
                            </View>
                            {index < 2 ? <Text style={[styles.dashaChainArrow, { color: colors.accent }]}>→</Text> : null}
                          </React.Fragment>
                        ))
                      )}
                    </View>
                    <Text style={[styles.dashaPanelHint, { color: colors.onSurfaceInverseMuted }]}>{t('premiumUi.profile.exploreDashas')}</Text>
                  </TouchableOpacity>
                </LinearGradient>
              </View>
            </Animated.View>

            <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
              <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{t('premiumUi.profile.library')}</Text>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                {t('profile.quickActionsTitle', 'Continue your journey')}
              </Text>
              <View style={styles.actionsGrid}>
                <ActionButton
                  icon="chatbubbles"
                  label={t('profile.quickActions.newChat')}
                  onPress={() => navigation.navigate('Home', { startChat: true })}
                />
                <ActionButton
                  icon="pie-chart"
                  label={t('profile.quickActions.viewChart')}
                  onPress={() => openChartsHub()}
                />
                <ActionButton
                  icon="time"
                  label={t('profile.quickActions.dashas')}
                  onPress={openDashaBrowser}
                />
                <ActionButton
                  icon="calendar"
                  label={t('profile.quickActions.history')}
                  onPress={() => navigation.navigate('ChatHistory')}
                />
                <ActionButton
                  icon="list"
                  label={t('profile.quickActions.myFacts')}
                  onPress={() => {
                    if (birthData?.id) {
                      navigation.navigate('Facts', { birthChartId: birthData.id, nativeName: birthData.name });
                    } else {
                      navigation.navigate('Facts');
                    }
                  }}
                />
                <ActionButton
                  icon="language"
                  label={t('profile.quickActions.language')}
                  onPress={() => setShowLanguageModal(true)}
                />
              </View>
            </Animated.View>

            <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
              <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{t('premiumUi.profile.preferences')}</Text>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                {t('profile.settings', 'Settings')}
              </Text>
              <View style={[styles.settingsCard, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
                <TouchableOpacity
                  style={styles.settingItem}
                  onPress={() => navigation.navigate('AccountSecurity')}
                >
                  <View style={styles.settingLeft}>
                    <Ionicons name="shield-checkmark-outline" size={22} color={colors.primary} />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {t('profile.accountAndSecurity', 'Account & security')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>

                <View style={[styles.settingDivider, { backgroundColor: colors.cardBorder }]} />

                <TouchableOpacity
                  style={styles.settingItem}
                  onPress={async () => {
                    const { openPanditMode } = require('../Pandit/openPanditMode');
                    if (isPanditMode) {
                      await exitPanditMode();
                      return;
                    }
                    await openPanditMode({
                      navigation,
                      requireAuthForPaid,
                      enterPanditMode,
                    });
                  }}
                >
                  <View style={styles.settingLeft}>
                    <Ionicons name="flower-outline" size={22} color={colors.primary} />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {isPanditMode
                        ? t('profile.exitPanditMode', 'Exit Pandit mode')
                        : t('profile.panditDesk', 'I am a Pandit')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>

                <View style={[styles.settingDivider, { backgroundColor: colors.cardBorder }]} />

                <View style={{ paddingHorizontal: 16, paddingVertical: 18 }}>
                  <ThemePicker />
                </View>

                <View style={[styles.settingDivider, { backgroundColor: colors.cardBorder }]} />

                <TouchableOpacity
                  style={styles.settingItem}
                  onPress={() => navigation.navigate('NudgeInbox')}
                >
                  <View style={styles.settingLeft}>
                    <Ionicons name="mail-unread-outline" size={22} color={colors.primary} />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {t('profile.notificationHistory', 'Notification history')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>

                <View style={[styles.settingDivider, { backgroundColor: colors.cardBorder }]} />

                <TouchableOpacity
                  style={styles.settingItem}
                  disabled={pushSyncing}
                  onPress={async () => {
                    if (Platform.OS === 'ios') {
                      Alert.alert('Notifications', 'Push notifications are temporarily unavailable on iOS.');
                      return;
                    }
                    setPushSyncing(true);
                    try {
                      const { registerPushTokenIfLoggedIn } = require('../../services/pushNotifications');
                      const result = await registerPushTokenIfLoggedIn();
                      if (result.ok) {
                        Alert.alert('Notifications', result.message);
                      } else {
                        const isDenied = result.message.includes('Settings');
                        Alert.alert(
                          'Notifications',
                          result.message,
                          isDenied
                            ? [
                                { text: 'OK', style: 'cancel' },
                                { text: 'Open Settings', onPress: () => Linking.openSettings() },
                              ]
                            : [{ text: 'OK' }]
                        );
                      }
                    } finally {
                      setPushSyncing(false);
                    }
                  }}
                >
                  <View style={styles.settingLeft}>
                    <Ionicons name="notifications-outline" size={22} color={colors.primary} />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {pushSyncing
                        ? t('profile.turningOnNotifications', 'Turning on…')
                        : t('profile.turnOnNotifications', 'Turn ON Notifications')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>

                <View style={[styles.settingDivider, { backgroundColor: colors.cardBorder }]} />

                <TouchableOpacity style={styles.settingItem} onPress={() => navigation.navigate('SelectNative', { returnTo: 'Profile' })}>
                  <View style={styles.settingLeft}>
                    <Ionicons name="people-outline" size={22} color={colors.primary} />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {t('profile.familyCharts', 'Family Charts')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>

                <View style={[styles.settingDivider, { backgroundColor: colors.cardBorder }]} />

                <TouchableOpacity style={styles.settingItem} onPress={() => navigation.navigate('BirthForm', { editProfile: birthData })}>
                  <View style={styles.settingLeft}>
                    <Ionicons name="person-outline" size={22} color={colors.primary} />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {t('profile.editBirthDetails', 'Edit Birth Details')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>

                <View style={[styles.settingDivider, { backgroundColor: colors.cardBorder }]} />

                <TouchableOpacity style={styles.settingItem} onPress={() => navigation.navigate('About')}>
                  <View style={styles.settingLeft}>
                    <Ionicons name="information-circle-outline" size={22} color={colors.primary} />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {t('profile.aboutApp', 'About AstroRoshni')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>
              </View>
            </Animated.View>

            {!isGuest ? (
            <TouchableOpacity
              style={[styles.logoutButton, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}
              onPress={async () => {
                try {
                  await storage.clearAccountSession();
                } catch (_) {}
                try {
                  await refreshAuthState?.();
                } catch (_) {}
                // Guest mode: return to Home as guest instead of a Login wall.
                navigation.reset({ index: 0, routes: [{ name: 'Home' }] });
              }}
            >
              <Text
                style={[
                  styles.logoutText,
                  { color: colors.primary },
                ]}
              >
                {t('profile.logout', 'Log out')}
              </Text>
            </TouchableOpacity>
            ) : null}

            <View style={styles.bottomSpacer} />
          </GHScrollView>
        </SafeAreaView>
      </LinearGradient>

      <Modal
        visible={showLanguageModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowLanguageModal(false)}
      >
        <View style={[styles.modalOverlay, { backgroundColor: colors.overlay }]}>
          <View style={[styles.modalContent, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
            <Text style={[styles.modalTitle, { color: colors.text }]}>{t('languageModal.title')}</Text>
            <RNScrollView
              style={styles.languageModalScrollView}
              contentContainerStyle={styles.languageModalScrollContent}
              showsVerticalScrollIndicator={true}
              keyboardShouldPersistTaps="handled"
            >
              {LANGUAGES.map((lang) => (
                <TouchableOpacity
                  key={lang.code}
                  style={[
                    styles.languageOption,
                    { backgroundColor: colors.surfaceMuted, borderColor: 'transparent' },
                    language === lang.code && { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder },
                  ]}
                  onPress={() => handleLanguageChange(lang.code)}
                >
                  <Text style={[styles.languageText, { color: colors.text }]}>
                    {lang.flag} {lang.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </RNScrollView>
            <TouchableOpacity
              style={[styles.modalCloseButton, { backgroundColor: colors.primary }]}
              onPress={() => setShowLanguageModal(false)}
            >
              <Text style={[styles.modalCloseText, { color: colors.onPrimary }]}>{t('languageModal.close')}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      <Modal
        visible={!!selectedFamilyChart}
        transparent
        animationType="fade"
        onRequestClose={() => setSelectedFamilyChart(null)}
      >
        <View style={[styles.chartModalOverlay, { backgroundColor: colors.overlay }]}>
          <View
            style={[
              styles.chartModalContent,
              {
                backgroundColor: colors.surface,
                borderColor: colors.cardBorder,
              },
            ]}
          >
            <View style={styles.chartModalHeader}>
              <View style={[styles.chartModalIcon, { backgroundColor: colors.selectionSurface }]}>
                <Ionicons name="person-circle-outline" size={28} color={colors.primary} />
              </View>
              <View style={styles.chartModalTitleWrap}>
                <Text style={[styles.chartModalRelation, { color: colors.primary }]} numberOfLines={1}>
                  {selectedFamilyChart ? getRelationLabel(selectedFamilyChart) : ''}
                </Text>
                <Text style={[styles.chartModalName, { color: colors.text }]} numberOfLines={2}>
                  {selectedFamilyChart?.name || t('profile.unnamedChart', 'Unnamed')}
                </Text>
              </View>
              <TouchableOpacity style={styles.chartModalClose} onPress={() => setSelectedFamilyChart(null)}>
                <Ionicons name="close" size={22} color={colors.textSecondary} />
              </TouchableOpacity>
            </View>

            <View style={styles.chartModalDetails}>
              <View style={styles.chartModalRow}>
                <Text style={[styles.chartModalLabel, { color: colors.textSecondary }]}>
                  {t('profile.birthDate', 'Birth date')}
                </Text>
                <Text style={[styles.chartModalValue, { color: colors.text }]}>
                  {selectedFamilyChart?.date
                    ? formatBirthDateForDisplay(selectedFamilyChart.date, { month: 'long', day: 'numeric', year: 'numeric' })
                    : t('common.notSet', 'Not set')}
                </Text>
              </View>
              <View style={styles.chartModalRow}>
                <Text style={[styles.chartModalLabel, { color: colors.textSecondary }]}>
                  {t('profile.birthTime', 'Birth time')}
                </Text>
                <Text style={[styles.chartModalValue, { color: colors.text }]}>
                  {selectedFamilyChart?.time || t('common.notSet', 'Not set')}
                </Text>
              </View>
              <View style={styles.chartModalRow}>
                <Text style={[styles.chartModalLabel, { color: colors.textSecondary }]}>
                  {t('profile.birthPlace', 'Birth place')}
                </Text>
                <Text style={[styles.chartModalValue, { color: colors.text }]} numberOfLines={2}>
                  {selectedFamilyChart?.place || t('common.notSet', 'Not set')}
                </Text>
              </View>
              {selectedFamilyChart?.gender ? (
                <View style={styles.chartModalRow}>
                  <Text style={[styles.chartModalLabel, { color: colors.textSecondary }]}>
                    {t('profile.gender', 'Gender')}
                  </Text>
                  <Text style={[styles.chartModalValue, { color: colors.text }]}>
                    {selectedFamilyChart.gender}
                  </Text>
                </View>
              ) : null}
            </View>

            <View style={styles.chartModalActions}>
              <TouchableOpacity
                style={[styles.chartModalAction, { backgroundColor: colors.primary }]}
                onPress={() => {
                  const chart = selectedFamilyChart;
                  setSelectedFamilyChart(null);
                  openChartsHub(chart);
                }}
              >
                <Ionicons name="analytics-outline" size={18} color={colors.onPrimary} />
                <Text style={[styles.chartModalActionText, { color: colors.onPrimary }]}>{t('profile.viewChart', 'View Chart')}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.chartModalAction,
                  styles.chartModalSecondaryAction,
                  { borderColor: colors.primary },
                ]}
                onPress={() => {
                  const chart = selectedFamilyChart;
                  setSelectedFamilyChart(null);
                  navigation.navigate('BirthForm', { editProfile: chart });
                }}
              >
                <Ionicons name="create-outline" size={18} color={colors.primary} />
                <Text style={[styles.chartModalSecondaryActionText, { color: colors.primary }]}>
                  {t('common.edit', 'Edit')}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      <CascadingDashaBrowser
        visible={showDashaBrowser}
        onClose={() => setShowDashaBrowser(false)}
        birthData={birthData}
        onRequireBirthData={() => navigation.navigate('BirthProfileIntro', { returnTo: 'Profile' })}
        selectNativeReturnTo="Profile"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 13, borderBottomWidth: StyleSheet.hairlineWidth },
  backButton: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  headerTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 24, fontWeight: '600' },
  editButton: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  scrollView: { flex: 1 },
  scrollContent: { paddingHorizontal: 18, paddingTop: 18, paddingBottom: 48 },
  guestCard: { marginBottom: 14, borderRadius: 18, padding: 16, borderWidth: 1 },
  profileHeader: { alignItems: 'center', marginBottom: 14, paddingHorizontal: 22, paddingVertical: 24, borderRadius: 28, borderWidth: 1, overflow: 'hidden' },
  heroLinework: { ...StyleSheet.absoluteFillObject },
  heroOrbitOuter: { position: 'absolute', width: 190, height: 190, borderRadius: 95, borderWidth: 1, top: -98, right: -58, opacity: 0.72 },
  heroOrbitInner: { position: 'absolute', width: 126, height: 126, borderRadius: 63, borderWidth: StyleSheet.hairlineWidth, top: -66, right: -26, opacity: 0.38 },
  heroGoldRule: { position: 'absolute', width: 76, height: 1, left: 0, bottom: 28, opacity: 0.64 },
  heroGoldDot: { position: 'absolute', width: 5, height: 5, borderRadius: 3, left: 81, bottom: 26, opacity: 0.9 },
  profileEyebrow: { fontSize: 10, fontWeight: '800', letterSpacing: 1.8, marginBottom: 7 },
  avatarContainer: { marginBottom: 13 },
  zodiacRing: { display: 'none' },
  ringGradient: { display: 'none' },
  avatar: { width: 68, height: 68, borderRadius: 34, alignItems: 'center', justifyContent: 'center', borderWidth: 1 },
  avatarText: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 35 },
  userName: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 31, lineHeight: 37, fontWeight: '500', marginBottom: 7, textAlign: 'center' },
  userSubtitle: { fontSize: 13, lineHeight: 18, marginBottom: 2, textAlign: 'center' },
  userLocation: { fontSize: 12, lineHeight: 17, textAlign: 'center', marginTop: 3 },
  creditsCard: { marginBottom: 18, borderRadius: 22, overflow: 'hidden', elevation: 0 },
  creditsGradient: { paddingHorizontal: 20, paddingVertical: 17 },
  creditsContent: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  creditsLabel: { fontSize: 10, fontWeight: '800', letterSpacing: 1.4, textTransform: 'uppercase', marginBottom: 4 },
  creditsValue: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 31, lineHeight: 34, fontWeight: '500' },
  addCreditsButton: { paddingHorizontal: 17, paddingVertical: 10, borderRadius: 999, borderWidth: 1 },
  addCreditsText: { fontSize: 13, fontWeight: '800' },
  statsGrid: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 26, gap: 9 },
  statCard: { flex: 1, minHeight: 102, borderRadius: 18, overflow: 'hidden', borderWidth: 1 },
  statGradient: { paddingHorizontal: 8, paddingVertical: 14, alignItems: 'center' },
  statIcon: { fontSize: 21, marginBottom: 6 },
  statIconWrap: { height: 24, marginBottom: 6, alignItems: 'center', justifyContent: 'center' },
  statValue: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 22, lineHeight: 25, fontWeight: '600', marginBottom: 2 },
  statLabel: { fontSize: 10, fontWeight: '700', letterSpacing: 0.5, textTransform: 'uppercase' },
  section: { marginBottom: 28 },
  sectionEyebrow: { fontSize: 10, fontWeight: '800', letterSpacing: 1.6, marginBottom: 5 },
  sectionTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 25, lineHeight: 30, fontWeight: '500', marginBottom: 13 },
  familySectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 },
  familySectionTitle: { marginBottom: 0 },
  familyAddButton: { flexDirection: 'row', alignItems: 'center', gap: 4, borderRadius: 999, paddingVertical: 7, paddingHorizontal: 11 },
  familyAddText: { fontSize: 13, fontWeight: '800' },
  familyChipsScroll: { width: '100%' },
  familyChipRow: { flexDirection: 'row', gap: 10, paddingRight: 20 },
  familyChip: {
    width: 136,
    minHeight: 72,
    borderWidth: 1,
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 11,
    justifyContent: 'center',
  },
  familyChipRelation: { fontSize: 12, fontWeight: '800', marginBottom: 4 },
  familyChipName: { fontSize: 15, fontWeight: '700' },
  familyEmptyCard: {
    borderWidth: 1,
    borderRadius: 16,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  familyEmptyText: { flex: 1, fontSize: 14, fontWeight: '600', lineHeight: 19 },
  chartSummaryCard: { borderRadius: 24, overflow: 'hidden', borderWidth: 1 },
  chartSummaryGradient: { padding: 18 },
  essenceHeader: { flexDirection: 'row', alignItems: 'center', gap: 13, marginBottom: 17 },
  essenceChartIcon: { width: 66, height: 66, borderRadius: 19, alignItems: 'center', justifyContent: 'center' },
  essenceHeaderCopy: { flex: 1, minWidth: 0 },
  essenceLabel: { fontSize: 9, fontWeight: '800', letterSpacing: 1.2, marginBottom: 4 },
  essenceName: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 21, lineHeight: 25, fontWeight: '600', marginBottom: 3 },
  essenceMeta: { fontSize: 11, lineHeight: 15, fontWeight: '600' },
  essenceArrow: { width: 36, height: 36, borderRadius: 18, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  bigThreeGrid: { flexDirection: 'row', borderTopWidth: 1, borderBottomWidth: 1, marginBottom: 16 },
  bigThreeItem: { flex: 1, alignItems: 'center', paddingHorizontal: 5, paddingVertical: 13 },
  bigThreeLabel: { fontSize: 8, fontWeight: '800', letterSpacing: 0.8, textTransform: 'uppercase', marginBottom: 5 },
  bigThreeValue: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 15, fontWeight: '600' },
  dashaPanel: { borderRadius: 20, borderWidth: 1, paddingHorizontal: 16, paddingVertical: 15 },
  dashaPanelHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 13 },
  dashaPanelEyebrow: { fontSize: 8, fontWeight: '800', letterSpacing: 1.2, marginBottom: 4 },
  dashaPanelTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 19, lineHeight: 22, fontWeight: '600' },
  dashaPanelChain: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  dashaChainItem: { flex: 1, minWidth: 0 },
  dashaChainArrow: { fontSize: 15, marginHorizontal: 6 },
  dashaPanelHint: { fontSize: 10, fontWeight: '600', marginTop: 12 },
  miniChart: { alignItems: 'center', marginBottom: 18, paddingVertical: 16, borderRadius: 18 },
  miniChartIcon: { width: 48, height: 48, marginBottom: 8 },
  miniChartIcon: { fontSize: 48, marginBottom: 8 },
  miniChartText: { fontSize: 14, fontWeight: '600' },
  chartDetails: { gap: 12 },
  chartDetailRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  chartDetailLabel: { fontSize: 14 },
  chartDetailValue: { fontSize: 14, fontWeight: '600' },
  dashasContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.2)',
  },
  dashasTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    marginBottom: 8,
  },
  dashasRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    flexWrap: 'wrap',
    gap: 6,
  },
  dashasLoading: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    textAlign: 'center',
  },
  dashaChip: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    alignItems: 'center',
    minWidth: 50,
  },
  dashaLevel: {
    fontSize: 9,
    color: 'rgba(255, 255, 255, 0.7)',
    fontWeight: '600',
  },
  dashaPlanet: {
    fontSize: 11,
    fontWeight: '700',
    marginTop: 1,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    ...Platform.select({
      // PWA/web: percentage widths so 2 columns fit despite padding/gap rounding.
      // Native keeps the existing fixed-width layout (already correct on device).
      web: {
        justifyContent: 'space-between',
        rowGap: 12,
      },
      default: {
        gap: 12,
      },
    }),
  },
  actionButton: {
    borderRadius: 18,
    overflow: 'hidden',
    borderWidth: 1,
    elevation: 0,
    ...Platform.select({
      web: {
        width: '48%',
        maxWidth: '48%',
        flexGrow: 0,
        flexShrink: 0,
        boxSizing: 'border-box',
      },
      default: {
        width: (width - 52) / 2,
      },
    }),
  },
  actionGradient: { paddingHorizontal: 13, paddingVertical: 12 },
  actionContent: { flexDirection: 'row', alignItems: 'center', gap: 9 },
  actionIcon: { width: 34, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
  actionLabel: { flex: 1, fontSize: 13, fontWeight: '700' },
  settingsCard: { borderRadius: 22, padding: 4, borderWidth: 1, overflow: 'hidden' },
  settingItem: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16 },
  settingLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  settingText: { fontSize: 16, fontWeight: '500' },
  settingValue: { fontSize: 14, color: 'rgba(255, 255, 255, 0.6)' },
  settingDivider: { height: 1, backgroundColor: 'rgba(255, 255, 255, 0.1)', marginHorizontal: 16 },
  logoutButton: { borderWidth: 1, borderRadius: 18, padding: 16, alignItems: 'center', marginTop: 4 },
  logoutText: { fontSize: 16, fontWeight: '700' },
  bottomSpacer: { height: 20 },
  connectChartButton: {
    marginTop: 12,
    borderRadius: 16,
    overflow: 'hidden',
    elevation: 0,
  },
  connectChartGradient: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  connectChartText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    borderRadius: 24,
    padding: 24,
    width: '88%',
    maxHeight: '75%',
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  modalTitle: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 27,
    fontWeight: '500',
    textAlign: 'left',
    marginBottom: 24,
  },
  languageModalScrollView: {
    maxHeight: 320,
  },
  languageModalScrollContent: {
    paddingRight: 8,
    paddingBottom: 8,
  },
  languageOption: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
  },
  languageOptionSelected: {},
  languageText: {
    fontSize: 16,
    fontWeight: '600',
  },
  modalCloseButton: {
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  modalCloseText: {
    fontSize: 16,
    fontWeight: '700',
  },
  chartModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.62)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  chartModalContent: {
    width: '100%',
    borderRadius: 24,
    borderWidth: 1,
    padding: 18,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.35,
    shadowRadius: 24,
    elevation: 12,
  },
  chartModalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 18,
  },
  chartModalIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  chartModalTitleWrap: { flex: 1 },
  chartModalRelation: { fontSize: 13, fontWeight: '800', marginBottom: 2 },
  chartModalName: { fontSize: 20, fontWeight: '800', lineHeight: 24 },
  chartModalClose: { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  chartModalDetails: { gap: 12, marginBottom: 18 },
  chartModalRow: {
    borderTopWidth: 1,
    borderTopColor: 'rgba(128,128,128,0.16)',
    paddingTop: 10,
  },
  chartModalLabel: { fontSize: 12, fontWeight: '700', marginBottom: 3 },
  chartModalValue: { fontSize: 15, fontWeight: '700', lineHeight: 20 },
  chartModalActions: { flexDirection: 'row', gap: 10 },
  chartModalAction: {
    flex: 1,
    minHeight: 46,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 7,
  },
  chartModalSecondaryAction: {
    backgroundColor: 'transparent',
    borderWidth: 1,
  },
  chartModalActionText: { color: COLORS.white, fontSize: 14, fontWeight: '800' },
  chartModalSecondaryActionText: { fontSize: 14, fontWeight: '800' },
});
