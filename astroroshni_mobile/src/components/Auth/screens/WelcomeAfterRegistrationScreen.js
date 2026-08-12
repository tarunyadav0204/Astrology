import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  ActivityIndicator,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../../context/ThemeContext';
import { chartAPI } from '../../../services/api';
import storage from '../../../services/storage';
import {
  clearPendingPaidAction,
  getPendingPaidAction,
} from '../../../auth/guestAuth';
import { trackGA4EventOnly } from '../../../utils/analytics';
import { resetToRoute } from '../../../navigation/navHelpers';

export default function WelcomeAfterRegistrationScreen({
  formData,
  navigation
}) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const [routing, setRouting] = useState(true);

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 8,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const pending = await getPendingPaidAction();
        const localActive = await storage.getBirthDetails();
        let charts = [];
        try {
          const chartsRes = await chartAPI.getExistingCharts('', 10, 0);
          charts = Array.isArray(chartsRes?.data?.charts) ? chartsRes.data.charts : [];
        } catch (_) {
          /* offline / guest merge already ran */
        }

        if (cancelled) return;

        if (charts.length > 0 || localActive) {
          if (!localActive && charts.length > 0) {
            const selfChart = charts.find(
              (c) => String(c?.relation || '').trim().toLowerCase() === 'self'
            );
            const selected = selfChart || charts[0];
            await storage.setBirthDetails({
              id: selected.id ?? selected._id,
              name: selected.name,
              date: selected.date,
              time: selected.time,
              place: selected.place,
              latitude: selected.latitude,
              longitude: selected.longitude,
              gender: selected.gender,
              relation: selected.relation,
              isSelf: String(selected?.relation || '').trim().toLowerCase() === 'self',
            });
          }
          if (pending?.resumeRoute) {
            await clearPendingPaidAction();
            trackGA4EventOnly('auth_gate_completed', {
              feature: pending.feature || 'paid_feature',
            }).catch(() => {});
            resetToRoute(navigation, pending.resumeRoute, pending.resumeParams || {});
            return;
          }
          navigation.reset({ index: 0, routes: [{ name: 'Home' }] });
          return;
        }

        // Zero charts after register: birth chart required.
        setRouting(false);
      } catch (_) {
        if (!cancelled) setRouting(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [navigation]);

  const handleCreateBirthChart = () => {
    navigation.replace('BirthForm', {
      prefillData: {
        name: formData.name
      },
      chartRequired: true,
    });
  };

  if (routing) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color={colors.accent} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Animated.View
          style={[
            styles.welcomeContainer,
            {
              opacity: fadeAnim,
              transform: [
                { translateY: slideAnim },
                { scale: scaleAnim }
              ],
            },
          ]}
        >
          <View style={[styles.card, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}>
          <View style={[styles.orbit, styles.orbitLarge, { borderColor: colors.cosmicLine }]} />
          <View style={[styles.orbit, styles.orbitSmall, { borderColor: colors.cosmicLine }]} />
          <View style={[styles.iconContainer, { backgroundColor: colors.accentSoft }]}>
              <Ionicons name="checkmark" size={34} color={colors.onAccent} />
          </View>

          <Text style={[styles.eyebrow, { color: colors.accent }]}>{t('authOnboarding.accountReady', 'YOUR ACCOUNT IS READY')}</Text>
          <Text style={[styles.welcomeTitle, { color: colors.textInverse }]}>
            {t('authOnboarding.welcomeTitle', { name: formData.name || '' })}
          </Text>

          <Text style={[styles.welcomeSubtitle, { color: colors.textInverseMuted }]}>
            {t(
              'authOnboarding.chartRequiredSubtitle',
              'A birth chart is required to use chart-based features. Add your birth details to continue.',
            )}
          </Text>

          <View style={styles.featuresList}>
            <View style={[styles.featureItem, { borderColor: colors.cosmicLine }]}>
              <Ionicons name="grid-outline" size={20} color={colors.accent} />
              <Text style={[styles.featureText, { color: colors.textInverse }]}>{t('authOnboarding.featureChart')}</Text>
            </View>
            <View style={[styles.featureItem, { borderColor: colors.cosmicLine }]}>
              <Ionicons name="sparkles-outline" size={20} color={colors.accent} />
              <Text style={[styles.featureText, { color: colors.textInverse }]}>{t('authOnboarding.featureAi')}</Text>
            </View>
            <View style={[styles.featureItem, { borderColor: colors.cosmicLine }]}>
              <Ionicons name="sunny-outline" size={20} color={colors.accent} />
              <Text style={[styles.featureText, { color: colors.textInverse }]}>{t('authOnboarding.featureDaily')}</Text>
            </View>
          </View>

          <TouchableOpacity
            style={[styles.createChartButton, { backgroundColor: colors.accent }]}
            onPress={handleCreateBirthChart}
          >
              <Text style={[styles.buttonText, { color: colors.onAccent }]}>{t('authOnboarding.createBirthChart')}</Text>
              <Ionicons name="arrow-forward" size={20} color={colors.onAccent} />
          </TouchableOpacity>
          </View>
        </Animated.View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 20,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
  },
  welcomeContainer: {
    width: '100%',
  },
  card: { borderRadius: 30, borderWidth: 1, padding: 24, overflow: 'hidden' },
  orbit: { position: 'absolute', borderWidth: 1, borderRadius: 999 },
  orbitLarge: { width: 230, height: 230, right: -105, top: -115 },
  orbitSmall: { width: 156, height: 156, right: -50, top: -80 },
  iconContainer: {
    width: 54,
    height: 54,
    borderRadius: 27,
    marginBottom: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  eyebrow: { fontSize: 11, fontWeight: '800', letterSpacing: 2, marginBottom: 8 },
  welcomeTitle: {
    fontSize: 28,
    fontFamily: 'serif',
    fontWeight: '600',
    marginBottom: 16,
  },
  welcomeSubtitle: {
    fontSize: 16,
    lineHeight: 24,
    marginBottom: 28,
  },
  featuresList: {
    width: '100%',
    marginBottom: 24,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 16,
    padding: 14,
    marginBottom: 9,
    borderWidth: 1,
    gap: 12,
  },
  featureText: {
    fontSize: 16,
    fontWeight: '500',
    flex: 1,
  },
  createChartButton: {
    width: '100%',
    minHeight: 58,
    borderRadius: 999,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 9,
    shadowRadius: 16,
    elevation: 8,
    marginBottom: 16,
  },
  buttonText: {
    fontSize: 18,
    fontWeight: '700',
  },
});
