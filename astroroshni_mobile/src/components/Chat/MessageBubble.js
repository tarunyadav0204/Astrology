import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Linking,
  Alert,
  Animated,
  Easing,
  Share,
  ActivityIndicator,
  Modal,
  Image,
  ScrollView,
  Dimensions,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import * as Clipboard from 'expo-clipboard';
import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';
import { stopAnimatedValue, stopAnimationLoop } from '../../utils/safeAnimated';
import { generatePDF, sharePDFOnWhatsApp, getLogoDataUriForModule, userFacingPdfExportError } from '../../utils/pdfGenerator';
import { getTextToSpeech } from '../../utils/textToSpeechLazy';
import { buildReadableEvidence } from '../../utils/instantEvidence';

const WHY_TARA_SAYS_THIS = {
  english: 'Why Tara says this',
  hindi: 'तारा ऐसा क्यों कहती हैं',
  es: 'Por qué Tara dice esto',
  fr: 'Pourquoi Tara dit cela',
  german: 'Warum Tara das sagt',
  russian: 'Почему Тара так говорит',
  chinese: '塔拉为什么这样说',
  tamil: 'தாரா ஏன் இப்படிச் சொல்கிறார்',
  telugu: 'తార ఇలా ఎందుకు చెబుతోంది',
  gujarati: 'તારા આવું કેમ કહે છે',
  marathi: 'तारा असे का म्हणते',
};

const CHAT_LANGUAGE_ALIASES = {
  en: 'english', hi: 'hindi', de: 'german', ru: 'russian', zh: 'chinese',
  ta: 'tamil', te: 'telugu', gu: 'gujarati', mr: 'marathi',
};

const whyTaraSaysThis = (language) => WHY_TARA_SAYS_THIS[
  CHAT_LANGUAGE_ALIASES[String(language || '').toLowerCase()] || String(language || 'english').toLowerCase()
] || WHY_TARA_SAYS_THIS.english;

const InstantEvidenceDetails = ({ evidence, colors, t }) => {
  const sections = buildReadableEvidence(evidence);
  return (
    <>
      {!sections.length ? (
        <Text style={[styles.instantEvidenceMeta, { color: colors.textSecondary }]}>
          {t('premiumUi.chat.noEvidenceYet', 'Tara’s supporting chart notes are not available for this answer.')}
        </Text>
      ) : sections.map((section) => (
        <View key={section.key} style={styles.instantEvidenceSection}>
          <View style={styles.instantEvidenceSectionTitleRow}>
            {section.step ? (
              <View style={[styles.instantEvidenceStepBadge, { backgroundColor: colors.accentSoft }]}>
                <Text style={[styles.instantEvidenceStepText, { color: colors.accent }]}>{section.step}</Text>
              </View>
            ) : null}
            <Text style={[styles.instantEvidenceLabel, styles.instantEvidenceSectionTitle, { color: colors.textSecondary }]}>{section.title}</Text>
          </View>
          {(section.lines || []).map((line, index) => (
            <View key={`${section.key}_${index}`} style={styles.instantEvidenceBulletRow}>
              <View style={[styles.instantEvidenceBulletDot, { backgroundColor: colors.accent }]} />
              <Text style={[styles.instantEvidenceBulletText, { color: colors.text }]}>{line}</Text>
            </View>
          ))}
          {(section.groups || []).map((group) => (
            <View key={`${section.key}_${group.key}`} style={[styles.instantEvidenceGroup, { borderColor: colors.cardBorder, backgroundColor: colors.surfaceMuted }]}>
              <Text style={[styles.instantEvidenceGroupTitle, { color: colors.accent }]}>{group.title}</Text>
              {(group.lines || []).map((line, index) => (
                <Text key={`${group.key}_line_${index}`} style={[styles.instantEvidenceBulletText, { color: colors.text }]}>{line}</Text>
              ))}
              {(group.items || []).map((item, index) => (
                <View key={`${group.key}_item_${index}`} style={styles.instantEvidenceFactor}>
                  <Text style={[styles.instantEvidenceFactorTitle, { color: colors.text }]}>{item.title}</Text>
                  <Text style={[styles.instantEvidenceBulletText, { color: colors.textSecondary }]}>{item.text}</Text>
                </View>
              ))}
            </View>
          ))}
        </View>
      ))}
    </>
  );
};
import { chatAPI } from '../../services/api';
import { storage } from '../../services/storage';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { DISPLAY_FONT_FAMILY } from '../../theme/tokens';
import { useCredits } from '../../credits/CreditContext';
import { useAuthGate } from '../../auth/AuthGateContext';
import ConfirmCreditsModal from '../ConfirmCreditsModal';
import AppAlertModal from '../Common/AppAlertModal';
import PodcastPlayerModal from '../PodcastPlayerModal';
import PodcastLanguageModal from './PodcastLanguageModal';
import { creditAPI } from '../../services/api';
import { sharePodcastBase64OnWeb } from '../../utils/sharePodcastWeb';
import {
  freeDetailRevealClickedStorageKey,
  freeDetailUnlockStorageKey,
  splitFreeAnswerContent,
} from '../../utils/freeAnswerSplit';

const formatGlossaryTitle = (value) => String(value || '')
  .trim()
  .split(/\s+/)
  .map((word) => (/\d/.test(word) || word.length <= 2
    ? word.toUpperCase()
    : `${word.charAt(0).toUpperCase()}${word.slice(1).toLowerCase()}`))
  .join(' ');

/** Avoid replaying slide-in when a tall bubble remounts (Android clipping / recycle). */
const messageBubbleEntryPlayedIds = new Set();
const remedyScreenImpressionClaims = new Set();
const premiumPodcastReadyKeys = new Set();

const PODCAST_LISTEN_LANG_KEY = 'podcast_listen_lang';

const podcastLangFromUiLanguage = (language) =>
  String(language || '').toLowerCase().startsWith('hi') ? 'hi' : 'en';

const podcastReadyKey = (messageId, language) => {
  const mid = messageId != null ? String(messageId) : '';
  return mid ? `${mid}:${podcastLangFromUiLanguage(language)}` : '';
};

const messageHasReadyPodcast = (messageId) => {
  if (messageId == null || messageId === '') return false;
  return (
    premiumPodcastReadyKeys.has(podcastReadyKey(messageId, 'en'))
    || premiumPodcastReadyKeys.has(podcastReadyKey(messageId, 'hi'))
  );
};

const resolveReadyPodcastLang = (messageId, preferredLang) => {
  const mid = messageId != null ? String(messageId) : '';
  if (!mid) return null;
  const preferred = podcastLangFromUiLanguage(preferredLang);
  const alternate = preferred === 'hi' ? 'en' : 'hi';
  if (premiumPodcastReadyKeys.has(podcastReadyKey(mid, preferred))) return preferred;
  if (premiumPodcastReadyKeys.has(podcastReadyKey(mid, alternate))) return alternate;
  return null;
};

const podcastLanguagesFromStatus = (response, requestedLang = 'en') => {
  const data = response?.data || {};
  const languages = Array.isArray(data.languages)
    ? data.languages.map(podcastLangFromUiLanguage)
    : [];
  // Backward compatibility while mobile and backend releases overlap.
  if (!languages.length && data.cached === true) {
    languages.push(podcastLangFromUiLanguage(requestedLang));
  }
  return [...new Set(languages)];
};

const sanitizeVisibleChatContent = (content, { asHtmlSpans = false } = {}) => {
  let out = String(content || '');
  out = out.replace(
    /\n?\s*(?:NEXT_ACTION_META|FAQ_META|PREDICTION_ANCHOR_META)\s*:\s*\{[\s\S]*?\}\s*/gi,
    '\n',
  );
  const held = [];
  const hold = (kind, inner) => {
    const token = `\u0000SENT${held.length}\u0000`;
    held.push({ kind, inner: String(inner).replace(/\n+/g, ' ').trim() });
    return token;
  };
  out = out.replace(/(?:【|\[)POS_START(?:】|\])([\s\S]*?)(?:【|\[)POS_END(?:】|\])/gi, (_, inner) => hold('pos', inner));
  out = out.replace(/(?:【|\[)NEG_START(?:】|\])([\s\S]*?)(?:【|\[)NEG_END(?:】|\])/gi, (_, inner) => hold('neg', inner));
  out = out.replace(/(?:【|\[)(?:POS|NEG)_(?:START|END)(?:】|\])/gi, '');
  held.forEach((item, i) => {
    const token = `\u0000SENT${i}\u0000`;
    const replacement = asHtmlSpans
      ? `<span class="chat-sentiment-${item.kind === 'pos' ? 'positive' : 'negative'}">${item.inner}</span>`
      : `${item.kind === 'pos' ? '【POS_START】' : '【NEG_START】'}${item.inner}${item.kind === 'pos' ? '【POS_END】' : '【NEG_END】'}`;
    out = out.split(token).join(replacement);
  });
  return out;
};

const localCalendarDay = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const recordRemedyScreenImpressionOnce = async ({ sessionId, message }) => {
  const sessionScope = String(
    sessionId
      || message?.session_id
      || message?.sessionId
      || 'current',
  );
  const impressionId = `chat_screen:${sessionScope}:${localCalendarDay()}`;
  if (remedyScreenImpressionClaims.has(impressionId)) return;
  remedyScreenImpressionClaims.add(impressionId);

  const storageKey = `remedy_funnel_card_shown:${impressionId}`;
  try {
    if (await AsyncStorage.getItem(storageKey)) return;
    // Claim before networking so remounts/reloads cannot create a retry storm.
    await AsyncStorage.setItem(storageKey, '1');
  } catch (_) {
    // The in-memory claim still guarantees one request for this app process.
  }

  await creditAPI.recordRemedyFunnelEvent(
    'card_shown',
    impressionId,
    Platform.OS === 'web' ? 'web' : 'app',
  );
};

