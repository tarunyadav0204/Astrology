import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Animated,
  KeyboardAvoidingView,
  ScrollView,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../../utils/constants';
import { trackAcquisitionFunnelEvent, updateAcquisitionLeadContact } from '../../../services/acquisitionTracking';

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
    <KeyboardAvoidingView 
      style={styles.container} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
    >
      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => navigateToScreen(backTarget, 'back')}
        >
          <Ionicons name="arrow-back" size={24} color="#ffffff" />
        </TouchableOpacity>

        <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.emoji}>📧</Text>
          <Text style={styles.title}>What's your email?</Text>
          <Text style={styles.subtitle}>
            We'll use this to keep your account secure
          </Text>
        </View>

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
        </View>
        <View style={styles.extraPadding} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingBottom: 160,
  },
  backButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 20,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 60,
  },
  emoji: {
    fontSize: 60,
    marginBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 12,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    lineHeight: 22,
  },
  inputContainer: {
    marginBottom: 40,
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
    marginBottom: 40,
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
  extraPadding: {
    height: 120,
  },
});
