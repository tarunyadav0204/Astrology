import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  RefreshControl,
  StatusBar,
  Platform,
  ActivityIndicator,
} from 'react-native';
import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { storage } from '../../services/storage';
import { chatAPI } from '../../services/api';
import { getTextToSpeech } from '../../utils/textToSpeechLazy';
import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import { useAnalytics } from '../../hooks/useAnalytics';

export default function PodcastHistoryScreen({ navigation }) {
  useAnalytics('PodcastHistoryScreen');
  const { theme, colors, getCardElevation } = useTheme();
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [playingMessageId, setPlayingMessageId] = useState(null);
  const [sharingMessageId, setSharingMessageId] = useState(null);

  const loadHistory = useCallback(async () => {
    try {
      const token = await storage.getAuthToken();
      if (!token) {
        setList([]);
        return;
      }
      const res = await chatAPI.getPodcastHistory();
      const podcasts = res?.data?.podcasts ?? [];
      setList(Array.isArray(podcasts) ? podcasts : []);
    } catch (e) {
      setList([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const onRefresh = () => {
    setRefreshing(true);
    loadHistory();
  };

  const getRelativeTime = (dateStr) => {
    if (!dateStr) return '';
    const now = new Date();
    const then = new Date(dateStr);
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

  const playFromStream = async (entry) => {
    const token = await storage.getAuthToken();
    if (!token) {
      navigation.replace('Login');
      return;
    }
    const streamUrl = chatAPI.getPodcastStreamUrl(entry.message_id, entry.lang);
    setPlayingMessageId(entry.message_id);
    getTextToSpeech().playPodcastFromStream(streamUrl, token, {
      onStart: () => setPlayingMessageId(entry.message_id),
      onDone: () => setPlayingMessageId(null),
      onError: () => {
        setPlayingMessageId(null);
        Alert.alert('Error', 'Could not play podcast.');
      },
      onStop: () => setPlayingMessageId(null),
    });
  };

  const stopPlaying = () => {
    getTextToSpeech().stopPodcast();
    setPlayingMessageId(null);
  };

  const sharePodcast = async (entry, e) => {
    if (e) e.stopPropagation();
    const token = await storage.getAuthToken();
    if (!token) {
      navigation.replace('Login');
      return;
    }
    setSharingMessageId(entry.message_id);
    try {
      const streamUrl = chatAPI.getPodcastStreamUrl(entry.message_id, entry.lang);
      const filename = `AstroRoshni-Podcast-${entry.message_id || Date.now()}.mp3`;
      const localPath = `${FileSystem.cacheDirectory}${filename}`;
      const { status } = await FileSystem.downloadAsync(streamUrl, localPath, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (status !== 200) {
        Alert.alert('Error', 'Could not load podcast to share.');
        return;
      }
      const isAvailable = await Sharing.isAvailableAsync();
      if (!isAvailable) {
        Alert.alert('Error', 'Sharing is not available on this device.');
        return;
      }
      await Sharing.shareAsync(localPath, {
        mimeType: 'audio/mpeg',
        dialogTitle: 'Share Podcast',
      });
    } catch (err) {
      console.error('[PodcastHistory] share error', err);
      Alert.alert('Error', 'Could not share podcast. Please try again.');
    } finally {
      setSharingMessageId(null);
    }
  };

  const openSession = async (entry) => {
    const sessionId = entry.session_id;
    if (!sessionId) {
      Alert.alert('Cannot open', 'This podcast was from an older session. Find it in Chat History.');
      return;
    }
    try {
      const authToken = await storage.getAuthToken();
      if (!authToken) {
        navigation.replace('Login');
        return;
      }
      const base = (API_BASE_URL || '').replace(/\/$/, '');
      const path = getEndpoint(`/chat-v2/session/${sessionId}`);
      const response = await fetch(`${base}${path}`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (!response.ok) {
        Alert.alert('Error', 'Failed to load conversation.');
        return;
      }
      const sessionData = await response.json();
      const mappedMessages = (sessionData.messages || []).map((msg, idx) => ({
        messageId: msg.message_id ?? msg.messageId,
        role: (msg.sender === 'ai' || msg.sender === 'assistant') ? 'assistant' : (msg.sender === 'user' ? 'user' : msg.sender),
        content: msg.content,
        timestamp: msg.timestamp,
        id: `${msg.message_id ?? msg.messageId ?? idx}_${msg.timestamp}`,
        native_name: msg.native_name ?? sessionData.native_name ?? null,
        terms: msg.terms,
        glossary: msg.glossary,
        images: msg.images,
      }));
      const session = {
        session_id: sessionId,
        native_name: sessionData.native_name ?? null,
        created_at: sessionData.created_at,
        messages: mappedMessages,
      };
      navigation.navigate('ChatView', { session });
    } catch (e) {
      Alert.alert('Error', 'Failed to load conversation.');
    }
  };

  const renderItem = ({ item }) => {
    const isPlaying = playingMessageId === item.message_id;
    const isSharing = sharingMessageId === item.message_id;
    return (
      <View style={[styles.card, { elevation: getCardElevation(5) }]}>
        <TouchableOpacity
          style={styles.cardGradientTouchable}
          onPress={() => openSession(item)}
          activeOpacity={0.9}
        >
          <LinearGradient
            colors={Platform.OS === 'android'
              ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
              : (theme === 'dark' ? ['rgba(255, 255, 255, 0.12)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.12)', 'rgba(249, 115, 22, 0.06)'])}
            style={styles.cardGradient}
          >
            <View style={styles.cardHeader}>
              <TouchableOpacity
                onPress={(e) => { e.stopPropagation(); isPlaying ? stopPlaying() : playFromStream(item); }}
                style={styles.iconWrap}
              >
                <LinearGradient colors={['#ff6b35', '#ff8c5a']} style={styles.iconGrad}>
                  {isPlaying ? (
                    <Icon name="stop" size={20} color="#fff" />
                  ) : (
                    <Icon name="play" size={20} color="#fff" />
                  )}
                </LinearGradient>
              </TouchableOpacity>
              <View style={styles.cardMeta}>
                <Text style={[styles.playedAt, { color: colors.textSecondary }]}>{getRelativeTime(item.created_at)}</Text>
              </View>
              <TouchableOpacity
                onPress={(e) => sharePodcast(item, e)}
                style={styles.shareIconWrap}
                disabled={isSharing}
              >
                {isSharing ? (
                  <ActivityIndicator size="small" color={colors.text} />
                ) : (
                  <Icon name="share-outline" size={22} color={colors.textSecondary} />
                )}
              </TouchableOpacity>
              <Icon name="chevron-forward" size={20} color={colors.textSecondary} />
            </View>
            <Text style={[styles.preview, { color: colors.textSecondary }]} numberOfLines={2}>
              {item.preview || 'Podcast'}
            </Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    );
  };

  const renderEmpty = () => (
    <View style={styles.empty}>
      <View style={styles.emptyIconWrap}>
        <LinearGradient colors={['#ff6b35', '#ffd700']} style={styles.emptyIconGrad}>
          <Icon name="radio-outline" size={48} color="#fff" />
        </LinearGradient>
      </View>
      <Text style={[styles.emptyTitle, { color: colors.text }]}>No podcast history</Text>
      <Text style={[styles.emptySub, { color: colors.textSecondary }]}>
        Podcasts you listen to from chat or chat history will appear here.
      </Text>
      <TouchableOpacity style={styles.emptyBtn} onPress={() => navigation.navigate('Home')}>
        <LinearGradient colors={['#ff6b35', '#ff8c5a']} style={styles.emptyBtnGrad}>
          <Text style={styles.emptyBtnText}>Go to Chat</Text>
        </LinearGradient>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
      <LinearGradient
        colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.primary] : [colors.gradientStart, colors.gradientStart, colors.gradientStart, colors.gradientStart]}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safe}>
          <View style={styles.header}>
            <TouchableOpacity
              style={[styles.backBtn, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.15)' : 'rgba(249,115,22,0.25)' }]}
              onPress={() => navigation.goBack()}
            >
              <Icon name="arrow-back" size={24} color={colors.text} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]}>Podcast History</Text>
            <View style={styles.placeholder} />
          </View>
          {loading ? (
            <View style={styles.loadingWrap}>
              <Text style={[styles.loadingText, { color: colors.textSecondary }]}>Loading…</Text>
            </View>
          ) : (
            <FlatList
              data={list}
              renderItem={renderItem}
              keyExtractor={(item, i) => (item.message_id ? `${item.message_id}_${item.lang}_${i}` : `ph_${i}`)}
              contentContainerStyle={[styles.list, list.length === 0 && styles.listEmpty]}
              ListEmptyComponent={renderEmpty}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.white} />
              }
            />
          )}
          {playingMessageId ? (
            <View style={[styles.nowPlayingBar, { backgroundColor: theme === 'dark' ? 'rgba(0,0,0,0.9)' : 'rgba(249,115,22,0.2)' }]}>
              <Icon name="radio" size={20} color={colors.text} />
              <Text style={[styles.nowPlayingText, { color: colors.text }]} numberOfLines={1}>Playing podcast</Text>
              <TouchableOpacity onPress={stopPlaying} style={styles.nowPlayingStop}>
                <Text style={styles.nowPlayingStopText}>Stop</Text>
              </TouchableOpacity>
            </View>
          ) : null}
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safe: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: { fontSize: 20, fontWeight: '700' },
  placeholder: { width: 40 },
  list: { padding: 20, paddingTop: 8, paddingBottom: 100 },
  listEmpty: { flexGrow: 1 },
  loadingWrap: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { fontSize: 16 },
  card: {
    marginBottom: 16,
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  cardGradientTouchable: { flex: 1 },
  cardGradient: { padding: 16, borderRadius: 20 },
  cardHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  iconWrap: { marginRight: 12 },
  iconGrad: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cardMeta: { flex: 1 },
  shareIconWrap: { padding: 8, marginRight: 4, justifyContent: 'center', alignItems: 'center' },
  nativeName: { fontSize: 15, fontWeight: '600' },
  playedAt: { fontSize: 12, marginTop: 2 },
  preview: { fontSize: 14, lineHeight: 20 },
  empty: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  emptyIconWrap: { marginBottom: 20 },
  emptyIconGrad: {
    width: 88,
    height: 88,
    borderRadius: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyTitle: { fontSize: 20, fontWeight: '700', marginBottom: 8, textAlign: 'center' },
  emptySub: { fontSize: 15, textAlign: 'center', marginBottom: 24 },
  emptyBtn: { borderRadius: 20, overflow: 'hidden' },
  emptyBtnGrad: { paddingVertical: 14, paddingHorizontal: 28 },
  emptyBtnText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  nowPlayingBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 10,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.1)',
  },
  nowPlayingText: { flex: 1, fontSize: 14 },
  nowPlayingStop: { paddingHorizontal: 12, paddingVertical: 6 },
  nowPlayingStopText: { color: '#ff6b35', fontWeight: '600', fontSize: 14 },
});
