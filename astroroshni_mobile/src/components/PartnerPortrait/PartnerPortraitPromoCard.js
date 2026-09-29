import React, { useEffect } from 'react';
import { Image, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';

import { useTheme } from '../../context/ThemeContext';
import { useCredits } from '../../credits/CreditContext';
import { trackEvent } from '../../utils/analytics';

const SAMPLE = require('../../../assets/partner-portrait/sample-example.jpg');

export default function PartnerPortraitPromoCard({
  onPress,
  cost = 44,
  placement = 'unknown',
  compact = false,
  nativeName = '',
  completed = false,
  previewUrl = '',
}) {
  const { colors, typography } = useTheme();
  const { t } = useTranslation();
  const { pricingFeatures } = useCredits();
  const enabled = Boolean(pricingFeatures?.partner_portrait_enabled);

  useEffect(() => {
    if (!enabled) return;
    trackEvent('partner_portrait_promo_impression', { placement });
  }, [enabled, placement]);

  if (!enabled) return null;

  const open = () => {
    trackEvent('partner_portrait_promo_open', { placement, cost });
    onPress?.();
  };

  return (
    <TouchableOpacity
      onPress={open}
      activeOpacity={0.86}
      accessibilityRole="button"
      accessibilityLabel={t('partnerPortrait.promoTitle', 'See the partner your birth chart describes')}
      style={[styles.shell, compact && styles.shellCompact, { borderColor: colors.cosmicLine }]}
    >
      <LinearGradient
        colors={[colors.cosmicSurface, colors.cosmicRaised || colors.cosmicSurface]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[styles.card, compact && styles.cardCompact]}
      >
        <Image source={previewUrl ? { uri: previewUrl } : SAMPLE} style={[styles.image, compact && styles.imageCompact]} resizeMode="cover" />
        <LinearGradient
          colors={['rgba(24,4,16,0)', 'rgba(24,4,16,0.95)']}
          style={styles.imageShade}
          pointerEvents="none"
        />
        {!completed ? (
          <View style={styles.sampleBadge}><Text style={styles.sampleBadgeText}>{t('partnerPortrait.sampleWatermark', 'SAMPLE')}</Text></View>
        ) : null}
        <View style={[styles.copy, compact && styles.copyCompact]}>
          <View style={styles.badgeRow}>
            <View style={[styles.badge, { backgroundColor: colors.accentSoft }]}> 
              <Text style={[styles.badgeText, { color: colors.onAccent }]}> 
                {completed ? t('partnerPortrait.readyBadge', 'YOUR PORTRAIT IS READY') : t('partnerPortrait.promoBadge', 'NEW · CLASSICAL CHART READING')}
              </Text>
            </View>
          </View>
          <Text style={[styles.title, compact && styles.titleCompact, typography?.title, { color: colors.textInverse }]}> 
            {completed ? t('partnerPortrait.readyTitle', 'Your Partner Portrait is ready') : t('partnerPortrait.promoTitle', 'See the partner your birth chart describes')}
          </Text>
          {!compact ? (
            <Text style={[styles.body, { color: colors.textInverseMuted }]}> 
              {nativeName
                ? t('partnerPortrait.promoBodyNamed', 'Create an appearance and personality portrait from {{name}}’s classical partner indications.', { name: nativeName })
                : t('partnerPortrait.promoBody', 'Bring the strongest repeated appearance and personality indications in the chart to life.')}
            </Text>
          ) : null}
          <View style={styles.footer}>
            <View style={[styles.cta, { backgroundColor: colors.accentSoft }]}> 
              <Text style={[styles.ctaText, { color: colors.onAccent }]}> 
                {completed ? t('partnerPortrait.openPortrait', "Open my partner's portrait") : t('partnerPortrait.promoCta', "Create my partner's portrait")}
              </Text>
              <Ionicons name="arrow-forward" size={15} color={colors.onAccent} />
            </View>
            <View style={[styles.cost, { borderColor: colors.cosmicLine, backgroundColor: colors.cosmicSurface }]}> 
              <Ionicons name="diamond-outline" size={12} color={colors.accent} />
              <Text style={[styles.costText, { color: colors.textInverse }]}>{cost}</Text>
            </View>
          </View>
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  shell: { minHeight: 330, borderWidth: 1, borderRadius: 26, overflow: 'hidden' },
  shellCompact: { minHeight: 220, borderRadius: 22 },
  card: { flex: 1, minHeight: 330, justifyContent: 'flex-end', overflow: 'hidden' },
  cardCompact: { minHeight: 220 },
  image: { ...StyleSheet.absoluteFillObject, width: '100%', height: '100%' },
  imageCompact: { width: '48%', left: '52%' },
  imageShade: { ...StyleSheet.absoluteFillObject },
  sampleBadge: { position: 'absolute', top: 14, right: 14, borderWidth: 1, borderColor: 'rgba(255,255,255,.72)', borderRadius: 999, backgroundColor: 'rgba(26,5,17,.72)', paddingHorizontal: 9, paddingVertical: 5 },
  sampleBadgeText: { color: '#FFF8EB', fontSize: 9, lineHeight: 12, fontWeight: '900', letterSpacing: 1.1 },
  copy: { minHeight: 210, padding: 20, justifyContent: 'flex-end' },
  copyCompact: { width: '74%', minHeight: 220, padding: 17 },
  badgeRow: { flexDirection: 'row', marginBottom: 9 },
  badge: { borderRadius: 999, paddingHorizontal: 9, paddingVertical: 5 },
  badgeText: { fontSize: 10, lineHeight: 13, fontWeight: '900', letterSpacing: 0.6 },
  title: { maxWidth: 480, fontSize: 28, lineHeight: 33, fontWeight: '800' },
  titleCompact: { fontSize: 21, lineHeight: 25 },
  body: { maxWidth: 500, marginTop: 8, fontSize: 13, lineHeight: 19, fontWeight: '500' },
  footer: { marginTop: 15, flexDirection: 'row', alignItems: 'center', gap: 9 },
  cta: { minHeight: 38, borderRadius: 999, paddingHorizontal: 13, flexDirection: 'row', alignItems: 'center', gap: 7 },
  ctaText: { fontSize: 12, fontWeight: '900' },
  cost: { minHeight: 36, borderWidth: 1, borderRadius: 999, paddingHorizontal: 10, flexDirection: 'row', alignItems: 'center', gap: 4 },
  costText: { fontSize: 12, fontWeight: '900' },
});
