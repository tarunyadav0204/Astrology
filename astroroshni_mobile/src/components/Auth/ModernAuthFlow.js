import React, { useState, useRef, useEffect, useCallback } from 'react';
import { View, StyleSheet, Animated, Dimensions, AppState, BackHandler, Platform } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';

import { storage } from '../../services/storage';
import WelcomeScreen from './screens/WelcomeScreen';
import PhoneInputScreen from './screens/PhoneInputScreen';
import PasswordScreen from './screens/PasswordScreen';
import ForgotPasswordScreen from './screens/ForgotPasswordScreen';
import NameInputScreen from './screens/NameInputScreen';
import EmailInputScreen from './screens/EmailInputScreen';
import OTPScreen from './screens/OTPScreen';
import BirthDetailsOptionScreen from './screens/BirthDetailsOptionScreen';
import BirthNameScreen from './screens/BirthNameScreen';
import BirthDateScreen from './screens/BirthDateScreen';
import BirthTimeScreen from './screens/BirthTimeScreen';
import BirthLocationScreen from './screens/BirthLocationScreen';
import GenderScreen from './screens/GenderScreen';
import SuccessScreen from './screens/SuccessScreen';
import WelcomeAfterRegistrationScreen from './screens/WelcomeAfterRegistrationScreen';
import ChooseLanguageScreen from './screens/ChooseLanguageScreen';

import { COLORS } from '../../utils/constants';

const { width } = Dimensions.get('window');

/** @returns {string|null} next screen id, or '__root_go_back__' to pop Login off the root stack */
function resolveAuthHardwareBackTarget(currentScreen, isLogin, formData) {
  const cc = formData?.countryCode || '';
  const otpEmailRequired = cc !== '+91';
  switch (currentScreen) {
    case 'welcome':
      return '__root_go_back__';
    case 'phone':
      return 'welcome';
    case 'password':
      return isLogin ? 'phone' : (cc === '+91' ? 'email' : 'name');
    case 'forgotPassword':
      return 'password';
    case 'email': {
      if (isLogin) {
        return 'password';
      }
      const nonIndiaPreOtp = cc !== '+91' && !(formData?.otpCode || '').trim();
      return nonIndiaPreOtp ? 'phone' : 'name';
    }
    case 'otp':
      return otpEmailRequired ? 'email' : 'phone';
    case 'name':
      return 'otp';
    case 'chooseLanguage':
      return 'password';
    case 'welcomeAfterRegistration':
      return 'chooseLanguage';
    default:
      return null;
  }
}

const INITIAL_FORM_DATA = {
  phone: '',
  countryCode: '+91',
  password: '',
  name: '',
  email: '',
  otpCode: '',
  devOtpCode: '',
  resetCode: '',
  newPassword: '',
  birthDetails: {
    name: '',
    date: new Date().toISOString().split('T')[0],
    time: '12:00:00',
    place: '',
    latitude: null,
    longitude: null,
    gender: ''
  },
  collectBirthDetails: false
};

export default function ModernAuthFlow({ navigation, route }) {
  const [currentScreen, setCurrentScreen] = useState('welcome');
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState(INITIAL_FORM_DATA);
  const restoredRef = useRef(false);

  const slideAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(1)).current;

  // Restore in-progress registration (e.g. user left on OTP, app was killed, came back)
  useEffect(() => {
    const restore = route.params?.restore;
    if (!restore?.step || restoredRef.current) return;
    restoredRef.current = true;
    storage.clearPendingRegistration();
    setFormData(prev => ({
      ...prev,
      phone: restore.phone || prev.phone,
      countryCode: restore.countryCode || prev.countryCode,
    }));
    setCurrentScreen(restore.step === 'otp' || restore.step === 'phone' ? restore.step : 'otp');
  }, [route.params?.restore]);

  // When user leaves app during OTP/phone step, persist so we can restore after cold start
  useEffect(() => {
    const sub = AppState.addEventListener('change', (state) => {
      if (state !== 'background') return;
      if (currentScreen !== 'otp' && currentScreen !== 'phone') return;
      storage.setPendingRegistration({
        phone: formData.phone,
        countryCode: formData.countryCode || '+91',
        step: currentScreen,
      });
    });
    return () => sub.remove();
  }, [currentScreen, formData.phone, formData.countryCode]);

  // Clear pending when leaving auth flow so we don't restore next time
  useEffect(() => {
    return () => storage.clearPendingRegistration();
  }, []);

  const navigateToScreenRef = useRef(null);
  const navigateToScreen = (screenName, direction = 'forward') => {
    const slideValue = direction === 'forward' ? -width : width;
    
    Animated.parallel([
      Animated.timing(slideAnim, {
        toValue: slideValue,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 150,
        useNativeDriver: true,
      }),
    ]).start(() => {
      if (screenName === 'name') storage.clearPendingRegistration();
      setCurrentScreen(screenName);
      slideAnim.setValue(direction === 'forward' ? width : -width);
      
      Animated.parallel([
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start();
    });
  };
  navigateToScreenRef.current = navigateToScreen;

  useFocusEffect(
    useCallback(() => {
      if (Platform.OS !== 'android') {
        return undefined;
      }
      const sub = BackHandler.addEventListener('hardwareBackPress', () => {
        const target = resolveAuthHardwareBackTarget(currentScreen, isLogin, formData);
        if (target === '__root_go_back__') {
          if (navigation.canGoBack()) {
            navigation.goBack();
            return true;
          }
          return false;
        }
        if (target) {
          navigateToScreenRef.current?.(target, 'back');
          return true;
        }
        return false;
      });
      return () => sub.remove();
    }, [navigation, currentScreen, isLogin, formData])
  );

  const updateFormData = (field, value) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }
  };

  const getScreenComponent = () => {
    const screenProps = {
      formData,
      updateFormData,
      navigateToScreen,
      isLogin,
      setIsLogin,
      navigation
    };

    switch (currentScreen) {
      case 'welcome':
        return <WelcomeScreen {...screenProps} />;
      case 'phone':
        return <PhoneInputScreen {...screenProps} />;
      case 'password':
        return <PasswordScreen {...screenProps} />;
      case 'forgotPassword':
        return <ForgotPasswordScreen {...screenProps} />;
      case 'name':
        return <NameInputScreen {...screenProps} />;
      case 'email':
        return <EmailInputScreen {...screenProps} />;
      case 'otp':
        return <OTPScreen {...screenProps} />;
      case 'birthOption':
        return <BirthDetailsOptionScreen {...screenProps} />;
      case 'birthName':
        return <BirthNameScreen {...screenProps} />;
      case 'birthDate':
        return <BirthDateScreen {...screenProps} />;
      case 'birthTime':
        return <BirthTimeScreen {...screenProps} />;
      case 'birthLocation':
        return <BirthLocationScreen {...screenProps} />;
      case 'gender':
        return <GenderScreen {...screenProps} />;
      case 'success':
        return <SuccessScreen {...screenProps} />;
      case 'welcomeAfterRegistration':
        return <WelcomeAfterRegistrationScreen {...screenProps} />;
      case 'chooseLanguage':
        return <ChooseLanguageScreen {...screenProps} />;
      default:
        return <WelcomeScreen {...screenProps} />;
    }
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <Animated.View
            style={[
              styles.screenContainer,
              {
                transform: [{ translateX: slideAnim }],
                opacity: fadeAnim,
              },
            ]}
          >
            {getScreenComponent()}
          </Animated.View>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  screenContainer: {
    flex: 1,
  },
});