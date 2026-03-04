import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
  ScrollView,
  Image,
} from 'react-native';
const { width } = Dimensions.get('window');

export default function WelcomeScreen({ navigateToScreen, setIsLogin }) {
  const logoAnim = useRef(new Animated.Value(0)).current;
  const glowAnim = useRef(new Animated.Value(0)).current;
  const titleAnim = useRef(new Animated.Value(50)).current;
  const buttonAnim = useRef(new Animated.Value(100)).current;

  useEffect(() => {
    Animated.sequence([
      Animated.timing(logoAnim, {
        toValue: 1,
        duration: 900,
        useNativeDriver: true,
      }),
      Animated.timing(glowAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(titleAnim, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }),
      Animated.timing(buttonAnim, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const handleSignIn = () => {
    setIsLogin(true);
    navigateToScreen('phone');
  };

  const handleCreateAccount = () => {
    setIsLogin(false);
    navigateToScreen('phone');
  };

  const glowOpacity = glowAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 0.6],
  });

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
      bounces={true}
    >
      <View style={styles.content}>
        {/* Logo with glow ring */}
        <Animated.View
          style={[
            styles.logoWrapper,
            {
              opacity: logoAnim,
              transform: [
                {
                  scale: logoAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0.6, 1],
                  }),
                },
              ],
            },
          ]}
        >
          <Animated.View style={[styles.logoGlow, { opacity: glowOpacity }]} />
          <View style={styles.logoRing} />
          <View style={styles.logoImageWrap}>
            <Image
              source={require('../../../../assets/logo.png')}
              style={styles.logoImage}
              resizeMode="cover"
            />
          </View>
        </Animated.View>

        <Animated.View
          style={[
            styles.titleContainer,
            {
              transform: [{ translateY: titleAnim }],
              opacity: titleAnim.interpolate({
                inputRange: [0, 50],
                outputRange: [1, 0],
              }),
            },
          ]}
        >
          <Text style={styles.title}>AstroRoshni</Text>
          <View style={styles.subtitleLine} />
          <Text style={styles.subtitle}>Learn Vedic chart methods</Text>
        </Animated.View>

        <Animated.View
          style={[
            styles.buttonContainer,
            {
              transform: [{ translateY: buttonAnim }],
              opacity: buttonAnim.interpolate({
                inputRange: [0, 100],
                outputRange: [1, 0],
              }),
            },
          ]}
        >
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={handleSignIn}
            activeOpacity={0.9}
          >
            <View style={[styles.buttonGradient, styles.primaryButtonInner]}>
              <Text style={styles.primaryButtonText}>Sign In</Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={handleCreateAccount}
            activeOpacity={0.85}
          >
            <View style={styles.secondaryButtonInner}>
              <Text style={styles.secondaryButtonText}>Create New Account</Text>
            </View>
          </TouchableOpacity>
        </Animated.View>
      </View>

      <View style={styles.footer}>
        <View style={styles.footerDots}>
          <View style={[styles.dot, styles.dot1]} />
          <View style={[styles.dot, styles.dot2]} />
          <View style={[styles.dot, styles.dot3]} />
        </View>
        <Text style={styles.footerText}>Practice reading Vedic chart diagrams</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'space-between',
    paddingTop: 24,
    paddingBottom: 32,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  logoWrapper: {
    position: 'relative',
    width: 140,
    height: 140,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 48,
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
  titleContainer: {
    alignItems: 'center',
    marginBottom: 56,
    width: '100%',
    paddingHorizontal: 16,
  },
  title: {
    fontSize: width < 375 ? 30 : 38,
    fontWeight: '800',
    color: '#000000',
    marginBottom: 8,
    textAlign: 'center',
    letterSpacing: 2,
  },
  subtitleLine: {
    width: 48,
    height: 3,
    borderRadius: 2,
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    marginBottom: 14,
  },
  subtitle: {
    fontSize: width < 375 ? 16 : 18,
    color: '#666666',
    textAlign: 'center',
    fontWeight: '400',
    letterSpacing: 0.8,
    lineHeight: 24,
  },
  buttonContainer: {
    width: '100%',
    gap: 14,
    paddingHorizontal: 8,
  },
  primaryButton: {
    borderRadius: 28,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 6,
  },
  buttonGradient: {
    paddingVertical: 18,
    paddingHorizontal: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButtonInner: {
    backgroundColor: '#000000',
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  secondaryButton: {
    borderRadius: 28,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'rgba(0, 0, 0, 0.22)',
  },
  secondaryButtonInner: {
    paddingVertical: 16,
    paddingHorizontal: 32,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'transparent',
  },
  secondaryButtonText: {
    color: '#333333',
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  footer: {
    paddingBottom: 24,
    alignItems: 'center',
  },
  footerDots: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginBottom: 10,
  },
  dot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(0, 0, 0, 0.35)',
  },
  dot1: { opacity: 0.5 },
  dot2: { opacity: 0.8 },
  dot3: { opacity: 0.5 },
  footerText: {
    color: '#666666',
    fontSize: 13,
    fontWeight: '400',
    letterSpacing: 0.5,
  },
});