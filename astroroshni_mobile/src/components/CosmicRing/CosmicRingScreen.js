import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  useWindowDimensions,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Circle, Path } from 'react-native-svg';
import Icon from '@expo/vector-icons/Ionicons';
import { useFocusEffect } from '@react-navigation/native';
import { GestureHandlerRootView, PinchGestureHandler, PanGestureHandler, State } from 'react-native-gesture-handler';
import { useTheme } from '../../context/ThemeContext';
import CosmicRingSvg from './CosmicRingSvg';
import DateNavigator from '../Common/DateNavigator';
import { chartAPI } from '../../services/api';
import { storage } from '../../services/storage';

/** Deterministic star positions for full-screen background (x,y in 0..100, r, opacity) */
function getScreenStarPoints() {
  const points = [];
  for (let i = 0; i < 72; i++) {
    const x = ((i * 47 + 13) % 97) + 1.5;
    const y = ((i * 73 + 31) % 98) + 1;
    const r = 0.15 + ((i * 11) % 5) / 15;
    const opacity = 0.2 + ((i * 17) % 12) / 25;
    points.push({ x, y, r, opacity });
  }
  return points;
}

const SCREEN_STAR_POINTS = getScreenStarPoints();

function StarfieldBackground({ theme }) {
  const starFill = theme === 'dark' ? '#fef9c3' : '#fef08a';
  const sparkleStroke = theme === 'dark' ? 'rgba(254,249,195,0.75)' : 'rgba(254,240,138,0.7)';
  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      <Svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid slice">
        {SCREEN_STAR_POINTS.map((s, i) => (
          <Circle key={`bg-star-${i}`} cx={s.x} cy={s.y} r={s.r} fill={starFill} opacity={s.opacity} />
        ))}
        {[
          { x: 8, y: 15 }, { x: 92, y: 22 }, { x: 15, y: 88 }, { x: 88, y: 82 }, { x: 50, y: 12 }, { x: 25, y: 45 }, { x: 78, y: 55 },
        ].map((p, i) => (
          <Path
            key={`bg-sparkle-${i}`}
            d={`M ${p.x} ${p.y - 0.8} L ${p.x} ${p.y + 0.8} M ${p.x - 0.8} ${p.y} L ${p.x + 0.8} ${p.y} M ${p.x - 0.35} ${p.y - 0.35} L ${p.x + 0.35} ${p.y + 0.35} M ${p.x + 0.35} ${p.y - 0.35} L ${p.x - 0.35} ${p.y + 0.35}`}
            fill="none"
            stroke={sparkleStroke}
            strokeWidth={0.2}
            opacity={0.8}
          />
        ))}
      </Svg>
    </View>
  );
}

const MIN_SCALE = 0.5;
const MAX_SCALE = 4;
const RING_LEFT_OFFSET = -20;

const PLANET_ORDER = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];

const PLANET_COLORS = {
  Sun: '#fbbf24',
  Moon: '#f8fafc',
  Mars: '#ef4444',
  Mercury: '#34d399',
  Jupiter: '#fcd34d',
  Venus: '#c084fc',
  Saturn: '#60a5fa',
  Rahu: '#a78bfa',
  Ketu: '#fb923c',
};

function formatDateLabel(isoDate) {
  if (!isoDate || typeof isoDate !== 'string') return '—';
  const [y, m, d] = isoDate.split('T')[0].split('-').map(Number);
  if (!y || !m || !d) return isoDate;
  const months = 'JAN,FEB,MAR,APR,MAY,JUN,JUL,AUG,SEP,OCT,NOV,DEC'.split(',');
  return `${months[m - 1]} ${d}, ${y}`;
}

function planetsFromChart(planetsObj) {
  if (!planetsObj || typeof planetsObj !== 'object') return [];
  return PLANET_ORDER.filter((name) => planetsObj[name]).map((name) => {
    const p = planetsObj[name];
    const sign = p.sign != null ? parseInt(p.sign, 10) : 0;
    const degree = p.degree != null ? parseFloat(p.degree) : p.longitude != null ? parseFloat(p.longitude) % 30 : 0;
    return {
      name,
      sign: isNaN(sign) ? 0 : sign,
      degree: isNaN(degree) ? 0 : degree,
      isRetrograde: p.retrograde === true || p.is_retrograde === true,
    };
  });
}

