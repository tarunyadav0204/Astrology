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
        console.log('💰 Fetching credit cost from:', API_BASE_URL + '/api/credits/settings/event-timeline-cost');
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
      if (elapsed <= 60000) {
        setLoadingProgress((elapsed / 60000) * 90);
      } else if (elapsed <= 90000) {
        setLoadingProgress(90);
      } else {
        setLoadingProgress(-1);
      }
    }, 100);
    
    try {
      const birthData = await getBirthDetails();
      if (!birthData) return;
      
      console.log('👤 Birth data loaded:', { id: birthData.id, name: birthData.name?.substring(0, 5) });
      
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
      
      console.log('🚀 Starting monthly events request for year:', year);
      const startResponse = await chatAPI.getMonthlyEvents({
        ...birthData,
        selectedYear: year,
        birth_chart_id: birthData.id
      });
      console.log('✅ Monthly events response:', startResponse.data);
      
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
        
        console.log('🔍 Checking cache with:', { 
          birth_chart_id: birthData.id, 
          selectedYear: selectedYear,
          name: birthData.name 
        });
        
        const cacheResponse = await chatAPI.getCachedMonthlyEvents({
          ...birthData,
          selectedYear: selectedYear,
          birth_chart_id: birthData.id
        });
        
        console.log('📦 Cache response:', cacheResponse.data);
        
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
    navigation.navigate('ChatScreen', {
      initialMessage: `I want to know more about the ${type} prediction for ${context.title || context.month}.`,
      contextData: context,
      contextType: type
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
    <SafeAreaView style={styles.container}>
      {/* Regenerate Confirmation Modal */}
      <Modal
        visible={showRegenerateModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowRegenerateModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Ionicons name="refresh-circle" size={48} color="#FFD700" style={styles.modalIcon} />
            <Text style={styles.modalTitle}>Regenerate Predictions?</Text>
            <Text style={styles.modalText}>This will cost {creditCost} credits to generate fresh predictions for {selectedYear}.</Text>
            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={[styles.modalButton, styles.modalButtonCancel]} 
                onPress={() => setShowRegenerateModal(false)}
              >
                <Text style={styles.modalButtonTextCancel}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.modalButton, styles.modalButtonConfirm]} 
                onPress={handleRegenerateConfirm}
              >
                <Text style={styles.modalButtonTextConfirm}>Confirm</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => analysisStarted ? setAnalysisStarted(false) : navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="white" />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>{analysisStarted ? `${selectedYear} Predictions` : 'Major Life Events'}</Text>
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
            <TouchableOpacity onPress={() => setShowRegenerateModal(true)} style={styles.regenerateButton}>
              <Ionicons name="refresh" size={20} color="white" />
            </TouchableOpacity>
          )}
          {analysisStarted && (
            <TouchableOpacity onPress={() => setAnalysisStarted(false)} style={styles.settingsButton}>
              <Ionicons name="settings-outline" size={24} color="white" />
            </TouchableOpacity>
          )}
        </View>
        {!analysisStarted && <View style={styles.headerSpacer} />}
      </View>

      {!analysisStarted ? (
        <View style={styles.selectionContainer}>
          <Text style={styles.selectionTitle}>🌟 Select Your Year</Text>
          <Text style={styles.selectionSubtitle}>Which year would you like to explore?</Text>
          
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
                      selectedYear === item && styles.yearChipSelected,
                      { width: ITEM_WIDTH }
                    ]}
                    onPress={() => handleYearChange(item)}
                  >
                    <Text style={[
                      styles.yearChipText,
                      selectedYear === item && styles.yearChipTextSelected
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
              style={styles.quickSelectButton}
              onPress={() => handleYearChange(new Date().getFullYear())}
            >
              <Text style={styles.quickSelectText}>This Year</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.quickSelectButton}
              onPress={() => handleYearChange(new Date().getFullYear() + 1)}
            >
              <Text style={styles.quickSelectText}>Next Year</Text>
            </TouchableOpacity>
          </View>

          {/* What's Included */}
          <View style={styles.featuresContainer}>
            <Text style={styles.featuresTitle}>What's Included:</Text>
            <View style={styles.featureItem}>
              <Ionicons name="checkmark-circle" size={20} color="#FFD700" />
              <Text style={styles.featureText}>12 Monthly Forecasts</Text>
            </View>
            <View style={styles.featureItem}>
              <Ionicons name="checkmark-circle" size={20} color="#FFD700" />
              <Text style={styles.featureText}>Major Life Events</Text>
            </View>
            <View style={styles.featureItem}>
              <Ionicons name="checkmark-circle" size={20} color="#FFD700" />
              <Text style={styles.featureText}>Timing Guidance</Text>
            </View>
            <View style={styles.featureItem}>
              <Ionicons name="checkmark-circle" size={20} color="#FFD700" />
              <Text style={styles.featureText}>AI-Powered Insights</Text>
            </View>
          </View>

          {/* Continue Button */}
          <View style={styles.unlockButtonContainer}>
            <TouchableOpacity style={styles.unlockButton} onPress={handleContinue}>
              <LinearGradient colors={['#FFD700', '#FFA500']} style={styles.unlockGradient}>
                <Text style={styles.unlockButtonText}>Continue</Text>
                <Ionicons name="arrow-forward" size={20} color="#000" />
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <ScrollView 
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="white" />}
      >
        {/* Native Name */}
        {nativeName && (
          <View style={styles.nameContainer}>
            <Text style={styles.nameText}>{nativeName}</Text>
          </View>
        )}

        {/* Macro Trends (The "Vibe") */}
        {monthlyData?.macro_trends && (
          <LinearGradient colors={['#2A2A40', '#1F1F30']} style={styles.macroCard}>
            <View style={styles.macroHeader}>
              <Ionicons name="planet" size={18} color="#FFD700" />
              <Text style={styles.macroTitle}>The Vibe of {selectedYear}</Text>
            </View>
            {monthlyData.macro_trends.map((trend, index) => (
              <View key={index} style={styles.trendRow}>
                <Text style={styles.bullet}>•</Text>
                <Text style={styles.trendText}>{trend}</Text>
              </View>
            ))}
          </LinearGradient>
        )}

        {/* SECTION 3: Monthly Guide (The "Details") */}
        {loadingMonthly ? (
          <View style={styles.section}>
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#FFD700" />
              <Text style={styles.loadingIcon}>{loadingMessages[loadingMessageIndex].icon}</Text>
              <Text style={styles.loadingText}>{loadingMessages[loadingMessageIndex].text}</Text>
              
              {loadingProgress >= 0 ? (
                <View style={styles.progressBarContainer}>
                  <View style={styles.progressBarTrack}>
                    <View style={[styles.progressBarFill, { width: `${loadingProgress}%` }]} />
                  </View>
                  <Text style={styles.progressPercentText}>
                    {loadingProgress < 90 ? `${Math.round(loadingProgress)}%` : 'Almost there...'}
                  </Text>
                </View>
              ) : (
                <Text style={styles.takingLongerText}>Taking longer than usual...</Text>
              )}
            </View>
          </View>
        ) : monthlyData?.monthly_predictions ? (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>📅 Monthly Guide</Text>
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
        ) : null}

      </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121212' },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#1E1E2E',
    borderBottomWidth: 1,
    borderBottomColor: '#333',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between'
  },
  backButton: {
    padding: 4
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: { 
    fontSize: 20, 
    fontWeight: 'bold', 
    color: 'white', 
    textAlign: 'center',
    marginBottom: 4
  },
  headerSpacer: { width: 32 },
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  regenerateButton: { 
    width: 36, 
    height: 36, 
    borderRadius: 18, 
    backgroundColor: 'rgba(255, 255, 255, 0.2)', 
    justifyContent: 'center', 
    alignItems: 'center' 
  },
  settingsButton: { padding: 4 },
  
  scrollContent: { paddingBottom: 40 },
  
  section: { marginTop: 20, marginBottom: 20 },
  sectionHeader: { paddingHorizontal: 20, marginBottom: 15 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: 'white', marginBottom: 4 },
  sectionSubtitle: { fontSize: 13, color: '#AAA' },
  
  macroCard: {
    margin: 20,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#333'
  },
  macroHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 10, gap: 8 },
  macroTitle: { fontSize: 16, fontWeight: 'bold', color: '#FFD700' },
  trendRow: { flexDirection: 'row', marginBottom: 6 },
  bullet: { color: '#FFD700', marginRight: 8, fontSize: 16 },
  trendText: { color: '#DDD', fontSize: 14, lineHeight: 20, flex: 1 },
  
  loadingContainer: { alignItems: 'center', marginTop: 60, paddingHorizontal: 40 },
  loadingIcon: { fontSize: 48, marginTop: 16, marginBottom: 8, color: 'white' },
  loadingText: { color: 'white', marginTop: 12, fontSize: 16, fontWeight: '600', textAlign: 'center', lineHeight: 24 },
  progressBarContainer: { width: '100%', marginTop: 24, alignItems: 'center' },
  progressBarTrack: { width: '100%', height: 6, backgroundColor: '#333', borderRadius: 3, overflow: 'hidden' },
  progressBarFill: { height: '100%', backgroundColor: '#FFD700', borderRadius: 3 },
  progressPercentText: { color: '#FFD700', fontSize: 14, fontWeight: '600', marginTop: 8 },
  takingLongerText: { color: '#AAA', fontSize: 14, marginTop: 24, fontStyle: 'italic' },
  
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
    padding: 20
  },
  selectionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFD700',
    textAlign: 'center',
    marginTop: 10,
    marginBottom: 4
  },
  selectionSubtitle: {
    fontSize: 14,
    color: '#AAA',
    textAlign: 'center',
    marginBottom: 20
  },
  yearChipsContainer: {
    marginBottom: 20,
    height: 60
  },
  yearChipsContent: {
    paddingHorizontal: (width - 80) / 2
  },
  yearChip: {
    paddingVertical: 12,
    backgroundColor: '#2A2A40',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#444',
    alignItems: 'center',
    justifyContent: 'center'
  },
  yearChipSelected: {
    backgroundColor: '#FFD700',
    borderColor: '#FFD700'
  },
  yearChipText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#AAA'
  },
  yearChipTextSelected: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#000'
  },
  quickSelectContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16
  },
  quickSelectButton: {
    flex: 1,
    paddingVertical: 10,
    backgroundColor: '#2A2A40',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#444'
  },
  quickSelectText: {
    color: '#FFD700',
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center'
  },
  featuresContainer: {
    backgroundColor: '#1E1E2E',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16
  },
  featuresTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 10
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8
  },
  featureText: {
    fontSize: 14,
    color: '#DDD'
  },
  unlockButtonContainer: {
    marginTop: 'auto'
  },
  unlockButton: {
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#FFD700',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8
  },
  unlockGradient: {
    paddingVertical: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8
  },
  unlockButtonText: {
    color: '#000',
    fontSize: 17,
    fontWeight: 'bold'
  },
  nameContainer: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 8
  },
  nameText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFD700',
    textAlign: 'center'
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20
  },
  modalContent: {
    backgroundColor: '#1E1E2E',
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 340,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#333'
  },
  modalIcon: {
    marginBottom: 16
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 12,
    textAlign: 'center'
  },
  modalText: {
    fontSize: 14,
    color: '#AAA',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 24
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
    width: '100%'
  },
  modalButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center'
  },
  modalButtonCancel: {
    backgroundColor: '#2A2A40',
    borderWidth: 1,
    borderColor: '#444'
  },
  modalButtonConfirm: {
    backgroundColor: '#FFD700'
  },
  modalButtonTextCancel: {
    color: 'white',
    fontSize: 15,
    fontWeight: '600'
  },
  modalButtonTextConfirm: {
    color: '#000',
    fontSize: 15,
    fontWeight: 'bold'
  }
});