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
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      <LinearGradient
        colors={['#ffffff', '#f8f8f8', '#f5f5f5']}
        style={StyleSheet.absoluteFill}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />
      <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
        <View style={styles.content}>
          <View style={styles.iconWrap}>
            <Ionicons name="planet-outline" size={56} color="#000000" />
          </View>
          <Text style={styles.title}>
            {t('birthProfileIntro.title', 'Your birth chart powers your experience')}
          </Text>
          <Text style={styles.body}>
            {t('birthProfileIntro.body', 'We use your date, time and place of birth to calculate your Vedic chart and personalize insights. You can add or change this anytime in Profile.')}
          </Text>

          {loading ? (
            <ActivityIndicator size="large" color="#000000" style={styles.loader} />
          ) : (
            <>
              <TouchableOpacity onPress={handleContinue} activeOpacity={0.85} style={styles.primaryWrap}>
                <View style={styles.primaryButton}>
                  <Text style={styles.primaryText}>
                    {t('birthProfileIntro.continue', 'Continue')}
                  </Text>
                  <Text style={styles.primaryIcon}>✨</Text>
                </View>
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
    backgroundColor: '#ffffff',
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
    backgroundColor: 'rgba(0, 0, 0, 0.06)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#000000',
    textAlign: 'center',
    marginBottom: 16,
    paddingHorizontal: 8,
  },
  body: {
    fontSize: 16,
    lineHeight: 24,
    color: '#666666',
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
    backgroundColor: '#000000',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 6,
  },
  primaryText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    marginRight: 8,
  },
  primaryIcon: {
    fontSize: 20,
    color: '#FFFFFF',
  },
  skipWrap: {
    alignItems: 'center',
  },
  skipText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333333',
    marginBottom: 4,
  },
  skipSubtext: {
    fontSize: 13,
    color: '#666666',
  },
});
