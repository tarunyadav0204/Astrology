import React, { useEffect, useRef, useState } from 'react';
import { Animated, Platform, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { LANGUAGES } from '../../../utils/constants';
import { storage } from '../../../services/storage';
import i18n from '../../../locales/i18n';
import { useTheme } from '../../../context/ThemeContext';

export default function ChooseLanguageScreen({ navigateToScreen }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const [selectedCode, setSelectedCode] = useState('english');
  const entrance = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    let cancelled = false;
    storage.getLanguage().then((saved) => { if (!cancelled && saved) setSelectedCode(saved); });
    Animated.timing(entrance, { toValue: 1, duration: 420, useNativeDriver: true }).start();
    return () => { cancelled = true; };
  }, [entrance]);

  const handleContinue = async () => {
    await storage.setLanguage(selectedCode);
    await i18n.changeLanguage(selectedCode);
    navigateToScreen('welcomeAfterRegistration');
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={[styles.icon, { backgroundColor: colors.accentSoft }]}><Ionicons name="language-outline" size={24} color={colors.onAccent} /></View>
        <Text style={[styles.eyebrow, { color: colors.accent }]}>{t('authOnboarding.languageEyebrow', 'MAKE IT YOURS')}</Text>
        <Text style={[styles.title, { color: colors.textInverse }]}>{t('authOnboarding.chooseLanguageTitle')}</Text>
        <Text style={[styles.subtitle, { color: colors.textInverseMuted }]}>{t('authOnboarding.chooseLanguageSubtitle')}</Text>
      </View>
      <ScrollView style={styles.scroll} contentContainerStyle={styles.list} showsVerticalScrollIndicator={false}>
        <Animated.View style={{ opacity: entrance, transform: [{ translateY: entrance.interpolate({ inputRange: [0, 1], outputRange: [20, 0] }) }] }}>
          {LANGUAGES.map((lang) => {
            const selected = selectedCode === lang.code;
            return (
              <TouchableOpacity key={lang.code} style={[styles.option, { backgroundColor: selected ? colors.selectionSurface : colors.cosmicRaised, borderColor: selected ? colors.selectionBorder : colors.cosmicLine }]} onPress={() => setSelectedCode(lang.code)}>
                <Text style={styles.flag}>{lang.flag}</Text>
                <Text style={[styles.optionText, { color: selected ? colors.selectionText : colors.textInverse }]}>{lang.name}</Text>
                <View style={[styles.check, { backgroundColor: selected ? colors.selectionControl : 'transparent', borderColor: selected ? colors.selectionBorder : colors.cosmicLine }]}>{selected && <Ionicons name="checkmark" size={17} color={colors.selectionText} />}</View>
              </TouchableOpacity>
            );
          })}
        </Animated.View>
      </ScrollView>
      <TouchableOpacity style={[styles.continueButton, { backgroundColor: colors.accent }]} onPress={handleContinue}>
        <Text style={[styles.buttonText, { color: colors.onAccent }]}>{t('authOnboarding.continue')}</Text>
        <Ionicons name="arrow-forward" size={19} color={colors.onAccent} />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingHorizontal: 20, paddingTop: 10, paddingBottom: 16 },
  header: { alignItems: 'center', marginBottom: 20 },
  icon: { width: 50, height: 50, borderRadius: 25, alignItems: 'center', justifyContent: 'center', marginBottom: 15 },
  eyebrow: { fontSize: 11, fontWeight: '800', letterSpacing: 2.1, marginBottom: 7 },
  title: { fontSize: 31, lineHeight: 36, fontFamily: 'serif', fontWeight: '600', textAlign: 'center' },
  subtitle: { fontSize: 14, lineHeight: 20, textAlign: 'center', marginTop: 8, paddingHorizontal: 15 },
  scroll: { flex: 1, minHeight: 0 },
  list: { paddingBottom: 8 },
  option: { minHeight: 68, borderRadius: 18, borderWidth: 1, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, marginBottom: 9 },
  flag: { width: 39, fontSize: 23, lineHeight: Platform.OS === 'android' ? 31 : 28 },
  optionText: { flex: 1, fontSize: 18, fontFamily: 'serif', fontWeight: '600' },
  check: { width: 28, height: 28, borderRadius: 14, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  continueButton: { minHeight: 58, borderRadius: 999, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, marginTop: 12 },
  buttonText: { fontSize: 16, fontWeight: '800' },
});
