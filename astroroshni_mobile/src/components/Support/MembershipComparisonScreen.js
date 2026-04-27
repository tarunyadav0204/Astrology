import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  useWindowDimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { creditAPI, pricingAPI } from '../../services/api';

const FEATURE_ROWS = [
  { key: 'chat', label: 'Chat question' },
  { key: 'premium_chat', label: 'Premium deep analysis chat' },
  { key: 'career', label: 'Career analysis' },
  { key: 'marriage', label: 'Marriage analysis' },
  { key: 'health', label: 'Health analysis' },
  { key: 'wealth', label: 'Wealth analysis' },
  { key: 'education', label: 'Education analysis' },
  { key: 'progeny', label: 'Progeny analysis' },
  { key: 'karma', label: 'Karma analysis' },
  { key: 'partnership', label: 'Partnership compatibility analysis' },
  { key: 'ashtakavarga', label: 'Ashtakavarga life predictions' },
  { key: 'events', label: 'Yearly event timeline analysis' },
  { key: 'business', label: 'Business opening muhurat' },
  { key: 'childbirth', label: 'Childbirth muhurat planning' },
  { key: 'gold', label: 'Gold purchase muhurat' },
  { key: 'griha_pravesh', label: 'Griha pravesh muhurat' },
  { key: 'vehicle', label: 'Vehicle purchase muhurat' },
  { key: 'trading', label: 'Daily trading forecast' },
  { key: 'trading_monthly', label: 'Monthly trading calendar' },
  { key: 'podcast', label: 'Podcast (listen as audio)' },
];

const resolveTierDiscounts = (plans = []) => {
  const result = { silver: 0, gold: 0, platinum: 0 };
  plans.forEach((p) => {
    const tier = String(p?.tier_name || '').trim().toLowerCase();
    const discount = Math.max(0, Number(p?.discount_percent || 0));
    if (tier.includes('silver')) result.silver = discount;
    else if (tier.includes('gold')) result.gold = discount;
    else if (tier.includes('platinum')) result.platinum = discount;
  });
  return result;
};

const applyTierDiscount = (regular, percent) =>
  Math.max(1, Math.round(Number(regular) * (100 - Number(percent || 0)) / 100));

