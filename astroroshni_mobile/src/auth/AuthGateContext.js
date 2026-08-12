import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import {
  clearPendingPaidAction,
  getAuthTokenSafe,
  isGuestSession,
  setPendingPaidAction,
} from './guestAuth';
import { trackGA4EventOnly } from '../utils/analytics';
import { trackAcquisitionFunnelEvent, trackGuestActivity } from '../services/acquisitionTracking';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { DISPLAY_FONT_FAMILY } from '../theme/tokens';

const AuthGateContext = createContext({
  isGuest: true,
  refreshAuthState: async () => {},
  requireAuthForPaid: async () => false,
  openAuthGate: () => {},
  closeAuthGate: () => {},
});

export function AuthGateProvider({ children }) {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { theme, colors } = useTheme();
  const { t } = useTranslation();
  const isDark = theme === 'dark';
  const [isGuest, setIsGuest] = useState(true);
  const [visible, setVisible] = useState(false);
  const [gateMeta, setGateMeta] = useState({
    feature: '',
    message: '',
  });

  const refreshAuthState = useCallback(async () => {
    const guest = await isGuestSession();
    setIsGuest(guest);
    return guest;
  }, []);

  useEffect(() => {
    refreshAuthState();
  }, [refreshAuthState]);

  const closeAuthGate = useCallback(() => {
    setVisible(false);
  }, []);

  const openAuthGate = useCallback((meta = {}) => {
    setGateMeta({
      feature: meta.feature || t('authGate.featureCredits', 'this feature'),
      message: meta.message || t('authGate.defaultMessage'),
    });
    setVisible(true);
    trackGA4EventOnly('auth_gate_shown', {
      feature: meta.feature || 'unknown',
    }).catch(() => {});
    trackGuestActivity('auth_gate_shown').catch(() => {});
    trackAcquisitionFunnelEvent(
      'auth_gate_shown',
      { feature: meta.feature || 'unknown' },
      { status: 'shown', screenName: 'AuthGate' },
    ).catch(() => {});
  }, [t]);

  const requireAuthForPaid = useCallback(
    async ({ feature, message, resume } = {}) => {
      const token = await getAuthTokenSafe();
      if (token) {
        setIsGuest(false);
        return true;
      }
      setIsGuest(true);
      if (resume) {
        await setPendingPaidAction({
          feature: feature || 'paid_feature',
          ...resume,
        });
      }
      openAuthGate({ feature, message });
      return false;
    },
    [openAuthGate],
  );

  const goToLogin = useCallback(async () => {
    setVisible(false);
    trackGA4EventOnly('auth_gate_login_tapped', {
      feature: gateMeta.feature || 'unknown',
    }).catch(() => {});
    navigation.navigate('Login');
  }, [gateMeta.feature, navigation]);

  const dismissGate = useCallback(async () => {
    await clearPendingPaidAction();
    setVisible(false);
  }, []);

  const value = useMemo(
    () => ({
      isGuest,
      refreshAuthState,
      requireAuthForPaid,
      openAuthGate,
      closeAuthGate,
    }),
    [isGuest, refreshAuthState, requireAuthForPaid, openAuthGate, closeAuthGate],
  );

  const sheetBg = colors.surfaceRaised || colors.surface;
  const sheetBorder = colors.cardBorder;
  const iconBg = colors.cosmicGlow;
  const ctaColors = [colors.primaryStrong, colors.primary];
  const isChatGate = /chat|tara|question/i.test(`${gateMeta.feature} ${gateMeta.message}`);

  return (
    <AuthGateContext.Provider value={value}>
      {children}
      <Modal
        visible={visible}
        transparent
        animationType="slide"
        onRequestClose={dismissGate}
      >
        <View style={[styles.backdrop, { backgroundColor: colors.overlay }]}>
          <TouchableOpacity
            style={styles.backdropTap}
            activeOpacity={1}
            onPress={dismissGate}
            accessibilityLabel={t('authGate.dismiss')}
          />
          <View
            style={[
              styles.sheet,
              {
                backgroundColor: sheetBg,
                borderColor: sheetBorder,
                paddingBottom: Math.max(insets.bottom, 16) + 8,
              },
            ]}
          >
            <View
              style={[
                styles.handle,
                { backgroundColor: isDark ? 'rgba(255,255,255,0.28)' : 'rgba(28,25,23,0.2)' },
              ]}
            />
            <View style={[styles.iconWrap, { backgroundColor: iconBg, borderColor: colors.cosmicLine }]}>
              <Text style={[styles.gateGlyph, { color: colors.accent }]}>त</Text>
            </View>
            <Text style={[styles.eyebrow, { color: colors.primary }]}>PRIVATE · CHART-AWARE · CONTINUOUS</Text>
            <Text style={[styles.title, { color: colors.text }]}>
              {isChatGate ? 'Begin your consultation' : t('authGate.title')}
            </Text>
            <Text style={[styles.body, { color: colors.textSecondary }]}>
              {gateMeta.message ||
                t('authGate.messageGeneric', { feature: gateMeta.feature || t('authGate.featureCredits') })}
            </Text>
            <TouchableOpacity onPress={goToLogin} activeOpacity={0.9}>
              <LinearGradient
                colors={ctaColors}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.primaryBtn}
              >
                <Text style={[styles.primaryText, { color: colors.onPrimary }]}>{t('authGate.cta')}</Text>
                <Ionicons name="arrow-forward" size={17} color={colors.onPrimary} />
              </LinearGradient>
            </TouchableOpacity>
            <TouchableOpacity onPress={dismissGate} style={styles.secondaryBtn} activeOpacity={0.7}>
              <Text style={[styles.secondaryText, { color: colors.textTertiary }]}>
                {t('authGate.dismiss')}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </AuthGateContext.Provider>
  );
}

export const useAuthGate = () => useContext(AuthGateContext);

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(10, 5, 20, 0.55)',
    justifyContent: 'flex-end',
  },
  backdropTap: {
    flex: 1,
  },
  sheet: {
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    paddingHorizontal: 24,
    paddingTop: 10,
    borderWidth: 1,
    borderBottomWidth: 0,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: -6 },
        shadowOpacity: 0.18,
        shadowRadius: 16,
      },
      android: {
        elevation: 16,
      },
      default: {},
    }),
  },
  handle: {
    alignSelf: 'center',
    width: 40,
    height: 4,
    borderRadius: 2,
    marginBottom: 16,
  },
  iconWrap: {
    width: 58,
    height: 58,
    borderRadius: 29,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  gateGlyph: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 30 },
  eyebrow: { fontSize: 9, lineHeight: 13, fontWeight: '900', letterSpacing: 1.3, marginBottom: 7 },
  title: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 29,
    lineHeight: 34,
    fontWeight: '400',
    marginBottom: 8,
  },
  body: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 20,
  },
  primaryBtn: {
    borderRadius: 999,
    paddingVertical: 15,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  primaryText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '800',
  },
  secondaryBtn: {
    marginTop: 10,
    paddingVertical: 12,
    alignItems: 'center',
  },
  secondaryText: {
    fontSize: 14,
    fontWeight: '600',
  },
});
