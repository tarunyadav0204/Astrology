import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Image, Text } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'react-native';
import { THEME_PALETTES, normalizeThemeId } from '../theme/tokens';

const SplashScreen = ({ themeId = 'heritage', panditMode = false }) => {
  const resolvedThemeId = panditMode ? 'pandit' : normalizeThemeId(themeId);
  const colors = THEME_PALETTES[resolvedThemeId] || THEME_PALETTES.heritage;
  const splashSurface = colors.cosmicSurface || colors.headerSurface || colors.background;
  const splashRaised = colors.cosmicRaised || colors.surfaceInverse || splashSurface;
  const splashAccent = colors.accent || colors.primary;
  const splashText = colors.textInverse || colors.onPrimary || colors.text;
  const splashTextMuted = colors.textInverseMuted || colors.textSecondary;
  const splashLine = colors.cosmicLine || colors.cardBorder;
  const splashGlow = colors.cosmicGlow || colors.accentSoft || colors.primary;
  const glowAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    const glowLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 1,
          duration: 1500,
          useNativeDriver: false,
        }),
        Animated.timing(glowAnim, {
          toValue: 0,
          duration: 1500,
          useNativeDriver: false,
        }),
      ])
    );
    glowLoop.start();

    Animated.parallel([
        Animated.timing(fadeAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
        }),
        Animated.spring(slideAnim, {
            toValue: 0,
            tension: 50,
            friction: 8,
            useNativeDriver: true,
        }),
    ]).start();
    return () => {
      glowLoop.stop();
    };
  }, []);

  return (
    <View style={[styles.container, { backgroundColor: splashSurface }]}>
      <StatusBar barStyle="light-content" backgroundColor={splashSurface} />
      <LinearGradient
        colors={[splashSurface, splashRaised, splashSurface]}
        locations={[0, 0.52, 1]}
        style={styles.gradientBg}
      >
        <View pointerEvents="none" style={[styles.orbit, styles.orbitLarge, { borderColor: splashLine }]} />
        <View pointerEvents="none" style={[styles.orbit, styles.orbitSmall, { borderColor: splashLine }]} />
        <SafeAreaView style={styles.safeArea}>
          <Animated.View style={[styles.content, {opacity: fadeAnim, transform: [{translateY: slideAnim}]}]}>
            <Animated.View style={[styles.logoContainer, {
                backgroundColor: splashRaised,
                borderColor: splashAccent,
                shadowColor: splashGlow,
                shadowOpacity: glowAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0.6, 1],
                }),
                shadowRadius: glowAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [12, 20],
                }),
                transform: [{
                    scale: glowAnim.interpolate({
                        inputRange: [0, 1],
                        outputRange: [1, 1.1],
                    })
                }]
            }]}>
              <Image 
                source={require('../../assets/logo.png')}
                style={styles.logoImage}
                resizeMode="contain"
              />
            </Animated.View>
            <Text style={[styles.eyebrow, { color: splashAccent }]}>THE VEDIC SKY, INTERPRETED</Text>
            <Text style={[styles.title, { color: splashText }]}>AstroRoshni</Text>
            <Text style={[styles.subtitle, { color: splashTextMuted }]}>Your Vedic guide</Text>
            <View style={[styles.rule, { backgroundColor: splashAccent }]} />
          </Animated.View>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradientBg: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  logoContainer: {
    width: 112,
    height: 112,
    borderRadius: 32,
    marginBottom: 28,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
    shadowOffset: { width: 0, height: 4 },
    elevation: 8,
  },
  logoImage: {
    width: 92,
    height: 92,
    borderRadius: 26,
  },
  eyebrow: {
    marginBottom: 12,
    fontSize: 11,
    lineHeight: 15,
    fontWeight: '800',
    letterSpacing: 2.1,
    textAlign: 'center',
  },
  title: {
    fontFamily: 'serif',
    fontSize: 43,
    lineHeight: 50,
    fontWeight: '500',
    textAlign: 'center',
    marginBottom: 8,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  subtitle: {
    fontSize: 15,
    fontWeight: '600',
    letterSpacing: 0.6,
    textAlign: 'center',
    lineHeight: 22,
  },
  rule: {
    width: 44,
    height: 1,
    marginTop: 22,
    opacity: 0.78,
  },
  orbit: {
    position: 'absolute',
    borderWidth: 1,
    borderRadius: 999,
    opacity: 0.75,
  },
  orbitLarge: {
    width: 310,
    height: 310,
    top: -170,
    right: -110,
  },
  orbitSmall: {
    width: 176,
    height: 176,
    bottom: -82,
    left: -68,
  },
});

export default SplashScreen;
