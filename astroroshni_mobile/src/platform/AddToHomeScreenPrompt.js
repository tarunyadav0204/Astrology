/**
 * Web-only "Add to Home Screen" / Install guide.
 * iOS Safari: Share → Add to Home Screen (no install API).
 * Android Chrome: do NOT hijack beforeinstallprompt — calling preventDefault()
 * hides Chrome's native Install UI. We only show instructions (⋮ → Install app).
 * Never mounts on native Play/iOS app builds (Platform.OS !== 'web').
 */
import React, { useEffect, useState } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Platform,
  Image,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Ionicons from '@expo/vector-icons/Ionicons';
import { LinearGradient } from 'expo-linear-gradient';
import { useTheme } from '../context/ThemeContext';

const DISMISS_KEY = 'ar_add_to_home_dismissed_v2';
const SNOOZE_KEY = 'ar_add_to_home_snooze_until_v2';
const SNOOZE_MS = 7 * 24 * 60 * 60 * 1000;
const SHOW_DELAY_MS = 1800;

function isStandaloneWebApp() {
  if (typeof window === 'undefined') return false;
  try {
    if (window.navigator?.standalone === true) return true;
    if (typeof window.matchMedia === 'function') {
      if (window.matchMedia('(display-mode: standalone)').matches) return true;
      if (window.matchMedia('(display-mode: fullscreen)').matches) return true;
    }
  } catch (_) {
    /* ignore */
  }
  return false;
}

function isIosWeb() {
  if (typeof navigator === 'undefined') return false;
  const ua = navigator.userAgent || '';
  const iPhoneLike = /iPad|iPhone|iPod/i.test(ua);
  const iPadOs = navigator.platform === 'MacIntel' && (navigator.maxTouchPoints || 0) > 1;
  return iPhoneLike || iPadOs;
}

function isAndroidWeb() {
  if (typeof navigator === 'undefined') return false;
  return /Android/i.test(navigator.userAgent || '');
}

/** Prefer /mobile production shell; allow local Expo web for testing. */
function shouldOfferOnThisPath() {
  if (typeof window === 'undefined') return false;
  const path = String(window.location?.pathname || '');
  if (/^\/mobile(\/|$)/.test(path)) return true;
  const host = String(window.location?.hostname || '');
  return host === 'localhost' || host === '127.0.0.1';
}

