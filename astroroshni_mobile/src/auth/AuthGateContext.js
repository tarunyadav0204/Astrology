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
import Ionicons from '@expo/vector-icons/Ionicons';
import {
  clearPendingPaidAction,
  getAuthTokenSafe,
  isGuestSession,
  setPendingPaidAction,
} from './guestAuth';
import { trackGA4EventOnly } from '../utils/analytics';

const AuthGateContext = createContext({
  isGuest: true,
  refreshAuthState: async () => {},
  requireAuthForPaid: async () => false,
  openAuthGate: () => {},
  closeAuthGate: () => {},
});

export function AuthGateProvider({ children }) {
  const navigation = useNavigation();
  const [isGuest, setIsGuest] = useState(true);
  const [visible, setVisible] = useState(false);
  const [gateMeta, setGateMeta] = useState({
    feature: 'this feature',
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
      feature: meta.feature || 'this feature',
      message:
        meta.message ||
        'Create a free account to continue. Your charts on this device will be saved to your account.',
    });
    setVisible(true);
    trackGA4EventOnly('auth_gate_shown', {
      feature: meta.feature || 'unknown',
    }).catch(() => {});
  }, []);

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

  return (
    <AuthGateContext.Provider value={value}>
      {children}
      <Modal
        visible={visible}
        transparent
        animationType="fade"
        onRequestClose={dismissGate}
      >
        <TouchableOpacity
          style={styles.backdrop}
          activeOpacity={1}
          onPress={dismissGate}
        >
          <TouchableOpacity activeOpacity={1} onPress={() => {}} style={styles.sheetWrap}>
            <View style={styles.sheet}>
              <View style={styles.iconWrap}>
                <Ionicons name="lock-closed" size={22} color="#B45309" />
              </View>
              <Text style={styles.title}>Sign in to continue</Text>
              <Text style={styles.body}>
                {gateMeta.message ||
                  `Sign in to use ${gateMeta.feature}. Free chart tools stay available without an account.`}
              </Text>
              <TouchableOpacity onPress={goToLogin} activeOpacity={0.9}>
                <LinearGradient
                  colors={['#ff7b45', '#FF6B35', '#e85a2a']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={styles.primaryBtn}
                >
                  <Text style={styles.primaryText}>Sign in / Register</Text>
                </LinearGradient>
              </TouchableOpacity>
              <TouchableOpacity onPress={dismissGate} style={styles.secondaryBtn}>
                <Text style={styles.secondaryText}>Keep exploring free tools</Text>
              </TouchableOpacity>
            </View>
          </TouchableOpacity>
        </TouchableOpacity>
      </Modal>
    </AuthGateContext.Provider>
  );
}

export const useAuthGate = () => useContext(AuthGateContext);

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.55)',
    justifyContent: 'flex-end',
  },
  sheetWrap: {
    width: '100%',
  },
  sheet: {
    backgroundColor: '#fffbeb',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 22,
    paddingTop: 22,
    paddingBottom: Platform.OS === 'ios' ? 34 : 22,
    borderWidth: 1,
    borderColor: 'rgba(245, 158, 11, 0.28)',
  },
  iconWrap: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(245, 158, 11, 0.18)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: '#1c1917',
    marginBottom: 8,
  },
  body: {
    fontSize: 14,
    lineHeight: 20,
    color: '#57534e',
    marginBottom: 18,
  },
  primaryBtn: {
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
  },
  primaryText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '800',
  },
  secondaryBtn: {
    marginTop: 12,
    paddingVertical: 10,
    alignItems: 'center',
  },
  secondaryText: {
    color: '#78716c',
    fontSize: 14,
    fontWeight: '600',
  },
});
