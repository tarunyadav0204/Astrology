import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Alert,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../../utils/constants';
import { authAPI, chartAPI } from '../../../services/api';
import { storage } from '../../../services/storage';
import { trackAstrologyEvent } from '../../../utils/analytics';
import { apiErrorMessage } from '../../../utils/apiErrorMessage';
import { useCredits } from '../../../credits/CreditContext';
import { trackAcquisitionFunnelEvent } from '../../../services/acquisitionTracking';
import AuthKeyboardScreen from './AuthKeyboardScreen';
import AuthLegalNotice from '../AuthLegalNotice';
import {
  clearPendingPaidAction,
  getPendingPaidAction,
  mergeGuestProfilesAfterLogin,
} from '../../../auth/guestAuth';
import { useAuthGate } from '../../../auth/AuthGateContext';
import { trackGA4EventOnly } from '../../../utils/analytics';
import { resetToRoute } from '../../../navigation/navHelpers';

export default function PasswordScreen({ 
  formData, 
  updateFormData, 
  navigateToScreen, 
  isLogin,
  setIsLogin,
  navigation 
}) {
  const { refreshCredits } = useCredits();
  const { refreshAuthState } = useAuthGate();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isValid, setIsValid] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  
  const inputAnim = useRef(new Animated.Value(0)).current;
  const buttonAnim = useRef(new Animated.Value(50)).current;
  const passwordInputRef = useRef(null);

  useEffect(() => {
    trackAcquisitionFunnelEvent(
      'auth_password_screen_viewed',
      { mode: isLogin ? 'login' : 'register' },
      { screenName: 'PasswordScreen' },
    ).catch(() => {});
    Animated.parallel([
      Animated.timing(inputAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(buttonAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const acquisitionErrorMeta = (error) => ({
    status_code: error?.response?.status || '',
    reason:
      apiErrorMessage(error, 'request failed')
        .replace(/\s+/g, ' ')
        .slice(0, 160) || 'request failed',
  });

  useEffect(() => {
    const password = formData.password || '';
    setIsValid(isLogin ? password.length >= 6 : password.length >= 8 && /\d/.test(password));
  }, [formData.password, isLogin]);

  const passwordCriteria = [
    {
      label: 'Minimum 8 characters',
      met: (formData.password || '').length >= 8,
    },
    {
      label: 'At least 1 number',
      met: /\d/.test(formData.password || ''),
    },
  ];

  const passwordStrengthLabel = (() => {
    const password = formData.password || '';
    const metCount = passwordCriteria.filter((item) => item.met).length;
    if (password.length === 0) return 'Start typing';
    if (metCount === passwordCriteria.length && password.length >= 10) return 'Strong';
    if (metCount === passwordCriteria.length) return 'Good';
    return 'Weak';
  })();

  const passwordStrengthColor = (() => {
    if (passwordStrengthLabel === 'Strong') return '#4CAF50';
    if (passwordStrengthLabel === 'Good') return '#8BC34A';
    if (passwordStrengthLabel === 'Start typing') return 'rgba(255, 255, 255, 0.45)';
    return '#FF9800';
  })();

  const passwordStrengthProgress = (() => {
    const password = formData.password || '';
    if (!password) return 0;
    const lengthScore = Math.min(password.length / 8, 1) * 70;
    const numberScore = /\d/.test(password) ? 30 : 0;
    return Math.min(lengthScore + numberScore, 100);
  })();

  // Delay initial focus so keyboard avoidance/layout is ready first (fixes first-load overlap on Android)
  useEffect(() => {
    const timer = setTimeout(() => {
      passwordInputRef.current?.focus();
    }, 280);

    return () => clearTimeout(timer);
  }, []);

  const handleContinue = async () => {
    if (!isValid) {
      trackAcquisitionFunnelEvent(
        'auth_password_submit_blocked',
        { mode: isLogin ? 'login' : 'register', reason: 'invalid_password' },
        { status: 'blocked', screenName: 'PasswordScreen' },
      ).catch(() => {});
      return;
    }
    
    // Combine country code with phone for API calls
    const fullPhone = `${formData.countryCode || ''}${formData.phone}`;
    
    console.log('🔐 Password Screen - handleContinue');
    console.log('  formData.phone:', formData.phone);
    console.log('  formData.countryCode:', formData.countryCode);
    console.log('  fullPhone:', fullPhone);
    console.log('  isLogin:', isLogin);
    
    setPasswordError('');
    setLoading(true);
    try {
      if (isLogin) {
        trackAcquisitionFunnelEvent('login_submitted', {}, { status: 'started', screenName: 'PasswordScreen' }).catch(() => {});
        console.log('  📤 Calling login API with phone:', fullPhone);
        
        let response;
        try {
          // Try with country code first
          response = await authAPI.login({ 
            phone: fullPhone, 
            password: formData.password 
          });
        } catch (error) {
          // If 401, try without country code for legacy users
          if (error.response?.status === 401) {
            console.log('  🔄 Retrying without country code:', formData.phone);
            response = await authAPI.login({ 
              phone: formData.phone, 
              password: formData.password 
            });
          } else {
            throw error;
          }
        }
        
        console.log('  ✅ Login successful');
        
        await storage.setAuthToken(response.data.access_token);
        await storage.setUserData(response.data.user);
        try {
          const { linkAcquisitionInstallationToUser } = require('../../../services/acquisitionTracking');
          linkAcquisitionInstallationToUser().catch(() => {});
        } catch (_) {}
        trackAcquisitionFunnelEvent('login_completed', {}, { status: 'success', screenName: 'PasswordScreen' }).catch(() => {});
        trackAstrologyEvent.userLoggedIn();
        await refreshCredits();
        try {
          await refreshAuthState?.();
        } catch (_) {}
        if (Platform.OS !== 'ios') {
          try {
            const { syncPushTokenIfPermissionGranted } = require('../../../services/pushNotifications');
            syncPushTokenIfPermissionGranted();
          } catch (_) {}
        }

        const resetTo = (routeName, params) => {
          resetToRoute(navigation, routeName, params);
        };

        // Merge any guest-local charts onto the account before routing.
        try {
          await mergeGuestProfilesAfterLogin({ chartAPI });
        } catch (_) {
          /* non-fatal */
        }

        const pending = await getPendingPaidAction();
        if (pending?.resumeRoute) {
          await clearPendingPaidAction();
          trackGA4EventOnly('auth_gate_completed', {
            feature: pending.feature || 'paid_feature',
          }).catch(() => {});
          resetTo(pending.resumeRoute, pending.resumeParams || {});
          return;
        }

        // Route by chart COUNT (not only self chart):
        // - If user has >=1 chart, pick one and land Home.
        // - Show BirthProfileIntro only when user truly has zero charts.
        if (response.data.self_birth_chart) {
          resetTo('Home');
        } else {
          try {
            const chartsRes = await chartAPI.getExistingCharts('', 10, 0);
            const charts = Array.isArray(chartsRes?.data?.charts) ? chartsRes.data.charts : [];
            const localActive = await storage.getBirthDetails();
            if (charts.length > 0 || localActive) {
              if (!localActive && charts.length > 0) {
                const selfChart = charts.find(
                  (c) => String(c?.relation || '').trim().toLowerCase() === 'self'
                );
                const selected = selfChart || charts[0];
                const birthDetails = {
                  id: selected.id ?? selected._id,
                  name: selected.name,
                  date: selected.date,
                  time: selected.time,
                  place: selected.place,
                  latitude: selected.latitude,
                  longitude: selected.longitude,
                  gender: selected.gender,
                  relation: selected.relation,
                  isSelf: String(selected?.relation || '').trim().toLowerCase() === 'self',
                };
                await storage.setBirthDetails(birthDetails);
              }
              resetTo('Home');
            } else {
              resetTo('BirthProfileIntro', { chartRequired: true });
            }
          } catch (_) {
            // If charts lookup fails, keep the safe onboarding path.
            resetTo('BirthProfileIntro', { chartRequired: true });
          }
        }
      } else {
        // Registration complete - register user and navigate to birth form
        try {
          trackAcquisitionFunnelEvent(
            'registration_submitted',
            { with_birth_details: Boolean(formData?.birthDetails) },
            { status: 'started', screenName: 'PasswordScreen' },
          ).catch(() => {});
          const emailTrim = (formData.email || '').trim();
          const response = await authAPI.registerWithBirth({
            name: formData.name,
            phone: fullPhone,
            password: formData.password,
            ...(emailTrim ? { email: emailTrim } : {}),
            ...(formData.otpToken ? { otp_token: formData.otpToken } : {}),
            role: 'user',
            signup_client: 'mobile',
            ...(formData?.birthDetails?.gender ? { gender: formData.birthDetails.gender } : {}),
          });
          
          await storage.setAuthToken(response.data.access_token);
          await storage.setUserData(response.data.user);
          try {
            const { linkAcquisitionInstallationToUser } = require('../../../services/acquisitionTracking');
            linkAcquisitionInstallationToUser().catch(() => {});
          } catch (_) {}
          trackAcquisitionFunnelEvent(
            'registration_completed',
            { with_birth_details: Boolean(response.data.self_birth_chart) },
            { status: 'success', screenName: 'PasswordScreen' },
          ).catch(() => {});
          trackAstrologyEvent.userRegistered('mobile');
          await refreshCredits();
          try {
            await refreshAuthState?.();
          } catch (_) {}
          try {
            await mergeGuestProfilesAfterLogin({ chartAPI });
          } catch (_) {
            /* non-fatal */
          }
          trackGA4EventOnly('auth_gate_completed', { feature: 'registration' }).catch(() => {});
          
          // Language selection, then welcome (same preference as Profile → language)
          navigateToScreen('chooseLanguage');
        } catch (error) {
          const already =
            typeof error.response?.data?.detail === 'string' &&
            error.response.data.detail.includes('already registered');
          const alreadyFrom422 =
            Array.isArray(error.response?.data?.detail) &&
            error.response.data.detail.some(
              (d) =>
                typeof d?.msg === 'string' && d.msg.toLowerCase().includes('already registered'),
            );
          if ((error.response?.status === 400 || error.response?.status === 409) && (already || alreadyFrom422)) {
            trackAcquisitionFunnelEvent(
              'registration_existing_user_redirected',
              { status_code: error.response?.status || '' },
              { status: 'redirected', screenName: 'PasswordScreen' },
            ).catch(() => {});
            setIsLogin?.(true);
            setPasswordError('This number is already registered. Enter your password to sign in.');
            updateFormData('password', '');
            passwordInputRef.current?.focus();
          } else {
            trackAcquisitionFunnelEvent(
              'registration_failed',
              acquisitionErrorMeta(error),
              { status: 'failed', screenName: 'PasswordScreen' },
            ).catch(() => {});
            Alert.alert('Registration Error', apiErrorMessage(error, 'Registration failed'));
          }
        }
      }
    } catch (error) {
      trackAcquisitionFunnelEvent(
        isLogin ? 'login_failed' : 'registration_failed',
        acquisitionErrorMeta(error),
        { status: 'failed', screenName: 'PasswordScreen' },
      ).catch(() => {});
      console.log('  ❌ Error in handleContinue:', error.message);
      console.log('  Error response:', error.response?.data);
      console.log('  Error status:', error.response?.status);
      if (isLogin) {
        const message = apiErrorMessage(error, 'Invalid phone number or password');
        setPasswordError(message || 'Invalid phone number or password');
        passwordInputRef.current?.focus();
      } else {
        Alert.alert('Error', apiErrorMessage(error, 'Authentication failed'));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthKeyboardScreen
      emoji="🔐"
      title={isLogin ? 'Enter your password' : 'Create a password'}
      subtitle={isLogin ? 'Welcome back to your chart journey' : 'Choose a strong password to secure your account'}
      onBack={() => navigateToScreen(isLogin ? 'phone' : 'name', 'back')}
      action={(
        <Animated.View
          style={[
            styles.buttonContainer,
            {
              transform: [{ translateY: buttonAnim }],
            },
          ]}
        >
          <TouchableOpacity
            style={[styles.continueButton, !isValid && styles.buttonDisabled]}
            onPress={handleContinue}
            disabled={!isValid || loading}
          >
            <LinearGradient
              colors={isValid ? ['#ff6b35', '#ff8c5a'] : ['#666', '#444']}
              style={styles.buttonGradient}
            >
              <Text style={styles.buttonText}>
                {loading ? (isLogin ? 'Signing In...' : 'Continue') : (isLogin ? 'Sign In' : 'Continue')}
              </Text>
              <Ionicons name="arrow-forward" size={20} color="#ffffff" />
            </LinearGradient>
          </TouchableOpacity>
        </Animated.View>
      )}
      footer={!isLogin ? <AuthLegalNotice compact /> : null}
    >
      <Animated.View
        style={[
          styles.inputContainer,
          {
            opacity: inputAnim,
            transform: [
              {
                translateY: inputAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: [30, 0],
                }),
              },
            ],
          },
        ]}
      >
        <View style={[styles.inputWrapper, isValid && styles.inputValid]}>
          <Ionicons name="lock-closed-outline" size={20} color="rgba(255, 255, 255, 0.5)" />
          <TextInput
            ref={passwordInputRef}
            style={styles.input}
            placeholder="Password"
            placeholderTextColor="rgba(255, 255, 255, 0.5)"
            value={formData.password}
            onChangeText={(value) => {
              if (passwordError) setPasswordError('');
              updateFormData('password', value);
            }}
            secureTextEntry={!showPassword}
          />
          <TouchableOpacity
            onPress={() => setShowPassword(!showPassword)}
            style={styles.eyeButton}
          >
            <Ionicons
              name={showPassword ? 'eye-off-outline' : 'eye-outline'}
              size={20}
              color="rgba(255, 255, 255, 0.5)"
            />
          </TouchableOpacity>
          {isValid && (
            <Ionicons name="checkmark-circle" size={24} color="#4CAF50" />
          )}
        </View>

        {!!passwordError && (
          <View style={styles.inlineError}>
            <Ionicons name="alert-circle-outline" size={15} color="#ffb4a2" />
            <Text style={styles.inlineErrorText}>{passwordError}</Text>
          </View>
        )}

        {!isLogin && (
          <View style={styles.strengthContainer}>
            <View style={styles.strengthBar}>
              <View
                style={[
                  styles.strengthFill,
                  {
                    width: `${passwordStrengthProgress}%`,
                    backgroundColor: passwordStrengthColor,
                  }
                ]}
              />
            </View>
            <Text style={[styles.strengthText, { color: passwordStrengthColor }]}>
              {passwordStrengthLabel}
            </Text>
            <View style={styles.passwordCriteriaList}>
              {passwordCriteria.map((item) => (
                <View key={item.label} style={styles.passwordCriterionRow}>
                  <Ionicons
                    name={item.met ? 'checkmark-circle' : 'ellipse-outline'}
                    size={14}
                    color={item.met ? '#4CAF50' : 'rgba(255, 255, 255, 0.45)'}
                  />
                  <Text style={[
                    styles.passwordCriterionText,
                    item.met && styles.passwordCriterionTextMet,
                  ]}>
                    {item.label}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {isLogin && (
          <TouchableOpacity 
            style={styles.forgotButton}
            onPress={() => navigateToScreen('forgotPassword')}
          >
            <Text style={styles.forgotText}>Forgot Password?</Text>
          </TouchableOpacity>
        )}
      </Animated.View>
    </AuthKeyboardScreen>
  );
}

const styles = StyleSheet.create({
  inputContainer: {
    marginBottom: 8,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 16,
    paddingVertical: 4,
    gap: 12,
  },
  inputValid: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  input: {
    flex: 1,
    fontSize: 18,
    color: '#ffffff',
    paddingVertical: 16,
    fontWeight: '500',
    ...(Platform.OS === 'web'
      ? { outlineStyle: 'none', outlineWidth: 0, boxShadow: 'none' }
      : null),
  },
  eyeButton: {
    padding: 4,
  },
  inlineError: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 107, 53, 0.14)',
    borderWidth: 1,
    borderColor: 'rgba(255, 180, 162, 0.35)',
  },
  inlineErrorText: {
    flex: 1,
    color: '#ffcfbf',
    fontSize: 12,
    fontWeight: '700',
  },
  strengthContainer: {
    marginTop: 12,
  },
  strengthBar: {
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 2,
    overflow: 'hidden',
    marginBottom: 8,
  },
  strengthFill: {
    height: '100%',
    borderRadius: 2,
  },
  strengthText: {
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 10,
  },
  passwordCriteriaList: {
    gap: 6,
  },
  passwordCriterionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
  },
  passwordCriterionText: {
    color: 'rgba(255, 255, 255, 0.55)',
    fontSize: 12,
    fontWeight: '500',
  },
  passwordCriterionTextMet: {
    color: '#9BE7A0',
    fontWeight: '700',
  },
  buttonContainer: {
    marginBottom: 0,
  },
  continueButton: {
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    gap: 8,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600',
  },
  forgotButton: {
    alignItems: 'center',
    paddingVertical: 12,
  },
  forgotText: {
    color: '#ff6b35',
    fontSize: 14,
    fontWeight: '500',
  },
});
