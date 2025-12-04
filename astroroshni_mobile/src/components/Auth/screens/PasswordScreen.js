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
  ScrollView,
  Keyboard,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../../utils/constants';
import { authAPI } from '../../../services/api';
import { storage } from '../../../services/storage';
import { useCredits } from '../../../credits/CreditContext';

export default function PasswordScreen({ 
  formData, 
  updateFormData, 
  navigateToScreen, 
  isLogin,
  navigation 
}) {
  const { refreshCredits } = useCredits();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isValid, setIsValid] = useState(false);
  
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
    setIsValid(formData.password.length >= 6);
  }, [formData.password]);

  useEffect(() => {
    const keyboardDidShowListener = Keyboard.addListener('keyboardDidShow', () => {
      if (scrollViewRef.current && isLogin) {
        scrollViewRef.current.scrollToEnd({ animated: true });
      }
    });

    return () => {
      keyboardDidShowListener?.remove();
    };
  }, [isLogin]);

  const handleContinue = async () => {
    if (!isValid) return;
    
    setLoading(true);
    try {
      if (isLogin) {
        const response = await authAPI.login({ 
          phone: formData.phone, 
          password: formData.password 
        });
        
        await storage.setAuthToken(response.data.access_token);
        await storage.setUserData(response.data.user);
        await refreshCredits();
        
        // Navigate based on self_birth_chart
        if (response.data.self_birth_chart) {
          navigation.replace('Home');
        } else {
          // Check existing charts
          try {
            const { chartAPI } = require('../../../services/api');
            const chartResponse = await chartAPI.getExistingCharts();
            const hasCharts = chartResponse.data.charts && chartResponse.data.charts.length > 0;
            
            if (hasCharts) {
              navigation.replace('SelectNative');
            } else {
              navigation.replace('BirthForm');
            }
          } catch (error) {
            navigation.replace('BirthForm');
          }
        }
      } else {
        // Registration complete - register user and navigate to birth form
        try {
          const response = await authAPI.registerWithBirth({
            name: formData.name,
            phone: formData.phone,
            password: formData.password,
            email: formData.email,
            role: 'user'
          });
          
          await storage.setAuthToken(response.data.access_token);
          await storage.setUserData(response.data.user);
          await refreshCredits();
          
          // Navigate to welcome screen after successful registration
          navigateToScreen('welcomeAfterRegistration');
        } catch (error) {
          if (error.response?.status === 400 && error.response?.data?.detail?.includes('already registered')) {
            // User already exists, navigate to welcome screen
            navigateToScreen('welcomeAfterRegistration');
          } else {
            Alert.alert('Registration Error', error.response?.data?.detail || 'Registration failed');
          }
        }
      }
    } catch (error) {
      Alert.alert('Error', error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView 
        ref={scrollViewRef}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => navigateToScreen('phone', 'back')}
        >
          <Ionicons name="arrow-back" size={24} color="#ffffff" />
        </TouchableOpacity>

        <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.emoji}>🔐</Text>
          <Text style={styles.title}>
            {isLogin ? "Enter your password" : "Create a password"}
          </Text>
          <Text style={styles.subtitle}>
            {isLogin 
              ? "Welcome back to your cosmic journey" 
              : "Choose a strong password to secure your account"
            }
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
            <Ionicons name="lock-closed-outline" size={20} color="rgba(255, 255, 255, 0.5)" />
            <TextInput
              style={styles.input}
              placeholder="Password"
              placeholderTextColor="rgba(255, 255, 255, 0.5)"
              value={formData.password}
              onChangeText={(value) => updateFormData('password', value)}
              secureTextEntry={!showPassword}
              autoFocus
            />
            <TouchableOpacity
              onPress={() => setShowPassword(!showPassword)}
              style={styles.eyeButton}
            >
              <Ionicons 
                name={showPassword ? 'eye-off-outline' : 'eye-outline'} 
                size={20} 
                color="rgba(255, 255, 255, 0.5)" 
              />
            </TouchableOpacity>
            {isValid && (
              <Ionicons name="checkmark-circle" size={24} color="#4CAF50" />
            )}
          </View>
          
          {!isLogin && (
            <View style={styles.strengthContainer}>
              <View style={styles.strengthBar}>
                <View 
                  style={[
                    styles.strengthFill,
                    { 
                      width: `${Math.min((formData.password.length / 8) * 100, 100)}%`,
                      backgroundColor: formData.password.length < 6 ? '#FF5722' : 
                                     formData.password.length < 8 ? '#FF9800' : '#4CAF50'
                    }
                  ]} 
                />
              </View>
              <Text style={styles.strengthText}>
                {formData.password.length < 6 ? 'Weak' : 
                 formData.password.length < 8 ? 'Good' : 'Strong'}
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
            onPress={handleContinue}
            disabled={!isValid || loading}
          >
            <LinearGradient
              colors={isValid ? ['#ff6b35', '#ff8c5a'] : ['#666', '#444']}
              style={styles.buttonGradient}
            >
              <Text style={styles.buttonText}>
                {loading ? (isLogin ? 'Signing In...' : 'Continue') : (isLogin ? 'Sign In' : 'Continue')}
              </Text>
              <Ionicons name="arrow-forward" size={20} color="#ffffff" />
            </LinearGradient>
          </TouchableOpacity>
        </Animated.View>

        {isLogin && (
          <TouchableOpacity 
            style={styles.forgotButton}
            onPress={() => navigateToScreen('forgotPassword')}
          >
            <Text style={styles.forgotText}>Forgot Password?</Text>
          </TouchableOpacity>
        )}
        </View>
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
  },
  eyeButton: {
    padding: 4,
  },
  strengthContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    gap: 12,
  },
  strengthBar: {
    flex: 1,
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 2,
    overflow: 'hidden',
  },
  strengthFill: {
    height: '100%',
    borderRadius: 2,
  },
  strengthText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    fontWeight: '500',
  },
  buttonContainer: {
    marginBottom: 20,
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
  forgotButton: {
    alignItems: 'center',
    paddingVertical: 12,
  },
  forgotText: {
    color: '#ff6b35',
    fontSize: 14,
    fontWeight: '500',
  },
});