import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar } from 'expo-status-bar';
import AsyncStorage from '@react-native-async-storage/async-storage';

import LandingScreen from './src/screens/LandingScreen';
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import BirthFormScreen from './src/screens/BirthFormScreen';
import ChartListScreen from './src/screens/ChartListScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import { AstrologyProvider } from './src/context/AstrologyContext';
import { navigationRef } from './src/services/navigationService';

const Stack = createStackNavigator();

export default function App() {
  const [initialRoute, setInitialRoute] = useState('Landing');
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      if (token) {
        setInitialRoute('ChartList');
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
    } finally {
      setIsReady(true);
    }
  };

  if (!isReady) {
    return null;
  }

  return (
    <AstrologyProvider>
      <NavigationContainer ref={navigationRef}>
        <StatusBar style="auto" />
        <Stack.Navigator 
          initialRouteName={initialRoute}
          screenOptions={{ headerShown: false }}
        >
          <Stack.Screen name="Landing" component={LandingScreen} />
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Register" component={RegisterScreen} />
          <Stack.Screen name="BirthForm" component={BirthFormScreen} />
          <Stack.Screen name="ChartList" component={ChartListScreen} />
          <Stack.Screen name="Dashboard" component={DashboardScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    </AstrologyProvider>
  );
}