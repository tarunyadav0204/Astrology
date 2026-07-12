import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  TouchableOpacity,
  Animated,
  StatusBar,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { storage } from '../../services/storage';
import { yogaAPI } from '../../services/api';
import NativeSelectorChip from '../Common/NativeSelectorChip';

const CATEGORY_ACCENT = {
  raj_yogas: '#ea580c',
  dhana_yogas: '#059669',
  panch_mahapurusha_yogas: '#d97706',
  nabhasa_yogas: '#3b82f6',
  parivartana_yogas: '#8b5cf6',
  major_doshas: '#dc2626',
  chandra_yogas: '#3b82f6',
  surya_yogas: '#f59e0b',
  marriage_yogas: '#db2777',
  health_yogas: '#10b981',
  career_specific_yogas: '#6366f1',
  education_yogas: '#0ea5e9',
  neecha_bhanga_yogas: '#14b8a6',
  gaja_kesari_yogas: '#a855f7',
  viparita_raja_yogas: '#f97316',
};

const formatCategoryLabel = (category, t) => {
  const fallback = category
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
  return t(`yogas.${category}`, fallback);
};

const YogaScreen = ({ navigation }) => {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const [yogas, setYogas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentNative, setCurrentNative] = useState(null);
  const [expandedCategories, setExpandedCategories] = useState(new Set());
  const [initialized, setInitialized] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useFocusEffect(
    React.useCallback(() => {
      loadInitialNative();
    }, [])
  );

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 400,
      useNativeDriver: true,
    }).start();
  }, []);

  const loadInitialNative = async () => {
    try {
      let birthData = await storage.getBirthDetails();
      if (!birthData) {
        const profiles = await storage.getBirthProfiles();
        if (profiles?.length) birthData = profiles.find((p) => p.relation === 'self') || profiles[0];
      }
      if (!birthData?.name) {
        navigation.replace('BirthProfileIntro', { returnTo: 'Yogas' });
        return;
      }
      if (!currentNative || currentNative.id !== birthData.id) {
        setCurrentNative(birthData);
        fetchYogas(birthData);
      }
    } catch (error) {
      console.error('Error loading initial native:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    // Expand only the first category with yogas — keeps the screen scannable.
    if (yogas && !initialized) {
      const firstKey = Object.keys(yogas).find((category) => {
        if (category === 'nabhasa_yogas' || category === 'parivartana_yogas') {
          return Object.keys(yogas[category] || {}).some(
            (sub) => Array.isArray(yogas[category][sub]) && yogas[category][sub].length > 0
          );
        }
        return Array.isArray(yogas[category]) && yogas[category].length > 0;
      });

      if (firstKey) {
        if (firstKey === 'nabhasa_yogas' || firstKey === 'parivartana_yogas') {
          const firstSub = Object.keys(yogas[firstKey] || {}).find(
            (sub) => Array.isArray(yogas[firstKey][sub]) && yogas[firstKey][sub].length > 0
          );
          if (firstSub) setExpandedCategories(new Set([`${firstKey}_${firstSub}`]));
        } else {
          setExpandedCategories(new Set([firstKey]));
        }
      }
      setInitialized(true);
    }
  }, [yogas, initialized]);

  const fetchYogas = async (birthData) => {
    try {
      setLoading(true);
      if (birthData) {
        const response = await yogaAPI.getYogas(birthData);
        if (response.data && response.data.status === 'success') {
          setYogas(response.data.yogas);
          setInitialized(false);
        }
      }
    } catch (error) {
      console.error('Error fetching yogas:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleCategory = (category) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  };

  const getStrengthColor = (strength) => {
    switch (strength?.toLowerCase()) {
      case 'high':
        return '#22c55e';
      case 'medium':
        return '#f59e0b';
      case 'low':
        return '#ef4444';
      default:
        return colors.textSecondary;
    }
  };

  const getCategoryAccent = (category) => {
    if (CATEGORY_ACCENT[category]) return CATEGORY_ACCENT[category];
    const base = category.split('_').slice(0, 2).join('_');
    return CATEGORY_ACCENT[base] || colors.primary;
  };

  const renderYogaItem = (yoga, index, isLast) => (
    <View
      key={`${yoga.name}-${index}`}
      style={[
        styles.yogaItem,
        !isLast && {
          borderBottomWidth: StyleSheet.hairlineWidth,
          borderBottomColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
        },
      ]}
    >
      <View style={styles.yogaItemHeader}>
        <Text style={[styles.yogaName, { color: colors.text }]} numberOfLines={2}>
          {yoga.name}
        </Text>
        {yoga.strength ? (
          <Text style={[styles.strengthText, { color: getStrengthColor(yoga.strength) }]}>
            {yoga.strength}
          </Text>
        ) : null}
      </View>

      {yoga.description ? (
        <Text style={[styles.yogaDescription, { color: colors.textSecondary }]}>
          {yoga.description}
        </Text>
      ) : null}

      {(yoga.planets?.length > 0 || yoga.houses?.length > 0) && (
        <View style={styles.metaRow}>
          {yoga.planets?.length > 0 ? (
            <Text style={[styles.metaText, { color: colors.textTertiary || colors.textSecondary }]}>
              {yoga.planets.join(' · ')}
            </Text>
          ) : null}
          {yoga.houses?.length > 0 ? (
            <Text style={[styles.metaText, { color: colors.textTertiary || colors.textSecondary }]}>
              {yoga.planets?.length ? '  ·  ' : ''}H{yoga.houses.join(', H')}
            </Text>
          ) : null}
        </View>
      )}
    </View>
  );

  const renderCategory = (category, yogaList) => {
    const isExpanded = expandedCategories.has(category);
    const yogaCount = Array.isArray(yogaList) ? yogaList.length : 0;
    if (yogaCount === 0) return null;

    const accent = getCategoryAccent(category);
    const surface = isDark ? 'rgba(255,255,255,0.04)' : colors.cardBackground || '#fff';
    const border = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';

    return (
      <View key={category} style={[styles.categoryBlock, { backgroundColor: surface, borderColor: border }]}>
        <TouchableOpacity
          onPress={() => toggleCategory(category)}
          activeOpacity={0.7}
          style={styles.categoryRow}
          accessibilityRole="button"
          accessibilityState={{ expanded: isExpanded }}
        >
          <View style={[styles.accentBar, { backgroundColor: accent }]} />
          <View style={styles.categoryTextWrap}>
            <Text style={[styles.categoryTitle, { color: colors.text }]} numberOfLines={1}>
              {formatCategoryLabel(category, t)}
            </Text>
            <Text style={[styles.categoryCount, { color: colors.textSecondary }]}>
              {yogaCount} {yogaCount === 1 ? 'yoga' : 'yogas'}
            </Text>
          </View>
          <Ionicons
            name={isExpanded ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={colors.textSecondary}
          />
        </TouchableOpacity>

        {isExpanded ? (
          <View style={styles.yogasList}>
            {yogaList.map((yoga, index) =>
              renderYogaItem(yoga, index, index === yogaList.length - 1)
            )}
          </View>
        ) : null}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: colors.background }]}>
        <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} />
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
          {t('yogas.loading', 'Reading yogas…')}
        </Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} />
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <View
          style={[
            styles.header,
            { borderBottomColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)' },
          ]}
        >
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            style={[
              styles.backButton,
              { backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.12)' },
            ]}
          >
            <Ionicons name="arrow-back" size={20} color={colors.text} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1}>
            {t('yogas.title', 'Yogas')}
          </Text>
          <NativeSelectorChip
            birthData={currentNative}
            onPress={() => navigation.navigate('SelectNative', { returnTo: 'Yogas' })}
            maxLength={10}
            showIcon={false}
          />
        </View>

        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          <Animated.View style={{ opacity: fadeAnim }}>
            <Text style={[styles.introText, { color: colors.textSecondary }]}>
              {t(
                'yogas.intro',
                'Planetary combinations in this chart that shape strengths, patterns, and life themes.'
              )}
            </Text>

            {yogas &&
              Object.keys(yogas).map((category) => {
                if (category === 'nabhasa_yogas' || category === 'parivartana_yogas') {
                  return Object.keys(yogas[category] || {}).map((subCategory) =>
                    renderCategory(`${category}_${subCategory}`, yogas[category][subCategory])
                  );
                }
                return renderCategory(category, yogas[category]);
              })}
          </Animated.View>
        </ScrollView>
      </SafeAreaView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    flex: 1,
    fontSize: 17,
    fontWeight: '800',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    fontWeight: '500',
  },
  introText: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  categoryBlock: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 10,
    overflow: 'hidden',
  },
  categoryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingRight: 12,
    minHeight: 52,
  },
  accentBar: {
    width: 3,
    alignSelf: 'stretch',
    marginRight: 12,
    borderTopRightRadius: 2,
    borderBottomRightRadius: 2,
  },
  categoryTextWrap: {
    flex: 1,
    paddingRight: 8,
  },
  categoryTitle: {
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 2,
  },
  categoryCount: {
    fontSize: 12,
    fontWeight: '500',
  },
  yogasList: {
    paddingHorizontal: 14,
    paddingBottom: 6,
  },
  yogaItem: {
    paddingVertical: 12,
  },
  yogaItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 10,
    marginBottom: 4,
  },
  yogaName: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
  },
  strengthText: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'capitalize',
    marginTop: 2,
  },
  yogaDescription: {
    fontSize: 13,
    lineHeight: 19,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 6,
  },
  metaText: {
    fontSize: 12,
    fontWeight: '500',
  },
});

export default YogaScreen;
