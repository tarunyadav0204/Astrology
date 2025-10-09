import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';

import BirthFormScreen from './src/screens/BirthFormScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import ChartsScreen from './src/screens/ChartsScreen';
import AnalysisScreen from './src/screens/AnalysisScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#e91e63',
        tabBarInactiveTintColor: '#666',
        headerShown: false,
      }}
    >
      <Tab.Screen 
        name="Dashboard" 
        component={DashboardScreen}
        options={{
          tabBarLabel: 'Dashboard',
          tabBarIcon: () => '📊',
        }}
      />
      <Tab.Screen 
        name="Charts" 
        component={ChartsScreen}
        options={{
          tabBarLabel: 'Charts',
          tabBarIcon: () => '🔮',
        }}
      />
      <Tab.Screen 
        name="Analysis" 
        component={AnalysisScreen}
        options={{
          tabBarLabel: 'Analysis',
          tabBarIcon: () => '📈',
        }}
      />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="auto" />
      <Stack.Navigator initialRouteName="BirthForm">
        <Stack.Screen 
          name="BirthForm" 
          component={BirthFormScreen}
          options={{ title: 'Birth Details' }}
        />
        <Stack.Screen 
          name="Main" 
          component={MainTabs}
          options={{ headerShown: false }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}