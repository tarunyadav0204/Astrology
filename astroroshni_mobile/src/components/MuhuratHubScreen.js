import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/Ionicons';
import { pricingAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';

const { width } = Dimensions.get('window');

// Cost key for each card: maps to pricing from API (credits/settings/analysis-pricing)
const COST_KEYS = {
  childbirth: 'childbirth',
  vehicle: 'vehicle',
  property: 'griha_pravesh',
  gold: 'gold',
  business: 'business'
};

// CONFIGURATION: Add new Muhurats here in the future
const MUHURAT_TYPES = [
  {
    id: 'childbirth',
    title: 'C-Section',
    subtitle: 'Safe delivery planning',
    icon: 'medical',
    gradient: ['#FF6B6B', '#EE5D5D'],
    route: 'ChildbirthPlanner' // Keep legacy separate if needed
  },
  {
    id: 'vehicle',
    title: 'Vehicle Buy',
    subtitle: 'Safety & Longevity',
    icon: 'car-sport',
    gradient: ['#FF9800', '#F57C00'],
    endpoint: '/muhurat/vehicle-purchase'
  },
  {
    id: 'property',
    title: 'Griha Pravesh',
    subtitle: 'Peace & Prosperity',
    icon: 'home',
    gradient: ['#4CAF50', '#388E3C'],
    endpoint: '/muhurat/griha-pravesh'
  },
  {
    id: 'gold',
    title: 'Gold Purchase',
    subtitle: 'Wealth & Prosperity',
    icon: 'diamond',
    gradient: ['#FFD700', '#FFA500'],
    endpoint: '/muhurat/gold-purchase'
  },
  {
    id: 'business',
    title: 'Business Opening',
    subtitle: 'Success & Growth',
    icon: 'briefcase',
    gradient: ['#9C27B0', '#7B1FA2'],
    endpoint: '/muhurat/business-opening'
  }
];

export default function MuhuratHubScreen({ navigation }) {
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const [pricing, setPricing] = useState({});
  const [pricingOriginal, setPricingOriginal] = useState({});

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
      // Pass the config to the Universal Screen
      navigation.navigate('UniversalMuhurat', { config: item });
    }
  };

  const cardBg = isDark ? 'rgba(255,255,255,0.08)' : colors.cardBackground;
  const cardBorder = isDark ? 'rgba(255,255,255,0.1)' : colors.cardBorder;
  const bannerBg = isDark ? 'rgba(249,115,22,0.18)' : 'rgba(24, 24, 27, 0.04)';
  const bannerBorder = isDark ? 'rgba(255,215,0,0.35)' : colors.cardBorder;
  const iconCircleBg = isDark ? '#f97316' : colors.primary;

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {isDark ? (
        <LinearGradient colors={['#120E24', '#261C45']} style={StyleSheet.absoluteFill} />
      ) : null}
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Icon name="arrow-back" size={24} color={colors.text} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: colors.text }]}>Auspicious Timings</Text>
          <View style={{ width: 24 }} />
        </View>

        <Text style={[styles.subHeader, { color: colors.textSecondary }]}>Select an event to plan</Text>

        <TouchableOpacity
          style={[styles.panchangBanner, { backgroundColor: bannerBg, borderColor: bannerBorder }]}
          onPress={() => navigation.navigate('DailyPanchang')}
          activeOpacity={0.88}
        >
          <View style={[styles.panchangBannerIcon, { backgroundColor: iconCircleBg }]}>
            <Icon name="sunny" size={22} color="#fff" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={[styles.panchangBannerTitle, { color: colors.text }]}>Today's Panchang</Text>
            <Text style={[styles.panchangBannerSub, { color: colors.textSecondary }]}>
              Tithi, Choghadiya, Hora, Amrit & Rahu Kaal
            </Text>
          </View>
          <Icon name="chevron-forward" size={18} color={isDark ? '#FFD700' : colors.textTertiary} />
        </TouchableOpacity>

        <ScrollView contentContainerStyle={styles.grid}>
          {MUHURAT_TYPES.map((item, index) => {
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
                {isDark ? (
                  <LinearGradient colors={item.gradient} style={styles.iconCircle}>
                    <Icon name={item.icon} size={28} color="#fff" />
                  </LinearGradient>
                ) : (
                  <View style={[styles.iconCircle, { backgroundColor: colors.backgroundSecondary }]}>
                    <Icon name={item.icon} size={28} color={colors.primary} />
                  </View>
                )}
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
  headerTitle: { fontSize: 20, fontWeight: 'bold' },
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
  panchangBannerTitle: { fontSize: 15, fontWeight: '800' },
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
  cardTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 4 },
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
    fontWeight: '800',
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
