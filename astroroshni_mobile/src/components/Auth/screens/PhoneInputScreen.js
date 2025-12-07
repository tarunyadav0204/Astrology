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

export default function PhoneInputScreen({ 
  formData, 
  updateFormData, 
  navigateToScreen, 
  isLogin 
}) {
  const [loading, setLoading] = useState(false);
  const [isValid, setIsValid] = useState(false);
  
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
  }, []);

  useEffect(() => {
    setIsValid(formData.phone.length >= 10);
  }, [formData.phone]);

  const handleContinue = async () => {
    if (!isValid) return;
    
    if (isLogin) {
      navigateToScreen('password');
    } else {
      // Check if phone exists by trying to send registration OTP
      setLoading(true);
      // console.log('🔍 Starting phone validation for:', formData.phone);
      // console.log('📡 API Request - Phone:', formData.phone);
      // console.log('🌐 Network info - API Base URL:', require('../../../utils/constants').API_BASE_URL);
      
      const startTime = Date.now();
      try {
        // console.log('⏱️ Sending API request at:', new Date().toISOString());
        
        // Add network connectivity check
        // console.log('🔍 Checking network connectivity...');
        
        const response = await authAPI.sendRegistrationOtp({ phone: formData.phone });
        const endTime = Date.now();
        
        // console.log('✅ API Response received in', endTime - startTime, 'ms');
        // console.log('📥 Response status:', response.status);
        // console.log('📥 Response data:', response.data);
        
        // Store dev OTP code if available
        if (response.data.dev_code) {
          // console.log('📱 Development OTP Code:', response.data.dev_code);
          updateFormData('devOtpCode', response.data.dev_code);
        }
        
        // If successful, phone doesn't exist, continue to OTP verification
        navigateToScreen('otp');
      } catch (error) {
        const endTime = Date.now();
        // console.log('❌ API Error after', endTime - startTime, 'ms');
        // console.log('📥 Error code:', error.code);
        // console.log('📥 Error status:', error.response?.status);
        // console.log('📥 Error data:', error.response?.data);
        // console.log('📥 Error message:', error.message);
        // console.log('📥 Error config URL:', error.config?.url);
        // console.log('📥 Error config method:', error.config?.method);
        // console.log('📥 Error config timeout:', error.config?.timeout);
        
        if (error.code === 'ECONNABORTED') {
          Alert.alert('Timeout Error', 'Request timed out. Please check your internet connection and try again.');
        } else if (error.code === 'NETWORK_ERROR' || error.message.includes('Network Error')) {
          Alert.alert('Network Error', 'Unable to connect to server. Please check your internet connection.');
        } else if (error.response?.status === 409) {
          Alert.alert('Phone Already Registered', 'This phone number is already registered. Please sign in instead.');
        } else {
          Alert.alert('Error', `Unable to verify phone number: ${error.message}. Please try again.`);
        }
      } finally {
        setLoading(false);
        // console.log('🏁 Phone validation completed');
      }
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
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
            {isLogin ? "Enter your phone number to sign in" : "We'll send you a verification code"}
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
            <View style={styles.countryCode}>
              <Text style={styles.countryText}>🇮🇳 +91</Text>
            </View>
            <TextInput
              style={styles.input}
              placeholder="Phone Number"
              placeholderTextColor="rgba(255, 255, 255, 0.5)"
              value={formData.phone}
              onChangeText={(value) => updateFormData('phone', value)}
              keyboardType="phone-pad"
              autoFocus
              maxLength={10}
            />
            {isValid && (
              <Ionicons name="checkmark-circle" size={24} color="#4CAF50" />
            )}
          </View>
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
  footer: {
    paddingBottom: 40,
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