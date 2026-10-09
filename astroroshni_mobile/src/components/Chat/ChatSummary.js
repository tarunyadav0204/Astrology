import React, { useState } from 'react';
import { Modal, View, Text, TouchableOpacity, FlatList, ActivityIndicator, ScrollView } from 'react-native';
import ConflictResolution from './ConflictResolution';
import Ionicons from '@expo/vector-icons/Ionicons';
import * as Clipboard from 'expo-clipboard';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { storage } from '../../services/storage';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';

export default function ChatSummary({ messages = [], onResolved, header = false }) {
  const { colors } = useTheme(); const { t, i18n } = useTranslation();
  const [tool, setTool] = useState('summary');
  const [open, setOpen] = useState(false), [ids, setIds] = useState([]), [summary, setSummary] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const answers = messages.filter(message => (message.role || message.sender) === 'assistant' && (message.messageId || message.message_id) && message.content && !message.isProcessing && !message.isTyping && !message.instantStreaming && (!message.status || message.status === 'completed') && (!message.message_type || message.message_type === 'answer'));
  const generate = async () => {
    setBusy(true); setError('');
    try {
      const token = await storage.getAuthToken();
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat/summaries')}`, { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ message_ids: ids, language: i18n.resolvedLanguage || i18n.language || 'english' }) });
      const data = await response.json();
      if (!response.ok) throw new Error(t('premiumUi.chat.summaryError', 'Unable to summarize these answers.'));
      setSummary(data.summary);
    } catch (err) { setError(t('premiumUi.chat.summaryError', 'Unable to summarize these answers.')); } finally { setBusy(false); }
  };
  return <><TouchableOpacity accessibilityRole="button" accessibilityLabel={t('premiumUi.chat.conflict.tools', 'Chat tools')} onPress={() => setOpen(true)} style={{ width: 40, height: 40, borderRadius: 20, borderWidth: 1, borderColor: header ? colors.textInverse : colors.cardBorder, alignItems: 'center', justifyContent: 'center', backgroundColor: header ? 'transparent' : colors.surface }}><Ionicons name="construct-outline" size={20} color={header ? colors.textInverse : colors.primary} /></TouchableOpacity>
    <Modal visible={open} transparent animationType="slide" onRequestClose={() => { if (!busy) setOpen(false); }}><View style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: colors.overlay }}><View accessibilityViewIsModal style={{ height: '85%', padding: 20, borderTopLeftRadius: 20, borderTopRightRadius: 20, backgroundColor: colors.surfaceRaised }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}><Text style={{ color: colors.text, fontSize: 20, fontWeight: '600' }}>{tool === 'summary' ? t('premiumUi.chat.summarizeChat', 'Summarize chat') : t('premiumUi.chat.conflict.title', 'Resolve conflicting answers')}</Text><TouchableOpacity disabled={busy} onPress={() => setOpen(false)} accessibilityLabel={t('common.close', 'Close')}><Ionicons name="close" size={24} color={colors.text} /></TouchableOpacity></View>
      <View style={{ flexDirection: 'row', gap: 10, marginVertical: 12 }}><TouchableOpacity disabled={busy} onPress={() => setTool('summary')} style={{ padding: 10, borderRadius: 10, backgroundColor: tool === 'summary' ? colors.primary : colors.surface }}><Text style={{ color: tool === 'summary' ? colors.onPrimary : colors.text }}>{t('premiumUi.chat.conflict.summarize', 'Summarize')}</Text></TouchableOpacity><TouchableOpacity disabled={busy} onPress={() => setTool('conflict')} style={{ padding: 10, borderRadius: 10, backgroundColor: tool === 'conflict' ? colors.primary : colors.surface }}><Text style={{ color: tool === 'conflict' ? colors.onPrimary : colors.text }}>{t('premiumUi.chat.conflict.resolveTab', 'Resolve conflicts')}</Text></TouchableOpacity></View>
      {tool === 'conflict' ? <ConflictResolution onResolved={onResolved} messages={messages} /> : <>
      <Text style={{ color: colors.textSecondary, marginVertical: 12 }}>{t('premiumUi.chat.summarySelect', 'Select 1–3 answers. Their original questions will be included.')}</Text>
      <FlatList style={{ flexGrow: 0, maxHeight: summary ? '30%' : '60%' }} data={answers} keyExtractor={item => String(item.messageId || item.message_id)} renderItem={({ item }) => { const id = Number(item.messageId || item.message_id); const index = messages.indexOf(item); const question = [...messages.slice(0, index)].reverse().find(message => (message.role || message.sender) === 'user'); return <TouchableOpacity accessibilityRole="checkbox" accessibilityState={{ checked: ids.includes(id), disabled: busy || (!ids.includes(id) && ids.length === 3) }} disabled={busy || (!ids.includes(id) && ids.length === 3)} onPress={() => { setSummary(''); setError(''); setIds(previous => previous.includes(id) ? previous.filter(value => value !== id) : [...previous, id]); }} style={{ padding: 12, marginBottom: 8, borderRadius: 12, borderWidth: 1, borderColor: ids.includes(id) ? colors.primary : colors.cardBorder, backgroundColor: colors.surface }}><Text style={{ color: colors.text }}>{ids.includes(id) ? '☑ ' : '☐ '}{question?.content || String(item.content).replace(/<[^>]*>/g, '').slice(0, 150)}</Text></TouchableOpacity>; }} />
      <TouchableOpacity disabled={!ids.length || busy} onPress={generate} style={{ padding: 12, marginVertical: 10, borderRadius: 12, backgroundColor: colors.primary, opacity: !ids.length || busy ? 0.5 : 1 }}><Text style={{ color: colors.onPrimary, textAlign: 'center' }}>{t('premiumUi.chat.summarizeSelected', 'Summarize selected ({{count}})', { count: ids.length })}</Text></TouchableOpacity>
      {busy && <ActivityIndicator color={colors.primary} />}{error ? <Text accessibilityLiveRegion="polite" style={{ color: colors.error }}>{error}</Text> : null}
      {summary ? <ScrollView><Text style={{ color: colors.text, fontWeight: '600', marginVertical: 10 }}>{t('premiumUi.chat.summaryCount', 'Summary of {{count}} selected answers', { count: ids.length })}</Text>{summary.split('\n').map((line, index) => <Text selectable key={index} style={{ color: colors.text, lineHeight: 23, marginVertical: 4, fontWeight: /^#{1,6} /.test(line) ? '600' : '400' }}>{line.replace(/^#{1,6} /, '').split(/(\*\*[^*]+\*\*)/g).map((part, i) => part.startsWith('**') ? <Text key={i} style={{ fontWeight: '700' }}>{part.slice(2, -2)}</Text> : part)}</Text>)}<TouchableOpacity onPress={async () => { try { await Clipboard.setStringAsync(summary); } catch (_) { setError(t('premiumUi.chat.summaryCopyError', 'Could not copy the summary.')); } }} style={{ paddingVertical: 12 }}><Text style={{ color: colors.primary }}>{t('premiumUi.chat.copySummary', 'Copy summary')}</Text></TouchableOpacity></ScrollView> : null}
      </>}
    </View></View></Modal>
  </>;
}
