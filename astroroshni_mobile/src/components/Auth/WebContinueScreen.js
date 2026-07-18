import React, { useEffect, useState } from 'react';
import { View, Text, ActivityIndicator, StyleSheet, Platform } from 'react-native';
import { useTheme } from '../../context/ThemeContext';
import { storage } from '../../services/storage';
import api from '../../services/api';
import { getEndpoint } from '../../utils/constants';
import { resetToRoute } from '../../navigation/navHelpers';

/**
 * Deep link landing: /mobile/c/:token
 * Exchanges reusable continue token for JWT and opens Credits.
 */
export default function WebContinueScreen({ route, navigation }) {
  const { colors } = useTheme();
  const token = String(route?.params?.token || '').trim();
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!token) {
        setError('This link is missing a login token.');
        return;
      }
      try {
        const { data } = await api.post(getEndpoint('/auth/web-continue'), { token });
        if (cancelled) return;
        if (!data?.access_token) {
          setError('Could not sign you in from this link.');
          return;
        }
        await storage.setAuthToken(data.access_token);
        if (data.user) {
          await storage.setUserData(data.user);
        }
        try {
          const { linkAcquisitionInstallationToUser } = require('../../services/acquisitionTracking');
          linkAcquisitionInstallationToUser().catch(() => {});
        } catch (_) {
          /* optional */
        }
        resetToRoute(navigation, 'Credits');
      } catch (e) {
        if (cancelled) return;
        const detail = e?.response?.data?.detail || e?.message || 'Invalid or expired link';
        setError(String(detail));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, navigation]);

  return (
    <View style={[styles.wrap, { backgroundColor: colors.background }]}>
      {error ? (
        <Text style={[styles.error, { color: colors.error || '#dc2626' }]}>{error}</Text>
      ) : (
        <>
          <ActivityIndicator size="large" color={colors.primary || '#f97316'} />
          <Text style={[styles.hint, { color: colors.textSecondary || colors.text }]}>
            Signing you in…
          </Text>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    minHeight: Platform.OS === 'web' ? '100vh' : undefined,
  },
  hint: {
    marginTop: 16,
    fontSize: 16,
    textAlign: 'center',
  },
  error: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 22,
    maxWidth: 360,
  },
});
