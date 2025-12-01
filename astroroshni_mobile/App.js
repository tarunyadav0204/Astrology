import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar } from 'react-native';
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
import { CreditProvider } from './src/credits/CreditContext';

const Stack = createStackNavigator();

export default function App() {
  React.useEffect(() => {
    console.log('App.js loaded');
  }, []);
  
  return (
    <SafeAreaProvider>
      <CreditProvider>
        <NavigationContainer>
        <StatusBar barStyle="dark-content" backgroundColor="#ff6b35" />
        <Stack.Navigator
          initialRouteName="Welcome"
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
            name="Chat" 
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
        </Stack.Navigator>
        </NavigationContainer>
      </CreditProvider>
    </SafeAreaProvider>
  );
}