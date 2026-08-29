import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  Platform,
} from 'react-native';
import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { storage } from '../../services/storage';
import { chatAPI } from '../../services/api';
import { getTextToSpeech } from '../../utils/textToSpeechLazy';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import PodcastPlayerModal from '../PodcastPlayerModal';
import { goBackOrHome } from '../../navigation/navHelpers';
import FocusedStatusBar from '../Common/FocusedStatusBar';
import { sharePodcastBlobOnWeb } from '../../utils/sharePodcastWeb';

export default function PodcastHistoryScreen({ navigation }) {
  useAnalytics('PodcastHistoryScreen');
  const { t, i18n } = useTranslation();
  const { colors } = useTheme();
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [playingMessageId, setPlayingMessageId] = useState(null);
  const [sharingMessageId, setSharingMessageId] = useState(null);
  const [showPlayer, setShowPlayer] = useState(false);
  const [playerMode, setPlayerMode] = useState('playing');
  const [positionMillis, setPositionMillis] = useState(0);
  const [durationMillis, setDurationMillis] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [podcastViewMode, setPodcastViewMode] = useState('listen');
  const [visualManifest, setVisualManifest] = useState(null);
  const [visualLoading, setVisualLoading] = useState(false);
  const [visualError, setVisualError] = useState('');
  const visualRequestKeyRef = useRef('');

  const loadHistory = useCallback(async () => {
    try {
      const token = await storage.getAuthToken();
      if (!token) {
        setList([]);
        return;
      }
      const response = await chatAPI.getPodcastHistory();
      const podcasts = response?.data?.podcasts ?? [];
      setList(Array.isArray(podcasts) ? podcasts : []);
    } catch (error) {
      setList([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const stopPlaying = () => {
    getTextToSpeech().stopPodcast();
    setPlayingMessageId(null);
    setShowPlayer(false);
    setSelectedEntry(null);
    setPodcastViewMode('listen');
    setVisualManifest(null);
    setVisualLoading(false);
    setVisualError('');
    visualRequestKeyRef.current = '';
  };

  const playFromStream = async (entry) => {
    const token = await storage.getAuthToken();
    if (!token) {
      navigation.replace('Login');
      return;
    }
    const streamUrl = chatAPI.getPodcastStreamUrl(entry.message_id, entry.lang);
    setSelectedEntry(entry);
    setPlayingMessageId(entry.message_id);
    setShowPlayer(true);
    setPlayerMode('playing');
    setPositionMillis(0);
    setDurationMillis(0);
    setPodcastViewMode('listen');
    setVisualManifest(null);
    setVisualLoading(false);
    setVisualError('');
    visualRequestKeyRef.current = '';
    getTextToSpeech().playPodcastFromStream(streamUrl, token, {
      onStart: () => { setPlayingMessageId(entry.message_id); setPlayerMode('playing'); getTextToSpeech().setPodcastRate(playbackRate); },
      onProgress: (position, duration) => { setPositionMillis(position); setDurationMillis(duration); },
      onPause: () => setPlayerMode('paused'),
      onResume: () => setPlayerMode('playing'),
      onDone: stopPlaying,
      onStop: stopPlaying,
      onError: () => { stopPlaying(); Alert.alert(t('historyUi.common.error'), t('historyUi.podcast.playError')); },
    });
  };

  const handleViewModeChange = async (nextMode) => {
    const mode = nextMode === 'watch' ? 'watch' : 'listen';
    setPodcastViewMode(mode);
    if (mode !== 'watch') return;
    const entry = selectedEntry;
    if (!entry?.message_id) {
      setVisualError(t('podcast.visualUnavailableBody', 'You can continue listening to the podcast.'));
      return;
    }
    const lang = String(entry.lang || 'en').toLowerCase().startsWith('hi') ? 'hi' : 'en';
    const requestKey = `${entry.message_id}:${lang}`;
    if (visualRequestKeyRef.current === requestKey && visualManifest) return;
    visualRequestKeyRef.current = requestKey;
    setVisualLoading(true);
    setVisualError('');
    try {
      const response = await chatAPI.getPodcastVisuals(entry.message_id, lang, entry.birth_chart_id || null);
      const manifest = response?.data?.manifest;
      if (!manifest || !Array.isArray(manifest.scenes) || !manifest.scenes.length) {
        throw new Error('Visual podcast manifest was empty');
      }
      if (visualRequestKeyRef.current === requestKey) setVisualManifest(manifest);
    } catch (error) {
      if (visualRequestKeyRef.current === requestKey) {
        visualRequestKeyRef.current = '';
        setVisualError(
          error?.response?.data?.detail
          || t('podcast.visualUnavailableBody', 'You can continue listening to the podcast.'),
        );
      }
    } finally {
      if (visualRequestKeyRef.current === requestKey || !visualRequestKeyRef.current) {
        setVisualLoading(false);
      }
    }
  };

  const sharePodcast = async (entry) => {
    const token = await storage.getAuthToken();
    if (!token) {
      navigation.replace('Login');
      return;
    }
    setSharingMessageId(entry.message_id);
    try {
      const streamUrl = chatAPI.getPodcastStreamUrl(entry.message_id, entry.lang);
      if (Platform.OS === 'web') {
        const response = await fetch(streamUrl, { headers: { Authorization: `Bearer ${token}` } });
        if (!response.ok) throw new Error('download_failed');
        const blob = await response.blob();
        await sharePodcastBlobOnWeb(
          blob,
          `AstroRoshni-Podcast-${entry.message_id || Date.now()}.mp3`,
        );
        return;
      }
      const localPath = `${FileSystem.cacheDirectory}AstroRoshni-Podcast-${entry.message_id || Date.now()}.mp3`;
      const { status } = await FileSystem.downloadAsync(streamUrl, localPath, { headers: { Authorization: `Bearer ${token}` } });
      if (status !== 200) throw new Error('download_failed');
      if (!(await Sharing.isAvailableAsync())) {
        Alert.alert(t('historyUi.common.error'), t('historyUi.podcast.sharingUnavailable'));
        return;
      }
      await Sharing.shareAsync(localPath, { mimeType: 'audio/mpeg', dialogTitle: t('historyUi.podcast.share') });
    } catch (error) {
      Alert.alert(t('historyUi.common.error'), t('historyUi.podcast.shareError'));
    } finally {
      setSharingMessageId(null);
    }
  };

  const openSession = async (entry) => {
    if (!entry.session_id) {
      Alert.alert(t('historyUi.podcast.cannotOpen'), t('historyUi.podcast.olderSession'));
      return;
    }
    try {
      const token = await storage.getAuthToken();
      if (!token) {
        navigation.replace('Login');
        return;
      }
      const base = (API_BASE_URL || '').replace(/\/$/, '');
      const response = await fetch(`${base}${getEndpoint(`/chat-v2/session/${entry.session_id}`)}`, { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error('conversation_failed');
      const sessionData = await response.json();
      const messages = (sessionData.messages || []).map((message, index) => ({
        messageId: message.message_id ?? message.messageId,
        role: message.sender === 'ai' || message.sender === 'assistant' ? 'assistant' : message.sender === 'user' ? 'user' : message.sender,
        content: message.content,
        timestamp: message.timestamp,
        id: `${message.message_id ?? message.messageId ?? index}_${message.timestamp}`,
        native_name: message.native_name ?? sessionData.native_name ?? null,
        terms: message.terms,
        glossary: message.glossary,
        images: message.images,
      }));
      navigation.navigate('ChatView', { session: { session_id: entry.session_id, native_name: sessionData.native_name ?? null, created_at: sessionData.created_at, messages } });
    } catch (error) {
      Alert.alert(t('historyUi.common.error'), t('historyUi.podcast.conversationError'));
    }
  };

  const formatDate = (value) => {
    const parsed = new Date(value);
    if (!value || Number.isNaN(parsed.getTime())) return '';
    return new Intl.DateTimeFormat(i18n.resolvedLanguage || undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(parsed);
  };

  const renderItem = ({ item, index }) => {
    const isPlaying = playingMessageId === item.message_id;
    const isSharing = sharingMessageId === item.message_id;
    return (
      <View style={[styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
        <View style={styles.cardTop}>
          <TouchableOpacity
            onPress={() => isPlaying ? setShowPlayer(true) : playFromStream(item)}
            style={[styles.playButton, { backgroundColor: colors.accentSoft }]}
            accessibilityLabel={isPlaying ? t('historyUi.podcast.openPlayer') : t('historyUi.podcast.play')}
          >
            <Ionicons name={isPlaying ? 'radio' : 'play'} size={20} color={colors.onAccent} />
          </TouchableOpacity>
          <View style={styles.cardCopy}>
            <Text style={[styles.cardEyebrow, { color: colors.primary }]}>{t('historyUi.podcast.episode', { number: list.length - index })}</Text>
            <Text style={[styles.cardTitle, { color: colors.text }]} numberOfLines={2}>{item.preview || t('historyUi.podcast.fallbackTitle')}</Text>
            <Text style={[styles.cardDate, { color: colors.textSecondary }]}>{formatDate(item.created_at)}</Text>
          </View>
          <TouchableOpacity onPress={() => sharePodcast(item)} disabled={isSharing} style={[styles.iconButton, { borderColor: colors.cardBorder }]}>
            {isSharing ? <ActivityIndicator size="small" color={colors.primary} /> : <Ionicons name="share-outline" size={18} color={colors.primary} />}
          </TouchableOpacity>
        </View>
        <TouchableOpacity onPress={() => openSession(item)} style={[styles.conversationButton, { borderTopColor: colors.cardBorder }]}>
          <Text style={[styles.conversationText, { color: colors.textSecondary }]}>{t('historyUi.podcast.openConversation')}</Text>
          <Ionicons name="arrow-forward" size={16} color={colors.primary} />
        </TouchableOpacity>
      </View>
    );
  };

  const emptyState = (
    <View style={styles.emptyState}>
      <View style={[styles.emptyIcon, { backgroundColor: colors.accentSoft }]}><Ionicons name="headset-outline" size={31} color={colors.onAccent} /></View>
      <Text style={[styles.emptyTitle, { color: colors.text }]}>{t('historyUi.podcast.emptyTitle')}</Text>
      <Text style={[styles.emptyBody, { color: colors.textSecondary }]}>{t('historyUi.podcast.emptyBody')}</Text>
      <TouchableOpacity onPress={() => navigation.navigate('Home', { startChat: true })} style={[styles.emptyCta, { backgroundColor: colors.primary }]}>
        <Text style={[styles.emptyCtaText, { color: colors.onPrimary }]}>{t('historyUi.podcast.goToChat')}</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <FocusedStatusBar backgroundColor={colors.headerSurface} />
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.headerSurface }]} edges={['top']}>
        <View
          style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cardBorder }]}
        >
          <TouchableOpacity onPress={() => goBackOrHome(navigation)} style={[styles.backButton, { borderColor: colors.cosmicLine || colors.cardBorder }]}>
            <Ionicons name="arrow-back" size={21} color={colors.textInverse} />
          </TouchableOpacity>
          <View style={styles.headerCopy}>
            <Text style={[styles.headerEyebrow, { color: colors.accent }]}>{t('historyUi.library')}</Text>
            <Text style={[styles.headerTitle, { color: colors.textInverse }]}>{t('historyUi.podcast.title')}</Text>
          </View>
          <View style={[styles.countPill, { backgroundColor: colors.accentSoft }]}><Text style={[styles.countText, { color: colors.onAccent }]}>{list.length}</Text></View>
        </View>

        <View style={[styles.contentShell, { backgroundColor: colors.background }]}>
        <View style={styles.intro}>
          <Text style={[styles.introTitle, { color: colors.text }]}>{t('historyUi.podcast.heroTitle')}</Text>
          <Text style={[styles.introBody, { color: colors.textSecondary }]}>{t('historyUi.podcast.heroBody')}</Text>
        </View>

        {loading ? (
          <View style={styles.loadingState}><ActivityIndicator color={colors.primary} /><Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('historyUi.podcast.loading')}</Text></View>
        ) : (
          <FlatList
            data={list}
            renderItem={renderItem}
            keyExtractor={(item, index) => item.message_id ? `${item.message_id}_${item.lang}_${index}` : `podcast-${index}`}
            contentContainerStyle={[styles.list, !list.length && styles.emptyList]}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadHistory(); }} tintColor={colors.primary} />}
            ListEmptyComponent={emptyState}
          />
        )}

        {playingMessageId && !showPlayer ? (
          <View style={[styles.nowPlaying, { backgroundColor: colors.surfaceInverse, borderColor: colors.cardBorder }]}>
            <Ionicons name="radio" size={18} color={colors.accent} />
            <TouchableOpacity style={styles.nowPlayingCopy} onPress={() => setShowPlayer(true)}>
              <Text style={[styles.nowPlayingText, { color: colors.onSurfaceInverse || colors.textInverse }]} numberOfLines={1}>{t('historyUi.podcast.nowPlaying')}</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={stopPlaying}><Text style={[styles.stopText, { color: colors.accent }]}>{t('historyUi.podcast.stop')}</Text></TouchableOpacity>
          </View>
        ) : null}

        <PodcastPlayerModal
          visible={showPlayer}
          onClose={stopPlaying}
          mode={playerMode}
          positionMillis={positionMillis}
          durationMillis={durationMillis}
          onSeek={(position) => { getTextToSpeech().seekPodcast(position); setPositionMillis(position); }}
          onPause={() => getTextToSpeech().pausePodcast()}
          onResume={() => getTextToSpeech().resumePodcast()}
          onStop={stopPlaying}
          onShare={() => selectedEntry && sharePodcast(selectedEntry)}
          playbackRate={playbackRate}
          onSpeedChange={(rate) => { setPlaybackRate(rate); getTextToSpeech().setPodcastRate(rate); }}
          viewMode={podcastViewMode}
          onViewModeChange={handleViewModeChange}
          visualManifest={visualManifest}
          isVisualLoading={visualLoading}
          visualError={visualError}
        />
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 }, safeArea: { flex: 1 }, contentShell: { flex: 1 },
  header: { minHeight: 78, paddingHorizontal: 18, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1 },
  backButton: { width: 42, height: 42, borderRadius: 21, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  headerCopy: { flex: 1, paddingHorizontal: 14 },
  headerEyebrow: { fontSize: 10, fontWeight: '900', letterSpacing: 2 },
  headerTitle: { fontSize: 23, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontWeight: '600', marginTop: 2 },
  countPill: { minWidth: 38, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 10 },
  countText: { fontSize: 13, fontWeight: '900' },
  intro: { paddingHorizontal: 20, paddingTop: 24, paddingBottom: 20 },
  introTitle: { fontSize: 31, lineHeight: 36, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontWeight: '500' },
  introBody: { fontSize: 14, lineHeight: 21, marginTop: 8, maxWidth: 470 },
  list: { paddingHorizontal: 20, paddingBottom: 100, gap: 12 }, emptyList: { flexGrow: 1 },
  card: { borderWidth: 1, borderRadius: 22, overflow: 'hidden' },
  cardTop: { flexDirection: 'row', alignItems: 'flex-start', gap: 13, padding: 15 },
  playButton: { width: 48, height: 48, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  cardCopy: { flex: 1, minWidth: 0 },
  cardEyebrow: { fontSize: 9, fontWeight: '900', letterSpacing: 1.4, textTransform: 'uppercase' },
  cardTitle: { fontSize: 16, lineHeight: 21, fontWeight: '700', marginTop: 4 },
  cardDate: { fontSize: 11, fontWeight: '600', marginTop: 7 },
  iconButton: { width: 38, height: 38, borderRadius: 19, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  conversationButton: { borderTopWidth: 1, paddingHorizontal: 16, minHeight: 46, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  conversationText: { fontSize: 12, fontWeight: '700' },
  loadingState: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 }, loadingText: { fontSize: 13, fontWeight: '700' },
  emptyState: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 28, paddingVertical: 40 },
  emptyIcon: { width: 64, height: 64, borderRadius: 24, alignItems: 'center', justifyContent: 'center', marginBottom: 18 },
  emptyTitle: { fontSize: 22, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontWeight: '600', textAlign: 'center' },
  emptyBody: { fontSize: 14, lineHeight: 21, textAlign: 'center', marginTop: 8, maxWidth: 340 },
  emptyCta: { marginTop: 20, paddingHorizontal: 22, paddingVertical: 13, borderRadius: 18 }, emptyCtaText: { fontSize: 14, fontWeight: '900' },
  nowPlaying: { position: 'absolute', left: 14, right: 14, bottom: 14, minHeight: 58, borderRadius: 20, borderWidth: 1, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', gap: 10 },
  nowPlayingCopy: { flex: 1 }, nowPlayingText: { fontSize: 13, fontWeight: '700' }, stopText: { fontSize: 12, fontWeight: '900' },
});
