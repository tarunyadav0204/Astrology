import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Platform, StatusBar, Linking, Alert, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import Constants from 'expo-constants';
import * as Application from 'expo-application';
import * as Sentry from '@sentry/react-native';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { isSentryInitialized } from '../../services/instrumentSentry';

export default function AboutScreen({ navigation }) {
  const { colors } = useTheme();
  const { t } = useTranslation();

  const appVersion = Application.nativeApplicationVersion || Constants.expoConfig?.version || '1.0.0';
  const androidCode = Number(Application.nativeBuildVersion || Constants.expoConfig?.android?.versionCode || 0) || undefined;
  const iosBuild = Application.nativeBuildVersion || Constants.expoConfig?.ios?.buildNumber;
  const platform = Platform.OS;

  const versionLine =
    platform === 'android' && androidCode
      ? t('about.versionWithCode', { version: appVersion, code: androidCode })
      : platform === 'ios' && iosBuild
      ? t('about.versionWithBuild', { version: appVersion, build: iosBuild })
      : t('about.version', { version: appVersion });

  const handleOpenUrl = (url) => {
    try {
      if (url) Linking.openURL(url);
    } catch (e) {
      // ignore
    }
  };

  const sendTestSentryIssue = async () => {
    if (!isSentryInitialized()) {
      Alert.alert('Sentry', 'SDK not initialized (missing DSN in this build).');
      return;
    }
    try {
      Sentry.captureException(new Error('AstroRoshni AboutScreen Sentry test (dev-only)'));
    } catch (_) {
      /* ignore */
    }
    try {
      await Sentry.flush(2000);
    } catch (_) {
      /* ignore */
    }
    Alert.alert(
      'Sentry',
      'Test error queued. Open Sentry → Issues (filter: unresolved). It can take 10–30 seconds.'
    );
  };

  return (
    <SafeAreaView edges={['top']} style={[styles.container, { backgroundColor: colors.headerSurface }]}>
      <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} />
      <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine }]}>
        <TouchableOpacity
          onPress={() => navigation.goBack()}
          style={[styles.backButton, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}
          accessibilityRole="button"
          accessibilityLabel={t('common.back', 'Back')}
        >
          <Ionicons name="arrow-back" size={22} color={colors.textInverse} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: colors.textInverse }]}>{t('about.title', 'About AstroRoshni')}</Text>
        <View style={{ width: 40 }} />
      </View>

      <View style={[styles.body, { backgroundColor: colors.background }]}>
        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={[styles.hero, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
          <View style={[styles.orbit, styles.orbitLarge, { borderColor: colors.cosmicLine }]} />
          <View style={[styles.orbit, styles.orbitSmall, { borderColor: colors.cosmicLine }]} />
          <View style={styles.heroTopline}>
            <View style={[styles.heroRule, { backgroundColor: colors.accent }]} />
            <Text style={[styles.heroEyebrow, { color: colors.accent }]}>ASTROROSHNI</Text>
          </View>
          <View style={styles.logoRow}>
            <View style={[styles.logoBadge, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}>
              <Image source={require('../../../assets/logo.png')} style={styles.logoImage} resizeMode="cover" />
            </View>
            <View style={styles.brandCopy}>
              <Text style={[styles.appName, { color: colors.textInverse }]}>AstroRoshni</Text>
              <Text style={[styles.versionText, { color: colors.textInverseMuted }]}>{versionLine}</Text>
            </View>
          </View>
          <Text style={[styles.heroDescription, { color: colors.textInverseMuted }]}>
            {t(
              'about.description',
              'AstroRoshni combines Vedic astrology with intelligent guidance to help you understand your life path, timing, and hidden potentials.'
            )}
          </Text>
        </View>

        <View style={styles.sectionHeading}>
          <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{t('about.legalHeading', 'Legal & Policies')}</Text>
          <View style={[styles.sectionLine, { backgroundColor: colors.cardBorder }]} />
        </View>
        <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
          <TouchableOpacity
            style={[styles.rowItem, { borderBottomColor: colors.cardBorder }]}
            onPress={() => handleOpenUrl('https://astroroshni.com/policy')}
          >
            <View style={[styles.rowIcon, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
              <Ionicons name="shield-checkmark-outline" size={20} color={colors.primary} />
            </View>
            <Text style={[styles.rowText, { color: colors.text }]}>{t('about.privacyPolicy', 'Privacy Policy')}</Text>
            <View style={[styles.rowArrow, { borderColor: colors.cardBorder }]}>
              <Ionicons name="arrow-forward" size={17} color={colors.primary} />
            </View>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.rowItem, styles.rowItemLast]}
            onPress={() => handleOpenUrl('https://astroroshni.com/terms')}
          >
            <View style={[styles.rowIcon, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
              <Ionicons name="document-text-outline" size={20} color={colors.primary} />
            </View>
            <Text style={[styles.rowText, { color: colors.text }]}>{t('about.termsOfService', 'Terms of Service')}</Text>
            <View style={[styles.rowArrow, { borderColor: colors.cardBorder }]}>
              <Ionicons name="arrow-forward" size={17} color={colors.primary} />
            </View>
          </TouchableOpacity>
        </View>

        <View style={styles.sectionHeading}>
          <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{t('about.supportHeading', 'Support')}</Text>
          <View style={[styles.sectionLine, { backgroundColor: colors.cardBorder }]} />
        </View>
        <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
          <TouchableOpacity
            style={[styles.rowItem, { borderBottomColor: colors.cardBorder }]}
            onPress={() => handleOpenUrl('mailto:help@astroroshni.com?subject=AstroRoshni%20Support')}
          >
            <View style={[styles.rowIcon, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
              <Ionicons name="mail-outline" size={20} color={colors.primary} />
            </View>
            <Text style={[styles.rowText, { color: colors.text }]}>{t('about.contactSupport', 'Contact support')}</Text>
            <View style={[styles.rowArrow, { borderColor: colors.cardBorder }]}>
              <Ionicons name="arrow-forward" size={17} color={colors.primary} />
            </View>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.rowItem, styles.rowItemLast]}
            onPress={() => handleOpenUrl('https://astroroshni.com')}
          >
            <View style={[styles.rowIcon, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
              <Ionicons name="globe-outline" size={20} color={colors.primary} />
            </View>
            <Text style={[styles.rowText, { color: colors.text }]}>{t('about.visitWebsite', 'Visit website')}</Text>
            <View style={[styles.rowArrow, { borderColor: colors.cardBorder }]}>
              <Ionicons name="arrow-forward" size={17} color={colors.primary} />
            </View>
          </TouchableOpacity>
        </View>

        {__DEV__ ? (
          <View style={[styles.card, styles.developerCard, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>Developer</Text>
            <Text style={[styles.description, { color: colors.textSecondary, marginBottom: 12 }]}>
              Sends one test error to Sentry so you can confirm the Issues tab. Remove this block before shipping if you prefer.
            </Text>
            <TouchableOpacity
              style={[styles.rowItem, styles.developerAction, { backgroundColor: colors.surfaceMuted, borderColor: colors.error }]}
              onPress={sendTestSentryIssue}
            >
              <Text style={[styles.rowText, { color: colors.text, fontWeight: '600' }]}>Send test Sentry issue</Text>
              <Ionicons name="bug-outline" size={20} color={colors.error} />
            </TouchableOpacity>
          </View>
        ) : null}

          <View style={{ height: 32 }} />
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  body: {
    flex: 1,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 18,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif', default: 'serif' }),
    fontSize: 21,
    fontWeight: '600',
  },
  content: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 30,
  },
  hero: {
    minHeight: 300,
    borderRadius: 30,
    padding: 24,
    marginBottom: 28,
    borderWidth: 1,
    overflow: 'hidden',
    justifyContent: 'flex-end',
  },
  orbit: {
    position: 'absolute',
    borderWidth: 1,
    borderRadius: 999,
  },
  orbitLarge: {
    width: 250,
    height: 250,
    right: -110,
    top: -105,
  },
  orbitSmall: {
    width: 170,
    height: 170,
    right: -65,
    top: -68,
  },
  heroTopline: {
    position: 'absolute',
    top: 25,
    left: 24,
    flexDirection: 'row',
    alignItems: 'center',
  },
  heroRule: {
    width: 28,
    height: 1,
    marginRight: 10,
  },
  heroEyebrow: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 2.2,
  },
  card: {
    borderRadius: 24,
    paddingHorizontal: 17,
    marginBottom: 25,
    borderWidth: 1,
    overflow: 'hidden',
  },
  logoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 18,
  },
  logoBadge: {
    width: 64,
    height: 64,
    borderRadius: 19,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    marginRight: 15,
  },
  logoImage: {
    width: 62,
    height: 62,
    borderRadius: 18,
  },
  brandCopy: {
    flex: 1,
  },
  appName: {
    fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif', default: 'serif' }),
    fontSize: 31,
    lineHeight: 35,
    fontWeight: '600',
  },
  versionText: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.35,
    marginTop: 5,
  },
  heroDescription: {
    fontSize: 15,
    lineHeight: 23,
    maxWidth: 450,
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
    marginTop: 4,
  },
  sectionHeading: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 11,
    paddingHorizontal: 2,
  },
  sectionEyebrow: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.8,
    textTransform: 'uppercase',
  },
  sectionLine: {
    flex: 1,
    height: StyleSheet.hairlineWidth,
    marginLeft: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginTop: 17,
    marginBottom: 8,
  },
  rowItem: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 72,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  rowItemLast: {
    borderBottomWidth: 0,
  },
  rowText: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    marginHorizontal: 13,
  },
  rowIcon: {
    width: 40,
    height: 40,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rowArrow: {
    width: 34,
    height: 34,
    borderRadius: 17,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  developerCard: {
    paddingBottom: 17,
  },
  developerAction: {
    minHeight: 54,
    borderBottomWidth: 1,
    borderWidth: 1,
    borderRadius: 16,
    paddingHorizontal: 13,
  },
});
