import React from 'react';
import { Linking, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

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
  return (
    <View style={[styles.container, compact && styles.containerCompact]}>
      <Text style={[styles.text, compact && styles.textCompact]}>
        By continuing, you agree to our{' '}
        <Text style={styles.link} onPress={() => openUrl(TERMS_URL)}>
          Terms of Service
        </Text>{' '}
        and{' '}
        <Text style={styles.link} onPress={() => openUrl(PRIVACY_URL)}>
          Privacy Policy
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
