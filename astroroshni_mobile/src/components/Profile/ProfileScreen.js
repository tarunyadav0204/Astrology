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
import { useTheme } from '../../context/ThemeContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useTranslation } from 'react-i18next';
import i18n from '../../locales/i18n';
import CascadingDashaBrowser from '../Dasha/CascadingDashaBrowser';
import NorthIndianChart from '../Chart/NorthIndianChart';

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
  const { theme, toggleTheme, colors } = useTheme();
  const { credits } = useCredits();
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
  const rotateAnim = useRef(new Animated.Value(0)).current;

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
    Animated.parallel([
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
    ]).start();

    const rotateLoop = Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 20000,
        useNativeDriver: true,
      })
    );
    rotateLoop.start();
    return () => {
      rotateLoop.stop();
    };
  };

  const loadUserData = async () => {
    try {
      const user = await storage.getUserData();
      setUserData(user);
      
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
        setBirthData(null);
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
    const en = ZODIAC_KEYS[signNumber];
    if (en == null) return signNumber;
    return t(`signs.${en}`, en);
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

  const getPlanetColor = (planetName) => {
    const colors = {
      'Sun': '#ff6b35',
      'Moon': '#e0e0e0',
      'Mars': '#d32f2f',
      'Mercury': '#4caf50',
      'Jupiter': '#ffd700',
      'Venus': '#e91e63',
      'Saturn': '#2196f3',
      'Rahu': '#9e9e9e',
      'Ketu': '#795548',
    };
    return colors[planetName] || '#ffffff';
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

  const spin = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const ChartIconSvg = ({ color = '#9c27b0', size = 32 }) => (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Rect x="2" y="2" width="44" height="44" fill="none" stroke={color} strokeWidth="2" />
      <Polygon points="24,2 46,24 24,46 2,24" fill="none" stroke={color} strokeWidth="1.5" opacity={0.9} />
      <Line x1="2" y1="2" x2="46" y2="46" stroke={color} strokeWidth="1" opacity={0.7} />
      <Line x1="46" y1="2" x2="2" y2="46" stroke={color} strokeWidth="1" opacity={0.7} />
    </Svg>
  );

  const StatCard = ({ icon, iconElement, value, label, color, onPress }) => (
    <TouchableOpacity
      activeOpacity={0.85}
      onPress={onPress}
      disabled={!onPress}
      style={{ flex: 1 }}
    >
      <Animated.View style={[styles.statCard, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
        <LinearGradient
          colors={[color + '20', color + '10']}
          style={styles.statGradient}
        >
          {iconElement != null ? (
            <View style={styles.statIconWrap}>{iconElement}</View>
          ) : (
            <Text style={[styles.statIcon, { color }]}>{icon}</Text>
          )}
          <Text style={[styles.statValue, { color: colors.text }]}>{value}</Text>
          <Text style={[styles.statLabel, { color: colors.textSecondary }]}>{label}</Text>
        </LinearGradient>
      </Animated.View>
    </TouchableOpacity>
  );

  const ActionButton = ({ icon, label, onPress, color = COLORS.accent }) => (
    <TouchableOpacity style={styles.actionButton} onPress={onPress}>
      <LinearGradient
        colors={[color, color + 'dd']}
        style={styles.actionGradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View style={styles.actionContent}>
          <Ionicons name={icon} size={20} color={COLORS.white} />
          <Text style={styles.actionLabel}>{label}</Text>
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );

  const FamilyChartChip = ({ chart }) => {
    const relation = getRelationLabel(chart);
    return (
      <TouchableOpacity
        style={[
          styles.familyChip,
          {
            backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.78)',
            borderColor: theme === 'dark' ? 'rgba(255,255,255,0.16)' : 'rgba(249,115,22,0.24)',
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
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a0033" translucent={false} />
      <LinearGradient
        colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.primary] : [colors.gradientStart, colors.gradientStart, colors.gradientStart, colors.gradientStart]}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={colors.text} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]}>
              {t('profile.myProfile', 'My Profile')}
            </Text>
            <View style={styles.editButton} />
          </View>

          <GHScrollView 
            style={styles.scrollView}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
            <Animated.View style={[styles.profileHeader, { opacity: fadeAnim }]}>
              <View style={styles.avatarContainer}>
                <Animated.View style={[styles.zodiacRing, { transform: [{ rotate: spin }] }]}>
                  <LinearGradient
                    colors={['#ff6b35', '#ffd700', '#ff6b35']}
                    style={styles.ringGradient}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                  />
                </Animated.View>
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>
                    {chartData ? (() => {
                      const signIndex = chartData?.houses?.[0]?.sign || 0;
                      return getSignIcon(signIndex);
                    })() : (loadingChart ? '⏳' : getZodiacSign(birthData?.date))}
                  </Text>
                </View>
              </View>
              <Text style={[styles.userName, { color: colors.text }]}>
                {userData?.name || t('profile.user', 'User')}
              </Text>
              <Text style={[styles.userSubtitle, { color: colors.textSecondary }]}>
                {birthData?.date
                  ? formatBirthDateForDisplay(birthData.date, {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric',
                    })
                  : t('profile.birthDateNotSet', 'Birth date not set')}
              </Text>
              {birthData?.time && (
                <Text style={[styles.userSubtitle, { color: colors.textSecondary }]}>🕐 {birthData.time}</Text>
              )}
              {!birthData?.date && (
                <TouchableOpacity 
                  style={styles.connectChartButton}
                  onPress={() => navigation.navigate('SelectNative', { fromProfile: true })}
                >
                  <LinearGradient
                    colors={['#ff6b35', '#ff8c5a']}
                    style={styles.connectChartGradient}
                  >
                    <Text style={styles.connectChartText}>
                      {`📊 ${t('profile.connectChart', 'Connect Chart to Profile')}`}
                    </Text>
                  </LinearGradient>
                </TouchableOpacity>
              )}
              {birthData?.place && (
                <Text style={[styles.userLocation, { color: colors.textSecondary }]}>📍 {birthData.place}</Text>
              )}
            </Animated.View>

            <Animated.View style={[styles.creditsCard, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
              <LinearGradient
                colors={['#ff6b35', '#ff8c5a', '#ffab7a']}
                style={styles.creditsGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <View style={styles.creditsContent}>
                  <View>
                    <Text style={styles.creditsLabel}>
                      {t('profile.availableCredits', 'Available Credits')}
                    </Text>
                    <Text style={styles.creditsValue}>{credits}</Text>
                  </View>
                  <TouchableOpacity 
                    style={styles.addCreditsButton}
                    onPress={() => navigation.navigate('Credits')}
                  >
                    <Text style={styles.addCreditsText}>{t('profile.add', '+ Add')}</Text>
                  </TouchableOpacity>
                </View>
              </LinearGradient>
            </Animated.View>

            <View style={styles.statsGrid}>
              <StatCard
                icon="💬"
                value={stats.totalChats}
                label={t('profile.chats', 'Chats')}
                color="#4a90e2"
                onPress={() => navigation.navigate('ChatHistory')}
              />
              <StatCard
                iconElement={<ChartIconSvg color="#ffd700" size={32} />}
                value={stats.chartsViewed}
                label={t('profile.charts', 'Charts')}
                color="#9c27b0"
                onPress={() => navigation.navigate('SelectNative', { fromProfile: true })}
              />
              <StatCard
                icon="🎙️"
                value={stats.podcastsCount}
                label={t('profile.podcasts', 'Podcasts')}
                color="#ff6b35"
                onPress={() => navigation.navigate('PodcastHistory')}
              />
            </View>

            <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
              <View style={styles.familySectionHeader}>
                <Text style={[styles.sectionTitle, styles.familySectionTitle, { color: colors.text }]}>
                  {t('profile.familyCharts', 'Family Charts')}
                </Text>
                <TouchableOpacity
                  style={[
                    styles.familyAddButton,
                    { backgroundColor: theme === 'dark' ? 'rgba(255,107,53,0.18)' : 'rgba(249,115,22,0.12)' },
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
                      backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(249,115,22,0.08)',
                      borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)',
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
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                {`✨ ${t('profile.birthChartEssence', 'Birth Chart Essence')}`}
              </Text>
              <View style={styles.chartSummaryCard}>
                <LinearGradient
                  colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.15)', 'rgba(249, 115, 22, 0.08)']}
                  style={styles.chartSummaryGradient}
                >
                  <TouchableOpacity 
                    style={styles.miniChart}
                    onPress={() => {
                      if (birthData) {
                        navigation.navigate('Chart', { birthData });
                      } else {
                        navigation.navigate('Home');
                      }
                    }}
                  >
                    <Svg width="48" height="48" viewBox="0 0 48 48" style={{ marginBottom: 8 }}>
                      {/* Outer square */}
                      <Rect x="2" y="2" width="44" height="44" fill="none" stroke="#ff6b35" strokeWidth="2" />
                      {/* Inner diamond */}
                      <Polygon points="24,2 46,24 24,46 2,24" fill="none" stroke="#ffd700" strokeWidth="1.5" />
                      {/* Diagonal lines creating triangular houses */}
                      <Line x1="2" y1="2" x2="46" y2="46" stroke="#ff8a65" strokeWidth="1" />
                      <Line x1="46" y1="2" x2="2" y2="46" stroke="#ff8a65" strokeWidth="1" />
                    </Svg>
                    <Text style={[styles.miniChartText, { color: colors.text }]}>
                      {t('profile.viewFullChart', 'View Full Chart')}
                    </Text>
                  </TouchableOpacity>
                  
                  <View style={styles.chartDetails}>
                    <View style={styles.chartDetailRow}>
                      <Text style={[styles.chartDetailLabel, { color: colors.textSecondary }]}>
                        {`☀️ ${t('profile.sunSign', 'Sun Sign')}`}
                      </Text>
                      <Text style={[styles.chartDetailValue, { color: colors.text }]}>
                        {loadingChart
                          ? t('profile.calculating', 'Calculating...')
                          : `${getSignIcon(chartData?.planets?.Sun?.sign)} ${getSignName(chartData?.planets?.Sun?.sign)}`}
                      </Text>
                    </View>
                    <View style={styles.chartDetailRow}>
                      <Text style={[styles.chartDetailLabel, { color: colors.textSecondary }]}>
                        {`🌙 ${t('profile.moonSign', 'Moon Sign')}`}
                      </Text>
                      <Text style={[styles.chartDetailValue, { color: colors.text }]}>
                        {loadingChart
                          ? t('profile.calculating', 'Calculating...')
                          : `${getSignIcon(chartData?.planets?.Moon?.sign)} ${getSignName(chartData?.planets?.Moon?.sign)}`}
                      </Text>
                    </View>
                    <View style={styles.chartDetailRow}>
                      <Text style={[styles.chartDetailLabel, { color: colors.textSecondary }]}>
                        {`⬆️ ${t('profile.ascendant', 'Ascendant')}`}
                      </Text>
                      <Text style={[styles.chartDetailValue, { color: colors.text }]}>
                        {loadingChart
                          ? t('profile.calculating', 'Calculating...')
                          : `${getSignIcon(chartData?.houses?.[0]?.sign)} ${getSignName(chartData?.houses?.[0]?.sign)}`}
                      </Text>
                    </View>
                  </View>
                  
                  {/* Current Running Dashas */}
                  <View style={[styles.dashasContainer, { borderTopColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)' }]}>
                    <Text style={[styles.dashasTitle, { color: colors.textSecondary }]}>
                      {t('profile.currentRunningDashas', 'Current Running Dashas')}
                    </Text>
                    <View style={styles.dashasRow}>
                      {loadingDashas ? (
                        <Text style={styles.dashasLoading}>
                          {t('profile.loading', 'Loading...')}
                        </Text>
                      ) : (
                        [
                          { level: 'Maha', data: dashaData?.maha_dashas?.find(d => d.current) },
                          { level: 'Antar', data: dashaData?.antar_dashas?.find(d => d.current) },
                          { level: 'Pratyantar', data: dashaData?.pratyantar_dashas?.find(d => d.current) },
                          { level: 'Sookshma', data: dashaData?.sookshma_dashas?.find(d => d.current) },
                          { level: 'Prana', data: dashaData?.prana_dashas?.find(d => d.current) }
                        ].map((dasha, index) => {
                          const planetColor = getPlanetColor(dasha.data?.planet);
                          return (
                            <View key={index} style={[styles.dashaChip, { borderColor: planetColor, backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)' }]}>
                              <Text style={[styles.dashaLevel, { color: colors.textSecondary }]}>
                                {t(`profile.dashaLevels.${dasha.level}`, dasha.level)}
                              </Text>
                              <Text style={[styles.dashaPlanet, { color: planetColor }]}>
                                {getDashaPlanetLabel(dasha.data?.planet)}
                              </Text>
                            </View>
                          );
                        })
                      )}
                    </View>
                  </View>
                </LinearGradient>
              </View>
            </Animated.View>

            <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                {`⚡ ${t('profile.quickActionsTitle', 'Quick Actions')}`}
              </Text>
              <View style={styles.actionsGrid}>
                <ActionButton 
                  icon="chatbubbles" 
                  label={t('profile.quickActions.newChat')} 
                  onPress={() => navigation.navigate('Home', { startChat: true })}
                  color="#4a90e2"
                />
                <ActionButton 
                  icon="pie-chart" 
                  label={t('profile.quickActions.viewChart')} 
                  onPress={() => {
                    if (birthData) {
                      navigation.navigate('Chart', { birthData });
                    } else {
                      navigation.navigate('Home');
                    }
                  }}
                  color="#9c27b0"
                />
                <ActionButton 
                  icon="time" 
                  label={t('profile.quickActions.dashas')} 
                  onPress={() => {
                    if (birthData) {
                      setShowDashaBrowser(true);
                    } else {
                      // Show message that birth data is needed
                      Alert.alert(
                        t('profile.birthDataRequired', 'Birth Data Required'),
                        t('profile.dashasAlert', 'Please connect your birth chart to view dashas.')
                      );
                    }
                  }}
                  color="#ff6b35"
                />
                <ActionButton 
                  icon="calendar" 
                  label={t('profile.quickActions.history')} 
                  onPress={() => navigation.navigate('ChatHistory')}
                  color="#4caf50"
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
                  color="#e91e63"
                />
                <ActionButton 
                  icon="language" 
                  label={t('profile.quickActions.language')} 
                  onPress={() => setShowLanguageModal(true)}
                  color="#2196f3"
                />
              </View>
            </Animated.View>

            <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                {`⚙️ ${t('profile.settings', 'Settings')}`}
              </Text>
              <View style={[styles.settingsCard, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.03)' }]}>
                <TouchableOpacity
                  style={styles.settingItem}
                  onPress={() => navigation.navigate('AccountSecurity')}
                >
                  <View style={styles.settingLeft}>
                    <Ionicons name="shield-checkmark-outline" size={22} color="#22c55e" />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {t('profile.accountAndSecurity', 'Account & security')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>

                <View style={[styles.settingDivider, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)' }]} />

                <TouchableOpacity style={styles.settingItem} onPress={toggleTheme}>
                  <View style={styles.settingLeft}>
                    <Ionicons name={theme === 'dark' ? 'sunny-outline' : 'moon-outline'} size={22} color="#ffd700" />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {theme === 'dark' ? t('profile.darkTheme', 'Light Theme') : t('profile.lightTheme', 'Dark Theme')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>
                
                <View style={[styles.settingDivider, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)' }]} />

                <TouchableOpacity
                  style={styles.settingItem}
                  onPress={() => navigation.navigate('NudgeInbox')}
                >
                  <View style={styles.settingLeft}>
                    <Ionicons name="mail-unread-outline" size={22} color="#ff6b35" />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {t('profile.notificationHistory', 'Notification history')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>

                <View style={[styles.settingDivider, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)' }]} />

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
                    <Ionicons name="notifications-outline" size={22} color="#ff6b35" />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {pushSyncing
                        ? t('profile.turningOnNotifications', 'Turning on…')
                        : t('profile.turnOnNotifications', 'Turn ON Notifications')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>
                
                <View style={[styles.settingDivider, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)' }]} />
                
                <TouchableOpacity style={styles.settingItem} onPress={() => navigation.navigate('SelectNative', { returnTo: 'Profile' })}>
                  <View style={styles.settingLeft}>
                    <Ionicons name="people-outline" size={22} color="#9c27b0" />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {t('profile.familyCharts', 'Family Charts')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>

                <View style={[styles.settingDivider, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)' }]} />

                <TouchableOpacity style={styles.settingItem} onPress={() => navigation.navigate('BirthForm', { editProfile: birthData })}>
                  <View style={styles.settingLeft}>
                    <Ionicons name="person-outline" size={22} color="#ff6b35" />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {t('profile.editBirthDetails', 'Edit Birth Details')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>

                <View style={[styles.settingDivider, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)' }]} />

                <TouchableOpacity style={styles.settingItem} onPress={() => navigation.navigate('About')}>
                  <View style={styles.settingLeft}>
                    <Ionicons name="information-circle-outline" size={22} color="#3b82f6" />
                    <Text style={[styles.settingText, { color: colors.text }]}>
                      {t('profile.aboutApp', 'About AstroRoshni')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </TouchableOpacity>
              </View>
            </Animated.View>

            <TouchableOpacity 
              style={[styles.logoutButton, { backgroundColor: theme === 'dark' ? 'rgba(255, 107, 53, 0.2)' : 'rgba(255, 107, 53, 0.15)', borderColor: theme === 'dark' ? 'rgba(255, 107, 53, 0.5)' : 'rgba(255, 107, 53, 0.4)' }]}
              onPress={async () => {
                await storage.clearAll();
                const { replaceWithLogin } = require('../../navigation/replaceWithLogin');
                replaceWithLogin(navigation);
              }}
            >
              <Text
                style={[
                  styles.logoutText,
                  { color: theme === 'dark' ? '#ffffff' : colors.primary },
                ]}
              >
                {`🚪 ${t('profile.logout', 'Logout')}`}
              </Text>
            </TouchableOpacity>

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
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>🌐 {t('languageModal.title')}</Text>
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
                    language === lang.code && styles.languageOptionSelected
                  ]}
                  onPress={() => handleLanguageChange(lang.code)}
                >
                  <Text style={styles.languageText}>
                    {lang.flag} {lang.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </RNScrollView>
            <TouchableOpacity
              style={styles.modalCloseButton}
              onPress={() => setShowLanguageModal(false)}
            >
              <Text style={styles.modalCloseText}>{t('languageModal.close')}</Text>
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
        <View style={styles.chartModalOverlay}>
          <View
            style={[
              styles.chartModalContent,
              {
                backgroundColor: theme === 'dark' ? 'rgba(31,21,45,0.98)' : 'rgba(255,255,255,0.98)',
                borderColor: theme === 'dark' ? 'rgba(255,255,255,0.14)' : 'rgba(249,115,22,0.22)',
              },
            ]}
          >
            <View style={styles.chartModalHeader}>
              <View style={[styles.chartModalIcon, { backgroundColor: theme === 'dark' ? 'rgba(255,107,53,0.18)' : 'rgba(249,115,22,0.12)' }]}>
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
                  navigation.navigate('Chart', { birthData: chart });
                }}
              >
                <Ionicons name="analytics-outline" size={18} color={COLORS.white} />
                <Text style={styles.chartModalActionText}>{t('profile.viewChart', 'View Chart')}</Text>
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
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 16 },
  backButton: { width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(255, 255, 255, 0.1)', alignItems: 'center', justifyContent: 'center' },
  headerTitle: { fontSize: 20, fontWeight: '700' },
  editButton: { width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(255, 255, 255, 0.1)', alignItems: 'center', justifyContent: 'center' },
  scrollView: { flex: 1 },
  scrollContent: { paddingHorizontal: 20, paddingBottom: 40 },
  profileHeader: { alignItems: 'center', marginTop: 20, marginBottom: 30 },
  avatarContainer: { position: 'relative', marginBottom: 16 },
  zodiacRing: { position: 'absolute', width: 120, height: 120, borderRadius: 60, top: -10, left: -10 },
  ringGradient: { width: '100%', height: '100%', borderRadius: 60, opacity: 0.3 },
  avatar: { width: 100, height: 100, borderRadius: 50, backgroundColor: 'rgba(255, 255, 255, 0.15)', alignItems: 'center', justifyContent: 'center', borderWidth: 3, borderColor: 'rgba(255, 255, 255, 0.3)' },
  avatarText: { fontSize: 48 },
  userName: { fontSize: 28, fontWeight: '700', marginBottom: 4 },
  userSubtitle: { fontSize: 14, marginBottom: 4 },
  userLocation: { fontSize: 13 },
  creditsCard: { marginBottom: 24, borderRadius: 20, overflow: 'hidden', shadowColor: '#ff6b35', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.3, shadowRadius: 12, elevation: 8 },
  creditsGradient: { padding: 24 },
  creditsContent: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  creditsLabel: { fontSize: 14, color: 'rgba(255, 255, 255, 0.9)', marginBottom: 4 },
  creditsValue: { fontSize: 36, fontWeight: '700', color: COLORS.white },
  addCreditsButton: { backgroundColor: 'rgba(255, 255, 255, 0.25)', paddingHorizontal: 20, paddingVertical: 12, borderRadius: 20, borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.3)' },
  addCreditsText: { color: COLORS.white, fontSize: 16, fontWeight: '700' },
  statsGrid: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 24, gap: 12 },
  statCard: { flex: 1, borderRadius: 16, overflow: 'hidden' },
  statGradient: { padding: 16, alignItems: 'center' },
  statIcon: { fontSize: 32, marginBottom: 8 },
  statIconWrap: { marginBottom: 8, alignItems: 'center', justifyContent: 'center' },
  statValue: { fontSize: 24, fontWeight: '700', color: COLORS.white, marginBottom: 4 },
  statLabel: { fontSize: 12, color: 'rgba(255, 255, 255, 0.8)' },
  section: { marginBottom: 24 },
  sectionTitle: { fontSize: 18, fontWeight: '700', marginBottom: 12 },
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
  chartSummaryCard: { borderRadius: 16, overflow: 'hidden' },
  chartSummaryGradient: { padding: 20 },
  miniChart: { alignItems: 'center', marginBottom: 20, paddingVertical: 20, borderRadius: 12, backgroundColor: 'rgba(255, 255, 255, 0.05)' },
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
  actionsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  actionButton: { width: (width - 52) / 2, borderRadius: 16, overflow: 'hidden', shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 5 },
  actionGradient: { padding: 12, justifyContent: 'center' },
  actionContent: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  actionLabel: { color: COLORS.white, fontSize: 13, fontWeight: '600' },
  settingsCard: { borderRadius: 16, padding: 4 },
  settingItem: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16 },
  settingLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  settingText: { fontSize: 16, fontWeight: '500' },
  settingValue: { fontSize: 14, color: 'rgba(255, 255, 255, 0.6)' },
  settingDivider: { height: 1, backgroundColor: 'rgba(255, 255, 255, 0.1)', marginHorizontal: 16 },
  logoutButton: { backgroundColor: 'rgba(255, 107, 53, 0.2)', borderWidth: 1, borderColor: 'rgba(255, 107, 53, 0.5)', borderRadius: 16, padding: 16, alignItems: 'center', marginTop: 12 },
  logoutText: { fontSize: 16, fontWeight: '700' },
  bottomSpacer: { height: 20 },
  connectChartButton: {
    marginTop: 12,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
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
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 24,
    padding: 24,
    width: '88%',
    maxHeight: '75%',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.accent,
    textAlign: 'center',
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
    backgroundColor: COLORS.lightGray,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  languageOptionSelected: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    borderColor: COLORS.accent,
  },
  languageText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.black,
  },
  modalCloseButton: {
    backgroundColor: COLORS.accent,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 16,
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  modalCloseText: {
    color: COLORS.white,
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
