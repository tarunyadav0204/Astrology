import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Animated,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../utils/constants';

const { width } = Dimensions.get('window');

export default function HomeScreen({ birthData, onOptionSelect }) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const starAnims = useRef([...Array(20)].map(() => new Animated.Value(0))).current;
  
  useEffect(() => {
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
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();
    
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.05,
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
    
    starAnims.forEach((anim, index) => {
      Animated.loop(
        Animated.sequence([
          Animated.delay(index * 100),
          Animated.timing(anim, {
            toValue: 1,
            duration: 2000,
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0,
            duration: 2000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    });
  }, []);
  
  const place = birthData?.place || `${birthData?.latitude}, ${birthData?.longitude}`;
  const time = birthData?.time || 'Unknown time';

  const options = [
    {
      id: 'question',
      icon: '💬',
      title: 'Ask Any Question',
      description: 'Get insights about your personality, relationships, career, or any astrological topic',
      action: 'question'
    },
    {
      id: 'periods',
      icon: '🎯',
      title: 'Find Event Periods',
      description: 'Discover high-probability periods when specific events might happen',
      action: 'periods'
    }
  ];

  const analysisOptions = [
    { 
      id: 'wealth', 
      title: 'Wealth Analysis', 
      icon: '💰', 
      description: 'Financial prospects & opportunities',
      gradient: ['#FFD700', '#FF8C00'],
      cost: 5
    },
    { 
      id: 'health', 
      title: 'Health Analysis', 
      icon: '🏥', 
      description: 'Wellness insights & precautions',
      gradient: ['#32CD32', '#228B22'],
      cost: 5
    },
    { 
      id: 'marriage', 
      title: 'Marriage Analysis', 
      icon: '💕', 
      description: 'Relationship compatibility & timing',
      gradient: ['#FF69B4', '#DC143C'],
      cost: 5
    },
    { 
      id: 'education', 
      title: 'Education Analysis', 
      icon: '🎓', 
      description: 'Learning path & career guidance',
      gradient: ['#4169E1', '#1E90FF'],
      cost: 5
    }
  ];

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']}
        style={styles.gradient}
      >
        {starAnims.map((anim, index) => {
          const top = Math.random() * 100;
          const left = Math.random() * 100;
          return (
            <Animated.View
              key={index}
              style={[
                styles.star,
                {
                  top: `${top}%`,
                  left: `${left}%`,
                  opacity: anim,
                },
              ]}
            >
              <Text style={styles.starText}>✨</Text>
            </Animated.View>
          );
        })}
        
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Animated.View style={[styles.greetingContainer, { opacity: fadeAnim, transform: [{ translateY: slideAnim }, { scale: scaleAnim }] }]}>
          <Animated.View style={[styles.cosmicOrb, { transform: [{ scale: pulseAnim }] }]}>
            <LinearGradient
              colors={['#ff6b35', '#ffd700', '#ff6b35']}
              style={styles.orbGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Text style={styles.orbIcon}>🔮</Text>
            </LinearGradient>
          </Animated.View>
          
          <Text style={styles.greetingTitle}>
            Welcome, {birthData?.name}!
          </Text>
          <View style={styles.birthInfoCard}>
            <Text style={styles.birthInfoText}>
              📅 {new Date(birthData?.date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            </Text>
            <Text style={styles.birthInfoText}>
              🕐 {time}
            </Text>
            <Text style={styles.birthInfoText}>
              📍 {place}
            </Text>
          </View>
          <Text style={styles.greetingSubtext}>
            Your cosmic blueprint awaits. Choose your path to enlightenment.
          </Text>
        </Animated.View>

        <Animated.View style={[styles.optionsContainer, { opacity: fadeAnim }]}>
          <Text style={styles.optionsTitle}>Choose Your Path</Text>
          {options.map((option, index) => {
            const cardDelay = (index + 1) * 200;
            const cardAnim = useRef(new Animated.Value(0)).current;
            
            useEffect(() => {
              Animated.sequence([
                Animated.delay(cardDelay),
                Animated.spring(cardAnim, {
                  toValue: 1,
                  tension: 50,
                  friction: 7,
                  useNativeDriver: true,
                }),
              ]).start();
            }, []);
            
            return (
              <Animated.View
                key={option.id}
                style={[
                  styles.optionCard,
                  {
                    opacity: cardAnim,
                    transform: [
                      {
                        translateY: cardAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: [50, 0],
                        }),
                      },
                      {
                        scale: cardAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: [0.9, 1],
                        }),
                      },
                    ],
                  },
                ]}
              >
                <TouchableOpacity
                  onPress={() => onOptionSelect(option)}
                  activeOpacity={0.9}
                >
                  <LinearGradient
                    colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                    style={styles.optionGradient}
                  >
                    <View style={styles.optionIconContainer}>
                      <LinearGradient
                        colors={['#ff6b35', '#ff8c5a']}
                        style={styles.optionIconGradient}
                      >
                        <Text style={styles.optionEmoji}>{option.icon}</Text>
                      </LinearGradient>
                    </View>
                    <View style={styles.optionContent}>
                      <Text style={styles.optionTitle}>{option.title}</Text>
                      <Text style={styles.optionDescription}>{option.description}</Text>
                    </View>
                    <Icon name="chevron-forward" size={24} color="rgba(255, 255, 255, 0.6)" />
                  </LinearGradient>
                </TouchableOpacity>
              </Animated.View>
            );
          })}
        </Animated.View>

        {/* Analysis Options */}
        <Animated.View style={[styles.analysisContainer, { opacity: fadeAnim }]}>
          <Text style={styles.analysisTitle}>🔮 Specialized Analysis</Text>
          {analysisOptions.map((option, index) => {
            const cardDelay = (index + 3) * 200;
            const cardAnim = useRef(new Animated.Value(0)).current;
            
            useEffect(() => {
              Animated.sequence([
                Animated.delay(cardDelay),
                Animated.spring(cardAnim, {
                  toValue: 1,
                  tension: 50,
                  friction: 7,
                  useNativeDriver: true,
                }),
              ]).start();
            }, []);
            
            return (
              <Animated.View
                key={option.id}
                style={[
                  styles.analysisCard,
                  {
                    opacity: cardAnim,
                    transform: [
                      {
                        translateY: cardAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: [50, 0],
                        }),
                      },
                      {
                        scale: cardAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: [0.9, 1],
                        }),
                      },
                    ],
                  },
                ]}
              >
                <TouchableOpacity
                  onPress={() => onOptionSelect({ action: 'analysis', type: option.id })}
                  activeOpacity={0.9}
                >
                  <LinearGradient
                    colors={option.gradient}
                    style={styles.analysisGradient}
                  >
                    <View style={styles.analysisIconContainer}>
                      <Text style={styles.analysisEmoji}>{option.icon}</Text>
                    </View>
                    <View style={styles.analysisContent}>
                      <Text style={styles.analysisCardTitle}>{option.title}</Text>
                      <Text style={styles.analysisDescription}>{option.description}</Text>
                      <Text style={styles.analysisCost}>{option.cost} credits</Text>
                    </View>
                    <Icon name="chevron-forward" size={24} color="rgba(255, 255, 255, 0.9)" />
                  </LinearGradient>
                </TouchableOpacity>
              </Animated.View>
            );
          })}
        </Animated.View>
      </ScrollView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  star: {
    position: 'absolute',
  },
  starText: {
    fontSize: 12,
  },
  greetingContainer: {
    alignItems: 'center',
    marginBottom: 40,
    paddingVertical: 30,
  },
  cosmicOrb: {
    width: 100,
    height: 100,
    borderRadius: 50,
    marginBottom: 24,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.6,
    shadowRadius: 20,
    elevation: 10,
  },
  orbGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 50,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  orbIcon: {
    fontSize: 48,
  },
  greetingTitle: {
    fontSize: 32,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 16,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  birthInfoCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  birthInfoText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    marginVertical: 2,
  },
  greetingSubtext: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    lineHeight: 24,
    paddingHorizontal: 20,
  },
  optionsContainer: {
    marginBottom: 30,
  },
  optionsTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 24,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  optionCard: {
    marginBottom: 16,
    borderRadius: 20,
    overflow: 'hidden',
  },
  optionGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  optionIconContainer: {
    marginRight: 16,
  },
  optionIconGradient: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  optionEmoji: {
    fontSize: 28,
  },
  optionContent: {
    flex: 1,
  },
  optionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 6,
  },
  optionDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: 20,
  },
  quickQuestionsContainer: {
    alignItems: 'center',
    paddingVertical: 20,
    paddingHorizontal: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  quickQuestionsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    textAlign: 'center',
    marginBottom: 8,
    textShadowColor: 'rgba(255, 255, 255, 0.8)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  quickQuestionsSubtext: {
    fontSize: 14,
    color: '#2d2d2d',
    textAlign: 'center',
    lineHeight: 20,
    textShadowColor: 'rgba(255, 255, 255, 0.6)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 1,
  },
  analysisContainer: {
    marginBottom: 30,
  },
  analysisTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 24,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  analysisCard: {
    marginBottom: 16,
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  analysisGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
  },
  analysisIconContainer: {
    marginRight: 16,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.4)',
  },
  analysisEmoji: {
    fontSize: 28,
  },
  analysisContent: {
    flex: 1,
  },
  analysisCardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 6,
  },
  analysisDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    lineHeight: 20,
    marginBottom: 6,
  },
  analysisCost: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '600',
  },
});