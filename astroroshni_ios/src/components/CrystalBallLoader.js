import React, { useEffect, useRef } from 'react';
import { Animated, Easing } from 'react-native';
import Svg, { Circle, Path, G, Defs, RadialGradient, Stop, Ellipse } from 'react-native-svg';

const AnimatedCircle = Animated.createAnimatedComponent(Circle);
const AnimatedG = Animated.createAnimatedComponent(G);
const AnimatedPath = Animated.createAnimatedComponent(Path);

const CrystalBallLoader = ({ size = 60 }) => {
  const rotation1 = useRef(new Animated.Value(0)).current;
  const rotation2 = useRef(new Animated.Value(0)).current;
  const pulse = useRef(new Animated.Value(1)).current;
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(rotation1, {
        toValue: 1,
        duration: 3000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();

    Animated.loop(
      Animated.timing(rotation2, {
        toValue: 1,
        duration: 4000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, {
          toValue: 1.15,
          duration: 1200,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          toValue: 1,
          duration: 1200,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();

    Animated.loop(
      Animated.timing(shimmer, {
        toValue: 1,
        duration: 2000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();
  }, []);

  const rotate1 = rotation1.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const rotate2 = rotation2.interpolate({
    inputRange: [0, 1],
    outputRange: ['360deg', '0deg'],
  });

  const shimmerOpacity = shimmer.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [0.3, 1, 0.3],
  });

  return (
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Defs>
        <RadialGradient id="ballGradient" cx="40%" cy="40%">
          <Stop offset="0%" stopColor="#E1BEE7" stopOpacity="1" />
          <Stop offset="40%" stopColor="#9C27B0" stopOpacity="0.8" />
          <Stop offset="70%" stopColor="#673AB7" stopOpacity="0.6" />
          <Stop offset="100%" stopColor="#311B92" stopOpacity="0.4" />
        </RadialGradient>
        <RadialGradient id="glowGradient" cx="50%" cy="50%">
          <Stop offset="0%" stopColor="#FFD700" stopOpacity="0.8" />
          <Stop offset="50%" stopColor="#FF6B35" stopOpacity="0.4" />
          <Stop offset="100%" stopColor="#9C27B0" stopOpacity="0" />
        </RadialGradient>
      </Defs>

      {/* Outer glow */}
      <AnimatedCircle
        cx="50"
        cy="50"
        r="40"
        fill="url(#glowGradient)"
        opacity={shimmerOpacity}
      />

      {/* Crystal ball */}
      <AnimatedCircle
        cx="50"
        cy="50"
        r="25"
        fill="url(#ballGradient)"
        scale={pulse}
        origin="50, 50"
      />

      {/* Swirling particles - outer ring */}
      <AnimatedG rotation={rotate1} origin="50, 50">
        {[0, 60, 120, 180, 240, 300].map((angle) => {
          const rad = (angle * Math.PI) / 180;
          const x = 50 + 20 * Math.cos(rad);
          const y = 50 + 20 * Math.sin(rad);
          return (
            <Circle
              key={`outer-${angle}`}
              cx={x}
              cy={y}
              r="2"
              fill="#FFD700"
              opacity="0.8"
            />
          );
        })}
      </AnimatedG>

      {/* Swirling particles - inner ring */}
      <AnimatedG rotation={rotate2} origin="50, 50">
        {[30, 90, 150, 210, 270, 330].map((angle) => {
          const rad = (angle * Math.PI) / 180;
          const x = 50 + 12 * Math.cos(rad);
          const y = 50 + 12 * Math.sin(rad);
          return (
            <Circle
              key={`inner-${angle}`}
              cx={x}
              cy={y}
              r="1.5"
              fill="#FF6B35"
              opacity="0.9"
            />
          );
        })}
      </AnimatedG>

      {/* Highlight shine */}
      <Ellipse
        cx="42"
        cy="42"
        rx="8"
        ry="12"
        fill="rgba(255, 255, 255, 0.4)"
        transform="rotate(-30 42 42)"
      />

      {/* Center mystical symbol */}
      <Circle cx="50" cy="50" r="4" fill="#FFD700" opacity="0.9" />
    </Svg>
  );
};

export default CrystalBallLoader;
