import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  RefreshControl,
  StatusBar,
  TextInput,
  Animated,
  Dimensions,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { storage } from '../../services/storage';
import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import { useAnalytics } from '../../hooks/useAnalytics';

const { width } = Dimensions.get('window');

const SkeletonCard = () => {
  const { theme } = useTheme();
  const shimmerAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmerAnim, {
          toValue: 1,
          duration: 1500,
          useNativeDriver: true,
        }),
        Animated.timing(shimmerAnim, {
          toValue: 0,
          duration: 1500,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  const shimmerOpacity = shimmerAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 0.7],
  });

  return (
    <View style={styles.sessionCard}>
      <Animated.View style={[styles.skeleton, styles.skeletonTitle, { opacity: shimmerOpacity }]} />
      <Animated.View style={[styles.skeleton, styles.skeletonText, { opacity: shimmerOpacity }]} />
      <Animated.View style={[styles.skeleton, styles.skeletonFooter, { opacity: shimmerOpacity }]} />
    </View>
  );
};

export default function ChatHistoryScreen({ navigation }) {
  useAnalytics('ChatHistoryScreen');
  const { theme, colors, getCardElevation } = useTheme();
  const [chatSessions, setChatSessions] = useState([]);
  const [filteredSessions, setFilteredSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [favorites, setFavorites] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    loadChatHistory();
    loadFavorites();
    
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 600,
      useNativeDriver: true,
    }).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.2,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  useEffect(() => {
    filterSessions();
  }, [searchQuery, chatSessions]);

  const loadFavorites = async () => {
    try {
      const saved = await storage.getFavorites();
      setFavorites(saved || []);
    } catch (error) {}
  };

  const loadChatHistory = async (pageNum = 1, append = false) => {
    try {
      const authToken = await storage.getAuthToken();
      if (!authToken) {
        navigation.replace('Login');
        return;
      }
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat-v2/history')}?page=${pageNum}&limit=20`, {
        method: 'GET',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const sessions = Array.isArray(data.sessions) ? data.sessions : [];
        
        if (append) {
          setChatSessions(prev => {
            const existingIds = new Set(prev.map(s => s.session_id));
            const newSessions = sessions.filter(s => !existingIds.has(s.session_id));
            return [...prev, ...newSessions];
          });
        } else {
          setChatSessions(sessions);
          setPage(1);
        }
        
        setHasMore(data.pagination?.has_more || false);
      } else if (response.status === 401) {
        await storage.removeAuthToken();
        navigation.replace('Login');
      }
    } catch (error) {

    } finally {
      if (!append) {
        setLoading(false);
        setRefreshing(false);
      } else {
        setLoadingMore(false);
      }
    }
  };

  const filterSessions = () => {
    if (!searchQuery.trim()) {
      setFilteredSessions(chatSessions);
      return;
    }
    const filtered = chatSessions.filter(session =>
      session.preview?.toLowerCase().includes(searchQuery.toLowerCase())
    );
    setFilteredSessions(filtered);
  };

  const onRefresh = () => {
    setRefreshing(true);
    setPage(1);
    setHasMore(true);
    loadChatHistory(1, false);
  };

  const loadMore = () => {
    if (!loadingMore && hasMore) {
      setLoadingMore(true);
      const nextPage = page + 1;
      setPage(nextPage);
      loadChatHistory(nextPage, true);
    }
  };

  const viewChatSession = async (session) => {
    try {
      const authToken = await storage.getAuthToken();
      const response = await fetch(`${API_BASE_URL}${getEndpoint(`/chat-v2/session/${session.session_id}`)}`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      if (response.ok) {
        const sessionData = await response.json();
        // Map API response; native_name comes from DB (session + each message)
        const mappedMessages = (sessionData.messages || []).map(msg => ({
          messageId: msg.message_id,
          role: msg.sender,
          content: msg.content,
          timestamp: msg.timestamp,
          id: `${msg.message_id}_${msg.timestamp}`,
          native_name: msg.native_name ?? sessionData.native_name ?? session.native_name ?? null,
          terms: msg.terms,
          glossary: msg.glossary,
          images: msg.images,
        }));
        
        navigation.navigate('ChatView', {
          session: { ...session, native_name: sessionData.native_name ?? session.native_name, messages: mappedMessages }
        });
      } else {
        Alert.alert('Error', 'Failed to load chat messages');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to load chat messages');
    }
  };

  const toggleFavorite = async (sessionId) => {
    const newFavorites = favorites.includes(sessionId)
      ? favorites.filter(id => id !== sessionId)
      : [...favorites, sessionId];
    setFavorites(newFavorites);
    await storage.setFavorites(newFavorites);
  };

  const getRelativeTime = (date) => {
    const now = new Date();
    const then = new Date(date);
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return then.toLocaleDateString();
  };

  const ChatSessionCard = React.memo(({ item, index }) => {
    const isFavorite = favorites.includes(item.session_id);
    const cardAnim = useRef(new Animated.Value(0)).current;

    useEffect(() => {
      Animated.spring(cardAnim, {
        toValue: 1,
        delay: index * 100,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }).start();
    }, []);

    return (
      <Animated.View
        style={[
          styles.sessionCardWrapper,
          {
            opacity: cardAnim,
            transform: [
              {
                translateY: cardAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: [50, 0],
                }),
              },
              {
                scale: cardAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: [0.9, 1],
                }),
              },
            ],
          },
        ]}
      >
        <TouchableOpacity
          style={[styles.sessionCard, { elevation: getCardElevation(8) }]}
          onPress={() => viewChatSession(item)}
          activeOpacity={0.9}
        >
          <LinearGradient
            colors={Platform.OS === 'android'
              ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
              : (theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.15)', 'rgba(249, 115, 22, 0.08)'])}
            style={styles.sessionGradient}
          >
            <View style={styles.sessionHeader}>
              <View style={styles.sessionIconContainer}>
                <LinearGradient
                  colors={['#ff6b35', '#ff8c5a']}
                  style={styles.sessionIconGradient}
                >
                  <Text style={styles.sessionIcon}>💬</Text>
                </LinearGradient>
              </View>
              <View style={styles.sessionInfo}>
                <View style={styles.sessionTitleRow}>
                  {item.native_name && (
                    <Text style={[styles.nativeName, { color: colors.text }]}>{item.native_name}</Text>
                  )}
                  <Text style={[styles.sessionDate, { color: colors.textSecondary }]}>{getRelativeTime(item.created_at)}</Text>
                </View>
                {item.unread && (
                  <Animated.View style={[styles.unreadBadge, { transform: [{ scale: pulseAnim }] }]}>
                    <Text style={styles.unreadText}>New</Text>
                  </Animated.View>
                )}
              </View>
            </View>

            <Text style={[styles.sessionPreview, { color: colors.textSecondary }]} numberOfLines={2}>
              {item.preview || 'Chat conversation'}
            </Text>

            <View style={styles.sessionFooter}>
              <Text style={[styles.sessionTime, { color: colors.textSecondary }]}>
                {new Date(item.created_at).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </Text>
              <View style={styles.sessionActions}>
                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => toggleFavorite(item.session_id)}
                >
                  <Icon
                    name={isFavorite ? 'star' : 'star-outline'}
                    size={20}
                    color={isFavorite ? '#ffd700' : 'rgba(255, 255, 255, 0.6)'}
                  />
                </TouchableOpacity>
              </View>
            </View>
          </LinearGradient>
        </TouchableOpacity>
      </Animated.View>
    );
  });

  const renderChatSession = React.useCallback(({ item, index }) => (
    <ChatSessionCard item={item} index={index} />
  ), [favorites]);

  const renderEmptyState = () => (
    <Animated.View style={[styles.emptyState, { opacity: fadeAnim }]}>
      <View style={styles.emptyIconContainer}>
        <LinearGradient
          colors={['#ff6b35', '#ffd700', '#ff6b35']}
          style={styles.emptyIconGradient}
        >
          <Text style={styles.emptyIcon}>💬</Text>
        </LinearGradient>
      </View>
      <Text style={styles.emptyTitle}>No Chat History</Text>
      <Text style={styles.emptyText}>
        {searchQuery ? 'No chats match your search' : 'Start a conversation to see your chat history here'}
      </Text>
      {!searchQuery && (
        <TouchableOpacity
          style={styles.startChatButton}
          onPress={() => navigation.navigate('Home')}
        >
          <LinearGradient colors={['#ff6b35', '#ff8c5a']} style={styles.startChatGradient}>
            <Text style={styles.startChatText}>Start Chatting</Text>
          </LinearGradient>
        </TouchableOpacity>
      )}
    </Animated.View>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
      <LinearGradient colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.primary] : [colors.gradientStart, colors.gradientStart, colors.gradientStart, colors.gradientStart]} style={styles.gradient}>
        <SafeAreaView style={styles.safeArea}>
          
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity style={[styles.backButton, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(249, 115, 22, 0.25)' }]} onPress={() => navigation.goBack()}>
              <Icon name="arrow-back" size={24} color={colors.text} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]}>Chat History</Text>
            <View style={styles.placeholder} />
          </View>

          {/* Search Bar */}
          <View style={styles.searchContainer}>
            <LinearGradient
              colors={Platform.OS === 'android'
                ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                : (theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)'])}
              style={styles.searchGradient}
            >
              <Icon name="search" size={20} color={colors.textSecondary} />
              <TextInput
                style={[styles.searchInput, { color: colors.text }]}
                placeholder="Search conversations..."
                placeholderTextColor={colors.textSecondary}
                value={searchQuery}
                onChangeText={setSearchQuery}
              />
              {searchQuery.length > 0 && (
                <TouchableOpacity onPress={() => setSearchQuery('')}>
                  <Icon name="close-circle" size={20} color="rgba(255, 255, 255, 0.6)" />
                </TouchableOpacity>
              )}
            </LinearGradient>
          </View>

          {/* Content */}
          {loading ? (
            <View style={styles.listContainer}>
              {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
            </View>
          ) : (
            <FlatList
              data={filteredSessions}
              renderItem={renderChatSession}
              keyExtractor={(item, index) => item.session_id || `session-${index}-${Date.now()}`}
              contentContainerStyle={[styles.listContainer, { paddingBottom: loadingMore ? 200 : 100 }]}
              showsVerticalScrollIndicator={false}
              refreshControl={
                <RefreshControl
                  refreshing={refreshing}
                  onRefresh={onRefresh}
                  tintColor={COLORS.white}
                />
              }
              ListEmptyComponent={renderEmptyState}
              // onEndReached={loadMore}
              // onEndReachedThreshold={0.5}
              removeClippedSubviews={false}
              maxToRenderPerBatch={5}
              windowSize={5}
              initialNumToRender={15}
              ListFooterComponent={() => 
                hasMore ? (
                  <View style={styles.loadMoreContainer}>
                    {loadingMore ? (
                      <View style={styles.loadingMore}>
                        <SkeletonCard />
                        <SkeletonCard />
                        <Text style={styles.loadingMoreText}>Loading more chats...</Text>
                      </View>
                    ) : (
                      <TouchableOpacity 
                        style={styles.loadMoreButton} 
                        onPress={loadMore}
                      >
                        <LinearGradient colors={['#ff6b35', '#ff8c5a']} style={styles.loadMoreGradient}>
                          <Text style={styles.loadMoreText}>Load More Chats</Text>
                        </LinearGradient>
                      </TouchableOpacity>
                    )}
                  </View>
                ) : null
              }
            />
          )}
        </SafeAreaView>
        

      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
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
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
  },
  placeholder: { width: 40 },
  searchContainer: {
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  searchGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  searchInput: {
    flex: 1,
    marginLeft: 12,
    fontSize: 16,
    color: COLORS.white,
  },
  listContainer: {
    padding: 20,
    paddingTop: 0,
    flexGrow: 1,
  },
  sessionCardWrapper: {
    marginBottom: 16,
  },
  sessionCard: {
    borderRadius: 20,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.3,
        shadowRadius: 12,
      },
      android: {
        // elevation set dynamically
      },
    }),
  },
  sessionGradient: {
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 20,
  },
  sessionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  sessionIconContainer: {
    marginRight: 12,
  },
  sessionIconGradient: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  sessionIcon: {
    fontSize: 24,
  },
  sessionInfo: {
    flex: 1,
  },
  sessionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  nativeName: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
    marginRight: 8,
  },
  sessionDate: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.7)',
  },
  unreadBadge: {
    backgroundColor: '#ff6b35',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  unreadText: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.white,
  },
  sessionPreview: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: 22,
    marginBottom: 12,
  },
  sessionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sessionTime: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  sessionActions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    padding: 8,
  },
  skeleton: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 8,
  },
  skeletonTitle: {
    width: '60%',
    height: 20,
    marginBottom: 12,
  },
  skeletonText: {
    width: '100%',
    height: 16,
    marginBottom: 8,
  },
  skeletonFooter: {
    width: '40%',
    height: 14,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyIconContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    marginBottom: 24,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.6,
    shadowRadius: 20,
    elevation: 10,
  },
  emptyIconGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  emptyIcon: {
    fontSize: 48,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  startChatButton: {
    borderRadius: 25,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.6,
    shadowRadius: 12,
    elevation: 8,
  },
  startChatGradient: {
    paddingHorizontal: 32,
    paddingVertical: 16,
  },
  startChatText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '700',
  },
  loadingMore: {
    paddingVertical: 10,
  },
  loadingMoreText: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 14,
    textAlign: 'center',
    padding: 20,
  },
  endSpacer: {
    height: 80,
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(26, 0, 51, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  loadingContent: {
    alignItems: 'center',
    padding: 20,
  },
  loadMoreButton: {
    margin: 20,
    borderRadius: 12,
    overflow: 'hidden',
  },
  loadMoreGradient: {
    padding: 16,
    alignItems: 'center',
  },
  loadMoreText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  loadMoreContainer: {
    minHeight: 80,
  },
});
