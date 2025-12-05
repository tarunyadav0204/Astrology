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
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'react-native';

import MessageBubble from './MessageBubble';
import EventPeriods from './EventPeriods';
import HomeScreen from './HomeScreen';
import { storage } from '../../services/storage';
import { chatAPI } from '../../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS, LANGUAGES, API_BASE_URL, getEndpoint } from '../../utils/constants';

import CascadingDashaBrowser from '../Dasha/CascadingDashaBrowser';
import { useCredits } from '../../credits/CreditContext';

const { width: screenWidth } = Dimensions.get('window');
const isSmallScreen = screenWidth < 375;
const cardWidth = screenWidth * 0.22;
const fontSize = isSmallScreen ? 11 : 13;
const smallFontSize = isSmallScreen ? 9 : 10;

export default function ChatScreen({ navigation, route }) {
  const { credits, fetchBalance } = useCredits();
  const [chatCost, setChatCost] = useState(1);
  const [premiumChatCost, setPremiumChatCost] = useState(3);
  const [isPremiumAnalysis, setIsPremiumAnalysis] = useState(false);
  const [showEnhancedPopup, setShowEnhancedPopup] = useState(false);
  const [showPremiumBadge, setShowPremiumBadge] = useState(false);
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
  const [language, setLanguage] = useState('english');
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const drawerAnim = useRef(new Animated.Value(300)).current;
  const menuScrollViewRef = useRef(null);

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
        pollForResponse(messageId, null, sessionId, null, true); // true = resume mode
      });
    }
  };

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
    return signs[signNumber] || signNumber;
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
        longitude: parseFloat(birth.longitude),
        timezone: birth.timezone || 'Asia/Kolkata'
      };
      
      const { chartAPI } = require('../../services/api');
      // Use calculateChart instead of calculateChartOnly to save birth data to database
      const response = await chartAPI.calculateChart(formattedData);
      setChartData(response.data);

    } catch (error) {
      console.error('Error loading chart data:', error);
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
        timezone: birth.timezone || 'Asia/Kolkata',
        location: birth.place || 'Unknown'
      };
      
      const { chartAPI } = require('../../services/api');
      const response = await chartAPI.calculateCascadingDashas(formattedBirthData, targetDate);
      
      if (response.data && !response.data.error) {
        setDashaData(response.data);
      }
    } catch (error) {
      console.error('Error loading dasha data:', error);
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
      navigation.setParams({ startChat: undefined });
      // Use the same logic as greeting option select for question action
      handleGreetingOptionSelect({ action: 'question' });
    }
    
    // Handle back button - go to home screen if in chat mode, exit if on home screen
    const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
      if (!showGreeting) {
        // In chat mode, go back to home screen
        setShowGreeting(true);
        return true; // Prevent default back behavior
      } else {
        // On home screen, exit app
        BackHandler.exitApp();
        return true;
      }
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
            
            // Check for processing messages and resume polling
            const processingMessage = storedMessages.find(msg => msg.isTyping && msg.messageId);
            if (processingMessage) {
              setLoading(true);
              setIsTyping(true);
              // Use personId directly to avoid timing issues
              setTimeout(() => {
                pollForResponse(processingMessage.messageId, null, sessionId, null, true);
              }, 100);
            }
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
            setMessages(prev => prev.length === 0 ? storedMessages : prev);
            // Don't auto-switch if app startup or we already have messages loaded
            if (!isAppStartup && messages.length === 0) {
              setShowGreeting(false);
            }
            
            // Only resume polling if not already polling
            if (!loading && !isTyping) {
              const processingMessage = storedMessages.find(msg => msg.isTyping && msg.messageId);
              if (processingMessage) {
                setLoading(true);
                setIsTyping(true);
                pollForResponse(processingMessage.messageId, null, sessionId, null, true);
              }
            }
          }
        });
      }
    });
    
    return unsubscribe;
  }, [currentPersonId, loading, isTyping]);

  const handleGreetingOptionSelect = async (option) => {
    
    if (option.action === 'periods') {
      setShowEventPeriods(true);
    } else if (option.action === 'analysis') {
      navigation.navigate('AnalysisDetail', { 
        analysisType: option.type,
        title: `${option.type.charAt(0).toUpperCase() + option.type.slice(1)} Analysis`,
        cost: 5
      });
    } else {
      
      // First load any existing chat history
      await loadChatHistory();
      
      // Switch to chat mode immediately
      setShowGreeting(false);
      
      // Check if we need to show welcome message
      setTimeout(async () => {
        
        const storedMessages = await loadMessagesFromStorage(currentPersonId);
        
        // Always show fresh welcome message when explicitly starting chat
        const nativeName = birthData?.name || 'there';
        
        const welcomeMessage = {
          id: Date.now().toString(),
          content: `🌟 Welcome ${nativeName}! I'm here to help you understand your birth chart and provide astrological insights.\n\nFeel free to ask me anything about:\n\n• Personality traits and characteristics\n• Career and professional guidance\n• Relationships and compatibility\n• Health and wellness insights\n• Timing for important decisions\n• Current planetary transits\n• Strengths and areas for growth\n\nWhat would you like to explore first?`,
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
      const savedBirthData = await storage.getBirthDetails();
      
      if (savedBirthData && typeof savedBirthData === 'object' && savedBirthData.name && savedBirthData.name.trim()) {
        setBirthData(savedBirthData);
      } else {
        
        // Try to load first available chart from database
        try {
          const { chartAPI } = require('../../services/api');
          const response = await chartAPI.getExistingCharts();
          
          if (response.data && response.data.charts && response.data.charts.length > 0) {
            const firstChart = response.data.charts[0];
            
            // Convert database chart to birth data format
            const birthDataFromChart = {
              name: firstChart.name,
              date: firstChart.date,
              time: firstChart.time,
              latitude: firstChart.latitude,
              longitude: firstChart.longitude,
              timezone: firstChart.timezone,
              place: firstChart.place,
              gender: firstChart.gender
            };
            
            
            // Save to storage for future use
            await storage.setBirthDetails(birthDataFromChart);
            setBirthData(birthDataFromChart);
          } else {
            setBirthData(null);
            navigation.navigate('BirthForm');
          }
        } catch (apiError) {
          console.error('❌ Error loading charts from database:', apiError);
          setBirthData(null);
          navigation.navigate('BirthForm');
        }
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
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat-v2/session')}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const newSessionId = data.session_id;
        setSessionId(newSessionId);
        
        // Immediately track this session for current person
        const currentBirthHash = `${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}`;
        const personSessions = JSON.parse(await AsyncStorage.getItem(`chatSessions_${currentBirthHash}`) || '[]');
        personSessions.push(newSessionId);
        await AsyncStorage.setItem(`chatSessions_${currentBirthHash}`, JSON.stringify(personSessions));
        
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

  const pollForResponse = async (messageId, processingMessageId, currentSessionId, loadingInterval = null, isResume = false) => {
    if (!messageId) {
      console.error('❌ No messageId provided to pollForResponse');
      return;
    }
    
    const maxPolls = 80; // 4 minutes max
    let pollCount = 0;
    
    // Add to pending messages if not resuming
    if (!isResume) {
      await addPendingMessage(messageId);
    }
    
    const loadingMessages = [
      '🔮 Analyzing your birth chart...',
      '⭐ Consulting the cosmic energies...',
      '📊 Calculating planetary positions...',
      '🌟 Interpreting astrological patterns...',
      '✨ Preparing your personalized insights...'
    ];
    
    const poll = async () => {
      try {
        const token = await AsyncStorage.getItem('authToken');
        const url = `${API_BASE_URL}${getEndpoint(`/chat-v2/status/${messageId}`)}`;
        
        const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('❌ Poll response error:', response.status, errorText);
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const status = await response.json();
        
        if (status.status === 'completed') {
          // Check if person changed during processing - use more reliable check
          const currentPersonIdNow = birthData ? `${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}` : null;
          
          // Only skip if we have a clear person change (both IDs exist and are different)
          if (currentPersonId && currentPersonIdNow && currentPersonIdNow !== currentPersonId) {
            await removePendingMessage(messageId);
            return;
          }
          
          if (loadingInterval) clearInterval(loadingInterval);
          
          // Update message with response content
          setMessagesWithStorage(prev => {
            const updated = prev.map(msg => 
              msg.messageId === messageId 
                ? { ...msg, content: status.content || 'Response received but content is empty', isTyping: false }
                : msg
            );
            return updated;
          });
          
          setLoading(false);
          setIsTyping(false);
          await removePendingMessage(messageId);
          fetchBalance();
          
          // Scroll to bottom to show new response
          setTimeout(() => {
            scrollViewRef.current?.scrollToEnd({ animated: true });
          }, 100);
          
          return;
        }
        
        if (status.status === 'failed') {
          if (loadingInterval) clearInterval(loadingInterval);
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
        
        // Still processing - update message and continue polling
        if (status.status === 'processing') {
          const randomMessage = loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
          
          setMessagesWithStorage(prev => {
            const updated = prev.map(msg => 
              msg.messageId === messageId 
                ? { ...msg, content: randomMessage }
                : msg
            );
            return updated;
          });
          
          pollCount++;
          if (pollCount < maxPolls) {
            setTimeout(poll, 3000);
          } else {
            // Timeout - show restart option
            if (loadingInterval) clearInterval(loadingInterval);
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
        console.error('❌ Polling error for messageId:', messageId, error);
        
        if (loadingInterval) clearInterval(loadingInterval);
        setMessagesWithStorage(prev => prev.map(msg => 
          msg.messageId === messageId 
            ? { ...msg, content: `Connection error: ${error.message}. Please try again.`, isTyping: false }
            : msg
        ));
        setLoading(false);
        setIsTyping(false);
        await removePendingMessage(messageId);
      }
    };
    
    // Start polling immediately
    setTimeout(poll, 1000);
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
    pollForResponse(messageId, null, sessionId, null, true);
  };

  const sendMessage = async (messageText = inputText) => {
    if (!messageText.trim() || !birthData) {
      return;
    }

    // Clear input and set states immediately
    setInputText('');
    setLoading(true);
    setIsTyping(true);
    setShowGreeting(false);
    
    // Remove test message code

    // Add user message immediately
    const userMessage = {
      id: Date.now().toString(),
      content: messageText,
      role: 'user',
      timestamp: new Date().toISOString(),
    };
    
    setMessagesWithStorage(prev => {
      const newMessages = [...prev, userMessage];
      return newMessages;
    });

    // Add processing message immediately
    const processingMessageId = Date.now() + '_processing';
    const processingMessage = {
      id: processingMessageId,
      content: '🔮 Analyzing your birth chart...',
      role: 'assistant',
      timestamp: new Date().toISOString(),
      isTyping: true,
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

    // Loading messages for cycling
    const loadingMessages = [
      '🔮 Analyzing your birth chart...',
      '⭐ Consulting the cosmic energies...',
      '📊 Calculating planetary positions...',
      '🌟 Interpreting astrological patterns...',
      '✨ Preparing your personalized insights...'
    ];

    // Start cycling through loading messages
    let messageIndex = 0;
    const loadingInterval = setInterval(() => {
      messageIndex = (messageIndex + 1) % loadingMessages.length;
      setMessagesWithStorage(prev => prev.map(msg => 
        msg.id === processingMessageId 
          ? { ...msg, content: loadingMessages[messageIndex] }
          : msg
      ));
    }, 3000);

    try {
      const token = await AsyncStorage.getItem('authToken');
      
      const requestBody = {
        session_id: currentSessionId,
        question: messageText,
        language: language || 'english',
        response_style: 'detailed',
        premium_analysis: isPremiumAnalysis,
        native_name: birthData?.name,
        birth_details: {
          name: birthData.name,
          date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
          time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
          latitude: parseFloat(birthData.latitude),
          longitude: parseFloat(birthData.longitude),
          timezone: birthData.timezone || 'Asia/Kolkata',
          place: birthData.place || '',
          gender: birthData.gender || ''
        }
      };
      

      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat-v2/ask')}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
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
      pollForResponse(messageId, processingMessageId, currentSessionId, loadingInterval);

    } catch (error) {
      console.error('❌ Error sending message:', error);
      clearInterval(loadingInterval);
      
      // Replace processing message with error
      setMessagesWithStorage(prev => prev.map(msg => 
        msg.id === processingMessageId 
          ? { ...msg, content: 'Sorry, I encountered an error. Please try again.', isTyping: false }
          : msg
      ));
      setLoading(false);
      setIsTyping(false);
    }
  };

  const handleLanguageChange = async (newLanguage) => {
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
        message: `🔮 AstroRoshni Chat\n\n${chatText}\n\nShared from AstroRoshni App`,
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

  const renderMessage = ({ item }) => (
    <MessageBubble message={item} language={language} />
  );

  const renderSuggestion = ({ item }) => (
    <TouchableOpacity
      style={styles.suggestionButton}
      onPress={() => setInputText(item)}
    >
      <Text style={styles.suggestionText}>{item}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a0033" translucent={false} />
      <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']} style={styles.gradientBg}>
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView 
          style={styles.keyboardAvoidingView}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={0}
        >
        {/* Header */}
        <View style={styles.headerContainer}>
          <LinearGradient
            colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
            style={styles.header}
          >
            {!showGreeting && (
              <TouchableOpacity
                style={styles.backButton}
                onPress={() => setShowGreeting(true)}
              >
                <Ionicons name="arrow-back" size={20} color={COLORS.white} />
              </TouchableOpacity>
            )}
            
            <View style={styles.headerCenter}>
              {showGreeting ? (
                <Text style={styles.headerTitle}>🌟 AstroRoshni</Text>
              ) : (
                <Text style={styles.headerTitle}>Chat</Text>
              )}
              {birthData && (
                <TouchableOpacity onPress={() => navigation.navigate('SelectNative')} style={styles.nameChip}>
                  <Text style={styles.nameChipText}>{birthData.name?.slice(0, 12)}{birthData.name?.length > 12 ? '...' : ''}</Text>
                </TouchableOpacity>
              )}
            </View>
            
            <View style={styles.headerRight}>
              <TouchableOpacity
                style={[styles.creditButton, isPremiumAnalysis && styles.creditButtonPremium]}
                onPress={() => navigation.navigate('Credits')}
              >
                <Text style={styles.creditText}>
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
                <Ionicons name="menu" size={20} color={COLORS.white} />
              </TouchableOpacity>
            </View>
          </LinearGradient>
        </View>

        {/* Content */}
        {showGreeting ? (
          <HomeScreen 
            birthData={birthData}
            onOptionSelect={handleGreetingOptionSelect}
          />
        ) : (
          <ScrollView 
            ref={scrollViewRef}
            style={styles.messagesContainer}
            contentContainerStyle={styles.messagesContent}
            showsVerticalScrollIndicator={false}
          >
            {/* Signs Display */}
            {birthData && (
              <View style={styles.signsContainer}>
                <LinearGradient
                  colors={['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']}
                  style={styles.signsGradient}
                >
                  <Text style={styles.signsTitle}>✨ {birthData.name}'s Chart Essence</Text>
                  <View style={styles.signsRow}>
                    <View style={styles.signItem}>
                      <Text style={styles.signLabel}>☀️ Sun</Text>
                      <Text style={styles.signValue}>
                        {loadingChart ? '...' : `${getSignIcon(chartData?.planets?.Sun?.sign)} ${getSignName(chartData?.planets?.Sun?.sign)}`}
                      </Text>
                    </View>
                    <View style={styles.signItem}>
                      <Text style={styles.signLabel}>🌙 Moon</Text>
                      <Text style={styles.signValue}>
                        {loadingChart ? '...' : `${getSignIcon(chartData?.planets?.Moon?.sign)} ${getSignName(chartData?.planets?.Moon?.sign)}`}
                      </Text>
                    </View>
                    <View style={styles.signItem}>
                      <Text style={styles.signLabel}>⬆️ Ascendant</Text>
                      <Text style={styles.signValue}>
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
                              style={[styles.dashaChip, { backgroundColor: planetColor + '20', borderColor: planetColor }]}
                              onPress={() => setShowDashaBrowser(true)}
                              activeOpacity={0.8}
                            >
                              <Text style={[styles.dashaChipPlanet, { color: planetColor }]}>{dasha.planet}</Text>
                              <Text style={styles.dashaChipDates}>{startDate}</Text>
                              <Text style={styles.dashaChipDates}>{endDate}</Text>
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
            
            {messages.map((item) => {
              return (
                <MessageBubble key={item.id} message={item} language={language} onFollowUpClick={setInputText} />
              );
            })}
          </ScrollView>
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
                    <Text style={styles.suggestionChipText}>{item}</Text>
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
              colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
              style={styles.inputBarGradient}
            >
              <TextInput
                style={styles.modernTextInput}
                value={inputText}
                onChangeText={setInputText}
                placeholder={loading ? "Analyzing..." : credits < chatCost ? "Insufficient credits" : "Ask me anything..."}
                placeholderTextColor="rgba(255, 255, 255, 0.5)"
                maxLength={500}
                editable={!loading && credits >= chatCost}
                multiline
              />
              
              <TouchableOpacity
                style={styles.premiumToggleButton}
                onPress={() => setIsPremiumAnalysis(!isPremiumAnalysis)}
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
                    </View>
                  )}
                </Animated.View>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.modernSendButton,
                  (loading || !inputText.trim() || credits < (isPremiumAnalysis ? premiumChatCost : chatCost)) && styles.modernSendButtonDisabled
                ]}
                onPress={() => sendMessage()}
                disabled={loading || !inputText.trim() || credits < (isPremiumAnalysis ? premiumChatCost : chatCost)}
              >
                <LinearGradient
                  colors={isPremiumAnalysis ? ['#ffd700', '#ff6b35'] : ['#ff6b35', '#ff8c5a']}
                  style={styles.modernSendGradient}
                >
                  {loading ? (
                    <Text style={styles.modernSendText}>⏳</Text>
                  ) : credits < (isPremiumAnalysis ? premiumChatCost : chatCost) ? (
                    <Text style={styles.modernSendText}>💳</Text>
                  ) : (
                    <Ionicons name="send" size={20} color={COLORS.white} />
                  )}
                </LinearGradient>
              </TouchableOpacity>
            </LinearGradient>
            
            {credits < (isPremiumAnalysis ? premiumChatCost : chatCost) && (
              <TouchableOpacity 
                style={styles.lowCreditBanner}
                onPress={() => navigation.navigate('Credits')}
              >
                <Text style={styles.lowCreditText}>💳 Get more credits to continue</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* Quick Actions Bar */}
        {!showGreeting && (
          <View style={styles.quickActionsBar}>
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => navigation.navigate('Chart', { birthData })}
            >
              <Ionicons name="pie-chart-outline" size={18} color="rgba(255, 255, 255, 0.8)" />
              <Text style={styles.quickActionText}>Chart</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => setShowDashaBrowser(true)}
            >
              <Ionicons name="time-outline" size={18} color="rgba(255, 255, 255, 0.8)" />
              <Text style={styles.quickActionText}>Dasha</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => setShowEventPeriods(true)}
            >
              <Ionicons name="calendar-outline" size={18} color="rgba(255, 255, 255, 0.8)" />
              <Text style={styles.quickActionText}>Events</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => navigation.navigate('AnalysisHub')}
            >
              <Ionicons name="analytics-outline" size={18} color="rgba(255, 255, 255, 0.8)" />
              <Text style={styles.quickActionText}>Analysis</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => navigation.navigate('ChatHistory')}
            >
              <Ionicons name="chatbubbles-outline" size={18} color="rgba(255, 255, 255, 0.8)" />
              <Text style={styles.quickActionText}>History</Text>
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
              <Text style={styles.modalTitle}>🌐 Select Language</Text>
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
                <Text style={styles.modalCloseText}>Close</Text>
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
                colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']}
                style={styles.drawerGradient}
              >
                <View style={styles.drawerHeader}>
                  <View style={styles.cosmicOrbSmall}>
                    <LinearGradient
                      colors={['#ff6b35', '#ffd700', '#ff6b35']}
                      style={styles.orbGradientSmall}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 1 }}
                    >
                      <Text style={styles.orbIconSmall}>🔮</Text>
                    </LinearGradient>
                  </View>
                  <Text style={styles.drawerTitle}>Cosmic Menu</Text>
                  <Text style={styles.drawerSubtitle}>Navigate Your Journey</Text>
                </View>

                <ScrollView 
                  ref={menuScrollViewRef}
                  style={styles.menuScrollView}
                  contentContainerStyle={styles.menuScrollContent}
                  showsVerticalScrollIndicator={false}
                  nestedScrollEnabled={true}
                >
                  <TouchableOpacity
                    style={styles.menuOption}
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
                      colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                      style={styles.menuGradient}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>✨</Text>
                        </LinearGradient>
                      </View>
                      <Text style={styles.menuText}>My Profile</Text>
                      <Ionicons name="chevron-forward" size={20} color="rgba(255, 255, 255, 0.6)" />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.menuOption}
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
                      colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                      style={styles.menuGradient}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>👤</Text>
                        </LinearGradient>
                      </View>
                      <Text style={styles.menuText}>Select Native</Text>
                      <Ionicons name="chevron-forward" size={20} color="rgba(255, 255, 255, 0.6)" />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.menuOption}
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
                      colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                      style={styles.menuGradient}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>➕</Text>
                        </LinearGradient>
                      </View>
                      <Text style={styles.menuText}>New Native</Text>
                      <Ionicons name="chevron-forward" size={20} color="rgba(255, 255, 255, 0.6)" />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.menuOption}
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
                      colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                      style={styles.menuGradient}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>📊</Text>
                        </LinearGradient>
                      </View>
                      <Text style={styles.menuText}>View Chart</Text>
                      <Ionicons name="chevron-forward" size={20} color="rgba(255, 255, 255, 0.6)" />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.menuOption}
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
                      colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                      style={styles.menuGradient}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>⏰</Text>
                        </LinearGradient>
                      </View>
                      <Text style={styles.menuText}>Dasha Browser</Text>
                      <Ionicons name="chevron-forward" size={20} color="rgba(255, 255, 255, 0.6)" />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.menuOption}
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
                      colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                      style={styles.menuGradient}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>💳</Text>
                        </LinearGradient>
                      </View>
                      <Text style={styles.menuText}>Credits</Text>
                      <Ionicons name="chevron-forward" size={20} color="rgba(255, 255, 255, 0.6)" />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.menuOption}
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
                      colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                      style={styles.menuGradient}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🔮</Text>
                        </LinearGradient>
                      </View>
                      <Text style={styles.menuText}>Life Analysis</Text>
                      <Ionicons name="chevron-forward" size={20} color="rgba(255, 255, 255, 0.6)" />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.menuOption}
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
                      colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                      style={styles.menuGradient}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>💬</Text>
                        </LinearGradient>
                      </View>
                      <Text style={styles.menuText}>Chat History</Text>
                      <Ionicons name="chevron-forward" size={20} color="rgba(255, 255, 255, 0.6)" />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.menuOption}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        setShowLanguageModal(true);
                      });
                    }}
                  >
                    <LinearGradient
                      colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                      style={styles.menuGradient}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🌐</Text>
                        </LinearGradient>
                      </View>
                      <Text style={styles.menuText}>Language</Text>
                      <Ionicons name="chevron-forward" size={20} color="rgba(255, 255, 255, 0.6)" />
                    </LinearGradient>
                  </TouchableOpacity>



                  <TouchableOpacity
                    style={[styles.menuOption, styles.menuOptionLast]}
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
                      style={styles.menuGradient}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff3b30', '#ff6b60']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🚪</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: '#ff6b60' }]}>Logout</Text>
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
                      <Text style={styles.benefitIcon}>🔮</Text>
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
        </KeyboardAvoidingView>
      </SafeAreaView>
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
    borderColor: 'rgba(255, 255, 255, 0.2)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 6,
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
    color: COLORS.white,
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
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
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
    color: COLORS.white,
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
    borderColor: 'rgba(255, 255, 255, 0.2)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
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
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
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
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 6,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  drawerSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
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
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
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
    color: COLORS.white,
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
});