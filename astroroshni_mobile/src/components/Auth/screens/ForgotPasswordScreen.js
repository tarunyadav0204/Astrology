import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Alert,
  ScrollView,
  Keyboard,
  Modal,
  FlatList,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { authAPI } from '../../../services/api';
import {
  COUNTRY_CODES,
  getNationalPhoneMaxLength,
  isNationalPhoneValid,
} from '../countryCodes';

export default function ForgotPasswordScreen({ 
  formData, 
  updateFormData, 
  navigateToScreen 
}) {
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1: phone, 2: code, 3: new password
  const [resetToken, setResetToken] = useState('');
  const [localNewPassword, setLocalNewPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showCountryPicker, setShowCountryPicker] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState(
    () => COUNTRY_CODES.find((c) => c.code === (formData.countryCode || '+91')) || COUNTRY_CODES[2]
  );

  const nationalDigits = (formData.phone || '').replace(/[^0-9]/g, '');
  const fullPhone = `${selectedCountry.code}${nationalDigits}`;
  const isUSPhone = selectedCountry.code === '+1';
  const isPhoneValid = isNationalPhoneValid(selectedCountry.code, nationalDigits);

  useEffect(() => {
    const match = COUNTRY_CODES.find((c) => c.code === formData.countryCode);
    if (match) setSelectedCountry(match);
  }, [formData.countryCode]);
  
  const inputAnim = useRef(new Animated.Value(0)).current;
  const buttonAnim = useRef(new Animated.Value(50)).current;
  const scrollViewRef = useRef(null);

  useEffect(() => {
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
    const keyboardDidShowListener = Keyboard.addListener('keyboardDidShow', () => {
      if (scrollViewRef.current) {
        scrollViewRef.current.scrollToEnd({ animated: true });
      }
    });

    return () => {
      keyboardDidShowListener?.remove();
    };
  }, []);

  const handleSendCode = async () => {
    if (!nationalDigits) {
      Alert.alert('Error', 'Please enter phone number');
      return;
    }
    if (!isPhoneValid) {
      Alert.alert(
        'Error',
        selectedCountry.code === '+91' || selectedCountry.code === '+1'
          ? 'Enter a valid 10-digit phone number'
          : 'Please enter a valid phone number for the selected country'
      );
      return;
    }
    if (isUSPhone && !formData.email) {
      Alert.alert('Error', 'Please enter email for US numbers');
      return;
    }

    setLoading(true);
    try {
      const buildPayload = (phoneVal) => {
        const payload = { phone: phoneVal };
        if (isUSPhone && formData.email) {
          payload.email = formData.email;
        }
        return payload;
      };
      let response;
      try {
        response = await authAPI.sendResetCode(buildPayload(fullPhone));
      } catch (error) {
        // Match PasswordScreen login: DB may store 10-digit local while UI sends +91…
        if (
          error.response?.status === 404 &&
          nationalDigits &&
          fullPhone !== nationalDigits
        ) {
          response = await authAPI.sendResetCode(buildPayload(nationalDigits));
        } else {
          throw error;
        }
      }
      Alert.alert('Success', response.data.message);
      setStep(2);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.detail || error.response?.data?.message || 'Phone number not found');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    if (!formData.resetCode) {
      Alert.alert('Error', 'Please enter verification code');
      return;
    }

    setLoading(true);
    try {
      const response = await authAPI.verifyResetCode({
        phone: fullPhone,
        code: formData.resetCode
      });
      setResetToken(response.data.reset_token);
      setLocalNewPassword(''); // Reset password field
      Alert.alert('Success', 'Code verified! Enter new password.');
      setStep(3);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.detail || error.response?.data?.message || 'Invalid or expired code');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!localNewPassword) {
      Alert.alert('Error', 'Please enter new password');
      return;
    }

    setLoading(true);
    try {
      await authAPI.resetPasswordWithToken({
        token: resetToken,
        new_password: localNewPassword
      });
      Alert.alert('Success', 'Password reset successfully!', [
        { text: 'OK', onPress: () => navigateToScreen('welcome') }
      ]);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.detail || error.response?.data?.message || 'Password reset failed');
    } finally {
      setLoading(false);
    }
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <>
            <View style={styles.header}>
              <Text style={styles.emoji}>📱</Text>
              <Text style={styles.title}>Reset Password</Text>
              <Text style={styles.subtitle}>
                {isUSPhone
                  ? 'Enter your phone number and email. We will send a reset code to your email.'
                  : 'Enter your phone number to receive a reset code'}
              </Text>
            </View>

            <Animated.View style={[styles.inputContainer, { opacity: inputAnim }]}>
              <View style={[styles.inputWrapper, isPhoneValid && styles.inputValid]}>
                <TouchableOpacity
                  style={styles.countryCode}
                  onPress={() => setShowCountryPicker(true)}
                >
                  <Text style={styles.countryText}>
                    {selectedCountry.flag} {selectedCountry.code}
                  </Text>
                  <Ionicons
                    name="chevron-down"
                    size={16}
                    color="rgba(255, 255, 255, 0.7)"
                    style={{ marginLeft: 4 }}
                  />
                </TouchableOpacity>
                <TextInput
                  style={styles.input}
                  placeholder={
                    selectedCountry.code === '+91' || selectedCountry.code === '+1'
                      ? '10-digit number'
                      : 'Phone Number'
                  }
                  placeholderTextColor="rgba(255, 255, 255, 0.5)"
                  value={formData.phone}
                  onChangeText={(value) => {
                    const digits = value.replace(/[^0-9]/g, '');
                    const maxLen = getNationalPhoneMaxLength(selectedCountry.code);
                    updateFormData('phone', digits.slice(0, maxLen));
                  }}
                  keyboardType="phone-pad"
                  autoFocus
                  maxLength={getNationalPhoneMaxLength(selectedCountry.code)}
                />
                {isPhoneValid ? (
                  <Ionicons name="checkmark-circle" size={24} color="#4CAF50" />
                ) : null}
              </View>
            </Animated.View>

            {isUSPhone && (
              <Animated.View style={[styles.inputContainer, { opacity: inputAnim }]}>
                <View style={styles.inputWrapper}>
                  <Ionicons name="mail-outline" size={20} color="rgba(255, 255, 255, 0.5)" />
                  <TextInput
                    style={styles.input}
                    placeholder="Email Address"
                    placeholderTextColor="rgba(255, 255, 255, 0.5)"
                    value={formData.email}
                    onChangeText={(value) => updateFormData('email', value)}
                    keyboardType="email-address"
                    autoCapitalize="none"
                  />
                </View>
              </Animated.View>
            )}

            <Animated.View style={[styles.buttonContainer, { transform: [{ translateY: buttonAnim }] }]}>
              <TouchableOpacity
                style={[styles.continueButton, (!isPhoneValid || loading) && styles.buttonDisabled]}
                onPress={handleSendCode}
                disabled={loading || !isPhoneValid}
              >
                <LinearGradient
                  colors={isPhoneValid && !loading ? ['#ff6b35', '#ff8c5a'] : ['#666', '#444']}
                  style={styles.buttonGradient}
                >
                  <Text style={styles.buttonText}>
                    {loading ? 'Sending...' : 'Send Code'}
                  </Text>
                </LinearGradient>
              </TouchableOpacity>
            </Animated.View>
          </>
        );

      case 2:
        return (
          <>
            <View style={styles.header}>
              <Text style={styles.emoji}>🔐</Text>
              <Text style={styles.title}>Enter Code</Text>
              <Text style={styles.subtitle}>
                We've sent a 6-digit code to{'\n'}
                {isUSPhone && formData.email ? formData.email : fullPhone}
              </Text>
            </View>

            <Animated.View style={[styles.inputContainer, { opacity: inputAnim }]}>
              <View style={styles.inputWrapper}>
                <Ionicons name="keypad-outline" size={20} color="rgba(255, 255, 255, 0.5)" />
                <TextInput
                  style={styles.input}
                  placeholder="Enter 6-digit Code"
                  placeholderTextColor="rgba(255, 255, 255, 0.5)"
                  value={formData.resetCode}
                  onChangeText={(value) => updateFormData('resetCode', value)}
                  keyboardType="numeric"
                  maxLength={6}
                  autoFocus
                />
              </View>
            </Animated.View>

            <Animated.View style={[styles.buttonContainer, { transform: [{ translateY: buttonAnim }] }]}>
              <TouchableOpacity
                style={styles.continueButton}
                onPress={handleVerifyCode}
                disabled={loading}
              >
                <LinearGradient colors={['#ff6b35', '#ff8c5a']} style={styles.buttonGradient}>
                  <Text style={styles.buttonText}>
                    {loading ? 'Verifying...' : 'Verify Code'}
                  </Text>
                </LinearGradient>
              </TouchableOpacity>
            </Animated.View>
          </>
        );

      case 3:
        return (
          <>
            <View style={styles.header}>
              <Text style={styles.emoji}>🔄</Text>
              <Text style={styles.title}>New Password</Text>
              <Text style={styles.subtitle}>Enter your new password</Text>
            </View>

            <Animated.View style={[styles.inputContainer, { opacity: inputAnim }]}>
              <View style={styles.inputWrapper}>
                <Ionicons name="lock-closed-outline" size={20} color="rgba(255, 255, 255, 0.5)" />
                <TextInput
                  key="newPassword"
                  style={styles.input}
                  placeholder="New Password"
                  placeholderTextColor="rgba(255, 255, 255, 0.5)"
                  value={localNewPassword}
                  onChangeText={setLocalNewPassword}
                  secureTextEntry={!showPassword}
                  autoFocus
                  editable={true}
                  selectTextOnFocus={true}
                  textContentType="newPassword"
                />
                <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                  <Ionicons 
                    name={showPassword ? "eye-off-outline" : "eye-outline"} 
                    size={20} 
                    color="rgba(255, 255, 255, 0.5)" 
                  />
                </TouchableOpacity>
              </View>
            </Animated.View>

            <Animated.View style={[styles.buttonContainer, { transform: [{ translateY: buttonAnim }] }]}>
              <TouchableOpacity
                style={styles.continueButton}
                onPress={handleResetPassword}
                disabled={loading}
              >
                <LinearGradient colors={['#ff6b35', '#ff8c5a']} style={styles.buttonGradient}>
                  <Text style={styles.buttonText}>
                    {loading ? 'Resetting...' : 'Reset Password'}
                  </Text>
                </LinearGradient>
              </TouchableOpacity>
            </Animated.View>
          </>
        );
    }
  };

  return (
    <>
      <ScrollView
        ref={scrollViewRef}
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigateToScreen('password', 'back')}
        >
          <Ionicons name="arrow-back" size={24} color="#ffffff" />
        </TouchableOpacity>

        <View style={styles.content}>{renderStep()}</View>
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
                  {selectedCountry.code === item.code ? (
                    <Ionicons name="checkmark" size={24} color="#4CAF50" />
                  ) : null}
                </TouchableOpacity>
              )}
            />
          </View>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingBottom: 150,
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
    minHeight: 600,
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
  buttonContainer: {
    marginBottom: 100,
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
    opacity: 0.85,
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