export default function MembershipComparisonScreen({ navigation }) {
  const { colors, theme } = useTheme();
  const { t } = useTranslation();
  const { height: windowHeight } = useWindowDimensions();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [pricing, setPricing] = useState({});
  const [pricingOriginal, setPricingOriginal] = useState({});
  const [tierDiscounts, setTierDiscounts] = useState({ silver: 0, gold: 0, platinum: 0 });
  const [tableViewportHeight, setTableViewportHeight] = useState(0);
  const frozenBodyRef = useRef(null);
  const scrollBodyRef = useRef(null);
  const syncingRef = useRef(false);

  const loadData = async () => {
    setError('');
    try {
      const [pricingRes, plansRes] = await Promise.all([
        pricingAPI.getPricing(),
        creditAPI.getSubscriptionPlans(),
      ]);
      const pricingData = pricingRes?.data || {};
      const plans = Array.isArray(plansRes?.data?.plans) ? plansRes.data.plans : [];
      setPricing(pricingData?.pricing || {});
      setPricingOriginal(pricingData?.pricing_original || {});
      setTierDiscounts(resolveTierDiscounts(plans));
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load membership pricing.');
      setPricing({});
      setPricingOriginal({});
      setTierDiscounts({ silver: 0, gold: 0, platinum: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const rows = useMemo(() => {
    return FEATURE_ROWS.map(({ key, label }) => {
      const discounted = Number(pricing?.[key]);
      const original = Number(pricingOriginal?.[key]);
      if (!Number.isFinite(discounted) && !Number.isFinite(original)) return null;
      const regular = Number.isFinite(original)
        ? original
        : (Number.isFinite(discounted) ? discounted : null);
      if (!Number.isFinite(regular)) return null;
      const discountedValue = Number.isFinite(discounted) ? discounted : regular;
      return {
        key,
        label,
        regular: regular,
        discounted: discountedValue,
        silver: applyTierDiscount(regular, tierDiscounts.silver),
        gold: applyTierDiscount(regular, tierDiscounts.gold),
        platinum: applyTierDiscount(regular, tierDiscounts.platinum),
      };
    }).filter(Boolean);
  }, [pricing, pricingOriginal, tierDiscounts]);

  const isDark = theme === 'dark';
  const cardBg = isDark ? 'rgba(15,23,42,0.95)' : colors.surface;
  const fallbackBodyHeight = Math.max(220, Math.min(540, windowHeight - 360));
  const tableBodyHeight =
    tableViewportHeight > 0 ? Math.max(220, tableViewportHeight - 42) : fallbackBodyHeight;

  const syncVerticalScroll = (source, y) => {
    if (syncingRef.current) return;
    syncingRef.current = true;
    const target = source === 'scroll' ? frozenBodyRef.current : scrollBodyRef.current;
    target?.scrollTo?.({ y, animated: false });
    requestAnimationFrame(() => {
      syncingRef.current = false;
    });
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top', 'left', 'right']}>
      <View style={[styles.header, { borderBottomColor: colors.border }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: colors.text }]}>Plan Comparison</Text>
        <View style={{ width: 40 }} />
      </View>

      <View style={[styles.summaryCard, { backgroundColor: cardBg, borderColor: colors.border }]}>
        <Text style={[styles.summaryTitle, { color: colors.text }]}>Transparent pricing per feature</Text>
        <Text style={[styles.summaryText, { color: colors.textSecondary }]}>
          Regular and discounted prices are shown along with tier-wise credits for Silver, Gold, and Platinum.
        </Text>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={colors.primary} style={{ marginTop: 24 }} />
      ) : (
        <View style={styles.contentArea}>
          {error ? (
            <View style={styles.errorBar}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : null}

          <View
            style={[styles.tableCard, styles.tableCardFlex, { backgroundColor: cardBg, borderColor: colors.border }]}
            onLayout={(e) => {
              const h = Number(e?.nativeEvent?.layout?.height || 0);
              if (h > 0) setTableViewportHeight(h);
            }}
          >
            <View style={styles.tableSplitWrap}>
              <View style={[styles.frozenColumn, { borderRightColor: colors.border }]}>
                <View style={[styles.tableHeaderRow, { borderBottomColor: colors.border }]}>
                  <Text
                    style={[styles.colFeature, styles.colHeader, styles.headerCell, { color: colors.textSecondary }]}
                    numberOfLines={1}
                  >
                    Feature
                  </Text>
                </View>
                <ScrollView
                  ref={frozenBodyRef}
                  style={[styles.tableBody, { height: tableBodyHeight }]}
                  showsVerticalScrollIndicator={false}
                  scrollEnabled={false}
                  nestedScrollEnabled
                >
                  {rows.map((row, idx) => (
                    <View
                      key={`frozen-${row.key}`}
                      style={[
                        styles.tableDataRow,
                        { borderBottomColor: idx < rows.length - 1 ? colors.border : 'transparent' },
                      ]}
                    >
                      <Text style={[styles.colFeature, styles.featureText, { color: colors.text }]}>{row.label}</Text>
                    </View>
                  ))}
                </ScrollView>
              </View>

              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                nestedScrollEnabled
                directionalLockEnabled
              >
                <View>
                  <View style={[styles.tableHeaderRow, { borderBottomColor: colors.border }]}>
                    <Text style={[styles.colSmall, styles.colHeader, styles.headerCell, { color: colors.textSecondary }]} numberOfLines={1}>Regular</Text>
                    <Text style={[styles.colDiscounted, styles.colHeader, styles.headerCell, { color: colors.textSecondary }]} numberOfLines={1}>Discounted</Text>
                    <Text style={[styles.colSmall, styles.colHeader, styles.headerCell, { color: colors.textSecondary }]} numberOfLines={1}>Silver</Text>
                    <Text style={[styles.colSmall, styles.colHeader, styles.headerCell, { color: colors.textSecondary }]} numberOfLines={1}>Gold</Text>
                    <Text style={[styles.colSmall, styles.colHeader, styles.headerCell, { color: colors.textSecondary }]} numberOfLines={1}>Platinum</Text>
                  </View>
                  <ScrollView
                    ref={scrollBodyRef}
                    style={[styles.tableBody, { height: tableBodyHeight }]}
                    nestedScrollEnabled
                    showsVerticalScrollIndicator
                    directionalLockEnabled
                    scrollEventThrottle={16}
                    onScroll={(e) => syncVerticalScroll('scroll', e.nativeEvent.contentOffset.y)}
                  >
                    {rows.map((row, idx) => (
                      <View
                        key={`scroll-${row.key}`}
                        style={[
                          styles.tableDataRow,
                          { borderBottomColor: idx < rows.length - 1 ? colors.border : 'transparent' },
                        ]}
                      >
                        <Text style={[styles.colSmall, { color: colors.text }]}>{row.regular}</Text>
                        <Text style={[styles.colDiscounted, { color: colors.primary, fontWeight: '700' }]}>{row.discounted}</Text>
                        <Text style={[styles.colSmall, { color: colors.text }]}>{row.silver}</Text>
                        <Text style={[styles.colSmall, { color: colors.text }]}>{row.gold}</Text>
                        <Text style={[styles.colSmall, { color: colors.text }]}>{row.platinum}</Text>
                      </View>
                    ))}
                  </ScrollView>
                </View>
              </ScrollView>
            </View>
          </View>

          <TouchableOpacity
            style={[styles.supportButton, { backgroundColor: colors.primary }]}
            onPress={() => navigation.navigate('Support')}
          >
            <Ionicons name="help-circle-outline" size={18} color="#fff" />
            <Text style={styles.supportButtonText}>
              {t('support.title')}: Need help choosing a plan?
            </Text>
          </TouchableOpacity>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 8,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backButton: { padding: 8 },
  headerTitle: { fontSize: 18, fontWeight: '700' },
  summaryCard: {
    borderWidth: 1,
    borderRadius: 14,
    marginHorizontal: 16,
    marginTop: 12,
    padding: 12,
  },
  summaryTitle: { fontSize: 15, fontWeight: '700', marginBottom: 4 },
  summaryText: { fontSize: 13, lineHeight: 18 },
  contentArea: {
    flex: 1,
    padding: 16,
    paddingBottom: 12,
  },
  errorBar: {
    backgroundColor: 'rgba(220,38,38,0.12)',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginBottom: 12,
  },
  errorText: { color: '#b91c1c', fontSize: 13 },
  tableCard: {
    borderWidth: 1,
    borderRadius: 14,
    overflow: 'hidden',
  },
  tableCardFlex: {
    flex: 1,
    minHeight: 0,
  },
  tableSplitWrap: {
    flexDirection: 'row',
  },
  frozenColumn: {
    width: 185,
    borderRightWidth: 1,
    backgroundColor: 'rgba(148,163,184,0.08)',
  },
  tableBody: {
    minHeight: 260,
  },
  tableHeaderRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    backgroundColor: 'rgba(148,163,184,0.12)',
    minHeight: 42,
    alignItems: 'center',
  },
  tableDataRow: {
    flexDirection: 'row',
    borderBottomWidth: StyleSheet.hairlineWidth,
    minHeight: 56,
    alignItems: 'center',
  },
  colFeature: {
    width: 185,
    paddingVertical: 10,
    paddingHorizontal: 10,
  },
  colSmall: {
    width: 86,
    textAlign: 'center',
    paddingVertical: 10,
    paddingHorizontal: 4,
  },
  colDiscounted: {
    width: 110,
    textAlign: 'center',
    paddingVertical: 10,
    paddingHorizontal: 4,
  },
  colHeader: {
    fontSize: 11,
    fontWeight: '700',
  },
  headerCell: {
    includeFontPadding: false,
    textAlignVertical: 'center',
  },
  featureText: {
    fontSize: 13,
    lineHeight: 18,
  },
  supportButton: {
    marginTop: 16,
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 14,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  supportButtonText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 14,
  },
});
