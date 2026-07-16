import React, { useEffect, useRef, useState } from 'react';
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
import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';
import { stopAnimatedValue, stopAnimationLoop } from '../../utils/safeAnimated';
import { generatePDF, sharePDFOnWhatsApp, getLogoDataUriForModule } from '../../utils/pdfGenerator';
import { getTextToSpeech } from '../../utils/textToSpeechLazy';
import { chatAPI } from '../../services/api';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { useCredits } from '../../credits/CreditContext';
import { useAuthGate } from '../../auth/AuthGateContext';
import ConfirmCreditsModal from '../ConfirmCreditsModal';
import PodcastPlayerModal from '../PodcastPlayerModal';

/** Avoid replaying slide-in when a tall bubble remounts (Android clipping / recycle). */
const messageBubbleEntryPlayedIds = new Set();

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
}) {
  const { t } = useTranslation();
  const { theme } = useTheme();
  const { podcastCost, credits } = useCredits();
  const { requireAuthForPaid } = useAuthGate();
  const navigation = useNavigation();
  // Init from the played-ids set so FlatList remounts do not flash translateY:50 for one frame
  // (that looked like the long answer bouncing between sections while reading).
  const entryIdForAnim = String(message?.messageId || message?.id || message?.clientRequestId || '');
  const entryAlreadyPlayed =
    Boolean(entryIdForAnim) && messageBubbleEntryPlayedIds.has(entryIdForAnim);
  const fadeAnim = useRef(new Animated.Value(entryAlreadyPlayed ? 1 : 0)).current;
  const slideAnim = useRef(new Animated.Value(entryAlreadyPlayed ? 0 : 50)).current;
  const isPartnership = partnership || message.partnership_mode;
  const messageChatTier = String(message?.chatTier || message?.chat_tier || '').trim().toLowerCase();
  const isInstantChatMessage = messageChatTier === 'instant';
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [tooltipModal, setTooltipModal] = useState({ show: false, term: '', definition: '' });
  const [isLoadingPodcast, setIsLoadingPodcast] = useState(false);
  const [isPlayingPodcast, setIsPlayingPodcast] = useState(false);
  const [isPausedPodcast, setIsPausedPodcast] = useState(false);
  const [isSharingPodcast, setIsSharingPodcast] = useState(false);
  const [showPodcastCreditsModal, setShowPodcastCreditsModal] = useState(false);
  const [showPodcastPlayerModal, setShowPodcastPlayerModal] = useState(false);
  const [podcastPlayerMode, setPodcastPlayerMode] = useState('generating');
  const [podcastPositionMillis, setPodcastPositionMillis] = useState(0);
  const [podcastDurationMillis, setPodcastDurationMillis] = useState(0);
  const [podcastPlaybackRate, setPodcastPlaybackRate] = useState(1);
  const [showImageModal, setShowImageModal] = useState(false);
  const [isImageLoading, setIsImageLoading] = useState(true);
  const skeletonAnim = useRef(new Animated.Value(0)).current;
  const skeletonLoopRef = useRef(null);
  const entryAnimRef = useRef(null);
  const typingAnimRef = useRef(null);
  const mountedRef = useRef(true);
  /** After seek, ignore progress updates briefly so we don't overwrite with stale position. */
  const lastSeekedAtRef = useRef(0);
  /** Set when user closes the modal while "Generating..." so we don't reopen or auto-play when the request completes. */
  const userDismissedGeneratingRef = useRef(false);
  useFocusEffect(
    React.useCallback(() => {
      mountedRef.current = true;
      return () => {
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
    if (!message.isTyping) {
      typingAnimRef.current?.stop?.();
      typingAnimRef.current = null;
      stopAnimatedValue(dot1Anim, 0.3);
      stopAnimatedValue(dot2Anim, 0.3);
      stopAnimatedValue(dot3Anim, 0.3);
      return undefined;
    }

    const animateLoader = () => {
      if (!mountedRef.current || !message.isTyping) return;
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
        if (finished && mountedRef.current && message.isTyping) {
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
  }, [message.isTyping, dot1Anim, dot2Anim, dot3Anim]);

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

  const playPodcast = async () => {
    if (isPlayingPodcast) {
      getTextToSpeech().stop();
      setIsPlayingPodcast(false);
      return;
    }
    if (isLoadingPodcast) return;

    const cleanText = getCleanMessageText();
    if (!cleanText) return;

    try {
      userDismissedGeneratingRef.current = false;
      setIsLoadingPodcast(true);
      setIsPlayingPodcast(false);
      await getTextToSpeech().playPodcast(cleanText, {
        language,
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
          }
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

  const onPodcastButtonPress = async () => {
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

    // Ask backend if podcast exists for this message. If cached, fetch and play (no charge). If not, show credit modal then generate.
    const messageId = message.messageId || null;
    if (messageId) {
      try {
        const res = await chatAPI.checkPodcastCache(messageId, language);
        if (res?.data?.cached === true) {
          playPodcast();
          return;
        }
      } catch (_) {
        // On error (e.g. network), show modal so user confirms before we attempt creation
      }
    }

    // No cached podcast: show credit confirmation modal; on confirm we call playPodcast() which generates and charges
    setShowPodcastCreditsModal(true);
  };

  const confirmPodcastCredits = async () => {
    const authOk = await requireAuthForPaid({
      feature: 'podcast',
      message: 'Sign in to generate a podcast from this answer.',
      resume: { resumeRoute: 'Home', resumeParams: {} },
    });
    if (!authOk) return;
    setShowPodcastCreditsModal(false);
    setPodcastPlayerMode('generating');
    setShowPodcastPlayerModal(true);
    setPodcastPositionMillis(0);
    setPodcastDurationMillis(0);
    playPodcast();
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
      const lang = language?.toLowerCase().startsWith('hi') ? 'hi' : 'en';
      const response = await chatAPI.getPodcastAudio(cleanText, lang, message.messageId || null, null, null, message.native_name || null);
      const base64Audio = response?.data?.audio;
      if (!base64Audio || typeof base64Audio !== 'string') {
        Alert.alert('Error', 'Could not get podcast audio to share.');
        return;
      }
      const filename = `AstroRoshni-Podcast-${Date.now()}.mp3`;
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
      Alert.alert('Error', `Failed to generate PDF: ${error.message}`);
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
      const cleanText = message.content
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/###\s*(.*?)$/gm, '$1')
        .replace(/<[^>]*>/g, '')
        .replace(/•\s*/g, '• ')
        .trim();

      const clipboard = require('expo-clipboard');
      if (clipboard?.setStringAsync) {
        await clipboard.setStringAsync(cleanText);
      }
      Alert.alert('Copied!', 'Message copied to clipboard');
    } catch (error) {
      // Error copying to clipboard
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
              colors={Platform.OS === 'android' 
                ? ['rgba(255, 255, 255, 0.98)', 'rgba(255, 248, 225, 0.95)'] 
                : ['rgba(255, 255, 255, 0.25)', 'rgba(255, 255, 255, 0.1)']}
              style={styles.quickAnswerCard}
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
                  <Text style={styles.cardTitle}>Quick Answer</Text>
                  <View style={styles.titleUnderline} />
                </View>
              </View>
              <View style={styles.cardText}>
                {renderTextWithBold(cardContent, quickKey * 1000, message.role, styles.cardText)}
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
              colors={Platform.OS === 'android'
                ? ['rgba(240, 249, 255, 0.98)', 'rgba(224, 242, 254, 0.95)']
                : ['rgba(230, 243, 255, 0.25)', 'rgba(176, 224, 230, 0.1)']}
              style={styles.finalThoughtsCard}
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
                  <Text style={[styles.cardTitle, { color: '#4169E1' }]}>Final Thoughts</Text>
                  <View style={[styles.titleUnderline, { backgroundColor: '#4169E1' }]} />
                </View>
              </View>
              <View style={styles.cardText}>
                {renderTextWithBold(cardContent, finalKey * 1000, message.role, styles.cardText)}
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
                <View style={[styles.tableContainer, { width: tableWidth }]}>
                  {/* Header */}
                  <View style={styles.tableHeaderRow}>
                    {headerRow.map((header, idx) => (
                      <View key={`th-${idx}`} style={[styles.tableHeaderCellWrap, { width: columnWidth }]}>
                        {renderTextWithBold(header, 2000 + idx, message.role, styles.tableHeaderCell)}
                      </View>
                    ))}
                  </View>
                  {/* Rows */}
                  {dataRows.map((row, rowIdx) => {
                    const cells = row.split('|').map(c => c.trim()).filter(c => c);
                    if (cells.length === 0) return null;
                    return (
                      <View key={`tr-${rowIdx}`} style={styles.tableRow}>
                        {cells.map((cell, cellIdx) => (
                          <View key={`td-${rowIdx}-${cellIdx}`} style={[styles.tableCellWrap, { width: columnWidth }]}>
                            {renderTextWithBold(cell, 2000 + rowIdx * 100 + cellIdx, message.role, styles.tableCell)}
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
            style={[styles.tooltipText, baseTextStyle]}
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
      ? [styles.regularText, baseTextStyle, message.role === 'user' && styles.userText]
      : [styles.regularText, message.role === 'user' && styles.userText];
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
            <Text style={styles.headerText}>{headerText}</Text>
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
            <Text style={styles.headerText}>{headerText}</Text>
          </View>
        );
      } else if (part.match(/^####\s+(.+)$/m)) {
        let headerText = part.split('\n')[0].replace(/^#+\s*/, '').trim();
        headerText = headerText.replace(/<tooltip[^>]*>([^<]+)<\/tooltip>/g, '$1');
        const symbol = getHeaderSymbol(headerText);
        elements.push(
          <View key={`subheader-${currentIndex++}`} style={styles.subHeaderContainer}>
            <Text style={styles.subHeaderIcon}>{symbol}</Text>
            <Text style={styles.subHeaderText}>{headerText}</Text>
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
                  <View style={styles.numberCircle}>
                    <Text style={styles.numberText}>{number}</Text>
                  </View>
                ) : (
                  <View style={styles.bulletContainer}>
                    <View style={styles.bulletDot} />
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

  // Promo CTA on ChatScreen: skip the credits modal; user already consented in PodcastPromoModal.
  useEffect(() => {
    if (isInstantChatMessage) return;
    if (!podcastAutoLaunchMessageId || !podcastAutoLaunchKey) return;
    const mid = message.messageId;
    if (!mid || String(mid) !== String(podcastAutoLaunchMessageId)) return;
    if (message.role !== 'assistant' || message.isTyping) return;
    if (isClarification || isNativeGate) return;
    const body = getCleanMessageText();
    if (!body || body.length < 80) return;

    const timer = setTimeout(() => {
      void (async () => {
        try {
          userDismissedGeneratingRef.current = false;
          const msgId = message.messageId || null;
          if (msgId) {
            try {
              const res = await chatAPI.checkPodcastCache(msgId, language);
              if (res?.data?.cached === true) {
                await playPodcast();
                return;
              }
            } catch (_) {
              // Network failure: still attempt generation (server enforces credits).
            }
          }
          setShowPodcastCreditsModal(false);
          setPodcastPlayerMode('generating');
          setShowPodcastPlayerModal(true);
          setPodcastPositionMillis(0);
          setPodcastDurationMillis(0);
          playPodcast();
        } catch (e) {
          console.error('[Podcast] auto-launch', e);
        }
      })();
    }, 400);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- playPodcast closes over latest message/session; avoid re-firing loops
  }, [
    isInstantChatMessage,
    podcastAutoLaunchKey,
    podcastAutoLaunchMessageId,
    message.messageId,
    message.role,
    message.isTyping,
    message.content,
    language,
    isClarification,
    isNativeGate,
  ]);

  // Loading rows use LoadingBubble (isTyping), not MessageBubble — skip empty assistant rows safely.
  if (!contentStr.trim()) {
    return null;
  }

  const formattedContent = formatContent(contentStr);
  const renderedElements = renderFormattedText(formattedContent);

  const chartName = message.native_name || null;

  const BubbleWrapper = ({ children, role, isPartnership, isClarification, timestamp }) => {
    if (role === 'user') {
      return (
        <LinearGradient
          colors={['#fffef5', '#fffae6']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={[
            styles.bubble,
            styles.userBubble,
            isPartnership && styles.partnershipBubble
          ]}
        >
          <View style={styles.userHeader}>
            <LinearGradient
              colors={['#3b82f6', '#60a5fa']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.userBadge}
            >
            <Ionicons name="person" size={10} color="#fff" style={styles.userIcon} />
            <Text style={styles.userLabel}>{t('chat.you', 'You')}</Text>
          </LinearGradient>
            {chartName ? (
              <View style={[styles.chartNameBadge, styles.chartNameBadgeUser]}>
                <Ionicons name="calendar-outline" size={10} color="#1e3a8a" />
                <Text style={styles.chartNameBadgeTextUser} numberOfLines={1}>{chartName}</Text>
              </View>
            ) : null}
          </View>
          {children}
          <Text style={[styles.timestamp, { color: 'rgba(30, 58, 138, 0.5)' }]}>
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
        isClarification && styles.clarificationBubble
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
              colors={['#ff6b35', '#ff8c5a']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.verifiedBadge}
            >
            <Ionicons name="checkmark-circle" size={12} color="#fff" style={styles.verifiedIcon} />
            <Text style={styles.assistantLabel}>
              {isClarification
                ? t('chat.inquiry', 'AstroRoshni Inquiry')
                : isNativeGate
                  ? t('chat.nativeGateBadge', 'Saved profile needed')
                  : t('chat.verified', 'AstroRoshni Verified')}
            </Text>
          </LinearGradient>
            {chartName ? (
              <View style={[styles.chartNameBadge, styles.chartNameBadgeAssistant]}>
                <Ionicons name="calendar-outline" size={10} color="#7c2d12" />
                <Text style={styles.chartNameBadgeTextAssistant} numberOfLines={1}>{chartName}</Text>
              </View>
            ) : null}
            {message.isTyping && (
              <View style={styles.typingIndicatorBadge}>
                <Text style={styles.typingIndicatorText}>{Platform.OS === 'ios' ? 'Reviewing chart...' : 'Analyzing Chart...'}</Text>
              </View>
            )}
          </View>
        )}
        
        {/* Beta Notice for timeline-based interpretations */}
        {message.role === 'assistant' && !isClarification && !isNativeGate && (
          <View style={styles.betaNotice}>
            <Text style={styles.betaNoticeText}>{Platform.OS === 'ios' ? '⚠️ BETA: Timeline studies are experimental. Use judgment and discretion.' : t('chat.betaNotice', '⚠️ BETA: Timeline interpretations are experimental. Use judgment and discretion.')}</Text>
          </View>
        )}
        
        {/* Legal Disclaimer */}
        {message.role === 'assistant' && !isClarification && !isNativeGate && (
          <View style={styles.disclaimerNotice}>
            <Text style={styles.disclaimerNoticeText}>
              {t('chat.disclaimerNotice', '⚖️ DISCLAIMER: Astrology is a probabilistic tool for guidance. Not a substitute for medical, legal, financial, or mental health advice. Consult qualified professionals for important decisions.')}
            </Text>
          </View>
        )}

        {/* Quick action buttons under disclaimer (for long messages) - show for assistant messages with content (incl. chat history) */}
        {!message.isTyping && message.role === 'assistant' && !message.isWelcome && !isNativeGate && (message.messageId || message.content) && (
          <View style={styles.actionButtons}>
            {message.showRestartButton && (
              <TouchableOpacity
                style={[styles.actionButton, styles.restartButton]}
                onPress={() => onRestart && onRestart(message.messageId)}
              >
                <Ionicons name="refresh" size={16} color="#ff6b35" />
              </TouchableOpacity>
            )}
            {message.showSendRetryButton && !message.messageId && (
              <TouchableOpacity
                style={[styles.actionButton, styles.restartButton]}
                onPress={() => onSendRetry && onSendRetry(message)}
              >
                <Ionicons name="refresh" size={16} color="#ff6b35" />
              </TouchableOpacity>
            )}
            <>
              {!(isPlayingPodcast || isPausedPodcast) && (
                <TouchableOpacity
                  style={[styles.actionButton, styles.listenPodcastButton]}
                  onPress={onPodcastButtonPress}
                  disabled={isLoadingPodcast}
                >
                  {isLoadingPodcast ? (
                    <ActivityIndicator size="small" color="#ff6b35" />
                  ) : (
                    <Ionicons name="radio-outline" size={17} color="#ff6b35" />
                  )}
                </TouchableOpacity>
              )}
              {(isPlayingPodcast || isPausedPodcast) && (
                <>
                  {isPlayingPodcast && (
                    <TouchableOpacity
                      style={styles.actionButton}
                      onPress={handlePausePodcast}
                    >
                      <Ionicons name="pause" size={16} color="#ff6b35" />
                    </TouchableOpacity>
                  )}
                  {isPausedPodcast && (
                    <TouchableOpacity
                      style={styles.actionButton}
                      onPress={onPodcastButtonPress}
                    >
                      <Ionicons name="play" size={16} color="#666" />
                    </TouchableOpacity>
                  )}
                  <TouchableOpacity
                    style={styles.actionButton}
                    onPress={handleStopPodcast}
                  >
                    <Ionicons name="stop-circle" size={16} color="#666" />
                  </TouchableOpacity>
                </>
              )}
              <TouchableOpacity
                style={styles.actionButton}
                onPress={sharePodcastAudio}
                disabled={isSharingPodcast || isLoadingPodcast}
              >
                {isSharingPodcast ? (
                  <ActivityIndicator size="small" color="#666" />
                ) : (
                  <Ionicons name="share-outline" size={16} color="#666" />
                )}
              </TouchableOpacity>
            </>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={copyToClipboard}
            >
              <Ionicons name="copy-outline" size={16} color="#666" />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={shareMessage}
            >
              <Ionicons name="share-social-outline" size={16} color="#666" />
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionButton, styles.pdfButton]}
              onPress={sharePDF}
              disabled={isGeneratingPDF}
            >
              {isGeneratingPDF ? (
                <ActivityIndicator size="small" color={COLORS.primary} />
              ) : (
                <Ionicons name="document-text-outline" size={16} color="#666" />
              )}
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionButton, styles.deleteButton]}
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
              <Ionicons name="trash-outline" size={16} color="#666" />
            </TouchableOpacity>
          </View>
        )}

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
                  <Text style={styles.skeletonText}>Preparing Chart...</Text>
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
              <Text style={styles.tapToEnlarge}>Tap to enlarge</Text>
            )}
          </TouchableOpacity>
        )}
        
        <View style={styles.messageContent}>
          {renderedElements}
        </View>

        {isNativeGate && !message.isTyping && (
          <View style={styles.nativeGateActionsWrap}>
            <Text style={styles.nativeGateHelperText}>
              {t(
                'chat.nativeGateTapInstruction',
                'Please tap one of the options below to continue.'
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
                {(isSubjectChartGate || isPartnershipOfferGate) && (
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
                {(isSubjectChartGate || isPartnershipOfferGate) && (
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
                        style={styles.nativeGateSecondaryCta}
                        onPress={() => onStartPartnershipGate && onStartPartnershipGate(gateMetadata)}
                        activeOpacity={0.85}
                        accessibilityRole="button"
                        accessibilityLabel={t('chat.startPartnershipA11y', 'Start partnership study')}
                      >
                        <Ionicons name="people-outline" size={16} color="#ea580c" style={{ marginRight: 6 }} />
                        <Text style={styles.nativeGateSecondaryCtaText}>
                        {t('chat.startPartnershipAnalysis', Platform.OS === 'ios' ? 'Start partnership study' : 'Start Partnership Analysis')}
                        </Text>
                      </TouchableOpacity>
                    )}
                    <TouchableOpacity
                      style={styles.nativeGatePlainCta}
                      onPress={() => onContinueSingleChartGate && onContinueSingleChartGate(gateMetadata)}
                      activeOpacity={0.85}
                      accessibilityRole="button"
                      accessibilityLabel={t('chat.continueSingleChartA11y', 'Continue with selected chart only')}
                    >
                      <Text style={styles.nativeGatePlainCtaText}>
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
                  style={styles.followUpButton}
                  onPress={() => onFollowUpClick && onFollowUpClick(cleanQuestion)}
                >
                  <Text style={styles.followUpText}>{cleanQuestion}</Text>
                </TouchableOpacity>
              );
            }).filter(Boolean)}
          </View>
        )}

        {message.next_action?.type === 'remedy' && (
          <View style={styles.remedyCard}>
            {console.log('[Mobile MessageBubble] remedy card render', {
              messageId: message.messageId,
              nextAction: message.next_action,
            })}
            <View style={styles.remedyCardHeader}>
              <View style={styles.remedyBadge}>
                <Ionicons name="leaf-outline" size={14} color="#16a34a" />
                <Text style={styles.remedyBadgeText}>
                  {t('chat.remedyCardLabel', 'Remedy')}
                </Text>
              </View>
            </View>
            {message.next_action?.title ? (
              <Text style={styles.remedyCardTitle}>{message.next_action.title}</Text>
            ) : null}
            {message.next_action?.reason ? (
              <Text style={styles.remedyCardReason}>{message.next_action.reason}</Text>
            ) : (
              <Text style={styles.remedyCardReason}>
                {t('chat.remedyCardDefaultReason', 'A practical next step based on your chart answer.')}
              </Text>
            )}
            <TouchableOpacity
              style={styles.remedyCardButton}
              onPress={() => {
                const remedyPrompt = (
                  message.next_action?.follow_up_questions?.[0]
                  || message.next_action?.title
                  || t('chat.askForRemedy', 'Show me the remedy')
                ).trim();
                if (onRemedyFollowUpClick) {
                  onRemedyFollowUpClick(remedyPrompt, {
                    source: 'remedy_card',
                    nextAction: message.next_action || null,
                    messageId: message.messageId || null,
                  });
                  return;
                }
                onFollowUpClick && onFollowUpClick(remedyPrompt);
              }}
              activeOpacity={0.88}
            >
              <Text style={styles.remedyCardButtonText}>
                {t('chat.openRemedy', 'Open remedy')}
              </Text>
              <Ionicons name="arrow-forward" size={16} color="#fff" />
            </TouchableOpacity>
          </View>
        )}

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
        {!message.isTyping && message.role === 'assistant' && !message.isWelcome && !isNativeGate && (message.messageId || message.content) && (
          <View style={styles.actionButtons}>
            {/* Restart Button for timeout messages */}
            {message.showRestartButton && message.messageId && (
              <TouchableOpacity
                style={[styles.actionButton, styles.restartButton]}
                onPress={() => onRestart && onRestart(message.messageId)}
              >
                <Ionicons name="refresh" size={16} color="#ff6b35" />
              </TouchableOpacity>
            )}
            {/* Retry send button for initial network failures (no messageId yet) */}
            {message.showSendRetryButton && !message.messageId && (
              <TouchableOpacity
                style={[styles.actionButton, styles.restartButton]}
                onPress={() => onSendRetry && onSendRetry(message)}
              >
                <Ionicons name="refresh" size={16} color="#ff6b35" />
              </TouchableOpacity>
            )}
            {message.role === 'assistant' && (
              <>
                {!isInstantChatMessage && !(isPlayingPodcast || isPausedPodcast) && (
                  <TouchableOpacity
                    style={[styles.actionButton, styles.listenPodcastButton]}
                    onPress={onPodcastButtonPress}
                    disabled={isLoadingPodcast}
                  >
                    {isLoadingPodcast ? (
                      <ActivityIndicator size="small" color="#ff6b35" />
                    ) : (
                      <Ionicons name="radio-outline" size={17} color="#ff6b35" />
                    )}
                  </TouchableOpacity>
                )}
                {!isInstantChatMessage && (isPlayingPodcast || isPausedPodcast) && (
                  <>
                    {isPlayingPodcast && (
                      <TouchableOpacity
                        style={styles.actionButton}
                        onPress={handlePausePodcast}
                      >
                        <Ionicons name="pause" size={16} color="#ff6b35" />
                      </TouchableOpacity>
                    )}
                    {isPausedPodcast && (
                      <TouchableOpacity
                        style={styles.actionButton}
                        onPress={onPodcastButtonPress}
                      >
                        <Ionicons name="play" size={16} color="#666" />
                      </TouchableOpacity>
                    )}
                    <TouchableOpacity
                      style={styles.actionButton}
                      onPress={handleStopPodcast}
                    >
                      <Ionicons name="stop-circle" size={16} color="#666" />
                    </TouchableOpacity>
                  </>
                )}
                {!isInstantChatMessage && (
                  <TouchableOpacity
                    style={styles.actionButton}
                    onPress={sharePodcastAudio}
                    disabled={isSharingPodcast || isLoadingPodcast}
                  >
                    {isSharingPodcast ? (
                      <ActivityIndicator size="small" color="#666" />
                    ) : (
                      <Ionicons name="share-outline" size={16} color="#666" />
                    )}
                  </TouchableOpacity>
                )}
              </>
            )}
            <TouchableOpacity
              style={styles.actionButton}
              onPress={copyToClipboard}
            >
              <Ionicons name="copy-outline" size={16} color="#666" />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={shareMessage}
            >
              <Ionicons name="share-social-outline" size={16} color="#666" />
            </TouchableOpacity>
            {message.role === 'assistant' && (
              <TouchableOpacity
                style={[styles.actionButton, styles.pdfButton]}
                onPress={sharePDF}
                disabled={isGeneratingPDF}
              >
                {isGeneratingPDF ? (
                  <ActivityIndicator size="small" color={COLORS.primary} />
                ) : (
                  <Ionicons name="document-text-outline" size={16} color="#666" />
                )}
              </TouchableOpacity>
            )}
            <TouchableOpacity
              style={[styles.actionButton, styles.deleteButton]}
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
              <Ionicons name="trash-outline" size={16} color="#666" />
            </TouchableOpacity>
          </View>
        )}

        {!message.isTyping && message.role === 'user' && !!(message.content && message.content.trim()) && (
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={copyToClipboard}
            >
              <Ionicons name="copy-outline" size={16} color="#666" />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={shareMessage}
            >
              <Ionicons name="share-social-outline" size={16} color="#666" />
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionButton, styles.deleteButton]}
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
              <Ionicons name="trash-outline" size={16} color="#666" />
            </TouchableOpacity>
          </View>
        )}

        {message.role === 'assistant' && (
          <Text style={styles.timestamp}>
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
          style={styles.tooltipModalOverlay} 
          activeOpacity={1} 
          onPress={() => setTooltipModal({ show: false, term: '', definition: '' })}
        >
          <Animated.View style={styles.tooltipModalContent}>
            <LinearGradient
              colors={theme === 'dark'
                ? ['rgba(0, 0, 0, 0.9)', 'rgba(20, 20, 20, 0.85)']
                : ['rgba(255, 255, 255, 0.98)', 'rgba(255, 248, 240, 0.95)']}
              style={[styles.tooltipGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 107, 53, 0.1)' }]}
            >
              <View style={styles.tooltipHeader}>
                <View style={styles.tooltipIconCircle}>
                  <Ionicons name="book-outline" size={20} color="#ff6b35" />
                </View>
                <Text style={styles.tooltipModalTitle}>{tooltipModal.term}</Text>
              </View>
              
              <ScrollView style={styles.tooltipScrollView} showsVerticalScrollIndicator={false}>
                <Text style={[styles.tooltipModalDefinition, { color: theme === 'dark' ? '#ecf0f1' : '#2c3e50' }]}>{tooltipModal.definition}</Text>
              </ScrollView>

              <TouchableOpacity
                style={styles.tooltipModalClose}
                onPress={() => setTooltipModal({ show: false, term: '', definition: '' })}
              >
                <Text style={styles.tooltipModalCloseText}>{t('languageModal.close', 'Close')}</Text>
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
        onRequestClose={() => setShowImageModal(false)}
      >
        <TouchableOpacity
          style={styles.imageModalOverlay}
          activeOpacity={1}
          onPress={() => setShowImageModal(false)}
        >
          <View style={styles.imageModalContainer}>
            {message.summary_image && (
              <Image
                source={{ uri: message.summary_image }}
                style={styles.fullScreenImage}
                resizeMode="contain"
              />
            )}
            <TouchableOpacity
              style={styles.closeImageButton}
              onPress={() => setShowImageModal(false)}
            >
              <Text style={styles.closeImageButtonText}>✕</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>

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
  if (prevProps.onStartPartnershipGate !== nextProps.onStartPartnershipGate) return false;
  if (prevProps.onContinueSingleChartGate !== nextProps.onContinueSingleChartGate) return false;
  if (prevProps.onRelationshipContextGate !== nextProps.onRelationshipContextGate) return false;
  return true;
};

export default React.memo(MessageBubble, areMessageBubblePropsEqual);

  const styles = StyleSheet.create({
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
    borderRadius: 20,
    padding: 16,
    marginVertical: 6,
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
  chartNameBadgeUser: {
    backgroundColor: 'rgba(59, 130, 246, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.3)',
  },
  chartNameBadgeAssistant: {
    backgroundColor: 'rgba(255, 107, 53, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.25)',
  },
  chartNameBadgeTextUser: {
    fontSize: 10,
    fontWeight: '600',
    color: '#1e3a8a',
  },
  chartNameBadgeTextAssistant: {
    fontSize: 10,
    fontWeight: '600',
    color: '#7c2d12',
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
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
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
    paddingBottom: 4,
  },
  regularText: {
    fontSize: 15,
    lineHeight: 22,
    marginVertical: 2,
    color: '#2c3e50',
    flexShrink: 1,
  },
  userText: {
    color: '#1e3a8a',
    fontWeight: '500',
  },
  boldText: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '700',
    color: '#2c3e50',
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
    backgroundColor: '#ff6b35',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
    marginTop: 2,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
    elevation: 3,
  },
  numberText: {
    color: '#ffffff',
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
    backgroundColor: '#ff6b35',
    shadowColor: '#ff6b35',
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
    color: '#2c3e50',
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
    color: Platform.OS === 'android' ? '#2c3e50' : '#2c3e50',
    lineHeight: 22,
    zIndex: 1,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 8,
    gap: 8,
  },
  actionButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 10,
    width: 36,
    height: 36,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
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
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginVertical: 6,
    gap: 6,
  },
  remedyCard: {
    backgroundColor: Platform.OS === 'android' ? 'rgba(22, 163, 74, 0.12)' : 'rgba(22, 163, 74, 0.08)',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(22, 163, 74, 0.25)',
    padding: 14,
    marginTop: 8,
    marginBottom: 4,
  },
  remedyCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
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
    color: '#14532d',
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 6,
  },
  remedyCardReason: {
    color: '#166534',
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 12,
    fontWeight: '500',
  },
  remedyCardButton: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#16a34a',
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  remedyCardButtonText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 13,
  },
  followUpButton: {
    backgroundColor: Platform.OS === 'android' ? 'rgba(255, 107, 53, 0.18)' : 'rgba(255, 107, 53, 0.12)',
    borderRadius: 25,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginBottom: 8,
    borderWidth: 1.5,
    borderColor: Platform.OS === 'android' ? 'rgba(255, 107, 53, 0.4)' : 'rgba(255, 107, 53, 0.3)',
    shadowColor: Platform.OS === 'android' ? 'transparent' : '#ff6b35',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: Platform.OS === 'android' ? 0 : 0.2,
    shadowRadius: Platform.OS === 'android' ? 0 : 4,
    elevation: Platform.OS === 'android' ? 0 : 3,
  },
  followUpText: {
    color: '#ff6b35',
    fontSize: 13,
    fontWeight: '600',
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
    color: '#ff6b35',
    fontWeight: '700',
    backgroundColor: 'rgba(255, 107, 53, 0.08)',
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderWidth: 0.5,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    textDecorationLine: 'underline',
    textDecorationStyle: Platform.OS === 'ios' ? 'solid' : 'dashed',
    overflow: 'hidden',
  },
  tooltipModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  tooltipModalContent: {
    width: '90%',
    maxWidth: 400,
    borderRadius: 24,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  tooltipGradient: {
    padding: 24,
    borderRadius: 24,
    borderWidth: 1,
  },
  tooltipHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 12,
  },
  tooltipIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.2)',
  },
  tooltipModalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#ff6b35',
    flex: 1,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  tooltipScrollView: {
    maxHeight: 300,
    marginBottom: 20,
  },
  tooltipModalDefinition: {
    fontSize: 15,
    lineHeight: 22,
  },
  tooltipModalClose: {
    backgroundColor: '#ff6b35',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 25,
    alignSelf: 'center',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  tooltipModalCloseText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
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
    borderColor: 'rgba(255, 107, 53, 0.15)',
    backgroundColor: '#fff',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  tableHeaderRow: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 107, 53, 0.08)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 107, 53, 0.15)',
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
    color: '#ff6b35',
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
    backgroundColor: 'rgba(156, 39, 176, 0.08)',
    borderLeftWidth: 3,
    borderLeftColor: '#9C27B0',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  disclaimerNoticeText: {
    fontSize: 11,
    color: '#6A1B9A',
    fontWeight: '600',
    lineHeight: 16,
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
    justifyContent: 'center',
    alignItems: 'center',
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
    borderColor: 'rgba(234, 88, 12, 0.35)',
    backgroundColor: 'rgba(255, 247, 237, 0.92)',
  },
  nativeGateSecondaryCtaText: {
    color: '#ea580c',
    fontSize: 14,
    fontWeight: '700',
  },
  nativeGatePlainCta: {
    borderRadius: 999,
    paddingVertical: 9,
    paddingHorizontal: 14,
    borderWidth: 1,
    borderColor: 'rgba(120, 113, 108, 0.28)',
    backgroundColor: 'rgba(255, 255, 255, 0.82)',
  },
  nativeGatePlainCtaText: {
    color: '#57534e',
    fontSize: 13,
    fontWeight: '700',
  },
  nativeGateHelperText: {
    fontSize: 13,
    lineHeight: 18,
    color: '#7c2d12',
    fontWeight: '600',
    marginBottom: 12,
  },
});
