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
} from 'react-native';
import { LinearGradient } from 'react-native-linear-gradient';
import Ionicons from 'react-native-vector-icons/Ionicons';
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
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState('english');
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [showChart, setShowChart] = useState(false);
  const [showEventPeriods, setShowEventPeriods] = useState(false);
  const [showDashaBrowser, setShowDashaBrowser] = useState(false);
  const [showGreeting, setShowGreeting] = useState(true);
  const [birthData, setBirthData] = useState(null);
  const scrollViewRef = useRef(null);

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

  useEffect(() => {
    const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
      if (!showGreeting) {
        setShowGreeting(true);
        setMessages([]);
        return true; // Prevent default back action
      }
      return false; // Allow default back action
    });

    return () => backHandler.remove();
  }, [showGreeting]);

  const fetchChatCost = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/credits/settings/chat-cost')}`);
      const data = await response.json();
      setChatCost(data.cost || 1);
    } catch (error) {
      console.error('Error fetching chat cost:', error);
    }
  };

  useEffect(() => {
    if (birthData) {
      loadChatHistory();
    }
  }, [birthData]);

  const handleGreetingOptionSelect = async (option) => {
    console.log('🎯 Greeting option selected:', option);
    if (option.action === 'periods') {
      console.log('📅 Opening Event Periods modal');
      console.log('📊 Birth data available:', !!birthData);
      setShowEventPeriods(true);
    } else {
      console.log('💬 Going to chat mode');
      setShowGreeting(false);
      
      // Get user data to differentiate from native
      let userData = null;
      try {
        userData = await storage.getUserData();
      } catch (error) {
        console.log('Could not get user data:', error);
      }
      
      const userName = userData?.name || 'User';
      const nativeName = birthData?.name || 'the native';
      
      // Create personalized welcome message
      let welcomeContent;
      if (userName.toLowerCase() === nativeName.toLowerCase()) {
        // User and native are the same person
        welcomeContent = `🌟 Welcome to your personalized astrological consultation, ${nativeName}!\n\nI'm here to help you understand your birth chart and provide insights about your life path. Feel free to ask me anything about:\n\n• Your personality traits and characteristics\n• Career and professional guidance\n• Relationships and compatibility\n• Health and wellness insights\n• Timing for important decisions\n• Current planetary transits affecting you\n• Your strengths and areas for growth\n\nWhat would you like to explore first?`;
      } else {
        // User and native are different people
        welcomeContent = `🌟 Welcome ${userName}! I'm here to help you understand ${nativeName}'s birth chart and provide astrological insights.\n\nFeel free to ask me anything about ${nativeName}'s:\n\n• Personality traits and characteristics\n• Career and professional guidance\n• Relationships and compatibility\n• Health and wellness insights\n• Timing for important decisions\n• Current planetary transits affecting them\n• Strengths and areas for growth\n\nWhat would you like to explore first about ${nativeName}'s chart?`;
      }
      
      const welcomeMessage = {
        id: Date.now().toString(),
        content: welcomeContent,
        role: 'assistant',
        timestamp: new Date().toISOString(),
      };
      
      setMessages([welcomeMessage]);
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
    try {
      if (!birthData) return;
      const response = await chatAPI.getChatHistory(birthData);
      const existingMessages = response.data.messages || [];
      setMessages(existingMessages);
      
      // Show greeting if no existing messages, otherwise go to chat
      if (existingMessages.length === 0) {
        setShowGreeting(true);
      } else {
        setShowGreeting(false);
      }
    } catch (error) {
      // Show greeting on error too
      setShowGreeting(true);
    }
  };

  const loadLanguagePreference = async () => {
    const savedLanguage = await storage.getLanguage();
    if (savedLanguage) {
      setLanguage(savedLanguage);
    }
  };

  const saveMessageToHistory = async (message) => {
    try {
      if (!birthData) return;
      
      await chatAPI.saveMessage(birthData, {
        role: message.role,
        content: message.content,
        timestamp: message.timestamp
      });
    } catch (error) {
      console.warn('Error saving message to history:', error);
    }
  };

  const sendMessage = async (messageText = inputText) => {
    console.log('🚀 sendMessage called with:', { messageText, birthData: !!birthData });
    
    if (!messageText.trim() || !birthData) {
      console.log('❌ Validation failed:', { hasText: !!messageText.trim(), hasBirthData: !!birthData });
      return;
    }

    // Hide greeting when sending first message
    setShowGreeting(false);

    const userMessage = {
      id: Date.now().toString(),
      content: messageText,
      role: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setLoading(true);
    
    // Save user message to database
    await saveMessageToHistory(userMessage);
    
    // Scroll to bottom when user sends a message
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);

    // Add typing indicator with engaging messages like web version
    const loadingMessages = [
      '🔮 Analyzing your birth chart...',
      '⭐ Consulting the cosmic energies...',
      '📊 Calculating planetary positions...',
      '🌟 Interpreting astrological patterns...',
      '✨ Preparing your personalized insights...',
      '🌙 Reading lunar influences...',
      '☀️ Examining solar aspects...',
      '♃ Studying Jupiter blessings...',
      '♀ Analyzing Venus placements...',
      '♂ Checking Mars energy...',
      '☿ Decoding Mercury messages...',
      '♄ Understanding Saturn lessons...',
      '🐉 Exploring Rahu-Ketu axis...',
      '🏠 Examining house strengths...',
      '🔄 Calculating dasha periods...',
      '🎯 Identifying key yogas...',
      '🌊 Flowing through nakshatras...',
      '⚖️ Balancing planetary forces...',
      '🎭 Unveiling karmic patterns...',
      '🗝️ Unlocking hidden potentials...'
    ];
    
    // Add initial typing message
    const typingMessageId = Date.now() + '_typing';
    const typingMessage = {
      id: typingMessageId,
      content: loadingMessages[0],
      role: 'assistant',
      timestamp: new Date().toISOString(),
      isTyping: true,
    };
    
    setMessages(prev => [...prev, typingMessage]);
    
    // Cycle through loading messages
    let currentIndex = 0;
    const loadingInterval = setInterval(() => {
      currentIndex = (currentIndex + 1) % loadingMessages.length;
      
      setMessages(prev => {
        return prev.map(msg => 
          msg.id === typingMessageId 
            ? { ...msg, content: loadingMessages[currentIndex] }
            : msg
        );
      });
    }, 3000);

    // Retry function with exponential backoff
    const retryRequest = async (attempt = 1) => {
      try {
        // Fix date and time formats to match web version
        const fixedBirthData = { ...birthData };
        
        // Fix date format - extract YYYY-MM-DD from ISO string
        if (fixedBirthData.date && fixedBirthData.date.includes('T')) {
          fixedBirthData.date = fixedBirthData.date.split('T')[0]; // Extract YYYY-MM-DD
        }
        
        // Fix time format - extract HH:MM from ISO string
        if (fixedBirthData.time && fixedBirthData.time.includes('T')) {
          const timeDate = new Date(fixedBirthData.time);
          fixedBirthData.time = timeDate.toTimeString().slice(0, 5); // Extract HH:MM
        }
        
        // Get user context
        let userData = null;
        try {
          userData = await storage.getUserData();
        } catch (error) {
          console.log('Could not get user data:', error);
        }
        
        const userName = userData?.name || 'User';
        const nativeName = birthData?.name || 'Native';
        const relationship = (userName.toLowerCase() === nativeName.toLowerCase()) ? 'self' : 'other';
        
        const requestBody = { 
          ...fixedBirthData, 
          question: messageText, 
          language: language || 'english', 
          response_style: 'detailed',
          user_name: userName,
          user_relationship: relationship
        };
        const fullUrl = `${API_BASE_URL}${getEndpoint('/chat/ask')}`;
        console.log(`🌐 NETWORK REQUEST (attempt ${attempt})`);
        console.log(`📍 Full URL: ${fullUrl}`);
        console.log(`📦 Request Body:`, JSON.stringify(requestBody, null, 2));
        
        // Update loading message for retries
        if (attempt > 1) {
          setMessages(prev => {
            return prev.map(msg => 
              msg.id === typingMessageId 
                ? { ...msg, content: `🔄 Server busy, retrying... (attempt ${attempt} of 3)` }
                : msg
            );
          });
        }
        
        // Get auth token for authenticated request
        const token = await AsyncStorage.getItem('authToken');
        const headers = {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        };
        
        const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat/ask')}`, {
          method: 'POST',
          headers,
          body: JSON.stringify(requestBody)
        });

        console.log(`✅ NETWORK RESPONSE: ${response.status}`);
        console.log(`🔗 Response URL: ${response.url}`);
        console.log(`📊 Response Headers:`, response.headers);

        // Check for server errors that should trigger retry
        if (response.status === 502 || response.status === 503 || response.status === 504) {
          throw new Error(`Server error: ${response.status}`);
        }

        if (!response.ok) {
          throw new Error(`Chat API error: ${response.status}`);
        }
        
        return response;
      } catch (error) {
        const isRetryableError = error.message.includes('502') || 
                               error.message.includes('503') || 
                               error.message.includes('504') || 
                               error.message.includes('upstream') ||
                               error.message.includes('Network') ||
                               error.message.includes('fetch');
        
        if (isRetryableError && attempt < 3) {
          const delay = Math.min(1000 * Math.pow(2, attempt - 1), 4000); // 1s, 2s, 4s
          console.log(`Retrying in ${delay}ms due to:`, error.message);
          
          // Show retry message
          setMessages(prev => {
            return prev.map(msg => 
              msg.id === typingMessageId 
                ? { ...msg, content: `⏳ Connection issue detected, retrying in ${delay/1000}s...` }
                : msg
            );
          });
          
          await new Promise(resolve => setTimeout(resolve, delay));
          return retryRequest(attempt + 1);
        }
        throw error;
      }
    };
    
    try {
      const response = await retryRequest();

      let assistantMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString()
      };
      
      // Update balance after successful response
      fetchBalance();

      // Clear loading interval and replace typing message with actual response
      clearInterval(loadingInterval);
      setMessages(prev => [
        ...prev.filter(msg => msg.id !== typingMessageId),
        assistantMessage
      ]);

      // Handle response exactly like web version
      const responseText = await response.text();
      console.log('Full response text:', responseText);
      
      let hasReceivedContent = false;
      
      // Process SSE format exactly like web
      const lines = responseText.split('\n').filter(line => line.trim());
      console.log('Total lines to process:', lines.length);
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          console.log('Processing data:', data);
          
          if (data === '[DONE]') break;
          if (data && data.length > 0) {
            try {
              console.log('DEBUG: Attempting to parse JSON data');
              // Decode HTML entities exactly like web version
              const decodeHtmlEntities = (text) => {
                // For React Native, we can't use textarea, so use manual replacement
                return text
                  .replace(/&quot;/g, '"')
                  .replace(/&amp;/g, '&')
                  .replace(/&lt;/g, '<')
                  .replace(/&gt;/g, '>')
                  .replace(/&#39;/g, "'")
                  .replace(/&nbsp;/g, ' ');
              };
              
              // First try to parse as-is, then decode if needed (exactly like web)
              let parsed;
              try {
                parsed = JSON.parse(data);
                console.log('DEBUG: JSON parsed successfully, status:', parsed.status);
              } catch (parseError) {
                console.log('DEBUG: Direct JSON parse failed, trying with HTML decode');
                // If direct parsing fails, try decoding first
                const decodedData = decodeHtmlEntities(data);
                parsed = JSON.parse(decodedData);
                console.log('DEBUG: JSON parsed after HTML decode, status:', parsed.status);
              }
              
              console.log('Parsed data:', parsed);
              
              // Handle chunks like web version
              if (parsed.status === 'chunk') {
                console.log('DEBUG: Processing chunk response', parsed.chunk_index, 'of', parsed.total_chunks);
                // Decode HTML entities in chunk content
                let chunkContent = parsed.response || '';
                if (chunkContent.includes('&lt;') || chunkContent.includes('&gt;') || chunkContent.includes('&quot;') || chunkContent.includes('&#39;')) {
                  chunkContent = decodeHtmlEntities(chunkContent);
                }
                assistantMessage.content += chunkContent;
                hasReceivedContent = true;
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[newMessages.length - 1] = { ...assistantMessage };
                  return newMessages;
                });
              } else if (parsed.status === 'complete' && parsed.response) {
                // Decode HTML entities in complete response
                let responseContent = parsed.response;
                if (responseContent.includes('&lt;') || responseContent.includes('&gt;') || responseContent.includes('&quot;') || responseContent.includes('&#39;')) {
                  responseContent = decodeHtmlEntities(responseContent);
                }
                assistantMessage.content = responseContent;
                hasReceivedContent = true;
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[newMessages.length - 1] = { ...assistantMessage };
                  return newMessages;
                });
                break;
              } else if (parsed.status === 'complete') {
                // Complete without response means use accumulated content
                console.log('DEBUG: Complete status without response, using accumulated content');
                break;
              } else if (parsed.status === 'error') {
                throw new Error(parsed.error || 'AI analysis failed');
              } else if (parsed.content) {
                // Decode HTML entities in content like web version
                let content = parsed.content;
                if (content.includes('&lt;') || content.includes('&gt;') || content.includes('&quot;') || content.includes('&#39;')) {
                  content = decodeHtmlEntities(content);
                }
                assistantMessage.content += content;
                hasReceivedContent = true;
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[newMessages.length - 1] = { ...assistantMessage };
                  return newMessages;
                });
              }
            } catch (parseError) {
              console.error('Error parsing chunk:', parseError);
              console.log('Raw data causing error:', data);
              
              // Try regex extraction as fallback
              const contentMatch = data.match(/["']content["']\s*:\s*["']((?:[^"'\\]|\\.)*)['"]/i);
              if (contentMatch) {
                const content = contentMatch[1]
                  .replace(/\\n/g, '\n')
                  .replace(/\\"/g, '"')
                  .replace(/\\\\/g, '/');
                console.log('Extracted content via regex:', content.substring(0, 100));
                assistantMessage.content += content;
                hasReceivedContent = true;
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[newMessages.length - 1] = { ...assistantMessage };
                  return newMessages;
                });
              }
            }
          }
        }
      }
      
      // Final validation like web version
      if (!hasReceivedContent || !assistantMessage.content.trim()) {
        console.error('Empty response detected:', { hasReceivedContent, content: assistantMessage.content });
        throw new Error('Empty response received - please try again');
      }
      
      // Save assistant message to database
      await saveMessageToHistory(assistantMessage);

    } catch (error) {
      console.error('Error sending message after retries:', error);
      clearInterval(loadingInterval);
      
      let errorContent = 'Sorry, I encountered an error. Please try again.';
      
      if (error.message.includes('502') || error.message.includes('503') || error.message.includes('upstream')) {
        errorContent = 'Server is experiencing high load. Please try again in a few moments.';
      } else if (error.message.includes('Network')) {
        errorContent = 'Network connection issue. Please check your internet and try again.';
      }
      
      // Remove empty assistant message and add error message
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== typingMessageId && !(msg.role === 'assistant' && !msg.content.trim()));
        return [...filtered, {
          id: Date.now().toString(),
          content: errorContent,
          role: 'assistant',
          timestamp: new Date().toISOString(),
        }];
      });
    } finally {
      setLoading(false);
      // Clean up any empty messages
      setTimeout(() => {
        setMessages(prev => prev.filter(msg => !(msg.role === 'assistant' && !msg.content.trim())));
      }, 1000);
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
    <LinearGradient colors={[COLORS.gradientStart, COLORS.gradientEnd]} style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#ff6f00" translucent={false} />
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView 
          style={styles.keyboardAvoidingView}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
        >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerTitleContainer}>
            <Text style={styles.headerTitle}>🌟 AstroRoshni</Text>
            <TouchableOpacity onPress={() => navigation.navigate('BirthForm')} style={styles.nameButton}>
              <Text style={styles.headerSubtitle}>with 👤 {birthData?.name} ▼</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.headerButtons}>
            <TouchableOpacity
              style={styles.creditButton}
              onPress={() => navigation.navigate('Credits')}
            >
              <Text style={styles.creditText}>💳 {credits}</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.headerButton}
              onPress={() => setShowLanguageModal(true)}
            >
              <Text style={styles.headerButtonText}>🌐</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.headerButton}
              onPress={() => setShowMenu(true)}
            >
              <Text style={styles.headerButtonText}>☰</Text>
            </TouchableOpacity>
          </View>
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
            {messages.map((item) => (
              <MessageBubble key={item.id} message={item} language={language} onFollowUpClick={setInputText} />
            ))}
          </ScrollView>
        )}

        {/* Suggestions (only show when not loading and not showing greeting) */}
        {!loading && !showGreeting && (
          <View style={styles.suggestionsContainer}>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.suggestionsContent}
            >
              {suggestions.map((item, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.suggestionButton}
                  onPress={() => setInputText(item)}
                >
                  <Text style={styles.suggestionText}>{item}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Credit cost info */}
        {!showGreeting && (
          <View style={styles.creditInfo}>
            <Text style={styles.creditInfoText}>
              Each question costs {chatCost} credit{chatCost > 1 ? 's' : ''} • Balance: {credits}
            </Text>
            {credits < chatCost && (
              <TouchableOpacity onPress={() => navigation.navigate('Credits')}>
                <Text style={styles.lowCreditWarning}>Get more credits</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* Input (only show when not showing greeting) */}
        {!showGreeting && (
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.textInput}
              value={inputText}
              onChangeText={setInputText}
              placeholder={loading ? "Analyzing your chart..." : credits < chatCost ? "Insufficient credits" : "Ask me about your birth chart..."}
              placeholderTextColor={COLORS.gray}
              maxLength={500}
              editable={!loading && credits >= chatCost}
            />
            <TouchableOpacity
              style={[styles.sendButton, (loading || !inputText.trim() || credits < chatCost) && styles.sendButtonDisabled]}
              onPress={() => sendMessage()}
              disabled={loading || !inputText.trim() || credits < chatCost}
            >
              <Text style={styles.sendButtonText}>
                {loading ? '...' : credits < chatCost ? 'No Credits' : 'Send'}
              </Text>
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

        {/* Menu Modal */}
        <Modal
          visible={showMenu}
          transparent
          animationType="slide"
          onRequestClose={() => setShowMenu(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Menu</Text>
              
              <TouchableOpacity
                style={styles.menuOption}
                onPress={() => {
                  setShowMenu(false);
                  navigation.setOptions({ addWelcomeMessage: setMessages });
                  navigation.navigate('BirthForm');
                }}
              >
                <Text style={styles.menuIcon}>👤</Text>
                <Text style={styles.menuText}>Select Native</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.menuOption}
                onPress={() => {
                  setShowMenu(false);
                  setShowChart(true);
                }}
              >
                <Text style={styles.menuIcon}>📊</Text>
                <Text style={styles.menuText}>View Chart</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.menuOption}
                onPress={() => {
                  setShowMenu(false);
                  setShowDashaBrowser(true);
                }}
              >
                <Text style={styles.menuIcon}>⏰</Text>
                <Text style={styles.menuText}>Dasha Browser</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.menuOption}
                onPress={() => {
                  setShowMenu(false);
                  navigation.navigate('Credits');
                }}
              >
                <Text style={styles.menuIcon}>💳</Text>
                <Text style={styles.menuText}>Credits</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.menuOption}
                onPress={() => {
                  setShowMenu(false);
                  navigation.navigate('ChatHistory');
                }}
              >
                <Text style={styles.menuIcon}>💬</Text>
                <Text style={styles.menuText}>Chat History</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.menuOption}
                onPress={() => {
                  setShowMenu(false);
                  setShowGreeting(true);
                  setMessages([]);
                }}
              >
                <Text style={styles.menuIcon}>🏠</Text>
                <Text style={styles.menuText}>Back to Home</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.menuOption}
                onPress={() => {
                  setShowMenu(false);
                  logout();
                }}
              >
                <Text style={[styles.menuIcon, { color: COLORS.error }]}>🚪</Text>
                <Text style={[styles.menuText, { color: COLORS.error }]}>Logout</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.modalCloseButton}
                onPress={() => setShowMenu(false)}
              >
                <Text style={styles.modalCloseText}>Close</Text>
              </TouchableOpacity>
            </View>
          </View>
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
              console.log('🎯 Period selected:', period);
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
        </KeyboardAvoidingView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  headerTitleContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
    lineHeight: 20,
  },
  headerSubtitle: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.accent,
    marginTop: 1,
    marginLeft: 22,
    opacity: 0.9,
  },
  nameButton: {
    paddingVertical: 2,
    paddingHorizontal: 4,
    borderRadius: 4,
  },
  headerButtons: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  creditButton: {
    marginRight: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: COLORS.primary,
  },
  creditText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
  headerButton: {
    marginLeft: 12,
    padding: 8,
    borderRadius: 20,
    backgroundColor: COLORS.lightGray,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  headerButtonText: {
    fontSize: 20,
    color: COLORS.accent,
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
    backgroundColor: COLORS.surface,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  suggestionsContent: {
    paddingHorizontal: 16,
  },
  suggestionButton: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.accent,
    borderRadius: 25,
    paddingHorizontal: 18,
    paddingVertical: 10,
    marginRight: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  suggestionText: {
    color: COLORS.accent,
    fontSize: 13,
    fontWeight: '600',
    textAlign: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 16,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  textInput: {
    flex: 1,
    backgroundColor: COLORS.surface,
    borderRadius: 25,
    paddingHorizontal: 18,
    paddingVertical: 12,
    marginRight: 12,
    fontSize: 16,
    minHeight: 50,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: COLORS.border,
    color: COLORS.textPrimary,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sendButton: {
    backgroundColor: COLORS.accent,
    borderRadius: 25,
    paddingHorizontal: 20,
    paddingVertical: 12,
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: 50,
    minWidth: 50,
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 4,
  },
  sendButtonDisabled: {
    opacity: 0.6,
    backgroundColor: COLORS.gray,
  },
  sendButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '700',
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
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    backgroundColor: COLORS.lightGray,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 1,
  },
  menuIcon: {
    fontSize: 20,
    color: COLORS.accent,
  },
  menuText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.black,
    marginLeft: 12,
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
  creditInfo: {
    backgroundColor: COLORS.surface,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  creditInfoText: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  lowCreditWarning: {
    fontSize: 12,
    color: COLORS.primary,
    fontWeight: '600',
  },
});