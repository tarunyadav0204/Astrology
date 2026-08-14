import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { chartAPI } from '../../services/api';
import storage from '../../services/storage';

export default function BirthProfileIntroScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { colors, typography } = useTheme();
  const returnTo = route.params?.returnTo;
  const returnParams = route.params?.returnParams;
  const chartRequired = Boolean(route.params?.chartRequired || (returnTo && returnTo !== 'Home'));
  const [hasCharts, setHasCharts] = useState(null);
  const [loading, setLoading] = useState(true);

  const destinationParams = useMemo(
    () => ({
      ...(returnTo ? { returnTo } : {}),
      ...(returnParams ? { returnParams } : {}),
    }),
    [returnParams, returnTo],
  );

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const response = await Promise.race([
          chartAPI.getExistingCharts(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 8000)),
        ]);
        const apiCharts = response?.data?.charts || [];
        if (apiCharts.length > 0) {
          if (mounted) setHasCharts(true);
        } else {
          const localProfiles = await storage.getBirthProfiles();
          if (mounted) setHasCharts((localProfiles || []).length > 0);
        }
      } catch (_) {
        try {
          const localProfiles = await storage.getBirthProfiles();
          if (mounted) setHasCharts((localProfiles || []).length > 0);
        } catch {
          if (mounted) setHasCharts(false);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (hasCharts === true) {
      navigation.replace('SelectNative', destinationParams);
    }
  }, [destinationParams, hasCharts, navigation]);

  const handleContinue = () => {
    navigation.replace('BirthForm', destinationParams);
  };

  const handleSkip = () => {
    navigation.replace('Home');
  };

  const benefits = [
    { icon: 'grid-outline', label: t('authOnboarding.featureChart', 'Detailed Birth Chart Study') },
    { icon: 'sparkles-outline', label: t('authOnboarding.featureAi', 'AI-Powered Study') },
    { icon: 'time-outline', label: t('authOnboarding.featureDaily', 'Daily Chart Notes') },
  ];

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}> 
      <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} translucent={false} />
      <LinearGradient
        colors={[colors.background, colors.backgroundSecondary, colors.background]}
        style={StyleSheet.absoluteFill}
      />
      <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          bounces={false}
        >
          <View
            style={[
              styles.hero,
              { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine },
            ]}
          >
            <View style={[styles.orbit, styles.orbitLarge, { borderColor: colors.cosmicLine }]} />
            <View style={[styles.orbit, styles.orbitSmall, { borderColor: colors.cosmicLine }]} />
            <View style={[styles.orbitDot, { backgroundColor: colors.accent }]} />

            <View style={[styles.iconWrap, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}> 
              <View style={[styles.iconOrbit, { borderColor: colors.accent }]} />
              <Ionicons name="sparkles-outline" size={26} color={colors.accent} />
            </View>

            <Text style={[styles.eyebrow, typography.eyebrow, { color: colors.accent }]}> 
              {chartRequired
                ? t('birthProfileIntro.chartRequiredTitle', 'Birth chart required')
                : t('birthProfileIntro.emptyStateCta', 'Add birth profile')}
            </Text>
            <Text style={[styles.title, typography.display, { color: colors.textInverse }]}> 
              {chartRequired
                ? t('birthProfileIntro.chartRequiredTitle', 'Birth chart required')
                : t('birthProfileIntro.title', 'Your birth chart powers your experience')}
            </Text>
            <Text style={[styles.body, { color: colors.textInverseMuted }]}> 
              {chartRequired
                ? t(
                    'birthProfileIntro.chartRequiredBody',
                    'Your account has no birth chart yet. Add birth details to unlock charts, dashas, and personalized features.',
                  )
                : t(
                    'birthProfileIntro.body',
                    'We use your date, time and place of birth to calculate your Vedic chart and personalize chart-based insights. You can add or change this anytime in Profile.',
                  )}
            </Text>

            <View style={[styles.benefits, { borderColor: colors.cosmicLine }]}> 
              {benefits.map((benefit, index) => (
                <View
                  key={benefit.icon}
                  style={[
                    styles.benefit,
                    index < benefits.length - 1 && { borderBottomColor: colors.cosmicLine, borderBottomWidth: 1 },
                  ]}
                >
                  <View style={[styles.benefitIcon, { backgroundColor: colors.cosmicRaised }]}> 
                    <Ionicons name={benefit.icon} size={18} color={colors.accent} />
                  </View>
                  <Text style={[styles.benefitText, { color: colors.textInverse }]}>{benefit.label}</Text>
                  <Ionicons name="checkmark" size={17} color={colors.accent} />
                </View>
              ))}
            </View>

            {loading ? (
              <ActivityIndicator size="large" color={colors.accent} style={styles.loader} />
            ) : (
              <TouchableOpacity
                onPress={handleContinue}
                activeOpacity={0.86}
                style={[styles.primaryButton, { backgroundColor: colors.accent }]}
                accessibilityRole="button"
              >
                <Text style={[styles.primaryText, { color: colors.onAccent }]}> 
                  {t('authOnboarding.createBirthChart', 'Create My Birth Chart')}
                </Text>
                <Ionicons name="arrow-forward" size={20} color={colors.onAccent} />
              </TouchableOpacity>
            )}
          </View>

          {!chartRequired && !loading ? (
            <TouchableOpacity
              onPress={handleSkip}
              activeOpacity={0.72}
              style={[styles.skipCard, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}
              accessibilityRole="button"
            >
              <Text style={[styles.skipText, { color: colors.primary }]}> 
                {t('birthProfileIntro.skip', 'Skip for now')}
              </Text>
              <Text style={[styles.skipSubtext, { color: colors.textSecondary }]}> 
                {t('birthProfileIntro.skipSubtext', 'Explore the app and add your profile later')}
              </Text>
            </TouchableOpacity>
          ) : null}
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safe: { flex: 1 },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: 20,
    paddingVertical: 24,
  },
  hero: {
    width: '100%',
    maxWidth: 480,
    alignSelf: 'center',
    overflow: 'hidden',
    borderWidth: 1,
    borderRadius: 30,
    padding: 26,
  },
  orbit: { position: 'absolute', borderWidth: 1, borderRadius: 999 },
  orbitLarge: { width: 280, height: 280, right: -128, top: -145 },
  orbitSmall: { width: 190, height: 190, right: -67, top: -105 },
  orbitDot: { position: 'absolute', width: 9, height: 9, borderRadius: 5, right: 61, top: 52 },
  iconWrap: {
    width: 58,
    height: 58,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderRadius: 29,
    marginBottom: 24,
  },
  iconOrbit: {
    position: 'absolute',
    width: 38,
    height: 38,
    borderWidth: 1,
    borderRadius: 19,
    opacity: 0.65,
    transform: [{ scaleY: 0.48 }, { rotate: '-18deg' }],
  },
  eyebrow: { marginBottom: 9 },
  title: {
    maxWidth: 340,
    marginBottom: 14,
    fontSize: 38,
    lineHeight: 42,
    letterSpacing: -0.8,
  },
  body: { maxWidth: 390, fontSize: 15, lineHeight: 23, marginBottom: 22 },
  benefits: { borderTopWidth: 1, borderBottomWidth: 1, marginBottom: 24 },
  benefit: { minHeight: 54, flexDirection: 'row', alignItems: 'center' },
  benefitIcon: {
    width: 34,
    height: 34,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 17,
    marginRight: 12,
  },
  benefitText: { flex: 1, fontSize: 14, lineHeight: 19, fontWeight: '700' },
  loader: { minHeight: 56, justifyContent: 'center' },
  primaryButton: {
    minHeight: 58,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    borderRadius: 999,
    paddingHorizontal: 24,
  },
  primaryText: { fontSize: 16, fontWeight: '800' },
  skipCard: {
    width: '100%',
    maxWidth: 480,
    alignSelf: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 20,
    marginTop: 14,
    paddingHorizontal: 20,
    paddingVertical: 15,
  },
  skipText: { fontSize: 15, fontWeight: '800', marginBottom: 3 },
  skipSubtext: { fontSize: 12, lineHeight: 17, textAlign: 'center' },
});
