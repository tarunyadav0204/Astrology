import React, { useEffect, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, ActivityIndicator } from 'react-native';
import AppAlertModal from '../Common/AppAlertModal';
import Ionicons from '@expo/vector-icons/Ionicons';
import { openSavedConversation } from '../../utils/savedConversation.cjs';
import { storage } from '../../services/storage';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';

async function request(path = '', method = 'GET', signal) {
  const token = await storage.getAuthToken();
  const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat/bookmarks')}${path}`, { method, signal, headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) throw new Error('Unable to access saved answers. Please try again.');
  return response.json();
}
export function SaveAnswerButton({ message, style }) {
  const { colors } = useTheme();
  const id = Number(message.messageId || message.message_id);
  const eligible = Number.isInteger(id) && id > 0 && (message.role || message.sender) === 'assistant' && !message.isTyping && !message.isProcessing && !message.instantStreaming && !message.isWelcome && (!message.message_type || message.message_type === 'answer') && Boolean(message.content);
  const [saved, setSaved] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('');
  useEffect(() => { if (!eligible) return; const controller = new AbortController(); request(`/${id}`, 'GET', controller.signal).then(data => setSaved(data.saved)).catch(() => {}); return () => controller.abort(); }, [id, eligible]);
  if (!eligible) return null;
  return <><TouchableOpacity accessibilityRole="button" accessibilityLabel={saved ? 'Remove saved answer' : 'Save answer'} accessibilityState={{ selected: saved, disabled: busy }} disabled={busy} style={[{ width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center', borderWidth: 1, backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }, style, saved && { backgroundColor: colors.surfaceMuted, borderColor: colors.primary }]} onPress={async () => { setBusy(true); try { const data = await request(`/${id}`, saved ? 'DELETE' : 'PUT'); setSaved(data.saved); } catch (err) { setError(err.message); } finally { setBusy(false); } }}><Ionicons name={saved ? 'bookmark' : 'bookmark-outline'} size={16} color={colors.primary} /></TouchableOpacity><AppAlertModal visible={Boolean(error)} title="Saved answers" message={error} variant="error" onPrimaryPress={() => setError('')} onRequestClose={() => setError('')} /></>;
}
const plain = text => String(text || '').replace(/<[^>]*>/g, '').replace(/(?:【|\[)(?:POS|NEG)_(?:START|END)(?:】|\])/gi, '').replace(/\*\*/g, '').replace(/^#{1,6}\s*/gm, '');
export default function SavedAnswers({ navigation }) {
  const { colors } = useTheme();
  const [query, setQuery] = useState(''), [rows, setRows] = useState([]), [page, setPage] = useState(1), [more, setMore] = useState(false), [loading, setLoading] = useState(false), [error, setError] = useState(''), [revision, setRevision] = useState(0), [expanded, setExpanded] = useState(null);
  useEffect(() => { const controller = new AbortController(); setLoading(true); setError(''); const timer = setTimeout(() => { request(`?q=${encodeURIComponent(query)}&page=${page}`, 'GET', controller.signal).then(data => { setRows(prev => page === 1 ? data.answers : [...prev, ...data.answers]); setMore(data.has_more); }).catch(err => { if (err.name !== 'AbortError') setError(err.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); }); }, 200); return () => { clearTimeout(timer); controller.abort(); }; }, [query, page, revision]);
  return <View style={{ flex: 1, paddingHorizontal: 18 }}><TextInput accessibilityLabel="Search saved answers" value={query} onChangeText={value => { setQuery(value); setPage(1); }} placeholder="Search a question, answer or person" placeholderTextColor={colors.textSecondary} style={{ padding: 12, marginVertical: 12, color: colors.text, backgroundColor: colors.surfaceRaised, borderRadius: 12 }} />
    {loading && <ActivityIndicator color={colors.primary} />}{error ? <TouchableOpacity onPress={() => setRevision(value => value + 1)}><Text style={{ color: colors.text }}>{error} Tap to retry.</Text></TouchableOpacity> : null}
    <FlatList data={rows} keyExtractor={item => String(item.message_id)} ListEmptyComponent={!loading && !error ? <Text style={{ color: colors.textSecondary }}>{query ? 'No saved answers match your search.' : 'Tap the bookmark icon beneath an answer to save it here.'}</Text> : null} renderItem={({ item }) => <View style={{ padding: 14, marginBottom: 12, borderRadius: 14, backgroundColor: colors.cardBackground, borderWidth: 1, borderColor: colors.cardBorder }}><Text style={{ color: colors.textSecondary }}>{item.name} · {new Date(item.saved_at).toLocaleDateString()}</Text><Text style={{ color: colors.text, fontWeight: '600', marginVertical: 10 }}>{plain(item.question) || 'Saved answer'}</Text><TouchableOpacity onPress={() => setExpanded(expanded === item.message_id ? null : item.message_id)}><Text style={{ color: colors.primary }}>{expanded === item.message_id ? 'Hide answer' : 'Read answer'}</Text></TouchableOpacity>{expanded === item.message_id && <Text style={{ color: colors.text, marginVertical: 10, lineHeight: 23 }}>{plain(item.content)}</Text>}<View style={{ flexDirection: 'row', gap: 16, marginTop: 12 }}><TouchableOpacity onPress={async () => { try { await openSavedConversation(item, { navigate: navigation.navigate, fetchSession: async id => { const token = await storage.getAuthToken(); const response = await fetch(`${API_BASE_URL}${getEndpoint(`/chat-v2/session/${encodeURIComponent(id)}`)}`, { headers: { Authorization: `Bearer ${token}` } }); if (!response.ok) throw new Error(`Unable to open conversation (${response.status}). Please try again.`); return response.json(); } }); } catch (err) { setError(err.message); } }}><Text style={{ color: colors.primary }}>Open conversation</Text></TouchableOpacity><TouchableOpacity onPress={async () => { try { await request(`/${item.message_id}`, 'DELETE'); setPage(1); setRevision(value => value + 1); } catch (err) { setError(err.message); } }}><Text style={{ color: colors.primary }}>Remove bookmark</Text></TouchableOpacity></View></View>} ListFooterComponent={more ? <TouchableOpacity disabled={loading} onPress={() => setPage(value => value + 1)}><Text style={{ color: colors.primary, padding: 14 }}>Load more</Text></TouchableOpacity> : null} />
  </View>;
}
