import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Platform, StatusBar, Linking } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import Constants from 'expo-constants';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';

export default function AboutScreen({ navigation }) {
  const { theme, colors } = useTheme();
  const { t } = useTranslation();

  const appVersion = Constants.expoConfig?.version || '1.0.0';
  const androidCode = Constants.expoConfig?.android?.versionCode;
  const iosBuild = Constants.expoConfig?.ios?.buildNumber;
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

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme === 'dark' ? '#020617' : colors.background }]}>
      <StatusBar barStyle={theme === 'dark' ? 'light-content' : 'dark-content'} backgroundColor="#ff6b35" />
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: colors.text }]}>{t('about.title', 'About AstroRoshni')}</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={[styles.card, { backgroundColor: theme === 'dark' ? 'rgba(15,23,42,0.9)' : colors.surface, borderColor: colors.border }]}>
          <View style={styles.logoRow}>
            <View style={[styles.logoBadge, { backgroundColor: '#f97316' }]}>
              <Text style={styles.logoText}>AR</Text>
            </View>
            <View>
              <Text style={[styles.appName, { color: colors.text }]}>AstroRoshni</Text>
              <Text style={[styles.versionText, { color: colors.textSecondary }]}>{versionLine}</Text>
            </View>
          </View>
          <Text style={[styles.description, { color: colors.textSecondary }]}>
            {t(
              'about.description',
              'AstroRoshni combines Vedic astrology with intelligent guidance to help you understand your life path, timing, and hidden potentials.'
            )}
          </Text>
        </View>

        <View style={[styles.card, { backgroundColor: theme === 'dark' ? 'rgba(15,23,42,0.9)' : colors.surface, borderColor: colors.border }]}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('about.legalHeading', 'Legal & Policies')}</Text>
          <TouchableOpacity
            style={styles.rowItem}
            onPress={() => handleOpenUrl('https://astroroshni.com/privacy')}
          >
            <Text style={[styles.rowText, { color: colors.text }]}>{t('about.privacyPolicy', 'Privacy Policy')}</Text>
            <Ionicons name="chevron-forward" size={18} color={colors.textSecondary} />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.rowItem}
            onPress={() => handleOpenUrl('https://astroroshni.com/terms')}
          >
            <Text style={[styles.rowText, { color: colors.text }]}>{t('about.termsOfService', 'Terms of Service')}</Text>
            <Ionicons name="chevron-forward" size={18} color={colors.textSecondary} />
          </TouchableOpacity>
        </View>

        <View style={[styles.card, { backgroundColor: theme === 'dark' ? 'rgba(15,23,42,0.9)' : colors.surface, borderColor: colors.border }]}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('about.supportHeading', 'Support')}</Text>
          <TouchableOpacity
            style={styles.rowItem}
            onPress={() => handleOpenUrl('mailto:support@astroroshni.com?subject=AstroRoshni%20Support')}
          >
            <Text style={[styles.rowText, { color: colors.text }]}>{t('about.contactSupport', 'Contact support')}</Text>
            <Ionicons name="chevron-forward" size={18} color={colors.textSecondary} />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.rowItem}
            onPress={() => handleOpenUrl('https://astroroshni.com')}
          >
            <Text style={[styles.rowText, { color: colors.text }]}>{t('about.visitWebsite', 'Visit website')}</Text>
            <Ionicons name="chevron-forward" size={18} color={colors.textSecondary} />
          </TouchableOpacity>
        </View>

        <View style={{ height: 32 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
  },
  content: {
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  card: {
    borderRadius: 18,
    padding: 18,
    marginBottom: 16,
    borderWidth: 1,
  },
  logoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 12,
  },
  logoBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 18,
  },
  appName: {
    fontSize: 20,
    fontWeight: '700',
  },
  versionText: {
    fontSize: 13,
    marginTop: 2,
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 8,
  },
  rowItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
  },
  rowText: {
    fontSize: 14,
  },
});

