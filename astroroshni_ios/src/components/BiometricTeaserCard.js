import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

export const BiometricTeaserCard = ({ onPressReveal, isLoading }) => {
  return (
    <TouchableOpacity onPress={onPressReveal} activeOpacity={0.9}>
      <LinearGradient
        colors={['#1a0033', '#2d1b4e', '#4a2c6d']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.card}
      >
        {/* Top Section */}
        <View style={styles.topSection}>
          <View style={styles.iconContainer}>
            <Ionicons name="scan-outline" size={28} color="#FFD700" />
            <View style={styles.badge} /> 
          </View>
          <Text style={styles.title}>🧬 Cosmic Biometric Check</Text>
        </View>
        
        {/* Content Section */}
        <Text style={styles.subtitle}>
          Your birth chart suggests specific physical traits. Reveal them to verify your chart's accuracy.
        </Text>
        
        {/* Button Section */}
        <View style={styles.buttonContainer}>
          {isLoading ? (
            <ActivityIndicator color="#FFD700" size="small" />
          ) : (
            <View style={styles.button}>
              <Text style={styles.buttonText}>Reveal & Verify</Text>
              <Ionicons name="chevron-forward" size={18} color="#1E1E2E" />
            </View>
          )}
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 20,
    marginTop: -15,
    marginBottom: 20,
    padding: 20,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.4)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 8,
  },
  topSection: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255, 215, 0, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    borderWidth: 2,
    borderColor: 'rgba(255, 215, 0, 0.3)',
  },
  badge: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#FF4444',
    borderWidth: 2,
    borderColor: '#1a0033',
  },
  title: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    flex: 1,
  },
  subtitle: {
    color: '#CCCCCC',
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 16,
  },
  buttonContainer: {
    alignItems: 'center',
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFD700',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 25,
    shadowColor: '#FFD700',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  buttonText: {
    color: '#1E1E2E',
    fontSize: 14,
    fontWeight: '700',
    marginRight: 6,
  }
});