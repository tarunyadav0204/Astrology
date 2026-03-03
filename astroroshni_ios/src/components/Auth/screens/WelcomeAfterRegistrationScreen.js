import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../../utils/constants';

export default function WelcomeAfterRegistrationScreen({ 
  formData, 
  navigation 
}) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 8,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const handleCreateBirthChart = () => {
    navigation.replace('BirthForm', { 
      prefillData: { 
        name: formData.name 
      } 
    });
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Animated.View
          style={[
            styles.welcomeContainer,
            {
              opacity: fadeAnim,
              transform: [
                { translateY: slideAnim },
                { scale: scaleAnim }
              ],
            },
          ]}
        >
          {/* Success Icon */}
          <View style={styles.iconContainer}>
            <View style={styles.iconGradient}>
              <Text style={styles.successIcon}>🎉</Text>
            </View>
          </View>

          {/* Welcome Message */}
          <Text style={styles.welcomeTitle}>
            Welcome to AstroRoshni, {formData.name}!
          </Text>
          
          <Text style={styles.welcomeSubtitle}>
            Your account has been created successfully.{'\n'}
            Let's create your personalized birth chart to unlock cosmic insights.
          </Text>

          {/* Features List */}
          <View style={styles.featuresList}>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>📊</Text>
              <Text style={styles.featureText}>Detailed Birth Chart Analysis</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>🔮</Text>
              <Text style={styles.featureText}>AI-Powered Predictions</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>💫</Text>
              <Text style={styles.featureText}>Daily Cosmic Guidance</Text>
            </View>
          </View>

          {/* Create Birth Chart Button */}
          <TouchableOpacity
            style={styles.createChartButton}
            onPress={handleCreateBirthChart}
          >
            <View style={styles.buttonGradient}>
              <Text style={styles.buttonText}>Create My Birth Chart</Text>
              <Ionicons name="arrow-forward" size={20} color="#ffffff" />
            </View>
          </TouchableOpacity>

          {/* Skip Option */}
          <TouchableOpacity
            style={styles.skipButton}
            onPress={() => navigation.replace('Home')}
          >
            <Text style={styles.skipText}>Skip for now</Text>
          </TouchableOpacity>
        </Animated.View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 20,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
  },
  welcomeContainer: {
    alignItems: 'center',
  },
  iconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    marginBottom: 32,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 6,
  },
  iconGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 60,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(0, 0, 0, 0.12)',
    backgroundColor: 'rgba(0, 0, 0, 0.06)',
  },
  successIcon: {
    fontSize: 56,
  },
  welcomeTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#000000',
    textAlign: 'center',
    marginBottom: 16,
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 40,
  },
  featuresList: {
    width: '100%',
    marginBottom: 40,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.06)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.1)',
  },
  featureIcon: {
    fontSize: 24,
    marginRight: 16,
  },
  featureText: {
    fontSize: 16,
    color: '#000000',
    fontWeight: '500',
    flex: 1,
  },
  createChartButton: {
    width: '100%',
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 6,
    marginBottom: 16,
  },
  buttonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    gap: 8,
    backgroundColor: '#000000',
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '700',
  },
  skipButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
  },
  skipText: {
    color: '#666666',
    fontSize: 16,
    fontWeight: '500',
  },
});