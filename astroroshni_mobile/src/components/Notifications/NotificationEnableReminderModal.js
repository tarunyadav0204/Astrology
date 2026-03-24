import React, { useEffect, useRef, useState } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import * as Device from 'expo-device';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import {
  shouldShowPushReminder,
  recordReminderShown,
  recordReminderDeclinedForever,
} from '../../services/notificationReminder';

const OPEN_DELAY_MS = 1600;

/**
 * Full-screen style reminder on the home dashboard (props.homeActive) for users
 * without notification permission. Android only (iOS push is skipped in App.js).
 */
export default function NotificationEnableReminderModal({ homeActive }) {
  const { theme, colors } = useTheme();
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!homeActive || Platform.OS === 'ios' || !Device.isDevice) {
      if (timerRef.current) clearTimeout(timerRef.current);
      setVisible(false);
      return;
    }

    let cancelled = false;
    timerRef.current = setTimeout(async () => {
      if (cancelled) return;
      try {
        const show = await shouldShowPushReminder();
        if (cancelled) return;
        if (show) setVisible(true);
      } catch (_) {
        /* ignore */
      }
    }, OPEN_DELAY_MS);

    return () => {
      cancelled = true;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [homeActive]);

  const close = () => setVisible(false);

  const onNotNow = async () => {
    await recordReminderShown();
    close();
  };

  const onNeverAgain = async () => {
    await recordReminderDeclinedForever();
    close();
  };

  const onTurnOn = async () => {
    setBusy(true);
    try {
      const { registerPushTokenIfLoggedIn } = require('../../services/pushNotifications');
      const result = await registerPushTokenIfLoggedIn();
      await recordReminderShown();
      close();
      if (!result.ok) {
        Alert.alert('Notifications', result.message);
      }
    } catch (e) {
      await recordReminderShown();
      close();
      Alert.alert('Notifications', e?.message || 'Something went wrong. You can enable notifications anytime in Profile.');
    } finally {
      setBusy(false);
    }
  };

  const cardBg = theme === 'dark' ? colors.cardBackground || '#1e293b' : '#ffffff';
  const borderColor = colors.cardBorder || 'rgba(0,0,0,0.08)';

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      statusBarTranslucent
      onRequestClose={onNotNow}
    >
      <View style={styles.overlay}>
        <View style={[styles.card, { backgroundColor: cardBg, borderColor }]}>
          <View style={styles.iconWrap}>
            <Ionicons name="notifications" size={36} color="#ff6b35" />
          </View>
          <Text style={[styles.title, { color: colors.text }]}>Never miss what matters</Text>
          <Text style={[styles.body, { color: colors.textSecondary }]}>
            Turn on notifications to get a ping when your readings, chat updates, or special offers are ready — so
            you don't miss them by accident.
          </Text>
          <TouchableOpacity
            style={[styles.primaryBtn, busy && styles.btnDisabled]}
            onPress={onTurnOn}
            disabled={busy}
            activeOpacity={0.85}
          >
            {busy ? (
              <ActivityIndicator color="#0f172a" />
            ) : (
              <Text style={styles.primaryBtnText}>Turn on notifications</Text>
            )}
          </TouchableOpacity>
          <TouchableOpacity style={styles.secondaryBtn} onPress={onNotNow} disabled={busy}>
            <Text style={[styles.secondaryBtnText, { color: colors.textSecondary }]}>Not now</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.neverBtn} onPress={onNeverAgain} disabled={busy}>
            <Text style={[styles.neverBtnText, { color: colors.textSecondary }]}>Don't ask again</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.55)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  card: {
    width: '100%',
    maxWidth: 400,
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
  },
  iconWrap: {
    alignSelf: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 10,
  },
  body: {
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
    marginBottom: 22,
  },
  primaryBtn: {
    backgroundColor: '#ff6b35',
    paddingVertical: 14,
    borderRadius: 14,
    alignItems: 'center',
    marginBottom: 10,
  },
  primaryBtnText: {
    color: '#0f172a',
    fontSize: 16,
    fontWeight: '800',
  },
  btnDisabled: {
    opacity: 0.7,
  },
  secondaryBtn: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  secondaryBtnText: {
    fontSize: 15,
    fontWeight: '600',
  },
  neverBtn: {
    paddingVertical: 8,
    alignItems: 'center',
  },
  neverBtnText: {
    fontSize: 13,
    fontWeight: '500',
  },
});
