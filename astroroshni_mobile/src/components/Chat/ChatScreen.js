import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  FlatList,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Modal,
  Share,
  Platform,
  KeyboardAvoidingView,
  BackHandler,
  Animated,
  Dimensions,
  InteractionManager,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';

import MessageBubble from './MessageBubble';
import LoadingBubble from '../LoadingBubble';
import FeedbackComponent from './FeedbackComponent';
import EventPeriods from './EventPeriods';
import HomeScreen from './HomeScreen';
import CalibrationCard from './CalibrationCard';
import PremiumAnalysisModal from './PremiumAnalysisModal';
import { storage } from '../../services/storage';
import { chatAPI } from '../../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS, LANGUAGES, API_BASE_URL, getEndpoint } from '../../utils/constants';
import { COUNTRIES, YEARS } from '../../utils/mundaneConstants';
import { trackAstrologyEvent } from '../../utils/analytics';
import { useTheme } from '../../context/ThemeContext';
import { Image } from 'react-native';

import CascadingDashaBrowser from '../Dasha/CascadingDashaBrowser';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import { useCredits } from '../../credits/CreditContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useTranslation } from 'react-i18next';

const { width: screenWidth } = Dimensions.get('window');
const isSmallScreen = screenWidth < 375;
const cardWidth = screenWidth * 0.22;
const fontSize = isSmallScreen ? 11 : 13;
const smallFontSize = isSmallScreen ? 9 : 10;

