import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  Image,
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
      <View style={styles.featureGradient}>
        <View style={styles.featureIconContainer}>
          <View style={styles.featureIconGradient}>
            <Text style={styles.featureIcon}>{icon}</Text>
          </View>
        </View>
        <Text style={styles.featureTitle}>{title}</Text>
        <Text style={styles.featureDescription}>{description}</Text>
      </View>
    </Animated.View>
  );
};

const WelcomeScreen = ({ navigation }) => {
  const logoScale = useRef(new Animated.Value(0)).current;
  const titleOpacity = useRef(new Animated.Value(0)).current;
  const subtitleOpacity = useRef(new Animated.Value(0)).current;
  const buttonOpacity = useRef(new Animated.Value(0)).current;
  

  
  const features = [
    { icon: '📊', title: 'Birth Chart Diagrams', description: 'North & South Indian layouts with precise Swiss-Ephemeris calculations' },
    { icon: '📐', title: 'Vedic Calculators', description: 'Explore houses, divisional charts, and classical combinations as structured formulas' },
    { icon: '🧭', title: 'Dasha & Period Viewers', description: 'See how traditional time-period tables are constructed in Vedic chart methods' },
    { icon: '📚', title: 'Concept Library', description: 'Step-by-step explanations of houses, planets, and key chart building blocks' },
    { icon: '⊞', title: 'Ashtakavarga Tables', description: 'Visualize point-based strength grids used in Vedic chart mathematics' },
    { icon: '🧪', title: 'Chart Lab Mode', description: 'Use your chart as a worked example to practice reading techniques' },
  ];

  useEffect(() => {
    // Check if user is already logged in
    checkAuthStatus();
    
    // Logo entrance animation
    Animated.sequence([
      Animated.timing(logoScale, {
        toValue: 1,
        duration: 900,
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
  }, []);

  const checkAuthStatus = async () => {
    try {
      const authToken = await storage.getAuthToken();
      const birthDetails = await storage.getBirthDetails();
      
      if (authToken && birthDetails) {
        // User is logged in and has birth details, go to Home
        navigation.replace('Home');
      } else if (authToken) {
        // Already logged in but no birth details: go to Home (empty state + Add profile CTA)
        navigation.replace('Home');
      }
      // If no auth token, stay on Welcome screen
    } catch (error) {

    }
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      
      {/* White theme background */}
      <LinearGradient
        colors={['#ffffff', '#f8f8f8', '#f5f5f5']}
        style={styles.background}
        start={{ x: 0.2, y: 0 }}
        end={{ x: 0.8, y: 1 }}
      />
      <View style={styles.backgroundGlow} pointerEvents="none" />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        bounces={true}
        scrollEnabled={true}
      >
        {/* Hero Section — same logo as Auth Welcome (glow + ring + image) */}
        <View style={styles.heroSection}>
          <Animated.View
            style={[
              styles.logoWrapper,
              {
                opacity: logoScale,
                transform: [
                  {
                    scale: logoScale.interpolate({
                      inputRange: [0, 1],
                      outputRange: [0.6, 1],
                    }),
                  },
                ],
              },
            ]}
          >
            <View style={styles.logoGlow} />
            <View style={styles.logoRing} />
            <View style={styles.logoImageWrap}>
              <Image
                source={require('../../../assets/logo.png')}
                style={styles.logoImage}
                resizeMode="cover"
              />
            </View>
          </Animated.View>

          <Animated.Text
            style={[styles.appTitle, { opacity: titleOpacity }]}
            numberOfLines={1}
            adjustsFontSizeToFit
          >
            AstroRoshni
          </Animated.Text>
          <View style={styles.titleAccent} />
          <Animated.View style={[styles.taglineContainer, { opacity: subtitleOpacity }]}>
            <Text style={styles.tagline}>Learn Vedic cosmic mathematics</Text>
            <Text style={styles.subtitle}>Use your birth chart as a case study to understand classical chart diagrams and calculations.</Text>
            <TouchableOpacity
              onPress={() => navigation.navigate('Login')}
              activeOpacity={0.88}
              style={styles.heroCtaWrap}
            >
              <View style={styles.heroCtaButton}>
                <Text style={styles.heroCtaText} numberOfLines={1} adjustsFontSizeToFit>
                  Begin Your Cosmic Journey
                </Text>
                <Text style={styles.buttonIcon}>✦</Text>
              </View>
            </TouchableOpacity>
          </Animated.View>
        </View>

        {/* Trust & Privacy — single merged section */}
        <View style={styles.trustSection}>
          <Text style={styles.sectionTitle}>Trust & Privacy</Text>
          <View style={styles.trustPrivacyCard}>
            <View style={styles.trustPrivacyList}>
              <View style={styles.trustPrivacyItem}>
                <Ionicons name="lock-closed" size={20} color="#4CAF50" style={styles.trustPrivacyIcon} />
                <Text style={styles.trustPrivacyText}>Your data is encrypted and never sold or shared</Text>
              </View>
              <View style={styles.trustPrivacyItem}>
                <Ionicons name="telescope" size={20} color="#FF6B35" style={styles.trustPrivacyIcon} />
                <Text style={styles.trustPrivacyText}>Swiss Ephemeris for precise calculations</Text>
              </View>
              <View style={styles.trustPrivacyItem}>
                <Ionicons name="eye-off" size={20} color="#4CAF50" style={styles.trustPrivacyIcon} />
                <Text style={styles.trustPrivacyText}>We don’t share your birth details with third parties</Text>
              </View>
              <View style={styles.trustPrivacyItem}>
                <Ionicons name="ribbon" size={20} color="#FF6B35" style={styles.trustPrivacyIcon} />
                <Text style={styles.trustPrivacyText}>Rooted in traditional Vedic chart methods</Text>
              </View>
              <View style={styles.trustPrivacyItem}>
                <Ionicons name="gift" size={20} color="#4CAF50" style={styles.trustPrivacyIcon} />
                <Text style={styles.trustPrivacyText}>Free to start — no credit card required</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Features Section */}
        <View style={styles.featuresSection}>
          <Text style={styles.sectionTitle}>Explore Vedic Chart Tools</Text>
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

        {/* CTA Section */}
        <View style={styles.ctaSection}>
          <Animated.View style={[styles.buttonContainer, { opacity: buttonOpacity }]}>
            <TouchableOpacity onPress={() => navigation.navigate('Login')} activeOpacity={0.88} style={styles.getStartedButtonWrap}>
              <View style={styles.getStartedButton}>
                <Text style={styles.buttonText} numberOfLines={1} adjustsFontSizeToFit>Begin Your Cosmic Journey</Text>
                <Text style={styles.buttonIcon}>✦</Text>
              </View>
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
              <Text style={styles.ctaSubtextSub}>Free to start • No credit card required</Text>
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
    backgroundColor: '#ffffff',
  },
  background: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
    pointerEvents: 'none',
  },
  backgroundGlow: {
    position: 'absolute',
    top: '15%',
    left: '50%',
    marginLeft: -150,
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: 'rgba(0, 0, 0, 0.03)',
    pointerEvents: 'none',
  },
  scrollView: {
    flex: 1,
    width: '100%',
    height: '100%',
  },
  scrollContent: {
    paddingBottom: 48,
  },
  heroSection: {
    alignItems: 'center',
    paddingHorizontal: 36,
    paddingTop: 72,
    paddingBottom: 52,
  },
  logoWrapper: {
    position: 'relative',
    width: 140,
    height: 140,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 36,
    overflow: 'visible',
  },
  logoGlow: {
    position: 'absolute',
    width: 140,
    height: 140,
    borderRadius: 70,
    left: 0,
    top: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.06)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 4,
  },
  logoRing: {
    position: 'absolute',
    width: 108,
    height: 108,
    borderRadius: 54,
    left: 16,
    top: 16,
    borderWidth: 2,
    borderColor: 'rgba(0, 0, 0, 0.12)',
  },
  logoImageWrap: {
    width: 88,
    height: 88,
    borderRadius: 44,
    overflow: 'hidden',
    backgroundColor: 'rgba(0, 0, 0, 0.06)',
  },
  logoImage: {
    width: 88,
    height: 88,
  },
  appTitle: {
    fontSize: width < 375 ? 34 : width < 414 ? 40 : 44,
    fontWeight: '800',
    color: '#000000',
    letterSpacing: width < 375 ? 1.5 : 2.5,
    textAlign: 'center',
    marginBottom: 12,
    flexShrink: 0,
    paddingHorizontal: 12,
  },
  titleAccent: {
    width: 56,
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(0, 0, 0, 0.25)',
    marginBottom: 24,
  },
  taglineContainer: {
    alignItems: 'center',
  },
  tagline: {
    fontSize: width < 375 ? 19 : 22,
    color: '#333333',
    textAlign: 'center',
    marginBottom: 8,
    fontWeight: '600',
    letterSpacing: 0.8,
    flexShrink: 0,
    paddingHorizontal: 12,
  },
  subtitle: {
    fontSize: width < 375 ? 14 : 16,
    color: '#666666',
    textAlign: 'center',
    lineHeight: 24,
    fontWeight: '400',
    flexShrink: 0,
    paddingHorizontal: 12,
    marginBottom: 4,
  },
  heroCtaWrap: {
    marginTop: 28,
    alignSelf: 'center',
    maxWidth: 320,
    width: '100%',
  },
  heroCtaButton: {
    paddingHorizontal: 32,
    paddingVertical: 18,
    borderRadius: 30,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#000000',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 6,
  },
  heroCtaText: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.5,
    marginRight: 10,
  },
  sectionTitle: {
    fontSize: 26,
    fontWeight: '700',
    color: '#000000',
    textAlign: 'center',
    marginBottom: 24,
    letterSpacing: 0.5,
  },
  trustSection: {
    paddingHorizontal: 24,
    paddingVertical: 36,
  },
  trustPrivacyCard: {
    borderRadius: 24,
    padding: 24,
    overflow: 'hidden',
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.1)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 4,
  },
  trustPrivacyList: {},
  trustPrivacyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 18,
  },
  trustPrivacyIcon: {
    marginRight: 14,
  },
  trustPrivacyText: {
    fontSize: 15,
    color: '#333',
    fontWeight: '500',
    flex: 1,
    lineHeight: 22,
  },
  featuresSection: {
    paddingHorizontal: 24,
    paddingVertical: 36,
    paddingBottom: 24,
  },
  featuresGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  featureCard: {
    width: (width - 56) / 2,
    marginBottom: 18,
    borderRadius: 22,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.22,
    shadowRadius: 18,
    elevation: 8,
  },
  featureGradient: {
    padding: 18,
    alignItems: 'center',
    minHeight: 200,
    justifyContent: 'space-between',
    backgroundColor: '#ffffff',
    borderRadius: 22,
  },
  featureIconContainer: {
    marginBottom: 14,
  },
  featureIconGradient: {
    width: 52,
    height: 52,
    borderRadius: 26,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.08)',
  },
  featureIcon: {
    fontSize: 26,
  },
  featureTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#333',
    textAlign: 'center',
    marginBottom: 6,
  },
  featureDescription: {
    fontSize: 12,
    color: '#555',
    textAlign: 'center',
    lineHeight: 18,
  },
  ctaSection: {
    paddingHorizontal: 36,
    paddingVertical: 48,
    alignItems: 'center',
  },
  buttonContainer: {
    width: '100%',
    alignItems: 'center',
  },
  getStartedButtonWrap: {
    marginBottom: 20,
    minWidth: 280,
  },
  getStartedButton: {
    paddingHorizontal: 36,
    paddingVertical: 18,
    borderRadius: 30,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#000000',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 6,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: width < 375 ? 16 : 18,
    fontWeight: '700',
    marginRight: 10,
    letterSpacing: 0.5,
    flexShrink: 1,
  },
  buttonIcon: {
    fontSize: 18,
    color: 'rgba(255,255,255,0.95)',
  },
  ctaSubtext: {
    alignItems: 'center',
  },
  ctaSubtextSub: {
    fontSize: 13,
    color: '#666666',
    fontWeight: '400',
    letterSpacing: 0.3,
  },
  secondaryButton: {
    marginTop: 16,
    borderRadius: 28,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.25)',
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