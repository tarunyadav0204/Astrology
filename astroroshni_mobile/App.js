import React, { useState, useEffect, useRef } from 'react';
import { AppState, Platform } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar, View, ActivityIndicator, Animated, Text, TouchableOpacity, Linking } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

import i18n from './src/locales/i18n';

import WelcomeScreen from './src/components/Welcome/WelcomeScreen';
import ModernAuthFlow from './src/components/Auth/ModernAuthFlow';
import ChatScreen from './src/components/Chat/ChatScreen';
import ChatHistoryScreen from './src/components/Chat/ChatHistoryScreen';
import ChatViewScreen from './src/components/Chat/ChatViewScreen';
import BirthFormScreen from './src/components/BirthForm/BirthFormScreen';
import BirthProfileIntroScreen from './src/components/BirthProfileIntro/BirthProfileIntroScreen';
import SelectNativeScreen from './src/components/Native/SelectNativeScreen';
import CreditScreen from './src/credits/CreditScreen';
import CreditRequestScreen from './src/credits/CreditRequestScreen';
import ProfileScreen from './src/components/Profile/ProfileScreen';
import AnalysisHubScreen from './src/components/Analysis/AnalysisHubScreen';
import AnalysisDetailScreen from './src/components/Analysis/AnalysisDetailScreen';
import KarmaAnalysisScreen from './src/components/KarmaAnalysis/KarmaAnalysisScreen';
import ChartScreen from './src/components/Chart/ChartScreen';
import PlanetaryPositionsScreen from './src/components/Chart/PlanetaryPositionsScreen';
import TradingDashboardScreen from './src/components/Trading/TradingDashboardScreen';
import TradingCalendarScreen from './src/components/Trading/TradingCalendarScreen';
import ChildbirthPlannerScreen from './src/components/ChildbirthPlannerScreen';
import MuhuratHubScreen from './src/components/MuhuratHubScreen';
import UniversalMuhuratScreen from './src/components/UniversalMuhuratScreen';
import EventScreen from './src/components/EventScreen';
import AshtakvargaOracle from './src/components/Ashtakvarga/AshtakvargaOracle';
import NumerologyScreen from './src/components/Numerology/NumerologyScreen';
import FinancialDashboard from './src/components/Financial/FinancialDashboard';
import SectorDetailScreen from './src/components/Financial/SectorDetailScreen';
import AllOpportunitiesScreen from './src/components/Financial/AllOpportunitiesScreen';
import KotaChakraScreen from './src/components/KotaChakra/KotaChakraScreen';
import FactsScreen from './src/components/Facts/FactsScreen';
import ShadbalaScreen from './src/components/Shadbala/ShadbalaScreen';
import YogaScreen from './src/components/Yogas/YogaScreen';
import KPScreen from './src/screens/KPScreen';
import SadeSatiScreen from './src/components/SadeSati/SadeSatiScreen';
import NakshatraCalendarScreen from './src/components/NakshatraCalendar/NakshatraCalendarScreen';
import CosmicRingScreen from './src/components/CosmicRing/CosmicRingScreen';
import GlobalErrorHandler from './src/components/GlobalErrorHandler';
import ErrorOverlay from './src/components/ErrorOverlay';
import ErrorBoundary from './src/components/ErrorBoundary';
import AboutScreen from './src/components/About/AboutScreen';
import { CreditProvider } from './src/credits/CreditContext';
import { ThemeProvider } from './src/context/ThemeContext';
import { ErrorProvider } from './src/context/ErrorContext';
import { storage } from './src/services/storage';
import SplashScreen from './src/components/SplashScreen';
import { API_BASE_URL, getEndpoint } from './src/utils/constants';
// Push notifications: imported lazily in useEffect to avoid touching native module at launch (reduces iOS device crash risk).

