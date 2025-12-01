import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  Platform,
  KeyboardAvoidingView,
  Animated,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import DateTimePicker from '@react-native-community/datetimepicker';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { storage } from '../../services/storage';
import { chartAPI } from '../../services/api';
import { COLORS } from '../../utils/constants';

const { width } = Dimensions.get('window');

export default function BirthFormScreen({ navigation, route }) {
  const editProfile = route?.params?.editProfile;
  const prefillData = route?.params?.prefillData;
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: editProfile?.name || prefillData?.name || '',
    date: editProfile?.date ? new Date(editProfile.date) : new Date(),
    time: editProfile?.time ? new Date(`2000-01-01T${editProfile.time}`) : new Date(),
    place: editProfile?.place || '',
    latitude: editProfile?.latitude || null,
    longitude: editProfile?.longitude || null,
    timezone: editProfile?.timezone || 'Asia/Kolkata',
    gender: editProfile?.gender?.trim() || '',
  });
  
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchTimeout, setSearchTimeout] = useState(null);
  const [showConfetti, setShowConfetti] = useState(false);
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;
  const shakeAnim = useRef(new Animated.Value(0)).current;
  const confettiAnims = useRef([...Array(20)].map(() => ({
    x: new Animated.Value(0),
    y: new Animated.Value(0),
    rotate: new Animated.Value(0),
    opacity: new Animated.Value(0),
  }))).current;

  useEffect(() => {
    animateStepTransition();
  }, [step]);

  const animateStepTransition = () => {
    fadeAnim.setValue(0);
    slideAnim.setValue(50);
    scaleAnim.setValue(0.9);
    
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
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
      Animated.timing(progressAnim, {
        toValue: step / 5,
        duration: 400,
        useNativeDriver: false,
      }),
    ]).start();
  };

  const shakeAnimation = () => {
    Animated.sequence([
      Animated.timing(shakeAnim, { toValue: 10, duration: 50, useNativeDriver: true }),
      Animated.timing(shakeAnim, { toValue: -10, duration: 50, useNativeDriver: true }),
      Animated.timing(shakeAnim, { toValue: 10, duration: 50, useNativeDriver: true }),
      Animated.timing(shakeAnim, { toValue: 0, duration: 50, useNativeDriver: true }),
    ]).start();
  };

  const triggerConfetti = () => {
    setShowConfetti(true);
    confettiAnims.forEach((anim, index) => {
      const startX = Math.random() * width;
      const endX = startX + (Math.random() - 0.5) * 200;
      const endY = 800;
      
      Animated.parallel([
        Animated.timing(anim.x, {
          toValue: endX,
          duration: 2000 + Math.random() * 1000,
          useNativeDriver: true,
        }),
        Animated.timing(anim.y, {
          toValue: endY,
          duration: 2000 + Math.random() * 1000,
          useNativeDriver: true,
        }),
        Animated.timing(anim.rotate, {
          toValue: Math.random() * 720,
          duration: 2000 + Math.random() * 1000,
          useNativeDriver: true,
        }),
        Animated.sequence([
          Animated.timing(anim.opacity, {
            toValue: 1,
            duration: 200,
            useNativeDriver: true,
          }),
          Animated.delay(1500),
          Animated.timing(anim.opacity, {
            toValue: 0,
            duration: 500,
            useNativeDriver: true,
          }),
        ]),
      ]).start();
      
      anim.x.setValue(startX);
      anim.y.setValue(-50);
      anim.rotate.setValue(0);
      anim.opacity.setValue(0);
    });
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    if (field === 'place') {
      setFormData(prev => ({ ...prev, [field]: value, latitude: null, longitude: null }));
      if (searchTimeout) clearTimeout(searchTimeout);
      const timeout = setTimeout(() => {
        if (value.length >= 3) searchPlaces(value);
        else { setSuggestions([]); setShowSuggestions(false); }
      }, 300);
      setSearchTimeout(timeout);
    }
  };

  const searchPlaces = async (query) => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`,
        { headers: { 'User-Agent': 'AstrologyApp/1.0' } }
      );
      const data = await response.json();
      const places = data.map(item => ({
        id: item.place_id,
        name: item.display_name,
        latitude: parseFloat(item.lat),
        longitude: parseFloat(item.lon),
        timezone: 'Asia/Kolkata'
      }));
      setSuggestions(places);
      setShowSuggestions(true);
    } catch (error) {}
  };

  const handlePlaceSelect = (place) => {
    setFormData(prev => ({
      ...prev,
      place: place.name,
      latitude: place.latitude,
      longitude: place.longitude,
      timezone: place.timezone
    }));
    setShowSuggestions(false);
    setSuggestions([]);
  };

  const validateStep = () => {
    if (step === 1 && !formData.name.trim()) {
      shakeAnimation();
      return false;
    }
    if (step === 2 && !formData.gender) {
      shakeAnimation();
      return false;
    }
    if (step === 5) {
      if (!formData.place.trim()) {
        shakeAnimation();
        return false;
      }
      if (!formData.latitude || !formData.longitude) {
        Alert.alert('Invalid Location', 'Please select a location from the suggestions to ensure accurate calculations.');
        shakeAnimation();
        return false;
      }
    }
    return true;
  };

  const nextStep = () => {
    if (validateStep()) {
      if (step < 5) setStep(step + 1);
      else handleSubmit();
    }
  };

  const prevStep = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleSubmit = async () => {
    // Final validation before submission
    if (!formData.latitude || !formData.longitude) {
      Alert.alert('Invalid Location', 'Please select a location from the suggestions.');
      setLoading(false);
      return;
    }
    
    setLoading(true);
    try {
      const birthData = {
        name: formData.name,
        date: formData.date.toISOString().split('T')[0],
        time: formData.time.toTimeString().split(' ')[0],
        place: formData.place,
        latitude: formData.latitude,
        longitude: formData.longitude,
        timezone: formData.timezone,
        gender: formData.gender,
      };

      const [chartData, yogiData] = await Promise.all([
        chartAPI.calculateChart(birthData),
        chartAPI.calculateYogi(birthData)
      ]);

      const profileData = {
        ...formData,
        time: formData.time.toTimeString().split(' ')[0]
      };
      
      await storage.setBirthDetails(profileData);
      await storage.addBirthProfile(profileData);
      
      await storage.setChartData({
        birthData: birthData,
        chartData: chartData
      });

      triggerConfetti();
      setTimeout(() => {
        Alert.alert('Success', 'Birth chart calculated successfully!', [
          { text: 'OK', onPress: () => navigation.navigate('Chat') }
        ]);
      }, 1000);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.message || 'Failed to process birth details');
    } finally {
      setLoading(false);
    }
  };

  const getStepIcon = () => {
    const icons = ['👤', '⚧️', '📅', '🕐', '📍'];
    return icons[step - 1];
  };

  const getStepTitle = () => {
    const titles = ['What\'s your name?', 'Select your gender', 'When were you born?', 'What time were you born?', 'Where were you born?'];
    return titles[step - 1];
  };

  const progressWidth = progressAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0%', '100%'],
  });

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']} style={styles.gradient}>
        <SafeAreaView style={styles.safeArea}>
          <KeyboardAvoidingView style={styles.keyboardAvoid} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            
            {/* Header */}
            <View style={styles.header}>
              <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                <Ionicons name="arrow-back" size={24} color={COLORS.white} />
              </TouchableOpacity>
              <View style={styles.headerTitleContainer}>
                <Ionicons name="person" size={20} color="#ff6b35" />
                <Text style={styles.headerTitle}>{editProfile ? 'Edit Profile' : 'Birth Details'}</Text>
              </View>
              <View style={styles.placeholder} />
            </View>

            {/* Progress Bar */}
            <View style={styles.progressContainer}>
              <View style={styles.progressBar}>
                <Animated.View style={[styles.progressFill, { width: progressWidth }]}>
                  <LinearGradient colors={['#ff6b35', '#ffd700']} style={styles.progressGradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} />
                </Animated.View>
              </View>
              <Text style={styles.progressText}>Step {step} of 5</Text>
            </View>

            <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
              <Animated.View style={[styles.stepContainer, { opacity: fadeAnim, transform: [{ translateY: slideAnim }, { scale: scaleAnim }, { translateX: shakeAnim }] }]}>
                
                {/* Step Icon */}
                <View style={styles.iconContainer}>
                  <LinearGradient colors={['#ff6b35', '#ffd700', '#ff6b35']} style={styles.iconGradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
                    <Text style={styles.stepIcon}>{getStepIcon()}</Text>
                  </LinearGradient>
                </View>

                {/* Step Title */}
                <Text style={styles.stepTitle}>{getStepTitle()}</Text>

                {/* Step Content */}
                {step === 1 && (
                  <View style={styles.inputContainer}>
                    <TextInput
                      style={styles.input}
                      value={formData.name}
                      onChangeText={(value) => handleInputChange('name', value)}
                      placeholder="Enter your full name"
                      placeholderTextColor="rgba(255, 255, 255, 0.5)"
                      autoFocus
                    />
                  </View>
                )}

                {step === 2 && (
                  <View style={styles.genderContainer}>
                    <TouchableOpacity
                      style={[styles.genderCard, formData.gender === 'Male' && styles.genderCardSelected]}
                      onPress={() => handleInputChange('gender', 'Male')}
                    >
                      <LinearGradient
                        colors={formData.gender === 'Male' ? ['#ff6b35', '#ff8c5a'] : ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                        style={styles.genderGradient}
                      >
                        <Text style={styles.genderIcon}>♂️</Text>
                        <Text style={styles.genderText}>Male</Text>
                      </LinearGradient>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.genderCard, formData.gender === 'Female' && styles.genderCardSelected]}
                      onPress={() => handleInputChange('gender', 'Female')}
                    >
                      <LinearGradient
                        colors={formData.gender === 'Female' ? ['#ff6b35', '#ff8c5a'] : ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                        style={styles.genderGradient}
                      >
                        <Text style={styles.genderIcon}>♀️</Text>
                        <Text style={styles.genderText}>Female</Text>
                      </LinearGradient>
                    </TouchableOpacity>
                  </View>
                )}

                {step === 3 && (
                  <View style={styles.dateTimeContainer}>
                    <TouchableOpacity style={styles.dateTimeCard} onPress={() => setShowDatePicker(true)}>
                      <LinearGradient colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']} style={styles.dateTimeGradient}>
                        <Text style={styles.dateTimeIcon}>📅</Text>
                        <Text style={styles.dateTimeValue}>
                          {formData.date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                        </Text>
                      </LinearGradient>
                    </TouchableOpacity>
                    <View style={styles.zodiacWheel}>
                      <Text style={styles.zodiacText}>♈♉♊♋♌♍</Text>
                      <Text style={styles.zodiacText}>♎♏♐♑♒♓</Text>
                    </View>
                  </View>
                )}

                {step === 4 && (
                  <View style={styles.dateTimeContainer}>
                    <TouchableOpacity style={styles.dateTimeCard} onPress={() => setShowTimePicker(true)}>
                      <LinearGradient colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']} style={styles.dateTimeGradient}>
                        <Text style={styles.dateTimeIcon}>🕐</Text>
                        <Text style={styles.dateTimeValue}>
                          {formData.time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}
                        </Text>
                      </LinearGradient>
                    </TouchableOpacity>
                  </View>
                )}

                {step === 5 && (
                  <View style={styles.inputContainer}>
                    <View style={styles.locationInputWrapper}>
                      <TextInput
                        style={styles.input}
                        value={formData.place}
                        onChangeText={(value) => handleInputChange('place', value)}
                        placeholder="City, State, Country"
                        placeholderTextColor="rgba(255, 255, 255, 0.5)"
                      />
                      {showSuggestions && suggestions.length > 0 && (
                        <View style={styles.suggestionsList}>
                          {suggestions.slice(0, 3).map(suggestion => (
                            <TouchableOpacity
                              key={suggestion.id}
                              style={styles.suggestionItem}
                              onPress={() => handlePlaceSelect(suggestion)}
                            >
                              <Text style={styles.suggestionText} numberOfLines={1}>📍 {suggestion.name}</Text>
                            </TouchableOpacity>
                          ))}
                        </View>
                      )}
                    </View>
                  </View>
                )}

              </Animated.View>
            </ScrollView>

            {/* Navigation Buttons */}
            <View style={styles.navigationContainer}>
              {step > 1 && (
                <TouchableOpacity style={styles.navButton} onPress={prevStep}>
                  <LinearGradient colors={['rgba(255, 255, 255, 0.2)', 'rgba(255, 255, 255, 0.1)']} style={styles.navGradient}>
                    <Ionicons name="arrow-back" size={20} color={COLORS.white} />
                    <Text style={styles.navText}>Back</Text>
                  </LinearGradient>
                </TouchableOpacity>
              )}
              <TouchableOpacity style={[styles.navButton, styles.navButtonPrimary, step === 1 && styles.navButtonFull]} onPress={nextStep} disabled={loading}>
                <LinearGradient colors={['#ff6b35', '#ff8c5a']} style={styles.navGradient}>
                  <Text style={styles.navTextPrimary}>{loading ? 'Processing...' : step === 5 ? 'Complete' : 'Next'}</Text>
                  {step < 5 && <Ionicons name="arrow-forward" size={20} color={COLORS.white} />}
                </LinearGradient>
              </TouchableOpacity>
            </View>

            {/* Date Picker */}
            {showDatePicker && Platform.OS !== 'web' && (
              <DateTimePicker
                value={formData.date}
                mode="date"
                display="default"
                onChange={(event, selectedDate) => {
                  setShowDatePicker(false);
                  if (selectedDate) handleInputChange('date', selectedDate);
                }}
                maximumDate={new Date()}
              />
            )}

            {/* Time Picker */}
            {showTimePicker && Platform.OS !== 'web' && (
              <DateTimePicker
                value={formData.time}
                mode="time"
                display="default"
                onChange={(event, selectedTime) => {
                  setShowTimePicker(false);
                  if (selectedTime) handleInputChange('time', selectedTime);
                }}
              />
            )}

            {/* Confetti */}
            {showConfetti && confettiAnims.map((anim, index) => (
              <Animated.View
                key={index}
                style={[
                  styles.confetti,
                  {
                    transform: [
                      { translateX: anim.x },
                      { translateY: anim.y },
                      { rotate: anim.rotate.interpolate({ inputRange: [0, 360], outputRange: ['0deg', '360deg'] }) }
                    ],
                    opacity: anim.opacity,
                  },
                ]}
              >
                <Text style={styles.confettiText}>{['🎉', '✨', '⭐', '🌟', '💫'][index % 5]}</Text>
              </Animated.View>
            ))}

          </KeyboardAvoidingView>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  keyboardAvoid: { flex: 1 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
  },
  placeholder: { width: 40 },
  progressContainer: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  progressBar: {
    height: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  progressGradient: {
    flex: 1,
  },
  progressText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
  },
  scrollView: { flex: 1 },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  stepContainer: {
    alignItems: 'center',
  },
  iconContainer: {
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
  iconGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  stepIcon: {
    fontSize: 48,
  },
  stepTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 40,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  inputContainer: {
    width: '100%',
  },
  locationInputWrapper: {
    position: 'relative',
    zIndex: 1000,
  },
  input: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 16,
    padding: 18,
    fontSize: 18,
    color: COLORS.white,
    textAlign: 'center',
  },
  genderContainer: {
    flexDirection: 'row',
    gap: 16,
    width: '100%',
  },
  genderCard: {
    flex: 1,
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  genderCardSelected: {
    shadowColor: '#ff6b35',
    shadowOpacity: 0.6,
  },
  genderGradient: {
    padding: 24,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 20,
  },
  genderIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  genderText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.white,
  },
  dateTimeContainer: {
    width: '100%',
    alignItems: 'center',
  },
  dateTimeCard: {
    width: '100%',
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
    marginBottom: 24,
  },
  dateTimeGradient: {
    padding: 24,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 20,
  },
  dateTimeIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  dateTimeValue: {
    fontSize: 20,
    fontWeight: '600',
    color: COLORS.white,
  },
  zodiacWheel: {
    alignItems: 'center',
  },
  zodiacText: {
    fontSize: 32,
    color: 'rgba(255, 255, 255, 0.4)',
    letterSpacing: 8,
    marginVertical: 4,
  },
  suggestionsList: {
    position: 'absolute',
    bottom: '100%',
    left: 0,
    right: 0,
    backgroundColor: 'rgba(30, 30, 30, 0.95)',
    borderRadius: 12,
    marginBottom: 8,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    zIndex: 1001,
    maxHeight: 200,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 10,
  },
  suggestionItem: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  suggestionText: {
    fontSize: 14,
    color: COLORS.white,
  },
  navigationContainer: {
    flexDirection: 'row',
    gap: 12,
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  navButton: {
    flex: 1,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  navButtonFull: {
    flex: 1,
  },
  navButtonPrimary: {
    shadowColor: '#ff6b35',
    shadowOpacity: 0.6,
  },
  navGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    gap: 8,
  },
  navText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
  },
  navTextPrimary: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
  },
  confetti: {
    position: 'absolute',
    top: 0,
  },
  confettiText: {
    fontSize: 24,
  },
});
