import React, { useState } from 'react';
import { Modal, View, Text, TouchableOpacity, FlatList, ActivityIndicator, ScrollView, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import ConflictResolution from './ConflictResolution';
import PrashnaSetup from './PrashnaSetup';
import Ionicons from '@expo/vector-icons/Ionicons';
import * as Clipboard from 'expo-clipboard';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { storage } from '../../services/storage';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';

export default function ChatSummary({ messages = [], onResolved, header = false, headerSize = 36, onPrashna, onDisablePrashna }) {
  const { colors } = useTheme(); const { t, i18n } = useTranslation();
  const insets = useSafeAreaInsets();
  const [tool, setTool] = useState(null);
  const tr = (key, fallback) => t(`premiumUi.chat.tools.${key}`, fallback);
  const close = () => { if (!busy) setOpen(false); };
  const cards = [
    { key: 'summary', icon: 'reader-outline', title: t('premiumUi.chat.summarizeChat', 'Summarize chat'), description: tr('summaryDescription', 'Bring up to three answers together into one clear summary.') },
    { key: 'conflict', icon: 'git-compare-outline', title: t('premiumUi.chat.conflict.title', 'Resolve conflicting answers'), description: tr('conflictDescription', 'Compare two answers and understand why the guidance differs.') },
    ...(onPrashna ? [{ key: 'prashna', icon: 'sparkles-outline', title: t('premiumUi.chat.prashna.ask', 'Ask with Prashna'), description: tr('prashnaDescription', 'Explore a specific question using the chart for the moment you ask.') }] : []),
  ];
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
  return <><TouchableOpacity accessibilityRole="button" accessibilityLabel={t('premiumUi.chat.conflict.tools', 'Chat tools')} hitSlop={header ? { top: 6, bottom: 6, left: 3, right: 6 } : undefined} onPress={() => { setTool(null); setOpen(true); }} style={{ width: header ? headerSize : 40, height: header ? headerSize : 40, borderRadius: header ? headerSize / 2 : 20, flexShrink: 0, borderWidth: header ? 0 : 1, borderColor: colors.cardBorder, alignItems: 'center', justifyContent: 'center', backgroundColor: header ? colors.cosmicGlow : colors.surface }}><Ionicons name="construct-outline" size={header ? (headerSize >= 48 ? 24 : 20) : 20} color={header ? colors.textInverseMuted : colors.primary} /></TouchableOpacity>
    <Modal visible={open} transparent animationType="slide" onRequestClose={close}>
      <KeyboardAvoidingView enabled={tool === 'prashna'} behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1, justifyContent: 'flex-end' }}>
        <Pressable onPress={close} accessibilityRole="button" accessibilityLabel={t('common.close', 'Close')} style={{ position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, backgroundColor: colors.overlay }} />
        <View accessibilityViewIsModal style={{ ...(tool ? { height: '85%' } : { maxHeight: '85%' }), paddingHorizontal: 20, paddingBottom: Math.max(insets.bottom, 16), borderTopLeftRadius: 28, borderTopRightRadius: 28, backgroundColor: colors.surfaceRaised, borderWidth: 1, borderColor: colors.cardBorder }}>
          <View accessible={false} style={{ alignSelf: 'center', width: 36, height: 4, borderRadius: 2, backgroundColor: colors.cardBorder, marginTop: 10, marginBottom: 16 }} />
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingBottom: 16, borderBottomWidth: tool ? 1 : 0, borderBottomColor: colors.cardBorder }}>
            {tool && <TouchableOpacity accessibilityRole="button" accessibilityLabel={t('premiumUi.common.goBack', 'Go back')} disabled={busy} onPress={() => setTool(null)} style={{ width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.cardBorder }}><Ionicons name="arrow-back" size={20} color={colors.text} /></TouchableOpacity>}
            <View style={{ flex: 1 }}><Text style={{ color: colors.text, fontSize: 22, fontWeight: '700' }}>{tool ? cards.find(card => card.key === tool)?.title : t('premiumUi.chat.conflict.tools', 'Chat tools')}</Text>
              {!tool && <Text style={{ color: colors.textSecondary, fontSize: 14, lineHeight: 21, marginTop: 6 }}>{tr('description', 'Get more from your conversation.')}</Text>}
            </View>
            <TouchableOpacity accessibilityRole="button" disabled={busy} onPress={close} accessibilityLabel={t('common.close', 'Close')} style={{ width: 44, height: 44, borderRadius: 22, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.cardBorder, alignItems: 'center', justifyContent: 'center' }}><Ionicons name="close" size={21} color={colors.textSecondary} /></TouchableOpacity>
          </View>
          {!tool ? <ScrollView style={{ flexGrow: 0 }} bounces={false} contentContainerStyle={{ gap: 12, paddingBottom: 12 }}>
            {cards.map(card => <TouchableOpacity key={card.key} accessibilityRole="button" onPress={() => setTool(card.key)} activeOpacity={0.75} style={{ flexDirection: 'row', alignItems: 'center', gap: 14, padding: 16, borderRadius: 18, borderWidth: 1, borderColor: colors.cardBorder, backgroundColor: colors.surface }}>
              <View style={{ width: 48, height: 48, borderRadius: 15, backgroundColor: colors.surfaceRaised, borderWidth: 1, borderColor: colors.cardBorder, alignItems: 'center', justifyContent: 'center' }}><Ionicons name={card.icon} size={23} color={colors.primary} /></View>
              <View style={{ flex: 1 }}><Text style={{ color: colors.text, fontSize: 16, fontWeight: '600', lineHeight: 23 }}>{card.title}</Text><Text style={{ color: colors.textSecondary, fontSize: 13, lineHeight: 20, marginTop: 4 }}>{card.description}</Text></View>
              <Ionicons name="chevron-forward" size={18} color={colors.textSecondary} />
            </TouchableOpacity>)}
            {onDisablePrashna && <TouchableOpacity accessibilityRole="button" onPress={() => { onDisablePrashna(); setOpen(false); }} style={{ padding: 14, alignItems: 'center' }}><Text style={{ color: colors.primary, fontWeight: '600' }}>{t('premiumUi.chat.prashna.disable', 'Turn off Prashna')}</Text></TouchableOpacity>}
          </ScrollView> : <View style={{ flex: 1, paddingTop: 8 }}>
      {tool === 'prashna' ? <PrashnaSetup onSelect={place => { onPrashna(place); setOpen(false); }} /> : tool === 'conflict' ? <ConflictResolution onResolved={onResolved} messages={messages} /> : <>
      <Text style={{ color: colors.textSecondary, marginVertical: 12 }}>{t('premiumUi.chat.summarySelect', 'Select 1–3 answers. Their original questions will be included.')}</Text>
      <FlatList ListEmptyComponent={<View style={{ alignItems: 'center', padding: 24, borderRadius: 16, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.cardBorder }}><Ionicons name="chatbubbles-outline" size={28} color={colors.textSecondary} /><Text style={{ color: colors.textSecondary, textAlign: 'center', lineHeight: 22, marginTop: 10 }}>{tr('emptyAnswers', 'Your completed answers will appear here to summarize.')}</Text></View>} style={{ flexGrow: 0, maxHeight: summary ? '30%' : '60%' }} data={answers} keyExtractor={item => String(item.messageId || item.message_id)} renderItem={({ item }) => { const id = Number(item.messageId || item.message_id); const index = messages.indexOf(item); const question = [...messages.slice(0, index)].reverse().find(message => (message.role || message.sender) === 'user'); return <TouchableOpacity accessibilityRole="checkbox" accessibilityState={{ checked: ids.includes(id), disabled: busy || (!ids.includes(id) && ids.length === 3) }} disabled={busy || (!ids.includes(id) && ids.length === 3)} onPress={() => { setSummary(''); setError(''); setIds(previous => previous.includes(id) ? previous.filter(value => value !== id) : [...previous, id]); }} style={{ padding: 12, marginBottom: 8, borderRadius: 12, borderWidth: 1, borderColor: ids.includes(id) ? colors.primary : colors.cardBorder, backgroundColor: colors.surface }}><Text style={{ color: colors.text }}>{ids.includes(id) ? '☑ ' : '☐ '}{question?.content || String(item.content).replace(/<[^>]*>/g, '').slice(0, 150)}</Text></TouchableOpacity>; }} />
      <TouchableOpacity disabled={!ids.length || busy} onPress={generate} style={{ padding: 12, marginVertical: 10, borderRadius: 12, backgroundColor: colors.primary, opacity: !ids.length || busy ? 0.5 : 1 }}><Text style={{ color: colors.onPrimary, textAlign: 'center' }}>{t('premiumUi.chat.summarizeSelected', 'Summarize selected ({{count}})', { count: ids.length })}</Text></TouchableOpacity>
      {busy && <ActivityIndicator color={colors.primary} />}{error ? <Text accessibilityLiveRegion="polite" style={{ color: colors.error }}>{error}</Text> : null}
      {summary ? <ScrollView><Text style={{ color: colors.text, fontWeight: '600', marginVertical: 10 }}>{t('premiumUi.chat.summaryCount', 'Summary of {{count}} selected answers', { count: ids.length })}</Text>{summary.split('\n').map((line, index) => <Text selectable key={index} style={{ color: colors.text, lineHeight: 23, marginVertical: 4, fontWeight: /^#{1,6} /.test(line) ? '600' : '400' }}>{line.replace(/^#{1,6} /, '').split(/(\*\*[^*]+\*\*)/g).map((part, i) => part.startsWith('**') ? <Text key={i} style={{ fontWeight: '700' }}>{part.slice(2, -2)}</Text> : part)}</Text>)}<TouchableOpacity onPress={async () => { try { await Clipboard.setStringAsync(summary); } catch (_) { setError(t('premiumUi.chat.summaryCopyError', 'Could not copy the summary.')); } }} style={{ paddingVertical: 12 }}><Text style={{ color: colors.primary }}>{t('premiumUi.chat.copySummary', 'Copy summary')}</Text></TouchableOpacity></ScrollView> : null}
      </>}
          </View>}
        </View>
      </KeyboardAvoidingView>
    </Modal>
  </>;
}
