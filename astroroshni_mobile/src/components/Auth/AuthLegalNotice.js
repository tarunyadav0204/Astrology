import React from 'react';
import { Linking, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';

const TERMS_URL = 'https://astroroshni.com/terms';
const PRIVACY_URL = 'https://astroroshni.com/policy';

function openUrl(url) {
  try {
    Linking.openURL(url);
  } catch (_) {
    // ignore
  }
}

export default function AuthLegalNotice({ compact = false }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  return (
    <View style={[styles.container, compact && styles.containerCompact]}>
      <Text style={[styles.text, { color: colors.textInverseMuted }, compact && styles.textCompact]}>
        {t('authOnboarding.legalPrefix', 'By continuing, you agree to our')}{' '}
        <Text style={[styles.link, { color: colors.accent }]} onPress={() => openUrl(TERMS_URL)}>
          {t('authOnboarding.terms', 'Terms of Service')}
        </Text>{' '}
        {t('authOnboarding.and', 'and')}{' '}
        <Text style={[styles.link, { color: colors.accent }]} onPress={() => openUrl(PRIVACY_URL)}>
          {t('authOnboarding.privacy', 'Privacy Policy')}
        </Text>
        .
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    paddingHorizontal: 12,
  },
  containerCompact: {
    paddingHorizontal: 6,
  },
  text: {
    color: 'rgba(255, 255, 255, 0.62)',
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
  },
  textCompact: {
    fontSize: 11,
    lineHeight: 16,
  },
  link: {
    color: '#ffb088',
    textDecorationLine: 'underline',
    fontWeight: '700',
  },
});
