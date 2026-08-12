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
import { useTranslation } from 'react-i18next';
import {
  shouldShowContextualPushReminder,
  recordContextualReminderShown,
} from '../../services/notificationReminder';

const COPY_KEYS = {
  report_ready: {
    title: 'premiumUi.chat.notifyReportTitle',
    body: 'premiumUi.chat.notifyReportBody',
  },
  chat_answer: {
    title: 'premiumUi.chat.notifyAnswerTitle',
    body: 'premiumUi.chat.notifyAnswerBody',
  },
  generic: {
    title: 'premiumUi.chat.notifyGenericTitle',
    body: 'premiumUi.chat.notifyGenericBody',
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
  const { colors } = useTheme();
  const { t } = useTranslation();
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

  const copyKeys = COPY_KEYS[reason] || COPY_KEYS.generic;
  const copy = { title: t(copyKeys.title), body: t(copyKeys.body) };
  return (
    <View
      style={[
        styles.wrap,
        {
          backgroundColor: colors.surface,
          borderColor: colors.cardBorder,
        },
        style,
      ]}
    >
      <View style={[styles.iconWrap, { backgroundColor: colors.accentSoft }]}>
        <Ionicons name="notifications-outline" size={18} color={colors.onAccent} />
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
            style={[styles.primaryBtn, { backgroundColor: colors.primary }]}
            onPress={onTurnOn}
            disabled={busy}
            activeOpacity={0.85}
          >
            {busy ? (
              <ActivityIndicator size="small" color={colors.onPrimary} />
            ) : (
              <Text style={[styles.primaryText, { color: colors.onPrimary }]}>{t('premiumUi.chat.enableAlerts')}</Text>
            )}
          </TouchableOpacity>
          <TouchableOpacity onPress={dismiss} disabled={busy} hitSlop={8}>
            <Text style={[styles.secondaryText, { color: colors.textSecondary }]}>{t('chat.insufficientCreditsLater')}</Text>
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
    borderRadius: 20,
    paddingHorizontal: 13,
    paddingVertical: 12,
    marginBottom: 10,
    gap: 11,
  },
  iconWrap: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  textWrap: {
    flex: 1,
  },
  title: {
    fontSize: 15,
    fontWeight: '800',
    marginBottom: 3,
  },
  body: {
    fontSize: 12,
    lineHeight: 17,
    marginBottom: 9,
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  primaryBtn: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 999,
    minWidth: 102,
    alignItems: 'center',
  },
  primaryText: {
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
