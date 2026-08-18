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
import { useCredits } from '../../credits/CreditContext';
import { useTranslation } from 'react-i18next';

const OPEN_DELAY_MS = 1600;

/**
 * Full-screen style reminder on the home dashboard (props.homeActive) for users
 * without notification permission. Android only (iOS push is skipped in App.js).
 */
export default function NotificationEnableReminderModal({
  homeActive,
  fomoTriggerNonce = 0,
  allowGeneralPrompt = false,
}) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const { fetchBalance } = useCredits();
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const [variant, setVariant] = useState('general');
  const timerRef = useRef(null);
  const handledFomoTriggerRef = useRef(0);

  useEffect(() => {
    // A generic permission wall during first paint damages trust. The app now
    // asks only after a contextual success moment unless explicitly enabled.
    if (!allowGeneralPrompt || !homeActive || Platform.OS === 'ios' || !Device.isDevice) {
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
  }, [allowGeneralPrompt, homeActive]);

  useEffect(() => {
    if (
      !fomoTriggerNonce
      || handledFomoTriggerRef.current === fomoTriggerNonce
      || Platform.OS === 'ios'
      || Platform.OS === 'web'
      || !Device.isDevice
    ) {
      return;
    }
    handledFomoTriggerRef.current = fomoTriggerNonce;
    let cancelled = false;
    const checkAndOpen = async () => {
      try {
        const { getPushPermissionStatusAsync } = require('../../services/pushNotifications');
        const status = await getPushPermissionStatusAsync();
        if (cancelled || status === 'granted') return;
        // This explicit contextual prompt owns the reminder slot, preventing the
        // generic delayed home reminder from appearing immediately afterwards.
        await recordReminderShown();
        if (cancelled) return;
        setVariant('fomo');
        setVisible(true);
      } catch (_) {
        /* A notification prompt must never interrupt navigation. */
      }
    };
    checkAndOpen();
    return () => {
      cancelled = true;
    };
  }, [fomoTriggerNonce]);

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
      await fetchBalance();
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

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      statusBarTranslucent
      onRequestClose={onNotNow}
    >
      <View style={[styles.overlay, { backgroundColor: colors.overlay }]}>
        <View style={[styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
          <View style={[styles.iconWrap, { backgroundColor: colors.accentSoft }]}>
            <Ionicons name="notifications-outline" size={30} color={colors.onAccent} />
          </View>
          <View style={[styles.rule, { backgroundColor: colors.accent }]} />
          <Text style={[styles.title, { color: colors.text }]}>
            {t('fomoHome.notificationTitle')}
          </Text>
          <Text style={[styles.body, { color: colors.textSecondary }]}>
            {t('fomoHome.notificationBody')}
          </Text>
          <TouchableOpacity
            style={[styles.primaryBtn, { backgroundColor: colors.primary }, busy && styles.btnDisabled]}
            onPress={onTurnOn}
            disabled={busy}
            activeOpacity={0.85}
          >
            {busy ? (
              <ActivityIndicator color={colors.onPrimary} />
            ) : (
              <Text style={[styles.primaryBtnText, { color: colors.onPrimary }]}>
                {t('fomoHome.notificationEnable')}
              </Text>
            )}
          </TouchableOpacity>
          <TouchableOpacity style={styles.secondaryBtn} onPress={onNotNow} disabled={busy}>
            <Text style={[styles.secondaryBtnText, { color: colors.textSecondary }]}>
              {t('fomoHome.notificationLater')}
            </Text>
          </TouchableOpacity>
          {variant !== 'fomo' ? (
            <TouchableOpacity style={styles.neverBtn} onPress={onNeverAgain} disabled={busy}>
              <Text style={[styles.neverBtnText, { color: colors.textSecondary }]}>{t('premiumUi.chat.dontAskAgain')}</Text>
            </TouchableOpacity>
          ) : null}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  card: {
    width: '100%',
    maxWidth: 400,
    borderRadius: 28,
    padding: 26,
    borderWidth: 1,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
  },
  iconWrap: {
    alignSelf: 'center',
    width: 58,
    height: 58,
    borderRadius: 29,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  rule: {
    alignSelf: 'center',
    width: 54,
    height: 2,
    borderRadius: 1,
    marginBottom: 18,
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
    paddingVertical: 14,
    borderRadius: 14,
    alignItems: 'center',
    marginBottom: 10,
  },
  primaryBtnText: {
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
