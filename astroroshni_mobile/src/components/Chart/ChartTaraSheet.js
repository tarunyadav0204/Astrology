import React, { useEffect, useRef, useState } from 'react';
import { Animated, BackHandler, Keyboard, PanResponder, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View, useWindowDimensions } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useIsFocused } from '@react-navigation/native';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { useCredits } from '../../credits/CreditContext';
import { useAuthGate } from '../../auth/AuthGateContext';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import { buildQueryContext } from '../../utils/queryContext';
import { chartTaraRequest } from '../../utils/chartTaraConversation';
import { askOverConversation, takeConversationStream, closeConversationSession } from '../../utils/instantConversation';
import MessageBubble from '../Chat/MessageBubble';

const apiUrl = path => `${API_BASE_URL}${getEndpoint(path)}`;
const socketUrl = path => apiUrl(path).replace(/^http:/i, 'ws:').replace(/^https:/i, 'wss:');
const errorText = data => typeof data?.detail === 'string' ? data.detail : data?.detail?.message || data?.error_message || data?.error || 'Could not complete this question. Please try again.';

// Mounted at the chart screen root, outside its scroll view. No modal/backdrop:
// gestures on the uncovered chart continue to work.
export default function ChartTaraSheet({ birthData, chartType, openSignal }) {
  const { colors } = useTheme();
  const { i18n } = useTranslation();
  const { pricing, pricingFeatures, isAstrologerLicensed, fetchPricing, fetchBalance } = useCredits();
  const { requireAuthForPaid } = useAuthGate();
  const focused = useIsFocused();
  const insets = useSafeAreaInsets();
  const { height: windowHeight } = useWindowDimensions();
  const [level, setLevel] = useState(0);
  const [keyboardTop, setKeyboardTop] = useState(null);
  const keyboardHeight = keyboardTop == null ? 0 : Math.max(0, windowHeight - keyboardTop);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [activity, setActivity] = useState('');
  const session = useRef(null);
  const turn = useRef(null);
  const sendLock = useRef(false);
  const active = useRef(true);
  const listener = useRef(null);
  const timer = useRef(null);
  const generation = useRef(0);
  const scroll = useRef(null);
  const stickToBottom = useRef(true);
  const sheetHeight = useRef(new Animated.Value(72)).current;
  const heightRef = useRef(72);
  const dragStart = useRef(72);
  const maxHeight = Math.max(180, windowHeight - keyboardHeight - 100);
  const halfHeight = Math.min(maxHeight, windowHeight * 0.52);
  const target = level === 1 ? 72 : level === 2 ? halfHeight : maxHeight;
  const geometry = useRef({ maxHeight, halfHeight, setLevel });
  geometry.current = { maxHeight, halfHeight, setLevel };

  const stopObserving = () => {
    clearTimeout(timer.current);
    const previous = listener.current;
    listener.current = null;
    previous?.close();
  };
  useEffect(() => {
    const id = sheetHeight.addListener(({ value }) => { heightRef.current = value; });
    return () => sheetHeight.removeListener(id);
  }, [sheetHeight]);
  useEffect(() => {
    if (level) Animated.timing(sheetHeight, { toValue: target, duration: 180, useNativeDriver: false }).start();
  }, [target, level, sheetHeight]);
  useEffect(() => {
    if (openSignal) { setLevel(2); fetchPricing({ force: true }); }
  }, [openSignal, fetchPricing]);
  useEffect(() => {
    const show = Keyboard.addListener('keyboardDidShow', event => { setKeyboardTop(event.endCoordinates.screenY); setLevel(3); });
    const hide = Keyboard.addListener('keyboardDidHide', () => setKeyboardTop(null));
    return () => { show.remove(); hide.remove(); };
  }, []);
  useEffect(() => {
    const back = BackHandler.addEventListener('hardwareBackPress', () => {
      if (!focused || level < 2) return false;
      Keyboard.dismiss(); setLevel(1); return true;
    });
    return () => back.remove();
  }, [focused, level]);
  useEffect(() => {
    active.current = true;
    return () => { active.current = false; generation.current += 1; stopObserving(); closeConversationSession(session.current); };
  }, []);

  useEffect(() => {
    if (!focused) {
      generation.current += 1;
      stopObserving();
      setBusy(false);
      if (turn.current) setError('Your question is saved. Tap retry to resume its response.');
      setKeyboardTop(null);
    }
  }, [focused]);

  const pan = useRef(PanResponder.create({
    onMoveShouldSetPanResponder: (_, g) => Math.abs(g.dy) > 6,
    onPanResponderGrant: () => { sheetHeight.stopAnimation(); dragStart.current = heightRef.current; },
    onPanResponderMove: (_, g) => sheetHeight.setValue(Math.max(72, Math.min(geometry.current.maxHeight, dragStart.current - g.dy))),
    onPanResponderRelease: (_, g) => {
      const { maxHeight: max, halfHeight: half, setLevel: snap } = geometry.current;
      const proposed = dragStart.current - g.dy - g.vy * 100;
      const points = [72, half, max];
      const index = points.reduce((best, value, i) => Math.abs(value - proposed) < Math.abs(points[best] - proposed) ? i : best, 0);
      if (!index) Keyboard.dismiss();
      snap(index + 1);
      Animated.timing(sheetHeight, { toValue: points[index], duration: 180, useNativeDriver: false }).start();
    },
  })).current;

  const updateAnswer = (id, content, extra = {}) => setMessages(items => items.map(item => item.id === id ? { ...item, ...(content != null ? { content, instantStreaming: true } : {}), ...extra } : item));
  const request = async (path, token, body) => {
    const response = await fetch(apiUrl(path), { method: body ? 'POST' : 'GET', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, ...(body ? { body: JSON.stringify(body) } : {}) });
    const data = await response.json();
    if (!response.ok) throw new Error(errorText(data));
    return data;
  };

  const observe = (messageId, answerId, token, epoch) => {
    const valid = () => active.current && generation.current === epoch;
    const finish = data => {
      if (!valid()) return;
      stopObserving();
      updateAnswer(answerId, data.response || data.content || '', { isTyping: false, instantStreaming: false, terms: data.terms || [], glossary: data.glossary || {} });
      setBusy(false); setActivity(''); turn.current = null; fetchBalance();
    };
    const poll = async () => {
      if (!valid()) return;
      try {
        const data = await request(`/chat-v2/status/${messageId}`, token);
        if (!valid()) return;
        if (data.status === 'completed') { finish(data); return; }
        if (data.status === 'failed' || data.status === 'error') throw new Error(errorText(data));
        if (data.partial_content || data.content) updateAnswer(answerId, data.partial_content || data.content);
        if (data.engagement_updates?.length) setActivity(data.engagement_updates.slice(-1).map(item => item.detail || item.title).join(''));
        timer.current = setTimeout(poll, 1500);
      } catch (err) {
        if (valid()) { stopObserving(); setBusy(false); setError(err.message); updateAnswer(answerId, null, { isTyping: false }); }
      }
    };
    let socket;
    try { socket = takeConversationStream(messageId) || new WebSocket(`${socketUrl(`/chat-v2/stream/${messageId}`)}?token=${encodeURIComponent(token)}`); }
    catch (_) { poll(); return; }
    listener.current = socket;
    const recover = () => { if (listener.current === socket) { socket.onclose = null; stopObserving(); poll(); } };
    socket.onmessage = event => {
      if (!valid()) return;
      let data;
      try { data = JSON.parse(event.data); } catch (_) { return; }
      if (data.type === 'content_delta') updateAnswer(answerId, data.content);
      if (data.type === 'progress') setActivity((data.engagement_updates || []).map(item => item.detail || item.message || item.title).filter(Boolean).slice(-1).join(''));
      if (data.type === 'completed') finish(data.payload || {});
      if (data.type === 'error') recover();
    };
    socket.onclose = recover;
    socket.onerror = recover;
    // Status is authoritative even if a mobile socket silently stops delivering.
    timer.current = setTimeout(() => { stopObserving(); poll(); }, 45000);
  };

  const send = async () => {
    if (busy || sendLock.current || (!input.trim() && !turn.current)) return;
    sendLock.current = true;
    const epoch = generation.current;
    try {
      if (!await requireAuthForPaid({ feature: 'chart_chat' })) return;
      if (!active.current || epoch !== generation.current) return;
      setBusy(true); setError(''); setActivity('Reading your question…');
      if (!birthData?.id && !birthData?.birth_chart_id) throw new Error('Save this birth profile to your account before starting a chat.');
      if (!pricingFeatures?.instant_chat_enabled) throw new Error('Live chat is not available for this account.');
      const token = await AsyncStorage.getItem('authToken');
      if (!session.current) {
        const created = await request('/chat-v2/session', token, { birth_chart_id: birthData.id ?? birthData.birth_chart_id, query_context: buildQueryContext() });
        if (!active.current || epoch !== generation.current) return;
        session.current = created.session_id;
      }
      if (!turn.current) {
        const question = input.trim();
        const id = `chart-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        turn.current = { id, answerId: `${id}-answer`, question, chartType };
        setMessages(items => [...items, { id, role: 'user', content: question }, { id: `${id}-answer`, role: 'assistant', content: '', isTyping: true, timestamp: new Date().toISOString() }]);
        setInput('');
        stickToBottom.current = true;
      }
      const pending = turn.current;
      if (pending.messageId) { observe(pending.messageId, pending.answerId, token, epoch); return; }
      const body = chartTaraRequest({ sessionId: session.current, pending, birthData, language: i18n.language, queryContext: buildQueryContext() });
      const response = await askOverConversation(socketUrl('/chat-v2/conversation'), token, body, () => fetch(apiUrl('/chat-v2/ask'), { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify(body) }));
      const data = await response.json();
      if (!active.current || epoch !== generation.current) return;
      if (!response.ok) throw new Error(errorText(data));
      if (!data.message_id) throw new Error('The question could not be queued. Please retry.');
      pending.messageId = data.message_id;
      observe(data.message_id, pending.answerId, token, epoch);
    } catch (err) {
      if (active.current && epoch === generation.current) { setError(err.message); setBusy(false); setActivity(''); }
    } finally { sendLock.current = false; }
  };

  if (!focused || !level) return null;
  return <Animated.View style={[styles.sheet, { height: sheetHeight, bottom: keyboardHeight, backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
    <View {...pan.panHandlers} style={styles.dragArea}>
      <View style={[styles.handle, { backgroundColor: colors.borderStrong }]} />
      <View style={styles.header}>
        <TouchableOpacity onPress={() => setLevel(level === 1 ? 2 : 1)} style={styles.title} accessibilityLabel={level === 1 ? 'Expand Ask Tara' : 'Collapse Ask Tara'}>
          <Text style={{ color: colors.text, fontWeight: '700', fontSize: 17 }}>✧ Ask Tara</Text>
          <Text numberOfLines={1} style={{ color: colors.textSecondary, fontSize: 12 }}>{birthData?.name} · {chartType}</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => { Keyboard.dismiss(); setLevel(level === 1 ? 2 : 1); }} style={styles.icon} accessibilityLabel="Resize chat"><Ionicons name={level === 1 ? 'chevron-up' : 'chevron-down'} size={22} color={colors.text} /></TouchableOpacity>
      </View>
    </View>
    {level > 1 && <>
      <ScrollView ref={scroll} style={{ flex: 1 }} contentContainerStyle={{ padding: 12 }} keyboardShouldPersistTaps="handled" scrollEventThrottle={32} onScroll={({ nativeEvent: event }) => { stickToBottom.current = event.contentSize.height - event.layoutMeasurement.height - event.contentOffset.y < 80; }} onContentSizeChange={() => { if (stickToBottom.current) scroll.current?.scrollToEnd({ animated: false }); }}>
        {!messages.length && <Text style={{ color: colors.textSecondary, lineHeight: 22 }}>Ask about this chart. Drag this sheet down whenever you want to inspect the chart.</Text>}
        {messages.map(message => message.role === 'user' ? <Text key={message.id} style={[styles.question, { backgroundColor: colors.surfaceMuted, color: colors.text }]}>{message.content}</Text> : message.content ? <MessageBubble key={message.id} message={{ ...message, isTyping: false }} sessionId={session.current} forceInstantPresentation onFollowUpClick={question => setInput(question)} /> : null)}
        {busy && <Text accessibilityLiveRegion="polite" style={{ color: colors.textSecondary, marginVertical: 12 }}>{activity || 'Preparing your answer…'}</Text>}
        {!!error && <View><Text style={{ color: colors.text }}>{error}</Text>{turn.current && !busy && <TouchableOpacity onPress={send} style={styles.icon}><Text style={{ color: colors.primary }}>Retry question</Text></TouchableOpacity>}</View>}
      </ScrollView>
      <View style={[styles.composer, { borderColor: colors.cardBorder, paddingBottom: keyboardTop == null ? Math.max(12, insets.bottom) : 12 }]}>
        <Text style={{ color: colors.textSecondary, fontSize: 11 }}>{pricing?.chart_chat === 0 ? (isAstrologerLicensed ? 'Free · Astrologer License' : 'Free') : pricing?.chart_chat != null ? `${pricing.chart_chat} credits / question` : '2 credits / question'} · Answers saved to chat history</Text>
        <View style={styles.inputRow}>
          <TextInput accessibilityLabel="Question for Tara" placeholder="Ask about this chart…" placeholderTextColor={colors.textTertiary} value={input} onChangeText={setInput} onFocus={() => setLevel(3)} multiline editable={!busy && !turn.current} style={[styles.input, { color: colors.text, backgroundColor: colors.surfaceMuted }]} />
          <TouchableOpacity accessibilityLabel="Send question" disabled={busy || !input.trim() || !!turn.current} onPress={send} style={[styles.send, { backgroundColor: colors.primary, opacity: busy || !input.trim() || turn.current ? 0.45 : 1 }]}><Ionicons name="arrow-up" size={22} color={colors.onPrimary} /></TouchableOpacity>
        </View>
      </View>
    </>}
  </Animated.View>;
}
const styles = StyleSheet.create({
  sheet: { position: 'absolute', left: 0, right: 0, zIndex: 100, elevation: 12, borderWidth: 1, borderTopLeftRadius: 24, borderTopRightRadius: 24, overflow: 'hidden' },
  dragArea: { paddingHorizontal: 16, paddingTop: 7 }, handle: { width: 36, height: 4, borderRadius: 2, alignSelf: 'center' },
  header: { flexDirection: 'row', alignItems: 'center', paddingVertical: 7 }, title: { flex: 1 }, icon: { padding: 10 },
  composer: { padding: 12, borderTopWidth: 1 }, inputRow: { flexDirection: 'row', alignItems: 'flex-end', gap: 8, marginTop: 7 },
  input: { flex: 1, minHeight: 42, maxHeight: 120, padding: 10, borderRadius: 14, textAlignVertical: 'top', fontSize: 15 },
  send: { width: 42, height: 42, borderRadius: 21, alignItems: 'center', justifyContent: 'center' },
  question: { padding: 12, borderRadius: 14, marginBottom: 12, alignSelf: 'flex-end', maxWidth: '90%', lineHeight: 22 },
});
