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

const { width } = Dimensions.get('window');

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
  const [nativeName, setNativeName] = useState('');
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

  // Load native name on mount
  useEffect(() => {
    const loadName = async () => {
      const birthData = await getBirthDetails();
      if (birthData?.name) {
        setNativeName(birthData.name.substring(0, 7));
      }
    };
    loadName();
  }, []);

  // Fetch credit cost on component mount
  useEffect(() => {
    const fetchCreditCost = async () => {
      try {
        const response = await creditAPI.getEventTimelineCost();
        if (response.data.cost) {
          setCreditCost(response.data.cost);
        }
      } catch (error) {
        console.error('Error fetching credit cost:', error);
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
    
    try {
      const birthData = await getBirthDetails();
      if (!birthData) return;
      
      const startResponse = await chatAPI.getMonthlyEvents({
        ...birthData,
        selectedYear: year
      });
      
      // Check if we got the old format (direct data) or new format (job_id)
      if (startResponse.data?.data && !startResponse.data?.job_id) {
        setMonthlyData(startResponse.data.data);
        fetchBalance();
        setLoadingMonthly(false);
        if (loadingIntervalRef.current) {
          clearInterval(loadingIntervalRef.current);
          loadingIntervalRef.current = null;
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
          Alert.alert('Timeout', 'Analysis is taking longer than expected. Please try again.');
          setAnalysisStarted(false);
        }
      }, 300000);
      
    } catch (error) {
      let errorMessage = 'Failed to load timeline. Please try again.';
      
      if (error.response?.status === 402) {
        errorMessage = 'You need more credits for this analysis.';
        Alert.alert('Insufficient Credits', errorMessage, [
          { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
          { text: 'OK' }
        ]);
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error. Please contact support or try again later.';
        Alert.alert('Server Error', errorMessage);
      } else {
        Alert.alert('Error', errorMessage);
      }
      
      setAnalysisStarted(false);
      setLoadingMonthly(false);
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
        loadingIntervalRef.current = null;
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
        
        const cacheResponse = await chatAPI.getCachedMonthlyEvents({
          ...birthData,
          selectedYear: selectedYear
        });
        
        if (cacheResponse.data?.cached && cacheResponse.data?.data) {
          setMonthlyData(cacheResponse.data.data);
        } else {
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
    };
  }, [selectedYear, analysisStarted]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchMonthlyGuide(selectedYear).then(() => setRefreshing(false));
  }, [selectedYear]);

  const handleYearChange = (year) => {
    setSelectedYear(year);
    setTimeout(() => {
      const index = year - 1950;
      yearSliderRef.current?.scrollToIndex({ index, animated: true, viewPosition: 0.5 });
    }, 100);
  };

  const navigateToChat = (context, type) => {
    navigation.navigate('ChatScreen', {
      initialMessage: `I want to know more about the ${type} prediction for ${context.title || context.month}.`,
      contextData: context,
      contextType: type
    });
  };

  const handleStartAnalysis = async () => {
    // Fetch fresh balance to ensure sync with backend
    await fetchBalance();
    
    // Re-check after fetching fresh balance
    const freshBalance = await creditAPI.getBalance();
    const actualCredits = freshBalance.data.balance;
    
    if (actualCredits < creditCost) {
      Alert.alert('Insufficient Credits', `You need ${creditCost} credits for this analysis. You have ${actualCredits} credits.`, [
        { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
        { text: 'Cancel', style: 'cancel' }
      ]);
      return;
    }

    // Don't manually deduct credits - the monthly-events endpoint handles it automatically
    setAnalysisStarted(true);
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
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="white" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{analysisStarted ? `${selectedYear} Predictions` : 'Select Year'}</Text>
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
          
          {/* Year Picker */}
          <View style={styles.yearPickerContainer}>
            <FlatList
              ref={yearSliderRef}
              data={Array.from({length: 101}, (_, i) => 1950 + i)}
              keyExtractor={(item) => item.toString()}
              showsVerticalScrollIndicator={false}
              contentContainerStyle={styles.yearPickerContent}
              snapToInterval={60}
              decelerationRate="fast"
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={styles.yearItem}
                  onPress={() => handleYearChange(item)}
                >
                  <Text style={[styles.yearText, selectedYear === item && styles.selectedYearText]}>
                    {item}
                  </Text>
                </TouchableOpacity>
              )}
              getItemLayout={(data, index) => ({
                length: 60,
                offset: 60 * index,
                index,
              })}
              initialScrollIndex={selectedYear - 1950}
              onScrollToIndexFailed={(info) => {
                setTimeout(() => {
                  yearSliderRef.current?.scrollToIndex({ index: info.index, animated: true, viewPosition: 0.5 });
                }, 100);
              }}
            />
            <View style={styles.yearPickerOverlay} pointerEvents="none">
              <View style={styles.yearPickerHighlight} />
            </View>
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

          {/* Unlock or Get Credits Button */}
          <View style={styles.unlockButtonContainer}>
                {credits < creditCost ? (
              <TouchableOpacity style={styles.unlockButton} onPress={() => navigation.navigate('Credits')}>
                <LinearGradient colors={['#FF6B6B', '#FF8E53']} style={styles.unlockGradient}>
                  <Text style={styles.unlockButtonText}>Get {creditCost - credits} More Credits</Text>
                  <Ionicons name="card" size={20} color="#000" />
                </LinearGradient>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity style={styles.unlockButton} onPress={handleStartAnalysis}>
                <LinearGradient colors={['#FFD700', '#FFA500']} style={styles.unlockGradient}>
                  <Text style={styles.unlockButtonText}>Unlock for {creditCost} Credits</Text>
                  <Ionicons name="arrow-forward" size={20} color="#000" />
                </LinearGradient>
              </TouchableOpacity>
            )}
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
              <View style={styles.loadingDotsContainer}>
                {loadingMessages.map((_, index) => (
                  <View 
                    key={index} 
                    style={[
                      styles.loadingDot,
                      index === loadingMessageIndex && styles.loadingDotActive
                    ]} 
                  />
                ))}
              </View>
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
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: 'white', flex: 1, textAlign: 'center' },
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
  loadingIcon: { fontSize: 48, marginTop: 16, marginBottom: 8 },
  loadingText: { color: 'white', marginTop: 12, fontSize: 16, fontWeight: '600', textAlign: 'center', lineHeight: 24 },
  loadingDotsContainer: { flexDirection: 'row', marginTop: 20, gap: 8 },
  loadingDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#333' },
  loadingDotActive: { backgroundColor: '#FFD700', width: 24 },
  
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
  yearPickerContainer: {
    height: 180,
    marginBottom: 16,
    position: 'relative'
  },
  yearPickerContent: {
    paddingVertical: 60
  },
  yearItem: {
    height: 60,
    justifyContent: 'center',
    alignItems: 'center'
  },
  yearText: {
    fontSize: 28,
    fontWeight: '600',
    color: '#555'
  },
  selectedYearText: {
    fontSize: 40,
    fontWeight: 'bold',
    color: '#FFD700'
  },
  yearPickerOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center'
  },
  yearPickerHighlight: {
    height: 60,
    borderTopWidth: 2,
    borderBottomWidth: 2,
    borderColor: '#FFD700'
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