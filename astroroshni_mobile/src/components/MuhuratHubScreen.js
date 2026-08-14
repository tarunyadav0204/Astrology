import React, { useMemo, useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { pricingAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import FocusedStatusBar from './Common/FocusedStatusBar';

const { width } = Dimensions.get('window');

// Cost key for each card: maps to pricing from API (credits/settings/analysis-pricing)
const COST_KEYS = {
  childbirth: 'childbirth',
  vehicle: 'vehicle',
  property: 'griha_pravesh',
  gold: 'gold',
  business: 'business'
};

const MUHURAT_TYPE_DEFS = [
  {
    id: 'childbirth',
    icon: 'medical',
    gradient: ['#FF6B6B', '#EE5D5D'],
    route: 'ChildbirthPlanner',
  },
  {
    id: 'vehicle',
    icon: 'car-sport',
    gradient: ['#FF9800', '#F57C00'],
    endpoint: '/muhurat/vehicle-purchase',
  },
  {
    id: 'property',
    icon: 'home',
    gradient: ['#4CAF50', '#388E3C'],
    endpoint: '/muhurat/griha-pravesh',
  },
  {
    id: 'gold',
    icon: 'diamond',
    gradient: ['#FFD700', '#FFA500'],
    endpoint: '/muhurat/gold-purchase',
  },
  {
    id: 'business',
    icon: 'briefcase',
    gradient: ['#9C27B0', '#7B1FA2'],
    endpoint: '/muhurat/business-opening',
  },
];

export default function MuhuratHubScreen({ navigation }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const [pricing, setPricing] = useState({});
  const [pricingOriginal, setPricingOriginal] = useState({});

  const muhuratTypes = useMemo(
    () =>
      MUHURAT_TYPE_DEFS.map((item) => ({
        ...item,
        title: t(`muhurat.types.${item.id}.title`, item.id),
        subtitle: t(`muhurat.types.${item.id}.subtitle`, ''),
      })),
    [t],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await pricingAPI.getPricing();
        const data = res?.data || res;
        if (!cancelled && data?.pricing) {
          setPricing(data.pricing);
          setPricingOriginal(data.pricing_original || {});
        }
      } catch (e) {
        // keep defaults
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const handlePress = (item) => {
    if (item.route) {
      navigation.navigate(item.route);
    } else {
      navigation.navigate('UniversalMuhurat', { config: item });
    }
  };

  const cardBg = colors.cardBackground;
  const cardBorder = colors.cardBorder;
  const bannerBg = colors.surfaceRaised;
  const bannerBorder = colors.selectionBorder;
  const iconCircleBg = colors.primary;

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <LinearGradient colors={[colors.gradientStart, colors.gradientMid, colors.gradientEnd]} style={StyleSheet.absoluteFill} />
      <FocusedStatusBar
        backgroundColor={colors.background}
        barStyle={colors.statusBarStyle || 'dark-content'}
      />
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.background }]}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Icon name="arrow-back" size={24} color={colors.text} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: colors.text }]}>
            {t('muhurat.hub.title', 'Auspicious Timings')}
          </Text>
          <View style={{ width: 24 }} />
        </View>

        <Text style={[styles.subHeader, { color: colors.textSecondary }]}>
          {t('muhurat.hub.subtitle', 'Select an event to plan')}
        </Text>

        <TouchableOpacity
          style={[styles.panchangBanner, { backgroundColor: bannerBg, borderColor: bannerBorder }]}
          onPress={() => navigation.navigate('DailyPanchang')}
          activeOpacity={0.88}
        >
          <View style={[styles.panchangBannerIcon, { backgroundColor: iconCircleBg }]}>
            <Icon name="sunny" size={22} color="#fff" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={[styles.panchangBannerTitle, { color: colors.text }]}>
              {t('muhurat.hub.todaysPanchang', "Today's Panchang")}
            </Text>
            <Text style={[styles.panchangBannerSub, { color: colors.textSecondary }]}>
              {t('muhurat.hub.todaysPanchangSub', 'Tithi, Choghadiya, Hora, Amrit & Rahu Kaal')}
            </Text>
          </View>
          <Icon name="chevron-forward" size={18} color={colors.accent} />
        </TouchableOpacity>

        <ScrollView contentContainerStyle={styles.grid}>
          {muhuratTypes.map((item, index) => {
            const costKey = COST_KEYS[item.id];
            const cost = costKey != null ? (pricing[costKey] ?? 0) : 0;
            const originalCost = costKey != null ? pricingOriginal[costKey] : null;
            const showCost = cost > 0;
            return (
              <TouchableOpacity
                key={index}
                style={[styles.card, { backgroundColor: cardBg, borderColor: cardBorder }]}
                onPress={() => handlePress(item)}
              >
                {showCost && (
                  <View style={styles.costBadge}>
                    <Icon name="flash" size={8} color="#854d0e" />
                    {originalCost != null && originalCost > cost ? (
                      <View style={styles.costWithDiscount}>
                        <Text style={[styles.costText, styles.costOriginal]}>{originalCost}</Text>
                        <Text style={styles.costText}>{cost}</Text>
                      </View>
                    ) : (
                      <Text style={styles.costText}>{cost}</Text>
                    )}
                  </View>
                )}
                <LinearGradient colors={[colors.primary, colors.primaryStrong]} style={styles.iconCircle}>
                  <Icon name={item.icon} size={28} color={colors.onPrimary} />
                </LinearGradient>
                <Text style={[styles.cardTitle, { color: colors.text }]}>{item.title}</Text>
                <Text style={[styles.cardSubtitle, { color: colors.textSecondary }]}>{item.subtitle}</Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  header: { flexDirection: 'row', justifyContent: 'space-between', padding: 20, alignItems: 'center' },
  // Keep ≤600: heavy weights look smudged on light/Hindi (faux-bold Devanagari).
  headerTitle: { fontSize: 20, fontWeight: '600' },
  subHeader: { marginLeft: 20, marginBottom: 12 },
  panchangBanner: {
    marginHorizontal: 20,
    marginBottom: 18,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  panchangBannerIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  panchangBannerTitle: { fontSize: 15, fontWeight: '600' },
  panchangBannerSub: { fontSize: 11, marginTop: 2 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 15 },
  card: {
    width: (width - 50) / 2,
    borderRadius: 16,
    padding: 15,
    margin: 5,
    marginBottom: 15,
    alignItems: 'center',
    borderWidth: 1,
  },
  iconCircle: { width: 50, height: 50, borderRadius: 25, justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
  cardTitle: { fontSize: 16, fontWeight: '600', marginBottom: 4 },
  cardSubtitle: { fontSize: 11, textAlign: 'center' },
  costBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(255, 215, 0, 0.95)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#fff',
    zIndex: 1,
  },
  costText: {
    fontSize: 9,
    fontWeight: '600',
    color: '#854d0e',
    marginLeft: 2,
  },
  costWithDiscount: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  costOriginal: {
    textDecorationLine: 'line-through',
    color: '#854d0e',
    opacity: 0.8,
  },
});
