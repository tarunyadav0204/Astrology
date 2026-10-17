import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Platform,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../../utils/constants';
import { trackAcquisitionFunnelEvent } from '../../../services/acquisitionTracking';
import { registrationEmailRequiredForCountry } from '../countryCodes';
import AuthKeyboardScreen from './AuthKeyboardScreen';
import { useTheme } from '../../../context/ThemeContext';
import { useTranslation } from 'react-i18next';

export default function NameInputScreen({
  formData,
  updateFormData,
  navigateToScreen
}) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const isValid = formData.name.trim().length >= 2;
  const emailRequiredForRegistration = registrationEmailRequiredForCountry(formData.countryCode || '+91');

  const inputAnim = useRef(new Animated.Value(0)).current;
  const buttonAnim = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    trackAcquisitionFunnelEvent('registration_name_screen_viewed', {}, { screenName: 'NameInputScreen' }).catch(() => {});
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

  const handleContinue = () => {
    if (isValid) {
      const emailTrim = (formData.email || '').trim();
      trackAcquisitionFunnelEvent(
        'registration_name_submitted',
        { has_email: Boolean(emailTrim) },
        { status: 'accepted', screenName: 'NameInputScreen' },
      ).catch(() => {});
      if (emailTrim && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailTrim)) {
        navigateToScreen('password');
        return;
      }
      navigateToScreen(emailRequiredForRegistration ? 'email' : 'password');
    }
  };

  return (
    <AuthKeyboardScreen
      emoji="✦"
      title={t('authOnboarding.nameTitle', 'What should Tara call you?')}
      subtitle={t('authOnboarding.nameSubtitle', 'This personalizes your chart experience')}
      onBack={() => navigateToScreen('otp', 'back')}
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
            key={isValid ? 'enabled-action' : 'disabled-action'}
            style={[styles.continueButton, styles.buttonGradient, { shadowColor: colors.accent, backgroundColor: isValid ? '#d7b878' : colors.cosmicRaised }, !isValid && [styles.buttonDisabled, { borderColor: colors.cosmicLine }]]}
            onPress={handleContinue}
            disabled={!isValid}
          >
              <Text style={[styles.buttonText, { color: isValid ? '#210b17' : colors.textInverseMuted }]}>Continue</Text>
              <Ionicons name="arrow-forward" size={20} color={isValid ? '#210b17' : colors.textInverseMuted} />
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
        <View style={[styles.inputWrapper, { borderColor: isValid ? colors.accent : colors.cosmicLine, backgroundColor: colors.cosmicRaised }]}>
          <Ionicons name="person-outline" size={20} color={colors.textInverseMuted} />
          <TextInput
            style={styles.input}
            placeholder="Full Name"
            placeholderTextColor={colors.textInverseMuted}
            value={formData.name}
            onChangeText={(value) => updateFormData('name', value)}
            autoFocus
            autoCapitalize="words"
          />
          {isValid && (
            <Ionicons name="checkmark-circle" size={24} color={colors.accent} />
          )}
        </View>
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
  buttonContainer: {
    marginBottom: 0,
  },
  continueButton: {
    borderRadius: 16,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
  },
  buttonDisabled: {
    borderWidth: 1,
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
  },
  buttonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    gap: 8,
  },
  buttonText: {
    fontSize: 18,
    opacity: 1,
    fontWeight: '600',
  },
});
