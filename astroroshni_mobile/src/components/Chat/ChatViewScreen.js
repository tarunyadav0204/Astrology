import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Platform,
  Share,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import MessageBubble from './MessageBubble';
import { storage } from '../../services/storage';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import { goBackOrHome } from '../../navigation/navHelpers';
import FocusedStatusBar from '../Common/FocusedStatusBar';

const DAY_SESSION_BATCH_SIZE = 2;
const LANGUAGE_LOCALES = {
  english: 'en-IN',
  es: 'es-ES',
  hindi: 'hi-IN',
  tamil: 'ta-IN',
  telugu: 'te-IN',
  gujarati: 'gu-IN',
  marathi: 'mr-IN',
  german: 'de-DE',
  french: 'fr-FR',
  russian: 'ru-RU',
  chinese: 'zh-CN',
  mandarin: 'zh-CN',
};

const getDateKey = (timestamp) => {
  if (!timestamp) return 'unknown';
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return 'unknown';
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
};

const mapSessionMessages = (sessionData, dayKey = null) => {
  const messages = (sessionData?.messages || []).map((message, index) => ({
    messageId: message.message_id ?? message.messageId,
    role: message.sender === 'ai' || message.sender === 'assistant' ? 'assistant' : message.sender === 'user' ? 'user' : message.sender,
    content: message.content,
    timestamp: message.completed_at || message.timestamp,
    id: `${message.message_id ?? message.messageId ?? index}_${message.completed_at || message.timestamp}`,
    native_name: message.native_name ?? sessionData.native_name ?? null,
    terms: message.terms,
    glossary: message.glossary,
    images: message.images,
    message_type: message.message_type,
    intent_gate: message.intent_gate,
    gate_metadata: message.gate_metadata,
  }));
  return dayKey ? messages.filter((message) => getDateKey(message.timestamp) === dayKey) : messages;
};

