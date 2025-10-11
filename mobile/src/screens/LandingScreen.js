import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';

const { width, height } = Dimensions.get('window');

export default function LandingScreen({ navigation }) {
  const [rotateAnim] = useState(new Animated.Value(0));
  const [floatAnim] = useState(new Animated.Value(0));
  const [twinkleAnim] = useState(new Animated.Value(0));

  useEffect(() => {
    // Rotation animation
    Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 60000,
        useNativeDriver: true,
      })
    ).start();

    // Float animation
    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, {
          toValue: 1,
          duration: 3000,
          useNativeDriver: true,
        }),
        Animated.timing(floatAnim, {
          toValue: 0,
          duration: 3000,
          useNativeDriver: true,
        }),
      ])
    ).start();

    // Twinkle animation
    Animated.loop(
      Animated.sequence([
        Animated.timing(twinkleAnim, {
          toValue: 1,
          duration: 2000,
          useNativeDriver: true,
        }),
        Animated.timing(twinkleAnim, {
          toValue: 0,
          duration: 2000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  const zodiacSigns = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];

  const rotateInterpolate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const floatInterpolate = floatAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, -10],
  });

  const twinkleInterpolate = twinkleAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 1],
  });

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient
        colors={['#1a1a2e', '#16213e', '#0f3460']}
        style={styles.gradient}
      >
        {/* Moving Stars Background */}
        <Animated.View style={[styles.starsField, { transform: [{ translateX: rotateAnim.interpolate({ inputRange: [0, 1], outputRange: [0, -200] }) }] }]}>
          {[...Array(100)].map((_, i) => (
            <Animated.View
              key={i}
              style={[
                styles.star,
                {
                  left: (i * 47) % width,
                  top: (i * 23) % height,
                  opacity: twinkleInterpolate,
                  backgroundColor: ['#fff', '#ff6b35', '#f7931e', '#ffcc80'][i % 4],
                }
              ]}
            />
          ))}
        </Animated.View>

        {/* Orbiting Planets */}
        <Animated.View style={[styles.orbitingPlanet1, { 
          transform: [
            { translateX: floatAnim.interpolate({ inputRange: [0, 1], outputRange: [0, 50] }) },
            { translateY: floatAnim.interpolate({ inputRange: [0, 1], outputRange: [0, -30] }) },
            { rotate: rotateInterpolate }
          ]
        }]} />
        <Animated.View style={[styles.orbitingPlanet2, { 
          transform: [
            { translateX: floatAnim.interpolate({ inputRange: [0, 1], outputRange: [0, -50] }) },
            { translateY: floatAnim.interpolate({ inputRange: [0, 1], outputRange: [0, -60] }) },
            { rotate: rotateAnim.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '-360deg'] }) }
          ]
        }]} />
        <Animated.View style={[styles.orbitingPlanet3, { 
          transform: [
            { translateX: floatAnim.interpolate({ inputRange: [0, 1], outputRange: [0, -30] }) },
            { translateY: floatAnim.interpolate({ inputRange: [0, 1], outputRange: [0, 40] }) },
            { rotate: rotateAnim.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '270deg'] }) }
          ]
        }]} />

        <View style={styles.heroContent}>
          <View style={styles.heroText}>
            <Animated.Text style={[styles.heroTitle, { transform: [{ translateY: floatInterpolate }] }]}>
              <Text style={styles.mystical}>✨</Text>
              {'\n'}Discover Your{'\n'}Cosmic Journey{'\n'}
              <Text style={styles.mystical}>🌟</Text>
            </Animated.Text>
            
            <Text style={styles.heroSubtitle}>
              Unlock the secrets of your birth chart with authentic Vedic astrology
            </Text>

            <View style={styles.featuresGrid}>
              <View style={styles.feature}>
                <Text style={styles.featureIcon}>🌙</Text>
                <Text style={styles.featureText}>Precise Calculations</Text>
              </View>
              <View style={styles.feature}>
                <Text style={styles.featureIcon}>⭐</Text>
                <Text style={styles.featureText}>Vedic Traditions</Text>
              </View>
              <View style={styles.feature}>
                <Text style={styles.featureIcon}>🔮</Text>
                <Text style={styles.featureText}>Life Predictions</Text>
              </View>
              <View style={styles.feature}>
                <Text style={styles.featureIcon}>🌟</Text>
                <Text style={styles.featureText}>Dasha Analysis</Text>
              </View>
            </View>

            <TouchableOpacity
              style={styles.ctaButton}
              onPress={() => navigation.navigate('Login')}
            >
              <Text style={styles.ctaButtonText}>Begin Your Reading</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.heroVisual}>
            <Animated.View style={[styles.zodiacWheel, { transform: [{ rotate: rotateInterpolate }] }]}>
              <View style={styles.wheelCenter}>
                <Text style={styles.centerSymbol}>☉</Text>
              </View>
              {zodiacSigns.map((sign, i) => (
                <View
                  key={i}
                  style={[
                    styles.zodiacSign,
                    {
                      transform: [
                        { rotate: `${i * 30}deg` },
                        { translateY: -100 },
                        { rotate: `${-i * 30}deg` }
                      ]
                    }
                  ]}
                >
                  <Text style={styles.zodiacSignText}>{sign}</Text>
                </View>
              ))}
            </Animated.View>
          </View>
        </View>
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
  starsField: {
    position: 'absolute',
    width: width * 2,
    height: '100%',
  },
  star: {
    position: 'absolute',
    width: 4,
    height: 4,
    borderRadius: 2,
    shadowColor: '#fff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius: 8,
    elevation: 5,
  },
  orbitingPlanet1: {
    position: 'absolute',
    top: '20%',
    left: '10%',
    width: 12,
    height: 12,
    backgroundColor: '#ff6b35',
    borderRadius: 6,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 15,
    elevation: 8,
  },
  orbitingPlanet2: {
    position: 'absolute',
    bottom: '30%',
    right: '20%',
    width: 8,
    height: 8,
    backgroundColor: '#f7931e',
    borderRadius: 4,
    shadowColor: '#f7931e',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 12,
    elevation: 6,
  },
  orbitingPlanet3: {
    position: 'absolute',
    top: '60%',
    left: '20%',
    width: 6,
    height: 6,
    backgroundColor: '#ffcc80',
    borderRadius: 3,
    shadowColor: '#ffcc80',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 10,
    elevation: 4,
  },
  heroContent: {
    flex: 1,
    paddingHorizontal: 20,
    paddingVertical: 20,
    justifyContent: 'space-between',
  },
  heroText: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
  },
  heroTitle: {
    fontSize: 28,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 15,
    color: '#ff6f00',
    lineHeight: 34,
  },
  mystical: {
    fontSize: 22,
  },
  heroSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    marginBottom: 25,
    lineHeight: 22,
    paddingHorizontal: 10,
  },
  featuresGrid: {
    width: '100%',
    marginBottom: 25,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 111, 0, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 111, 0, 0.3)',
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
  },
  featureIcon: {
    fontSize: 18,
    marginRight: 10,
  },
  featureText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '500',
  },
  ctaButton: {
    backgroundColor: '#ff6f00',
    paddingVertical: 15,
    paddingHorizontal: 35,
    borderRadius: 25,
    shadowColor: '#ff6f00',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 15,
    elevation: 8,
  },
  ctaButtonText: {
    color: 'white',
    fontSize: 17,
    fontWeight: '600',
    textAlign: 'center',
  },
  heroVisual: {
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 20,
  },
  zodiacWheel: {
    width: 200,
    height: 200,
    borderWidth: 3,
    borderColor: 'rgba(255, 111, 0, 0.6)',
    borderRadius: 100,
    position: 'relative',
    justifyContent: 'center',
    alignItems: 'center',
  },
  wheelCenter: {
    width: 45,
    height: 45,
    backgroundColor: '#ff6f00',
    borderRadius: 22.5,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#ff6f00',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 15,
    elevation: 8,
  },
  centerSymbol: {
    fontSize: 22,
    color: 'white',
    fontWeight: 'bold',
  },
  zodiacSign: {
    position: 'absolute',
    width: 28,
    height: 28,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 2,
    borderColor: 'rgba(255, 111, 0, 0.4)',
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  zodiacSignText: {
    fontSize: 14,
    color: '#ff6f00',
    fontWeight: 'bold',
  },
});