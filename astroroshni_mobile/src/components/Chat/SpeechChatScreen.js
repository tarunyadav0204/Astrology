import React, { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  Alert,
  Dimensions,
  Linking,
  PermissionsAndroid,
  Platform,
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

import { chatAPI, pricingAPI } from '../../services/api';
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

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const SCREEN_WIDTH = Dimensions.get('window').width;
const VOICE_STAGE_WIDTH = 186;
/** Base circle diameter before scaleX/scaleY — wide soft blobs, not sharp rectangles. */
const WAVE_BLOB_SIZE = 108;

/** i18n keys for short spoken handoff after listening → thinking (rotate to avoid repetition). */
const THINKING_HANDOFF_KEYS = [
  'speechChat.thinkingHandoff1',
  'speechChat.thinkingHandoff2',
  'speechChat.thinkingHandoff3',
];
const THINKING_HANDOFF_DEFAULTS = [
  'Got it. Give me a moment.',
  'Okay, I’m looking at that now.',
  'I have what I need. Let me read that for you.',
];

export default function SpeechChatScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const [userName, setUserName] = useState('');
  const [birthData, setBirthData] = useState(route.params?.birthData || null);
  const [sessionId, setSessionId] = useState(null);
  const [language, setLanguage] = useState(route.params?.language || 'english');
  const [status, setStatus] = useState('idle');
  const [turns, setTurns] = useState([]);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [followUps, setFollowUps] = useState([]);
  const [errorText, setErrorText] = useState('');
  const [handsFreeEnabled, setHandsFreeEnabled] = useState(true);
  const [speechChatCost, setSpeechChatCost] = useState(null);
  const mountedRef = useRef(true);
  const scrollRef = useRef(null);
  const handsFreeRestartRef = useRef(false);
  const greetedRef = useRef(false);
  const thinkingLeadInIndexRef = useRef(0);
  const pulseAnim = useRef(new Animated.Value(0)).current;
  const cardPulseAnim = useRef(new Animated.Value(0)).current;
  const bottomWaveAnims = useRef([
    new Animated.Value(0),
    new Animated.Value(0),
    new Animated.Value(0),
  ]).current;
  const waveAnims = useRef([
    new Animated.Value(0.35),
    new Animated.Value(0.55),
    new Animated.Value(0.8),
    new Animated.Value(0.55),
    new Animated.Value(0.35),
  ]).current;

  useEffect(() => {
    mountedRef.current = true;
    const subscription = speechRecognition.addPartialListener((partial) => {
      const next = String(partial || '').trim();
      if (!next || !mountedRef.current) return;
      setCurrentTranscript(next);
    });

    const loadContext = async () => {
      const [storedBirthData, storedLanguage, storedUser] = await Promise.all([
        storage.getBirthDetails(),
        storage.getLanguage(),
        storage.getUserData(),
      ]);
      if (mountedRef.current) {
        if (!birthData && storedBirthData) setBirthData(storedBirthData);
        if (!route.params?.language && storedLanguage) setLanguage(storedLanguage);
        setUserName(String(storedUser?.name || storedUser?.full_name || '').trim());
      }
    };

    loadContext();

    let cancelledPricing = false;
    (async () => {
      try {
        const res = await pricingAPI.getPricing();
        const pricing = res?.data?.pricing || {};
        const sc = pricing.speech_chat != null ? Number(pricing.speech_chat) : null;
        const ic = pricing.instant_chat != null ? Number(pricing.instant_chat) : null;
        const val =
          sc != null && !Number.isNaN(sc) && sc > 0
            ? sc
            : ic != null && !Number.isNaN(ic) && ic > 0
              ? ic
              : 1;
        if (!cancelledPricing && mountedRef.current) setSpeechChatCost(val);
      } catch {
        if (!cancelledPricing && mountedRef.current) setSpeechChatCost(1);
      }
    })();

    return () => {
      cancelledPricing = true;
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
    if (!currentTranscript) return undefined;
    const timer = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 80);
    return () => clearTimeout(timer);
  }, [currentTranscript]);

  useEffect(() => {
    pulseAnim.stopAnimation();
    waveAnims.forEach((anim) => anim.stopAnimation());
    bottomWaveAnims.forEach((anim) => anim.stopAnimation());

    if (status === 'listening' || status === 'speaking') {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1, duration: 900, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 0, duration: 900, useNativeDriver: true }),
        ])
      ).start();

      waveAnims.forEach((anim, index) => {
        Animated.loop(
          Animated.sequence([
            Animated.timing(anim, {
              toValue: status === 'listening' ? 1.1 - (index % 2) * 0.15 : 0.95 - (index % 2) * 0.1,
              duration: 240 + index * 90,
              useNativeDriver: true,
            }),
            Animated.timing(anim, {
              toValue: 0.3 + (index % 3) * 0.12,
              duration: 260 + index * 80,
              useNativeDriver: true,
            }),
          ])
        ).start();
      });

      bottomWaveAnims.forEach((anim, index) => {
        Animated.loop(
          Animated.sequence([
            Animated.timing(anim, {
              toValue: status === 'speaking' ? 1 : 0.8,
              duration: 1100 + index * 180,
              useNativeDriver: true,
            }),
            Animated.timing(anim, {
              toValue: 0,
              duration: 1050 + index * 160,
              useNativeDriver: true,
            }),
          ])
        ).start();
      });
      return;
    }

    if (status === 'thinking' || status === 'transcribing') {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 0.6, duration: 700, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 0.1, duration: 700, useNativeDriver: true }),
        ])
      ).start();
      bottomWaveAnims.forEach((anim, index) => {
        Animated.loop(
          Animated.sequence([
            Animated.timing(anim, {
              toValue: 0.45,
              duration: 1300 + index * 140,
              useNativeDriver: true,
            }),
            Animated.timing(anim, {
              toValue: 0,
              duration: 1200 + index * 120,
              useNativeDriver: true,
            }),
          ])
        ).start();
      });
    } else {
      pulseAnim.setValue(0);
      waveAnims.forEach((anim, index) => anim.setValue(0.28 + index * 0.06));
      bottomWaveAnims.forEach((anim) => anim.setValue(0));
    }
  }, [bottomWaveAnims, pulseAnim, status, waveAnims]);

  useEffect(() => {
    cardPulseAnim.stopAnimation();
    if (status === 'listening' || status === 'thinking' || status === 'speaking') {
      Animated.loop(
        Animated.sequence([
          Animated.timing(cardPulseAnim, { toValue: 1, duration: 1200, useNativeDriver: true }),
          Animated.timing(cardPulseAnim, { toValue: 0, duration: 1200, useNativeDriver: true }),
        ])
      ).start();
    } else {
      cardPulseAnim.setValue(0);
    }
  }, [cardPulseAnim, status]);

  useEffect(() => {
    greetedRef.current = false;
  }, [birthData?.id]);

  useEffect(() => {
    if (greetedRef.current || !birthData?.name || status !== 'idle') return;

    const greet = async () => {
      greetedRef.current = true;
      const chartName = String(birthData?.name || '').trim();
      const trimmedUserName = String(userName || '').trim();
      const greeting = trimmedUserName
        ? t('speechChat.greetingWithUser', {
            userName: trimmedUserName,
            chartName,
            defaultValue:
              `Hello ${trimmedUserName}, I'm Tara, your voice guide on AstroRoshni. Thanks for sharing ${chartName}'s chart. How can I help you? Do you have a question for me?`,
          })
        : t('speechChat.greetingAnonymous', {
            chartName,
            defaultValue:
              `Hello, I'm Tara, your voice guide on AstroRoshni. Thanks for sharing ${chartName}'s chart. How can I help you? Do you have a question for me?`,
          });

      setStatus('speaking');
      await getTextToSpeech().speak(greeting, {
        language,
        onDone: () => {
          if (!mountedRef.current) return;
          if (handsFreeEnabled) {
            maybeStartAfterGreeting();
            return;
          }
          setStatus('idle');
        },
        onError: () => mountedRef.current && setStatus('idle'),
      });
    };

    greet();
  }, [birthData?.name, language, status, t, userName]);

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

  const ensureMicrophonePermission = async () => {
    if (Platform.OS !== 'android') return true;

    const alreadyGranted = await PermissionsAndroid.check(PermissionsAndroid.PERMISSIONS.RECORD_AUDIO);
    if (alreadyGranted) return true;

    const result = await PermissionsAndroid.request(
      PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
      {
        title: t('speechChat.micPermissionTitle', 'Microphone permission needed'),
        message: t('speechChat.micPermissionBody', 'Please allow microphone access so AstroRoshni can hear your question.'),
        buttonPositive: t('speechChat.allow', 'Allow'),
        buttonNegative: t('speechChat.cancel', 'Cancel'),
      }
    );

    if (result === PermissionsAndroid.RESULTS.GRANTED) return true;

    if (result === PermissionsAndroid.RESULTS.NEVER_ASK_AGAIN) {
      Alert.alert(
        t('speechChat.micPermissionTitle', 'Microphone permission needed'),
        t('speechChat.micPermissionSettingsBody', 'Microphone access is turned off for AstroRoshni. Please enable it in app settings and try again.'),
        [
          { text: t('speechChat.cancel', 'Cancel'), style: 'cancel' },
          { text: t('speechChat.openSettings', 'Open Settings'), onPress: () => Linking.openSettings() },
        ]
      );
      return false;
    }

    setErrorText(t('speechChat.micPermissionBody', 'Please allow microphone access so AstroRoshni can hear your question.'));
    return false;
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

    const permissionGranted = await ensureMicrophonePermission();
    if (!permissionGranted) return;

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
        await speakThinkingHandoff();
        if (!mountedRef.current) return;
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
      await wait(260);
      await startListening();
    } catch (error) {
      if (!mountedRef.current) return;
      setErrorText(error?.message || t('speechChat.genericError', 'Something went wrong. Please try again.'));
      setStatus('idle');
    }
  };

  const maybeStartAfterGreeting = async () => {
    if (!mountedRef.current || !handsFreeEnabled) return;
    setErrorText('');
    try {
      await wait(260);
      await startListening();
    } catch (error) {
      if (!mountedRef.current) return;
      setErrorText(error?.message || t('speechChat.genericError', 'Something went wrong. Please try again.'));
      setStatus('idle');
    }
  };

  /** Brief natural line when recognition is done so the jump to “thinking” is not silent. */
  const speakThinkingHandoff = async () => {
    if (!mountedRef.current) return;
    const i = thinkingLeadInIndexRef.current % THINKING_HANDOFF_KEYS.length;
    thinkingLeadInIndexRef.current += 1;
    const phrase = t(THINKING_HANDOFF_KEYS[i], THINKING_HANDOFF_DEFAULTS[i]);
    try {
      await getTextToSpeech().speak(phrase, { language });
    } catch {
      // ignore short transition TTS failures
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
      response_style: 'concise',
      premium_analysis: false,
      chat_tier: 'instant',
      speech_chat: true,
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
    const spokenAnswer = handsFreeEnabled
      ? answer
      : `${answer} ${t('speechChat.afterAnswerPrompt', "If you'd like, ask me another question.")}`.trim();
    const nextFollowUps = Array.isArray(data.follow_up_questions)
      ? data.follow_up_questions.map((item) => String(item || '').trim()).filter(Boolean).slice(0, 3)
      : [];
    setFollowUps(nextFollowUps);
    setTurns((prev) => [...prev, { question, answer, followUps: nextFollowUps }]);
    setCurrentTranscript('');
    setStatus('speaking');
    handsFreeRestartRef.current = !!handsFreeEnabled;
    await getTextToSpeech().speak(spokenAnswer, {
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
      await speakThinkingHandoff();
      if (!mountedRef.current) return;
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
        await startListening();
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
  const glowScaleX = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [1, status === 'speaking' ? 1.12 : 1.08],
  });
  const orbOpacity = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.22, 0.5],
  });
  const thinkingScale = pulseAnim.interpolate({
    inputRange: [0, 0.6],
    outputRange: [1, 1.05],
  });
  const bottomWaveTransforms = bottomWaveAnims.map((anim, index) =>
    anim.interpolate({
      inputRange: [0, 1],
      outputRange: [0, status === 'speaking' ? -(14 + index * 5) : -(10 + index * 3)],
    })
  );
  const bottomWaveDrift = bottomWaveAnims.map((anim, index) =>
    anim.interpolate({
      inputRange: [0, 1],
      outputRange: [0, (index === 1 ? 1 : -1) * (6 + index * 2)],
    })
  );
  const waveBlobScale1 = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [3.9, 4.5],
  });
  const waveBlobScale2 = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [3.35, 3.95],
  });
  const waveBlobScale3 = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [2.85, 3.45],
  });
  const transcriptScale = cardPulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 1.015],
  });
  const transcriptGlow = cardPulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.16, 0.34],
  });
  const voiceBarWidth = Math.min(280, SCREEN_WIDTH * 0.78);

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
            <Text style={[styles.title, { color: colors.text }]}>
              {t('speechChat.screenTitle', 'Tara')}
            </Text>
            <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
              {birthData?.name
                ? t('speechChat.screenSubtitleWithChart', {
                    name: birthData.name,
                    defaultValue: `Voice guide on AstroRoshni · Instant answers for ${birthData.name}`,
                  })
                : t('speechChat.screenSubtitleDefault', 'Voice guide on AstroRoshni · Instant spoken answers')}
            </Text>
          </View>
          <View style={[styles.liveBadge, { backgroundColor: isDark ? 'rgba(59,130,246,0.18)' : 'rgba(59,130,246,0.10)', borderColor: isDark ? 'rgba(125,211,252,0.22)' : 'rgba(59,130,246,0.14)' }]}>
            <View style={styles.liveDot} />
            <Text style={[styles.liveBadgeText, { color: isDark ? '#bfdbfe' : '#2563eb' }]}>Live</Text>
          </View>
        </View>

        <View style={styles.mainColumn}>
        <ScrollView ref={scrollRef} style={styles.conversation} contentContainerStyle={styles.conversationContent}>
          {turns.length === 0 && !currentTranscript ? (
            <View style={[styles.emptyCard, { borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}>
              <Ionicons name="mic-circle-outline" size={44} color={colors.primary} />
              <Text style={[styles.emptyTitle, { color: colors.text }]}>
                {t('speechChat.emptyCardTitle', 'Ask by speaking')}
              </Text>
              <Text style={[styles.emptyBody, { color: colors.textSecondary }]}>
                {t(
                  'speechChat.emptyCardBody',
                  'Keep questions short and natural. Tara answers aloud and suggests follow-ups.',
                )}
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
                <Text style={[styles.bubbleLabel, { color: colors.textSecondary }]}>
                  {t('speechChat.answerBubbleLabel', 'Tara answered')}
                </Text>
                <Text style={[styles.bubbleText, { color: colors.text }]}>{turn.answer}</Text>
              </View>
            </View>
          ))}

          {currentTranscript ? (
            <Animated.View
              style={[
                styles.liveCard,
                {
                  borderColor: isDark ? 'rgba(125,211,252,0.18)' : 'rgba(59,130,246,0.12)',
                  backgroundColor: isDark ? 'rgba(15,23,42,0.82)' : 'rgba(255,255,255,0.88)',
                  shadowOpacity: status === 'idle' ? 0.08 : transcriptGlow,
                  transform: [{ scale: transcriptScale }],
                },
              ]}
            >
              <Text style={[styles.bubbleLabel, { color: colors.textSecondary }]}>
                {status === 'listening' ? t('speechChat.heardSoFar', 'Heard so far') : t('speechChat.currentQuestion', 'Current question')}
              </Text>
              <Text style={[styles.bubbleText, { color: colors.text }]}>{currentTranscript}</Text>
            </Animated.View>
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
        </View>

        <LinearGradient
          colors={
            isDark
              ? ['rgba(8,47,73,0.14)', 'rgba(29,78,216,0.24)', 'rgba(37,99,235,0.12)']
              : ['rgba(239,246,255,0.96)', 'rgba(219,234,254,0.92)', 'rgba(224,242,254,0.86)']
          }
          style={[styles.controlsShell, { borderColor: isDark ? 'rgba(125,211,252,0.12)' : 'rgba(59,130,246,0.10)' }]}
        >
        <View style={styles.controls}>
          <View pointerEvents="none" style={styles.waveBackdrop}>
            {/* Stretched circles = horizontal “aurora” blobs (visible on light + dark shells). */}
            <Animated.View
              style={[
                styles.waveBlob,
                {
                  backgroundColor: isDark ? 'rgba(30,64,175,0.42)' : 'rgba(59,130,246,0.38)',
                  left: SCREEN_WIDTH / 2 - WAVE_BLOB_SIZE / 2,
                  bottom: -WAVE_BLOB_SIZE * 0.42,
                  transform: [
                    { translateX: bottomWaveDrift[0] },
                    { translateY: bottomWaveTransforms[0] },
                    { scaleX: waveBlobScale1 },
                    { scaleY: 0.52 },
                  ],
                },
              ]}
            >
              <LinearGradient
                colors={
                  isDark
                    ? ['rgba(56,189,248,0.15)', 'rgba(37,99,235,0.55)', 'rgba(14,165,233,0.35)']
                    : ['rgba(147,197,253,0.5)', 'rgba(59,130,246,0.55)', 'rgba(96,165,250,0.45)']
                }
                start={{ x: 0.5, y: 0 }}
                end={{ x: 0.5, y: 1 }}
                style={StyleSheet.absoluteFill}
              />
            </Animated.View>
            <Animated.View
              style={[
                styles.waveBlob,
                {
                  backgroundColor: isDark ? 'rgba(14,116,144,0.35)' : 'rgba(125,211,252,0.32)',
                  left: SCREEN_WIDTH / 2 - WAVE_BLOB_SIZE / 2,
                  bottom: -WAVE_BLOB_SIZE * 0.36,
                  transform: [
                    { translateX: bottomWaveDrift[1] },
                    { translateY: bottomWaveTransforms[1] },
                    { scaleX: waveBlobScale2 },
                    { scaleY: 0.44 },
                  ],
                },
              ]}
            >
              <LinearGradient
                colors={
                  isDark
                    ? ['rgba(56,189,248,0.1)', 'rgba(59,130,246,0.4)', 'rgba(30,58,138,0.35)']
                    : ['rgba(224,242,254,0.65)', 'rgba(59,130,246,0.4)', 'rgba(37,99,235,0.38)']
                }
                start={{ x: 0, y: 0.5 }}
                end={{ x: 1, y: 0.5 }}
                style={StyleSheet.absoluteFill}
              />
            </Animated.View>
            <Animated.View
              style={[
                styles.waveBlob,
                {
                  backgroundColor: isDark ? 'rgba(14,165,233,0.38)' : 'rgba(96,165,250,0.36)',
                  left: SCREEN_WIDTH / 2 - WAVE_BLOB_SIZE / 2,
                  bottom: -WAVE_BLOB_SIZE * 0.3,
                  transform: [
                    { translateX: bottomWaveDrift[2] },
                    { translateY: bottomWaveTransforms[2] },
                    { scaleX: waveBlobScale3 },
                    { scaleY: 0.38 },
                  ],
                },
              ]}
            >
              <LinearGradient
                colors={
                  isDark
                    ? ['rgba(125,211,252,0.2)', 'rgba(14,165,233,0.5)', 'rgba(37,99,235,0.45)']
                    : ['rgba(255,255,255,0.35)', 'rgba(125,211,252,0.55)', 'rgba(59,130,246,0.48)']
                }
                start={{ x: 0.5, y: 0 }}
                end={{ x: 0.5, y: 1 }}
                style={StyleSheet.absoluteFill}
              />
            </Animated.View>
          </View>
          <View style={styles.voiceStage}>
            <Animated.View
              pointerEvents="none"
              style={[
                styles.voiceGlowBar,
                {
                  width: voiceBarWidth,
                  left: (VOICE_STAGE_WIDTH - voiceBarWidth) / 2,
                  opacity: status === 'idle' ? 0.1 : orbOpacity,
                  transform: [
                    {
                      scaleX:
                        status === 'thinking' || status === 'transcribing' ? thinkingScale : glowScaleX,
                    },
                  ],
                },
              ]}
            >
              <LinearGradient
                colors={
                  isDark
                    ? ['rgba(56,189,248,0.12)', 'rgba(37,99,235,0.38)', 'rgba(14,165,233,0.22)']
                    : ['rgba(147,197,253,0.35)', 'rgba(59,130,246,0.45)', 'rgba(125,211,252,0.3)']
                }
                start={{ x: 0, y: 0.5 }}
                end={{ x: 1, y: 0.5 }}
                style={StyleSheet.absoluteFill}
              />
            </Animated.View>
            <View style={styles.waveRow}>
              {waveAnims.map((anim, index) => (
                <Animated.View
                  key={`wave_${index}`}
                  style={[
                    styles.waveBar,
                    {
                      backgroundColor:
                        status === 'speaking'
                          ? '#60a5fa'
                          : status === 'listening'
                            ? '#38bdf8'
                            : '#93c5fd',
                      opacity: status === 'idle' ? 0.3 : 0.95,
                      transform: [{ scaleY: anim }],
                    },
                  ]}
                />
              ))}
            </View>
          </View>
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
          {speechChatCost != null ? (
            <Text style={[styles.speechCostHint, { color: colors.textSecondary }]}>
              {t('speechChat.creditsPerTurn', { count: speechChatCost })}
            </Text>
          ) : null}
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={handleMicPress}
            disabled={busy}
            style={[styles.micButtonOuter, busy && styles.micButtonDisabled]}
          >
            <LinearGradient
              colors={status === 'listening' ? ['#0ea5e9', '#2563eb'] : ['#38bdf8', '#2563eb']}
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
    flexShrink: 0,
  },
  mainColumn: {
    flex: 1,
    minHeight: 0,
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
  liveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  liveDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#38bdf8',
  },
  liveBadgeText: {
    fontSize: 12,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
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
    shadowColor: '#38bdf8',
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 8 },
    elevation: 4,
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
    flexShrink: 0,
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
    flexShrink: 0,
  },
  controlsShell: {
    marginHorizontal: -18,
    paddingHorizontal: 18,
    paddingTop: 16,
    paddingBottom: 8,
    borderTopWidth: 1,
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    overflow: 'hidden',
    flexShrink: 0,
  },
  controls: {
    alignItems: 'center',
    paddingBottom: 28,
    overflow: 'visible',
  },
  waveBackdrop: {
    position: 'absolute',
    left: -18,
    right: -18,
    bottom: -40,
    height: 220,
    overflow: 'visible',
  },
  waveBlob: {
    position: 'absolute',
    width: WAVE_BLOB_SIZE,
    height: WAVE_BLOB_SIZE,
    borderRadius: WAVE_BLOB_SIZE / 2,
    overflow: 'hidden',
  },
  voiceStage: {
    width: VOICE_STAGE_WIDTH,
    height: 120,
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginBottom: 10,
  },
  voiceGlowBar: {
    position: 'absolute',
    bottom: 10,
    height: 44,
    borderRadius: 22,
    overflow: 'hidden',
  },
  waveRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'center',
    gap: 8,
    height: 58,
  },
  waveBar: {
    width: 10,
    height: 44,
    borderRadius: 999,
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
    marginBottom: 6,
    textAlign: 'center',
  },
  speechCostHint: {
    fontSize: 12,
    marginBottom: 14,
    textAlign: 'center',
    fontWeight: '600',
  },
  micButtonOuter: {
    borderRadius: 44,
    shadowColor: '#2563eb',
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
