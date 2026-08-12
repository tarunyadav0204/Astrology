import React, { useEffect, useRef } from 'react';
import { Animated, Image, Platform, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../../context/ThemeContext';
import { trackAcquisitionFunnelEvent } from '../../../services/acquisitionTracking';
import AuthLegalNotice from '../AuthLegalNotice';

export default function WelcomeScreen({ navigateToScreen, setIsLogin, navigation }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const entrance = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    trackAcquisitionFunnelEvent('auth_welcome_viewed', {}, { screenName: 'WelcomeScreen' }).catch(() => {});
    Animated.spring(entrance, { toValue: 1, tension: 38, friction: 9, useNativeDriver: true }).start();
  }, [entrance]);

  const choose = (login) => {
    trackAcquisitionFunnelEvent('auth_mode_selected', { mode: login ? 'login' : 'register' }, { status: 'selected', screenName: 'WelcomeScreen' }).catch(() => {});
    setIsLogin(login);
    navigateToScreen('phone');
  };

  const canLeaveToRoot = typeof navigation?.canGoBack === 'function' && navigation.canGoBack();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
      <View style={styles.topBar}>
        {canLeaveToRoot ? (
          <TouchableOpacity style={[styles.backButton, { borderColor: colors.cosmicLine }]} onPress={() => navigation.goBack()} accessibilityLabel={t('common.back', 'Back')}>
            <Ionicons name="arrow-back" size={23} color={colors.textInverse} />
          </TouchableOpacity>
        ) : <View style={styles.backButton} />}
        <View style={styles.brand}>
          <Image source={require('../../../../assets/logo.png')} style={styles.brandLogo} />
          <Text style={[styles.brandName, { color: colors.textInverse }]}>{t('about.title', 'About AstroRoshni').replace(/^About\s+/i, '')}</Text>
        </View>
        <View style={styles.backButton} />
      </View>

      <Animated.View style={[styles.hero, { borderColor: colors.cosmicLine, opacity: entrance, transform: [{ translateY: entrance.interpolate({ inputRange: [0, 1], outputRange: [30, 0] }) }] }]}>
        <View style={[styles.orbit, styles.orbitLarge, { borderColor: colors.cosmicLine }]} />
        <View style={[styles.orbit, styles.orbitSmall, { borderColor: colors.cosmicLine }]} />
        <Text style={[styles.eyebrow, { color: colors.accent }]}>{t('authOnboarding.welcomeEyebrow', 'YOUR VEDIC GUIDE')}</Text>
        <Text style={[styles.title, { color: colors.textInverse }]}>{t('authOnboarding.welcomeHero', 'Meet Tara.\nRead your life.')}</Text>
        <Text style={[styles.subtitle, { color: colors.textInverseMuted }]}>{t('authOnboarding.welcomeHeroBody', 'Your complete chart—synthesized through Parashari, Nadi, Jaimini and KP—then translated into clear guidance.')}</Text>

        <View style={styles.proofRow}>
          <View style={[styles.proof, { borderColor: colors.cosmicLine }]}><Text style={[styles.proofValue, { color: colors.textInverse }]}>90+</Text><Text style={[styles.proofLabel, { color: colors.textInverseMuted }]}>{t('authOnboarding.analysisLayers', 'analysis layers')}</Text></View>
          <View style={[styles.proof, { borderColor: colors.cosmicLine }]}><Text style={[styles.proofValue, { color: colors.textInverse }]}>4</Text><Text style={[styles.proofLabel, { color: colors.textInverseMuted }]}>{t('authOnboarding.vedicSystems', 'Vedic systems')}</Text></View>
        </View>
      </Animated.View>

      <View style={styles.actions}>
        <TouchableOpacity style={[styles.primary, { backgroundColor: colors.accent }]} onPress={() => choose(false)} activeOpacity={0.9}>
          <Text style={[styles.primaryText, { color: colors.onAccent }]}>{t('authOnboarding.createAccount', 'Create account')}</Text>
          <Ionicons name="arrow-forward" size={19} color={colors.onAccent} />
        </TouchableOpacity>
        <TouchableOpacity style={[styles.secondary, { borderColor: colors.cosmicLine }]} onPress={() => choose(true)} activeOpacity={0.86}>
          <Text style={[styles.secondaryText, { color: colors.textInverse }]}>{t('authOnboarding.signIn', 'Sign in')}</Text>
        </TouchableOpacity>
      </View>
      <AuthLegalNotice />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, ...(Platform.OS === 'web' ? { minHeight: 0 } : null) },
  scrollContent: { flexGrow: 1, paddingHorizontal: 20, paddingTop: 8, paddingBottom: 28 },
  topBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 },
  backButton: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', borderWidth: 1 },
  brand: { flexDirection: 'row', alignItems: 'center', gap: 9 },
  brandLogo: { width: 38, height: 38, borderRadius: 10 },
  brandName: { fontSize: 21, fontFamily: 'serif', fontWeight: '600' },
  hero: { flex: 1, minHeight: 430, borderRadius: 32, borderWidth: 1, padding: 28, justifyContent: 'flex-end', overflow: 'hidden' },
  orbit: { position: 'absolute', borderWidth: 1, borderRadius: 999 },
  orbitLarge: { width: 330, height: 330, right: -165, top: -126 },
  orbitSmall: { width: 224, height: 224, right: -91, top: -76 },
  eyebrow: { fontSize: 12, letterSpacing: 2.4, fontWeight: '800', marginBottom: 13 },
  title: { fontSize: 48, lineHeight: 51, fontFamily: 'serif', fontWeight: '600', maxWidth: 315 },
  subtitle: { fontSize: 15, lineHeight: 23, marginTop: 19, maxWidth: 330 },
  proofRow: { flexDirection: 'row', gap: 10, marginTop: 26 },
  proof: { flex: 1, borderWidth: 1, borderRadius: 18, paddingHorizontal: 14, paddingVertical: 12 },
  proofValue: { fontSize: 22, fontFamily: 'serif', fontWeight: '700' },
  proofLabel: { fontSize: 11, lineHeight: 15, marginTop: 2 },
  actions: { gap: 11, paddingTop: 18, paddingBottom: 16 },
  primary: { minHeight: 58, borderRadius: 999, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9 },
  primaryText: { fontSize: 16, fontWeight: '800' },
  secondary: { minHeight: 56, borderRadius: 999, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  secondaryText: { fontSize: 16, fontWeight: '800' },
});