export default function AddToHomeScreenPrompt() {
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const [visible, setVisible] = useState(false);
  const [iosMode, setIosMode] = useState(true);

  useEffect(() => {
    if (Platform.OS !== 'web') return undefined;
    if (isStandaloneWebApp()) return undefined;
    if (!shouldOfferOnThisPath()) return undefined;

    const ios = isIosWeb();
    const android = isAndroidWeb();
    if (!ios && !android) return undefined;
    setIosMode(ios);

    let cancelled = false;
    let timer = null;

    (async () => {
      try {
        const dismissed = await AsyncStorage.getItem(DISMISS_KEY);
        if (dismissed === '1') return;
        const snoozeRaw = await AsyncStorage.getItem(SNOOZE_KEY);
        const snoozeUntil = snoozeRaw ? Number(snoozeRaw) : 0;
        if (Number.isFinite(snoozeUntil) && snoozeUntil > Date.now()) return;
      } catch (_) {
        /* show anyway */
      }
      if (cancelled) return;
      timer = setTimeout(() => {
        if (!cancelled && !isStandaloneWebApp()) setVisible(true);
      }, SHOW_DELAY_MS);
    })();

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, []);

  if (Platform.OS !== 'web') return null;

  const dismissForever = async () => {
    setVisible(false);
    try {
      await AsyncStorage.setItem(DISMISS_KEY, '1');
    } catch (_) {
      /* ignore */
    }
  };

  const snooze = async () => {
    setVisible(false);
    try {
      await AsyncStorage.setItem(SNOOZE_KEY, String(Date.now() + SNOOZE_MS));
    } catch (_) {
      /* ignore */
    }
  };

  const cardBg = isDark
    ? [colors.gradientStart || '#1a0033', colors.gradientMid || '#2d1b4e']
    : ['#ffffff', '#fff7ed'];

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={snooze}>
      <View style={styles.overlay}>
        <LinearGradient colors={cardBg} style={[styles.card, { borderColor: colors.cardBorder || 'rgba(0,0,0,0.08)' }]}>
          <View style={styles.logoWrap}>
            <Image source={require('../../assets/logo.png')} style={styles.logo} resizeMode="contain" />
          </View>
          <Text style={[styles.title, { color: colors.text }]}>
            {iosMode ? 'Add AstroRoshni to your Home Screen' : 'Install AstroRoshni'}
          </Text>
          <Text style={[styles.body, { color: colors.textSecondary }]}>
            {iosMode
              ? 'Apple does not allow astrology apps on the App Store. Save AstroRoshni like an app from Safari — it opens full-screen from your Home Screen.'
              : 'Save AstroRoshni from Chrome so it opens full-screen like an app. Use this exact page: astroroshni.com/mobile/'}
          </Text>

          {iosMode ? (
            <View style={[styles.steps, { backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(249,115,22,0.08)' }]}>
              <View style={styles.stepRow}>
                <View style={[styles.stepNum, { backgroundColor: colors.primary || '#f97316' }]}>
                  <Text style={styles.stepNumText}>1</Text>
                </View>
                <View style={styles.stepTextCol}>
                  <Text style={[styles.stepText, { color: colors.text }]}>
                    Tap the Share button in Safari (bottom center)
                  </Text>
                  <View style={styles.shareHint}>
                    <Ionicons name="share-outline" size={18} color={colors.primary || '#f97316'} />
                    <Text style={[styles.shareHintLabel, { color: colors.primary || '#f97316' }]}>Share</Text>
                  </View>
                </View>
              </View>
              <View style={styles.stepRow}>
                <View style={[styles.stepNum, { backgroundColor: colors.primary || '#f97316' }]}>
                  <Text style={styles.stepNumText}>2</Text>
                </View>
                <Text style={[styles.stepText, { color: colors.text }]}>
                  Scroll and tap <Text style={styles.stepEm}>Add to Home Screen</Text>
                </Text>
              </View>
              <View style={styles.stepRow}>
                <View style={[styles.stepNum, { backgroundColor: colors.primary || '#f97316' }]}>
                  <Text style={styles.stepNumText}>3</Text>
                </View>
                <Text style={[styles.stepText, { color: colors.text }]}>
                  Tap <Text style={styles.stepEm}>Add</Text> — AstroRoshni appears on your Home Screen
                </Text>
              </View>
            </View>
          ) : (
            <View style={[styles.steps, { backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(249,115,22,0.08)' }]}>
              <View style={styles.stepRow}>
                <View style={[styles.stepNum, { backgroundColor: colors.primary || '#f97316' }]}>
                  <Text style={styles.stepNumText}>1</Text>
                </View>
                <Text style={[styles.stepText, { color: colors.text }]}>
                  Open in <Text style={styles.stepEm}>Chrome</Text> (not WhatsApp/Instagram in-app browser)
                </Text>
              </View>
              <View style={styles.stepRow}>
                <View style={[styles.stepNum, { backgroundColor: colors.primary || '#f97316' }]}>
                  <Text style={styles.stepNumText}>2</Text>
                </View>
                <Text style={[styles.stepText, { color: colors.text }]}>
                  Tap the <Text style={styles.stepEm}>⋮</Text> menu (top right)
                </Text>
              </View>
              <View style={styles.stepRow}>
                <View style={[styles.stepNum, { backgroundColor: colors.primary || '#f97316' }]}>
                  <Text style={styles.stepNumText}>3</Text>
                </View>
                <Text style={[styles.stepText, { color: colors.text }]}>
                  Tap <Text style={styles.stepEm}>Install app</Text> or <Text style={styles.stepEm}>Add to Home screen</Text>
                </Text>
              </View>
              <Text style={[styles.androidNote, { color: colors.textSecondary }]}>
                If Install is missing, the Play Store app may already be installed — Chrome hides the PWA install then. You can still use Add to Home screen.
              </Text>
            </View>
          )}

          <TouchableOpacity
            style={[styles.primaryBtn, { backgroundColor: colors.primary || '#f97316' }]}
            onPress={dismissForever}
            activeOpacity={0.85}
          >
            <Text style={styles.primaryBtnText}>Got it</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.secondaryBtn} onPress={snooze} activeOpacity={0.7}>
            <Text style={[styles.secondaryBtnText, { color: colors.textSecondary }]}>Not now</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.linkBtn} onPress={dismissForever} activeOpacity={0.7}>
            <Text style={[styles.linkBtnText, { color: colors.textTertiary || colors.textSecondary }]}>
              Don’t ask again
            </Text>
          </TouchableOpacity>
        </LinearGradient>
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
    borderWidth: 1,
    paddingHorizontal: 22,
    paddingTop: 22,
    paddingBottom: 16,
  },
  logoWrap: {
    alignItems: 'center',
    marginBottom: 12,
  },
  logo: {
    width: 56,
    height: 56,
    borderRadius: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 10,
    letterSpacing: 0.2,
  },
  body: {
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
    marginBottom: 14,
  },
  steps: {
    borderRadius: 14,
    padding: 14,
    marginBottom: 16,
    gap: 12,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  stepNum: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  stepNumText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '800',
  },
  stepTextCol: {
    flex: 1,
  },
  stepText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },
  shareHint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 6,
  },
  shareHintLabel: {
    fontSize: 13,
    fontWeight: '700',
  },
  stepEm: {
    fontWeight: '800',
  },
  androidNote: {
    fontSize: 12,
    lineHeight: 17,
    marginTop: 2,
  },
  primaryBtn: {
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
  },
  primaryBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '800',
  },
  secondaryBtn: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  secondaryBtnText: {
    fontSize: 15,
    fontWeight: '600',
  },
  linkBtn: {
    paddingVertical: 4,
    alignItems: 'center',
  },
  linkBtnText: {
    fontSize: 13,
  },
});
