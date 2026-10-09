import React, { useEffect, useRef, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { storage } from '../../services/storage';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import useConflictResolution from '../../hooks/useConflictResolution';

const plain = text => String(text || '').replace(/<[^>]*>/g, '');
export default function ConflictResolution({ messages = [], onResolved }) {
  const { colors } = useTheme(); const { t, i18n } = useTranslation();
  const flow = useConflictResolution({ apiBase: `${API_BASE_URL}${getEndpoint('')}`, getToken: () => storage.getAuthToken() });
  const [selected, setSelected] = useState([]), [concern, setConcern] = useState(''), [reply, setReply] = useState(''), [history, setHistory] = useState(false), [query, setQuery] = useState(''), [page, setPage] = useState(1), [answers, setAnswers] = useState([]), [hasMore, setHasMore] = useState(false), [loading, setLoading] = useState(false), [searchError, setSearchError] = useState(''), [recent, setRecent] = useState([]), [expanded, setExpanded] = useState({});
  const tr = (key, fallback, values) => t(`premiumUi.chat.conflict.${key}`, fallback, values);
  const textStyle = { color: colors.text, lineHeight: 23, marginVertical: 5 };
  const inputStyle = { color: colors.text, backgroundColor: colors.surface, padding: 12, borderWidth: 1, borderColor: colors.cardBorder, borderRadius: 10, marginVertical: 8, minHeight: 48 };
  const boldText = text => <Text selectable style={textStyle}>{String(text || '').split(/(\*\*[^*]+\*\*)/g).map((part, index) => part.startsWith('**') ? <Text key={index} style={{ fontWeight: '700' }}>{part.slice(2, -2)}</Text> : part)}</Text>;
  const button = (label, onPress, disabled = false, primary = false) => <TouchableOpacity accessibilityRole="button" disabled={disabled} onPress={onPress} style={{ padding: 12, marginVertical: 5, borderRadius: 10, borderWidth: 1, borderColor: colors.cardBorder, backgroundColor: primary ? colors.primary : colors.surface, opacity: disabled ? 0.5 : 1 }}><Text style={{ color: primary ? colors.onPrimary : colors.text, textAlign: 'center' }}>{label}</Text></TouchableOpacity>;
  useEffect(() => { let active = true; flow.request('/recent').then(data => { if (active) setRecent(data.comparisons); }).catch(() => {}); return () => { active = false; }; }, [flow.request]);
  useEffect(() => { if (!history) return undefined; let active = true; setLoading(true); setSearchError(''); const timer = setTimeout(() => { flow.request(`/answers?q=${encodeURIComponent(query)}&page=${page}`).then(data => { if (active) { setAnswers(data.answers); setHasMore(data.has_more); } }).catch(err => { if (active) setSearchError(err.message); }).finally(() => { if (active) setLoading(false); }); }, 250); return () => { active = false; clearTimeout(timer); }; }, [history, query, page, flow.request]);
  const current = messages.filter(m => (m.role || m.sender) === 'assistant' && (m.messageId || m.message_id) && m.content && !m.isProcessing && !m.isTyping && !m.instantStreaming && (!m.status || m.status === 'completed') && (!m.message_type || m.message_type === 'answer')).map(m => { const index = messages.indexOf(m); return { answer_id: Number(m.messageId || m.message_id), answer: plain(m.content), question: plain([...messages.slice(0, index)].reverse().find(q => (q.role || q.sender) === 'user')?.content), answered_at: m.timestamp }; });
  const filteredCurrent = current.filter(source => !query.trim() || `${source.question} ${source.answer}`.toLowerCase().includes(query.trim().toLowerCase()));
  const visibleAnswers = history ? answers : filteredCurrent.slice((page - 1) * 30, page * 30);
  const more = history ? hasMore : page * 30 < filteredCurrent.length;
  const toggle = source => setSelected(previous => previous.some(s => s.answer_id === source.answer_id) ? previous.filter(s => s.answer_id !== source.answer_id) : previous.length < 2 ? [...previous, source] : previous);
  const notified = useRef(null);
  useEffect(() => {
    if (flow.state?.phase === 'completed' && notified.current !== flow.state.id) {
      notified.current = flow.state.id;
      onResolved?.(flow.state);
    }
  }, [flow.state, onResolved]);
  const result = flow.state?.resolution;
  return <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 20 }}>
    {!flow.state && <><Text style={textStyle}>{tr('select', 'Select exactly two answers. You can compare different chat modes or conversations.')}</Text>
      {button(tr('thisConversation', 'This conversation'), () => { setHistory(false); setPage(1); }, flow.busy, !history)}{button(tr('allConversations', 'All conversations'), () => { setHistory(true); setPage(1); }, flow.busy, history)}
      {<TextInput accessibilityLabel={tr('search', 'Search past answers')} placeholder={tr('searchPlaceholder', 'Search questions or answers across conversations')} placeholderTextColor={colors.textSecondary} value={query} onChangeText={value => { setQuery(value); setPage(1); }} style={inputStyle} />}
      {selected.map((source, index) => <View key={source.answer_id}><Text style={textStyle}>{tr('answerNumber', 'Answer {{number}}', { number: index + 1 })}: {source.question}</Text>{button(tr('remove', 'Remove selection'), () => toggle(source), flow.busy)}</View>)}
      {loading && <ActivityIndicator color={colors.primary} />}{searchError ? <Text style={{ color: colors.error }}>{searchError}</Text> : null}
      {visibleAnswers.map(source => { const checked = selected.some(s => s.answer_id === source.answer_id); return <View key={source.answer_id} style={{ padding: 12, marginVertical: 5, borderWidth: 1, borderColor: checked ? colors.primary : colors.cardBorder, borderRadius: 12, backgroundColor: colors.surface }}><TouchableOpacity accessibilityRole="checkbox" accessibilityState={{ checked, disabled: flow.busy || (!checked && selected.length === 2) }} disabled={flow.busy || (!checked && selected.length === 2)} onPress={() => toggle(source)}><Text style={{ ...textStyle, fontWeight: '600' }}>{checked ? '☑ ' : '☐ '}{source.question || tr('answerNumber', 'Answer {{number}}', { number: '' })}</Text><Text style={{ color: colors.textSecondary }}>{plain(source.answer).slice(0, 220)}</Text></TouchableOpacity>
        {source.answered_at && <Text style={{ color: colors.textSecondary, marginTop: 5 }}>{new Date(source.answered_at).toLocaleString()}</Text>}
        {button(expanded[source.answer_id] ? tr('hide', 'Hide answer') : tr('read', 'Read answer'), async () => { if (expanded[source.answer_id]) { setExpanded(previous => ({ ...previous, [source.answer_id]: null })); return; } try { const data = await flow.request(`/answers/${source.answer_id}`); setExpanded(previous => ({ ...previous, [source.answer_id]: data.answer })); } catch (err) { setSearchError(err.message); } })}
        {expanded[source.answer_id] ? boldText(expanded[source.answer_id]) : null}</View>; })}
      {!loading && !visibleAnswers.length && <Text style={textStyle}>{tr('empty', 'No answers found.')}</Text>}
      {<>{button(t('common.previous', 'Previous'), () => setPage(page - 1), page === 1 || loading)}{button(t('common.next', 'Next'), () => setPage(page + 1), !more || loading)}</>}
      <Text style={textStyle}>{tr('concern', 'What seems contradictory? (optional)')}</Text><TextInput multiline maxLength={2000} editable={!flow.busy} accessibilityLabel={tr('concern', 'What seems contradictory? (optional)')} placeholder={tr('concernPlaceholder', 'For example: one answer recommends a field, while the other advises against it.')} placeholderTextColor={colors.textSecondary} value={concern} onChangeText={setConcern} style={{ ...inputStyle, minHeight: 90 }} />
      {button(tr('resolveSelected', 'Resolve selected answers ({{count}}/2)', { count: selected.length }), () => flow.start(selected.map(s => s.answer_id), concern, i18n.resolvedLanguage || i18n.language || 'english'), selected.length !== 2 || flow.busy, true)}
      {recent.length > 0 && <><Text style={{ ...textStyle, fontWeight: '600' }}>{tr('recent', 'Recent comparisons')}</Text>{recent.map(run => <View key={run.id}>{button(run.sources.map(s => s.question || `#${s.answer_id}`).join(' / ') + ' · ' + (run.phase === 'completed' ? tr('readResolution', 'Read resolution') : tr('resume', 'Resume')), () => flow.resume(run.id), flow.busy)}</View>)}</>}
    </>}
    {flow.state && <><Text style={{ ...textStyle, fontWeight: '600' }}>{tr('rounds', 'Information rounds {{count}}/{{limit}}', { count: flow.state.rounds, limit: flow.state.max_rounds || 8 })}</Text>{flow.state.sources.map((source, index) => <Text key={source.answer_id} style={textStyle}>{tr('answerNumber', 'Answer {{number}}', { number: index + 1 })}: {source.question}</Text>)}
      {flow.state.events.filter(event => event.kind === 'question' || event.kind === 'user_reply').map((event, index) => <Text key={index} style={textStyle}>{event.kind === 'question' ? tr('clarification', 'Clarification') : tr('yourReply', 'Your reply')}: {event.text}</Text>)}
      {flow.state.phase === 'waiting' && <><Text style={{ ...textStyle, fontWeight: '600' }}>{flow.state.question}</Text><TextInput multiline maxLength={3000} editable={!flow.busy} accessibilityLabel={tr('yourReply', 'Your reply')} placeholder={tr('replyPlaceholder', 'Provide the detail requested above')} placeholderTextColor={colors.textSecondary} value={reply} onChangeText={setReply} style={{ ...inputStyle, minHeight: 90 }} />{button(tr('send', 'Send clarification'), () => { flow.send('reply', reply); setReply(''); }, !reply.trim() || flow.busy, true)}{button(tr('finish', 'Resolve with available information'), () => flow.send('finish'), flow.busy)}</>}
    </>}
    {flow.busy && <><ActivityIndicator color={colors.primary} /><Text style={textStyle}>{flow.progress || tr('checking', 'Checking the comparison…')}</Text></>}
    {flow.error && <><Text accessibilityLiveRegion="polite" style={{ color: colors.error }}>{flow.error}</Text>{flow.state && button(tr('reconnect', 'Reconnect'), () => flow.resume(flow.state.id), flow.busy)}</>}
    {result && <><Text style={{ ...textStyle, fontSize: 18, fontWeight: '700' }}>{tr('corrected', 'Your answer')}</Text>{boldText(result.corrected_answer)}
      <Text style={{ ...textStyle, fontWeight: '700' }}>{tr('whatConflicted', 'Why the guidance differed')}</Text>{boldText(result.explanation)}
      {result.evidence.length > 0 && <><Text style={{ ...textStyle, fontWeight: '700' }}>{tr('evidence', 'Why this is most likely')}</Text>{result.evidence.map((item, index) => <View key={index}>{boldText(item.finding)}</View>)}</>}
      {result.uncertainty.length > 0 && <><Text style={{ ...textStyle, fontWeight: '700' }}>{tr('uncertainty', 'Keep in mind')}</Text>{boldText(result.uncertainty[0])}</>}
      <Text style={{ color: colors.textSecondary, marginVertical: 12 }}>{tr('saved', 'Saved in your chat history.')}</Text>
    </>}
    {flow.state && !flow.busy && button(tr('another', 'Compare another pair'), () => { flow.reset(); setSelected([]); setConcern(''); setReply(''); })}
  </ScrollView>;
}
