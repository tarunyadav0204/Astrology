import React, { useEffect, useRef, useState } from 'react';
import {
  AccessibilityInfo,
  ActivityIndicator,
  Animated,
  AppState,
  Alert,
  Dimensions,
  Linking,
  PermissionsAndroid,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  Vibration,
  View,
  ScrollView,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { Audio, InterruptionModeIOS, InterruptionModeAndroid } from 'expo-av';
import * as FileSystem from 'expo-file-system/legacy';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { chatAPI, creditAPI, pricingAPI, speechAPI } from '../../services/api';
import { storage } from '../../services/storage';
import { buildQueryContext } from '../../utils/queryContext';
import { getTextToSpeech } from '../../utils/textToSpeechLazy';
import { useTheme } from '../../context/ThemeContext';
import { speechRecognition } from '../../native/speechRecognition';
import { useAuthGate } from '../../auth/AuthGateContext';
import FocusedStatusBar from '../Common/FocusedStatusBar';

const POLL_INTERVAL_MS = 1400;
const MAX_POLLS = 90;
const USE_BACKEND_SPEECH_TRANSCRIPTION = true;
const ALLOW_NATIVE_RUNTIME_BACKEND_FALLBACK = true;
const IS_IOS_WEB = Platform.OS === 'web'
  && typeof navigator !== 'undefined'
  && (
    /iPad|iPhone|iPod/i.test(String(navigator.userAgent || ''))
    || (/Macintosh/i.test(String(navigator.userAgent || '')) && Number(navigator.maxTouchPoints || 0) > 1)
  );
// Use the platform recognizer for the real-time experience on installed apps.
// The recorded-audio backend remains a compatibility fallback when a device
// has no recognizer service or the native recognizer fails to initialize.
const PREFER_NATIVE_SPEECH_RECOGNITION = ['android', 'ios', 'web'].includes(Platform.OS);
const REQUIRE_NATIVE_SPEECH_FOR_WEBSOCKET = Platform.OS === 'ios';
const USE_SPEECH_WEBSOCKET = true;
const HANDS_FREE_AUTO_STOP_MS = 45 * 1000;
const BACKEND_RECORDING_UNDETECTED_SPEECH_MAX_MS = 18 * 1000;
const BACKEND_RECORDING_MIN_MS = 2600;
const BACKEND_RECORDING_SILENCE_STOP_MS = 4200;
const BACKEND_RECORDING_LONG_SILENCE_STOP_MS = 7000;
const BACKEND_RECORDING_LONG_QUESTION_AFTER_MS = 5000;
const BACKEND_RECORDING_SPEECH_THRESHOLD_DB = -55;
// A brief pause often means the user is thinking, especially for a detailed
// astrology question. Wait for a deliberate three-second pause before ending.
const NATIVE_PARTIAL_STABLE_SUBMIT_MS = 3000;
const NATIVE_MAX_LISTENING_MS = 30000;
const NATIVE_READY_TIMEOUT_MS = 4500;
const POST_TTS_LISTEN_DELAY_MS = Platform.OS === 'android' ? 1200 : 900;
const POST_TTS_ECHO_GUARD_MS = Platform.OS === 'android' ? 250 : 200;
const HANDS_FREE_NO_SPEECH_RETRY_DELAY_MS = Platform.OS === 'android' ? 1100 : 800;
const HANDS_FREE_MAX_NO_SPEECH_RETRIES = 4;
const TRANSCRIPT_SEND_GRACE_MS = 1800;
const SPEECH_BILLING_MIN_START_MINUTES = 5;
const SPEECH_CREDIT_WARNING_SECONDS = 60;
const SPEECH_CREDIT_WARNING_INTERVAL_SECONDS = 10;
const CREDIT_WARNING_BEEP_BASE64 = 'UklGRqQCAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YYACAACAudjOoWQ0JkJ6tNfRpmk3Jj50sNXTq286Jjpvq9PVsHQ+JjdpptHXtHpCJjRkoc7YuX9GJzFem8vZvYVLKC5ZlsjZwYtPKixUkMXaxZBULCpPi8HZyJZZLihLhb3Zy5teMSdGgLnYzqFkNCZCerTX0aZpNyY+dLDV06tvOiY6b6vT1bB0PiY3aabR17R6QiY0ZKHO2LmARicxXpvL2b2FSyguWZbI2cGLTyosVJDF2sWQVCwqT4vB2ciWWS4oS4W92cubXjEnRoC52M6hZDQmQnq019GmaTcmPnSw1dOrbzomOm+r09WwdD4mN2mm0de0ekImNGShzti5f0YnMV6by9m9hUsoLlmWyNnBi08qLFSQxdrFkFQsKk+LwdnIllkuKEuFvdnLm14xJ0Z/udjOoWQ0JkJ6tNfRpmk3Jj50sNXTq286Jjpvq9PVsHQ+JjdpptHXtHpCJjRkoc7YuX9GJzFem8vZvYVLKC5ZlsjZwYtPKixUkMXaxZBULCpPi8HZyJZZLihLhb3Zy5teMSdGgLnYzqFkNCZCerTX0aZpNyY+dLDV06tvOiY6b6vT1bB0PiY3aabR17R6QiY0ZKHO2Ll/RicxXpvL2b2FSyguWZbI2cGLTyosVJDF2sWQVCwqT4vB2ciWWS4oS4W92cubXjEnRoC52M6hZDQmQnq019GmaTcmPnSw1dOrbzomOm+r09WwdD4mN2mm0de0ekImNGShzti5f0YnMV6by9m9hUsoLlmWyNnBi08qLFSQxdrFkFQsKk+LwdnIllkuKEuFvdnLm14xJ0Z/udjOoWQ0JkJ6tNfRpmk3Jj50sNXTq286Jjpvq9PVsHQ+JjdpptHX';
const getSupportedWebRecordingMimeType = () => {
  if (Platform.OS !== 'web' || typeof MediaRecorder === 'undefined') return '';
  const candidates = IS_IOS_WEB
    ? ['audio/mp4;codecs=mp4a.40.2', 'audio/mp4', 'audio/webm;codecs=opus', 'audio/webm']
    : ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4;codecs=mp4a.40.2', 'audio/mp4'];
  if (typeof MediaRecorder.isTypeSupported !== 'function') return IS_IOS_WEB ? 'audio/mp4' : '';
  return candidates.find((candidate) => MediaRecorder.isTypeSupported(candidate)) || '';
};
const WEB_SPEECH_RECORDING_MIME_TYPE = getSupportedWebRecordingMimeType();
const SPEECH_RECORDING_OPTIONS = {
  ...Audio.RecordingOptionsPresets.HIGH_QUALITY,
  isMeteringEnabled: true,
  ...(Platform.OS === 'web'
    ? {
      web: {
        ...(WEB_SPEECH_RECORDING_MIME_TYPE ? { mimeType: WEB_SPEECH_RECORDING_MIME_TYPE } : {}),
        bitsPerSecond: 128000,
      },
    }
    : {}),
};

const normalizeLanguageCode = (language) => {
  const raw = String(language || 'english').toLowerCase();
  return raw.startsWith('hi') ? 'hindi' : 'english';
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
const SPEECH_CHAT_TTS_PROVIDER = 'google';
const SPEECH_GREETING_CACHE_VERSION = 'v3';
const SPEECH_LANGUAGE_OPTIONS = [
  { key: 'english', labelKey: 'speechChat.languageEnglish', fallback: 'English' },
  { key: 'hindi', labelKey: 'speechChat.languageHindi', fallback: 'हिंदी' },
];

const hashGreetingText = (value) => {
  const text = String(value || '');
  let hash = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16);
};

const estimateSpeechDurationMs = (text) => {
  const spoken = String(text || '').replace(/\s+/g, ' ').trim();
  if (!spoken) return 2500;
  const words = spoken.split(/\s+/).filter(Boolean).length;
  const punctuationPauses = (spoken.match(/[.!?।]/g) || []).length * 180;
  const estimate = 900 + words * 360 + punctuationPauses;
  return Math.max(2600, Math.min(42000, estimate));
};

const progressiveSpeechCaption = (text, positionMs, durationMs, minimumWords = 1) => {
  const words = String(text || '').trim().split(/\s+/).filter(Boolean);
  if (!words.length) return '';
  const ratio = durationMs > 0 ? Math.max(0, Math.min(1, positionMs / durationMs)) : 0;
  const count = Math.min(words.length, Math.max(minimumWords, Math.ceil(words.length * ratio)));
  return words.slice(0, count).join(' ');
};

const buildSpeechAfterAnswerPrompt = (turnLanguage, followUpQuestion, translate) => {
  const lang = normalizeLanguageCode(turnLanguage || 'english');
  const question = String(followUpQuestion || '').trim();
  if (question) {
    return lang === 'hindi'
      ? 'अगर आप चाहें, तो मैं इसी से जुड़े अगले विषय पर और बता सकती हूँ।'
      : 'If you would like, I can continue with the next related part of this reading.';
  }
  if (lang === 'hindi') {
    return 'अब आप किस बात को थोड़ा और समझना चाहेंगे?';
  }
  return translate(
    'speechChat.afterAnswerPrompt',
    'What would you like to understand a little better next?'
  );
};

export default function SpeechChatScreen({ navigation, route }) {
  const insets = useSafeAreaInsets();
  const { t, i18n } = useTranslation();
  const { colors } = useTheme();
  const { requireAuthForPaid } = useAuthGate();
  const initialSpeechLanguage = normalizeLanguageCode(
    i18n.resolvedLanguage || i18n.language || route.params?.language || 'english'
  );
  const [userName, setUserName] = useState('');
  const [birthData, setBirthData] = useState(route.params?.birthData || null);
  // Reuse the text-chat thread when Speech was opened as a consultation mode.
  // Speech remains an Instant interaction, while both modalities share history.
  const [sessionId, setSessionId] = useState(route.params?.sessionId || null);
  const [language, setLanguage] = useState(initialSpeechLanguage);
  const [answerStyle, setAnswerStyle] = useState(
    route.params?.responseStyle === 'technical' ? 'technical' : 'simple'
  );
  const [status, setStatus] = useState('idle');
  const [turns, setTurns] = useState([]);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [streamingAnswer, setStreamingAnswer] = useState('');
  const [processingBridgeCaption, setProcessingBridgeCaption] = useState('');
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
  const [speechTtsProvider, setSpeechTtsProvider] = useState(SPEECH_CHAT_TTS_PROVIDER);
  const [speechTtsReady, setSpeechTtsReady] = useState(true);
  const [speechContextReady, setSpeechContextReady] = useState(false);
  const [requiresFirstMicTap, setRequiresFirstMicTap] = useState(IS_IOS_WEB);
  const [pendingTranscript, setPendingTranscript] = useState('');
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
  const greetingPlaybackEpochRef = useRef(0);
  const processingBridgeEpochRef = useRef(0);
  const processingBridgeSpeakingRef = useRef(false);
  const recentProcessingBridgeLinesRef = useRef([]);
  const pendingSpokenFollowUpRef = useRef('');
  const recordingRef = useRef(null);
  const recordingStartPromiseRef = useRef(null);
  const recordingTeardownPromiseRef = useRef(Promise.resolve());
  const listeningModeRef = useRef(null);
  const recordingMeterTimerRef = useRef(null);
  const recordingAutoStopTimerRef = useRef(null);
  const nativePartialStableTimerRef = useRef(null);
  const transcriptSendTimerRef = useRef(null);
  const nativeMaxListenTimerRef = useRef(null);
  const nativeReadyTimerRef = useRef(null);
  const latestNativeTranscriptRef = useRef('');
  const nativeNoSpeechRetryCountRef = useRef(0);
  const backendNoSpeechRetryCountRef = useRef(0);
  const nativeSpeechUnavailableForSessionRef = useRef(false);
  const recordingAutoStoppingRef = useRef(false);
  const recordingStartedAtRef = useRef(0);
  const recordingSpeechDetectedRef = useRef(false);
  const recordingSpeechFirstDetectedAtRef = useRef(0);
  const recordingSpeechSampleCountRef = useRef(0);
  const recordingLastSpeechAtRef = useRef(0);
  const recordingMeterSamplesRef = useRef([]);
  const startListeningInFlightRef = useRef(false);
  const appStateRef = useRef(AppState.currentState);
  const resumeHandsFreeOnActiveRef = useRef(false);
  const activeTurnSerialRef = useRef(0);
  const activeTurnLanguageRef = useRef(initialSpeechLanguage);
  const speechLanguageLockedRef = useRef(true);
  const speechSocketRef = useRef(null);
  const speechSocketConnectPromiseRef = useRef(null);
  const speechSocketPendingTurnsRef = useRef(new Map());
  const greetingPrefetchKeyRef = useRef('');
  const speakingWatchdogRef = useRef(null);
  const billingSessionRef = useRef(null);
  const iosWebMicPrimedRef = useRef(!IS_IOS_WEB);
  const billingTimerRef = useRef(null);
  const billingHeartbeatInFlightRef = useRef(false);
  const lastBillingHeartbeatSecondRef = useRef(0);
  const billingStartMsRef = useRef(0);
  const lastCreditWarningBeepRef = useRef(0);
  const billingEndingRef = useRef(false);
  const micRequestedAtRef = useRef(0);
  const firstPartialReportedRef = useRef(false);
  const questionSubmittedAtRef = useRef(0);
  const firstAnswerTextReportedRef = useRef(false);
  const pulseAnim = useRef(new Animated.Value(0)).current;
  const micLevelAnim = useRef(new Animated.Value(0.15)).current;
  const cardPulseAnim = useRef(new Animated.Value(0)).current;
  const sparkleAnims = useRef(
    Array.from({ length: 8 }, () => new Animated.Value(0))
  ).current;

  const getSpeechTranslator = (selectedLanguage = language) => (
    i18n.getFixedT(normalizeLanguageCode(selectedLanguage) === 'hindi' ? 'hindi' : 'english')
  );

  const emitSpeechMetric = (event, options = {}) => {
    speechAPI.logTelemetry({
      event,
      platform: Platform.OS,
      session_id: billingSessionRef.current?.session_id || null,
      turn_id: activeTurnSerialRef.current ? String(activeTurnSerialRef.current) : null,
      value_ms: options.valueMs == null ? null : Math.max(0, Math.round(options.valueMs)),
      success: options.success == null ? null : Boolean(options.success),
      metadata: {
        language: normalizeLanguageCode(activeTurnLanguageRef.current || language),
        hands_free: Boolean(handsFreeEnabledRef.current),
        ...(options.metadata || {}),
      },
    }).catch(() => {});
  };

  const buildGreetingText = () => {
    const speechT = getSpeechTranslator();
    const chartName = String(birthData?.name || '').trim();
    const trimmedUserName = String(userName || '').trim();
    if (!chartName) return '';
    return trimmedUserName
      ? speechT('speechChat.greetingWithUser', {
          userName: trimmedUserName,
          chartName,
          defaultValue:
            `${trimmedUserName}, ${chartName}'s chart is ready. What would you like to explore?`,
        })
      : speechT('speechChat.greetingAnonymous', {
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
    await releaseSpeechRecognizer();
    setStatus('idle');
    setErrorText(t('speechChat.creditFinished', 'Talk To Tara ended because your available talk credits finished.'));
    await endSpeechBillingSession('credit_finished');
  };

  const startSpeechBillingSession = async () => {
    if (billingSessionRef.current?.session_id) return true;
    const authOk = await requireAuthForPaid({
      feature: t('speechChat.title', 'Talk To Tara'),
      message: t('authGate.messageSpeech'),
      resume: { resumeRoute: 'SpeechChat', resumeParams: route?.params || {} },
    });
    if (!authOk) return false;
    try {
      const res = await creditAPI.startSpeechSession();
      const data = res?.data || {};
      billingSessionRef.current = data;
      const resumedElapsedSeconds = Math.max(0, Number(data.elapsed_seconds || 0));
      billingStartMsRef.current = Date.now() - resumedElapsedSeconds * 1000;
      lastBillingHeartbeatSecondRef.current = resumedElapsedSeconds;
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
        const heartbeatEvery = Math.max(5, Number(currentSession.heartbeat_interval_seconds || 10));
        if (
          elapsed > 0
          && elapsed - lastBillingHeartbeatSecondRef.current >= heartbeatEvery
          && !billingHeartbeatInFlightRef.current
        ) {
          lastBillingHeartbeatSecondRef.current = elapsed;
          billingHeartbeatInFlightRef.current = true;
          creditAPI.heartbeatSpeechSession(currentSession.session_id)
            .then((heartbeat) => {
              const heartbeatData = heartbeat?.data || {};
              if (heartbeatData.status && heartbeatData.status !== 'active') {
                stopSpeechForCreditFinish();
              }
            })
            .catch((error) => {
              logSpeechDebug('billing.heartbeatFailed', { message: error?.message });
            })
            .finally(() => {
              billingHeartbeatInFlightRef.current = false;
            });
        }
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
        || `Talk To Tara needs at least ${SPEECH_BILLING_MIN_START_MINUTES * perMinute} credits to start.`;
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
      if (!firstPartialReportedRef.current && micRequestedAtRef.current) {
        firstPartialReportedRef.current = true;
        emitSpeechMetric('first_partial_transcript_ms', {
          valueMs: Date.now() - micRequestedAtRef.current,
          success: true,
          metadata: { recognizer: 'native' },
        });
      }
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
      const rmsDb = Number(event?.rmsDb ?? event?.rms_db ?? event?.metering);
      if (Number.isFinite(rmsDb)) {
        micLevelAnim.setValue(Math.max(0.12, Math.min(1, (rmsDb + 60) / 60)));
      }
      if (['onReadyForSpeech', 'onBeginningOfSpeech', 'onPartialResults'].includes(eventName)) {
        if (mountedRef.current) setNativeRecognizerReady(true);
        if (mountedRef.current) setNativeRecognizerPhase('ready');
        if (eventName === 'onReadyForSpeech') {
          Vibration.vibrate(20);
          emitSpeechMetric('microphone_ready_ms', {
            valueMs: micRequestedAtRef.current ? Date.now() - micRequestedAtRef.current : null,
            success: true,
            metadata: { recognizer: 'native' },
          });
        }
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
      try {
        const [storedBirthData, storedLanguage, storedSpeechLanguage, storedUser] = await Promise.all([
          storage.getBirthDetails(),
          storage.getLanguage(),
          storage.getSpeechLanguage(),
          storage.getUserData(),
        ]);
        if (mountedRef.current) {
          if (!birthData && storedBirthData) setBirthData(storedBirthData);
          const selectedAppLanguage = storedLanguage
            || i18n.resolvedLanguage
            || i18n.language
            || route.params?.language
            || storedSpeechLanguage;
          if (selectedAppLanguage) {
            const nextLanguage = normalizeLanguageCode(selectedAppLanguage);
            setLanguage(nextLanguage);
            activeTurnLanguageRef.current = nextLanguage;
            speechLanguageLockedRef.current = true;
          }
          setUserName(String(storedUser?.name || storedUser?.full_name || '').trim());
        }
      } finally {
        if (mountedRef.current) setSpeechContextReady(true);
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
      if (transcriptSendTimerRef.current) {
        clearTimeout(transcriptSendTimerRef.current);
        transcriptSendTimerRef.current = null;
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
    if (!currentTranscript && !streamingAnswer && !turns.length) return undefined;
    const timer = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 80);
    return () => clearTimeout(timer);
  }, [currentTranscript, streamingAnswer, turns]);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextState) => {
      appStateRef.current = nextState;
      if (nextState === 'active' && statusRef.current === 'speaking') {
        getTextToSpeech().resumeCurrentSpeech?.().catch?.(() => {});
        emitSpeechMetric('playback_resumed', { success: true, metadata: { app_state: nextState } });
      }
      if (
        nextState === 'active'
        && resumeHandsFreeOnActiveRef.current
        && handsFreeEnabledRef.current
      ) {
        resumeHandsFreeOnActiveRef.current = false;
        setTimeout(() => {
          if (mountedRef.current && handsFreeEnabledRef.current) {
            maybeRestartHandsFree();
          }
        }, POST_TTS_LISTEN_DELAY_MS);
      }
    });
    return () => subscription?.remove?.();
  }, []);

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
    if (!speechContextReady || !birthData?.name || !speechTtsReady) return;
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
  }, [birthData?.id, birthData?.name, language, speechContextReady, speechTtsReady, userName, i18n]);

  useEffect(() => {
    if (greetedRef.current || !birthData?.name || status !== 'idle') return;
    if (!speechContextReady || !speechTtsReady) return;

    const greet = async () => {
      greetedRef.current = true;
      const greetingEpoch = greetingPlaybackEpochRef.current + 1;
      greetingPlaybackEpochRef.current = greetingEpoch;
      const greeting = buildGreetingText();
      if (!greeting || !mountedRef.current) return;
      const cacheKey = getGreetingCacheKey();
      setStatus('speaking');
      await speakWithAvatar(greeting, {
        language,
        provider: SPEECH_CHAT_TTS_PROVIDER,
        cacheKey,
        prepareSpoken: false,
        onDone: () => {
          if (!mountedRef.current || greetingPlaybackEpochRef.current !== greetingEpoch) return;
          if (handsFreeEnabledRef.current) {
            maybeStartAfterGreeting();
            return;
          }
          setStatus('idle');
        },
        onError: () => {
          if (!mountedRef.current || greetingPlaybackEpochRef.current !== greetingEpoch) return;
          // A greeting playback failure must not strand a hands-free session.
          // The user can still begin speaking even when the welcome audio failed.
          if (handsFreeEnabledRef.current) {
            maybeStartAfterGreeting();
            return;
          }
          setStatus('idle');
        },
      });
    };

    greet();
  }, [birthData?.name, language, speechContextReady, speechTtsReady, status, userName, i18n]);

  const ensureSession = async () => {
    if (sessionId) return sessionId;
    if (!birthData?.id) {
      Alert.alert(
        t('speechChat.profileRequired', 'Birth chart required'),
        t('speechChat.profileRequiredBody', 'Please select or create a birth chart before you Talk To Tara.')
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

  const primeIosWebMicrophone = async () => {
    if (!IS_IOS_WEB || iosWebMicPrimedRef.current) return true;
    if (!navigator?.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      throw new Error(t(
        'speechChat.safariMicUnavailable',
        'Microphone recording is not available here. Open AstroRoshni in Safari over HTTPS and try again.'
      ));
    }
    let permissionStream = null;
    try {
      // Keep getUserMedia directly inside the tap call chain. Safari can reject
      // the first capture request when it starts later from greeting onDone.
      permissionStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      iosWebMicPrimedRef.current = true;
      setRequiresFirstMicTap(false);
      return true;
    } catch (error) {
      const permissionBlocked = ['NotAllowedError', 'PermissionDeniedError', 'SecurityError']
        .includes(String(error?.name || ''));
      throw new Error(permissionBlocked
        ? t(
          'speechChat.safariMicBlocked',
          'Microphone access is blocked. In iPhone Settings, open Safari, check Microphone access, then reopen Talk To Tara.'
        )
        : t('speechChat.micStartError', 'Could not start the microphone. Please try again.'));
    } finally {
      permissionStream?.getTracks?.().forEach((track) => track.stop());
    }
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
        || code === 'speech_error_3'
        || code === 'speech_error_4'
        || code === 'speech_error_5'
        || code === 'speech_error_11'
        || /network|server|client|service/i.test(message)
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
        t('speechChat.profileRequiredBody', 'Please select or create a birth chart before you Talk To Tara.')
      );
      return;
    }

    startListeningInFlightRef.current = true;
    try {
      micRequestedAtRef.current = Date.now();
      firstPartialReportedRef.current = false;
      await logSpeechDebug('startListening.begin', { source, status, stopCurrentSpeech });
      setNativeRecognizerReady(false);
      setNativeRecognizerPhase('starting');
      setErrorText('');
      setCurrentTranscript('');
      setFollowUps([]);
      if (source !== 'nativeRetryAfterNoSpeech') {
        nativeNoSpeechRetryCountRef.current = 0;
      }
      if (source !== 'backendRetryAfterNoSpeech') {
        backendNoSpeechRetryCountRef.current = 0;
      }
      handsFreeRestartRef.current = false;
      setAvatarSpeech({ active: false, text: '', timeline: [], positionMs: 0, durationMs: 0, audioStarted: false });
      if (stopCurrentSpeech) {
        await getTextToSpeech().stop();
      }

      const permissionGranted = await ensureMicrophonePermission();
      if (!permissionGranted) {
        setNativeRecognizerReady(false);
        setNativeRecognizerPhase('idle');
        setStatus('idle');
        return;
      }

      let useBackendTranscription = USE_BACKEND_SPEECH_TRANSCRIPTION;
      // Safari's browser speech service is not dependable in an installed
      // Home Screen web app. Record audio and use our server transcription.
      if (PREFER_NATIVE_SPEECH_RECOGNITION && !IS_IOS_WEB) {
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
                  'Talk To Tara needs the native speech recognizer in this build. Rebuild/reinstall the app, or test on a device with Google Speech Services enabled.'
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
        setNativeRecognizerReady(false);
        setNativeRecognizerPhase('idle');
        await logSpeechDebug('startListening.backendTranscription', {
          platform: route?.params?.platform || 'native',
          language: activeTurnLanguageRef.current || language,
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
        normalizedLanguage: normalizeLanguageCode(activeTurnLanguageRef.current || language),
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

      speechRecognition.startListening(normalizeLanguageCode(activeTurnLanguageRef.current || language))
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
          queueRecognizedQuestion(finalTranscript);
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
            nativeSpeechUnavailableForSessionRef.current = true;
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
              || error?.code === 'speech_error_7'
              || error?.code === 'no_speech'
              || /no speech|timeout/i.test(String(error?.message || '')));
          if (shouldKeepListening) {
            nativeNoSpeechRetryCountRef.current += 1;
            setCurrentTranscript('');
            if (nativeNoSpeechRetryCountRef.current >= HANDS_FREE_MAX_NO_SPEECH_RETRIES) {
              pauseSpeechChat('inactivity_timeout').then(() => {
                setErrorText(t('speechChat.inactivityPaused', 'Talk To Tara paused after prolonged silence. Tap the mic when you are ready.'));
                endSpeechBillingSession('inactivity_timeout');
              });
              return;
            }
            setTimeout(() => {
              if (mountedRef.current && handsFreeEnabledRef.current) {
                startListening({ source: 'nativeRetryAfterNoSpeech', stopCurrentSpeech: false }).catch((retryError) => {
                  if (!mountedRef.current) return;
                  setErrorText(retryError?.message || t('speechChat.genericError', 'Something went wrong. Please try again.'));
                  setStatus('idle');
                });
              }
            }, HANDS_FREE_NO_SPEECH_RETRY_DELAY_MS);
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
    if (appStateRef.current !== 'active') {
      // Keep playback alive while locked, but defer the next microphone cycle
      // until the app is visible again.
      resumeHandsFreeOnActiveRef.current = true;
      setStatus('idle');
      return;
    }
    resumeHandsFreeOnActiveRef.current = false;
    setErrorText('');
    try {
      await wait(POST_TTS_LISTEN_DELAY_MS);
      await startListening({ source: 'handsFreeAfterAnswer', stopCurrentSpeech: false });
      emitSpeechMetric('hands_free_restart', { success: true, metadata: { reason: 'after_answer' } });
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
    if (IS_IOS_WEB && !iosWebMicPrimedRef.current) {
      setRequiresFirstMicTap(true);
      setStatus('idle');
      return;
    }
    try {
      // The welcome itself is free. Start metered time only when the live
      // microphone conversation is about to begin.
      if (!billingSessionRef.current?.session_id) {
        const billingOk = await startSpeechBillingSession();
        if (!billingOk || !mountedRef.current) {
          setStatus('idle');
          return;
        }
      }
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
      const teardown = recordingTeardownPromiseRef.current
        .catch(() => {})
        .then(() => recording.stopAndUnloadAsync?.())
        .catch(() => {});
      recordingTeardownPromiseRef.current = teardown;
    }
    try {
      speechRecognition.cancelListening();
    } catch {
      // Ignore cleanup failures; recognizer may already be inactive.
    }
    return recordingTeardownPromiseRef.current;
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

  const startBackendRecording = async () => {
    const permission = await Audio.requestPermissionsAsync();
    if (permission?.status !== 'granted') {
      throw new Error(t('speechChat.micPermissionBody', 'Please allow microphone access so AstroRoshni can hear your question.'));
    }

    // Expo permits only one prepared Recording instance. Wait for any prior
    // stop/unload to finish and share an in-flight create across rapid taps or
    // hands-free restarts.
    await recordingTeardownPromiseRef.current.catch(() => {});
    if (recordingRef.current || listeningModeRef.current === 'backend') return;
    if (recordingStartPromiseRef.current) {
      await recordingStartPromiseRef.current;
      return;
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
    const createPromise = Audio.Recording.createAsync(SPEECH_RECORDING_OPTIONS);
    recordingStartPromiseRef.current = createPromise;
    let recording;
    try {
      ({ recording } = await createPromise);
    } finally {
      if (recordingStartPromiseRef.current === createPromise) {
        recordingStartPromiseRef.current = null;
      }
    }
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
        const isNoSpeechFailure = /no speech|understand|empty|too short/i.test(String(detail));
        if (
          handsFreeEnabledRef.current
          && isNoSpeechFailure
        ) {
          backendNoSpeechRetryCountRef.current += 1;
          setErrorText('');
          setCurrentTranscript('');
          if (backendNoSpeechRetryCountRef.current >= HANDS_FREE_MAX_NO_SPEECH_RETRIES) {
            pauseSpeechChat('inactivity_timeout').then(() => {
              setErrorText(t('speechChat.inactivityPaused', 'Talk To Tara paused after prolonged silence. Tap the mic when you are ready.'));
              endSpeechBillingSession('inactivity_timeout');
            });
            return;
          }
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
          }, HANDS_FREE_NO_SPEECH_RETRY_DELAY_MS);
          return;
        }
        backendNoSpeechRetryCountRef.current = 0;
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
    Vibration.vibrate(20);
    emitSpeechMetric('microphone_ready_ms', {
      valueMs: micRequestedAtRef.current ? Date.now() - micRequestedAtRef.current : null,
      success: true,
      metadata: { recognizer: 'backend' },
    });
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
            micLevelAnim.setValue(Math.max(0.12, Math.min(1, (metering + 60) / 60)));
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
          if (
            handsFreeEnabledRef.current
            && elapsedMs >= BACKEND_RECORDING_UNDETECTED_SPEECH_MAX_MS
            && !recordingSpeechDetectedRef.current
          ) {
            // Metering may be absent or too quiet to cross the configured
            // threshold on some Android devices. Submit the captured audio
            // anyway; server transcription is a better terminal decision than
            // leaving the microphone spinning indefinitely.
            stopBackendFromTimer('speech_detection_timeout');
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

    let finishRecordingTeardown;
    recordingTeardownPromiseRef.current = new Promise((resolve) => {
      finishRecordingTeardown = resolve;
    });

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
    try {
      await recording.stopAndUnloadAsync();
    } finally {
      finishRecordingTeardown?.();
    }
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

    const transcriptionLanguage = normalizeLanguageCode(activeTurnLanguageRef.current || language);
    const recordingMimeType = Platform.OS === 'web'
      ? (WEB_SPEECH_RECORDING_MIME_TYPE || 'audio/mp4')
      : 'audio/mp4';
    const recordingExtension = recordingMimeType.includes('webm') ? 'webm' : 'm4a';
    await logSpeechDebug('backendTranscribe.request', {
      uri,
      language: transcriptionLanguage,
      durationMs,
      meteringMax,
      meteringAvg,
      recordingMimeType,
    });
    let response;
    try {
      response = await speechAPI.transcribeAudio(
        {
          uri,
          name: `speech-question-${Date.now()}.${recordingExtension}`,
          type: recordingMimeType,
        },
        transcriptionLanguage,
        { durationMs, meteringMax, meteringAvg }
      );
    } catch (error) {
      await logSpeechDebug('backendTranscribe.error', {
        message: error?.message,
        status: error?.response?.status,
        detail: error?.response?.data?.detail,
      });
      throw error;
    } finally {
      if (Platform.OS === 'web' && String(uri).startsWith('blob:')) {
        URL.revokeObjectURL(uri);
      }
    }
    const finalTranscript = String(response?.data?.transcript || '').trim();
    await logSpeechDebug('backendTranscribe.result', { transcript: finalTranscript });
    if (!finalTranscript) {
      throw new Error(t('speechChat.noTranscript', 'I could not understand that. Please try again.'));
    }
    backendNoSpeechRetryCountRef.current = 0;
    setCurrentTranscript(finalTranscript);
    queueRecognizedQuestion(finalTranscript);
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

  const cancelProcessingBridge = async (reason = 'cancelled', { interruptCurrent = true } = {}) => {
    processingBridgeEpochRef.current += 1;
    if (!processingBridgeSpeakingRef.current) {
      setProcessingBridgeCaption('');
      return;
    }
    if (!interruptCurrent) {
      emitSpeechMetric('processing_bridge_cancelled', {
        success: true,
        metadata: { cancel_reason: `${reason}_after_current_line` },
      });
      const gracefulDeadline = Date.now() + 20000;
      while (mountedRef.current && processingBridgeSpeakingRef.current && Date.now() < gracefulDeadline) {
        await wait(40);
      }
      if (processingBridgeSpeakingRef.current) {
        processingBridgeSpeakingRef.current = false;
        await getTextToSpeech().stop();
      }
      if (mountedRef.current) setProcessingBridgeCaption('');
      return;
    }
    setProcessingBridgeCaption('');
    processingBridgeSpeakingRef.current = false;
    await getTextToSpeech().stop();
    emitSpeechMetric('processing_bridge_cancelled', {
      success: true,
      metadata: { cancel_reason: reason },
    });
  };

  const startProcessingBridge = async (question, turnSerial, turnLanguage, submittedAt) => {
    const epoch = processingBridgeEpochRef.current + 1;
    processingBridgeEpochRef.current = epoch;
    const generatedAt = Date.now();
    try {
      const response = await speechAPI.getGuideLines({
        scene: 'processing',
        language: turnLanguage,
        userName: userName || null,
        chartName: birthData?.name || null,
        question,
        handsFree: handsFreeEnabledRef.current,
        recentLines: recentProcessingBridgeLinesRef.current.slice(-20),
        answerStyle,
      });
      if (!mountedRef.current || activeTurnSerialRef.current !== turnSerial || processingBridgeEpochRef.current !== epoch) return;
      const data = response?.data || {};
      const lines = Array.isArray(data.lines)
        ? data.lines.map((line) => String(line || '').trim()).filter(Boolean).slice(0, Number(data.max_lines) || 3)
        : [];
      emitSpeechMetric('processing_bridge_generated_ms', {
        valueMs: Date.now() - generatedAt,
        success: Boolean(lines.length),
        metadata: { line_count: lines.length },
      });
      if (!lines.length) return;
      const delayMs = Math.max(0, (Number(data.initial_delay_ms) || 0) - (Date.now() - submittedAt));
      if (delayMs) await wait(delayMs);
      for (const line of lines) {
        if (!mountedRef.current || activeTurnSerialRef.current !== turnSerial || processingBridgeEpochRef.current !== epoch) break;
        processingBridgeSpeakingRef.current = true;
        setProcessingBridgeCaption(line);
        const spoken = await playAvatarLine(line, { language: turnLanguage, segmented: false });
        processingBridgeSpeakingRef.current = false;
        if (spoken) recentProcessingBridgeLinesRef.current = [...recentProcessingBridgeLinesRef.current, line].slice(-20);
        if (!spoken || processingBridgeEpochRef.current !== epoch) break;
        emitSpeechMetric('processing_bridge_spoken', { success: true });
        const gapMs = Math.max(0, Number(data.line_gap_ms) || 0);
        if (gapMs) await wait(gapMs);
      }
      if (processingBridgeEpochRef.current === epoch) setProcessingBridgeCaption('');
    } catch {
      if (processingBridgeEpochRef.current === epoch) setProcessingBridgeCaption('');
    }
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

            if (event?.type === 'turn_started' || event?.type === 'turn_queued') {
              pending.accepted = true;
              if (event?.message_id) pending.messageId = event.message_id;
              return;
            }

            if (event?.type === 'answer_chunk') {
              const delta = String(event.text || '');
              pending.content = String(event.content || `${pending.content || ''}${delta}`);
              pending.onChunk?.(delta, { ...event, content: pending.content });
              return;
            }
            if (event?.type === 'answer_replace') {
              pending.content = String(event.content || '');
              pending.onReplace?.(pending.content, event);
              return;
            }
            if (event?.type === 'turn_completed') {
              speechSocketPendingTurnsRef.current.delete(turnId);
              pending.resolve({
                status: 'completed',
                message_id: event.message_id,
                content: String(event.content || pending.content || '').trim(),
                follow_up_questions: Array.isArray(event.follow_up_questions) ? event.follow_up_questions : [],
                next_action: event.next_action || null,
              });
              return;
            }
            if (event?.type === 'turn_error') {
              speechSocketPendingTurnsRef.current.delete(turnId);
              const error = new Error(event.message || event.error || 'Speech turn failed');
              error.turnAccepted = true;
              error.messageId = pending.messageId;
              error.clientRequestId = pending.clientRequestId;
              pending.reject(error);
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
              const error = new Error('Speech socket disconnected');
              error.turnAccepted = Boolean(pending.accepted);
              error.messageId = pending.messageId;
              error.clientRequestId = pending.clientRequestId;
              error.retryableConnectionFailure = true;
              pending.reject?.(error);
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

  const askSpeechSocket = async (
    question,
    turnLanguage = language,
    streamHandlers = {},
    suppliedClientRequestId = null,
    queryContext = null
  ) => {
    if (!USE_SPEECH_WEBSOCKET) {
      throw new Error('Speech websocket disabled');
    }
    let activeSessionId = await ensureSession();
    if (!activeSessionId) throw new Error(t('speechChat.sessionError', 'Could not start Talk To Tara.'));
    const socketClient = await ensureSpeechSocket();
    const turnId = `turn_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    const clientRequestId = suppliedClientRequestId
      || `speech_ws_${Date.now()}_${Math.random().toString(36).slice(2)}`;

    return new Promise((resolve, reject) => {
      speechSocketPendingTurnsRef.current.set(turnId, {
        resolve,
        reject,
        content: '',
        accepted: false,
        clientRequestId,
        onChunk: streamHandlers.onChunk,
        onReplace: streamHandlers.onReplace,
      });
      const sent = socketClient.send({
        type: 'ask',
        turn_id: turnId,
        session_id: activeSessionId,
        question,
        query_context: queryContext || buildQueryContext(),
        language: turnLanguage || language || 'english',
        response_style: answerStyle,
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

  const askInstant = async (question, turnLanguage = language, streamHandlers = {}) => {
    const clientRequestId = `speech_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    const offeredFollowUp = pendingSpokenFollowUpRef.current;
    pendingSpokenFollowUpRef.current = '';
    const speechQueryContext = buildQueryContext(
      offeredFollowUp ? { speech_follow_up_offer: offeredFollowUp } : {}
    );
    if (USE_SPEECH_WEBSOCKET) {
      try {
        return await askSpeechSocket(
          question,
          turnLanguage,
          streamHandlers,
          clientRequestId,
          speechQueryContext
        );
      } catch (socketError) {
        logSpeechDebug('speechSocket.fallbackToHttp', {
          message: socketError?.message,
        });
        closeSpeechSocket();
        if (socketError?.turnAccepted && socketError?.messageId) {
          return await pollForAnswer(question, socketError.messageId, streamHandlers);
        }
        if (socketError?.turnAccepted && !socketError?.retryableConnectionFailure) throw socketError;
        // Continue over HTTP with the same idempotency key if the socket
        // disconnected before returning a message id.
      }
    }
    let activeSessionId = await ensureSession();
    if (!activeSessionId) throw new Error(t('speechChat.sessionError', 'Could not start Talk To Tara.'));
    const buildAskBody = (sid) => ({
      session_id: sid,
      question,
      query_context: speechQueryContext,
      language: turnLanguage || language || 'english',
      response_style: answerStyle,
      premium_analysis: false,
      chat_tier: 'instant',
      speech_chat: true,
      speech_billing: false,
      native_name: birthData?.name,
      birth_details: toChatBirthDetails(birthData),
      client_request_id: clientRequestId,
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
    return await pollForAnswer(question, askData.message_id, streamHandlers);
  };

  const pollForAnswer = async (question, messageId, streamHandlers = {}) => {
    let previousPartial = '';
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
      const partial = String(data.partial_content || '');
      if (partial && partial !== previousPartial) {
        if (partial.startsWith(previousPartial)) {
          streamHandlers.onChunk?.(partial.slice(previousPartial.length), {
            content: partial,
            validated: false,
          });
        } else {
          streamHandlers.onReplace?.(partial, { validated: false });
        }
        previousPartial = partial;
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
    const bridgeHandoffPromise = cancelProcessingBridge('answer_complete', { interruptCurrent: false });
    const answer = String(data.content || '').trim();
    if (!answer) {
      throw new Error(t('speechChat.emptyAnswerError', 'Tara finished processing, but no answer text came back. Please try again.'));
    }
    if (!firstAnswerTextReportedRef.current) {
      firstAnswerTextReportedRef.current = true;
      emitSpeechMetric('first_answer_text_ms', {
        valueMs: questionSubmittedAtRef.current ? Date.now() - questionSubmittedAtRef.current : null,
        success: true,
        metadata: { transport: 'completed' },
      });
    }
    const nextFollowUps = Array.isArray(data.follow_up_questions)
      ? data.follow_up_questions.map((item) => String(item || '').trim()).filter(Boolean).slice(0, 3)
      : [];
    const generatedClosingLines = nextFollowUps.length
      ? await getGuideLines('closing', {
        language: turnLanguage,
        followUps: nextFollowUps,
        answerStyle,
      })
      : [];
    const closingLine = generatedClosingLines[0] || buildSpeechAfterAnswerPrompt(
      turnLanguage,
      nextFollowUps[0],
      getSpeechTranslator(turnLanguage)
    );
    const conversationalAnswer = `${answer}\n\n${closingLine}`.trim();
    const spokenAnswer = conversationalAnswer;
    const speechTurnId = `speech_${turnSerial}`;
    const updateSpeechTurn = (answerText, voiceState) => {
      setTurns((prev) => prev.map((turn) => (
        turn.id === speechTurnId ? { ...turn, answer: answerText, voiceState } : turn
      )));
    };
    setFollowUps(nextFollowUps);
    pendingSpokenFollowUpRef.current = nextFollowUps[0] || '';
    setTurns((prev) => [...prev, {
      id: speechTurnId,
      question,
      answer: '',
      fullAnswer: conversationalAnswer,
      voiceState: 'waiting',
      followUps: nextFollowUps,
    }]);
    setStreamingAnswer('');
    setCurrentTranscript('');
    const answerCacheKey = `speech-answer:${turnSerial}:${hashGreetingText(spokenAnswer)}`;
    const prefetchPromise = speechTtsProvider === 'google'
      ? getTextToSpeech().prefetchServerTts?.(spokenAnswer, {
        language: turnLanguage || language,
        cacheKey: answerCacheKey,
        prepareSpoken: false,
      })
      : null;
    await bridgeHandoffPromise;
    if (!mountedRef.current || activeTurnSerialRef.current !== turnSerial) return;
    Promise.resolve(prefetchPromise).catch(() => null);
    handsFreeRestartRef.current = !!handsFreeEnabledRef.current;
    let answerStarted = false;
    let fallbackRevealed = false;
    let captionTimer = null;
    let hasPlaybackProgress = false;
    const revealFallbackTimer = setTimeout(() => {
      if (!answerStarted && mountedRef.current && activeTurnSerialRef.current === turnSerial) {
        fallbackRevealed = true;
        updateSpeechTurn(conversationalAnswer, 'fallback');
      }
    }, 8000);
    // Use one native audio item for the complete visible answer. The backend
    // concatenates any Google TTS chunks before returning the MP3, so playback
    // remains continuous and can survive a screen lock without waiting for JS.
    const ok = await playAvatarLine(spokenAnswer, {
      language: turnLanguage || language,
      cacheKey: answerCacheKey,
      segmented: false,
      onStart: () => {
        answerStarted = true;
        clearTimeout(revealFallbackTimer);
        setStatus('speaking');
        if (!fallbackRevealed) updateSpeechTurn(progressiveSpeechCaption(conversationalAnswer, 0, 1), 'speaking');
        const captionStartedAt = Date.now();
        captionTimer = setInterval(() => {
          if (hasPlaybackProgress) return;
          if (!fallbackRevealed) updateSpeechTurn(
            progressiveSpeechCaption(
              conversationalAnswer,
              Date.now() - captionStartedAt,
              estimateSpeechDurationMs(conversationalAnswer)
            ),
            'speaking'
          );
        }, 350);
        if (questionSubmittedAtRef.current) {
          emitSpeechMetric('first_spoken_audio_ms', {
            valueMs: Date.now() - questionSubmittedAtRef.current,
            success: true,
            metadata: { provider: speechTtsProvider || 'unknown' },
          });
        }
      },
      onProgress: (positionMs, durationMs) => {
        if (durationMs > 0 && !fallbackRevealed) {
          hasPlaybackProgress = true;
          updateSpeechTurn(
            progressiveSpeechCaption(conversationalAnswer, positionMs, durationMs),
            'speaking'
          );
        }
      },
    });
    if (captionTimer) clearInterval(captionTimer);
    clearTimeout(revealFallbackTimer);
    if (!mountedRef.current || activeTurnSerialRef.current !== turnSerial) return;
    if (!ok) {
      updateSpeechTurn(conversationalAnswer, 'fallback');
      if (!mountedRef.current) return;
      setErrorText(t('speechChat.playbackError', 'Tara could not continue speaking, so the complete answer is shown on screen.'));
      if (handsFreeRestartRef.current && handsFreeEnabledRef.current) {
        await maybeRestartHandsFree();
        return;
      }
      handsFreeRestartRef.current = false;
      setStatus('idle');
      return;
    }
    updateSpeechTurn(conversationalAnswer, 'done');
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
    if (!billingSessionRef.current?.session_id) {
      const billingStarted = await startSpeechBillingSession();
      if (!billingStarted) return;
    }

    const turnSerial = activeTurnSerialRef.current + 1;
    activeTurnSerialRef.current = turnSerial;
    const selectedLanguage = normalizeLanguageCode(activeTurnLanguageRef.current || language);
    const turnLanguage = speechLanguageLockedRef.current
      ? selectedLanguage
      : inferSpeechTurnLanguage(spokenQuestion, selectedLanguage);
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
    setStreamingAnswer('');
    // Recognition has finished before generation starts. Release its audio
    // session now so it cannot interrupt the completed-answer TTS playback.
    await releaseSpeechRecognizer();
    const answerPromise = askInstant(spokenQuestion, turnLanguage, {
      onChunk: (delta, event) => {
        if (!isCurrentTurn()) return;
        if (!firstAnswerTextReportedRef.current) {
          firstAnswerTextReportedRef.current = true;
          emitSpeechMetric('first_answer_text_ms', {
            valueMs: questionSubmittedAtRef.current ? Date.now() - questionSubmittedAtRef.current : null,
            success: true,
            metadata: { transport: 'stream' },
          });
        }
        setStreamingAnswer(String(event?.content || delta || '').trimStart());
      },
      onReplace: (content) => {
        if (!isCurrentTurn()) return;
        setStreamingAnswer(String(content || '').trimStart());
      },
    });
    void startProcessingBridge(
      spokenQuestion,
      turnSerial,
      turnLanguage,
      questionSubmittedAtRef.current || Date.now()
    );

    try {
      const finalData = await answerPromise;
      if (!isCurrentTurn() || !finalData) return;
      await handleCompletedAnswer(spokenQuestion, finalData, turnSerial, turnLanguage);
    } catch (error) {
      if (!isCurrentTurn()) return;
      await cancelProcessingBridge('answer_error');
      setStreamingAnswer('');
      await getTextToSpeech().stop();
      throw error;
    }
  };

  const clearTranscriptSendTimer = () => {
    if (!transcriptSendTimerRef.current) return;
    clearTimeout(transcriptSendTimerRef.current);
    transcriptSendTimerRef.current = null;
  };

  const submitPendingTranscript = async (overrideText = null) => {
    const question = String(overrideText ?? pendingTranscript).trim();
    clearTranscriptSendTimer();
    setPendingTranscript('');
    if (!question || !mountedRef.current) {
      setCurrentTranscript('');
      setStatus('idle');
      return;
    }
    nativeNoSpeechRetryCountRef.current = 0;
    backendNoSpeechRetryCountRef.current = 0;
    setCurrentTranscript(question);
    setErrorText('');
    setStatus('thinking');
    questionSubmittedAtRef.current = Date.now();
    firstAnswerTextReportedRef.current = false;
    emitSpeechMetric('question_submitted', { success: true });
    Vibration.vibrate(35);
    AccessibilityInfo.announceForAccessibility?.(
      t('speechChat.questionSentA11y', 'Question sent. Tara is reading the chart.')
    );
    try {
      await runQuestionTurn(question);
    } catch (error) {
      if (!mountedRef.current) return;
      setErrorText(error?.message || t('speechChat.answerError', 'Answer failed. Please try again.'));
      setStatus('idle');
    }
  };

  const queueRecognizedQuestion = (transcript) => {
    const question = String(transcript || '').trim();
    if (!question || !mountedRef.current) return;
    clearTranscriptSendTimer();
    setPendingTranscript(question);
    setCurrentTranscript(question);
    setStatus('reviewing');
    transcriptSendTimerRef.current = setTimeout(() => {
      transcriptSendTimerRef.current = null;
      submitPendingTranscript(question);
    }, TRANSCRIPT_SEND_GRACE_MS);
  };

  const cancelPendingTranscript = () => {
    clearTranscriptSendTimer();
    setPendingTranscript('');
    setCurrentTranscript('');
    setStatus('idle');
    AccessibilityInfo.announceForAccessibility?.(
      t('speechChat.questionCancelledA11y', 'Question cancelled.')
    );
  };

  const askFollowUp = async (question) => {
    if (status !== 'idle') return;
    if (Platform.OS === 'web') getTextToSpeech().unlockWebAudio?.();
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
    processingBridgeEpochRef.current += 1;
    processingBridgeSpeakingRef.current = false;
    setProcessingBridgeCaption('');
    handsFreeRestartRef.current = false;
    startListeningInFlightRef.current = false;
    clearTranscriptSendTimer();
    setPendingTranscript('');
    setTurns((prev) => prev.map((turn) => (
      ['waiting', 'speaking'].includes(turn.voiceState) && turn.fullAnswer
        ? { ...turn, answer: turn.fullAnswer, voiceState: 'stopped' }
        : turn
    )));
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
    await releaseSpeechRecognizer();
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
    await releaseSpeechRecognizer();
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
    await releaseSpeechRecognizer();
    stopSpeechUiImmediately();
    setCurrentTranscript('');
    setErrorText('');
    setStatus('idle');
  };

  const handleMicPress = async () => {
    // This must run synchronously inside Chrome's click gesture. Awaiting
    // permission, billing, or generation first loses autoplay authorization.
    if (Platform.OS === 'web') getTextToSpeech().unlockWebAudio?.();
    try {
      logSpeechDebug('micPress', {
        status,
        listeningMode: listeningModeRef.current,
        inFlight: startListeningInFlightRef.current,
        hasRecording: Boolean(recordingRef.current),
      }).catch(() => {});
      if (IS_IOS_WEB && status !== 'listening' && !iosWebMicPrimedRef.current) {
        setErrorText('');
        setStatus('listening');
        const permissionGranted = await primeIosWebMicrophone();
        if (!permissionGranted) {
          setStatus('idle');
          return;
        }
      }
      if (status === 'listening') {
        if (handsFreeEnabledRef.current) {
          await pauseSpeechChat('main_button_while_hands_free_listening');
        } else {
          await stopListening();
        }
      } else if (status === 'reviewing') {
        cancelPendingTranscript();
        await forceStartListening();
      } else if (status === 'speaking') {
        // Barge-in: stop Tara and listen immediately without silently turning
        // off the user's hands-free preference.
        await forceStartListening();
      } else {
        await forceStartListening();
      }
    } catch (error) {
      setErrorText(error?.message || t('speechChat.genericError', 'Something went wrong. Please try again.'));
      setStatus('idle');
    }
  };

  const handleSpeechLanguageChange = async (nextLanguage) => {
    const normalized = normalizeLanguageCode(nextLanguage);
    if (
      ['transcribing', 'thinking'].includes(statusRef.current)
      || normalized === normalizeLanguageCode(activeTurnLanguageRef.current || language)
    ) return;
    const previousStatus = statusRef.current;
    const switchingInitialGreeting = previousStatus === 'speaking' && turns.length === 0;
    const switchingActiveMicrophone = previousStatus === 'listening';
    speechLanguageLockedRef.current = true;
    activeTurnLanguageRef.current = normalized;
    greetingPrefetchKeyRef.current = '';
    greetedRef.current = switchingInitialGreeting ? false : turns.length > 0;
    if (switchingInitialGreeting || switchingActiveMicrophone) setFollowUps([]);
    setErrorText('');
    setLanguage(normalized);
    storage.setSpeechLanguage(normalized).catch(() => {});
    if (switchingInitialGreeting) {
      greetingPlaybackEpochRef.current += 1;
      activeTurnSerialRef.current += 1;
      handsFreeRestartRef.current = false;
      startListeningInFlightRef.current = false;
      setAvatarSpeech({ active: false, text: '', timeline: [], positionMs: 0, durationMs: 0, audioStarted: false });
      // Wait until the English sound is fully stopped and unloaded. Starting
      // the Hindi greeting during that teardown lets the old player interrupt
      // the new one after its first word.
      await getTextToSpeech().stop();
      if (mountedRef.current) setStatus('idle');
      return;
    }
    if (switchingActiveMicrophone) {
      startListeningInFlightRef.current = false;
      await releaseSpeechRecognizer();
      setCurrentTranscript('');
      setStatus('idle');
      await wait(100);
      if (mountedRef.current) {
        await startListening({ source: 'languageChange', stopCurrentSpeech: false });
      }
    }
  };

  const speechPreparing = status === 'speaking' && avatarSpeech.active && !avatarSpeech.audioStarted;
  const nativeRecognizerStarting = status === 'listening'
    && nativeRecognizerPhase === 'starting'
    && !currentTranscript;
  const statusText = {
    idle: requiresFirstMicTap
      ? t('speechChat.statusTapForSafariMic', 'Tap the mic once to allow microphone access')
      : handsFreeEnabled
      ? t('speechChat.statusIdleHandsFree', 'Tap the mic and AstroRoshni will keep listening after each answer')
      : t('speechChat.statusIdle', 'Tap the mic and ask your question'),
    listening: nativeRecognizerStarting
      ? t('speechChat.statusStartingRecognizer', 'Starting microphone...')
      : handsFreeEnabled
        ? t('speechChat.statusListeningHandsFree', 'Speak now. Tap pause if you want to stop listening.')
        : t('speechChat.statusListening', 'Listening... tap again when done'),
    transcribing: t('speechChat.statusTranscribing', 'Finishing your question...'),
    reviewing: t('speechChat.statusReviewing', 'Check your question — sending shortly'),
    thinking: t('speechChat.statusThinking', 'Reading the chart...'),
    speaking: speechPreparing
      ? t('speechChat.statusPreparingSpeech', 'Tara is about to speak...')
      : t('speechChat.statusSpeaking', 'Speaking the answer... tap pause to stop hands-free'),
  }[status] || '';

  const busy = ['transcribing', 'thinking'].includes(status) || speechPreparing || nativeRecognizerStarting;
  const languageSwitchDisabled = ['transcribing', 'thinking'].includes(status);
  const screenPalette = {
    background: colors.background,
    backgroundAlt: colors.backgroundSecondary || colors.background,
    surface: colors.surface,
    surfaceStrong: colors.surfaceRaised || colors.surface,
    surfaceMuted: colors.surfaceMuted || colors.backgroundSecondary || colors.surface,
    border: colors.cardBorder || colors.strokeMuted || colors.border,
    text: colors.text,
    textSecondary: colors.textSecondary,
    primary: colors.primary,
    primaryStrong: colors.primaryStrong || colors.primary,
    onPrimary: colors.onPrimary || colors.textInverse || colors.text,
    accent: colors.secondary || colors.primary,
    selectionSurface: colors.selectionSurface || colors.surfaceMuted,
    selectionControl: colors.selectionControl || colors.selectionSurface || colors.surfaceMuted,
    selectionBorder: colors.selectionBorder || colors.primary,
    selectionText: colors.selectionText || colors.text,
    selectionTextMuted: colors.selectionTextMuted || colors.textSecondary,
    glow: colors.cosmicGlow || colors.selectionSurface || colors.surfaceMuted,
    line: colors.strokeMuted || colors.cardBorder || colors.border,
  };
  const stageProfile = {
    idle: {
      eyebrow: t('speechChat.stageEyebrowIdle', 'Voice Chamber'),
      headline: t('speechChat.stageHeadlineIdle', 'Ask Tara anything'),
      chamberColors: [screenPalette.surfaceStrong, screenPalette.surface, screenPalette.backgroundAlt],
      haloOuter: screenPalette.glow,
      haloInner: screenPalette.selectionSurface,
      line: screenPalette.line,
      star: colors.accent || screenPalette.primary,
      dot: screenPalette.accent,
    },
    listening: {
      eyebrow: t('speechChat.stageEyebrowListening', 'Listening'),
      headline: t('speechChat.stageHeadlineListening', 'Speak now'),
      chamberColors: [screenPalette.surfaceStrong, screenPalette.selectionSurface, screenPalette.backgroundAlt],
      haloOuter: screenPalette.selectionSurface,
      haloInner: screenPalette.selectionControl,
      line: screenPalette.selectionBorder,
      star: screenPalette.accent,
      dot: screenPalette.primary,
    },
    thinking: {
      eyebrow: t('speechChat.stageEyebrowThinking', 'Reading The Chart'),
      headline: t('speechChat.stageHeadlineThinking', 'Patterns are settling'),
      chamberColors: [screenPalette.surfaceStrong, screenPalette.surfaceMuted, screenPalette.backgroundAlt],
      haloOuter: screenPalette.glow,
      haloInner: screenPalette.selectionSurface,
      line: screenPalette.line,
      star: colors.accent || screenPalette.primary,
      dot: screenPalette.accent,
    },
    speaking: {
      eyebrow: t('speechChat.stageEyebrowSpeaking', 'Speaking'),
      headline: t('speechChat.stageHeadlineSpeaking', 'Tara is answering'),
      chamberColors: [screenPalette.surfaceStrong, screenPalette.selectionSurface, screenPalette.backgroundAlt],
      haloOuter: screenPalette.glow,
      haloInner: screenPalette.selectionControl,
      line: screenPalette.selectionBorder,
      star: screenPalette.primary,
      dot: colors.accent || screenPalette.accent,
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

  useEffect(() => {
    if (!statusText) return;
    AccessibilityInfo.announceForAccessibility?.(statusText);
  }, [status]);

  useEffect(() => {
    if (!errorText) return;
    Vibration.vibrate([0, 70, 45, 70]);
    AccessibilityInfo.announceForAccessibility?.(errorText);
  }, [errorText]);

  return (
    <SafeAreaView
      edges={['top']}
      style={[styles.safeArea, { backgroundColor: colors.headerSurface }]}
    >
      <FocusedStatusBar backgroundColor={colors.headerSurface} barStyle="light-content" />
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
              {t('chat.modeIntro.speech.name', 'Talk To Tara')}
            </Text>
            <Text style={[styles.subtitle, { color: screenPalette.textSecondary }]}>
              {birthData?.name
                ? t('speechChat.screenSubtitleWithChart', {
                    name: birthData.name,
                    defaultValue: `Voice consultation for ${birthData.name}`,
                  })
                : t('speechChat.screenSubtitleDefault', 'A live voice conversation with Tara')}
            </Text>
          </View>
          <View style={[
            styles.liveBadge,
            {
              backgroundColor: screenPalette.selectionSurface,
              borderColor: screenPalette.selectionBorder,
            },
          ]}>
            <View style={[styles.liveDot, { backgroundColor: screenPalette.primary }]} />
            <Text style={[styles.liveBadgeText, { color: screenPalette.selectionText }]}>
              {t('speechChat.liveBadge', 'Live')}
            </Text>
          </View>
          <TouchableOpacity
            onPress={() => navigation.navigate('AccountSecurity')}
            style={[styles.privacyButton, { borderColor: screenPalette.border, backgroundColor: screenPalette.surfaceStrong }]}
            accessibilityRole="button"
            accessibilityLabel={t('speechChat.privacyControls', 'Voice privacy and saved chat controls')}
          >
            <Ionicons name="shield-checkmark-outline" size={18} color={screenPalette.textSecondary} />
          </TouchableOpacity>
        </View>

        <View style={[styles.callMeter, { borderColor: screenPalette.border, backgroundColor: screenPalette.surfaceStrong }]}>
          <View style={styles.callMeterItem}>
            <Ionicons name="time-outline" size={15} color={screenPalette.primary} />
            <Text style={[styles.callMeterText, { color: screenPalette.text }]}>
              {formatCallTime(callElapsedSeconds)}
            </Text>
          </View>
          <View style={[styles.callMeterDivider, { backgroundColor: screenPalette.line }]} />
          <Text style={[styles.callMeterSubtext, { color: screenPalette.textSecondary }]}>
            {speechPerMinuteCost != null
              ? `${speechPerMinuteCost} credits/min`
              : 'Talk To Tara billing'}
            {callRemainingSeconds != null ? ` · ${formatCallTime(callRemainingSeconds)} left` : ''}
          </Text>
        </View>

        <View
          style={[styles.languageBar, { borderColor: screenPalette.border, backgroundColor: screenPalette.surfaceStrong }]}
          accessibilityRole="radiogroup"
          accessibilityLabel={t('speechChat.languageLabel', 'Conversation language')}
        >
          <View style={styles.languageLabelWrap}>
            <Ionicons name="language-outline" size={16} color={screenPalette.primary} />
            <Text style={[styles.languageLabel, { color: screenPalette.textSecondary }]}>
              {t('speechChat.languageLabel', 'Conversation language')}
            </Text>
          </View>
          <View style={[styles.languageToggle, { borderColor: screenPalette.border }]}>
            {SPEECH_LANGUAGE_OPTIONS.map((option) => {
              const selected = normalizeLanguageCode(language) === option.key;
              const label = t(option.labelKey, option.fallback);
              return (
                <TouchableOpacity
                  key={option.key}
                  disabled={languageSwitchDisabled}
                  onPress={() => handleSpeechLanguageChange(option.key)}
                  style={[
                    styles.languageOption,
                    selected && {
                      backgroundColor: screenPalette.selectionSurface,
                      borderColor: screenPalette.selectionBorder,
                    },
                    languageSwitchDisabled && !selected && styles.optionDisabled,
                  ]}
                  accessibilityRole="radio"
                  accessibilityState={{ selected, checked: selected, disabled: languageSwitchDisabled }}
                  accessibilityLabel={label}
                >
                  <Text style={[
                    styles.languageOptionText,
                    { color: selected ? screenPalette.selectionText : screenPalette.textSecondary },
                  ]}>
                    {label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        <View
          style={[styles.answerStyleBar, { borderColor: screenPalette.border, backgroundColor: screenPalette.surfaceStrong }]}
          accessibilityRole="radiogroup"
          accessibilityLabel={t('chat.answerStyle.label', 'Answer style')}
        >
          <Text style={[styles.answerStyleLabel, { color: screenPalette.textSecondary }]}>
            {t('chat.answerStyle.label', 'Answer style')}
          </Text>
          <View style={[styles.answerStyleToggle, { borderColor: screenPalette.border }]}>
            {['simple', 'technical'].map((styleKey) => {
              const selected = answerStyle === styleKey;
              const label = styleKey === 'simple'
                ? t('chat.answerStyle.simple', 'Simple')
                : t('chat.answerStyle.technical', 'Technical');
              return (
                <TouchableOpacity
                  key={styleKey}
                  onPress={() => {
                    setAnswerStyle(styleKey);
                    chatAPI.updateAnswerStylePreference(styleKey).catch(() => {});
                  }}
                  style={[
                    styles.answerStyleOption,
                    selected && {
                      backgroundColor: screenPalette.selectionSurface,
                      borderColor: screenPalette.selectionBorder,
                    },
                  ]}
                  accessibilityRole="radio"
                  accessibilityState={{ selected, checked: selected }}
                  accessibilityLabel={label}
                >
                  <Text style={[
                    styles.answerStyleOptionText,
                    { color: selected ? screenPalette.selectionText : screenPalette.textSecondary },
                  ]}>
                    {label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        <View style={styles.mainColumn}>
        <ScrollView ref={scrollRef} style={styles.conversation} contentContainerStyle={styles.conversationContent}>
          {turns.map((turn, index) => (
            <View key={`${turn.question}_${index}`} style={styles.turnBlock}>
              <View style={[styles.userBubble, { backgroundColor: screenPalette.selectionSurface }]}>
                <Text style={[styles.bubbleLabel, { color: screenPalette.textSecondary }]}>You asked</Text>
                <Text style={[styles.bubbleText, { color: screenPalette.text }]}>{turn.question}</Text>
              </View>
              {turn.answer ? (
                <View style={[styles.answerBubble, { backgroundColor: screenPalette.surfaceStrong, borderColor: screenPalette.border }]}>
                  <Text style={[styles.bubbleLabel, { color: screenPalette.textSecondary }]}>
                    {turn.voiceState === 'speaking'
                      ? t('speechChat.speaking', 'Tara is speaking')
                      : t('speechChat.answerBubbleLabel', 'Tara answered')}
                  </Text>
                  <Text style={[styles.bubbleText, { color: screenPalette.text }]}>{turn.answer}</Text>
                </View>
              ) : null}
            </View>
          ))}

          {status === 'reviewing' ? (
            <View style={[styles.reviewCard, { borderColor: screenPalette.selectionBorder, backgroundColor: screenPalette.surfaceStrong }]}> 
              <Text style={[styles.bubbleLabel, { color: screenPalette.textSecondary }]}> 
                {t('speechChat.reviewTitle', 'Check your question')}
              </Text>
              <TextInput
                value={pendingTranscript}
                onFocus={clearTranscriptSendTimer}
                onChangeText={(value) => {
                  clearTranscriptSendTimer();
                  setPendingTranscript(value);
                  setCurrentTranscript(value);
                }}
                multiline
                style={[styles.reviewInput, { color: screenPalette.text, borderColor: screenPalette.border }]}
                placeholder={t('speechChat.reviewPlaceholder', 'Edit the transcript if needed')}
                placeholderTextColor={screenPalette.textSecondary}
                accessibilityLabel={t('speechChat.reviewPlaceholder', 'Edit the transcript if needed')}
              />
              <View style={styles.reviewActions}>
                <TouchableOpacity
                  onPress={cancelPendingTranscript}
                  style={[styles.reviewSecondaryButton, { borderColor: screenPalette.border }]}
                  accessibilityRole="button"
                >
                  <Text style={[styles.reviewSecondaryText, { color: screenPalette.textSecondary }]}> 
                    {t('speechChat.cancelQuestion', 'Cancel')}
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={() => submitPendingTranscript()}
                  disabled={!pendingTranscript.trim()}
                  style={[styles.reviewPrimaryButton, { backgroundColor: screenPalette.primary }, !pendingTranscript.trim() && styles.optionDisabled]}
                  accessibilityRole="button"
                >
                  <Text style={styles.reviewPrimaryText}>{t('speechChat.sendNow', 'Send now')}</Text>
                </TouchableOpacity>
              </View>
            </View>
          ) : currentTranscript || status === 'listening' ? (
            <Animated.View
              style={[
                styles.liveCard,
                {
                  borderColor: screenPalette.selectionBorder,
                  backgroundColor: screenPalette.surfaceStrong,
                  shadowColor: screenPalette.primary,
                  shadowOpacity: status === 'idle' ? 0.08 : transcriptGlow,
                  transform: [{ scale: transcriptScale }],
                },
              ]}
            >
              <Text style={[styles.bubbleLabel, { color: screenPalette.textSecondary }]}>
                {status === 'listening' ? t('speechChat.heardSoFar', 'Heard so far') : t('speechChat.currentQuestion', 'Current question')}
              </Text>
              <Text style={[styles.bubbleText, { color: screenPalette.text }]}>
                {currentTranscript || t(
                  'speechChat.listeningLivePlaceholder',
                  normalizeLanguageCode(language) === 'hindi' ? 'सुन रही हूँ…' : 'Listening…'
                )}
              </Text>
            </Animated.View>
          ) : null}

          {processingBridgeCaption && status === 'thinking' ? (
            <Animated.View style={[styles.answerBubble, { backgroundColor: screenPalette.surfaceStrong, borderColor: screenPalette.border }]}>
              <Text style={[styles.bubbleLabel, { color: screenPalette.textSecondary }]}>
                {t('speechChat.answering', 'Tara is answering')}
              </Text>
              <Text style={[styles.bubbleText, { color: screenPalette.text }]}>{processingBridgeCaption}</Text>
            </Animated.View>
          ) : null}
        </ScrollView>

        {followUps.length > 0 && status === 'idle' ? (
          <View style={styles.followUpRow}>
            {followUps.map((item) => (
              <TouchableOpacity key={item} onPress={() => askFollowUp(item)} style={[styles.followUpChip, { borderColor: screenPalette.border, backgroundColor: screenPalette.surfaceStrong }]}>
                <Text style={[styles.followUpText, { color: screenPalette.text }]} numberOfLines={2}>{item}</Text>
              </TouchableOpacity>
            ))}
          </View>
        ) : null}

        {errorText ? <Text style={[styles.errorText, { color: colors.error }]}>{errorText}</Text> : null}
        </View>

        <LinearGradient
          colors={[screenPalette.surfaceStrong, screenPalette.surface, screenPalette.backgroundAlt]}
          style={[
            styles.controlsShell,
            compactVoiceLayout && styles.controlsShellCompact,
            tinyVoiceLayout && styles.controlsShellTiny,
            {
              borderColor: screenPalette.border,
              paddingBottom: Math.max(4, insets.bottom || 0),
            },
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
              <View style={[styles.moonArcOuter, { borderColor: stageProfile.line }]} />
              <View style={[styles.moonArcInner, { borderColor: stageProfile.line }]} />
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

              <Animated.View
                style={[
                  styles.voiceStateOrb,
                  compactVoiceLayout && styles.voiceStateOrbCompact,
                  tinyVoiceLayout && styles.voiceStateOrbTiny,
                  {
                    backgroundColor: screenPalette.selectionSurface,
                    borderColor: screenPalette.selectionBorder,
                    shadowColor: screenPalette.primary,
                    transform: [{ scale: status === 'idle' ? 1 : thinkingScale }],
                  },
                ]}
              >
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
                  size={tinyVoiceLayout ? 32 : compactVoiceLayout ? 38 : 44}
                  color={screenPalette.selectionText}
                />
                <View style={styles.voiceWave}>
                  {[0.52, 0.82, 1, 0.82, 0.52].map((scale, index) => (
                    <Animated.View
                      key={`${scale}_${index}`}
                      style={[
                        styles.voiceWaveBar,
                        {
                          backgroundColor: screenPalette.primary,
                          transform: [{
                            scaleY: status === 'listening'
                              ? micLevelAnim.interpolate({
                                  inputRange: [0, 1],
                                  outputRange: [Math.max(0.18, scale * 0.35), Math.min(1, 0.58 + scale * 0.42)],
                                })
                              : status === 'idle'
                                ? scale
                                : thinkingScale,
                          }],
                        },
                      ]}
                    />
                  ))}
                </View>
              </Animated.View>
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
                      backgroundColor: handsFreeEnabled
                        ? screenPalette.selectionSurface
                        : screenPalette.surfaceMuted,
                      borderColor: handsFreeEnabled
                        ? screenPalette.selectionBorder
                        : screenPalette.border,
                    },
                  ]}
              >
                <Ionicons
                  name={handsFreeEnabled ? 'radio-outline' : 'radio-button-off-outline'}
                  size={16}
                  color={handsFreeEnabled ? screenPalette.selectionText : screenPalette.textSecondary}
                />
                <Text style={[
                  styles.handsFreeInlineText,
                  { color: handsFreeEnabled ? screenPalette.selectionText : screenPalette.text },
                ]}>
                  {t('speechChat.handsFreeLabel', 'Hands-free follow-up')}
                </Text>
                <Text style={[styles.handsFreeInlineState, { color: handsFreeEnabled ? screenPalette.selectionText : screenPalette.textSecondary }]}>
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
                  { shadowColor: screenPalette.primary },
                ]}
              >
                <LinearGradient
                  colors={status === 'listening'
                    ? [screenPalette.accent, screenPalette.primary]
                    : [screenPalette.primaryStrong, screenPalette.primary]}
                  style={styles.chamberMicButton}
                >
                  {busy ? (
                    <ActivityIndicator color={screenPalette.onPrimary} />
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
                      color={screenPalette.onPrimary}
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
  },
  liveBadgeText: {
    fontSize: 12,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  privacyButton: {
    width: 34,
    height: 34,
    borderWidth: 1,
    borderRadius: 17,
    alignItems: 'center',
    justifyContent: 'center',
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
  },
  callMeterSubtext: {
    flex: 1,
    fontSize: 12,
    fontWeight: '700',
  },
  languageBar: {
    minHeight: 44,
    marginBottom: 6,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexShrink: 0,
  },
  languageLabelWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flexShrink: 1,
  },
  languageLabel: {
    fontSize: 12,
    fontWeight: '800',
  },
  languageToggle: {
    padding: 2,
    borderWidth: 1,
    borderRadius: 999,
    flexDirection: 'row',
  },
  languageOption: {
    minWidth: 70,
    minHeight: 34,
    paddingHorizontal: 9,
    borderWidth: 1,
    borderColor: 'transparent',
    borderRadius: 999,
    alignItems: 'center',
    justifyContent: 'center',
  },
  languageOptionText: {
    fontSize: 12,
    fontWeight: '800',
  },
  optionDisabled: {
    opacity: 0.5,
  },
  answerStyleBar: {
    minHeight: 50,
    marginBottom: 6,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexShrink: 0,
  },
  answerStyleLabel: {
    fontSize: 12,
    fontWeight: '800',
  },
  answerStyleToggle: {
    padding: 2,
    borderWidth: 1,
    borderRadius: 999,
    flexDirection: 'row',
  },
  answerStyleOption: {
    minWidth: 78,
    minHeight: 44,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: 'transparent',
    borderRadius: 999,
    alignItems: 'center',
    justifyContent: 'center',
  },
  answerStyleOptionText: {
    fontSize: 12,
    fontWeight: '800',
  },
  conversation: {
    flex: 1,
  },
  conversationContent: {
    paddingVertical: 8,
    gap: 10,
    flexGrow: 1,
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
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 8 },
    elevation: 4,
  },
  reviewCard: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
    gap: 10,
  },
  reviewInput: {
    minHeight: 56,
    maxHeight: 120,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
    lineHeight: 21,
    textAlignVertical: 'top',
  },
  reviewActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 9,
  },
  reviewSecondaryButton: {
    minHeight: 40,
    paddingHorizontal: 14,
    borderWidth: 1,
    borderRadius: 999,
    alignItems: 'center',
    justifyContent: 'center',
  },
  reviewSecondaryText: {
    fontSize: 13,
    fontWeight: '800',
  },
  reviewPrimaryButton: {
    minHeight: 40,
    paddingHorizontal: 16,
    borderRadius: 999,
    alignItems: 'center',
    justifyContent: 'center',
  },
  reviewPrimaryText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '800',
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
    height: 150,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 2,
    overflow: 'visible',
  },
  voiceStageCompact: {
    height: 124,
    maxWidth: 220,
    marginBottom: 0,
  },
  voiceStageTiny: {
    height: 104,
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
  voiceStateOrb: {
    width: 116,
    height: 116,
    borderRadius: 58,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    shadowOpacity: 0.12,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 8 },
    elevation: 4,
  },
  voiceStateOrbCompact: {
    width: 96,
    height: 96,
    borderRadius: 48,
  },
  voiceStateOrbTiny: {
    width: 82,
    height: 82,
    borderRadius: 41,
    gap: 5,
  },
  voiceWave: {
    height: 22,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
  },
  voiceWaveBar: {
    width: 4,
    height: 18,
    borderRadius: 999,
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
  },
  sparkleHorizontal: {
    position: 'absolute',
    width: 18,
    height: 2,
    borderRadius: 999,
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
  },
  sparkleDotFour: {
    top: 262,
    right: 56,
    width: 4,
    height: 4,
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
