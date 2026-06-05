import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Modal,
  FlatList,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../../utils/constants';
import { authAPI } from '../../../services/api';
import { apiErrorMessage } from '../../../utils/apiErrorMessage';
import {
  COUNTRY_CODES,
  getNationalPhoneMaxLength,
  isNationalPhoneValid,
} from '../countryCodes';
import { trackAcquisitionFunnelEvent, updateAcquisitionLeadContact } from '../../../services/acquisitionTracking';

export default function PhoneInputScreen({ 
  formData, 
  updateFormData, 
  navigateToScreen, 
  isLogin,
  setIsLogin,
}) {
  const [loading, setLoading] = useState(false);
  const [isValid, setIsValid] = useState(false);
  const [showCountryPicker, setShowCountryPicker] = useState(false);
  const [phoneError, setPhoneError] = useState('');
  const [selectedCountry, setSelectedCountry] = useState(
    COUNTRY_CODES.find(c => c.code === formData.countryCode) || COUNTRY_CODES[2]
  );
  
  const inputAnim = useRef(new Animated.Value(0)).current;
  const buttonAnim = useRef(new Animated.Value(50)).current;
  const lastAutoSubmitPhoneRef = useRef('');

  useEffect(() => {
    trackAcquisitionFunnelEvent(
      'auth_phone_screen_viewed',
      { mode: isLogin ? 'login' : 'register', country_code: selectedCountry.code },
      { screenName: 'PhoneInputScreen' },
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

  useEffect(() => {
    setIsValid(isNationalPhoneValid(selectedCountry.code, formData.phone));
  }, [formData.phone, selectedCountry]);

  const goToSignInWithPhone = () => {
    setPhoneError('');
    setIsLogin?.(true);
    updateFormData('countryCode', selectedCountry.code);
    navigateToScreen('password');
  };

  const handleContinue = async (phoneOverride = null) => {
    const phoneForSubmit = phoneOverride != null ? phoneOverride : formData.phone;
    const phoneIsValid = isNationalPhoneValid(selectedCountry.code, phoneForSubmit);
    if (!phoneIsValid || loading) return;
    setPhoneError('');
    
    // Construct full phone number with country code
    const fullPhone = `${selectedCountry.code}${phoneForSubmit}`;
    
    console.log('📱 Phone Input - handleContinue');
    console.log('  Local phone:', phoneForSubmit);
    console.log('  Country code:', selectedCountry.code);
    console.log('  Full phone:', fullPhone);
    console.log('  Is login:', isLogin);
    
    if (isLogin) {
      updateFormData('countryCode', selectedCountry.code);
      updateAcquisitionLeadContact({ phone: fullPhone }).catch(() => {});
      trackAcquisitionFunnelEvent(
        'auth_phone_submitted',
        { mode: 'login', country_code: selectedCountry.code },
        { status: 'accepted', screenName: 'PhoneInputScreen' },
      ).catch(() => {});
      console.log('  → Navigating to password screen');
      navigateToScreen('password');
      return;
    }

    setLoading(true);
    try {
      updateFormData('countryCode', selectedCountry.code);
      updateAcquisitionLeadContact({ phone: fullPhone }).catch(() => {});
      trackAcquisitionFunnelEvent(
        'auth_phone_submitted',
        { mode: 'register', country_code: selectedCountry.code },
        { status: 'accepted', screenName: 'PhoneInputScreen' },
      ).catch(() => {});
      trackAcquisitionFunnelEvent(
        'registration_otp_requested',
        { source: 'phone_screen' },
        { status: 'started', screenName: 'PhoneInputScreen' },
      ).catch(() => {});

      const response = await authAPI.sendRegistrationOtp({ phone: fullPhone });
      updateFormData('otpDelivery', response?.data?.delivery || null);
      if (response?.data?.dev_code) {
        updateFormData('devOtpCode', response.data.dev_code);
      }
      trackAcquisitionFunnelEvent(
        'registration_otp_requested',
        {
          source: 'phone_screen',
          channel: response?.data?.delivery?.registration_otp_channel || '',
        },
        { status: 'success', screenName: 'PhoneInputScreen' },
      ).catch(() => {});
      navigateToScreen('otp');
    } catch (error) {
      const message = apiErrorMessage(error, 'Unable to verify this phone number. Please try again.');
      trackAcquisitionFunnelEvent(
        'registration_otp_requested',
        {
          source: 'phone_screen',
          status_code: error?.response?.status || '',
          reason: message.replace(/\s+/g, ' ').slice(0, 160),
        },
        { status: 'failed', screenName: 'PhoneInputScreen' },
      ).catch(() => {});
      if (error?.response?.status === 409 || /already registered/i.test(message)) {
        setPhoneError('This number is already registered.');
      } else {
        Alert.alert('Could not continue', message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePhoneChange = (value) => {
    const digits = value.replace(/[^0-9]/g, '');
    const maxLen = getNationalPhoneMaxLength(selectedCountry.code);
    const nextPhone = digits.slice(0, maxLen);
    setPhoneError('');
    updateFormData('phone', nextPhone);

    const complete = isNationalPhoneValid(selectedCountry.code, nextPhone);
    const autoKey = `${selectedCountry.code}${nextPhone}:${isLogin ? 'login' : 'register'}`;
    if (complete && !loading && lastAutoSubmitPhoneRef.current !== autoKey) {
      lastAutoSubmitPhoneRef.current = autoKey;
      setTimeout(() => {
        handleContinue(nextPhone);
      }, 80);
    }
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
          onPress={() => navigateToScreen('welcome', 'back')}
        >
          <Ionicons name="arrow-back" size={24} color="#ffffff" />
        </TouchableOpacity>

        <View style={styles.content}>
          <View style={styles.header}>
            <Text style={styles.emoji}>📱</Text>
            <Text style={styles.title}>
              {isLogin ? "Welcome back!" : "What's your number?"}
            </Text>
            <Text style={styles.subtitle}>
              {isLogin ? "Enter your phone number to sign in" : "We'll send a verification code to this phone"}
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
              <TouchableOpacity
                style={styles.countryCode}
                onPress={() => setShowCountryPicker(true)}
              >
                <Text style={styles.countryText}>{selectedCountry.flag} {selectedCountry.code}</Text>
                <Ionicons name="chevron-down" size={16} color="rgba(255, 255, 255, 0.7)" style={{ marginLeft: 4 }} />
              </TouchableOpacity>
              <TextInput
                style={styles.input}
                placeholder="Phone Number"
                placeholderTextColor="rgba(255, 255, 255, 0.5)"
                value={formData.phone}
                onChangeText={handlePhoneChange}
                keyboardType="number-pad"
                inputMode="numeric"
                textContentType="telephoneNumber"
                autoFocus
                maxLength={getNationalPhoneMaxLength(selectedCountry.code)}
              />
              {isValid && (
                <Ionicons name="checkmark-circle" size={24} color="#4CAF50" />
              )}
            </View>
            {!!phoneError && !isLogin && (
              <View style={styles.inlineErrorRow}>
                <Ionicons name="alert-circle" size={16} color="#ff6b6b" />
                <Text style={styles.inlineErrorText}>
                  {phoneError}{' '}
                  <Text style={styles.inlineErrorLink} onPress={goToSignInWithPhone}>
                    Sign In Instead
                  </Text>
                </Text>
              </View>
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
              onPress={() => handleContinue()}
              disabled={!isValid || loading}
            >
              <LinearGradient
                colors={isValid ? ['#ff6b35', '#ff8c5a'] : ['#666', '#444']}
                style={styles.buttonGradient}
              >
                <Text style={styles.buttonText}>
                  {loading ? 'Checking...' : 'Continue'}
                </Text>
                <Ionicons name="arrow-forward" size={20} color="#ffffff" />
              </LinearGradient>
            </TouchableOpacity>
          </Animated.View>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <Text
              style={styles.footerLink}
              onPress={() => navigateToScreen('welcome', 'back')}
            >
              {isLogin ? "Create one" : "Sign in"}
            </Text>
          </Text>
        </View>
      </ScrollView>

      <Modal
        visible={showCountryPicker}
        transparent
        animationType="slide"
        onRequestClose={() => setShowCountryPicker(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Country</Text>
              <TouchableOpacity onPress={() => setShowCountryPicker(false)}>
                <Ionicons name="close" size={24} color="#ffffff" />
              </TouchableOpacity>
            </View>
            <FlatList
              data={COUNTRY_CODES}
              keyExtractor={(item) => item.code}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={styles.countryItem}
                  onPress={() => {
                    setSelectedCountry(item);
                    updateFormData('countryCode', item.code);
                    const maxLen = getNationalPhoneMaxLength(item.code);
                    const current = (formData.phone || '').replace(/[^0-9]/g, '');
                    updateFormData('phone', current.slice(0, maxLen));
                    setShowCountryPicker(false);
                  }}
                >
                  <Text style={styles.countryFlag}>{item.flag}</Text>
                  <View style={styles.countryInfo}>
                    <Text style={styles.countryName}>{item.name}</Text>
                    <Text style={styles.countryCodeText}>{item.code}</Text>
                  </View>
                  {selectedCountry.code === item.code && (
                    <Ionicons name="checkmark" size={24} color="#4CAF50" />
                  )}
                </TouchableOpacity>
              )}
            />
          </View>
        </View>
      </Modal>
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
  },
  inputValid: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  countryCode: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingRight: 12,
    borderRightWidth: 1,
    borderRightColor: 'rgba(255, 255, 255, 0.2)',
    marginRight: 12,
  },
  countryText: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a2e',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '70%',
    paddingBottom: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#ffffff',
  },
  countryItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.05)',
  },
  countryFlag: {
    fontSize: 28,
    marginRight: 12,
  },
  countryInfo: {
    flex: 1,
  },
  countryName: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: '600',
    marginBottom: 2,
  },
  countryCodeText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  input: {
    flex: 1,
    fontSize: 18,
    color: '#ffffff',
    paddingVertical: 16,
    fontWeight: '500',
  },
  inlineErrorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 10,
    paddingHorizontal: 4,
  },
  inlineErrorText: {
    flex: 1,
    color: '#ffb4b4',
    fontSize: 13,
    fontWeight: '500',
    lineHeight: 18,
  },
  inlineErrorLink: {
    color: '#ff8c5a',
    fontWeight: '800',
    textDecorationLine: 'underline',
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
  footer: {
    paddingBottom: 20,
    alignItems: 'center',
  },
  footerText: {
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: 14,
  },
  footerLink: {
    color: '#ff6b35',
    fontWeight: '600',
  },
});
