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
import { BlurView } from 'expo-blur';
import { Ionicons } from '@expo/vector-icons';
import { authAPI } from '../../services/api';
import { storage } from '../../services/storage';
import { COLORS } from '../../utils/constants';

const { width, height } = Dimensions.get('window');

export default function LoginScreen({ navigation }) {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
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
      navigation.replace('Chat');
    }
  };

  const handleAuth = async () => {
    if (!phone || !password || (!isLogin && !name)) {
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
        navigation.replace('Chat');
      } else {
        // For registration, send OTP using registration endpoint
        setRegistrationData({ name, phone, password });
        await authAPI.sendRegistrationOtp({ phone });
        setShowOtpVerification(true);
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
      const response = await authAPI.register(registrationData);
      console.log('✅ Registration successful:', response.data);
      await storage.setAuthToken(response.data.access_token);
      await storage.setUserData(response.data.user);
      
      navigation.replace('Chat');
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
    justifyContent: 'center',
    padding: 20,
  },
  animatedContainer: {
    flex: 1,
    justifyContent: 'center',
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
});