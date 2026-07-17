import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { COLORS } from '../../../utils/constants';
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
        <ActivityIndicator size="large" color="#ffd700" />
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
          <View style={styles.iconContainer}>
            <LinearGradient
              colors={['#ff6b35', '#ffd700', '#ff6b35']}
              style={styles.iconGradient}
            >
              <Text style={styles.successIcon}>🎉</Text>
            </LinearGradient>
          </View>

          <Text style={styles.welcomeTitle}>
            {t('authOnboarding.welcomeTitle', { name: formData.name || '' })}
          </Text>
          
          <Text style={styles.welcomeSubtitle}>
            {t(
              'authOnboarding.chartRequiredSubtitle',
              'A birth chart is required to use chart-based features. Add your birth details to continue.',
            )}
          </Text>

          <View style={styles.featuresList}>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>📊</Text>
              <Text style={styles.featureText}>{t('authOnboarding.featureChart')}</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>🔮</Text>
              <Text style={styles.featureText}>{t('authOnboarding.featureAi')}</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>💫</Text>
              <Text style={styles.featureText}>{t('authOnboarding.featureDaily')}</Text>
            </View>
          </View>

          <TouchableOpacity
            style={styles.createChartButton}
            onPress={handleCreateBirthChart}
          >
            <LinearGradient
              colors={['#ff6b35', '#ff8c5a']}
              style={styles.buttonGradient}
            >
              <Text style={styles.buttonText}>{t('authOnboarding.createBirthChart')}</Text>
              <Ionicons name="arrow-forward" size={20} color="#ffffff" />
            </LinearGradient>
          </TouchableOpacity>
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
    alignItems: 'center',
  },
  iconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    marginBottom: 32,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.6,
    shadowRadius: 20,
    elevation: 10,
  },
  iconGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 60,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  successIcon: {
    fontSize: 56,
  },
  welcomeTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ffffff',
    textAlign: 'center',
    marginBottom: 16,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 40,
  },
  featuresList: {
    width: '100%',
    marginBottom: 40,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  featureIcon: {
    fontSize: 24,
    marginRight: 16,
  },
  featureText: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: '500',
    flex: 1,
  },
  createChartButton: {
    width: '100%',
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 8,
    marginBottom: 16,
  },
  buttonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    gap: 8,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '700',
  },
});