const Stack = createStackNavigator();

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [initialRoute, setInitialRoute] = useState('Welcome');
  const [initialTheme, setInitialTheme] = useState(null);
  const [forceUpdateInfo, setForceUpdateInfo] = useState(null);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const navigationRef = useRef(null);

  useEffect(() => {
    bootstrap();
  }, []);

  useEffect(() => {
    if (!isLoading) {
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 280,
        useNativeDriver: true,
      }).start();
    }
  }, [isLoading]);

  const loadSavedLanguage = async () => {
    try {
      const savedLanguage = await storage.getLanguage();
      if (savedLanguage) {
        i18n.changeLanguage(savedLanguage);
      }
    } catch (error) {
      console.log('Error loading saved language:', error);
    }
  };

  const SPLASH_MIN_MS = 3000;

  const checkForceUpdate = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}${getEndpoint('/app/config')}`);
      if (!res.ok) return;
      const data = await res.json();

      const minAndroid = Number(data?.min_android_version_code || 0);
      const minIos = Number(data?.min_ios_build_number || 0);

      if (Platform.OS === 'android') {
        const current = Number(Constants.expoConfig?.android?.versionCode || 0);
        if (minAndroid && current && current < minAndroid) {
          setForceUpdateInfo({
            platform: 'android',
            currentVersion: current,
            minVersion: minAndroid,
          });
        }
      } else if (Platform.OS === 'ios') {
        const current = Number(Constants.expoConfig?.ios?.buildNumber || 0);
        if (minIos && current && current < minIos) {
          setForceUpdateInfo({
            platform: 'ios',
            currentVersion: current,
            minVersion: minIos,
          });
        }
      }
    } catch (e) {
      // If config fetch fails, do not block app usage.
      if (__DEV__) {
        console.warn('[App] Failed to fetch app config for version gate:', e?.message || e);
      }
    }
  };

  const bootstrap = async () => {
    const start = Date.now();
    try {
      // Load theme first so first paint has correct theme (avoids flash/flicker)
      const savedTheme = await AsyncStorage.getItem('appTheme');
      setInitialTheme(savedTheme === 'light' || savedTheme === 'dark' ? savedTheme : 'dark');

      loadSavedLanguage();

      // Check if this build is still allowed by backend config.
      await checkForceUpdate();

      const authToken = await storage.getAuthToken();

      if (authToken) {
        try {
          const { chartAPI } = require('./src/services/api');
          const response = await Promise.race([
            chartAPI.getExistingCharts(),
            new Promise((_, reject) =>
              setTimeout(() => reject(new Error('Timeout')), 10000)
            )
          ]);
          if (response.data && response.data.charts && response.data.charts.length > 0) {
            const localBirthData = await storage.getBirthDetails();
            if (localBirthData) {
              setInitialRoute('Home');
            } else {
              // Already logged in, no native selected: land on Home (empty state + CTA)
              setInitialRoute('Home');
            }
          } else {
            // No charts: land on Home; user can add profile via CTA
            setInitialRoute('Home');
          }
        } catch (apiError) {
          console.log('API Error on startup:', apiError);
          setInitialRoute('Home');
        }
      } else {
        setInitialRoute('Welcome');
      }
    } catch (error) {
      console.log('Bootstrap error:', error);
      setInitialRoute('Welcome');
    } finally {
      const elapsed = Date.now() - start;
      const remaining = Math.max(0, SPLASH_MIN_MS - elapsed);
      setTimeout(() => setIsLoading(false), remaining);
    }
  };

  // When app is ready and user is logged in, register push token; retry on foreground and once after delay.
  // On iOS skip loading the notification module entirely to avoid native crash on device (expo-notifications
  // and/or expo-device can crash when entitlements/APNs config is wrong). Android unchanged.
  const skipPushOnIos = Platform.OS === 'ios';
  useEffect(() => {
    if (isLoading) return;
    if (skipPushOnIos) {
      if (__DEV__) console.warn('[App] Push notifications skipped on iOS (crash workaround).');
      return;
    }
    let notifCleanupRef = null;
    const deferMs = Platform.OS === 'ios' ? 800 : 100;
    const notifSetupTimer = setTimeout(() => {
      try {
        const pushNotifications = require('./src/services/pushNotifications');
        pushNotifications.setupNotificationHandler();
        const cleanup = pushNotifications.setupNotificationResponseListener(navigationRef);
        if (typeof cleanup === 'function') notifCleanupRef = cleanup;
      } catch (e) {
        if (__DEV__) console.warn('[App] Notification setup failed (non-fatal):', e?.message || e);
      }
    }, deferMs);
    const tryRegisterPush = async () => {
      try {
        const token = await storage.getAuthToken();
        if (!token) return;
        const pushNotifications = require('./src/services/pushNotifications');
        await pushNotifications.registerPushTokenIfLoggedIn();
      } catch (e) {
        if (__DEV__) console.warn('[App] registerPushToken failed:', e?.message || e);
      }
    };
    tryRegisterPush();
    const delayed = setTimeout(tryRegisterPush, 3000);
    const sub = AppState.addEventListener('change', (state) => {
      if (state === 'active') tryRegisterPush();
    });
    return () => {
      clearTimeout(delayed);
      clearTimeout(notifSetupTimer);
      sub?.remove?.();
      if (typeof notifCleanupRef === 'function') notifCleanupRef();
    };
  }, [isLoading, skipPushOnIos]);

  const handleUpdatePress = () => {
    try {
      if (Platform.OS === 'android') {
        const pkg = Constants.expoConfig?.android?.package || 'com.astroroshni.mobile';
        const playUrl = `https://play.google.com/store/apps/details?id=${pkg}`;
        Linking.openURL(playUrl);
      } else if (Platform.OS === 'ios') {
        // TODO: replace with actual App Store URL for AstroRoshni
        const appStoreUrl = 'https://astroroshni.com';
        Linking.openURL(appStoreUrl);
      }
    } catch (e) {
      if (__DEV__) {
        console.warn('[App] Failed to open store URL:', e?.message || e);
      }
    }
  };

  if (isLoading) {
    return <SplashScreen />;
  }

  if (forceUpdateInfo) {
    return (
      <SafeAreaProvider>
        <StatusBar barStyle="dark-content" backgroundColor="#ffedd5" />
        <View style={{ flex: 1, backgroundColor: '#fff7ed', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
          <Text style={{ fontSize: 24, fontWeight: '700', marginBottom: 12, textAlign: 'center', color: '#7c2d12' }}>
            Update required
          </Text>
          <Text style={{ fontSize: 15, textAlign: 'center', color: '#7c2d12', marginBottom: 24 }}>
            A new version of AstroRoshni is available. Please update the app to continue.
          </Text>
          <TouchableOpacity
            onPress={handleUpdatePress}
            style={{
              backgroundColor: '#f97316',
              borderRadius: 999,
              paddingHorizontal: 24,
              paddingVertical: 12,
            }}
          >
            <Text style={{ color: '#ffffff', fontSize: 16, fontWeight: '600' }}>Update app</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaProvider>
    );
  }

  return (
    <SafeAreaProvider>
      <ThemeProvider initialTheme={initialTheme}>
        <Animated.View style={{ flex: 1, opacity: fadeAnim }}>
          <ErrorProvider>
            <CreditProvider>
              <ErrorBoundary>
              <NavigationContainer ref={navigationRef}>
              <GlobalErrorHandler />
              <StatusBar barStyle="dark-content" backgroundColor="#ff6b35" />
        <Stack.Navigator
          initialRouteName={initialRoute}
          screenOptions={{
            headerStyle: {
              backgroundColor: '#ff6b35',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
            gestureEnabled: true,
            gestureDirection: 'horizontal',
          }}
        >
          <Stack.Screen 
            name="Welcome" 
            component={WelcomeScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Login" 
            component={ModernAuthFlow}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Home" 
            component={ChatScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="BirthForm" 
            component={BirthFormScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="BirthProfileIntro" 
            component={BirthProfileIntroScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="SelectNative" 
            component={SelectNativeScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="ChatHistory" 
            component={ChatHistoryScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="ChatView" 
            component={ChatViewScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Credits" 
            component={CreditScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="CreditRequest" 
            component={CreditRequestScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Profile" 
            component={ProfileScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="AnalysisHub" 
            component={AnalysisHubScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="AnalysisDetail" 
            component={AnalysisDetailScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="KarmaAnalysis" 
            component={KarmaAnalysisScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Chart" 
            component={ChartScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="TradingDashboard" 
            component={TradingDashboardScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="TradingCalendar" 
            component={TradingCalendarScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="ChildbirthPlanner" 
            component={ChildbirthPlannerScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="MuhuratHub" 
            component={MuhuratHubScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="UniversalMuhurat" 
            component={UniversalMuhuratScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="EventScreen" 
            component={EventScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="AshtakvargaOracle" 
            component={AshtakvargaOracle}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Numerology" 
            component={NumerologyScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="PlanetaryPositions" 
            component={PlanetaryPositionsScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="FinancialDashboard" 
            component={FinancialDashboard}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="SectorDetail" 
            component={SectorDetailScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="AllOpportunities" 
            component={AllOpportunitiesScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="KotaChakra" 
            component={KotaChakraScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Facts" 
            component={FactsScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="About" 
            component={AboutScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Shadbala" 
            component={ShadbalaScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Yogas" 
            component={YogaScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="KPSystem"
            component={KPScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="SadeSati"
            component={SadeSatiScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="NakshatraCalendar"
            component={NakshatraCalendarScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="CosmicRing"
            component={CosmicRingScreen}
            options={{ headerShown: false }}
          />
        </Stack.Navigator>
        <ErrorOverlay />
        </NavigationContainer>
        </ErrorBoundary>
      </CreditProvider>
      </ErrorProvider>
        </Animated.View>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}