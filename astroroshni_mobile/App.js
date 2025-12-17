import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar, View, ActivityIndicator } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import WelcomeScreen from './src/components/Welcome/WelcomeScreen';
import ModernAuthFlow from './src/components/Auth/ModernAuthFlow';
import ChatScreen from './src/components/Chat/ChatScreen';
import ChatHistoryScreen from './src/components/Chat/ChatHistoryScreen';
import ChatViewScreen from './src/components/Chat/ChatViewScreen';
import BirthFormScreen from './src/components/BirthForm/BirthFormScreen';
import SelectNativeScreen from './src/components/Native/SelectNativeScreen';
import CreditScreen from './src/credits/CreditScreen';
import ProfileScreen from './src/components/Profile/ProfileScreen';
import AnalysisHubScreen from './src/components/Analysis/AnalysisHubScreen';
import AnalysisDetailScreen from './src/components/Analysis/AnalysisDetailScreen';
import ChartScreen from './src/components/Chart/ChartScreen';
import TradingDashboardScreen from './src/components/Trading/TradingDashboardScreen';
import TradingCalendarScreen from './src/components/Trading/TradingCalendarScreen';
import ChildbirthPlannerScreen from './src/components/ChildbirthPlannerScreen';
import MuhuratHubScreen from './src/components/MuhuratHubScreen';
import UniversalMuhuratScreen from './src/components/UniversalMuhuratScreen';
import EventScreen from './src/components/EventScreen';
import AshtakvargaOracle from './src/components/Ashtakvarga/AshtakvargaOracle';
import { CreditProvider } from './src/credits/CreditContext';
import { storage } from './src/services/storage';

const Stack = createStackNavigator();

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [initialRoute, setInitialRoute] = useState('Welcome');

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const authToken = await storage.getAuthToken();
      
      if (authToken) {
        // User is logged in, check if they have charts
        try {
          const { chartAPI } = require('./src/services/api');
          const response = await chartAPI.getExistingCharts();
          
          if (response.data && response.data.charts && response.data.charts.length > 0) {
            // User has charts, check if one is selected in local storage
            const localBirthData = await storage.getBirthDetails();
            if (localBirthData) {
              setInitialRoute('Home');
            } else {
              // Charts exist but none selected, go to SelectNative
              setInitialRoute('SelectNative');
            }
          } else {
            // User has no charts, go to BirthForm
            setInitialRoute('BirthForm');
          }
        } catch (apiError) {
          // If API fails, go to BirthForm as fallback
          setInitialRoute('BirthForm');
        }
      } else {
        // User not logged in, show Welcome
        setInitialRoute('Welcome');
      }
    } catch (error) {
      setInitialRoute('Welcome');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <SafeAreaProvider>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0a0a23' }}>
          <ActivityIndicator size="large" color="#ff6b35" />
        </View>
      </SafeAreaProvider>
    );
  }
  
  return (
    <SafeAreaProvider>
      <CreditProvider>
        <NavigationContainer>
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
        </Stack.Navigator>
        </NavigationContainer>
      </CreditProvider>
    </SafeAreaProvider>
  );
}