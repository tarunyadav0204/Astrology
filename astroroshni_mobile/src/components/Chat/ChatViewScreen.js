import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Share,
  StatusBar,
  Animated,
  Dimensions,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import MessageBubble from './MessageBubble';
import { storage } from '../../services/storage';
import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';

const { width } = Dimensions.get('window');
const DAY_SESSION_BATCH_SIZE = 2;

function getDateKey(timestamp) {
  if (!timestamp) return 'unknown';
  const d = new Date(timestamp);
  if (Number.isNaN(d.getTime())) return 'unknown';
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function mapSessionMessages(sessionData, dayKey = null) {
  const messages = (sessionData?.messages || []).map((msg, idx) => ({
    messageId: msg.message_id ?? msg.messageId,
    role:
      msg.sender === 'ai' || msg.sender === 'assistant'
        ? 'assistant'
        : msg.sender === 'user'
          ? 'user'
          : msg.sender,
    content: msg.content,
    timestamp: msg.completed_at || msg.timestamp,
    id: `${msg.message_id ?? msg.messageId ?? idx}_${msg.completed_at || msg.timestamp}`,
    native_name: msg.native_name ?? sessionData.native_name ?? null,
    terms: msg.terms,
    glossary: msg.glossary,
    images: msg.images,
    message_type: msg.message_type,
    intent_gate: msg.intent_gate,
    gate_metadata: msg.gate_metadata,
  }));

  return dayKey ? messages.filter((msg) => getDateKey(msg.timestamp) === dayKey) : messages;
}

function MessageRow({ message, index, sessionId, onDelete }) {
  return (
    <View>
      <MessageBubble
        message={message}
        language="english"
        onDelete={onDelete}
        sessionId={sessionId}
      />
    </View>
  );
}

export default function ChatViewScreen({ route, navigation }) {
  const { theme, colors, getCardElevation } = useTheme();
  const { session } = route.params;
  const [messages, setMessages] = useState(session.messages || []);
  const [isLoadingInitialMessages, setIsLoadingInitialMessages] = useState(false);
  const [isLoadingMoreMessages, setIsLoadingMoreMessages] = useState(false);
  const [loadMoreError, setLoadMoreError] = useState('');
  const daySessionIds = Array.from(new Set((session?.session_ids || []).filter(Boolean)));
  const isDayTranscript = daySessionIds.length > 0;
  const [loadedSessionCount, setLoadedSessionCount] = useState(
    isDayTranscript && Array.isArray(session.messages) && session.messages.length > 0
      ? daySessionIds.length
      : 0
  );
  
  const handleDeleteMessage = (messageId) => {
    setMessages(prev => prev.filter(msg => msg.messageId !== messageId));
  };
  
  // One conversation = one final assistant answer (clarification turns are excluded).
  const isUserMessage = (msg) => (msg?.sender || msg?.role) === 'user';
  const isAssistantMessage = (msg) => (msg?.sender || msg?.role) === 'assistant';
  const answerCount = messages.filter(
    (msg) => isAssistantMessage(msg) && msg?.message_type === 'answer'
  ).length;
  const conversationCount = answerCount > 0 ? answerCount : messages.filter(isUserMessage).length;
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const starAnims = useRef([...Array(15)].map(() => new Animated.Value(0))).current;
  const starPositions = useRef(
    [...Array(15)].map(() => ({
      top: `${Math.random() * 100}%`,
      left: `${Math.random() * 100}%`,
    }))
  ).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 8,
        useNativeDriver: true,
      }),
    ]).start();

    const pulseLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 1500,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1500,
          useNativeDriver: true,
        }),
      ])
    );
    pulseLoop.start();

    const starLoops = starAnims.map((anim, index) => {
      const loop = Animated.loop(
        Animated.sequence([
          Animated.delay(index * 150),
          Animated.timing(anim, {
            toValue: 1,
            duration: 2000,
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0,
            duration: 2000,
            useNativeDriver: true,
          }),
        ])
      );
      loop.start();
      return loop;
    });
    return () => {
      pulseLoop.stop();
      starLoops.forEach((loop) => loop?.stop?.());
    };
  }, []);

  useEffect(() => {
    if (!isDayTranscript || messages.length > 0 || loadedSessionCount > 0) {
      return;
    }

    let cancelled = false;

    const loadInitialBatch = async () => {
      setIsLoadingInitialMessages(true);
      setLoadMoreError('');
      try {
        const authToken = await storage.getAuthToken();
        if (!authToken) {
          navigation.replace('Login');
          return;
        }

        const batchSessionIds = daySessionIds.slice(0, DAY_SESSION_BATCH_SIZE);
        const responses = await Promise.all(
          batchSessionIds.map((sid) =>
            fetch(`${API_BASE_URL}${getEndpoint(`/chat-v2/session/${sid}`)}`, {
              method: 'GET',
              headers: { Authorization: `Bearer ${authToken}` },
            })
          )
        );

        if (cancelled) return;

        if (responses.some((response) => response.status === 401)) {
          await storage.removeAuthToken();
          navigation.replace('Login');
          return;
        }

        const okResponses = responses.filter((response) => response.ok);
        const sessions = await Promise.all(okResponses.map((response) => response.json()));
        const nextMessages = sessions
          .flatMap((sessionData) => mapSessionMessages(sessionData, session?.date_key))
          .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

        if (cancelled) return;

        setMessages(nextMessages);
        setLoadedSessionCount(batchSessionIds.length);
      } catch (error) {
        if (!cancelled) {
          setLoadMoreError('Failed to load messages for this day.');
        }
      } finally {
        if (!cancelled) {
          setIsLoadingInitialMessages(false);
        }
      }
    };

    loadInitialBatch();

    return () => {
      cancelled = true;
    };
  }, [daySessionIds, isDayTranscript, loadedSessionCount, messages.length, navigation, session?.date_key]);

  const hasMoreMessages = isDayTranscript && loadedSessionCount < daySessionIds.length;

  const loadMoreMessages = async () => {
    if (!hasMoreMessages || isLoadingMoreMessages) return;

    setIsLoadingMoreMessages(true);
    setLoadMoreError('');
    try {
      const authToken = await storage.getAuthToken();
      if (!authToken) {
        navigation.replace('Login');
        return;
      }

      const nextSessionIds = daySessionIds.slice(
        loadedSessionCount,
        loadedSessionCount + DAY_SESSION_BATCH_SIZE
      );
      const responses = await Promise.all(
        nextSessionIds.map((sid) =>
          fetch(`${API_BASE_URL}${getEndpoint(`/chat-v2/session/${sid}`)}`, {
            method: 'GET',
            headers: { Authorization: `Bearer ${authToken}` },
          })
        )
      );

      if (responses.some((response) => response.status === 401)) {
        await storage.removeAuthToken();
        navigation.replace('Login');
        return;
      }

      const okResponses = responses.filter((response) => response.ok);
      const sessions = await Promise.all(okResponses.map((response) => response.json()));
      const nextMessages = sessions.flatMap((sessionData) => mapSessionMessages(sessionData, session?.date_key));

      setMessages((prev) => {
        const seen = new Set(prev.map((msg) => msg.id || msg.messageId));
        const merged = [...prev];
        for (const message of nextMessages) {
          const key = message.id || message.messageId;
          if (!seen.has(key)) {
            seen.add(key);
            merged.push(message);
          }
        }
        merged.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
        return merged;
      });
      setLoadedSessionCount((prev) => prev + nextSessionIds.length);
    } catch (error) {
      setLoadMoreError('Failed to load more messages.');
    } finally {
      setIsLoadingMoreMessages(false);
    }
  };

  const getRelativeTime = (date) => {
    const now = new Date();
    const then = new Date(date);
    const diffMs = now - then;
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return then.toLocaleDateString();
  };

  const shareChat = async () => {
    try {
      if (!Array.isArray(messages) || messages.length === 0) {
        Alert.alert('No Messages', 'There are no messages to share.');
        return;
      }
      
      const chatText = messages
        .map(msg => `${msg.role === 'user' ? 'You' : 'AstroRoshni'}: ${msg.content}`)
        .join('\n\n');
      
      await Share.share({
        message: `🔮 AstroRoshni Chat - ${new Date(session.created_at || Date.now()).toLocaleDateString()}\n\n${chatText}\n\nShared from AstroRoshni App`,
      });
    } catch (error) {

    }
  };

  const continueConversation = () => {
    navigation.navigate('Home', { startChat: true });
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
      <LinearGradient colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.primary] : [colors.gradientStart, colors.gradientStart, colors.gradientStart, colors.gradientStart]} style={styles.gradient}>
        
        {/* Twinkling Stars */}
        {starAnims.map((anim, index) => {
          return (
            <Animated.View
              key={index}
              style={[
                styles.star,
                {
                  top: starPositions[index].top,
                  left: starPositions[index].left,
                  opacity: anim,
                },
              ]}
            >
              <Text style={styles.starText}>✨</Text>
            </Animated.View>
          );
        })}

        <SafeAreaView style={styles.safeArea}>
          
          {/* Header */}
          <Animated.View style={[styles.header, { opacity: fadeAnim }]}>
            <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
              <Icon name="arrow-back" size={24} color={colors.text} />
            </TouchableOpacity>
            
            <View style={styles.headerInfo}>
              <View style={styles.headerIconContainer}>
                <LinearGradient
                  colors={['#ff6b35', '#ff8c5a']}
                  style={styles.headerIconGradient}
                >
                  <Text style={styles.headerIcon}>💬</Text>
                </LinearGradient>
              </View>
              <View style={styles.headerTextContainer}>
                {session.native_name && (
                  <Text style={[styles.nativeName, { color: colors.text }]}>{session.native_name}</Text>
                )}
                <Text style={[styles.headerTitle, { color: colors.text }]}>
                  {session?.date_label || getRelativeTime(session.created_at)}
                </Text>
                <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>
                  {conversationCount} {conversationCount === 1 ? 'conversation' : 'conversations'}
                </Text>
              </View>
            </View>
            
            <TouchableOpacity style={styles.shareButton} onPress={shareChat}>
              <Icon name="share-outline" size={24} color={colors.text} />
            </TouchableOpacity>
          </Animated.View>

          {/* Info Card */}
          <Animated.View style={[
            styles.infoCard,
            {
              opacity: fadeAnim,
              transform: [{ translateY: slideAnim }],
              elevation: getCardElevation(5),
            }
          ]}>
            <LinearGradient
              colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.15)', 'rgba(249, 115, 22, 0.08)']}
              style={styles.infoGradient}
            >
              <View style={styles.infoItem}>
                <Icon name="calendar-outline" size={16} color={colors.textSecondary} />
                <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                  {(() => {
                    const firstMsg = messages.find(isUserMessage);
                    const timestamp = firstMsg?.timestamp || session.created_at;
                    const utcTimestamp = (timestamp && typeof timestamp === 'string')
                      ? (timestamp.includes('Z') ? timestamp : timestamp.replace(' ', 'T') + 'Z')
                      : (timestamp != null ? new Date(timestamp).toISOString() : new Date().toISOString());
                    return new Date(utcTimestamp).toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric', 
                      year: 'numeric' 
                    });
                  })()}
                </Text>
              </View>
              <View style={styles.infoDivider} />
              <View style={styles.infoItem}>
                <Icon name="time-outline" size={16} color={colors.textSecondary} />
                <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                  {(() => {
                    const firstMsg = messages.find(isUserMessage);
                    const timestamp = firstMsg?.timestamp || session.created_at;
                    const utcTimestamp = (timestamp && typeof timestamp === 'string')
                      ? (timestamp.includes('Z') ? timestamp : timestamp.replace(' ', 'T') + 'Z')
                      : (timestamp != null ? new Date(timestamp).toISOString() : new Date().toISOString());
                    const date = new Date(utcTimestamp);
                    return date.toLocaleTimeString('en-US', { 
                      hour: '2-digit', 
                      minute: '2-digit',
                      hour12: true
                    });
                  })()}
                </Text>
              </View>
              <View style={styles.infoDivider} />
              <View style={styles.infoItem}>
                <Icon name="chatbubbles-outline" size={16} color={colors.textSecondary} />
                <Text style={[styles.infoText, { color: colors.textSecondary }]}>{conversationCount}</Text>
              </View>
            </LinearGradient>
          </Animated.View>

          {/* Messages */}
          <FlatList
            data={messages}
            renderItem={({ item, index }) => (
              <MessageRow
                message={item}
                index={index}
                onDelete={handleDeleteMessage}
                sessionId={session?.session_id}
              />
            )}
            keyExtractor={(item, index) => String(item?.id || item?.messageId || `${item?.timestamp}_${index}`)}
            style={styles.messagesContainer}
            contentContainerStyle={styles.messagesContent}
            showsVerticalScrollIndicator={false}
            initialNumToRender={8}
            maxToRenderPerBatch={8}
            windowSize={7}
            removeClippedSubviews={Platform.OS === 'android'}
            ListEmptyComponent={
              isLoadingInitialMessages ? (
                <View style={styles.loadingState}>
                  <ActivityIndicator size="large" color="#ff6b35" />
                  <Text style={styles.loadingText}>Loading messages...</Text>
                </View>
              ) : (
              <Animated.View style={[styles.emptyState, { opacity: fadeAnim }]}>
                <Text style={styles.emptyIcon}>💬</Text>
                <Text style={styles.emptyText}>No messages to display</Text>
              </Animated.View>
              )
            }
            ListFooterComponent={
              <>
                {loadMoreError ? (
                  <View style={styles.loadMoreContainer}>
                    <Text style={styles.loadMoreError}>{loadMoreError}</Text>
                  </View>
                ) : null}
                {hasMoreMessages ? (
                  <View style={styles.loadMoreContainer}>
                    <TouchableOpacity
                      style={styles.loadMoreButton}
                      onPress={loadMoreMessages}
                      disabled={isLoadingMoreMessages}
                    >
                      {isLoadingMoreMessages ? (
                        <ActivityIndicator color="#ffffff" />
                      ) : (
                        <Text style={styles.loadMoreText}>Load more messages</Text>
                      )}
                    </TouchableOpacity>
                    <Text style={styles.loadMoreMeta}>
                      Loaded {loadedSessionCount} of {daySessionIds.length} chat sessions for this day
                    </Text>
                  </View>
                ) : null}
              </>
            }
          />

          {/* Floating Action Buttons */}
          <Animated.View style={[styles.floatingButtons, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
            <TouchableOpacity style={[styles.floatingButtonSecondary, { elevation: getCardElevation(5) }]} onPress={shareChat}>
              <LinearGradient
                colors={['rgba(255, 107, 53, 0.6)', 'rgba(255, 140, 90, 0.5)']}
                style={styles.floatingButtonGradient}
              >
                <Icon name="share-outline" size={20} color={colors.text} />
                <Text style={styles.floatingButtonText}>Share</Text>
              </LinearGradient>
            </TouchableOpacity>

            <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
              <TouchableOpacity style={[styles.floatingButtonPrimary, { elevation: getCardElevation(8) }]} onPress={continueConversation}>
                <LinearGradient
                  colors={['#ff6b35', '#ff8c5a']}
                  style={styles.floatingButtonGradient}
                >
                  <Icon name="chatbubbles" size={20} color={colors.text} />
                  <Text style={styles.floatingButtonTextPrimary}>Continue Chat</Text>
                  <Icon name="arrow-forward" size={20} color={colors.text} />
                </LinearGradient>
              </TouchableOpacity>
            </Animated.View>
          </Animated.View>

        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  star: { position: 'absolute' },
  starText: { fontSize: 10 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
  },
  headerIconContainer: {
    marginRight: 12,
  },
  headerIconGradient: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  headerIcon: { fontSize: 22 },
  headerTextContainer: { flex: 1 },
  nativeName: {
    fontSize: 18,
    fontWeight: '800',
    color: COLORS.white,
    marginBottom: 2,
  },
  headerTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.85)',
  },
  headerSubtitle: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 2,
  },
  shareButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  infoCard: {
    marginHorizontal: 20,
    marginBottom: 16,
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
        // elevation set dynamically
      },
    }),
  },
  infoGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 16,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  infoText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.9)',
    fontWeight: '600',
  },
  infoDivider: {
    width: 1,
    height: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  messagesContainer: {
    flex: 1,
    paddingHorizontal: 4,
  },
  messagesContent: {
    paddingVertical: 16,
    paddingHorizontal: 12,
    paddingBottom: 100,
    flexGrow: 1,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
  },
  loadingState: {
    paddingVertical: 48,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '600',
  },
  loadMoreContainer: {
    alignItems: 'center',
    paddingTop: 8,
    paddingBottom: 20,
  },
  loadMoreButton: {
    minWidth: 190,
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderRadius: 999,
    backgroundColor: '#ff6b35',
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadMoreText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#ffffff',
  },
  loadMoreMeta: {
    marginTop: 10,
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
  },
  loadMoreError: {
    marginBottom: 10,
    fontSize: 13,
    color: '#fecaca',
    textAlign: 'center',
  },
  floatingButtons: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    flexDirection: 'row',
    gap: 12,
  },
  floatingButtonSecondary: {
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
      android: {
        // elevation set dynamically
      },
    }),
  },
  floatingButtonPrimary: {
    flex: 2,
    borderRadius: 16,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#ff6b35',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.6,
        shadowRadius: 12,
      },
      android: {
        // elevation set dynamically
      },
    }),
  },
  floatingButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    gap: 8,
  },
  floatingButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
  },
  floatingButtonTextPrimary: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
  },
});
