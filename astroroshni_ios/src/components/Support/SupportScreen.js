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
  StatusBar,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useRoute } from '@react-navigation/native';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { supportAPI } from '../../services/api';
import { sanitizeSupportBody, sanitizeSupportSubject } from '../../utils/supportText';

function formatApiError(e) {
  const d = e.response?.data?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return d.map((x) => x.msg || String(x)).join(' ');
  return e.message || 'Request failed';
}

export default function SupportScreen({ navigation }) {
  const route = useRoute();
  const { theme, colors } = useTheme();
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

  const loadTickets = useCallback(async () => {
    setError('');
    try {
      const { data } = await supportAPI.listTickets();
      setTickets(data.tickets || []);
    } catch (e) {
      setError(formatApiError(e));
      setTickets([]);
    } finally {
      setListLoading(false);
      setRefreshing(false);
    }
  }, []);

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
      setError(formatApiError(e));
      setTicketMeta(null);
      setMessages([]);
    } finally {
      setThreadLoading(false);
    }
  }, []);

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
      setError(formatApiError(e));
    }
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
      setSubject('');
      setComposeBody('');
      setView('list');
      await loadTickets();
    } catch (e) {
      setError(formatApiError(e));
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
      setError(formatApiError(e));
    } finally {
      setSubmitting(false);
    }
  };

  const bg = theme === 'dark' ? '#020617' : colors.background;
  const cardBg = theme === 'dark' ? 'rgba(15,23,42,0.95)' : colors.surface;
  const borderCol = colors.border;

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
      <TouchableOpacity
        style={[styles.primaryBtn, { backgroundColor: '#f97316' }]}
        onPress={() => {
          setView('compose');
          setError('');
        }}
      >
        <Text style={styles.primaryBtnText}>{t('support.newTicket')}</Text>
      </TouchableOpacity>

      {listLoading ? (
        <ActivityIndicator size="large" color="#f97316" style={{ marginTop: 24 }} />
      ) : tickets.length === 0 ? (
        <Text style={[styles.empty, { color: colors.textSecondary }]}>{t('support.noTickets')}</Text>
      ) : (
        tickets.map((tk) => (
          <TouchableOpacity
            key={tk.id}
            style={[styles.card, { backgroundColor: cardBg, borderColor: borderCol }]}
            onPress={() => openThread(tk.id)}
          >
            <Text style={[styles.ticketTitle, { color: colors.text }]} numberOfLines={2}>
              {tk.subject}
            </Text>
            <Text style={[styles.ticketMeta, { color: colors.textSecondary }]}>
              #{tk.id} · {tk.status} · {tk.source}
            </Text>
            {tk.last_message_preview ? (
              <Text style={[styles.preview, { color: colors.textSecondary }]} numberOfLines={2}>
                {tk.last_message_preview}
              </Text>
            ) : null}
          </TouchableOpacity>
        ))
      )}
    </ScrollView>
  );

  const renderCompose = () => (
    <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
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
        style={[styles.primaryBtn, { backgroundColor: submitting ? '#999' : '#f97316' }]}
        onPress={submitNew}
        disabled={submitting}
      >
        {submitting ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.primaryBtnText}>{t('support.send')}</Text>
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
        <ActivityIndicator size="large" color="#f97316" style={{ marginTop: 24 }} />
      ) : ticketMeta ? (
        <>
          <Text style={[styles.threadTitle, { color: colors.text }]}>{ticketMeta.subject}</Text>
          <Text style={[styles.ticketMeta, { color: colors.textSecondary, marginBottom: 12 }]}>
            {t('support.status')}: {ticketMeta.status}
          </Text>
          {messages.map((m) => (
            <View
              key={m.id}
              style={[
                styles.bubble,
                { backgroundColor: m.author_role === 'admin' ? 'rgba(34,197,94,0.15)' : 'rgba(0,0,0,0.06)' },
              ]}
            >
              <Text style={[styles.bubbleMeta, { color: colors.textSecondary }]}>
                {m.author_role === 'admin' ? t('support.roleAdmin') : t('support.roleYou')} · {m.created_at || ''}
              </Text>
              <Text style={[styles.bubbleBody, { color: colors.text }]}>{m.body}</Text>
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
                style={[styles.primaryBtn, { backgroundColor: submitting ? '#999' : '#f97316' }]}
                onPress={sendReply}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.primaryBtnText}>{t('support.sendReply')}</Text>
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
    <SafeAreaView style={[styles.container, { backgroundColor: bg }]} edges={['top', 'left', 'right']}>
      <StatusBar barStyle={theme === 'dark' ? 'light-content' : 'dark-content'} backgroundColor="#ff6b35" />
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: colors.text }]}>{t('support.title')}</Text>
        <View style={{ width: 40 }} />
      </View>

      {error ? (
        <View style={styles.errBar}>
          <Text style={styles.errText}>{error}</Text>
        </View>
      ) : null}

      {view === 'list' && renderList()}
      {view === 'compose' && renderCompose()}
      {view === 'thread' && renderThread()}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 8,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(0,0,0,0.08)',
  },
  backButton: { padding: 8 },
  headerTitle: { fontSize: 18, fontWeight: '700' },
  errBar: { backgroundColor: 'rgba(220,38,38,0.12)', paddingHorizontal: 12, paddingVertical: 8 },
  errText: { color: '#b91c1c', fontSize: 13 },
  scrollContent: { padding: 16, paddingBottom: 40 },
  primaryBtn: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  primaryBtnText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  secondaryBtn: { paddingVertical: 12, alignItems: 'center' },
  secondaryBtnText: { fontSize: 16 },
  card: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    marginBottom: 12,
  },
  ticketTitle: { fontSize: 16, fontWeight: '600' },
  ticketMeta: { fontSize: 12, marginTop: 6 },
  preview: { fontSize: 13, marginTop: 8 },
  empty: { textAlign: 'center', marginTop: 32, fontSize: 15 },
  label: { fontWeight: '600', marginBottom: 6, marginTop: 8 },
  input: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
  },
  textarea: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    minHeight: 120,
    textAlignVertical: 'top',
  },
  threadTitle: { fontSize: 20, fontWeight: '700', marginBottom: 4 },
  bubble: { borderRadius: 10, padding: 12, marginBottom: 10 },
  bubbleMeta: { fontSize: 11, marginBottom: 6 },
  bubbleBody: { fontSize: 15, lineHeight: 22 },
});
