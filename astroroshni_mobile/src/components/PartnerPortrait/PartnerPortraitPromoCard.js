import React, { useEffect } from 'react';
import { Image, StyleSheet, Text, TouchableOpacity, useWindowDimensions, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';

import { useTheme } from '../../context/ThemeContext';
import { useCredits } from '../../credits/CreditContext';
import { trackEvent } from '../../utils/analytics';

const SAMPLE_MALE = require('../../../assets/partner-portrait/sample-partner-man.jpg');
const SAMPLE_FEMALE = require('../../../assets/partner-portrait/sample-woman-face.jpg');
const FACE_ASPECT = 4 / 5;

const showsFemaleSample = (gender) => !['female', 'woman', 'f', 'girl'].includes(String(gender || '').trim().toLowerCase());

export default function PartnerPortraitPromoCard({
  onPress,
  cost = 44,
  placement = 'unknown',
  compact = false,
  nativeName = '',
  completed = false,
  previewUrl = '',
  imageAspect = FACE_ASPECT,
  chartGender = '',
}) {
  const { colors, typography } = useTheme();
  const { width: windowWidth } = useWindowDimensions();
  const { t } = useTranslation();
  const { pricingFeatures } = useCredits();
  const enabled = Boolean(pricingFeatures?.partner_portrait_enabled);
  const showingSample = !previewUrl;
  const sampleSource = showsFemaleSample(chartGender) ? SAMPLE_FEMALE : SAMPLE_MALE;
  const frameAspect = showingSample
    ? 3 / 4
    : (imageAspect > 0 ? imageAspect : FACE_ASPECT);
  const imageWidth = Math.round(Math.min(
    compact ? 280 : 340,
    Math.max(compact ? 150 : 190, windowWidth * (compact ? 0.3 : 0.34)),
  ));

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
      accessibilityLabel={t('partnerPortrait.promoTitle', 'Your Kundali has clues about your life partner. See them come to life.')}
      style={[styles.shell, compact && styles.shellCompact, { minHeight: Math.round(imageWidth / frameAspect), borderColor: colors.cosmicLine }]}
    >
      <LinearGradient
        colors={[colors.cosmicSurface, colors.cosmicRaised || colors.cosmicSurface]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[styles.card, { minHeight: Math.round(imageWidth / frameAspect) }]}
      >
        <View style={[styles.imageClip, { width: imageWidth }]} pointerEvents="none">
          <Image
            source={showingSample ? sampleSource : { uri: previewUrl }}
            style={styles.image}
            resizeMode="cover"
          />
          <LinearGradient
            colors={[colors.cosmicSurface, 'rgba(24,4,16,0)']}
            start={{ x: 0, y: 0.5 }}
            end={{ x: 0.42, y: 0.5 }}
            style={StyleSheet.absoluteFill}
          />
        </View>
        <View style={[styles.copy, compact && styles.copyCompact, { marginRight: imageWidth - 36 }]}>
          <View style={styles.badgeRow}>
            <View style={[styles.badge, { backgroundColor: colors.accentSoft }]}>
              <Text style={[styles.badgeText, { color: colors.onAccent }]}>
                {completed ? t('partnerPortrait.readyBadge', 'YOUR PORTRAIT IS READY') : t('partnerPortrait.promoBadge', 'NEW · CLASSICAL CHART READING')}
              </Text>
            </View>
            {showingSample ? (
              <View style={styles.sampleBadge}>
                <Text style={styles.sampleBadgeText}>{t('partnerPortrait.sampleWatermark', 'SAMPLE')}</Text>
              </View>
            ) : null}
          </View>
          <Text style={[styles.title, compact && styles.titleCompact, typography?.title, { color: colors.textInverse }]}>
            {completed ? t('partnerPortrait.readyTitle', 'Your Partner Portrait is ready') : t('partnerPortrait.promoTitle', 'Your Kundali has clues about your life partner. See them come to life.')}
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
  shell: { borderWidth: 1, borderRadius: 26, overflow: 'hidden' },
  shellCompact: { borderRadius: 22 },
  card: { flex: 1, justifyContent: 'flex-end', overflow: 'hidden' },
  imageClip: { position: 'absolute', top: 0, right: 0, bottom: 0, overflow: 'hidden' },
  image: { ...StyleSheet.absoluteFillObject, width: '100%', height: '100%' },
  copy: { justifyContent: 'flex-end', padding: 20 },
  copyCompact: { minHeight: 168, padding: 17 },
  badgeRow: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 8, marginBottom: 9 },
  badge: { borderRadius: 999, paddingHorizontal: 9, paddingVertical: 5 },
  badgeText: { fontSize: 10, lineHeight: 13, fontWeight: '900', letterSpacing: 0.6 },
  sampleBadge: { borderWidth: 1, borderColor: 'rgba(255,255,255,.72)', borderRadius: 999, backgroundColor: 'rgba(26,5,17,.72)', paddingHorizontal: 9, paddingVertical: 5 },
  sampleBadgeText: { color: '#FFF8EB', fontSize: 9, lineHeight: 12, fontWeight: '900', letterSpacing: 1.1 },
  title: { maxWidth: 480, fontSize: 28, lineHeight: 33, fontWeight: '800' },
  titleCompact: { fontSize: 21, lineHeight: 25 },
  body: { maxWidth: 460, marginTop: 8, fontSize: 13, lineHeight: 19, fontWeight: '500' },
  footer: { marginTop: 15, flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 9 },
  cta: { minHeight: 38, borderRadius: 999, paddingHorizontal: 13, flexDirection: 'row', alignItems: 'center', gap: 7 },
  ctaText: { fontSize: 12, fontWeight: '900' },
  cost: { minHeight: 36, borderWidth: 1, borderRadius: 999, paddingHorizontal: 10, flexDirection: 'row', alignItems: 'center', gap: 4 },
  costText: { fontSize: 12, fontWeight: '900' },
});
