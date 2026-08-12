import React, { useCallback, useEffect, useLayoutEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
  Platform,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useRoute } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { supportAPI } from '../../services/api';
import { sanitizeSupportBody, sanitizeSupportSubject } from '../../utils/supportText';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import { trackAstrologyEvent } from '../../utils/analytics';
import { goBackOrHome } from '../../navigation/navHelpers';
import FocusedStatusBar from '../Common/FocusedStatusBar';

function formatApiError(e, t) {
  const d = e.response?.data?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return d.map((x) => x.msg || String(x)).join(' ');
  return e.message || (t ? t('support.requestFailed') : 'Request failed');
}

export default function SupportScreen({ navigation }) {
  const route = useRoute();
  const { colors } = useTheme();
  const { t } = useTranslation();
  const source = Platform.OS === 'ios' ? 'ios' : 'android';

  const [view, setView] = useState('list');
  const [tickets, setTickets] = useState([]);
  const [listLoading, setListLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [threadLoading, setThreadLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [subject, setSubject] = useState('');
  const [composeBody, setComposeBody] = useState('');

  const [activeId, setActiveId] = useState(null);
  const [ticketMeta, setTicketMeta] = useState(null);
  const [messages, setMessages] = useState([]);
  const [replyText, setReplyText] = useState('');
  const [downloadingAttachmentId, setDownloadingAttachmentId] = useState(null);

  const loadTickets = useCallback(async () => {
    setError('');
    try {
      const { data } = await supportAPI.listTickets();
      setTickets(data.tickets || []);
    } catch (e) {
      setError(formatApiError(e, t));
      setTickets([]);
    } finally {
      setListLoading(false);
      setRefreshing(false);
    }
  }, [t]);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  const openThread = useCallback(async (id) => {
    setActiveId(id);
    setView('thread');
    setThreadLoading(true);
    setError('');
    setReplyText('');
    try {
      const { data } = await supportAPI.getTicket(id);
      setTicketMeta(data.ticket);
      setMessages(data.messages || []);
    } catch (e) {
      setError(formatApiError(e, t));
      setTicketMeta(null);
      setMessages([]);
    } finally {
      setThreadLoading(false);
    }
  }, [t]);

  /** Push notification tap: open this ticket’s thread with latest messages */
  useLayoutEffect(() => {
    const raw = route.params?.ticketId;
    if (raw == null || raw === '') return;
    const id = Number(raw);
    if (Number.isNaN(id) || id < 1) return;
    openThread(id);
    try {
      navigation.setParams({ ticketId: undefined });
    } catch (_) {}
  }, [route.params?.ticketId, navigation, openThread]);

  const refreshThread = async () => {
    if (!activeId) return;
    try {
      const { data } = await supportAPI.getTicket(activeId);
      setTicketMeta(data.ticket);
      setMessages(data.messages || []);
    } catch (e) {
      setError(formatApiError(e, t));
    }
  };

  const ticketStatusLabel = (status) => {
    if (!status) return '';
    const s = String(status).toLowerCase();
    if (s === 'open') return t('support.statusOpen');
    if (s === 'closed') return t('support.statusClosed');
    if (s === 'pending') return t('support.statusPending');
    return status;
  };

  const ticketSourceLabel = (src) => {
    if (!src) return '';
    const s = String(src).toLowerCase();
    if (s === 'ios') return t('support.sourceIos');
    if (s === 'android') return t('support.sourceAndroid');
    return src;
  };

  const submitNew = async () => {
    const sub = sanitizeSupportSubject(subject);
    const msg = sanitizeSupportBody(composeBody);
    if (!sub || !msg) {
      setError(t('support.fillBoth'));
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await supportAPI.createTicket({ subject: sub, message: msg, source });
      trackAstrologyEvent.contact();
      setSubject('');
      setComposeBody('');
      setView('list');
      await loadTickets();
    } catch (e) {
      setError(formatApiError(e, t));
    } finally {
      setSubmitting(false);
    }
  };

  const sendReply = async () => {
    const msg = sanitizeSupportBody(replyText);
    if (!msg || !activeId) {
      setError(t('support.enterMessage'));
      return;
    }
    if (ticketMeta?.status === 'closed') {
      setError(t('support.closedTicket'));
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await supportAPI.postMessage(activeId, msg);
      setReplyText('');
      await refreshThread();
      await loadTickets();
    } catch (e) {
      setError(formatApiError(e, t));
    } finally {
      setSubmitting(false);
    }
  };

  const downloadAttachment = async (attachment) => {
    if (!attachment?.id) return;
    setDownloadingAttachmentId(attachment.id);
    try {
      const token = (await AsyncStorage.getItem('authToken')) || '';
      if (!token) {
        throw new Error(t('knowledgeSupport.loginToDownload'));
      }
      const filename = attachment.filename || `support_attachment_${attachment.id}.pdf`;
      const targetPath = `${FileSystem.cacheDirectory}${Date.now()}_${filename.replace(/[^a-zA-Z0-9._-]/g, '_')}`;
      const url = `${API_BASE_URL}${getEndpoint(`/support/attachments/${attachment.id}/download`)}`;
      const { status, uri } = await FileSystem.downloadAsync(url, targetPath, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-AstroRoshni-Authorization': `Bearer ${token}`,
          Accept: 'application/pdf',
        },
      });
      if (status < 200 || status >= 300) {
        throw new Error(t('knowledgeSupport.downloadFailed'));
      }
      const isAvailable = await Sharing.isAvailableAsync();
      if (!isAvailable) {
        Alert.alert(t('knowledgeSupport.downloaded'), t('knowledgeSupport.downloadedBody'));
        return;
      }
      await Sharing.shareAsync(uri, {
        mimeType: attachment.mime_type || 'application/pdf',
        dialogTitle: filename,
        UTI: 'com.adobe.pdf',
      });
    } catch (e) {
      Alert.alert(t('knowledgeSupport.downloadFailed'), e?.message || t('knowledgeSupport.downloadFailedBody'));
    } finally {
      setDownloadingAttachmentId(null);
    }
  };

  const bg = colors.background;
  const cardBg = colors.surfaceRaised;
  const borderCol = colors.cardBorder;

  const renderList = () => (
    <ScrollView
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true);
            loadTickets();
          }}
        />
      }
    >
      <View style={[styles.hero, { backgroundColor: colors.surfaceInverse, borderColor: colors.cosmicLine || borderCol }]}>
        <View pointerEvents="none" style={styles.heroLinework}><View style={[styles.heroOrbit, styles.heroOrbitLarge, { borderColor: colors.accent }]} /><View style={[styles.heroOrbit, styles.heroOrbitSmall, { borderColor: colors.accent }]} /></View>
        <Text style={[styles.heroEyebrow, { color: colors.accent }]}>{t('knowledgeSupport.supportEyebrow')}</Text>
        <Text style={[styles.heroTitle, { color: colors.onSurfaceInverse }]}>{t('knowledgeSupport.supportTitle')}</Text>
        <Text style={[styles.heroBody, { color: colors.onSurfaceInverseMuted }]}>{t('knowledgeSupport.supportBody')}</Text>
      </View>
      <View style={styles.listHeading}><View><Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{t('knowledgeSupport.yourRequests')}</Text><Text style={[styles.sectionTitle, { color: colors.text }]}>{t('knowledgeSupport.conversationTitle')}</Text></View><View style={[styles.countBadge, { backgroundColor: colors.accentSoft }]}><Text style={[styles.countText, { color: colors.onAccent }]}>{tickets.length}</Text></View></View>
      <TouchableOpacity
        style={[styles.primaryBtn, { backgroundColor: colors.primary }]}
        onPress={() => {
          setView('compose');
          setError('');
        }}
      >
        <Ionicons name="add" size={20} color={colors.onPrimary} /><Text style={[styles.primaryBtnText, { color: colors.onPrimary }]}>{t('support.newTicket')}</Text>
      </TouchableOpacity>

      {listLoading ? (
        <ActivityIndicator size="large" color={colors.primary} style={{ marginTop: 24 }} />
      ) : tickets.length === 0 ? (
        <Text style={[styles.empty, { color: colors.textSecondary }]}>{t('support.noTickets')}</Text>
      ) : (
        tickets.map((tk) => (
          <TouchableOpacity
            key={tk.id}
            style={[styles.card, { backgroundColor: cardBg, borderColor: borderCol }]}
            onPress={() => openThread(tk.id)}
          >
            <View style={styles.ticketTop}><Text style={[styles.ticketNumber, { color: colors.primary }]}>#{tk.id}</Text><View style={[styles.statusPill, { backgroundColor: colors.surfaceMuted }]}><Text style={[styles.statusText, { color: colors.textSecondary }]}>{ticketStatusLabel(tk.status)}</Text></View></View>
            <Text style={[styles.ticketTitle, { color: colors.text }]} numberOfLines={2}>{tk.subject}</Text>
            {tk.last_message_preview ? <Text style={[styles.preview, { color: colors.textSecondary }]} numberOfLines={2}>{tk.last_message_preview}</Text> : null}
            <View style={styles.ticketFooter}><Text style={[styles.ticketMeta, { color: colors.textTertiary }]}>{ticketSourceLabel(tk.source)}</Text><Ionicons name="arrow-forward" size={18} color={colors.primary} /></View>
          </TouchableOpacity>
        ))
      )}
    </ScrollView>
  );

  const renderCompose = () => (
    <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
      <View style={[styles.composeIntro, { backgroundColor: colors.surfaceInverse, borderColor: colors.cosmicLine || borderCol }]}><Text style={[styles.heroEyebrow, { color: colors.accent }]}>{t('knowledgeSupport.newRequest')}</Text><Text style={[styles.composeTitle, { color: colors.onSurfaceInverse }]}>{t('knowledgeSupport.tellUs')}</Text><Text style={[styles.composeBody, { color: colors.onSurfaceInverseMuted }]}>{t('knowledgeSupport.tellUsBody')}</Text></View>
      <Text style={[styles.label, { color: colors.text }]}>{t('support.subject')}</Text>
      <TextInput
        style={[styles.input, { color: colors.text, borderColor: borderCol, backgroundColor: cardBg }]}
        value={subject}
        onChangeText={setSubject}
        maxLength={220}
        placeholder={t('support.subjectPlaceholder')}
        placeholderTextColor={colors.textSecondary}
      />
      <Text style={[styles.label, { color: colors.text }]}>{t('support.message')}</Text>
      <TextInput
        style={[styles.textarea, { color: colors.text, borderColor: borderCol, backgroundColor: cardBg }]}
        value={composeBody}
        onChangeText={setComposeBody}
        maxLength={9000}
        multiline
        placeholder={t('support.messagePlaceholder')}
        placeholderTextColor={colors.textSecondary}
      />
      <TouchableOpacity
        style={[styles.primaryBtn, { backgroundColor: submitting ? colors.textTertiary : colors.primary }]}
        onPress={submitNew}
        disabled={submitting}
      >
        {submitting ? (
          <ActivityIndicator color={colors.onPrimary} />
        ) : (
          <Text style={[styles.primaryBtnText, { color: colors.onPrimary }]}>{t('support.send')}</Text>
        )}
      </TouchableOpacity>
      <TouchableOpacity style={styles.secondaryBtn} onPress={() => setView('list')}>
        <Text style={[styles.secondaryBtnText, { color: colors.text }]}>{t('support.back')}</Text>
      </TouchableOpacity>
    </ScrollView>
  );

  const renderThread = () => (
    <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
      {threadLoading ? (
        <ActivityIndicator size="large" color={colors.primary} style={{ marginTop: 24 }} />
      ) : ticketMeta ? (
        <>
          <View style={[styles.threadHero, { backgroundColor: colors.surfaceInverse, borderColor: colors.cosmicLine || borderCol }]}><Text style={[styles.heroEyebrow, { color: colors.accent }]}>#{ticketMeta.id || activeId} · {ticketStatusLabel(ticketMeta.status)}</Text><Text style={[styles.threadTitle, { color: colors.onSurfaceInverse }]}>{ticketMeta.subject}</Text></View>
          {messages.map((m) => (
            <View
              key={m.id}
              style={[
                styles.bubble,
                { backgroundColor: m.author_role === 'admin' ? colors.surfaceRaised : colors.surfaceMuted, borderColor: borderCol, alignSelf: m.author_role === 'admin' ? 'flex-start' : 'flex-end' },
              ]}
            >
              <Text style={[styles.bubbleMeta, { color: colors.textSecondary }]}>
                {m.author_role === 'admin' ? t('support.roleAdmin') : t('support.roleYou')} · {m.created_at || ''}
              </Text>
              {m.body ? <Text style={[styles.bubbleBody, { color: colors.text }]}>{m.body}</Text> : null}
              {Array.isArray(m.attachments) && m.attachments.length > 0 ? (
                <View style={styles.attachmentList}>
                  {m.attachments.map((att) => {
                    const isDownloading = downloadingAttachmentId === att.id;
                    return (
                      <TouchableOpacity
                        key={att.id}
                        style={[styles.attachmentCard, { borderColor: borderCol, backgroundColor: cardBg }]}
                        onPress={() => downloadAttachment(att)}
                        disabled={isDownloading}
                      >
                        <View style={{ flex: 1 }}>
                          <Text style={[styles.attachmentName, { color: colors.text }]} numberOfLines={1}>
                            {att.filename}
                          </Text>
                          <Text style={[styles.attachmentMeta, { color: colors.textSecondary }]}>
                            {`PDF · ${Math.max(1, Math.round((Number(att.size_bytes || 0) / 1024) || 0))} KB`}
                          </Text>
                        </View>
                        {isDownloading ? (
                          <ActivityIndicator size="small" color={colors.primary} />
                        ) : (
                          <Ionicons name="download-outline" size={20} color={colors.text} />
                        )}
                      </TouchableOpacity>
                    );
                  })}
                </View>
              ) : null}
            </View>
          ))}
          {ticketMeta.status !== 'closed' ? (
            <>
              <Text style={[styles.label, { color: colors.text }]}>{t('support.reply')}</Text>
              <TextInput
                style={[styles.textarea, { color: colors.text, borderColor: borderCol, backgroundColor: cardBg }]}
                value={replyText}
                onChangeText={setReplyText}
                maxLength={9000}
                multiline
                placeholder={t('support.replyPlaceholder')}
                placeholderTextColor={colors.textSecondary}
              />
              <TouchableOpacity
                style={[styles.primaryBtn, { backgroundColor: submitting ? colors.textTertiary : colors.primary }]}
                onPress={sendReply}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator color={colors.onPrimary} />
                ) : (
                  <Text style={[styles.primaryBtnText, { color: colors.onPrimary }]}>{t('support.sendReply')}</Text>
                )}
              </TouchableOpacity>
            </>
          ) : (
            <Text style={{ color: colors.textSecondary, marginTop: 8 }}>{t('support.closedHint')}</Text>
          )}
        </>
      ) : (
        <Text style={{ color: colors.textSecondary }}>{t('support.loadFailed')}</Text>
      )}
      <TouchableOpacity
        style={styles.secondaryBtn}
        onPress={() => {
          setView('list');
          setActiveId(null);
          loadTickets();
        }}
      >
        <Text style={[styles.secondaryBtnText, { color: colors.text }]}>{t('support.backToList')}</Text>
      </TouchableOpacity>
    </ScrollView>
  );

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.headerSurface }]} edges={['top', 'left', 'right']}>
      <FocusedStatusBar backgroundColor={colors.headerSurface} />
      <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine || borderCol }]}>
        <TouchableOpacity onPress={() => view === 'list' ? goBackOrHome(navigation) : setView('list')} style={[styles.backButton, { borderColor: colors.cosmicLine || borderCol }]}>
          <Ionicons name="arrow-back" size={21} color={colors.textInverse} />
        </TouchableOpacity>
        <View style={styles.headerCopy}><Text style={[styles.headerEyebrow, { color: colors.accent }]}>{t('knowledgeSupport.helpDesk')}</Text><Text style={[styles.headerTitle, { color: colors.textInverse }]}>{t('support.title')}</Text></View>
        <View style={[styles.headerSeal, { borderColor: colors.cosmicLine || borderCol }]}><Ionicons name="chatbubbles-outline" size={19} color={colors.accent} /></View>
      </View>

      <View style={[styles.contentShell, { backgroundColor: bg }]}>
      {error ? (
        <View style={styles.errBar}>
          <Text style={styles.errText}>{error}</Text>
        </View>
      ) : null}

      {view === 'list' && renderList()}
      {view === 'compose' && renderCompose()}
      {view === 'thread' && renderThread()}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  contentShell: { flex: 1 },
  header: {
    minHeight: 78,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 18,
    borderBottomWidth: 1,
  },
  backButton: { width: 42, height: 42, borderRadius: 21, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  headerCopy: { flex: 1, paddingHorizontal: 14 }, headerEyebrow: { fontSize: 9, fontWeight: '900', letterSpacing: 1.7 }, headerTitle: { fontSize: 21, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontWeight: '600', marginTop: 2 },
  headerSeal: { width: 42, height: 42, borderRadius: 21, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  errBar: { backgroundColor: 'rgba(220,38,38,0.12)', paddingHorizontal: 12, paddingVertical: 8 },
  errText: { color: '#b91c1c', fontSize: 13 },
  scrollContent: { padding: 16, paddingBottom: 60 },
  hero: { minHeight: 250, borderRadius: 30, borderWidth: 1, padding: 26, justifyContent: 'flex-end', overflow: 'hidden', marginBottom: 28 },
  heroLinework: { ...StyleSheet.absoluteFillObject, opacity: 0.48 }, heroOrbit: { position: 'absolute', borderWidth: 1 }, heroOrbitLarge: { width: 180, height: 180, borderRadius: 90, right: -50, top: -72 }, heroOrbitSmall: { width: 112, height: 112, borderRadius: 56, right: -13, top: -35 },
  heroEyebrow: { fontSize: 10, fontWeight: '900', letterSpacing: 1.8, textTransform: 'uppercase' }, heroTitle: { fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontSize: 36, lineHeight: 40, marginTop: 10 }, heroBody: { fontSize: 15, lineHeight: 22, fontWeight: '600', marginTop: 12, maxWidth: '90%' },
  listHeading: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 18 }, sectionEyebrow: { fontSize: 10, fontWeight: '900', letterSpacing: 1.6 }, sectionTitle: { fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontSize: 27, marginTop: 4 }, countBadge: { minWidth: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center' }, countText: { fontSize: 13, fontWeight: '900' },
  primaryBtn: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  primaryBtnText: { fontWeight: '800', fontSize: 15 },
  secondaryBtn: { paddingVertical: 12, alignItems: 'center' },
  secondaryBtnText: { fontSize: 16 },
  card: {
    borderRadius: 20,
    borderWidth: 1,
    padding: 17,
    marginBottom: 12,
  },
  ticketTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }, ticketNumber: { fontSize: 10, fontWeight: '900', letterSpacing: 1.2 }, statusPill: { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999 }, statusText: { fontSize: 10, fontWeight: '800' }, ticketFooter: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 14 },
  ticketTitle: { fontSize: 18, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontWeight: '600' },
  ticketMeta: { fontSize: 12, marginTop: 6 },
  preview: { fontSize: 13, marginTop: 8 },
  empty: { textAlign: 'center', marginTop: 32, fontSize: 15 },
  composeIntro: { borderRadius: 26, borderWidth: 1, padding: 22, marginBottom: 20 }, composeTitle: { fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontSize: 28, marginTop: 8 }, composeBody: { fontSize: 14, lineHeight: 21, marginTop: 9 }, label: { fontWeight: '800', marginBottom: 8, marginTop: 10 },
  input: {
    borderWidth: 1,
    borderRadius: 17,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
  },
  textarea: {
    borderWidth: 1,
    borderRadius: 17,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    minHeight: 120,
    textAlignVertical: 'top',
  },
  threadHero: { borderRadius: 26, borderWidth: 1, padding: 22, marginBottom: 20 }, threadTitle: { fontSize: 28, lineHeight: 34, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), marginTop: 8 },
  bubble: { maxWidth: '91%', borderRadius: 20, borderWidth: 1, padding: 14, marginBottom: 11 },
  bubbleMeta: { fontSize: 11, marginBottom: 6 },
  bubbleBody: { fontSize: 15, lineHeight: 22 },
  attachmentList: { marginTop: 10, gap: 8 },
  attachmentCard: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  attachmentName: { fontSize: 14, fontWeight: '600' },
  attachmentMeta: { fontSize: 12, marginTop: 2 },
});
