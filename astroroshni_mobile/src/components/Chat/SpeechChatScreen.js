import React, { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  Alert,
  Dimensions,
  Image,
  Linking,
  PermissionsAndroid,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  Vibration,
  View,
  ScrollView,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { Audio, InterruptionModeIOS, InterruptionModeAndroid } from 'expo-av';
import * as FileSystem from 'expo-file-system/legacy';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { chatAPI, creditAPI, pricingAPI, speechAPI } from '../../services/api';
import { storage } from '../../services/storage';
import { buildQueryContext } from '../../utils/queryContext';
import { getTextToSpeech } from '../../utils/textToSpeechLazy';
import { useTheme } from '../../context/ThemeContext';
import { speechRecognition } from '../../native/speechRecognition';

const POLL_INTERVAL_MS = 1400;
const MAX_POLLS = 90;
const SPEECH_TTS_MAX_CHARS = 820;
const USE_BACKEND_SPEECH_TRANSCRIPTION = true;
const ALLOW_NATIVE_RUNTIME_BACKEND_FALLBACK = false;
const PREFER_NATIVE_SPEECH_RECOGNITION = Platform.OS === 'ios';
const REQUIRE_NATIVE_SPEECH_FOR_WEBSOCKET = Platform.OS === 'ios';
const USE_SPEECH_WEBSOCKET = true;
const HANDS_FREE_AUTO_STOP_MS = 5 * 60 * 1000;
const BACKEND_RECORDING_MIN_MS = 2600;
const BACKEND_RECORDING_SILENCE_STOP_MS = 4200;
const BACKEND_RECORDING_LONG_SILENCE_STOP_MS = 7000;
const BACKEND_RECORDING_LONG_QUESTION_AFTER_MS = 5000;
const BACKEND_RECORDING_SPEECH_THRESHOLD_DB = -55;
const NATIVE_PARTIAL_STABLE_SUBMIT_MS = 1300;
const NATIVE_MAX_LISTENING_MS = 14000;
const NATIVE_READY_TIMEOUT_MS = 4500;
const POST_TTS_LISTEN_DELAY_MS = Platform.OS === 'android' ? 1200 : 900;
const POST_TTS_ECHO_GUARD_MS = Platform.OS === 'android' ? 250 : 200;
const MAX_NATIVE_NO_SPEECH_RETRIES = 0;
const SPEECH_BILLING_MIN_START_MINUTES = 5;
const SPEECH_CREDIT_WARNING_SECONDS = 60;
const SPEECH_CREDIT_WARNING_INTERVAL_SECONDS = 10;
const CREDIT_WARNING_BEEP_BASE64 = 'UklGRqQCAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YYACAACAudjOoWQ0JkJ6tNfRpmk3Jj50sNXTq286Jjpvq9PVsHQ+JjdpptHXtHpCJjRkoc7YuX9GJzFem8vZvYVLKC5ZlsjZwYtPKixUkMXaxZBULCpPi8HZyJZZLihLhb3Zy5teMSdGgLnYzqFkNCZCerTX0aZpNyY+dLDV06tvOiY6b6vT1bB0PiY3aabR17R6QiY0ZKHO2LmARicxXpvL2b2FSyguWZbI2cGLTyosVJDF2sWQVCwqT4vB2ciWWS4oS4W92cubXjEnRoC52M6hZDQmQnq019GmaTcmPnSw1dOrbzomOm+r09WwdD4mN2mm0de0ekImNGShzti5f0YnMV6by9m9hUsoLlmWyNnBi08qLFSQxdrFkFQsKk+LwdnIllkuKEuFvdnLm14xJ0Z/udjOoWQ0JkJ6tNfRpmk3Jj50sNXTq286Jjpvq9PVsHQ+JjdpptHXtHpCJjRkoc7YuX9GJzFem8vZvYVLKC5ZlsjZwYtPKixUkMXaxZBULCpPi8HZyJZZLihLhb3Zy5teMSdGgLnYzqFkNCZCerTX0aZpNyY+dLDV06tvOiY6b6vT1bB0PiY3aabR17R6QiY0ZKHO2Ll/RicxXpvL2b2FSyguWZbI2cGLTyosVJDF2sWQVCwqT4vB2ciWWS4oS4W92cubXjEnRoC52M6hZDQmQnq019GmaTcmPnSw1dOrbzomOm+r09WwdD4mN2mm0de0ekImNGShzti5f0YnMV6by9m9hUsoLlmWyNnBi08qLFSQxdrFkFQsKk+LwdnIllkuKEuFvdnLm14xJ0Z/udjOoWQ0JkJ6tNfRpmk3Jj50sNXTq286Jjpvq9PVsHQ+JjdpptHX';
const SPEECH_RECORDING_OPTIONS = {
  ...Audio.RecordingOptionsPresets.HIGH_QUALITY,
  isMeteringEnabled: true,
};

const normalizeLanguageCode = (language) => {
  const raw = String(language || 'english').toLowerCase();
  return raw.startsWith('hi') ? 'hindi' : language || 'english';
};

const inferSpeechTurnLanguage = (text, fallback = 'english') => {
  const raw = String(text || '').trim();
  const fallbackLang = normalizeLanguageCode(fallback || 'english');
  if (!raw) return fallbackLang;

  const devanagariChars = raw.match(/[\u0900-\u097F]/g)?.length || 0;
  if (devanagariChars >= 2) return 'hindi';

  const latinWords = raw
    .toLowerCase()
    .replace(/[^a-z\s']/g, ' ')
    .split(/\s+/)
    .filter(Boolean);
  if (!latinWords.length) return fallbackLang;

  const romanHindiWords = new Set([
    'mera', 'meri', 'mere', 'mujhe', 'main', 'mein', 'mai', 'kya', 'kaise',
    'kaisa', 'kaisi', 'kaun', 'kab', 'kyun', 'kyu', 'hoga', 'hogi', 'honge',
    'hai', 'hain', 'tha', 'thi', 'rahega', 'rahegi', 'batao', 'bataye',
    'kundli', 'dasha', 'mahadasha', 'antar', 'antardasha', 'shaadi',
    'vivah', 'patni', 'pati', 'naukri', 'swasthya', 'career', 'paisa',
    'rishta', 'sambandh', 'saal', 'mahina', 'abhi', 'aage', 'ke', 'ka', 'ki',
  ]);
  const hits = latinWords.filter((word) => romanHindiWords.has(word)).length;
  const ratio = hits / latinWords.length;

  if (hits >= 2 && ratio >= 0.18) return 'hindi';
  if (fallbackLang === 'hindi' && hits >= 1 && latinWords.length <= 5) return 'hindi';
  return fallbackLang;
};

const toChatBirthDetails = (birthData) => ({
  id: birthData?.id || birthData?.birth_chart_id || birthData?.birthChartId,
  birth_chart_id: birthData?.birth_chart_id || birthData?.id || birthData?.birthChartId,
  name: birthData?.name,
  date: typeof birthData?.date === 'string' ? birthData.date.split('T')[0] : birthData?.date,
  time: typeof birthData?.time === 'string'
    ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time
    : birthData?.time,
  latitude: parseFloat(birthData?.latitude),
  longitude: parseFloat(birthData?.longitude),
  timezone: birthData?.timezone,
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
const SCREEN_HEIGHT = Dimensions.get('window').height;
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
const SPEECH_CHAT_TTS_PROVIDER = 'google';
const SPEECH_GREETING_CACHE_VERSION = 'v3';

const hashGreetingText = (value) => {
  const text = String(value || '');
  let hash = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16);
};

const trimForSpeechPlayback = (text, limit = SPEECH_TTS_MAX_CHARS) => {
  const raw = String(text || '').replace(/\s+/g, ' ').trim();
  if (raw.length <= limit) return raw;
  const slice = raw.slice(0, limit);
  const boundary = Math.max(
    slice.lastIndexOf('.'),
    slice.lastIndexOf('?'),
    slice.lastIndexOf('!'),
    slice.lastIndexOf('।')
  );
  if (boundary >= 500) return slice.slice(0, boundary + 1).trim();
  return `${slice.slice(0, Math.max(0, limit - 1)).trim()}…`;
};

const estimateSpeechDurationMs = (text) => {
  const spoken = String(text || '').replace(/\s+/g, ' ').trim();
  if (!spoken) return 2500;
  const words = spoken.split(/\s+/).filter(Boolean).length;
  const punctuationPauses = (spoken.match(/[.!?।]/g) || []).length * 180;
  const estimate = 900 + words * 360 + punctuationPauses;
  return Math.max(2600, Math.min(42000, estimate));
};

const buildSpeechAfterAnswerPrompt = (turnLanguage, followUpQuestion, translate) => {
  const lang = normalizeLanguageCode(turnLanguage || 'english');
  const question = String(followUpQuestion || '').trim();
  if (lang === 'hindi') {
    return question
      ? `आप यह भी पूछ सकते हैं: ${question}`
      : 'आप चाहें तो एक और सवाल पूछ सकते हैं।';
  }
  return question
    ? translate('speechChat.afterAnswerPromptWithFollowUp', {
        question,
        defaultValue: `You can also ask: ${question}`,
      })
    : translate('speechChat.afterAnswerPrompt', "If you'd like, ask me another question.");
};

const TARA_BASE = require('../../assets/tara/base_head_body.png');
const TARA_EYES_OPEN = require('../../assets/tara/eyes_open.png');
const TARA_EYES_CLOSED = require('../../assets/tara/eyes_closed.png');
const TARA_MOUTH_CLOSED = require('../../assets/tara/mouth_closed.png');
const TARA_VISEME_SOURCES = {
  rest: TARA_MOUTH_CLOSED,
};

function TaraSpeakingAvatar({ status, compact = false, tiny = false }) {
  const [blinkClosed, setBlinkClosed] = useState(false);
  const bobAnim = useRef(new Animated.Value(0)).current;
  const blinkTimerRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    const scheduleBlink = () => {
      const delay = 2200 + Math.random() * 2600;
      blinkTimerRef.current = setTimeout(() => {
        if (cancelled) return;
        setBlinkClosed(true);
        setTimeout(() => {
          if (cancelled) return;
          setBlinkClosed(false);
          scheduleBlink();
        }, 120);
      }, delay);
    };

    scheduleBlink();

    return () => {
      cancelled = true;
      if (blinkTimerRef.current) clearTimeout(blinkTimerRef.current);
    };
  }, []);

  useEffect(() => {
    bobAnim.stopAnimation();
    bobAnim.setValue(0);
  }, [bobAnim, status]);

  const translateY = bobAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, status === 'speaking' ? -3 : -1.5],
  });
  const mouthSource = TARA_VISEME_SOURCES.rest;

  return (
    <Animated.View style={[
      styles.avatarWrap,
      compact && styles.avatarWrapCompact,
      tiny && styles.avatarWrapTiny,
      { transform: [{ translateY }] },
    ]}>
      <View style={[
        styles.avatarImageStage,
        compact && styles.avatarImageStageCompact,
        tiny && styles.avatarImageStageTiny,
      ]}>
        <Image source={TARA_BASE} style={[styles.avatarImageLayer, styles.avatarBaseLayer]} resizeMode="contain" />
        <Image
          source={blinkClosed ? TARA_EYES_CLOSED : TARA_EYES_OPEN}
          style={[styles.avatarImageLayer, styles.avatarFeatureLayer]}
          resizeMode="contain"
        />
        <Image source={mouthSource} style={[styles.avatarImageLayer, styles.avatarFeatureLayer]} resizeMode="contain" />
      </View>
    </Animated.View>
  );
}

