import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Image, Text } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'react-native';

const SplashScreen = () => {
  const glowAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    Animated.loop(
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
    ).start();

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
  }, []);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a0033" />
      <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']} style={styles.gradientBg}>
        <SafeAreaView style={styles.safeArea}>
          <Animated.View style={[styles.content, {opacity: fadeAnim, transform: [{translateY: slideAnim}]}]}>
            <Animated.View style={[styles.logoContainer, {
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
            <Text style={styles.title}>AstroRoshni</Text>
            <Text style={styles.subtitle}>Your Cosmic Guide</Text>
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
  },
  logoContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    marginBottom: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    elevation: 8,
  },
  logoImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
  },
  title: {
    fontSize: 40,
    fontWeight: '800',
    color: '#ffffff',
    textAlign: 'center',
    marginBottom: 12,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  subtitle: {
    fontSize: 18,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    lineHeight: 24,
  },
});

export default SplashScreen;
