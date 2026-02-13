import React, { useEffect, useRef } from 'react';
import { Animated, Easing } from 'react-native';
import Svg, { Circle, Path, G, Defs, LinearGradient, Stop, Text as SvgText } from 'react-native-svg';

const AnimatedG = Animated.createAnimatedComponent(G);

const ZodiacLoader = ({ size = 60 }) => {
  const rotation = useRef(new Animated.Value(0)).current;
  const glow = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(rotation, {
        toValue: 1,
        duration: 4000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(glow, {
          toValue: 1,
          duration: 1500,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(glow, {
          toValue: 0,
          duration: 1500,
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

  const glowOpacity = glow.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 1],
  });

  return (
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Defs>
        <LinearGradient id="wheelGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <Stop offset="0%" stopColor="#9C27B0" stopOpacity="0.8" />
          <Stop offset="50%" stopColor="#673AB7" stopOpacity="0.6" />
          <Stop offset="100%" stopColor="#FF6B35" stopOpacity="0.8" />
        </LinearGradient>
      </Defs>

      {/* Outer glow ring */}
      <Animated.Circle
        cx="50"
        cy="50"
        r="35"
        fill="none"
        stroke="url(#wheelGradient)"
        strokeWidth="2"
        opacity={glowOpacity}
      />

      {/* Rotating wheel */}
      <AnimatedG rotation={rotate} origin="50, 50">
        {/* 12 zodiac dots */}
        {[...Array(12)].map((_, i) => {
          const angle = (i * 30 - 90) * (Math.PI / 180);
          const x = 50 + 30 * Math.cos(angle);
          const y = 50 + 30 * Math.sin(angle);
          return (
            <Circle
              key={i}
              cx={x}
              cy={y}
              r="2"
              fill="#FFD700"
              opacity={0.8}
            />
          );
        })}
        
        {/* Connecting lines */}
        <Circle cx="50" cy="50" r="30" fill="none" stroke="rgba(255,215,0,0.3)" strokeWidth="1" />
        <Circle cx="50" cy="50" r="20" fill="none" stroke="rgba(156,39,176,0.3)" strokeWidth="1" />
      </AnimatedG>

      {/* Center symbol */}
      <SvgText
        x="50"
        y="55"
        fontSize="20"
        fill="#FFD700"
        textAnchor="middle"
      >
        ☉
      </SvgText>
    </Svg>
  );
};

export default ZodiacLoader;
