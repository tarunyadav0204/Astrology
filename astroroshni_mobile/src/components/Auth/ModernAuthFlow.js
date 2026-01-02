import React, { useState, useRef } from 'react';
import { View, StyleSheet, Animated, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';

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

import { COLORS } from '../../utils/constants';

const { width } = Dimensions.get('window');

export default function ModernAuthFlow({ navigation }) {
  const [currentScreen, setCurrentScreen] = useState('welcome');
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    phone: '',
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
  });

  const slideAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(1)).current;

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