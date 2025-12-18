import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
  Dimensions,
  StatusBar,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../utils/constants';
import { storage } from '../../services/storage';

const { width, height } = Dimensions.get('window');



const TrustBadge = ({ icon, title, description, delay = 0 }) => {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  useEffect(() => {
    Animated.sequence([
      Animated.delay(delay),
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 600,
          useNativeDriver: true,
        }),
        Animated.spring(slideAnim, {
          toValue: 0,
          tension: 50,
          friction: 8,
          useNativeDriver: true,
        }),
      ]),
    ]).start();
  }, []);

  return (
    <Animated.View
      style={[
        styles.trustBadge,
        {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }]
        }
      ]}
    >
      <View style={styles.trustIconContainer}>
        <LinearGradient
          colors={['#ff6b35', '#ff8c5a']}
          style={styles.trustIconGradient}
        >
          <Ionicons name={icon} size={24} color="white" />
        </LinearGradient>
      </View>
      <Text style={styles.trustTitle}>{title}</Text>
      <Text style={styles.trustDescription}>{description}</Text>
    </Animated.View>
  );
};

const FeatureCard = ({ icon, title, description, delay = 0 }) => {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;

  useEffect(() => {
    Animated.sequence([
      Animated.delay(delay),
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 600,
          useNativeDriver: true,
        }),
        Animated.spring(scaleAnim, {
          toValue: 1,
          tension: 50,
          friction: 7,
          useNativeDriver: true,
        }),
      ]),
    ]).start();
  }, []);

  return (
    <Animated.View
      style={[
        styles.featureCard,
        {
          opacity: fadeAnim,
          transform: [{ scale: scaleAnim }]
        }
      ]}
    >
      <LinearGradient
        colors={['rgba(255, 255, 255, 0.95)', 'rgba(248, 249, 250, 0.95)']}
        style={styles.featureGradient}
      >
        <View style={styles.featureIconContainer}>
          <LinearGradient
            colors={['#ff6b35', '#ffd700']}
            style={styles.featureIconGradient}
          >
            <Text style={styles.featureIcon}>{icon}</Text>
          </LinearGradient>
        </View>
        <Text style={styles.featureTitle}>{title}</Text>
        <Text style={styles.featureDescription}>{description}</Text>
      </LinearGradient>
    </Animated.View>
  );
};

