import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Platform,
  Alert,
  ActivityIndicator,
  Linking,
} from 'react-native';
import * as Device from 'expo-device';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { useCredits } from '../../credits/CreditContext';
import {
  shouldShowContextualPushReminder,
  recordContextualReminderShown,
} from '../../services/notificationReminder';

const COPY = {
  report_ready: {
    title: 'Get alerted next time',
    body: 'Turn on notifications and we’ll ping you when a report is ready.',
  },
  chat_answer: {
    title: 'Don’t miss the next answer',
    body: 'Turn on notifications so we can alert you when a reply is ready.',
  },
  generic: {
    title: 'Stay in the loop',
    body: 'Turn on notifications for chart reviews, chat updates, and offers.',
  },
};

/**
 * Compact inline banner for high-value moments (report ready / chat answer).
 * Android only — matches Home modal policy while iOS push is skipped.
 */
export default function NotificationEnableBanner({
  reason = 'generic',
  active = false,
  style,
}) {
  const { theme, colors } = useTheme();
  const { fetchBalance } = useCredits();
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const checkedRef = useRef(false);

  useEffect(() => {
    if (!active || Platform.OS === 'ios' || !Device.isDevice) {
      setVisible(false);
      return;
    }
    if (checkedRef.current) return;
    checkedRef.current = true;

    let cancelled = false;
    (async () => {
      try {
        const show = await shouldShowContextualPushReminder(reason);
        if (!cancelled && show) {
          setVisible(true);
          await recordContextualReminderShown(reason);
        }
      } catch (_) {
        /* ignore */
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [active, reason]);

  const dismiss = useCallback(() => {
    setVisible(false);
  }, []);

  const onTurnOn = useCallback(async () => {
    setBusy(true);
    try {
      const {
        getPushPermissionStatusAsync,
        registerPushTokenIfLoggedIn,
      } = require('../../services/pushNotifications');
      const status = await getPushPermissionStatusAsync();
      if (status === 'denied') {
        dismiss();
        Alert.alert(
          'Notifications',
          'Notifications are blocked for AstroRoshni. Open Settings to allow them.',
          [
            { text: 'Not now', style: 'cancel' },
            { text: 'Open Settings', onPress: () => Linking.openSettings() },
          ]
        );
        return;
      }
      const result = await registerPushTokenIfLoggedIn();
      dismiss();
      await fetchBalance();
      if (!result.ok) {
        if (String(result.message || '').toLowerCase().includes('turned off')) {
          Alert.alert(
            'Notifications',
            result.message,
            [
              { text: 'Not now', style: 'cancel' },
              { text: 'Open Settings', onPress: () => Linking.openSettings() },
            ]
          );
        } else {
          Alert.alert('Notifications', result.message);
        }
      }
    } catch (e) {
      dismiss();
      Alert.alert(
        'Notifications',
        e?.message || 'Something went wrong. You can enable notifications anytime in Profile.'
      );
    } finally {
      setBusy(false);
    }
  }, [dismiss, fetchBalance]);

  if (!visible) return null;

  const copy = COPY[reason] || COPY.generic;
  const isDark = theme === 'dark';

  return (
    <View
      style={[
        styles.wrap,
        {
          backgroundColor: isDark ? 'rgba(249,115,22,0.14)' : 'rgba(249,115,22,0.1)',
          borderColor: isDark ? 'rgba(249,115,22,0.35)' : 'rgba(249,115,22,0.28)',
        },
        style,
      ]}
    >
      <View style={styles.iconWrap}>
        <Ionicons name="notifications-outline" size={18} color="#f97316" />
      </View>
      <View style={styles.textWrap}>
        <Text style={[styles.title, { color: colors.text }]} numberOfLines={1}>
          {copy.title}
        </Text>
        <Text style={[styles.body, { color: colors.textSecondary }]} numberOfLines={2}>
          {copy.body}
        </Text>
        <View style={styles.actions}>
          <TouchableOpacity
            style={styles.primaryBtn}
            onPress={onTurnOn}
            disabled={busy}
            activeOpacity={0.85}
          >
            {busy ? (
              <ActivityIndicator size="small" color="#0f172a" />
            ) : (
              <Text style={styles.primaryText}>Turn on</Text>
            )}
          </TouchableOpacity>
          <TouchableOpacity onPress={dismiss} disabled={busy} hitSlop={8}>
            <Text style={[styles.secondaryText, { color: colors.textSecondary }]}>Not now</Text>
          </TouchableOpacity>
        </View>
      </View>
      <TouchableOpacity onPress={dismiss} disabled={busy} hitSlop={10} style={styles.closeBtn}>
        <Ionicons name="close" size={16} color={colors.textSecondary} />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    borderWidth: 1,
    borderRadius: 14,
    padding: 12,
    marginBottom: 12,
    gap: 10,
  },
  iconWrap: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: 'rgba(249,115,22,0.16)',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  textWrap: {
    flex: 1,
  },
  title: {
    fontSize: 14,
    fontWeight: '800',
    marginBottom: 2,
  },
  body: {
    fontSize: 12,
    lineHeight: 17,
    marginBottom: 8,
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  primaryBtn: {
    backgroundColor: '#f97316',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 10,
    minWidth: 76,
    alignItems: 'center',
  },
  primaryText: {
    color: '#0f172a',
    fontSize: 13,
    fontWeight: '800',
  },
  secondaryText: {
    fontSize: 13,
    fontWeight: '600',
  },
  closeBtn: {
    padding: 2,
  },
});
