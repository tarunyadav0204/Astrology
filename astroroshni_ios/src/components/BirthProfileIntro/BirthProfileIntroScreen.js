import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  StatusBar,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { chartAPI } from '../../services/api';
import storage from '../../services/storage';
import { useTranslation } from 'react-i18next';

export default function BirthProfileIntroScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const returnTo = route.params?.returnTo;
  const [hasCharts, setHasCharts] = useState(null);
  const [loading, setLoading] = useState(true);

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
      } catch (e) {
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

  const handleContinue = () => {
    if (hasCharts) {
      navigation.replace('SelectNative', returnTo ? { returnTo } : {});
    } else {
      navigation.replace('BirthForm', returnTo ? { returnTo } : {});
    }
  };

  const handleSkip = () => {
    navigation.replace('Home');
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      <LinearGradient
        colors={['#0a0a23', '#1a1a3a', '#2d1b69', '#4a2c7a']}
        style={StyleSheet.absoluteFill}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />
      <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
        <View style={styles.content}>
          <View style={styles.iconWrap}>
            <Ionicons name="planet-outline" size={56} color="#FFD700" />
          </View>
          <Text style={styles.title}>
            {t('birthProfileIntro.title', 'Your birth chart powers your experience')}
          </Text>
          <Text style={styles.body}>
            {t('birthProfileIntro.body', 'We use your date, time and place of birth to calculate your Vedic chart and personalize insights. You can add or change this anytime in Profile.')}
          </Text>

          {loading ? (
            <ActivityIndicator size="large" color="#FFD700" style={styles.loader} />
          ) : (
            <>
              <TouchableOpacity onPress={handleContinue} activeOpacity={0.85} style={styles.primaryWrap}>
                <LinearGradient
                  colors={['#FF6B35', '#F7931E', '#FFD700']}
                  style={styles.primaryButton}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                >
                  <Text style={styles.primaryText}>
                    {t('birthProfileIntro.continue', 'Continue')}
                  </Text>
                  <Text style={styles.primaryIcon}>✨</Text>
                </LinearGradient>
              </TouchableOpacity>

              <TouchableOpacity onPress={handleSkip} activeOpacity={0.7} style={styles.skipWrap}>
                <Text style={styles.skipText}>
                  {t('birthProfileIntro.skip', 'Skip for now')}
                </Text>
                <Text style={styles.skipSubtext}>
                  {t('birthProfileIntro.skipSubtext', 'Explore the app and add your profile later')}
                </Text>
              </TouchableOpacity>
            </>
          )}
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a23',
  },
  safe: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 28,
  },
  content: {
    alignItems: 'center',
    maxWidth: 360,
    alignSelf: 'center',
  },
  iconWrap: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(255, 215, 0, 0.12)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 16,
    paddingHorizontal: 8,
  },
  body: {
    fontSize: 16,
    lineHeight: 24,
    color: 'rgba(255, 255, 255, 0.85)',
    textAlign: 'center',
    marginBottom: 32,
    paddingHorizontal: 8,
  },
  loader: {
    marginTop: 24,
  },
  primaryWrap: {
    width: '100%',
    marginBottom: 24,
  },
  primaryButton: {
    paddingVertical: 18,
    paddingHorizontal: 28,
    borderRadius: 28,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#FF6B35',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.5,
    shadowRadius: 16,
    elevation: 10,
  },
  primaryText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    marginRight: 8,
  },
  primaryIcon: {
    fontSize: 20,
  },
  skipWrap: {
    alignItems: 'center',
  },
  skipText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: 4,
  },
  skipSubtext: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.6)',
  },
});
