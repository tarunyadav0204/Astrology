import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../../utils/constants';
import { trackAcquisitionFunnelEvent, updateAcquisitionLeadContact } from '../../../services/acquisitionTracking';
import AuthKeyboardScreen from './AuthKeyboardScreen';

function validateEmail(value) {
  const email = String(value || '').trim().toLowerCase();
  if (!email) return { valid: false, message: '' };
  if (email.length > 254) return { valid: false, message: 'Email address is too long' };
  if (!/^[^\s@]+@[^\s@]+\.[a-z]{2,24}$/i.test(email)) {
    return { valid: false, message: 'Enter a valid email address' };
  }

  const domain = email.split('@')[1] || '';
  const [domainName, ...tldParts] = domain.split('.');
  const tld = tldParts[tldParts.length - 1] || '';
  const knownProviderTlds = new Set(['com', 'co.in', 'in', 'net', 'org']);
  const commonProviders = new Set([
    'gmail',
    'googlemail',
    'yahoo',
    'hotmail',
    'outlook',
    'live',
    'icloud',
    'me',
    'rediffmail',
    'proton',
    'protonmail',
  ]);
  const fullTld = tldParts.join('.');
  const typoTlds = new Set(['coma', 'con', 'cmo', 'comm', 'coom', 'om', 'cm']);

  if (typoTlds.has(tld)) {
    return { valid: false, message: 'Check the email ending. Did you mean .com?' };
  }
  if (commonProviders.has(domainName) && !knownProviderTlds.has(fullTld)) {
    return { valid: false, message: `Check the ${domainName} email ending` };
  }

  return { valid: true, message: '' };
}

export default function EmailInputScreen({ 
  formData, 
  updateFormData, 
  navigateToScreen,
  isLogin,
}) {
  const emailValidation = validateEmail(formData.email);
  const isValid = emailValidation.valid;
  const hasName = String(formData.name || '').trim().length >= 2;
  const backTarget = isLogin ? 'password' : (hasName ? 'name' : 'otp');
  
  const inputAnim = useRef(new Animated.Value(0)).current;
  const buttonAnim = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    trackAcquisitionFunnelEvent(
      'auth_email_screen_viewed',
      {
        mode: isLogin ? 'login' : 'register',
        phone_otp_verified: Boolean(formData.otpToken),
      },
      { screenName: 'EmailInputScreen' },
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

  const handleContinue = async () => {
    if (!isValid) return;

    if (isLogin) {
      trackAcquisitionFunnelEvent(
        'auth_email_submitted',
        { mode: 'login', sends_otp: false },
        { status: 'accepted', screenName: 'EmailInputScreen' },
      ).catch(() => {});
      navigateToScreen('password');
      return;
    }

    const email = String(formData.email || '').trim();
    updateFormData('email', email);
    const fullPhone = `${formData.countryCode || ''}${formData.phone}`;
    updateAcquisitionLeadContact({ phone: fullPhone, email }).catch(() => {});
    trackAcquisitionFunnelEvent(
      'auth_email_submitted',
      { mode: 'register', sends_otp: false },
      { status: 'accepted', screenName: 'EmailInputScreen' },
    ).catch(() => {});
    navigateToScreen(hasName ? 'password' : 'name');
  };

  return (
    <AuthKeyboardScreen
      emoji="📧"
      title="What's your email?"
      subtitle="We'll use this to keep your account secure"
      onBack={() => navigateToScreen(backTarget, 'back')}
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
            disabled={!isValid}
          >
            <LinearGradient
              colors={isValid ? ['#ff6b35', '#ff8c5a'] : ['#666', '#444']}
              style={styles.buttonGradient}
            >
              <Text style={styles.buttonText}>Continue</Text>
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
            <Ionicons name="mail-outline" size={20} color="rgba(255, 255, 255, 0.5)" />
            <TextInput
              style={styles.input}
              placeholder="Email Address"
              placeholderTextColor="rgba(255, 255, 255, 0.5)"
              value={formData.email}
              onChangeText={(value) => updateFormData('email', value)}
              keyboardType="email-address"
              inputMode="email"
              autoCapitalize="none"
              autoCorrect={false}
              spellCheck={false}
              autoComplete="email"
              textContentType="emailAddress"
              importantForAutofill="yes"
              autoFocus
            />
            {isValid && (
              <Ionicons name="checkmark-circle" size={24} color="#4CAF50" />
            )}
          </View>
          {!!formData.email && !isValid && !!emailValidation.message && (
            <Text style={styles.validationText}>{emailValidation.message}</Text>
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
  validationText: {
    color: '#ffccbc',
    fontSize: 13,
    marginTop: 8,
    paddingHorizontal: 4,
  },
  input: {
    flex: 1,
    fontSize: 18,
    color: '#ffffff',
    paddingVertical: 16,
    fontWeight: '500',
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
});
