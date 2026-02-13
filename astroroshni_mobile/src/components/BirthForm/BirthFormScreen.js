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
  Modal,
  Keyboard,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import DateTimePicker from '@react-native-community/datetimepicker';
import { Picker } from '@react-native-picker/picker';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTranslation } from 'react-i18next';
import { storage } from '../../services/storage';
import { chartAPI, authAPI } from '../../services/api';
import { COLORS, API_BASE_URL } from '../../utils/constants';
import locationCache from '../../services/locationCache';
import { useTheme } from '../../context/ThemeContext';
import { useAnalytics } from '../../hooks/useAnalytics';

const { width } = Dimensions.get('window');

export default function BirthFormScreen({ navigation, route }) {
  useAnalytics('BirthFormScreen');
  const { t } = useTranslation();
  const { theme, colors, getCardElevation } = useTheme();
  const editProfile = route?.params?.editProfile;
  const prefillData = route?.params?.prefillData;
  const updateGender = route?.params?.updateGender;
  const [step, setStep] = useState(updateGender ? 2 : 1); // Start at gender step if updating gender
  const getTimeDate = (timeString) => {
    if (!timeString) return new Date();
    const [hours, minutes] = timeString.split(':');
    const date = new Date();
    date.setHours(parseInt(hours), parseInt(minutes), 0, 0);
    return date;
  };

  const [formData, setFormData] = useState({
    name: editProfile?.name || prefillData?.name || '',
    date: editProfile?.date ? new Date(editProfile.date) : new Date(),
    time: editProfile?.time ? getTimeDate(editProfile.time) : new Date(),
    place: editProfile?.place || '',
    latitude: editProfile?.latitude || null,
    longitude: editProfile?.longitude || null,
    gender: editProfile?.gender?.trim() || '',
  });
  
  // Log edit mode for debugging
  useEffect(() => {
    if (editProfile) {
      console.log('📝 Edit mode activated with profile:', editProfile.name);
    }
  }, []);
  
  const getPickerDate = () => {
    const d = new Date();
    d.setHours(formData.time.getHours(), formData.time.getMinutes(), 0, 0);
    return d;
  };
  const [loadingExistingData, setLoadingExistingData] = useState(updateGender);
  
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [tempTime, setTempTime] = useState(null);
  const [tempHour, setTempHour] = useState(12);
  const [tempMinute, setTempMinute] = useState(0);
  const [tempPeriod, setTempPeriod] = useState('AM');
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
  const stableDateRef = useRef(null);
  const confettiAnims = useRef([...Array(20)].map(() => ({
    x: new Animated.Value(0),
    y: new Animated.Value(0),
    rotate: new Animated.Value(0),
    opacity: new Animated.Value(0),
  }))).current;

  useEffect(() => {
    if (updateGender && step === 2 && !formData.gender) {
      loadExistingBirthData();
    }
    animateStepTransition();
  }, [step]);
  
  const loadExistingBirthData = async () => {
    try {
      // console.log('🔄 [DEBUG] BirthForm: Loading existing birth data for gender update...');
      const existingData = await storage.getBirthDetails();
      // console.log('📂 [DEBUG] BirthForm: Existing data loaded:', JSON.stringify(existingData, null, 2));
      
      if (existingData) {
        // Only load data if user hasn't made a selection yet
        setFormData(prev => ({
          name: existingData.name || prev.name,
          date: existingData.date ? new Date(existingData.date) : prev.date,
          time: existingData.time ? getTimeDate(existingData.time) : prev.time,
          place: existingData.place || prev.place,
          latitude: existingData.latitude || prev.latitude,
          longitude: existingData.longitude || prev.longitude,
          gender: prev.gender || '', // Keep existing selection, don't overwrite
        }));
        // console.log('✅ [DEBUG] BirthForm: Data loaded without overwriting gender selection');
      }
    } catch (error) {
      console.error('❌ [DEBUG] BirthForm: Failed to load existing birth data:', error);
    } finally {
      setLoadingExistingData(false);
    }
  };

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
    if (field === 'time') {
      console.log('⏰ Time change:', value, 'Hours:', value.getHours(), 'Minutes:', value.getMinutes());
    }
    setFormData(prev => {
      const newData = { ...prev, [field]: value };
      return newData;
    });
    
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

  // Geocoding service configuration - change 'photon' to 'nominatim' to switch back
  const GEOCODING_SERVICE = 'photon'; // Options: 'photon' or 'nominatim'

  const formatPlaceName = (item, service = GEOCODING_SERVICE) => {
    if (service === 'photon') {
      // Photon format
      const properties = item.properties || {};
      const parts = [];
      
      const city = properties.city || properties.name;
      const state = properties.state;
      const country = properties.country;
      
      if (city) parts.push(city);
      if (state && state !== city) parts.push(state);
      if (country) parts.push(country);
      
      return parts.length > 0 ? parts.join(', ') : properties.name || 'Unknown';
    } else {
      // Nominatim format
      const addressParts = item.address || {};
      const parts = [];
      
      const mainPlace = addressParts.city || addressParts.town || addressParts.village || 
                        addressParts.municipality || addressParts.county || addressParts.state_district;
      const state = addressParts.state || addressParts.region;
      const country = addressParts.country;
      
      if (mainPlace) {
        parts.push(mainPlace);
        if (state && state !== mainPlace && !mainPlace.includes(state)) {
          parts.push(state);
        }
      } else if (state) {
        parts.push(state);
      }
      
      if (country) parts.push(country);
      
      return parts.length > 0 ? parts.join(', ') : item.display_name.split(',').slice(0, 3).join(',');
    }
  };

  const searchPlaces = async (query) => {
    try {
      // Use hybrid cache strategy
      const results = await locationCache.searchLocations(query, async (q) => {
        // Photon API fallback
        const url = `https://photon.komoot.io/api/?q=${encodeURIComponent(q)}&limit=10`;
        const response = await fetch(url);
        const json = await response.json();
        const data = json.features || [];
        
        const timestamp = Date.now();
        return data.map((item, index) => {
          const coords = item.geometry?.coordinates || [0, 0];
          const properties = item.properties || {};
          const parts = [];
          
          const city = properties.city || properties.name;
          const state = properties.state;
          const country = properties.country;
          
          if (city) parts.push(city);
          if (state && state !== city) parts.push(state);
          if (country) parts.push(country);
          
          const name = parts.length > 0 ? parts.join(', ') : properties.name || 'Unknown';
          
          return {
            id: `photon_${timestamp}_${index}`,
            name,
            latitude: coords[1],
            longitude: coords[0]
          };
        });
      });
      
      // Remove duplicates
      const uniquePlaces = results.filter((place, index, self) =>
        index === self.findIndex(p => p.name === place.name)
      );
      
      setSuggestions(uniquePlaces.slice(0, 5));
      setShowSuggestions(true);
    } catch (error) {
      console.error('Location search error:', error);
    }
  };



  const handlePlaceSelect = (place) => {
    setShowSuggestions(false);
    setSuggestions([]);
    setFormData(prev => ({
      ...prev,
      place: place.name,
      latitude: place.latitude,
      longitude: place.longitude
    }));
    setTimeout(() => Keyboard.dismiss(), 100);
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
        Alert.alert(t('birthForm.alerts.invalidLocation.title', 'Invalid Location'), t('birthForm.alerts.invalidLocation.suggestions', 'Please select a location from the suggestions to ensure accurate calculations.'));
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
      Alert.alert(t('birthForm.alerts.invalidLocation.title', 'Invalid Location'), t('birthForm.alerts.invalidLocation.noSelection', 'Please select a location from the suggestions.'));
      setLoading(false);
      return;
    }
    
    setLoading(true);
    try {
      // console.log('🚀 [DEBUG] BirthForm: Starting handleSubmit');
      console.log('📝 [DEBUG] BirthForm: Form data:', JSON.stringify({
        name: formData.name,
        updateGender,
        editProfile
      }, null, 2));
      
      // Check existing profiles BEFORE any changes
      const existingProfiles = await storage.getBirthProfiles();
      // console.log('📋 [DEBUG] BirthForm: BEFORE - Existing profiles count:', existingProfiles.length);
      // console.log('📋 [DEBUG] BirthForm: BEFORE - Existing profiles:', existingProfiles.map(p => ({ name: p.name, id: p.id })));
      
      const birthData = {
        name: formData.name,
        date: `${formData.date.getFullYear()}-${String(formData.date.getMonth() + 1).padStart(2, '0')}-${String(formData.date.getDate()).padStart(2, '0')}`,
        time: formData.time.toTimeString().split(' ')[0],
        place: formData.place,
        latitude: formData.latitude,
        longitude: formData.longitude,
        gender: formData.gender,
        relation: editProfile?.relation || 'other',
      };
      
      // DEBUG: Log the exact relation value being sent
      // console.log('🔍 [BIRTH_FORM_DEBUG] Birth data being sent to API:');
      // console.log('🔍 [BIRTH_FORM_DEBUG] - Name:', birthData.name);
      // console.log('🔍 [BIRTH_FORM_DEBUG] - editProfile:', editProfile);
      // console.log('🔍 [BIRTH_FORM_DEBUG] - editProfile?.relation:', editProfile?.relation);
      // console.log('🔍 [BIRTH_FORM_DEBUG] - Final relation value:', birthData.relation);

      // 1. Calculate chart and handle save/update
      let chartData, birthChartId;
      
      if (editProfile?.id) {
        // EDIT MODE: Calculate chart only (no DB save) and update existing record
        console.log('✏️ Edit mode: Updating existing chart ID:', editProfile.id);
        chartData = await chartAPI.calculateChartOnly(birthData);
        await chartAPI.updateChart(editProfile.id, birthData);
        birthChartId = editProfile.id;
      } else {
        // CREATE MODE: Calculate and save new chart
        console.log('➕ Create mode: Saving new chart');
        chartData = await chartAPI.calculateChart(birthData);
        console.log('📦 Received chartData:', JSON.stringify({
          has_birth_chart_id: !!chartData.birth_chart_id,
          birth_chart_id: chartData.birth_chart_id,
          data_keys: Object.keys(chartData.data || chartData)
        }));
        
        // Check if response is wrapped in data property
        const actualData = chartData.data || chartData;
        birthChartId = actualData.birth_chart_id;
        
        if (!birthChartId) {
          console.error('❌ No birth_chart_id returned from API. Full response:', JSON.stringify(chartData, null, 2));
          throw new Error('Failed to get birth chart ID from server');
        }
        
        console.log('✅ Got birth_chart_id:', birthChartId);
      }
      
      const yogiData = await chartAPI.calculateYogi(birthData);

      // 3. Create profile data with REAL ID from database
      const profileData = {
        ...formData,
        time: formData.time.toTimeString().split(' ')[0],
        id: birthChartId
      };
      
      // 4. THEN save to local storage with real ID
      await storage.setBirthDetails(profileData);
      if (!updateGender && !editProfile) {
        // console.log('📝 [DEBUG] BirthForm: Adding to profiles list (new profile)...');
        await storage.addBirthProfile(profileData);
        // console.log('✅ [DEBUG] BirthForm: addBirthProfile completed');
        
        // Check profiles AFTER adding
        const updatedProfiles = await storage.getBirthProfiles();
        // console.log('📋 [DEBUG] BirthForm: AFTER - Updated profiles count:', updatedProfiles.length);
        // console.log('📋 [DEBUG] BirthForm: AFTER - Updated profiles:', updatedProfiles.map(p => ({ name: p.name, id: p.id })));
      } else {
        console.log('⏭️ [DEBUG] BirthForm: Skipping addBirthProfile (update/edit mode)');
      }
      
      // 5. Save chart data
      await storage.setChartData({
        birthData: birthData,
        chartData: chartData
      });

      triggerConfetti();
      setTimeout(() => {
        const successMessage = updateGender ? t('birthForm.alerts.success.genderUpdated', 'Gender updated successfully!') : editProfile ? t('birthForm.alerts.success.profileUpdated', 'Profile updated successfully!') : t('birthForm.alerts.success.chartCalculated', 'Birth chart calculated successfully!');
        Alert.alert(t('birthForm.alerts.success.title', 'Success'), successMessage, [
          { text: t('birthForm.alerts.ok', 'OK'), onPress: () => {
            if (editProfile) {
              navigation.navigate('SelectNative');
            } else {
              navigation.replace('Home');
            }
          }}
        ]);
      }, 1000);
    } catch (error) {
      Alert.alert(t('birthForm.alerts.error.title', 'Error'), error.response?.data?.message || t('birthForm.alerts.error.default', 'Failed to process birth details'));
    } finally {
      setLoading(false);
    }
  };

  const getStepIcon = () => {
    const icons = ['👤', '⚧️', '📅', '🕐', '📍'];
    return icons[step - 1];
  };

  const getStepTitle = () => {
    const titles = [t('birthForm.stepTitle.name', 'What\'s your name?'), t('birthForm.stepTitle.gender', 'Select your gender'), t('birthForm.stepTitle.date', 'When were you born?'), t('birthForm.stepTitle.time', 'What time were you born?'), t('birthForm.stepTitle.place', 'Where were you born?')];
    return titles[step - 1];
  };

  const progressWidth = progressAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0%', '100%'],
  });

  return (
    <View style={styles.container}>
      <LinearGradient colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.primary] : [colors.gradientStart, colors.gradientStart, colors.gradientStart, colors.gradientStart]} style={styles.gradient}>
        <SafeAreaView style={styles.safeArea}>
          <KeyboardAvoidingView style={styles.keyboardAvoid} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            
            {/* Header */}
            <View style={styles.header}>
              <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                <Ionicons name="arrow-back" size={24} color={colors.text} />
              </TouchableOpacity>
              <View style={styles.headerTitleContainer}>
                <Ionicons name="person" size={20} color="#ff6b35" />
                <Text style={[styles.headerTitle, { color: colors.text }]}>{updateGender ? t('birthForm.headerTitle.updateGender', 'Update Gender') : editProfile ? t('birthForm.headerTitle.editProfile', 'Edit Profile') : t('birthForm.headerTitle.birthDetails', 'Birth Details')}</Text>
              </View>
              <View style={styles.placeholder} />
            </View>

            {/* Progress Bar */}
            <View style={styles.progressContainer}>
              <View style={[styles.progressBar, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.15)' }]}>
                <Animated.View style={[styles.progressFill, { width: progressWidth }]}>
                  <LinearGradient colors={['#ff6b35', '#ffd700']} style={styles.progressGradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} />
                </Animated.View>
              </View>
              <Text style={[styles.progressText, { color: colors.textSecondary }]}>{t('birthForm.progressText', 'Step {{step}} of 5', { step })}</Text>
            </View>

            <ScrollView 
              style={styles.scrollView} 
              contentContainerStyle={styles.scrollContent} 
              showsVerticalScrollIndicator={false}
              keyboardShouldPersistTaps="always"
            >
              <Animated.View style={[styles.stepContainer, { opacity: fadeAnim, transform: [{ translateY: slideAnim }, { scale: scaleAnim }, { translateX: shakeAnim }] }]}>
                
                {/* Step Icon */}
                <View style={[styles.iconContainer, { elevation: getCardElevation(10) }]}>
                  <LinearGradient colors={['#ff6b35', '#ffd700', '#ff6b35']} style={styles.iconGradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
                    <Text style={styles.stepIcon}>{getStepIcon()}</Text>
                  </LinearGradient>
                </View>

                {/* Step Title */}
                <Text style={[styles.stepTitle, { color: colors.text }]}>{getStepTitle()}</Text>

                {/* Step Content */}
                {step === 1 && (
                  <View style={styles.inputContainer}>
                    <TextInput
                      style={[styles.input, { color: colors.text, backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.05)', borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.2)' }]}
                      value={formData.name}
                      onChangeText={(value) => handleInputChange('name', value)}
                      placeholder={t('birthForm.namePlaceholder', 'Enter your full name')}
                      placeholderTextColor={colors.textSecondary}
                      autoFocus
                      autoCorrect={false}
                    />
                  </View>
                )}

                {step === 2 && (
                  <View style={styles.genderContainer}>
                    <TouchableOpacity
                      style={[styles.genderCard, formData.gender === 'Male' && styles.genderCardSelected, { elevation: getCardElevation(8) }]}
                      onPress={() => handleInputChange('gender', 'Male')}
                    >
                      <LinearGradient
                        colors={formData.gender === 'Male' ? ['#ff6b35', '#ff8c5a'] : theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.25)', 'rgba(249, 115, 22, 0.15)']}
                        style={[styles.genderGradient, { borderColor: formData.gender === 'Male' ? 'rgba(255, 107, 53, 0.5)' : theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.3)' }]}
                      >
                        <Text style={styles.genderIcon}>♂️</Text>
                        <Text style={[styles.genderText, { color: colors.text }]}>{t('birthForm.gender.male', 'Male')}</Text>
                        {formData.gender === 'Male' && <Text style={[styles.selectedIndicator, { color: colors.text }]}>✓</Text>}
                      </LinearGradient>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.genderCard, formData.gender === 'Female' && styles.genderCardSelected, { elevation: getCardElevation(8) }]}
                      onPress={() => handleInputChange('gender', 'Female')}
                    >
                      <LinearGradient
                        colors={formData.gender === 'Female' ? ['#ff6b35', '#ff8c5a'] : theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.25)', 'rgba(249, 115, 22, 0.15)']}
                        style={[styles.genderGradient, { borderColor: formData.gender === 'Female' ? 'rgba(255, 107, 53, 0.5)' : theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.3)' }]}
                      >
                        <Text style={styles.genderIcon}>♀️</Text>
                        <Text style={[styles.genderText, { color: colors.text }]}>{t('birthForm.gender.female', 'Female')}</Text>
                        {formData.gender === 'Female' && <Text style={[styles.selectedIndicator, { color: colors.text }]}>✓</Text>}
                      </LinearGradient>
                    </TouchableOpacity>
                  </View>
                )}

                {step === 3 && (
                  <View style={styles.dateTimeContainer}>
                    <TouchableOpacity style={[styles.dateTimeCard, { elevation: getCardElevation(8) }]} onPress={() => setShowDatePicker(true)}>
                      <LinearGradient colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.25)', 'rgba(249, 115, 22, 0.15)']} style={[styles.dateTimeGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.3)' }]}>
                        <Text style={styles.dateTimeIcon}>📅</Text>
                        <Text style={[styles.dateTimeValue, { color: colors.text }]}>
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
                    <TouchableOpacity style={[styles.dateTimeCard, { elevation: getCardElevation(8) }]} onPress={() => {
                      const hours = formData.time.getHours();
                      const minutes = formData.time.getMinutes();
                      setTempHour(hours % 12 || 12);
                      setTempMinute(minutes);
                      setTempPeriod(hours >= 12 ? 'PM' : 'AM');
                      setShowTimePicker(true);
                    }}>
                      <LinearGradient colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.25)', 'rgba(249, 115, 22, 0.15)']} style={[styles.dateTimeGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.3)' }]}>
                        <Text style={styles.dateTimeIcon}>🕐</Text>
                        <Text style={[styles.dateTimeValue, { color: colors.text }]}>
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
                        style={[styles.input, { color: colors.text, backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.05)', borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.2)' }]}
                        value={formData.place}
                        onChangeText={(value) => handleInputChange('place', value)}
                        placeholder={t('birthForm.placePlaceholder', 'City, State, Country')}
                        placeholderTextColor={colors.textSecondary}
                        autoCorrect={false}
                        onBlur={() => {
                          // Delay hiding suggestions to allow tap to register
                          setTimeout(() => setShowSuggestions(false), 200);
                        }}
                        onFocus={() => {
                          if (suggestions.length > 0) setShowSuggestions(true);
                        }}
                      />
                      {showSuggestions && suggestions.length > 0 && (
                        <ScrollView 
                          style={[styles.suggestionsList, { backgroundColor: theme === 'dark' ? 'rgba(30, 30, 30, 0.95)' : 'rgba(255, 255, 255, 0.98)', borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.2)', elevation: getCardElevation(10) }]}
                          keyboardShouldPersistTaps="always"
                          nestedScrollEnabled={true}
                        >
                          {suggestions.map(suggestion => (
                            <TouchableOpacity
                              key={suggestion.id}
                              style={[styles.suggestionItem, { borderBottomColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)' }]}
                              onPress={() => handlePlaceSelect(suggestion)}
                              activeOpacity={0.7}
                            >
                              <Text style={[styles.suggestionText, { color: colors.text }]}>📍 {suggestion.name}</Text>
                            </TouchableOpacity>
                          ))}
                        </ScrollView>
                      )}
                    </View>
                    {formData.latitude && formData.longitude && (
                      <View style={[styles.locationDetails, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)', borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)' }]}>
                        <Text style={[styles.locationDetailsTitle, { color: colors.text }]}>📍 {t('birthForm.selectedLocation', 'Selected Location')}</Text>
                        <Text style={[styles.locationDetailsText, { color: colors.text }]}>{formData.place}</Text>
                        <View style={[styles.coordinatesRow, { borderTopColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)' }]}>
                          <Text style={[styles.coordinateText, { color: colors.textSecondary }]}>{t('birthForm.coords.lat', 'Lat:')} {formData.latitude.toFixed(4)}</Text>
                          <Text style={[styles.coordinateText, { color: colors.textSecondary }]}>{t('birthForm.coords.long', 'Long:')} {formData.longitude.toFixed(4)}</Text>
                        </View>
                      </View>
                    )}
                  </View>
                )}

              </Animated.View>
            </ScrollView>

            {/* Navigation Buttons */}
            <View style={styles.navigationContainer}>
              {step > 1 && (
                <TouchableOpacity style={[styles.navButton, { elevation: getCardElevation(5) }]} onPress={prevStep}>
                  <LinearGradient colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.2)', 'rgba(255, 255, 255, 0.1)'] : ['rgba(249, 115, 22, 0.25)', 'rgba(249, 115, 22, 0.15)']} style={styles.navGradient}>
                    <Ionicons name="arrow-back" size={20} color={colors.text} />
                    <Text style={[styles.navText, { color: colors.text }]}>{t('birthForm.buttons.back', 'Back')}</Text>
                  </LinearGradient>
                </TouchableOpacity>
              )}
              <TouchableOpacity style={[styles.navButton, styles.navButtonPrimary, step === 1 && styles.navButtonFull, { elevation: getCardElevation(5) }]} onPress={nextStep} disabled={loading}>
                <LinearGradient colors={['#ff6b35', '#ff8c5a']} style={styles.navGradient}>
                  <Text style={styles.navTextPrimary}>{loading ? t('birthForm.buttons.processing', 'Processing...') : step === 5 ? t('birthForm.buttons.complete', 'Complete') : t('birthForm.buttons.next', 'Next')}</Text>
                  {step < 5 && <Ionicons name="arrow-forward" size={20} color={COLORS.white} />}
                </LinearGradient>
              </TouchableOpacity>
            </View>

            {/* Date Picker */}
            {Platform.OS === 'ios' ? (
              <Modal visible={showDatePicker} transparent animationType="slide">
                <View style={styles.modalOverlay}>
                  <View style={styles.pickerContainer}>
                    <LinearGradient colors={[COLORS.white, COLORS.lightGray]} style={styles.pickerGradient}>
                      <View style={styles.pickerHeader}>
                        <TouchableOpacity onPress={() => setShowDatePicker(false)}>
                          <Text style={styles.pickerButton}>{t('birthForm.picker.cancel', 'Cancel')}</Text>
                        </TouchableOpacity>
                        <TouchableOpacity onPress={() => setShowDatePicker(false)}>
                          <Text style={[styles.pickerButton, styles.pickerButtonDone]}>{t('birthForm.picker.done', 'Done')}</Text>
                        </TouchableOpacity>
                      </View>
                      <DateTimePicker
                        value={formData.date}
                        mode="date"
                        display="spinner"
                        onChange={(event, selectedDate) => {
                          if (selectedDate) handleInputChange('date', selectedDate);
                        }}
                        maximumDate={new Date()}
                        style={styles.picker}
                      />
                    </LinearGradient>
                  </View>
                </View>
              </Modal>
            ) : (
              showDatePicker && (
                <DateTimePicker
                  value={formData.date}
                  mode="date"
                  display="default"
                  onChange={(event, selectedDate) => {
                    setShowDatePicker(false);
                    if (selectedDate) handleInputChange('date', selectedDate);
                  }}
                  maximumDate={new Date()}
                  minimumDate={new Date(1900, 0, 1)}
                />
              )
            )}

            {/* Time Picker */}
            {Platform.OS === 'ios' ? (
              <Modal visible={showTimePicker} transparent animationType="slide">
                <View style={styles.modalOverlay}>
                  <View style={styles.pickerContainer}>
                    <LinearGradient colors={[COLORS.white, COLORS.lightGray]} style={styles.pickerGradient}>
                      <View style={styles.pickerHeader}>
                        <TouchableOpacity onPress={() => setShowTimePicker(false)}>
                          <Text style={styles.pickerButton}>{t('birthForm.picker.cancel', 'Cancel')}</Text>
                        </TouchableOpacity>
                        <TouchableOpacity onPress={() => {
                          const hours = tempPeriod === 'PM' ? (tempHour === 12 ? 12 : tempHour + 12) : (tempHour === 12 ? 0 : tempHour);
                          const newTime = new Date();
                          newTime.setHours(hours, tempMinute, 0, 0);
                          handleInputChange('time', newTime);
                          setShowTimePicker(false);
                        }}>
                          <Text style={[styles.pickerButton, styles.pickerButtonDone]}>{t('birthForm.picker.done', 'Done')}</Text>
                        </TouchableOpacity>
                      </View>
                      <View style={styles.customPickerRow}>
                        <Picker
                          selectedValue={tempHour}
                          onValueChange={setTempHour}
                          style={styles.customPicker}
                          itemStyle={styles.pickerItem}
                        >
                          {[...Array(12)].map((_, i) => (
                            <Picker.Item key={i + 1} label={String(i + 1)} value={i + 1} />
                          ))}
                        </Picker>
                        <Picker
                          selectedValue={tempMinute}
                          onValueChange={setTempMinute}
                          style={styles.customPicker}
                          itemStyle={styles.pickerItem}
                        >
                          {[...Array(60)].map((_, i) => (
                            <Picker.Item key={i} label={String(i).padStart(2, '0')} value={i} />
                          ))}
                        </Picker>
                        <Picker
                          selectedValue={tempPeriod}
                          onValueChange={setTempPeriod}
                          style={styles.customPicker}
                          itemStyle={styles.pickerItem}
                        >
                          <Picker.Item label="AM" value="AM" />
                          <Picker.Item label="PM" value="PM" />
                        </Picker>
                      </View>
                    </LinearGradient>
                  </View>
                </View>
              </Modal>
            ) : (
              showTimePicker && (
                <DateTimePicker
                  value={formData.time}
                  mode="time"
                  display="default"
                  onChange={(event, selectedTime) => {
                    setShowTimePicker(false);
                    if (selectedTime) handleInputChange('time', selectedTime);
                  }}
                />
              )
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
  },
  placeholder: { width: 40 },
  progressContainer: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  progressBar: {
    height: 6,
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
    ...Platform.select({
      ios: {
        shadowColor: '#ff6b35',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.6,
        shadowRadius: 20,
      },
    }),
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
    borderWidth: 2,
    borderRadius: 16,
    padding: 18,
    fontSize: 18,
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
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.3,
        shadowRadius: 12,
      },
    }),
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
  },
  genderDebugText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    marginBottom: 16,
  },
  selectedIndicator: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 8,
  },
  dateTimeContainer: {
    width: '100%',
    alignItems: 'center',
  },
  dateTimeCard: {
    width: '100%',
    borderRadius: 20,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.3,
        shadowRadius: 12,
      },
    }),
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
    borderRadius: 12,
    marginBottom: 8,
    overflow: 'hidden',
    borderWidth: 1,
    zIndex: 1001,
    maxHeight: 200,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
      },
    }),
  },
  suggestionItem: {
    padding: 16,
    borderBottomWidth: 1,
  },
  suggestionText: {
    fontSize: 14,
  },
  locationDetails: {
    marginTop: 24,
    borderRadius: 16,
    padding: 20,
    borderWidth: 2,
  },
  locationDetailsTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
    textAlign: 'center',
  },
  locationDetailsText: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 12,
  },
  coordinatesRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 12,
    borderTopWidth: 1,
  },
  coordinateText: {
    fontSize: 12,
    fontWeight: '600',
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
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
      },
    }),
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'flex-end',
  },
  pickerContainer: {
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    overflow: 'hidden',
  },
  pickerGradient: {
    paddingBottom: 20,
  },
  pickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 0, 0, 0.1)',
  },
  pickerButton: {
    fontSize: 16,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  pickerButtonDone: {
    color: '#ff6b35',
    fontWeight: '700',
  },
  picker: {
    height: 200,
  },
  customPickerRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  customPicker: {
    flex: 1,
    height: 200,
  },
  pickerItem: {
    fontSize: 20,
    height: 200,
  },
});
