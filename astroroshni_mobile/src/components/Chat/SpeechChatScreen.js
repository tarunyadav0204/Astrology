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
  View,
  ScrollView,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { chatAPI, pricingAPI, speechAPI } from '../../services/api';
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
const isSpeechUnavailableMessage = (message) => {
  const value = String(message || '').toLowerCase();
  return value.includes('speech recognition is not available')
    || value.includes('use the test question button below')
    || value.includes('expo go cannot access the native speech recognizer')
    || value.includes('needs a development build');
};

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
const DEV_SPEECH_TEST_QUESTIONS = [
  'When will I buy a house?',
  'When will I get a new job?',
  'What is my marriage timing over the next two years?',
];
const DEV_SPEECH_TEST_QUESTIONS_HI = [
  'मैं घर कब खरीदूँगा?',
  'मुझे नई नौकरी कब मिलेगी?',
  'अगले दो सालों में मेरी शादी का समय क्या है?',
];

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

const splitSpeechTokens = (text) => {
  const raw = String(text || '').trim();
  if (!raw) return [];

  return raw
    .split(/\s+/)
    .flatMap((chunk) => {
      const parts = [];
      let working = chunk;

      const leading = working.match(/^[("'\[]+/);
      if (leading?.[0]) {
        parts.push(leading[0]);
        working = working.slice(leading[0].length);
      }

      const trailing = working.match(/[.,!?;:…।]+$/);
      const trailingText = trailing?.[0] || '';
      if (trailingText) {
        working = working.slice(0, -trailingText.length);
      }

      if (working) parts.push(working);
      if (trailingText) parts.push(trailingText);
      return parts;
    })
    .filter(Boolean);
};

const estimateSyllables = (word) => {
  const cleaned = String(word || '')
    .toLowerCase()
    .replace(/[^a-z0-9\u00c0-\u024f\u0900-\u097f]/g, '');

  if (!cleaned) return 1;

  const vowelGroups =
    cleaned.match(/[aeiouy\u0904-\u094c\u0962\u0963]+/g)?.length ||
    cleaned.match(/[aeiouy]+/g)?.length ||
    1;

  return clamp(vowelGroups, 1, 5);
};

const punctuationPauseMs = (token) => {
  const value = String(token || '');
  if (!value) return 0;
  if (/[.?!…।]+/.test(value)) return 360;
  if (/[;:]/.test(value)) return 250;
  if (/[,]/.test(value)) return 190;
  return 0;
};

const buildMouthTimeline = (text) => {
  const tokens = splitSpeechTokens(text);
  if (!tokens.length) return [{ frame: 0, duration: 180 }];

  const timeline = [];

  tokens.forEach((token, index) => {
    const pauseMs = punctuationPauseMs(token);
    if (pauseMs > 0) {
      timeline.push({ frame: 0, duration: pauseMs });
      return;
    }

    const word = String(token || '');
    const syllables = estimateSyllables(word);
    const letters = word.replace(/[^0-9\p{L}]/gu, '').length || word.length || 1;
    const strongWord = syllables >= 3 || letters >= 7 || /\d/.test(word);
    const mediumWord = !strongWord && (syllables >= 2 || letters >= 4);

    const pattern = strongWord
      ? [1, 2, 1, 3, 2, 1, 0]
      : mediumWord
        ? [1, 2, 1, 0]
        : [1, 0];

    const totalWordMs = clamp(
      110 + letters * 14 + syllables * 34 + (strongWord ? 32 : mediumWord ? 18 : 0),
      170,
      420
    );

    const weights = pattern.map((frame) => {
      if (frame === 3) return 1.18;
      if (frame === 2) return 1.02;
      if (frame === 1) return 0.92;
      return 0.72;
    });
    const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);

    pattern.forEach((frame, frameIndex) => {
      const duration = Math.round((totalWordMs * weights[frameIndex]) / totalWeight);
      timeline.push({ frame, duration });
    });

    const nextToken = tokens[index + 1];
    if (!punctuationPauseMs(nextToken)) {
      timeline.push({ frame: 0, duration: clamp(55 + syllables * 10, 60, 120) });
    }
  });

  timeline.push({ frame: 0, duration: 180 });
  return timeline;
};

const buildFramePattern = (intensity) => {
  if (intensity >= 3) return [1, 2, 3, 2, 1, 0];
  if (intensity >= 2) return [1, 2, 1, 0];
  return [1, 0];
};

const getMouthFrameFromPlaybackTimeline = (timeline, positionMs, durationMs = 0) => {
  if (!Array.isArray(timeline) || !timeline.length) return 0;
  const now = Math.max(0, Number(positionMs) || 0);

  let currentIndex = -1;
  for (let i = 0; i < timeline.length; i += 1) {
    const start = Number(timeline[i]?.start_ms);
    if (!Number.isFinite(start)) continue;
    if (start <= now) currentIndex = i;
    else break;
  }

  if (currentIndex < 0) return 0;

  const current = timeline[currentIndex];
  const currentStart = Number(current?.start_ms) || 0;
  const nextStartRaw = Number(timeline[currentIndex + 1]?.start_ms);
  const nextStart = Number.isFinite(nextStartRaw)
    ? nextStartRaw
    : Math.max(
        currentStart + clamp(Number(current?.estimated_word_ms) || 180, 120, 340),
        Number(durationMs) || currentStart + 260
      );
  const activeSpan = Math.max(120, nextStart - currentStart);
  const progress = clamp((now - currentStart) / activeSpan, 0, 0.999);
  const pattern = buildFramePattern(Number(current?.intensity) || 1);
  const patternIndex = Math.min(pattern.length - 1, Math.floor(progress * pattern.length));
  return pattern[patternIndex];
};

const getMouthFrameFromAudioProgress = (speechText, positionMs, durationMs) => {
  const frames = buildMouthTimeline(speechText);
  if (!frames.length) return 0;

  const totalFrameMs = frames.reduce((sum, item) => sum + Math.max(1, Number(item?.duration) || 0), 0);
  const totalAudioMs = Math.max(1, Number(durationMs) || 0);
  const scaledNow = clamp((Math.max(0, Number(positionMs) || 0) / totalAudioMs) * totalFrameMs, 0, totalFrameMs - 1);

  let cursor = 0;
  for (const item of frames) {
    const duration = Math.max(1, Number(item?.duration) || 0);
    if (scaledNow < cursor + duration) {
      return Number(item?.frame) || 0;
    }
    cursor += duration;
  }

  return Number(frames[frames.length - 1]?.frame) || 0;
};

const TARA_BASE = require('../../assets/tara/base_head_body.png');
const TARA_EYES_OPEN = require('../../assets/tara/eyes_open.png');
const TARA_EYES_CLOSED = require('../../assets/tara/eyes_closed.png');
const TARA_MOUTH_CLOSED = require('../../assets/tara/mouth_closed.png');
const TARA_MOUTH_SMALL = require('../../assets/tara/mouth_small_open.png');
const TARA_MOUTH_MEDIUM = require('../../assets/tara/mouth_medium_open.png');
const TARA_MOUTH_WIDE = require('../../assets/tara/mouth_wide_open.png');

function TaraSpeakingAvatar({ status, isDark, speechText, speechActive, speechTimeline, speechPositionMs, speechDurationMs, speechAudioStarted }) {
  const [blinkClosed, setBlinkClosed] = useState(false);
  const [mouthFrame, setMouthFrame] = useState(0);
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
    const hasPlaybackTimeline = Array.isArray(speechTimeline) && speechTimeline.length > 0;

    if (speechActive && hasPlaybackTimeline) {
      if (!speechAudioStarted) {
        setMouthFrame(0);
        return undefined;
      }

      setMouthFrame(
        getMouthFrameFromPlaybackTimeline(speechTimeline, speechPositionMs, speechDurationMs)
      );
      return undefined;
    }

    if (speechActive && speechAudioStarted && Number(speechDurationMs) > 0) {
      setMouthFrame(
        getMouthFrameFromAudioProgress(speechText, speechPositionMs, speechDurationMs)
      );
      return undefined;
    }

    setMouthFrame(0);
    return undefined;
  }, [speechActive, speechText, speechTimeline, speechPositionMs, speechDurationMs, speechAudioStarted]);

  useEffect(() => {
    bobAnim.stopAnimation();
    bobAnim.setValue(0);
  }, [bobAnim, status]);

  const translateY = bobAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, status === 'speaking' ? -3 : -1.5],
  });
  const mouthSource =
    mouthFrame >= 3
      ? TARA_MOUTH_WIDE
      : mouthFrame >= 2
        ? TARA_MOUTH_MEDIUM
        : mouthFrame >= 1
          ? TARA_MOUTH_SMALL
        : TARA_MOUTH_CLOSED;

  return (
    <Animated.View style={[styles.avatarWrap, { transform: [{ translateY }] }]}>
      <View style={styles.avatarImageStage}>
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
  const scrollRef = useRef(null);
  const handsFreeRestartRef = useRef(false);
  const greetedRef = useRef(false);
  const thinkingLeadInIndexRef = useRef(0);
  const devQuestionIndexRef = useRef(0);
  const pulseAnim = useRef(new Animated.Value(0)).current;
  const cardPulseAnim = useRef(new Animated.Value(0)).current;
  const sparkleAnims = useRef(
    Array.from({ length: 8 }, () => new Animated.Value(0))
  ).current;

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
    // Speech chat lip sync depends on timed backend audio, so prefer Google TTS here.
    getTextToSpeech().setSpeechProvider(SPEECH_CHAT_TTS_PROVIDER);

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
        const configuredSpeechTtsProvider =
          String(res?.data?.features?.speech_tts_provider || '').trim().toLowerCase() || null;
        const nextSpeechProvider = SPEECH_CHAT_TTS_PROVIDER;
        console.log('[SpeechChat] pricing/features resolved', {
          speechChatCost: val,
          configuredSpeechTtsProvider,
          speechTtsProvider: nextSpeechProvider,
          rawFeatures: res?.data?.features || null,
        });
        getTextToSpeech().setSpeechProvider(nextSpeechProvider);
        if (!cancelledPricing && mountedRef.current) {
          setSpeechChatCost(val);
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
      try {
        speechRecognition.cancelListening();
      } catch {
        // ignore teardown errors
      }
      handsFreeRestartRef.current = false;
      setAvatarSpeech({ active: false, text: '', timeline: [], positionMs: 0, durationMs: 0, audioStarted: false });
      getTextToSpeech().stop();
    };
  }, []);

  useEffect(() => {
    getTextToSpeech().setSpeechProvider(speechTtsProvider);
  }, [speechTtsProvider]);

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
  }, [birthData?.id]);

  useEffect(() => {
    if (greetedRef.current || !birthData?.name || status !== 'idle') return;
    if (!speechTtsReady) return;

    const greet = async () => {
      greetedRef.current = true;
      const chartName = String(birthData?.name || '').trim();
      const trimmedUserName = String(userName || '').trim();
      const fallbackGreeting = trimmedUserName
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
      const guideLines = await getGuideLines('greeting');
      const greeting = guideLines[0] || fallbackGreeting;

      setStatus('speaking');
      await speakWithAvatar(greeting, {
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
  }, [birthData?.name, language, speechTtsReady, status, t, userName]);

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
    setAvatarSpeech({ active: false, text: '', timeline: [], positionMs: 0, durationMs: 0, audioStarted: false });
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
      throw new Error(
        t(
          'speechChat.devNativeUnavailable',
          'Speech recognition is not available in this emulator/build right now. Use the test question button below to simulate a speech turn.'
        )
      );
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
        await runQuestionTurn(finalTranscript);
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

    setAvatarSpeech({
      active: true,
      text: spoken,
      timeline: [],
      positionMs: 0,
      durationMs: 0,
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
        ...ttsOptions,
        onTimeline: (timeline) => {
          if (!mountedRef.current) return;
          console.log('[SpeechChat] received playback timeline', {
            count: Array.isArray(timeline) ? timeline.length : 0,
            first: Array.isArray(timeline) && timeline.length ? timeline[0] : null,
            last: Array.isArray(timeline) && timeline.length ? timeline[timeline.length - 1] : null,
          });
          setAvatarSpeech((prev) => ({
            ...prev,
            timeline: Array.isArray(timeline) ? timeline : [],
            positionMs: 0,
            durationMs: 0,
            audioStarted: false,
          }));
        },
        onProgress: (positionMs, durationMs) => {
          if (!mountedRef.current) return;
          setAvatarSpeech((prev) => ({
            ...prev,
            positionMs: Number(positionMs) || 0,
            durationMs: Number(durationMs) || 0,
            audioStarted:
              prev.audioStarted
              || Number(positionMs) > 0
              || Number(durationMs) > 0,
          }));
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
    const i = thinkingLeadInIndexRef.current % THINKING_HANDOFF_KEYS.length;
    thinkingLeadInIndexRef.current += 1;
    const phrase = t(THINKING_HANDOFF_KEYS[i], THINKING_HANDOFF_DEFAULTS[i]);
    try {
      await speakWithAvatar(phrase, { language });
    } catch {
      // ignore short transition TTS failures
    }
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

  const askInstant = async (question) => {
    let activeSessionId = await ensureSession();
    if (!activeSessionId) throw new Error(t('speechChat.sessionError', 'Could not start a speech chat session.'));
    const buildAskBody = (sid) => ({
      session_id: sid,
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

  const handleCompletedAnswer = async (question, data) => {
    const answer = String(data.content || '').trim();
    const nextFollowUps = Array.isArray(data.follow_up_questions)
      ? data.follow_up_questions.map((item) => String(item || '').trim()).filter(Boolean).slice(0, 3)
      : [];
    const closingLines = await getGuideLines('closing', {
      question,
      followUps: nextFollowUps,
    });
    const closingLine = closingLines[0]
      || t('speechChat.afterAnswerPrompt', "If you'd like, ask me another question.");
    const spokenAnswer = `${answer} ${closingLine}`.trim();
    setFollowUps(nextFollowUps);
    setTurns((prev) => [...prev, { question, answer, followUps: nextFollowUps }]);
    setCurrentTranscript('');
    setStatus('speaking');
    handsFreeRestartRef.current = !!handsFreeEnabled;
    await speakWithAvatar(spokenAnswer, {
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

  const runQuestionTurn = async (question) => {
    const spokenQuestion = String(question || '').trim();
    if (!spokenQuestion) return;

    const answerPromise = askInstant(spokenQuestion);
    let answerSettled = false;
    let answerError = null;

    answerPromise
      .then(() => {
        answerSettled = true;
      })
      .catch((error) => {
        answerSettled = true;
        answerError = error;
      });

    const guideLines = await getGuideLines('processing', { question: spokenQuestion });
    if (!answerSettled) {
      if (guideLines.length) {
        const extendedLines = guideLines.length > 2
          ? [...guideLines, guideLines[guideLines.length - 2], guideLines[guideLines.length - 1]]
          : guideLines;
        for (let index = 0; index < extendedLines.length; index += 1) {
          if (!mountedRef.current || answerSettled) break;
          await playAvatarLine(extendedLines[index]);
          if (!mountedRef.current || answerSettled) break;
          await wait(index === 0 ? 140 : index < guideLines.length ? 220 : 320);
        }
      } else {
        await speakThinkingHandoff();
      }
    }

    try {
      const finalData = await answerPromise;
      if (!mountedRef.current || !finalData) return;
      await handleCompletedAnswer(spokenQuestion, finalData);
    } catch (error) {
      if (!mountedRef.current) return;
      throw answerError || error;
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

  const runDevSampleQuestion = async () => {
    if (!birthData) {
      Alert.alert(
        t('speechChat.profileRequired', 'Birth chart required'),
        t('speechChat.profileRequiredBody', 'Please select or create a birth chart before using speech chat.')
      );
      return;
    }

    const sampleQuestions =
      String(language || '').toLowerCase().startsWith('hi')
        ? DEV_SPEECH_TEST_QUESTIONS_HI
        : DEV_SPEECH_TEST_QUESTIONS;
    const question = sampleQuestions[devQuestionIndexRef.current % sampleQuestions.length];
    devQuestionIndexRef.current += 1;

    try {
      handsFreeRestartRef.current = false;
      setErrorText('');
      setCurrentTranscript(question);
      setFollowUps([]);
      setAvatarSpeech({ active: false, text: '', timeline: [], positionMs: 0, durationMs: 0, audioStarted: false });
      await getTextToSpeech().stop();
      setStatus('thinking');
      await runQuestionTurn(question);
    } catch (error) {
      if (!mountedRef.current) return;
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
      if (isSpeechUnavailableMessage(error?.message)) {
        await runDevSampleQuestion();
        return;
      }
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
      headline: t('speechChat.stageHeadlineListening', 'Tara is tuned in'),
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

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: screenPalette.background }]}>
      <LinearGradient
        colors={[screenPalette.background, screenPalette.backgroundAlt]}
        style={styles.container}
      >
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
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

        <View style={styles.mainColumn}>
        <ScrollView ref={scrollRef} style={styles.conversation} contentContainerStyle={styles.conversationContent}>
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
        <View style={styles.devToolsRow}>
          <TouchableOpacity
            type="button"
            activeOpacity={0.85}
            onPress={runDevSampleQuestion}
            disabled={busy}
            style={[
              styles.devSampleButton,
              {
                borderColor: screenPalette.border,
                backgroundColor: busy ? 'rgba(255,255,255,0.45)' : 'rgba(249,115,22,0.08)',
              },
            ]}
          >
            <Ionicons name="flask-outline" size={16} color={screenPalette.primary} />
            <Text style={[styles.devSampleButtonText, { color: screenPalette.primary }]}>
              {busy ? 'Testing…' : 'Run test question'}
            </Text>
          </TouchableOpacity>
        </View>
        </View>

        <LinearGradient
          colors={['rgba(255,251,247,0.98)', 'rgba(248,241,233,0.98)', 'rgba(244,235,226,0.96)']}
          style={[styles.controlsShell, { borderColor: screenPalette.border }]}
        >
        <View style={styles.controls}>
          <LinearGradient
            colors={stageProfile.chamberColors}
            style={[styles.voiceChamber, { borderColor: screenPalette.border }]}
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

            <View style={styles.stageHeader}>
              <Text style={[styles.stageEyebrow, { color: screenPalette.textSecondary }]}>{stageProfile.eyebrow}</Text>
              <Text style={[styles.stageHeadline, { color: screenPalette.text }]}>{stageProfile.headline}</Text>
            </View>

            <View style={styles.voiceStage}>
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
                isDark={isDark}
                speechText={avatarSpeech.text}
                speechActive={avatarSpeech.active}
                speechTimeline={avatarSpeech.timeline}
                speechPositionMs={avatarSpeech.positionMs}
                speechDurationMs={avatarSpeech.durationMs}
                speechAudioStarted={avatarSpeech.audioStarted}
              />
            </View>

            <Text style={[styles.statusTextStage, { color: screenPalette.textSecondary }]}>{statusText}</Text>

            <View style={styles.chamberFooter}>
              <TouchableOpacity
                onPress={() => setHandsFreeEnabled((prev) => !prev)}
                style={[
                  styles.handsFreeToggleInline,
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

              {speechChatCost != null ? (
                <Text style={[styles.chamberCreditText, { color: screenPalette.textSecondary }]}>
                  {t('speechChat.creditsPerTurn', { count: speechChatCost })}
                </Text>
              ) : null}

              <TouchableOpacity
                activeOpacity={0.88}
                onPress={handleMicPress}
                disabled={busy}
                style={[styles.chamberMicOuter, busy && styles.micButtonDisabled]}
              >
                <LinearGradient
                  colors={status === 'listening' ? ['#0ea5e9', '#2563eb'] : ['#fb923c', '#f97316']}
                  style={styles.chamberMicButton}
                >
                  {busy ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <Ionicons name={status === 'speaking' ? 'stop' : status === 'listening' ? 'stop-circle' : 'mic'} size={34} color="#fff" />
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
  devToolsRow: {
    width: '100%',
    alignItems: 'center',
    marginBottom: 12,
  },
  devSampleButton: {
    minHeight: 42,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  devSampleButtonText: {
    fontSize: 13,
    fontWeight: '700',
  },
  controlsShell: {
    marginHorizontal: -18,
    paddingHorizontal: 18,
    paddingTop: 18,
    paddingBottom: 10,
    borderTopWidth: 1,
    borderTopLeftRadius: 34,
    borderTopRightRadius: 34,
    overflow: 'hidden',
    flexShrink: 0,
  },
  controls: {
    alignItems: 'center',
    paddingBottom: 18,
    overflow: 'visible',
  },
  voiceChamber: {
    width: '100%',
    maxWidth: 420,
    borderWidth: 1,
    borderRadius: 32,
    paddingTop: 18,
    paddingHorizontal: 18,
    paddingBottom: 22,
    overflow: 'hidden',
    alignItems: 'center',
    shadowColor: '#f59e0b',
    shadowOpacity: 0.08,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 10 },
    elevation: 4,
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
    marginBottom: 10,
  },
  stageEyebrow: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1.2,
    marginBottom: 8,
    textAlign: 'center',
  },
  stageHeadline: {
    fontSize: 24,
    lineHeight: 29,
    fontWeight: '800',
    textAlign: 'center',
    alignSelf: 'center',
    maxWidth: 280,
  },
  voiceStage: {
    width: '100%',
    maxWidth: 340,
    height: 408,
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginBottom: 10,
    overflow: 'visible',
  },
  voiceGlowBar: {
    position: 'absolute',
    width: 248,
    bottom: 40,
    height: 108,
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
    width: 312,
    height: 354,
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginBottom: 0,
  },
  avatarImageStage: {
    width: 312,
    height: 354,
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'visible',
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
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    paddingHorizontal: 34,
    marginTop: 2,
    marginBottom: 14,
    alignSelf: 'center',
    maxWidth: 320,
  },
  chamberFooter: {
    width: '100%',
    alignItems: 'center',
  },
  handsFreeToggleInline: {
    width: '100%',
    minHeight: 48,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    justifyContent: 'flex-start',
    marginBottom: 14,
  },
  handsFreeInlineText: {
    fontSize: 13,
    fontWeight: '700',
    flexShrink: 1,
    flex: 1,
  },
  handsFreeInlineState: {
    fontSize: 13,
    fontWeight: '800',
  },
  chamberCreditText: {
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 16,
  },
  chamberMicOuter: {
    width: 94,
    height: 94,
    borderRadius: 999,
    shadowColor: '#ea580c',
    shadowOpacity: 0.22,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 12 },
    elevation: 8,
    alignSelf: 'center',
    overflow: 'hidden',
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
