import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { storage } from '../../services/storage';
import { yogaAPI } from '../../services/api';
import { typographyTokens } from '../../theme/tokens';
import NativeSelectorChip from '../Common/NativeSelectorChip';

const CATEGORY_ICONS = {
  raj_yogas: 'diamond-outline',
  dhana_yogas: 'wallet-outline',
  panch_mahapurusha_yogas: 'star-outline',
  nabhasa_yogas: 'planet-outline',
  parivartana_yogas: 'swap-horizontal-outline',
  major_doshas: 'warning-outline',
  chandra_yogas: 'moon-outline',
  surya_yogas: 'sunny-outline',
  marriage_yogas: 'heart-outline',
  health_yogas: 'pulse-outline',
  career_specific_yogas: 'briefcase-outline',
  education_yogas: 'book-outline',
  neecha_bhanga_yogas: 'trending-up-outline',
  gaja_kesari_yogas: 'shield-checkmark-outline',
  viparita_raja_yogas: 'sparkles-outline',
};

const formatCategoryLabel = (category, t) => {
  const fallback = category.replace(/_/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase());
  return t(`yogas.${category}`, fallback);
};

const YogaScreen = ({ navigation }) => {
  const { t } = useTranslation();
  const { colors } = useTheme();
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
      duration: 420,
      useNativeDriver: true,
    }).start();
  }, [fadeAnim]);

  const categories = useMemo(() => {
    if (!yogas) return [];

    return Object.keys(yogas).flatMap((category) => {
      if (category === 'nabhasa_yogas' || category === 'parivartana_yogas') {
        return Object.keys(yogas[category] || {}).map((subCategory) => ({
          key: `${category}_${subCategory}`,
          iconKey: category,
          items: yogas[category][subCategory],
        }));
      }
      return [{ key: category, iconKey: category, items: yogas[category] }];
    }).filter(({ items }) => Array.isArray(items) && items.length > 0);
  }, [yogas]);

  const totalYogas = useMemo(
    () => categories.reduce((total, category) => total + category.items.length, 0),
    [categories]
  );

  useEffect(() => {
    if (!initialized && categories.length > 0) {
      setExpandedCategories(new Set([categories[0].key]));
      setInitialized(true);
    }
  }, [categories, initialized]);

  const loadInitialNative = async () => {
    try {
      let birthData = await storage.getBirthDetails();
      if (!birthData) {
        const profiles = await storage.getBirthProfiles();
        if (profiles?.length) birthData = profiles.find((profile) => profile.relation === 'self') || profiles[0];
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

  const fetchYogas = async (birthData) => {
    try {
      setLoading(true);
      const response = await yogaAPI.getYogas(birthData);
      if (response.data?.status === 'success') {
        setYogas(response.data.yogas);
        setInitialized(false);
      }
    } catch (error) {
      console.error('Error fetching yogas:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleCategory = (category) => {
    setExpandedCategories((previous) => {
      const next = new Set(previous);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  };

  const strengthTreatment = (strength) => {
    switch (strength?.toLowerCase()) {
      case 'high':
        return { color: colors.success, backgroundColor: colors.successSoft || colors.surfaceMuted };
      case 'medium':
        return { color: colors.warning, backgroundColor: colors.warningSoft || colors.surfaceMuted };
      case 'low':
        return { color: colors.error, backgroundColor: colors.errorSoft || colors.surfaceMuted };
      default:
        return { color: colors.textSecondary, backgroundColor: colors.surfaceMuted };
    }
  };

  const renderYogaItem = (yoga, index, isLast) => {
    const strengthStyle = strengthTreatment(yoga.strength);
    return (
      <View
        key={`${yoga.name}-${index}`}
        style={[styles.yogaItem, !isLast && { borderBottomColor: colors.cardBorder, borderBottomWidth: StyleSheet.hairlineWidth }]}
      >
        <View style={styles.yogaItemHeader}>
          <View style={[styles.yogaOrdinal, { backgroundColor: colors.accentSoft, borderColor: colors.selectionBorder }]}>
            <Text style={[styles.yogaOrdinalText, { color: colors.primaryStrong }]}>{String(index + 1).padStart(2, '0')}</Text>
          </View>
          <Text style={[styles.yogaName, { color: colors.text }]}>{yoga.name}</Text>
          {yoga.strength ? (
            <View style={[styles.strengthBadge, { backgroundColor: strengthStyle.backgroundColor }]}>
              <Text style={[styles.strengthText, { color: strengthStyle.color }]}>{yoga.strength}</Text>
            </View>
          ) : null}
        </View>

        {yoga.description ? (
          <Text style={[styles.yogaDescription, { color: colors.textSecondary }]}>{yoga.description}</Text>
        ) : null}

        {(yoga.planets?.length > 0 || yoga.houses?.length > 0) && (
          <View style={styles.metaRow}>
            {yoga.planets?.length > 0 ? (
              <View style={[styles.metaChip, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                <Ionicons name="planet-outline" size={13} color={colors.primary} />
                <Text style={[styles.metaText, { color: colors.textSecondary }]}>{yoga.planets.join(' · ')}</Text>
              </View>
            ) : null}
            {yoga.houses?.length > 0 ? (
              <View style={[styles.metaChip, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                <Ionicons name="grid-outline" size={13} color={colors.primary} />
                <Text style={[styles.metaText, { color: colors.textSecondary }]}>H{yoga.houses.join(', H')}</Text>
              </View>
            ) : null}
          </View>
        )}
      </View>
    );
  };

  const renderCategory = ({ key, iconKey, items }) => {
    const isExpanded = expandedCategories.has(key);
    return (
      <View key={key} style={[styles.categoryBlock, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
        <TouchableOpacity
          onPress={() => toggleCategory(key)}
          activeOpacity={0.76}
          style={styles.categoryRow}
          accessibilityRole="button"
          accessibilityState={{ expanded: isExpanded }}
        >
          <View style={[styles.categoryIcon, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
            <Ionicons name={CATEGORY_ICONS[iconKey] || 'sparkles-outline'} size={20} color={colors.selectionText} />
          </View>
          <View style={styles.categoryTextWrap}>
            <Text style={[styles.categoryTitle, { color: colors.text }]}>{formatCategoryLabel(key, t)}</Text>
            <Text style={[styles.categoryCount, { color: colors.textSecondary }]}>
              {t('premiumUi.yogas.combinationsFound', { count: items.length })}
            </Text>
          </View>
          <View style={[styles.expandButton, { backgroundColor: isExpanded ? colors.primary : colors.surfaceMuted }]}>
            <Ionicons name={isExpanded ? 'remove' : 'add'} size={18} color={isExpanded ? colors.onPrimary : colors.textSecondary} />
          </View>
        </TouchableOpacity>
        {isExpanded ? <View style={[styles.yogasList, { borderTopColor: colors.cardBorder }]}>{items.map((yoga, index) => renderYogaItem(yoga, index, index === items.length - 1))}</View> : null}
      </View>
    );
  };

  const renderHeader = () => (
    <View style={[styles.headerShell, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine }]}>
      <SafeAreaView edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.headerButton, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]} accessibilityLabel={t('premiumUi.common.goBack')}>
            <Ionicons name="arrow-back" size={21} color={colors.textInverse} />
          </TouchableOpacity>
          <View style={styles.headerCopy}>
            <Text style={[styles.headerEyebrow, { color: colors.accent }]}>{t('premiumUi.yogas.chartPatterns')}</Text>
            <Text style={[styles.headerTitle, { color: colors.textInverse }]}>{t('yogas.title', 'Yogas')}</Text>
          </View>
          <NativeSelectorChip
            birthData={currentNative}
            onPress={() => navigation.navigate('SelectNative', { returnTo: 'Yogas' })}
            maxLength={9}
            showIcon={false}
            style={{ backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }}
            textStyle={{ color: colors.textInverseMuted }}
            iconColor={colors.accent}
          />
        </View>
      </SafeAreaView>
    </View>
  );

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} />
        {renderHeader()}
        <View style={styles.loadingContainer}>
          <View style={[styles.loadingMark, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
            <ActivityIndicator size="small" color={colors.accent} />
          </View>
          <Text style={[styles.loadingTitle, { color: colors.text }]}>{t('premiumUi.yogas.readingPatterns')}</Text>
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('yogas.loading', 'Identifying planetary combinations…')}</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} />
      {renderHeader()}
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Animated.View style={{ opacity: fadeAnim }}>
          <View style={[styles.heroCard, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
            <View style={[styles.orbitLarge, { borderColor: colors.cosmicLine }]} />
            <View style={[styles.orbitSmall, { borderColor: colors.cosmicLine }]} />
            <Text style={[styles.heroEyebrow, { color: colors.accent }]}>{t('premiumUi.yogas.celestialSignature')}</Text>
            <Text style={[styles.heroTitle, { color: colors.textInverse }]}>{t('premiumUi.yogas.patternsPurpose')}</Text>
            <Text style={[styles.heroBody, { color: colors.textInverseMuted }]}>
              {t('yogas.intro', 'Planetary combinations in this chart that shape strengths, patterns, and life themes.')}
            </Text>
            <View style={[styles.heroMetrics, { borderTopColor: colors.cosmicLine }]}>
              <View style={styles.heroMetric}>
                <Text style={[styles.metricValue, { color: colors.accent }]}>{totalYogas}</Text>
                <Text style={[styles.metricLabel, { color: colors.textInverseMuted }]}>{t('premiumUi.yogas.yogasFound')}</Text>
              </View>
              <View style={[styles.metricDivider, { backgroundColor: colors.cosmicLine }]} />
              <View style={styles.heroMetric}>
                <Text style={[styles.metricValue, { color: colors.accent }]}>{categories.length}</Text>
                <Text style={[styles.metricLabel, { color: colors.textInverseMuted }]}>{t('premiumUi.yogas.lifeThemes')}</Text>
              </View>
            </View>
          </View>

          <View style={styles.sectionHeader}>
            <View>
              <Text style={[styles.sectionEyebrow, { color: colors.primaryStrong }]}>{t('premiumUi.yogas.detected')}</Text>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('premiumUi.yogas.explore')}</Text>
            </View>
            {categories.length > 1 ? (
              <TouchableOpacity onPress={() => setExpandedCategories(expandedCategories.size === categories.length ? new Set() : new Set(categories.map((category) => category.key)))}>
                <Text style={[styles.expandAllText, { color: colors.primaryStrong }]}>{t(expandedCategories.size === categories.length ? 'premiumUi.yogas.collapse' : 'premiumUi.yogas.expandAll')}</Text>
              </TouchableOpacity>
            ) : null}
          </View>

          {categories.length > 0 ? categories.map(renderCategory) : (
            <View style={[styles.emptyCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
              <View style={[styles.emptyIcon, { backgroundColor: colors.accentSoft }]}>
                <Ionicons name="sparkles-outline" size={24} color={colors.primaryStrong} />
              </View>
              <Text style={[styles.emptyTitle, { color: colors.text }]}>{t('premiumUi.yogas.noCombinations')}</Text>
              <Text style={[styles.emptyBody, { color: colors.textSecondary }]}>{t('premiumUi.yogas.noDetails')}</Text>
            </View>
          )}
        </Animated.View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  headerShell: { borderBottomWidth: StyleSheet.hairlineWidth },
  header: { minHeight: 72, paddingHorizontal: 18, paddingVertical: 10, flexDirection: 'row', alignItems: 'center', gap: 12 },
  headerButton: { width: 42, height: 42, borderRadius: 21, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  headerCopy: { flex: 1 },
  headerEyebrow: { ...typographyTokens.eyebrow, fontSize: 9, marginBottom: 3 },
  headerTitle: { ...typographyTokens.sectionTitle, fontSize: 25 },
  scrollView: { flex: 1 },
  scrollContent: { paddingHorizontal: 18, paddingTop: 18, paddingBottom: 48 },
  loadingContainer: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 28 },
  loadingMark: { width: 58, height: 58, borderRadius: 29, borderWidth: 1, alignItems: 'center', justifyContent: 'center', marginBottom: 18 },
  loadingTitle: { ...typographyTokens.sectionTitle, fontSize: 22, marginBottom: 6 },
  loadingText: { fontSize: 14, textAlign: 'center' },
  heroCard: { borderRadius: 28, borderWidth: 1, padding: 24, overflow: 'hidden', marginBottom: 28 },
  orbitLarge: { position: 'absolute', width: 176, height: 176, borderRadius: 88, borderWidth: 1, right: -74, top: -80 },
  orbitSmall: { position: 'absolute', width: 118, height: 118, borderRadius: 59, borderWidth: 1, right: -18, top: -58 },
  heroEyebrow: { ...typographyTokens.eyebrow, marginBottom: 14 },
  heroTitle: { ...typographyTokens.display, fontSize: 36, lineHeight: 40, maxWidth: 270, marginBottom: 12 },
  heroBody: { fontSize: 15, lineHeight: 23, maxWidth: 310 },
  heroMetrics: { flexDirection: 'row', borderTopWidth: StyleSheet.hairlineWidth, marginTop: 22, paddingTop: 18 },
  heroMetric: { flex: 1 },
  metricValue: { ...typographyTokens.sectionTitle, fontSize: 28, lineHeight: 31 },
  metricLabel: { ...typographyTokens.eyebrow, fontSize: 9, marginTop: 4 },
  metricDivider: { width: StyleSheet.hairlineWidth, marginHorizontal: 18 },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end', gap: 16, marginBottom: 14 },
  sectionEyebrow: { ...typographyTokens.eyebrow, fontSize: 9, marginBottom: 5 },
  sectionTitle: { ...typographyTokens.sectionTitle, fontSize: 23 },
  expandAllText: { fontSize: 12, fontWeight: '800', paddingVertical: 5 },
  categoryBlock: { borderRadius: 20, borderWidth: 1, marginBottom: 12, overflow: 'hidden' },
  categoryRow: { minHeight: 76, paddingHorizontal: 14, paddingVertical: 12, flexDirection: 'row', alignItems: 'center', gap: 12 },
  categoryIcon: { width: 44, height: 44, borderRadius: 15, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  categoryTextWrap: { flex: 1 },
  categoryTitle: { ...typographyTokens.sectionTitle, fontSize: 17, lineHeight: 21, marginBottom: 3 },
  categoryCount: { fontSize: 12, lineHeight: 16 },
  expandButton: { width: 30, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center' },
  yogasList: { borderTopWidth: StyleSheet.hairlineWidth, paddingHorizontal: 16 },
  yogaItem: { paddingVertical: 17 },
  yogaItemHeader: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  yogaOrdinal: { minWidth: 28, height: 28, borderRadius: 9, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  yogaOrdinalText: { fontSize: 9, fontWeight: '800', letterSpacing: 0.8 },
  yogaName: { flex: 1, ...typographyTokens.sectionTitle, fontSize: 17, lineHeight: 22, paddingTop: 2 },
  strengthBadge: { borderRadius: 999, paddingHorizontal: 9, paddingVertical: 5 },
  strengthText: { fontSize: 9, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.7 },
  yogaDescription: { fontSize: 14, lineHeight: 21, marginTop: 10, paddingLeft: 38 },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginTop: 12, paddingLeft: 38 },
  metaChip: { minHeight: 29, borderRadius: 999, borderWidth: 1, paddingHorizontal: 9, flexDirection: 'row', alignItems: 'center', gap: 5 },
  metaText: { fontSize: 11, fontWeight: '600' },
  emptyCard: { borderRadius: 20, borderWidth: 1, padding: 26, alignItems: 'center' },
  emptyIcon: { width: 50, height: 50, borderRadius: 25, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  emptyTitle: { ...typographyTokens.sectionTitle, fontSize: 19, marginBottom: 6 },
  emptyBody: { fontSize: 13, lineHeight: 19, textAlign: 'center' },
});

export default YogaScreen;
