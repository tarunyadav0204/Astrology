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
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'react-native';

import MessageBubble from './MessageBubble';
import EventPeriods from './EventPeriods';
import ChatGreeting from './ChatGreeting';
import { storage } from '../../services/storage';
import { chatAPI } from '../../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS, LANGUAGES, API_BASE_URL, getEndpoint } from '../../utils/constants';
import ChartScreen from '../Chart/ChartScreen';
import CascadingDashaBrowser from '../Dasha/CascadingDashaBrowser';
import { useCredits } from '../../credits/CreditContext';

export default function ChatScreen({ navigation }) {
  const { credits, fetchBalance } = useCredits();
  const [chatCost, setChatCost] = useState(1);
  const [premiumChatCost, setPremiumChatCost] = useState(3);
  const [isPremiumAnalysis, setIsPremiumAnalysis] = useState(false);
  const [showEnhancedPopup, setShowEnhancedPopup] = useState(false);
  const [showPremiumBadge, setShowPremiumBadge] = useState(false);
  const glowAnim = useRef(new Animated.Value(0)).current;
  const badgeFadeAnim = useRef(new Animated.Value(0)).current;

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
  const [showChart, setShowChart] = useState(false);
  const [showEventPeriods, setShowEventPeriods] = useState(false);
  const [showDashaBrowser, setShowDashaBrowser] = useState(false);
  const [showGreeting, setShowGreeting] = useState(true);
  const [birthData, setBirthData] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [currentPersonId, setCurrentPersonId] = useState(null);
  const [pendingMessages, setPendingMessages] = useState(new Set());
  const scrollViewRef = useRef(null);
  
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
    console.log('🔍 Checking pending responses for person:', personId);
    const stored = await AsyncStorage.getItem(`pendingChatMessages_${personId}`);
    if (stored) {
      const pendingIds = JSON.parse(stored);
      console.log('🔍 Found pending message IDs:', pendingIds);
      pendingIds.forEach(messageId => {
        console.log('🔄 Resuming polling for pending message:', messageId);
        // Resume polling for each pending message
        pollForResponse(messageId, null, sessionId, null, true); // true = resume mode
      });
    } else {
      console.log('🔍 No pending messages found');
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



  useEffect(() => {
    checkBirthData();
    loadLanguagePreference();
    fetchChatCost();
    
    // Add focus listener to re-check birth data when returning to screen
    const unsubscribe = navigation.addListener('focus', () => {
      console.log('🔄 Chat screen focused, re-checking birth data...');
      checkBirthData();
    });
    
    return unsubscribe;
  }, [navigation]);

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
        console.log('👤 Person changed from', currentPersonId, 'to', personId);
        
        // Set person ID first to avoid null issues
        setCurrentPersonId(personId);
        
        // Load messages from storage immediately
        loadMessagesFromStorage(personId).then(storedMessages => {
          console.log('📱 PERSON_CHANGE: Found stored messages:', storedMessages.length);
          if (storedMessages.length > 0) {
            setMessages(storedMessages);
            setShowGreeting(false);
            
            // Check for processing messages and resume polling
            const processingMessage = storedMessages.find(msg => msg.isTyping && msg.messageId);
            if (processingMessage) {
              console.log('🔄 RESUMING polling for stored processing message:', processingMessage.messageId);
              setLoading(true);
              setIsTyping(true);
              // Use personId directly to avoid timing issues
              setTimeout(() => {
                pollForResponse(processingMessage.messageId, null, sessionId, null, true);
              }, 100);
            }
          } else {
            console.log('📱 No stored messages, showing greeting');
            setShowGreeting(true);
          }
        });
        
        // Check pending responses after person ID is set
        setTimeout(() => {
          checkPendingResponses(personId);
        }, 200);
      }
    }
  }, [birthData]);

  // Save messages to AsyncStorage per person (like web app)
  const saveMessagesToStorage = async (messages, personId = currentPersonId) => {
    if (!personId) return;
    try {
      await AsyncStorage.setItem(`chatMessages_${personId}`, JSON.stringify(messages));
      console.log('💾 Messages saved to storage for person:', personId);
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
        console.log('📱 Loaded messages from storage:', messages.length);
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
      console.log('💾 Saving messages to storage:', newMessages.length, 'for person:', personId);
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
      console.log('🔄 Screen focused, checking for stored messages...');
      if (currentPersonId) {
        loadMessagesFromStorage(currentPersonId).then(storedMessages => {
          console.log('📱 FOCUS: Found stored messages:', storedMessages.length);
          if (storedMessages.length > 0) {
            // Only update messages if we don't have any current messages to avoid overwriting
            setMessages(prev => prev.length === 0 ? storedMessages : prev);
            setShowGreeting(false);
            
            // Only resume polling if not already polling
            if (!loading && !isTyping) {
              const processingMessage = storedMessages.find(msg => msg.isTyping && msg.messageId);
              if (processingMessage) {
                console.log('🔄 FOCUS: Resuming polling for processing message:', processingMessage.messageId);
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
    console.log('🎯 Greeting option selected:', option);
    if (option.action === 'periods') {
      console.log('📅 Opening Event Periods modal');
      console.log('📊 Birth data available:', !!birthData);
      setShowEventPeriods(true);
    } else if (option.action === 'analysis') {
      navigation.navigate('AnalysisDetail', { 
        analysisType: option.type,
        title: `${option.type.charAt(0).toUpperCase() + option.type.slice(1)} Analysis`,
        cost: 5
      });
    } else {
      console.log('💬 Going to chat mode');
      
      // First load any existing chat history
      await loadChatHistory();
      
      // Check if we need to show welcome message
      setTimeout(async () => {
        const storedMessages = await loadMessagesFromStorage(currentPersonId);
        console.log('👋 Welcome check: stored messages:', storedMessages.length);
        if (storedMessages.length === 0 && messages.length === 0) {
          const welcomeMessage = {
            id: Date.now().toString(),
            content: `🌟 Welcome! I'm here to help you understand your birth chart and provide astrological insights.\n\nFeel free to ask me anything about:\n\n• Personality traits and characteristics\n• Career and professional guidance\n• Relationships and compatibility\n• Health and wellness insights\n• Timing for important decisions\n• Current planetary transits\n• Strengths and areas for growth\n\nWhat would you like to explore first?`,
            role: 'assistant',
            timestamp: new Date().toISOString(),
          };
          console.log('👋 Adding welcome message');
          setMessagesWithStorage([welcomeMessage]);
          setShowGreeting(false);
        }
      }, 100);
    }
  };

  const checkBirthData = async () => {
    try {
      const savedBirthData = await storage.getBirthDetails();
      console.log('📊 Raw birth data from storage:', savedBirthData);
      console.log('📊 Birth data type:', typeof savedBirthData);
      console.log('📊 Birth data keys:', savedBirthData ? Object.keys(savedBirthData) : 'null');
      
      if (savedBirthData && typeof savedBirthData === 'object' && savedBirthData.name && savedBirthData.name.trim()) {
        console.log('✅ Valid birth data found:', {
          name: savedBirthData.name,
          hasDate: !!savedBirthData.date,
          hasTime: !!savedBirthData.time,
          hasPlace: !!savedBirthData.place,
          hasCoords: !!(savedBirthData.latitude && savedBirthData.longitude)
        });
        setBirthData(savedBirthData);
      } else {
        console.log('❌ Invalid birth data:', {
          exists: !!savedBirthData,
          type: typeof savedBirthData,
          hasName: savedBirthData?.name,
          nameLength: savedBirthData?.name?.length
        });
        setBirthData(null);
        navigation.navigate('BirthForm');
      }
    } catch (error) {
      console.error('❌ Error checking birth data:', error);
      setBirthData(null);
      navigation.navigate('BirthForm');
    }
  };

  const loadChatHistory = async () => {
    console.log('📚 loadChatHistory called - skipping, using local storage');
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
        console.log('💾 Session saved:', newSessionId);
        
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
    console.log('🔄 Starting polling for messageId:', messageId, 'isResume:', isResume);
    console.log('🔄 Polling params:', { messageId, processingMessageId, currentSessionId, isResume });
    
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
        console.log('🔍 Polling attempt', pollCount + 1, 'for messageId:', messageId);
        const token = await AsyncStorage.getItem('authToken');
        const url = `${API_BASE_URL}${getEndpoint(`/chat-v2/status/${messageId}`)}`;
        console.log('🔍 Polling URL:', url);
        
        const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        console.log('🔍 Response status:', response.status);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('❌ Poll response error:', response.status, errorText);
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const status = await response.json();
        console.log('📊 Poll response for', messageId, ':', JSON.stringify(status, null, 2));
        
        if (status.status === 'completed') {
          console.log('✅ Message completed:', messageId);
          console.log('📝 Response content:', status.content);
          
          // Check if person changed during processing - use more reliable check
          const currentPersonIdNow = birthData ? `${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}` : null;
          console.log('🔍 Person check - current:', currentPersonId, 'calculated:', currentPersonIdNow);
          
          // Only skip if we have a clear person change (both IDs exist and are different)
          if (currentPersonId && currentPersonIdNow && currentPersonIdNow !== currentPersonId) {
            console.log('👤 Person actually changed during processing, cleaning up');
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
            console.log('📋 Updated messages with response:', updated.length);
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
          console.log('❌ Message failed:', messageId, status.error_message);
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
          console.log('⏳ Still processing, updating message:', randomMessage);
          
          setMessagesWithStorage(prev => {
            const updated = prev.map(msg => 
              msg.messageId === messageId 
                ? { ...msg, content: randomMessage }
                : msg
            );
            console.log('📋 Updated processing message, total messages:', updated.length);
            return updated;
          });
          
          pollCount++;
          if (pollCount < maxPolls) {
            setTimeout(poll, 3000);
          } else {
            // Timeout - show restart option
            console.log('⏰ Polling timeout for messageId:', messageId);
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
        } else {
          console.log('❓ Unexpected status:', status.status);
        }
        
      } catch (error) {
        console.error('❌ Polling error for messageId:', messageId, error);
        console.error('❌ Error details:', error.message, error.stack);
        
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
    console.log('🔄 Starting initial poll in 1 second...');
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
    console.log('🚀 sendMessage called with:', { messageText, birthData: !!birthData });
    
    if (!messageText.trim() || !birthData) {
      console.log('❌ Validation failed:', { hasText: !!messageText.trim(), hasBirthData: !!birthData });
      return;
    }

    console.log('✅ Starting sendMessage process');
    
    // Clear input and set states immediately
    setInputText('');
    setLoading(true);
    setIsTyping(true);
    setShowGreeting(false);

    console.log('📝 Input cleared, loading and typing set to true');
    
    // Remove test message code

    // Add user message immediately
    const userMessage = {
      id: Date.now().toString(),
      content: messageText,
      role: 'user',
      timestamp: new Date().toISOString(),
    };
    
    console.log('👤 Adding user message:', userMessage);
    setMessagesWithStorage(prev => {
      const newMessages = [...prev, userMessage];
      console.log('📋 Messages after adding user:', newMessages.length);
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
    
    console.log('🤖 Adding processing message:', processingMessage);
    setMessagesWithStorage(prev => {
      const newMessages = [...prev, processingMessage];
      console.log('📋 Messages after adding processing:', newMessages.length);
      return newMessages;
    });

    // Scroll to bottom
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);

    // Create session if needed
    let currentSessionId = sessionId;
    if (!currentSessionId) {
      console.log('🆕 Creating new session');
      currentSessionId = await createSession();
      if (!currentSessionId) {
        console.log('❌ Failed to create session');
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
      console.log('🌐 Making API request');
      const token = await AsyncStorage.getItem('authToken');
      
      const requestBody = {
        session_id: currentSessionId,
        question: messageText,
        language: language || 'english',
        response_style: 'detailed',
        premium_analysis: isPremiumAnalysis
      };
      
      console.log('📦 Request body:', requestBody);
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat-v2/ask')}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      });

      console.log('📡 API response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ API Error Response:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      console.log('📝 API Response:', result);
      
      const messageId = result.message_id;
      console.log('🆔 Got message ID:', messageId);

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
            <View style={styles.headerLeft}>
              <View style={styles.headerTitleRow}>
                <Text style={styles.headerTitle} numberOfLines={1} adjustsFontSizeToFit>🌟 AstroRoshni</Text>
                <TouchableOpacity onPress={() => navigation.navigate('SelectNative')} style={styles.nameChip}>
                  <LinearGradient
                    colors={['rgba(255, 255, 255, 0.25)', 'rgba(255, 255, 255, 0.15)']}
                    style={styles.nameChipGradient}
                  >
                    <Text style={styles.nameChipIcon}>👤</Text>
                    <Text style={styles.nameChipText} numberOfLines={1}>{birthData?.name?.slice(0, 8)}{birthData?.name?.length > 8 ? '...' : ''}</Text>
                    <Text style={styles.nameChipArrow}>▼</Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            </View>
            <View style={styles.headerButtons}>
              <TouchableOpacity
                style={styles.creditButton}
                onPress={() => navigation.navigate('Credits')}
              >
                <LinearGradient
                  colors={['#ff6b35', '#ff8c5a']}
                  style={styles.creditGradient}
                >
                  <Text style={styles.creditText}>💳 {credits}</Text>
                </LinearGradient>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.headerButton}
                onPress={() => setShowLanguageModal(true)}
              >
                <Text style={styles.headerButtonText}>🌐</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.headerButton}
                onPress={() => {
                  setShowMenu(true);
                  Animated.spring(drawerAnim, {
                    toValue: 0,
                    useNativeDriver: true,
                    tension: 65,
                    friction: 11,
                  }).start(() => {
                    // Reset scroll position when menu opens
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
          <ChatGreeting 
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
            {messages.map((item) => {
              console.log('📋 Rendering message:', item.id, 'role:', item.role, 'content length:', item.content?.length, 'isTyping:', item.isTyping);
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

        {/* Floating Premium Badge - Auto-hides after 3s */}
        {!showGreeting && showPremiumBadge && (
          <Animated.View
            style={[
              styles.floatingPremiumBadge,
              { opacity: badgeFadeAnim },
            ]}
          >
            <TouchableOpacity onPress={() => setShowEnhancedPopup(true)} style={styles.floatingBadgeContent}>
              <LinearGradient
                colors={['#ff6b35', '#ff8c5a']}
                style={styles.floatingBadgeGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
              >
                <Text style={styles.floatingBadgeText}>✨ Premium • {premiumChatCost} credits</Text>
              </LinearGradient>
            </TouchableOpacity>
          </Animated.View>
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
              onPress={() => setShowChart(true)}
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
                        setShowChart(true);
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

        {/* Chart Modal */}
        <ChartScreen 
          visible={showChart} 
          onClose={() => setShowChart(false)} 
        />

        {/* Event Periods Modal */}
        {showEventPeriods && (
          <EventPeriods 
            visible={showEventPeriods} 
            onClose={() => {
              console.log('📅 Closing Event Periods modal');
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
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.25)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 8,
  },
  headerLeft: {
    flex: 1,
    alignItems: 'flex-start',
  },
  headerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    width: '100%',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.white,
    textShadowColor: 'rgba(0, 0, 0, 0.4)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
    letterSpacing: 0.3,
    flexShrink: 1,
  },
  nameChip: {
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  nameChipGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  nameChipIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  nameChipText: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.white,
    marginRight: 4,
  },
  nameChipArrow: {
    fontSize: 10,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  headerButtons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  creditButton: {
    borderRadius: 18,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.4,
    shadowRadius: 6,
    elevation: 4,
  },
  creditGradient: {
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  creditText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '700',
  },
  headerButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerButtonText: {
    fontSize: 18,
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
  floatingPremiumBadge: {
    marginHorizontal: 12,
    marginBottom: 8,
  },
  floatingBadgeContent: {
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
    elevation: 6,
  },
  floatingBadgeGradient: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  floatingBadgeText: {
    color: COLORS.white,
    fontSize: 13,
    fontWeight: '700',
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