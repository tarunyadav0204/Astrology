import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Animated,
  Dimensions,
  Modal,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

import Ionicons from '@expo/vector-icons/Ionicons';
import { authAPI } from '../../services/api';
import { storage } from '../../services/storage';
import { COLORS } from '../../utils/constants';
import { useCredits } from '../../credits/CreditContext';

const { width, height } = Dimensions.get('window');

export default function LoginScreen({ navigation }) {
  const { refreshCredits } = useCredits();
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetData, setResetData] = useState({ phone: '', code: '', newPassword: '' });
  const [resetStep, setResetStep] = useState(1);
  const [resetToken, setResetToken] = useState('');
  const [showOtpVerification, setShowOtpVerification] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [registrationData, setRegistrationData] = useState(null);
  const [showBirthDetailsOption, setShowBirthDetailsOption] = useState(false);
  const [collectBirthDetails, setCollectBirthDetails] = useState(false);
  const [birthDetails, setBirthDetails] = useState({
    name: '',
    date: new Date().toISOString().split('T')[0],
    time: '12:00:00',
    place: '',
    latitude: null,
    longitude: null,
    timezone: 'Asia/Kolkata',
    gender: ''
  });
  const [debugInfo, setDebugInfo] = useState('');
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [errorModalData, setErrorModalData] = useState({ title: '', message: '', actions: [] });
  const [fadeAnim] = useState(new Animated.Value(0));
  const [slideAnim] = useState(new Animated.Value(50));

  useEffect(() => {
    checkAuthStatus();
    
    // Start entrance animation
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const checkAuthStatus = async () => {
    const token = await storage.getAuthToken();
    if (token) {
      // Check if user has existing birth details/charts
      try {
        const { chartAPI } = require('../../services/api');
        const response = await chartAPI.getExistingCharts();
        const hasCharts = response.data.charts && response.data.charts.length > 0;
        
        if (hasCharts) {
          navigation.navigate('SelectNative');
        } else {
          navigation.navigate('BirthForm');
        }
      } catch (error) {
        // If API fails, go to birth form
        navigation.navigate('BirthForm');
      }
    }
  };

  const handleAuth = async () => {
    if (!phone || !password || (!isLogin && (!name || !email))) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    console.log('🔐 Attempting auth with:', { phone, name: name || 'N/A', isLogin });
    setLoading(true);
    try {
      if (isLogin) {
        const response = await authAPI.login({ phone, password });
        console.log('✅ Login successful:', response.data);
        await storage.setAuthToken(response.data.access_token);
        await storage.setUserData(response.data.user);
        // Refresh credits after successful login
        await refreshCredits();
        
        // Check if user has self birth chart from login response
        if (response.data.self_birth_chart) {
          // User has self birth chart, go directly to main app
          navigation.navigate('SelectNative');
        } else {
          // Check if user has existing charts
          try {
            const { chartAPI } = require('../../services/api');
            const chartResponse = await chartAPI.getExistingCharts();
            const hasCharts = chartResponse.data.charts && chartResponse.data.charts.length > 0;
            
            if (hasCharts) {
              navigation.navigate('SelectNative');
            } else {
              navigation.navigate('BirthForm');
            }
          } catch (error) {
            // If API fails, go to birth form
            navigation.navigate('BirthForm');
          }
        }
      } else {
        // For registration, show birth details option first
        setRegistrationData({ name, phone, password, email });
        setBirthDetails(prev => ({ ...prev, name }));
        setShowBirthDetailsOption(true);
      }
    } catch (error) {
      let errorMessage = isLogin ? 'Login failed' : 'Registration failed';
      
      if (error.response?.status === 409) {
        // Phone already registered - show custom modal
        setErrorModalData({
          title: 'Phone Already Registered',
          message: 'This phone number is already registered. Please login instead.',
          actions: [
            { text: 'Cancel', style: 'cancel', onPress: () => setShowErrorModal(false) },
            { text: 'Switch to Login', style: 'primary', onPress: () => { setShowErrorModal(false); setIsLogin(true); } }
          ]
        });
        setShowErrorModal(true);
        return;
      }
      
      if (error.code === 'NETWORK_ERROR' || error.message.includes('Network')) {
        errorMessage = 'Network connection failed. Please check your internet connection.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      }
      
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleOtpVerification = async () => {
    if (!otpCode) {
      Alert.alert('Error', 'Please enter OTP code');
      return;
    }

    setLoading(true);
    try {
      // First verify OTP
      await authAPI.verifyResetCode({ phone: registrationData.phone, code: otpCode });
      
      // If OTP is valid, proceed with registration
      let response;
      if (collectBirthDetails && birthDetails.place && birthDetails.latitude && birthDetails.longitude) {
        // Register with birth details
        response = await authAPI.registerWithBirth({
          ...registrationData,
          birth_details: birthDetails
        });
      } else {
        // Regular registration
        response = await authAPI.register(registrationData);
      }
      
      await storage.setAuthToken(response.data.access_token);
      await storage.setUserData(response.data.user);
      
      // Navigate based on whether birth details were provided
      if (response.data.self_birth_chart) {
        // User has self birth chart, go directly to main app
        navigation.navigate('SelectNative');
      } else {
        // Go to birth form to add first profile
        navigation.navigate('BirthForm');
      }
    } catch (error) {
      Alert.alert('Error', error.response?.data?.message || 'Invalid OTP or registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSendCode = async () => {
    if (!resetData.phone) {
      Alert.alert('Error', 'Please enter phone number');
      return;
    }

    setLoading(true);
    try {
      const response = await authAPI.sendResetCode({ phone: resetData.phone });
      Alert.alert('Success', response.data.message);
      setResetStep(2);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.message || 'Phone number not found');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    if (!resetData.code) {
      Alert.alert('Error', 'Please enter verification code');
      return;
    }

    setLoading(true);
    try {
      const response = await authAPI.verifyResetCode({
        phone: resetData.phone,
        code: resetData.code
      });
      setResetToken(response.data.reset_token);
      Alert.alert('Success', 'Code verified! Enter new password.');
      setResetStep(3);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.message || 'Invalid or expired code');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!resetData.newPassword) {
      Alert.alert('Error', 'Please enter new password');
      return;
    }

    setLoading(true);
    try {
      await authAPI.resetPasswordWithToken({
        token: resetToken,
        new_password: resetData.newPassword
      });
      Alert.alert('Success', 'Password reset successfully!');
      setShowForgotPassword(false);
      setResetStep(1);
      setResetData({ phone: '', code: '', newPassword: '' });
      setResetToken('');
    } catch (error) {
      Alert.alert('Error', error.response?.data?.message || 'Password reset failed');
    } finally {
      setLoading(false);
    }
  };

  const handleBirthDetailsOption = async (withBirthDetails) => {
    setCollectBirthDetails(withBirthDetails);
    setShowBirthDetailsOption(false);
    
    // Send OTP for registration
    try {
      await authAPI.sendRegistrationOtp({ phone: registrationData.phone });
      setShowOtpVerification(true);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.message || 'Failed to send OTP');
    }
  };

  const searchPlaces = async (query) => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`,
        { headers: { 'User-Agent': 'AstrologyApp/1.0' } }
      );
      const data = await response.json();
      return data.map(item => ({
        id: item.place_id,
        name: item.display_name,
        latitude: parseFloat(item.lat),
        longitude: parseFloat(item.lon),
        timezone: 'Asia/Kolkata'
      }));
    } catch (error) {
      return [];
    }
  };

  const handlePlaceSelect = (place) => {
    setBirthDetails(prev => ({
      ...prev,
      place: place.name,
      latitude: place.latitude,
      longitude: place.longitude,
      timezone: place.timezone
    }));
  };

  if (showBirthDetailsOption) {
    return (
      <LinearGradient
        colors={[COLORS.gradientStart, COLORS.gradientEnd]}
        style={styles.container}
      >
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <View style={styles.formContainer}>
            <View style={styles.logoContainer}>
              <LinearGradient
                colors={[COLORS.primary, COLORS.secondary, '#ffb347']}
                style={styles.logoGradient}
              >
                <Text style={styles.logoEmoji}>🎯</Text>
              </LinearGradient>
              <Text style={styles.title}>Quick Setup</Text>
              <Text style={styles.subtitle}>Would you like to add your birth details now for instant chart access?</Text>
            </View>

            <View style={styles.optionContainer}>
              <TouchableOpacity
                style={styles.optionCard}
                onPress={() => handleBirthDetailsOption(true)}
              >
                <LinearGradient
                  colors={[COLORS.primary, COLORS.secondary]}
                  style={styles.optionGradient}
                >
                  <Text style={styles.optionIcon}>⚡</Text>
                  <Text style={styles.optionTitle}>Yes, Add Birth Details</Text>
                  <Text style={styles.optionSubtitle}>Skip the setup later and get instant access to your charts</Text>
                </LinearGradient>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.optionCard}
                onPress={() => handleBirthDetailsOption(false)}
              >
                <LinearGradient
                  colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                  style={styles.optionGradient}
                >
                  <Text style={styles.optionIcon}>⏭️</Text>
                  <Text style={styles.optionTitle}>Skip for Now</Text>
                  <Text style={styles.optionSubtitle}>Add birth details later when needed</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>

            <TouchableOpacity
              style={styles.switchButton}
              onPress={() => {
                setShowBirthDetailsOption(false);
                setRegistrationData(null);
              }}
            >
              <Text style={styles.switchText}>← Back to Registration</Text>
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
      </LinearGradient>
    );
  }

  if (showOtpVerification) {
    return (
      <LinearGradient
        colors={[COLORS.gradientStart, COLORS.gradientEnd]}
        style={styles.container}
      >
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <View style={styles.formContainer}>
            <View style={styles.logoContainer}>
              <LinearGradient
                colors={[COLORS.primary, COLORS.secondary, '#ffb347']}
                style={styles.logoGradient}
              >
                <Text style={styles.logoEmoji}>📱</Text>
              </LinearGradient>
              <Text style={styles.title}>Verify Phone</Text>
              <Text style={styles.subtitle}>We've sent a 6-digit code to {registrationData?.phone}</Text>
            </View>

            <View style={styles.inputContainer}>
              <View style={styles.inputWrapper}>
                <Ionicons name="keypad-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
                <TextInput
                  style={styles.modernInput}
                  placeholder="Enter 6-digit OTP"
                  placeholderTextColor={COLORS.textSecondary}
                  value={otpCode}
                  onChangeText={setOtpCode}
                  keyboardType="numeric"
                  maxLength={6}
                />
              </View>
              
              {collectBirthDetails && (
                <>
                  <View style={styles.birthDetailsSection}>
                    <Text style={styles.sectionTitle}>Birth Details (Optional)</Text>
                    
                    <View style={styles.inputWrapper}>
                      <Ionicons name="calendar-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
                      <TextInput
                        style={styles.modernInput}
                        placeholder="Birth Date (YYYY-MM-DD)"
                        placeholderTextColor={COLORS.textSecondary}
                        value={birthDetails.date}
                        onChangeText={(value) => setBirthDetails(prev => ({ ...prev, date: value }))}
                      />
                    </View>
                    
                    <View style={styles.inputWrapper}>
                      <Ionicons name="time-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
                      <TextInput
                        style={styles.modernInput}
                        placeholder="Birth Time (HH:MM:SS)"
                        placeholderTextColor={COLORS.textSecondary}
                        value={birthDetails.time}
                        onChangeText={(value) => setBirthDetails(prev => ({ ...prev, time: value }))}
                      />
                    </View>
                    
                    <View style={styles.inputWrapper}>
                      <Ionicons name="location-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
                      <TextInput
                        style={styles.modernInput}
                        placeholder="Birth Place (City, Country)"
                        placeholderTextColor={COLORS.textSecondary}
                        value={birthDetails.place}
                        onChangeText={async (value) => {
                          setBirthDetails(prev => ({ ...prev, place: value, latitude: null, longitude: null }));
                          if (value.length >= 3) {
                            const places = await searchPlaces(value);
                            if (places.length > 0) {
                              handlePlaceSelect(places[0]);
                            }
                          }
                        }}
                      />
                    </View>
                    
                    <View style={styles.genderRow}>
                      <TouchableOpacity
                        style={[styles.genderButton, birthDetails.gender === 'Male' && styles.genderButtonSelected]}
                        onPress={() => setBirthDetails(prev => ({ ...prev, gender: 'Male' }))}
                      >
                        <Text style={[styles.genderButtonText, birthDetails.gender === 'Male' && styles.genderButtonTextSelected]}>Male</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={[styles.genderButton, birthDetails.gender === 'Female' && styles.genderButtonSelected]}
                        onPress={() => setBirthDetails(prev => ({ ...prev, gender: 'Female' }))}
                      >
                        <Text style={[styles.genderButtonText, birthDetails.gender === 'Female' && styles.genderButtonTextSelected]}>Female</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                </>
              )}
              
              <TouchableOpacity
                style={[styles.modernButton, loading && styles.buttonDisabled]}
                onPress={handleOtpVerification}
                disabled={loading}
              >
                <LinearGradient
                  colors={loading ? ['#ccc', '#999'] : [COLORS.primary, COLORS.secondary]}
                  style={styles.buttonGradient}
                >
                  <Text style={styles.buttonText}>
                    {loading ? 'Creating Account...' : 'Verify & Continue'}
                  </Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>

            <TouchableOpacity
              style={styles.switchButton}
              onPress={() => {
                setShowOtpVerification(false);
                setOtpCode('');
                if (collectBirthDetails) {
                  setShowBirthDetailsOption(true);
                } else {
                  setRegistrationData(null);
                }
              }}
            >
              <Text style={styles.switchText}>← Back</Text>
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
      </LinearGradient>
    );
  }

  if (showForgotPassword) {
    return (
      <LinearGradient
        colors={[COLORS.gradientStart, COLORS.gradientEnd]}
        style={styles.container}
      >
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <ScrollView 
            contentContainerStyle={styles.scrollContainer}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
          >
            <View style={styles.formContainer}>
              <View style={styles.logoContainer}>
                <LinearGradient
                  colors={[COLORS.primary, COLORS.secondary, '#ffb347']}
                  style={styles.logoGradient}
                >
                  <Text style={styles.logoEmoji}>🔐</Text>
                </LinearGradient>
                <Text style={styles.title}>Reset Password</Text>
                <Text style={styles.subtitle}>Secure your cosmic journey</Text>
              </View>

              {resetStep === 1 ? (
                <View style={styles.inputContainer}>
                  <View style={styles.inputWrapper}>
                    <Ionicons name="call-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
                    <TextInput
                      style={styles.modernInput}
                      placeholder="Phone Number"
                      placeholderTextColor={COLORS.textSecondary}
                      value={resetData.phone}
                      onChangeText={(value) => setResetData(prev => ({ ...prev, phone: value }))}
                      keyboardType="phone-pad"
                    />
                  </View>
                  <TouchableOpacity
                    style={[styles.modernButton, loading && styles.buttonDisabled]}
                    onPress={handleSendCode}
                    disabled={loading}
                  >
                    <LinearGradient
                      colors={loading ? ['#ccc', '#999'] : [COLORS.primary, COLORS.secondary]}
                      style={styles.buttonGradient}
                    >
                      <Text style={styles.buttonText}>
                        {loading ? '📤 Sending...' : '📤 Send Code'}
                      </Text>
                    </LinearGradient>
                  </TouchableOpacity>
                </View>
              ) : resetStep === 2 ? (
                <View style={styles.inputContainer}>
                  <View style={styles.inputWrapper}>
                    <Ionicons name="keypad-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
                    <TextInput
                      style={styles.modernInput}
                      placeholder="Enter 6-digit Code"
                      placeholderTextColor={COLORS.textSecondary}
                      value={resetData.code}
                      onChangeText={(value) => setResetData(prev => ({ ...prev, code: value }))}
                      keyboardType="numeric"
                      maxLength={6}
                    />
                  </View>
                  <TouchableOpacity
                    style={[styles.modernButton, loading && styles.buttonDisabled]}
                    onPress={handleVerifyCode}
                    disabled={loading}
                  >
                    <LinearGradient
                      colors={loading ? ['#ccc', '#999'] : [COLORS.primary, COLORS.secondary]}
                      style={styles.buttonGradient}
                    >
                      <Text style={styles.buttonText}>
                        {loading ? '🔍 Verifying...' : '🔍 Verify Code'}
                      </Text>
                    </LinearGradient>
                  </TouchableOpacity>
                </View>
              ) : (
                <View style={styles.inputContainer}>
                  <View style={styles.inputWrapper}>
                    <Ionicons name="lock-closed-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
                    <TextInput
                      style={styles.modernInput}
                      placeholder="New Password"
                      placeholderTextColor={COLORS.textSecondary}
                      value={resetData.newPassword}
                      onChangeText={(value) => setResetData(prev => ({ ...prev, newPassword: value }))}
                      secureTextEntry
                    />
                  </View>
                  <TouchableOpacity
                    style={[styles.modernButton, loading && styles.buttonDisabled]}
                    onPress={handleResetPassword}
                    disabled={loading}
                  >
                    <LinearGradient
                      colors={loading ? ['#ccc', '#999'] : [COLORS.primary, COLORS.secondary]}
                      style={styles.buttonGradient}
                    >
                      <Text style={styles.buttonText}>
                        {loading ? '🔄 Resetting...' : '🔄 Reset Password'}
                      </Text>
                    </LinearGradient>
                  </TouchableOpacity>
                </View>
              )}

              <TouchableOpacity
                style={styles.switchButton}
                onPress={() => {
                  setShowForgotPassword(false);
                  setResetStep(1);
                  setResetData({ phone: '', code: '', newPassword: '' });
                  setResetToken('');
                }}
              >
                <Text style={styles.switchText}>← Back to Login</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </LinearGradient>
    );
  }

  return (
    <LinearGradient
      colors={[COLORS.gradientStart, COLORS.gradientEnd]}
      style={styles.container}
    >
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContainer}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <Animated.View 
            style={[
              styles.animatedContainer,
              {
                opacity: fadeAnim,
                transform: [{ translateY: slideAnim }]
              }
            ]}
          >
            <View style={styles.formContainer}>
              <View style={styles.logoContainer}>
                <LinearGradient
                  colors={[COLORS.primary, COLORS.secondary, '#ffb347']}
                  style={styles.logoGradient}
                >
                  <Text style={styles.logoEmoji}>🔮</Text>
                </LinearGradient>
                <Text style={styles.title}>AstroRoshni</Text>
                <Text style={styles.subtitle}>Unlock Your Cosmic Journey</Text>
              </View>

              <View style={styles.inputContainer}>
                {!isLogin && (
                  <>
                    <View style={styles.inputWrapper}>
                      <Ionicons name="person-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
                      <TextInput
                        style={styles.modernInput}
                        placeholder="Full Name"
                        placeholderTextColor={COLORS.textSecondary}
                        value={name}
                        onChangeText={setName}
                        autoComplete="name"
                      />
                    </View>
                    <View style={styles.inputWrapper}>
                      <Ionicons name="mail-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
                      <TextInput
                        style={styles.modernInput}
                        placeholder="Email Address"
                        placeholderTextColor={COLORS.textSecondary}
                        value={email}
                        onChangeText={setEmail}
                        keyboardType="email-address"
                        autoComplete="email"
                        autoCapitalize="none"
                      />
                    </View>
                  </>
                )}
                
                <View style={styles.inputWrapper}>
                  <Ionicons name="call-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
                  <TextInput
                    style={styles.modernInput}
                    placeholder="Phone Number"
                    placeholderTextColor={COLORS.textSecondary}
                    value={phone}
                    onChangeText={setPhone}
                    keyboardType="phone-pad"
                    autoComplete="tel"
                  />
                </View>
                
                <View style={styles.inputWrapper}>
                  <Ionicons name="lock-closed-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
                  <TextInput
                    style={[styles.modernInput, styles.passwordInput]}
                    placeholder="Password"
                    placeholderTextColor={COLORS.textSecondary}
                    value={password}
                    onChangeText={setPassword}
                    secureTextEntry={!showPassword}
                    autoComplete="current-password"
                  />
                  <TouchableOpacity
                    style={styles.eyeButton}
                    onPress={() => setShowPassword(!showPassword)}
                  >
                    <Ionicons 
                      name={showPassword ? 'eye-off-outline' : 'eye-outline'} 
                      size={20} 
                      color={COLORS.textSecondary} 
                    />
                  </TouchableOpacity>
                </View>
              </View>

              <TouchableOpacity
                style={[styles.modernButton, loading && styles.buttonDisabled]}
                onPress={handleAuth}
                disabled={loading}
              >
                <LinearGradient
                  colors={loading ? ['#ccc', '#999'] : [COLORS.primary, COLORS.secondary]}
                  style={styles.buttonGradient}
                >
                  {loading ? (
                    <View style={styles.loadingContainer}>
                      <Text style={styles.loadingDot}>●</Text>
                      <Text style={styles.loadingDot}>●</Text>
                      <Text style={styles.loadingDot}>●</Text>
                    </View>
                  ) : (
                    <Text style={styles.buttonText}>
                      {isLogin ? '✨ Sign In' : '🚀 Create Account'}
                    </Text>
                  )}
                </LinearGradient>
              </TouchableOpacity>

              <View style={styles.actionContainer}>
                {isLogin && (
                  <TouchableOpacity
                    style={styles.forgotButton}
                    onPress={() => setShowForgotPassword(true)}
                  >
                    <Text style={styles.forgotText}>Forgot Password?</Text>
                  </TouchableOpacity>
                )}

                <TouchableOpacity
                  style={styles.switchButton}
                  onPress={() => setIsLogin(!isLogin)}
                >
                  <Text style={styles.switchText}>
                    {isLogin ? "New here? Create Account" : "Already a member? Sign In"}
                  </Text>
                </TouchableOpacity>
              </View>
              
              {debugInfo ? (
                <View style={styles.debugContainer}>
                  <Text style={styles.debugText}>{debugInfo}</Text>
                  <TouchableOpacity onPress={() => setDebugInfo('')}>
                    <Text style={styles.clearDebug}>Clear</Text>
                  </TouchableOpacity>
                </View>
              ) : null}
            </View>
          </Animated.View>
        </ScrollView>
      </KeyboardAvoidingView>
      
      {/* Error Modal */}
      <Modal
        visible={showErrorModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowErrorModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.errorModalContent}>
            <Text style={styles.errorModalTitle}>{errorModalData.title}</Text>
            <Text style={styles.errorModalMessage}>{errorModalData.message}</Text>
            
            <View style={styles.errorModalActions}>
              {errorModalData.actions.map((action, index) => (
                <TouchableOpacity
                  key={index}
                  style={[
                    styles.errorModalButton,
                    action.style === 'primary' ? styles.errorModalButtonPrimary : styles.errorModalButtonSecondary
                  ]}
                  onPress={action.onPress}
                >
                  <Text style={[
                    styles.errorModalButtonText,
                    action.style === 'primary' ? styles.errorModalButtonTextPrimary : styles.errorModalButtonTextSecondary
                  ]}>
                    {action.text}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>
      </Modal>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  backgroundGradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
  orb: {
    position: 'absolute',
    borderRadius: 100,
    opacity: 0.1,
  },
  orb1: {
    width: 200,
    height: 200,
    backgroundColor: COLORS.primary,
    top: -50,
    right: -50,
  },
  orb2: {
    width: 150,
    height: 150,
    backgroundColor: COLORS.secondary,
    bottom: 100,
    left: -30,
  },
  orb3: {
    width: 100,
    height: 100,
    backgroundColor: '#ffb347',
    top: height * 0.3,
    right: 50,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  animatedContainer: {
    width: '100%',
  },
  glassContainer: {
    borderRadius: 25,
    overflow: 'hidden',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  formContainer: {
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    padding: 30,
    margin: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logoGradient: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  logoEmoji: {
    fontSize: 35,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.textSecondary,
    textAlign: 'center',
    fontWeight: '300',
  },
  inputContainer: {
    width: '100%',
    marginBottom: 30,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    marginBottom: 15,
    paddingHorizontal: 15,
    borderWidth: 1,
    borderColor: COLORS.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  inputIcon: {
    marginRight: 10,
  },
  modernInput: {
    flex: 1,
    padding: 15,
    fontSize: 16,
    color: COLORS.textPrimary,
    fontWeight: '400',
  },
  passwordInput: {
    paddingRight: 45,
  },
  eyeButton: {
    position: 'absolute',
    right: 15,
    padding: 5,
  },
  modernButton: {
    width: '100%',
    marginBottom: 25,
    borderRadius: 15,
    overflow: 'hidden',
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 15,
    elevation: 8,
  },
  buttonGradient: {
    paddingVertical: 18,
    paddingHorizontal: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  loadingDot: {
    color: 'white',
    fontSize: 8,
    marginHorizontal: 2,
    opacity: 0.7,
  },
  actionContainer: {
    alignItems: 'center',
    width: '100%',
  },
  forgotButton: {
    padding: 12,
    marginBottom: 15,
  },
  forgotText: {
    color: COLORS.accent,
    fontSize: 14,
    fontWeight: '500',
    textDecorationLine: 'underline',
  },
  switchButton: {
    padding: 12,
    backgroundColor: COLORS.lightGray,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  switchText: {
    color: COLORS.textPrimary,
    fontSize: 14,
    fontWeight: '500',
    textAlign: 'center',
  },
  debugContainer: {
    marginTop: 20,
    padding: 15,
    backgroundColor: COLORS.lightGray,
    borderRadius: 12,
    width: '100%',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  debugText: {
    fontSize: 10,
    color: COLORS.textSecondary,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  clearDebug: {
    color: COLORS.primary,
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorModalContent: {
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    padding: 24,
    margin: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  errorModalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.error,
    marginBottom: 12,
    textAlign: 'center',
  },
  errorModalMessage: {
    fontSize: 16,
    color: COLORS.textPrimary,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 22,
  },
  errorModalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  errorModalButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
    minWidth: 80,
  },
  errorModalButtonPrimary: {
    backgroundColor: COLORS.accent,
  },
  errorModalButtonSecondary: {
    backgroundColor: COLORS.lightGray,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  errorModalButtonText: {
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  errorModalButtonTextPrimary: {
    color: COLORS.white,
  },
  errorModalButtonTextSecondary: {
    color: COLORS.textPrimary,
  },
  optionContainer: {
    width: '100%',
    gap: 16,
    marginBottom: 30,
  },
  optionCard: {
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 5,
  },
  optionGradient: {
    padding: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 16,
  },
  optionIcon: {
    fontSize: 32,
    marginBottom: 12,
  },
  optionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 8,
    textAlign: 'center',
  },
  optionSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    lineHeight: 20,
  },
  birthDetailsSection: {
    width: '100%',
    marginTop: 20,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 15,
    textAlign: 'center',
  },
  genderRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 10,
  },
  genderButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: COLORS.lightGray,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  genderButtonSelected: {
    backgroundColor: COLORS.accent,
    borderColor: COLORS.accent,
  },
  genderButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.textPrimary,
  },
  genderButtonTextSelected: {
    color: COLORS.white,
  },
});