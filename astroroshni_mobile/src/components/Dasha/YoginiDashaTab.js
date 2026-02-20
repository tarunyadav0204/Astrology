import React, { useState, useMemo, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';

const { width } = Dimensions.get('window');

// --- CONSTANTS & HELPERS ---

const formatDate = (dateString) => {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
  } catch {
    return '';
  }
};

// --- SUB-COMPONENTS ---

const DashaProgress = ({ percentage = 0, t, trackBg, fillColors, progressTextColor }) => (
  <View style={[styles.progressContainer, trackBg && { backgroundColor: trackBg }]}>
    <View style={[styles.track, trackBg && { backgroundColor: trackBg }]} />
    <LinearGradient
      colors={fillColors || ['#8E2DE2', '#4A00E0']}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 0 }}
      style={[styles.fill, { width: `${percentage}%` }]}
    />
    <Text style={[styles.progressText, progressTextColor && { color: progressTextColor }]}>{t('dasha.percentCompleted', '{{percentage}}% Completed', { percentage: Math.round(percentage) })}</Text>
  </View>
);

const YoginiCard = ({ item, isCurrent, isExpanded, onPress, t, tYogini, YOGINI_CONFIG, colors, isDark }) => {
  const config = YOGINI_CONFIG[item.name] || YOGINI_CONFIG['Mangala'];
  const cardBg = isDark ? colors.surface : colors.cardBackground;
  const listBg = isDark ? colors.background : colors.surface;
  const cardBorder = isCurrent ? colors.primary : colors.cardBorder;
  const accent = colors.primary;

  return (
    <View>
      <TouchableOpacity 
        style={[styles.card, { backgroundColor: cardBg, borderColor: cardBorder }, isCurrent && { borderColor: accent, borderWidth: 1.5 }]} 
        onPress={onPress}
        activeOpacity={0.9}
      >
        <LinearGradient
          colors={config.color}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.cardHeader}
        />

        <View style={styles.cardContent}>
          <View style={styles.cardLeft}>
            <View style={[styles.iconBox, { backgroundColor: config.color[0] + '20' }]}>
              <Ionicons name={config.icon} size={24} color={config.color[0]} />
            </View>
            <View>
              <Text style={[styles.yoginiName, { color: colors.text }]}>{tYogini(item.name)}</Text>
              <Text style={[styles.yoginiLord, { color: colors.textSecondary }]}>{item.lord}</Text>
            </View>
          </View>

          <View style={styles.cardRight}>
            <View style={[styles.vibeBadge, { backgroundColor: config.color[0] + '15' }]}>
              <Text style={[styles.vibeText, { color: config.color[0] }]}>{config.label}</Text>
            </View>
            <Text style={[styles.dateText, { color: colors.textSecondary }]}>
              {formatDate(item.start)} - {formatDate(item.end)}
            </Text>
          </View>
        </View>

        {isCurrent && (
          <View style={[styles.currentIndicator, { backgroundColor: isDark ? colors.background : '#f8f0ff', borderTopColor: colors.cardBorder }]}>
            <Text style={[styles.currentText, { color: accent }]}>{t('dasha.currentlyRunning', 'Currently Running')}</Text>
          </View>
        )}
      </TouchableOpacity>

      {isExpanded && item.sub_periods && (
        <View style={[styles.subList, { backgroundColor: listBg }]}>
          {item.sub_periods.map((sub, idx) => {
            const now = new Date();
            const subStart = new Date(sub.start);
            const subEnd = new Date(sub.end);
            const isCurrentAntar = now >= subStart && now <= subEnd;
            return (
              <View
                key={idx}
                style={[
                  styles.subItem,
                  isCurrentAntar && styles.currentSubItem,
                  isCurrentAntar && { backgroundColor: isDark ? colors.surface : '#f8f0ff', borderColor: accent },
                ]}
              >
                <View style={[styles.subTimelineLine, { backgroundColor: colors.cardBorder }]} />
                <View style={[styles.subDot, { backgroundColor: YOGINI_CONFIG[sub.name]?.color[0] || '#ccc', borderColor: listBg }]} />
                <View style={styles.subContent}>
                  <Text style={[styles.subName, { color: colors.text }, isCurrentAntar && { color: accent, fontWeight: '700' }]}>{tYogini(sub.name)} ({sub.lord})</Text>
                  <Text style={[styles.subDates, { color: colors.textSecondary }, isCurrentAntar && { color: accent, fontWeight: '600' }]}>{formatDate(sub.start)} - {formatDate(sub.end)}</Text>
                </View>
                <Text style={[styles.subVibe, { color: YOGINI_CONFIG[sub.name]?.color[0] || colors.textSecondary }, isCurrentAntar && styles.currentSubVibe]}>
                  {YOGINI_CONFIG[sub.name]?.label}
                </Text>
                {isCurrentAntar && (
                  <View style={[styles.currentAntarIndicator, { backgroundColor: accent }]}>
                    <Text style={styles.currentAntarText}>{t('common.current', 'Current')}</Text>
                  </View>
                )}
              </View>
            );
          })}
        </View>
      )}
    </View>
  );
};

