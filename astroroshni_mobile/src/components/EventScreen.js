import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
  FlatList,
  Alert,
  Modal
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useNavigation } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { chatAPI, creditAPI } from '../services/api';
import { storage } from '../services/storage';
import { useCredits } from '../credits/CreditContext';
import MonthlyAccordion from './MonthlyAccordion';
import NativeSelectorChip from './Common/NativeSelectorChip';
import { API_BASE_URL } from '../utils/constants';
import { useTheme } from '../context/ThemeContext';

const { width } = Dimensions.get('window');

// Layout constants for FlatList
const START_YEAR = 1950;
const ITEM_WIDTH = 80;
const ITEM_GAP = 12;
const TOTAL_ITEM_SIZE = ITEM_WIDTH + ITEM_GAP;
const SIDE_PADDING = (width - ITEM_WIDTH) / 2;

export default function EventScreen({ route }) {
  const navigation = useNavigation();
  const { credits, fetchBalance } = useCredits();
  const { theme, colors } = useTheme();
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [monthlyData, setMonthlyData] = useState(null);
  
  // Loading states
  const [loadingMonthly, setLoadingMonthly] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [creditCost, setCreditCost] = useState(100);
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const progressIntervalRef = useRef(null);
  const [nativeName, setNativeName] = useState('');
  const [birthData, setBirthData] = useState(null);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const yearSliderRef = useRef(null);
  const loadingIntervalRef = useRef(null);

  const loadingMessages = [
    { icon: '🌟', text: 'Analyzing planetary positions...' },
    { icon: '🔮', text: `Calculating dasha periods for ${selectedYear}...` },
    { icon: '✨', text: 'Examining transit patterns...' },
    { icon: '🌙', text: 'Consulting the cosmic calendar...' },
    { icon: '⭐', text: 'Mapping celestial influences...' },
    { icon: '🪐', text: 'Decoding planetary alignments...' },
    { icon: '💫', text: 'Synthesizing astrological insights...' },
    { icon: '🌠', text: 'Studying nakshatra transits...' },
    { icon: '☀️', text: 'Analyzing solar influences...' },
    { icon: '🌕', text: 'Examining lunar cycles...' },
    { icon: '♃', text: 'Calculating Jupiter transits...' },
    { icon: '♄', text: 'Tracking Saturn movements...' },
    { icon: '♂️', text: 'Assessing Mars energy...' },
    { icon: '♀️', text: 'Evaluating Venus positions...' },
    { icon: '☿', text: 'Analyzing Mercury patterns...' },
    { icon: '🔱', text: 'Computing Rahu-Ketu axis...' },
    { icon: '📊', text: 'Calculating house strengths...' },
    { icon: '🎯', text: 'Identifying key life events...' },
    { icon: '🌈', text: 'Mapping yogas and combinations...' },
    { icon: '⚡', text: 'Detecting planetary aspects...' },
    { icon: '🧭', text: 'Determining auspicious periods...' },
    { icon: '📅', text: 'Analyzing monthly forecasts...' },
    { icon: '🔬', text: 'Examining divisional charts...' },
    { icon: '🎨', text: 'Painting your cosmic picture...' },
    { icon: '🌊', text: 'Flowing through time cycles...' },
    { icon: '🔥', text: 'Igniting predictive insights...' },
    { icon: '🌸', text: 'Blooming astrological wisdom...' },
    { icon: '🎭', text: 'Revealing karmic patterns...' },
    { icon: '🗝️', text: 'Unlocking celestial secrets...' },
    { icon: '💎', text: 'Polishing your predictions...' },
    { icon: '🌺', text: 'Cultivating cosmic clarity...' },
    { icon: '🦋', text: 'Transforming raw data...' },
    { icon: '🌻', text: 'Growing your timeline...' },
    { icon: '🎪', text: 'Orchestrating planetary dance...' },
    { icon: '🏔️', text: 'Scaling astrological peaks...' },
    { icon: '🌅', text: 'Dawning new insights...' },
    { icon: '🎼', text: 'Composing cosmic symphony...' },
    { icon: '🔭', text: 'Peering into your future...' },
    { icon: '🌌', text: 'Navigating the cosmos...' },
    { icon: '✅', text: 'Finalizing your predictions...' }
  ];

  // Get birth data from storage
  const getBirthDetails = async () => {
    try {
      return await storage.getBirthDetails();
    } catch (error) {
      console.error('Error getting birth details:', error);
      return null;
    }
  };

  // Load native name and birth data on mount
  useEffect(() => {
    const loadBirthData = async () => {
      const birthData = await getBirthDetails();
      if (birthData?.name) {
        setNativeName(birthData.name.substring(0, 7));
        setBirthData(birthData); // Store full birth data for the chip
      }
    };
    loadBirthData();
  }, []);

  // Fetch credit cost on component mount
  useEffect(() => {
    const fetchCreditCost = async () => {
      try {
        // console.log('💰 Fetching credit cost from:', API_BASE_URL + '/api/credits/settings/event-timeline-cost');
        const response = await creditAPI.getEventTimelineCost();
        console.log('✅ Credit cost response:', response.data);
        if (response.data.cost) {
          setCreditCost(response.data.cost);
        }
      } catch (error) {
        console.error('❌ Error fetching credit cost:', {
          message: error.message,
          status: error.response?.status,
          data: error.response?.data,
          url: error.config?.url
        });
      }
    };
    fetchCreditCost();
  }, []);

  // Fetch Monthly Guide (AI Powered) with Polling
  const fetchMonthlyGuide = useCallback(async (year) => {
    setLoadingMonthly(true);
    setMonthlyData(null);
    setLoadingMessageIndex(0);
    
    // Start rotating loading messages
    loadingIntervalRef.current = setInterval(() => {
      setLoadingMessageIndex(prev => (prev + 1) % loadingMessages.length);
    }, 3000);
    
    // Start progress bar animation
    setLoadingProgress(0);
    let elapsed = 0;
    progressIntervalRef.current = setInterval(() => {
      elapsed += 100;
      if (elapsed <= 100000) {
        setLoadingProgress((elapsed / 100000) * 90);
      } else {
        setLoadingProgress(-1);
      }
    }, 100);
    
    try {
      const birthData = await getBirthDetails();
      if (!birthData) return;
      
      // console.log('👤 Birth data loaded:', { id: birthData.id, name: birthData.name?.substring(0, 5) });
      
      if (!birthData.id) {
        Alert.alert('Error', 'Birth chart ID not found. Please re-select your birth chart from Select Native screen.');
        setAnalysisStarted(false);
        setLoadingMonthly(false);
        if (loadingIntervalRef.current) {
          clearInterval(loadingIntervalRef.current);
          loadingIntervalRef.current = null;
        }
        return;
      }
      
      // console.log('🚀 Starting monthly events request for year:', year);
      const startResponse = await chatAPI.getMonthlyEvents({
        ...birthData,
        selectedYear: year,
        birth_chart_id: birthData.id
      });
      // console.log('✅ Monthly events response:', startResponse.data);
      
      // Check if we got the old format (direct data) or new format (job_id)
      if (startResponse.data?.data && !startResponse.data?.job_id) {
        setMonthlyData(startResponse.data.data);
        fetchBalance();
        setLoadingMonthly(false);
        if (loadingIntervalRef.current) {
          clearInterval(loadingIntervalRef.current);
          loadingIntervalRef.current = null;
        }
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
          progressIntervalRef.current = null;
        }
        return;
      }
      
      const jobId = startResponse.data?.job_id;
      if (!jobId) {
        throw new Error('No job_id received from server.');
      }
      
      // Step 2: Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await chatAPI.getMonthlyEventsStatus(jobId);
          const status = statusResponse.data.status;
          
          if (status === 'completed') {
            clearInterval(pollInterval);
            console.log('✅ Analysis completed, setting monthlyData:', JSON.stringify(statusResponse.data.data, null, 2));
            setMonthlyData(statusResponse.data.data);
            fetchBalance();
            setLoadingMonthly(false);
            if (loadingIntervalRef.current) {
              clearInterval(loadingIntervalRef.current);
              loadingIntervalRef.current = null;
            }
            if (progressIntervalRef.current) {
              clearInterval(progressIntervalRef.current);
              progressIntervalRef.current = null;
            }
          } else if (status === 'failed') {
            clearInterval(pollInterval);
            throw new Error(statusResponse.data.error || 'Analysis failed');
          }
        } catch (pollError) {
          clearInterval(pollInterval);
          throw pollError;
        }
      }, 3000); // Poll every 3 seconds
      
      // Cleanup polling after 5 minutes timeout
      setTimeout(() => {
        clearInterval(pollInterval);
        if (loadingMonthly) {
          setLoadingMonthly(false);
          if (loadingIntervalRef.current) {
            clearInterval(loadingIntervalRef.current);
            loadingIntervalRef.current = null;
          }
          if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current);
            progressIntervalRef.current = null;
          }
          Alert.alert('Timeout', 'Analysis is taking longer than expected. Please try again.');
          setAnalysisStarted(false);
        }
      }, 300000);
      
    } catch (error) {
      console.error('❌ EventScreen Error Details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.config?.url,
        headers: error.config?.headers
      });
      
      let errorMessage = 'Failed to load timeline. Please try again.';
      
      if (error.response?.status === 401) {
        errorMessage = 'Session expired. Please login again.';
        Alert.alert('Authentication Error', errorMessage, [
          { text: 'Login', onPress: () => navigation.navigate('Login') },
          { text: 'Cancel' }
        ]);
      } else if (error.response?.status === 402) {
        errorMessage = 'You need more credits for this analysis.';
        Alert.alert('Insufficient Credits', errorMessage, [
          { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
          { text: 'OK' }
        ]);
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error. Please contact support or try again later.';
        Alert.alert('Server Error', errorMessage);
      } else if (error.message === 'Network Error' || !error.response) {
        errorMessage = 'Cannot connect to server. Check your internet connection.';
        Alert.alert('Network Error', errorMessage);
      } else {
        Alert.alert('Error', errorMessage + '\n\nDetails: ' + (error.response?.data?.detail || error.message));
      }
      
      setAnalysisStarted(false);
      setLoadingMonthly(false);
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
        loadingIntervalRef.current = null;
      }
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
    }
  }, [fetchBalance, loadingMessages.length]);

  // Check for cached data when analysis starts or year changes
  useEffect(() => {
    const loadCachedData = async () => {
      if (!analysisStarted) return;
      
      if (monthlyData) return;
      
      try {
        const birthData = await getBirthDetails();
        if (!birthData) return;
        
        // console.log('🔍 Checking cache with:', { 
        //   birth_chart_id: birthData.id, 
        //   selectedYear: selectedYear,
        //   name: birthData.name 
        // });
        
        const cacheResponse = await chatAPI.getCachedMonthlyEvents({
          ...birthData,
          selectedYear: selectedYear,
          birth_chart_id: birthData.id
        });
        
        // console.log('📦 Cache response:', cacheResponse.data);
        
        if (cacheResponse.data?.cached && cacheResponse.data?.data) {
          setMonthlyData(cacheResponse.data.data);
        } else {
          // No cached data - check credits before generating
          await fetchBalance();
          const freshBalance = await creditAPI.getBalance();
          const actualCredits = freshBalance.data.balance;
          
          if (actualCredits < creditCost) {
            Alert.alert('Insufficient Credits', `You need ${creditCost} credits for this analysis. You have ${actualCredits} credits.`, [
              { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
              { text: 'Cancel', onPress: () => setAnalysisStarted(false) }
            ]);
            return;
          }
          
          fetchMonthlyGuide(selectedYear);
        }
      } catch (error) {
        fetchMonthlyGuide(selectedYear);
      }
    };
    
    if (analysisStarted) {
      loadCachedData();
    }
    
    // Cleanup interval on unmount
    return () => {
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
      }
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, [selectedYear, analysisStarted]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchMonthlyGuide(selectedYear).then(() => setRefreshing(false));
  }, [selectedYear]);

  const years = React.useMemo(() => Array.from({length: 101}, (_, i) => START_YEAR + i), []);

  useEffect(() => {
    if (yearSliderRef.current && !analysisStarted) {
      const index = selectedYear - START_YEAR;
      setTimeout(() => {
        yearSliderRef.current?.scrollToIndex({ 
          index, 
          animated: false,
          viewPosition: 0
        });
      }, 100);
    }
  }, [analysisStarted]);

  const handleYearChange = (year) => {
    setSelectedYear(year);
    setMonthlyData(null); // Clear data when year changes
    const index = year - START_YEAR;
    yearSliderRef.current?.scrollToIndex({ 
      index, 
      animated: true, 
      viewPosition: 0 
    });
  };

  const navigateToChat = (context, type) => {
    // Build detailed prediction text from context
    console.log('📋 Context data:', JSON.stringify(context, null, 2));
    console.log('📋 Events count:', context.events?.length);
    
    let predictionText = `${context.month} Predictions:\n\n`;
    
    if (context.events && context.events.length > 0) {
      context.events.forEach((event, idx) => {
        predictionText += `Event ${idx + 1}: ${event.type}\n`;
        predictionText += `${event.prediction}\n`;
        if (event.start_date && event.end_date) {
          predictionText += `Period: ${event.start_date} to ${event.end_date}\n`;
        }
        
        // Include manifestations if available
        if (event.possible_manifestations && event.possible_manifestations.length > 0) {
          predictionText += `\nPossible Scenarios (${event.possible_manifestations.length}):\n`;
          event.possible_manifestations.forEach((manifest, mIdx) => {
            const scenario = typeof manifest === 'string' ? manifest : manifest.scenario;
            predictionText += `${mIdx + 1}. ${scenario}\n`;
          });
        }
        predictionText += `\n`;
      });
    }
    
    predictionText += `Please explain these predictions in more detail.`;
    
    console.log('📋 Final prediction text:', predictionText);
    
    navigation.navigate('Home', {
      startChat: true,
      initialMessage: predictionText
    });
  };

  const handleContinue = async () => {
    try {
      const birthData = await getBirthDetails();
      if (!birthData || !birthData.id) {
        Alert.alert('Error', 'Birth chart not found. Please select a birth chart.');
        return;
      }
      
      // Check if cached data exists
      const cacheResponse = await chatAPI.getCachedMonthlyEvents({
        ...birthData,
        selectedYear: selectedYear,
        birth_chart_id: birthData.id
      });
      
      if (cacheResponse.data?.cached) {
        // Cached data exists - proceed directly
        setAnalysisStarted(true);
      } else {
        // No cache - show credit confirmation modal
        await fetchBalance();
        const freshBalance = await creditAPI.getBalance();
        const actualCredits = freshBalance.data.balance;
        
        if (actualCredits < creditCost) {
          Alert.alert('Insufficient Credits', `You need ${creditCost} credits for this analysis. You have ${actualCredits} credits.`, [
            { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
            { text: 'Cancel', style: 'cancel' }
          ]);
          return;
        }
        
        // Show confirmation modal
        Alert.alert(
          'Generate Predictions',
          `This will cost ${creditCost} credits to generate predictions for ${selectedYear}. Continue?`,
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Continue', onPress: () => setAnalysisStarted(true) }
          ]
        );
      }
    } catch (error) {
      console.error('❌ Cache Check Error Details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.config?.url
      });
      
      if (error.response?.status === 401) {
        Alert.alert('Authentication Error', 'Session expired. Please login again.', [
          { text: 'Login', onPress: () => navigation.navigate('Login') },
          { text: 'Cancel' }
        ]);
      } else {
        Alert.alert('Error', 'Failed to check for existing predictions. Please try again.');
      }
    }
  };

  const getMonthName = (monthId) => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months[monthId - 1] || `Month ${monthId}`;
  };

  const handleRegenerateConfirm = async () => {
    setShowRegenerateModal(false);
    await fetchBalance();
    
    const freshBalance = await creditAPI.getBalance();
    const actualCredits = freshBalance.data.balance;
    
    if (actualCredits < creditCost) {
      Alert.alert('Insufficient Credits', `You need ${creditCost} credits to regenerate. You have ${actualCredits} credits.`, [
        { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
        { text: 'Cancel', style: 'cancel' }
      ]);
      return;
    }
    
    setMonthlyData(null);
    fetchMonthlyGuide(selectedYear);
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Regenerate Confirmation Modal */}
      <Modal
        visible={showRegenerateModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowRegenerateModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: colors.backgroundSecondary, borderColor: colors.cardBorder }]}>
            <Ionicons name="refresh-circle" size={48} color={colors.accent} style={styles.modalIcon} />
            <Text style={[styles.modalTitle, { color: colors.accent }]}>Regenerate Predictions?</Text>
            <Text style={[styles.modalText, { color: colors.textSecondary }]}>This will cost {creditCost} credits to generate fresh predictions for {selectedYear}.</Text>
            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={[styles.modalButton, styles.modalButtonCancel, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]} 
                onPress={() => setShowRegenerateModal(false)}
              >
                <Text style={[styles.modalButtonTextCancel, { color: colors.text }]}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.modalButton, styles.modalButtonConfirm, { backgroundColor: colors.accent }]} 
                onPress={handleRegenerateConfirm}
              >
                <Text style={[styles.modalButtonTextConfirm, { color: theme === 'dark' ? colors.background : '#1a1a1a' }]}>Confirm</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
      {/* Header */}
      <View style={[styles.header, { backgroundColor: colors.backgroundSecondary, borderBottomColor: colors.cardBorder }]}>
        <TouchableOpacity onPress={() => analysisStarted ? setAnalysisStarted(false) : navigation.goBack()} style={[styles.backButton, { backgroundColor: colors.surface }]}>
          <Ionicons name="arrow-back" size={24} color={colors.accent} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={[styles.headerTitle, { color: colors.accent }]}>{analysisStarted ? `${selectedYear} Predictions` : 'Major Life Events'}</Text>
          {birthData && (
            <NativeSelectorChip 
              birthData={birthData}
              onPress={() => navigation.navigate('SelectNative')}
              maxLength={12}
            />
          )}
        </View>
        <View style={styles.headerRight}>
          {analysisStarted && monthlyData && (
            <TouchableOpacity onPress={() => setShowRegenerateModal(true)} style={[styles.regenerateButton, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
              <Ionicons name="refresh" size={22} color={colors.accent} />
            </TouchableOpacity>
          )}
          {analysisStarted && (
            <TouchableOpacity onPress={() => setAnalysisStarted(false)} style={[styles.settingsButton, { backgroundColor: colors.surface }]}>
              <Ionicons name="settings-outline" size={24} color={colors.accent} />
            </TouchableOpacity>
          )}
        </View>
        {!analysisStarted && <View style={styles.headerSpacer} />}
      </View>

      {!analysisStarted ? (
        <View style={[styles.selectionContainer, { backgroundColor: colors.background }]}>
          <Text style={[styles.selectionTitle, { color: colors.accent }]}>🌟 Select Your Year</Text>
          <Text style={[styles.selectionSubtitle, { color: colors.textSecondary }]}>Which year would you like to explore?</Text>
          
          {/* Year Picker - Horizontal Chips */}
          <View style={styles.yearChipsContainer}>
            <FlatList
              ref={yearSliderRef}
              horizontal
              data={years}
              keyExtractor={(item) => item.toString()}
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.yearChipsContent}
              decelerationRate="fast"
              getItemLayout={(data, index) => ({
                length: TOTAL_ITEM_SIZE,
                offset: TOTAL_ITEM_SIZE * index,
                index,
              })}
              onScrollToIndexFailed={(info) => {
                const wait = new Promise(resolve => setTimeout(resolve, 500));
                wait.then(() => {
                  yearSliderRef.current?.scrollToIndex({ 
                    index: info.index, 
                    animated: true,
                    viewPosition: 0
                  });
                });
              }}
              renderItem={({ item }) => (
                <View style={{ width: TOTAL_ITEM_SIZE }}>
                  <TouchableOpacity
                    style={[
                      styles.yearChip,
                      { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder },
                      selectedYear === item && { backgroundColor: colors.accent, borderColor: colors.accent },
                      { width: ITEM_WIDTH }
                    ]}
                    onPress={() => handleYearChange(item)}
                  >
                    <Text style={[
                      styles.yearChipText,
                      { color: colors.textSecondary },
                      selectedYear === item && { color: theme === 'dark' ? colors.background : '#1a1a1a' }
                    ]}>
                      {item}
                    </Text>
                  </TouchableOpacity>
                </View>
              )}
            />
          </View>

          {/* Quick Select */}
          <View style={styles.quickSelectContainer}>
            <TouchableOpacity 
              style={[styles.quickSelectButton, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}
              onPress={() => handleYearChange(new Date().getFullYear())}
            >
              <Text style={[styles.quickSelectText, { color: colors.accent }]}>This Year</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.quickSelectButton, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}
              onPress={() => handleYearChange(new Date().getFullYear() + 1)}
            >
              <Text style={[styles.quickSelectText, { color: colors.accent }]}>Next Year</Text>
            </TouchableOpacity>
          </View>

          {/* What's Included */}
          <View style={[styles.featuresContainer, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
            <Text style={[styles.featuresTitle, { color: colors.accent }]}>What's Included:</Text>
            <View style={styles.featureItem}>
              <Ionicons name="checkmark-circle" size={20} color={colors.accent} />
              <Text style={[styles.featureText, { color: colors.text }]}>12 Monthly Forecasts</Text>
            </View>
            <View style={styles.featureItem}>
              <Ionicons name="checkmark-circle" size={20} color={colors.accent} />
              <Text style={[styles.featureText, { color: colors.text }]}>Major Life Events</Text>
            </View>
            <View style={styles.featureItem}>
              <Ionicons name="checkmark-circle" size={20} color={colors.accent} />
              <Text style={[styles.featureText, { color: colors.text }]}>Timing Guidance</Text>
            </View>
            <View style={styles.featureItem}>
              <Ionicons name="checkmark-circle" size={20} color={colors.accent} />
              <Text style={[styles.featureText, { color: colors.text }]}>AI-Powered Insights</Text>
            </View>
          </View>

          {/* Continue Button */}
          <View style={styles.unlockButtonContainer}>
            <TouchableOpacity style={styles.unlockButton} onPress={handleContinue}>
              <LinearGradient colors={[colors.accent, colors.primary]} style={styles.unlockGradient}>
                <Text style={[styles.unlockButtonText, { color: theme === 'dark' ? colors.background : '#1a1a1a' }]}>Continue</Text>
                <Ionicons name="arrow-forward" size={22} color={theme === 'dark' ? colors.background : '#1a1a1a'} />
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <ScrollView 
        contentContainerStyle={[styles.scrollContent, { backgroundColor: colors.background }]}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accent} />}
      >
        {/* Native Name */}
        {nativeName && (
          <View style={styles.nameContainer}>
            <Text style={[styles.nameText, { color: colors.accent }]}>{nativeName}</Text>
          </View>
        )}

        {/* Macro Trends (The "Vibe") */}
        {monthlyData?.macro_trends && (
          <View style={[styles.macroCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
            <View style={styles.macroHeader}>
              <Ionicons name="planet" size={18} color={colors.accent} />
              <Text style={[styles.macroTitle, { color: colors.accent }]}>The Vibe of {selectedYear}</Text>
            </View>
            {monthlyData.macro_trends.map((trend, index) => (
              <View key={index} style={styles.trendRow}>
                <Text style={[styles.bullet, { color: colors.accent }]}>•</Text>
                <Text style={[styles.trendText, { color: colors.text }]}>{trend}</Text>
              </View>
            ))}
          </View>
        )}

        {/* SECTION 3: Monthly Guide (The "Details") */}
        {loadingMonthly ? (
          <View style={styles.section}>
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={colors.accent} />
              <Text style={styles.loadingIcon}>{loadingMessages[loadingMessageIndex].icon}</Text>
              <Text style={[styles.loadingText, { color: colors.text }]}>{loadingMessages[loadingMessageIndex].text}</Text>
              
              {loadingProgress >= 0 ? (
                <View style={styles.progressBarContainer}>
                  <View style={[styles.progressBarTrack, { backgroundColor: colors.backgroundSecondary, borderColor: colors.cardBorder }]}>
                    <View style={[styles.progressBarFill, { width: `${loadingProgress}%`, backgroundColor: colors.accent }]} />
                  </View>
                  <Text style={[styles.progressPercentText, { color: colors.accent }]}>
                    {loadingProgress < 90 ? `${Math.round(loadingProgress)}%` : 'Almost there...'}
                  </Text>
                </View>
              ) : (
                <Text style={[styles.takingLongerText, { color: colors.textSecondary }]}>Taking longer than usual...</Text>
              )}
            </View>
          </View>
        ) : monthlyData?.monthly_predictions && monthlyData.monthly_predictions.length > 0 ? (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.accent }]}>📅 Monthly Guide</Text>
            <View style={styles.accordionContainer}>
              {monthlyData?.monthly_predictions?.map((month, index) => (
                <MonthlyAccordion 
                  key={index} 
                  data={{...month, month: getMonthName(month.month_id)}} 
                  onChatPress={() => navigateToChat({...month, month: getMonthName(month.month_id)}, 'monthly')}
                />
              ))}
            </View>
          </View>
        ) : monthlyData ? (
          <View style={styles.section}>
            <View style={styles.loadingContainer}>
              <Text style={[styles.loadingText, { color: colors.text }]}>⚠️ No predictions generated. Please try regenerating.</Text>
            </View>
          </View>
        ) : null}

      </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0f' },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#1a1a2e',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 215, 0, 0.1)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    elevation: 4,
    shadowColor: '#FFD700',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4
  },
  backButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(255, 215, 0, 0.1)'
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: { 
    fontSize: 22, 
    fontWeight: '700', 
    color: '#FFD700', 
    textAlign: 'center',
    marginBottom: 4,
    letterSpacing: 0.5
  },
  headerSpacer: { width: 32 },
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  regenerateButton: { 
    width: 40, 
    height: 40, 
    borderRadius: 20, 
    backgroundColor: 'rgba(255, 215, 0, 0.15)', 
    justifyContent: 'center', 
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.3)'
  },
  settingsButton: { 
    padding: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(255, 215, 0, 0.1)'
  },
  
  scrollContent: { paddingBottom: 40, backgroundColor: '#0a0a0f' },
  
  section: { marginTop: 24, marginBottom: 24 },
  sectionHeader: { paddingHorizontal: 20, marginBottom: 16 },
  sectionTitle: { fontSize: 20, fontWeight: '700', color: '#FFD700', marginBottom: 6, letterSpacing: 0.3 },
  sectionSubtitle: { fontSize: 14, color: '#b8b8c8', lineHeight: 20 },
  
  macroCard: {
    margin: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.2)',
    backgroundColor: '#16162a',
    elevation: 3,
    shadowColor: '#FFD700',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8
  },
  macroHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 16, gap: 10 },
  macroTitle: { fontSize: 18, fontWeight: '700', color: '#FFD700', letterSpacing: 0.3 },
  trendRow: { flexDirection: 'row', marginBottom: 10, alignItems: 'flex-start' },
  bullet: { color: '#FFD700', marginRight: 10, fontSize: 18, marginTop: 2 },
  trendText: { color: '#e8e8f0', fontSize: 15, lineHeight: 22, flex: 1 },
  
  loadingContainer: { alignItems: 'center', marginTop: 60, paddingHorizontal: 40 },
  loadingIcon: { fontSize: 56, marginTop: 20, marginBottom: 12 },
  loadingText: { color: '#e8e8f0', marginTop: 16, fontSize: 17, fontWeight: '600', textAlign: 'center', lineHeight: 26 },
  progressBarContainer: { width: '100%', marginTop: 28, alignItems: 'center' },
  progressBarTrack: { width: '100%', height: 8, backgroundColor: '#1a1a2e', borderRadius: 4, overflow: 'hidden', borderWidth: 1, borderColor: 'rgba(255, 215, 0, 0.2)' },
  progressBarFill: { height: '100%', backgroundColor: '#FFD700', borderRadius: 4 },
  progressPercentText: { color: '#FFD700', fontSize: 15, fontWeight: '700', marginTop: 10 },
  takingLongerText: { color: '#b8b8c8', fontSize: 14, marginTop: 28, fontStyle: 'italic' },
  
  waitingContainer: { 
    flex: 1, 
    justifyContent: 'center', 
    alignItems: 'center' 
  },
  waitingText: { 
    color: 'white', 
    marginTop: 16, 
    fontSize: 16, 
    fontWeight: '600' 
  },
  
  accordionContainer: { paddingHorizontal: 20 },
  
  selectionContainer: {
    flex: 1,
    padding: 20,
    backgroundColor: '#0a0a0f'
  },
  selectionTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFD700',
    textAlign: 'center',
    marginTop: 20,
    marginBottom: 8,
    letterSpacing: 0.5
  },
  selectionSubtitle: {
    fontSize: 15,
    color: '#b8b8c8',
    textAlign: 'center',
    marginBottom: 28,
    lineHeight: 22
  },
  yearChipsContainer: {
    marginBottom: 24,
    height: 64
  },
  yearChipsContent: {
    paddingHorizontal: (width - 80) / 2
  },
  yearChip: {
    paddingVertical: 14,
    backgroundColor: '#16162a',
    borderRadius: 14,
    borderWidth: 2,
    borderColor: 'rgba(255, 215, 0, 0.2)',
    alignItems: 'center',
    justifyContent: 'center'
  },
  yearChipSelected: {
    backgroundColor: '#FFD700',
    borderColor: '#FFD700',
    elevation: 4,
    shadowColor: '#FFD700',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.4,
    shadowRadius: 6
  },
  yearChipText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#b8b8c8'
  },
  yearChipTextSelected: {
    fontSize: 22,
    fontWeight: '700',
    color: '#0a0a0f'
  },
  quickSelectContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24
  },
  quickSelectButton: {
    flex: 1,
    paddingVertical: 12,
    backgroundColor: '#16162a',
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 215, 0, 0.3)'
  },
  quickSelectText: {
    color: '#FFD700',
    fontSize: 15,
    fontWeight: '600',
    textAlign: 'center',
    letterSpacing: 0.3
  },
  featuresContainer: {
    backgroundColor: '#16162a',
    padding: 20,
    borderRadius: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.15)'
  },
  featuresTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFD700',
    marginBottom: 14,
    letterSpacing: 0.3
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 12
  },
  featureText: {
    fontSize: 15,
    color: '#e8e8f0',
    lineHeight: 20
  },
  unlockButtonContainer: {
    marginTop: 'auto',
    paddingTop: 20
  },
  unlockButton: {
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#FFD700',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.5,
    shadowRadius: 12,
    elevation: 10
  },
  unlockGradient: {
    paddingVertical: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10
  },
  unlockButtonText: {
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 0.5
  },
  nameContainer: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 12
  },
  nameText: {
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
    letterSpacing: 0.5
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20
  },
  modalContent: {
    borderRadius: 20,
    padding: 28,
    width: '100%',
    maxWidth: 340,
    alignItems: 'center',
    borderWidth: 1,
    elevation: 10
  },
  modalIcon: {
    marginBottom: 20
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 14,
    textAlign: 'center',
    letterSpacing: 0.3
  },
  modalText: {
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 28
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
    width: '100%'
  },
  modalButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center'
  },
  modalButtonCancel: {
    borderWidth: 1.5
  },
  modalButtonConfirm: {
    elevation: 4
  },
  modalButtonTextCancel: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.3
  },
  modalButtonTextConfirm: {
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.3
  }
});