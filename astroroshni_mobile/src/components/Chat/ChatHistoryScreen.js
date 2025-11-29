import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  RefreshControl,
  StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';

import { storage } from '../../services/storage';
import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';

export default function ChatHistoryScreen({ navigation }) {
  const [chatSessions, setChatSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  useEffect(() => {
    loadChatHistory();
  }, []);

  const loadChatHistory = async () => {
    try {
      const authToken = await storage.getAuthToken();
      
      if (!authToken) {
        // Redirect to login if no auth token
        navigation.replace('Login');
        return;
      }
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat/history')}`, {
        method: 'GET',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const sessions = Array.isArray(data.sessions) ? data.sessions : [];
        setChatSessions(sessions);
      } else if (response.status === 401) {
        // Token expired, redirect to login
        await storage.removeAuthToken();
        navigation.replace('Login');
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Remove groupMessagesByDate as backend now returns sessions directly

  const onRefresh = () => {
    setRefreshing(true);
    loadChatHistory();
  };

  const viewChatSession = async (session) => {
    try {
      const authToken = await storage.getAuthToken();
      const response = await fetch(`${API_BASE_URL}${getEndpoint(`/chat/session/${session.session_id}`)}`, {
        method: 'GET',
        headers: { 
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      if (response.ok) {
        const sessionData = await response.json();
        navigation.navigate('ChatView', { 
          session: {
            ...session,
            messages: sessionData.messages || []
          }
        });
      } else {
        Alert.alert('Error', 'Failed to load chat messages');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to load chat messages');
    }
  };

  const clearAllHistory = () => {
    Alert.alert(
      'Clear All History',
      'Are you sure you want to delete all chat history? This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear All',
          style: 'destructive',
          onPress: async () => {
            try {
              const authToken = await storage.getAuthToken();
              const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat/cleanup')}`, {
                method: 'DELETE',
                headers: { 
                  'Authorization': `Bearer ${authToken}`
                }
              });
              
              if (response.ok) {
                setChatSessions([]);
                Alert.alert('Success', 'Chat history cleared');
              }
            } catch (error) {
              Alert.alert('Error', 'Failed to clear chat history');
            }
          }
        }
      ]
    );
  };

  const renderChatSession = ({ item }) => (
    <TouchableOpacity
      style={styles.sessionCard}
      onPress={() => viewChatSession(item)}
    >
      <View style={styles.sessionHeader}>
        <Text style={styles.sessionDate}>
          {new Date(item.created_at).toLocaleDateString()}
        </Text>
        <Text style={styles.sessionId}>
          Session
        </Text>
      </View>
      
      <Text style={styles.sessionPreview} numberOfLines={2}>
        {item.preview || 'Chat conversation'}
      </Text>
      
      <View style={styles.sessionFooter}>
        <Text style={styles.sessionTime}>
          {new Date(item.created_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </Text>
        <Text style={styles.chevronIcon}>▶</Text>
      </View>
    </TouchableOpacity>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Text style={styles.emptyIcon}>💬</Text>
      <Text style={styles.emptyTitle}>No Chat History</Text>
      <Text style={styles.emptyText}>
        Start a conversation to see your chat history here
      </Text>
      <TouchableOpacity
        style={styles.startChatButton}
        onPress={() => navigation.navigate('Chat')}
      >
        <Text style={styles.startChatText}>Start Chatting</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <LinearGradient colors={[COLORS.gradientStart, COLORS.gradientEnd]} style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#ff6f00" translucent={false} />
      <SafeAreaView style={styles.safeArea}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
            <Text style={styles.backIcon}>←</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Chat History</Text>
          {Array.isArray(chatSessions) && chatSessions.length > 0 && (
            <TouchableOpacity
              style={styles.clearButton}
              onPress={clearAllHistory}
            >
              <Text style={styles.trashIcon}>🗑️</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Content */}
        <FlatList
          data={chatSessions}
          renderItem={renderChatSession}
          keyExtractor={(item) => item.session_id || `session-${Math.random()}`}
          contentContainerStyle={styles.listContainer}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              colors={[COLORS.accent]}
              tintColor={COLORS.accent}
            />
          }
          ListEmptyComponent={!loading ? renderEmptyState : null}
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
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: COLORS.lightGray,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.textPrimary,
    flex: 1,
    textAlign: 'center',
    marginHorizontal: 16,
  },
  clearButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: COLORS.lightGray,
  },
  backIcon: {
    fontSize: 20,
    color: COLORS.accent,
    fontWeight: 'bold',
  },
  trashIcon: {
    fontSize: 18,
  },
  chevronIcon: {
    fontSize: 12,
    color: COLORS.gray,
  },
  emptyIcon: {
    fontSize: 64,
  },
  listContainer: {
    padding: 16,
    flexGrow: 1,
  },
  sessionCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sessionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sessionDate: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  sessionId: {
    fontSize: 12,
    color: COLORS.gray,
    backgroundColor: COLORS.lightGray,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  sessionPreview: {
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 20,
    marginBottom: 12,
  },
  sessionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sessionTime: {
    fontSize: 12,
    color: COLORS.gray,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginTop: 16,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 16,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  startChatButton: {
    backgroundColor: COLORS.accent,
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 25,
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  startChatText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '700',
  },
});