import React, { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  ScrollView,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { chatAPI } from '../../services/api';
import { storage } from '../../services/storage';
import { buildQueryContext } from '../../utils/queryContext';
import { getTextToSpeech } from '../../utils/textToSpeechLazy';
import { useTheme } from '../../context/ThemeContext';
import { speechRecognition } from '../../native/speechRecognition';

const POLL_INTERVAL_MS = 1400;
const MAX_POLLS = 90;

const normalizeLanguageCode = (language) => {
  const raw = String(language || 'english').toLowerCase();
  return raw.startsWith('hi') ? 'hindi' : language || 'english';
};

const toChatBirthDetails = (birthData) => ({
  name: birthData?.name,
  date: typeof birthData?.date === 'string' ? birthData.date.split('T')[0] : birthData?.date,
  time: typeof birthData?.time === 'string'
    ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time
    : birthData?.time,
  latitude: parseFloat(birthData?.latitude),
  longitude: parseFloat(birthData?.longitude),
  place: birthData?.place || '',
  gender: birthData?.gender || '',
});

const logSpeechDebug = async (label, payload = {}) => {
  if (!__DEV__) return;
  try {
    console.log(`[SpeechChat] ${label}`, payload);
  } catch {
    // ignore debug logging failures
  }
};

export default function SpeechChatScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const [birthData, setBirthData] = useState(route.params?.birthData || null);
  const [sessionId, setSessionId] = useState(null);
  const [language, setLanguage] = useState(route.params?.language || 'english');
  const [status, setStatus] = useState('idle');
  const [turns, setTurns] = useState([]);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [followUps, setFollowUps] = useState([]);
  const [errorText, setErrorText] = useState('');
  const [handsFreeEnabled, setHandsFreeEnabled] = useState(true);
  const mountedRef = useRef(true);
  const scrollRef = useRef(null);
  const handsFreeRestartRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    const subscription = speechRecognition.addPartialListener((partial) => {
      const next = String(partial || '').trim();
      if (!next || !mountedRef.current) return;
      setCurrentTranscript(next);
    });

    const loadContext = async () => {
      const [storedBirthData, storedLanguage] = await Promise.all([
        storage.getBirthDetails(),
        storage.getLanguage(),
      ]);
      if (mountedRef.current) {
        if (!birthData && storedBirthData) setBirthData(storedBirthData);
        if (!route.params?.language && storedLanguage) setLanguage(storedLanguage);
      }
    };

    loadContext();

    return () => {
      mountedRef.current = false;
      subscription?.remove?.();
      try {
        speechRecognition.cancelListening();
      } catch {
        // ignore teardown errors
      }
      handsFreeRestartRef.current = false;
      getTextToSpeech().stop();
    };
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 80);
    return () => clearTimeout(timer);
  }, [turns, currentTranscript, status]);

  const ensureSession = async () => {
    if (sessionId) return sessionId;
    if (!birthData?.id) {
      Alert.alert(
        t('speechChat.profileRequired', 'Birth chart required'),
        t('speechChat.profileRequiredBody', 'Please select or create a birth chart before using speech chat.')
      );
      return null;
    }
    const response = await chatAPI.createV2Session(birthData.id);
    const nextSessionId = response?.data?.session_id;
    if (nextSessionId) {
      setSessionId(nextSessionId);
      return nextSessionId;
    }
    return null;
  };

  const startListening = async () => {
    if (!birthData) {
      Alert.alert(
        t('speechChat.profileRequired', 'Birth chart required'),
        t('speechChat.profileRequiredBody', 'Please select or create a birth chart before using speech chat.')
      );
      return;
    }

    setErrorText('');
    setCurrentTranscript('');
    setFollowUps([]);
    handsFreeRestartRef.current = false;
    await getTextToSpeech().stop();

    let available = false;
    try {
      available = await speechRecognition.isAvailable();
    } catch (error) {
      throw new Error(error?.message || t(
        'speechChat.nativeBuildRequired',
        'Speech input needs a development build of the app. Expo Go cannot access the native speech recognizer.'
      ));
    }

    if (!available) {
      throw new Error(t(
        'speechChat.nativeUnavailable',
        'Speech recognition is not available on this device right now.'
      ));
    }

    await logSpeechDebug('startListening.request', {
      platform: route?.params?.platform || 'native',
      language,
      normalizedLanguage: normalizeLanguageCode(language),
    });

    setStatus('listening');

    speechRecognition.startListening(normalizeLanguageCode(language))
      .then(async (transcript) => {
        const finalTranscript = String(transcript || '').trim();
        await logSpeechDebug('startListening.result', {
          transcript: finalTranscript,
        });
        if (!mountedRef.current) return;
        if (!finalTranscript) {
          throw new Error(t('speechChat.noTranscript', 'I could not understand that. Please try again.'));
        }
        setCurrentTranscript(finalTranscript);
        setStatus('thinking');
        await askInstant(finalTranscript);
      })
      .catch(async (error) => {
        await logSpeechDebug('startListening.error', {
          message: error?.message,
          code: error?.code,
        });
        if (!mountedRef.current) return;
        if (error?.code === 'cancelled') {
          setStatus('idle');
          return;
        }
        setErrorText(error?.message || t('speechChat.noTranscript', 'I could not understand that. Please try again.'));
        setStatus('idle');
      });
  };

  const stopListening = async () => {
    await logSpeechDebug('stopListening.request', {
      currentTranscript,
    });
    handsFreeRestartRef.current = false;
    setStatus('transcribing');
    speechRecognition.stopListening();
  };

  const maybeRestartHandsFree = async () => {
    if (!mountedRef.current || !handsFreeEnabled) return;
    handsFreeRestartRef.current = false;
    setStatus('idle');
    setErrorText('');
    try {
      await startListening();
    } catch (error) {
      if (!mountedRef.current) return;
      setErrorText(error?.message || t('speechChat.genericError', 'Something went wrong. Please try again.'));
      setStatus('idle');
    }
  };

  const askInstant = async (question) => {
    const activeSessionId = await ensureSession();
    if (!activeSessionId) throw new Error(t('speechChat.sessionError', 'Could not start a speech chat session.'));
    const requestBody = {
      session_id: activeSessionId,
      question,
      query_context: buildQueryContext(),
      language: language || 'english',
      response_style: 'detailed',
      premium_analysis: false,
      chat_tier: 'instant',
      native_name: birthData?.name,
      birth_details: toChatBirthDetails(birthData),
      client_request_id: `speech_${Date.now()}_${Math.random().toString(36).slice(2)}`,
    };
    const askResponse = await chatAPI.askV2(requestBody);
    const askData = askResponse?.data || {};
    if (askData.status === 'completed') {
      await handleCompletedAnswer(question, askData);
      return;
    }
    if (!askData.message_id) throw new Error(t('speechChat.askError', 'Could not send your question.'));
    await pollForAnswer(question, askData.message_id);
  };

  const pollForAnswer = async (question, messageId) => {
    for (let attempt = 0; attempt < MAX_POLLS; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
      if (!mountedRef.current) return;
      const response = await chatAPI.getMessageStatus(messageId);
      const data = response?.data || {};
      if (data.status === 'completed') {
        await handleCompletedAnswer(question, data);
        return;
      }
      if (data.status === 'failed') {
        throw new Error(data.error_message || t('speechChat.answerError', 'Answer failed. Please try again.'));
      }
    }
    throw new Error(t('speechChat.timeout', 'The answer is taking too long. Please try again.'));
  };

  const handleCompletedAnswer = async (question, data) => {
    const answer = String(data.content || '').trim();
    const nextFollowUps = Array.isArray(data.follow_up_questions)
      ? data.follow_up_questions.map((item) => String(item || '').trim()).filter(Boolean).slice(0, 3)
      : [];
    setFollowUps(nextFollowUps);
    setTurns((prev) => [...prev, { question, answer, followUps: nextFollowUps }]);
    setCurrentTranscript('');
    setStatus('speaking');
    handsFreeRestartRef.current = !!handsFreeEnabled;
    await getTextToSpeech().speak(answer, {
      language,
      onDone: () => {
        if (!mountedRef.current) return;
        if (handsFreeRestartRef.current && handsFreeEnabled) {
          maybeRestartHandsFree();
          return;
        }
        setStatus('idle');
      },
      onError: () => {
        if (!mountedRef.current) return;
        handsFreeRestartRef.current = false;
        setStatus('idle');
      },
    });
  };

  const askFollowUp = async (question) => {
    if (status !== 'idle') return;
    setCurrentTranscript(question);
    setFollowUps([]);
    setErrorText('');
    try {
      await getTextToSpeech().stop();
      setStatus('thinking');
      await askInstant(question);
    } catch (error) {
      setErrorText(error?.message || t('speechChat.answerError', 'Answer failed. Please try again.'));
      setStatus('idle');
    }
  };

  const handleMicPress = async () => {
    try {
      if (status === 'listening') {
        await stopListening();
      } else if (status === 'idle') {
        await startListening();
      } else if (status === 'speaking') {
        handsFreeRestartRef.current = false;
        await getTextToSpeech().stop();
        setStatus('idle');
      }
    } catch (error) {
      setErrorText(error?.message || t('speechChat.genericError', 'Something went wrong. Please try again.'));
      setStatus('idle');
    }
  };

  const statusText = {
    idle: handsFreeEnabled
      ? t('speechChat.statusIdleHandsFree', 'Tap the mic and AstroRoshni will keep listening after each answer')
      : t('speechChat.statusIdle', 'Tap the mic and ask your question'),
    listening: t('speechChat.statusListening', 'Listening... tap again when done'),
    transcribing: t('speechChat.statusTranscribing', 'Finishing your question...'),
    thinking: t('speechChat.statusThinking', 'Reading the chart...'),
    speaking: t('speechChat.statusSpeaking', 'Speaking the answer... tap to stop'),
  }[status] || '';

  const busy = ['transcribing', 'thinking'].includes(status);
  const isDark = theme === 'dark';

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.background }]}>
      <LinearGradient
        colors={isDark ? ['#1a0033', '#2d1b4e'] : ['#fffbf7', '#ffefe6']}
        style={styles.container}
      >
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
            <Ionicons name="chevron-back" size={26} color={colors.text} />
          </TouchableOpacity>
          <View style={styles.headerTextWrap}>
            <Text style={[styles.title, { color: colors.text }]}>Speech Chat</Text>
            <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
              {birthData?.name ? `Instant answers for ${birthData.name}` : 'Instant spoken answers'}
            </Text>
          </View>
        </View>

        <ScrollView ref={scrollRef} style={styles.conversation} contentContainerStyle={styles.conversationContent}>
          {turns.length === 0 && !currentTranscript ? (
            <View style={[styles.emptyCard, { borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}>
              <Ionicons name="mic-circle-outline" size={44} color={colors.primary} />
              <Text style={[styles.emptyTitle, { color: colors.text }]}>Ask by speaking</Text>
              <Text style={[styles.emptyBody, { color: colors.textSecondary }]}>
                Keep questions short and natural. AstroRoshni will answer aloud and suggest follow-ups.
              </Text>
            </View>
          ) : null}

          {turns.map((turn, index) => (
            <View key={`${turn.question}_${index}`} style={styles.turnBlock}>
              <View style={[styles.userBubble, { backgroundColor: isDark ? 'rgba(249,115,22,0.22)' : 'rgba(249,115,22,0.12)' }]}>
                <Text style={[styles.bubbleLabel, { color: colors.textSecondary }]}>You asked</Text>
                <Text style={[styles.bubbleText, { color: colors.text }]}>{turn.question}</Text>
              </View>
              <View style={[styles.answerBubble, { backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : '#fffaf5', borderColor: colors.cardBorder }]}>
                <Text style={[styles.bubbleLabel, { color: colors.textSecondary }]}>AstroRoshni answered</Text>
                <Text style={[styles.bubbleText, { color: colors.text }]}>{turn.answer}</Text>
              </View>
            </View>
          ))}

          {currentTranscript ? (
            <View style={[styles.liveCard, { borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}>
              <Text style={[styles.bubbleLabel, { color: colors.textSecondary }]}>
                {status === 'listening' ? t('speechChat.heardSoFar', 'Heard so far') : t('speechChat.currentQuestion', 'Current question')}
              </Text>
              <Text style={[styles.bubbleText, { color: colors.text }]}>{currentTranscript}</Text>
            </View>
          ) : null}
        </ScrollView>

        {followUps.length > 0 && status === 'idle' ? (
          <View style={styles.followUpRow}>
            {followUps.map((item) => (
              <TouchableOpacity key={item} onPress={() => askFollowUp(item)} style={[styles.followUpChip, { borderColor: colors.cardBorder }]}>
                <Text style={[styles.followUpText, { color: colors.text }]} numberOfLines={2}>{item}</Text>
              </TouchableOpacity>
            ))}
          </View>
        ) : null}

        {errorText ? <Text style={[styles.errorText, { color: colors.error }]}>{errorText}</Text> : null}

        <View style={styles.controls}>
          <TouchableOpacity
            onPress={() => setHandsFreeEnabled((prev) => !prev)}
            style={[
              styles.handsFreeToggle,
              {
                backgroundColor: handsFreeEnabled
                  ? (isDark ? 'rgba(249,115,22,0.18)' : 'rgba(249,115,22,0.10)')
                  : 'transparent',
                borderColor: colors.cardBorder,
              },
            ]}
          >
            <Ionicons
              name={handsFreeEnabled ? 'radio-outline' : 'radio-button-off-outline'}
              size={18}
              color={handsFreeEnabled ? colors.primary : colors.textSecondary}
            />
            <Text style={[styles.handsFreeText, { color: colors.text }]}>
              {t('speechChat.handsFreeLabel', 'Hands-free follow-up')}
            </Text>
            <Text style={[styles.handsFreeState, { color: handsFreeEnabled ? colors.primary : colors.textSecondary }]}>
              {handsFreeEnabled ? t('speechChat.handsFreeOn', 'On') : t('speechChat.handsFreeOff', 'Off')}
            </Text>
          </TouchableOpacity>
          <Text style={[styles.statusText, { color: colors.textSecondary }]}>{statusText}</Text>
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={handleMicPress}
            disabled={busy}
            style={[styles.micButtonOuter, busy && styles.micButtonDisabled]}
          >
            <LinearGradient
              colors={status === 'listening' ? ['#ef4444', '#f97316'] : ['#f97316', '#ec4899']}
              style={styles.micButton}
            >
              {busy ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Ionicons name={status === 'speaking' ? 'stop' : status === 'listening' ? 'stop-circle' : 'mic'} size={36} color="#fff" />
              )}
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </LinearGradient>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  container: {
    flex: 1,
    paddingHorizontal: 18,
    paddingTop: 10,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTextWrap: {
    flex: 1,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
  },
  subtitle: {
    fontSize: 13,
    marginTop: 2,
  },
  conversation: {
    flex: 1,
  },
  conversationContent: {
    paddingVertical: 12,
    gap: 14,
  },
  emptyCard: {
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 22,
    padding: 22,
    marginTop: 24,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '800',
    marginTop: 10,
  },
  emptyBody: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    marginTop: 8,
  },
  turnBlock: {
    gap: 10,
  },
  userBubble: {
    alignSelf: 'flex-end',
    maxWidth: '88%',
    borderRadius: 18,
    padding: 13,
  },
  answerBubble: {
    alignSelf: 'flex-start',
    maxWidth: '92%',
    borderRadius: 18,
    padding: 14,
    borderWidth: 1,
  },
  liveCard: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
  },
  bubbleLabel: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    marginBottom: 5,
  },
  bubbleText: {
    fontSize: 15,
    lineHeight: 21,
  },
  followUpRow: {
    gap: 8,
    marginBottom: 10,
  },
  followUpChip: {
    borderWidth: 1,
    borderRadius: 14,
    paddingVertical: 9,
    paddingHorizontal: 12,
    backgroundColor: 'rgba(255,255,255,0.08)',
  },
  followUpText: {
    fontSize: 13,
    fontWeight: '600',
  },
  errorText: {
    textAlign: 'center',
    fontSize: 13,
    marginBottom: 8,
  },
  controls: {
    alignItems: 'center',
    paddingBottom: 28,
  },
  handsFreeToggle: {
    width: '100%',
    borderWidth: 1,
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  handsFreeText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '700',
  },
  handsFreeState: {
    fontSize: 13,
    fontWeight: '800',
  },
  statusText: {
    fontSize: 14,
    marginBottom: 14,
    textAlign: 'center',
  },
  micButtonOuter: {
    borderRadius: 44,
    shadowColor: '#f97316',
    shadowOpacity: 0.35,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 8 },
    elevation: 8,
  },
  micButtonDisabled: {
    opacity: 0.7,
  },
  micButton: {
    width: 88,
    height: 88,
    borderRadius: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