function MessageBubble({
  message,
  language,
  onFollowUpClick,
  onRemedyFollowUpClick,
  partnership,
  onDelete,
  onRestart,
  onSendRetry,
  onStartNewChat,
  onStartPartnershipGate,
  onContinueSingleChartGate,
  onRelationshipContextGate,
  sessionId,
  podcastAutoLaunchMessageId = null,
  podcastAutoLaunchKey = 0,
  podcastAutoLaunchLang = 'en',
  onPodcastAutoLaunchConsumed,
  forceInstantPresentation = false,
}) {
  const { t, i18n } = useTranslation();
  const { theme, colors } = useTheme();
  const messageActionStyle = {
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.cardBorder,
  };
  const highlightedActionStyle = {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.primary,
  };
  const destructiveActionStyle = {
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.error,
  };
  const messageActionIcon = colors.textSecondary;
  const { podcastCost, credits, pricing, refreshCredits } = useCredits();
  const { requireAuthForPaid } = useAuthGate();
  const navigation = useNavigation();
  const standardChatCost = Math.max(1, Number(pricing?.chat ?? pricing?.standard ?? 1) || 1);
  const [detailUnlocked, setDetailUnlocked] = useState(false);
  const [showRevealCreditsModal, setShowRevealCreditsModal] = useState(false);
  const [copyAlert, setCopyAlert] = useState({ visible: false, error: false });
  const [showInstantEvidence, setShowInstantEvidence] = useState(false);
  const blurShownTrackedRef = useRef(false);
  // Init from the played-ids set so FlatList remounts do not flash translateY:50 for one frame
  // (that looked like the long answer bouncing between sections while reading).
  const entryIdForAnim = String(message?.messageId || message?.id || message?.clientRequestId || '');
  const entryAlreadyPlayed =
    Boolean(entryIdForAnim) && messageBubbleEntryPlayedIds.has(entryIdForAnim);
  const fadeAnim = useRef(new Animated.Value(entryAlreadyPlayed ? 1 : 0)).current;
  const slideAnim = useRef(new Animated.Value(entryAlreadyPlayed ? 0 : 50)).current;
  const isPartnership = partnership || message.partnership_mode;
  const messageChatTier = String(message?.chatTier || message?.chat_tier || '').trim().toLowerCase();
  const isInstantChatMessage = forceInstantPresentation || messageChatTier === 'instant';
  const isPremiumChatMessage = messageChatTier === 'premium' || message?.premium_analysis === true;
  const instantEvidence = message?.instant_evidence_debug
    || message?.gate_metadata?.instant_evidence_debug
    || null;
  const hasRemedyCard = Boolean(
    message.next_action?.type === 'remedy'
      && message.next_action?.title
      && message.next_action?.reason
      && message.next_action?.follow_up_questions?.[0]
  );
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [tooltipModal, setTooltipModal] = useState({ show: false, term: '', definition: '' });
  const [isLoadingPodcast, setIsLoadingPodcast] = useState(false);
  const [podcastReady, setPodcastReady] = useState(() =>
    messageHasReadyPodcast(message?.messageId)
  );
  const [isPlayingPodcast, setIsPlayingPodcast] = useState(false);
  const [isPausedPodcast, setIsPausedPodcast] = useState(false);
  const [isSharingPodcast, setIsSharingPodcast] = useState(false);
  const [showPodcastCreditsModal, setShowPodcastCreditsModal] = useState(false);
  const [showPodcastLanguageModal, setShowPodcastLanguageModal] = useState(false);
  const [podcastListenLang, setPodcastListenLang] = useState(() => podcastLangFromUiLanguage(language));
  const podcastListenLangRef = useRef(podcastListenLang);
  const skipPodcastCreditsRef = useRef(false);
  const podcastCacheCheckRef = useRef(false);
  const lastPodcastPromoKeyRef = useRef(0);
  const [showPodcastPlayerModal, setShowPodcastPlayerModal] = useState(false);
  const showPodcastPlayerModalRef = useRef(false);
  const [podcastPlayerMode, setPodcastPlayerMode] = useState('generating');
  const [podcastPositionMillis, setPodcastPositionMillis] = useState(0);
  const [podcastDurationMillis, setPodcastDurationMillis] = useState(0);
  const [podcastPlaybackRate, setPodcastPlaybackRate] = useState(1);
  const [showImageModal, setShowImageModal] = useState(false);
  const [imageZoomScale, setImageZoomScale] = useState(1);
  const [isImageLoading, setIsImageLoading] = useState(true);
  const skeletonAnim = useRef(new Animated.Value(0)).current;
  const skeletonLoopRef = useRef(null);
  const entryAnimRef = useRef(null);
  const typingAnimRef = useRef(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    showPodcastPlayerModalRef.current = showPodcastPlayerModal;
  }, [showPodcastPlayerModal]);
  /** After seek, ignore progress updates briefly so we don't overwrite with stale position. */
  const lastSeekedAtRef = useRef(0);
  /** Set when user closes the modal while "Generating..." so we don't reopen or auto-play when the request completes. */
  const userDismissedGeneratingRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    AsyncStorage.getItem(PODCAST_LISTEN_LANG_KEY)
      .then((stored) => {
        if (cancelled) return;
        if (stored !== 'hi' && stored !== 'en') return;
        podcastListenLangRef.current = stored;
        setPodcastListenLang(stored);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);
  useFocusEffect(
    React.useCallback(() => {
      mountedRef.current = true;
      return () => {
        // PWA: opening the podcast modal (or route blur) must not abort playback.
        if (Platform.OS === 'web') return;
        mountedRef.current = false;
        userDismissedGeneratingRef.current = true;
        getTextToSpeech().stopPodcast();
        setIsPlayingPodcast(false);
        setIsPausedPodcast(false);
        setShowPodcastPlayerModal(false);
        skeletonLoopRef.current && stopAnimationLoop(skeletonLoopRef.current);
        typingAnimRef.current?.stop?.();
        entryAnimRef.current?.stop?.();
        stopAnimatedValue(skeletonAnim, 0);
        stopAnimatedValue(fadeAnim);
        stopAnimatedValue(slideAnim);
      };
    }, [])
  );

  useEffect(() => {
    if (message.summary_image && isImageLoading) {
      skeletonLoopRef.current && stopAnimationLoop(skeletonLoopRef.current);
      const loop = Animated.loop(
        Animated.sequence([
          Animated.timing(skeletonAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(skeletonAnim, {
            toValue: 0,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      );
      skeletonLoopRef.current = loop;
      loop.start();
    } else {
      skeletonLoopRef.current && stopAnimationLoop(skeletonLoopRef.current);
      skeletonLoopRef.current = null;
      stopAnimatedValue(skeletonAnim, 0);
    }
    return () => {
      skeletonLoopRef.current && stopAnimationLoop(skeletonLoopRef.current);
      skeletonLoopRef.current = null;
      stopAnimatedValue(skeletonAnim, 0);
    };
  }, [message.summary_image, isImageLoading, skeletonAnim]);

  // Animated loader for typing indicator
  const dot1Anim = useRef(new Animated.Value(0)).current;
  const dot2Anim = useRef(new Animated.Value(0)).current;
  const dot3Anim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const shouldAnimateTyping = message.isTyping || message.instantStreaming;
    if (!shouldAnimateTyping) {
      typingAnimRef.current?.stop?.();
      typingAnimRef.current = null;
      stopAnimatedValue(dot1Anim, 0.3);
      stopAnimatedValue(dot2Anim, 0.3);
      stopAnimatedValue(dot3Anim, 0.3);
      return undefined;
    }

    const animateLoader = () => {
      if (!mountedRef.current || !(message.isTyping || message.instantStreaming)) return;
      const seq = Animated.sequence([
        Animated.timing(dot1Anim, { toValue: 1, duration: 400, useNativeDriver: true }),
        Animated.timing(dot2Anim, { toValue: 1, duration: 400, useNativeDriver: true }),
        Animated.timing(dot3Anim, { toValue: 1, duration: 400, useNativeDriver: true }),
        Animated.timing(dot1Anim, { toValue: 0.3, duration: 400, useNativeDriver: true }),
        Animated.timing(dot2Anim, { toValue: 0.3, duration: 400, useNativeDriver: true }),
        Animated.timing(dot3Anim, { toValue: 0.3, duration: 400, useNativeDriver: true }),
      ]);
      typingAnimRef.current = seq;
      seq.start(({ finished }) => {
        if (finished && mountedRef.current && (message.isTyping || message.instantStreaming)) {
          animateLoader();
        }
      });
    };
    animateLoader();

    return () => {
      typingAnimRef.current?.stop?.();
      typingAnimRef.current = null;
      stopAnimatedValue(dot1Anim, 0.3);
      stopAnimatedValue(dot2Anim, 0.3);
      stopAnimatedValue(dot3Anim, 0.3);
    };
  }, [message.isTyping, message.instantStreaming, dot1Anim, dot2Anim, dot3Anim]);

  useEffect(() => {
    const entryId = String(message?.messageId || message?.id || message?.clientRequestId || '');
    if (entryId && messageBubbleEntryPlayedIds.has(entryId)) {
      fadeAnim.setValue(1);
      slideAnim.setValue(0);
      return undefined;
    }
    if (entryId) {
      messageBubbleEntryPlayedIds.add(entryId);
    }
    const parallel = Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }),
    ]);
    entryAnimRef.current = parallel;
    parallel.start();
    return () => {
      entryAnimRef.current?.stop?.();
      entryAnimRef.current = null;
      stopAnimatedValue(fadeAnim, 1);
      stopAnimatedValue(slideAnim, 0);
    };
  }, [fadeAnim, slideAnim, message?.messageId, message?.id, message?.clientRequestId]);
  const getCleanMessageText = () => {
    const raw = message.content;
    const s = typeof raw === 'string' ? raw : raw != null ? String(raw) : '';
    return s
      .replace(/<[^>]*>/g, '')
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/&quot;/g, '"')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&#39;/g, "'")
      .replace(/&nbsp;/g, ' ')
      .trim();
  };

  const markPremiumPodcastReady = useCallback((key) => {
    if (!key) return;
    premiumPodcastReadyKeys.add(key);
    setPodcastReady(true);
  }, []);

  const persistPodcastListenLang = (listenLang) => {
    const lang = podcastLangFromUiLanguage(listenLang);
    podcastListenLangRef.current = lang;
    setPodcastListenLang(lang);
    AsyncStorage.setItem(PODCAST_LISTEN_LANG_KEY, lang).catch(() => {});
    return lang;
  };

  const playPodcast = async (listenLang) => {
    if (isPlayingPodcast) {
      getTextToSpeech().stop();
      setIsPlayingPodcast(false);
      return;
    }
    if (isLoadingPodcast) return;

    const cleanText = getCleanMessageText();
    if (!cleanText) return;
    const lang = podcastLangFromUiLanguage(listenLang || podcastListenLangRef.current || language);

    try {
      userDismissedGeneratingRef.current = false;
      setIsLoadingPodcast(true);
      setIsPlayingPodcast(false);
      await getTextToSpeech().playPodcast(cleanText, {
        language: lang,
        messageId: message.messageId || null,
        sessionId: sessionId || null,
        preview: (cleanText || message.content || '').slice(0, 150),
        nativeName: message.native_name || null,
        onProgress: (pos, dur) => {
          if (userDismissedGeneratingRef.current) return;
          if (Date.now() - lastSeekedAtRef.current < 600) return; // don't overwrite seek with stale callback
          setPodcastPositionMillis(pos);
          if (dur > 0) setPodcastDurationMillis(dur);
        },
        onStart: () => {
          if (userDismissedGeneratingRef.current) {
            getTextToSpeech().stopPodcast();
            setIsLoadingPodcast(false);
            return;
          }
          getTextToSpeech().setPodcastRate(podcastPlaybackRate);
          setIsLoadingPodcast(false);
          setIsPlayingPodcast(true);
          setIsPausedPodcast(false);
          setPodcastPlayerMode('playing');
          setShowPodcastPlayerModal(true);
          const readyKey = podcastReadyKey(message.messageId, lang);
          if (readyKey) markPremiumPodcastReady(readyKey);
        },
        onDone: () => {
          if (userDismissedGeneratingRef.current) return;
          setIsPlayingPodcast(false);
          setIsPausedPodcast(false);
          setShowPodcastPlayerModal(false);
        },
        onPause: () => {
          setIsPlayingPodcast(false);
          setIsPausedPodcast(true);
          setPodcastPlayerMode('paused');
        },
        onResume: () => {
          setIsPlayingPodcast(true);
          setIsPausedPodcast(false);
          setPodcastPlayerMode('playing');
        },
        onStop: () => {
          if (userDismissedGeneratingRef.current) return;
          setIsPlayingPodcast(false);
          setIsPausedPodcast(false);
          setShowPodcastPlayerModal(false);
        },
        onError: (err) => {
          userDismissedGeneratingRef.current = false;
          setIsLoadingPodcast(false);
          setIsPlayingPodcast(false);
          setIsPausedPodcast(false);
          setShowPodcastPlayerModal(false);
          if (err?.response?.status === 402) {
            const cost = podcastCost ?? 2;
            Alert.alert(
              t('credits.insufficient', 'Insufficient Credits'),
              t('credits.insufficientPodcast', 'You need {{cost}} credits to listen to this as a podcast. Please purchase more credits.', { cost }),
              [
                { text: t('common.cancel', 'Cancel'), style: 'cancel' },
                { text: t('credits.buyCredits', 'Buy Credits'), onPress: () => navigation.navigate('Credits') },
              ]
            );
            return;
          }
          Alert.alert(
            t('common.error', 'Error'),
            t('podcast.playFailed', 'Could not play podcast. Please try again.')
          );
        },
      });
    } catch (error) {
      console.error('[Podcast] error', error);
      setIsLoadingPodcast(false);
      setIsPlayingPodcast(false);
      setIsPausedPodcast(false);
      const status = error?.response?.status;
      const cost = podcastCost ?? 2;
      if (status === 402) {
        Alert.alert(
          t('credits.insufficient', 'Insufficient Credits'),
          t('credits.insufficientPodcast', 'You need {{cost}} credits to listen to this as a podcast. Please purchase more credits.', { cost }),
          [
            { text: t('common.cancel', 'Cancel'), style: 'cancel' },
            { text: t('credits.buyCredits', 'Buy Credits'), onPress: () => navigation.navigate('Credits') },
          ]
        );
        return;
      }
      Alert.alert('Error', 'Could not generate podcast. Please try again.');
    }
  };

  const playCachedPodcast = async (listenLang) => {
    const messageId = message.messageId || message.id;
    if (!messageId || isLoadingPodcast) return;
    const lang = persistPodcastListenLang(listenLang);
    try {
      userDismissedGeneratingRef.current = false;
      setIsLoadingPodcast(true);
      setIsPlayingPodcast(false);
      setIsPausedPodcast(false);
      setPodcastPlayerMode('generating');
      setShowPodcastPlayerModal(true);
      setPodcastPositionMillis(0);
      setPodcastDurationMillis(0);
      const token = await storage.getAuthToken();
      if (!token) {
        setIsLoadingPodcast(false);
        setShowPodcastPlayerModal(false);
        navigation.navigate('Login');
        return;
      }
      const streamUrl = chatAPI.getPodcastStreamUrl(messageId, lang);
      await getTextToSpeech().playPodcastFromStream(streamUrl, token, {
        onProgress: (pos, dur) => {
          if (userDismissedGeneratingRef.current) return;
          if (Date.now() - lastSeekedAtRef.current < 600) return;
          setPodcastPositionMillis(pos);
          if (dur > 0) setPodcastDurationMillis(dur);
        },
        onStart: () => {
          if (userDismissedGeneratingRef.current) {
            getTextToSpeech().stopPodcast();
            setIsLoadingPodcast(false);
            return;
          }
          getTextToSpeech().setPodcastRate(podcastPlaybackRate);
          setIsLoadingPodcast(false);
          setIsPlayingPodcast(true);
          setIsPausedPodcast(false);
          setPodcastPlayerMode('playing');
          markPremiumPodcastReady(podcastReadyKey(messageId, lang));
        },
        onDone: () => {
          if (userDismissedGeneratingRef.current) return;
          setIsLoadingPodcast(false);
          setIsPlayingPodcast(false);
          setIsPausedPodcast(false);
          setShowPodcastPlayerModal(false);
        },
        onPause: () => {
          setIsPlayingPodcast(false);
          setIsPausedPodcast(true);
          setPodcastPlayerMode('paused');
        },
        onResume: () => {
          setIsPlayingPodcast(true);
          setIsPausedPodcast(false);
          setPodcastPlayerMode('playing');
        },
        onStop: () => {
          if (userDismissedGeneratingRef.current) return;
          setIsLoadingPodcast(false);
          setIsPlayingPodcast(false);
          setIsPausedPodcast(false);
          setShowPodcastPlayerModal(false);
        },
        onError: () => {
          if (userDismissedGeneratingRef.current) return;
          setIsLoadingPodcast(false);
          setIsPlayingPodcast(false);
          setIsPausedPodcast(false);
          setShowPodcastPlayerModal(false);
          Alert.alert(
            t('common.error', 'Error'),
            t('podcast.playFailed', 'Could not play podcast. Please try again.'),
          );
        },
      });
    } catch (error) {
      console.error('[Podcast] cached playback error', error);
      setIsLoadingPodcast(false);
      setIsPlayingPodcast(false);
      setIsPausedPodcast(false);
      setShowPodcastPlayerModal(false);
      Alert.alert(
        t('common.error', 'Error'),
        t('podcast.playFailed', 'Could not play podcast. Please try again.'),
      );
    }
  };

  const startPodcastPlayback = (listenLang) => {
    const lang = persistPodcastListenLang(listenLang || podcastListenLangRef.current);
    setPodcastPlayerMode('generating');
    setShowPodcastPlayerModal(true);
    setPodcastPositionMillis(0);
    setPodcastDurationMillis(0);
    playPodcast(lang);
  };

  const continuePodcastAfterLanguage = async (listenLang) => {
    const lang = persistPodcastListenLang(listenLang);
    const skipCredits = skipPodcastCreditsRef.current;
    skipPodcastCreditsRef.current = false;
    setShowPodcastLanguageModal(false);

    const existingLocalLang = resolveReadyPodcastLang(message.messageId, lang);
    if (existingLocalLang) {
      playCachedPodcast(existingLocalLang);
      return;
    }

    if (isPremiumChatMessage || skipCredits) {
      startPodcastPlayback(lang);
      return;
    }

    const messageId = message.messageId || null;
    if (messageId) {
      // Give immediate visual feedback while the lightweight entitlement
      // lookup determines whether either language was generated previously.
      userDismissedGeneratingRef.current = false;
      setPodcastPlayerMode('generating');
      setShowPodcastPlayerModal(true);
      podcastCacheCheckRef.current = true;
      try {
        const res = await chatAPI.checkPodcastCache(messageId, lang);
        const existingLanguages = podcastLanguagesFromStatus(res, lang);
        existingLanguages.forEach((existingLang) => {
          markPremiumPodcastReady(podcastReadyKey(messageId, existingLang));
        });
        const existingLang = resolveReadyPodcastLang(messageId, lang);
        if (existingLang) {
          if (!userDismissedGeneratingRef.current) playCachedPodcast(existingLang);
          return;
        }
      } catch (_) {
        // On error (e.g. network), show modal so user confirms before we attempt creation
      } finally {
        podcastCacheCheckRef.current = false;
      }
      if (userDismissedGeneratingRef.current) return;
      setShowPodcastPlayerModal(false);
    }

    setShowPodcastCreditsModal(true);
  };

  const onPodcastButtonPress = async () => {
    // Web requires audio unlocking in the original user gesture. Native does
    // not, so avoid synchronously loading expo-av before the modal can paint.
    if (Platform.OS === 'web') getTextToSpeech().unlockWebAudio?.();
    if (isPausedPodcast) {
      getTextToSpeech().resumePodcast();
      return;
    }
    if (isPlayingPodcast) return; // Pause/Stop are separate buttons
    if (isLoadingPodcast) {
      // User closed the generating modal and tapped again – reopen it and wait for completion
      userDismissedGeneratingRef.current = false;
      setShowPodcastPlayerModal(true);
      setPodcastPlayerMode('generating');
      return;
    }
    const cleanText = getCleanMessageText();
    if (!cleanText) return;
    if (podcastCacheCheckRef.current) return;

    skipPodcastCreditsRef.current = false;

    const playCachedLang = (lang) => {
      const readyKey = podcastReadyKey(message.messageId, lang);
      if (readyKey) markPremiumPodcastReady(readyKey);
      playCachedPodcast(lang);
    };

    const localCachedLang = resolveReadyPodcastLang(
      message.messageId,
      podcastListenLangRef.current,
    );
    if (localCachedLang) {
      playCachedLang(localCachedLang);
      return;
    }

    // No known podcast exists: let the user choose immediately. Entitlement
    // is checked after selection, with a visible loader, before any credit UI.
    setShowPodcastLanguageModal(true);
  };

  const confirmPodcastCredits = async () => {
    const authOk = await requireAuthForPaid({
      feature: 'podcast',
      message: 'Sign in to generate a podcast from this answer.',
      resume: { resumeRoute: 'Home', resumeParams: {} },
    });
    if (!authOk) return;
    setShowPodcastCreditsModal(false);
    getTextToSpeech().unlockWebAudio?.();
    startPodcastPlayback(podcastListenLangRef.current);
  };

  const handlePausePodcast = () => {
    getTextToSpeech().pausePodcast();
  };

  const handleResumePodcast = () => {
    getTextToSpeech().resumePodcast();
  };

  const handleStopPodcast = () => {
    getTextToSpeech().stopPodcast();
    setShowPodcastPlayerModal(false);
  };

  const handlePodcastPlayerClose = () => {
    if (podcastPlayerMode === 'generating') {
      userDismissedGeneratingRef.current = true;
    }
    getTextToSpeech().stopPodcast();
    setShowPodcastPlayerModal(false);
  };

  const handlePodcastSeek = (positionMillis) => {
    lastSeekedAtRef.current = Date.now();
    getTextToSpeech().seekPodcast(positionMillis);
    setPodcastPositionMillis(positionMillis);
  };

  const sharePodcastAudio = async () => {
    const cleanText = getCleanMessageText();
    if (!cleanText) return;
    try {
      setIsSharingPodcast(true);
      const lang = podcastLangFromUiLanguage(podcastListenLangRef.current || language);
      const response = await chatAPI.getPodcastAudio(cleanText, lang, message.messageId || null, null, null, message.native_name || null);
      const base64Audio = response?.data?.audio;
      if (!base64Audio || typeof base64Audio !== 'string') {
        Alert.alert('Error', 'Could not get podcast audio to share.');
        return;
      }
      const filename = `AstroRoshni-Podcast-${Date.now()}.mp3`;
      if (Platform.OS === 'web') {
        await sharePodcastBase64OnWeb(base64Audio, filename);
        return;
      }
      const path = `${FileSystem.cacheDirectory}${filename}`;
      await FileSystem.writeAsStringAsync(path, base64Audio, {
        encoding: FileSystem.EncodingType.Base64,
      });
      const isAvailable = await Sharing.isAvailableAsync();
      if (!isAvailable) {
        Alert.alert('Error', 'Sharing is not available on this device.');
        return;
      }
      await Sharing.shareAsync(path, {
        mimeType: 'audio/mpeg',
        dialogTitle: 'Share Podcast',
      });
    } catch (error) {
      console.error('[Podcast] share error', error);
      Alert.alert('Error', 'Could not share podcast. Please try again.');
    } finally {
      setIsSharingPodcast(false);
    }
  };

  const sharePDF = async () => {
    try {
      setIsGeneratingPDF(true);
      console.log('📄 Starting PDF generation...');
      const logoDataUri = await getLogoDataUriForModule(require('../../../assets/logo.png'));
      const pdfUri = await generatePDF(message, { logoDataUri });
      console.log('✅ PDF generated:', pdfUri);
      await sharePDFOnWhatsApp(pdfUri);
      console.log('✅ PDF shared');
    } catch (error) {
      console.error('❌ PDF generation error:', error);
      Alert.alert('Export failed', userFacingPdfExportError(error));
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  const deleteMessage = async () => {
    const serverId = message.messageId || message.message_id;
    if (!serverId) {
      if (onDelete) {
        onDelete(message.id);
      }
      return;
    }
    try {
      const token = await AsyncStorage.getItem('authToken');
      const deleteUrl = `${API_BASE_URL}${getEndpoint(`/chat-v2/message/${serverId}`)}`;

      const response = await fetch(deleteUrl, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        Alert.alert('✅ Deleted', 'Message deleted successfully');
        if (onDelete) {
          onDelete(serverId);
        }
      } else {
        Alert.alert('❌ Error', 'Failed to delete message');
      }
    } catch (error) {
      Alert.alert('❌ Error', 'Failed to delete message');
    }
  };

  const copyToClipboard = async () => {
    try {
      const cleanText = String(message.content || '')
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/###\s*(.*?)$/gm, '$1')
        .replace(/<[^>]*>/g, '')
        .replace(/•\s*/g, '• ')
        .trim();

      await Clipboard.setStringAsync(cleanText);
      setCopyAlert({ visible: true, error: false });
    } catch (error) {
      console.error('[MessageBubble] Failed to copy message', error);
      setCopyAlert({ visible: true, error: true });
    }
  };

  const shareMessage = async () => {
    try {
      const cleanText = message.content
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/###\s*(.*?)$/gm, '$1')
        .replace(/<[^>]*>/g, '')
        .replace(/•\s*/g, '• ')
        .trim();

      const shareText = `☀️ AstroRoshni Prediction\n\n${cleanText}\n\nShared from AstroRoshni App`;

      await Share.share({
        message: shareText,
      });
    } catch (error) {
      // Error sharing message
    }
  };

  const formatContent = (content) => {
    if (!content || content.trim() === '') {
      return '';
    }

    // First decode HTML entities AGGRESSIVELY
    let formatted = content;

    // Multiple passes to handle nested encoding
    for (let i = 0; i < 3; i++) {
      formatted = formatted
        .replace(/&quot;/g, '"')
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&#39;/g, "'")
        .replace(/&nbsp;/g, ' ');
    }

    // Remove glossary JSON blocks that shouldn't be displayed
    formatted = formatted.replace(/GLOSSARY_START[\s\S]*?GLOSSARY_END/g, '');
    formatted = formatted.replace(/```json[\s\S]*?```/g, '');
    formatted = formatted.replace(/\{\s*"[^"]+"\s*:\s*"[^"]*"[\s\S]*?\}/g, '');
    // Remove glossary headers
    formatted = formatted.replace(/#### Glossary[\s\S]*?(?=####|$)/gi, '');
    formatted = formatted.replace(/### Glossary[\s\S]*?(?=###|$)/gi, '');
    formatted = formatted.replace(/## Glossary[\s\S]*?(?=##|$)/gi, '');
    formatted = sanitizeVisibleChatContent(formatted, { asHtmlSpans: true });

    // Remove standalone # at end of lines (trailing markdown artifacts)
    formatted = formatted
      .replace(/\n\s*#+\s*$/gm, '')
      .replace(/\n\s*#+\s*\n/g, '\n')
      .replace(/#+\s*$/, '');

    // Process term tooltips FIRST, after HTML entity decoding (only first occurrence per term per message)
    if (message.terms && message.glossary && Object.keys(message.glossary).length > 0) {
      const wrappedTermIds = new Set();
      // First try to find existing <term> tags
      let termCount = 0;
      formatted = formatted.replace(/<term\s+id=["']([^"']+)["']\s*>([^<]+)<\/term>/gi, (match, termId, termText) => {
        const normalizedId = termId.toLowerCase().trim();
        if (message.glossary[normalizedId]) {
          if (wrappedTermIds.has(normalizedId)) return termText;
          wrappedTermIds.add(normalizedId);
          termCount++;
          return `<tooltip data-term="${normalizedId}">${termText}</tooltip>`;
        }
        return termText;
      });

      // If no tags found, auto-wrap terms from glossary keys (first occurrence only per term)
      if (termCount === 0) {
        Object.keys(message.glossary).forEach(termKey => {
          const termPattern = new RegExp(`\\b(${termKey.replace(/[()]/g, '\\$&')})\\b`, 'gi');
          formatted = formatted.replace(termPattern, (match) => {
            const key = termKey.toLowerCase();
            if (wrappedTermIds.has(key)) return match;
            wrappedTermIds.add(key);
            return `<tooltip data-term="${termKey}">${match}</tooltip>`;
          });
        });
      }
    }

    // Normalize line breaks
    formatted = formatted.replace(/\r\n/g, '\n').replace(/\r/g, '\n').replace(/\\n/g, '\n');

    // Handle markdown tables - convert to simple format
    formatted = formatted.replace(/\|(.+?)\|\s*\n\s*\|[:\s-|]+\|\s*\n([\s\S]*?)(?=\n\n|\n###|\n##|$)/g, (match, header, rows) => {
      // console.log('Table regex match:', { match, header, rows });
      return `<table>${header.trim()}|||${rows.trim()}</table>`;
    });

    // Handle Final Thoughts section
    formatted = formatted.replace(/(### Final Thoughts[\s\S]*?)(?=###|$)/g, (match, finalThoughts) => {
      const cleanContent = finalThoughts.replace(/### Final Thoughts\n?/, '').trim();
      return `<finalthoughts>${cleanContent}</finalthoughts>`;
    });

    // Partnership/relational merges often use "Direct Answer" style headings instead of quick-answer-card HTML.
    // Normalize these to the same yellow quick-answer card UX used in single-chart responses.
    formatted = formatted.replace(
      /(###\s*(?:Direct Answer|Quick Answer|Short Answer|Bottom Line|Answer)\s*[\s\S]*?)(?=###|$)/gi,
      (match) => {
        const cleanContent = match.replace(/^###\s*(?:Direct Answer|Quick Answer|Short Answer|Bottom Line|Answer)\s*\n?/i, '').trim();
        return `<quickanswer>${cleanContent}</quickanswer>`;
      }
    );

    // Normalize common closing section names from partnership branches to Final Thoughts card.
    formatted = formatted.replace(
      /(###\s*(?:Final Thought|Final Thoughts|Closing Thoughts|Closing Guidance|Final Guidance|Practical Guidance|Takeaway)\s*[\s\S]*?)(?=###|$)/gi,
      (match) => {
        const cleanContent = match.replace(/^###\s*(?:Final Thought|Final Thoughts|Closing Thoughts|Closing Guidance|Final Guidance|Practical Guidance|Takeaway)\s*\n?/i, '').trim();
        return `<finalthoughts>${cleanContent}</finalthoughts>`;
      }
    );

    // Handle Quick Answer sections
    formatted = formatted.replace(/<div class="quick-answer-card">(.*?)<\/div>/gs, '<quickanswer>$1</quickanswer>');
    formatted = formatted.replace(/<div class="final-thoughts-card">(.*?)<\/div>/gs, '<finalthoughts>$1</finalthoughts>');

    // Normalize over-duplicated markdown header hashes while keeping a single header marker
    // Example: "#### #### Health" -> "#### Health" so our header parsing still works
    formatted = formatted.replace(/^(#{2,6})(?:\s+\1)+\s*(.*)$/gm, (_match, hashes, rest) => `${hashes} ${rest}`);

    return formatted;
  };

  const renderFormattedText = (text) => {
    const elements = [];
    let currentIndex = 0;
    let lastIndex = 0;
    const wrappedTermsInRender = new Set(); // first occurrence per term only (for line-level <term> fallback)

    // Handle all special sections
    const sections = [
      { regex: /<quickanswer>(.*?)<\/quickanswer>/gs, type: 'quick' },
      { regex: /<finalthoughts>(.*?)<\/finalthoughts>/gs, type: 'final' },
      { regex: /<table>(.*?)<\/table>/gs, type: 'table' }
    ];

    // Find all matches and sort by position
    const allMatches = [];
    sections.forEach(section => {
      section.regex.lastIndex = 0;
      let match;
      while ((match = section.regex.exec(text)) !== null) {
        allMatches.push({
          type: section.type,
          match: match,
          index: match.index,
          lastIndex: section.regex.lastIndex
        });
      }
    });

    allMatches.sort((a, b) => a.index - b.index);

    // Process matches in order
    for (const item of allMatches) {
      // Add text before this match
      if (item.index > lastIndex) {
        const beforeText = text.slice(lastIndex, item.index);
        elements.push(...parseRegularText(beforeText, currentIndex));
        currentIndex += 100;
      }

      // Add the special section
      if (item.type === 'quick') {
        let cardContent = item.match[1]
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&amp;/g, '&')
          .replace(/&#39;/g, "'")
          .replace(/&nbsp;/g, ' ')
          .replace(/<(?!\/?tooltip(?:\s|>))[^>]*>/gi, '') // preserve <tooltip> and </tooltip>
          .replace(/Quick Answer\s*:?/g, '')
          .replace(/^\s*:?\s*/, '')
          .replace(/^\n*:/, '')
          .replace(/^\s*:\s*/, '')
          .trim();

        const quickKey = currentIndex;
        currentIndex += 1;
        elements.push(
          <TouchableOpacity
            key={`quick-${quickKey}`}
            activeOpacity={0.95}
            style={styles.quickAnswerWrapper}
          >
            <LinearGradient
              colors={[colors.surfaceMuted, colors.surface]}
              style={[styles.quickAnswerCard, { borderColor: colors.cardBorder }]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <LinearGradient
                colors={['rgba(255, 107, 53, 0.1)', 'transparent']}
                style={styles.cardGlow}
                start={{ x: 0, y: 0 }}
                end={{ x: 0.5, y: 0.5 }}
              />
              <View style={styles.cardHeader}>
                <View style={styles.iconCircle}>
                  <Animated.Text style={[
                    styles.lightningIcon,
                    {
                      transform: [{
                        scale: fadeAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: [1, 1.2]
                        })
                      }]
                    }
                  ]}>⚡</Animated.Text>
                </View>
                <View>
                  <Text style={[styles.cardTitle, { color: colors.primary }]}>{t('premiumUi.chat.quickAnswer')}</Text>
                  <View style={[styles.titleUnderline, { backgroundColor: colors.primary }]} />
                </View>
              </View>
              <View style={styles.cardText}>
                {renderTextWithBold(cardContent, quickKey * 1000, message.role, [styles.cardText, { color: colors.text }])}
              </View>

              {/* Decorative sparkle */}
              <Text style={styles.sparkleIcon}>✨</Text>
            </LinearGradient>
          </TouchableOpacity>
        );
        currentIndex += 100;
      } else if (item.type === 'final') {
        let cardContent = item.match[1]
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&amp;/g, '&')
          .replace(/&#39;/g, "'")
          .replace(/&nbsp;/g, ' ')
          .replace(/<(?!\/?tooltip(?:\s|>))[^>]*>/gi, '') // preserve <tooltip> and </tooltip>
          .replace(/Final Thoughts\s*:?/g, '')
          .replace(/^\s*:?\s*/, '')
          .replace(/^\n*:/, '')
          .replace(/^\s*:\s*/, '')
          .trim();

        const finalKey = currentIndex;
        currentIndex += 100;
        elements.push(
          <TouchableOpacity
            key={`final-${finalKey}`}
            activeOpacity={0.95}
            style={styles.finalThoughtsWrapper}
          >
            <LinearGradient
              colors={[colors.surfaceMuted, colors.surface]}
              style={[styles.finalThoughtsCard, { borderColor: colors.cardBorder }]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <LinearGradient
                colors={['rgba(65, 105, 225, 0.1)', 'transparent']}
                style={styles.cardGlow}
                start={{ x: 1, y: 0 }}
                end={{ x: 0.5, y: 0.5 }}
              />
              <View style={styles.cardHeader}>
                <View style={[styles.iconCircle, { backgroundColor: 'rgba(65, 105, 225, 0.1)', borderColor: 'rgba(65, 105, 225, 0.2)' }]}>
                  <Text style={styles.thoughtIcon}>💭</Text>
                </View>
                <View>
                  <Text style={[styles.cardTitle, { color: colors.primary }]}>{t('premiumUi.chat.finalThoughts')}</Text>
                  <View style={[styles.titleUnderline, { backgroundColor: colors.primary }]} />
                </View>
              </View>
              <View style={styles.cardText}>
                {renderTextWithBold(cardContent, finalKey * 1000, message.role, [styles.cardText, { color: colors.text }])}
              </View>
              <Text style={[styles.sparkleIcon, { color: '#4169E1' }]}>📜</Text>
            </LinearGradient>
          </TouchableOpacity>
        );
      } else if (item.type === 'table') {
        // Parse table data
        const tableContent = item.match[1];
        const parts = tableContent.split('|||');
        if (parts.length >= 2) {
          const headerRow = parts[0].split('|').map(h => h.trim()).filter(h => h);
          const rowsText = parts[1].trim();
          const dataRows = rowsText.split('\n')
            .map(row => row.trim())
            .filter(row => row && row.includes('|') && !row.match(/^\s*\|[\s:-]+\|/))
            .slice(0, 10); // Limit rows to prevent infinite scroll

          // console.log('Table debug:', { headerRow, dataRows, rowsText, tableContent });

          if (dataRows.length > 0) {
            const columnWidth = headerRow.length >= 6 ? 132 : 108;
            const tableWidth = Math.max(headerRow.length * columnWidth, Dimensions.get('window').width - 56);
            elements.push(
              <ScrollView
                key={`table-${currentIndex++}`}
                horizontal
                showsHorizontalScrollIndicator
                nestedScrollEnabled
                style={styles.tableScroll}
                contentContainerStyle={styles.tableScrollContent}
              >
                <View
                  style={[
                    styles.tableContainer,
                    {
                      width: tableWidth,
                      backgroundColor: colors.surfaceMuted,
                      borderColor: colors.cardBorder,
                      shadowColor: colors.primary,
                    },
                  ]}
                >
                  {/* Header */}
                  <View
                    style={[
                      styles.tableHeaderRow,
                      {
                        backgroundColor: colors.cosmicSurface,
                        borderBottomColor: colors.cosmicLine,
                      },
                    ]}
                  >
                    {headerRow.map((header, idx) => (
                      <View key={`th-${idx}`} style={[styles.tableHeaderCellWrap, { width: columnWidth }]}>
                        {renderTextWithBold(header, 2000 + idx, message.role, [styles.tableHeaderCell, { color: colors.textInverse }])}
                      </View>
                    ))}
                  </View>
                  {/* Rows */}
                  {dataRows.map((row, rowIdx) => {
                    const cells = row.split('|').map(c => c.trim()).filter(c => c);
                    if (cells.length === 0) return null;
                    return (
                      <View
                        key={`tr-${rowIdx}`}
                        style={[
                          styles.tableRow,
                          {
                            backgroundColor: rowIdx % 2 === 0 ? colors.surface : colors.surfaceMuted,
                            borderBottomColor: colors.cardBorder,
                          },
                        ]}
                      >
                        {cells.map((cell, cellIdx) => (
                          <View key={`td-${rowIdx}-${cellIdx}`} style={[styles.tableCellWrap, { width: columnWidth }]}>
                            {renderTextWithBold(cell, 2000 + rowIdx * 100 + cellIdx, message.role, [styles.tableCell, { color: colors.text }])}
                          </View>
                        ))}
                      </View>
                    );
                  }).filter(Boolean)}
                </View>
              </ScrollView>
            );
          }
        }
      }

      lastIndex = item.lastIndex;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      const remainingText = text.slice(lastIndex);
      elements.push(...parseRegularText(remainingText, currentIndex));
    }

    return elements;
  };

  /** Bold + italic for one substring (no tooltips); used inside tooltip parts and sentiment wrappers. */
  const stripAnySentimentMarkers = (value) =>
    String(value || '')
      .replace(/\\?\[(POS|NEG)_(START|END)\]/g, '')
      .replace(/【(POS|NEG)_(START|END)】/g, '');

  const renderPlainSegmentWithBoldItalic = (segment, keyPrefix, baseTextStyle, textStyle, sentimentColor) => {
    const tone = sentimentColor ? { color: sentimentColor, fontWeight: '700' } : null;
    const elements = [];
    const boldRegex = /\*\*(.*?)\*\*/gs;
    const cleanSegment = stripAnySentimentMarkers(segment);
    const boldParts = cleanSegment.split(boldRegex);

    boldParts.forEach((boldPart, boldIndex) => {
      if (boldIndex % 2 === 1) {
        elements.push(
          <Text
            key={`bold-${keyPrefix}-${boldIndex}`}
            style={[
              styles.boldText,
              baseTextStyle,
              { color: colors.text },
              message.role === 'user' && styles.userText,
              message.role === 'user' && { fontWeight: '700' },
              tone,
            ]}
          >
            {boldPart}
          </Text>
        );
      } else if (boldPart) {
        const italicRegex = /\*(.*?)\*/g;
        const italicParts = boldPart.split(italicRegex);

        italicParts.forEach((italicPart, italicIndex) => {
          if (italicIndex % 2 === 1) {
            elements.push(
              <Text
                key={`italic-${keyPrefix}-${boldIndex}-${italicIndex}`}
                style={[
                  styles.regularText,
                  baseTextStyle,
                  { color: colors.text },
                  { fontStyle: 'italic' },
                  message.role === 'user' && styles.userText,
                  tone,
                ]}
              >
                {italicPart}
              </Text>
            );
          } else if (italicPart) {
            elements.push(
              <Text
                key={`text-${keyPrefix}-${boldIndex}-${italicIndex}`}
                style={[textStyle, tone]}
              >
                {italicPart}
              </Text>
            );
          }
        });
      }
    });
    return elements;
  };

  /** One line of text → inline Text nodes (tooltips, bold, italic, [PC-9] sentiment). */
  const buildInlineElementsForLine = (line, keyPrefix, baseTextStyle, textStyle) => {
    const elements = [];
    let text = String(line || '').replace(/^#+\s*/, '').replace(/\s+#+\s+/g, ' ').trim();
    const tooltipRegex = /<tooltip data-term="([^"]+)">([^<]+)<\/tooltip>/g;
    const parts = text.split(tooltipRegex);
    const segmentRegex = /(?:【|\[)POS_START(?:】|\])([\s\S]*?)(?:【|\[)POS_END(?:】|\])|(?:【|\[)NEG_START(?:】|\])([\s\S]*?)(?:【|\[)NEG_END(?:】|\])/g;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (i % 3 === 2) {
        const termId = parts[i - 1];
        const definition = (message.glossary && message.glossary[termId]) ? message.glossary[termId] : '';
        elements.push(
          <Text
            key={`tooltip-${keyPrefix}-${i}`}
            onPress={() => setTooltipModal({ show: true, term: part, definition: definition })}
            style={[
              baseTextStyle,
              styles.tooltipText,
              {
                color: colors.primary,
                backgroundColor: colors.surfaceMuted,
                borderColor: colors.cardBorder,
              },
            ]}
          >
            {part} ⓘ
          </Text>
        );
      } else if (i % 3 === 0 && part) {
        segmentRegex.lastIndex = 0;
        let last = 0;
        let m;
        let sub = 0;
        while ((m = segmentRegex.exec(part)) !== null) {
          if (m.index > last) {
            elements.push(
              ...renderPlainSegmentWithBoldItalic(
                part.slice(last, m.index),
                `${keyPrefix}-${i}-${sub++}`,
                baseTextStyle,
                textStyle,
                null
              )
            );
          }
          const isPos = m[1] !== undefined;
          const inner = isPos ? m[1] : m[2];
          const sentimentColor = isPos ? '#15803d' : '#b91c1c';
          const innerEls = renderPlainSegmentWithBoldItalic(
            inner,
            `${keyPrefix}-${i}-${sub++}`,
            baseTextStyle,
            textStyle,
            sentimentColor
          );
          elements.push(
            <Text
              key={`sentiment-${keyPrefix}-${i}-${m.index}`}
              style={[baseTextStyle, isPos ? styles.sentimentPositive : styles.sentimentNegative]}
            >
              {innerEls}
            </Text>
          );
          last = segmentRegex.lastIndex;
        }
        if (last < part.length) {
          elements.push(
            ...renderPlainSegmentWithBoldItalic(
              part.slice(last),
              `${keyPrefix}-${i}-${sub}`,
              baseTextStyle,
              textStyle,
              null
            )
          );
        }
      }
    }
    return elements;
  };

  const renderTextWithBold = (text, startIndex, role, baseTextStyle) => {
    const textStyle = baseTextStyle
      ? [styles.regularText, baseTextStyle, { color: colors.text }, message.role === 'user' && styles.userText]
      : [styles.regularText, { color: colors.text }, message.role === 'user' && styles.userText];
    const raw = (text || '');
    const lines = raw.split('\n');
    const allChildren = [];
    lines.forEach((line, li) => {
      if (li > 0) allChildren.push('\n');
      allChildren.push(...buildInlineElementsForLine(line, `${startIndex}-${li}`, baseTextStyle, textStyle));
    });
    if (allChildren.length === 0) return [];
    return [
      <Text key={`line-${startIndex}`} style={textStyle}>
        {allChildren}
      </Text>,
    ];
  };

  const getHeaderSymbol = (headerText) => {
    const text = headerText.toLowerCase();
    if (text.includes('life stage') || text.includes('context')) return '🌱';
    if (text.includes('astrological analysis') || text.includes('analysis')) return '🔍';
    if (text.includes('parashari')) return '🏛️';
    if (text.includes('jaimini')) return '🔱';
    if (text.includes('nadi')) return '🧬';
    if (text.includes('kp') || text.includes('stellar')) return '🎯';
    if (text.includes('synthesis')) return '⚛️';
    if (text.includes('career') || text.includes('profession')) return '💼';
    if (text.includes('nakshatra') || text.includes('star')) return '⭐';
    if (text.includes('classical authority') || text.includes('authority') || text.includes('classical')) return '📜';
    if (text.includes('timing') && text.includes('guidance')) return '⏰';
    if (text.includes('timing') || text.includes('time')) return '🕐';
    if (text.includes('guidance') || text.includes('advice')) return '🌟';
    if (text.includes('final thoughts') || text.includes('thoughts')) return '💭';
    if (text.includes('relationship') || text.includes('love') || text.includes('marriage')) return '💕';
    if (text.includes('health') || text.includes('wellness')) return '🌿';
    if (text.includes('finance') || text.includes('money') || text.includes('wealth')) return '💰';
    if (text.includes('spiritual') || text.includes('meditation')) return '🕉️';
    if (text.includes('remedy') || text.includes('solution')) return '☀️';
    if (text.includes('prediction') || text.includes('forecast')) return '🌙';
    if (text.includes('transit') || text.includes('planetary')) return '🪐';
    return '✨'; // Default symbol
  };

  /**
   * Convert web/chat HTML (and HTML emitted by the web formatter) into plain text + markdown
   * that parseRegularText understands. Preserves <tooltip> tags for renderTextWithBold.
   */
  const normalizeNativePlainChunk = (raw) => {
    if (!raw || !String(raw).trim()) return '';
    let out = String(raw);
    out = out.replace(/<br\s*\/?>/gi, '\n');
    out = out.replace(/<\/p>\s*<p[^>]*>/gi, '\n\n');
    out = out.replace(/<p[^>]*>/gi, '\n');
    out = out.replace(/<\/p>/gi, '\n');
    out = out.replace(/<div class="follow-up-questions">([\s\S]*?)<\/div>/gi, (_, inner) => {
      const lines = inner.split(/\n/).map((l) => l.replace(/^-\s*/, '').trim()).filter(Boolean);
      if (!lines.length) return '';
      return `\n\n${lines.map((l) => `- ${l.replace(/<(?!\/?tooltip\b)[^>]+>/gi, '').trim()}`).join('\n')}`;
    });
    out = out.replace(/<ul[^>]*>([\s\S]*?)<\/ul>/gi, (_, ul) => {
      const chunks = [];
      ul.replace(/<li[^>]*>([\s\S]*?)<\/li>/gi, (_m, li) => {
        let t = li.replace(/<(?!\/?tooltip\b)[^>]+>/gi, '').trim();
        while (/^[\u2022•]\s*/.test(t)) t = t.replace(/^[\u2022•]\s*/, '');
        chunks.push(`\n- ${t}`);
        return '';
      });
      return chunks.join('');
    });
    out = out.replace(/<h3[^>]*>([\s\S]*?)<\/h3>/gi, '\n\n### $1\n\n');
    out = out.replace(/<h4[^>]*>([\s\S]*?)<\/h4>/gi, '\n\n#### $1\n\n');
    out = out.replace(/<strong[^>]*>([\s\S]*?)<\/strong>/gi, '**$1**');
    out = out.replace(/<em[^>]*>([\s\S]*?)<\/em>/gi, '*$1*');
    // [PC-9] Web sentiment spans → markers (parsed in buildInlineElementsForLine)
    out = out.replace(
      /<span\s+class=["']chat-sentiment-positive["'][^>]*>([\s\S]*?)<\/span>/gi,
      '【POS_START】$1【POS_END】'
    );
    out = out.replace(
      /<span\s+class=["']chat-sentiment-negative["'][^>]*>([\s\S]*?)<\/span>/gi,
      '【NEG_START】$1【NEG_END】'
    );
    // Some model outputs emit ASCII marker brackets directly; normalize them.
    out = out.replace(/\\?\[POS_START\]/g, '【POS_START】');
    out = out.replace(/\\?\[POS_END\]/g, '【POS_END】');
    out = out.replace(/\\?\[NEG_START\]/g, '【NEG_START】');
    out = out.replace(/\\?\[NEG_END\]/g, '【NEG_END】');
    out = out.replace(/<div class="chat-response">\s*/gi, '');
    out = out.replace(/\s*<\/div>\s*$/i, '');
    out = out.replace(/<\/div>/gi, '\n');
    out = out.replace(/<div[^>]*>/gi, '\n');
    out = out.replace(/<(?!\/?tooltip\b)[^>]+>/gi, '');
    out = sanitizeVisibleChatContent(out, { asHtmlSpans: false });
    return out;
  };

  /** Row uses a custom bullet View; strip all leading markdown + literal • so we never show • twice. */
  const stripLeadingListMarkersForNativeRow = (line) => {
    let s = String(line || '').trim();
    s = s.replace(/^\d+\.\s*/, '');
    for (let n = 0; n < 12; n++) {
      const prev = s;
      s = s.replace(/^[-*]\s+/, '');
      s = s.replace(/^[\u2022•]\s*/, '');
      if (s === prev) break;
    }
    return s.trim();
  };

  const parseRegularText = (text, startIndex) => {
    const elements = [];
    let currentIndex = startIndex;
    let listCounter = 0;

    text = normalizeNativePlainChunk(text);

    // Split by headers and paragraphs — full header line including colons (e.g. "### Key Insights:")
    const parts = text.split(/(<h3>.*?<\/h3>|##\s+[^\n]+|###\s+[^\n]+|####\s+[^\n]+|\n\n+)/).filter(part => {
      const trimmed = part.trim();
      // Filter out standalone # symbols
      return trimmed && trimmed !== '#';
    });

    for (const part of parts) {
      if (part.match(/<h3>(.*?)<\/h3>/)) {
        listCounter = 0; // Reset counter for new section
        let headerText = part.replace(/<h3>(.*?)<\/h3>/, '$1');
        headerText = headerText.replace(/^#+\s*/, '').trim();
        headerText = headerText.replace(/<tooltip[^>]*>([^<]+)<\/tooltip>/g, '$1');
        const symbol = getHeaderSymbol(headerText);
        elements.push(
          <View key={`header-${currentIndex++}`} style={styles.headerContainer}>
            <Text style={styles.headerIcon}>{symbol}</Text>
            <Text style={[styles.headerText, { color: colors.text }]}>{headerText}</Text>
          </View>
        );
      } else if (part.match(/^##\s+(.+)$/m) || part.match(/^###\s+(.+)$/m)) {
        listCounter = 0; // Reset counter for new section
        let headerText = part.replace(/^#+\s*/, '').trim();
        headerText = headerText.replace(/<tooltip[^>]*>([^<]+)<\/tooltip>/g, '$1');
        const symbol = getHeaderSymbol(headerText);
        elements.push(
          <View key={`header-${currentIndex++}`} style={styles.headerContainer}>
            <Text style={styles.headerIcon}>{symbol}</Text>
            <Text style={[styles.headerText, { color: colors.text }]}>{headerText}</Text>
          </View>
        );
      } else if (part.match(/^####\s+(.+)$/m)) {
        let headerText = part.split('\n')[0].replace(/^#+\s*/, '').trim();
        headerText = headerText.replace(/<tooltip[^>]*>([^<]+)<\/tooltip>/g, '$1');
        const symbol = getHeaderSymbol(headerText);
        elements.push(
          <View key={`subheader-${currentIndex++}`} style={styles.subHeaderContainer}>
            <Text style={styles.subHeaderIcon}>{symbol}</Text>
            <Text style={[styles.subHeaderText, { color: colors.text }]}>{headerText}</Text>
          </View>
        );
      } else if (part.trim()) {
        // Handle lists and regular text
        // Clean up leading colons and whitespace that might be left over from header split
        let cleanPart = part.replace(/^\s*[:：]\s*/, '');
        if (!cleanPart.trim()) continue;

        const lines = cleanPart.split('\n');

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine) {
            elements.push(<View key={`para-gap-${currentIndex++}`} style={{ height: 8 }} />);
            continue;
          }

          const isMarkdownBullet =
            trimmedLine.startsWith('•') ||
            /^[-*]\s+/.test(trimmedLine) ||
            /^\d+\.\s*/.test(trimmedLine);
          if (isMarkdownBullet) {
            const isNumbered = trimmedLine.match(/^(\d+)\./);
            const number = isNumbered ? isNumbered[1] : null;

            listCounter++;
            let cleanListText = stripLeadingListMarkersForNativeRow(trimmedLine)
              .replace(/&lt;/g, '<')
              .replace(/&gt;/g, '>')
              .replace(/&quot;/g, '"')
              .replace(/&amp;/g, '&')
              .replace(/&#39;/g, "'")
              .replace(/&nbsp;/g, ' ')
              .replace(/<[^>]*>/g, '');

            const listTextElements = renderTextWithBold(cleanListText, currentIndex, message.role, styles.listText);

            elements.push(
              <View key={`list-${currentIndex++}`} style={styles.listItem}>
                {isNumbered ? (
                  <View
                    style={[
                      styles.numberCircle,
                      { backgroundColor: colors.primary, shadowColor: colors.primary },
                    ]}
                  >
                    <Text style={[styles.numberText, { color: colors.onPrimary }]}>{number}</Text>
                  </View>
                ) : (
                  <View style={styles.bulletContainer}>
                    <View
                      style={[
                        styles.bulletDot,
                        { backgroundColor: colors.primary, shadowColor: colors.primary },
                      ]}
                    />
                  </View>
                )}
                <View style={styles.listContent}>
                  {listTextElements}
                </View>
              </View>
            );
          } else {
            // Strip markdown header hashes so #### / ### / ## never show in paragraph text (leading or mid-line)
            let processedLine = trimmedLine.replace(/^#+\s*/, '').replace(/\s+#+\s+/g, ' ').trim();
            if (!processedLine) continue;
            processedLine = processedLine
              .replace(/&lt;/g, '<')
              .replace(/&gt;/g, '>')
              .replace(/&quot;/g, '"')
              .replace(/&amp;/g, '&')
              .replace(/&#39;/g, "'")
              .replace(/&nbsp;/g, ' ');

            // Process tooltips after HTML entity decoding (first occurrence per term only)
            if (message.terms && message.glossary) {
              processedLine = processedLine.replace(/<term id="([^"]+)">([^<]+)<\/term>/g, (match, termId, termText) => {
                const key = termId.toLowerCase().trim();
                if (message.glossary[termId] && !wrappedTermsInRender.has(key)) {
                  wrappedTermsInRender.add(key);
                  return `<tooltip data-term="${termId}">${termText}</tooltip>`;
                }
                return message.glossary[termId] ? termText : match;
              });
            }

            // Remove any remaining term tags that weren't processed
            processedLine = processedLine.replace(/<term id="[^"]+">([^<]+)<\/term>/g, '$1');

            // Regular text with bold formatting
            const textElements = renderTextWithBold(processedLine, currentIndex, message.role);
            elements.push(...textElements);
            currentIndex += textElements.length;
          }
        }
      }
    }

    return elements;
  };



  // Check if this is a clarification message
  const isClarification = message.message_type === 'clarification';
  const gateMetadata = message.gate_metadata || {};
  const gateIntent = message.intent_gate || gateMetadata.intent_gate || '';
  const isNativeGate =
    message.message_type === 'native_gate' ||
    message.intent_gate === 'create_native' ||
    (message.gate_metadata && message.gate_metadata.intent_gate === 'create_native') ||
    [
      'create_subject_chart',
      'complete_subject_birth_details',
      'relationship_setup',
      'partnership_offer',
    ].includes(gateIntent);
  const isRelationshipSetupGate = gateIntent === 'relationship_setup';
  const isPartnershipOfferGate = gateIntent === 'partnership_offer';
  const isSubjectChartGate =
    gateIntent === 'create_subject_chart' ||
    gateIntent === 'complete_subject_birth_details' ||
    gateIntent === 'create_native';

  const contentStr =
    typeof message.content === 'string'
      ? message.content
      : message.content != null
        ? String(message.content)
        : '';

  useEffect(() => {
    if (isInstantChatMessage) return;
    if (message.role !== 'assistant' || message.isTyping || message.isProcessing) return;
    if (isClarification || isNativeGate) return;
    const messageId = message.messageId || null;
    if (!messageId) return;
    if (messageHasReadyPodcast(messageId)) {
      setPodcastReady(true);
      return;
    }
    let active = true;
    void (async () => {
      try {
        const requestedLang = podcastLangFromUiLanguage(podcastListenLangRef.current);
        const status = await chatAPI.checkPodcastCache(messageId, requestedLang);
        if (!active) return;
        podcastLanguagesFromStatus(status, requestedLang).forEach((cachedLang) => {
          markPremiumPodcastReady(podcastReadyKey(messageId, cachedLang));
        });
      } catch (_) {
        /* ignore hydrate errors */
      }
    })();
    return () => {
      active = false;
    };
  }, [
    isClarification,
    isInstantChatMessage,
    isNativeGate,
    markPremiumPodcastReady,
    message.isProcessing,
    message.isTyping,
    message.messageId,
    message.role,
  ]);

  // Promo CTA on ChatScreen: skip the credits modal; user already consented in PodcastPromoModal.
  // This must run only for a fresh key. Remounting the bubble (open chat, scroll) must not replay.
  useEffect(() => {
    if (!podcastAutoLaunchKey) {
      lastPodcastPromoKeyRef.current = 0;
      return undefined;
    }
    if (isInstantChatMessage) return undefined;
    if (!podcastAutoLaunchMessageId) return undefined;
    const mid = message.messageId;
    if (!mid || String(mid) !== String(podcastAutoLaunchMessageId)) return undefined;
    if (message.role !== 'assistant' || message.isTyping) return undefined;
    if (isClarification || isNativeGate) return undefined;
    if (lastPodcastPromoKeyRef.current === podcastAutoLaunchKey) return undefined;
    const body = getCleanMessageText();
    if (!body || body.length < 80) return undefined;

    const timer = setTimeout(() => {
      lastPodcastPromoKeyRef.current = podcastAutoLaunchKey;
      skipPodcastCreditsRef.current = true;
      onPodcastAutoLaunchConsumed?.();
      continuePodcastAfterLanguage(
        String(podcastAutoLaunchLang || '').toLowerCase().startsWith('hi') ? 'hi' : 'en',
      );
    }, 400);
    return () => clearTimeout(timer);
  }, [
    isInstantChatMessage,
    podcastAutoLaunchKey,
    podcastAutoLaunchMessageId,
    podcastAutoLaunchLang,
    onPodcastAutoLaunchConsumed,
    message.messageId,
    message.role,
    message.isTyping,
    message.content,
    isClarification,
    isNativeGate,
  ]);

  const isFreeQuestionAnswer =
    message.role === 'assistant' &&
    !message.isTyping &&
    !isClarification &&
    !isNativeGate &&
    Boolean(gateMetadata.free_question_completed);
  const freeSplit = isFreeQuestionAnswer ? splitFreeAnswerContent(contentStr) : null;
  const canBlurFreeDetail =
    Boolean(freeSplit?.canBlur) && !isInstantChatMessage;

  useEffect(() => {
    let cancelled = false;
    const mid = message.messageId || message.id;
    if (!canBlurFreeDetail || !mid) {
      return undefined;
    }
    (async () => {
      try {
        const v = await AsyncStorage.getItem(freeDetailUnlockStorageKey(mid));
        if (!cancelled && v === '1') setDetailUnlocked(true);
      } catch (_) {
        /* ignore */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [canBlurFreeDetail, message.messageId, message.id]);

  useEffect(() => {
    if (!canBlurFreeDetail || detailUnlocked || blurShownTrackedRef.current) return;
    const mid = message.messageId || message.id;
    if (!mid) return;
    blurShownTrackedRef.current = true;
    creditAPI.recordFreeAnswerFunnelEvent('blur_shown', String(mid)).catch(() => {});
  }, [canBlurFreeDetail, detailUnlocked, message.messageId, message.id]);

  useEffect(() => {
    if (!hasRemedyCard) return;
    recordRemedyScreenImpressionOnce({ sessionId, message }).catch(() => {});
  }, [hasRemedyCard, sessionId, message]);

  useFocusEffect(
    useCallback(() => {
      if (!canBlurFreeDetail || detailUnlocked) return undefined;
      const mid = message.messageId || message.id;
      if (!mid) return undefined;
      let alive = true;
      (async () => {
        try {
          const clicked = await AsyncStorage.getItem(freeDetailRevealClickedStorageKey(mid));
          if (clicked !== '1') return;
          await refreshCredits?.();
          if (!alive) return;
          // Unlock after the user tapped reveal and returned with a positive balance.
          if (Number(credits) > 0) {
            try {
              await AsyncStorage.setItem(freeDetailUnlockStorageKey(mid), '1');
            } catch (_) {
              /* ignore */
            }
            setDetailUnlocked(true);
          }
        } catch (_) {
          /* ignore */
        }
      })();
      return () => {
        alive = false;
      };
    }, [canBlurFreeDetail, detailUnlocked, credits, refreshCredits, message.messageId, message.id]),
  );

  // Loading rows use LoadingBubble (isTyping), not MessageBubble — skip empty assistant rows safely.
  if (!contentStr.trim()) {
    return null;
  }

  const shouldBlurDetail = canBlurFreeDetail && !detailUnlocked;

  const displayContent = shouldBlurDetail ? freeSplit.quick : contentStr;
  const detailTeaser = shouldBlurDetail
    ? String(freeSplit.detail || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 280)
    : '';

  const formattedContent = formatContent(displayContent);
  const renderedElements = renderFormattedText(formattedContent);

  // Instant consultation is intentionally a conversation, not a report card.
  // Keep the payload readable but remove formatting chrome generated for the
  // Standard/Premium renderer (headings, markdown markers and HTML wrappers).
  const instantPlainContent = String(displayContent || '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    .replace(/[`*_]+/g, '')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();

  if (isInstantChatMessage) {
    const instantTime = new Date(message.timestamp || Date.now()).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
    const isUser = message.role === 'user';

    return (
      <>
      <Animated.View
        style={[
          styles.instantMessageRow,
          isUser ? styles.instantMessageRowUser : styles.instantMessageRowAssistant,
          { opacity: fadeAnim, transform: [{ translateY: slideAnim }] },
        ]}
      >
        <View
          style={[
            styles.instantMessageBubble,
            isUser ? styles.instantMessageBubbleUser : styles.instantMessageBubbleAssistant,
            {
              backgroundColor: isUser ? colors.selectionSurface : colors.surface,
              borderColor: isUser ? colors.selectionBorder : colors.cardBorder,
            },
          ]}
        >
          <Text style={[styles.instantMessageText, { color: colors.text }]}>
            {instantPlainContent}
          </Text>
          {message.instantStreaming ? (
            <View style={styles.instantInlineTyping}>
              {[dot1Anim, dot2Anim, dot3Anim].map((opacity, dot) => (
                <Animated.View
                  key={dot}
                  style={[styles.instantInlineTypingDot, { backgroundColor: colors.primary, opacity }]}
                />
              ))}
            </View>
          ) : null}
          <Text style={[styles.instantMessageTime, { color: colors.textTertiary }]}>{instantTime}</Text>
          {!isUser && instantEvidence ? (
            <>
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityState={{ expanded: showInstantEvidence }}
                accessibilityLabel={whyTaraSaysThis(language || i18n.resolvedLanguage || i18n.language)}
                style={[styles.instantEvidenceToggle, {
                  backgroundColor: colors.accentSoft,
                  borderColor: colors.cardBorder,
                }]}
                onPress={() => setShowInstantEvidence(true)}
              >
                <Ionicons name="diamond-outline" size={16} color={colors.text} />
                <Text
                  style={[styles.instantEvidenceToggleText, { color: colors.text }]}
                >
                  {whyTaraSaysThis(language || i18n.resolvedLanguage || i18n.language)
                    || t('premiumUi.chat.whyThisAnswer', 'Why Tara says this')}
                </Text>
                <Ionicons name="open-outline" size={15} color={colors.text} />
              </TouchableOpacity>
            </>
          ) : null}
        </View>
      </Animated.View>
        <Modal
          visible={!isUser && Boolean(showInstantEvidence && instantEvidence)}
          transparent
          animationType="slide"
          statusBarTranslucent
          onRequestClose={() => setShowInstantEvidence(false)}
        >
          <View style={styles.instantEvidenceModalBackdrop}>
            <View style={[styles.instantEvidenceModalCard, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
              <View style={[styles.instantEvidenceModalHeader, { borderBottomColor: colors.cardBorder }]}>
                <View style={styles.instantEvidenceHeaderCopy}>
                  <Text style={[styles.instantEvidenceEyebrow, { color: colors.accent }]}>
                    {whyTaraSaysThis(language || i18n.resolvedLanguage || i18n.language)}
                  </Text>
                </View>
                <TouchableOpacity
                  accessibilityRole="button"
                  accessibilityLabel={t('common.close', 'Close')}
                  style={[styles.instantEvidenceModalClose, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}
                  onPress={() => setShowInstantEvidence(false)}
                >
                  <Ionicons name="close" size={22} color={colors.text} />
                </TouchableOpacity>
              </View>
              <ScrollView
                style={styles.instantEvidenceModalScroll}
                contentContainerStyle={styles.instantEvidenceModalContent}
                showsVerticalScrollIndicator
              >
                <InstantEvidenceDetails evidence={instantEvidence} colors={colors} t={t} />
              </ScrollView>
            </View>
          </View>
        </Modal>
      </>
    );
  }

  const chartName = message.native_name || null;

  const BubbleWrapper = ({ children, role, isPartnership, isClarification, timestamp }) => {
    if (role === 'user') {
      return (
        <LinearGradient
          colors={[colors.surfaceMuted, colors.surfaceMuted]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={[
            styles.bubble,
            styles.userBubble,
            isPartnership && styles.partnershipBubble,
            { borderColor: colors.cardBorder },
          ]}
        >
          <View style={styles.userHeader}>
            <LinearGradient
              colors={[colors.primary, colors.primaryStrong]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.userBadge}
            >
            <Ionicons name="person" size={10} color={colors.onPrimary} style={styles.userIcon} />
            <Text style={[styles.userLabel, { color: colors.onPrimary }]}>{t('chat.you', 'You')}</Text>
          </LinearGradient>
            {chartName ? (
              <View style={[
                styles.chartNameBadge,
                {
                  backgroundColor: colors.accentSoft,
                  borderWidth: 1,
                  borderColor: colors.cardBorder,
                },
              ]}>
                <Ionicons name="calendar-outline" size={10} color={colors.onAccent} />
                <Text style={[styles.chartNameBadgeText, { color: colors.onAccent }]} numberOfLines={1}>{chartName}</Text>
              </View>
            ) : null}
          </View>
          {children}
          <Text style={[styles.timestamp, { color: colors.textTertiary }]}>
            {new Date(timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </Text>
        </LinearGradient>
      );
    }
    return (
      <View style={[
        styles.bubble,
        styles.assistantBubble,
        isPartnership && styles.partnershipBubble,
        isClarification && styles.clarificationBubble,
        { backgroundColor: colors.surface, borderColor: colors.cardBorder, borderLeftColor: colors.primary },
      ]}>
        {children}
      </View>
    );
  };

  return (
    <>
    <Animated.View style={[
      styles.container,
      message.role === 'user' ? styles.userContainer : styles.assistantContainer,
      { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }
    ]}>
      <BubbleWrapper
        role={message.role}
        isPartnership={isPartnership}
        isClarification={isClarification}
        timestamp={message.timestamp}
      >
        {message.role === 'assistant' && (
          <View style={styles.assistantHeader}>
            <LinearGradient
              colors={[colors.cosmicRaised, colors.cosmicRaised]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.verifiedBadge}
            >
            <Ionicons name="sparkles-outline" size={12} color={colors.accent} style={styles.verifiedIcon} />
            <Text style={[styles.assistantLabel, { color: colors.textInverse }]}>
              {isClarification
                ? t('chat.inquiry', 'AstroRoshni Inquiry')
                : isNativeGate
                  ? t('chat.nativeGateBadge', 'Saved profile needed')
                  : t('chat.verified', 'Tara · chart synthesis')}
            </Text>
          </LinearGradient>
            {chartName ? (
              <View style={[
                styles.chartNameBadge,
                {
                  backgroundColor: colors.accentSoft,
                  borderWidth: 1,
                  borderColor: colors.cardBorder,
                },
              ]}>
                <Ionicons name="calendar-outline" size={10} color={colors.onAccent} />
                <Text style={[styles.chartNameBadgeText, { color: colors.onAccent }]} numberOfLines={1}>{chartName}</Text>
              </View>
            ) : null}
            {message.isTyping && (
              <View style={styles.typingIndicatorBadge}>
                <Text style={styles.typingIndicatorText}>{Platform.OS === 'ios' ? 'Reviewing chart...' : 'Analyzing Chart...'}</Text>
              </View>
            )}
          </View>
        )}

        <View style={styles.messageContent}>
          {renderedElements}
          {message.instantStreaming ? (
            <View
              style={[
                styles.instantResponseTyping,
                { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder },
              ]}
              accessibilityLabel={t('chat.instantLoader.lineHouses', 'Tara is typing…')}
            >
              {[dot1Anim, dot2Anim, dot3Anim].map((opacity, dot) => (
                <Animated.View
                  key={dot}
                  style={[styles.instantResponseTypingDot, { backgroundColor: colors.primary, opacity }]}
                />
              ))}
            </View>
          ) : null}
        </View>

        {/* Summary Image */}
        {message.summary_image && (
          <TouchableOpacity
            style={styles.imageContainer}
            onPress={() => setShowImageModal(true)}
            activeOpacity={0.8}
          >
            {isImageLoading && (
              <View style={styles.skeletonWrapper}>
                <Animated.View
                  style={[
                    styles.skeletonGradient,
                    {
                      opacity: skeletonAnim.interpolate({
                        inputRange: [0, 1],
                        outputRange: [0.3, 0.7]
                      })
                    }
                  ]}
                />
                <View style={styles.skeletonContent}>
                  <Ionicons name="image-outline" size={32} color="rgba(255, 107, 53, 0.2)" />
                  <Text style={styles.skeletonText}>{t('premiumUi.chat.preparingChart')}</Text>
                </View>
              </View>
            )}
            <Image
              source={{ uri: message.summary_image }}
              style={[
                styles.summaryImage,
                isImageLoading && { position: 'absolute', opacity: 0 }
              ]}
              resizeMode="contain"
              onError={(e) => {
                console.log('❌ Image load error:', e.nativeEvent.error);
                setIsImageLoading(false);
              }}
              onLoad={() => {
                console.log('✅ Image loaded successfully');
                setIsImageLoading(false);
              }}
            />
            {!isImageLoading && (
              <Text style={styles.tapToEnlarge}>{t('premiumUi.chat.tapEnlarge')}</Text>
            )}
          </TouchableOpacity>
        )}

        {message.role === 'assistant' && !isClarification && !isNativeGate && (
          <View style={[styles.disclaimerNotice, { borderTopColor: colors.cardBorder }]}>
            <Ionicons name="information-circle-outline" size={13} color={colors.textTertiary} />
            <Text style={[styles.disclaimerNoticeText, { color: colors.textTertiary }]}>
              {t('chat.disclaimerNoticeCompact', 'Astrological guidance is probabilistic; use qualified advice for important medical, legal or financial decisions.')}
            </Text>
          </View>
        )}

        {shouldBlurDetail && (
          <View style={styles.freeDetailPaywall}>
            <View style={styles.freeDetailBlurBlock} pointerEvents="none">
              <Text style={styles.freeDetailTeaser} numberOfLines={5}>
                {detailTeaser ||
                  t(
                    'chat.freeDetailTeaserFallback',
                    'Key Insights, Astrological Analysis, Timing & more…',
                  )}
              </Text>
              <View style={styles.freeDetailBlurOverlay} />
            </View>
            <TouchableOpacity
              style={styles.freeDetailRevealBtn}
              activeOpacity={0.9}
              onPress={() => setShowRevealCreditsModal(true)}
              accessibilityRole="button"
              accessibilityLabel={t('chat.revealDetailedAnswerA11y', 'Reveal the detailed answer')}
            >
              <LinearGradient
                colors={['#ea580c', '#f97316']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.freeDetailRevealGradient}
              >
                <Ionicons name="lock-open-outline" size={16} color="#fff" style={{ marginRight: 6 }} />
                <Text style={styles.freeDetailRevealText}>
                  {t('chat.revealDetailedAnswer', 'Reveal the detailed answer')}
                </Text>
              </LinearGradient>
            </TouchableOpacity>
            <Text style={styles.freeDetailHint}>
              {t(
                'chat.revealDetailedAnswerHint',
                'Standard mode · {{count}} credits',
                { count: standardChatCost },
              )}
            </Text>
          </View>
        )}

        {isNativeGate && !message.isTyping && (
          <View style={styles.nativeGateActionsWrap}>
            <Text style={[styles.nativeGateHelperText, { color: colors.textSecondary }]}>
              {t(
                'chat.nativeGateTapInstruction',
                'Please choose one of the options below instead of typing a reply.'
              )}
            </Text>
            {isRelationshipSetupGate ? (
              <View style={styles.nativeGateOptionsWrap}>
                {(gateMetadata.relationship_setup?.options || []).map((option, index) => {
                  const label = String(option?.label || option?.value || '').trim();
                  const value = String(option?.value || label).trim();
                  if (!label || !value) return null;
                  const originalQuestion = String(gateMetadata.original_question || '').trim();
                  const nextQuestion = originalQuestion
                    ? `${originalQuestion}\n\nRelationship context: ${value}`
                    : `Relationship context: ${value}`;
                  return (
                    <TouchableOpacity
                      key={`relationship-gate-${index}-${label}`}
                      style={styles.nativeGateOptionChip}
                      onPress={() => {
                        if (onRelationshipContextGate) {
                          onRelationshipContextGate(gateMetadata, value, nextQuestion);
                        } else {
                          onFollowUpClick && onFollowUpClick(nextQuestion);
                        }
                      }}
                      activeOpacity={0.85}
                    >
                      <Text style={styles.nativeGateOptionText}>{label}</Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            ) : (
              <View style={styles.nativeGateActionsRow}>
                {isSubjectChartGate && (
                  <TouchableOpacity
                    style={styles.nativeGateSelectCta}
                    onPress={() => navigation.navigate('SelectNative', { returnTo: 'Home' })}
                    activeOpacity={0.85}
                    accessibilityRole="button"
                    accessibilityLabel={t('chat.selectNativeA11y', 'Select or create another birth chart')}
                  >
                    <Text style={styles.nativeGateSelectCtaText}>
                      {t('chat.nativeGateSelectNative', 'Select native')}
                    </Text>
                  </TouchableOpacity>
                )}
                {isSubjectChartGate && (
                  <TouchableOpacity
                    style={styles.nativeGateCtaOuter}
                    onPress={() => {
                      const hint = gateMetadata.extracted_birth_hint || {};
                      navigation.navigate('BirthForm', {
                        chartGatePrefill: {
                          name: hint.name || '',
                          date: hint.date || null,
                          time: hint.time || null,
                          place: hint.place || '',
                          latitude: hint.latitude ?? null,
                          longitude: hint.longitude ?? null,
                          gender: hint.gender || '',
                        },
                        returnTo: 'Home',
                      });
                    }}
                    activeOpacity={0.9}
                    accessibilityRole="button"
                    accessibilityLabel={t('chat.addBirthProfileA11y', 'Add a new birth profile')}
                  >
                    <LinearGradient
                      colors={['#ff6b35', '#f97316']}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 0 }}
                      style={styles.nativeGateCtaGradient}
                    >
                      <Ionicons name="add" size={17} color="#fff" style={{ marginRight: 6 }} />
                      <Text style={styles.nativeGateCtaText}>
                        {gateIntent === 'complete_subject_birth_details'
                          ? t('chat.nativeGateCompleteProfile', 'Complete birth profile')
                          : t('chat.nativeGateAddNewProfile', 'Add new native')}
                      </Text>
                    </LinearGradient>
                  </TouchableOpacity>
                )}
                {(isPartnershipOfferGate || isSubjectChartGate) && (
                  <>
                    {isPartnershipOfferGate && (
                      <TouchableOpacity
                        style={[
                          styles.nativeGateSecondaryCta,
                          {
                            backgroundColor: colors.accentSoft,
                            borderColor: colors.cardBorder,
                          },
                        ]}
                        onPress={() => onStartPartnershipGate && onStartPartnershipGate(gateMetadata)}
                        activeOpacity={0.85}
                        accessibilityRole="button"
                        accessibilityLabel={t('chat.startPartnershipA11y', 'Start partnership study')}
                      >
                        <Ionicons name="people-outline" size={16} color={colors.onAccent} style={{ marginRight: 6 }} />
                        <Text style={[styles.nativeGateSecondaryCtaText, { color: colors.onAccent }]}>
                        {t('chat.startPartnershipAnalysis', Platform.OS === 'ios' ? 'Start partnership study' : 'Start Partnership Analysis')}
                        </Text>
                      </TouchableOpacity>
                    )}
                    <TouchableOpacity
                      style={[
                        styles.nativeGatePlainCta,
                        {
                          borderColor: colors.cardBorder,
                          backgroundColor: colors.surfaceMuted,
                        },
                      ]}
                      onPress={() => onContinueSingleChartGate && onContinueSingleChartGate(gateMetadata)}
                      activeOpacity={0.85}
                      accessibilityRole="button"
                      accessibilityLabel={t('chat.continueSingleChartA11y', 'Continue with selected chart only')}
                    >
                      <Text style={[styles.nativeGatePlainCtaText, { color: colors.textSecondary }]}>
                        {t('chat.continueSingleChart', 'Continue with my chart only')}
                      </Text>
                    </TouchableOpacity>
                  </>
                )}
              </View>
            )}
          </View>
        )}

        {/* NEW: Render Follow-up Questions from the dedicated prop */}
        {message.follow_up_questions && message.follow_up_questions.length > 0 && (
          <View style={styles.followUpContainer}>
            <Text style={[styles.followUpEyebrow, { color: colors.primary }]}>{t('premiumUi.chat.continueReading')}</Text>
            {message.follow_up_questions.map((question, index) => {
              const cleanQuestion = question
                .replace(/^[\s☀️🌟⭐💫✨📅💼🍎📚🧘*•-]+/, '')
                .replace(/\\?\[(POS|NEG)_(START|END)\]/g, '')
                .replace(/【(POS|NEG)_(START|END)】/g, '')
                .trim();
              if (cleanQuestion.length < 5) return null;
              return (
                <TouchableOpacity
                  key={`followup-prop-${index}`}
                  style={[
                    styles.followUpButton,
                    {
                      backgroundColor: colors.surfaceMuted,
                      borderColor: colors.cardBorder,
                    },
                  ]}
                  onPress={() => onFollowUpClick && onFollowUpClick(cleanQuestion)}
                  activeOpacity={0.78}
                >
                  <Text style={[styles.followUpIndex, { color: colors.primary }]}>0{index + 1}</Text>
                  <Text style={[styles.followUpText, { color: colors.text }]}>{cleanQuestion}</Text>
                  <View style={[styles.followUpArrow, { backgroundColor: colors.accentSoft }]}>
                    <Ionicons name="arrow-forward" size={15} color={colors.onAccent} />
                  </View>
                </TouchableOpacity>
              );
            }).filter(Boolean)}
          </View>
        )}

        {hasRemedyCard ? (
          <View
            style={[
              styles.remedyCard,
              {
                backgroundColor: colors.cosmicSurface,
                borderColor: colors.cosmicLine,
                shadowColor: colors.cosmicGlow,
              },
            ]}
          >
            <View style={styles.remedyCardHeader}>
              <View style={[styles.remedySeal, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}>
                <Ionicons name="sparkles-outline" size={17} color={colors.accent} />
              </View>
              <Text style={[styles.remedyEyebrow, { color: colors.accent }]}>{t('premiumUi.chat.personalizedRemedy')}</Text>
            </View>
            <Text style={[styles.remedyCardTitle, { color: colors.textInverse }]}>{message.next_action.title}</Text>
            <Text style={[styles.remedyCardReason, { color: colors.textInverseMuted }]}>{message.next_action.reason}</Text>
            <TouchableOpacity
              style={[styles.remedyCardButton, { backgroundColor: colors.accent }]}
              onPress={() => {
                const remedyPrompt = String(message.next_action.follow_up_questions[0]).trim();
                const sourceMessageId = message.messageId || message.id;
                if (sourceMessageId) {
                  creditAPI.recordRemedyFunnelEvent('card_clicked', String(sourceMessageId)).catch(() => {});
                }
                if (onRemedyFollowUpClick) {
                  onRemedyFollowUpClick(remedyPrompt, {
                    source: 'remedy_card',
                    nextAction: message.next_action || null,
                    messageId: sourceMessageId || null,
                  });
                  return;
                }
                onFollowUpClick && onFollowUpClick(remedyPrompt);
              }}
              activeOpacity={0.88}
            >
              <Text style={[styles.remedyCardButtonText, { color: colors.onAccent }]}>
                {message.next_action.follow_up_questions[0]}
              </Text>
              <Ionicons name="arrow-forward" size={16} color={colors.onAccent} />
            </TouchableOpacity>
          </View>
        ) : null}

        {/* Hint when a response timed out or send failed: tell user to tap refresh or retry */}
        {(message.showRestartButton || message.showSendRetryButton) && (
          <View style={styles.timeoutHint}>
            <Text style={styles.timeoutHintText}>
              {message.showSendRetryButton
                ? t('chat.timeoutHintRetry', 'Tap refresh to retry. If the problem continues, use the menu (☰) → New conversation to start a fresh session. Past threads stay in Chat History.')
                : t('chat.timeoutHint', 'Tap the refresh icon below to check again, or find your response later in Chat History.')}
            </Text>
            {message.showSendRetryButton && onStartNewChat ? (
              <TouchableOpacity
                style={styles.startNewChatLink}
                onPress={onStartNewChat}
                accessibilityRole="button"
                accessibilityLabel={t('chat.startNewChatA11y', 'Start new conversation')}
              >
                <Text style={styles.startNewChatLinkText}>{t('chat.startNewChat', 'Start new conversation')}</Text>
              </TouchableOpacity>
            ) : null}
          </View>
        )}

        {/* Action buttons (podcast, share, copy, etc.) - show for assistant messages with content (incl. chat history) */}
        {!message.isTyping && !message.instantStreaming && message.role === 'assistant' && !message.isWelcome && !isNativeGate && (message.messageId || message.content) && (
          <View style={[styles.actionButtons, { borderTopColor: colors.cardBorder }]}>
            {/* Restart Button for timeout messages */}
            {message.showRestartButton && message.messageId && (
              <TouchableOpacity
                style={[styles.actionButton, messageActionStyle, styles.restartButton]}
                onPress={() => onRestart && onRestart(message.messageId)}
              >
                <Ionicons name="refresh" size={16} color={colors.primary} />
              </TouchableOpacity>
            )}
            {/* Retry send button for initial network failures (no messageId yet) */}
            {message.showSendRetryButton && !message.messageId && (
              <TouchableOpacity
                style={[styles.actionButton, messageActionStyle, styles.restartButton]}
                onPress={() => onSendRetry && onSendRetry(message)}
              >
                <Ionicons name="refresh" size={16} color={colors.primary} />
              </TouchableOpacity>
            )}
            {message.role === 'assistant' && (
              <>
                {!isInstantChatMessage && !(isPlayingPodcast || isPausedPodcast) && (
                  <TouchableOpacity
                    style={[
                      styles.actionButton,
                      styles.listenPodcastButton,
                      highlightedActionStyle,
                      podcastReady && styles.listenPodcastButtonReady,
                      isPremiumChatMessage && !isLoadingPodcast && styles.listenPodcastButtonLabeled,
                    ]}
                    onPress={onPodcastButtonPress}
                    disabled={isLoadingPodcast}
                    accessibilityRole="button"
                    accessibilityLabel={
                      podcastReady
                        ? t('chat.podcastReadyToast', 'Podcast ready — tap to listen')
                        : isPremiumChatMessage
                          ? t('chat.podcastIncludedA11y', 'Free podcast included — tap to listen')
                          : t('chat.listenPodcast', 'Listen as podcast')
                    }
                  >
                    {isLoadingPodcast ? (
                      <ActivityIndicator size="small" color={colors.primary} />
                    ) : (
                      <View style={styles.podcastButtonInner}>
                        <View style={styles.podcastReadyIconWrap}>
                          <Ionicons
                            name={podcastReady ? 'radio' : 'radio-outline'}
                            size={17}
                            color={podcastReady ? '#15803d' : colors.primary}
                          />
                          {podcastReady ? <View style={styles.podcastReadyDot} /> : null}
                        </View>
                        {isPremiumChatMessage && !podcastReady ? (
                          <Text style={[styles.podcastFreeLabel, { color: colors.primary }]}>
                            {t('chat.podcastFreeBadge', 'Free')}
                          </Text>
                        ) : null}
                      </View>
                    )}
                  </TouchableOpacity>
                )}
                {!isInstantChatMessage && (isPlayingPodcast || isPausedPodcast) && (
                  <>
                    {isPlayingPodcast && (
                      <TouchableOpacity
                        style={[styles.actionButton, messageActionStyle]}
                        onPress={handlePausePodcast}
                      >
                        <Ionicons name="pause" size={16} color={colors.primary} />
                      </TouchableOpacity>
                    )}
                    {isPausedPodcast && (
                      <TouchableOpacity
                        style={[styles.actionButton, messageActionStyle]}
                        onPress={onPodcastButtonPress}
                      >
                        <Ionicons name="play" size={16} color={messageActionIcon} />
                      </TouchableOpacity>
                    )}
                    <TouchableOpacity
                      style={[styles.actionButton, messageActionStyle]}
                      onPress={handleStopPodcast}
                    >
                      <Ionicons name="stop-circle" size={16} color={messageActionIcon} />
                    </TouchableOpacity>
                  </>
                )}
                {!isInstantChatMessage && (
                  <TouchableOpacity
                    style={[styles.actionButton, messageActionStyle]}
                    onPress={sharePodcastAudio}
                    disabled={isSharingPodcast || isLoadingPodcast}
                  >
                    {isSharingPodcast ? (
                      <ActivityIndicator size="small" color={messageActionIcon} />
                    ) : (
                      <Ionicons name="share-outline" size={16} color={messageActionIcon} />
                    )}
                  </TouchableOpacity>
                )}
              </>
            )}
            <TouchableOpacity
              style={[styles.actionButton, messageActionStyle]}
              onPress={copyToClipboard}
            >
              <Ionicons name="copy-outline" size={16} color={messageActionIcon} />
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionButton, messageActionStyle]}
              onPress={shareMessage}
            >
              <Ionicons name="share-social-outline" size={16} color={messageActionIcon} />
            </TouchableOpacity>
            {message.role === 'assistant' && (
              <TouchableOpacity
                style={[styles.actionButton, styles.pdfButton, messageActionStyle]}
                onPress={sharePDF}
                disabled={isGeneratingPDF}
              >
                {isGeneratingPDF ? (
                  <ActivityIndicator size="small" color={colors.primary} />
                ) : (
                  <Ionicons name="document-text-outline" size={16} color={messageActionIcon} />
                )}
              </TouchableOpacity>
            )}
            <TouchableOpacity
              style={[styles.actionButton, styles.deleteButton, destructiveActionStyle]}
              onPress={() => {
                Alert.alert(
                  'Delete Message',
                  'Are you sure you want to delete this message?',
                  [
                    { text: 'Cancel', style: 'cancel' },
                    { text: 'Delete', style: 'destructive', onPress: deleteMessage }
                  ]
                );
              }}
            >
              <Ionicons name="trash-outline" size={16} color={colors.error} />
            </TouchableOpacity>
          </View>
        )}

        {!message.isTyping && message.role === 'user' && !!(message.content && message.content.trim()) && (
          <View style={[styles.actionButtons, { borderTopColor: colors.cardBorder }]}>
            <TouchableOpacity
              style={[styles.actionButton, messageActionStyle]}
              onPress={copyToClipboard}
            >
              <Ionicons name="copy-outline" size={16} color={messageActionIcon} />
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionButton, messageActionStyle]}
              onPress={shareMessage}
            >
              <Ionicons name="share-social-outline" size={16} color={messageActionIcon} />
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionButton, styles.deleteButton, destructiveActionStyle]}
              onPress={() => {
                Alert.alert(
                  'Delete Message',
                  'Are you sure you want to delete this message?',
                  [
                    { text: 'Cancel', style: 'cancel' },
                    { text: 'Delete', style: 'destructive', onPress: deleteMessage }
                  ]
                );
              }}
            >
              <Ionicons name="trash-outline" size={16} color={colors.error} />
            </TouchableOpacity>
          </View>
        )}

        {message.role === 'assistant' && (
          <Text style={[styles.timestamp, { color: colors.textTertiary }]}>
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </Text>
        )}
      </BubbleWrapper>

      {/* Tooltip Modal */}
      <Modal
        visible={tooltipModal.show}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setTooltipModal({ show: false, term: '', definition: '' })}
      >
        <TouchableOpacity
          style={[styles.tooltipModalOverlay, { backgroundColor: colors.overlay }]}
          activeOpacity={1}
          onPress={() => setTooltipModal({ show: false, term: '', definition: '' })}
        >
          <Animated.View
            style={[
              styles.tooltipModalContent,
              {
                backgroundColor: colors.surface,
                borderColor: colors.cardBorder,
                shadowColor: colors.primary,
              },
            ]}
          >
            <LinearGradient
              colors={[colors.surfaceRaised, colors.surface]}
              style={styles.tooltipGradient}
            >
              <View style={styles.tooltipHeader}>
                <View style={[styles.tooltipIconCircle, { backgroundColor: colors.accentSoft, borderColor: colors.cardBorder }]}>
                  <Ionicons name="book-outline" size={19} color={colors.onAccent} />
                </View>
                <View style={styles.tooltipHeadingCopy}>
                  <Text style={[styles.tooltipEyebrow, { color: colors.primary }]}>{t('premiumUi.chat.vedicGlossary')}</Text>
                  <Text style={[styles.tooltipModalTitle, { color: colors.text }]}>{formatGlossaryTitle(tooltipModal.term)}</Text>
                </View>
                <TouchableOpacity
                  style={[styles.tooltipHeaderClose, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}
                  onPress={() => setTooltipModal({ show: false, term: '', definition: '' })}
                  hitSlop={8}
                  accessibilityRole="button"
                  accessibilityLabel={t('premiumUi.chat.closeDefinition')}
                >
                  <Ionicons name="close" size={18} color={colors.textSecondary} />
                </TouchableOpacity>
              </View>

              <ScrollView style={styles.tooltipScrollView} showsVerticalScrollIndicator={false}>
                <Text style={[styles.tooltipModalDefinition, { color: colors.textSecondary }]}>{tooltipModal.definition}</Text>
              </ScrollView>

              <TouchableOpacity
                style={[styles.tooltipModalClose, { backgroundColor: colors.primary }]}
                onPress={() => setTooltipModal({ show: false, term: '', definition: '' })}
                activeOpacity={0.82}
              >
                <Text style={[styles.tooltipModalCloseText, { color: colors.onPrimary }]}>{t('premiumUi.chat.gotIt')}</Text>
                <Ionicons name="checkmark" size={17} color={colors.onPrimary} />
              </TouchableOpacity>
            </LinearGradient>
          </Animated.View>
        </TouchableOpacity>
      </Modal>

      {/* Image Modal */}
      <Modal
        visible={showImageModal}
        transparent={true}
        animationType="fade"
        onRequestClose={() => {
          setShowImageModal(false);
          setImageZoomScale(1);
        }}
      >
        <View style={styles.imageModalOverlay}>
          <View style={styles.imageModalToolbar}>
            <View style={styles.imageModalZoomRow}>
              <TouchableOpacity
                style={styles.imageZoomBtn}
                onPress={() => setImageZoomScale((s) => Math.max(1, Number((s / 1.25).toFixed(2))))}
              >
                <Text style={styles.imageZoomBtnText}>−</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.imageZoomBtn}
                onPress={() => setImageZoomScale(1)}
              >
                <Text style={styles.imageZoomBtnText}>{Math.round(imageZoomScale * 100)}%</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.imageZoomBtn}
                onPress={() => setImageZoomScale((s) => Math.min(5, Number((s * 1.25).toFixed(2))))}
              >
                <Text style={styles.imageZoomBtnText}>+</Text>
              </TouchableOpacity>
            </View>
            <TouchableOpacity
              style={styles.closeImageButton}
              onPress={() => {
                setShowImageModal(false);
                setImageZoomScale(1);
              }}
              hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
            >
              <Text style={styles.closeImageButtonText}>✕</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.imageModalHint}>
            {Platform.OS === 'ios' ? 'Pinch to zoom · drag to pan' : 'Use + / − to zoom'}
          </Text>
          <ScrollView
            style={styles.imageModalScroll}
            contentContainerStyle={styles.imageModalScrollContent}
            maximumZoomScale={5}
            minimumZoomScale={1}
            showsHorizontalScrollIndicator={false}
            showsVerticalScrollIndicator={false}
            centerContent
            bouncesZoom
            horizontal={imageZoomScale > 1}
          >
            {message.summary_image ? (
              <Image
                source={{ uri: message.summary_image }}
                style={[
                  styles.fullScreenImage,
                  { transform: [{ scale: imageZoomScale }] },
                ]}
                resizeMode="contain"
              />
            ) : null}
          </ScrollView>
        </View>
      </Modal>

      <ConfirmCreditsModal
        visible={showRevealCreditsModal}
        onClose={() => setShowRevealCreditsModal(false)}
        title={t('chat.revealDetailedAnswer', 'Reveal the detailed answer')}
        description={t(
          'chat.revealDetailedAnswerDesc',
          'Unlock Key Insights, Astrological Analysis, Timing & Guidance, and Final Verdict. Uses Standard mode credits.',
        )}
        cost={standardChatCost}
        credits={credits}
        confirmLabel={
          Number(credits) >= standardChatCost
            ? t('chat.unlockNow', 'Unlock now')
            : t('chat.getCredits', 'Get credits')
        }
        onConfirm={async () => {
          const mid = message.messageId || message.id;
          setShowRevealCreditsModal(false);
          if (mid) {
            try {
              await AsyncStorage.setItem(freeDetailRevealClickedStorageKey(mid), '1');
            } catch (_) {
              /* ignore */
            }
            creditAPI.recordFreeAnswerFunnelEvent('reveal_clicked', String(mid)).catch(() => {});
          }
          if (Number(credits) >= standardChatCost) {
            if (mid) {
              try {
                await AsyncStorage.setItem(freeDetailUnlockStorageKey(mid), '1');
              } catch (_) {
                /* ignore */
              }
            }
            setDetailUnlocked(true);
            return;
          }
          navigation.navigate('Credits');
        }}
      />

      <ConfirmCreditsModal
        visible={showPodcastCreditsModal}
        onClose={() => setShowPodcastCreditsModal(false)}
        onConfirm={confirmPodcastCredits}
        title={t('credits.podcastModal.title', 'Listen as Podcast')}
        description={t('credits.podcastModal.description', 'This will generate an audio podcast of this message. Credits will be deducted when the podcast is created.')}
        cost={podcastCost ?? 2}
        credits={credits ?? 0}
        confirmLabel={t('common.continue', 'Continue')}
      />

      <PodcastLanguageModal
        visible={showPodcastLanguageModal}
        selectedLang={podcastListenLang}
        included={isPremiumChatMessage}
        colors={colors}
        onSelect={continuePodcastAfterLanguage}
        onClose={() => {
          skipPodcastCreditsRef.current = false;
          setShowPodcastLanguageModal(false);
        }}
      />

      <AppAlertModal
        visible={copyAlert.visible}
        variant={copyAlert.error ? 'error' : 'success'}
        icon={copyAlert.error ? 'alert-circle-outline' : 'copy-outline'}
        title={t(copyAlert.error ? 'copyAlert.failedTitle' : 'copyAlert.successTitle')}
        message={t(copyAlert.error ? 'copyAlert.failedBody' : 'copyAlert.successBody')}
        onPrimaryPress={() => setCopyAlert({ visible: false, error: false })}
        onRequestClose={() => setCopyAlert({ visible: false, error: false })}
      />

      <PodcastPlayerModal
        visible={showPodcastPlayerModal}
        onClose={handlePodcastPlayerClose}
        mode={podcastPlayerMode}
        positionMillis={podcastPositionMillis}
        durationMillis={podcastDurationMillis}
        onSeek={handlePodcastSeek}
        onPause={handlePausePodcast}
        onResume={handleResumePodcast}
        onStop={handleStopPodcast}
        onShare={sharePodcastAudio}
        playbackRate={podcastPlaybackRate}
        onSpeedChange={(rate) => {
          setPodcastPlaybackRate(rate);
          getTextToSpeech().setPodcastRate(rate);
        }}
      />
    </Animated.View>
    </>
  );
}

const areMessageBubblePropsEqual = (prevProps, nextProps) => {
  // Skip heavy bubble rerenders when unrelated parent state changes (e.g., input typing).
  // Message object identity changes whenever that row actually updates.
  if (prevProps.message !== nextProps.message) return false;
  if (prevProps.language !== nextProps.language) return false;
  if (prevProps.partnership !== nextProps.partnership) return false;
  if (prevProps.sessionId !== nextProps.sessionId) return false;
  if (prevProps.podcastAutoLaunchMessageId !== nextProps.podcastAutoLaunchMessageId) return false;
  if (prevProps.podcastAutoLaunchKey !== nextProps.podcastAutoLaunchKey) return false;
  if (prevProps.podcastAutoLaunchLang !== nextProps.podcastAutoLaunchLang) return false;
  if (prevProps.forceInstantPresentation !== nextProps.forceInstantPresentation) return false;
  if (prevProps.onStartPartnershipGate !== nextProps.onStartPartnershipGate) return false;
  if (prevProps.onContinueSingleChartGate !== nextProps.onContinueSingleChartGate) return false;
  if (prevProps.onRelationshipContextGate !== nextProps.onRelationshipContextGate) return false;
  return true;
};

export default React.memo(MessageBubble, areMessageBubblePropsEqual);

  const styles = StyleSheet.create({
  instantMessageRow: {
    width: '100%',
    paddingHorizontal: 12,
    marginVertical: 5,
  },
  instantMessageRowUser: {
    alignItems: 'flex-end',
  },
  instantMessageRowAssistant: {
    alignItems: 'flex-start',
  },
  instantMessageBubble: {
    maxWidth: '82%',
    minWidth: 72,
    paddingHorizontal: 14,
    paddingVertical: 11,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 18,
  },
  instantMessageBubbleUser: {
    borderBottomRightRadius: 5,
  },
  instantMessageBubbleAssistant: {
    borderBottomLeftRadius: 5,
  },
  instantMessageText: {
    fontSize: 16,
    lineHeight: 23,
    fontWeight: '400',
  },
  instantMessageTime: {
    marginTop: 5,
    alignSelf: 'flex-end',
    fontSize: 12,
    lineHeight: 16,
  },
  instantInlineTyping: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 7,
  },
  instantInlineTypingDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
  },
  instantEvidenceToggle: {
    marginTop: 8,
    minHeight: 44,
    paddingHorizontal: 9,
    paddingVertical: 7,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 999,
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 5,
  },
  instantEvidenceToggleText: {
    fontSize: 13,
    lineHeight: 17,
    fontWeight: '800',
  },
  instantEvidenceModalBackdrop: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(17, 12, 20, 0.58)',
    paddingTop: Platform.select({ ios: 54, android: 28, default: 28 }),
  },
  instantEvidenceModalCard: {
    flex: 1,
    width: '100%',
    maxHeight: '94%',
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    borderWidth: StyleSheet.hairlineWidth,
    overflow: 'hidden',
  },
  instantEvidenceModalHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    paddingHorizontal: 18,
    paddingVertical: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  instantEvidenceModalClose: {
    width: 38,
    height: 38,
    borderRadius: 19,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
    justifyContent: 'center',
  },
  instantEvidenceModalScroll: {
    flex: 1,
  },
  instantEvidenceModalContent: {
    paddingHorizontal: 18,
    paddingBottom: 32,
  },
  instantEvidenceHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 8,
  },
  instantEvidenceHeaderCopy: { flex: 1, gap: 2 },
  instantEvidenceEyebrow: { fontSize: 9, lineHeight: 12, fontWeight: '900', letterSpacing: 1.2 },
  instantEvidenceTitle: { fontSize: 13, lineHeight: 17, fontWeight: '800', textTransform: 'capitalize' },
  instantEvidenceStatus: { paddingHorizontal: 7, paddingVertical: 4, borderRadius: 999 },
  instantEvidenceStatusText: { fontSize: 9, lineHeight: 11, fontWeight: '800' },
  instantEvidenceVerdict: { marginTop: 9, paddingVertical: 8, borderTopWidth: StyleSheet.hairlineWidth, borderBottomWidth: StyleSheet.hairlineWidth },
  instantEvidenceLabel: { marginTop: 8, marginBottom: 4, fontSize: 9, lineHeight: 12, fontWeight: '900', letterSpacing: 1 },
  instantEvidenceValue: { fontSize: 13, lineHeight: 17, fontWeight: '800' },
  instantEvidenceMeta: { marginTop: 2, fontSize: 10, lineHeight: 14 },
  instantEvidenceRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, paddingVertical: 6, borderBottomWidth: StyleSheet.hairlineWidth },
  instantEvidenceRowName: { flex: 1, fontSize: 10, lineHeight: 14, fontWeight: '600' },
  instantEvidenceRowStatus: { fontSize: 9, lineHeight: 12, fontWeight: '800' },
  instantEvidenceSectionLabel: { marginTop: 12 },
  instantEvidenceSection: { marginTop: 8 },
  instantEvidenceSectionTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 7, marginBottom: 3 },
  instantEvidenceSectionTitle: { flex: 1, marginTop: 0, marginBottom: 0 },
  instantEvidenceGroup: { marginTop: 8, marginLeft: 22, padding: 10, borderWidth: 1, borderRadius: 12, gap: 6 },
  instantEvidenceGroupTitle: { fontSize: 11, fontWeight: '800', letterSpacing: 0.7, textTransform: 'uppercase' },
  instantEvidenceFactor: { paddingTop: 7, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: 'rgba(128,128,128,0.24)', gap: 2 },
  instantEvidenceFactorTitle: { fontSize: 12, fontWeight: '700' },
  instantEvidenceStepBadge: { width: 20, height: 20, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  instantEvidenceStepText: { fontSize: 10, lineHeight: 12, fontWeight: '900' },
  instantEvidenceBulletRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 7, paddingVertical: 2 },
  instantEvidenceBulletDot: { width: 5, height: 5, borderRadius: 3, marginTop: 6 },
  instantEvidenceBulletText: { flex: 1, fontSize: 12, lineHeight: 17, fontWeight: '600' },
  instantEvidenceRecord: { marginTop: 6, padding: 8, borderWidth: StyleSheet.hairlineWidth, borderRadius: 9 },
  instantEvidenceRecordTop: { flexDirection: 'row', justifyContent: 'space-between', gap: 6 },
  instantEvidenceId: { fontSize: 9, lineHeight: 12, fontWeight: '900' },
  instantEvidenceConfidence: { fontSize: 9, lineHeight: 12, fontWeight: '700' },
  instantEvidenceRecordKind: { marginTop: 3, fontSize: 11, lineHeight: 14, fontWeight: '800' },
  instantEvidenceRecordSource: { fontSize: 9, lineHeight: 12 },
  instantEvidenceJson: { marginTop: 5, fontSize: 8, lineHeight: 11, fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }) },
  container: {
    marginVertical: 4,
  },
  userContainer: {
    alignItems: 'flex-end',
  },
  assistantContainer: {
    alignItems: 'flex-start',
  },
  bubble: {
    maxWidth: '98%',
    width: '98%',
    borderRadius: 20,
    padding: 16,
    marginVertical: 6,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 6,
    elevation: 4,
  },
  userBubble: {
    borderBottomRightRadius: 4,
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.15)',
    shadowColor: '#3b82f6',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  assistantBubble: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderBottomLeftRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.1)',
    borderLeftWidth: 3,
    borderLeftColor: 'rgba(255, 107, 53, 0.4)',
  },
  assistantHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
    gap: 8,
  },
  userHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
    flexWrap: 'wrap',
  },
  userBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    shadowColor: '#3b82f6',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  userIcon: {
    marginRight: 4,
  },
  userLabel: {
    fontSize: 9,
    fontWeight: '800',
    color: '#fff',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  chartNameBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
    gap: 4,
    maxWidth: 140,
  },
  chartNameBadgeText: {
    fontSize: 10,
    fontWeight: '600',
  },
  imageContainer: {
    marginBottom: 15,
    alignItems: 'center',
    width: '100%',
    height: 250,
    borderRadius: 12,
    overflow: 'hidden',
  },
  summaryImage: {
    width: '100%',
    maxWidth: 400,
    height: 250,
    borderRadius: 12,
  },
  imageExpandHint: {
    position: 'absolute',
    right: 10,
    bottom: 10,
    backgroundColor: 'rgba(20, 24, 30, 0.72)',
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 999,
    overflow: 'hidden',
  },
  skeletonWrapper: {
    width: '100%',
    height: '100%',
    backgroundColor: 'rgba(255, 107, 53, 0.05)',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  skeletonGradient: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255, 107, 53, 0.15)',
  },
  skeletonContent: {
    alignItems: 'center',
    gap: 8,
  },
  skeletonText: {
    fontSize: 12,
    color: 'rgba(255, 107, 53, 0.4)',
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  tapToEnlarge: {
    fontSize: 11,
    color: '#666',
    marginTop: 4,
  },
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 4,
    elevation: 3,
  },
  verifiedIcon: {
    marginRight: 4,
  },
  assistantLabel: {
    fontSize: 10,
    fontWeight: '800',
    color: '#fff',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  typingIndicatorBadge: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
    borderWidth: 0.5,
    borderColor: 'rgba(255, 107, 53, 0.3)',
  },
  typingIndicatorText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#ff6b35',
    textTransform: 'uppercase',
  },
  messageContent: {
    paddingBottom: 8,
  },
  regularText: {
    fontSize: 15,
    lineHeight: 22,
    marginVertical: 2,
    flexShrink: 1,
  },
  userText: {
    fontWeight: '500',
  },
  boldText: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '700',
    flexShrink: 1,
  },
  sentimentPositive: {
    color: '#15803d',
    fontWeight: '700',
  },
  sentimentNegative: {
    color: '#b91c1c',
    fontWeight: '700',
  },
  headerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 12,
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: Platform.OS === 'android' ? 'rgba(255, 107, 53, 0.1)' : 'rgba(255, 107, 53, 0.06)',
    borderRadius: 25,
    alignSelf: 'flex-start',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'rgba(255, 107, 53, 0.3)',
  },
  headerIcon: {
    fontSize: 18,
    marginRight: 10,
  },
  headerText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#ff6b35',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  subHeaderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: Platform.OS === 'android' ? 'rgba(255, 107, 53, 0.05)' : 'rgba(255, 107, 53, 0.03)',
    borderRadius: 12,
    borderLeftWidth: 3,
    borderLeftColor: 'rgba(255, 107, 53, 0.5)',
  },
  subHeaderIcon: {
    fontSize: 16,
    marginRight: 10,
  },
  subHeaderText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#ff6b35',
    letterSpacing: 0.2,
    flex: 1,
  },
  listItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginVertical: 6,
  },
  numberCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
    marginTop: 2,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
    elevation: 3,
  },
  numberText: {
    fontSize: 11,
    fontWeight: '800',
  },
  bulletContainer: {
    width: 20,
    alignItems: 'center',
    justifyContent: 'flex-start',
    paddingTop: 8,
    marginRight: 8,
  },
  bulletDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 3,
    elevation: 2,
  },
  bullet: {
    color: '#ff6b35',
    fontSize: 20,
    marginRight: 8,
  },
  listContent: {
    flex: 1,
    marginLeft: -2,
  },
  listText: {
    fontSize: 15,
    lineHeight: 22,
    flexShrink: 1,
  },
  quickAnswerWrapper: {
    marginVertical: 12,
    width: '100%',
  },
  quickAnswerCard: {
    borderRadius: 24,
    padding: 20,
    borderWidth: StyleSheet.hairlineWidth * 2,
    borderColor: 'rgba(255, 107, 53, 0.2)',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.15,
    shadowRadius: 15,
    elevation: 5,
    overflow: 'hidden',
    position: 'relative',
  },
  cardGlow: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 100,
  },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.2)',
  },
  titleUnderline: {
    height: 2,
    width: 40,
    backgroundColor: '#ff6b35',
    marginTop: 2,
    borderRadius: 1,
    opacity: 0.4,
  },
  sparkleIcon: {
    position: 'absolute',
    bottom: 10,
    right: 15,
    fontSize: 16,
    opacity: 0.6,
    color: '#ff6b35',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    zIndex: 1,
  },
  lightningIcon: {
    fontSize: 18,
    marginRight: 8,
    color: '#FFD700',
  },
  finalThoughtsWrapper: {
    marginVertical: 12,
    width: '100%',
  },
  finalThoughtsCard: {
    borderRadius: 24,
    padding: 20,
    borderWidth: StyleSheet.hairlineWidth * 2,
    borderColor: 'rgba(65, 105, 225, 0.2)',
    shadowColor: '#4169E1',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.15,
    shadowRadius: 15,
    elevation: 5,
    overflow: 'hidden',
    position: 'relative',
  },
  thoughtIcon: {
    fontSize: 18,
    color: '#4169E1',
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: Platform.OS === 'android' ? '#ff6b35' : '#2c3e50',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  cardText: {
    fontSize: 15,
    lineHeight: 22,
    zIndex: 1,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-start',
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(80, 54, 64, 0.14)',
    gap: 6,
    flexWrap: 'wrap',
  },
  actionButton: {
    backgroundColor: 'rgba(120, 96, 104, 0.08)',
    borderRadius: 16,
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
  },
  // Podcast action button styling (no badge; just a subtle orange highlight).
  listenPodcastButton: {
    backgroundColor: 'rgba(255, 107, 53, 0.12)',
    borderColor: 'rgba(255, 107, 53, 0.25)',
    // Android: elevation from actionButton reads as a heavy outline; use flat fill + border only.
    ...(Platform.OS === 'android'
      ? {
          elevation: 0,
          shadowColor: 'transparent',
          shadowOffset: { width: 0, height: 0 },
          shadowOpacity: 0,
          shadowRadius: 0,
          borderWidth: 1.5,
          borderColor: 'rgba(255, 107, 53, 0.35)',
        }
      : {}),
  },
  listenPodcastButtonReady: {
    backgroundColor: 'rgba(22, 163, 74, 0.12)',
    borderColor: 'rgba(22, 163, 74, 0.38)',
  },
  listenPodcastButtonLabeled: {
    width: 'auto',
    minWidth: 32,
    paddingHorizontal: 8,
  },
  podcastButtonInner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  podcastFreeLabel: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.3,
  },
  podcastReadyIconWrap: {
    width: 17,
    height: 17,
    justifyContent: 'center',
    alignItems: 'center',
  },
  podcastReadyDot: {
    position: 'absolute',
    top: -2,
    right: -3,
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: '#16a34a',
    borderWidth: 1,
    borderColor: '#fff',
  },
  pdfButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderColor: 'rgba(59, 130, 246, 0.2)',
  },
  deleteButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderColor: 'rgba(239, 68, 68, 0.2)',
  },
  actionIcon: {
    fontSize: 16,
    color: COLORS.accent,
  },
  timestamp: {
    fontSize: 11,
    color: 'rgba(44, 62, 80, 0.6)',
    textAlign: 'right',
    marginTop: 6,
    fontWeight: '500',
  },
  followUpContainer: {
    flexDirection: 'column',
    alignSelf: 'stretch',
    width: '100%',
    maxWidth: '100%',
    marginTop: 14,
    marginBottom: 6,
    gap: 8,
  },
  followUpEyebrow: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.7,
    marginBottom: 2,
  },
  remedyCard: {
    borderRadius: 24,
    borderWidth: 1,
    padding: 18,
    marginTop: 14,
    marginBottom: 6,
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: Platform.OS === 'android' ? 0 : 0.24,
    shadowRadius: 22,
    elevation: Platform.OS === 'android' ? 3 : 0,
  },
  remedyCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 14,
  },
  remedySeal: {
    width: 34,
    height: 34,
    borderRadius: 17,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  remedyEyebrow: {
    flex: 1,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.5,
  },
  remedyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(22, 163, 74, 0.14)',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 5,
    gap: 6,
  },
  remedyBadgeText: {
    color: '#15803d',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
  remedyCardTitle: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 21,
    lineHeight: 26,
    fontWeight: '700',
    marginBottom: 8,
  },
  remedyCardReason: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 16,
    fontWeight: '500',
  },
  remedyCardButton: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 11,
  },
  remedyCardButtonText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 13,
  },
  followUpButton: {
    alignSelf: 'stretch',
    width: '100%',
    maxWidth: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    borderRadius: 18,
    paddingLeft: 13,
    paddingRight: 10,
    paddingVertical: 12,
    borderWidth: 1,
  },
  followUpIndex: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  followUpText: {
    fontSize: 13,
    fontWeight: '700',
    lineHeight: 19,
    flex: 1,
    flexShrink: 1,
    flexWrap: 'wrap',
  },
  followUpArrow: {
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  typingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  typingText: {
    fontSize: 15,
    color: '#2c3e50',
    marginRight: 8,
  },
  typingDots: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#ff6b35',
    marginHorizontal: 2,
  },
  typingBubble: {
    maxWidth: '88%',
  },
  partnershipBubble: {
    borderLeftWidth: 3,
    borderLeftColor: COLORS.partnershipBorder,
  },
  partnershipLabel: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: COLORS.partnershipBorder,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    zIndex: 10,
  },
  partnershipLabelText: {
    color: COLORS.white,
    fontSize: 10,
    fontWeight: '600',
  },
  clarificationBubble: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderLeftWidth: 3,
    borderLeftColor: '#FFA726',
    borderWidth: 1,
    borderColor: 'rgba(255, 167, 38, 0.3)',
    shadowColor: '#FFA726',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 5,
  },
  tooltipTerm: {
    backgroundColor: 'rgba(233, 30, 99, 0.15)',
    borderRadius: 4,
    paddingHorizontal: 4,
    borderWidth: 1,
    borderColor: 'rgba(233, 30, 99, 0.3)',
  },
  tooltipText: {
    fontWeight: '700',
    borderRadius: 7,
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderWidth: 1,
    overflow: 'hidden',
  },
  tooltipModalOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  tooltipModalContent: {
    width: '92%',
    maxWidth: 420,
    borderRadius: 28,
    borderWidth: 1,
    overflow: 'hidden',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.24,
    shadowRadius: 28,
    elevation: 10,
  },
  tooltipGradient: {
    padding: 22,
    borderRadius: 28,
  },
  tooltipHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 18,
    gap: 12,
  },
  tooltipIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
  },
  tooltipHeadingCopy: {
    flex: 1,
  },
  tooltipEyebrow: {
    fontSize: 9,
    lineHeight: 12,
    fontWeight: '800',
    letterSpacing: 1.5,
    marginBottom: 2,
  },
  tooltipHeaderClose: {
    width: 34,
    height: 34,
    borderRadius: 17,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tooltipModalTitle: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 22,
    lineHeight: 27,
    fontWeight: '600',
  },
  tooltipScrollView: {
    maxHeight: 300,
    marginBottom: 22,
  },
  tooltipModalDefinition: {
    fontSize: 15,
    lineHeight: 23,
    fontWeight: '500',
  },
  tooltipModalClose: {
    minHeight: 46,
    paddingHorizontal: 22,
    borderRadius: 999,
    alignSelf: 'stretch',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 7,
  },
  tooltipModalCloseText: {
    fontSize: 14,
    fontWeight: '800',
  },
  tableScroll: {
    marginVertical: 12,
  },
  tableScrollContent: {
    paddingRight: 16,
  },
  tableContainer: {
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: Platform.OS === 'android' ? 0 : 0.1,
    shadowRadius: 8,
    elevation: Platform.OS === 'android' ? 1 : 0,
  },
  tableHeaderRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
  },
  tableHeaderCellWrap: {
    paddingHorizontal: 6,
    justifyContent: 'center',
  },
  tableHeaderCell: {
    fontSize: 12,
    fontWeight: '800',
    textAlign: 'center',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    paddingHorizontal: 4,
    flexShrink: 0,
  },
  tableRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 0, 0, 0.03)',
    paddingVertical: 10,
    paddingHorizontal: 8,
    alignItems: 'center',
  },
  tableCellWrap: {
    paddingHorizontal: 6,
    justifyContent: 'center',
  },
  tableCell: {
    fontSize: 13,
    color: '#2c3e50',
    textAlign: 'center',
    fontWeight: '500',
    paddingHorizontal: 4,
    flexShrink: 0,
  },
  betaNotice: {
    backgroundColor: 'rgba(255, 152, 0, 0.1)',
    borderLeftWidth: 3,
    borderLeftColor: '#FF9800',
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
  },
  betaNoticeText: {
    fontSize: 12,
    color: '#E65100',
    fontWeight: '600',
    lineHeight: 16,
  },
  disclaimerNotice: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 6,
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingTop: 10,
    marginTop: 10,
  },
  disclaimerNoticeText: {
    flex: 1,
    fontSize: 9,
    fontWeight: '500',
    lineHeight: 13,
  },
  timeoutHint: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    borderLeftWidth: 3,
    borderLeftColor: '#ff6b35',
    borderRadius: 8,
    padding: 10,
    marginTop: 8,
    marginBottom: 8,
  },
  timeoutHintText: {
    fontSize: 12,
    color: '#7c2d12',
    fontWeight: '600',
    lineHeight: 18,
  },
  startNewChatLink: {
    marginTop: 10,
    alignSelf: 'flex-start',
  },
  startNewChatLinkText: {
    fontSize: 13,
    color: '#c2410c',
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
  imageModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.95)',
  },
  imageModalToolbar: {
    paddingTop: Platform.OS === 'ios' ? 54 : 28,
    paddingHorizontal: 16,
    paddingBottom: 4,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    zIndex: 2,
  },
  imageModalZoomRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  imageZoomBtn: {
    minWidth: 44,
    height: 36,
    paddingHorizontal: 12,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.16)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  imageZoomBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  imageModalHint: {
    color: 'rgba(255,255,255,0.65)',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 6,
  },
  imageModalScroll: {
    flex: 1,
  },
  imageModalScrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: Dimensions.get('window').height * 0.75,
  },
  fullScreenImage: {
    width: Dimensions.get('window').width,
    height: Dimensions.get('window').height * 0.75,
  },
  closeImageButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.18)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeImageButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
  },
  imageModalCloseButton: {
    position: 'absolute',
    top: 50,
    right: 20,
    zIndex: 10,
  },
  imageModalImage: {
    width: Dimensions.get('window').width,
    height: Dimensions.get('window').height * 0.8,
  },
  nativeGateActionsWrap: {
    marginTop: 12,
    marginBottom: 4,
    alignSelf: 'stretch',
  },
  nativeGateActionsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    columnGap: 12,
    rowGap: 8,
  },
  nativeGateLinkText: {
    fontSize: 14,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
  nativeGateSelectCta: {
    backgroundColor: '#7c2d12',
    borderWidth: 1,
    borderColor: '#7c2d12',
    borderRadius: 999,
    paddingVertical: 8,
    paddingHorizontal: 14,
    shadowColor: '#7c2d12',
    shadowOpacity: 0.2,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  nativeGateSelectCtaText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '800',
  },
  nativeGateCtaOuter: {
    borderRadius: 999,
    overflow: 'hidden',
    alignSelf: 'flex-start',
    maxWidth: '100%',
  },
  nativeGateCtaGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 9,
    paddingHorizontal: 14,
  },
  nativeGateCtaText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  nativeGateOptionsWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: 8,
  },
  nativeGateOptionChip: {
    backgroundColor: Platform.OS === 'android' ? 'rgba(255, 107, 53, 0.18)' : 'rgba(255, 107, 53, 0.12)',
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.35)',
  },
  nativeGateOptionText: {
    color: '#ea580c',
    fontSize: 13,
    fontWeight: '700',
  },
  nativeGateSecondaryCta: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 999,
    paddingVertical: 9,
    paddingHorizontal: 14,
    borderWidth: 1,
  },
  nativeGateSecondaryCtaText: {
    fontSize: 14,
    fontWeight: '700',
  },
  nativeGatePlainCta: {
    borderRadius: 999,
    paddingVertical: 9,
    paddingHorizontal: 14,
    borderWidth: 1,
  },
  nativeGatePlainCtaText: {
    fontSize: 13,
    fontWeight: '700',
  },
  nativeGateHelperText: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  freeDetailPaywall: {
    marginTop: 12,
    marginBottom: 4,
  },
  freeDetailBlurBlock: {
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: 'rgba(255, 247, 237, 0.9)',
    borderWidth: 1,
    borderColor: 'rgba(234, 88, 12, 0.18)',
    minHeight: 96,
    justifyContent: 'center',
    padding: 14,
    marginBottom: 10,
  },
  freeDetailTeaser: {
    fontSize: 13,
    lineHeight: 19,
    color: '#78716c',
  },
  freeDetailBlurOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255, 255, 255, 0.55)',
  },
  freeDetailRevealBtn: {
    borderRadius: 999,
    overflow: 'hidden',
    alignSelf: 'stretch',
  },
  freeDetailRevealGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 11,
    paddingHorizontal: 16,
  },
  freeDetailRevealText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '800',
  },
  freeDetailHint: {
    marginTop: 6,
    textAlign: 'center',
    fontSize: 12,
    color: '#a8a29e',
    fontWeight: '600',
  },
});
