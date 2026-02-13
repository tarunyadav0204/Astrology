import React, { useEffect, useRef } from 'react';
import { Animated, Easing } from 'react-native';
import Svg, { Circle, G, Defs, RadialGradient, Stop } from 'react-native-svg';

const AnimatedCircle = Animated.createAnimatedComponent(Circle);
const AnimatedG = Animated.createAnimatedComponent(G);

const CosmicLoader = ({ size = 60 }) => {
  const rotation = useRef(new Animated.Value(0)).current;
  const pulse = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(rotation, {
        toValue: 1,
        duration: 3000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, {
          toValue: 1.2,
          duration: 1000,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          toValue: 1,
          duration: 1000,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  const rotate = rotation.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Defs>
        <RadialGradient id="sunGradient" cx="50%" cy="50%">
          <Stop offset="0%" stopColor="#FFD700" stopOpacity="1" />
          <Stop offset="50%" stopColor="#FFA500" stopOpacity="0.8" />
          <Stop offset="100%" stopColor="#FF6B35" stopOpacity="0.6" />
        </RadialGradient>
        <RadialGradient id="planetGradient" cx="50%" cy="50%">
          <Stop offset="0%" stopColor="#9C27B0" stopOpacity="1" />
          <Stop offset="100%" stopColor="#673AB7" stopOpacity="0.8" />
        </RadialGradient>
      </Defs>

      {/* Central Sun with pulse */}
      <AnimatedCircle
        cx="50"
        cy="50"
        r="8"
        fill="url(#sunGradient)"
        opacity={pulse}
      />
      
      {/* Orbiting planets */}
      <AnimatedG rotation={rotate} origin="50, 50">
        <Circle cx="50" cy="25" r="3" fill="url(#planetGradient)" />
        <Circle cx="75" cy="50" r="2.5" fill="#4CAF50" opacity="0.8" />
        <Circle cx="50" cy="75" r="3.5" fill="#2196F3" opacity="0.8" />
      </AnimatedG>
      
      {/* Orbit paths */}
      <Circle cx="50" cy="50" r="25" fill="none" stroke="rgba(255,215,0,0.2)" strokeWidth="0.5" strokeDasharray="2,2" />
    </Svg>
  );
};

export default CosmicLoader;
