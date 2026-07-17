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
import { authAPI } from '../../../services/api';
import { trackAcquisitionFunnelEvent } from '../../../services/acquisitionTracking';
import { registrationEmailRequiredForCountry } from '../countryCodes';
import AuthKeyboardScreen from './AuthKeyboardScreen';

export default function OTPScreen({ 
  formData, 
  updateFormData, 
  navigateToScreen, 
  isLogin 
}) {
  const [loading, setLoading] = useState(false);
  const [isValid, setIsValid] = useState(false);
  const [resendTimer, setResendTimer] = useState(30);
  const [devOtpCode, setDevOtpCode] = useState(null);
  const otpChannel = formData?.otpDelivery?.registration_otp_channel || '';
  const otpSentToEmail = otpChannel === 'email';
  const emailRequiredForRegistration = registrationEmailRequiredForCountry(formData.countryCode || '+91');
  const otpDestination = otpSentToEmail && formData.email
    ? formData.email
    : `${formData.countryCode} ${formData.phone}`;
  
  const inputAnim = useRef(new Animated.Value(0)).current;
  const buttonAnim = useRef(new Animated.Value(50)).current;
  const lastAutoVerifyCodeRef = useRef('');

  useEffect(() => {
    trackAcquisitionFunnelEvent(
      'registration_otp_screen_viewed',
      { mode: isLogin ? 'login' : 'register' },
      { screenName: 'OTPScreen' },
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

    // Start countdown timer
    const timer = setInterval(() => {
      setResendTimer(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    setIsValid(formData.otpCode.length === 6);
  }, [formData.otpCode]);

  const handleVerifyOTP = async (codeOverride = null) => {
    const codeForSubmit = String(codeOverride != null ? codeOverride : formData.otpCode || '').replace(/[^0-9]/g, '').slice(0, 6);
    if (codeForSubmit.length !== 6 || loading) return;
    
    setLoading(true);
    try {
      trackAcquisitionFunnelEvent(
        'registration_otp_verify_submitted',
        { source: 'otp_screen' },
        { status: 'started', screenName: 'OTPScreen' },
      ).catch(() => {});
      const fullPhone = `${formData.countryCode || ''}${formData.phone}`;
      const response = await authAPI.verifyResetCode({
        phone: fullPhone,
        code: codeForSubmit,
      });
      updateFormData('otpToken', response?.data?.reset_token || '');
      trackAcquisitionFunnelEvent(
        'registration_otp_verified',
        { source: 'otp_screen' },
        { status: 'success', screenName: 'OTPScreen' },
      ).catch(() => {});
      
      // India verifies by SMS and skips email. International users collected email before this screen.
      navigateToScreen('name');
    } catch (error) {
      trackAcquisitionFunnelEvent(
        'registration_otp_verify_failed',
        { source: 'otp_screen' },
        { status: 'failed', screenName: 'OTPScreen' },
      ).catch(() => {});
      Alert.alert('Error', 'Invalid OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (value) => {
    const digits = value.replace(/[^0-9]/g, '').slice(0, 6);
    updateFormData('otpCode', digits);
    if (digits.length === 6 && !loading && lastAutoVerifyCodeRef.current !== digits) {
      lastAutoVerifyCodeRef.current = digits;
      setTimeout(() => {
        handleVerifyOTP(digits);
      }, 80);
    }
  };

  const handleResendOTP = async () => {
    if (resendTimer > 0) return;
    
    try {
      trackAcquisitionFunnelEvent(
        'registration_otp_resent',
        { source: 'otp_screen' },
        { status: 'started', screenName: 'OTPScreen' },
      ).catch(() => {});
      const fullPhone = `${formData.countryCode || ''}${formData.phone}`;
      const payload = { phone: fullPhone };
      if ((formData.email || '').trim()) {
        payload.email = formData.email.trim();
      }
      const response = await authAPI.sendRegistrationOtp(payload);
      updateFormData('otpDelivery', response?.data?.delivery || formData.otpDelivery || null);
      setResendTimer(30);
      
      // Show dev OTP code if available
      if (response.data.dev_code) {
        setDevOtpCode(response.data.dev_code);
      }
      trackAcquisitionFunnelEvent(
        'registration_otp_resent',
        { source: 'otp_screen' },
        { status: 'success', screenName: 'OTPScreen' },
      ).catch(() => {});
      
      Alert.alert('Success', 'OTP sent successfully!');
    } catch (error) {
      trackAcquisitionFunnelEvent(
        'registration_otp_resent',
        { source: 'otp_screen', status_code: error?.response?.status || '' },
        { status: 'failed', screenName: 'OTPScreen' },
      ).catch(() => {});
      Alert.alert('Error', 'Failed to resend OTP. Please try again.');
    }
  };

  // Show dev OTP on initial load if available from previous API call
  useEffect(() => {
    // console.log('📱 OTP Screen loaded for phone:', formData.phone);
    
    if (formData.devOtpCode) {
      // console.log('📱 Development OTP Code available:', formData.devOtpCode);
      setDevOtpCode(formData.devOtpCode);
    } else {
      console.log('💡 Check backend logs for development OTP code');
    }
  }, [formData.devOtpCode]);

  return (
    <AuthKeyboardScreen
      emoji={otpSentToEmail ? '📧' : '📱'}
      title="Enter OTP"
      subtitle={`We've sent a 6-digit code to ${otpDestination}`}
      onBack={() => navigateToScreen(emailRequiredForRegistration ? 'email' : 'phone', 'back')}
      headerExtra={devOtpCode ? (
            <View style={styles.devCodeContainer}>
              <Text style={styles.devCodeLabel}>Development OTP:</Text>
              <Text style={styles.devCodeText}>{devOtpCode}</Text>
            </View>
      ) : null}
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
            style={[styles.verifyButton, !isValid && styles.buttonDisabled]}
            onPress={() => handleVerifyOTP()}
            disabled={!isValid || loading}
          >
            <LinearGradient
              colors={isValid ? ['#ff6b35', '#ff8c5a'] : ['#666', '#444']}
              style={styles.buttonGradient}
            >
              <Text style={styles.buttonText}>
                {loading ? 'Verifying...' : 'Verify OTP'}
              </Text>
              <Ionicons name="arrow-forward" size={20} color="#ffffff" />
            </LinearGradient>
          </TouchableOpacity>
        </Animated.View>
      )}
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
            <TextInput
              style={styles.input}
              placeholder="6-digit code"
              placeholderTextColor="rgba(255, 255, 255, 0.5)"
              value={formData.otpCode}
              onChangeText={handleOtpChange}
              keyboardType="number-pad"
              inputMode="numeric"
              textContentType="oneTimeCode"
              autoComplete="sms-otp"
              autoFocus
              maxLength={6}
            />
            {isValid && (
              <Ionicons name="checkmark-circle" size={24} color="#4CAF50" />
            )}
          </View>
        </Animated.View>

        <View style={styles.resendContainer}>
          <TouchableOpacity
            onPress={handleResendOTP}
            disabled={resendTimer > 0}
            style={styles.resendButton}
          >
            <Text style={[styles.resendText, resendTimer > 0 && styles.resendDisabled]}>
              {resendTimer > 0 ? `Resend OTP in ${resendTimer}s` : 'Resend OTP'}
            </Text>
          </TouchableOpacity>
        </View>
    </AuthKeyboardScreen>
  );
}

const styles = StyleSheet.create({
  inputContainer: {
    marginBottom: 20,
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
  },
  inputValid: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  input: {
    flex: 1,
    fontSize: 24,
    color: '#ffffff',
    paddingVertical: 16,
    fontWeight: '600',
    textAlign: 'center',
    letterSpacing: 3,
    ...(Platform.OS === 'web'
      ? { outlineStyle: 'none', outlineWidth: 0, boxShadow: 'none' }
      : null),
  },
  resendContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  resendButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
  },
  resendText: {
    color: '#ff6b35',
    fontSize: 16,
    fontWeight: '600',
  },
  resendDisabled: {
    color: 'rgba(255, 255, 255, 0.5)',
  },
  buttonContainer: {
    marginTop: 0,
    marginBottom: 0,
  },
  verifyButton: {
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
  devCodeContainer: {
    marginTop: 20,
    padding: 12,
    backgroundColor: 'rgba(255, 107, 53, 0.2)',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ff6b35',
  },
  devCodeLabel: {
    color: '#ff6b35',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 4,
  },
  devCodeText: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '700',
    textAlign: 'center',
    letterSpacing: 4,
  },
});
