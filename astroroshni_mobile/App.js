import React, { useState, useEffect, useRef } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar, View, ActivityIndicator, Animated } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';

import i18n from './src/locales/i18n';

import WelcomeScreen from './src/components/Welcome/WelcomeScreen';
import ModernAuthFlow from './src/components/Auth/ModernAuthFlow';
import ChatScreen from './src/components/Chat/ChatScreen';
import ChatHistoryScreen from './src/components/Chat/ChatHistoryScreen';
import ChatViewScreen from './src/components/Chat/ChatViewScreen';
import BirthFormScreen from './src/components/BirthForm/BirthFormScreen';
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
import { CreditProvider } from './src/credits/CreditContext';
import { ThemeProvider } from './src/context/ThemeContext';
import { ErrorProvider } from './src/context/ErrorContext';
import { storage } from './src/services/storage';
import SplashScreen from './src/components/SplashScreen';

const Stack = createStackNavigator();

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [initialRoute, setInitialRoute] = useState('Welcome');
  const [initialTheme, setInitialTheme] = useState(null);
  const fadeAnim = useRef(new Animated.Value(0)).current;

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

  const bootstrap = async () => {
    const start = Date.now();
    try {
      // Load theme first so first paint has correct theme (avoids flash/flicker)
      const savedTheme = await AsyncStorage.getItem('appTheme');
      setInitialTheme(savedTheme === 'light' || savedTheme === 'dark' ? savedTheme : 'dark');

      loadSavedLanguage();

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
              setInitialRoute('SelectNative');
            }
          } else {
            setInitialRoute('BirthForm');
          }
        } catch (apiError) {
          console.log('API Error on startup:', apiError);
          setInitialRoute('BirthForm');
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

  if (isLoading) {
    return <SplashScreen />;
  }
  
  return (
    <SafeAreaProvider>
      <ThemeProvider initialTheme={initialTheme}>
        <Animated.View style={{ flex: 1, opacity: fadeAnim }}>
          <ErrorProvider>
            <CreditProvider>
              <NavigationContainer>
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
      </CreditProvider>
      </ErrorProvider>
        </Animated.View>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}