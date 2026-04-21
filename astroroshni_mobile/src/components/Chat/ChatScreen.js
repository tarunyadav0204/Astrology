import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  FlatList,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Modal,
  Share,
  Platform,
  KeyboardAvoidingView,
  BackHandler,
  Animated,
  Dimensions,
  InteractionManager,
  Keyboard,
  StatusBar,
  Linking,
} from 'react-native';
import { ScrollView as GHScrollView, FlatList as GHFlatList } from 'react-native-gesture-handler';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';

import MessageBubble from './MessageBubble';
import LoadingBubble from '../LoadingBubble';
import FeedbackComponent from './FeedbackComponent';
import EventPeriods from './EventPeriods';
import HomeScreen from './HomeScreen';
import CalibrationCard from './CalibrationCard';
import PremiumAnalysisModal from './PremiumAnalysisModal';
import NotificationEnableReminderModal from '../Notifications/NotificationEnableReminderModal';
import ConfirmCreditsModal from '../ConfirmCreditsModal';
import PodcastPromoModal from './PodcastPromoModal';
import ChatRatingPromptModal from './ChatRatingPromptModal';
import { storage } from '../../services/storage';
import { chatAPI, pricingAPI } from '../../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS, LANGUAGES, API_BASE_URL, getEndpoint } from '../../utils/constants';
import { COUNTRIES, YEARS } from '../../utils/mundaneConstants';
import { trackAstrologyEvent, trackEvent } from '../../utils/analytics';
import { useTheme } from '../../context/ThemeContext';
import { Image } from 'react-native';

import CascadingDashaBrowser from '../Dasha/CascadingDashaBrowser';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import { useCredits } from '../../credits/CreditContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useTranslation } from 'react-i18next';
import { getTextToSpeech } from '../../utils/textToSpeechLazy';

const { width: screenWidth } = Dimensions.get('window');
const isSmallScreen = screenWidth < 375;
// Width for Chart Essence dasha chips (wider so text fits comfortably)
const cardWidth = screenWidth * 0.3;
const fontSize = isSmallScreen ? 11 : 13;
const smallFontSize = isSmallScreen ? 9 : 10;
const CHAT_RATING_PROMPT_STATE_KEY = 'chatRatingPromptState_v1';

/** Dev testing: force rating modal on chat open (no question/scroll). Set to false after testing. */
const DEBUG_SHOW_RATING_PROMPT_ON_CHAT_OPEN = false;
/** Dev testing: if true, never redirect to Play/App Store from Rate now. */
const DEBUG_IN_APP_REVIEW_ONLY = false;

/** Listing with showAllReviews so users land near ratings when we must fall back to the browser/Play app. */
const GOOGLE_PLAY_REVIEW_URL =
  'https://play.google.com/store/apps/details?id=com.astroroshni.mobile&showAllReviews=true&pcampaignid=web_share';

/**
 * Open store listing when in-app review API cannot run (Expo Go, emulator, sideload, etc.).
 * Prefer expo’s storeUrl() once app.json has android.playStoreUrl / ios.appStoreUrl.
 */
const openRatingStoreListing = async (StoreReview) => {
  try {
    let url =
      StoreReview && typeof StoreReview.storeUrl === 'function' ? StoreReview.storeUrl() : null;
    if (!url && Platform.OS === 'android') {
      url = GOOGLE_PLAY_REVIEW_URL;
    }
    if (url) {
      await Linking.openURL(url);
      return true;
    }
  } catch (e) {
    if (__DEV__) console.warn('[StoreReview] open listing failed:', e?.message || e);
  }
  if (Platform.OS === 'android') {
    try {
      await Linking.openURL(GOOGLE_PLAY_REVIEW_URL);
      return true;
    } catch (_) {
      /* ignore */
    }
  }
  return false;
};

/**
 * Play In-App Review / SKStoreReviewController when available.
 * Important: do not use hasAction() as the only gate — it stays false if app.json has no store URLs,
 * which blocks requestReview() even on real Play installs. Use isAvailableAsync for that.
 */
const requestInAppStoreReview = async () => {
  let StoreReview = null;
  try {
    const mod = require('expo-store-review');
    StoreReview = mod?.default ?? mod;
  } catch (e) {
    if (__DEV__) console.warn('[StoreReview] load failed:', e?.message || e);
    return DEBUG_IN_APP_REVIEW_ONLY ? false : openRatingStoreListing(null);
  }

  if (!StoreReview || typeof StoreReview.requestReview !== 'function') {
    return DEBUG_IN_APP_REVIEW_ONLY ? false : openRatingStoreListing(null);
  }

  try {
    let available = true;
    if (typeof StoreReview.isAvailableAsync === 'function') {
      available = await StoreReview.isAvailableAsync();
    }

    if (available) {
      await StoreReview.requestReview();
      return true;
    }
  } catch (e) {
    if (__DEV__) console.warn('[StoreReview] requestReview failed:', e?.message || e);
  }

  if (DEBUG_IN_APP_REVIEW_ONLY) {
    return false;
  }

  return openRatingStoreListing(StoreReview);
};

const RELATIONSHIP_PRESETS = [
  {
    label: 'Husband & Wife',
    subSteps: [
      {
        prompt: 'Who is who?',
        options: (n, p) => [
          { label: `${n.name} (H) & ${p.name} (W)`, value: `${n.name} is husband and ${p.name} is wife` },
          { label: `${n.name} (W) & ${p.name} (H)`, value: `${n.name} is wife and ${p.name} is husband` }
        ]
      },
      {
        prompt: 'Marriage details?',
        options: () => [
          { label: 'First Marriage', value: '1st Marriage' },
          { label: 'Second Marriage', value: '2nd Marriage' },
          { label: 'Third Marriage', value: '3rd Marriage' }
        ]
      }
    ]
  },
  {
    label: 'Parent & Child',
    subSteps: [
      {
        prompt: 'Relationship roles?',
        options: (n, p) => [
          { label: `${n.name} is Parent`, value: `${n.name} is parent and ${p.name} is child` },
          { label: `${p.name} is Parent`, value: `${p.name} is parent and ${n.name} is child` }
        ]
      },
      {
        prompt: 'Specify child details?',
        options: () => [
          { label: '1st Son', value: '1st son' },
          { label: '2nd Son', value: '2nd son' },
          { label: '3rd Son', value: '3rd son' },
          { label: '1st Daughter', value: '1st daughter' },
          { label: '2nd Daughter', value: '2nd daughter' },
          { label: '3rd Daughter', value: '3rd daughter' }
        ]
      }
    ]
  },
  {
    label: 'Siblings',
    subSteps: [
      {
        prompt: 'Who is elder?',
        options: (n, p) => [
          { label: `${n.name} is Elder`, value: `${n.name} is elder sibling and ${p.name} is younger` },
          { label: `${p.name} is Elder`, value: `${p.name} is elder sibling and ${n.name} is younger` }
        ]
      }
    ]
  },
  {
    label: 'In-Laws',
    subSteps: [
      {
        prompt: 'Who is the In-Law?',
        options: (n, p) => [
          { label: `${n.name} is In-Law`, value: `${n.name} is in-law of ${p.name}` },
          { label: `${p.name} is In-Law`, value: `${p.name} is in-law of ${n.name}` }
        ]
      },
      {
        prompt: 'Specific relationship?',
        options: () => [
          { label: 'Mother-in-law & Daughter-in-law', value: 'Mother-in-law and Daughter-in-law' },
          { label: 'Mother-in-law & Son-in-law', value: 'Mother-in-law and Son-in-law' },
          { label: 'Father-in-law & Daughter-in-law', value: 'Father-in-law and Daughter-in-law' },
          { label: 'Father-in-law & Son-in-law', value: 'Father-in-law and Son-in-law' },
          { label: 'Brother-in-law', value: 'Brother-in-law relation' },
          { label: 'Sister-in-law', value: 'Sister-in-law relation' }
        ]
      }
    ]
  },
  {
    label: 'Grandparent & Grandchild',
    subSteps: [
      {
        prompt: 'Roles?',
        options: (n, p) => [
          { label: `${n.name} is Grandparent`, value: `${n.name} is grandparent and ${p.name} is grandchild` },
          { label: `${p.name} is Grandparent`, value: `${p.name} is grandparent and ${n.name} is grandchild` }
        ]
      }
    ]
  },
  {
    label: 'Uncle/Aunt & Nephew/Niece',
    subSteps: [
      {
        prompt: 'Roles?',
        options: (n, p) => [
          { label: `${n.name} is Uncle/Aunt`, value: `${n.name} is uncle/aunt and ${p.name} is nephew/niece` },
          { label: `${p.name} is Uncle/Aunt`, value: `${p.name} is uncle/aunt and ${n.name} is nephew/niece` }
        ]
      }
    ]
  },
  { label: 'Cousins' },
  { label: 'Guru & Disciple' },
  { label: 'Business Partners' },
  { label: 'Close Friends' },
  { label: 'Boyfriend & Girlfriend' },
  {
    label: 'Manager & Employee',
    subSteps: [
      {
        prompt: 'Work roles?',
        options: (n, p) => [
          { label: `${n.name} is Manager`, value: `${n.name} is manager and ${p.name} is employee` },
          { label: `${p.name} is Manager`, value: `${p.name} is manager and ${n.name} is employee` }
        ]
      }
    ]
  },
  { label: 'Colleague' },
  { label: 'Teacher & Student' },
  { label: 'Other...' }
];