export default function SpeechChatScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
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
  const [nativeRecognizerPhase, setNativeRecognizerPhase] = useState('idle');
  const [nativeRecognizerReady, setNativeRecognizerReady] = useState(false);
  const [speechChatCost, setSpeechChatCost] = useState(null);
  const [speechPerMinuteCost, setSpeechPerMinuteCost] = useState(null);
  const [billingSession, setBillingSession] = useState(null);
  const [callElapsedSeconds, setCallElapsedSeconds] = useState(0);
  const [callRemainingSeconds, setCallRemainingSeconds] = useState(null);
  const [speechTtsProvider, setSpeechTtsProvider] = useState('local');
  const [speechTtsReady, setSpeechTtsReady] = useState(false);
  const [avatarSpeech, setAvatarSpeech] = useState({
    active: false,
    text: '',
    timeline: [],
    positionMs: 0,
    durationMs: 0,
    audioStarted: false,
  });
  const mountedRef = useRef(true);
  const statusRef = useRef('idle');
  const handsFreeEnabledRef = useRef(true);
  const scrollRef = useRef(null);
  const handsFreeRestartRef = useRef(false);
  const greetedRef = useRef(false);
  const thinkingLeadInIndexRef = useRef(0);
  const recordingRef = useRef(null);
  const listeningModeRef = useRef(null);
  const recordingMeterTimerRef = useRef(null);
  const recordingAutoStopTimerRef = useRef(null);
  const nativePartialStableTimerRef = useRef(null);
  const nativeMaxListenTimerRef = useRef(null);
  const nativeReadyTimerRef = useRef(null);
  const latestNativeTranscriptRef = useRef('');
  const nativeNoSpeechRetryCountRef = useRef(0);
  const nativeSpeechUnavailableForSessionRef = useRef(false);
  const recordingAutoStoppingRef = useRef(false);
  const recordingStartedAtRef = useRef(0);
  const recordingSpeechDetectedRef = useRef(false);
  const recordingSpeechFirstDetectedAtRef = useRef(0);
  const recordingSpeechSampleCountRef = useRef(0);
  const recordingLastSpeechAtRef = useRef(0);
  const recordingMeterSamplesRef = useRef([]);
  const startListeningInFlightRef = useRef(false);
  const activeTurnSerialRef = useRef(0);
  const activeTurnLanguageRef = useRef(normalizeLanguageCode(route.params?.language || 'english'));
  const speechSocketRef = useRef(null);
  const speechSocketConnectPromiseRef = useRef(null);
  const speechSocketPendingTurnsRef = useRef(new Map());
  const greetingPrefetchKeyRef = useRef('');
  const speakingWatchdogRef = useRef(null);
  const billingSessionRef = useRef(null);
  const billingTimerRef = useRef(null);
  const billingStartMsRef = useRef(0);
  const lastCreditWarningBeepRef = useRef(0);
  const billingEndingRef = useRef(false);
  const pulseAnim = useRef(new Animated.Value(0)).current;
  const cardPulseAnim = useRef(new Animated.Value(0)).current;
  const sparkleAnims = useRef(
    Array.from({ length: 8 }, () => new Animated.Value(0))
  ).current;

  const buildGreetingText = () => {
    const chartName = String(birthData?.name || '').trim();
    const trimmedUserName = String(userName || '').trim();
    if (!chartName) return '';
    return trimmedUserName
      ? t('speechChat.greetingWithUser', {
          userName: trimmedUserName,
          chartName,
          defaultValue:
            `${trimmedUserName}, ${chartName}'s chart is ready. What would you like to explore?`,
        })
      : t('speechChat.greetingAnonymous', {
          chartName,
          defaultValue:
            `${chartName}'s chart is ready. What would you like to explore?`,
        });
  };

  const getGreetingCacheKey = () => [
    'speech_greeting',
    SPEECH_GREETING_CACHE_VERSION,
    String(language || 'english').toLowerCase(),
    SPEECH_CHAT_TTS_PROVIDER,
    String(birthData?.id || birthData?.birth_chart_id || birthData?.name || 'chart'),
    String(userName || 'user').trim().toLowerCase() || 'user',
    hashGreetingText(buildGreetingText()),
  ].join(':');

  const formatCallTime = (seconds) => {
    const total = Math.max(0, Math.floor(Number(seconds) || 0));
    const mins = Math.floor(total / 60);
    const secs = total % 60;
    return `${mins}:${String(secs).padStart(2, '0')}`;
  };

  const playCreditWarningBeep = async () => {
    Vibration.vibrate(160);
    try {
      const uri = `${FileSystem.cacheDirectory}speech_credit_warning_beep.wav`;
      const info = await FileSystem.getInfoAsync(uri);
      if (!info?.exists) {
        await FileSystem.writeAsStringAsync(uri, CREDIT_WARNING_BEEP_BASE64, {
          encoding: FileSystem.EncodingType.Base64,
        });
      }
      const { sound } = await Audio.Sound.createAsync({ uri }, { shouldPlay: true, volume: 1.0 });
      setTimeout(() => sound.unloadAsync().catch(() => {}), 900);
    } catch (error) {
      logSpeechDebug('creditWarning.beepFailed', { message: error?.message });
    }
  };

  const endSpeechBillingSession = async (reason = 'ended') => {
    const current = billingSessionRef.current;
    if (!current?.session_id || billingEndingRef.current) return null;
    billingEndingRef.current = true;
    if (billingTimerRef.current) {
      clearInterval(billingTimerRef.current);
      billingTimerRef.current = null;
    }
    try {
      const res = await creditAPI.endSpeechSession(current.session_id, reason);
      logSpeechDebug('billing.end', res?.data || {});
      return res?.data || null;
    } catch (error) {
      logSpeechDebug('billing.endFailed', {
        reason,
        status: error?.response?.status,
        detail: error?.response?.data?.detail || error?.message,
      });
      return null;
    } finally {
      billingEndingRef.current = false;
      billingSessionRef.current = null;
      setBillingSession(null);
    }
  };

  const stopSpeechForCreditFinish = async () => {
    logSpeechDebug('billing.creditFinished', {
      elapsedSeconds: callElapsedSeconds,
      sessionId: billingSessionRef.current?.session_id,
    });
    stopSpeechUiImmediately();
    releaseSpeechRecognizer();
    setStatus('idle');
    setErrorText(t('speechChat.creditFinished', 'Speech chat ended because your available talk credits finished.'));
    await endSpeechBillingSession('credit_finished');
  };

  const startSpeechBillingSession = async () => {
    if (billingSessionRef.current?.session_id) return true;
    try {
      const res = await creditAPI.startSpeechSession();
      const data = res?.data || {};
      billingSessionRef.current = data;
      billingStartMsRef.current = Date.now();
      lastCreditWarningBeepRef.current = 0;
      setBillingSession(data);
      setCallElapsedSeconds(0);
      setCallRemainingSeconds(Number(data.max_seconds || 0) || null);
      logSpeechDebug('billing.start', data);
      if (billingTimerRef.current) clearInterval(billingTimerRef.current);
      billingTimerRef.current = setInterval(() => {
        const currentSession = billingSessionRef.current;
        if (!currentSession?.session_id || !billingStartMsRef.current) return;
        const elapsed = Math.max(0, Math.floor((Date.now() - billingStartMsRef.current) / 1000));
        const maxSeconds = Number(currentSession.max_seconds || 0);
        const remaining = maxSeconds > 0 ? Math.max(0, maxSeconds - elapsed) : null;
        setCallElapsedSeconds(elapsed);
        setCallRemainingSeconds(remaining);
        if (
          remaining != null
          && remaining > 0
          && remaining <= SPEECH_CREDIT_WARNING_SECONDS
          && elapsed - lastCreditWarningBeepRef.current >= SPEECH_CREDIT_WARNING_INTERVAL_SECONDS
        ) {
          lastCreditWarningBeepRef.current = elapsed;
          playCreditWarningBeep();
        }
        if (remaining === 0) {
          stopSpeechForCreditFinish();
        }
      }, 1000);
      return true;
    } catch (error) {
      greetedRef.current = true;
      const detail = error?.response?.data?.detail;
      const required = detail?.required_credits;
      const balance = detail?.balance;
      const perMinute = detail?.per_minute_cost || speechPerMinuteCost || 1;
      const message = detail?.message
        || `Speech chat needs at least ${SPEECH_BILLING_MIN_START_MINUTES * perMinute} credits to start.`;
      Alert.alert(
        t('credits.insufficient', 'Insufficient Credits'),
        required != null && balance != null
          ? `${message}\n\nBalance: ${balance} credits`
          : message,
        [
          { text: t('speechChat.cancel', 'Cancel'), style: 'cancel', onPress: () => navigation.goBack() },
          { text: t('credits.buyCredits', 'Buy Credits'), onPress: () => navigation.navigate('Credits') },
        ]
      );
      setErrorText(message);
      logSpeechDebug('billing.startFailed', {
        status: error?.response?.status,
        detail,
      });
      return false;
    }
  };

  useEffect(() => {
    mountedRef.current = true;
    const subscription = speechRecognition.addPartialListener((partial) => {
      const next = String(partial || '').trim();
      if (!next || !mountedRef.current) return;
      latestNativeTranscriptRef.current = next;
      nativeNoSpeechRetryCountRef.current = 0;
      setNativeRecognizerReady(true);
      setNativeRecognizerPhase('ready');
      setCurrentTranscript(next);
      if (listeningModeRef.current === 'native' && statusRef.current === 'listening') {
        scheduleNativePartialSubmit();
      }
    });
    const debugSubscription = speechRecognition.addDebugListener?.((event) => {
      logSpeechDebug('nativeRecognizer', event || {});
      const eventName = String(event?.event || '');
      if (['onReadyForSpeech', 'onBeginningOfSpeech', 'onPartialResults'].includes(eventName)) {
        if (mountedRef.current) setNativeRecognizerReady(true);
        if (mountedRef.current) setNativeRecognizerPhase('ready');
        if (nativeReadyTimerRef.current) {
          clearTimeout(nativeReadyTimerRef.current);
          nativeReadyTimerRef.current = null;
        }
      }
      if (['onResults', 'onError', 'resolveWithLatestTranscript', 'resolveBlankMaxListening', 'cancelListening'].includes(eventName)) {
        if (mountedRef.current) setNativeRecognizerReady(false);
        if (mountedRef.current) setNativeRecognizerPhase('idle');
      }
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
    // Speech chat uses Tara's Google voice; greeting audio is prefetched and cached.
    getTextToSpeech().setSpeechProvider(SPEECH_CHAT_TTS_PROVIDER);

    let cancelledPricing = false;
    (async () => {
      try {
        const res = await pricingAPI.getPricing();
        const pricing = res?.data?.pricing || {};
        const sc = pricing.speech_chat != null ? Number(pricing.speech_chat) : null;
        const ic = pricing.instant_chat != null ? Number(pricing.instant_chat) : null;
        const pm = pricing.speech_chat_per_minute != null ? Number(pricing.speech_chat_per_minute) : null;
        const val =
          sc != null && !Number.isNaN(sc) && sc > 0
            ? sc
            : ic != null && !Number.isNaN(ic) && ic > 0
              ? ic
              : 1;
        const configuredSpeechTtsProvider =
          String(res?.data?.features?.speech_tts_provider || '').trim().toLowerCase() || null;
        const nextSpeechProvider = SPEECH_CHAT_TTS_PROVIDER;
        console.log('[SpeechChat] pricing/features resolved', {
          speechChatCost: val,
          speechPerMinuteCost: pm,
          configuredSpeechTtsProvider,
          speechTtsProvider: nextSpeechProvider,
          rawFeatures: res?.data?.features || null,
        });
        getTextToSpeech().setSpeechProvider(nextSpeechProvider);
        if (!cancelledPricing && mountedRef.current) {
          setSpeechChatCost(val);
          setSpeechPerMinuteCost(pm != null && !Number.isNaN(pm) && pm > 0 ? pm : 1);
          setSpeechTtsProvider(nextSpeechProvider);
          setSpeechTtsReady(true);
        }
      } catch {
        getTextToSpeech().setSpeechProvider(SPEECH_CHAT_TTS_PROVIDER);
        if (!cancelledPricing && mountedRef.current) {
          setSpeechChatCost(1);
          setSpeechTtsProvider(SPEECH_CHAT_TTS_PROVIDER);
          setSpeechTtsReady(true);
        }
      }
    })();

    return () => {
      cancelledPricing = true;
      mountedRef.current = false;
      subscription?.remove?.();
      debugSubscription?.remove?.();
      try {
        speechRecognition.cancelListening();
      } catch {
        // ignore teardown errors
      }
      clearNativeListeningTimers();
      handsFreeRestartRef.current = false;
      startListeningInFlightRef.current = false;
      speechSocketPendingTurnsRef.current.forEach((pending) => {
        pending.reject?.(new Error('Speech socket closed'));
      });
      speechSocketPendingTurnsRef.current.clear();
      speechSocketRef.current?.close?.();
      speechSocketRef.current = null;
      speechSocketConnectPromiseRef.current = null;
      if (speakingWatchdogRef.current) {
        clearTimeout(speakingWatchdogRef.current);
        speakingWatchdogRef.current = null;
      }
      if (billingTimerRef.current) {
        clearInterval(billingTimerRef.current);
        billingTimerRef.current = null;
      }
      if (billingSessionRef.current?.session_id) {
        creditAPI.endSpeechSession(billingSessionRef.current.session_id, 'screen_unmount').catch(() => {});
        billingSessionRef.current = null;
      }
      setAvatarSpeech({ active: false, text: '', timeline: [], positionMs: 0, durationMs: 0, audioStarted: false });
      getTextToSpeech().stop();
    };
  }, []);

  useEffect(() => {
    getTextToSpeech().setSpeechProvider(speechTtsProvider);
  }, [speechTtsProvider]);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    if (status !== 'listening' || !handsFreeEnabled) return undefined;
    const timer = setInterval(() => {
      if (!mountedRef.current || statusRef.current !== 'listening') return;
      const staleBackendListening =
        listeningModeRef.current === 'backend' && !recordingRef.current;
      const staleAndroidListening =
        Platform.OS === 'android' && !listeningModeRef.current && !recordingRef.current;
      if ((staleBackendListening || staleAndroidListening) && !startListeningInFlightRef.current) {
        logSpeechDebug('backendRecording.staleListeningWithoutRecorder', {
          listeningMode: listeningModeRef.current,
        });
        startListening({ source: 'staleListeningRecovery', stopCurrentSpeech: false }).catch((error) => {
          logSpeechDebug('backendRecording.staleListeningRecoveryError', {
            message: error?.message,
            status: error?.response?.status,
          });
        });
      }
    }, 700);
    return () => clearInterval(timer);
  }, [handsFreeEnabled, status]);

  useEffect(() => {
    if (speakingWatchdogRef.current) {
      clearTimeout(speakingWatchdogRef.current);
      speakingWatchdogRef.current = null;
    }
    // Do not auto-release speaking based on estimated duration. With segmented
    // remote TTS, synthesis/playback gaps can make estimates finish before the
    // final audio segment. Hands-free listening must restart only from TTS onDone.
    return () => {
      if (speakingWatchdogRef.current) {
        clearTimeout(speakingWatchdogRef.current);
        speakingWatchdogRef.current = null;
      }
    };
  }, [status]);

  useEffect(() => {
    handsFreeEnabledRef.current = handsFreeEnabled;
  }, [handsFreeEnabled]);

  useEffect(() => {
    if (!currentTranscript) return undefined;
    const timer = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 80);
    return () => clearTimeout(timer);
  }, [currentTranscript]);

  useEffect(() => {
    pulseAnim.stopAnimation();
    if (status === 'listening' || status === 'speaking') {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1, duration: 1300, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 0, duration: 1300, useNativeDriver: true }),
        ])
      ).start();
      return;
    }

    if (status === 'thinking' || status === 'transcribing') {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 0.6, duration: 1200, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 0.1, duration: 1200, useNativeDriver: true }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(0);
    }
  }, [pulseAnim, status]);

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
    const loops = sparkleAnims.map((anim, index) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(index * 320),
          Animated.timing(anim, {
            toValue: 1,
            duration: 3600 + index * 220,
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0,
            duration: 0,
            useNativeDriver: true,
          }),
        ])
      )
    );

    loops.forEach((loop) => loop.start());

    return () => {
      loops.forEach((loop) => loop.stop());
      sparkleAnims.forEach((anim) => anim.stopAnimation());
    };
  }, [sparkleAnims]);

  useEffect(() => {
    greetedRef.current = false;
    greetingPrefetchKeyRef.current = '';
  }, [birthData?.id]);

  useEffect(() => {
    if (!birthData?.name || !speechTtsReady) return;
    const greeting = buildGreetingText();
    if (!greeting) return;
    const cacheKey = getGreetingCacheKey();
    if (greetingPrefetchKeyRef.current === cacheKey) return;
    greetingPrefetchKeyRef.current = cacheKey;
    getTextToSpeech().prefetchServerTts(greeting, {
      language,
      cacheKey,
      prepareSpoken: false,
    }).then((result) => {
      if (!mountedRef.current) return;
      logSpeechDebug('greeting.prefetched', {
        cacheKey,
        cached: Boolean(result?.cached),
        uri: result?.uri || null,
      });
    });
  }, [birthData?.id, birthData?.name, language, speechTtsReady, userName, t]);

  useEffect(() => {
    if (greetedRef.current || !birthData?.name || status !== 'idle') return;
    if (!speechTtsReady) return;

    const greet = async () => {
      const billingOk = await startSpeechBillingSession();
      if (!billingOk || !mountedRef.current) return;
      greetedRef.current = true;
      const greeting = buildGreetingText();
      const cacheKey = getGreetingCacheKey();
      setStatus('speaking');
      await speakWithAvatar(greeting, {
        language,
        provider: SPEECH_CHAT_TTS_PROVIDER,
        cacheKey,
        prepareSpoken: false,
        onDone: () => {
          if (!mountedRef.current) return;
          if (handsFreeEnabledRef.current) {
            maybeStartAfterGreeting();
            return;
          }
          setStatus('idle');
        },
        onError: () => mountedRef.current && setStatus('idle'),
      });
    };

    greet();
  }, [birthData?.name, language, speechTtsReady, status, t, userName, speechPerMinuteCost]);

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

  const clearNativeListeningTimers = () => {
    if (nativePartialStableTimerRef.current) {
      clearTimeout(nativePartialStableTimerRef.current);
      nativePartialStableTimerRef.current = null;
    }
    if (nativeMaxListenTimerRef.current) {
      clearTimeout(nativeMaxListenTimerRef.current);
      nativeMaxListenTimerRef.current = null;
    }
    if (nativeReadyTimerRef.current) {
      clearTimeout(nativeReadyTimerRef.current);
      nativeReadyTimerRef.current = null;
    }
  };

  const scheduleNativePartialSubmit = () => {
    if (nativePartialStableTimerRef.current) {
      clearTimeout(nativePartialStableTimerRef.current);
      nativePartialStableTimerRef.current = null;
    }
    nativePartialStableTimerRef.current = setTimeout(() => {
      nativePartialStableTimerRef.current = null;
      if (
        !mountedRef.current
        || listeningModeRef.current !== 'native'
        || statusRef.current !== 'listening'
        || !latestNativeTranscriptRef.current.trim()
      ) {
        return;
      }
      logSpeechDebug('nativeRecognition.partialStableStop', {
        transcript: latestNativeTranscriptRef.current,
      });
      try {
        setStatus('transcribing');
        speechRecognition.stopListening();
      } catch (error) {
        logSpeechDebug('nativeRecognition.partialStableStopError', {
          message: error?.message,
          code: error?.code,
        });
      }
    }, NATIVE_PARTIAL_STABLE_SUBMIT_MS);
  };

  const shouldFallbackToBackendSpeech = (error) => {
    const code = String(error?.code || '');
    const message = String(error?.message || '');
    return ALLOW_NATIVE_RUNTIME_BACKEND_FALLBACK
      && USE_BACKEND_SPEECH_TRANSCRIPTION
      && !latestNativeTranscriptRef.current.trim()
      && (
        code === 'speech_error_1'
        || code === 'speech_error_2'
        || code === 'speech_error_4'
        || code === 'speech_error_5'
        || code === 'speech_error_7'
        || code === 'speech_error_11'
        || /network|server|client|service|understand/i.test(message)
      );
  };

  const startListening = async ({ source = 'manual', stopCurrentSpeech = true } = {}) => {
    if (startListeningInFlightRef.current) {
      await logSpeechDebug('startListening.skipInFlight', { source, status });
      return;
    }
    if (recordingRef.current || listeningModeRef.current === 'backend') {
      await logSpeechDebug('startListening.skipAlreadyRecording', { source, status });
      setStatus('listening');
      return;
    }
    if (!birthData) {
      Alert.alert(
        t('speechChat.profileRequired', 'Birth chart required'),
        t('speechChat.profileRequiredBody', 'Please select or create a birth chart before using speech chat.')
      );
      return;
    }

    startListeningInFlightRef.current = true;
    try {
      await logSpeechDebug('startListening.begin', { source, status, stopCurrentSpeech });
      setNativeRecognizerReady(false);
      setNativeRecognizerPhase('starting');
      setErrorText('');
      setCurrentTranscript('');
      setFollowUps([]);
      if (source !== 'nativeRetryAfterNoSpeech') {
        nativeNoSpeechRetryCountRef.current = 0;
      }
      handsFreeRestartRef.current = false;
      setAvatarSpeech({ active: false, text: '', timeline: [], positionMs: 0, durationMs: 0, audioStarted: false });
      if (stopCurrentSpeech) {
        await getTextToSpeech().stop();
      }

      const permissionGranted = await ensureMicrophonePermission();
      if (!permissionGranted) return;

      let useBackendTranscription = USE_BACKEND_SPEECH_TRANSCRIPTION;
      if (PREFER_NATIVE_SPEECH_RECOGNITION) {
        if (nativeSpeechUnavailableForSessionRef.current) {
          useBackendTranscription = true;
          await logSpeechDebug('startListening.nativeSkippedForSession', {
            source,
            reason: 'previous_native_runtime_failure',
          });
        } else {
          try {
            const nativeAvailable = await speechRecognition.isAvailable();
            useBackendTranscription = !nativeAvailable;
            await logSpeechDebug('startListening.nativePreference', {
              nativeAvailable,
              useBackendTranscription,
            });
            if (!nativeAvailable && REQUIRE_NATIVE_SPEECH_FOR_WEBSOCKET) {
              throw new Error(
                t(
                  'speechChat.nativeSpeechRequired',
                  'Voice chat needs the native speech recognizer in this Android build. Rebuild/reinstall the development app, or test on a device with Google Speech Services enabled.'
                )
              );
            }
          } catch (nativeAvailabilityError) {
            await logSpeechDebug('startListening.nativePreferenceFallback', {
              message: nativeAvailabilityError?.message,
              code: nativeAvailabilityError?.code,
            });
            if (REQUIRE_NATIVE_SPEECH_FOR_WEBSOCKET) {
              throw nativeAvailabilityError;
            }
            useBackendTranscription = true;
          }
        }
      }

      if (useBackendTranscription) {
        await logSpeechDebug('startListening.backendTranscription', {
          platform: route?.params?.platform || 'native',
          language,
        });
        await startBackendRecording();
        return;
      }

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
        throw new Error(
          t(
            'speechChat.devNativeUnavailable',
            'Speech recognition is not available in this emulator/build right now.'
          )
        );
      }

      await logSpeechDebug('startListening.request', {
        platform: route?.params?.platform || 'native',
        language,
        normalizedLanguage: normalizeLanguageCode(language),
      });

      setStatus('listening');
      listeningModeRef.current = 'native';
      latestNativeTranscriptRef.current = '';
      clearNativeListeningTimers();
      nativeReadyTimerRef.current = setTimeout(() => {
        nativeReadyTimerRef.current = null;
        if (!mountedRef.current || listeningModeRef.current !== 'native' || statusRef.current !== 'listening') {
          return;
        }
        logSpeechDebug('nativeRecognition.readyTimeout', {
          source,
          transcript: latestNativeTranscriptRef.current,
        });
        setNativeRecognizerReady(false);
        setNativeRecognizerPhase('idle');
        setErrorText(t(
          'speechChat.recognizerNotReady',
          'I could not start Android speech recognition. Please tap the mic again, or rebuild/reinstall the app if this keeps happening.'
        ));
        try {
          speechRecognition.cancelListening();
        } catch (error) {
          logSpeechDebug('nativeRecognition.readyTimeoutCancelError', {
            message: error?.message,
            code: error?.code,
          });
        }
      }, NATIVE_READY_TIMEOUT_MS);
      nativeMaxListenTimerRef.current = setTimeout(() => {
        nativeMaxListenTimerRef.current = null;
        if (!mountedRef.current || listeningModeRef.current !== 'native' || statusRef.current !== 'listening') {
          return;
        }
        logSpeechDebug('nativeRecognition.maxListenStop', {
          transcript: latestNativeTranscriptRef.current,
        });
        try {
          setStatus('transcribing');
          speechRecognition.stopListening();
        } catch (error) {
          logSpeechDebug('nativeRecognition.maxListenStopError', {
            message: error?.message,
            code: error?.code,
          });
        }
      }, NATIVE_MAX_LISTENING_MS);

      speechRecognition.startListening(normalizeLanguageCode(language))
        .then(async (transcript) => {
          clearNativeListeningTimers();
          listeningModeRef.current = null;
          setNativeRecognizerReady(false);
          setNativeRecognizerPhase('idle');
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
          await runQuestionTurn(finalTranscript);
        })
        .catch(async (error) => {
          clearNativeListeningTimers();
          listeningModeRef.current = null;
          setNativeRecognizerReady(false);
          setNativeRecognizerPhase('idle');
          await logSpeechDebug('startListening.error', {
            message: error?.message,
            code: error?.code,
          });
          if (!mountedRef.current) return;
          if (error?.code === 'cancelled') {
            setStatus('idle');
            return;
          }
          if (shouldFallbackToBackendSpeech(error)) {
            await logSpeechDebug('startListening.nativeRuntimeFallbackToBackend', {
              source,
              code: error?.code,
              message: error?.message,
            });
            setCurrentTranscript('');
            setErrorText('');
            try {
              await startBackendRecording();
            } catch (fallbackError) {
              if (!mountedRef.current) return;
              setErrorText(fallbackError?.message || t('speechChat.genericError', 'Something went wrong. Please try again.'));
              setStatus('idle');
            }
            return;
          }
          const shouldKeepListening =
            handsFreeEnabledRef.current
            && (error?.code === 'speech_error_6'
              || error?.code === 'speech_error_8'
              || error?.code === 'no_speech'
              || /no speech|timeout/i.test(String(error?.message || '')));
          if (shouldKeepListening && nativeNoSpeechRetryCountRef.current < MAX_NATIVE_NO_SPEECH_RETRIES) {
            nativeNoSpeechRetryCountRef.current += 1;
            setCurrentTranscript('');
            setTimeout(() => {
              if (mountedRef.current && handsFreeEnabledRef.current) {
                startListening({ source: 'nativeRetryAfterNoSpeech', stopCurrentSpeech: false }).catch((retryError) => {
                  if (!mountedRef.current) return;
                  setErrorText(retryError?.message || t('speechChat.genericError', 'Something went wrong. Please try again.'));
                  setStatus('idle');
                });
              }
            }, 320);
            return;
          }
          nativeNoSpeechRetryCountRef.current = 0;
          setErrorText(error?.message || t('speechChat.noTranscript', 'I could not understand that. Please try again.'));
          setStatus('idle');
        });
    } finally {
      startListeningInFlightRef.current = false;
    }
  };

  const stopListening = async () => {
    await logSpeechDebug('stopListening.request', {
      currentTranscript,
      listeningMode: listeningModeRef.current,
    });
    handsFreeRestartRef.current = false;
    if (recordingAutoStopTimerRef.current) {
      clearTimeout(recordingAutoStopTimerRef.current);
      recordingAutoStopTimerRef.current = null;
    }
    clearNativeListeningTimers();
    setNativeRecognizerReady(false);
    setNativeRecognizerPhase('idle');
    if (listeningModeRef.current === 'backend') {
      try {
        await stopBackendRecordingAndTranscribe();
      } catch (error) {
        if (!mountedRef.current) return;
        setErrorText(error?.response?.data?.detail || error?.message || t('speechChat.noTranscript', 'I could not understand that. Please try again.'));
        setStatus('idle');
      }
      return;
    }
    setStatus('transcribing');
    speechRecognition.stopListening();
  };

  const maybeRestartHandsFree = async () => {
    if (!mountedRef.current || !handsFreeEnabledRef.current) return;
    handsFreeRestartRef.current = false;
    setErrorText('');
    try {
      await wait(POST_TTS_LISTEN_DELAY_MS);
      await startListening({ source: 'handsFreeAfterAnswer', stopCurrentSpeech: false });
    } catch (error) {
      if (!mountedRef.current) return;
      setErrorText(error?.message || t('speechChat.genericError', 'Something went wrong. Please try again.'));
      setStatus('idle');
      if (handsFreeEnabledRef.current) {
        setTimeout(() => {
          if (mountedRef.current && handsFreeEnabledRef.current && !recordingRef.current && !startListeningInFlightRef.current) {
            startListening({ source: 'handsFreeRetryAfterError', stopCurrentSpeech: false }).catch(() => {});
          }
        }, 450);
      }
    }
  };

  const maybeStartAfterGreeting = async () => {
    if (!mountedRef.current || !handsFreeEnabledRef.current) return;
    setErrorText('');
    try {
      await wait(POST_TTS_LISTEN_DELAY_MS);
      await startListening({ source: 'handsFreeAfterGreeting', stopCurrentSpeech: false });
    } catch (error) {
      if (!mountedRef.current) return;
      setErrorText(error?.message || t('speechChat.genericError', 'Something went wrong. Please try again.'));
      setStatus('idle');
    }
  };

  const getGuideLines = async (scene, extra = {}) => {
    try {
      const response = await speechAPI.getGuideLines({
        scene,
        language,
        userName: userName || null,
        chartName: birthData?.name || null,
        handsFree: handsFreeEnabled,
        ...extra,
      });
      return Array.isArray(response?.data?.lines)
        ? response.data.lines.map((item) => String(item || '').trim()).filter(Boolean)
        : [];
    } catch (error) {
      console.log('[SpeechChat] guide lines fallback', {
        scene,
        message: error?.message || String(error),
      });
      return [];
    }
  };

  const releaseSpeechRecognizer = () => {
    if (recordingMeterTimerRef.current) {
      clearInterval(recordingMeterTimerRef.current);
      recordingMeterTimerRef.current = null;
    }
    if (recordingAutoStopTimerRef.current) {
      clearTimeout(recordingAutoStopTimerRef.current);
      recordingAutoStopTimerRef.current = null;
    }
    clearNativeListeningTimers();
    setNativeRecognizerReady(false);
    setNativeRecognizerPhase('idle');
    recordingAutoStoppingRef.current = false;
    recordingStartedAtRef.current = 0;
    recordingSpeechDetectedRef.current = false;
    recordingLastSpeechAtRef.current = 0;
    const recording = recordingRef.current;
    recordingRef.current = null;
    listeningModeRef.current = null;
    if (recording) {
      recording.stopAndUnloadAsync?.().catch?.(() => {});
    }
    try {
      speechRecognition.cancelListening();
    } catch {
      // Ignore cleanup failures; recognizer may already be inactive.
    }
  };

  const speakWithAvatar = async (
    text,
    {
      onDone,
      onError,
      ...ttsOptions
    } = {}
  ) => {
    const spoken = String(text || '').trim();
    if (!spoken) return;
    const estimatedDurationMs = estimateSpeechDurationMs(spoken);

    setAvatarSpeech({
      active: true,
      text: spoken,
      timeline: [],
      positionMs: 0,
      durationMs: estimatedDurationMs,
      audioStarted: false,
    });
    console.log('[SpeechChat] speakWithAvatar', {
      provider: getTextToSpeech().getSpeechProvider?.() || 'unknown',
      language,
      textLength: spoken.length,
      preview: spoken.slice(0, 80),
    });
    try {
      await getTextToSpeech().speak(spoken, {
        segmented: spoken.length > 280,
        ...ttsOptions,
        onStart: () => {
          if (!mountedRef.current) return;
          setAvatarSpeech((prev) => ({
            ...prev,
            durationMs: Number(prev.durationMs || 0) || estimatedDurationMs,
            audioStarted: true,
          }));
          if (ttsOptions.onStart) ttsOptions.onStart();
        },
        onDone: () => {
          if (mountedRef.current) {
            setAvatarSpeech({ active: false, text: '', timeline: [], positionMs: 0, durationMs: 0, audioStarted: false });
          }
          if (onDone) onDone();
        },
        onError: (e) => {
          if (mountedRef.current) {
            setAvatarSpeech({ active: false, text: '', timeline: [], positionMs: 0, durationMs: 0, audioStarted: false });
          }
          if (onError) onError(e);
        },
      });
    } catch (error) {
      if (mountedRef.current) {
        setAvatarSpeech({ active: false, text: '', timeline: [], positionMs: 0, durationMs: 0, audioStarted: false });
      }
      if (onError) onError(error);
    }
  };

  /** Brief natural line when recognition is done so the jump to “thinking” is not silent. */
  const speakThinkingHandoff = async () => {
    if (!mountedRef.current) return;
    releaseSpeechRecognizer();
    const i = thinkingLeadInIndexRef.current % THINKING_HANDOFF_KEYS.length;
    thinkingLeadInIndexRef.current += 1;
    const phrase = t(THINKING_HANDOFF_KEYS[i], THINKING_HANDOFF_DEFAULTS[i]);
    try {
      await speakWithAvatar(phrase, { language });
    } catch {
      // ignore short transition TTS failures
    }
  };

  const startBackendRecording = async () => {
    const permission = await Audio.requestPermissionsAsync();
    if (permission?.status !== 'granted') {
      throw new Error(t('speechChat.micPermissionBody', 'Please allow microphone access so AstroRoshni can hear your question.'));
    }

    await Audio.setAudioModeAsync({
      allowsRecordingIOS: true,
      playsInSilentModeIOS: true,
      staysActiveInBackground: false,
      interruptionModeIOS: InterruptionModeIOS.DoNotMix,
      interruptionModeAndroid: InterruptionModeAndroid.DoNotMix,
      shouldDuckAndroid: false,
      playThroughEarpieceAndroid: false,
    });

    recordingMeterSamplesRef.current = [];
    recordingAutoStoppingRef.current = false;
    recordingStartedAtRef.current = Date.now();
    recordingSpeechDetectedRef.current = false;
    recordingSpeechFirstDetectedAtRef.current = 0;
    recordingSpeechSampleCountRef.current = 0;
    recordingLastSpeechAtRef.current = 0;
    const { recording } = await Audio.Recording.createAsync(SPEECH_RECORDING_OPTIONS);
    const stopBackendFromTimer = (reason) => {
      if (!recordingRef.current || recordingAutoStoppingRef.current) return;
      recordingAutoStoppingRef.current = true;
      setStatus('transcribing');
      logSpeechDebug('backendRecording.autoStop', {
        reason,
        elapsedMs: Date.now() - recordingStartedAtRef.current,
        speechDetected: recordingSpeechDetectedRef.current,
        samples: recordingMeterSamplesRef.current?.length || 0,
      });
      stopBackendRecordingAndTranscribe().catch((error) => {
        if (!mountedRef.current) return;
        const detail = error?.response?.data?.detail || error?.message || '';
        logSpeechDebug('backendRecording.autoStopError', {
          message: error?.message,
          status: error?.response?.status,
          detail: error?.response?.data?.detail,
        });
        if (handsFreeEnabledRef.current) {
          setErrorText('');
          setCurrentTranscript('');
          setTimeout(() => {
            if (mountedRef.current && handsFreeEnabledRef.current && !recordingRef.current) {
              startListening({ source: 'backendRetryAfterNoSpeech', stopCurrentSpeech: false }).catch((retryError) => {
                if (!mountedRef.current) return;
                logSpeechDebug('backendRecording.retryError', {
                  message: retryError?.message,
                  status: retryError?.response?.status,
                });
                setStatus('idle');
              });
            }
          }, /no speech|understand|audio/i.test(String(detail)) ? 1100 : 1400);
          return;
        }
        setErrorText(detail || t('speechChat.noTranscript', 'I could not understand that. Please try again.'));
        setStatus('idle');
      });
    };
    const handleBackendRecordingStatus = (recStatus, source) => {
      if (!recordingRef.current || recordingAutoStoppingRef.current || !recStatus) return false;
      if (recStatus.isRecording === false) {
        logSpeechDebug('backendRecording.nativeStopped', {
          source,
          canRecord: recStatus?.canRecord,
          durationMs: recStatus?.durationMillis,
          speechDetected: recordingSpeechDetectedRef.current,
        });
        stopBackendFromTimer(
          recordingSpeechDetectedRef.current ? 'native_stopped_after_speech' : 'native_stopped_before_speech'
        );
        return true;
      }
      return false;
    };
    recordingRef.current = recording;
    listeningModeRef.current = 'backend';
    recording.setOnRecordingStatusUpdate?.((recStatus) => {
      handleBackendRecordingStatus(recStatus, 'status_update');
    });
    recording.setProgressUpdateInterval?.(180);
    await logSpeechDebug('backendRecording.started', {
      handsFree: handsFreeEnabledRef.current,
      autoStopMs: handsFreeEnabledRef.current ? HANDS_FREE_AUTO_STOP_MS : null,
      silenceStopMs: handsFreeEnabledRef.current ? BACKEND_RECORDING_SILENCE_STOP_MS : null,
      longSilenceStopMs: handsFreeEnabledRef.current ? BACKEND_RECORDING_LONG_SILENCE_STOP_MS : null,
      speechThresholdDb: BACKEND_RECORDING_SPEECH_THRESHOLD_DB,
      stopMode: handsFreeEnabledRef.current ? 'wait_for_speech_then_silence' : 'manual',
    });
    recordingMeterTimerRef.current = setInterval(() => {
      recording.getStatusAsync()
        .then((recStatus) => {
          if (!recordingRef.current || recordingAutoStoppingRef.current) return;
          if (handleBackendRecordingStatus(recStatus, 'poll')) return;
          const now = Date.now();
          const elapsedMs = now - recordingStartedAtRef.current;
          const metering = Number(recStatus?.metering);
          if (Number.isFinite(metering)) {
            recordingMeterSamplesRef.current.push(metering);
            if (recordingMeterSamplesRef.current.length > 80) {
              recordingMeterSamplesRef.current = recordingMeterSamplesRef.current.slice(-80);
            }
            const echoGuardActive = elapsedMs < POST_TTS_ECHO_GUARD_MS;
            if (metering >= BACKEND_RECORDING_SPEECH_THRESHOLD_DB && !echoGuardActive) {
              recordingSpeechSampleCountRef.current += 1;
              if (!recordingSpeechFirstDetectedAtRef.current) {
                recordingSpeechFirstDetectedAtRef.current = now;
              }
              if (!recordingSpeechDetectedRef.current && recordingSpeechSampleCountRef.current >= 2) {
                logSpeechDebug('backendRecording.speechDetected', { elapsedMs, metering });
                recordingSpeechDetectedRef.current = true;
              }
              recordingLastSpeechAtRef.current = now;
            }
          }
          if (
            handsFreeEnabledRef.current
            && recordingSpeechDetectedRef.current
            && elapsedMs >= BACKEND_RECORDING_MIN_MS
          ) {
            const speechRunMs = recordingSpeechFirstDetectedAtRef.current
              ? now - recordingSpeechFirstDetectedAtRef.current
              : elapsedMs;
            const silenceStopMs = speechRunMs >= BACKEND_RECORDING_LONG_QUESTION_AFTER_MS
              ? BACKEND_RECORDING_LONG_SILENCE_STOP_MS
              : BACKEND_RECORDING_SILENCE_STOP_MS;
            if (now - recordingLastSpeechAtRef.current >= silenceStopMs) {
              stopBackendFromTimer(
                silenceStopMs === BACKEND_RECORDING_LONG_SILENCE_STOP_MS
                  ? 'long_silence_after_speech'
                  : 'silence_after_speech'
              );
            }
          }
        })
        .catch(() => {});
    }, 180);
    if (handsFreeEnabledRef.current) {
      recordingAutoStopTimerRef.current = setTimeout(() => {
        stopBackendFromTimer('max_duration');
      }, HANDS_FREE_AUTO_STOP_MS);
    }
    setStatus('listening');
  };

  const stopBackendRecordingAndTranscribe = async () => {
    const recording = recordingRef.current;
    recordingRef.current = null;
    listeningModeRef.current = null;
    if (!recording) return;

    setStatus('transcribing');
    if (recordingMeterTimerRef.current) {
      clearInterval(recordingMeterTimerRef.current);
      recordingMeterTimerRef.current = null;
    }
    if (recordingAutoStopTimerRef.current) {
      clearTimeout(recordingAutoStopTimerRef.current);
      recordingAutoStopTimerRef.current = null;
    }
    let durationMs = 0;
    const meterSamples = recordingMeterSamplesRef.current || [];
    recordingMeterSamplesRef.current = [];
    recordingAutoStoppingRef.current = false;
    recordingStartedAtRef.current = 0;
    const speechDetected = recordingSpeechDetectedRef.current;
    const speechSampleCount = recordingSpeechSampleCountRef.current;
    recordingSpeechDetectedRef.current = false;
    recordingSpeechFirstDetectedAtRef.current = 0;
    recordingSpeechSampleCountRef.current = 0;
    recordingLastSpeechAtRef.current = 0;
    const meteringMax = meterSamples.length ? Math.max(...meterSamples) : null;
    const meteringAvg = meterSamples.length
      ? meterSamples.reduce((sum, value) => sum + value, 0) / meterSamples.length
      : null;
    try {
      const statusBeforeStop = await recording.getStatusAsync();
      durationMs = Number(statusBeforeStop?.durationMillis || 0);
      await logSpeechDebug('backendRecording.statusBeforeStop', {
        durationMs,
        isRecording: Boolean(statusBeforeStop?.isRecording),
        canRecord: Boolean(statusBeforeStop?.canRecord),
        metering: statusBeforeStop?.metering,
        meteringMax,
        meteringAvg,
        meterSamples: meterSamples.length,
        speechDetected,
        speechSampleCount,
      });
    } catch (statusError) {
      await logSpeechDebug('backendRecording.statusBeforeStopError', {
        message: statusError?.message,
      });
    }
    await recording.stopAndUnloadAsync();
    const uri = recording.getURI();
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: false,
      playsInSilentModeIOS: true,
      staysActiveInBackground: false,
      interruptionModeIOS: InterruptionModeIOS.DoNotMix,
      interruptionModeAndroid: InterruptionModeAndroid.DoNotMix,
      shouldDuckAndroid: false,
      playThroughEarpieceAndroid: false,
    });
    if (!uri) {
      throw new Error(t('speechChat.recordingError', 'Recording failed. Please try again.'));
    }

    if (durationMs > 0 && durationMs < 700) {
      throw new Error(t('speechChat.recordingTooShort', 'I only caught a tiny bit of audio. Please hold the mic a moment longer and try again.'));
    }

    await logSpeechDebug('backendTranscribe.request', { uri, language, durationMs, meteringMax, meteringAvg });
    let response;
    try {
      response = await speechAPI.transcribeAudio(
        {
          uri,
          name: `speech-question-${Date.now()}.m4a`,
          type: Platform.OS === 'android' ? 'audio/mp4' : 'audio/mp4',
        },
        language || 'english',
        { durationMs, meteringMax, meteringAvg }
      );
    } catch (error) {
      await logSpeechDebug('backendTranscribe.error', {
        message: error?.message,
        status: error?.response?.status,
        detail: error?.response?.data?.detail,
      });
      throw error;
    }
    const finalTranscript = String(response?.data?.transcript || '').trim();
    await logSpeechDebug('backendTranscribe.result', { transcript: finalTranscript });
    if (!finalTranscript) {
      throw new Error(t('speechChat.noTranscript', 'I could not understand that. Please try again.'));
    }
    setCurrentTranscript(finalTranscript);
    setStatus('thinking');
    await runQuestionTurn(finalTranscript);
  };

  const playAvatarLine = async (text, options = {}) => {
    const spoken = String(text || '').trim();
    if (!spoken) return false;
    return new Promise((resolve) => {
      speakWithAvatar(spoken, {
        language,
        ...options,
        onDone: () => resolve(true),
        onError: () => resolve(false),
      });
    });
  };

  const closeSpeechSocket = () => {
    speechSocketPendingTurnsRef.current.forEach((pending) => {
      pending.reject?.(new Error('Speech socket closed'));
    });
    speechSocketPendingTurnsRef.current.clear();
    speechSocketRef.current?.close?.();
    speechSocketRef.current = null;
    speechSocketConnectPromiseRef.current = null;
  };

  const ensureSpeechSocket = async () => {
    if (speechSocketRef.current?.isOpen?.()) return speechSocketRef.current;
    if (speechSocketConnectPromiseRef.current) return speechSocketConnectPromiseRef.current;

    speechSocketConnectPromiseRef.current = new Promise(async (resolve, reject) => {
      let settled = false;
      const timeout = setTimeout(() => {
        if (settled) return;
        settled = true;
        speechSocketConnectPromiseRef.current = null;
        reject(new Error('Speech socket connection timed out'));
      }, 8000);

      try {
        const client = await speechAPI.createConversationSocket({
          onOpen: () => {
            logSpeechDebug('speechSocket.open');
          },
          onMessage: (event) => {
            logSpeechDebug('speechSocket.event', {
              type: event?.type,
              turnId: event?.turn_id,
              status: event?.status,
            });
            if (event?.type === 'ready') {
              if (!settled) {
                settled = true;
                clearTimeout(timeout);
                speechSocketRef.current = client;
                speechSocketConnectPromiseRef.current = null;
                resolve(client);
              }
              return;
            }
            if (event?.type === 'ping') {
              client.send({ type: 'pong' });
              return;
            }
            const turnId = event?.turn_id;
            const pending = turnId ? speechSocketPendingTurnsRef.current.get(turnId) : null;
            if (!pending) return;

            if (event?.type === 'answer_chunk') {
              pending.chunks.push(String(event.text || ''));
              pending.onChunk?.(String(event.text || ''), event);
              return;
            }
            if (event?.type === 'turn_completed') {
              speechSocketPendingTurnsRef.current.delete(turnId);
              pending.resolve({
                status: 'completed',
                message_id: event.message_id,
                content: String(event.content || pending.chunks.join(' ')).trim(),
                follow_up_questions: Array.isArray(event.follow_up_questions) ? event.follow_up_questions : [],
                next_action: event.next_action || null,
              });
              return;
            }
            if (event?.type === 'turn_error') {
              speechSocketPendingTurnsRef.current.delete(turnId);
              pending.reject(new Error(event.message || event.error || 'Speech turn failed'));
            }
          },
          onError: () => {
            logSpeechDebug('speechSocket.error');
          },
          onClose: (event) => {
            logSpeechDebug('speechSocket.close', {
              code: event?.code,
              reason: event?.reason,
            });
            speechSocketPendingTurnsRef.current.forEach((pending) => {
              pending.reject?.(new Error('Speech socket disconnected'));
            });
            speechSocketPendingTurnsRef.current.clear();
            speechSocketRef.current = null;
            speechSocketConnectPromiseRef.current = null;
          },
        });
      } catch (error) {
        if (!settled) {
          settled = true;
          clearTimeout(timeout);
          speechSocketConnectPromiseRef.current = null;
          reject(error);
        }
      }
    });

    return speechSocketConnectPromiseRef.current;
  };

  const askSpeechSocket = async (question, turnLanguage = language) => {
    if (!USE_SPEECH_WEBSOCKET) {
      throw new Error('Speech websocket disabled');
    }
    let activeSessionId = await ensureSession();
    if (!activeSessionId) throw new Error(t('speechChat.sessionError', 'Could not start a speech chat session.'));
    const socketClient = await ensureSpeechSocket();
    const turnId = `turn_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    const clientRequestId = `speech_ws_${Date.now()}_${Math.random().toString(36).slice(2)}`;

    return new Promise((resolve, reject) => {
      speechSocketPendingTurnsRef.current.set(turnId, {
        resolve,
        reject,
        chunks: [],
        onChunk: () => {},
      });
      const sent = socketClient.send({
        type: 'ask',
        turn_id: turnId,
        session_id: activeSessionId,
        question,
        query_context: buildQueryContext(),
        language: turnLanguage || language || 'english',
        speech_billing: false,
        native_name: birthData?.name,
        birth_details: toChatBirthDetails(birthData),
        client_request_id: clientRequestId,
      });
      if (!sent) {
        speechSocketPendingTurnsRef.current.delete(turnId);
        reject(new Error('Speech socket is not connected'));
      }
    });
  };

  const askInstant = async (question, turnLanguage = language) => {
    if (USE_SPEECH_WEBSOCKET) {
      try {
        return await askSpeechSocket(question, turnLanguage);
      } catch (socketError) {
        logSpeechDebug('speechSocket.fallbackToHttp', {
          message: socketError?.message,
        });
        closeSpeechSocket();
      }
    }
    let activeSessionId = await ensureSession();
    if (!activeSessionId) throw new Error(t('speechChat.sessionError', 'Could not start a speech chat session.'));
    const buildAskBody = (sid) => ({
      session_id: sid,
      question,
      query_context: buildQueryContext(),
      language: turnLanguage || language || 'english',
      response_style: 'concise',
      premium_analysis: false,
      chat_tier: 'instant',
      speech_chat: true,
      speech_billing: false,
      native_name: birthData?.name,
      birth_details: toChatBirthDetails(birthData),
      client_request_id: `speech_${Date.now()}_${Math.random().toString(36).slice(2)}`,
    });
    let askResponse;
    try {
      askResponse = await chatAPI.askV2(buildAskBody(activeSessionId));
    } catch (err) {
      const status = err?.response?.status;
      const detailRaw = err?.response?.data?.detail;
      const detail = typeof detailRaw === 'string' ? detailRaw : JSON.stringify(detailRaw || '');
      if (status === 409 && /session_turn_limit/i.test(detail) && birthData?.id) {
        setSessionId(null);
        const created = await chatAPI.createV2Session(birthData.id);
        const nextSid = created?.data?.session_id;
        if (!nextSid) throw err;
        setSessionId(nextSid);
        activeSessionId = nextSid;
        askResponse = await chatAPI.askV2(buildAskBody(activeSessionId));
      } else {
        throw err;
      }
    }
    const askData = askResponse?.data || {};
    if (askData.status === 'completed') {
      return askData;
    }
    if (!askData.message_id) throw new Error(t('speechChat.askError', 'Could not send your question.'));
    return await pollForAnswer(question, askData.message_id);
  };

  const pollForAnswer = async (question, messageId) => {
    for (let attempt = 0; attempt < MAX_POLLS; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
      if (!mountedRef.current) return;
      const response = await chatAPI.getMessageStatus(messageId);
      const data = response?.data || {};
      if (data.status === 'completed') {
        return data;
      }
      if (data.status === 'failed') {
        throw new Error(data.error_message || t('speechChat.answerError', 'Answer failed. Please try again.'));
      }
    }
    throw new Error(t('speechChat.timeout', 'The answer is taking too long. Please try again.'));
  };

  const handleCompletedAnswer = async (
    question,
    data,
    turnSerial = activeTurnSerialRef.current,
    turnLanguage = activeTurnLanguageRef.current || language
  ) => {
    releaseSpeechRecognizer();
    const answer = String(data.content || '').trim();
    if (!answer) {
      throw new Error(t('speechChat.emptyAnswerError', 'Tara finished processing, but no answer text came back. Please try again.'));
    }
    const nextFollowUps = Array.isArray(data.follow_up_questions)
      ? data.follow_up_questions.map((item) => String(item || '').trim()).filter(Boolean).slice(0, 3)
      : [];
    const closingLine = buildSpeechAfterAnswerPrompt(turnLanguage, nextFollowUps[0], t);
    const spokenAnswer = trimForSpeechPlayback(`${answer} ${closingLine}`);
    setFollowUps(nextFollowUps);
    setTurns((prev) => [...prev, { question, answer, followUps: nextFollowUps }]);
    setCurrentTranscript('');
    setStatus('speaking');
    handsFreeRestartRef.current = !!handsFreeEnabledRef.current;
    if (!mountedRef.current || activeTurnSerialRef.current !== turnSerial) return;
    const ok = await playAvatarLine(spokenAnswer, { language: turnLanguage || language });
    if (!mountedRef.current || activeTurnSerialRef.current !== turnSerial) return;
    if (!ok) {
      if (!mountedRef.current) return;
      handsFreeRestartRef.current = false;
      setErrorText(t('speechChat.playbackError', 'I prepared the answer, but audio playback failed. Please read the answer on screen or try again.'));
      setStatus('idle');
      return;
    }
    if (!mountedRef.current || activeTurnSerialRef.current !== turnSerial) return;
    if (handsFreeRestartRef.current && handsFreeEnabledRef.current) {
      await maybeRestartHandsFree();
      return;
    }
    setStatus('idle');
  };

  const runQuestionTurn = async (question) => {
    const spokenQuestion = String(question || '').trim();
    if (!spokenQuestion) return;

    const turnSerial = activeTurnSerialRef.current + 1;
    activeTurnSerialRef.current = turnSerial;
    const turnLanguage = inferSpeechTurnLanguage(spokenQuestion, language);
    activeTurnLanguageRef.current = turnLanguage;
    if (turnLanguage !== normalizeLanguageCode(language)) {
      setLanguage(turnLanguage);
    }
    logSpeechDebug('speechTurn.language', {
      question: spokenQuestion.slice(0, 120),
      previousLanguage: language,
      turnLanguage,
    });
    const isCurrentTurn = () => mountedRef.current && activeTurnSerialRef.current === turnSerial;
    const answerPromise = askInstant(spokenQuestion, turnLanguage);

    try {
      const finalData = await answerPromise;
      if (!isCurrentTurn() || !finalData) return;
      await handleCompletedAnswer(spokenQuestion, finalData, turnSerial, turnLanguage);
    } catch (error) {
      if (!isCurrentTurn()) return;
      throw error;
    }
  };

  const askFollowUp = async (question) => {
    if (status !== 'idle') return;
    setCurrentTranscript(question);
    setFollowUps([]);
    setErrorText('');
    try {
      await getTextToSpeech().stop();
      setStatus('thinking');
      await runQuestionTurn(question);
    } catch (error) {
      setErrorText(error?.message || t('speechChat.answerError', 'Answer failed. Please try again.'));
      setStatus('idle');
    }
  };

  const stopSpeechUiImmediately = () => {
    activeTurnSerialRef.current += 1;
    handsFreeRestartRef.current = false;
    startListeningInFlightRef.current = false;
    if (speakingWatchdogRef.current) {
      clearTimeout(speakingWatchdogRef.current);
      speakingWatchdogRef.current = null;
    }
    setAvatarSpeech({ active: false, text: '', timeline: [], positionMs: 0, durationMs: 0, audioStarted: false });
    try {
      const tts = getTextToSpeech();
      if (typeof tts.stopImmediate === 'function') {
        tts.stopImmediate();
      } else {
        tts.stop().catch?.(() => {});
      }
    } catch {
      // ignore immediate stop failures
    }
  };

  const handleBackPress = async () => {
    logSpeechDebug('backPress', { status, listeningMode: listeningModeRef.current }).catch(() => {});
    stopSpeechUiImmediately();
    releaseSpeechRecognizer();
    endSpeechBillingSession('back').catch(() => {});
    navigation.goBack();
  };

  const forceStartListening = async () => {
    logSpeechDebug('forceStartListening', {
      status,
      listeningMode: listeningModeRef.current,
      hasRecording: Boolean(recordingRef.current),
    }).catch(() => {});
    stopSpeechUiImmediately();
    releaseSpeechRecognizer();
    if (!billingSessionRef.current?.session_id) {
      const billingOk = await startSpeechBillingSession();
      if (!billingOk) return;
    }
    setErrorText('');
    setCurrentTranscript('');
    setFollowUps([]);
    await wait(80);
    await startListening({ source: 'forceMic', stopCurrentSpeech: false });
  };

  const pauseSpeechChat = async (source = 'pause') => {
    logSpeechDebug('pauseSpeechChat', { source, status, listeningMode: listeningModeRef.current }).catch(() => {});
    handsFreeRestartRef.current = false;
    setHandsFreeEnabled(false);
    handsFreeEnabledRef.current = false;
    startListeningInFlightRef.current = false;
    releaseSpeechRecognizer();
    stopSpeechUiImmediately();
    setCurrentTranscript('');
    setErrorText('');
    setStatus('idle');
  };

  const handleMicPress = async () => {
    try {
      logSpeechDebug('micPress', {
        status,
        listeningMode: listeningModeRef.current,
        inFlight: startListeningInFlightRef.current,
        hasRecording: Boolean(recordingRef.current),
      }).catch(() => {});
      if (status === 'listening') {
        if (handsFreeEnabledRef.current) {
          await pauseSpeechChat('main_button_while_hands_free_listening');
        } else {
          await stopListening();
        }
      } else if (status === 'speaking') {
        await pauseSpeechChat('main_button_while_speaking');
      } else {
        await forceStartListening();
      }
    } catch (error) {
      setErrorText(error?.message || t('speechChat.genericError', 'Something went wrong. Please try again.'));
      setStatus('idle');
    }
  };

  const speechPreparing = status === 'speaking' && avatarSpeech.active && !avatarSpeech.audioStarted;
  const nativeRecognizerStarting = status === 'listening'
    && nativeRecognizerPhase === 'starting'
    && !currentTranscript;
  const statusText = {
    idle: handsFreeEnabled
      ? t('speechChat.statusIdleHandsFree', 'Tap the mic and AstroRoshni will keep listening after each answer')
      : t('speechChat.statusIdle', 'Tap the mic and ask your question'),
    listening: nativeRecognizerStarting
      ? t('speechChat.statusStartingRecognizer', 'Starting microphone...')
      : handsFreeEnabled
        ? t('speechChat.statusListeningHandsFree', 'Speak now. Tap pause if you want to stop listening.')
        : t('speechChat.statusListening', 'Listening... tap again when done'),
    transcribing: t('speechChat.statusTranscribing', 'Finishing your question...'),
    thinking: t('speechChat.statusThinking', 'Reading the chart...'),
    speaking: speechPreparing
      ? t('speechChat.statusPreparingSpeech', 'Preparing Tara’s voice...')
      : t('speechChat.statusSpeaking', 'Speaking the answer... tap pause to stop hands-free'),
  }[status] || '';

  const busy = ['transcribing', 'thinking'].includes(status) || speechPreparing || nativeRecognizerStarting;
  const screenPalette = {
    background: '#fbf4ed',
    backgroundAlt: '#f6ede5',
    surface: 'rgba(255,255,255,0.74)',
    surfaceStrong: '#fffaf5',
    border: 'rgba(148,163,184,0.18)',
    text: '#1f2937',
    textSecondary: '#6b7280',
    primary: '#c2410c',
    accent: '#2563eb',
  };
  const stageProfile = {
    idle: {
      eyebrow: t('speechChat.stageEyebrowIdle', 'Voice Chamber'),
      headline: t('speechChat.stageHeadlineIdle', 'Ask Tara anything'),
      chamberColors: ['rgba(255,255,255,0.98)', 'rgba(252,245,238,0.96)', 'rgba(247,237,227,0.94)'],
      haloOuter: 'rgba(251,191,36,0.12)',
      haloInner: 'rgba(245,158,11,0.10)',
      line: 'rgba(148,163,184,0.18)',
      star: 'rgba(245,158,11,0.82)',
      dot: 'rgba(249,115,22,0.50)',
    },
    listening: {
      eyebrow: t('speechChat.stageEyebrowListening', 'Listening'),
      headline: t('speechChat.stageHeadlineListening', 'Speak now'),
      chamberColors: ['rgba(255,255,255,0.98)', 'rgba(239,246,255,0.96)', 'rgba(224,242,254,0.94)'],
      haloOuter: 'rgba(56,189,248,0.16)',
      haloInner: 'rgba(37,99,235,0.10)',
      line: 'rgba(37,99,235,0.22)',
      star: 'rgba(37,99,235,0.78)',
      dot: 'rgba(56,189,248,0.52)',
    },
    thinking: {
      eyebrow: t('speechChat.stageEyebrowThinking', 'Reading The Chart'),
      headline: t('speechChat.stageHeadlineThinking', 'Patterns are settling'),
      chamberColors: ['rgba(255,255,255,0.98)', 'rgba(248,245,255,0.96)', 'rgba(238,232,255,0.94)'],
      haloOuter: 'rgba(168,85,247,0.14)',
      haloInner: 'rgba(124,58,237,0.10)',
      line: 'rgba(124,58,237,0.18)',
      star: 'rgba(168,85,247,0.74)',
      dot: 'rgba(196,181,253,0.55)',
    },
    speaking: {
      eyebrow: t('speechChat.stageEyebrowSpeaking', 'Speaking'),
      headline: t('speechChat.stageHeadlineSpeaking', 'Tara is answering'),
      chamberColors: ['rgba(255,255,255,0.98)', 'rgba(255,246,237,0.96)', 'rgba(255,237,213,0.94)'],
      haloOuter: 'rgba(251,146,60,0.16)',
      haloInner: 'rgba(249,115,22,0.12)',
      line: 'rgba(249,115,22,0.18)',
      star: 'rgba(249,115,22,0.82)',
      dot: 'rgba(251,191,36,0.56)',
    },
  }[
    status === 'listening'
      ? 'listening'
      : status === 'thinking' || status === 'transcribing'
        ? 'thinking'
        : status === 'speaking'
          ? 'speaking'
          : 'idle'
  ];
  const glowScaleX = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [1, status === 'speaking' ? 1.08 : 1.04],
  });
  const orbOpacity = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.16, 0.34],
  });
  const thinkingScale = pulseAnim.interpolate({
    inputRange: [0, 0.6],
    outputRange: [1, 1.03],
  });
  const sparkleMotionStyles = sparkleAnims.map((anim, index) => ({
    opacity: anim.interpolate({
      inputRange: [0, 0.15, 0.75, 1],
      outputRange: [0, 0.85, 0.55, 0],
    }),
    transform: [
      {
        translateY: anim.interpolate({
          inputRange: [0, 1],
          outputRange: [-14 - index * 2, 26 + index * 8],
        }),
      },
      {
        translateX: anim.interpolate({
          inputRange: [0, 0.5, 1],
          outputRange: [0, index % 2 === 0 ? 6 : -6, index % 2 === 0 ? -3 : 3],
        }),
      },
      {
        scale: anim.interpolate({
          inputRange: [0, 0.5, 1],
          outputRange: [0.88, 1, 0.92],
        }),
      },
    ],
  }));
  const transcriptScale = cardPulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 1.015],
  });
  const transcriptGlow = cardPulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.16, 0.34],
  });
  const voiceBarWidth = Math.min(280, SCREEN_WIDTH * 0.78);
  const compactVoiceLayout = SCREEN_HEIGHT < 840;
  const tinyVoiceLayout = SCREEN_HEIGHT < 740;
  const micIconSize = tinyVoiceLayout ? 24 : compactVoiceLayout ? 26 : 30;

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: screenPalette.background }]}>
      <LinearGradient
        colors={[screenPalette.background, screenPalette.backgroundAlt]}
        style={styles.container}
      >
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBackPress} style={styles.backButton}>
            <Ionicons name="chevron-back" size={26} color={screenPalette.text} />
          </TouchableOpacity>
          <View style={styles.headerTextWrap}>
            <Text style={[styles.title, { color: screenPalette.text }]}>
              {t('speechChat.screenTitle', 'Tara')}
            </Text>
            <Text style={[styles.subtitle, { color: screenPalette.textSecondary }]}>
              {birthData?.name
                ? t('speechChat.screenSubtitleWithChart', {
                    name: birthData.name,
                    defaultValue: `Voice guide on AstroRoshni · Instant answers for ${birthData.name}`,
                  })
                : t('speechChat.screenSubtitleDefault', 'Voice guide on AstroRoshni · Instant spoken answers')}
            </Text>
          </View>
          <View style={[styles.liveBadge, { backgroundColor: 'rgba(37,99,235,0.08)', borderColor: 'rgba(37,99,235,0.12)' }]}>
            <View style={styles.liveDot} />
            <Text style={[styles.liveBadgeText, { color: screenPalette.accent }]}>Live</Text>
          </View>
        </View>

        <View style={[styles.callMeter, { borderColor: screenPalette.border, backgroundColor: screenPalette.surfaceStrong }]}>
          <View style={styles.callMeterItem}>
            <Ionicons name="time-outline" size={15} color={screenPalette.accent} />
            <Text style={[styles.callMeterText, { color: screenPalette.text }]}>
              {formatCallTime(callElapsedSeconds)}
            </Text>
          </View>
          <View style={styles.callMeterDivider} />
          <Text style={[styles.callMeterSubtext, { color: screenPalette.textSecondary }]}>
            {speechPerMinuteCost != null
              ? `${speechPerMinuteCost} credits/min`
              : 'Speech billing'}
            {callRemainingSeconds != null ? ` · ${formatCallTime(callRemainingSeconds)} left` : ''}
          </Text>
        </View>

        <View style={styles.mainColumn}>
        <ScrollView ref={scrollRef} style={styles.conversation} contentContainerStyle={styles.conversationContent}>
          {turns.length === 0 && !currentTranscript ? (
            <View style={[
              styles.emptyVoiceState,
              {
                borderColor: screenPalette.border,
                backgroundColor: screenPalette.surface,
              },
            ]}>
              <View style={[styles.emptyVoiceIcon, { backgroundColor: stageProfile.haloOuter }]}>
                <Ionicons
                  name={
                    status === 'listening'
                      ? 'mic'
                      : status === 'thinking' || status === 'transcribing'
                        ? 'sparkles'
                        : status === 'speaking'
                          ? 'volume-high'
                          : 'chatbubble-ellipses'
                  }
                  size={28}
                  color={status === 'listening' ? screenPalette.accent : screenPalette.primary}
                />
              </View>
              <Text style={[styles.emptyVoiceTitle, { color: screenPalette.text }]}>
                {stageProfile.headline}
              </Text>
              <Text style={[styles.emptyVoiceBody, { color: screenPalette.textSecondary }]}>
                {statusText}
              </Text>
            </View>
          ) : null}

          {turns.map((turn, index) => (
            <View key={`${turn.question}_${index}`} style={styles.turnBlock}>
              <View style={[styles.userBubble, { backgroundColor: 'rgba(249,115,22,0.10)' }]}>
                <Text style={[styles.bubbleLabel, { color: screenPalette.textSecondary }]}>You asked</Text>
                <Text style={[styles.bubbleText, { color: screenPalette.text }]}>{turn.question}</Text>
              </View>
              <View style={[styles.answerBubble, { backgroundColor: screenPalette.surfaceStrong, borderColor: screenPalette.border }]}>
                <Text style={[styles.bubbleLabel, { color: screenPalette.textSecondary }]}>
                  {t('speechChat.answerBubbleLabel', 'Tara answered')}
                </Text>
                <Text style={[styles.bubbleText, { color: screenPalette.text }]}>{turn.answer}</Text>
              </View>
            </View>
          ))}

          {currentTranscript ? (
            <Animated.View
              style={[
                styles.liveCard,
                {
                  borderColor: 'rgba(37,99,235,0.12)',
                  backgroundColor: 'rgba(255,255,255,0.92)',
                  shadowOpacity: status === 'idle' ? 0.08 : transcriptGlow,
                  transform: [{ scale: transcriptScale }],
                },
              ]}
            >
              <Text style={[styles.bubbleLabel, { color: screenPalette.textSecondary }]}>
                {status === 'listening' ? t('speechChat.heardSoFar', 'Heard so far') : t('speechChat.currentQuestion', 'Current question')}
              </Text>
              <Text style={[styles.bubbleText, { color: screenPalette.text }]}>{currentTranscript}</Text>
            </Animated.View>
          ) : null}
        </ScrollView>

        {followUps.length > 0 && status === 'idle' ? (
          <View style={styles.followUpRow}>
            {followUps.map((item) => (
              <TouchableOpacity key={item} onPress={() => askFollowUp(item)} style={[styles.followUpChip, { borderColor: screenPalette.border, backgroundColor: 'rgba(255,255,255,0.8)' }]}>
                <Text style={[styles.followUpText, { color: screenPalette.text }]} numberOfLines={2}>{item}</Text>
              </TouchableOpacity>
            ))}
          </View>
        ) : null}

        {errorText ? <Text style={[styles.errorText, { color: colors.error }]}>{errorText}</Text> : null}
        </View>

        <LinearGradient
          colors={['rgba(255,251,247,0.98)', 'rgba(248,241,233,0.98)', 'rgba(244,235,226,0.96)']}
          style={[
            styles.controlsShell,
            compactVoiceLayout && styles.controlsShellCompact,
            tinyVoiceLayout && styles.controlsShellTiny,
            { borderColor: screenPalette.border },
          ]}
        >
        <View style={[styles.controls, compactVoiceLayout && styles.controlsCompact]}>
          <LinearGradient
            colors={stageProfile.chamberColors}
            style={[
              styles.voiceChamber,
              compactVoiceLayout && styles.voiceChamberCompact,
              tinyVoiceLayout && styles.voiceChamberTiny,
              { borderColor: screenPalette.border },
            ]}
          >
            <View pointerEvents="none" style={styles.chamberBackdrop}>
              <View style={[styles.moonArcOuter, { borderColor: stageProfile.line, backgroundColor: stageProfile.haloOuter }]} />
              <View style={[styles.moonArcInner, { borderColor: stageProfile.line, backgroundColor: stageProfile.haloInner }]} />
              <View style={[styles.geometryCircleLarge, { borderColor: stageProfile.line }]} />
              <View style={[styles.geometryCircleSmall, { borderColor: stageProfile.line }]} />
              <View style={[styles.constellationLine, styles.constellationLineLeft, { backgroundColor: stageProfile.line }]} />
              <View style={[styles.constellationLine, styles.constellationLineRight, { backgroundColor: stageProfile.line }]} />
              <View style={[styles.constellationNode, styles.constellationNodeLeftTop, { backgroundColor: stageProfile.dot }]} />
              <View style={[styles.constellationNode, styles.constellationNodeLeftBottom, { backgroundColor: stageProfile.dot }]} />
              <View style={[styles.constellationNode, styles.constellationNodeRightTop, { backgroundColor: stageProfile.dot }]} />
              <View style={[styles.constellationNode, styles.constellationNodeRightBottom, { backgroundColor: stageProfile.dot }]} />
            </View>

            <View style={[styles.stageHeader, compactVoiceLayout && styles.stageHeaderCompact]}>
              <Text style={[styles.stageEyebrow, { color: screenPalette.textSecondary }]}>{stageProfile.eyebrow}</Text>
              <Text style={[
                styles.stageHeadline,
                compactVoiceLayout && styles.stageHeadlineCompact,
                tinyVoiceLayout && styles.stageHeadlineTiny,
                { color: screenPalette.text },
              ]}>{stageProfile.headline}</Text>
            </View>

            <View style={[
              styles.voiceStage,
              compactVoiceLayout && styles.voiceStageCompact,
              tinyVoiceLayout && styles.voiceStageTiny,
            ]}>
              <View pointerEvents="none" style={styles.cosmicLayer}>
                <Animated.View style={[styles.sparkleStar, styles.sparkleStarTopLeft, sparkleMotionStyles[0]]}>
                  <View style={[styles.sparkleVertical, { backgroundColor: stageProfile.star }]} />
                  <View style={[styles.sparkleHorizontal, { backgroundColor: stageProfile.star }]} />
                </Animated.View>
                <Animated.View style={[styles.sparkleStar, styles.sparkleStarTopRight, sparkleMotionStyles[1]]}>
                  <View style={[styles.sparkleVertical, { backgroundColor: stageProfile.star }]} />
                  <View style={[styles.sparkleHorizontal, { backgroundColor: stageProfile.star }]} />
                </Animated.View>
                <Animated.View style={[styles.sparkleStar, styles.sparkleStarMidLeft, sparkleMotionStyles[2]]}>
                  <View style={[styles.sparkleVertical, { backgroundColor: stageProfile.star }]} />
                  <View style={[styles.sparkleHorizontal, { backgroundColor: stageProfile.star }]} />
                </Animated.View>
                <Animated.View style={[styles.sparkleStar, styles.sparkleStarMidRight, sparkleMotionStyles[3]]}>
                  <View style={[styles.sparkleVertical, { backgroundColor: stageProfile.star }]} />
                  <View style={[styles.sparkleHorizontal, { backgroundColor: stageProfile.star }]} />
                </Animated.View>
                <Animated.View style={[styles.sparkleDot, styles.sparkleDotOne, sparkleMotionStyles[4], { backgroundColor: stageProfile.dot }]} />
                <Animated.View style={[styles.sparkleDot, styles.sparkleDotTwo, sparkleMotionStyles[5], { backgroundColor: stageProfile.dot }]} />
                <Animated.View style={[styles.sparkleDot, styles.sparkleDotThree, sparkleMotionStyles[6], { backgroundColor: stageProfile.dot }]} />
                <Animated.View style={[styles.sparkleDot, styles.sparkleDotFour, sparkleMotionStyles[7], { backgroundColor: stageProfile.dot }]} />
              </View>

              <Animated.View
                pointerEvents="none"
                style={[
                  styles.voiceGlowBar,
                  {
                    width: voiceBarWidth,
                    opacity: status === 'idle' ? 0.08 : orbOpacity,
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
                  colors={[stageProfile.haloOuter, stageProfile.haloInner, 'rgba(255,255,255,0)']}
                  start={{ x: 0.5, y: 0 }}
                  end={{ x: 0.5, y: 1 }}
                  style={StyleSheet.absoluteFill}
                />
              </Animated.View>

              <TaraSpeakingAvatar
                status={status}
                compact={compactVoiceLayout}
                tiny={tinyVoiceLayout}
              />
            </View>

            <Text style={[
              styles.statusTextStage,
              compactVoiceLayout && styles.statusTextStageCompact,
              tinyVoiceLayout && styles.statusTextStageTiny,
              { color: screenPalette.textSecondary },
            ]}>{statusText}</Text>

            <View style={styles.chamberFooter}>
              <TouchableOpacity
                onPress={() => {
                  if (handsFreeEnabled && ['speaking', 'listening', 'transcribing', 'thinking'].includes(status)) {
                    pauseSpeechChat('hands_free_toggle').catch(() => {});
                    return;
                  }
                  setHandsFreeEnabled((prev) => !prev);
                }}
                  style={[
                    styles.handsFreeToggleInline,
                    compactVoiceLayout && styles.handsFreeToggleInlineCompact,
                    {
                      backgroundColor: handsFreeEnabled ? 'rgba(249,115,22,0.10)' : 'rgba(255,255,255,0.58)',
                      borderColor: screenPalette.border,
                  },
                ]}
              >
                <Ionicons
                  name={handsFreeEnabled ? 'radio-outline' : 'radio-button-off-outline'}
                  size={16}
                  color={handsFreeEnabled ? screenPalette.primary : screenPalette.textSecondary}
                />
                <Text style={[styles.handsFreeInlineText, { color: screenPalette.text }]}>
                  {t('speechChat.handsFreeLabel', 'Hands-free follow-up')}
                </Text>
                <Text style={[styles.handsFreeInlineState, { color: handsFreeEnabled ? screenPalette.primary : screenPalette.textSecondary }]}>
                  {handsFreeEnabled ? t('speechChat.handsFreeOn', 'On') : t('speechChat.handsFreeOff', 'Off')}
                </Text>
              </TouchableOpacity>

              {speechPerMinuteCost != null && !tinyVoiceLayout ? (
                <Text style={[styles.chamberCreditText, compactVoiceLayout && styles.chamberCreditTextCompact, { color: screenPalette.textSecondary }]}>
                  {speechPerMinuteCost}/min
                </Text>
              ) : null}

              <TouchableOpacity
                activeOpacity={0.88}
                onPress={handleMicPress}
                disabled={busy}
                style={[
                  styles.chamberMicOuter,
                  compactVoiceLayout && styles.chamberMicOuterCompact,
                  tinyVoiceLayout && styles.chamberMicOuterTiny,
                  busy && styles.micButtonDisabled,
                ]}
              >
                <LinearGradient
                  colors={status === 'listening' ? ['#0ea5e9', '#2563eb'] : ['#fb923c', '#f97316']}
                  style={styles.chamberMicButton}
                >
                  {busy ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <Ionicons
                      name={
                        status === 'speaking'
                          ? 'pause'
                          : status === 'listening' && handsFreeEnabled
                            ? 'pause'
                            : status === 'listening'
                              ? 'stop'
                              : 'mic'
                      }
                      size={micIconSize}
                      color="#fff"
                    />
                  )}
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </LinearGradient>
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
    paddingHorizontal: 14,
    paddingTop: 6,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 8,
    flexShrink: 0,
  },
  mainColumn: {
    flex: 1,
    minHeight: 0,
  },
  backButton: {
    width: 34,
    height: 34,
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
    paddingHorizontal: 8,
    paddingVertical: 4,
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
    fontSize: 19,
    fontWeight: '800',
  },
  subtitle: {
    fontSize: 11,
    marginTop: 2,
  },
  callMeter: {
    minHeight: 38,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 7,
    marginBottom: 6,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
    flexShrink: 0,
  },
  callMeterItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  callMeterText: {
    fontSize: 14,
    fontWeight: '800',
  },
  callMeterDivider: {
    width: 1,
    height: 18,
    backgroundColor: 'rgba(148,163,184,0.26)',
  },
  callMeterSubtext: {
    flex: 1,
    fontSize: 12,
    fontWeight: '700',
  },
  conversation: {
    flex: 1,
  },
  conversationContent: {
    paddingVertical: 8,
    gap: 10,
    flexGrow: 1,
  },
  emptyVoiceState: {
    flex: 1,
    minHeight: 180,
    borderWidth: 1,
    borderRadius: 20,
    paddingHorizontal: 20,
    paddingVertical: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyVoiceIcon: {
    width: 58,
    height: 58,
    borderRadius: 999,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  emptyVoiceTitle: {
    fontSize: 22,
    lineHeight: 27,
    fontWeight: '800',
    textAlign: 'center',
  },
  emptyVoiceBody: {
    fontSize: 14,
    lineHeight: 20,
    marginTop: 8,
    textAlign: 'center',
    maxWidth: 300,
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
    marginHorizontal: -14,
    paddingHorizontal: 14,
    paddingTop: 8,
    paddingBottom: 4,
    borderTopWidth: 1,
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    overflow: 'hidden',
    flexShrink: 0,
  },
  controlsShellCompact: {
    paddingTop: 6,
    paddingBottom: 2,
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
  },
  controlsShellTiny: {
    paddingTop: 4,
    paddingBottom: 0,
  },
  controls: {
    alignItems: 'center',
    paddingBottom: 6,
    overflow: 'visible',
  },
  controlsCompact: {
    paddingBottom: 2,
  },
  voiceChamber: {
    width: '100%',
    maxWidth: 420,
    borderWidth: 1,
    borderRadius: 20,
    paddingTop: 10,
    paddingHorizontal: 12,
    paddingBottom: 10,
    overflow: 'hidden',
    alignItems: 'center',
    shadowColor: '#f59e0b',
    shadowOpacity: 0.08,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 10 },
    elevation: 4,
  },
  voiceChamberCompact: {
    borderRadius: 18,
    paddingTop: 8,
    paddingHorizontal: 10,
    paddingBottom: 8,
  },
  voiceChamberTiny: {
    paddingTop: 6,
    paddingBottom: 6,
  },
  chamberBackdrop: {
    position: 'absolute',
    inset: 0,
  },
  moonArcOuter: {
    position: 'absolute',
    width: 292,
    height: 292,
    borderRadius: 146,
    top: 88,
    alignSelf: 'center',
    borderWidth: 1,
  },
  moonArcInner: {
    position: 'absolute',
    width: 214,
    height: 214,
    borderRadius: 107,
    top: 128,
    alignSelf: 'center',
    borderWidth: 1,
  },
  geometryCircleLarge: {
    position: 'absolute',
    width: 344,
    height: 344,
    borderRadius: 172,
    top: 62,
    alignSelf: 'center',
    borderWidth: 1,
  },
  geometryCircleSmall: {
    position: 'absolute',
    width: 164,
    height: 164,
    borderRadius: 82,
    top: 154,
    alignSelf: 'center',
    borderWidth: 1,
  },
  constellationLine: {
    position: 'absolute',
    height: 1,
    opacity: 0.8,
  },
  constellationLineLeft: {
    width: 84,
    top: 176,
    left: 34,
    transform: [{ rotate: '28deg' }],
  },
  constellationLineRight: {
    width: 92,
    top: 202,
    right: 28,
    transform: [{ rotate: '-24deg' }],
  },
  constellationNode: {
    position: 'absolute',
    width: 6,
    height: 6,
    borderRadius: 999,
  },
  constellationNodeLeftTop: {
    top: 154,
    left: 28,
  },
  constellationNodeLeftBottom: {
    top: 202,
    left: 108,
  },
  constellationNodeRightTop: {
    top: 182,
    right: 112,
  },
  constellationNodeRightBottom: {
    top: 228,
    right: 28,
  },
  stageHeader: {
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  stageHeaderCompact: {
    marginBottom: 4,
  },
  stageEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1.2,
    marginBottom: 3,
    textAlign: 'center',
  },
  stageHeadline: {
    fontSize: 20,
    lineHeight: 24,
    fontWeight: '800',
    textAlign: 'center',
    alignSelf: 'center',
    maxWidth: 280,
  },
  stageHeadlineCompact: {
    fontSize: 18,
    lineHeight: 22,
  },
  stageHeadlineTiny: {
    fontSize: 16,
    lineHeight: 19,
  },
  voiceStage: {
    width: '100%',
    maxWidth: 260,
    height: 188,
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginBottom: 2,
    overflow: 'visible',
  },
  voiceStageCompact: {
    height: 150,
    maxWidth: 220,
    marginBottom: 0,
  },
  voiceStageTiny: {
    height: 124,
    maxWidth: 188,
    marginBottom: 0,
  },
  voiceGlowBar: {
    position: 'absolute',
    width: 248,
    bottom: 16,
    height: 62,
    borderRadius: 44,
    overflow: 'hidden',
    alignSelf: 'center',
  },
  avatarStageBlank: {
    position: 'absolute',
    inset: 0,
  },
  cosmicLayer: {
    position: 'absolute',
    inset: 0,
  },
  sparkleStar: {
    position: 'absolute',
    width: 22,
    height: 22,
    alignItems: 'center',
    justifyContent: 'center',
    opacity: 0.72,
  },
  sparkleVertical: {
    position: 'absolute',
    width: 2,
    height: 18,
    borderRadius: 999,
    backgroundColor: 'rgba(245,158,11,0.85)',
  },
  sparkleHorizontal: {
    position: 'absolute',
    width: 18,
    height: 2,
    borderRadius: 999,
    backgroundColor: 'rgba(251,191,36,0.82)',
  },
  sparkleStarTopLeft: {
    top: 54,
    left: 42,
    transform: [{ rotate: '16deg' }, { scale: 0.92 }],
  },
  sparkleStarTopRight: {
    top: 72,
    right: 44,
    transform: [{ rotate: '-12deg' }, { scale: 0.78 }],
  },
  sparkleStarMidLeft: {
    top: 174,
    left: 20,
    transform: [{ rotate: '-8deg' }, { scale: 0.64 }],
  },
  sparkleStarMidRight: {
    top: 204,
    right: 18,
    transform: [{ rotate: '12deg' }, { scale: 0.58 }],
  },
  sparkleDot: {
    position: 'absolute',
    width: 6,
    height: 6,
    borderRadius: 999,
    backgroundColor: 'rgba(249,115,22,0.48)',
  },
  sparkleDotOne: {
    top: 102,
    left: 74,
  },
  sparkleDotTwo: {
    top: 132,
    right: 70,
    width: 4,
    height: 4,
  },
  sparkleDotThree: {
    top: 248,
    left: 54,
    width: 5,
    height: 5,
    backgroundColor: 'rgba(251,191,36,0.42)',
  },
  sparkleDotFour: {
    top: 262,
    right: 56,
    width: 4,
    height: 4,
    backgroundColor: 'rgba(245,158,11,0.4)',
  },
  avatarWrap: {
    width: 166,
    height: 188,
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginBottom: 0,
  },
  avatarWrapCompact: {
    width: 132,
    height: 150,
  },
  avatarWrapTiny: {
    width: 110,
    height: 124,
  },
  avatarImageStage: {
    width: 166,
    height: 188,
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'visible',
  },
  avatarImageStageCompact: {
    width: 132,
    height: 150,
  },
  avatarImageStageTiny: {
    width: 110,
    height: 124,
  },
  avatarImageLayer: {
    position: 'absolute',
    width: '100%',
    height: '100%',
  },
  avatarBaseLayer: {
    width: '124%',
    height: '124%',
    bottom: -6,
  },
  avatarFeatureLayer: {
    width: '124%',
    height: '124%',
    bottom: -6,
  },
  avatarHairBack: {
    position: 'absolute',
    width: 88,
    height: 78,
    borderTopLeftRadius: 44,
    borderTopRightRadius: 44,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
    top: 8,
  },
  avatarShoulders: {
    position: 'absolute',
    width: 110,
    height: 42,
    borderTopLeftRadius: 34,
    borderTopRightRadius: 34,
    borderBottomLeftRadius: 18,
    borderBottomRightRadius: 18,
    bottom: 0,
  },
  avatarNeck: {
    position: 'absolute',
    width: 20,
    height: 18,
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 8,
    bottom: 26,
  },
  avatarHead: {
    width: 76,
    height: 86,
    borderRadius: 32,
    alignItems: 'center',
    paddingTop: 16,
    overflow: 'hidden',
    marginBottom: 14,
  },
  avatarHairTop: {
    position: 'absolute',
    width: 78,
    height: 34,
    top: 0,
    borderBottomLeftRadius: 18,
    borderBottomRightRadius: 18,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
  },
  avatarBindi: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginBottom: 6,
  },
  avatarBrowsRow: {
    width: 36,
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 3,
  },
  avatarBrow: {
    width: 12,
    height: 2,
    borderRadius: 2,
  },
  avatarEyesRow: {
    width: 40,
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 7,
  },
  avatarEye: {
    width: 12,
    height: 8,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarEyeClosed: {
    height: 2,
    marginTop: 3,
  },
  avatarPupil: {
    width: 4,
    height: 4,
    borderRadius: 2,
  },
  avatarNose: {
    width: 4,
    height: 12,
    borderRadius: 3,
    marginBottom: 8,
  },
  avatarMouth: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  handsFreeToggle: {
    width: '100%',
    borderWidth: 1,
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginBottom: 10,
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
  statusTextStage: {
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 17,
    paddingHorizontal: 12,
    marginTop: 0,
    marginBottom: 8,
    alignSelf: 'center',
    maxWidth: 320,
  },
  statusTextStageCompact: {
    fontSize: 12,
    lineHeight: 15,
    paddingHorizontal: 8,
    marginBottom: 6,
  },
  statusTextStageTiny: {
    fontSize: 11,
    lineHeight: 14,
    marginBottom: 5,
  },
  chamberFooter: {
    width: '100%',
    alignItems: 'center',
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'space-between',
  },
  handsFreeToggleInline: {
    flex: 1,
    minHeight: 42,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    justifyContent: 'flex-start',
  },
  handsFreeToggleInlineCompact: {
    minHeight: 36,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  handsFreeInlineText: {
    fontSize: 12,
    fontWeight: '700',
    flexShrink: 1,
    flex: 1,
  },
  handsFreeInlineState: {
    fontSize: 12,
    fontWeight: '800',
  },
  chamberCreditText: {
    fontSize: 10,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 0,
    maxWidth: 70,
  },
  chamberCreditTextCompact: {
    fontSize: 10,
    marginBottom: 0,
  },
  chamberMicOuter: {
    width: 66,
    height: 66,
    borderRadius: 999,
    shadowColor: '#ea580c',
    shadowOpacity: 0.22,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
    elevation: 8,
    alignSelf: 'center',
    overflow: 'hidden',
  },
  chamberMicOuterCompact: {
    width: 58,
    height: 58,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
  },
  chamberMicOuterTiny: {
    width: 52,
    height: 52,
  },
  chamberMicButton: {
    width: '100%',
    height: '100%',
    borderRadius: 999,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
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
