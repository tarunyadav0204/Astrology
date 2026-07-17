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
import { trackGuestActivity } from '../services/acquisitionTracking';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from 'react-i18next';

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

  const sheetBg = isDark ? colors.backgroundSecondary : colors.cardBackground;
  const sheetBorder = colors.cardBorder;
  const iconBg = isDark ? 'rgba(249, 115, 22, 0.18)' : 'rgba(234, 88, 12, 0.12)';
  const ctaColors = isDark
    ? ['#f97316', '#ea580c', '#c2410c']
    : ['#fb923c', '#ea580c', '#c2410c'];

  return (
    <AuthGateContext.Provider value={value}>
      {children}
      <Modal
        visible={visible}
        transparent
        animationType="slide"
        onRequestClose={dismissGate}
      >
        <View style={styles.backdrop}>
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
            <View style={[styles.iconWrap, { backgroundColor: iconBg }]}>
              <Ionicons name="lock-closed" size={22} color={colors.primary} />
            </View>
            <Text style={[styles.title, { color: colors.text }]}>
              {t('authGate.title')}
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
                <Text style={styles.primaryText}>{t('authGate.cta')}</Text>
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
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    paddingHorizontal: 22,
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
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    marginBottom: 8,
  },
  body: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 20,
  },
  primaryBtn: {
    borderRadius: 14,
    paddingVertical: 15,
    alignItems: 'center',
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