export default function ChatScreen({ navigation, route }) {
  const { t, i18n } = useTranslation();
  useAnalytics('ChatScreen');
  const { theme, colors, getCardElevation } = useTheme();
  const {
    credits,
    partnershipCost,
    freeQuestionAvailable,
    freeQuestionRequiresNotifications,
    fetchBalance,
    podcastCost,
  } = useCredits();
  const insets = useSafeAreaInsets();
  
  // Mundane mode state
  const [isMundane, setIsMundane] = useState(false);
  const isMundaneRef = useRef(false);
  useEffect(() => { isMundaneRef.current = isMundane; }, [isMundane]);

  const [mundaneContext, setMundaneContext] = useState(null);
  const mundaneContextRef = useRef(null);
  useEffect(() => { mundaneContextRef.current = mundaneContext; }, [mundaneContext]);
  const [selectedCountry, setSelectedCountry] = useState(COUNTRIES[0]);
  const [selectedYear, setSelectedYear] = useState(YEARS[0]);
  const [showCountryPicker, setShowCountryPicker] = useState(false);
  const [countrySearchQuery, setCountrySearchQuery] = useState('');
  const [showYearPicker, setShowYearPicker] = useState(false);
  const [chatCost, setChatCost] = useState(1);
  const [premiumChatCost, setPremiumChatCost] = useState(3);
  const [chatCostOriginal, setChatCostOriginal] = useState(null);
  const [premiumChatCostOriginal, setPremiumChatCostOriginal] = useState(null);
  const [showModeSelector, setShowModeSelector] = useState(false);
  const [isPremiumAnalysis, setIsPremiumAnalysis] = useState(false);
  const [showEnhancedPopup, setShowEnhancedPopup] = useState(false);
  const [showPremiumBadge, setShowPremiumBadge] = useState(false);
  const [showPremiumModal, setShowPremiumModal] = useState(false);
  const [showPremiumTooltip, setShowPremiumTooltip] = useState(true);
  const tooltipResetRef = useRef(true);
  const freeUsedThisSendRef = useRef(false);
  const glowAnim = useRef(new Animated.Value(0)).current;
  const badgeFadeAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (isPremiumAnalysis) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(glowAnim, {
            toValue: 1,
            duration: 1500,
            useNativeDriver: true,
          }),
          Animated.timing(glowAnim, {
            toValue: 0,
            duration: 1500,
            useNativeDriver: true,
          }),
        ])
      ).start();
      
      // Show badge
      setShowPremiumBadge(true);
      Animated.timing(badgeFadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
      
      // Hide after 3 seconds
      const timer = setTimeout(() => {
        Animated.timing(badgeFadeAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }).start(() => setShowPremiumBadge(false));
      }, 3000);
      
      return () => clearTimeout(timer);
    } else {
      setShowPremiumBadge(false);
    }
  }, [isPremiumAnalysis]);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [language, setLanguage] = useState('english');
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const drawerAnim = useRef(new Animated.Value(300)).current;
  const menuScrollViewRef = useRef(null);
  const menuLogoGlow = useRef(new Animated.Value(0)).current;
  const menuJustClosedAt = useRef(0);

  useEffect(() => {
    let animation;
    if (showMenu) {
      animation = Animated.loop(
        Animated.sequence([
          Animated.timing(menuLogoGlow, {
            toValue: 1,
            duration: 1500,
            useNativeDriver: false,
          }),
          Animated.timing(menuLogoGlow, {
            toValue: 0,
            duration: 1500,
            useNativeDriver: false,
          }),
        ])
      );
      animation.start();
    } else {
      menuLogoGlow.setValue(0);
    }
    return () => {
      animation?.stop();
    };
  }, [showMenu]);

  const [showEventPeriods, setShowEventPeriods] = useState(false);
  const [showDashaBrowser, setShowDashaBrowser] = useState(false);
  const [showGreeting, setShowGreeting] = useState(true);
  const [nudgeUnreadCount, setNudgeUnreadCount] = useState(0);
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false);
  /** Keyboard frame height for bottom inset (iOS + Android; edge-to-edge often breaks adjustResize for RN root). */
  const [keyboardBottomInset, setKeyboardBottomInset] = useState(0);
  const [isAppStartup, setIsAppStartup] = useState(true);
  const [birthData, setBirthData] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [currentPersonId, setCurrentPersonId] = useState(null);
  const [pendingMessages, setPendingMessages] = useState(new Set());
  const scrollViewRef = useRef(null);
  const [forceGreeting, setForceGreeting] = useState(false);
  const [chartData, setChartData] = useState(null);
  const [loadingChart, setLoadingChart] = useState(false);
  const [dashaData, setDashaData] = useState(null);
  const [loadingDashas, setLoadingDashas] = useState(false);
  const lastMessageRef = useRef(null);
  
  // Calibration state
  const [calibrationEvent, setCalibrationEvent] = useState(null);
  
  // Partnership mode state
  const [partnershipMode, setPartnershipMode] = useState(false);
  const [partnershipStep, setPartnershipStep] = useState(0); // 0: select first, 1: select second, 2: describe relation, 3: done
  const [partnershipSubStep, setPartnershipSubStep] = useState(0);
  const [partnershipRelation, setPartnershipRelation] = useState('');
  const [isTypingOtherRelation, setIsTypingOtherRelation] = useState(false);
  const [otherRelationText, setOtherRelationText] = useState('');
  const [nativeSearchQuery, setNativeSearchQuery] = useState('');
  const [showPartnershipSetupModal, setShowPartnershipSetupModal] = useState(false);
  const [nativeChart, setNativeChart] = useState(null);
  const [partnerChart, setPartnerChart] = useState(null);
  const [showChartPicker, setShowChartPicker] = useState(false);
  const [selectingFor, setSelectingFor] = useState(null); // 'native' or 'partner'
  const [savedCharts, setSavedCharts] = useState([]);
  const [showPartnershipModal, setShowPartnershipModal] = useState(false);
  const [partnershipModalCost, setPartnershipModalCost] = useState(2);
  const [showMundaneModal, setShowMundaneModal] = useState(false);
  const [mundaneModalCost, setMundaneModalCost] = useState(1);
  const [podcastPromoVisible, setPodcastPromoVisible] = useState(false);
  const [podcastPromoMessageId, setPodcastPromoMessageId] = useState(null);
  const [podcastAutoLaunchKey, setPodcastAutoLaunchKey] = useState(0);
  const [ratingPromptVisible, setRatingPromptVisible] = useState(false);
  const [ratingPromptPending, setRatingPromptPending] = useState(false);
  const [ratingPromptMessageId, setRatingPromptMessageId] = useState(null);
  const [ratingEligibleMessageId, setRatingEligibleMessageId] = useState(null);
  const [ratingPromptStateLoaded, setRatingPromptStateLoaded] = useState(false);
  const [ratingPromptState, setRatingPromptState] = useState({
    completed: false,
    neverAskAgain: false,
    shownCount: 0,
    lastShownAt: null,
    lastAction: null,
  });
  const ratingPromptShownMessageIdsRef = useRef(new Set());

  const saveRatingPromptState = async (updater) => {
    setRatingPromptState((prev) => {
      const next = typeof updater === 'function' ? updater(prev) : updater;
      AsyncStorage.setItem(CHAT_RATING_PROMPT_STATE_KEY, JSON.stringify(next)).catch(() => {});
      return next;
    });
  };

  const triggerRatingPrompt = (messageId, source) => {
    if (!messageId) return;
    if (!ratingPromptStateLoaded) return;
    if (ratingPromptState.completed || ratingPromptState.neverAskAgain) return;
    if (ratingPromptShownMessageIdsRef.current.has(messageId)) return;
    if (podcastPromoVisible) {
      setRatingPromptPending(true);
      setRatingPromptMessageId(messageId);
      return;
    }
    ratingPromptShownMessageIdsRef.current.add(messageId);
    const shownAt = new Date().toISOString();
    saveRatingPromptState((prev) => ({
      ...prev,
      shownCount: Number(prev.shownCount || 0) + 1,
      lastShownAt: shownAt,
      lastAction: 'shown',
    }));
    setRatingPromptMessageId(messageId);
    setRatingPromptVisible(true);
    trackEvent('rating_prompt_shown', {
      source,
      message_id: String(messageId),
      shown_count: Number(ratingPromptState.shownCount || 0) + 1,
    });
  };

  useEffect(() => {
    let cancelled = false;
    const loadRatingPromptState = async () => {
      try {
        const raw = await AsyncStorage.getItem(CHAT_RATING_PROMPT_STATE_KEY);
        if (cancelled) return;
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed && typeof parsed === 'object') {
            setRatingPromptState((prev) => ({
              ...prev,
              ...parsed,
            }));
          }
        }
      } catch (_) {
        // ignore corrupted local state
      } finally {
        if (!cancelled) {
          setRatingPromptStateLoaded(true);
        }
      }
    };
    loadRatingPromptState();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!DEBUG_SHOW_RATING_PROMPT_ON_CHAT_OPEN) return;
    const t = setTimeout(() => {
      setRatingPromptMessageId('debug_open_chat');
      setRatingPromptVisible(true);
      trackEvent('rating_prompt_shown', {
        source: 'debug_open_chat',
        message_id: 'debug_open_chat',
        shown_count: 0,
      });
    }, 500);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    const maxKeyboardInset = Math.min(520, Math.round(Dimensions.get('window').height * 0.58));
    const clearKeyboardInset = () => {
      setIsKeyboardVisible(false);
      setKeyboardBottomInset(0);
    };
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';
    const showSub = Keyboard.addListener(showEvent, (e) => {
      setIsKeyboardVisible(true);
      const h = e?.endCoordinates?.height;
      if (typeof h === 'number' && h > 0) {
        setKeyboardBottomInset(Math.min(h, maxKeyboardInset));
      }
    });
    const hideSub = Keyboard.addListener(hideEvent, clearKeyboardInset);
    /** iOS Simulator / hardware keyboard: WillHide sometimes never fires; DidHide clears stuck inset. */
    const hideDidSub =
      Platform.OS === 'ios' ? Keyboard.addListener('keyboardDidHide', clearKeyboardInset) : null;

    return () => {
      showSub.remove();
      hideSub.remove();
      hideDidSub?.remove();
    };
  }, []);
  // Stop any ongoing TTS playback when leaving the chat screen
  useFocusEffect(
    React.useCallback(() => {
      return () => {
        try {
          getTextToSpeech().stop();
        } catch (e) {
          // ignore
        }
        setKeyboardBottomInset(0);
        setIsKeyboardVisible(false);
      };
    }, [])
  );

  useFocusEffect(
    React.useCallback(() => {
      let cancelled = false;
      const loadUnread = async () => {
        try {
          const { nudgeAPI } = require('../../services/api');
          const res = await nudgeAPI.getUnreadCount();
          if (!cancelled) {
            setNudgeUnreadCount(Number(res.data?.unread_count) || 0);
          }
        } catch {
          if (!cancelled) setNudgeUnreadCount(0);
        }
      };
      loadUnread();
      return () => {
        cancelled = true;
      };
    }, [])
  );

  // Pending message management (like web app)
  const addPendingMessage = async (messageId) => {
    const key = `pendingChatMessages_${currentPersonId}`;
    const stored = await AsyncStorage.getItem(key);
    const pendingIds = stored ? JSON.parse(stored) : [];
    if (!pendingIds.includes(messageId)) {
      pendingIds.push(messageId);
      await AsyncStorage.setItem(key, JSON.stringify(pendingIds));
    }
    setPendingMessages(prev => new Set([...prev, messageId]));
  };
  
  const removePendingMessage = async (messageId) => {
    const key = `pendingChatMessages_${currentPersonId}`;
    const stored = await AsyncStorage.getItem(key);
    if (stored) {
      const pendingIds = JSON.parse(stored).filter(id => id !== messageId);
      await AsyncStorage.setItem(key, JSON.stringify(pendingIds));
    }
    setPendingMessages(prev => {
      const newSet = new Set(prev);
      newSet.delete(messageId);
      return newSet;
    });
  };
  
  const checkPendingResponses = async (personId = currentPersonId) => {
    const stored = await AsyncStorage.getItem(`pendingChatMessages_${personId}`);
    if (stored) {
      const pendingIds = JSON.parse(stored);
      pendingIds.forEach(messageId => {
        // Resume polling for each pending message
        pollForResponse(messageId, null, sessionId, '', true); // true = resume mode
      });
    }
  };
  
  // Load saved charts for partnership mode
  const loadSavedCharts = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/birth-charts')}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSavedCharts(data.charts || []);
      } else {
        setSavedCharts([]);
      }
    } catch (error) {
      console.error('Error loading saved charts:', error);
      setSavedCharts([]);
    }
  };
  
  // Load charts when component mounts
  useEffect(() => {
    loadSavedCharts();
  }, []);
  
  // Reload charts when picker opens
  useEffect(() => {
    if (showChartPicker) {
      loadSavedCharts();
    }
  }, [showChartPicker]);
  
  // Fetch calibration event when birth data changes
  useEffect(() => {
    if (birthData?.id && !showGreeting) {
      fetchCalibrationEvent();
    }
  }, [birthData?.id, showGreeting]);
  
  const fetchCalibrationEvent = async () => {
    try {
      
      // Use the proper API service instead of direct fetch
      const { lifeEventsAPI } = require('../../services/api');
      
      const response = await lifeEventsAPI.scanLifeEvents({
        name: birthData.name,
        date: birthData.date,
        time: birthData.time,
        latitude: birthData.latitude,
        longitude: birthData.longitude,
        place: birthData.place || "",
        place: birthData.place || '',
        gender: birthData.gender || ''
      }, 18, 50);
      
      if (response.data && response.data.events && response.data.events.length > 0) {
        setCalibrationEvent(response.data.events[0]);
      }
    } catch (error) {
    }
  };
  
  const handleCalibrationConfirm = async (event) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      await fetch(`${API_BASE_URL}${getEndpoint('/chat/verify-calibration')}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          birth_chart_id: birthData.id,
          event_year: event.year,
          verified: true
        })
      });
      
      setCalibrationEvent({ ...event, verified: true });
      Alert.alert('✅ Verified', 'Chart calibrated successfully!');
    } catch (error) {
      console.error('Calibration error:', error);
    }
  };
  
  const handleCalibrationReject = async (event) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      await fetch(`${API_BASE_URL}${getEndpoint('/chat/verify-calibration')}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          birth_chart_id: birthData.id,
          event_year: event.year,
          verified: false
        })
      });
      
      setCalibrationEvent(null);
    } catch (error) {
      console.error('Calibration error:', error);
    }
  };

  const getMenuOptionStyle = () => [
    styles.menuOption,
    { elevation: getCardElevation(3) }
  ];

  const suggestions = [
    "What does my birth chart say about my career?",
    "When is a good time for marriage?",
    "What are my health vulnerabilities?",
    "Tell me about my current dasha period",
    "What do the current transits mean for me?",
    "Show me significant periods in my life",
    "What are my strengths and weaknesses?"
  ];

  const getSignName = (signNumber) => {
    if (signNumber === undefined || signNumber === null) return t('common.unknown', 'Unknown');
    const signs = {
      0: 'Aries', 1: 'Taurus', 2: 'Gemini', 3: 'Cancer',
      4: 'Leo', 5: 'Virgo', 6: 'Libra', 7: 'Scorpio',
      8: 'Sagittarius', 9: 'Capricorn', 10: 'Aquarius', 11: 'Pisces'
    };
    const signName = signs[signNumber] || signNumber;
    return t(`signs.${signName}`, signName);
  };

  const getSignIcon = (signNumber) => {
    if (signNumber === undefined || signNumber === null) return '⭐';
    const icons = {
      0: '♈', 1: '♉', 2: '♊', 3: '♋',
      4: '♌', 5: '♍', 6: '♎', 7: '♏',
      8: '♐', 9: '♑', 10: '♒', 11: '♓'
    };
    return icons[signNumber] || '⭐';
  };

  const getPlanetColor = (planetName) => {
    const colors = {
      'Sun': '#ff6b35',
      'Moon': '#e0e0e0',
      'Mars': '#d32f2f',
      'Mercury': '#4caf50',
      'Jupiter': '#ffd700',
      'Venus': '#e91e63',
      'Saturn': '#2196f3',
      'Rahu': '#9e9e9e',
      'Ketu': '#795548',
    };
    return colors[planetName] || '#ffffff';
  };

  const loadChartData = async (birth) => {
    try {
      setLoadingChart(true);
      const formattedData = {
        ...birth,
        date: typeof birth.date === 'string' ? birth.date.split('T')[0] : birth.date,
        time: typeof birth.time === 'string' ? birth.time.split('T')[1]?.slice(0, 5) || birth.time : birth.time,
        latitude: parseFloat(birth.latitude),
        longitude: parseFloat(birth.longitude)
      };
      
      const { chartAPI } = require('../../services/api');
      const response = await chartAPI.calculateChartOnly(formattedData);
      setChartData(response.data);

    } catch (error) {
      console.error('Error loading chart data:', error);
      if (error.response?.status === 503) {
      }
    } finally {
      setLoadingChart(false);
    }
  };

  const loadDashaData = async (birth) => {
    try {
      setLoadingDashas(true);
      const targetDate = new Date().toISOString().split('T')[0];
      
      const formattedBirthData = {
        name: birth.name,
        date: birth.date.includes('T') ? birth.date.split('T')[0] : birth.date,
        time: birth.time.includes('T') ? new Date(birth.time).toTimeString().slice(0, 5) : birth.time,
        latitude: parseFloat(birth.latitude),
        longitude: parseFloat(birth.longitude),
        location: birth.place || 'Unknown'
      };
      
      const { chartAPI } = require('../../services/api');
      const response = await chartAPI.calculateCascadingDashas(formattedBirthData, targetDate);
      
      if (response.data && !response.data.error) {
        setDashaData(response.data);
      }
    } catch (error) {
      console.error('Error loading dasha data:', error);
      if (error.response?.status === 503) {
      }
    } finally {
      setLoadingDashas(false);
    }
  };



  useEffect(() => {
    checkBirthData();
    loadLanguagePreference();
    fetchChatCost();
    
    // Add focus listener to re-check birth data when returning to screen
    const unsubscribe = navigation.addListener('focus', () => {
      checkBirthData();
    });
    
    // Handle navigation params
    if (route.params?.resetToGreeting) {
      setShowGreeting(true);
      navigation.setParams({ resetToGreeting: undefined });
    }
    
    // Handle start chat param (e.g. from notification tap). Refresh birth data from storage
    // first so the notification's native_id selection is applied, then open chat.
    if (route.params?.startChat) {
      const initialMsg = route.params?.initialMessage;
      const responseReadySessionId = route.params?.responseReadySessionId;
      navigation.setParams({ startChat: undefined, initialMessage: undefined, responseReadySessionId: undefined });
      (async () => {
        await checkBirthData();
        if (responseReadySessionId) {
          try {
            const token = await AsyncStorage.getItem('authToken');
            const res = await fetch(`${API_BASE_URL}${getEndpoint(`/chat-v2/session/${responseReadySessionId}`)}`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
              const data = await res.json();
              const msgs = (data.messages || []).map((m) => ({
                messageId: m.message_id,
                role: m.sender,
                content: m.content || '',
                timestamp: m.timestamp,
                id: `${m.message_id}_${m.timestamp}`,
                native_name: m.native_name ?? data.native_name ?? null,
                terms: m.terms,
                glossary: m.glossary,
                images: m.images,
                message_type: m.message_type,
                intent_gate: m.intent_gate,
                gate_metadata: m.gate_metadata,
              }));
              setSessionId(responseReadySessionId);
              setMessagesWithStorage(msgs);
              setShowGreeting(false);
              return;
            }
          } catch (err) {
            if (__DEV__) console.warn('[Chat] Fetch session for push failed:', err?.message);
          }
        }
        setTimeout(() => {
          handleGreetingOptionSelect({ action: 'question' });
          if (initialMsg) {
            setInputText(initialMsg);
          }
        }, 150);
      })();
    }
    
    // Handle mundane mode param
    if (route.params?.mode === 'mundane') {
      setIsMundane(true);
      setIsPremiumAnalysis(false); // No premium in mundane
      setShowModeSelector(false);
      if (route.params?.mundaneContext) {
        setMundaneContext(route.params.mundaneContext);
        
        // Sync selected country if provided in context
        if (route.params.mundaneContext.country) {
          const countryMatch = COUNTRIES.find(c => c.name === route.params.mundaneContext.country);
          if (countryMatch) {
            setSelectedCountry(countryMatch);
          }
        }
        
        // Sync selected year if provided in context (event_date)
        if (route.params.mundaneContext.event_date) {
          const year = new Date(route.params.mundaneContext.event_date).getFullYear();
          setSelectedYear(year);
        }
      }
      navigation.setParams({ mode: undefined, mundaneContext: undefined });
    }
    
    // Handle back button
    const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
      if (!showGreeting) {
        // In chat mode, show greeting screen and reset special modes
        setShowGreeting(true);
        if (isMundane) {
          setIsMundane(false);
          setMundaneContext(null);
        }
        if (partnershipMode) {
          setPartnershipMode(false);
          setNativeChart(null);
          setPartnerChart(null);
          setPartnershipRelation('');
          setIsTypingOtherRelation(false);
          setOtherRelationText('');
          setNativeSearchQuery('');
        }
        setIsPremiumAnalysis(false);
        setShowModeSelector(false);
        return true;
      }
      return false;
    });
    
    return () => {
      unsubscribe();
      backHandler.remove();
    };
  }, [navigation, showGreeting, route.params]);

  // Remove problematic back handler that clears messages

  const fetchChatCost = async () => {
    try {
      const res = await pricingAPI.getPricing();
      const data = res?.data || res;
      const pricing = data?.pricing || {};
      const orig = data?.pricing_original || {};
      // Standard chat (user-discounted when VIP)
      const chatVal = pricing.chat != null ? Number(pricing.chat) || 1 : 1;
      const chatOriginal = orig.chat != null ? Number(orig.chat) : null;
      setChatCost(chatVal);
      setChatCostOriginal(Number.isNaN(chatOriginal) ? null : chatOriginal);
      // Premium chat (user-discounted when VIP; same source as standard)
      const premiumVal = pricing.premium_chat != null ? Number(pricing.premium_chat) : 3;
      const premiumOriginal = orig.premium_chat != null ? Number(orig.premium_chat) : null;
      setPremiumChatCost(Number.isNaN(premiumVal) || premiumVal <= 0 ? 3 : premiumVal);
      setPremiumChatCostOriginal(Number.isNaN(premiumOriginal) ? null : premiumOriginal);
    } catch (error) {
      console.error('Error fetching chat cost:', error);
    }
  };

  useEffect(() => {
    
    if (birthData) {
      // Create unique person ID from birth data
      const personId = `${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}`;
      
      // Check if person changed
      if (currentPersonId && currentPersonId !== personId) {
        // Different person selected - clear current state
        setMessages([]);
        setSessionId(null);
        setShowGreeting(true);
      }
      
      // Only update if person ID actually changed
      if (currentPersonId !== personId) {
        
        // Set person ID first to avoid null issues
        setCurrentPersonId(personId);
        
        // Load chart data for the new person
        setChartData(null); // Clear cached data
        loadChartData(birthData);
        loadDashaData(birthData);
        
        // Load messages from storage immediately
        loadMessagesFromStorage(personId).then(storedMessages => {
          if (storedMessages.length > 0) {
            setMessages(storedMessages);
            // Only auto-switch to chat if not app startup
            if (!isAppStartup && messages.length === 0) {
              setShowGreeting(false);
            }
            
            // Set flag to auto-scroll when content renders
            setTimeout(() => {
              if (messages.length > 0) {
                lastMessageRef.current?.measureLayout(
                  scrollViewRef.current,
                  (x, y) => {
                    scrollViewRef.current?.scrollTo({ y: y, animated: false });
                  },
                  () => {}
                );
              }
            }, 50);
            
            // Check for processing messages and resume polling.
            // This prevents a stuck "Analyzing..." state after app/background refresh.
            const processingMessage = storedMessages.find(
              msg => msg.isTyping && msg.messageId && !pendingMessages.has(msg.messageId)
            );
            if (processingMessage) {
              setLoading(true);
              setIsTyping(true);
              setTimeout(() => {
                const userMessage = storedMessages.filter(m => m.role === 'user').pop();
                pollForResponse(processingMessage.messageId, null, sessionId, userMessage?.content || '', true);
              }, 100);
            }
          } else {
            setShowGreeting(true);
          }
          // Reset force greeting and app startup after handling
          if (forceGreeting) {
            setTimeout(() => setForceGreeting(false), 100);
          }
          // Clear app startup flag after first load
          if (isAppStartup) {
            setTimeout(() => setIsAppStartup(false), 500);
          }
        });
        
        // Check pending responses after person ID is set
        setTimeout(() => {
          checkPendingResponses(personId);
        }, 200);
      }
    } else {
    }
  }, [birthData]);

  // Save messages to AsyncStorage per person (like web app)
  const saveMessagesToStorage = async (messages, personId = currentPersonId) => {
    if (!personId) return;
    try {
      await AsyncStorage.setItem(`chatMessages_${personId}`, JSON.stringify(messages));
    } catch (error) {
      console.error('Error saving messages:', error);
    }
  };

  // Load messages from AsyncStorage per person (like web app)
  const loadMessagesFromStorage = async (personId = currentPersonId) => {
    if (!personId) return [];
    try {
      const stored = await AsyncStorage.getItem(`chatMessages_${personId}`);
      if (stored) {
        const messages = JSON.parse(stored);
        return messages;
      }
    } catch (error) {
      console.error('Error loading messages from storage:', error);
    }
    return [];
  };

  // Override setMessages to also save to storage
  const setMessagesWithStorage = (messagesOrUpdater) => {
    setMessages(prev => {
      const newMessages = typeof messagesOrUpdater === 'function' ? messagesOrUpdater(prev) : messagesOrUpdater;
      // Get current person ID from birthData if currentPersonId is null
      const personId = currentPersonId || (birthData ? `${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}` : null);
      // Save to storage
      if (personId) {
        saveMessagesToStorage(newMessages, personId);
      }
      return newMessages;
    });
  };

  // Load messages when screen focuses - but don't interfere with ongoing polling
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      if (currentPersonId) {
        loadMessagesFromStorage(currentPersonId).then(storedMessages => {
          if (storedMessages.length > 0) {
            // Only update messages if we don't have any current messages to avoid overwriting
            const prevLength = messages.length;
            setMessages(prev => prev.length === 0 ? storedMessages : prev);
            // Don't auto-switch if app startup or we already have messages loaded
            if (!isAppStartup && messages.length === 0) {
              setShowGreeting(false);
            }
            
            // Set flag to scroll if we loaded new messages and not showing greeting
            if (prevLength === 0 && storedMessages.length > 0 && !showGreeting) {
              setTimeout(() => {
                if (storedMessages.length > 0) {
                  lastMessageRef.current?.measureLayout(
                    scrollViewRef.current,
                    (x, y) => {
                      scrollViewRef.current?.scrollTo({ y: y, animated: false });
                    },
                    () => {}
                  );
                }
              }, 50);
            }
            
            // Only resume polling if not already polling.
            if (!loading && !isTyping) {
              const processingMessage = storedMessages.find(
                msg => msg.isTyping && msg.messageId && !pendingMessages.has(msg.messageId)
              );
              if (processingMessage) {
                setLoading(true);
                setIsTyping(true);
                const userMessage = storedMessages.filter(m => m.role === 'user').pop();
                pollForResponse(processingMessage.messageId, null, sessionId, userMessage?.content || '', true);
              }
            }
          }
        });
      }
    });
    
    return unsubscribe;
  }, [currentPersonId, loading, isTyping, showGreeting, pendingMessages, sessionId]);

  // First question free: standard chat only (not partnership, not mundane)
  const effectiveChatCost = (!partnershipMode && !isMundane && freeQuestionAvailable)
    ? 0
    : (isPremiumAnalysis ? premiumChatCost : partnershipMode ? partnershipCost : chatCost);

  const openNotificationsForFreeQuestion = async () => {
    try {
      const { registerPushTokenIfLoggedIn } = require('../../services/pushNotifications');
      const result = await registerPushTokenIfLoggedIn();
      await fetchBalance();
      if (!result.ok) {
        Alert.alert('Notifications', result.message);
      }
    } catch (e) {
      Alert.alert('Notifications', e?.message || 'Could not enable notifications.');
    }
  };

  const openPartnershipModal = (cost) => {
    setPartnershipModalCost((cost != null && cost > 0) ? cost : partnershipCost);
    setShowPartnershipModal(true);
  };

  const confirmPartnershipMode = () => {
    loadSavedCharts(); // Refresh charts when starting partnership mode
    setShowPartnershipModal(false);
    setPartnershipMode(true);
    setIsPremiumAnalysis(false); // No premium in partnership
    setShowModeSelector(false);
    setPartnershipStep(0);
    setPartnershipSubStep(0);
    setPartnershipRelation('');
    setIsTypingOtherRelation(false);
    setOtherRelationText('');
    setNativeSearchQuery('');
    setNativeChart(null);
    setPartnerChart(null);
    setShowGreeting(false);
    setShowMenu(false);
    setShowPartnershipSetupModal(true); // Open the new setup modal
    
    // Add initial assistant message for partnership setup (the summarized bubble)
    const setupMessage = {
      id: `setup_${Date.now()}`,
      content: "🤝 Partnership Setup",
      role: 'assistant',
      timestamp: new Date().toISOString(),
      isSetup: true,
      setupType: 'partnership'
    };
    
    setMessagesWithStorage([setupMessage]);
  };

  const handlePartnershipChartSelect = (chart) => {
    setNativeSearchQuery('');
    if (partnershipStep === 0) {
      setNativeChart(chart);
      setPartnershipStep(1);
    } else if (partnershipStep === 1) {
      setPartnerChart(chart);
      setPartnershipStep(2);
      setPartnershipSubStep(0);
    }
  };

  const handleRelationshipSelect = (selection) => {
    if (selection === 'Other...') {
      setIsTypingOtherRelation(true);
      setOtherRelationText('');
      return;
    }

    // selection can be a string (label) or an option object from a sub-step
    const selectionLabel = typeof selection === 'object' ? selection.label : selection;
    const activePreset = RELATIONSHIP_PRESETS.find(p => p.label === selectionLabel);
    
    if (activePreset && activePreset.subSteps && partnershipRelation !== activePreset.label) {
      // Starting a complex preset flow
      setPartnershipRelation(activePreset.label);
      setPartnershipSubStep(0);
    } else {
      // Continuing a sub-step or selecting a simple preset
      const currentPreset = RELATIONSHIP_PRESETS.find(p => partnershipRelation === p.label || partnershipRelation.startsWith(p.label + ':'));
      
      if (currentPreset && currentPreset.subSteps && partnershipSubStep < currentPreset.subSteps.length) {
        // We are in the middle of sub-steps
        const valueToUse = typeof selection === 'object' ? selection.value : selection;
        const newRelation = (partnershipRelation === currentPreset.label)
          ? `${currentPreset.label}: ${valueToUse}`
          : `${partnershipRelation}, ${valueToUse}`;
        
        setPartnershipRelation(newRelation);
        
        if (partnershipSubStep + 1 < currentPreset.subSteps.length) {
          setPartnershipSubStep(partnershipSubStep + 1);
        } else {
          setPartnershipStep(3); // Done with sub-steps
        }
      } else {
        // Simple preset or final string
        setPartnershipRelation(selectionLabel);
        setPartnershipStep(3);
      }
    }
  };

  const renderPartnershipSetupModal = () => {
    const isNativeSet = !!nativeChart;
    const isPartnerSet = !!partnerChart;
    const isRelationSet = !!partnershipRelation;
    
    return (
      <Modal
        visible={showPartnershipSetupModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowPartnershipSetupModal(false)}
      >
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={[styles.partnershipModalContent, { backgroundColor: colors.background }]}>
            <View style={styles.modalHeader}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
                <Text style={{ fontSize: 20 }}>🤝</Text>
                <Text style={[styles.modalTitle, { color: colors.text, fontSize: 18 }]}>Partnership Setup</Text>
              </View>
              <TouchableOpacity 
                onPress={() => setShowPartnershipSetupModal(false)}
                style={{ backgroundColor: colors.border, padding: 6, borderRadius: 20 }}
              >
                <Ionicons name="close" size={20} color={colors.text} />
              </TouchableOpacity>
            </View>

            <GHScrollView
              showsVerticalScrollIndicator={false}
              contentContainerStyle={{ paddingBottom: 30 }}
              keyboardShouldPersistTaps="always"
            >
              <View style={styles.setupSlotsContainer}>
                {/* Slot 1: Native */}
                <TouchableOpacity 
                  style={[
                    styles.setupSlot, 
                    partnershipStep === 0 && styles.setupSlotActive,
                    isNativeSet && styles.setupSlotFilled
                  ]}
                  onPress={() => {
                    setPartnershipStep(0);
                    setNativeChart(null);
                    setPartnerChart(null);
                    setPartnershipRelation('');
                    setPartnershipSubStep(0);
                    setNativeSearchQuery('');
                  }}
                >
                  <View style={styles.setupSlotIcon}>
                    <Text>{isNativeSet ? '👤' : '1️⃣'}</Text>
                  </View>
                  <View style={styles.setupSlotContent}>
                    <Text style={styles.setupSlotLabel}>First Person</Text>
                    <Text style={isNativeSet ? styles.setupSlotValue : styles.setupSlotPlaceholder} numberOfLines={1}>
                      {isNativeSet ? nativeChart.name : 'Select from list below...'}
                    </Text>
                  </View>
                  {isNativeSet && <Ionicons name="checkmark-circle" size={20} color="#ff6b35" />}
                </TouchableOpacity>

                {/* Slot 2: Partner */}
                <TouchableOpacity 
                  style={[
                    styles.setupSlot, 
                    partnershipStep === 1 && styles.setupSlotActive,
                    isPartnerSet && styles.setupSlotFilled,
                    !isNativeSet && { opacity: 0.5 }
                  ]}
                  onPress={() => {
                    if (isNativeSet) {
                      setPartnershipStep(1);
                      setPartnerChart(null);
                      setPartnershipRelation('');
                      setPartnershipSubStep(0);
                      setNativeSearchQuery('');
                    }
                  }}
                  disabled={!isNativeSet}
                >
                  <View style={styles.setupSlotIcon}>
                    <Text>{isPartnerSet ? '👫' : '2️⃣'}</Text>
                  </View>
                  <View style={styles.setupSlotContent}>
                    <Text style={styles.setupSlotLabel}>Partner / Family / Friend</Text>
                    <Text style={isPartnerSet ? styles.setupSlotValue : styles.setupSlotPlaceholder} numberOfLines={1}>
                      {isPartnerSet ? partnerChart.name : (isNativeSet ? 'Select from list below...' : 'Complete Step 1 first')}
                    </Text>
                  </View>
                  {isPartnerSet && <Ionicons name="checkmark-circle" size={20} color="#ff6b35" />}
                </TouchableOpacity>

                {/* Slot 3: Relationship */}
                <TouchableOpacity 
                  style={[
                    styles.setupSlot, 
                    partnershipStep === 2 && styles.setupSlotActive,
                    isRelationSet && styles.setupSlotFilled,
                    !isPartnerSet && { opacity: 0.5 }
                  ]}
                  onPress={() => {
                    if (isPartnerSet) {
                      setPartnershipStep(2);
                      setPartnershipRelation('');
                      setPartnershipSubStep(0);
                      setNativeSearchQuery('');
                    }
                  }}
                  disabled={!isPartnerSet}
                >
                  <View style={styles.setupSlotIcon}>
                    <Text>{isRelationSet ? '💍' : '3️⃣'}</Text>
                  </View>
                  <View style={styles.setupSlotContent}>
                    <Text style={styles.setupSlotLabel}>Relationship Status</Text>
                    <Text style={isRelationSet ? styles.setupSlotValue : styles.setupSlotPlaceholder} numberOfLines={1}>
                      {isRelationSet ? partnershipRelation : (isPartnerSet ? 'Select or describe relationship...' : 'Complete Step 2 first')}
                    </Text>
                  </View>
                  {isRelationSet && <Ionicons name="checkmark-circle" size={20} color="#ff6b35" />}
                </TouchableOpacity>
              </View>

              {/* Action Buttons based on current step */}
              {(partnershipStep === 0 || partnershipStep === 1) && savedCharts.length > 5 && (
                <View style={styles.modalSearchContainer}>
                  <View style={[styles.modalSearchWrapper, { backgroundColor: colors.border + '40' }]}>
                    <Ionicons name="search" size={18} color={colors.textSecondary} />
                    <TextInput
                      style={[styles.modalSearchInput, { color: colors.text }]}
                      placeholder={`Search ${partnershipStep === 0 ? 'first person' : 'partner'}...`}
                      placeholderTextColor={colors.textSecondary + '80'}
                      value={nativeSearchQuery}
                      onChangeText={setNativeSearchQuery}
                      autoCorrect={false}
                    />
                    {nativeSearchQuery.length > 0 && (
                      <TouchableOpacity onPress={() => setNativeSearchQuery('')}>
                        <Ionicons name="close-circle" size={18} color={colors.textSecondary} />
                      </TouchableOpacity>
                    )}
                  </View>
                </View>
              )}

              {partnershipStep === 0 && (
                <View style={styles.setupSelectorContainer}>
                  {(() => {
                    const filtered = nativeSearchQuery 
                      ? savedCharts.filter(c => c.name.toLowerCase().includes(nativeSearchQuery.toLowerCase()))
                      : savedCharts;
                    
                    return (
                      <GHFlatList
                        horizontal
                        data={filtered.length > 0 ? filtered : [{ id: 'add-new', name: nativeSearchQuery ? 'No results found' : 'Add New Profile', isNew: true, isEmpty: !nativeSearchQuery }]}
                        keyExtractor={(chart) => chart.id}
                        showsHorizontalScrollIndicator={false}
                        keyboardShouldPersistTaps="always"
                        contentContainerStyle={styles.setupSelectorScroll}
                        renderItem={({ item: chart }) => (
                          <TouchableOpacity
                            style={[
                              styles.setupSelectorChip, 
                              { backgroundColor: '#ff6b3515', borderColor: '#ff6b35' },
                              chart.id === 'add-new' && chart.isEmpty === false && { opacity: 0.6 }
                            ]}
                            onPress={() => {
                              if (chart.id === 'add-new') {
                                if (chart.isEmpty) navigation.navigate('BirthForm');
                              } else {
                                handlePartnershipChartSelect(chart);
                              }
                            }}
                            disabled={chart.id === 'add-new' && !chart.isEmpty}
                          >
                            <Text style={[styles.setupSelectorText, { color: colors.text }]}>
                              {chart.id === 'add-new' ? (chart.isEmpty ? '➕ ' : '🔍 ') : '👤 '}
                              {chart.name}
                            </Text>
                          </TouchableOpacity>
                        )}
                      />
                    );
                  })()}
                </View>
              )}

              {partnershipStep === 1 && (
                <View style={styles.setupSelectorContainer}>
                  {(() => {
                    const otherCharts = savedCharts.filter(c => c.id !== nativeChart?.id);
                    const filtered = nativeSearchQuery 
                      ? otherCharts.filter(c => c.name.toLowerCase().includes(nativeSearchQuery.toLowerCase()))
                      : otherCharts;

                    return (
                      <GHFlatList
                        horizontal
                        data={filtered.length > 0 ? filtered : [{ id: 'add-new', name: nativeSearchQuery ? 'No results found' : 'Add New Profile', isNew: true, isEmpty: !nativeSearchQuery }]}
                        keyExtractor={(chart) => chart.id}
                        showsHorizontalScrollIndicator={false}
                        keyboardShouldPersistTaps="always"
                        contentContainerStyle={styles.setupSelectorScroll}
                        renderItem={({ item: chart }) => (
                          <TouchableOpacity
                            style={[
                              styles.setupSelectorChip, 
                              { backgroundColor: '#ff6b3515', borderColor: '#ff6b35' },
                              chart.id === 'add-new' && chart.isEmpty === false && { opacity: 0.6 }
                            ]}
                            onPress={() => {
                              if (chart.id === 'add-new') {
                                if (chart.isEmpty) navigation.navigate('BirthForm');
                              } else {
                                handlePartnershipChartSelect(chart);
                              }
                            }}
                            disabled={chart.id === 'add-new' && !chart.isEmpty}
                          >
                            <Text style={[styles.setupSelectorText, { color: colors.text }]}>
                              {chart.id === 'add-new' ? (chart.isEmpty ? '➕ ' : '🔍 ') : '👤 '}
                              {chart.name}
                            </Text>
                          </TouchableOpacity>
                        )}
                      />
                    );
                  })()}
                </View>
              )}

              {partnershipStep === 2 && (
                <View style={styles.setupSelectorContainer}>
                  {isTypingOtherRelation ? (
                    <View style={styles.otherRelationContainer}>
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                        <Text style={[styles.setupHelperText, { color: '#ff6b35', fontWeight: '700', fontSize: 13, marginBottom: 0 }]}>
                          Describe Relationship
                        </Text>
                        <TouchableOpacity 
                          onPress={() => {
                            setIsTypingOtherRelation(false);
                            setOtherRelationText('');
                          }}
                        >
                          <Text style={{ color: '#ff6b35', fontSize: 11, fontWeight: '600', textDecorationLine: 'underline' }}>← Back</Text>
                        </TouchableOpacity>
                      </View>
                      <View style={styles.otherInputWrapper}>
                        <TextInput
                          style={[styles.otherTextInput, { color: colors.text }]}
                          value={otherRelationText}
                          onChangeText={setOtherRelationText}
                          placeholder="e.g. Mentor, Distant Cousin, etc."
                          placeholderTextColor={theme === 'dark' ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.3)'}
                          autoFocus
                        />
                        <TouchableOpacity 
                          style={[
                            styles.otherDoneButton,
                            !otherRelationText.trim() && { opacity: 0.5 }
                          ]}
                          onPress={() => {
                            if (otherRelationText.trim()) {
                              setPartnershipRelation(otherRelationText.trim());
                              setPartnershipStep(3);
                              setIsTypingOtherRelation(false);
                            }
                          }}
                          disabled={!otherRelationText.trim()}
                        >
                          <Ionicons name="checkmark" size={20} color="#fff" />
                        </TouchableOpacity>
                      </View>
                    </View>
                  ) : (() => {
                    const currentPreset = RELATIONSHIP_PRESETS.find(p => partnershipRelation === p.label || partnershipRelation.startsWith(p.label + ':'));
                    
                    if (currentPreset && currentPreset.subSteps && partnershipSubStep < currentPreset.subSteps.length) {
                      const subStep = currentPreset.subSteps[partnershipSubStep];
                      const options = subStep.options(nativeChart, partnerChart);
                      
                      return (
                        <View>
                          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                            <Text style={[styles.setupHelperText, { color: '#ff6b35', fontWeight: '700', fontSize: 13, marginBottom: 0 }]}>
                              {subStep.prompt}
                            </Text>
                            <TouchableOpacity 
                              onPress={() => {
                                setPartnershipRelation('');
                                setPartnershipSubStep(0);
                              }}
                            >
                              <Text style={{ color: '#ff6b35', fontSize: 11, fontWeight: '600', textDecorationLine: 'underline' }}>← Back</Text>
                            </TouchableOpacity>
                          </View>
                          <GHFlatList
                            horizontal
                            data={options}
                            keyExtractor={(item, idx) => idx.toString()}
                            showsHorizontalScrollIndicator={false}
                            contentContainerStyle={styles.setupSelectorScroll}
                            renderItem={({ item }) => (
                              <TouchableOpacity
                                style={[styles.setupSelectorChip, { backgroundColor: '#ff6b3515', borderColor: '#ff6b35', minWidth: 100 }]}
                                onPress={() => handleRelationshipSelect(item)}
                              >
                                <Text style={[styles.setupSelectorText, { color: colors.text }]}>{item.label}</Text>
                              </TouchableOpacity>
                            )}
                          />
                        </View>
                      );
                    }

                    return (
                      <View>
                        <GHFlatList
                          horizontal
                          data={RELATIONSHIP_PRESETS}
                          keyExtractor={(item, idx) => idx.toString()}
                          showsHorizontalScrollIndicator={false}
                          contentContainerStyle={styles.setupSelectorScroll}
                          renderItem={({ item: relation }) => (
                            <TouchableOpacity
                              style={[styles.setupSelectorChip, { backgroundColor: '#ff6b3515', borderColor: '#ff6b35' }]}
                              onPress={() => handleRelationshipSelect(relation.label)}
                            >
                              <Text style={[styles.setupSelectorText, { color: colors.text }]}>{relation.label}</Text>
                            </TouchableOpacity>
                          )}
                        />
                        <Text style={[styles.setupHelperText, { color: colors.textSecondary, marginTop: 8 }]}>
                          Pick a preset or type your own relationship in the chat box after closing this modal.
                        </Text>
                      </View>
                    );
                  })()}
                </View>
              )}

              {partnershipStep === 3 && (
                <TouchableOpacity 
                  style={styles.setupConfirmButton}
                  onPress={() => {
                    // Add confirmation message to chat
                    const confirmMsg = {
                      id: `confirm_${Date.now()}`,
                      content: `Everything set! Analysis for **${nativeChart.name}** & **${partnerChart.name}** (${partnershipRelation}) is ready.\n\nAsk any question about your compatibility!`,
                      role: 'assistant',
                      timestamp: new Date().toISOString(),
                    };
                    setMessagesWithStorage(prev => [...prev, confirmMsg]);
                    setPartnershipStep(4); // Setup done
                    setShowPartnershipSetupModal(false); // Close modal
                    
                    // Scroll to bottom
                    setTimeout(() => {
                      scrollViewRef.current?.scrollToEnd({ animated: true });
                    }, 100);
                  }}
                >
                  <LinearGradient colors={['#ff6b35', '#f97316']} style={styles.setupConfirmGradient}>
                    <Text style={styles.setupConfirmText}>Ready for Analysis ✨</Text>
                    <Ionicons name="arrow-forward" size={20} color="#fff" />
                  </LinearGradient>
                </TouchableOpacity>
              )}

              {partnershipStep < 4 && (
                <TouchableOpacity 
                  style={styles.setupResetButton}
                  onPress={() => {
                    setNativeChart(null);
                    setPartnerChart(null);
                    setPartnershipRelation('');
                    setPartnershipStep(0);
                    setPartnershipSubStep(0);
                  }}
                >
                  <Text style={styles.setupResetText}>Reset Setup</Text>
                </TouchableOpacity>
              )}
            </GHScrollView>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    );
  };

  const openMundaneModal = (cost) => {
    // Use passed cost from HomeScreen option, fallback to chatCost
    const finalCost = (cost != null && cost > 0) ? cost : chatCost;
    setMundaneModalCost(finalCost);
    setShowMundaneModal(true);
  };

  const confirmMundaneMode = () => {
    setShowMundaneModal(false);
    navigation.navigate('MundaneHub');
  };

  const handleGreetingOptionSelect = async (option) => {
    
    if (option.action === 'partnership') {
      openPartnershipModal(option.cost);
    } else if (option.action === 'mundane') {
      openMundaneModal(option.cost);
    } else if (option.action === 'periods') {
      setShowEventPeriods(true);
    } else if (option.action === 'events') {
      navigation.navigate('EventScreen');
    } else if (option.action === 'ashtakvarga') {
      navigation.navigate('AshtakvargaOracle');
    } else if (option.action === 'muhurat') {
      navigation.navigate('MuhuratHub');
    } else if (option.action === 'numerology') {
      navigation.navigate('Numerology');
    } else if (option.action === 'analysis') {
      if (option.type === 'karma') {
        navigation.navigate('KarmaAnalysis', { chartId: birthData?.id });
      } else if (option.type === 'trading') {
        navigation.navigate('TradingDashboard');
      } else if (option.type === 'financial') {
        navigation.navigate('FinancialDashboard');
      } else if (option.type === 'childbirth') {
        navigation.navigate('ChildbirthPlanner');
      } else {
        navigation.navigate('AnalysisDetail', { 
          analysisType: option.type,
          title: `${option.type.charAt(0).toUpperCase() + option.type.slice(1)} Analysis`,
          cost: option.cost,
          originalCost: option.originalCost,
        });
      }
    } else {
      
      // First load any existing chat history
      await loadChatHistory();
      
      // Switch to chat mode immediately
      setShowGreeting(false);
      
      // Reset special modes when starting standard chat
      if (partnershipMode) {
        setPartnershipMode(false);
        setNativeChart(null);
        setPartnerChart(null);
        setPartnershipRelation('');
        setIsTypingOtherRelation(false);
        setOtherRelationText('');
        setNativeSearchQuery('');
      }
      if (isMundane) {
        setIsMundane(false);
        setMundaneContext(null);
      }
      setIsPremiumAnalysis(false);
      setShowModeSelector(false);
      
      // Set flag to scroll when content renders
      setTimeout(() => {
        if (messages.length > 0) {
          lastMessageRef.current?.measureLayout(
            scrollViewRef.current,
            (x, y) => {
              scrollViewRef.current?.scrollTo({ y: y, animated: false });
            },
            () => {}
          );
        }
      }, 50);
      
      // Check if we need to show welcome message
      setTimeout(async () => {
        
        const storedMessages = await loadMessagesFromStorage(currentPersonId);
        
        // Always show fresh welcome message when explicitly starting chat
        const nativeName = birthData?.name || 'there';
        
        let welcomeMessage;
        
        if (isMundaneRef.current) {
          welcomeMessage = {
            id: Date.now().toString(),
            content: `🌍 Welcome to Global Markets & Events Analysis!\n\nI'm ready to analyze ${mundaneContextRef.current?.event_name || 'the event'} for you using elite mundane astrology techniques.\n\nI have the charts for ${mundaneContextRef.current?.entities?.join(', ') || 'the involved parties'} and the event moment ready. Ask your question below.`,
            role: 'assistant',
            isWelcome: true,
            timestamp: new Date().toISOString(),
          };
        } else {
          welcomeMessage = {
            id: Date.now().toString(),
            content: t('chat.welcomeMessage', "🌟 Welcome {{name}}! I'm here to help you understand your birth chart and provide astrological insights.\n\nFeel free to ask me anything about:\n\n• Personality traits and characteristics\n• Career and professional guidance\n• Relationships and compatibility\n• Health and wellness insights\n• Timing for important decisions\n• Current planetary transits\n• Strengths and areas for growth\n\nWhat would you like to explore first?", { name: nativeName }),
            role: 'assistant',
            isWelcome: true,
            timestamp: new Date().toISOString(),
          };
        }
        
        // If no stored messages, show welcome. If stored messages exist, prepend welcome if it's not already there
        if (storedMessages.length === 0) {
          setMessagesWithStorage([welcomeMessage]);
        } else {
          // Check if first message is already a welcome message
          const firstMessage = storedMessages[0];
          if (!firstMessage.content.includes('Welcome')) {
            setMessagesWithStorage([welcomeMessage, ...storedMessages]);
          } else {
            // Replace old welcome with new personalized one
            const updatedMessages = [welcomeMessage, ...storedMessages.slice(1)];
            setMessagesWithStorage(updatedMessages);
          }
        }
      }, 100);
    }
  };

  const checkBirthData = async () => {
    try {
      // First try to get single birth details
      let selectedBirthData = await storage.getBirthDetails();
      
      // If no single birth details, get from profiles
      if (!selectedBirthData) {
        const profiles = await storage.getBirthProfiles();
        
        if (profiles && profiles.length > 0) {
          // Use the first profile or find 'self' relation
          selectedBirthData = profiles.find(p => p.relation === 'self') || profiles[0];
        }
      }
      
      if (selectedBirthData && selectedBirthData.name) {
        setBirthData(selectedBirthData);
      } else {
        // No local birth data: stay on Home and show empty state (Add birth profile CTA).
        // Do not auto-redirect to SelectNative/BirthForm; user can tap CTA to see BirthProfileIntro.
        setBirthData(null);
      }
    } catch (error) {
      console.error('❌ Error checking birth data:', error);
      setBirthData(null);
    }
  };

  const loadChatHistory = async () => {
  };

  const loadLanguagePreference = async () => {
    const savedLanguage = await storage.getLanguage();
    if (savedLanguage) {
      setLanguage(savedLanguage);
    }
  };

  const createSession = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      
      // Different endpoint for mundane vs personal
      const endpoint = isMundane ? '/mundane/session' : '/chat-v2/session';
      const body = isMundane ? {} : { birth_chart_id: birthData?.id };
      
      if (!isMundane && !birthData?.id) {
        Alert.alert(
          t('chat.sessionNeedsProfile', 'Profile required'),
          t(
            'chat.sessionNeedsProfileBody',
            'Save your birth profile to your account (open Birth profile and ensure it is connected) so chat can start a session.'
          )
        );
        return null;
      }
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint(endpoint)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      });
      
      if (response.ok) {
        const data = await response.json();
        const newSessionId = data.session_id;
        setSessionId(newSessionId);
        
        if (!isMundane) {
          // Track session for personal chat only
          const currentBirthHash = `${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}`;
          const personSessions = JSON.parse(await AsyncStorage.getItem(`chatSessions_${currentBirthHash}`) || '[]');
          personSessions.push(newSessionId);
          await AsyncStorage.setItem(`chatSessions_${currentBirthHash}`, JSON.stringify(personSessions));
        }
        
        return newSessionId;
      }
    } catch (error) {
      console.error('Error creating session:', error);
    }
    return null;
  };

  const saveMessageToHistory = async (message, sessionId) => {
    // This is handled by the backend when processing messages
    // No need to save manually in mobile app
    return;
  };


  const getLoadingMessages = (messageText) => {
    const lowerCaseMessage = messageText.toLowerCase();
    
    // Keywords for different categories
    const careerKeywords = ['career', 'job', 'profession', 'work', 'employment'];
    const marriageKeywords = ['marriage', 'spouse', 'partner', 'relationship', 'love'];
    const healthKeywords = ['health', 'illness', 'disease', 'wellness'];
    const financeKeywords = ['finance', 'money', 'wealth', 'investment'];
    const spiritualKeywords = ['spiritual', 'soul', 'karma', 'purpose'];

    if (careerKeywords.some(keyword => lowerCaseMessage.includes(keyword))) {
      return [
        '💼 Analyzing career prospects in your chart...',
        '🏢 Evaluating professional strengths and weaknesses...',
        '📈 Identifying key periods for career growth...',
        '🌟 Uncovering hidden talents and opportunities...',
        '🎯 Aligning your career with your life purpose...',
        '☀️ Predicting potential challenges in your professional life...',
        '✨ Providing guidance for career advancement...',
        'Congratulations on taking this important step in your career exploration! I am now examining the intricate details of your birth chart to provide you with the most accurate and personalized insights available.',
        'I am analyzing the placement of Saturn, the planet of career and responsibility, in your birth chart. This will help me understand your professional potential and challenges.',
        'I am also looking at the 10th house, which represents your career and public life. This will give me a better understanding of your professional path.',
        'Your birth chart is a unique cosmic blueprint that holds valuable information about your career. I am now decoding this information to provide you with a detailed analysis of your professional life.',
        'I am examining the placement of Jupiter, the planet of expansion and opportunities, in your birth chart. This will help me identify potential career opportunities for you.',
        'I am also looking at the 6th house, which represents your daily work and service. This will give me a better understanding of your work environment and professional relationships.',
      ];
    }
    if (marriageKeywords.some(keyword => lowerCaseMessage.includes(keyword))) {
      return [
        '💍 Assessing marital compatibility and timing...',
        '❤️ Exploring romantic connections in your chart...',
        '💑 Understanding partnership dynamics...',
        '☀️ Predicting potential challenges in your married life...',
        '✨ Providing guidance for a harmonious relationship...',
        'Now, I am delving into the complexities of your birth chart to provide you with a comprehensive analysis of your marital prospects. This is an important step in understanding your future, and I am committed to providing you with the most accurate and personalized insights available.',
        'I am analyzing the placement of Venus, the planet of love and relationships, in your birth chart. This will help me understand your romantic potential and challenges.',
        'I am also looking at the 7th house, which represents your marriage and partnerships. This will give me a better understanding of your marital path.',
        'Your birth chart is a unique cosmic blueprint that holds valuable information about your relationships. I am now decoding this information to provide you with a detailed analysis of your marital life.',
        'I am examining the placement of Jupiter, the planet of expansion and opportunities, in your birth chart. This will help me identify potential marital opportunities for you.',
      ];
    }
    if (healthKeywords.some(keyword => lowerCaseMessage.includes(keyword))) {
      return [
        '⚕️ Examining health indicators and vulnerabilities...',
        '🌿 Looking into planetary influences on your well-being...',
        '🏃‍♂️ Identifying periods for focusing on health...',
        'Congratulations on taking this important step in understanding your health from an astrological perspective. I am now examining the intricate details of your birth chart to provide you with the most accurate and personalized insights available.',
        'I am analyzing the placement of Mars, the planet of energy and vitality, in your birth chart. This will help me understand your physical potential and challenges.',
        'I am also looking at the 6th house, which represents your health and daily routines. This will give me a better understanding of your health path.',
        'Your birth chart is a unique cosmic blueprint that holds valuable information about your health. I am now decoding this information to provide you with a detailed analysis of your physical well-being.',
        'I am examining the placement of Saturn, the planet of limitations and discipline, in your birth chart. This will help me identify potential health challenges for you.',
      ];
    }
    if (financeKeywords.some(keyword => lowerCaseMessage.includes(keyword))) {
        return [
            '💰 Scrutinizing financial planets and houses...',
            '🏦 Identifying opportunities for wealth creation...',
            '💸 Analyzing potential for financial challenges...',
            'Congratulations on taking this important step in understanding your financial situation from an astrological perspective. I am now examining the intricate details of your birth chart to provide you with the most accurate and personalized insights available.',
            'I am analyzing the placement of Jupiter, the planet of expansion and opportunities, in your birth chart. This will help me identify potential financial opportunities for you.',
            'I am also looking at the 2nd house, which represents your wealth and possessions. This will give me a better understanding of your financial path.',
            'Your birth chart is a unique cosmic blueprint that holds valuable information about your finances. I am now decoding this information to provide you with a detailed analysis of your financial situation.',
            'I am examining the placement of Saturn, the planet of limitations and discipline, in your birth chart. This will help me identify potential financial challenges for you.',
        ];
    }
    if (spiritualKeywords.some(keyword => lowerCaseMessage.includes(keyword))) {
        return [
            '🧘‍♀️ Exploring your spiritual path and purpose...',
            '🕉️ Examining karmic influences and lessons...',
            '✨ Delving into your soul\'s journey...',
            'Congratulations on taking this important step in understanding your spiritual path from an astrological perspective. I am now examining the intricate details of your birth chart to provide you with the most accurate and personalized insights available.',
            'I am analyzing the placement of Neptune, the planet of spirituality and intuition, in your birth chart. This will help me understand your spiritual potential and challenges.',
            'I am also looking at the 12th house, which represents your subconscious and spiritual life. This will give me a better understanding of your spiritual path.',
            'Your birth chart is a unique cosmic blueprint that holds valuable information about your spirituality. I am now decoding this information to provide you with a detailed analysis of your spiritual journey.',
        ];
    }
    
    // Default messages
    return [
      '☀️ Analyzing your birth chart...',
      '⭐ Consulting the cosmic energies...',
      '📊 Calculating planetary positions...',
      '🌟 Interpreting astrological patterns...',
      '✨ Preparing your personalized insights...'
    ];
  };

  const pollForResponse = async (messageId, processingMessageId, currentSessionId, userQuestion = '', isResume = false) => {
    if (!messageId) {
      return;
    }
    
    const maxPolls = 120; // 4 minutes max
    let pollCount = 0;
    
    // Add to pending messages if not resuming
    if (!isResume) {
      await addPendingMessage(messageId);
    }
    
    const poll = async () => {
      const pollStartTime = new Date().toISOString();
      // console.log(`🔍 [POLL START] messageId: ${messageId}, pollCount: ${pollCount}, time: ${pollStartTime}`);
      
      try {
        const token = await AsyncStorage.getItem('authToken');
        const url = `${API_BASE_URL}${getEndpoint(`/chat-v2/status/${messageId}`)}`;
        
        // console.log(`🌐 [FETCH START] URL: ${url}, time: ${new Date().toISOString()}`);
        
        // Add timeout to prevent long-hanging requests
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
          // console.log(`⏰ [FETCH TIMEOUT] Aborting request for messageId: ${messageId} after 5 seconds`);
          controller.abort();
        }, 5000); // 5 second timeout
        
        const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${token}` },
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        // console.log(`📡 [FETCH END] Response received for messageId: ${messageId}, status: ${response.status}, time: ${new Date().toISOString()}`);
        
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const status = await response.json();
        const pollEndTime = new Date().toISOString();
        // console.log(`📊 [POLL END] messageId: ${messageId}, status: ${status.status}, pollCount: ${pollCount}, startTime: ${pollStartTime}, endTime: ${pollEndTime}`);
        
        if (status.status === 'completed') {

          const showFinalMessage = () => {
            setMessagesWithStorage(prev => {
              const processingMsg = prev.find(m => m.messageId === messageId);
              const userMsg = processingMsg?.userMessageId ? prev.find(m => m.id === processingMsg.userMessageId) : null;
              const chartName = userMsg?.native_name || null;
              const updated = prev.map(msg =>
                msg.messageId === messageId
                  ? {
                      ...msg,
                      content: status.content || 'Response received but content is empty',
                      isTyping: false,
                      terms: status.terms || [],
                      glossary: status.glossary || {},
                      message_type: status.message_type || 'answer',
                      summary_image: status.summary_image || null,
                      follow_up_questions: status.follow_up_questions || [],
                      native_name: chartName,
                      intent_gate: status.intent_gate || (status.gate_metadata && status.gate_metadata.intent_gate),
                      gate_metadata: status.gate_metadata || null,
                    }
                  : msg
              );
              return updated;
            });
            setLoading(false);
            setIsTyping(false);
            removePendingMessage(messageId);
            const gatedNoCharge = status.message_type === 'native_gate' || status.message_type === 'clarification';
            if (!gatedNoCharge) {
              fetchBalance();
            } else {
              freeUsedThisSendRef.current = false;
            }
            if (freeUsedThisSendRef.current && !gatedNoCharge) {
              freeUsedThisSendRef.current = false;
              Alert.alert(
                'Free question used',
                'You used your free question. Next questions will use credits.',
                [{ text: 'OK' }]
              );
            }
            const mt = status.message_type || 'answer';
            const body = (status.content || '').trim();
            if (!gatedNoCharge && mt !== 'clarification' && mt !== 'native_gate' && body.length >= 80) {
              setRatingEligibleMessageId(messageId);
              setPodcastPromoMessageId(messageId);
              setPodcastPromoVisible(true);
            }
          };

          showFinalMessage();
          
          return;
        }
        
        if (status.status === 'failed') {
          setMessagesWithStorage(prev => prev.map(msg => 
            msg.messageId === messageId 
              ? { ...msg, content: status.error_message || 'Analysis failed. Please try again.', isTyping: false }
              : msg
          ));
          setLoading(false);
          setIsTyping(false);
          await removePendingMessage(messageId);
          return;
        }
        
        // Still processing - continue polling
        if (status.status === 'processing') {
          console.log(`🔄 [POLL PROCESSING] messageId: ${messageId}, pollCount: ${pollCount}, continuing...`);
          
          pollCount++;
          if (pollCount < maxPolls) {
            // Use InteractionManager to ensure polling isn't blocked by UI updates
            const nextPollTime = new Date(Date.now() + 1500).toISOString();
            console.log(`⏰ [POLL SCHEDULE] Next poll for messageId: ${messageId} scheduled at: ${nextPollTime}`);
            setTimeout(() => {
              // console.log(`🔄 [POLL RETRY] messageId: ${messageId}, pollCount: ${pollCount}`);
              poll();
            }, 1500);
          } else {
            // console.log(`⏰ [POLL TIMEOUT] messageId: ${messageId} reached max polls (${maxPolls})`);
            // Timeout - show restart option
            setMessagesWithStorage(prev => prev.map(msg => 
              msg.messageId === messageId 
                ? { 
                    ...msg, 
                    content: 'Analysis is taking longer than expected. The system is still working on your request.', 
                    isTyping: false,
                    showRestartButton: true
                  }
                : msg
            ));
            setLoading(false);
            setIsTyping(false);
            // Keep in pending messages for later resume
          }
        }
        
      } catch (error) {
        console.error('❌ Polling error:', error);
        // Log to backend for admin error list (non-timeout polling failures)
        if (error.name !== 'AbortError') {
          try {
            const { chatErrorAPI } = require('../../services/api');
            await chatErrorAPI.logError(
              error.name || 'PollingError',
              error.message || 'Poll failed',
              userQuestion || `messageId: ${messageId}`,
              error.stack
            );
          } catch (logErr) {
            console.error('Failed to log polling error:', logErr);
          }
        }
        // Show user-friendly error message based on error type
        let userMessage = 'I apologize, but I\'m having trouble processing your request right now. Please try again in a moment.';
        
        // Handle specific error types
        if (error.name === 'AbortError') {
          // console.log(`⏰ [POLL TIMEOUT] Fetch timeout for messageId: ${messageId}, pollCount: ${pollCount}`);
          // Don't show error for timeout, just continue polling
          pollCount++;
          if (pollCount < maxPolls) {
            const nextPollTime = new Date(Date.now() + 1000).toISOString();
            // console.log(`🔄 [POLL RETRY AFTER TIMEOUT] Next poll for messageId: ${messageId} scheduled at: ${nextPollTime}`);
            setTimeout(() => {
              // console.log(`🔄 [POLL RETRY] messageId: ${messageId}, pollCount: ${pollCount}`);
              poll();
            }, 1000);
          } else {
            // console.log(`⏰ [POLL MAX TIMEOUT] messageId: ${messageId} reached max polls (${maxPolls})`);
            // Show timeout message
            setMessagesWithStorage(prev => prev.map(msg => 
              msg.messageId === messageId 
                ? { 
                    ...msg, 
                    content: 'Analysis is taking longer than expected. The system is still working on your request.', 
                    isTyping: false,
                    showRestartButton: true
                  }
                : msg
            ));
            setLoading(false);
            setIsTyping(false);
          }
          return;
        }
        
        setMessagesWithStorage(prev => prev.map(msg => 
          msg.messageId === messageId 
            ? { ...msg, content: userMessage, isTyping: false }
            : msg
        ));
        setLoading(false);
        setIsTyping(false);
        await removePendingMessage(messageId);
      }
    };
    
    // Start polling immediately (no delay)
    poll();
  };
  
  const restartPolling = (messageId) => {
    // Update message to show restarting
    setMessagesWithStorage(prev => prev.map(msg => 
      msg.messageId === messageId 
        ? { ...msg, content: '🔄 Checking for response...', isTyping: true, showRestartButton: false }
        : msg
    ));
    setLoading(true);
    
    // Restart polling (resume mode)
    const processingMessage = messages.find(msg => msg.messageId === messageId);
    const userMessage = messages.find(msg => msg.id === processingMessage?.userMessageId);
    pollForResponse(messageId, null, sessionId, userMessage?.content || '', true);
  };

  const sendChatRequestWithRetry = async ({
    messageText,
    currentSessionId,
    processingMessageId,
    userMessageId,
    clientRequestId,
  }) => {
    const token = await AsyncStorage.getItem('authToken');
    let activeSessionId = currentSessionId;

    const attemptSend = async (attempt = 1) => {
      try {
        // When using first question free, send as standard so backend applies free-question logic
        const useFreeQuestion = !partnershipMode && !isMundane && freeQuestionAvailable;
        
        // Prepend relationship info to question for better backend context/logging
        const finalQuestion = (partnershipMode && partnershipRelation)
          ? `[Relationship: ${partnershipRelation}] ${messageText}`
          : messageText;

        const requestBody = {
          session_id: activeSessionId,
          question: finalQuestion,
          language: language || 'english',
          response_style: 'detailed',
          premium_analysis: useFreeQuestion ? false : isPremiumAnalysis,
          native_name: partnershipMode ? nativeChart?.name : birthData?.name,
          birth_details: partnershipMode ? {
            name: nativeChart.name,
            date: typeof nativeChart.date === 'string' ? nativeChart.date.split('T')[0] : nativeChart.date,
            time: typeof nativeChart.time === 'string' ? nativeChart.time.split('T')[1]?.slice(0, 5) || nativeChart.time : nativeChart.time,
            latitude: parseFloat(nativeChart.latitude),
            longitude: parseFloat(nativeChart.longitude),
            place: nativeChart.place || '',
            gender: nativeChart.gender || ''
          } : {
            name: birthData.name,
            date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
            time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
            latitude: parseFloat(birthData.latitude),
            longitude: parseFloat(birthData.longitude),
            place: birthData.place || '',
            gender: birthData.gender || ''
          },
          // Partnership mode fields
          partnership_mode: partnershipMode,
          ...(partnershipMode && partnerChart && {
            partner_name: partnerChart.name,
            partner_date: typeof partnerChart.date === 'string' ? partnerChart.date.split('T')[0] : partnerChart.date,
            partner_time: typeof partnerChart.time === 'string' ? partnerChart.time.split('T')[1]?.slice(0, 5) || partnerChart.time : partnerChart.time,
            partner_place: partnerChart.place || '',
            partner_latitude: parseFloat(partnerChart.latitude),
            partner_longitude: parseFloat(partnerChart.longitude),
            partner_gender: partnerChart.gender || '',
            partnership_relationship: partnershipRelation
          }),
          client_request_id: clientRequestId,
        };

        console.log(`🚀 [API CALL] Sending request to /chat-v2/ask at: ${new Date().toISOString()} (attempt ${attempt})`);

        const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat-v2/ask')}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(requestBody)
        });

        console.log(`📡 [API RESPONSE] Received response at: ${new Date().toISOString()}, status: ${response.status}`);

        if (!response.ok) {
          const errorText = await response.text();
          const sessionMissing =
            response.status === 404 &&
            /session not found/i.test(errorText) &&
            attempt === 1 &&
            !isMundane;
          if (sessionMissing) {
            console.warn('🔄 Stale chat session — creating a new one and retrying once');
            setSessionId(null);
            const newSessionId = await createSession();
            if (newSessionId) {
              setSessionId(newSessionId);
              activeSessionId = newSessionId;
              return attemptSend(2);
            }
          }
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const result = await response.json();
        const { user_message_id, message_id: assistantMessageId, loading_messages, chart_insights } = result;

        console.log(`📦 [RESULT] Got messageId: ${assistantMessageId} at: ${new Date().toISOString()}`);
        console.log(`📊 [LOADING MESSAGES] Received ${loading_messages?.length || 0} dynamic messages from backend`);
        console.log(`🏠 [CHART INSIGHTS] Received ${chart_insights?.length || 0} chart insights from backend`);

        if (!assistantMessageId) {
          throw new Error('No message ID received from server');
        }

        // Native profile gate or clarification returned synchronously (no credit spend / no poll)
        if (
          result.status === 'completed' &&
          (result.message_type === 'native_gate' || result.message_type === 'clarification')
        ) {
          freeUsedThisSendRef.current = false;
          setLoading(false);
          setIsTyping(false);
          if (user_message_id) {
            setMessagesWithStorage((prev) =>
              prev.map((msg) =>
                msg.id === userMessageId ? { ...msg, messageId: user_message_id } : msg
              )
            );
          }
          setMessagesWithStorage((prev) =>
            prev.map((msg) =>
              msg.id === processingMessageId
                ? {
                    ...msg,
                    messageId: assistantMessageId,
                    content: result.content || '',
                    isTyping: false,
                    message_type: result.message_type,
                    terms: [],
                    glossary: {},
                    follow_up_questions: [],
                    chartInsights: [],
                    intent_gate: result.intent_gate || (result.gate_metadata && result.gate_metadata.intent_gate),
                    gate_metadata: result.gate_metadata || null,
                    showSendRetryButton: false,
                  }
                : msg
            )
          );
          return;
        }

        console.log(`🚀 [POLLING START] Starting polling for messageId: ${assistantMessageId} at: ${new Date().toISOString()}`);

        // Start polling IMMEDIATELY before state updates to avoid delay
        pollForResponse(assistantMessageId, processingMessageId, activeSessionId, messageText);

        // Update user message with real DB ID (async, non-blocking)
        if (user_message_id) {
          setMessagesWithStorage(prev => {
            const updated = prev.map(msg => {
              if (msg.id === userMessageId) {
                const updatedMsg = { ...msg, messageId: user_message_id };
                return updatedMsg;
              }
              return msg;
            });
            return updated;
          });
        }

        // Update processing message with messageId and chart insights
        setMessagesWithStorage(prev => {
          const updated = prev.map(msg => {
            if (msg.id === processingMessageId) {
              const updatedMsg = { ...msg, messageId: assistantMessageId, chartInsights: chart_insights, showSendRetryButton: false };
              return updatedMsg;
            }
            return msg;
          });
          return updated;
        });
      } catch (error) {
        // Only auto-retry for network-level errors
        if ((error.message?.includes('Network') || error.message?.includes('fetch')) && attempt < 3) {
          console.warn(`⚠️ Network error on attempt ${attempt}, retrying...`, error.message);
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
          return attemptSend(attempt + 1);
        }
        throw error;
      }
    };

    await attemptSend();
  };

  const sendMessage = async (messageText = inputText) => {
    if (!messageText.trim() || !birthData) {
      return;
    }
    // Gate rating prompt to the next completed answer only.
    setRatingEligibleMessageId(null);
    setRatingPromptPending(false);
    setRatingPromptMessageId(null);

    // Partnership Step 2: Relationship description
    if (partnershipMode && partnershipStep === 2) {
      setPartnershipRelation(messageText);
      setPartnershipStep(3);
      setInputText('');
      
      // Scroll to bottom
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
      return;
    } else {
      // Normal flow
      setInputText('');
    }

    setLoading(true);
    setIsTyping(true);
    setShowGreeting(false);
    
    // Remove test message code

    // Add user message immediately (include chart name for badge)
    const userMessageId = Date.now().toString();
    const chartName = partnershipMode ? nativeChart?.name : birthData?.name;
    const userMessage = {
      id: userMessageId,
      content: messageText,
      role: 'user',
      timestamp: new Date().toISOString(),
      native_name: chartName || null,
    };
    
    // Track chat message sent event
    trackAstrologyEvent.chatMessageSent('user_question');
    
    setMessagesWithStorage(prev => {
      const newMessages = [...prev, userMessage];
      return newMessages;
    });

    const loadingMessages = getLoadingMessages(messageText);

    // Add processing message immediately
    const clientRequestId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const processingMessageId = Date.now() + '_processing';
    const processingMessage = {
      id: processingMessageId,
      content: '', // Content is now handled by LoadingBubble
      role: 'assistant',
      timestamp: new Date().toISOString(),
      isTyping: true,
      userMessageId: userMessageId,
      clientRequestId,
      failedQuestion: messageText,
    };
    
    setMessagesWithStorage(prev => {
      const newMessages = [...prev, processingMessage];
      return newMessages;
    });

    // Scroll to bottom
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);

    // Create session if needed
    let currentSessionId = sessionId;
    if (!currentSessionId) {
      currentSessionId = await createSession();
      if (!currentSessionId) {
        setLoading(false);
        setIsTyping(false);
        setMessagesWithStorage(prev => prev.filter(msg => msg.id !== processingMessageId));
        Alert.alert(
          t('chat.couldNotStart', 'Could not start chat'),
          t(
            'chat.couldNotStartBody',
            'Check your connection, ensure your birth profile is saved to your account, then try again.'
          )
        );
        return;
      }
    }

    try {
      const token = await AsyncStorage.getItem('authToken');
      
      // Mundane mode - async with polling
      if (isMundane) {
        const mundaneBody = {
          session_id: currentSessionId,
          country: selectedCountry.name,
          year: selectedYear,
          latitude: selectedCountry.lat,
          longitude: selectedCountry.lng,
          question: messageText,
          // NEW: Specialized mundane context
          category: mundaneContext?.category || 'general',
          event_date: mundaneContext?.event_date,
          event_time: mundaneContext?.event_time,
          // Ref fallback: state can lag one frame behind route params when starting from MundaneHub
          entities: mundaneContext?.entities ?? mundaneContextRef.current?.entities,
        };
        
        const response = await fetch(`${API_BASE_URL}${getEndpoint('/mundane/analyze')}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(mundaneBody)
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('❌ API Error Response:', errorText);
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const result = await response.json();
        const messageId = result.message_id;
        
        if (!messageId) {
          throw new Error('No message ID received from server');
        }
        
        // Update processing message with messageId
        setMessagesWithStorage(prev => prev.map(msg => 
          msg.id === processingMessageId ? { ...msg, messageId } : msg
        ));
        
        // Start polling
        pollForResponse(messageId, processingMessageId, currentSessionId, messageText);
        return;
      }
      
      // Partnership mode validation
      if (partnershipMode && (!nativeChart || !partnerChart)) {
        Alert.alert('Error', 'Please select both charts for partnership analysis');
        setMessagesWithStorage(prev => prev.filter(msg => msg.id !== processingMessageId));
        setLoading(false);
        setIsTyping(false);
        return;
      }

      // Track if this send uses the free standard question (for post-success toast)
      if (!partnershipMode && freeQuestionAvailable) {
        freeUsedThisSendRef.current = true;
      }

      await sendChatRequestWithRetry({
        messageText,
        currentSessionId,
        processingMessageId,
        userMessageId,
        clientRequestId,
      });

    } catch (error) {
      console.error('❌ Error sending message:', error);
      
      // Log error to backend for developer monitoring
      try {
        const { chatErrorAPI } = require('../../services/api');
        await chatErrorAPI.logError(
          error.name || 'ChatError',
          error.message || 'Unknown error',
          messageText,
          error.stack
        );
      } catch (logError) {
        console.error('Failed to log error:', logError);
      }
      
      // Show user-friendly error message based on error type
      let userMessage = 'I apologize, but I\'m having trouble processing your request right now. Please try again in a moment.';
      
      // Check for specific error patterns
      if (error.message?.includes('DeadlineExceeded') || error.message?.includes('504') || error.message?.includes('timeout')) {
        userMessage = 'Your question is quite complex and is taking longer than usual to analyze. Please try asking a more specific question or try again later.';
      } else if (error.message?.includes('Network') || error.message?.includes('fetch')) {
        userMessage = 'I\'m having trouble connecting right now. Please check your internet connection and try again.';
      } else if (error.message?.includes('HTTP 500')) {
        userMessage = 'I\'m experiencing some technical difficulties. Please try again in a few moments.';
      } else if (error.message?.includes('HTTP 404') && /session not found/i.test(error.message)) {
        userMessage = 'Your chat session expired or was reset. Tap retry — we will start a fresh session.';
      }
      
      // Replace processing message with error and show retry button
      setMessagesWithStorage(prev => prev.map(msg => 
        msg.id === processingMessageId 
          ? { ...msg, content: userMessage, isTyping: false, showSendRetryButton: true, failedQuestion: messageText }
          : msg
      ));
      setLoading(false);
      setIsTyping(false);
    }
  };

  const handleSendRetry = async (failedMessage) => {
    const { clientRequestId, userMessageId, failedQuestion } = failedMessage || {};
    if (!clientRequestId || !failedQuestion) {
      return;
    }

    setLoading(true);
    setIsTyping(true);

    // Reset the failed message to typing state
    setMessagesWithStorage(prev => prev.map(msg =>
      msg.id === failedMessage.id
        ? { ...msg, isTyping: true, showSendRetryButton: false }
        : msg
    ));

    let currentSessionId = sessionId;
    if (!currentSessionId) {
      currentSessionId = await createSession();
      if (!currentSessionId) {
        setLoading(false);
        setIsTyping(false);
        Alert.alert(
          t('chat.couldNotStart', 'Could not start chat'),
          t(
            'chat.couldNotStartBody',
            'Check your connection, ensure your birth profile is saved to your account, then try again.'
          )
        );
        return;
      }
    }

    try {
      await sendChatRequestWithRetry({
        messageText: failedQuestion,
        currentSessionId,
        processingMessageId: failedMessage.id,
        userMessageId,
        clientRequestId,
      });
    } catch (error) {
      console.error('❌ Error retrying message:', error);

      // Log error to backend for developer monitoring
      try {
        const { chatErrorAPI } = require('../../services/api');
        await chatErrorAPI.logError(
          error.name || 'ChatRetryError',
          error.message || 'Unknown retry error',
          failedQuestion,
          error.stack
        );
      } catch (logError) {
        console.error('Failed to log retry error:', logError);
      }

      // Show user-friendly error message based on error type
      let userMessage = 'I apologize, but I\'m still having trouble sending your question. Please check your connection and try again.';
      if (error.message?.includes('DeadlineExceeded') || error.message?.includes('504') || error.message?.includes('timeout')) {
        userMessage = 'Your question is quite complex and is taking longer than usual to analyze. Please try asking a more specific question or try again later.';
      } else if (error.message?.includes('Network') || error.message?.includes('fetch')) {
        userMessage = 'I\'m having trouble connecting right now. Please check your internet connection and try again.';
      } else if (error.message?.includes('HTTP 500')) {
        userMessage = 'I\'m experiencing some technical difficulties. Please try again in a few moments.';
      }

      setMessagesWithStorage(prev => prev.map(msg =>
        msg.id === failedMessage.id
          ? { ...msg, content: userMessage, isTyping: false, showSendRetryButton: true, failedQuestion }
          : msg
      ));
      setLoading(false);
      setIsTyping(false);
    }
  };

  const handleLanguageChange = async (newLanguage) => {
    i18n.changeLanguage(newLanguage);
    setLanguage(newLanguage);
    await storage.setLanguage(newLanguage);
    setShowLanguageModal(false);
  };

  const shareChat = async () => {
    try {
      const chatText = messages
        .map(msg => `${msg.role === 'user' ? 'You' : 'AstroRoshni'}: ${msg.content}`)
        .join('\n\n');
      
      await Share.share({
        message: `☀️ AstroRoshni Chat\n\n${chatText}\n\nShared from AstroRoshni App`,
      });
    } catch (error) {
      console.error('Error sharing chat:', error);
    }
  };

  /** Clears local thread, resets server session id (next send creates a new session). Server Chat History entries stay as-is. */
  const performStartNewChat = () => {
    setSessionId(null);
    setLoading(false);
    setIsTyping(false);
    const nativeName = birthData?.name || 'there';
    let welcomeMessage;
    if (isMundaneRef.current) {
      welcomeMessage = {
        id: Date.now().toString(),
        content: `🌍 Welcome to Global Markets & Events Analysis!\n\nI'm ready to analyze ${mundaneContextRef.current?.event_name || 'the event'} for you using elite mundane astrology techniques.\n\nI have the charts for ${mundaneContextRef.current?.entities?.join(', ') || 'the involved parties'} and the event moment ready. Ask your question below.`,
        role: 'assistant',
        isWelcome: true,
        timestamp: new Date().toISOString(),
      };
    } else {
      welcomeMessage = {
        id: Date.now().toString(),
        content: t('chat.welcomeMessage', "🌟 Welcome {{name}}! I'm here to help you understand your birth chart and provide astrological insights.\n\nFeel free to ask me anything about:\n\n• Personality traits and characteristics\n• Career and professional guidance\n• Relationships and compatibility\n• Health and wellness insights\n• Timing for important decisions\n• Current planetary transits\n• Strengths and areas for growth\n\nWhat would you like to explore first?", { name: nativeName }),
        role: 'assistant',
        isWelcome: true,
        timestamp: new Date().toISOString(),
      };
    }
    setMessagesWithStorage([welcomeMessage]);
    setShowGreeting(false);
  };

  const confirmStartNewChat = () => {
    Alert.alert(
      t('chat.newConversationTitle', 'New conversation'),
      t('chat.newConversationMessage', 'This clears the chat on this screen and starts a fresh session on your next message. Your past threads remain in Chat History.'),
      [
        { text: t('common.cancel', 'Cancel'), style: 'cancel' },
        {
          text: t('chat.newConversationConfirm', 'Start fresh'),
          style: 'destructive',
          onPress: performStartNewChat,
        },
      ]
    );
  };

  const clearChat = confirmStartNewChat;

  const logout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await storage.clearAll();
            const { replaceWithLogin } = require('../../navigation/replaceWithLogin');
            replaceWithLogin(navigation);
          },
        },
      ]
    );
  };

  const handleDeleteMessage = async (messageIdOrLocalId) => {
    const message = messages.find(
      msg =>
        msg.messageId === messageIdOrLocalId ||
        msg.message_id === messageIdOrLocalId ||
        msg.id === messageIdOrLocalId
    );

    if (!message) {
      return;
    }
    
    // Get the actual messageId (handle both camelCase and snake_case)
    const actualMessageId = message.messageId || message.message_id;
    
    if (!actualMessageId) {
      // If no messageId, it's a local-only message, just remove from local state
      setMessagesWithStorage(prev => prev.filter(msg => msg.id !== message.id));
      return;
    }
    
    // If it's a user message (role === 'user'), just remove from local state
    if (message.role === 'user' || message.sender === 'user') {
      setMessagesWithStorage(prev => prev.filter(msg => 
        (msg.messageId !== actualMessageId && msg.message_id !== actualMessageId)
      ));
      return;
    }
    
    // If it's an assistant message, call the API to delete from server
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}${getEndpoint(`/chat-v2/message/${actualMessageId}`)}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        // Remove from local state after successful server deletion
        setMessagesWithStorage(prev => prev.filter(msg => 
          (msg.messageId !== actualMessageId && msg.message_id !== actualMessageId)
        ));
      } else if (response.status === 404) {
        // Message not found in database, remove from local state anyway
        setMessagesWithStorage(prev => prev.filter(msg => 
          (msg.messageId !== actualMessageId && msg.message_id !== actualMessageId)
        ));
      } else {
        Alert.alert('❌ Error', 'Failed to delete message from server');
      }
    } catch (error) {
      console.error('Error deleting message:', error);
      Alert.alert('❌ Error', 'Failed to delete message');
    }
  };

  const handleMessagesScroll = (e) => {
    if (!ratingPromptStateLoaded) return;
    if (ratingPromptVisible) return;
    if (ratingPromptState.completed || ratingPromptState.neverAskAgain) return;
    const y = Number(e?.nativeEvent?.contentOffset?.y || 0);
    const h = Number(e?.nativeEvent?.layoutMeasurement?.height || 0);
    const ch = Number(e?.nativeEvent?.contentSize?.height || 0);
    if (h <= 0 || ch <= 0) return;
    const nearBottom = y + h >= ch - 120;
    if (!nearBottom) return;
    const messageId = ratingEligibleMessageId;
    if (!messageId) return;
    triggerRatingPrompt(messageId, 'answer_scroll_bottom');
  };

  const renderMessage = ({ item }) => (
    <MessageBubble
      message={item}
      language={language}
      podcastAutoLaunchMessageId={podcastPromoMessageId}
      podcastAutoLaunchKey={podcastAutoLaunchKey}
    />
  );

  const renderSuggestion = ({ item }) => (
    <TouchableOpacity
      style={styles.suggestionButton}
      onPress={() => setInputText(item)}
    >
      <Text style={[styles.suggestionText, { color: colors.text }]}>{item}</Text>
    </TouchableOpacity>
  );

  const inputScopeNativeTrimmed = birthData?.name?.trim() ?? '';
  const inputScopeNativeShown =
    inputScopeNativeTrimmed.length > 7
      ? `${inputScopeNativeTrimmed.slice(0, 7)}...`
      : inputScopeNativeTrimmed;

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
      <LinearGradient
        colors={
          theme === 'dark'
            ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, '#ea580c']
            : [colors.gradientStart, colors.gradientStart, colors.gradientStart, colors.gradientStart]
        }
        style={styles.gradientBg}
      >
      <SafeAreaView
        style={styles.safeArea}
        edges={['top']}
      >
        <View style={styles.safeAreaInner}>
        {/* Header - outside KeyboardAvoidingView so home/greeting layout is never affected by keyboard */}
        <View style={styles.headerContainer}>
          <LinearGradient
            colors={theme === 'dark' 
              ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']
              : ['rgba(249, 115, 22, 0.15)', 'rgba(249, 115, 22, 0.05)']}
            style={[
              styles.header,
              {
                borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.2)',
                elevation: getCardElevation(3),
              }
            ]}
          >
            {!showGreeting && (
              <TouchableOpacity
                style={[styles.backButton, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(249, 115, 22, 0.25)' }]}
                onPress={() => {
                  setShowGreeting(true);
                  if (isMundane) {
                    setIsMundane(false);
                    setMundaneContext(null);
                  }
                  if (partnershipMode) {
                    setPartnershipMode(false);
                    setNativeChart(null);
                    setPartnerChart(null);
                    setPartnershipRelation('');
                    setIsTypingOtherRelation(false);
                    setOtherRelationText('');
                    setNativeSearchQuery('');
                  }
                  setIsPremiumAnalysis(false);
                  setShowModeSelector(false);
                }}
              >
                <Ionicons name="arrow-back" size={20} color={colors.text} />
              </TouchableOpacity>
            )}
            
            <View style={styles.headerCenter}>
              {showGreeting ? (
                <View style={{ flexDirection: 'row', alignItems: 'center', marginLeft: -16 }}>
                  <View style={styles.headerLogoContainer}>
                    <Image 
                      source={require('../../../assets/logo.png')}
                      style={styles.headerLogo}
                      resizeMode="contain"
                    />
                  </View>
                  <View>
                    <Text style={[styles.headerTitle, { color: colors.text, marginBottom: 4 }]}>AstroRoshni</Text>
                  </View>
                </View>
              ) : isMundane ? (
                <View style={styles.partnershipChipsContainer}>
                  <TouchableOpacity 
                    onPress={() => setShowCountryPicker(true)} 
                    style={[styles.nameChip, styles.compactChip]}
                  >
                    <Text style={[styles.compactChipText, { color: colors.textSecondary }]}>
                      {selectedCountry.name}
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    onPress={() => setShowYearPicker(true)} 
                    style={[styles.nameChip, styles.compactChip]}
                  >
                    <Text style={[styles.compactChipText, { color: colors.textSecondary }]}>
                      {selectedYear}
                    </Text>
                  </TouchableOpacity>
                </View>
              ) : !partnershipMode ? (
                <View style={styles.headerNativeChipWrap}>
                  {birthData ? (
                    <NativeSelectorChip
                      birthData={birthData}
                      onPress={() => navigation.navigate('SelectNative', { returnTo: 'Home' })}
                      maxLength={8}
                      showIcon={false}
                      style={styles.headerNativeChip}
                      textStyle={styles.headerNativeChipText}
                    />
                  ) : (
                    <Text style={[styles.headerTitle, { color: colors.text }]}>Chat</Text>
                  )}
                </View>
              ) : (
                <View style={styles.partnershipChipsContainer}>
                  <TouchableOpacity 
                    onPress={() => {
                      setSelectingFor('native');
                      setShowChartPicker(true);
                    }} 
                    style={[styles.nameChip, styles.nativeChip, styles.compactChip]}
                  >
                    <Text style={styles.compactChipText}>
                      {nativeChart?.name?.slice(0, 6) || 'Native'}{nativeChart?.name?.length > 6 ? '..' : ''}
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    onPress={() => {
                      setSelectingFor('partner');
                      setShowChartPicker(true);
                    }} 
                    style={[styles.nameChip, styles.partnerChip, styles.compactChip]}
                  >
                    <Text style={styles.compactChipText}>
                      {partnerChart?.name?.slice(0, 6) || 'Partner'}{partnerChart?.name?.length > 6 ? '..' : ''}
                    </Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
            
            <View style={styles.headerRight}>
              <TouchableOpacity
                style={[styles.creditButton, isPremiumAnalysis && styles.creditButtonPremium]}
                onPress={() => navigation.navigate('Credits')}
              >
                <Text style={[styles.creditText, { color: colors.text }]}>
                  {isPremiumAnalysis ? '⚡' : '💳'} {credits}
                  {effectiveChatCost === 0 && (
                    <Text style={[styles.creditText, { color: colors.primary, fontSize: 10, marginLeft: 4 }]}> · Free</Text>
                  )}
                </Text>
              </TouchableOpacity>

              {showGreeting && (
                <TouchableOpacity
                  style={styles.headerBellButton}
                  onPress={() => navigation.navigate('NudgeInbox')}
                  accessibilityRole="button"
                  accessibilityLabel="Notification history"
                >
                  {/* Fixed 40×40 box: icon + badge both live inside so nothing draws outside bounds (no clipping surprises). */}
                  <View style={styles.headerBellHitBox} pointerEvents="none">
                    <Ionicons name="notifications-outline" size={22} color={colors.text} />
                    {nudgeUnreadCount > 0 && (
                      <View style={styles.headerBellBadge}>
                        <Text
                          style={styles.headerBellBadgeText}
                          numberOfLines={1}
                          maxFontSizeMultiplier={1.35}
                          allowFontScaling
                        >
                          {nudgeUnreadCount > 99 ? '99+' : String(nudgeUnreadCount)}
                        </Text>
                      </View>
                    )}
                  </View>
                </TouchableOpacity>
              )}
              
              <TouchableOpacity
                style={styles.menuButton}
                onPress={() => {
                  if (Date.now() - menuJustClosedAt.current < 400) return;
                  setShowMenu(true);
                  Animated.spring(drawerAnim, {
                    toValue: 0,
                    useNativeDriver: true,
                    tension: 65,
                    friction: 11,
                  }).start(() => {
                    setTimeout(() => {
                      menuScrollViewRef.current?.scrollTo({ y: 0, animated: false });
                    }, 100);
                  });
                }}
              >
                <Ionicons name="menu" size={20} color={colors.text} />
              </TouchableOpacity>
            </View>
          </LinearGradient>
        </View>

        {showGreeting ? (
          <View style={{ flex: 1 }}>
            <HomeScreen 
              birthData={birthData}
              onOptionSelect={handleGreetingOptionSelect}
              navigation={navigation}
              setShowDashaBrowser={setShowDashaBrowser}
            />
          </View>
        ) : (
          <>
          <KeyboardAvoidingView
            style={styles.keyboardAvoidingView}
            enabled={false}
          >
          {partnershipMode && (
            <View style={styles.floatingBadgesContainer}>
              <TouchableOpacity 
                style={styles.floatingChangeBadge}
                onPress={() => {
                  setShowPartnershipSetupModal(true);
                }}
                activeOpacity={0.8}
              >
                <Ionicons name="create-outline" size={14} color="#ff6b35" />
                <Text style={styles.changeBadgeText}>Change Partnership</Text>
              </TouchableOpacity>

              <View style={styles.floatingPartnershipBadge}>
                <View style={styles.partnershipBadgeTextContent}>
                  <LinearGradient
                    colors={['#ec4899', '#f472b6']}
                    style={styles.partnershipBadgeGradient}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                  >
                    <Text style={[styles.partnershipBadgeText, { color: COLORS.white }]}>👥 Partnership Mode</Text>
                  </LinearGradient>
                </View>
                <TouchableOpacity 
                  style={styles.partnershipBadgeClose}
                  onPress={() => {
                    setPartnershipMode(false);
                    setIsPremiumAnalysis(false);
                    setShowModeSelector(false);
                    setNativeChart(null);
                    setPartnerChart(null);
                    setPartnershipRelation('');
                    setIsTypingOtherRelation(false);
                    setOtherRelationText('');
                    setNativeSearchQuery('');
                  }}
                >
                  <Ionicons name="close" size={18} color="#f472b6" />
                </TouchableOpacity>
              </View>
            </View>
          )}
          <GHScrollView 
            ref={scrollViewRef}
            style={styles.messagesContainer}
            contentContainerStyle={styles.messagesContent}
            showsVerticalScrollIndicator={false}
            onScroll={handleMessagesScroll}
            scrollEventThrottle={120}
            keyboardShouldPersistTaps="handled"
            keyboardDismissMode="none"
            {...(Platform.OS === 'ios'
              ? {
                  contentInsetAdjustmentBehavior: 'never',
                  removeClippedSubviews: false,
                }
              : {})}
          >
            {/* Calibration Card - COMMENTED OUT */}
            {/* {calibrationEvent && !calibrationEvent.verified && (
              <CalibrationCard 
                data={calibrationEvent}
                onConfirm={() => handleCalibrationConfirm(calibrationEvent)}
                onReject={() => handleCalibrationReject(calibrationEvent)}
              />
            )} */}
            
            {/* Signs Display – only for native-centric chat, not Global Markets (mundane) */}
            {birthData && !isMundane && (
              <View style={styles.signsContainer}>
                <LinearGradient
                  colors={Platform.OS === 'android'
                    ? (theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.1)'] : ['rgba(249, 115, 22, 0.15)', 'rgba(249, 115, 22, 0.1)'])
                    : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.15)', 'rgba(249, 115, 22, 0.08)'])}
                  style={styles.signsGradient}
                >
                  <Text style={[styles.signsTitle, { color: colors.text }]}>✨ {t('chat.chartEssence', "{{name}}'s Chart Essence", { name: birthData.name })}</Text>
                  <View style={styles.signsRow}>
                    <View style={styles.signItem}>
                      <Text style={[styles.signLabel, { color: colors.textSecondary }]}>☀️ {t('home.signs.sun', 'Sun')}</Text>
                      <Text style={[styles.signValue, { color: colors.text }]}>
                        {loadingChart ? '...' : (chartData?.planets?.Sun ? `${getSignIcon(chartData.planets.Sun.sign)} ${getSignName(chartData.planets.Sun.sign)}` : '...')}
                      </Text>
                    </View>
                    <View style={styles.signItem}>
                      <Text style={[styles.signLabel, { color: colors.textSecondary }]}>🌙 {t('home.signs.moon', 'Moon')}</Text>
                      <Text style={[styles.signValue, { color: colors.text }]}>
                        {loadingChart ? '...' : (chartData?.planets?.Moon ? `${getSignIcon(chartData.planets.Moon.sign)} ${getSignName(chartData.planets.Moon.sign)}` : '...')}
                      </Text>
                    </View>
                    <View style={styles.signItem}>
                      <Text style={[styles.signLabel, { color: colors.textSecondary }]}>⬆️ {t('home.signs.ascendant', 'Ascendant')}</Text>
                      <Text style={[styles.signValue, { color: colors.text }]}>
                        {loadingChart ? '...' : (chartData?.houses?.[0] ? `${getSignIcon(chartData.houses[0].sign)} ${getSignName(chartData.houses[0].sign)}` : '...')}
                      </Text>
                    </View>
                  </View>
                  
                  {/* Current Running Dashas */}
                  {dashaData && (
                    <Animated.View style={[styles.dashaSection, { opacity: fadeAnim }]}>
                      <GHFlatList
                        horizontal
                        showsHorizontalScrollIndicator={false}
                        data={[
                          dashaData.maha_dashas?.find(d => d.current),
                          dashaData.antar_dashas?.find(d => d.current),
                          dashaData.pratyantar_dashas?.find(d => d.current),
                          dashaData.sookshma_dashas?.find(d => d.current),
                          dashaData.prana_dashas?.find(d => d.current)
                        ].filter(Boolean)}
                        keyExtractor={(item, index) => index.toString()}
                        renderItem={({ item: dasha }) => {
                          if (!dasha || !dasha.planet || !dasha.start || !dasha.end) return null;
                          const planetColor = getPlanetColor(dasha.planet);
                          const startDateObj = new Date(dasha.start);
                          const endDateObj = new Date(dasha.end);
                          const startDate = !isNaN(startDateObj.getTime()) ? startDateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' }) : '...';
                          const endDate = !isNaN(endDateObj.getTime()) ? endDateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' }) : '...';
                          return (
                            <TouchableOpacity 
                              style={[
                                styles.dashaChip,
                                {
                                  backgroundColor: theme === 'dark' ? planetColor + '40' : planetColor + '60',
                                  borderColor: planetColor,
                                  borderWidth: 2,
                                },
                              ]}
                              onPress={() => setShowDashaBrowser(true)}
                              activeOpacity={0.8}
                            >
                              <Text style={[styles.dashaChipPlanet, { color: theme === 'dark' ? planetColor : '#1a1a1a' }]}>{t(`home.planet_names.${dasha.planet}`, dasha.planet)}</Text>
                              <Text style={[styles.dashaChipDates, { color: colors.textSecondary }]}>{startDate}</Text>
                              <Text style={[styles.dashaChipDates, { color: colors.textSecondary }]}>{endDate}</Text>
                            </TouchableOpacity>
                          );
                        }}
                        contentContainerStyle={styles.dashaFlatListContent}
                        snapToInterval={cardWidth + 8}
                        decelerationRate="fast"
                        pagingEnabled={false}
                      />
                    </Animated.View>
                  )}
                </LinearGradient>
              </View>
            )}
            

            
            {messages.map((item, index) => {
              const isLastMessage = index === messages.length - 1;

              if (item.isTyping) {
                return (
                  <View key={item.id} ref={isLastMessage ? lastMessageRef : null}>
                    <LoadingBubble 
                      chartInsights={item.chartInsights}
                      chartData={chartData}
                      scrollViewRef={scrollViewRef}
                    />
                  </View>
                );
              }

              // Render Partnership Setup Card
              if (item.setupType === 'partnership' && partnershipMode) {
                return (
                  <View key={item.id} style={{ marginBottom: 16 }}>
                    <LinearGradient
                      colors={['rgba(255, 107, 53, 0.1)', 'rgba(249, 115, 22, 0.05)']}
                      style={{ borderRadius: 16, padding: 16, borderWidth: 1, borderColor: 'rgba(255, 107, 53, 0.2)' }}
                    >
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                        <View style={{ backgroundColor: '#ff6b3520', padding: 8, borderRadius: 12 }}>
                          <Text style={{ fontSize: 18 }}>🤝</Text>
                        </View>
                        <View>
                          <Text style={{ color: colors.text, fontWeight: '700', fontSize: 16 }}>Partnership Analysis</Text>
                          <Text style={{ color: colors.textSecondary, fontSize: 12 }}>Setup complete</Text>
                        </View>
                      </View>
                      <TouchableOpacity 
                        style={{ backgroundColor: '#ff6b3520', paddingVertical: 10, borderRadius: 12, alignItems: 'center', marginTop: 8 }}
                        onPress={() => setShowPartnershipSetupModal(true)}
                      >
                        <Text style={{ color: '#ff6b35', fontWeight: '700', fontSize: 13 }}>Edit Setup ✏️</Text>
                      </TouchableOpacity>
                    </LinearGradient>
                  </View>
                );
              }

              return (
                <View key={item.id}>
                  <View ref={isLastMessage ? lastMessageRef : null}>
                    <MessageBubble
                      message={item}
                      language={language}
                      onFollowUpClick={setInputText}
                      partnership={partnershipMode}
                      onDelete={handleDeleteMessage}
                      onRestart={restartPolling}
                      onSendRetry={handleSendRetry}
                      onStartNewChat={confirmStartNewChat}
                      sessionId={sessionId}
                      podcastAutoLaunchMessageId={podcastPromoMessageId}
                      podcastAutoLaunchKey={podcastAutoLaunchKey}
                    />
                    
                    {/* OLD Partnership Chart Selector UI - REMOVED since we have the Card above */}
                  </View>
                  <FeedbackComponent 
                    message={item} 
                    onFeedbackSubmitted={(messageId, rating) => {
                      console.log('Feedback submitted:', messageId, rating);
                    }}
                  />
                </View>
              );
            })}
          </GHScrollView>

        {/* Suggestions + Input: lift by keyboard frame when open (Android needs this with edge-to-edge). */}
        <View
          style={{
          backgroundColor: 'transparent',
          paddingTop: 12,
          marginHorizontal: -12,
          paddingHorizontal: 12,
          paddingBottom: keyboardBottomInset > 0 ? keyboardBottomInset + 20 : 0,
        }}
        >
        {/* Suggestions (only show when not loading and not showing greeting) */}
        {!loading && !showGreeting && messages.length > 0 && (
          <View style={styles.suggestionsContainer}>
            <GHScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.suggestionsContent}
              keyboardShouldPersistTaps="handled"
            >
              {suggestions.slice(0, 3).map((item, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.suggestionChip}
                  onPress={() => setInputText(item)}
                >
                  <LinearGradient
                    colors={['rgba(255, 107, 53, 0.1)', 'rgba(255, 107, 53, 0.03)']}
                    style={styles.suggestionChipGradient}
                  >
                    <Text style={[styles.suggestionChipText, { color: colors.text }]}>{item}</Text>
                  </LinearGradient>
                </TouchableOpacity>
              ))}
            </GHScrollView>
          </View>
        )}



        {/* Unified Input Bar */}
        {!showGreeting && (
          <View style={styles.unifiedInputContainer}>
            {!partnershipMode && !isMundane && birthData && (
              <Text
                style={[styles.chatInputScopeHint, { color: colors.textSecondary }]}
                maxFontSizeMultiplier={1.35}
              >
                {t('chat.inputScopeAskAbout', 'Ask about')}{' '}
                <Text
                  style={[styles.chatInputScopeName, { color: colors.text }]}
                  accessibilityLabel={
                    inputScopeNativeTrimmed.length > 7
                      ? inputScopeNativeTrimmed
                      : undefined
                  }
                >
                  {inputScopeNativeTrimmed
                    ? inputScopeNativeShown
                    : t('chat.yourChart', 'your chart')}
                </Text>
                {' '}
                {t('chat.inputScopeOr', 'or')}{' '}
                <Text
                  onPress={() => navigation.navigate('SelectNative')}
                  style={[styles.chatInputScopeLink, { color: colors.primary }]}
                  accessibilityRole="link"
                  accessibilityLabel={t('chat.selectNativeA11y', 'Select or create another birth chart')}
                >
                  {t(
                    'chat.inputScopeSelectChart',
                    'select or create another birth chart'
                  )}
                </Text>
              </Text>
            )}
            <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.15)', 'rgba(0, 0, 0, 0.05)'] : ['rgba(249, 115, 22, 0.04)', 'rgba(249, 115, 22, 0.02)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.08)', 'rgba(255, 255, 255, 0.03)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
              style={[
                styles.inputBarGradient,
                {
                  borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.12)' : 'rgba(249, 115, 22, 0.2)',
                }
              ]}
            >
              {/* Expanded row to the left: Standard | Premium with cost/discount (only when not partnership/mundane) */}
              {!partnershipMode && !isMundane && showModeSelector && (
                <View style={styles.modeSelectorExpanded}>
                  <TouchableOpacity
                    style={[
                      styles.modeSelectorPill,
                      !isPremiumAnalysis && styles.modeSelectorPillActive,
                      !isPremiumAnalysis && { backgroundColor: theme === 'dark' ? 'rgba(255, 107, 53, 0.35)' : 'rgba(255, 107, 53, 0.25)' },
                      isPremiumAnalysis && { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)' },
                    ]}
                    onPress={() => { setIsPremiumAnalysis(false); setShowModeSelector(false); }}
                  >
                    <Text style={[styles.modeSelectorLabel, { color: colors.text }]}>Standard</Text>
                    <View style={styles.modeSelectorCostRow}>
                      {chatCostOriginal != null && chatCostOriginal > chatCost ? (
                        <>
                          <Text style={[styles.modeSelectorCostOriginal, { color: colors.textSecondary }]}>{chatCostOriginal}</Text>
                          <Text style={[styles.modeSelectorCost, { color: colors.text }]}>{chatCost}</Text>
                        </>
                      ) : (
                        <Text style={[styles.modeSelectorCost, { color: colors.text }]}>{chatCost}</Text>
                      )}
                      <Text style={[styles.modeSelectorCreditLabel, { color: colors.textSecondary }]}> credit{chatCost !== 1 ? 's' : ''}</Text>
                    </View>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[
                      styles.modeSelectorPill,
                      isPremiumAnalysis && styles.modeSelectorPillActivePremium,
                      isPremiumAnalysis && { backgroundColor: theme === 'dark' ? 'rgba(255, 215, 0, 0.25)' : 'rgba(255, 215, 0, 0.2)' },
                      !isPremiumAnalysis && { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)' },
                    ]}
                    onPress={() => { setIsPremiumAnalysis(true); setShowModeSelector(false); }}
                  >
                    <Text style={[styles.modeSelectorLabel, { color: colors.text }]}>Premium</Text>
                    <View style={styles.modeSelectorCostRow}>
                      {premiumChatCostOriginal != null && premiumChatCostOriginal > premiumChatCost ? (
                        <>
                          <Text style={[styles.modeSelectorCostOriginal, { color: colors.textSecondary }]}>{premiumChatCostOriginal}</Text>
                          <Text style={[styles.modeSelectorCost, { color: colors.text }]}>{premiumChatCost}</Text>
                        </>
                      ) : (
                        <Text style={[styles.modeSelectorCost, { color: colors.text }]}>{premiumChatCost}</Text>
                      )}
                      <Text style={[styles.modeSelectorCreditLabel, { color: colors.textSecondary }]}> credit{premiumChatCost !== 1 ? 's' : ''}</Text>
                    </View>
                  </TouchableOpacity>
                </View>
              )}

              <TextInput
                key="chat-main-input"
                style={[
                  styles.modernTextInput,
                  { color: colors.text },
                  showModeSelector && styles.modernTextInputCollapsed
                ]}
                value={inputText}
                onChangeText={setInputText}
                placeholder={
                  loading ? "Analyzing..." :
                  freeQuestionRequiresNotifications && !partnershipMode && !isMundane && !isPremiumAnalysis && credits < effectiveChatCost
                    ? "Turn on notifications to unlock your free question"
                  : credits < effectiveChatCost ? "Insufficient credits" :
                  partnershipMode && (partnershipStep === 0 || partnershipStep === 1) ? "Select a chart above..." :
                  partnershipMode && partnershipStep === 2 ? "Describe the relationship..." :
                  partnershipMode && partnershipStep === 3 ? "Click 'Ready' button above..." :
                  showModeSelector ? "Type here..." : 
                  isMundane ? "Ask about markets, politics, events..." : 
                  t('chat.inputPlaceholderShort', 'Type your question...')
                }
                placeholderTextColor={theme === 'dark' ? "rgba(255, 255, 255, 0.5)" : "rgba(0, 0, 0, 0.4)"}
                maxLength={500}
                editable={!loading && credits >= effectiveChatCost && !(partnershipMode && (partnershipStep === 0 || partnershipStep === 1 || partnershipStep === 3))}
                multiline
                blurOnSubmit={false}
              />

              {!partnershipMode && !isMundane && (
                <TouchableOpacity
                  style={styles.premiumToggleButton}
                  onPress={() => setShowModeSelector(prev => !prev)}
                  onLongPress={() => setShowPremiumModal(true)}
                >
                  <Animated.View
                    style={[
                      styles.premiumToggleIcon,
                      isPremiumAnalysis && {
                        transform: [{
                          scale: glowAnim.interpolate({
                            inputRange: [0, 1],
                            outputRange: [1, 1.15],
                          }),
                        }],
                      },
                    ]}
                  >
                    {isPremiumAnalysis ? (
                      <LinearGradient
                        colors={['#ffd700', '#ff6b35']}
                        style={styles.premiumIconGradient}
                      >
                        <Text style={styles.premiumIconText}>P</Text>
                      </LinearGradient>
                    ) : (
                      <View style={styles.premiumIconInactive}>
                        <Text style={styles.premiumIconTextInactive}>S</Text>
                      </View>
                    )}
                  </Animated.View>
                </TouchableOpacity>
              )}

              <TouchableOpacity
                style={[
                  styles.modernSendButton,
                  (loading || !inputText.trim() || credits < effectiveChatCost || (partnershipMode && (partnershipStep === 0 || partnershipStep === 1 || partnershipStep === 3))) && styles.modernSendButtonDisabled
                ]}
                onPress={() => sendMessage()}
                disabled={loading || !inputText.trim() || credits < effectiveChatCost || (partnershipMode && (partnershipStep === 0 || partnershipStep === 1 || partnershipStep === 3))}
              >
                <LinearGradient
                  colors={isPremiumAnalysis ? ['#ffd700', '#ff6b35'] : ['#ff6b35', '#ff8c5a']}
                  style={styles.modernSendGradient}
                >
                  {loading ? (
                    <Text style={styles.modernSendText}>⏳</Text>
                  ) : credits < effectiveChatCost ? (
                    <Text style={styles.modernSendText}>💳</Text>
                  ) : effectiveChatCost === 0 ? (
                    <Text style={styles.modernSendText}>Free</Text>
                  ) : (
                    <Ionicons name="send" size={20} color={COLORS.white} />
                  )}
                </LinearGradient>
              </TouchableOpacity>
            </LinearGradient>
            
            {effectiveChatCost === 0 && !isKeyboardVisible && (
              <View style={styles.firstQuestionFreeBanner}>
                <Text style={styles.firstQuestionFreeIcon}>🎁</Text>
                <View style={styles.firstQuestionFreeTextWrap}>
                  <Text style={styles.firstQuestionFreeTitle}>First question free</Text>
                  <Text style={styles.firstQuestionFreeSubtext}>Ask anything — no credits needed</Text>
                </View>
              </View>
            )}
            
            {freeQuestionRequiresNotifications && !partnershipMode && !isMundane && !isPremiumAnalysis && credits < effectiveChatCost && !isKeyboardVisible && (
              <TouchableOpacity
                style={styles.notifGateBanner}
                onPress={openNotificationsForFreeQuestion}
                activeOpacity={0.85}
              >
                <Text style={styles.notifGateText}>
                  🔔 Turn on notifications to use your free first question — tap here
                </Text>
              </TouchableOpacity>
            )}

            {credits < effectiveChatCost && !freeQuestionRequiresNotifications && !isKeyboardVisible && (
              <TouchableOpacity 
                style={styles.lowCreditBanner}
                onPress={() => navigation.navigate('Credits')}
              >
                <Text style={styles.lowCreditText}>💳 Get more credits to continue</Text>
              </TouchableOpacity>
            )}
            
            {showPremiumTooltip && !isPremiumAnalysis && !partnershipMode && !isMundane && !isKeyboardVisible && (
              <View style={styles.premiumTooltip}>
                <TouchableOpacity 
                  style={styles.tooltipClose}
                  onPress={() => {
                    console.log('❌ Tooltip closed');
                    tooltipResetRef.current = true;
                    setShowPremiumTooltip(false);
                  }}
                >
                  <Text style={styles.tooltipCloseText}>✕</Text>
                </TouchableOpacity>
                <Text style={styles.tooltipText}>⚡ Premium Analysis</Text>
                <Text style={styles.tooltipSubtext}>Get deeper insights</Text>
                <TouchableOpacity 
                  style={styles.tooltipButton}
                  onPress={() => {
                    console.log('💡 Learn More clicked');
                    tooltipResetRef.current = true;
                    setShowPremiumTooltip(false);
                    setShowPremiumModal(true);
                  }}
                >
                  <Text style={styles.tooltipButtonText}>Learn More</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        )}
        </View>
        </KeyboardAvoidingView>

        {/* Quick Actions Bar - hide while keyboard is open so input isn't sandwiched above system keyboard */}
        {!showGreeting && !isKeyboardVisible && (
          <View style={[styles.quickActionsBar, { paddingBottom: Math.max(8, insets.bottom) }]}>
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => setShowLanguageModal(true)}
            >
              <Ionicons name="language-outline" size={18} color={colors.text} />
              <Text style={[styles.quickActionText, { color: colors.text }]}>{t('quickActions.language')}</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => navigation.navigate('Chart', { birthData })}
            >
              <Ionicons name="pie-chart-outline" size={18} color={colors.text} />
              <Text style={[styles.quickActionText, { color: colors.text }]}>{t('quickActions.chart')}</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => setShowDashaBrowser(true)}
            >
              <Ionicons name="time-outline" size={18} color={colors.text} />
              <Text style={[styles.quickActionText, { color: colors.text }]}>{t('quickActions.dasha')}</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.quickActionButton, partnershipMode && styles.quickActionButtonActive]}
              onPress={() => {
                if (!partnershipMode) {
                  openPartnershipModal(partnershipCost);
                } else {
                  setPartnershipMode(false);
                  setNativeChart(null);
                  setPartnerChart(null);
                }
              }}
            >
              <Ionicons name="people-outline" size={18} color={colors.text} />
              <Text style={[styles.quickActionText, { color: colors.text }]}>{t('quickActions.partner')}</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => navigation.navigate('ChatHistory')}
            >
              <Ionicons name="chatbubbles-outline" size={18} color={colors.text} />
              <Text style={[styles.quickActionText, { color: colors.text }]}>{t('quickActions.history')}</Text>
            </TouchableOpacity>
          </View>
        )}
        </>
        )}

        {/* Language Modal – closes only via close button */}
        <Modal
          visible={showLanguageModal}
          transparent
          animationType="slide"
          onRequestClose={() => setShowLanguageModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>🌐 {t('languageModal.title')}</Text>
              <ScrollView
                style={styles.languageModalScrollView}
                contentContainerStyle={styles.languageModalScrollContent}
                showsVerticalScrollIndicator={true}
                keyboardShouldPersistTaps="handled"
              >
                {LANGUAGES.map((lang) => (
                  <TouchableOpacity
                    key={lang.code}
                    style={[
                      styles.languageOption,
                      language === lang.code && styles.languageOptionSelected
                    ]}
                    onPress={() => handleLanguageChange(lang.code)}
                  >
                    <Text style={styles.languageText}>
                      {lang.flag} {lang.name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
              <TouchableOpacity
                style={styles.modalCloseButton}
                onPress={() => setShowLanguageModal(false)}
              >
                <Text style={styles.modalCloseText}>{t('languageModal.close')}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>

        {/* Menu Drawer */}
        <Modal
          visible={showMenu}
          transparent
          animationType="fade"
          onRequestClose={() => {
            Animated.timing(drawerAnim, {
              toValue: 300,
              duration: 250,
              useNativeDriver: true,
            }).start(() => {
              menuJustClosedAt.current = Date.now();
              setShowMenu(false);
            });
          }}
        >
          <TouchableOpacity 
            style={styles.drawerOverlay} 
            activeOpacity={1}
            onPress={() => {
              Animated.timing(drawerAnim, {
                toValue: 300,
                duration: 250,
                useNativeDriver: true,
              }).start(() => {
                menuJustClosedAt.current = Date.now();
                setShowMenu(false);
              });
            }}
          >
            <Animated.View 
              style={[styles.drawerContent, {
                transform: [{ translateX: drawerAnim }]
              }]}
              onStartShouldSetResponder={() => true}
            >
              <LinearGradient
                colors={theme === 'dark' ? ['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35'] : ['#fefcfb', '#fefcfb', '#fefcfb', '#fefcfb']}
                style={styles.drawerGradient}
              >
                <View style={styles.drawerHeader}>
                  <Animated.View style={[styles.logoContainer, {
                    shadowOpacity: menuLogoGlow.interpolate({
                      inputRange: [0, 1],
                      outputRange: [0.6, 1],
                    }),
                    shadowRadius: menuLogoGlow.interpolate({
                      inputRange: [0, 1],
                      outputRange: [12, 20],
                    }),
                    transform: [{
                      scale: menuLogoGlow.interpolate({
                        inputRange: [0, 1],
                        outputRange: [1, 1.05],
                      })
                    }]
                  }]}>
                    <Image 
                      source={require('../../../assets/logo.png')}
                      style={styles.logoImage}
                      resizeMode="contain"
                    />
                  </Animated.View>
                  <Text style={[styles.drawerTitle, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.title')}</Text>
                  <Text style={[styles.drawerSubtitle, { color: theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : 'rgba(31, 41, 55, 0.7)' }]}>{t('menu.subtitle')}</Text>
                </View>

                <GHScrollView 
                  ref={menuScrollViewRef}
                  style={styles.menuScrollView}
                  contentContainerStyle={styles.menuScrollContent}
                  showsVerticalScrollIndicator={false}
                  nestedScrollEnabled={true}
                >
                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('Profile');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>✨</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.myProfile')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('SelectNative');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>👤</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.selectNative')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('BirthForm');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>➕</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.newNative')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('Chart', { birthData });
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>📊</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.viewChart')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        setShowDashaBrowser(true);
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>⏰</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.dashaBrowser')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('AshtakvargaOracle');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#9C27B0', '#E91E63']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>⊞</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.ashtakvarga')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('Shadbala', { birthData });
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#FF6B35', '#FFA500']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>⚖️</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.shadbala')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>


                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('KotaChakra', { birthChartId: birthData?.id });
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#795548', '#8D6E63']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🏰</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.kotaChakra')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('Yogas');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#8b5cf6', '#6366f1']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🧘</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.yogas')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        if (birthData) {
                            navigation.navigate('KPSystem', { birthDetails: birthData });
                        }
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#10b981', '#34d399']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🔢</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.kpSystem')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('AnalysisHub');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🧘</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.lifeAnalysis')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('KarmaAnalysis', { chartId: birthData?.id });
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#667eea', '#764ba2']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🕉️</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.pastLifeRegression')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('Numerology');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#667eea', '#764ba2']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🔢</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.numerology')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('ChatHistory');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#667eea', '#764ba2']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>💬</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.chatHistory')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  {!showGreeting && (
                    <TouchableOpacity
                      style={getMenuOptionStyle()}
                      onPress={() => {
                        Animated.timing(drawerAnim, {
                          toValue: 300,
                          duration: 250,
                          useNativeDriver: true,
                        }).start(() => {
                          menuJustClosedAt.current = Date.now();
                          setShowMenu(false);
                          confirmStartNewChat();
                        });
                      }}
                    >
                      <LinearGradient
                        colors={Platform.OS === 'android'
                          ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                          : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                        style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                      >
                        <View style={styles.menuIconContainer}>
                          <LinearGradient
                            colors={['#ff6b35', '#ff8c5a']}
                            style={styles.menuIconGradient}
                          >
                            <Text style={styles.menuEmoji}>🔁</Text>
                          </LinearGradient>
                        </View>
                        <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.newConversation', 'New conversation')}</Text>
                        <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                      </LinearGradient>
                    </TouchableOpacity>
                  )}

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('PodcastHistory');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🎙️</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.podcastHistory', 'Podcast History')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  {!isMundane && !showGreeting && (
                    <TouchableOpacity
                      style={getMenuOptionStyle()}
                      onPress={() => {
                        if (!partnershipMode) {
                          openPartnershipModal(partnershipCost);
                          Animated.timing(drawerAnim, {
                            toValue: 300,
                            duration: 250,
                            useNativeDriver: true,
                          }).start(() => setShowMenu(false));
                        } else {
                          setPartnershipMode(false);
                          setNativeChart(null);
                          setPartnerChart(null);
                          Animated.timing(drawerAnim, {
                            toValue: 300,
                            duration: 250,
                            useNativeDriver: true,
                          }).start(() => {
                            menuJustClosedAt.current = Date.now();
                            setShowMenu(false);
                          });
                        }
                      }}
                    >
                      <LinearGradient
                        colors={partnershipMode 
                          ? (Platform.OS === 'android' ? ['rgba(147, 51, 234, 0.3)', 'rgba(147, 51, 234, 0.15)'] : ['rgba(147, 51, 234, 0.3)', 'rgba(147, 51, 234, 0.1)'])
                          : (Platform.OS === 'android' 
                            ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                            : (theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.2)', 'rgba(249, 115, 22, 0.1)']))}
                        style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                      >
                        <View style={styles.menuIconContainer}>
                          <LinearGradient
                            colors={partnershipMode ? ['#9333ea', '#a855f7'] : ['#ff6b35', '#ff8c5a']}
                            style={styles.menuIconGradient}
                          >
                            <Text style={styles.menuEmoji}>👥</Text>
                          </LinearGradient>
                        </View>
                        <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t(partnershipMode ? 'menu.partnershipOn' : 'menu.partnershipOff')}</Text>
                        <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                      </LinearGradient>
                    </TouchableOpacity>
                  )}

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('BlogList');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#6366f1', '#8b5cf6']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>📚</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.blog')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('Credits');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff6b35', '#ff8c5a']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>💳</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.credits')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={getMenuOptionStyle()}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        navigation.navigate('Support');
                      });
                    }}
                  >
                    <LinearGradient
                      colors={Platform.OS === 'android'
                        ? (theme === 'dark' ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])
                        : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.2)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#0ea5e9', '#38bdf8']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>💬</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ffffff' : '#1f2937' }]}>{t('menu.support')}</Text>
                      <Ionicons name="chevron-forward" size={20} color={theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(31, 41, 55, 0.6)'} />
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[getMenuOptionStyle(), styles.menuOptionLast]}
                    onPress={() => {
                      Animated.timing(drawerAnim, {
                        toValue: 300,
                        duration: 250,
                        useNativeDriver: true,
                      }).start(() => {
                        setShowMenu(false);
                        logout();
                      });
                    }}
                  >
                    <LinearGradient
                      colors={['rgba(255, 59, 48, 0.2)', 'rgba(255, 59, 48, 0.1)']}
                      style={[styles.menuGradient, { borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.3)' }]}
                    >
                      <View style={styles.menuIconContainer}>
                        <LinearGradient
                          colors={['#ff3b30', '#ff6b60']}
                          style={styles.menuIconGradient}
                        >
                          <Text style={styles.menuEmoji}>🚪</Text>
                        </LinearGradient>
                      </View>
                      <Text style={[styles.menuText, { color: theme === 'dark' ? '#ff6b60' : '#dc2626' }]}>{t('menu.logout')}</Text>
                      <Ionicons name="chevron-forward" size={20} color="rgba(255, 107, 96, 0.6)" />
                    </LinearGradient>
                  </TouchableOpacity>
                </GHScrollView>
              </LinearGradient>
            </Animated.View>
          </TouchableOpacity>
        </Modal>



        {/* Event Periods Modal */}
        {showEventPeriods && (
          <EventPeriods 
            visible={showEventPeriods} 
            onClose={() => {
              setShowEventPeriods(false);
            }}
            birthData={birthData}
            onPeriodSelect={(period) => {
              setShowEventPeriods(false);
              setShowGreeting(false);
              const startDate = period.start_date ? new Date(period.start_date) : null;
              const endDate = period.end_date ? new Date(period.end_date) : null;
              const startDateStr = (startDate && !isNaN(startDate.getTime())) ? startDate.toLocaleDateString() : '...';
              const endDateStr = (endDate && !isNaN(endDate.getTime())) ? endDate.toLocaleDateString() : '...';
              const periodQuestion = `Tell me more about the period from ${startDateStr} to ${endDateStr} when ${period.transit_planet} activates ${period.natal_planet}. What specific events should I expect?`;
              sendMessage(periodQuestion);
            }}
          />
        )}

        {/* Dasha Browser Modal */}
        <CascadingDashaBrowser 
          visible={showDashaBrowser} 
          onClose={() => setShowDashaBrowser(false)}
          birthData={birthData}
          onRequireBirthData={() => navigation.navigate('BirthProfileIntro', { returnTo: 'Home' })}
        />

        {/* Enhanced Analysis Popup */}
        <Modal
          visible={showEnhancedPopup}
          transparent
          animationType="fade"
          onRequestClose={() => setShowEnhancedPopup(false)}
        >
          <View style={styles.enhancedPopupOverlay}>
            <View style={styles.enhancedPopup}>
              <TouchableOpacity 
                style={styles.popupClose}
                onPress={() => setShowEnhancedPopup(false)}
              >
                <Text style={styles.popupCloseText}>×</Text>
              </TouchableOpacity>
              
              <View style={styles.popupHeader}>
                <LinearGradient
                  colors={['#ff6b35', '#ff8c5a', '#ffd700']}
                  style={styles.popupHeaderGradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                />
                <View style={styles.popupHeaderContent}>
                  <View style={styles.popupIconContainer}>
                    <LinearGradient
                      colors={['#ffd700', '#ffed4e']}
                      style={styles.popupIconGradient}
                    >
                      <Text style={styles.popupIcon}>✨</Text>
                    </LinearGradient>
                  </View>
                  <Text style={styles.popupTitle}>Enhanced Deep Analysis</Text>
                  <Text style={styles.popupSubtitle}>Unlock Advanced Cosmic Insights</Text>
                </View>
              </View>
              
              <GHScrollView 
                style={styles.popupContent}
                contentContainerStyle={styles.popupContentContainer}
                showsVerticalScrollIndicator={false}
              >
                <Text style={styles.popupIntro}>
                  Experience the most sophisticated astrological analysis with advanced calculations and deeper interpretation techniques for comprehensive cosmic insights.
                </Text>
                
                <View style={styles.benefitItem}>
                  <View style={styles.benefitIconContainer}>
                    <LinearGradient
                      colors={['#ff6b35', '#ff8c5a']}
                      style={styles.benefitIconGradient}
                    >
                      <Text style={styles.benefitIcon}>☀️</Text>
                    </LinearGradient>
                  </View>
                  <View style={styles.benefitText}>
                    <Text style={styles.benefitTitle}>Multi-Layered Chart Analysis</Text>
                    <Text style={styles.benefitDesc}>Examines Lagna, Navamsa, and divisional charts with intricate planetary relationships and house lordships</Text>
                  </View>
                </View>
                
                <View style={styles.benefitItem}>
                  <View style={styles.benefitIconContainer}>
                    <LinearGradient
                      colors={['#4CAF50', '#66BB6A']}
                      style={styles.benefitIconGradient}
                    >
                      <Text style={styles.benefitIcon}>🌟</Text>
                    </LinearGradient>
                  </View>
                  <View style={styles.benefitText}>
                    <Text style={styles.benefitTitle}>Advanced Dasha Interpretation</Text>
                    <Text style={styles.benefitDesc}>Analyzes Mahadasha, Antardasha, and Pratyantardasha periods with precise event timing predictions</Text>
                  </View>
                </View>
                
                <View style={styles.benefitItem}>
                  <View style={styles.benefitIconContainer}>
                    <LinearGradient
                      colors={['#2196F3', '#42A5F5']}
                      style={styles.benefitIconGradient}
                    >
                      <Text style={styles.benefitIcon}>🎯</Text>
                    </LinearGradient>
                  </View>
                  <View style={styles.benefitText}>
                    <Text style={styles.benefitTitle}>Yoga & Dosha Detection</Text>
                    <Text style={styles.benefitDesc}>Identifies powerful yogas like Raja, Dhana, Gaja Kesari and doshas affecting your life trajectory</Text>
                  </View>
                </View>
                
                <View style={styles.benefitItem}>
                  <View style={styles.benefitIconContainer}>
                    <LinearGradient
                      colors={['#9C27B0', '#BA68C8']}
                      style={styles.benefitIconGradient}
                    >
                      <Text style={styles.benefitIcon}>🌙</Text>
                    </LinearGradient>
                  </View>
                  <View style={styles.benefitText}>
                    <Text style={styles.benefitTitle}>Nakshatra Deep Dive</Text>
                    <Text style={styles.benefitDesc}>Reveals hidden personality traits, karmic patterns, and life purpose through nakshatra analysis</Text>
                  </View>
                </View>
                
                <View style={styles.benefitItem}>
                  <View style={styles.benefitIconContainer}>
                    <LinearGradient
                      colors={['#FF9800', '#FFB74D']}
                      style={styles.benefitIconGradient}
                    >
                      <Text style={styles.benefitIcon}>⚡</Text>
                    </LinearGradient>
                  </View>
                  <View style={styles.benefitText}>
                    <Text style={styles.benefitTitle}>Transit Correlation</Text>
                    <Text style={styles.benefitDesc}>Maps current planetary transits against your birth chart for accurate timing of events</Text>
                  </View>
                </View>
                
                <View style={styles.benefitItem}>
                  <View style={styles.benefitIconContainer}>
                    <LinearGradient
                      colors={['#795548', '#A1887F']}
                      style={styles.benefitIconGradient}
                    >
                      <Text style={styles.benefitIcon}>🏆</Text>
                    </LinearGradient>
                  </View>
                  <View style={styles.benefitText}>
                    <Text style={styles.benefitTitle}>Remedial Recommendations</Text>
                    <Text style={styles.benefitDesc}>Provides personalized gemstone, mantra, and ritual suggestions based on planetary strengths</Text>
                  </View>
                </View>
                
                <TouchableOpacity 
                  style={styles.popupButton}
                  onPress={() => setShowEnhancedPopup(false)}
                >
                  <LinearGradient
                    colors={['#ff6b35', '#ff8c5a']}
                    style={styles.popupButtonGradient}
                  >
                    <Text style={styles.popupButtonText}>Got it!</Text>
                  </LinearGradient>
                </TouchableOpacity>
              </GHScrollView>
            </View>
          </View>
        </Modal>
        
        {/* Chart Picker Modal */}
        <Modal
          visible={showChartPicker}
          transparent={true}
          animationType="slide"
          onRequestClose={() => setShowChartPicker(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.chartPickerModal}>
              <View style={styles.chartPickerHeader}>
                <Text style={styles.chartPickerTitle}>
                  Select {selectingFor === 'native' ? 'Native' : 'Partner'} Chart
                </Text>
                <TouchableOpacity onPress={() => setShowChartPicker(false)}>
                  <Ionicons name="close" size={24} color={COLORS.textPrimary} />
                </TouchableOpacity>
              </View>
              
              <GHScrollView style={styles.chartPickerList}>
                {savedCharts.map((chart, index) => (
                  <TouchableOpacity
                    key={index}
                    style={styles.chartPickerItem}
                    onPress={() => {
                      if (selectingFor === 'native') {
                        setNativeChart(chart);
                      } else {
                        setPartnerChart(chart);
                      }
                      setShowChartPicker(false);
                    }}
                  >
                    <View style={styles.chartPickerItemContent}>
                      <Text style={styles.chartPickerItemName}>{chart.name}</Text>
                      <Text style={styles.chartPickerItemDetails}>
                        {chart.date} • {chart.time}
                      </Text>
                      <Text style={styles.chartPickerItemPlace}>{chart.place}</Text>
                    </View>
                    <Ionicons name="chevron-forward" size={20} color={COLORS.textSecondary} />
                  </TouchableOpacity>
                ))}
                
                {savedCharts.length === 0 && (
                  <View style={styles.emptyChartList}>
                    <Text style={styles.emptyChartText}>No saved charts found</Text>
                    <Text style={styles.emptyChartSubtext}>Please save charts first</Text>
                  </View>
                )}
              </GHScrollView>
            </View>
          </View>
        </Modal>
        
        {/* Country Picker Modal */}
        <Modal
          visible={showCountryPicker}
          transparent={true}
          animationType="slide"
          onRequestClose={() => { setShowCountryPicker(false); setCountrySearchQuery(''); }}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.chartPickerModal}>
              <View style={styles.chartPickerHeader}>
                <Text style={styles.chartPickerTitle}>Select Country</Text>
                <TouchableOpacity onPress={() => { setShowCountryPicker(false); setCountrySearchQuery(''); }}>
                  <Ionicons name="close" size={24} color={COLORS.textPrimary} />
                </TouchableOpacity>
              </View>
              <View style={[styles.chartPickerSearchWrap, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)' }]}>
                <Ionicons name="search" size={20} color={colors.textTertiary} style={styles.chartPickerSearchIcon} />
                <TextInput
                  style={[styles.chartPickerSearchInput, { color: colors.text }]}
                  placeholder="Search countries..."
                  placeholderTextColor={colors.textTertiary}
                  value={countrySearchQuery}
                  onChangeText={setCountrySearchQuery}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
                {countrySearchQuery.length > 0 && (
                  <TouchableOpacity onPress={() => setCountrySearchQuery('')} style={styles.chartPickerSearchClear}>
                    <Ionicons name="close-circle" size={20} color={colors.textTertiary} />
                  </TouchableOpacity>
                )}
              </View>
              <GHScrollView style={styles.chartPickerList} keyboardShouldPersistTaps="handled">
                {COUNTRIES.filter(c => {
                  const q = countrySearchQuery.trim().toLowerCase();
                  if (!q) return true;
                  return (c.name && c.name.toLowerCase().includes(q)) || (c.capital && c.capital.toLowerCase().includes(q));
                }).map((country, index) => (
                  <TouchableOpacity
                    key={`${country.name}-${index}`}
                    style={styles.chartPickerItem}
                    onPress={() => {
                      setSelectedCountry(country);
                      setShowCountryPicker(false);
                      setCountrySearchQuery('');
                    }}
                  >
                    <View style={styles.chartPickerItemContent}>
                      <Text style={styles.chartPickerItemName}>{country.name}</Text>
                      <Text style={styles.chartPickerItemDetails}>{country.capital}</Text>
                    </View>
                    <Ionicons name="chevron-forward" size={20} color={COLORS.textSecondary} />
                  </TouchableOpacity>
                ))}
              </GHScrollView>
            </View>
          </View>
        </Modal>
        
        {/* Year Picker Modal */}
        <Modal
          visible={showYearPicker}
          transparent={true}
          animationType="slide"
          onRequestClose={() => setShowYearPicker(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.chartPickerModal}>
              <View style={styles.chartPickerHeader}>
                <Text style={styles.chartPickerTitle}>Select Year</Text>
                <TouchableOpacity onPress={() => setShowYearPicker(false)}>
                  <Ionicons name="close" size={24} color={COLORS.textPrimary} />
                </TouchableOpacity>
              </View>
              <GHScrollView style={styles.chartPickerList}>
                {YEARS.map((year, index) => (
                  <TouchableOpacity
                    key={index}
                    style={styles.chartPickerItem}
                    onPress={() => {
                      setSelectedYear(year);
                      setShowYearPicker(false);
                    }}
                  >
                    <View style={styles.chartPickerItemContent}>
                      <Text style={styles.chartPickerItemName}>{year}</Text>
                    </View>
                    <Ionicons name="chevron-forward" size={20} color={COLORS.textSecondary} />
                  </TouchableOpacity>
                ))}
              </GHScrollView>
            </View>
          </View>
        </Modal>

        </View>
      </SafeAreaView>

      <NotificationEnableReminderModal homeActive={showGreeting} />

      <PodcastPromoModal
        visible={podcastPromoVisible}
        podcastCost={podcastCost}
        colors={colors}
        onClose={() => {
          setPodcastPromoVisible(false);
          setPodcastPromoMessageId(null);
          if (ratingPromptPending && ratingPromptMessageId) {
            setRatingPromptPending(false);
            triggerRatingPrompt(ratingPromptMessageId, 'after_podcast_close');
          }
        }}
        onGenerate={() => {
          setPodcastPromoVisible(false);
          setPodcastAutoLaunchKey((k) => k + 1);
          if (ratingPromptPending && ratingPromptMessageId) {
            setRatingPromptPending(false);
            triggerRatingPrompt(ratingPromptMessageId, 'after_podcast_generate');
          }
        }}
      />
      <ChatRatingPromptModal
        visible={ratingPromptVisible}
        colors={colors}
        onLater={() => {
          const actionAt = new Date().toISOString();
          setRatingPromptVisible(false);
          saveRatingPromptState((prev) => ({
            ...prev,
            lastAction: 'later',
            lastActionAt: actionAt,
          }));
          trackEvent('rating_prompt_action', {
            action: 'later',
            message_id: String(ratingPromptMessageId || ''),
          });
        }}
        onRateNow={async () => {
          const actionAt = new Date().toISOString();
          setRatingPromptVisible(false);
          trackEvent('rating_prompt_action', {
            action: 'rate_now',
            message_id: String(ratingPromptMessageId || ''),
          });
          const started = await requestInAppStoreReview();
          if (started) {
            saveRatingPromptState((prev) => ({
              ...prev,
              completed: true,
              neverAskAgain: true,
              lastAction: 'rate_now',
              lastActionAt: actionAt,
            }));
          } else {
            saveRatingPromptState((prev) => ({
              ...prev,
              lastAction: 'later',
              lastActionAt: actionAt,
            }));
            trackEvent('rating_prompt_action', {
              action: 'rate_now_unavailable',
              message_id: String(ratingPromptMessageId || ''),
            });
          }
        }}
      />
      
      <PremiumAnalysisModal
        visible={showPremiumModal}
        onClose={() => setShowPremiumModal(false)}
        premiumCost={premiumChatCost}
        standardCost={chatCost}
      />
      <ConfirmCreditsModal
        visible={showPartnershipModal}
        onClose={() => setShowPartnershipModal(false)}
        onConfirm={confirmPartnershipMode}
        title="Partnership Mode"
        description="Partnership mode uses credits per question for comprehensive compatibility analysis between two charts."
        cost={partnershipModalCost}
        credits={credits}
        confirmLabel="Continue"
      />
      <ConfirmCreditsModal
        visible={showMundaneModal}
        onClose={() => setShowMundaneModal(false)}
        onConfirm={confirmMundaneMode}
        title="Global Markets & Events"
        description="Global Markets & Events analysis uses credits per question for deep mundane astrology of nations, markets, and world events."
        cost={mundaneModalCost}
        credits={credits}
        confirmLabel="Continue"
      />
      {renderPartnershipSetupModal()}
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradientBg: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  safeAreaInner: {
    flex: 1,
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  headerContainer: {
    paddingHorizontal: 12,
    paddingTop: 12,
    paddingBottom: 8,
    overflow: 'visible',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
    borderWidth: 1,
    overflow: 'visible',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
  },
  headerLogoContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius: 8,
    elevation: 8,
  },
  headerLogo: {
    width: 44,
    height: 44,
    borderRadius: 22,
  },
  nameChip: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    marginTop: 2,
  },
  nameChipText: {
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'center',
  },
  partnershipChipsContainer: {
    flexDirection: 'row',
    gap: 4,
    marginTop: 2,
  },
  nativeChip: {
    backgroundColor: 'rgba(59, 130, 246, 0.25)',
    borderWidth: 1.5,
    borderColor: 'rgba(59, 130, 246, 0.8)',
  },
  partnerChip: {
    backgroundColor: 'rgba(236, 72, 153, 0.25)',
    borderWidth: 1.5,
    borderColor: 'rgba(236, 72, 153, 0.8)',
  },
  compactChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  compactChipText: {
    fontSize: 10,
    fontWeight: '700',
    textAlign: 'center',
    color: '#ffffff',
  },
  headerNativeChipWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerNativeChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    minHeight: 32,
  },
  headerNativeChipText: {
    fontSize: 11,
    fontWeight: '600',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flexShrink: 0,
    overflow: 'visible',
  },
  creditButton: {
    backgroundColor: 'rgba(255, 107, 53, 0.2)',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.4)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  creditButtonPremium: {
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
    borderColor: 'rgba(255, 215, 0, 0.4)',
  },
  creditText: {
    fontSize: 13,
    fontWeight: '700',
  },
  menuButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerBellButton: {
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    minWidth: 40,
    minHeight: 40,
  },
  headerBellHitBox: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  headerBellBadge: {
    position: 'absolute',
    top: 3,
    right: 2,
    minWidth: 18,
    minHeight: 18,
    maxWidth: 34,
    paddingHorizontal: 5,
    borderRadius: 10,
    backgroundColor: '#ff6b35',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'rgba(255, 255, 255, 0.35)',
  },
  headerBellBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '800',
    textAlign: 'center',
    includeFontPadding: false,
  },
  messagesContainer: {
    flex: 1,
    paddingHorizontal: 4,
  },
  messagesContent: {
    paddingVertical: 16,
    paddingHorizontal: 12,
    flexGrow: 1,
  },

  suggestionsContainer: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  suggestionsContent: {
    paddingHorizontal: 4,
  },
  suggestionChip: {
    marginRight: 8,
    borderRadius: 20,
    overflow: 'hidden',
  },
  suggestionChipGradient: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.2)',
    borderRadius: 20,
  },
  suggestionChipText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '600',
  },

  unifiedInputContainer: {
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  chatInputScopeHint: {
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 8,
    paddingHorizontal: 4,
    flexWrap: 'wrap',
  },
  chatInputScopeName: {
    fontWeight: '700',
  },
  chatInputScopeLink: {
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
  inputBarGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 28,
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderWidth: 1,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
      },
      android: {
        // elevation set dynamically
      },
    }),
  },
  modernTextInput: {
    flex: 1,
    fontSize: 16,
    color: COLORS.white,
    paddingHorizontal: 16,
    paddingVertical: 10,
    maxHeight: 100,
  },
  modernTextInputCollapsed: {
    height: 44,
    maxHeight: 44,
    minHeight: 44,
  },
  premiumToggleButton: {
    marginHorizontal: 4,
  },
  premiumToggleIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  premiumIconGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.4)',
    shadowColor: '#ffd700',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 8,
    elevation: 6,
  },
  premiumIconText: {
    fontSize: 24,
  },
  premiumIconInactive: {
    width: '100%',
    height: '100%',
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  premiumIconTextInactive: {
    fontSize: 24,
    opacity: 0.7,
  },
  modernSendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.4,
    shadowRadius: 4,
    elevation: 4,
  },
  modernSendButtonDisabled: {
    opacity: 0.5,
  },
  modernSendGradient: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modernSendText: {
    fontSize: 20,
  },
  modeSelectorExpanded: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginRight: 8,
    paddingVertical: 4,
  },
  modeSelectorPill: {
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 10,
    alignItems: 'center',
    minWidth: 72,
  },
  modeSelectorPillActive: {
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.5)',
  },
  modeSelectorPillActivePremium: {
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.6)',
  },
  modeSelectorLabel: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 2,
  },
  modeSelectorCostRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  modeSelectorCost: {
    fontSize: 11,
    fontWeight: '700',
  },
  modeSelectorCostOriginal: {
    fontSize: 11,
    fontWeight: '600',
    textDecorationLine: 'line-through',
    marginRight: 4,
    opacity: 0.8,
  },
  modeSelectorCreditLabel: {
    fontSize: 10,
    fontWeight: '500',
  },
  firstQuestionFreeBanner: {
    marginTop: 8,
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 14,
    backgroundColor: 'rgba(34, 197, 94, 0.2)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(34, 197, 94, 0.4)',
  },
  firstQuestionFreeIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  firstQuestionFreeTextWrap: {
    flex: 1,
  },
  firstQuestionFreeTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#22c55e',
    letterSpacing: 0.3,
  },
  firstQuestionFreeSubtext: {
    fontSize: 12,
    color: 'rgba(34, 197, 94, 0.9)',
    marginTop: 2,
    fontWeight: '500',
  },
  lowCreditBanner: {
    marginTop: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: 'rgba(255, 107, 53, 0.2)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
  },
  lowCreditText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
  notifGateBanner: {
    marginTop: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: 'rgba(59, 130, 246, 0.22)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.45)',
  },
  notifGateText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
  },
  quickActionsBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: Platform.OS === 'ios' ? 8 : 8,
  },
  quickActionButton: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    opacity: 0.8,
  },
  quickActionButtonActive: {
    opacity: 1,
  },
  quickActionText: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '600',
  },
  signsContainer: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  signsGradient: {
    padding: 16,
  },
  signsTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 12,
  },
  signsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  signItem: {
    alignItems: 'center',
    flex: 1,
  },
  signLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: 4,
  },
  signValue: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.white,
    textAlign: 'center',
  },
  dashasContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.2)',
  },
  dashasTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    marginBottom: 8,
  },
  dashasRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    flexWrap: 'wrap',
    gap: 6,
  },
  dashasLoading: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    textAlign: 'center',
  },
  dashaChip: {
    borderWidth: 1.5,
    borderRadius: 16,
    paddingHorizontal: 10,
    paddingVertical: 10,
    alignItems: 'center',
    marginRight: 8,
    width: cardWidth,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.2,
        shadowRadius: 4,
      },
      android: {
        // elevation set dynamically
      },
    }),
  },
  dashaChipPlanet: {
    fontSize: fontSize,
    fontWeight: '700',
    marginBottom: 2,
  },
  dashaChipDates: {
    fontSize: smallFontSize,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '500',
  },
  dashaSection: {
    marginTop: 16,
    marginBottom: 24,
  },
  dashaSectionTitle: {
    fontSize: isSmallScreen ? 16 : 18,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  dashaFlatListContent: {
    paddingHorizontal: 4,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.98)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  partnershipModalContent: {
    borderRadius: 32,
    width: '100%',
    maxHeight: '90%',
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    elevation: 20,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 107, 53, 0.1)',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '800',
  },
  modalContent: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 24,
    padding: 24,
    width: '88%',
    maxHeight: '75%',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  drawerOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
    flexDirection: 'row',
  },
  drawerContent: {
    width: 300,
    height: '100%',
    shadowColor: '#000',
    shadowOffset: { width: -2, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 12,
    elevation: 15,
  },
  drawerGradient: {
    flex: 1,
  },
  drawerHeader: {
    alignItems: 'center',
    paddingTop: 60,
    paddingBottom: 20,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  logoContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    elevation: 8,
  },
  logoImage: {
    width: 70,
    height: 70,
    borderRadius: 35,
  },
  cosmicOrbSmall: {
    width: 70,
    height: 70,
    borderRadius: 35,
    marginBottom: 16,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.6,
    shadowRadius: 12,
    elevation: 8,
  },
  orbGradientSmall: {
    width: '100%',
    height: '100%',
    borderRadius: 35,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  orbIconSmall: {
    fontSize: 36,
  },
  drawerTitle: {
    fontSize: 24,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 6,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  drawerSubtitle: {
    fontSize: 14,
    textAlign: 'center',
  },
  menuScrollView: {
    height: 450,
  },
  menuScrollContent: {
    padding: 20,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.accent,
    textAlign: 'center',
    marginBottom: 24,
  },
  languageModalScrollView: {
    maxHeight: 320,
  },
  languageModalScrollContent: {
    paddingRight: 8,
    paddingBottom: 8,
  },
  languageOption: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    backgroundColor: COLORS.lightGray,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  languageOptionSelected: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    borderColor: COLORS.accent,
  },
  languageText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.black,
  },
  menuOption: {
    marginBottom: 12,
    borderRadius: 16,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  menuOptionLast: {
    marginTop: 8,
  },
  menuGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  menuIconContainer: {
    marginRight: 14,
  },
  menuIconGradient: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  menuEmoji: {
    fontSize: 22,
  },
  menuText: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
  },
  modalCloseButton: {
    backgroundColor: COLORS.accent,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 16,
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  modalCloseText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '700',
  },

  enhancedPopupOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  enhancedPopup: {
    backgroundColor: '#ffffff',
    borderRadius: 24,
    width: '100%',
    maxHeight: '90%',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 20 },
    shadowOpacity: 0.15,
    shadowRadius: 30,
    elevation: 15,
    overflow: 'hidden',
  },
  popupClose: {
    position: 'absolute',
    top: 20,
    right: 20,
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  popupCloseText: {
    fontSize: 20,
    color: '#666',
    fontWeight: '600',
  },
  popupHeader: {
    paddingVertical: 40,
    paddingHorizontal: 24,
    alignItems: 'center',
    position: 'relative',
    overflow: 'hidden',
  },
  popupHeaderGradient: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  popupHeaderContent: {
    alignItems: 'center',
    zIndex: 2,
  },
  popupIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 16,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  popupIconGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.8)',
  },
  popupIcon: {
    fontSize: 40,
  },
  popupTitle: {
    color: COLORS.white,
    fontSize: 26,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 8,
    textShadowColor: 'rgba(0, 0, 0, 0.2)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  popupSubtitle: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 16,
    textAlign: 'center',
    fontWeight: '500',
  },
  popupContent: {
    maxHeight: '65%',
  },
  popupContentContainer: {
    padding: 24,
    paddingBottom: 32,
  },
  popupIntro: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 24,
    fontWeight: '400',
  },
  benefitItem: {
    flexDirection: 'row',
    marginBottom: 16,
    padding: 16,
    backgroundColor: '#fafafa',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#f0f0f0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },
  benefitIconContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    marginRight: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  benefitIconGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  benefitIcon: {
    fontSize: 20,
  },
  benefitText: {
    flex: 1,
    justifyContent: 'center',
  },
  benefitTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#333',
    marginBottom: 4,
  },
  benefitDesc: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    fontWeight: '400',
  },
  popupButton: {
    borderRadius: 16,
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 8,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
  popupButtonGradient: {
    paddingVertical: 16,
    paddingHorizontal: 32,
    width: '100%',
    alignItems: 'center',
  },
  popupButtonText: {
    color: COLORS.white,
    fontSize: 18,
    fontWeight: '700',
  },
  // Partnership mode styles
  chartSelectionContainer: {
    padding: 16,
    backgroundColor: COLORS.lightGray,
    borderRadius: 12,
    margin: 16,
  },
  chartSelectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 12,
  },
  chartSelectButton: {
    padding: 12,
    backgroundColor: COLORS.white,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 8,
  },
  chartSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.quickAnswerStart,
  },
  chartSelectText: {
    fontSize: 14,
    color: COLORS.textPrimary,
  },
  chartsDisplayContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  miniChartCard: {
    flex: 1,
    padding: 12,
    backgroundColor: COLORS.white,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  miniChartLabel: {
    fontSize: 10,
    color: COLORS.textSecondary,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  miniChartName: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  miniChartDetails: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  chartPickerModal: {
    backgroundColor: COLORS.white,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '70%',
  },
  chartPickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  chartPickerSearchWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 4,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  chartPickerSearchIcon: {
    marginRight: 10,
  },
  chartPickerSearchInput: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 0,
  },
  chartPickerSearchClear: {
    padding: 4,
  },
  chartPickerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  chartPickerList: {
    padding: 16,
  },
  chartPickerItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: COLORS.lightGray,
    borderRadius: 12,
    marginBottom: 12,
  },
  chartPickerItemContent: {
    flex: 1,
  },
  chartPickerItemName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  chartPickerItemDetails: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: 2,
  },
  chartPickerItemPlace: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  setupSelectorContainer: {
    width: screenWidth - 32, // Width of parent minus horizontal padding of messagesContent (16*2)
    paddingVertical: 12,
    marginTop: 8,
    alignSelf: 'center',
  },
  setupSelectorScroll: {
    paddingLeft: 4,
    paddingRight: 16,
    alignItems: 'center',
    flexDirection: 'row',
  },
  setupSelectorChip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    marginRight: 10,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    flexShrink: 0,
    minHeight: 40,
    justifyContent: 'center',
  },
  setupSelectorText: {
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  setupHelperText: {
    fontSize: 12,
    marginTop: 8,
    textAlign: 'center',
    fontStyle: 'italic',
    paddingHorizontal: 20,
    width: '100%',
  },
  partnershipSetupCard: {
    marginHorizontal: 16,
    marginVertical: 12,
    borderRadius: 24,
    padding: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.2,
    shadowRadius: 20,
    elevation: 5,
  },
  partnershipSetupTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#fff',
    marginBottom: 20,
    textAlign: 'center',
  },
  setupSlotsContainer: {
    gap: 12,
  },
  setupSlot: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 16,
    padding: 12,
    borderWidth: 1.5,
    borderColor: 'transparent',
  },
  setupSlotActive: {
    borderColor: '#ff6b35',
    backgroundColor: 'rgba(255, 107, 53, 0.15)',
  },
  setupSlotFilled: {
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
  },
  setupSlotIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  setupSlotContent: {
    flex: 1,
  },
  setupSlotLabel: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.5)',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  setupSlotValue: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '700',
  },
  setupSlotPlaceholder: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.3)',
    fontWeight: '500',
  },
  setupConfirmButton: {
    marginTop: 24,
    borderRadius: 16,
    overflow: 'hidden',
    elevation: 4,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  setupConfirmGradient: {
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  setupConfirmText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '800',
  },
  modalSearchContainer: {
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  modalSearchWrapper: {
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    height: 44,
  },
  modalSearchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 14,
  },
  setupResetButton: {
    marginTop: 12,
    alignItems: 'center',
    padding: 8,
  },
  setupResetText: {
    color: 'rgba(255, 255, 255, 0.4)',
    fontSize: 13,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
  emptyChartList: {
    padding: 32,
    alignItems: 'center',
  },
  emptyChartText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textSecondary,
    marginBottom: 8,
  },
  emptyChartSubtext: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  floatingBadgesContainer: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    alignItems: 'center',
    marginHorizontal: 16,
    marginTop: 8,
    marginBottom: 8,
    gap: 8,
  },
  floatingChangeBadge: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    gap: 4,
  },
  changeBadgeText: {
    color: '#ff6b35',
    fontSize: 11,
    fontWeight: '700',
  },
  floatingPartnershipBadge: {
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(244, 114, 182, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(244, 114, 182, 0.3)',
    shadowColor: '#ec4899',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  partnershipBadgeTextContent: {
    overflow: 'hidden',
    borderTopLeftRadius: 20,
    borderBottomLeftRadius: 20,
  },
  partnershipBadgeGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderTopLeftRadius: 20,
    borderBottomLeftRadius: 20,
  },
  partnershipBadgeText: {
    color: COLORS.white,
    fontSize: 11,
    fontWeight: '700',
  },
  partnershipBadgeClose: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    justifyContent: 'center',
    alignItems: 'center',
    borderLeftWidth: 1,
    borderLeftColor: 'rgba(244, 114, 182, 0.2)',
    backgroundColor: 'rgba(244, 114, 182, 0.05)',
    borderTopRightRadius: 20,
    borderBottomRightRadius: 20,
  },
  premiumTooltip: {
    position: 'absolute',
    bottom: 80,
    right: 10,
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 5,
    width: 180,
    zIndex: 1000,
  },
  tooltipText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  tooltipSubtext: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },
  tooltipButton: {
    backgroundColor: '#ff6b35',
    padding: 8,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 4,
  },
  tooltipButtonText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '600',
  },
  tooltipClose: {
    position: 'absolute',
    top: 4,
    right: 4,
    padding: 4,
    zIndex: 1001,
  },
  tooltipCloseText: {
    fontSize: 16,
    color: '#999',
  },
  premiumBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    backgroundColor: '#ff6b35',
    width: 16,
    height: 16,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#1a0033',
  },
  premiumBadgeText: {
    color: COLORS.white,
    fontSize: 10,
    fontWeight: 'bold',
  },
  otherRelationContainer: {
    width: '100%',
    paddingHorizontal: 4,
  },
  otherInputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  otherTextInput: {
    flex: 1,
    height: 48,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#ff6b35',
    paddingHorizontal: 16,
    fontSize: 15,
    backgroundColor: 'rgba(255, 107, 53, 0.05)',
  },
  otherDoneButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#ff6b35',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
  },
});
