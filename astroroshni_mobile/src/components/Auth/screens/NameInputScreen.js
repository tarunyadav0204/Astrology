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
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../../utils/constants';
import { trackAcquisitionFunnelEvent } from '../../../services/acquisitionTracking';
import { registrationEmailRequiredForCountry } from '../countryCodes';
import AuthKeyboardScreen from './AuthKeyboardScreen';

export default function NameInputScreen({ 
  formData, 
  updateFormData, 
  navigateToScreen 
}) {
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
      emoji="👋"
      title="What's your name?"
      subtitle="Help us personalize your chart experience"
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
          <Ionicons name="person-outline" size={20} color="rgba(255, 255, 255, 0.5)" />
          <TextInput
            style={styles.input}
            placeholder="Full Name"
            placeholderTextColor="rgba(255, 255, 255, 0.5)"
            value={formData.name}
            onChangeText={(value) => updateFormData('name', value)}
            autoFocus
            autoCapitalize="words"
          />
          {isValid && (
            <Ionicons name="checkmark-circle" size={24} color="#4CAF50" />
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
