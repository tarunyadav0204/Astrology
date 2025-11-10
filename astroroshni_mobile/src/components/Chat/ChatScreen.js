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
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';

import MessageBubble from './MessageBubble';
import { storage } from '../../services/storage';
import { COLORS, LANGUAGES, API_BASE_URL } from '../../utils/constants';
import ChartScreen from '../Chart/ChartScreen';

export default function ChatScreen({ navigation }) {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState('english');
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [showChart, setShowChart] = useState(false);
  const [birthData, setBirthData] = useState(null);
  const scrollViewRef = useRef(null);

  const suggestions = [
    "What does my birth chart say about my career?",
    "When is a good time for marriage?",
    "What are my health vulnerabilities?",
    "Tell me about my current dasha period",
    "What do the current transits mean for me?",
    "What are my strengths and weaknesses?"
  ];

  useEffect(() => {
    checkBirthData();
    loadLanguagePreference();
  }, []);

  useEffect(() => {
    if (birthData) {
      loadChatHistory();
    }
  }, [birthData]);

  const addGreetingMessage = () => {
    const place = birthData.place && !birthData.place.includes(',') ? birthData.place : `${birthData.latitude}, ${birthData.longitude}`;
    const greetingMessage = {
      id: 'greeting-' + Date.now(),
      role: 'assistant',
      content: `Hello ${birthData.name}! I see you were born on ${new Date(birthData.date).toLocaleDateString()} at ${place}. I'm here to help you understand your birth chart and provide astrological guidance. What would you like to know about your cosmic blueprint?`,
      timestamp: new Date().toISOString()
    };
    setMessages([greetingMessage]);
  };

  const checkBirthData = async () => {
    try {
      const savedBirthData = await storage.getBirthDetails();
      if (savedBirthData) {
        setBirthData(savedBirthData);
      } else {
        navigation.navigate('BirthForm');
      }
    } catch (error) {
      console.error('Error checking birth data:', error);
      navigation.navigate('BirthForm');
    }
  };

  const loadChatHistory = async () => {
    try {
      if (!birthData) return;
      const response = await fetch(`${API_BASE_URL}/api/chat/history`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(birthData)
      });
      const data = await response.json();
      const existingMessages = data.messages || [];
      setMessages(existingMessages);
      
      // Add greeting if no existing messages
      if (existingMessages.length === 0) {
        addGreetingMessage();
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
      // Add greeting on error too
      addGreetingMessage();
    }
  };

  const loadLanguagePreference = async () => {
    const savedLanguage = await storage.getLanguage();
    if (savedLanguage) {
      setLanguage(savedLanguage);
    }
  };

  const sendMessage = async (messageText = inputText) => {
    if (!messageText.trim() || !birthData) return;

    const userMessage = {
      id: Date.now().toString(),
      content: messageText,
      role: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setLoading(true);

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
      
      const requestBody = { ...fixedBirthData, question: messageText, language, response_style: 'detailed' };
      console.log('Sending chat request:', JSON.stringify(requestBody, null, 2));
      
      const response = await fetch(`${API_BASE_URL}/api/chat/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      console.log('Chat response status:', response.status);

      if (!response.ok) {
        throw new Error(`Chat API error: ${response.status}`);
      }

      let assistantMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString()
      };

      // Clear loading interval and replace typing message with actual response
      clearInterval(loadingInterval);
      setMessages(prev => [
        ...prev.filter(msg => msg.id !== typingMessageId),
        assistantMessage
      ]);

      // Check if response supports streaming
      if (response.body && response.body.getReader) {
        // Handle streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim();
              if (data === '[DONE]') break;
              if (data && data.length > 0) {
                try {
                  // First decode HTML entities in the raw data
                  const cleanData = data
                    .replace(/&quot;/g, '"')
                    .replace(/&amp;/g, '&')
                    .replace(/&lt;/g, '<')
                    .replace(/&gt;/g, '>')
                    .replace(/&#39;/g, "'")
                    .replace(/&nbsp;/g, ' ');
                  const parsed = JSON.parse(cleanData);
                  
                  if (parsed.status === 'complete' && parsed.response) {
                    // Decode HTML entities in the response content
                    let responseText = parsed.response
                      .replace(/&quot;/g, '"')
                      .replace(/&amp;/g, '&')
                      .replace(/&lt;/g, '<')
                      .replace(/&gt;/g, '>')
                      .replace(/&#39;/g, "'")
                      .replace(/&nbsp;/g, ' ')
                      .trim();
                    
                    if (responseText.length > 0) {
                      assistantMessage.content = responseText;
                      setMessages(prev => 
                        prev.map(msg => 
                          msg.id === assistantMessage.id ? { ...assistantMessage } : msg
                        )
                      );
                    }
                  } else if (parsed.status === 'error') {
                    console.log('API Error:', parsed.error);
                    assistantMessage.content = `Sorry, I encountered an error: ${parsed.error || 'Unknown error'}. Please try again.`;
                    setMessages(prev => 
                      prev.map(msg => 
                        msg.id === assistantMessage.id ? { ...assistantMessage } : msg
                      )
                    );
                  } else if (parsed.status === 'streaming' && parsed.content) {
                    assistantMessage.content += parsed.content;
                    setMessages(prev => 
                      prev.map(msg => 
                        msg.id === assistantMessage.id ? { ...assistantMessage } : msg
                      )
                    );
                  }
                } catch (e) {
                  const statusMatch = data.match(/"status"\s*:\s*"([^"]+)"/);
                  const responseMatch = data.match(/"response"\s*:\s*"((?:[^"\\]|\\.)*)"/);
                  
                  if (statusMatch && responseMatch && statusMatch[1] === 'complete') {
                    let response = responseMatch[1]
                      .replace(/\\n/g, '\n')
                      .replace(/\\"/g, '"')
                      .replace(/&quot;/g, '"')
                      .replace(/&amp;/g, '&')
                      .replace(/&lt;/g, '<')
                      .replace(/&gt;/g, '>')
                      .replace(/&#39;/g, "'")
                      .replace(/&nbsp;/g, ' ');
                    assistantMessage.content = response;
                    setMessages(prev => 
                      prev.map(msg => 
                        msg.id === assistantMessage.id ? { ...assistantMessage } : msg
                      )
                    );
                  }
                }
              }
            }
          }
        }
      } else {
        // Handle non-streaming response (fallback)
        const responseText = await response.text();
        
        console.log('Response text:', responseText.substring(0, 200));
        
        // Check if it's SSE format
        if (responseText.includes('data:')) {
          const lines = responseText.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim();
              if (data && data !== '[DONE]') {
                try {
                  const parsed = JSON.parse(data);
                  console.log('Parsed SSE data:', parsed);
                  if (parsed.status === 'complete' && parsed.response) {
                    // Decode HTML entities in response
                    let responseText = parsed.response
                      .replace(/&quot;/g, '"')
                      .replace(/&amp;/g, '&')
                      .replace(/&lt;/g, '<')
                      .replace(/&gt;/g, '>')
                      .replace(/&#39;/g, "'")
                      .replace(/&nbsp;/g, ' ');
                    assistantMessage.content = responseText;
                    setMessages(prev => 
                      prev.map(msg => 
                        msg.id === assistantMessage.id ? { ...assistantMessage } : msg
                      )
                    );
                    break;
                  }
                } catch (e) {
                  console.log('Parse error for line:', data);
                }
              }
            }
          }
        } else {
          // Try parsing as regular JSON
          try {
            const data = JSON.parse(responseText);
            console.log('Parsed JSON data:', data);
            if (data.response) {
              // Decode HTML entities in response
              let responseText = data.response
                .replace(/&quot;/g, '"')
                .replace(/&amp;/g, '&')
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>')
                .replace(/&#39;/g, "'")
                .replace(/&nbsp;/g, ' ');
              assistantMessage.content = responseText;
            } else if (data.error) {
              assistantMessage.content = `Sorry, I encountered an error: ${data.error}. Please try again.`;
            } else {
              assistantMessage.content = 'No response received from server.';
            }
          } catch (e) {
            console.log('JSON parse failed, using raw text');
            // If all else fails, use the raw text
            assistantMessage.content = responseText || 'Sorry, I received an invalid response. Please try again.';
          }
          
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessage.id ? { ...assistantMessage } : msg
            )
          );
        }
        
        console.log('Final assistant message:', assistantMessage);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      clearInterval(loadingInterval);
      
      const errorMessage = {
        id: Date.now().toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        role: 'assistant',
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [
        ...prev.filter(msg => msg.id !== typingMessageId),
        errorMessage
      ]);
    } finally {
      setLoading(false);
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
            navigation.replace('Login');
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
      <SafeAreaView style={styles.safeArea}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>🔮 AstroRoshni</Text>
          <View style={styles.headerButtons}>
            <TouchableOpacity
              style={styles.headerButton}
              onPress={() => setShowLanguageModal(true)}
            >
              <Ionicons name="language" size={24} color={COLORS.white} />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.headerButton}
              onPress={() => setShowMenu(true)}
            >
              <Ionicons name="menu" size={24} color={COLORS.white} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Messages */}
        <ScrollView 
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
          onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
        >
          {messages.map((item) => (
            <MessageBubble key={item.id} message={item} language={language} onFollowUpClick={setInputText} />
          ))}
        </ScrollView>

        {/* Suggestions (only show when not loading) */}
        {!loading && (
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

        {/* Input */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.textInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder={loading ? "Analyzing your chart..." : "Ask me about your birth chart..."}
            placeholderTextColor={COLORS.gray}
            maxLength={500}
            editable={!loading}
          />
          <TouchableOpacity
            style={[styles.sendButton, (loading || !inputText.trim()) && styles.sendButtonDisabled]}
            onPress={() => sendMessage()}
            disabled={loading || !inputText.trim()}
          >
            <Text style={styles.sendButtonText}>
              {loading ? '...' : 'Send'}
            </Text>
          </TouchableOpacity>
        </View>

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
                  setShowChart(true);
                }}
              >
                <Ionicons name="bar-chart" size={20} color={COLORS.primary} />
                <Text style={styles.menuText}>View Chart</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.menuOption}
                onPress={() => {
                  setShowMenu(false);
                  navigation.setOptions({ addWelcomeMessage: setMessages });
                  navigation.navigate('BirthForm');
                }}
              >
                <Ionicons name="person" size={20} color={COLORS.primary} />
                <Text style={styles.menuText}>Birth Details</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.menuOption}
                onPress={() => {
                  setShowMenu(false);
                  shareChat();
                }}
              >
                <Ionicons name="share" size={20} color={COLORS.primary} />
                <Text style={styles.menuText}>Share Chat</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.menuOption}
                onPress={() => {
                  setShowMenu(false);
                  clearChat();
                }}
              >
                <Ionicons name="trash" size={20} color={COLORS.error} />
                <Text style={[styles.menuText, { color: COLORS.error }]}>Clear Chat</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.menuOption}
                onPress={() => {
                  setShowMenu(false);
                  logout();
                }}
              >
                <Ionicons name="log-out" size={20} color={COLORS.error} />
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

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.white,
  },
  headerButtons: {
    flexDirection: 'row',
  },
  headerButton: {
    marginLeft: 15,
    padding: 5,
  },
  messagesContainer: {
    flex: 1,
    height: Platform.OS === 'web' ? 'calc(100vh - 200px)' : undefined,
    maxHeight: Platform.OS === 'web' ? 'calc(100vh - 200px)' : undefined,
  },
  messagesContent: {
    padding: 10,
    flexGrow: 1,
  },
  suggestionsContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingVertical: 10,
  },
  suggestionsContent: {
    paddingHorizontal: 15,
  },
  suggestionButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 8,
    marginRight: 10,
  },
  suggestionText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '500',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  textInput: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 25,
    paddingHorizontal: 15,
    paddingVertical: 0,
    marginRight: 10,
    fontSize: 16,
    height: 50,
  },
  sendButton: {
    backgroundColor: COLORS.white,
    borderRadius: 25,
    paddingHorizontal: 20,
    paddingVertical: 15,
    justifyContent: 'center',
    alignItems: 'center',
    height: 50,
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  sendButtonText: {
    color: COLORS.primary,
    fontSize: 16,
    fontWeight: 'bold',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: COLORS.white,
    borderRadius: 20,
    padding: 20,
    width: '80%',
    maxHeight: '70%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.primary,
    textAlign: 'center',
    marginBottom: 20,
  },
  languageOption: {
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    backgroundColor: COLORS.lightGray,
  },
  languageOptionSelected: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
  },
  languageText: {
    fontSize: 16,
    color: COLORS.black,
  },
  menuOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    backgroundColor: COLORS.lightGray,
  },
  menuText: {
    fontSize: 16,
    color: COLORS.black,
    marginLeft: 10,
  },
  modalCloseButton: {
    backgroundColor: COLORS.primary,
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 10,
  },
  modalCloseText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: 'bold',
  },
});