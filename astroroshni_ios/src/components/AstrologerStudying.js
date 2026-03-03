import React, { useEffect, useRef } from 'react';
import { View, Animated } from 'react-native';
import Svg, { Circle, Path, G, Defs, LinearGradient, RadialGradient, Stop } from 'react-native-svg';

const AnimatedCircle = Animated.createAnimatedComponent(Circle);
const AnimatedG = Animated.createAnimatedComponent(G);
const AnimatedPath = Animated.createAnimatedComponent(Path);

const AstrologerStudying = () => {
  const rotation = useRef(new Animated.Value(0)).current;
  const pulse = useRef(new Animated.Value(0)).current;
  const glow = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(rotation, {
        toValue: 1,
        duration: 20000,
        useNativeDriver: true,
      })
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 2000, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 2000, useNativeDriver: true }),
      ])
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(glow, { toValue: 1, duration: 3000, useNativeDriver: true }),
        Animated.timing(glow, { toValue: 0, duration: 3000, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const rotate = rotation.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const scale = pulse.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 1.1],
  });

  const opacity = glow.interpolate({
    inputRange: [0, 1],
    outputRange: [0.9, 1],
  });

  return (
    <View style={{ alignItems: 'center', justifyContent: 'center' }}>
      <Svg width="200" height="200" viewBox="0 0 200 200">
        <Defs>
          <RadialGradient id="space" cx="50%" cy="50%" r="50%">
            <Stop offset="0%" stopColor="#1a1a3e" />
            <Stop offset="100%" stopColor="#0a0a1e" />
          </RadialGradient>
          
          <RadialGradient id="glow" cx="50%" cy="50%" r="50%">
            <Stop offset="0%" stopColor="#ffd700" stopOpacity="0.8" />
            <Stop offset="100%" stopColor="#ff8c00" stopOpacity="0" />
          </RadialGradient>
          
          <RadialGradient id="zodiacGrad" cx="50%" cy="50%" r="50%">
            <Stop offset="0%" stopColor="#fff" stopOpacity="0.95" />
            <Stop offset="70%" stopColor="#ffd700" stopOpacity="0.9" />
            <Stop offset="100%" stopColor="#ff8c00" stopOpacity="0.8" />
          </RadialGradient>
          
          <LinearGradient id="ray" x1="0%" y1="0%" x2="100%" y2="100%">
            <Stop offset="0%" stopColor="#ffd700" stopOpacity="0.6" />
            <Stop offset="100%" stopColor="#ff8c00" stopOpacity="0" />
          </LinearGradient>
        </Defs>

        <Circle cx="100" cy="100" r="100" fill="url(#space)" />

        {[0, 45, 90, 135, 180, 225, 270, 315].map((angle, i) => (
          <Path
            key={`ray-${i}`}
            d={`M 100 100 L ${100 + Math.cos((angle * Math.PI) / 180) * 100} ${100 + Math.sin((angle * Math.PI) / 180) * 100}`}
            stroke="url(#ray)"
            strokeWidth="2"
            opacity={i % 2 === 0 ? 0.3 : 0.15}
          />
        ))}

        {[...Array(25)].map((_, i) => {
          const x = 20 + Math.random() * 160;
          const y = 20 + Math.random() * 160;
          const size = 0.5 + Math.random() * 1.5;
          return (
            <Circle key={`star-${i}`} cx={x} cy={y} r={size} fill="#fff" opacity={0.6 + Math.random() * 0.4} />
          );
        })}

        <G transform="translate(100, 100)">
          <AnimatedCircle r="55" fill="url(#glow)" scale={scale} origin="0,0" />
          
          <AnimatedCircle r="45" fill="url(#zodiacGrad)" opacity={opacity} />
          
          {[...Array(12)].map((_, i) => {
            const angle = (i * 30 - 90) * Math.PI / 180;
            const nextAngle = ((i + 1) * 30 - 90) * Math.PI / 180;
            const innerR = 20;
            const outerR = 45;
            
            return (
              <Path
                key={`section-${i}`}
                d={`M ${Math.cos(angle) * innerR} ${Math.sin(angle) * innerR} 
                    L ${Math.cos(angle) * outerR} ${Math.sin(angle) * outerR} 
                    A ${outerR} ${outerR} 0 0 1 ${Math.cos(nextAngle) * outerR} ${Math.sin(nextAngle) * outerR} 
                    L ${Math.cos(nextAngle) * innerR} ${Math.sin(nextAngle) * innerR} 
                    A ${innerR} ${innerR} 0 0 0 ${Math.cos(angle) * innerR} ${Math.sin(angle) * innerR}`}
                fill="none"
                stroke="#ff8c00"
                strokeWidth="0.5"
                opacity="0.6"
              />
            );
          })}
          
          <Circle r="20" fill="#1a1a3e" opacity="0.3" />
          
          <AnimatedG rotation={rotate} origin="0,0">
            {[0, 120, 240].map((angle, i) => (
              <Path
                key={`center-${i}`}
                d={`M 0 0 L ${Math.cos((angle * Math.PI) / 180) * 15} ${Math.sin((angle * Math.PI) / 180) * 15}`}
                stroke="#ffd700"
                strokeWidth="2"
                strokeLinecap="round"
              />
            ))}
          </AnimatedG>
          
          <AnimatedCircle r="4" fill="#ffd700" scale={scale} origin="0,0" />
        </G>

        {[
          { color: '#ff6b6b', size: 5, radius: 70, speed: 8000, offset: 0 },
          { color: '#4ecdc4', size: 4, radius: 70, speed: 10000, offset: 90 },
          { color: '#95e1d3', size: 3.5, radius: 70, speed: 12000, offset: 180 },
          { color: '#f38181', size: 4.5, radius: 70, speed: 9000, offset: 270 },
        ].map((planet, i) => {
          const planetRotation = useRef(new Animated.Value(0)).current;
          
          useEffect(() => {
            Animated.loop(
              Animated.timing(planetRotation, {
                toValue: 1,
                duration: planet.speed,
                useNativeDriver: true,
              })
            ).start();
          }, []);

          const planetRotate = planetRotation.interpolate({
            inputRange: [0, 1],
            outputRange: [`${planet.offset}deg`, `${planet.offset + 360}deg`],
          });

          return (
            <AnimatedG key={`planet-${i}`} rotation={planetRotate} origin="100,100">
              <Circle cx="100" cy={100 - planet.radius} r={planet.size} fill={planet.color} opacity="0.9" />
              <Circle cx="100" cy={100 - planet.radius} r={planet.size * 1.5} fill={planet.color} opacity="0.2" />
            </AnimatedG>
          );
        })}

        <G opacity="0.3">
          <Path d="M 30 40 L 50 30 L 70 45" stroke="#fff" strokeWidth="0.5" />
          <Path d="M 130 35 L 150 45 L 165 30" stroke="#fff" strokeWidth="0.5" />
          <Path d="M 35 160 L 45 170 L 60 165" stroke="#fff" strokeWidth="0.5" />
        </G>
      </Svg>
    </View>
  );
};

export default AstrologerStudying;