export default function CosmicRingScreen({ navigation }) {
  const { theme, colors } = useTheme();
  const { width: winWidth } = useWindowDimensions();
  const size = winWidth + 40;

  const scaleAnim = useRef(new Animated.Value(1)).current;
  const translateXAnim = useRef(new Animated.Value(RING_LEFT_OFFSET)).current;
  const translateYAnim = useRef(new Animated.Value(0)).current;
  const scaleOffset = useRef(1);
  const translateXOffset = useRef(RING_LEFT_OFFSET);
  const translateYOffset = useRef(0);

  const onPinchStateChange = useCallback((e) => {
    if (e.nativeEvent.oldState === State.ACTIVE) {
      let s = scaleOffset.current * e.nativeEvent.scale;
      s = Math.min(MAX_SCALE, Math.max(MIN_SCALE, s));
      scaleOffset.current = s;
      scaleAnim.setValue(s);
    }
  }, [scaleAnim]);

  const onPinchEvent = useCallback((e) => {
    const s = e.nativeEvent.scale;
    let v = scaleOffset.current * s;
    v = Math.min(MAX_SCALE, Math.max(MIN_SCALE, v));
    scaleAnim.setValue(v);
  }, [scaleAnim]);

  const onPanStateChange = useCallback((e) => {
    if (e.nativeEvent.oldState === State.ACTIVE) {
      translateXOffset.current += e.nativeEvent.translationX;
      translateYOffset.current += e.nativeEvent.translationY;
      translateXAnim.setValue(translateXOffset.current);
      translateYAnim.setValue(translateYOffset.current);
    }
  }, [translateXAnim, translateYAnim]);

  const onPanEvent = useCallback((e) => {
    translateXAnim.setValue(translateXOffset.current + e.nativeEvent.translationX);
    translateYAnim.setValue(translateYOffset.current + e.nativeEvent.translationY);
  }, [translateXAnim, translateYAnim]);

  const resetZoomPan = useCallback(() => {
    scaleOffset.current = 1;
    translateXOffset.current = RING_LEFT_OFFSET;
    translateYOffset.current = 0;
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true }),
      Animated.spring(translateXAnim, { toValue: RING_LEFT_OFFSET, useNativeDriver: true }),
      Animated.spring(translateYAnim, { toValue: 0, useNativeDriver: true }),
    ]).start();
  }, [scaleAnim, translateXAnim, translateYAnim]);

  const [activeTab, setActiveTab] = useState('today'); // 'birth' | 'today'
  const [birthChart, setBirthChart] = useState(null);
  const [birthDateIso, setBirthDateIso] = useState(null);
  const [formattedBirthData, setFormattedBirthData] = useState(null);
  const [transitDate, setTransitDate] = useState(() => new Date());
  const [transitData, setTransitData] = useState(null);
  const [transitLoading, setTransitLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let birth = await storage.getBirthDetails();
      if (!birth) {
        const profiles = await storage.getBirthProfiles();
        if (profiles?.length) birth = profiles.find((p) => p.relation === 'self') || profiles[0];
      }
      if (!birth?.date || !birth?.name) {
        navigation.replace('BirthProfileIntro', { returnTo: 'CosmicRing' });
        return;
      }
      const formatted = {
        name: birth.name || 'Unknown',
        date: (birth.date && birth.date.includes?.('T')) ? birth.date.split('T')[0] : (birth.date || ''),
        time: (birth.time && birth.time.includes?.('T')) ? new Date(birth.time).toTimeString().slice(0, 5) : (birth.time || ''),
        latitude: parseFloat(birth.latitude) || 0,
        longitude: parseFloat(birth.longitude) || 0,
        location: birth.place || 'Unknown',
      };
      setBirthDateIso(formatted.date);
      setFormattedBirthData(formatted);
      const chartRes = await chartAPI.calculateChartOnly(formatted).then((r) => r?.data).catch(() => null);
      if (chartRes) {
        setBirthChart(chartRes);
      } else {
        setBirthChart(null);
      }
    } catch (e) {
      setError(e?.message || 'Failed to load data');
      setBirthChart(null);
      setFormattedBirthData(null);
      setTransitData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!formattedBirthData) return;
    const iso = transitDate.toISOString().split('T')[0];
    let cancelled = false;
    setTransitLoading(true);
    chartAPI
      .calculateTransits(formattedBirthData, iso)
      .then((res) => {
        if (!cancelled && res?.data) setTransitData(res.data);
        else if (!cancelled) setTransitData(null);
      })
      .catch(() => {
        if (!cancelled) setTransitData(null);
      })
      .finally(() => {
        if (!cancelled) setTransitLoading(false);
      });
    return () => { cancelled = true; };
  }, [formattedBirthData, transitDate]);

  useFocusEffect(
    useCallback(() => {
      loadData();
    }, [loadData])
  );

  const birthPlanets = birthChart ? planetsFromChart(birthChart.planets) : [];
  const todayPlanets = transitData?.planets ? planetsFromChart(transitData.planets) : [];
  const birthDateLabel = birthChart ? formatDateLabel(birthChart.birth_date || birthChart.date || birthDateIso) : (birthDateIso ? formatDateLabel(birthDateIso) : '—');
  const todayDateLabel = formatDateLabel(transitDate.toISOString());

  const isDark = theme === 'dark';

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top']}>
      <View style={styles.screenWrapper}>
        <StarfieldBackground theme={theme} />
        <View style={[styles.header, { borderBottomColor: colors.cardBorder || 'rgba(255,255,255,0.1)' }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
          <Icon name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: colors.text }]}>Cosmic Ring</Text>
        <View style={styles.backBtn} />
      </View>
      <View style={[styles.tabs, isDark ? styles.tabsDark : styles.tabsLight]}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'birth' && (isDark ? styles.tabActiveDark : styles.tabActiveLight)]}
          onPress={() => setActiveTab('birth')}
        >
          <Text style={[styles.tabText, { color: activeTab === 'birth' ? colors.primary : colors.textSecondary }]}>
            Birth
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'today' && (isDark ? styles.tabActiveDark : styles.tabActiveLight)]}
          onPress={() => setActiveTab('today')}
        >
          <Text style={[styles.tabText, { color: activeTab === 'today' ? colors.primary : colors.textSecondary }]}>
            Today
          </Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>Loading positions…</Text>
        </View>
      ) : error ? (
        <View style={styles.centered}>
          <Text style={[styles.errorText, { color: colors.error }]}>{error}</Text>
        </View>
      ) : activeTab === 'birth' && !birthChart ? (
        <View style={styles.centered}>
          <Text style={[styles.hint, { color: colors.textSecondary }]}>No birth chart. Add birth details first.</Text>
        </View>
      ) : (
        <View style={styles.ringContainer}>
          {activeTab === 'today' && (
            <>
              <DateNavigator
                date={transitDate}
                onDateChange={setTransitDate}
                cosmicTheme={isDark}
                resetDate={new Date()}
              />
              {transitLoading && (
                <View style={styles.transitLoadingRow}>
                  <ActivityIndicator size="small" color={colors.primary} />
                  <Text style={[styles.transitLoadingText, { color: colors.textSecondary }]}>Loading transits…</Text>
                </View>
              )}
            </>
          )}
          <GestureHandlerRootView style={styles.gestureRoot}>
            <PinchGestureHandler
              onGestureEvent={onPinchEvent}
              onHandlerStateChange={onPinchStateChange}
            >
              <PanGestureHandler
                onGestureEvent={onPanEvent}
                onHandlerStateChange={onPanStateChange}
                minPointers={1}
              >
                <Animated.View
                  style={[
                    styles.ringWrapper,
                    {
                      transform: [
                        { scale: scaleAnim },
                        { translateX: translateXAnim },
                        { translateY: translateYAnim },
                      ],
                    },
                  ]}
                >
                  <CosmicRingSvg
                    theme={theme}
                    dateLabel={activeTab === 'birth' ? birthDateLabel : todayDateLabel}
                    subLabel="SIDEREAL LAHIRI"
                    planets={activeTab === 'birth' ? birthPlanets : todayPlanets}
                    planetColors={PLANET_COLORS}
                    width={size}
                    height={size}
                  />
                </Animated.View>
              </PanGestureHandler>
            </PinchGestureHandler>
          </GestureHandlerRootView>
          <TouchableOpacity
            style={[styles.resetButton, isDark ? styles.resetButtonDark : styles.resetButtonLight]}
            onPress={resetZoomPan}
            activeOpacity={0.8}
          >
            <Icon name="scan-outline" size={20} color={colors.text} />
            <Text style={[styles.resetButtonText, { color: colors.text }]}>Reset</Text>
          </TouchableOpacity>
        </View>
      )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  screenWrapper: {
    flex: 1,
    position: 'relative',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  backBtn: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  tabs: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  tabsDark: {
    backgroundColor: 'rgba(255,255,255,0.05)',
  },
  tabsLight: {
    backgroundColor: 'rgba(0,0,0,0.04)',
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  tabActiveDark: {
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  tabActiveLight: {
    backgroundColor: 'rgba(249, 115, 22, 0.15)',
  },
  tabText: {
    fontSize: 15,
    fontWeight: '600',
  },
  ringContainer: {
    flex: 1,
    overflow: 'hidden',
    width: '100%',
  },
  transitLoadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 6,
  },
  transitLoadingText: {
    fontSize: 13,
  },
  gestureRoot: {
    flex: 1,
    width: '100%',
    alignItems: 'flex-start',
    justifyContent: 'center',
  },
  ringWrapper: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  resetButton: {
    position: 'absolute',
    bottom: 24,
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 20,
  },
  resetButtonDark: {
    backgroundColor: 'rgba(255,255,255,0.12)',
  },
  resetButtonLight: {
    backgroundColor: 'rgba(0,0,0,0.08)',
  },
  resetButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  hint: {
    fontSize: 14,
    textAlign: 'center',
  },
});
