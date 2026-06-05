import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  ScrollView,
  Platform,
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
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.emoji}>🌐</Text>
        <Text style={styles.title}>{t('authOnboarding.chooseLanguageTitle')}</Text>
        <Text style={styles.subtitle}>{t('authOnboarding.chooseLanguageSubtitle')}</Text>
      </View>

      <ScrollView
        style={styles.listScroll}
        contentContainerStyle={styles.listScrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator
        bounces
      >
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
                <View style={styles.optionLabelWrap}>
                  <Text style={styles.optionFlag}>{lang.flag}</Text>
                  <Text
                    style={styles.optionText}
                    numberOfLines={1}
                    adjustsFontSizeToFit
                    minimumFontScale={0.82}
                  >
                    {lang.name}
                  </Text>
                </View>
                {selected ? (
                  <Ionicons name="checkmark-circle" size={26} color="#4CAF50" />
                ) : null}
              </TouchableOpacity>
            );
          })}
        </Animated.View>
      </ScrollView>

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
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 20,
  },
  listScroll: {
    flex: 1,
    minHeight: 0,
  },
  listScrollContent: {
    paddingBottom: 8,
  },
  header: {
    alignItems: 'center',
    paddingTop: 8,
    marginBottom: 22,
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
    marginBottom: 8,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: 78,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 14,
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.14)',
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 10,
  },
  optionSelected: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.12)',
  },
  optionLabelWrap: {
    flex: 1,
    minWidth: 0,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingRight: 14,
  },
  optionFlag: {
    width: 34,
    fontSize: 25,
    lineHeight: Platform.OS === 'android' ? 34 : 30,
    textAlign: 'center',
  },
  optionText: {
    flex: 1,
    includeFontPadding: true,
    fontSize: 20,
    lineHeight: Platform.OS === 'android' ? 34 : 28,
    color: '#ffffff',
    fontWeight: '700',
  },
  buttonContainer: {
    paddingTop: 12,
    paddingBottom: 12,
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