// --- MAIN COMPONENT ---

export default function YoginiDashaTab({ data }) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';

  const YOGINI_CONFIG = {
    Mangala: { color: ['#11998e', '#38ef7d'], icon: 'moon', label: t('yogini.success', 'Success') },
    Pingala: { color: ['#ff9966', '#ff5e62'], icon: 'sunny', label: t('yogini.aggression', 'Aggression') },
    Dhanya:  { color: ['#f2994a', '#f2c94c'], icon: 'wallet', label: t('yogini.wealth', 'Wealth') },
    Bhramari:{ color: ['#cb2d3e', '#ef473a'], icon: 'airplane', label: t('yogini.travel', 'Travel') },
    Bhadrika:{ color: ['#56ab2f', '#a8e063'], icon: 'people', label: t('yogini.career', 'Career') },
    Ulka:    { color: ['#2980b9', '#6dd5fa'], icon: 'thunderstorm', label: t('yogini.workload', 'Workload') },
    Siddha:  { color: ['#8E2DE2', '#4A00E0'], icon: 'star', label: t('yogini.victory', 'Victory') },
    Sankata: { color: ['#833ab4', '#fd1d1d'], icon: 'alert-circle', label: t('yogini.crisis', 'Crisis') },
  };

  const tYogini = (name) => {
    if (!name) return '';
    return t(`yogini.${name.toLowerCase()}`, name);
  };
  
  // Find current period index (safe with optional chaining)
  const currentIndex = useMemo(() => {
    if (!data?.timeline || !Array.isArray(data.timeline)) {
      console.log('No timeline in data:', data);
      return -1;
    }
    return data.timeline.findIndex(item => 
      item.name === data?.current?.mahadasha?.name && 
      item.start === data?.current?.mahadasha?.start && 
      item.end === data?.current?.mahadasha?.end
    );
  }, [data]);
  
  const [expandedId, setExpandedId] = useState(null);
  
  // Auto-expand current period on mount
  useEffect(() => {
    if (currentIndex >= 0 && expandedId === null) {
      console.log('Setting expandedId to:', currentIndex);
      console.log('Current period has sub_periods:', !!data?.timeline?.[currentIndex]?.sub_periods);
      setExpandedId(currentIndex);
    }
  }, [currentIndex, data, expandedId]);

  if (!data) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('dasha.loadingYogini', 'Loading Yogini Dasha data...')}</Text>
      </View>
    );
  }

  if (!data?.timeline || !Array.isArray(data.timeline) || !data?.current) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('dasha.dataStructureError', 'Data structure error. Check console for details.')}</Text>
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('dasha.availableKeys', 'Available keys: ')} {Object.keys(data || {}).join(', ')}</Text>
      </View>
    );
  }

  const handlePress = (name) => {
    setExpandedId(expandedId === name ? null : name);
  };

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]} contentContainerStyle={{ paddingBottom: 40 }} showsVerticalScrollIndicator={false}>
      <View style={styles.heroContainer}>
        <LinearGradient
          colors={isDark ? [colors.surface, colors.background] : [colors.cardBackground, colors.backgroundSecondary]}
          style={[styles.heroCard, { backgroundColor: isDark ? colors.surface : colors.cardBackground, borderColor: colors.cardBorder }]}
        >
          <View style={styles.heroHeader}>
            <Text style={[styles.heroTitle, { color: colors.text }]}>{t('dasha.currentYoginiPhase', 'Current Yogini Phase')}</Text>
            <TouchableOpacity>
              <Ionicons name="information-circle-outline" size={22} color={colors.textSecondary} />
            </TouchableOpacity>
          </View>

          <View style={styles.activeRow}>
            <View>
              <Text style={[styles.label, { color: colors.textSecondary }]}>{t('dasha.mahadasha', 'Mahadasha')}</Text>
              <Text style={[styles.activeValue, { color: colors.text }]}>{tYogini(data?.current?.mahadasha?.name) || 'N/A'}</Text>
              <Text style={[styles.activeLord, { color: colors.textSecondary }]}>{YOGINI_CONFIG[data?.current?.mahadasha?.name]?.label || t('common.unknown', 'Unknown')}</Text>
            </View>
            <View style={styles.arrowContainer}>
              <Ionicons name="chevron-forward" size={20} color={colors.cardBorder} />
            </View>
            <View>
              <Text style={[styles.label, { textAlign: 'right', color: colors.textSecondary }]}>{t('dasha.antardasha', 'Antardasha')}</Text>
              <Text style={[styles.activeValue, { textAlign: 'right', color: colors.primary }]}>
                {tYogini(data?.current?.antardasha?.name) || 'N/A'}
              </Text>
              <Text style={[styles.activeLord, { textAlign: 'right', color: colors.textSecondary }]}>
                {YOGINI_CONFIG[data?.current?.antardasha?.name]?.label || t('common.unknown', 'Unknown')}
              </Text>
            </View>
          </View>

          <DashaProgress 
            percentage={data?.current?.progress || 0} 
            t={t} 
            trackBg={isDark ? 'rgba(255,255,255,0.12)' : colors.surface}
            fillColors={[colors.primary, colors.secondary]}
          />
          
          <View style={styles.dateRange}>
            <Text style={[styles.dateLabel, { color: colors.textSecondary }]}>{t('common.ends', 'Ends: ')} {formatDate(data?.current?.antardasha?.end)}</Text>
            <Text style={[styles.remainingText, { color: colors.primary }]}>{t('dasha.criticalTiming', 'Critical Timing')}</Text>
          </View>
        </LinearGradient>
      </View>

      <View style={styles.tabsContainer}>
        <TouchableOpacity style={[styles.activeTab, { backgroundColor: colors.primary }]}>
          <Text style={styles.activeTabText}>{t('dasha.periods', 'Periods')}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.inactiveTab, { backgroundColor: isDark ? colors.surface : colors.cardBackground, borderColor: colors.cardBorder }]}>
          <Text style={[styles.inactiveTabText, { color: colors.textSecondary }]}>{t('dasha.analysis', 'Analysis')}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.inactiveTab, { backgroundColor: isDark ? colors.surface : colors.cardBackground, borderColor: colors.cardBorder }]}>
          <Text style={[styles.inactiveTabText, { color: colors.textSecondary }]}>{t('dasha.remedies', 'Remedies')}</Text>
        </TouchableOpacity>
      </View>

      <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('dasha.yoginiCycle', 'Yogini Cycle (36 Years)')}</Text>
      
      <View style={styles.listContainer}>
        {data.timeline.map((item, index) => {
          const isCurrent = item.name === data?.current?.mahadasha?.name && 
                           item.start === data?.current?.mahadasha?.start && 
                           item.end === data?.current?.mahadasha?.end;
          const isExpanded = expandedId === index;
          return (
            <YoginiCard 
              key={index} 
              item={item} 
              isCurrent={isCurrent}
              isExpanded={isExpanded}
              onPress={() => handlePress(index)}
              currentAntardasha={data?.current?.antardasha}
              t={t}
              tYogini={tYogini}
              YOGINI_CONFIG={YOGINI_CONFIG}
              colors={colors}
              isDark={isDark}
            />
          );
        })}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA', // Soft off-white background
  },
  heroContainer: {
    padding: 20,
    paddingBottom: 10,
  },
  heroCard: {
    borderRadius: 20,
    padding: 20,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#eee',
    shadowColor: '#8E2DE2',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
  heroHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  heroTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#333',
  },
  activeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  label: {
    fontSize: 12,
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 4,
  },
  activeValue: {
    fontSize: 24,
    fontWeight: '800',
    color: '#1a1a1a',
  },
  activeLord: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginTop: 2,
  },
  arrowContainer: {
    marginHorizontal: 8,
  },
  progressContainer: {
    height: 24,
    backgroundColor: '#f0f0f0',
    borderRadius: 12,
    overflow: 'hidden',
    position: 'relative',
    justifyContent: 'center',
  },
  track: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#f3f3f3',
  },
  fill: {
    height: '100%',
    borderRadius: 12,
  },
  progressText: {
    position: 'absolute',
    width: '100%',
    textAlign: 'center',
    fontSize: 11,
    fontWeight: '700',
    color: '#fff',
    textShadowColor: 'rgba(0,0,0,0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  dateRange: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  dateLabel: {
    fontSize: 13,
    color: '#666',
    fontWeight: '500',
  },
  remainingText: {
    fontSize: 13,
    color: '#8E2DE2',
    fontWeight: '700',
  },
  
  // Tabs
  tabsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
    gap: 12,
  },
  activeTab: {
    backgroundColor: '#8E2DE2',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 20,
  },
  activeTabText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 14,
  },
  inactiveTab: {
    backgroundColor: '#fff',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#eee',
  },
  inactiveTabText: {
    color: '#666',
    fontWeight: '600',
    fontSize: 14,
  },

  // List
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#333',
    marginLeft: 20,
    marginBottom: 12,
  },
  listContainer: {
    paddingHorizontal: 20,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#f0f0f0',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  activeCard: {
    borderColor: '#8E2DE2',
    borderWidth: 1.5,
  },
  cardHeader: {
    height: 4,
    width: '100%',
  },
  cardContent: {
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconBox: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  yoginiName: {
    fontSize: 17,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  yoginiLord: {
    fontSize: 13,
    color: '#888',
    marginTop: 2,
  },
  cardRight: {
    alignItems: 'flex-end',
  },
  vibeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    marginBottom: 6,
  },
  vibeText: {
    fontSize: 11,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  dateText: {
    fontSize: 12,
    color: '#999',
    fontWeight: '500',
  },
  currentIndicator: {
    backgroundColor: '#f8f0ff',
    paddingVertical: 4,
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  currentText: {
    fontSize: 11,
    color: '#8E2DE2',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },

  // Sub List
  subList: {
    backgroundColor: '#fafafa',
    marginTop: -16, // Pull up to connect with card
    marginBottom: 16,
    marginHorizontal: 10,
    borderBottomLeftRadius: 16,
    borderBottomRightRadius: 16,
    padding: 16,
    paddingTop: 24,
  },
  subItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    minHeight: 40,
    paddingHorizontal: 8,
    paddingVertical: 8,
    borderRadius: 8,
  },
  currentSubItem: {
    backgroundColor: '#f8f0ff',
    borderWidth: 1,
    borderColor: '#8E2DE2',
  },
  subTimelineLine: {
    position: 'absolute',
    left: 15,
    top: 0,
    bottom: -16, // Connect to next
    width: 2,
    backgroundColor: '#eee',
    zIndex: -1,
  },
  subDot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 3,
    borderColor: '#fff',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 2,
    marginRight: 12,
  },
  subContent: {
    flex: 1,
  },
  subName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  currentSubName: {
    color: '#8E2DE2',
    fontWeight: '700',
  },
  subDates: {
    fontSize: 11,
    color: '#999',
  },
  currentSubDates: {
    color: '#8E2DE2',
    fontWeight: '600',
  },
  subVibe: {
    fontSize: 12,
    fontWeight: '600',
  },
  currentSubVibe: {
    fontWeight: '700',
  },
  currentAntarIndicator: {
    backgroundColor: '#8E2DE2',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    marginLeft: 8,
  },
  currentAntarText: {
    fontSize: 9,
    color: '#fff',
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 40,
  },
});