export default function ChatScreen({ navigation, route }) {
  const { t, i18n } = useTranslation();
  useAnalytics('ChatScreen');
  const { theme, colors, getCardElevation } = useTheme();
  const { credits, partnershipCost, fetchBalance } = useCredits();
  
  // Mundane mode state
  const [isMundane, setIsMundane] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState(COUNTRIES[0]);
  const [selectedYear, setSelectedYear] = useState(YEARS[0]);
  const [showCountryPicker, setShowCountryPicker] = useState(false);
  const [showYearPicker, setShowYearPicker] = useState(false);
  const [chatCost, setChatCost] = useState(1);
  const [premiumChatCost, setPremiumChatCost] = useState(3);
  const [isPremiumAnalysis, setIsPremiumAnalysis] = useState(false);
  const [showEnhancedPopup, setShowEnhancedPopup] = useState(false);
  const [showPremiumBadge, setShowPremiumBadge] = useState(false);
  const [showPremiumModal, setShowPremiumModal] = useState(false);
  const [showPremiumTooltip, setShowPremiumTooltip] = useState(true);
  const tooltipResetRef = useRef(true);
  const glowAnim = useRef(new Animated.Value(0)).current;
  const badgeFadeAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (isPremiumAnalysis) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(glowAnim, {
            toValue: 1,
            duration: 1500,
            useNativeDriver: true,
          }),
          Animated.timing(glowAnim, {
            toValue: 0,
            duration: 1500,
            useNativeDriver: true,
          }),
        ])
      ).start();
      
      // Show badge
      setShowPremiumBadge(true);
      Animated.timing(badgeFadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
      
      // Hide after 3 seconds
      const timer = setTimeout(() => {
        Animated.timing(badgeFadeAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }).start(() => setShowPremiumBadge(false));
      }, 3000);
      
      return () => clearTimeout(timer);
    } else {
      setShowPremiumBadge(false);
    }
  }, [isPremiumAnalysis]);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [dynamicLoadingMessages, setDynamicLoadingMessages] = useState(null);
  const [language, setLanguage] = useState('english');
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const drawerAnim = useRef(new Animated.Value(300)).current;
  const menuScrollViewRef = useRef(null);
  const menuLogoGlow = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    let animation;
    if (showMenu) {
      animation = Animated.loop(
        Animated.sequence([
          Animated.timing(menuLogoGlow, {
            toValue: 1,
            duration: 1500,
            useNativeDriver: false,
          }),
          Animated.timing(menuLogoGlow, {
            toValue: 0,
            duration: 1500,
            useNativeDriver: false,
          }),
        ])
      );
      animation.start();
    } else {
      menuLogoGlow.setValue(0);
    }
    return () => {
      animation?.stop();
    };
  }, [showMenu]);

  const [showEventPeriods, setShowEventPeriods] = useState(false);
  const [showDashaBrowser, setShowDashaBrowser] = useState(false);
  const [showGreeting, setShowGreeting] = useState(true);
  const [isAppStartup, setIsAppStartup] = useState(true);
  const [birthData, setBirthData] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [currentPersonId, setCurrentPersonId] = useState(null);
  const [pendingMessages, setPendingMessages] = useState(new Set());
  const scrollViewRef = useRef(null);
  const [forceGreeting, setForceGreeting] = useState(false);
  const [chartData, setChartData] = useState(null);
  const [loadingChart, setLoadingChart] = useState(false);
  const [dashaData, setDashaData] = useState(null);
  const [loadingDashas, setLoadingDashas] = useState(false);
  const lastMessageRef = useRef(null);
  
  // Calibration state
  const [calibrationEvent, setCalibrationEvent] = useState(null);
  
  // Partnership mode state
  const [partnershipMode, setPartnershipMode] = useState(false);
  const [nativeChart, setNativeChart] = useState(null);
  const [partnerChart, setPartnerChart] = useState(null);
  const [showChartPicker, setShowChartPicker] = useState(false);
  const [selectingFor, setSelectingFor] = useState(null); // 'native' or 'partner'
  const [savedCharts, setSavedCharts] = useState([]);
  
  // Pending message management (like web app)
  const addPendingMessage = async (messageId) => {
    const key = `pendingChatMessages_${currentPersonId}`;
    const stored = await AsyncStorage.getItem(key);
    const pendingIds = stored ? JSON.parse(stored) : [];
    if (!pendingIds.includes(messageId)) {
      pendingIds.push(messageId);
      await AsyncStorage.setItem(key, JSON.stringify(pendingIds));
    }
    setPendingMessages(prev => new Set([...prev, messageId]));
  };
  
  const removePendingMessage = async (messageId) => {
    const key = `pendingChatMessages_${currentPersonId}`;
    const stored = await AsyncStorage.getItem(key);
    if (stored) {
      const pendingIds = JSON.parse(stored).filter(id => id !== messageId);
      await AsyncStorage.setItem(key, JSON.stringify(pendingIds));
    }
    setPendingMessages(prev => {
      const newSet = new Set(prev);
      newSet.delete(messageId);
      return newSet;
    });
  };
  
  const checkPendingResponses = async (personId = currentPersonId) => {
    const stored = await AsyncStorage.getItem(`pendingChatMessages_${personId}`);
    if (stored) {
      const pendingIds = JSON.parse(stored);
      pendingIds.forEach(messageId => {
        // Resume polling for each pending message
        pollForResponse(messageId, null, sessionId, '', true); // true = resume mode
      });
    }
  };
  
  // Load saved charts for partnership mode
  const loadSavedCharts = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/birth-charts')}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSavedCharts(data.charts || []);
      } else {
        setSavedCharts([]);
      }
    } catch (error) {
      console.error('Error loading saved charts:', error);
      setSavedCharts([]);
    }
  };
  
  // Load charts when component mounts
  useEffect(() => {
    loadSavedCharts();
  }, []);
  
  // Reload charts when picker opens
  useEffect(() => {
    if (showChartPicker) {
      loadSavedCharts();
    }
  }, [showChartPicker]);
  
  // Fetch calibration event when birth data changes
  useEffect(() => {
    if (birthData?.id && !showGreeting) {
      fetchCalibrationEvent();
    }
  }, [birthData?.id, showGreeting]);
  
  const fetchCalibrationEvent = async () => {
    try {
      
      // Use the proper API service instead of direct fetch
      const { lifeEventsAPI } = require('../../services/api');
      
      const response = await lifeEventsAPI.scanLifeEvents({
        name: birthData.name,
        date: birthData.date,
        time: birthData.time,
        latitude: birthData.latitude,
        longitude: birthData.longitude,
        place: birthData.place || "",
        place: birthData.place || '',
        gender: birthData.gender || ''
      }, 18, 50);
      
      if (response.data && response.data.events && response.data.events.length > 0) {
        setCalibrationEvent(response.data.events[0]);
      }
    } catch (error) {
    }
  };
  
  const handleCalibrationConfirm = async (event) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      await fetch(`${API_BASE_URL}${getEndpoint('/chat/verify-calibration')}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          birth_chart_id: birthData.id,
          event_year: event.year,
          verified: true
        })
      });
      
      setCalibrationEvent({ ...event, verified: true });
      Alert.alert('✅ Verified', 'Chart calibrated successfully!');
    } catch (error) {
      console.error('Calibration error:', error);
    }
  };
  
  const handleCalibrationReject = async (event) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      await fetch(`${API_BASE_URL}${getEndpoint('/chat/verify-calibration')}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          birth_chart_id: birthData.id,
          event_year: event.year,
          verified: false
        })
      });
      
      setCalibrationEvent(null);
    } catch (error) {
      console.error('Calibration error:', error);
    }
  };

  const getMenuOptionStyle = () => [
    styles.menuOption,
    { elevation: getCardElevation(3) }
  ];

  const suggestions = [
    "What does my birth chart say about my career?",
    "When is a good time for marriage?",
    "What are my health vulnerabilities?",
    "Tell me about my current dasha period",
    "What do the current transits mean for me?",
    "Show me significant periods in my life",
    "What are my strengths and weaknesses?"
  ];

  const getSignName = (signNumber) => {
    const signs = {
      0: 'Aries', 1: 'Taurus', 2: 'Gemini', 3: 'Cancer',
      4: 'Leo', 5: 'Virgo', 6: 'Libra', 7: 'Scorpio',
      8: 'Sagittarius', 9: 'Capricorn', 10: 'Aquarius', 11: 'Pisces'
    };
    const signName = signs[signNumber] || signNumber;
    return t(`signs.${signName}`, signName);
  };
  
  const getSignIcon = (signNumber) => {
    const icons = {
      0: '♈', 1: '♉', 2: '♊', 3: '♋',
      4: '♌', 5: '♍', 6: '♎', 7: '♏',
      8: '♐', 9: '♑', 10: '♒', 11: '♓'
    };
    return icons[signNumber] || '⭐';
  };

  const getPlanetColor = (planetName) => {
    const colors = {
      'Sun': '#ff6b35',
      'Moon': '#e0e0e0',
      'Mars': '#d32f2f',
      'Mercury': '#4caf50',
      'Jupiter': '#ffd700',
      'Venus': '#e91e63',
      'Saturn': '#2196f3',
      'Rahu': '#9e9e9e',
      'Ketu': '#795548',
    };
    return colors[planetName] || '#ffffff';
  };

  const loadChartData = async (birth) => {
    try {
      setLoadingChart(true);
      const formattedData = {
        ...birth,
        date: typeof birth.date === 'string' ? birth.date.split('T')[0] : birth.date,
        time: typeof birth.time === 'string' ? birth.time.split('T')[1]?.slice(0, 5) || birth.time : birth.time,
        latitude: parseFloat(birth.latitude),
        longitude: parseFloat(birth.longitude)
      };
      
      const { chartAPI } = require('../../services/api');
      const response = await chartAPI.calculateChartOnly(formattedData);
      setChartData(response.data);

    } catch (error) {
      console.error('Error loading chart data:', error);
      if (error.response?.status === 503) {
      }
    } finally {
      setLoadingChart(false);
    }
  };

  const loadDashaData = async (birth) => {
    try {
      setLoadingDashas(true);
      const targetDate = new Date().toISOString().split('T')[0];
      
      const formattedBirthData = {
        name: birth.name,
        date: birth.date.includes('T') ? birth.date.split('T')[0] : birth.date,
        time: birth.time.includes('T') ? new Date(birth.time).toTimeString().slice(0, 5) : birth.time,
        latitude: parseFloat(birth.latitude),
        longitude: parseFloat(birth.longitude),
        location: birth.place || 'Unknown'
      };
      
      const { chartAPI } = require('../../services/api');
      const response = await chartAPI.calculateCascadingDashas(formattedBirthData, targetDate);
      
      if (response.data && !response.data.error) {
        setDashaData(response.data);
      }
    } catch (error) {
      console.error('Error loading dasha data:', error);
      if (error.response?.status === 503) {
      }
    } finally {
      setLoadingDashas(false);
    }
  };



  useEffect(() => {
    checkBirthData();
    loadLanguagePreference();
    fetchChatCost();
    
    // Add focus listener to re-check birth data when returning to screen
    const unsubscribe = navigation.addListener('focus', () => {
      checkBirthData();
    });
    
    // Handle navigation params
    if (route.params?.resetToGreeting) {
      setShowGreeting(true);
      navigation.setParams({ resetToGreeting: undefined });
    }
    
    // Handle start chat param
    if (route.params?.startChat) {
      const initialMsg = route.params?.initialMessage;
      navigation.setParams({ startChat: undefined, initialMessage: undefined });
      
      // Use the same logic as greeting option select for question action
      handleGreetingOptionSelect({ action: 'question' });
      
      // Set initial message after a delay to ensure chat is ready
      if (initialMsg) {
        setTimeout(() => {
          setInputText(initialMsg);
        }, 500);
      }
    }
    
    // Handle mundane mode param
    if (route.params?.mode === 'mundane') {
      setIsMundane(true);
      navigation.setParams({ mode: undefined });
    }
    
    // Handle back button
    const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
      if (!showGreeting) {
        // In chat mode, show greeting screen
        setShowGreeting(true);
        return true;
      }
      return false;
    });
    
    return () => {
      unsubscribe();
      backHandler.remove();
    };
  }, [navigation, showGreeting, route.params]);

  // Remove problematic back handler that clears messages

  const fetchChatCost = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/credits/settings/chat-cost')}`);
      const data = await response.json();
      setChatCost(data.cost || 1);
      
      const premiumResponse = await fetch(`${API_BASE_URL}${getEndpoint('/credits/settings/premium-chat-cost')}`);
      const premiumData = await premiumResponse.json();
      setPremiumChatCost(premiumData.cost || 3);
    } catch (error) {
      console.error('Error fetching chat cost:', error);
    }
  };

  useEffect(() => {
    
    if (birthData) {
      // Create unique person ID from birth data
      const personId = `${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}`;
      
      // Check if person changed
      if (currentPersonId && currentPersonId !== personId) {
        // Different person selected - clear current state
        setMessages([]);
        setSessionId(null);
        setShowGreeting(true);
      }
      
      // Only update if person ID actually changed
      if (currentPersonId !== personId) {
        
        // Set person ID first to avoid null issues
        setCurrentPersonId(personId);
        
        // Load chart data for the new person
        setChartData(null); // Clear cached data
        loadChartData(birthData);
        loadDashaData(birthData);
        
        // Load messages from storage immediately
        loadMessagesFromStorage(personId).then(storedMessages => {
          if (storedMessages.length > 0) {
            setMessages(storedMessages);
            // Only auto-switch to chat if not app startup
            if (!isAppStartup && messages.length === 0) {
              setShowGreeting(false);
            }
            
            // Set flag to auto-scroll when content renders
            setTimeout(() => {
              if (messages.length > 0) {
                lastMessageRef.current?.measureLayout(
                  scrollViewRef.current,
                  (x, y) => {
                    scrollViewRef.current?.scrollTo({ y: y, animated: false });
                  },
                  () => {}
                );
              }
            }, 50);
            
            // Check for processing messages and resume polling
            // const processingMessage = storedMessages.find(msg => msg.isTyping && msg.messageId);
            // if (processingMessage) {
            //   setLoading(true);
            //   setIsTyping(true);
            //   // Use personId directly to avoid timing issues
            //   setTimeout(() => {
            //     const userMessage = storedMessages.filter(m => m.role === 'user').pop();
            //     pollForResponse(processingMessage.messageId, null, sessionId, userMessage?.content || '', true);
            //   }, 100);
            // }
          } else {
            setShowGreeting(true);
          }
          // Reset force greeting and app startup after handling
          if (forceGreeting) {
            setTimeout(() => setForceGreeting(false), 100);
          }
          // Clear app startup flag after first load
          if (isAppStartup) {
            setTimeout(() => setIsAppStartup(false), 500);
          }
        });
        
        // Check pending responses after person ID is set
        setTimeout(() => {
          checkPendingResponses(personId);
        }, 200);
      }
    } else {
    }
  }, [birthData]);

  // Save messages to AsyncStorage per person (like web app)
  const saveMessagesToStorage = async (messages, personId = currentPersonId) => {
    if (!personId) return;
    try {
      await AsyncStorage.setItem(`chatMessages_${personId}`, JSON.stringify(messages));
    } catch (error) {
      console.error('Error saving messages:', error);
    }
  };

  // Load messages from AsyncStorage per person (like web app)
  const loadMessagesFromStorage = async (personId = currentPersonId) => {
    if (!personId) return [];
    try {
      const stored = await AsyncStorage.getItem(`chatMessages_${personId}`);
      if (stored) {
        const messages = JSON.parse(stored);
        return messages;
      }
    } catch (error) {
      console.error('Error loading messages from storage:', error);
    }
    return [];
  };

  // Override setMessages to also save to storage
  const setMessagesWithStorage = (messagesOrUpdater) => {
    setMessages(prev => {
      const newMessages = typeof messagesOrUpdater === 'function' ? messagesOrUpdater(prev) : messagesOrUpdater;
      // Get current person ID from birthData if currentPersonId is null
      const personId = currentPersonId || (birthData ? `${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}` : null);
      // Save to storage
      if (personId) {
        saveMessagesToStorage(newMessages, personId);
      }
      return newMessages;
    });
  };

  // Load messages when screen focuses - but don't interfere with ongoing polling
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      if (currentPersonId) {
        loadMessagesFromStorage(currentPersonId).then(storedMessages => {
          if (storedMessages.length > 0) {
            // Only update messages if we don't have any current messages to avoid overwriting
            const prevLength = messages.length;
            setMessages(prev => prev.length === 0 ? storedMessages : prev);
            // Don't auto-switch if app startup or we already have messages loaded
            if (!isAppStartup && messages.length === 0) {
              setShowGreeting(false);
            }
            
            // Set flag to scroll if we loaded new messages and not showing greeting
            if (prevLength === 0 && storedMessages.length > 0 && !showGreeting) {
              setTimeout(() => {
                if (storedMessages.length > 0) {
                  lastMessageRef.current?.measureLayout(
                    scrollViewRef.current,
                    (x, y) => {
                      scrollViewRef.current?.scrollTo({ y: y, animated: false });
                    },
                    () => {}
                  );
                }
              }, 50);
            }
            
            // Only resume polling if not already polling
            // if (!loading && !isTyping) {
            //   const processingMessage = storedMessages.find(msg => msg.isTyping && msg.messageId);
            //   if (processingMessage) {
            //     setLoading(true);
            //     setIsTyping(true);
            //     const userMessage = storedMessages.filter(m => m.role === 'user').pop();
            //     pollForResponse(processingMessage.messageId, null, sessionId, userMessage?.content || '', true);
            //   }
            // }
          }
        });
      }
    });
    
    return unsubscribe;
  }, [currentPersonId, loading, isTyping, showGreeting]);

  const handleGreetingOptionSelect = async (option) => {
    
    if (option.action === 'partnership') {
      Alert.alert(
        'Partnership Mode',
        `Partnership mode uses ${partnershipCost} credits per question for comprehensive compatibility analysis. Continue?`,
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Continue', 
            onPress: () => {
              setPartnershipMode(true);
              setNativeChart(birthData);
              setShowGreeting(false);
              setShowChartPicker(true);
            }
          }
        ]
      );
    } else if (option.action === 'mundane') {
      setIsMundane(true);
      setShowGreeting(false);
      const welcomeMsg = {
        id: Date.now().toString(),
        content: `🌍 Welcome to Global Markets & Events Analysis!\n\nI can help you understand:\n\n• Economic trends and market movements\n• Political developments and elections\n• Natural events and their timing\n• Country-specific forecasts\n• Global financial markets\n\nSelect a country and year, then ask your question.`,
        role: 'assistant',
        timestamp: new Date().toISOString(),
      };
      setMessagesWithStorage([welcomeMsg]);
    } else if (option.action === 'periods') {
      setShowEventPeriods(true);
    } else if (option.action === 'events') {
      navigation.navigate('EventScreen');
    } else if (option.action === 'ashtakvarga') {
      navigation.navigate('AshtakvargaOracle');
    } else if (option.action === 'muhurat') {
      navigation.navigate('MuhuratHub');
    } else if (option.action === 'numerology') {
      navigation.navigate('Numerology');
    } else if (option.action === 'analysis') {
      if (option.type === 'trading') {
        navigation.navigate('TradingDashboard');
      } else if (option.type === 'financial') {
        navigation.navigate('FinancialDashboard');
      } else if (option.type === 'childbirth') {
        navigation.navigate('ChildbirthPlanner');
      } else {
        navigation.navigate('AnalysisDetail', { 
          analysisType: option.type,
          title: `${option.type.charAt(0).toUpperCase() + option.type.slice(1)} Analysis`,
          cost: 5
        });
      }
    } else {
      
      // First load any existing chat history
      await loadChatHistory();
      
      // Switch to chat mode immediately
      setShowGreeting(false);
      
      // Set flag to scroll when content renders
      setTimeout(() => {
        if (messages.length > 0) {
          lastMessageRef.current?.measureLayout(
            scrollViewRef.current,
            (x, y) => {
              scrollViewRef.current?.scrollTo({ y: y, animated: false });
            },
            () => {}
          );
        }
      }, 50);
      
      // Check if we need to show welcome message
      setTimeout(async () => {
        
        const storedMessages = await loadMessagesFromStorage(currentPersonId);
        
        // Always show fresh welcome message when explicitly starting chat
        const nativeName = birthData?.name || 'there';
        
        const welcomeMessage = {
          id: Date.now().toString(),
          content: t('chat.welcomeMessage', "🌟 Welcome {{name}}! I'm here to help you understand your birth chart and provide astrological insights.\n\nFeel free to ask me anything about:\n\n• Personality traits and characteristics\n• Career and professional guidance\n• Relationships and compatibility\n• Health and wellness insights\n• Timing for important decisions\n• Current planetary transits\n• Strengths and areas for growth\n\nWhat would you like to explore first?", { name: nativeName }),
          role: 'assistant',
          timestamp: new Date().toISOString(),
        };
        
        // If no stored messages, show welcome. If stored messages exist, prepend welcome if it's not already there
        if (storedMessages.length === 0) {
          setMessagesWithStorage([welcomeMessage]);
        } else {
          // Check if first message is already a welcome message
          const firstMessage = storedMessages[0];
          if (!firstMessage.content.includes('Welcome')) {
            setMessagesWithStorage([welcomeMessage, ...storedMessages]);
          } else {
            // Replace old welcome with new personalized one
            const updatedMessages = [welcomeMessage, ...storedMessages.slice(1)];
            setMessagesWithStorage(updatedMessages);
          }
        }
      }, 100);
    }
  };

  const checkBirthData = async () => {
    try {
      // First try to get single birth details
      let selectedBirthData = await storage.getBirthDetails();
      
      // If no single birth details, get from profiles
      if (!selectedBirthData) {
        const profiles = await storage.getBirthProfiles();
        
        if (profiles && profiles.length > 0) {
          // Use the first profile or find 'self' relation
          selectedBirthData = profiles.find(p => p.relation === 'self') || profiles[0];
        }
      }
      
      if (selectedBirthData && selectedBirthData.name) {
        setBirthData(selectedBirthData);
      } else {
        // Check if charts exist on server
        try {
          const { chartAPI } = require('../../services/api');
          const response = await chartAPI.getExistingCharts();
          if (response.data && response.data.charts && response.data.charts.length > 0) {
            navigation.navigate('SelectNative');
          } else {
            navigation.navigate('BirthForm');
          }
        } catch (apiError) {
          navigation.navigate('BirthForm');
        }
        setBirthData(null);
      }
    } catch (error) {
      console.error('❌ Error checking birth data:', error);
      setBirthData(null);
      navigation.navigate('BirthForm');
    }
  };

  const loadChatHistory = async () => {
  };

  const loadLanguagePreference = async () => {
    const savedLanguage = await storage.getLanguage();
    if (savedLanguage) {
      setLanguage(savedLanguage);
    }
  };

  const createSession = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      
      // Different endpoint for mundane vs personal
      const endpoint = isMundane ? '/mundane/session' : '/chat-v2/session';
      const body = isMundane ? {} : { birth_chart_id: birthData?.id };
      
      if (!isMundane && !birthData?.id) {
        return null;
      }
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint(endpoint)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      });
      
      if (response.ok) {
        const data = await response.json();
        const newSessionId = data.session_id;
        setSessionId(newSessionId);
        
        if (!isMundane) {
          // Track session for personal chat only
          const currentBirthHash = `${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}`;
          const personSessions = JSON.parse(await AsyncStorage.getItem(`chatSessions_${currentBirthHash}`) || '[]');
          personSessions.push(newSessionId);
          await AsyncStorage.setItem(`chatSessions_${currentBirthHash}`, JSON.stringify(personSessions));
        }
        
        return newSessionId;
      }
    } catch (error) {
      console.error('Error creating session:', error);
    }
    return null;
  };

  const saveMessageToHistory = async (message, sessionId) => {
    // This is handled by the backend when processing messages
    // No need to save manually in mobile app
    return;
  };


  const getLoadingMessages = (messageText) => {
    const lowerCaseMessage = messageText.toLowerCase();
    
    // Keywords for different categories
    const careerKeywords = ['career', 'job', 'profession', 'work', 'employment'];
    const marriageKeywords = ['marriage', 'spouse', 'partner', 'relationship', 'love'];
    const healthKeywords = ['health', 'illness', 'disease', 'wellness'];
    const financeKeywords = ['finance', 'money', 'wealth', 'investment'];
    const spiritualKeywords = ['spiritual', 'soul', 'karma', 'purpose'];

    if (careerKeywords.some(keyword => lowerCaseMessage.includes(keyword))) {
      return [
        '💼 Analyzing career prospects in your chart...',
        '🏢 Evaluating professional strengths and weaknesses...',
        '📈 Identifying key periods for career growth...',
        '🌟 Uncovering hidden talents and opportunities...',
        '🎯 Aligning your career with your life purpose...',
        '☀️ Predicting potential challenges in your professional life...',
        '✨ Providing guidance for career advancement...',
        'Congratulations on taking this important step in your career exploration! I am now examining the intricate details of your birth chart to provide you with the most accurate and personalized insights available.',
        'I am analyzing the placement of Saturn, the planet of career and responsibility, in your birth chart. This will help me understand your professional potential and challenges.',
        'I am also looking at the 10th house, which represents your career and public life. This will give me a better understanding of your professional path.',
        'Your birth chart is a unique cosmic blueprint that holds valuable information about your career. I am now decoding this information to provide you with a detailed analysis of your professional life.',
        'I am examining the placement of Jupiter, the planet of expansion and opportunities, in your birth chart. This will help me identify potential career opportunities for you.',
        'I am also looking at the 6th house, which represents your daily work and service. This will give me a better understanding of your work environment and professional relationships.',
      ];
    }
    if (marriageKeywords.some(keyword => lowerCaseMessage.includes(keyword))) {
      return [
        '💍 Assessing marital compatibility and timing...',
        '❤️ Exploring romantic connections in your chart...',
        '💑 Understanding partnership dynamics...',
        '☀️ Predicting potential challenges in your married life...',
        '✨ Providing guidance for a harmonious relationship...',
        'Now, I am delving into the complexities of your birth chart to provide you with a comprehensive analysis of your marital prospects. This is an important step in understanding your future, and I am committed to providing you with the most accurate and personalized insights available.',
        'I am analyzing the placement of Venus, the planet of love and relationships, in your birth chart. This will help me understand your romantic potential and challenges.',
        'I am also looking at the 7th house, which represents your marriage and partnerships. This will give me a better understanding of your marital path.',
        'Your birth chart is a unique cosmic blueprint that holds valuable information about your relationships. I am now decoding this information to provide you with a detailed analysis of your marital life.',
        'I am examining the placement of Jupiter, the planet of expansion and opportunities, in your birth chart. This will help me identify potential marital opportunities for you.',
      ];
    }
    if (healthKeywords.some(keyword => lowerCaseMessage.includes(keyword))) {
      return [
        '⚕️ Examining health indicators and vulnerabilities...',
        '🌿 Looking into planetary influences on your well-being...',
        '🏃‍♂️ Identifying periods for focusing on health...',
        'Congratulations on taking this important step in understanding your health from an astrological perspective. I am now examining the intricate details of your birth chart to provide you with the most accurate and personalized insights available.',
        'I am analyzing the placement of Mars, the planet of energy and vitality, in your birth chart. This will help me understand your physical potential and challenges.',
        'I am also looking at the 6th house, which represents your health and daily routines. This will give me a better understanding of your health path.',
        'Your birth chart is a unique cosmic blueprint that holds valuable information about your health. I am now decoding this information to provide you with a detailed analysis of your physical well-being.',
        'I am examining the placement of Saturn, the planet of limitations and discipline, in your birth chart. This will help me identify potential health challenges for you.',
      ];
    }
    if (financeKeywords.some(keyword => lowerCaseMessage.includes(keyword))) {
        return [
            '💰 Scrutinizing financial planets and houses...',
            '🏦 Identifying opportunities for wealth creation...',
            '💸 Analyzing potential for financial challenges...',
            'Congratulations on taking this important step in understanding your financial situation from an astrological perspective. I am now examining the intricate details of your birth chart to provide you with the most accurate and personalized insights available.',
            'I am analyzing the placement of Jupiter, the planet of expansion and opportunities, in your birth chart. This will help me identify potential financial opportunities for you.',
            'I am also looking at the 2nd house, which represents your wealth and possessions. This will give me a better understanding of your financial path.',
            'Your birth chart is a unique cosmic blueprint that holds valuable information about your finances. I am now decoding this information to provide you with a detailed analysis of your financial situation.',
            'I am examining the placement of Saturn, the planet of limitations and discipline, in your birth chart. This will help me identify potential financial challenges for you.',
        ];
    }
    if (spiritualKeywords.some(keyword => lowerCaseMessage.includes(keyword))) {
        return [
            '🧘‍♀️ Exploring your spiritual path and purpose...',
            '🕉️ Examining karmic influences and lessons...',
            '✨ Delving into your soul\'s journey...',
            'Congratulations on taking this important step in understanding your spiritual path from an astrological perspective. I am now examining the intricate details of your birth chart to provide you with the most accurate and personalized insights available.',
            'I am analyzing the placement of Neptune, the planet of spirituality and intuition, in your birth chart. This will help me understand your spiritual potential and challenges.',
            'I am also looking at the 12th house, which represents your subconscious and spiritual life. This will give me a better understanding of your spiritual path.',
            'Your birth chart is a unique cosmic blueprint that holds valuable information about your spirituality. I am now decoding this information to provide you with a detailed analysis of your spiritual journey.',
        ];
    }
    
    // Default messages
    return [
      '☀️ Analyzing your birth chart...',
      '⭐ Consulting the cosmic energies...',
      '📊 Calculating planetary positions...',
      '🌟 Interpreting astrological patterns...',
      '✨ Preparing your personalized insights...'
    ];
  };

  const pollForResponse = async (messageId, processingMessageId, currentSessionId, userQuestion = '', isResume = false) => {
    if (!messageId) {
      return;
    }
    
    const maxPolls = 120; // 4 minutes max
    let pollCount = 0;
    
    // Add to pending messages if not resuming
    if (!isResume) {
      await addPendingMessage(messageId);
    }
    
    const poll = async () => {
      const pollStartTime = new Date().toISOString();
      // console.log(`🔍 [POLL START] messageId: ${messageId}, pollCount: ${pollCount}, time: ${pollStartTime}`);
      
      try {
        const token = await AsyncStorage.getItem('authToken');
        const url = `${API_BASE_URL}${getEndpoint(`/chat-v2/status/${messageId}`)}`;
        
        // console.log(`🌐 [FETCH START] URL: ${url}, time: ${new Date().toISOString()}`);
        
        // Add timeout to prevent long-hanging requests
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
          // console.log(`⏰ [FETCH TIMEOUT] Aborting request for messageId: ${messageId} after 5 seconds`);
          controller.abort();
        }, 5000); // 5 second timeout
        
        const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${token}` },
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        // console.log(`📡 [FETCH END] Response received for messageId: ${messageId}, status: ${response.status}, time: ${new Date().toISOString()}`);
        
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const status = await response.json();
        const pollEndTime = new Date().toISOString();
        // console.log(`📊 [POLL END] messageId: ${messageId}, status: ${status.status}, pollCount: ${pollCount}, startTime: ${pollStartTime}, endTime: ${pollEndTime}`);
        
        if (status.status === 'completed') {

          const showFinalMessage = () => {
            setMessagesWithStorage(prev => {
              const updated = prev.map(msg => 
                msg.messageId === messageId 
                  ? { 
                      ...msg, 
                      content: status.content || 'Response received but content is empty', 
                      isTyping: false,
                      terms: status.terms || [],
                      glossary: status.glossary || {},
                      message_type: status.message_type || 'answer',
                      summary_image: status.summary_image || null,
                      follow_up_questions: status.follow_up_questions || []
                    }
                  : msg
              );
              return updated;
            });
            setLoading(false);
            setIsTyping(false);
            removePendingMessage(messageId);
            fetchBalance();
          };

          const analysisSteps = status.analysis_steps || [];
          if (analysisSteps.length > 0) {
            let stepIndex = 0;
            const stepInterval = setInterval(() => {
              if (stepIndex < analysisSteps.length) {
                const stepMessage = `⚙️ ${analysisSteps[stepIndex]}...`;
                setMessagesWithStorage(prev => prev.map(msg => 
                  msg.messageId === messageId ? { ...msg, content: stepMessage } : msg
                ));
                stepIndex++;
              } else {
                clearInterval(stepInterval);
                showFinalMessage();
              }
            }, 1500);
          } else {
            showFinalMessage();
          }
          
          return;
        }
        
        if (status.status === 'failed') {
          setMessagesWithStorage(prev => prev.map(msg => 
            msg.messageId === messageId 
              ? { ...msg, content: status.error_message || 'Analysis failed. Please try again.', isTyping: false }
              : msg
          ));
          setLoading(false);
          setIsTyping(false);
          await removePendingMessage(messageId);
          return;
        }
        
        // Still processing - continue polling
        if (status.status === 'processing') {
          // Check for and set dynamic loading messages once
          if (status.loading_messages && status.loading_messages.length > 0) {
            setDynamicLoadingMessages(status.loading_messages);
          }

          console.log(`🔄 [POLL PROCESSING] messageId: ${messageId}, pollCount: ${pollCount}, continuing...`);
          
          pollCount++;
          if (pollCount < maxPolls) {
            // Use InteractionManager to ensure polling isn't blocked by UI updates
            const nextPollTime = new Date(Date.now() + 1500).toISOString();
            console.log(`⏰ [POLL SCHEDULE] Next poll for messageId: ${messageId} scheduled at: ${nextPollTime}`);
            setTimeout(() => {
              // console.log(`🔄 [POLL RETRY] messageId: ${messageId}, pollCount: ${pollCount}`);
              poll();
            }, 1500);
          } else {
            // console.log(`⏰ [POLL TIMEOUT] messageId: ${messageId} reached max polls (${maxPolls})`);
            // Timeout - show restart option
            setMessagesWithStorage(prev => prev.map(msg => 
              msg.messageId === messageId 
                ? { 
                    ...msg, 
                    content: 'Analysis is taking longer than expected. The system is still working on your request.', 
                    isTyping: false,
                    showRestartButton: true
                  }
                : msg
            ));
            setLoading(false);
            setIsTyping(false);
            // Keep in pending messages for later resume
          }
        }
        
      } catch (error) {
        console.error('❌ Polling error:', error);
        
        // Show user-friendly error message based on error type
        let userMessage = 'I apologize, but I\'m having trouble processing your request right now. Please try again in a moment.';
        
        // Handle specific error types
        if (error.name === 'AbortError') {
          // console.log(`⏰ [POLL TIMEOUT] Fetch timeout for messageId: ${messageId}, pollCount: ${pollCount}`);
          // Don't show error for timeout, just continue polling
          pollCount++;
          if (pollCount < maxPolls) {
            const nextPollTime = new Date(Date.now() + 1000).toISOString();
            // console.log(`🔄 [POLL RETRY AFTER TIMEOUT] Next poll for messageId: ${messageId} scheduled at: ${nextPollTime}`);
            setTimeout(() => {
              // console.log(`🔄 [POLL RETRY] messageId: ${messageId}, pollCount: ${pollCount}`);
              poll();
            }, 1000);
          } else {
            // console.log(`⏰ [POLL MAX TIMEOUT] messageId: ${messageId} reached max polls (${maxPolls})`);
            // Show timeout message
            setMessagesWithStorage(prev => prev.map(msg => 
              msg.messageId === messageId 
                ? { 
                    ...msg, 
                    content: 'Analysis is taking longer than expected. The system is still working on your request.', 
                    isTyping: false,
                    showRestartButton: true
                  }
                : msg
            ));
            setLoading(false);
            setIsTyping(false);
          }
          return;
        }
        
        setMessagesWithStorage(prev => prev.map(msg => 
          msg.messageId === messageId 
            ? { ...msg, content: userMessage, isTyping: false }
            : msg
        ));
        setLoading(false);
        setIsTyping(false);
        await removePendingMessage(messageId);
      }
    };
    
    // Start polling immediately (no delay)
    poll();
  };
  
  const restartPolling = (messageId) => {
    // Update message to show restarting
    setMessagesWithStorage(prev => prev.map(msg => 
      msg.messageId === messageId 
        ? { ...msg, content: '🔄 Checking for response...', isTyping: true, showRestartButton: false }
        : msg
    ));
    setLoading(true);
    
    // Restart polling (resume mode)
    const processingMessage = messages.find(msg => msg.messageId === messageId);
    const userMessage = messages.find(msg => msg.id === processingMessage?.userMessageId);
    pollForResponse(messageId, null, sessionId, userMessage?.content || '', true);
  };

  const sendMessage = async (messageText = inputText) => {
    if (!messageText.trim() || !birthData) {
      return;
    }

    // Reset dynamic messages for the new question
    setDynamicLoadingMessages(null);

    // Clear input and set states immediately
    setInputText('');
    setLoading(true);
    setIsTyping(true);
    setShowGreeting(false);
    
    // Remove test message code

    // Add user message immediately
    const userMessageId = Date.now().toString();
    const userMessage = {
      id: userMessageId,
      content: messageText,
      role: 'user',
      timestamp: new Date().toISOString(),
    };
    
    // Track chat message sent event
    trackAstrologyEvent.chatMessageSent('user_question');
    
    setMessagesWithStorage(prev => {
      const newMessages = [...prev, userMessage];
      return newMessages;
    });

    const loadingMessages = getLoadingMessages(messageText);

    // Add processing message immediately
    const processingMessageId = Date.now() + '_processing';
    const processingMessage = {
      id: processingMessageId,
      content: '', // Content is now handled by LoadingBubble
      role: 'assistant',
      timestamp: new Date().toISOString(),
      isTyping: true,
      userMessageId: userMessageId,
    };
    
    setMessagesWithStorage(prev => {
      const newMessages = [...prev, processingMessage];
      return newMessages;
    });

    // Scroll to bottom
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);

    // Create session if needed
    let currentSessionId = sessionId;
    if (!currentSessionId) {
      currentSessionId = await createSession();
      if (!currentSessionId) {
        setLoading(false);
        return;
      }
    }

    try {
      const token = await AsyncStorage.getItem('authToken');
      
      // Mundane mode - async with polling
      if (isMundane) {
        const mundaneBody = {
          session_id: currentSessionId,
          country: selectedCountry.name,
          year: selectedYear,
          latitude: selectedCountry.lat,
          longitude: selectedCountry.lng,
          question: messageText
        };
        
        const response = await fetch(`${API_BASE_URL}${getEndpoint('/mundane/analyze')}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(mundaneBody)
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('❌ API Error Response:', errorText);
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const result = await response.json();
        const messageId = result.message_id;
        
        if (!messageId) {
          throw new Error('No message ID received from server');
        }
        
        // Update processing message with messageId
        setMessagesWithStorage(prev => prev.map(msg => 
          msg.id === processingMessageId ? { ...msg, messageId } : msg
        ));
        
        // Start polling
        pollForResponse(messageId, processingMessageId, currentSessionId, messageText);
        return;
      }
      
      // Partnership mode validation
      if (partnershipMode && (!nativeChart || !partnerChart)) {
        Alert.alert('Error', 'Please select both charts for partnership analysis');
        setMessagesWithStorage(prev => prev.filter(msg => msg.id !== processingMessageId));
        setLoading(false);
        setIsTyping(false);
        return;
      }
      
      const requestBody = {
        session_id: currentSessionId,
        question: messageText,
        language: language || 'english',
        response_style: 'detailed',
        premium_analysis: isPremiumAnalysis,
        native_name: partnershipMode ? nativeChart?.name : birthData?.name,
        birth_details: partnershipMode ? {
          name: nativeChart.name,
          date: typeof nativeChart.date === 'string' ? nativeChart.date.split('T')[0] : nativeChart.date,
          time: typeof nativeChart.time === 'string' ? nativeChart.time.split('T')[1]?.slice(0, 5) || nativeChart.time : nativeChart.time,
          latitude: parseFloat(nativeChart.latitude),
          longitude: parseFloat(nativeChart.longitude),
          place: nativeChart.place || '',
          gender: nativeChart.gender || ''
        } : {
          name: birthData.name,
          date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
          time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
          latitude: parseFloat(birthData.latitude),
          longitude: parseFloat(birthData.longitude),
          place: birthData.place || '',
          gender: birthData.gender || ''
        },
        // Partnership mode fields
        partnership_mode: partnershipMode,
        ...(partnershipMode && partnerChart && {
          partner_name: partnerChart.name,
          partner_date: typeof partnerChart.date === 'string' ? partnerChart.date.split('T')[0] : partnerChart.date,
          partner_time: typeof partnerChart.time === 'string' ? partnerChart.time.split('T')[1]?.slice(0, 5) || partnerChart.time : partnerChart.time,
          partner_place: partnerChart.place || '',
          partner_latitude: parseFloat(partnerChart.latitude),
          partner_longitude: parseFloat(partnerChart.longitude),
          partner_gender: partnerChart.gender || ''
        })
      };
      

      
      console.log(`🚀 [API CALL] Sending request to /chat-v2/ask at: ${new Date().toISOString()}`);
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat-v2/ask')}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      });

      console.log(`📡 [API RESPONSE] Received response at: ${new Date().toISOString()}, status: ${response.status}`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      const { user_message_id, message_id: assistantMessageId, loading_messages, chart_insights } = result;

      console.log(`📦 [RESULT] Got messageId: ${assistantMessageId} at: ${new Date().toISOString()}`);
      console.log(`📊 [LOADING MESSAGES] Received ${loading_messages?.length || 0} dynamic messages from backend`);
      console.log(`🏠 [CHART INSIGHTS] Received ${chart_insights?.length || 0} chart insights from backend`);

      if (!assistantMessageId) {
        throw new Error('No message ID received from server');
      }

      // Use dynamic loading messages from backend if available
      if (loading_messages && loading_messages.length > 0) {
        setDynamicLoadingMessages(loading_messages);
      }

      console.log(`🚀 [POLLING START] Starting polling for messageId: ${assistantMessageId} at: ${new Date().toISOString()}`);
      
      // Start polling IMMEDIATELY before state updates to avoid delay
      pollForResponse(assistantMessageId, processingMessageId, currentSessionId, messageText);

      // Update user message with real DB ID (async, non-blocking)
      if (user_message_id) {
        setMessagesWithStorage(prev => {
          const updated = prev.map(msg => {
            if (msg.id === userMessageId) {
              const updatedMsg = { ...msg, messageId: user_message_id };
              return updatedMsg;
            }
            return msg;
          });
          return updated;
        });
      }

      // Update processing message with messageId and chart insights
      setMessagesWithStorage(prev => {
        const updated = prev.map(msg => {
          if (msg.id === processingMessageId) {
            const updatedMsg = { ...msg, messageId: assistantMessageId, chartInsights: chart_insights };
            return updatedMsg;
          }
          return msg;
        });
        return updated;
      });

    } catch (error) {
      console.error('❌ Error sending message:', error);
      
      // Log error to backend for developer monitoring
      try {
        const { chatErrorAPI } = require('../../services/api');
        await chatErrorAPI.logError(
          error.name || 'ChatError',
          error.message || 'Unknown error',
          messageText,
          error.stack
        );
      } catch (logError) {
        console.error('Failed to log error:', logError);
      }
      
      // Show user-friendly error message based on error type
      let userMessage = 'I apologize, but I\'m having trouble processing your request right now. Please try again in a moment.';
      
      // Check for specific error patterns
      if (error.message?.includes('DeadlineExceeded') || error.message?.includes('504') || error.message?.includes('timeout')) {
        userMessage = 'Your question is quite complex and is taking longer than usual to analyze. Please try asking a more specific question or try again later.';
      } else if (error.message?.includes('Network') || error.message?.includes('fetch')) {
        userMessage = 'I\'m having trouble connecting right now. Please check your internet connection and try again.';
      } else if (error.message?.includes('HTTP 500')) {
        userMessage = 'I\'m experiencing some technical difficulties. Please try again in a few moments.';
      }
      
      // Replace processing message with error
      setMessagesWithStorage(prev => prev.map(msg => 
        msg.id === processingMessageId 
          ? { ...msg, content: userMessage, isTyping: false }
          : msg
      ));
      setLoading(false);
      setIsTyping(false);
    }
  };

  const handleLanguageChange = async (newLanguage) => {
    i18n.changeLanguage(newLanguage);
    setLanguage(newLanguage);
    await storage.setLanguage(newLanguage);
    setShowLanguageModal(false);
  };

  const shareChat = async () => {
    try {
      const chatText = messages
        .map(msg => `${msg.role === 'user' ? 'You' : 'AstroRoshni'}: ${msg.content}`)
        .join('\n\n');
      
      await Share.share({
        message: `☀️ AstroRoshni Chat\n\n${chatText}\n\nShared from AstroRoshni App`,
      });
    } catch (error) {
      console.error('Error sharing chat:', error);
    }
  };

  const clearChat = () => {
    Alert.alert(
      'Clear Chat',
      'Are you sure you want to clear all messages?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: () => setMessages([]),
        },
      ]
    );
  };

  const logout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await storage.clearAll();
            navigation.navigate('Login');
          },
        },
      ]
    );
  };

  const handleDeleteMessage = async (messageId) => {
    // Find the message to determine if it's a user message or assistant message
    const message = messages.find(msg => msg.messageId === messageId || msg.message_id === messageId);
    
    if (!message) {
      return;
    }
    
    // Get the actual messageId (handle both camelCase and snake_case)
    const actualMessageId = message.messageId || message.message_id;
    
    if (!actualMessageId) {
      // If no messageId, it's a local-only message, just remove from local state
      setMessagesWithStorage(prev => prev.filter(msg => msg.id !== message.id));
      return;
    }
    
    // If it's a user message (role === 'user'), just remove from local state
    if (message.role === 'user' || message.sender === 'user') {
      setMessagesWithStorage(prev => prev.filter(msg => 
        (msg.messageId !== actualMessageId && msg.message_id !== actualMessageId)
      ));
      return;
    }
    
    // If it's an assistant message, call the API to delete from server
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}${getEndpoint(`/chat-v2/message/${actualMessageId}`)}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        // Remove from local state after successful server deletion
        setMessagesWithStorage(prev => prev.filter(msg => 
          (msg.messageId !== actualMessageId && msg.message_id !== actualMessageId)
        ));
      } else if (response.status === 404) {
        // Message not found in database, remove from local state anyway
        setMessagesWithStorage(prev => prev.filter(msg => 
          (msg.messageId !== actualMessageId && msg.message_id !== actualMessageId)
        ));
      } else {
        Alert.alert('❌ Error', 'Failed to delete message from server');
      }
    } catch (error) {
      console.error('Error deleting message:', error);
      Alert.alert('❌ Error', 'Failed to delete message');
    }
  };

  const renderMessage = ({ item }) => (
    <MessageBubble message={item} language={language} />
  );

  const renderSuggestion = ({ item }) => (
    <TouchableOpacity
      style={styles.suggestionButton}
      onPress={() => setInputText(item)}
    >
      <Text style={[styles.suggestionText, { color: colors.text }]}>{item}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
      <LinearGradient colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.primary] : [colors.gradientStart, colors.gradientStart, colors.gradientStart, colors.gradientStart]} style={styles.gradientBg}>
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView 
          style={styles.keyboardAvoidingView}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={0}
        >
        {/* Header */}
        <View style={styles.headerContainer}>
          <LinearGradient
            colors={theme === 'dark' 
              ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']
              : ['rgba(249, 115, 22, 0.15)', 'rgba(249, 115, 22, 0.05)']}
            style={[
              styles.header,
              {
                borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.2)',
                elevation: getCardElevation(3),
              }
            ]}
          >
            {!showGreeting && (
              <TouchableOpacity
                style={[styles.backButton, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(249, 115, 22, 0.25)' }]}
                onPress={() => {
                  setShowGreeting(true);
                  if (isMundane) setIsMundane(false);
                }}
              >
                <Ionicons name="arrow-back" size={20} color={colors.text} />
              </TouchableOpacity>
            )}
            
            <View style={styles.headerCenter}>
              {showGreeting ? (
                <>
                  <Text style={[styles.headerTitle, { color: colors.text }]}>🌟 AstroRoshni</Text>
                  {birthData && (
                    <NativeSelectorChip 
                      birthData={birthData}
                      onPress={() => navigation.navigate('SelectNative')}
                      maxLength={7}
                    />
                  )}
                </>
              ) : isMundane ? (
                <View style={styles.partnershipChipsContainer}>
                  <TouchableOpacity 
                    onPress={() => setShowCountryPicker(true)} 
                    style={[styles.nameChip, styles.compactChip]}
                  >
                    <Text style={[styles.compactChipText, { color: colors.textSecondary }]}>
                      {selectedCountry.name}
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    onPress={() => setShowYearPicker(true)} 
                    style={[styles.nameChip, styles.compactChip]}
                  >
                    <Text style={[styles.compactChipText, { color: colors.textSecondary }]}>
                      {selectedYear}
                    </Text>
                  </TouchableOpacity>
                </View>
              ) : !partnershipMode ? (
                <>
                  <Text style={[styles.headerTitle, { color: colors.text }]}>Chat</Text>
                  {birthData && (
                    <NativeSelectorChip 
                      birthData={birthData}
                      onPress={() => navigation.navigate('SelectNative')}
                      maxLength={7}
                    />
                  )}
                </>
              ) : (
                <View style={styles.partnershipChipsContainer}>
                  <TouchableOpacity 
                    onPress={() => {
                      setSelectingFor('native');
                      setShowChartPicker(true);
                    }} 
                    style={[styles.nameChip, styles.nativeChip, styles.compactChip]}
                  >
                    <Text style={styles.compactChipText}>
                      {nativeChart?.name?.slice(0, 6) || 'Native'}{nativeChart?.name?.length > 6 ? '..' : ''}
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    onPress={() => {
                      setSelectingFor('partner');
                      setShowChartPicker(true);
                    }} 
                    style={[styles.nameChip, styles.partnerChip, styles.compactChip]}
                  >
                    <Text style={styles.compactChipText}>
                      {partnerChart?.name?.slice(0, 6) || 'Partner'}{partnerChart?.name?.length > 6 ? '..' : ''}
                    </Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
            
            <View style={styles.headerRight}>
              <TouchableOpacity
                style={[styles.creditButton, isPremiumAnalysis && styles.creditButtonPremium]}
                onPress={() => navigation.navigate('Credits')}
              >
                <Text style={[styles.creditText, { color: colors.text }]}>
                  {isPremiumAnalysis ? '⚡' : '💳'} {credits}
                </Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={styles.menuButton}
                onPress={() => {
                  setShowMenu(true);
                  Animated.spring(drawerAnim, {
                    toValue: 0,
                    useNativeDriver: true,
                    tension: 65,
                    friction: 11,
                  }).start(() => {
                    setTimeout(() => {
                      menuScrollViewRef.current?.scrollTo({ y: 0, animated: false });
                    }, 100);
                  });
                }}
              >
                <Ionicons name="menu" size={20} color={colors.text} />
              </TouchableOpacity>
            </View>
          </LinearGradient>
        </View>

        {/* Content */}
        {showGreeting ? (
          <HomeScreen 
            birthData={birthData}
            onOptionSelect={handleGreetingOptionSelect}
            navigation={navigation}
            setShowDashaBrowser={setShowDashaBrowser}
          />
        ) : (
          <>
          {partnershipMode && (
            <TouchableOpacity 
              style={styles.floatingPartnershipBadge}
              onPress={() => {
                setPartnershipMode(false);
                setNativeChart(null);
                setPartnerChart(null);
              }}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#ec4899', '#f472b6']}
                style={styles.partnershipBadgeGradient}
              >
                <Text style={[styles.partnershipBadgeText, { color: colors.text }]}>👥 Partnership Mode</Text>
                <Ionicons name="close-circle" size={16} color={COLORS.white} style={styles.partnershipBadgeIcon} />
              </LinearGradient>
            </TouchableOpacity>
          )}
          <ScrollView 
            ref={scrollViewRef}
            style={styles.messagesContainer}
            contentContainerStyle={styles.messagesContent}
            showsVerticalScrollIndicator={false}
          >
            {/* Calibration Card - COMMENTED OUT */}
            {/* {calibrationEvent && !calibrationEvent.verified && (
              <CalibrationCard 
                data={calibrationEvent}
                onConfirm={() => handleCalibrationConfirm(calibrationEvent)}
                onReject={() => handleCalibrationReject(calibrationEvent)}
              />
            )} */}
            
            {/* Signs Display */}
            {birthData && (
              <View style={styles.signsContainer}>
                <LinearGradient
                  colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.15)', 'rgba(249, 115, 22, 0.08)']}
                  style={styles.signsGradient}
                >
                  <Text style={[styles.signsTitle, { color: colors.text }]}>✨ {t('chat.chartEssence', "{{name}}'s Chart Essence", { name: birthData.name })}</Text>
                  <View style={styles.signsRow}>
                    <View style={styles.signItem}>
                      <Text style={[styles.signLabel, { color: colors.textSecondary }]}>☀️ {t('home.signs.sun', 'Sun')}</Text>
                      <Text style={[styles.signValue, { color: colors.text }]}>
                        {loadingChart ? '...' : `${getSignIcon(chartData?.planets?.Sun?.sign)} ${getSignName(chartData?.planets?.Sun?.sign)}`}
                      </Text>
                    </View>
                    <View style={styles.signItem}>
                      <Text style={[styles.signLabel, { color: colors.textSecondary }]}>🌙 {t('home.signs.moon', 'Moon')}</Text>
                      <Text style={[styles.signValue, { color: colors.text }]}>
                        {loadingChart ? '...' : `${getSignIcon(chartData?.planets?.Moon?.sign)} ${getSignName(chartData?.planets?.Moon?.sign)}`}
                      </Text>
                    </View>
                    <View style={styles.signItem}>
                      <Text style={[styles.signLabel, { color: colors.textSecondary }]}>⬆️ {t('home.signs.ascendant', 'Ascendant')}</Text>
                      <Text style={[styles.signValue, { color: colors.text }]}>
                        {loadingChart ? '...' : `${getSignIcon(chartData?.houses?.[0]?.sign)} ${getSignName(chartData?.houses?.[0]?.sign)}`}
                      </Text>
                    </View>
                  </View>
                  
                  {/* Current Running Dashas */}
                  {dashaData && (
                    <Animated.View style={[styles.dashaSection, { opacity: fadeAnim }]}>
                      <FlatList
                        horizontal
                        showsHorizontalScrollIndicator={false}
                        data={[
                          dashaData.maha_dashas?.find(d => d.current),
                          dashaData.antar_dashas?.find(d => d.current),
                          dashaData.pratyantar_dashas?.find(d => d.current),
                          dashaData.sookshma_dashas?.find(d => d.current),
                          dashaData.prana_dashas?.find(d => d.current)
                        ].filter(Boolean)}
                        keyExtractor={(item, index) => index.toString()}
                        renderItem={({ item: dasha }) => {
                          const planetColor = getPlanetColor(dasha.planet);
                          const startDate = new Date(dasha.start).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
                          const endDate = new Date(dasha.end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
                          return (
                            <TouchableOpacity 
                              style={[styles.dashaChip, { 
                                backgroundColor: theme === 'dark' ? planetColor + '40' : planetColor + '60',
                                borderColor: planetColor,
                                borderWidth: 2,
                                elevation: getCardElevation(3),
                              }]}
                              onPress={() => setShowDashaBrowser(true)}
                              activeOpacity={0.8}
                            >
                              <Text style={[styles.dashaChipPlanet, { color: theme === 'dark' ? planetColor : '#1a1a1a' }]}>{t(`home.planet_names.${dasha.planet}`, dasha.planet)}</Text>
                              <Text style={[styles.dashaChipDates, { color: colors.textSecondary }]}>{startDate}</Text>
                              <Text style={[styles.dashaChipDates, { color: colors.textSecondary }]}>{endDate}</Text>
                            </TouchableOpacity>
                          );
                        }}
                        contentContainerStyle={styles.dashaFlatListContent}
                        snapToInterval={cardWidth + 8}
                        decelerationRate="fast"
                        pagingEnabled={false}
                      />
                    </Animated.View>
                  )}
                </LinearGradient>
              </View>
            )}
            

            
            {messages.map((item, index) => {
              const isLastMessage = index === messages.length - 1;

              if (item.isTyping) {
                return (
                  <View key={item.id} ref={isLastMessage ? lastMessageRef : null}>
                    <LoadingBubble 
                      chartInsights={item.chartInsights}
                      chartData={chartData}
                      scrollViewRef={scrollViewRef}
                    />
                  </View>
                );
              }

              return (
                <View key={item.id}>
                  <View ref={isLastMessage ? lastMessageRef : null}>
                    <MessageBubble message={item} language={language} onFollowUpClick={setInputText} partnership={partnershipMode} onDelete={handleDeleteMessage} onRestart={restartPolling} />
                  </View>
                  <FeedbackComponent 
                    message={item} 
                    onFeedbackSubmitted={(messageId, rating) => {
                      console.log('Feedback submitted:', messageId, rating);
                    }}
                  />
                </View>
              );
            })}
          </ScrollView>
          </>
        )}



        {/* Suggestions (only show when not loading and not showing greeting) */}
        {!loading && !showGreeting && messages.length > 0 && (
          <View style={styles.suggestionsContainer}>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.suggestionsContent}
            >
              {suggestions.slice(0, 3).map((item, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.suggestionChip}
                  onPress={() => setInputText(item)}
                >
                  <LinearGradient
                    colors={['rgba(255, 107, 53, 0.15)', 'rgba(255, 107, 53, 0.05)']}
                    style={styles.suggestionChipGradient}
                  >
                    <Text style={[styles.suggestionChipText, { color: colors.text }]}>{item}</Text>
                  </LinearGradient>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}



        {/* Unified Input Bar */}
        {!showGreeting && (
          <View style={styles.unifiedInputContainer}>
            <LinearGradient
              colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
              style={[
                styles.inputBarGradient,
                {
                  borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.3)',
                  elevation: getCardElevation(5),
                }
              ]}
            >
              <TextInput
                style={[styles.modernTextInput, { color: colors.text }]}
                value={inputText}
                onChangeText={setInputText}
                placeholder={loading ? "Analyzing..." : credits < chatCost ? "Insufficient credits" : isMundane ? "Ask about markets, politics, events..." : "Ask me anything..."}
                placeholderTextColor={theme === 'dark' ? "rgba(255, 255, 255, 0.5)" : "rgba(0, 0, 0, 0.4)"}
                maxLength={500}
                editable={!loading && credits >= chatCost}
                multiline
              />
              
              <TouchableOpacity
                style={styles.premiumToggleButton}
                onPress={() => setIsPremiumAnalysis(!isPremiumAnalysis)}
                onLongPress={() => setShowPremiumModal(true)}
              >
                <Animated.View
                  style={[
                    styles.premiumToggleIcon,
                    isPremiumAnalysis && {
                      transform: [{
                        scale: glowAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: [1, 1.15],
                        }),
                      }],
                    },
                  ]}
                >
                  {isPremiumAnalysis ? (
                    <LinearGradient
                      colors={['#ffd700', '#ff6b35']}
                      style={styles.premiumIconGradient}
                    >
                      <Text style={styles.premiumIconText}>⚡</Text>
                    </LinearGradient>
                  ) : (
                    <View style={styles.premiumIconInactive}>
                      <Text style={styles.premiumIconTextInactive}>⚡</Text>
                      <View style={styles.premiumBadge}>
                        <Text style={styles.premiumBadgeText}>?</Text>
                      </View>
                    </View>
                  )}
                </Animated.View>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.modernSendButton,
                  (loading || !inputText.trim() || credits < (isPremiumAnalysis ? premiumChatCost : partnershipMode ? partnershipCost : chatCost)) && styles.modernSendButtonDisabled
                ]}
                onPress={() => sendMessage()}
                disabled={loading || !inputText.trim() || credits < (isPremiumAnalysis ? premiumChatCost : partnershipMode ? partnershipCost : chatCost)}
              >
                <LinearGradient
                  colors={isPremiumAnalysis ? ['#ffd700', '#ff6b35'] : ['#ff6b35', '#ff8c5a']}
                  style={styles.modernSendGradient}
                >
                  {loading ? (
                    <Text style={styles.modernSendText}>⏳</Text>
                  ) : credits < (isPremiumAnalysis ? premiumChatCost : partnershipMode ? partnershipCost : chatCost) ? (
                    <Text style={styles.modernSendText}>💳</Text>
                  ) : (
                    <Ionicons name="send" size={20} color={COLORS.white} />
                  )}
                </LinearGradient>
              </TouchableOpacity>
            </LinearGradient>
            
            {credits < (isPremiumAnalysis ? premiumChatCost : partnershipMode ? partnershipCost : chatCost) && (
              <TouchableOpacity 
                style={styles.lowCreditBanner}
                onPress={() => navigation.navigate('Credits')}
              >
                <Text style={styles.lowCreditText}>💳 Get more credits to continue</Text>
              </TouchableOpacity>
            )}
            
            {showPremiumTooltip && !isPremiumAnalysis && (
              <View style={styles.premiumTooltip}>
                <TouchableOpacity 
                  style={styles.tooltipClose}
                  onPress={() => {
                    console.log('❌ Tooltip closed');
                    tooltipResetRef.current = true;
                    setShowPremiumTooltip(false);
                  }}
                >
                  <Text style={styles.tooltipCloseText}>✕</Text>
                </TouchableOpacity>
                <Text style={styles.tooltipText}>⚡ Premium Analysis</Text>
                <Text style={styles.tooltipSubtext}>Get deeper insights</Text>
                <TouchableOpacity 
                  style={styles.tooltipButton}
                  onPress={() => {
                    console.log('💡 Learn More clicked');
                    tooltipResetRef.current = true;
                    setShowPremiumTooltip(false);
                    setShowPremiumModal(true);
                  }}
                >
                  <Text style={styles.tooltipButtonText}>Learn More</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        )}

        {/* Quick Actions Bar */}
        {!showGreeting && (
          <View style={styles.quickActionsBar}>
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => setShowLanguageModal(true)}
            >
              <Ionicons name="language-outline" size={18} color={colors.text} />
              <Text style={[styles.quickActionText, { color: colors.text }]}>{t('quickActions.language')}</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => navigation.navigate('Chart', { birthData })}
            >
              <Ionicons name="pie-chart-outline" size={18} color={colors.text} />
              <Text style={[styles.quickActionText, { color: colors.text }]}>{t('quickActions.chart')}</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => setShowDashaBrowser(true)}
            >
              <Ionicons name="time-outline" size={18} color={colors.text} />
              <Text style={[styles.quickActionText, { color: colors.text }]}>{t('quickActions.dasha')}</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.quickActionButton, partnershipMode && styles.quickActionButtonActive]}
              onPress={() => {
                if (!partnershipMode) {
                  Alert.alert(
                    'Partnership Mode',
                    `Partnership mode uses ${partnershipCost} credits per question for comprehensive compatibility analysis. Continue?`,
                    [
                      { text: 'Cancel', style: 'cancel' },
                      { 
                        text: 'Continue', 
                        onPress: () => {
                          setPartnershipMode(true);
                          setNativeChart(birthData);
                          setShowChartPicker(true);
                        }
                      }
                    ]
                  );
                } else {
                  setPartnershipMode(false);
                  setNativeChart(null);
                  setPartnerChart(null);
                }
              }}
            >
              <Ionicons name="people-outline" size={18} color={colors.text} />
              <Text style={[styles.quickActionText, { color: colors.text }]}>{t('quickActions.partner')}</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => navigation.navigate('ChatHistory')}
            >
              <Ionicons name="chatbubbles-outline" size={18} color={colors.text} />
              <Text style={[styles.quickActionText, { color: colors.text }]}>{t('quickActions.history')}</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Language Modal */}
        <Modal
          visible={showLanguageModal}
          transparent
          animationType="slide"
          onRequestClose={() => setShowLanguageModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>🌐 {t('languageModal.title')}</Text>
              {LANGUAGES.map((lang) => (
                <TouchableOpacity
                  key={lang.code}
                  style={[
                    styles.languageOption,
                    language === lang.code && styles.languageOptionSelected
                  ]}
                  onPress={() => handleLanguageChange(lang.code)}
                >
                  <Text style={styles.languageText}>
                    {lang.flag} {lang.name}
                  </Text>
                </TouchableOpacity>
              ))}
              <TouchableOpacity
                style={styles.modalCloseButton}
                onPress={() => setShowLanguageModal(false)}
              >
                <Text style={styles.modalCloseText}>{t('languageModal.close')}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>

        {/* Menu Drawer */}
        <Modal
          visible={showMenu}
          transparent
          animationType="fade"
          onRequestClose={() => {
            Animated.timing(drawerAnim, {
              toValue: 300,
              duration: 250,
              useNativeDriver: true,
            }).start(() => setShowMenu(false));
          }}
        >
          <TouchableOpacity 
            style={styles.drawerOverlay} 
            activeOpacity={1}
            onPress={() => {
              Animated.timing(drawerAnim, {
                toValue: 300,
                duration: 250,
                useNativeDriver: true,
              }).start(() => setShowMenu(false));
            }}
          >
            <Animated.View 
              style={[styles.drawerContent, {
                transform: [{ translateX: drawerAnim }]
              }]}
              onStartShouldSetResponder={() => true}
            >
              <LinearGradient
                colors={theme === 'dark' ? ['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35'] : ['#fefcfb', '#fefcfb', '#fefcfb', '#fefcfb']}
                style={styles.drawerGradient}
              >
                <View style={styles.drawerHeader}>
                  <Animated.View style={[styles.logoContainer, {
                    shadowOpacity: menuLogoGlow.interpolate({
                      inputRange: [0, 1],
                      outputRange: [0.6, 1],
                    }),
                    shadowRadius: menuLogoGlow.interpolate({
                      inputRange: [0, 1],
                      outputRange: [12, 20],
                    }),
                    transform: [{
                      scale: menuLogoGlow.interpolate({
                        inputRange: [0, 1],
                        outputRange: [1, 1.05],
                      })
                    }]
                  }]}>
                    <Image 
                      source={require('../../../assets/logo.png')}
                      style={styles.logoImage}
                      resizeMode="contain"
                    />
                  </Animated.View>
                  <Text style={[styles.drawerTitle, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.title')}</Text>
                  <Text style={[styles.drawerSubtitle, { color: theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : 'rgba(31, 41, 55, 0.7)' }]}>{t('menu.subtitle')}</Text>
                </View>

                <ScrollView 
                  ref={menuScrollViewRef}
                  style={styles.menuScrollView}
                  contentContainerStyle={styles.menuScrollContent}
                  showsVerticalScrollIndicator={false}
                  nestedScrollEnabled={true}
                >
                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('Profile');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>✨</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.myProfile')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('SelectNative');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>👤</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.selectNative')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('BirthForm');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>➕</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.newNative')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('Chart', { birthData });
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>📊</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.viewChart')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        setShowDashaBrowser(true);
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>⏰</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.dashaBrowser')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('AshtakvargaOracle');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#9C27B0', '#E91E63']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>⊞</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.ashtakvarga')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('Shadbala', { birthData });
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#FF6B35', '#FFA500']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>⚖️</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.shadbala')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>


                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('KotaChakra', { birthChartId: birthData?.id });
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#795548', '#8D6E63']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🏰</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.kotaChakra')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('Yogas');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#8b5cf6', '#6366f1']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🧘</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.yogas')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('AnalysisHub');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🧘</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.lifeAnalysis')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('KarmaAnalysis', { chartId: birthData?.id });
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#667eea', '#764ba2']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🕉️</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.pastLifeRegression')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('Numerology');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#667eea', '#764ba2']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🔢</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.numerology')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('ChatHistory');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#667eea', '#764ba2']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>💬</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.chatHistory')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  {!isMundane && !showGreeting && (
                    <TouchableOpacity
                      style={getMenuOptionStyle()}
                      onPress={() => {
                        if (!partnershipMode) {
                          Alert.alert(
                            'Partnership Mode',
                            `Partnership mode uses ${partnershipCost} credits per question for comprehensive compatibility analysis. Continue?`,
                            [
                              { text: 'Cancel', style: 'cancel' },
                              { 
                                text: 'Continue', 
                                onPress: () => {
                                  setPartnershipMode(true);
                                  setNativeChart(birthData);
                                  Animated.timing(drawerAnim, {
                                    toValue: 300,
                                    duration: 250,
                                    useNativeDriver: true,
                                  }).start(() => {
                                    setShowMenu(false);
                                    setShowChartPicker(true);
                                  });
                                }
                              }
                            ]
                          );
                        } else {
                          setPartnershipMode(false);
                          setNativeChart(null);
                          setPartnerChart(null);
                          Animated.timing(drawerAnim, {
                            toValue: 300,
                            duration: 250,
                            useNativeDriver: true,
                          }).start(() => setShowMenu(false));
                        }
                      }}
                    >
                      <LinearGradient
                        colors={partnershipMode ? ['rgba(147, 51, 234, 0.3)', 'rgba(147, 51, 234, 0.1)'] : ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                        style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                      >
                        <View style={styles.menuIconContainer}>
                          <LinearGradient
                            colors={partnershipMode ? ['#9333ea', '#a855f7'] : ['#ff6b35', '#ff8c5a']}
                            style={styles.menuIconGradient}
                          >
                            <Text style={styles.menuEmoji}>👥</Text>
                          </LinearGradient>
                        </View>
                        <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t(partnershipMode ? 'menu.partnershipOn' : 'menu.partnershipOff')}</Text>
                        <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                      </LinearGradient>
                    </TouchableOpacity>
                  )}

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('Credits');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>💳</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.credits')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[getMenuOptionStyle(), styles.menuOptionLast]}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        logout();
                      });
                    }}
                  >
                    <LinearGradient
                      colors={['rgba(255, 59, 48, 0.2)', 'rgba(255, 59, 48, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(249, 115, 22, 0.4)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff3b30', '#ff6b60']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🚪</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ff6b60' : '#dc2626' }]}>{t('menu.logout')}</Text>
                      <Ionicons name="chevron-forward" size={20} color="rgba(255, 107, 96, 0.6)" />
                    </LinearGradient>
                  </TouchableOpacity>
                </ScrollView>
              </LinearGradient>
            </Animated.View>
          </TouchableOpacity>
        </Modal>



        {/* Event Periods Modal */}
        {showEventPeriods && (
          <EventPeriods 
            visible={showEventPeriods} 
            onClose={() => {
              setShowEventPeriods(false);
            }}
            birthData={birthData}
            onPeriodSelect={(period) => {
              setShowEventPeriods(false);
              setShowGreeting(false);
              const periodQuestion = `Tell me more about the period from ${new Date(period.start_date).toLocaleDateString()} to ${new Date(period.end_date).toLocaleDateString()} when ${period.transit_planet} activates ${period.natal_planet}. What specific events should I expect?`;
              sendMessage(periodQuestion);
            }}
          />
        )}

        {/* Dasha Browser Modal */}
        <CascadingDashaBrowser 
          visible={showDashaBrowser} 
          onClose={() => setShowDashaBrowser(false)}
          birthData={birthData}
        />

        {/* Enhanced Analysis Popup */}
        <Modal
          visible={showEnhancedPopup}
          transparent
          animationType="fade"
          onRequestClose={() => setShowEnhancedPopup(false)}
        >
          <View style={styles.enhancedPopupOverlay}>
            <View style={styles.enhancedPopup}>
              <TouchableOpacity 
                style={styles.popupClose}
                onPress={() => setShowEnhancedPopup(false)}
              >
                <Text style={styles.popupCloseText}>×</Text>
              </TouchableOpacity>
              
              <View style={styles.popupHeader}>
                <LinearGradient
                  colors={['#ff6b35', '#ff8c5a', '#ffd700']}
                  style={styles.popupHeaderGradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                />
                <View style={styles.popupHeaderContent}>
                  <View style={styles.popupIconContainer}>
                    <LinearGradient
                      colors={['#ffd700', '#ffed4e']}
                      style={styles.popupIconGradient}
                    >
                      <Text style={styles.popupIcon}>✨</Text>
                    </LinearGradient>
                  </View>
                  <Text style={styles.popupTitle}>Enhanced Deep Analysis</Text>
                  <Text style={styles.popupSubtitle}>Unlock Advanced Cosmic Insights</Text>
                </View>
              </View>
              
              <ScrollView 
                style={styles.popupContent}
                contentContainerStyle={styles.popupContentContainer}
                showsVerticalScrollIndicator={false}
              >
                <Text style={styles.popupIntro}>
                  Experience the most sophisticated astrological analysis with advanced calculations and deeper interpretation techniques for comprehensive cosmic insights.
                </Text>
                
                <View style={styles.benefitItem}>
                  <View style={styles.benefitIconContainer}>
                    <LinearGradient
                      colors={['#ff6b35', '#ff8c5a']}
                      style={styles.benefitIconGradient}
                    >
                      <Text style={styles.benefitIcon}>☀️</Text>
                    </LinearGradient>
                  </View>
                  <View style={styles.benefitText}>
                    <Text style={styles.benefitTitle}>Multi-Layered Chart Analysis</Text>
                    <Text style={styles.benefitDesc}>Examines Lagna, Navamsa, and divisional charts with intricate planetary relationships and house lordships</Text>
                  </View>
                </View>
                
                <View style={styles.benefitItem}>
                  <View style={styles.benefitIconContainer}>
                    <LinearGradient
                      colors={['#4CAF50', '#66BB6A']}
                      style={styles.benefitIconGradient}
                    >
                      <Text style={styles.benefitIcon}>🌟</Text>
                    </LinearGradient>
                  </View>
                  <View style={styles.benefitText}>
                    <Text style={styles.benefitTitle}>Advanced Dasha Interpretation</Text>
                    <Text style={styles.benefitDesc}>Analyzes Mahadasha, Antardasha, and Pratyantardasha periods with precise event timing predictions</Text>
                  </View>
                </View>
                
                <View style={styles.benefitItem}>
                  <View style={styles.benefitIconContainer}>
                    <LinearGradient
                      colors={['#2196F3', '#42A5F5']}
                      style={styles.benefitIconGradient}
                    >
                      <Text style={styles.benefitIcon}>🎯</Text>
                    </LinearGradient>
                  </View>
                  <View style={styles.benefitText}>
                    <Text style={styles.benefitTitle}>Yoga & Dosha Detection</Text>
                    <Text style={styles.benefitDesc}>Identifies powerful yogas like Raja, Dhana, Gaja Kesari and doshas affecting your life trajectory</Text>
                  </View>
                </View>
                
                <View style={styles.benefitItem}>
                  <View style={styles.benefitIconContainer}>
                    <LinearGradient
                      colors={['#9C27B0', '#BA68C8']}
                      style={styles.benefitIconGradient}
                    >
                      <Text style={styles.benefitIcon}>🌙</Text>
                    </LinearGradient>
                  </View>
                  <View style={styles.benefitText}>
                    <Text style={styles.benefitTitle}>Nakshatra Deep Dive</Text>
                    <Text style={styles.benefitDesc}>Reveals hidden personality traits, karmic patterns, and life purpose through nakshatra analysis</Text>
                  </View>
                </View>
                
                <View style={styles.benefitItem}>
                  <View style={styles.benefitIconContainer}>
                    <LinearGradient
                      colors={['#FF9800', '#FFB74D']}
                      style={styles.benefitIconGradient}
                    >
                      <Text style={styles.benefitIcon}>⚡</Text>
                    </LinearGradient>
                  </View>
                  <View style={styles.benefitText}>
                    <Text style={styles.benefitTitle}>Transit Correlation</Text>
                    <Text style={styles.benefitDesc}>Maps current planetary transits against your birth chart for accurate timing of events</Text>
                  </View>
                </View>
                
                <View style={styles.benefitItem}>
                  <View style={styles.benefitIconContainer}>
                    <LinearGradient
                      colors={['#795548', '#A1887F']}
                      style={styles.benefitIconGradient}
                    >
                      <Text style={styles.benefitIcon}>🏆</Text>
                    </LinearGradient>
                  </View>
                  <View style={styles.benefitText}>
                    <Text style={styles.benefitTitle}>Remedial Recommendations</Text>
                    <Text style={styles.benefitDesc}>Provides personalized gemstone, mantra, and ritual suggestions based on planetary strengths</Text>
                  </View>
                </View>
                
                <TouchableOpacity 
                  style={styles.popupButton}
                  onPress={() => setShowEnhancedPopup(false)}
                >
                  <LinearGradient
                    colors={['#ff6b35', '#ff8c5a']}
                    style={styles.popupButtonGradient}
                  >
                    <Text style={styles.popupButtonText}>Got it!</Text>
                  </LinearGradient>
                </TouchableOpacity>
              </ScrollView>
            </View>
          </View>
        </Modal>
        
        {/* Chart Picker Modal */}
        <Modal
          visible={showChartPicker}
          transparent={true}
          animationType="slide"
          onRequestClose={() => setShowChartPicker(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.chartPickerModal}>
              <View style={styles.chartPickerHeader}>
                <Text style={styles.chartPickerTitle}>
                  Select {selectingFor === 'native' ? 'Native' : 'Partner'} Chart
                </Text>
                <TouchableOpacity onPress={() => setShowChartPicker(false)}>
                  <Ionicons name="close" size={24} color={COLORS.textPrimary} />
                </TouchableOpacity>
              </View>
              
              <ScrollView style={styles.chartPickerList}>
                {savedCharts.map((chart, index) => (
                  <TouchableOpacity
                    key={index}
                    style={styles.chartPickerItem}
                    onPress={() => {
                      if (selectingFor === 'native') {
                        setNativeChart(chart);
                      } else {
                        setPartnerChart(chart);
                      }
                      setShowChartPicker(false);
                    }}
                  >
                    <View style={styles.chartPickerItemContent}>
                      <Text style={styles.chartPickerItemName}>{chart.name}</Text>
                      <Text style={styles.chartPickerItemDetails}>
                        {chart.date} • {chart.time}
                      </Text>
                      <Text style={styles.chartPickerItemPlace}>{chart.place}</Text>
                    </View>
                    <Ionicons name="chevron-forward" size={20} color={COLORS.textSecondary} />
                  </TouchableOpacity>
                ))}
                
                {savedCharts.length === 0 && (
                  <View style={styles.emptyChartList}>
                    <Text style={styles.emptyChartText}>No saved charts found</Text>
                    <Text style={styles.emptyChartSubtext}>Please save charts first</Text>
                  </View>
                )}
              </ScrollView>
            </View>
          </View>
        </Modal>
        
        {/* Country Picker Modal */}
        <Modal
          visible={showCountryPicker}
          transparent={true}
          animationType="slide"
          onRequestClose={() => setShowCountryPicker(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.chartPickerModal}>
              <View style={styles.chartPickerHeader}>
                <Text style={styles.chartPickerTitle}>Select Country</Text>
                <TouchableOpacity onPress={() => setShowCountryPicker(false)}>
                  <Ionicons name="close" size={24} color={COLORS.textPrimary} />
                </TouchableOpacity>
              </View>
              <ScrollView style={styles.chartPickerList}>
                {COUNTRIES.map((country, index) => (
                  <TouchableOpacity
                    key={index}
                    style={styles.chartPickerItem}
                    onPress={() => {
                      setSelectedCountry(country);
                      setShowCountryPicker(false);
                    }}
                  >
                    <View style={styles.chartPickerItemContent}>
                      <Text style={styles.chartPickerItemName}>{country.name}</Text>
                      <Text style={styles.chartPickerItemDetails}>{country.capital}</Text>
                    </View>
                    <Ionicons name="chevron-forward" size={20} color={COLORS.textSecondary} />
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
          </View>
        </Modal>
        
        {/* Year Picker Modal */}
        <Modal
          visible={showYearPicker}
          transparent={true}
          animationType="slide"
          onRequestClose={() => setShowYearPicker(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.chartPickerModal}>
              <View style={styles.chartPickerHeader}>
                <Text style={styles.chartPickerTitle}>Select Year</Text>
                <TouchableOpacity onPress={() => setShowYearPicker(false)}>
                  <Ionicons name="close" size={24} color={COLORS.textPrimary} />
                </TouchableOpacity>
              </View>
              <ScrollView style={styles.chartPickerList}>
                {YEARS.map((year, index) => (
                  <TouchableOpacity
                    key={index}
                    style={styles.chartPickerItem}
                    onPress={() => {
                      setSelectedYear(year);
                      setShowYearPicker(false);
                    }}
                  >
                    <View style={styles.chartPickerItemContent}>
                      <Text style={styles.chartPickerItemName}>{year}</Text>
                    </View>
                    <Ionicons name="chevron-forward" size={20} color={COLORS.textSecondary} />
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
          </View>
        </Modal>
        </KeyboardAvoidingView>
      </SafeAreaView>
      
      <PremiumAnalysisModal
        visible={showPremiumModal}
        onClose={() => setShowPremiumModal(false)}
        premiumCost={premiumChatCost}
        standardCost={chatCost}
      />
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradientBg: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  headerContainer: {
    paddingHorizontal: 12,
    paddingTop: 12,
    paddingBottom: 8,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
    borderWidth: 1,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 2,
  },
  nameChip: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    marginTop: 2,
  },
  nameChipText: {
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'center',
  },
  partnershipChipsContainer: {
    flexDirection: 'row',
    gap: 4,
    marginTop: 2,
  },
  nativeChip: {
    backgroundColor: 'rgba(59, 130, 246, 0.25)',
    borderWidth: 1.5,
    borderColor: 'rgba(59, 130, 246, 0.8)',
  },
  partnerChip: {
    backgroundColor: 'rgba(236, 72, 153, 0.25)',
    borderWidth: 1.5,
    borderColor: 'rgba(236, 72, 153, 0.8)',
  },
  compactChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  compactChipText: {
    fontSize: 10,
    fontWeight: '700',
    textAlign: 'center',
    color: '#ffffff',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  creditButton: {
    backgroundColor: 'rgba(255, 107, 53, 0.2)',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.4)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  creditButtonPremium: {
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
    borderColor: 'rgba(255, 215, 0, 0.4)',
  },
  creditText: {
    fontSize: 13,
    fontWeight: '700',
  },
  menuButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  messagesContainer: {
    flex: 1,
    paddingHorizontal: 4,
  },
  messagesContent: {
    paddingVertical: 16,
    paddingHorizontal: 12,
    flexGrow: 1,
  },

  suggestionsContainer: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  suggestionsContent: {
    paddingHorizontal: 4,
  },
  suggestionChip: {
    marginRight: 8,
    borderRadius: 20,
    overflow: 'hidden',
  },
  suggestionChipGradient: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    borderRadius: 20,
  },
  suggestionChipText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '600',
  },

  unifiedInputContainer: {
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  inputBarGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 28,
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderWidth: 1,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
      },
      android: {
        // elevation set dynamically
      },
    }),
  },
  modernTextInput: {
    flex: 1,
    fontSize: 16,
    color: COLORS.white,
    paddingHorizontal: 16,
    paddingVertical: 10,
    maxHeight: 100,
  },
  premiumToggleButton: {
    marginHorizontal: 4,
  },
  premiumToggleIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  premiumIconGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.4)',
    shadowColor: '#ffd700',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 8,
    elevation: 6,
  },
  premiumIconText: {
    fontSize: 24,
  },
  premiumIconInactive: {
    width: '100%',
    height: '100%',
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  premiumIconTextInactive: {
    fontSize: 24,
    opacity: 0.7,
  },
  modernSendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.4,
    shadowRadius: 4,
    elevation: 4,
  },
  modernSendButtonDisabled: {
    opacity: 0.5,
  },
  modernSendGradient: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modernSendText: {
    fontSize: 20,
  },
  lowCreditBanner: {
    marginTop: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: 'rgba(255, 107, 53, 0.2)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
  },
  lowCreditText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
  quickActionsBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 0,
  },
  quickActionButton: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    opacity: 0.8,
  },
  quickActionButtonActive: {
    opacity: 1,
  },
  quickActionText: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '600',
  },
  signsContainer: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  signsGradient: {
    padding: 16,
  },
  signsTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 12,
  },
  signsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  signItem: {
    alignItems: 'center',
    flex: 1,
  },
  signLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: 4,
  },
  signValue: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.white,
    textAlign: 'center',
  },
  dashasContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.2)',
  },
  dashasTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    marginBottom: 8,
  },
  dashasRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    flexWrap: 'wrap',
    gap: 6,
  },
  dashasLoading: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    textAlign: 'center',
  },
  dashaChip: {
    borderWidth: 1.5,
    borderRadius: 16,
    paddingHorizontal: 10,
    paddingVertical: 10,
    alignItems: 'center',
    marginRight: 8,
    width: cardWidth,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.2,
        shadowRadius: 4,
      },
      android: {
        // elevation set dynamically
      },
    }),
  },
  dashaChipPlanet: {
    fontSize: fontSize,
    fontWeight: '700',
    marginBottom: 2,
  },
  dashaChipDates: {
    fontSize: smallFontSize,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '500',
  },
  dashaSection: {
    marginTop: 16,
    marginBottom: 24,
  },
  dashaSectionTitle: {
    fontSize: isSmallScreen ? 16 : 18,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  dashaFlatListContent: {
    paddingHorizontal: 4,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 24,
    padding: 24,
    width: '88%',
    maxHeight: '75%',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  drawerOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
    flexDirection: 'row',
  },
  drawerContent: {
    width: 300,
    height: '100%',
    shadowColor: '#000',
    shadowOffset: { width: -2, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 12,
    elevation: 15,
  },
  drawerGradient: {
    flex: 1,
  },
  drawerHeader: {
    alignItems: 'center',
    paddingTop: 60,
    paddingBottom: 20,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  logoContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    elevation: 8,
  },
  logoImage: {
    width: 70,
    height: 70,
    borderRadius: 35,
  },
  cosmicOrbSmall: {
    width: 70,
    height: 70,
    borderRadius: 35,
    marginBottom: 16,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.6,
    shadowRadius: 12,
    elevation: 8,
  },
  orbGradientSmall: {
    width: '100%',
    height: '100%',
    borderRadius: 35,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  orbIconSmall: {
    fontSize: 36,
  },
  drawerTitle: {
    fontSize: 24,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 6,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  drawerSubtitle: {
    fontSize: 14,
    textAlign: 'center',
  },
  menuScrollView: {
    height: 450,
  },
  menuScrollContent: {
    padding: 20,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.accent,
    textAlign: 'center',
    marginBottom: 24,
  },
  languageOption: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    backgroundColor: COLORS.lightGray,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  languageOptionSelected: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    borderColor: COLORS.accent,
  },
  languageText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.black,
  },
  menuOption: {
    marginBottom: 12,
    borderRadius: 16,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  menuOptionLast: {
    marginTop: 8,
  },
  menuGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  menuIconContainer: {
    marginRight: 14,
  },
  menuIconGradient: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  menuEmoji: {
    fontSize: 22,
  },
  menuText: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
  },
  modalCloseButton: {
    backgroundColor: COLORS.accent,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 16,
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  modalCloseText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '700',
  },

  enhancedPopupOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  enhancedPopup: {
    backgroundColor: '#ffffff',
    borderRadius: 24,
    width: '100%',
    maxHeight: '90%',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 20 },
    shadowOpacity: 0.15,
    shadowRadius: 30,
    elevation: 15,
    overflow: 'hidden',
  },
  popupClose: {
    position: 'absolute',
    top: 20,
    right: 20,
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  popupCloseText: {
    fontSize: 20,
    color: '#666',
    fontWeight: '600',
  },
  popupHeader: {
    paddingVertical: 40,
    paddingHorizontal: 24,
    alignItems: 'center',
    position: 'relative',
    overflow: 'hidden',
  },
  popupHeaderGradient: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  popupHeaderContent: {
    alignItems: 'center',
    zIndex: 2,
  },
  popupIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 16,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  popupIconGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.8)',
  },
  popupIcon: {
    fontSize: 40,
  },
  popupTitle: {
    color: COLORS.white,
    fontSize: 26,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 8,
    textShadowColor: 'rgba(0, 0, 0, 0.2)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  popupSubtitle: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 16,
    textAlign: 'center',
    fontWeight: '500',
  },
  popupContent: {
    maxHeight: '65%',
  },
  popupContentContainer: {
    padding: 24,
    paddingBottom: 32,
  },
  popupIntro: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 24,
    fontWeight: '400',
  },
  benefitItem: {
    flexDirection: 'row',
    marginBottom: 16,
    padding: 16,
    backgroundColor: '#fafafa',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#f0f0f0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },
  benefitIconContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    marginRight: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  benefitIconGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  benefitIcon: {
    fontSize: 20,
  },
  benefitText: {
    flex: 1,
    justifyContent: 'center',
  },
  benefitTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#333',
    marginBottom: 4,
  },
  benefitDesc: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    fontWeight: '400',
  },
  popupButton: {
    borderRadius: 16,
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 8,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
  popupButtonGradient: {
    paddingVertical: 16,
    paddingHorizontal: 32,
    width: '100%',
    alignItems: 'center',
  },
  popupButtonText: {
    color: COLORS.white,
    fontSize: 18,
    fontWeight: '700',
  },
  // Partnership mode styles
  chartSelectionContainer: {
    padding: 16,
    backgroundColor: COLORS.lightGray,
    borderRadius: 12,
    margin: 16,
  },
  chartSelectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 12,
  },
  chartSelectButton: {
    padding: 12,
    backgroundColor: COLORS.white,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 8,
  },
  chartSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.quickAnswerStart,
  },
  chartSelectText: {
    fontSize: 14,
    color: COLORS.textPrimary,
  },
  chartsDisplayContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  miniChartCard: {
    flex: 1,
    padding: 12,
    backgroundColor: COLORS.white,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  miniChartLabel: {
    fontSize: 10,
    color: COLORS.textSecondary,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  miniChartName: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  miniChartDetails: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  chartPickerModal: {
    backgroundColor: COLORS.white,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '70%',
  },
  chartPickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  chartPickerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  chartPickerList: {
    padding: 16,
  },
  chartPickerItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: COLORS.lightGray,
    borderRadius: 12,
    marginBottom: 12,
  },
  chartPickerItemContent: {
    flex: 1,
  },
  chartPickerItemName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  chartPickerItemDetails: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: 2,
  },
  chartPickerItemPlace: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  emptyChartList: {
    padding: 32,
    alignItems: 'center',
  },
  emptyChartText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textSecondary,
    marginBottom: 8,
  },
  emptyChartSubtext: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  floatingPartnershipBadge: {
    marginHorizontal: 16,
    marginTop: 8,
    marginBottom: 8,
    borderRadius: 20,
    overflow: 'hidden',
    alignSelf: 'flex-end',
    shadowColor: '#ec4899',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  partnershipBadgeGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 6,
  },
  partnershipBadgeText: {
    color: COLORS.white,
    fontSize: 11,
    fontWeight: '700',
  },
  partnershipBadgeIcon: {
    marginLeft: 2,
  },
  premiumTooltip: {
    position: 'absolute',
    bottom: 80,
    right: 10,
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 5,
    width: 180,
    zIndex: 1000,
  },
  tooltipText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  tooltipSubtext: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },
  tooltipButton: {
    backgroundColor: '#ff6b35',
    padding: 8,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 4,
  },
  tooltipButtonText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '600',
  },
  tooltipClose: {
    position: 'absolute',
    top: 4,
    right: 4,
    padding: 4,
    zIndex: 1001,
  },
  tooltipCloseText: {
    fontSize: 16,
    color: '#999',
  },
  premiumBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    backgroundColor: '#ff6b35',
    width: 16,
    height: 16,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#1a0033',
  },
  premiumBadgeText: {
    color: COLORS.white,
    fontSize: 10,
    fontWeight: 'bold',
  },
});