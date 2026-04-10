import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { COLORS, LANGUAGES } from '../../../utils/constants';
import { storage } from '../../../services/storage';
import i18n from '../../../locales/i18n';

export default function ChooseLanguageScreen({ navigateToScreen }) {
  const { t } = useTranslation();
  const [selectedCode, setSelectedCode] = useState('english');
  const listAnim = useRef(new Animated.Value(0)).current;
  const buttonAnim = useRef(new Animated.Value(40)).current;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const saved = await storage.getLanguage();
      if (!cancelled && saved) {
        setSelectedCode(saved);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    Animated.parallel([
      Animated.timing(listAnim, {
        toValue: 1,
        duration: 500,
        useNativeDriver: true,
      }),
      Animated.timing(buttonAnim, {
        toValue: 0,
        duration: 600,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const handleContinue = async () => {
    await storage.setLanguage(selectedCode);
    await i18n.changeLanguage(selectedCode);
    navigateToScreen('welcomeAfterRegistration');
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator
      bounces
    >
      <View>
        <View style={styles.header}>
          <Text style={styles.emoji}>🌐</Text>
          <Text style={styles.title}>{t('authOnboarding.chooseLanguageTitle')}</Text>
          <Text style={styles.subtitle}>{t('authOnboarding.chooseLanguageSubtitle')}</Text>
        </View>

        <Animated.View
          style={[
            styles.listWrap,
            {
              opacity: listAnim,
              transform: [
                {
                  translateY: listAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [24, 0],
                  }),
                },
              ],
            },
          ]}
        >
          {LANGUAGES.map((lang) => {
            const selected = selectedCode === lang.code;
            return (
              <TouchableOpacity
                key={lang.code}
                style={[styles.option, selected && styles.optionSelected]}
                onPress={() => setSelectedCode(lang.code)}
                activeOpacity={0.85}
              >
                <Text style={styles.optionText}>
                  {lang.flag} {lang.name}
                </Text>
                {selected ? (
                  <Ionicons name="checkmark-circle" size={22} color="#4CAF50" />
                ) : null}
              </TouchableOpacity>
            );
          })}
        </Animated.View>

        <Animated.View
          style={[
            styles.buttonContainer,
            { transform: [{ translateY: buttonAnim }] },
          ]}
        >
          <TouchableOpacity style={styles.continueButton} onPress={handleContinue}>
            <LinearGradient colors={['#ff6b35', '#ff8c5a']} style={styles.buttonGradient}>
              <Text style={styles.buttonText}>{t('authOnboarding.continue')}</Text>
              <Ionicons name="arrow-forward" size={20} color="#ffffff" />
            </LinearGradient>
          </TouchableOpacity>
        </Animated.View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 48,
  },
  header: {
    alignItems: 'center',
    marginBottom: 28,
  },
  emoji: {
    fontSize: 56,
    marginBottom: 16,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 10,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.72)',
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: 8,
  },
  listWrap: {
    marginBottom: 28,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 14,
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.14)',
    paddingVertical: 14,
    paddingHorizontal: 16,
    marginBottom: 10,
  },
  optionSelected: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.12)',
  },
  optionText: {
    fontSize: 17,
    color: '#ffffff',
    fontWeight: '500',
  },
  buttonContainer: {
    marginTop: 8,
  },
  continueButton: {
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
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
    fontWeight: '600',
  },
});