export default function ChatViewScreen({ route, navigation }) {
  const { t, i18n } = useTranslation();
  const { colors } = useTheme();
  const { session } = route.params;
  const locale = LANGUAGE_LOCALES[i18n.resolvedLanguage || i18n.language] || 'en-IN';
  const [messages, setMessages] = useState(session.messages || []);
  const [loadingInitial, setLoadingInitial] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadError, setLoadError] = useState('');
  const daySessionIds = useMemo(() => [...new Set((session?.session_ids || []).filter(Boolean))], [session?.session_ids]);
  const isDayTranscript = daySessionIds.length > 0;
  const [loadedSessionCount, setLoadedSessionCount] = useState(isDayTranscript && session.messages?.length ? daySessionIds.length : 0);

  const isUserMessage = (message) => (message?.sender || message?.role) === 'user';
  const isAssistantMessage = (message) => (message?.sender || message?.role) === 'assistant';
  const answerCount = messages.filter((message) => isAssistantMessage(message) && message?.message_type === 'answer').length;
  const conversationCount = answerCount || messages.filter(isUserMessage).length;
  const firstTimestamp = messages.find(isUserMessage)?.timestamp || session.created_at || session.date_key;

  const loadSessions = useCallback(async (sessionIds) => {
    const token = await storage.getAuthToken();
    if (!token) {
      navigation.replace('Login');
      return [];
    }
    const responses = await Promise.all(sessionIds.map((id) => fetch(`${API_BASE_URL}${getEndpoint(`/chat-v2/session/${id}`)}`, { headers: { Authorization: `Bearer ${token}` } })));
    if (responses.some((response) => response.status === 401)) {
      await storage.removeAuthToken();
      navigation.replace('Login');
      return [];
    }
    const sessions = await Promise.all(responses.filter((response) => response.ok).map((response) => response.json()));
    return sessions.flatMap((sessionData) => mapSessionMessages(sessionData, session?.date_key));
  }, [navigation, session?.date_key]);

  useEffect(() => {
    if (!isDayTranscript || messages.length || loadedSessionCount) return undefined;
    let cancelled = false;
    const run = async () => {
      setLoadingInitial(true);
      setLoadError('');
      try {
        const ids = daySessionIds.slice(0, DAY_SESSION_BATCH_SIZE);
        const next = await loadSessions(ids);
        if (!cancelled) {
          setMessages(next.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp)));
          setLoadedSessionCount(ids.length);
        }
      } catch (error) {
        if (!cancelled) setLoadError(t('historyDetail.loadError'));
      } finally {
        if (!cancelled) setLoadingInitial(false);
      }
    };
    run();
    return () => { cancelled = true; };
  }, [daySessionIds, isDayTranscript, loadSessions, loadedSessionCount, messages.length, t]);

  const loadMoreMessages = async () => {
    if (loadingMore || loadedSessionCount >= daySessionIds.length) return;
    setLoadingMore(true);
    setLoadError('');
    try {
      const ids = daySessionIds.slice(loadedSessionCount, loadedSessionCount + DAY_SESSION_BATCH_SIZE);
      const next = await loadSessions(ids);
      setMessages((current) => {
        const known = new Set(current.map((message) => message.id || message.messageId));
        return [...current, ...next.filter((message) => !known.has(message.id || message.messageId))]
          .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
      });
      setLoadedSessionCount((current) => current + ids.length);
    } catch (error) {
      setLoadError(t('historyDetail.loadMoreError'));
    } finally {
      setLoadingMore(false);
    }
  };

  const displayDate = useMemo(() => {
    if (session?.date_key) {
      const date = new Date(`${session.date_key}T00:00:00`);
      if (!Number.isNaN(date.getTime())) return new Intl.DateTimeFormat(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).format(date);
    }
    const date = new Date(firstTimestamp);
    return Number.isNaN(date.getTime()) ? session?.date_label || t('historyDetail.savedConversation') : new Intl.DateTimeFormat(locale, { dateStyle: 'long' }).format(date);
  }, [firstTimestamp, locale, session?.date_key, session?.date_label, t]);

  const displayTime = useMemo(() => {
    const date = new Date(firstTimestamp);
    return Number.isNaN(date.getTime()) ? '' : new Intl.DateTimeFormat(locale, { hour: 'numeric', minute: '2-digit' }).format(date);
  }, [firstTimestamp, locale]);

  const shareChat = async () => {
    if (!messages.length) {
      Alert.alert(t('historyDetail.noMessages'), t('historyDetail.nothingToShare'));
      return;
    }
    const transcript = messages.map((message) => `${isUserMessage(message) ? t('historyDetail.you') : 'AstroRoshni'}: ${message.content}`).join('\n\n');
    await Share.share({ message: `${t('historyDetail.sharedTitle', { date: displayDate })}\n\n${transcript}\n\n${t('historyDetail.sharedFrom')}` });
  };

  const renderMessage = ({ item }) => (
    <MessageBubble
      message={item}
      language={i18n.resolvedLanguage || i18n.language}
      onDelete={(messageId) => setMessages((current) => current.filter((message) => message.messageId !== messageId))}
      sessionId={session?.session_id}
    />
  );

  const footer = (
    <View style={styles.footerArea}>
      {loadError ? <Text style={[styles.errorText, { color: colors.error }]}>{loadError}</Text> : null}
      {loadedSessionCount < daySessionIds.length ? (
        <TouchableOpacity
          onPress={loadMoreMessages}
          disabled={loadingMore}
          style={[styles.loadMoreButton, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}
        >
          {loadingMore ? <ActivityIndicator color={colors.primary} /> : <Text style={[styles.loadMoreText, { color: colors.primary }]}>{t('historyDetail.loadMore')}</Text>}
        </TouchableOpacity>
      ) : null}
      {isDayTranscript && daySessionIds.length ? (
        <Text style={[styles.loadedMeta, { color: colors.textTertiary }]}>{t('historyDetail.loadedSessions', { loaded: loadedSessionCount, total: daySessionIds.length })}</Text>
      ) : null}
    </View>
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <FocusedStatusBar backgroundColor={colors.headerSurface} />
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.headerSurface }]} edges={['top']}>
        <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cardBorder }]}>
          <TouchableOpacity onPress={() => goBackOrHome(navigation)} style={[styles.headerButton, { borderColor: colors.cosmicLine || colors.cardBorder }]}>
            <Ionicons name="arrow-back" size={21} color={colors.textInverse} />
          </TouchableOpacity>
          <View style={styles.headerCopy}>
            <Text style={[styles.headerEyebrow, { color: colors.accent }]}>{t('historyDetail.privateArchive')}</Text>
            <Text style={[styles.headerTitle, { color: colors.textInverse }]} numberOfLines={1}>{session.native_name || t('historyDetail.title')}</Text>
          </View>
          <TouchableOpacity onPress={shareChat} style={[styles.headerButton, { borderColor: colors.cosmicLine || colors.cardBorder }]} accessibilityLabel={t('historyDetail.share')}>
            <Ionicons name="share-outline" size={20} color={colors.textInverse} />
          </TouchableOpacity>
        </View>

        <View style={[styles.contentShell, { backgroundColor: colors.background }]}>
        <View style={[styles.contextCard, { backgroundColor: colors.surfaceInverse, borderColor: colors.cardBorder }]}>
          <View pointerEvents="none" style={styles.linework}>
            <View style={[styles.orbitLarge, { borderColor: colors.accent }]} />
            <View style={[styles.orbitSmall, { borderColor: colors.accent }]} />
          </View>
          <Text style={[styles.contextEyebrow, { color: colors.accent }]}>{t('historyDetail.consultation')}</Text>
          <Text style={[styles.contextTitle, { color: colors.onSurfaceInverse || colors.textInverse }]}>{displayDate}</Text>
          <View style={styles.metaRow}>
            {displayTime ? <Text style={[styles.metaText, { color: colors.onSurfaceInverseMuted || colors.textInverseMuted }]}>{displayTime}</Text> : null}
            <View style={[styles.metaDot, { backgroundColor: colors.accent }]} />
            <Text style={[styles.metaText, { color: colors.onSurfaceInverseMuted || colors.textInverseMuted }]}>{t('historyDetail.conversationCount', { count: conversationCount })}</Text>
          </View>
        </View>

        <FlatList
          data={messages}
          renderItem={renderMessage}
          keyExtractor={(item, index) => String(item?.id || item?.messageId || `${item?.timestamp}_${index}`)}
          style={styles.list}
          contentContainerStyle={[styles.listContent, !messages.length && styles.emptyList]}
          showsVerticalScrollIndicator={false}
          initialNumToRender={8}
          maxToRenderPerBatch={8}
          windowSize={7}
          removeClippedSubviews={Platform.OS === 'android'}
          ListEmptyComponent={loadingInitial ? (
            <View style={styles.emptyState}><ActivityIndicator color={colors.primary} /><Text style={[styles.emptyBody, { color: colors.textSecondary }]}>{t('historyDetail.loading')}</Text></View>
          ) : (
            <View style={styles.emptyState}>
              <View style={[styles.emptyIcon, { backgroundColor: colors.accentSoft }]}><Ionicons name="chatbubbles-outline" size={28} color={colors.onAccent} /></View>
              <Text style={[styles.emptyTitle, { color: colors.text }]}>{t('historyDetail.noMessages')}</Text>
              <Text style={[styles.emptyBody, { color: colors.textSecondary }]}>{t('historyDetail.noMessagesBody')}</Text>
            </View>
          )}
          ListFooterComponent={footer}
        />

        <View style={[styles.actionBar, { backgroundColor: colors.background, borderTopColor: colors.cardBorder }]}>
          <TouchableOpacity onPress={shareChat} style={[styles.secondaryAction, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
            <Ionicons name="share-outline" size={18} color={colors.primary} />
            <Text style={[styles.secondaryActionText, { color: colors.text }]}>{t('historyDetail.share')}</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => navigation.navigate('Home', { startChat: true })} style={[styles.primaryAction, { backgroundColor: colors.primary }]}>
            <Ionicons name="sparkles-outline" size={18} color={colors.onPrimary} />
            <Text style={[styles.primaryActionText, { color: colors.onPrimary }]}>{t('historyDetail.continueChat')}</Text>
          </TouchableOpacity>
        </View>
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 }, safeArea: { flex: 1 }, contentShell: { flex: 1 },
  header: { minHeight: 78, paddingHorizontal: 18, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1 },
  headerButton: { width: 42, height: 42, borderRadius: 21, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  headerCopy: { flex: 1, minWidth: 0, paddingHorizontal: 14 },
  headerEyebrow: { fontSize: 10, fontWeight: '900', letterSpacing: 1.8 },
  headerTitle: { fontSize: 22, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontWeight: '600', marginTop: 2 },
  contextCard: { margin: 16, marginBottom: 4, borderWidth: 1, borderRadius: 26, paddingHorizontal: 22, paddingVertical: 22, overflow: 'hidden' },
  linework: { ...StyleSheet.absoluteFillObject, opacity: 0.45 },
  orbitLarge: { position: 'absolute', width: 150, height: 150, borderRadius: 75, borderWidth: 1, right: -48, top: -83 },
  orbitSmall: { position: 'absolute', width: 96, height: 96, borderRadius: 48, borderWidth: 1, right: -20, top: -56 },
  contextEyebrow: { fontSize: 10, fontWeight: '900', letterSpacing: 1.8 },
  contextTitle: { fontSize: 27, lineHeight: 33, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontWeight: '500', marginTop: 9, maxWidth: '87%' },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 9, marginTop: 13 },
  metaText: { fontSize: 12, fontWeight: '700' }, metaDot: { width: 4, height: 4, borderRadius: 2 },
  list: { flex: 1 }, listContent: { paddingHorizontal: 12, paddingTop: 12, paddingBottom: 24, flexGrow: 1 }, emptyList: { justifyContent: 'center' },
  emptyState: { alignItems: 'center', justifyContent: 'center', paddingHorizontal: 30, paddingVertical: 44, gap: 10 },
  emptyIcon: { width: 60, height: 60, borderRadius: 22, alignItems: 'center', justifyContent: 'center', marginBottom: 5 },
  emptyTitle: { fontSize: 21, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontWeight: '600', textAlign: 'center' },
  emptyBody: { fontSize: 14, lineHeight: 20, textAlign: 'center' },
  footerArea: { alignItems: 'center', paddingTop: 8, paddingBottom: 18, gap: 9 },
  errorText: { fontSize: 12, fontWeight: '700', textAlign: 'center' },
  loadMoreButton: { minWidth: 190, minHeight: 46, borderRadius: 17, borderWidth: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 18 },
  loadMoreText: { fontSize: 13, fontWeight: '900' }, loadedMeta: { fontSize: 11, textAlign: 'center' },
  actionBar: { borderTopWidth: 1, flexDirection: 'row', paddingHorizontal: 16, paddingTop: 12, paddingBottom: Platform.OS === 'ios' ? 12 : 16, gap: 10 },
  secondaryAction: { minHeight: 50, paddingHorizontal: 18, borderRadius: 18, borderWidth: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  secondaryActionText: { fontSize: 13, fontWeight: '800' },
  primaryAction: { flex: 1, minHeight: 50, paddingHorizontal: 18, borderRadius: 18, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  primaryActionText: { fontSize: 14, fontWeight: '900' },
});
