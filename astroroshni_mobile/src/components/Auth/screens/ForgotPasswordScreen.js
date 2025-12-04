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
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../../utils/constants';
import { authAPI } from '../../../services/api';

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
    if (!formData.phone) {
      Alert.alert('Error', 'Please enter phone number');
      return;
    }

    setLoading(true);
    try {
      const response = await authAPI.sendResetCode({ phone: formData.phone });
      Alert.alert('Success', response.data.message);
      setStep(2);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.message || 'Phone number not found');
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
        phone: formData.phone,
        code: formData.resetCode
      });
      setResetToken(response.data.reset_token);
      setLocalNewPassword(''); // Reset password field
      Alert.alert('Success', 'Code verified! Enter new password.');
      setStep(3);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.message || 'Invalid or expired code');
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
      Alert.alert('Error', error.response?.data?.message || 'Password reset failed');
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
              <Text style={styles.subtitle}>Enter your phone number to receive a reset code</Text>
            </View>

            <Animated.View style={[styles.inputContainer, { opacity: inputAnim }]}>
              <View style={styles.inputWrapper}>
                <Ionicons name="call-outline" size={20} color="rgba(255, 255, 255, 0.5)" />
                <TextInput
                  style={styles.input}
                  placeholder="Phone Number"
                  placeholderTextColor="rgba(255, 255, 255, 0.5)"
                  value={formData.phone}
                  onChangeText={(value) => updateFormData('phone', value)}
                  keyboardType="phone-pad"
                  autoFocus
                />
              </View>
            </Animated.View>

            <Animated.View style={[styles.buttonContainer, { transform: [{ translateY: buttonAnim }] }]}>
              <TouchableOpacity
                style={styles.continueButton}
                onPress={handleSendCode}
                disabled={loading}
              >
                <LinearGradient colors={['#ff6b35', '#ff8c5a']} style={styles.buttonGradient}>
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
              <Text style={styles.subtitle}>We've sent a 6-digit code to {formData.phone}</Text>
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

      <View style={styles.content}>
        {renderStep()}
      </View>
    </ScrollView>
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
    gap: 12,
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