const WelcomeScreen = ({ navigation }) => {
  const logoScale = useRef(new Animated.Value(0)).current;
  const logoRotate = useRef(new Animated.Value(0)).current;
  const titleOpacity = useRef(new Animated.Value(0)).current;
  const subtitleOpacity = useRef(new Animated.Value(0)).current;
  const buttonOpacity = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const scrollY = useRef(new Animated.Value(0)).current;
  

  
  const trustBadges = [
    { icon: 'shield-checkmark', title: 'Bank-Level Security', description: 'End-to-end encryption' },
    { icon: 'telescope', title: 'NASA-Grade Precision', description: 'Swiss Ephemeris calculations' },
    { icon: 'people', title: '10,000+ Happy Users', description: 'Trusted worldwide' },
    { icon: 'ribbon', title: 'Vedic Certified', description: 'Traditional authenticity' },
  ];
  
  const features = [
    { icon: '📊', title: 'Live Birth Charts', description: 'North & South Indian styles with real-time calculations' },
    { icon: '🔮', title: 'Life Analysis Suite', description: 'Wealth, Health, Marriage & Education insights' },
    { icon: '⏰', title: 'Real-Time Transits', description: 'Current planetary positions affecting you now' },
    { icon: '💬', title: 'Chat with Cosmos', description: 'Ask anything, get instant astrological guidance' },
    { icon: '⊞', title: 'Ashtakvarga Oracle', description: 'Unlock planetary strength secrets for precise predictions' },
    { icon: '🌀', title: 'Multi-Dasha System', description: 'Vimshottari, Yogini, Char & Kalachakra timing mastery' },
  ];

  useEffect(() => {
    // Check if user is already logged in
    checkAuthStatus();
    
    // Logo entrance animation
    Animated.sequence([
      Animated.timing(logoScale, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }),
      Animated.timing(titleOpacity, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(subtitleOpacity, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(buttonOpacity, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();

    // Continuous logo rotation
    Animated.loop(
      Animated.timing(logoRotate, {
        toValue: 1,
        duration: 20000,
        useNativeDriver: true,
      })
    ).start();

    // Pulsing animation
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 2000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 2000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const authToken = await storage.getAuthToken();
      const birthDetails = await storage.getBirthDetails();
      
      if (authToken && birthDetails) {
        // User is logged in and has birth details, go to Chat
        navigation.replace('Home');
      } else if (authToken) {
        // User is logged in but no birth details, go to BirthForm
        navigation.replace('BirthForm');
      }
      // If no auth token, stay on Welcome screen
    } catch (error) {

    }
  };

  const rotation = logoRotate.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      
      {/* Cosmic Background */}
      <LinearGradient
        colors={['#0a0a23', '#1a1a3a', '#2d1b69', '#4a2c7a']}
        style={styles.background}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />



      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        bounces={true}
        scrollEnabled={true}
      >
        {/* Hero Section */}
        <View style={styles.heroSection}>
          <Animated.View
            style={[
              styles.logoContainer,
              {
                transform: [
                  { scale: Animated.multiply(logoScale, pulseAnim) }
                ],
              },
            ]}
          >
            <View style={styles.logoWrapper}>
              {/* Rotating cosmic ring */}
              <Animated.View
                style={[
                  styles.cosmicRing,
                  {
                    transform: [{ rotate: rotation }]
                  }
                ]}
              >
                <View style={styles.ringDot} />
                <View style={[styles.ringDot, styles.ringDot2]} />
                <View style={[styles.ringDot, styles.ringDot3]} />
                <View style={[styles.ringDot, styles.ringDot4]} />
              </Animated.View>
              
              {/* Sacred Om symbol - stationary */}
              <LinearGradient
                colors={['#FFD700', '#FFA500', '#FF6B35']}
                style={styles.mandala}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Text style={styles.mandalaSymbol}>🕉️</Text>
              </LinearGradient>
            </View>
          </Animated.View>

          <Animated.Text style={[styles.appTitle, { opacity: titleOpacity }]} numberOfLines={1} adjustsFontSizeToFit>
            AstroRoshni
          </Animated.Text>
          
          <Animated.View style={[styles.taglineContainer, { opacity: subtitleOpacity }]}>
            <Text style={styles.tagline}>Your Personal Cosmic Guide</Text>
            <Text style={styles.subtitle}>
              Ancient Wisdom • Modern Precision • Trusted by Thousands
            </Text>
          </Animated.View>
        </View>

        {/* Trust & Security Section */}
        <View style={styles.trustSection}>
          <Text style={styles.sectionTitle}>Why Trust AstroRoshni?</Text>
          <View style={styles.trustGrid}>
            {trustBadges.map((badge, index) => (
              <TrustBadge
                key={index}
                icon={badge.icon}
                title={badge.title}
                description={badge.description}
                delay={index * 200}
              />
            ))}
          </View>
        </View>

        {/* Features Section */}
        <View style={styles.featuresSection}>
          <Text style={styles.sectionTitle}>Unlock Cosmic Insights</Text>
          <View style={styles.featuresGrid}>
            {features.map((feature, index) => (
              <FeatureCard
                key={index}
                icon={feature.icon}
                title={feature.title}
                description={feature.description}
                delay={index * 150}
              />
            ))}
          </View>
        </View>

        {/* Security Section */}
        <View style={styles.securitySection}>
          <LinearGradient
            colors={['rgba(255, 255, 255, 0.95)', 'rgba(248, 249, 250, 0.95)']}
            style={styles.securityCard}
          >
            <View style={styles.securityHeader}>
              <View style={styles.securityIconContainer}>
                <LinearGradient
                  colors={['#4CAF50', '#66BB6A']}
                  style={styles.securityIconGradient}
                >
                  <Ionicons name="shield-checkmark" size={32} color="white" />
                </LinearGradient>
              </View>
              <Text style={styles.securityTitle}>Your Privacy is Sacred</Text>
            </View>
            
            <View style={styles.securityFeatures}>
              <View style={styles.securityFeature}>
                <Ionicons name="lock-closed" size={16} color="#4CAF50" />
                <Text style={styles.securityFeatureText}>256-bit Military Encryption</Text>
              </View>
              <View style={styles.securityFeature}>
                <Ionicons name="eye-off" size={16} color="#4CAF50" />
                <Text style={styles.securityFeatureText}>Zero Data Sharing Policy</Text>
              </View>
              <View style={styles.securityFeature}>
                <Ionicons name="phone-portrait" size={16} color="#4CAF50" />
                <Text style={styles.securityFeatureText}>Local Device Processing</Text>
              </View>
              <View style={styles.securityFeature}>
                <Ionicons name="checkmark-circle" size={16} color="#4CAF50" />
                <Text style={styles.securityFeatureText}>GDPR Compliant</Text>
              </View>
            </View>
          </LinearGradient>
        </View>

        {/* Social Proof */}
        <View style={styles.socialProofSection}>
          <View style={styles.statsContainer}>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>10,000+</Text>
              <Text style={styles.statLabel}>Happy Users</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>4.8★</Text>
              <Text style={styles.statLabel}>App Rating</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>99.9%</Text>
              <Text style={styles.statLabel}>Accuracy</Text>
            </View>
          </View>
        </View>

        {/* CTA Section */}
        <View style={styles.ctaSection}>
          <Animated.View style={[styles.buttonContainer, { opacity: buttonOpacity }]}>
            <TouchableOpacity onPress={() => navigation.navigate('Login')} activeOpacity={0.8}>
              <LinearGradient
                colors={['#FF6B35', '#F7931E', '#FFD700']}
                style={styles.getStartedButton}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
              >
                <Text style={styles.buttonText} numberOfLines={1} adjustsFontSizeToFit>Begin Your Cosmic Journey</Text>
                <Text style={styles.buttonIcon}>✨</Text>
              </LinearGradient>
            </TouchableOpacity>
            
            {/* <TouchableOpacity 
              onPress={() => navigation.navigate('AnalysisHub')} 
              activeOpacity={0.8}
              style={styles.secondaryButton}
            >
              <LinearGradient
                colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                style={styles.secondaryButtonGradient}
              >
                <Text style={styles.secondaryButtonText}>🔮 Explore Life Analysis</Text>
              </LinearGradient>
            </TouchableOpacity> */}
            
            <View style={styles.ctaSubtext}>
              <Text style={styles.ctaSubtextMain}>Trusted by 10,000+ Users</Text>
              <Text style={styles.ctaSubtextSub}>Free to Start • No Hidden Fees</Text>
            </View>
          </Animated.View>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a23',
  },
  background: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
    pointerEvents: 'none',
  },

  scrollView: {
    flex: 1,
    width: '100%',
    height: '100%',
  },
  scrollContent: {
    paddingBottom: 40,
  },
  heroSection: {
    alignItems: 'center',
    paddingHorizontal: 40,
    paddingTop: 80,
    paddingBottom: 60,
  },
  logoContainer: {
    marginBottom: 30,
  },
  logoWrapper: {
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cosmicRing: {
    position: 'absolute',
    width: 180,
    height: 180,
    borderRadius: 90,
    borderWidth: 2,
    borderColor: 'rgba(255, 215, 0, 0.3)',
    borderStyle: 'dashed',
  },
  ringDot: {
    position: 'absolute',
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FFD700',
    top: -4,
    left: 86,
    shadowColor: '#FFD700',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 4,
  },
  ringDot2: {
    top: 86,
    left: 176,
    backgroundColor: '#FFA500',
  },
  ringDot3: {
    top: 176,
    left: 86,
    backgroundColor: '#FF6B35',
  },
  ringDot4: {
    top: 86,
    left: -4,
    backgroundColor: '#FFD700',
  },
  mandala: {
    width: 140,
    height: 140,
    borderRadius: 70,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#FFD700',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 30,
    elevation: 15,
  },
  mandalaSymbol: {
    fontSize: 70,
    color: '#FFFFFF',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 2, height: 2 },
    textShadowRadius: 4,
  },
  appTitle: {
    fontSize: width < 375 ? 32 : width < 414 ? 38 : 42,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: width < 375 ? 1 : 2,
    textAlign: 'center',
    textShadowColor: 'rgba(255, 215, 0, 0.5)',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 15,
    marginBottom: 20,
    flexShrink: 0,
    paddingHorizontal: 10,
  },
  taglineContainer: {
    alignItems: 'center',
  },
  tagline: {
    fontSize: width < 375 ? 18 : 22,
    color: '#FFD700',
    textAlign: 'center',
    marginBottom: 12,
    fontWeight: '600',
    letterSpacing: width < 375 ? 0.5 : 1,
    flexShrink: 0,
    paddingHorizontal: 10,
  },
  subtitle: {
    fontSize: width < 375 ? 14 : 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    lineHeight: width < 375 ? 20 : 24,
    fontWeight: '400',
    flexShrink: 0,
    paddingHorizontal: 10,
  },
  sectionTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 30,
    textShadowColor: 'rgba(255, 215, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 8,
  },
  trustSection: {
    paddingHorizontal: 20,
    paddingVertical: 40,
  },
  trustGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  trustBadge: {
    width: (width - 60) / 2,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  trustIconContainer: {
    marginBottom: 12,
  },
  trustIconGradient: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  trustTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 6,
  },
  trustDescription: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    lineHeight: 16,
  },
  featuresSection: {
    paddingHorizontal: 20,
    paddingVertical: 40,
    paddingBottom: 20,
  },
  featuresGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  featureCard: {
    width: (width - 60) / 2,
    marginBottom: 20,
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  featureGradient: {
    padding: 16,
    alignItems: 'center',
    minHeight: 200,
    justifyContent: 'space-between',
  },
  featureIconContainer: {
    marginBottom: 16,
  },
  featureIconGradient: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  featureIcon: {
    fontSize: 28,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#333',
    textAlign: 'center',
    marginBottom: 8,
  },
  featureDescription: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    lineHeight: 18,
  },
  securitySection: {
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  securityCard: {
    borderRadius: 24,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  securityHeader: {
    alignItems: 'center',
    marginBottom: 24,
  },
  securityIconContainer: {
    marginBottom: 16,
  },
  securityIconGradient: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },
  securityTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#333',
    textAlign: 'center',
  },
  securityFeatures: {
    gap: 16,
  },
  securityFeature: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  securityFeatureText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '500',
  },
  socialProofSection: {
    paddingHorizontal: 20,
    paddingVertical: 40,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: '800',
    color: '#FFD700',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '500',
  },
  ctaSection: {
    paddingHorizontal: 40,
    paddingVertical: 60,
    alignItems: 'center',
  },
  buttonContainer: {
    width: '100%',
    alignItems: 'center',
  },
  getStartedButton: {
    paddingHorizontal: 32,
    paddingVertical: 18,
    borderRadius: 30,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#FF6B35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.5,
    shadowRadius: 20,
    elevation: 12,
    marginBottom: 20,
    minWidth: 280,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: width < 375 ? 16 : 18,
    fontWeight: '700',
    marginRight: 8,
    letterSpacing: 0.5,
    flexShrink: 1,
  },
  buttonIcon: {
    fontSize: 20,
  },
  ctaSubtext: {
    alignItems: 'center',
  },
  ctaSubtextMain: {
    fontSize: 16,
    color: '#FFD700',
    fontWeight: '600',
    marginBottom: 4,
  },
  ctaSubtextSub: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    fontWeight: '400',
  },
  secondaryButton: {
    marginTop: 16,
    borderRadius: 25,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  secondaryButtonGradient: {
    paddingHorizontal: 28,
    paddingVertical: 14,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default WelcomeScreen;