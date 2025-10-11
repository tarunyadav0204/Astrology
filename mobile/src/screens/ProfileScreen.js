import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAstrology } from '../context/AstrologyContext';

export default function ProfileScreen({ navigation }) {
  const { user, setUser, birthData } = useAstrology();

  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.removeItem('userToken');
              await AsyncStorage.removeItem('userData');
              setUser(null);
              navigation.navigate('Landing');
            } catch (error) {
              console.error('Logout error:', error);
            }
          },
        },
      ]
    );
  };

  const menuItems = [
    {
      icon: '👤',
      title: 'Personal Information',
      subtitle: 'Update your profile details',
      onPress: () => Alert.alert('Coming Soon', 'This feature will be available soon'),
    },
    {
      icon: '📊',
      title: 'My Charts',
      subtitle: 'View all your saved birth charts',
      onPress: () => Alert.alert('Coming Soon', 'This feature will be available soon'),
    },
    {
      icon: '⚙️',
      title: 'Settings',
      subtitle: 'App preferences and configurations',
      onPress: () => Alert.alert('Coming Soon', 'This feature will be available soon'),
    },
    {
      icon: '🔔',
      title: 'Notifications',
      subtitle: 'Manage your notification preferences',
      onPress: () => Alert.alert('Coming Soon', 'This feature will be available soon'),
    },
    {
      icon: '💎',
      title: 'Premium Features',
      subtitle: 'Unlock advanced astrology features',
      onPress: () => Alert.alert('Coming Soon', 'Premium features coming soon'),
    },
    {
      icon: '📞',
      title: 'Support',
      subtitle: 'Get help and contact support',
      onPress: () => Alert.alert('Support', 'Email: support@astrologyapp.com'),
    },
    {
      icon: '📋',
      title: 'Privacy Policy',
      subtitle: 'Read our privacy policy',
      onPress: () => Alert.alert('Coming Soon', 'Privacy policy will be available soon'),
    },
    {
      icon: '📄',
      title: 'Terms of Service',
      subtitle: 'Read our terms of service',
      onPress: () => Alert.alert('Coming Soon', 'Terms of service will be available soon'),
    },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient
        colors={['#e91e63', '#ff6f00']}
        style={styles.gradient}
      >
        <ScrollView contentContainerStyle={styles.scrollContent}>
          {/* Profile Header */}
          <View style={styles.profileHeader}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {user?.name ? user.name.charAt(0).toUpperCase() : '👤'}
              </Text>
            </View>
            <Text style={styles.userName}>{user?.name || 'Guest User'}</Text>
            <Text style={styles.userEmail}>{user?.email || 'guest@example.com'}</Text>
            {birthData && (
              <Text style={styles.userBirth}>
                Birth Chart: {birthData.name} • {birthData.date}
              </Text>
            )}
          </View>

          {/* Menu Items */}
          <View style={styles.menuContainer}>
            {menuItems.map((item, index) => (
              <TouchableOpacity
                key={index}
                style={styles.menuItem}
                onPress={item.onPress}
              >
                <View style={styles.menuIcon}>
                  <Text style={styles.menuIconText}>{item.icon}</Text>
                </View>
                <View style={styles.menuContent}>
                  <Text style={styles.menuTitle}>{item.title}</Text>
                  <Text style={styles.menuSubtitle}>{item.subtitle}</Text>
                </View>
                <Text style={styles.menuArrow}>›</Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* App Info */}
          <View style={styles.appInfo}>
            <Text style={styles.appVersion}>AstroGPT v1.0.0</Text>
            <Text style={styles.appDescription}>
              AI-powered Vedic astrology application
            </Text>
          </View>

          {/* Logout Button */}
          <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
            <Text style={styles.logoutButtonText}>🚪 Logout</Text>
          </TouchableOpacity>
        </ScrollView>
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
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  profileHeader: {
    alignItems: 'center',
    marginBottom: 30,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 20,
    padding: 30,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
  },
  avatarText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: 'white',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 5,
  },
  userEmail: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 5,
  },
  userBirth: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
    textAlign: 'center',
  },
  menuContainer: {
    marginBottom: 30,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 15,
    padding: 20,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  menuIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  menuIconText: {
    fontSize: 20,
  },
  menuContent: {
    flex: 1,
  },
  menuTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 2,
  },
  menuSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
  },
  menuArrow: {
    fontSize: 24,
    color: 'rgba(255,255,255,0.5)',
    fontWeight: 'bold',
  },
  appInfo: {
    alignItems: 'center',
    marginBottom: 30,
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 15,
    padding: 20,
  },
  appVersion: {
    fontSize: 16,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 5,
  },
  appDescription: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
    textAlign: 'center',
  },
  logoutButton: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 15,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  logoutButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
  },
});