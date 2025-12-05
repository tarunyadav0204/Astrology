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
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../../utils/constants';
import { authAPI } from '../../../services/api';

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
  
  const inputAnim = useRef(new Animated.Value(0)).current;
  const buttonAnim = useRef(new Animated.Value(50)).current;

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

  const handleVerifyOTP = async () => {
    if (!isValid) return;
    
    setLoading(true);
    try {
      // For now, just proceed to next screen
      // In production, you'd verify the OTP with backend
      console.log('Verifying OTP:', formData.otpCode);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Continue to name screen for registration
      navigateToScreen('name');
    } catch (error) {
      Alert.alert('Error', 'Invalid OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    if (resendTimer > 0) return;
    
    try {
      const response = await authAPI.sendRegistrationOtp({ phone: formData.phone });
      setResendTimer(30);
      
      // Show dev OTP code if available
      if (response.data.dev_code) {
        setDevOtpCode(response.data.dev_code);
      }
      
      Alert.alert('Success', 'OTP sent successfully!');
    } catch (error) {
      Alert.alert('Error', 'Failed to resend OTP. Please try again.');
    }
  };

  // Show dev OTP on initial load if available from previous API call
  useEffect(() => {
    console.log('📱 OTP Screen loaded for phone:', formData.phone);
    
    if (formData.devOtpCode) {
      console.log('📱 Development OTP Code available:', formData.devOtpCode);
      setDevOtpCode(formData.devOtpCode);
    } else {
      console.log('💡 Check backend logs for development OTP code');
    }
  }, [formData.devOtpCode]);

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={0}
    >
      <TouchableOpacity 
        style={styles.backButton}
        onPress={() => navigateToScreen('phone', 'back')}
      >
        <Ionicons name="arrow-back" size={24} color="#ffffff" />
      </TouchableOpacity>

      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.emoji}>📱</Text>
          <Text style={styles.title}>Enter OTP</Text>
          <Text style={styles.subtitle}>
            We've sent a 6-digit code to{"\n"}
            +91 {formData.phone}
          </Text>
          {devOtpCode && (
            <View style={styles.devCodeContainer}>
              <Text style={styles.devCodeLabel}>Development OTP:</Text>
              <Text style={styles.devCodeText}>{devOtpCode}</Text>
            </View>
          )}
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
            <TextInput
              style={styles.input}
              placeholder="Enter 6-digit OTP"
              placeholderTextColor="rgba(255, 255, 255, 0.5)"
              value={formData.otpCode}
              onChangeText={(value) => updateFormData('otpCode', value.replace(/[^0-9]/g, ''))}
              keyboardType="numeric"
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
            onPress={handleVerifyOTP}
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
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 20,
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
    letterSpacing: 8,
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
    marginBottom: 40,
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