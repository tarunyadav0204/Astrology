import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAstrology } from '../context/AstrologyContext';
import { apiService } from '../services/apiService';

export default function LoginScreen({ navigation }) {
  const [formData, setFormData] = useState({
    phone: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetData, setResetData] = useState({ phone: '', code: '', newPassword: '' });
  const [resetStep, setResetStep] = useState(1);
  const [resetToken, setResetToken] = useState('');
  const { login } = useAstrology();

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleLogin = async () => {
    if (!formData.phone || !formData.password) {
      Alert.alert('Error', 'Please fill all fields');
      return;
    }

    if (loading) {
      return; // Prevent multiple simultaneous requests
    }

    setLoading(true);
    try {
      console.log('Starting login process...');
      const response = await login(formData);
      console.log('Login successful, navigating...');
      
      // Navigate to chart list
      navigation.reset({
        index: 0,
        routes: [{ name: 'ChartList' }],
      });
    } catch (error) {
      console.error('Login failed:', error.message);
      Alert.alert('Login Failed', error.message || 'Please check your credentials and try again');
    } finally {
      setLoading(false);
    }
  };

  const handleSendCode = async () => {
    if (!resetData.phone) {
      Alert.alert('Error', 'Please enter your phone number');
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.sendResetCode({ phone: resetData.phone });
      Alert.alert('Success', response.message || 'Reset code sent successfully');
      setResetStep(2);
    } catch (error) {
      Alert.alert('Error', error.message || 'Phone number not found');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    if (!resetData.code) {
      Alert.alert('Error', 'Please enter the verification code');
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.verifyResetCode({
        phone: resetData.phone,
        code: resetData.code
      });
      setResetToken(response.reset_token);
      Alert.alert('Success', 'Code verified! Enter new password.');
      setResetStep(3);
    } catch (error) {
      Alert.alert('Error', error.message || 'Invalid or expired code');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!resetData.newPassword) {
      Alert.alert('Error', 'Please enter a new password');
      return;
    }

    setLoading(true);
    try {
      await apiService.resetPasswordWithToken({
        token: resetToken,
        new_password: resetData.newPassword
      });
      Alert.alert('Success', 'Password reset successfully!');
      setShowForgotPassword(false);
      setResetStep(1);
      setResetData({ phone: '', code: '', newPassword: '' });
      setResetToken('');
    } catch (error) {
      Alert.alert('Error', error.message || 'Password reset failed');
    } finally {
      setLoading(false);
    }
  };

  if (showForgotPassword) {
    return (
      <SafeAreaView style={styles.container}>
        <LinearGradient
          colors={['#e91e63', '#ff6f00']}
          style={styles.gradient}
        >
          <KeyboardAvoidingView 
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.keyboardView}
          >
            <View style={styles.content}>
              <View style={styles.header}>
                <Text style={styles.title}>🔐 Reset Password</Text>
                <Text style={styles.subtitle}>
                  {resetStep === 1 ? 'Enter your phone number' : 
                   resetStep === 2 ? 'Enter verification code' : 'Enter new password'}
                </Text>
              </View>

              <View style={styles.form}>
                {resetStep === 1 && (
                  <>
                    <View style={styles.inputGroup}>
                      <Text style={styles.label}>Phone Number</Text>
                      <TextInput
                        style={styles.input}
                        value={resetData.phone}
                        onChangeText={(value) => setResetData(prev => ({ ...prev, phone: value }))}
                        placeholder="Enter your phone number"
                        placeholderTextColor="#999"
                        keyboardType="phone-pad"
                      />
                    </View>
                    <TouchableOpacity 
                      style={[styles.loginButton, loading && styles.disabledButton]}
                      onPress={handleSendCode}
                      disabled={loading}
                    >
                      <Text style={styles.loginButtonText}>
                        {loading ? 'Sending...' : 'Send Code'}
                      </Text>
                    </TouchableOpacity>
                  </>
                )}

                {resetStep === 2 && (
                  <>
                    <View style={styles.inputGroup}>
                      <Text style={styles.label}>Enter 6-digit Code</Text>
                      <TextInput
                        style={styles.input}
                        value={resetData.code}
                        onChangeText={(value) => setResetData(prev => ({ ...prev, code: value }))}
                        placeholder="Enter verification code"
                        placeholderTextColor="#999"
                        keyboardType="numeric"
                        maxLength={6}
                      />
                    </View>
                    <TouchableOpacity 
                      style={[styles.loginButton, loading && styles.disabledButton]}
                      onPress={handleVerifyCode}
                      disabled={loading}
                    >
                      <Text style={styles.loginButtonText}>
                        {loading ? 'Verifying...' : 'Verify Code'}
                      </Text>
                    </TouchableOpacity>
                  </>
                )}

                {resetStep === 3 && (
                  <>
                    <View style={styles.inputGroup}>
                      <Text style={styles.label}>New Password</Text>
                      <TextInput
                        style={styles.input}
                        value={resetData.newPassword}
                        onChangeText={(value) => setResetData(prev => ({ ...prev, newPassword: value }))}
                        placeholder="Enter new password"
                        placeholderTextColor="#999"
                        secureTextEntry
                      />
                    </View>
                    <TouchableOpacity 
                      style={[styles.loginButton, loading && styles.disabledButton]}
                      onPress={handleResetPassword}
                      disabled={loading}
                    >
                      <Text style={styles.loginButtonText}>
                        {loading ? 'Resetting...' : 'Reset Password'}
                      </Text>
                    </TouchableOpacity>
                  </>
                )}

                <TouchableOpacity 
                  style={styles.backToLoginLink}
                  onPress={() => {
                    setShowForgotPassword(false);
                    setResetStep(1);
                    setResetData({ phone: '', code: '', newPassword: '' });
                    setResetToken('');
                  }}
                >
                  <Text style={styles.backToLoginText}>Back to Login</Text>
                </TouchableOpacity>
              </View>
            </View>
          </KeyboardAvoidingView>
        </LinearGradient>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient
        colors={['#e91e63', '#ff6f00']}
        style={styles.gradient}
      >
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <View style={styles.content}>
            <View style={styles.header}>
              <Text style={styles.title}>Welcome Back</Text>
              <Text style={styles.subtitle}>Sign in to your account</Text>
            </View>

            <View style={styles.form}>
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Phone Number</Text>
                <TextInput
                  style={styles.input}
                  value={formData.phone}
                  onChangeText={(value) => handleInputChange('phone', value)}
                  placeholder="Enter your phone number"
                  placeholderTextColor="#999"
                  keyboardType="phone-pad"
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Password</Text>
                <TextInput
                  style={styles.input}
                  value={formData.password}
                  onChangeText={(value) => handleInputChange('password', value)}
                  placeholder="Enter your password"
                  placeholderTextColor="#999"
                  secureTextEntry
                />
              </View>

              <TouchableOpacity 
                style={[styles.loginButton, loading && styles.disabledButton]}
                onPress={handleLogin}
                disabled={loading}
              >
                <Text style={styles.loginButtonText}>
                  {loading ? 'Signing In...' : 'Sign In'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity 
                style={styles.forgotPasswordLink}
                onPress={() => setShowForgotPassword(true)}
              >
                <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
              </TouchableOpacity>

              <View style={styles.divider}>
                <View style={styles.dividerLine} />
                <Text style={styles.dividerText}>OR</Text>
                <View style={styles.dividerLine} />
              </View>

              <TouchableOpacity 
                style={styles.registerLink}
                onPress={() => navigation.navigate('Register')}
              >
                <Text style={styles.registerLinkText}>
                  Don't have an account? <Text style={styles.registerLinkBold}>Sign Up</Text>
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </LinearGradient>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 30,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
  },
  form: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 20,
    padding: 30,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
    marginBottom: 8,
  },
  input: {
    backgroundColor: 'rgba(255,255,255,0.9)',
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
    color: '#333',
  },
  loginButton: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
    marginTop: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 5,
  },
  disabledButton: {
    opacity: 0.7,
  },
  loginButtonText: {
    color: '#e91e63',
    fontSize: 18,
    fontWeight: 'bold',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 20,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.3)',
  },
  dividerText: {
    color: 'rgba(255,255,255,0.7)',
    paddingHorizontal: 15,
    fontSize: 14,
  },
  registerLink: {
    alignItems: 'center',
    marginBottom: 15,
  },
  registerLinkText: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: 16,
  },
  registerLinkBold: {
    fontWeight: 'bold',
    color: 'white',
  },
  forgotPasswordLink: {
    alignItems: 'center',
    marginVertical: 15,
  },
  forgotPasswordText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
  backToLoginLink: {
    alignItems: 'center',
    marginTop: 20,
  },
  backToLoginText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
});