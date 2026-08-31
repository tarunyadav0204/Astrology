import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Animated,
  Dimensions,
  Modal,
  StatusBar,
  Alert,
  ActivityIndicator,
  StyleSheet,
  TextInput,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { ScrollView as GHScrollView } from 'react-native-gesture-handler';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { useTranslation } from 'react-i18next';
import Ionicons from '@expo/vector-icons/Ionicons';
import { storage } from '../../services/storage';
import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';
import { parseCalendarDateInput } from '../../utils/birthDateUtils';
import AsyncStorage from '@react-native-async-storage/async-storage';
import AshtakvargaChart from './AshtakvargaChart';
import DateNavigator from '../Common/DateNavigator';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import { useTheme } from '../../context/ThemeContext';
import { useCredits } from '../../credits/CreditContext';
import { useAuthGate } from '../../auth/AuthGateContext';
import { pricingAPI } from '../../services/api';
import CreditModal from '../CreditModal';
import { typographyTokens } from '../../theme/tokens';

const { width, height } = Dimensions.get('window');

/** Labels for `life_domain_insights` keys from backend life-predictions JSON */
const LIFE_PREDICTION_DOMAIN_LABELS = {
  vitality_and_personality: 'Vitality & personality',
  wealth_family_speech: 'Wealth, family & speech',
  courage_siblings_skills: 'Courage, siblings & skills',
  home_comfort_mother: 'Home, comfort & mother',
  children_creativity_speculation: 'Children, creativity & speculation',
  health_service_obstacles: 'Health, service & obstacles',
  partnerships_marriage: 'Partnerships & marriage',
  longevity_shared_resources: 'Longevity & shared resources',
  fortune_dharma_father: 'Fortune, dharma & father-guru line',
  career_reputation: 'Career & reputation',
  gains_network_aspirations: 'Gains, network & aspirations',
  expenses_moksha_rest: 'Expenses, rest & liberation themes',
};

const LIFE_PREDICTIONS_POLL_MS = 3000;
const LIFE_PREDICTIONS_MAX_POLLS = 120;
const ASHTAKVARGA_TABS = [
  { key: 'matrix', labelKey: 'matrix', icon: 'table-outline' },
  { key: 'sav', labelKey: 'sav', icon: 'grid-outline' },
  { key: 'bav', labelKey: 'bav', icon: 'planet-outline' },
  { key: 'advanced', labelKey: 'pinda', icon: 'calculator-outline' },
  { key: 'transit', labelKey: 'transit', icon: 'navigate-circle-outline' },
  { key: 'ai', labelKey: 'analysis', icon: 'analytics-outline' },
];
const SIGN_SHORT_NAMES = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'];
const ASHTAKVARGA_PROFILES = [
  { id: 'pvr_narasimha_rao', label: 'P.V.R. Narasimha Rao', detail: 'Replacement rule · seven grahas' },
  { id: 'parasharas_light_7', label: 'Parashara’s Light 7', detail: 'Published-table profile · Lagna occupancy' },
];
const ADVANCED_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
const ADVANCED_TIMING_LABELS = {
  father: 'Sun · H9', mother: 'Moon · H4', siblings: 'Mars · H3',
  profession: 'Mercury · H10', children: 'Jupiter · H5',
  marriage: 'Venus · H7', longevity: 'Saturn · H8',
};
const ASHTAKVARGA_QUESTION_SUGGESTIONS = [
  'How is career support right now?',
  'Which houses are weakest at the moment?',
  'Is money support improving or weakening?',
  'How is marriage support in Ashtakavarga?',
  'Which planet is not delivering results well?',
];
const ASHTAKVARGA_ANALYSIS_MODES = [
  { key: 'birth', label: 'Birth', icon: 'person-circle-outline' },
  { key: 'transit', label: 'Transit', icon: 'today-outline' },
  { key: 'ask', label: 'Ask', icon: 'chatbubble-ellipses-outline' },
];

function lifePredictionsJobStatusUrl(jobId) {
  return `${API_BASE_URL}${getEndpoint(`/ashtakavarga/life-predictions/status/${jobId}`)}`;
}

async function pollLifePredictionsJobApi(jobId, token) {
  let pollCount = 0;
  while (pollCount < LIFE_PREDICTIONS_MAX_POLLS) {
    const res = await fetch(lifePredictionsJobStatusUrl(jobId), {
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg =
        typeof body?.detail === 'string'
          ? body.detail
          : body?.error || `Request failed (${res.status})`;
      throw new Error(msg);
    }
    if (body.status === 'completed' && body.result) {
      return body.result;
    }
    if (body.status === 'failed') {
      throw new Error(
        String(
          body.error ||
            body.result?.error ||
            body.result?.predictions?.error ||
            'Generation failed'
        )
      );
    }
    await new Promise((r) => setTimeout(r, LIFE_PREDICTIONS_POLL_MS));
    pollCount += 1;
  }
  throw new Error('TIMEOUT');
}

const HOUSE_SIGNIFICATIONS = {
  0: { // House 1
    name: "Self & Personality",
    significations: "Physical body, appearance, personality, self-expression, vitality, overall health, life path, and how you present yourself to the world."
  },
  1: { // House 2
    name: "Wealth & Family",
    significations: "Accumulated wealth, family values, speech, food habits, early childhood, face, eyes, right eye, financial security, and material possessions."
  },
  2: { // House 3
    name: "Courage & Siblings",
    significations: "Siblings, courage, short travels, communication skills, hobbies, neighbors, hands, arms, shoulders, and self-efforts."
  },
  3: { // House 4
    name: "Home & Mother",
    significations: "Mother, home, property, vehicles, emotional peace, education, chest, heart, domestic happiness, and inner contentment."
  },
  4: { // House 5
    name: "Children & Creativity",
    significations: "Children, creativity, intelligence, romance, speculation, past life merits, stomach, education, and spiritual practices."
  },
  5: { // House 6
    name: "Health & Enemies",
    significations: "Diseases, enemies, debts, obstacles, service, daily work, pets, maternal relatives, digestive system, and competitive abilities."
  },
  6: { // House 7
    name: "Marriage & Partnership",
    significations: "Spouse, marriage, business partnerships, public relations, sexual organs, lower abdomen, and long-term relationships."
  },
  7: { // House 8
    name: "Transformation & Longevity",
    significations: "Longevity, sudden events, inheritance, occult knowledge, research, chronic diseases, reproductive organs, and transformative experiences."
  },
  8: { // House 9
    name: "Fortune & Dharma",
    significations: "Father, luck, higher education, long journeys, spirituality, religion, philosophy, thighs, and life purpose."
  },
  9: { // House 10
    name: "Career & Status",
    significations: "Career, profession, reputation, authority, government, knees, public image, and social standing."
  },
  10: { // House 11
    name: "Gains & Aspirations",
    significations: "Income, gains, elder siblings, friends, social networks, left ear, fulfillment of desires, and large organizations."
  },
  11: { // House 12
    name: "Liberation & Expenses",
    significations: "Expenses, losses, foreign lands, spirituality, isolation, sleep, feet, bed pleasures, and final liberation (moksha)."
  }
};

export default function AshtakvargaOracle({ navigation, route, onHeaderStateChange }) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const { credits, fetchBalance } = useCredits();
  const { requireAuthForPaid } = useAuthGate();
  const embedded = !!route?.params?.embedded;
  const themedSurface = { backgroundColor: colors.surfaceRaised, borderColor: colors.borderStrong };
  const themedMutedSurface = { backgroundColor: colors.surfaceMuted, borderColor: colors.borderStrong };
  const themedAccentSurface = { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder };
  const inverseSurface = { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine };
  const [activeTab, setActiveTab] = useState(0);
  const [birthData, setBirthData] = useState(null);
  const [oracleData, setOracleData] = useState(null);
  const [birthOracleData, setBirthOracleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPillar, setSelectedPillar] = useState(null);
  const [showSecretScroll, setShowSecretScroll] = useState(false);
  const [completeOracleData, setCompleteOracleData] = useState(null);
  const [loadingInsight, setLoadingInsight] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [analysisQuestion, setAnalysisQuestion] = useState('');
  const [analysisMode, setAnalysisMode] = useState('birth');
  const [analysisResultMode, setAnalysisResultMode] = useState(null);
  const [askMessages, setAskMessages] = useState([]);
  const [lastAskedQuestion, setLastAskedQuestion] = useState('');
  const [ashtakavargaProfile, setAshtakavargaProfile] = useState('pvr_narasimha_rao');
  const [selectedAdvancedPlanet, setSelectedAdvancedPlanet] = useState('Saturn');
  const [classicalTransitData, setClassicalTransitData] = useState(null);
  const [transitDeskLoading, setTransitDeskLoading] = useState(false);
  const [transitEventFilter, setTransitEventFilter] = useState('all');

  // Animations
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const loadingRotateAnim = useRef(new Animated.Value(0)).current;
  const birthDataRef = useRef(null);
  birthDataRef.current = birthData;

  const [lifePredictionsCreditCost, setLifePredictionsCreditCost] = useState(15);
  /** null | 'open' (main CTA) | 'regenerate' (modal toolbar) */
  const [lifePredictionsCreditModalMode, setLifePredictionsCreditModalMode] = useState(null);
  const [lifePredictionsCacheChecking, setLifePredictionsCacheChecking] = useState(false);
  const [analysisCreditModalVisible, setAnalysisCreditModalVisible] = useState(false);
  const [pendingAnalysisQuestion, setPendingAnalysisQuestion] = useState(null);

  useEffect(() => {
    loadBirthData();
    startAnimations();
  }, []);

  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      (async () => {
        try {
          let data = await storage.getBirthDetails();
          if (!data) {
            const profiles = await storage.getBirthProfiles();
            if (profiles?.length) {
              data = profiles.find((p) => p.relation === 'self') || profiles[0];
            }
          }
          if (cancelled) return;
          if (!data?.name) {
            navigation.replace('BirthProfileIntro', { returnTo: embedded ? 'ChartsHub' : 'AshtakvargaOracle' });
            return;
          }
          const prev = birthDataRef.current;
          const unchanged =
            prev &&
            String(prev.id ?? '') === String(data.id ?? '') &&
            prev.name === data.name;
          if (unchanged) return;
          setBirthData(data);
          setSelectedDate(parseCalendarDateInput(data.date) || new Date());
        } catch (e) {
          console.error('Error syncing birth data on focus:', e);
        }
      })();
      return () => {
        cancelled = true;
      };
    }, [navigation, embedded])
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await pricingAPI.getPricing();
        const cost = r?.data?.pricing?.ashtakavarga;
        if (!cancelled && cost != null && !Number.isNaN(Number(cost))) {
          setLifePredictionsCreditCost(Math.max(1, Number(cost)));
        }
      } catch (_) {
        /* keep default */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (birthData) {
      fetchAshtakvargaData(birthData, selectedDate);
    }
  }, [birthData, selectedDate, ashtakavargaProfile]);

  useEffect(() => {
    if (!birthData || ASHTAKVARGA_TABS[activeTab]?.key !== 'transit') return;
    let cancelled = false;
    setTransitDeskLoading(true);
    (async () => {
      try {
        const token = await AsyncStorage.getItem('authToken');
        const response = await fetch(`${API_BASE_URL}${getEndpoint('/ashtakavarga/transit-analysis')}`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            birth_data: normalizeBirthForApi(birthData),
            transit_date: (selectedDate || new Date()).toISOString().split('T')[0],
            window_days: 30,
            ashtakavarga_profile: ashtakavargaProfile,
          }),
        });
        const body = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(typeof body?.detail === 'string' ? body.detail : body?.detail?.message || `Transit request failed (${response.status})`);
        if (!cancelled) setClassicalTransitData(body.classical_transit || null);
      } catch (error) {
        console.error('Error loading classical AV transit desk:', error);
        if (!cancelled) setClassicalTransitData(null);
      } finally {
        if (!cancelled) setTransitDeskLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [activeTab, birthData, selectedDate, ashtakavargaProfile]);

  const startAnimations = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 2000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 2000,
          useNativeDriver: true,
        }),
      ])
    ).start();

    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 1000,
      useNativeDriver: true,
    }).start();
  };

  const loadBirthData = async () => {
    try {
      // First try to get single birth details
      let data = await storage.getBirthDetails();

      // If no single birth details, get from profiles
      if (!data) {
        const profiles = await storage.getBirthProfiles();
        if (profiles && profiles.length > 0) {
          // Use the first profile or find 'self' relation
          data = profiles.find(p => p.relation === 'self') || profiles[0];
        }
      }

      if (data?.name) {
        setBirthData(data);
        const birthCal = parseCalendarDateInput(data.date) || new Date();
        setSelectedDate(birthCal);
        try {
          await fetchAshtakvargaData(data, birthCal);
        } catch (fetchErr) {
          console.error('Error fetching ashtakvarga:', fetchErr);
          setOracleData(null);
        }
      } else {
        navigation.replace('BirthProfileIntro', { returnTo: embedded ? 'ChartsHub' : 'AshtakvargaOracle' });
        return;
      }
    } catch (error) {
      console.error('Error loading birth data:', error);
      setOracleData(null);
    } finally {
      setLoading(false);
    }
  };

  const normalizeBirthForApi = (birth) => {
    let dateStr = birth.date;
    if (dateStr && typeof dateStr === 'string') {
      if (dateStr.includes('T')) dateStr = dateStr.split('T')[0];
      else if (dateStr.length === 10 && dateStr[4] === '-' && dateStr[7] === '-') {
        // already YYYY-MM-DD
      } else {
        const d = new Date(dateStr);
        if (!isNaN(d.getTime())) {
          dateStr = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
        }
      }
    }
    let timeStr = birth.time;
    if (timeStr && typeof timeStr === 'string' && timeStr.includes(':')) {
      const parts = timeStr.split(':');
      timeStr = parts.length >= 2 ? `${String(parseInt(parts[0], 10)).padStart(2, '0')}:${String(parseInt(parts[1], 10)).padStart(2, '0')}` : timeStr;
    }
    return {
      name: birth.name || 'User',
      date: dateStr || birth.date,
      time: timeStr || birth.time,
      latitude: Number(birth.latitude),
      longitude: Number(birth.longitude)
    };
  };

  const fetchAshtakvargaData = async (birth, date = null) => {
    try {
      const token = await AsyncStorage.getItem('authToken');

      if (!token || !birth) {
        throw new Error('Missing authentication token or birth data');
      }

      const birthNorm = normalizeBirthForApi(birth);
      const birthDate = parseCalendarDateInput(birthNorm.date) || new Date(birthNorm.date);
      const selectedDate = date || birthDate;

      // Compare only date parts (ignore time)
      const isSameDate = birthDate.getFullYear() === selectedDate.getFullYear() &&
                        birthDate.getMonth() === selectedDate.getMonth() &&
                        birthDate.getDate() === selectedDate.getDate();

      const requestBody = {
        birth_data: birthNorm,
        chart_type: isSameDate ? 'lagna' : 'transit',
        ashtakavarga_profile: ashtakavargaProfile,
      };

      if (!isSameDate) {
        requestBody.transit_date = selectedDate.toISOString().split('T')[0];
      }

      const response = await fetch(`${API_BASE_URL}${getEndpoint('/calculate-ashtakavarga')}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        setOracleData(data);
        setCompleteOracleData(null);
        setAnalysisResultMode(null);
        setAskMessages([]);
        setLastAskedQuestion('');

        // Store birth chart data for comparison if this is birth chart
        if (isSameDate) {
          setBirthOracleData(data);
        }
      } else {
        let message = `Failed to fetch ashtakvarga data: ${response.status}`;
        try {
          const errBody = await response.json();
          if (errBody?.detail) {
            message += ` - ${typeof errBody.detail === 'string' ? errBody.detail : JSON.stringify(errBody.detail)}`;
          }
        } catch (_) {}
        throw new Error(message);
      }
    } catch (error) {
      console.error('Error fetching ashtakvarga data:', error);
      throw error;
    }
  };

  const fetchDailyInsight = async (questionOverride = null) => {
    if (!oracleData || !birthData) {
      console.error('Missing ashtakvarga or birth data');
      return;
    }

    const questionText = (questionOverride ?? analysisQuestion).trim();
    setLoadingInsight(true);
    try {
      const token = await AsyncStorage.getItem('authToken');

      const dailyResponse = await fetch(`${API_BASE_URL}/api/ashtakavarga/oracle-insight`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          birth_data: normalizeBirthForApi(birthData),
          ashtakvarga_data: oracleData,
          birth_ashtakavarga_data: birthOracleData,
          date: (selectedDate || new Date()).toISOString().split('T')[0],
          query_type: questionText ? 'question' : 'overview',
          ...(questionText ? { question_text: questionText } : {}),
        })
      });

      if (dailyResponse.ok) {
        const completeData = await dailyResponse.json();
        console.log('Complete oracle data received:', completeData);
        setCompleteOracleData(completeData);
        setAnalysisResultMode(questionText ? 'ask' : 'transit');
        setLastAskedQuestion(questionText);
        if (questionText) {
          appendAskExchange(questionText, completeData);
          setAnalysisQuestion('');
        }
        if (Number(completeData?.credits_charged) > 0) {
          fetchBalance();
        }
      } else {
        let message = `Request failed (${dailyResponse.status})`;
        const errBody = await dailyResponse.json().catch(() => ({}));
        if (typeof errBody?.detail === 'string') {
          message = errBody.detail;
        } else if (Array.isArray(errBody?.detail) && errBody.detail.length) {
          message = errBody.detail.map((d) => d.msg || JSON.stringify(d)).join('\n');
        } else if (errBody?.error) {
          message = String(errBody.error);
        }
        console.error('Failed to fetch oracle insight:', dailyResponse.status, message);
        Alert.alert('Ashtakavarga Analysis', message);
        if (dailyResponse.status === 402) {
          fetchBalance();
        }
      }
    } catch (error) {
      console.error('Error fetching oracle insight:', error);
      Alert.alert('Ashtakavarga Analysis', 'Could not generate the analysis right now. Please try again.');
    } finally {
      setLoadingInsight(false);
    }
  };

  const appendAskExchange = (questionText, answerData) => {
    const baseId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setAskMessages((prev) => [
      ...prev,
      { id: `${baseId}-user`, role: 'user', text: questionText },
      { id: `${baseId}-assistant`, role: 'assistant', data: answerData },
    ]);
  };

  const probeAshtakavargaAnalysis = async (questionOverride = null) => {
    if (loadingInsight || !oracleData || !birthData) return;
    const questionText = (questionOverride ?? analysisQuestion).trim();
    setLoadingInsight(true);
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}/api/ashtakavarga/oracle-insight`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          birth_data: normalizeBirthForApi(birthData),
          ashtakvarga_data: oracleData,
          birth_ashtakavarga_data: birthOracleData,
          date: (selectedDate || new Date()).toISOString().split('T')[0],
          query_type: questionText ? 'question' : 'overview',
          ...(questionText ? { question_text: questionText } : {}),
          cache_probe: true,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        let message = `Request failed (${response.status})`;
        if (typeof data?.detail === 'string') message = data.detail;
        else if (data?.error) message = String(data.error);
        Alert.alert('Ashtakavarga Analysis', message);
        if (response.status === 402) fetchBalance();
        return;
      }
      if (data.cached === true && !data.error) {
        setCompleteOracleData(data);
        setAnalysisResultMode(questionText ? 'ask' : 'transit');
        setLastAskedQuestion(questionText);
        if (questionText) {
          appendAskExchange(questionText, data);
          setAnalysisQuestion('');
        }
        return;
      }
      if (data.credit_cost_next != null && !Number.isNaN(Number(data.credit_cost_next))) {
        setLifePredictionsCreditCost(Math.max(1, Number(data.credit_cost_next)));
      }
      setPendingAnalysisQuestion(questionText);
      setAnalysisCreditModalVisible(true);
    } catch (error) {
      console.error('Error probing Ashtakavarga analysis:', error);
      Alert.alert('Ashtakavarga Analysis', 'Could not check saved analyses right now. Please try again.');
    } finally {
      setLoadingInsight(false);
    }
  };

  const requestAshtakavargaAnalysis = () => {
    probeAshtakavargaAnalysis();
  };

  const requestAshtakavargaOverview = () => {
    setAnalysisQuestion('');
    probeAshtakavargaAnalysis('');
  };

  const onConfirmAnalysisCreditModal = async () => {
    const authOk = await requireAuthForPaid({
      feature: 'Ashtakavarga analysis',
      message: 'Sign in to run Ashtakavarga AI analysis. Saved replays stay free.',
      resume: { resumeRoute: 'AshtakvargaOracle', resumeParams: {} },
    });
    if (!authOk) return;
    setAnalysisCreditModalVisible(false);
    const nextQuestion = pendingAnalysisQuestion ?? '';
    setPendingAnalysisQuestion(null);
    fetchDailyInsight(nextQuestion);
  };

  const closeAnalysisCreditModal = () => {
    setAnalysisCreditModalVisible(false);
    setPendingAnalysisQuestion(null);
  };

  const modalAnalysisQuestion = analysisCreditModalVisible
    ? (pendingAnalysisQuestion ?? '')
    : analysisQuestion.trim();

  const analysisCreditModalTitle = modalAnalysisQuestion
    ? 'Ask Ashtakavarga?'
    : 'Generate Ashtakavarga overview?';

  const analysisCreditModalDescription = modalAnalysisQuestion
    ? `This will run a focused Ashtakavarga analysis for your question and use ${lifePredictionsCreditCost} credits if generation succeeds. Your balance: ${credits} credits.`
    : `This will generate a fresh Ashtakavarga overview and use ${lifePredictionsCreditCost} credits if generation succeeds. Your balance: ${credits} credits.`;

  const getCosmicWeatherTheme = () => {
    if (!oracleData?.ashtakavarga?.total_bindus) {
      return {
        theme: 'Loading',
        sentiment: 'neutral',
        colors: theme === 'dark' ? ['#1a0033', '#2d1b4e', '#4a2c6d'] : ['#fef3c7', '#fde68a', '#fcd34d'],
      };
    }
    const totalBindus = oracleData.ashtakavarga.total_bindus;
    const strength = Math.round((totalBindus / 337) * 100); // 337 is theoretical max

    if (strength >= 80) {
      return {
        theme: 'Breakthrough',
        sentiment: 'positive',
        colors: ['#ff6b35', '#ffd700', '#ff8c5a']
      };
    } else if (strength >= 50) {
      return {
        theme: 'Stability',
        sentiment: 'neutral',
        colors: ['#1a0033', '#2d1b4e', '#4a2c6d']
      };
    } else {
      return {
        theme: 'Reflection',
        sentiment: 'caution',
        colors: ['#2c3e50', '#34495e', '#5d6d7e']
      };
    }
  };

  const renderAnalysisModeTabs = () => (
    <View style={[styles.analysisModeTabs, themedMutedSurface]}>
      {ASHTAKVARGA_ANALYSIS_MODES.map((mode) => {
        const isActive = analysisMode === mode.key;
        return (
          <TouchableOpacity
            key={mode.key}
            style={[
              styles.analysisModeTab,
              isActive && themedAccentSurface,
            ]}
            onPress={() => setAnalysisMode(mode.key)}
          >
            <Ionicons
              name={mode.icon}
              size={17}
              color={isActive ? colors.selectionText : colors.textSecondary}
            />
            <Text style={[styles.analysisModeTabText, { color: isActive ? colors.selectionText : colors.textSecondary }]}>
              {mode.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );

  const renderAnalysisBenefit = (iconName, text) => (
    <View style={styles.analysisBenefitRow} key={text}>
      <Ionicons name={iconName} size={16} color={colors.primary} />
      <Text style={[styles.analysisBenefitText, { color: colors.textSecondary }]}>{text}</Text>
    </View>
  );

  const renderAnalysisAnswer = (expectedMode) => {
    const headline = completeOracleData?.headline || completeOracleData?.oracle_message || '';
    const sections = Array.isArray(completeOracleData?.sections) ? completeOracleData.sections : [];
    if (!completeOracleData) return null;
    if (expectedMode && analysisResultMode && analysisResultMode !== expectedMode) return null;

    return (
      <View style={[styles.analysisAnswerCard, themedSurface]}>
        <Text style={[styles.analysisAnswerTitle, { color: colors.text }]}>
          {lastAskedQuestion ? 'Answer' : 'Transit Overview'}
        </Text>
        {lastAskedQuestion ? (
          <Text style={[styles.analysisAnswerQuestion, { color: colors.primary }]}>Q: {lastAskedQuestion}</Text>
        ) : null}
        {headline ? (
          <Text style={[styles.analysisAnswerHeadline, { color: colors.textSecondary }]}>{headline}</Text>
        ) : null}
        {sections.map((section, index) => (
          <View key={`${section.title}-${index}`} style={styles.analysisAnswerSection}>
            <Text style={[styles.analysisAnswerSectionTitle, { color: colors.text }]}>{section.title}</Text>
            {(section.bullets || []).map((bullet, bulletIndex) => (
              <Text key={`${section.title}-${bulletIndex}`} style={[styles.bulletPoint, { color: colors.textSecondary }]}>
                • {String(bullet)}
              </Text>
            ))}
          </View>
        ))}
      </View>
    );
  };

  const renderBirthAnalysisPanel = () => (
    <View style={[styles.analysisPanelCard, themedSurface]}>
      <View style={styles.analysisPanelHeader}>
        <View style={[styles.analysisPanelIcon, { backgroundColor: colors.selectionSurface }]}>
          <Ionicons name="person-circle-outline" size={24} color={colors.selectionText} />
        </View>
        <View style={styles.analysisPanelTitleBlock}>
          <Text style={[styles.analysisPanelTitle, { color: colors.text }]}>Birth Chart Ashtakvarga Study</Text>
          <Text style={[styles.analysisPanelSubtitle, { color: colors.textSecondary }]}>
            A full chart study from your bindus, houses, dasha context, and life-area strengths.
          </Text>
        </View>
      </View>
      <View style={styles.analysisBenefits}>
        {renderAnalysisBenefit('home-outline', 'Lifelong strengths and weaker houses')}
        {renderAnalysisBenefit('briefcase-outline', 'Career, relationship, money, and health themes')}
        {renderAnalysisBenefit('refresh-circle-outline', 'Saved studies reopen without using credits')}
      </View>
      {renderLifePredictionsCta()}
    </View>
  );

  const renderTransitAnalysisPanel = () => {
    const selectedLabel = selectedDate?.toLocaleDateString?.('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    }) || 'selected date';

    return (
      <>
        <View style={[styles.analysisPanelCard, themedSurface]}>
          <View style={styles.analysisPanelHeader}>
            <View style={[styles.analysisPanelIcon, { backgroundColor: colors.selectionSurface }]}>
              <Ionicons name="today-outline" size={24} color={colors.selectionText} />
            </View>
            <View style={styles.analysisPanelTitleBlock}>
              <Text style={[styles.analysisPanelTitle, { color: colors.text }]}>Transit Ashtakvarga Study</Text>
              <Text style={[styles.analysisPanelSubtitle, { color: colors.textSecondary }]}>
                See how the selected date activates your birth chart strengths and pressure points.
              </Text>
            </View>
          </View>
          <DateNavigator
            date={selectedDate}
            onDateChange={setSelectedDate}
            cosmicTheme={true}
            resetDate={birthData ? (parseCalendarDateInput(birthData.date) || new Date()) : new Date()}
          />
          <View style={styles.analysisBenefits}>
            {renderAnalysisBenefit('calendar-outline', `Reading date: ${selectedLabel}`)}
            {renderAnalysisBenefit('trending-up-outline', 'Supportive and sensitive houses right now')}
            {renderAnalysisBenefit('compass-outline', 'Timing guidance from SAV and BAV')}
          </View>
          <View style={styles.analysisQuestionActions}>
            <TouchableOpacity
              style={[styles.analysisAskButton, { backgroundColor: colors.primary, opacity: loadingInsight ? 0.7 : 1 }]}
              onPress={requestAshtakavargaOverview}
              disabled={loadingInsight}
            >
              {loadingInsight ? (
                  <ActivityIndicator size="small" color={colors.onPrimary} />
              ) : (
                <>
                  <Ionicons name="analytics-outline" size={16} color={colors.onPrimary} />
                  <Text style={styles.analysisAskButtonText}>Generate Transit Reading</Text>
                </>
              )}
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.analysisHistoryButton, { borderColor: colors.cardBorder, backgroundColor: colors.surfaceMuted }]}
              onPress={() => navigation.navigate('AshtakvargaHistory')}
            >
              <Ionicons name="time-outline" size={15} color={colors.textSecondary} />
              <Text style={[styles.analysisHistoryButtonText, { color: colors.textSecondary }]}>History</Text>
            </TouchableOpacity>
          </View>
        </View>
        {renderAnalysisAnswer('transit')}
      </>
    );
  };

  const renderAskMessage = (message) => {
    if (message.role === 'user') {
      return (
        <View key={message.id} style={styles.askUserBubbleRow}>
          <View style={[styles.askUserBubble, { backgroundColor: colors.primary }]}>
            <Text style={[styles.askUserText, { color: colors.onPrimary }]}>{message.text}</Text>
          </View>
        </View>
      );
    }

    const answer = message.data || {};
    const headline = answer.headline || answer.oracle_message || '';
    const sections = Array.isArray(answer.sections) ? answer.sections : [];

    return (
      <View key={message.id} style={styles.askAssistantBubbleRow}>
        <View style={[styles.askAssistantAvatar, { backgroundColor: colors.selectionSurface }]}>
          <Ionicons name="sparkles-outline" size={16} color={colors.selectionText} />
        </View>
        <View style={[styles.askAssistantBubble, themedMutedSurface]}>
          {headline ? (
            <Text style={[styles.askAssistantHeadline, { color: colors.text }]}>{headline}</Text>
          ) : null}
          {sections.map((section, sectionIndex) => (
            <View key={`${message.id}-${section.title}-${sectionIndex}`} style={styles.askAssistantSection}>
              {section.title ? (
                <Text style={[styles.askAssistantSectionTitle, { color: colors.text }]}>{section.title}</Text>
              ) : null}
              {(section.bullets || []).map((bullet, bulletIndex) => (
                <Text key={`${message.id}-${sectionIndex}-${bulletIndex}`} style={[styles.askAssistantBullet, { color: colors.textSecondary }]}>
                  • {String(bullet)}
                </Text>
              ))}
            </View>
          ))}
          {!headline && sections.length === 0 ? (
            <Text style={[styles.askAssistantBullet, { color: colors.textSecondary }]}>
              I found your Ashtakvarga answer, but it came back without readable details. Try asking again with a more specific life area.
            </Text>
          ) : null}
        </View>
      </View>
    );
  };

  const renderAskAnalysisPanel = () => (
    <View style={[styles.askChatCard, themedSurface]}>
      <View style={styles.askChatHeader}>
        <View style={styles.askChatTitleBlock}>
          <Text style={[styles.analysisQuestionTitle, { color: colors.text }]}>Ask Ashtakvarga</Text>
          <Text style={[styles.analysisQuestionSubtitle, { color: colors.textSecondary }]}>
            Keep asking follow-ups about career, money, marriage, weak houses, planets, or timing.
          </Text>
        </View>
        <TouchableOpacity
          style={[styles.analysisHistoryButton, { borderColor: colors.cardBorder, backgroundColor: colors.surfaceMuted }]}
          onPress={() => navigation.navigate('AshtakvargaHistory')}
        >
          <Ionicons name="time-outline" size={15} color={colors.textSecondary} />
          <Text style={[styles.analysisHistoryButtonText, { color: colors.textSecondary }]}>History</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.askMessages}>
        {askMessages.length === 0 ? (
          <View style={styles.askAssistantBubbleRow}>
            <View style={[styles.askAssistantAvatar, { backgroundColor: colors.selectionSurface }]}>
              <Ionicons name="sparkles-outline" size={16} color={colors.selectionText} />
            </View>
            <View style={[styles.askAssistantBubble, themedMutedSurface]}>
              <Text style={[styles.askAssistantHeadline, { color: colors.text }]}>
                What would you like to understand from your Ashtakvarga?
              </Text>
              <Text style={[styles.askAssistantBullet, { color: colors.textSecondary }]}>
                Start with one life area, then ask follow-ups as the study unfolds.
              </Text>
            </View>
          </View>
        ) : (
          askMessages.map(renderAskMessage)
        )}
      </View>

      <GHScrollView
        horizontal
        nestedScrollEnabled
        keyboardShouldPersistTaps="handled"
        showsHorizontalScrollIndicator={false}
        style={styles.analysisSuggestionScroller}
        contentContainerStyle={styles.analysisSuggestionRow}
        scrollEventThrottle={16}
      >
        {ASHTAKVARGA_QUESTION_SUGGESTIONS.map((suggestion) => (
          <TouchableOpacity
            key={suggestion}
            style={[styles.analysisSuggestionChip, themedMutedSurface]}
            onPress={() => {
              setAnalysisQuestion(suggestion);
              probeAshtakavargaAnalysis(suggestion);
            }}
            disabled={loadingInsight}
          >
            <Text style={[styles.analysisSuggestionText, { color: colors.textSecondary }]}>{suggestion}</Text>
          </TouchableOpacity>
        ))}
      </GHScrollView>

      <View style={styles.askComposerToolbar}>
        <TouchableOpacity
          style={[styles.askComposerHistoryLink, themedMutedSurface]}
          onPress={() => navigation.navigate('AshtakvargaHistory')}
        >
          <Ionicons name="time-outline" size={15} color={colors.textSecondary} />
          <Text style={[styles.analysisHistoryButtonText, { color: colors.textSecondary }]}>History</Text>
        </TouchableOpacity>
      </View>

      <View style={[styles.askComposer, themedSurface]}>
        <TextInput
          value={analysisQuestion}
          onChangeText={setAnalysisQuestion}
          placeholder="Ask a follow-up..."
          placeholderTextColor={colors.textTertiary}
          multiline
          textAlignVertical="center"
          style={[styles.askComposerInput, { color: colors.text }]}
        />
        <TouchableOpacity
          style={[styles.askSendButton, { backgroundColor: colors.primary, opacity: loadingInsight || !analysisQuestion.trim() ? 0.7 : 1 }]}
          onPress={requestAshtakavargaAnalysis}
          disabled={loadingInsight || !analysisQuestion.trim()}
        >
          {loadingInsight ? (
            <ActivityIndicator size="small" color={colors.onPrimary} />
          ) : (
            <Ionicons name="send" size={18} color={colors.onPrimary} />
          )}
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderOraclesPulse = () => {
    const activePanel =
      analysisMode === 'transit'
        ? renderTransitAnalysisPanel()
        : analysisMode === 'ask'
          ? renderAskAnalysisPanel()
          : renderBirthAnalysisPanel();

    return (
      <ScrollView
        style={styles.tabContent}
        contentContainerStyle={styles.analysisTabContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="none"
      >
        <View style={styles.titleContainer}>
          <Text style={[styles.mapTitle, { color: colors.text }]}>Ashtakvarga Study</Text>
          <Text style={[styles.mapSubtitle, { color: colors.textSecondary }]}>
            Choose the kind of study you want before using credits.
          </Text>
        </View>

        {renderAnalysisModeTabs()}

        {activePanel}
      </ScrollView>
    );
  };

  const renderDestinyMap = () => {
    if (!oracleData || !oracleData.ashtakavarga || !oracleData.ashtakavarga.sarvashtakavarga) {
      return (
        <ScrollView style={styles.tabContent} contentContainerStyle={[styles.tabContent, { flex: 1, justifyContent: 'center', alignItems: 'center', paddingVertical: 40 }]} showsVerticalScrollIndicator={false}>
          <Text style={[styles.loadingSubtext, { color: colors.textSecondary, textAlign: 'center', marginBottom: 12 }]}>
            Ashtakvarga data couldn't be loaded.
          </Text>
          <Text style={[styles.loadingSubtext, { color: colors.textTertiary, textAlign: 'center', fontSize: 14 }]}>
            Please try again or select another date.
          </Text>
          {birthData && (
            <TouchableOpacity
              onPress={() => fetchAshtakvargaData(birthData, selectedDate)}
              style={{ marginTop: 20, paddingVertical: 12, paddingHorizontal: 24, backgroundColor: colors.primary, borderRadius: 24 }}
            >
              <Text style={{ color: colors.onPrimary, fontWeight: '700' }}>Retry</Text>
            </TouchableOpacity>
          )}
        </ScrollView>
      );
    }

    return (
      <ScrollView style={styles.tabContent} contentContainerStyle={{ paddingBottom: 20 }} showsVerticalScrollIndicator={false}>
        <View style={styles.titleContainer}>
          <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>12-HOUSE STRENGTH MAP</Text>
          <Text style={[styles.mapTitle, { color: colors.text }]}>Sarvashtakvarga</Text>
          <Text style={[styles.mapSubtitle, { color: colors.textSecondary }]}>Tap a house to understand its support, sensitivity and yearly timing.</Text>
        </View>

        <DateNavigator
          date={selectedDate}
          onDateChange={setSelectedDate}
          cosmicTheme={true}
          resetDate={birthData ? (parseCalendarDateInput(birthData.date) || new Date()) : new Date()}
        />

        <View style={[styles.chartContainer, themedSurface]}>
          <AshtakvargaChart
            chartData={oracleData.chart_data}
            ashtakvargaData={oracleData.chart_ashtakavarga}
            birthAshtakvargaData={birthOracleData?.chart_ashtakavarga}
            onHousePress={(houseNum, bindus, signName) => {
              openSecretScroll(signName, bindus, houseNum - 1);
            }}
            cosmicTheme={false}
          />
        </View>
      </ScrollView>
    );
  };

  const renderLifePredictionsCta = () => {
    if (loadingLifePredictions || lifePredictionsCacheChecking) {
      return (
        <View style={styles.lifePredictionsContainer}>
          <View style={[styles.lifePredictionsButton, styles.loadingButton]}>
            <LinearGradient
              colors={[colors.cosmicSurface, colors.cosmicRaised, colors.cosmicSurface]}
              style={styles.lifePredictionsGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              {loadingLifePredictions ? (
                <View style={styles.loadingContent}>
                  <Animated.View
                    style={[
                      styles.loadingIconContainer,
                      {
                        transform: [{
                          rotate: loadingRotateAnim.interpolate({
                            inputRange: [0, 1],
                            outputRange: ['0deg', '360deg']
                          })
                        }]
                      }
                    ]}
                  >
                    <Text style={styles.lifePredictionsIconLarge}>✨</Text>
                  </Animated.View>
                  <Text style={[styles.lifePredictionsText, { color: colors.textInverse }]}>
                    Reviewing chart strength patterns...
                  </Text>
                  <View style={styles.progressContainer}>
                    <View style={[styles.progressBar, { backgroundColor: colors.cosmicLine }]}>
                      <View style={[styles.progressFill, { width: `${loadingProgress}%`, backgroundColor: colors.accent }]} />
                    </View>
                    <Text style={[styles.progressText, { color: colors.accent }]}>{Math.round(loadingProgress)}%</Text>
                  </View>
                </View>
              ) : (
                <View style={styles.loadingContent}>
                  <ActivityIndicator size="small" color={colors.accent} style={{ marginBottom: 8 }} />
                  <Text style={[styles.lifePredictionsText, { color: colors.textInverse }]}>Checking saved study…</Text>
                </View>
              )}
            </LinearGradient>
          </View>
        </View>
      );
    }

    return (
      <View style={styles.lifePredictionsContainer}>
        <TouchableOpacity
          style={styles.lifePredictionsButton}
          onPress={onLifePredictionsMainCta}
          activeOpacity={0.9}
        >
          <LinearGradient
            colors={[colors.cosmicSurface, colors.cosmicRaised, colors.cosmicSurface]}
            style={styles.lifePredictionsGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <>
              <View style={[styles.lifePredictionsIconSeal, { borderColor: colors.accent }]}>
                <Ionicons name="sparkles-outline" size={22} color={colors.accent} />
              </View>
              <Text style={[styles.lifePredictionsHeadline, { color: colors.textInverse }]}>Ashtakvarga Study</Text>
              <Text style={[styles.lifePredictionsTeaser, { color: colors.textInverseMuted }]}>
                Full study from your bindus — career, relationships, timing windows, dasha & remedies.
              </Text>
              <View style={styles.lifePredictionsChips}>
                <Text style={[styles.lifePredictionsChip, { color: colors.textInverse, borderColor: colors.cosmicLine }]}>12 houses</Text>
                <Text style={[styles.lifePredictionsChip, { color: colors.textInverse, borderColor: colors.cosmicLine }]}>Transits</Text>
                <Text style={[styles.lifePredictionsChip, { color: colors.textInverse, borderColor: colors.cosmicLine }]}>Dasha</Text>
              </View>
              <View style={styles.lifePredictionsCtaRow}>
                <Text style={[styles.lifePredictionsCtaText, { color: colors.accentSoft }]}>{Platform.OS === 'ios' ? 'Open life study' : 'Open life insights'}</Text>
                <Ionicons name="arrow-forward" size={18} color={colors.accentSoft} style={{ marginLeft: 6 }} />
              </View>
              <Text style={[styles.lifePredictionsCreditHint, { color: colors.textInverseMuted }]}>
                {lifePredictionsCreditCost} credits first run · saved study replays free
              </Text>
              <Text style={[styles.lifePredictionsSubtext, { color: colors.textInverseMuted }]}>Vinay Aditya · Ashtakavarga methodology</Text>
            </>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    );
  };

  const renderBavTab = () => (
    <ScrollView style={styles.tabContent} contentContainerStyle={{ paddingBottom: 20 }} showsVerticalScrollIndicator={false}>
      <View style={styles.titleContainer}>
        <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>PLANETARY CONTRIBUTION</Text>
        <Text style={[styles.mapTitle, { color: colors.text }]}>Bhinnashtakvarga</Text>
        <Text style={[styles.mapSubtitle, { color: colors.textSecondary }]}>Planet-wise bindu maps. Tap any graha to open its full sign spread.</Text>
      </View>

      <View style={styles.planetaryToggle}>
        <Text style={[styles.toggleTitle, { color: colors.text }]}>Bhinnashtakvarga Charts</Text>
        <Text style={[styles.bavHint, { color: colors.textSecondary }]}>
          Each graha shows where it receives support across the zodiac.
        </Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].map(planet => {
            const planetChart = oracleData?.ashtakavarga?.individual_charts?.[planet];
            const totalBindus = planetChart?.total || 0;
            return (
              <TouchableOpacity
                key={planet}
                style={[styles.planetButton, themedSurface]}
                onPress={() => openPlanetChart(planet, planetChart)}
              >
                <Text style={[styles.planetIcon, { color: colors.primary }]}>{getPlanetIcon(planet)}</Text>
                <Text style={[styles.planetName, { color: colors.text }]}>{planet}</Text>
                <Text style={[styles.planetBindus, { color: colors.accent }]}>{totalBindus}</Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>
    </ScrollView>
  );

  const renderCombinedMatrixTab = () => {
    const individualCharts = oracleData?.ashtakavarga?.individual_charts || {};
    const savHouses = oracleData?.chart_ashtakavarga || {};
    const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
    const rows = Array.from({ length: 12 }, (_, index) => {
      const houseNum = index + 1;
      const houseData = savHouses?.[String(houseNum)];
      const signIndex =
        typeof houseData?.sign === 'number'
          ? houseData.sign
          : Number.isFinite(Number(houseData?.sign))
            ? Number(houseData.sign)
            : index;
      const signLabel = SIGN_SHORT_NAMES[signIndex] || SIGN_SHORT_NAMES[index];

      return {
        houseNum,
        sign: `${signLabel} (H${houseNum})`,
        values: planets.map((planet) => individualCharts?.[planet]?.bindus?.[signIndex] ?? 0),
        sav: houseData?.bindus ?? 0,
      };
    });

    return (
      <ScrollView style={styles.tabContent} contentContainerStyle={{ paddingBottom: 20 }} showsVerticalScrollIndicator={false}>
        <View style={styles.titleContainer}>
          <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>COMPLETE CALCULATION</Text>
          <Text style={[styles.mapTitle, { color: colors.text }]}>SAV + BAV Matrix</Text>
          <Text style={[styles.mapSubtitle, { color: colors.textSecondary }]}>See each house, its occupying sign, and the corresponding Bhinnashtakvarga values together with the Sarvashtakvarga total.</Text>
        </View>

        <View style={[styles.matrixCard, themedSurface]}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View>
              <View style={[styles.matrixRow, styles.matrixHeaderRow, { borderBottomColor: colors.borderStrong, backgroundColor: colors.surfaceMuted }]}>
                <Text style={[styles.matrixHeaderCell, styles.matrixSignCell, { color: colors.text }]}>House</Text>
                {planets.map((planet) => (
                  <Text key={planet} style={[styles.matrixHeaderCell, { color: colors.text }]}>{planet.slice(0, 2)}</Text>
                ))}
                <Text style={[styles.matrixHeaderCell, styles.matrixSavCell, { color: colors.primary }]}>SAV</Text>
              </View>

              {rows.map((row, rowIndex) => (
                <View
                  key={row.sign}
                  style={[
                    styles.matrixRow,
                    rowIndex % 2 === 0
                      ? { backgroundColor: colors.backgroundSecondary }
                      : null,
                    { borderBottomColor: colors.cardBorder },
                  ]}
                >
                  <Text style={[styles.matrixCell, styles.matrixSignCell, { color: colors.text }]}>{row.sign}</Text>
                  {row.values.map((value, idx) => (
                    <Text key={`${row.sign}-${planets[idx]}`} style={[styles.matrixCell, { color: colors.textSecondary }]}>
                      {value}
                    </Text>
                  ))}
                  <Text style={[styles.matrixCell, styles.matrixSavCell, { color: colors.primary }]}>
                    {row.sav}
                  </Text>
                </View>
              ))}
            </View>
          </ScrollView>
        </View>

        <Text style={[styles.matrixHint, { color: colors.textSecondary }]}>
          Read across a sign to compare each graha’s BAV support. The last column shows the SAV total for that same sign/house position in your chart view.
        </Text>
      </ScrollView>
    );
  };

  const renderAdvancedTab = () => {
    const advanced = oracleData?.advanced_ashtakavarga;
    const selected = advanced?.shodhya_pinda?.[selectedAdvancedPlanet];
    const selectedPrastara = advanced?.prastara?.[selectedAdvancedPlanet];
    const reductionRows = [
      [t('ashtakavargaUi.labels.raw'), selected?.raw_bav],
      [t('ashtakavargaUi.labels.afterTrikona'), selected?.after_trikona],
      [t('ashtakavargaUi.labels.afterEkadhipatya'), selected?.after_ekadhipatya],
    ];
    const chooseProfile = (profileId) => {
      setAshtakavargaProfile(profileId);
      const natalDate = parseCalendarDateInput(birthData?.date);
      if (natalDate) setSelectedDate(natalDate);
    };

    return (
      <ScrollView style={styles.tabContent} contentContainerStyle={styles.advancedContent} showsVerticalScrollIndicator={false}>
        <View style={styles.titleContainer}>
          <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{t('ashtakavargaUi.advanced.eyebrow').toUpperCase()}</Text>
          <Text style={[styles.mapTitle, { color: colors.text }]}>{t('ashtakavargaUi.advanced.title')}</Text>
          <Text style={[styles.mapSubtitle, { color: colors.textSecondary }]}>{t('ashtakavargaUi.advanced.subtitle')}</Text>
        </View>

        <View style={[styles.advancedCard, themedSurface]}>
          <Text style={[styles.advancedCardTitle, { color: colors.text }]}>{t('ashtakavargaUi.advanced.convention')}</Text>
          <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{t('ashtakavargaUi.advanced.conventionBody')}</Text>
          <View style={styles.profileButtonRow}>
            {ASHTAKVARGA_PROFILES.map((profile) => {
              const active = ashtakavargaProfile === profile.id;
              return (
                <TouchableOpacity key={profile.id} accessibilityRole="button" accessibilityState={{ selected: active }} onPress={() => chooseProfile(profile.id)} style={[styles.profileButton, { backgroundColor: active ? colors.primary : colors.surfaceMuted, borderColor: active ? colors.primary : colors.borderStrong }]}>
                  <Text style={[styles.profileButtonTitle, { color: active ? colors.onPrimary : colors.text }]}>{profile.label}</Text>
                  <Text style={[styles.profileButtonDetail, { color: active ? colors.onPrimary : colors.textSecondary }]}>Ekādhipatya · 7 grahas{profile.id === 'parasharas_light_7' ? ' · Lagna' : ''}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
          <Text style={[styles.advancedAudit, { color: colors.textSecondary }]}>{advanced ? t('ashtakavargaUi.advanced.active', { school: advanced.convention?.school }) : t('ashtakavargaUi.advanced.natalBody')}</Text>
        </View>

        {!advanced ? (
          <View style={[styles.advancedCard, themedSurface]}>
            <Text style={[styles.advancedCardTitle, { color: colors.text }]}>{t('ashtakavargaUi.advanced.natalRequired')}</Text>
            <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{t('ashtakavargaUi.advanced.natalBody')}</Text>
            <TouchableOpacity onPress={() => { const natalDate = parseCalendarDateInput(birthData?.date); if (natalDate) setSelectedDate(natalDate); }} style={[styles.advancedAction, { backgroundColor: colors.primary }]}><Text style={{ color: colors.onPrimary, fontWeight: '800' }}>{t('ashtakavargaUi.advanced.showNatal')}</Text></TouchableOpacity>
          </View>
        ) : (
          <>
            <View style={[styles.advancedCard, themedSurface]}>
              <Text style={[styles.advancedEyebrow, { color: colors.primary }]}>{t('ashtakavargaUi.advanced.tableTitle').toUpperCase()}</Text>
              <Text style={[styles.advancedCardTitle, { color: colors.text }]}>{t('ashtakavargaUi.advanced.tableTitle')}</Text>
              <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{t('ashtakavargaUi.advanced.tableBody')}</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.advancedTableScroll}>
                <View>
                  <View style={[styles.advancedTableRow, styles.advancedTableHeader, { backgroundColor: colors.surfaceMuted, borderBottomColor: colors.cardBorder }]}>
                    {[t('ashtakavargaUi.labels.graha'), t('ashtakavargaUi.labels.raw'), t('ashtakavargaUi.labels.reduced'), t('ashtakavargaUi.labels.rashi'), t('ashtakavargaUi.labels.graha'), t('ashtakavargaUi.labels.shodhya')].map((label, index) => <Text key={`${label}-${index}`} style={[styles.advancedTableCell, index === 0 && styles.advancedTableFirstCell, { color: colors.text }]}>{label}</Text>)}
                  </View>
                  {ADVANCED_PLANETS.map((planet) => {
                    const row = advanced.shodhya_pinda?.[planet];
                    const active = selectedAdvancedPlanet === planet;
                    const values = [planet, Object.values(row?.raw_bav || {}).reduce((sum, value) => sum + Number(value), 0), Object.values(row?.after_ekadhipatya || {}).reduce((sum, value) => sum + Number(value), 0), row?.rashi_pinda, row?.graha_pinda, row?.shodhya_pinda];
                    return <TouchableOpacity key={planet} onPress={() => setSelectedAdvancedPlanet(planet)} style={[styles.advancedTableRow, { backgroundColor: active ? colors.surfaceMuted : 'transparent', borderBottomColor: colors.borderStrong }]}>{values.map((value, index) => <Text key={`${planet}-${index}`} style={[styles.advancedTableCell, index === 0 && styles.advancedTableFirstCell, index === 5 && styles.advancedTableStrong, { color: index === 5 || active ? colors.primary : colors.textSecondary }]}>{value ?? '—'}</Text>)}</TouchableOpacity>;
                  })}
                </View>
              </ScrollView>
            </View>

            <View style={[styles.advancedCard, themedSurface]}>
              <Text style={[styles.advancedEyebrow, { color: colors.primary }]}>{t('ashtakavargaUi.advanced.audit').toUpperCase()}</Text>
              <Text style={[styles.advancedCardTitle, { color: colors.text }]}>{t('ashtakavargaUi.advanced.inspector', { planet: selectedAdvancedPlanet })}</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.advancedPlanetChips}>
                {ADVANCED_PLANETS.map((planet) => <TouchableOpacity key={planet} onPress={() => setSelectedAdvancedPlanet(planet)} style={[styles.advancedPlanetChip, { backgroundColor: selectedAdvancedPlanet === planet ? colors.primary : colors.surfaceMuted, borderColor: selectedAdvancedPlanet === planet ? colors.primary : colors.borderStrong }]}><Text style={{ color: selectedAdvancedPlanet === planet ? colors.onPrimary : colors.textSecondary, fontWeight: '800', fontSize: 11 }}>{planet}</Text></TouchableOpacity>)}
              </ScrollView>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.advancedTableScroll}>
                <View>
                  <View style={[styles.reductionRow, styles.advancedTableHeader, { backgroundColor: colors.surfaceMuted, borderBottomColor: colors.borderStrong }]}><Text style={[styles.reductionLabel, { color: colors.text }]}>{t('ashtakavargaUi.labels.stage')}</Text>{SIGN_SHORT_NAMES.map((sign) => <Text key={sign} style={[styles.reductionCell, { color: colors.text }]}>{sign.slice(0, 2)}</Text>)}</View>
                  {reductionRows.map(([label, values]) => <View key={label} style={[styles.reductionRow, { borderBottomColor: colors.borderStrong }]}><Text style={[styles.reductionLabel, { color: colors.text }]}>{label}</Text>{Array.from({ length: 12 }, (_, sign) => <Text key={sign} style={[styles.reductionCell, { color: colors.textSecondary }]}>{values?.[String(sign)] ?? 0}</Text>)}</View>)}
                </View>
              </ScrollView>
              <View style={[styles.traceBlock, { backgroundColor: colors.surfaceMuted }]}><Text style={[styles.traceTitle, { color: colors.text }]}>Trikona Shodhana</Text>{selected?.trikona_trace?.map((row) => <Text key={row.signs.join('-')} style={[styles.traceText, { color: colors.textSecondary }]}>{row.signs.join(' · ')}: {row.before.join('/')} → {row.after.join('/')}</Text>)}</View>
              <View style={[styles.traceBlock, { backgroundColor: colors.surfaceMuted }]}><Text style={[styles.traceTitle, { color: colors.text }]}>Ekadhipatya Shodhana</Text>{selected?.ekadhipatya_trace?.map((row) => <Text key={row.lord} style={[styles.traceText, { color: colors.textSecondary }]}>{row.signs.join(' · ')}: {row.before.join('/')} → {row.after.join('/')}</Text>)}</View>

              <Text style={[styles.advancedSubheading, { color: colors.text }]}>{t('ashtakavargaUi.advanced.prastara', { planet: selectedAdvancedPlanet })}</Text>
              <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{t('ashtakavargaUi.advanced.prastaraBody')}</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.advancedTableScroll}>
                <View>
                  <View style={[styles.reductionRow, styles.advancedTableHeader, { backgroundColor: colors.surfaceMuted, borderBottomColor: colors.borderStrong }]}><Text style={[styles.reductionLabel, { color: colors.text }]}>{t('ashtakavargaUi.labels.contributor')}</Text>{SIGN_SHORT_NAMES.map((sign) => <Text key={sign} style={[styles.reductionCell, { color: colors.text }]}>{sign.slice(0, 2)}</Text>)}</View>
                  {selectedPrastara?.contributors?.map((contributor) => <View key={contributor} style={[styles.reductionRow, { borderBottomColor: colors.borderStrong }]}><Text style={[styles.reductionLabel, { color: colors.text }]}>{contributor}</Text>{Array.from({ length: 12 }, (_, sign) => { const bindu = selectedPrastara.matrix?.[contributor]?.[String(sign)] ?? 0; return <Text key={sign} style={[styles.reductionCell, bindu ? { backgroundColor: colors.primary, color: colors.onPrimary } : { color: colors.textSecondary }]}>{bindu}</Text>; })}</View>)}
                  <View style={[styles.reductionRow, { backgroundColor: colors.surfaceMuted, borderBottomColor: colors.borderStrong }]}><Text style={[styles.reductionLabel, { color: colors.text, fontWeight: '900' }]}>{t('ashtakavargaUi.labels.bavTotal')}</Text>{Array.from({ length: 12 }, (_, sign) => <Text key={sign} style={[styles.reductionCell, { color: colors.primary, fontWeight: '900' }]}>{selectedPrastara?.sign_totals?.[String(sign)] ?? 0}</Text>)}</View>
                </View>
              </ScrollView>
            </View>

            <View style={[styles.advancedCard, themedSurface]}>
              <Text style={[styles.advancedEyebrow, { color: colors.primary }]}>{t('ashtakavargaUi.advanced.kakshyaTitle').toUpperCase()}</Text>
              <Text style={[styles.advancedCardTitle, { color: colors.text }]}>{t('ashtakavargaUi.advanced.kakshyaTitle')}</Text>
              <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{t('ashtakavargaUi.advanced.kakshyaBody')}</Text>
              {ADVANCED_PLANETS.map((planet) => { const row = advanced.natal_kakshya?.[planet]; return <View key={planet} style={[styles.kakshyaCard, { backgroundColor: colors.surfaceMuted, borderColor: row?.active ? colors.success : colors.error }]}><View style={styles.advancedCardHeader}><Text style={[styles.kakshyaPlanet, { color: colors.text }]}>{planet}</Text><Text style={[styles.kakshyaStatus, { color: row?.active ? colors.success : colors.error }]}>{row?.active ? t('ashtakavargaUi.labels.bindu').toUpperCase() : t('ashtakavargaUi.labels.noBindu').toUpperCase()}</Text></View><Text style={[styles.kakshyaCoordinate, { color: colors.text }]}>{row?.sign} {Number(row?.degree_in_sign || 0).toFixed(2)}°</Text><Text style={[styles.advancedBody, { color: colors.primary }]}>K{row?.kakshya_number} · {row?.kakshya_ruler}</Text><Text style={[styles.traceText, { color: colors.textSecondary }]}>{row?.start_degree}° ≤ degree &lt; {row?.end_degree}° · BAV {row?.sign_bav_total}</Text></View>; })}
            </View>

            <View style={[styles.advancedCard, themedSurface]}>
              <Text style={[styles.advancedEyebrow, { color: colors.primary }]}>{t('ashtakavargaUi.advanced.timingTitle').toUpperCase()}</Text>
              <Text style={[styles.advancedCardTitle, { color: colors.text }]}>{t('ashtakavargaUi.advanced.timingTitle')}</Text>
              <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{t('ashtakavargaUi.advanced.timingBody')}</Text>
              {Object.entries(advanced.classical_timing || {}).map(([key, row]) => <View key={key} style={[styles.timingCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}><Text style={[styles.traceTitle, { color: colors.text }]}>{ADVANCED_TIMING_LABELS[key] || key}</Text><Text style={[styles.timingCoordinate, { color: colors.text }]}>{row.nakshatra} · {row.rashi}</Text><Text style={[styles.advancedBody, { color: colors.primary }]}>{row.raw_rekhas} × {row.shodhya_pinda} = {row.product}</Text><Text style={[styles.traceText, { color: colors.textSecondary }]}>Nakshatra group: {row.vimshottari_group?.join(', ')}{`\n`}Rāśi trines: {row.rashi_trines?.join(', ')}</Text></View>)}
            </View>
          </>
        )}
      </ScrollView>
    );
  };

  const renderTransitDesk = () => {
    const transit = classicalTransitData;
    const filterOptions = [
      ['all', t('ashtakavargaUi.labels.all')],
      ['kakshya_ingress', t('ashtakavargaUi.labels.kakshya')],
      ['rashi_ingress', t('ashtakavargaUi.labels.rashi')],
      ['nakshatra_ingress', 'Nakshatra'],
      ['direction_station', t('ashtakavargaUi.labels.stations')],
    ];
    const eventLabels = {
      kakshya_ingress: t('ashtakavargaUi.labels.kakshya'),
      rashi_ingress: t('ashtakavargaUi.labels.rashi'),
      nakshatra_ingress: 'Nakshatra',
      direction_station: t('ashtakavargaUi.labels.stations'),
    };
    const allEvents = transit?.calendar_window?.events || [];
    const visibleEvents = transitEventFilter === 'all'
      ? allEvents
      : allEvents.filter((row) => row.type === transitEventFilter);

    const sensitiveLabel = (row) => {
      if (row?.sensitive_timing?.double_match) return 'Rāśi + Nakshatra ✓';
      if (row?.sensitive_timing?.rashi_match) return 'Rāśi ✓';
      if (row?.sensitive_timing?.nakshatra_match) return 'Nakshatra ✓';
      return '—';
    };

    return (
      <ScrollView style={styles.tabContent} contentContainerStyle={styles.advancedContent} showsVerticalScrollIndicator={false}>
        <View style={styles.titleContainer}>
          <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{t('ashtakavargaUi.transit.eyebrow').toUpperCase()}</Text>
          <Text style={[styles.mapTitle, { color: colors.text }]}>{t('ashtakavargaUi.transit.title')}</Text>
          <Text style={[styles.mapSubtitle, { color: colors.textSecondary }]}>{t('ashtakavargaUi.transit.subtitle')}</Text>
        </View>

        <DateNavigator
          date={selectedDate}
          onDateChange={setSelectedDate}
          cosmicTheme={true}
          resetDate={new Date()}
        />

        <View style={[styles.advancedCard, themedSurface]}>
          <Text style={[styles.advancedCardTitle, { color: colors.text }]}>{t('ashtakavargaUi.advanced.convention')}</Text>
          <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{t('ashtakavargaUi.transit.profileBody')}</Text>
          <View style={styles.profileButtonRow}>
            {ASHTAKVARGA_PROFILES.map((profile) => {
              const active = ashtakavargaProfile === profile.id;
              return (
                <TouchableOpacity
                  key={profile.id}
                  accessibilityRole="button"
                  accessibilityState={{ selected: active }}
                  onPress={() => setAshtakavargaProfile(profile.id)}
                  style={[styles.profileButton, { backgroundColor: active ? colors.primary : colors.surfaceMuted, borderColor: active ? colors.primary : colors.borderStrong }]}
                >
                  <Text style={[styles.profileButtonTitle, { color: active ? colors.onPrimary : colors.text }]}>{profile.label}</Text>
                  <Text style={[styles.profileButtonDetail, { color: active ? colors.onPrimary : colors.textSecondary }]}>Ekādhipatya · 7 grahas{profile.id === 'parasharas_light_7' ? ' · Lagna' : ''}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
          <Text style={[styles.advancedAudit, { color: colors.textSecondary }]}>{transitDeskLoading ? t('ashtakavargaUi.transit.recalculating') : t('ashtakavargaUi.transit.calculation', { school: transit?.convention?.school || 'BAV/SAV/Prastara' })}</Text>
        </View>

        {transitDeskLoading ? (
          <View style={[styles.transitLoadingCard, themedSurface]}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{t('ashtakavargaUi.transit.resolving')}</Text>
          </View>
        ) : !transit ? (
          <View style={[styles.advancedCard, themedSurface]}>
            <Text style={[styles.advancedCardTitle, { color: colors.text }]}>{t('ashtakavargaUi.transit.unavailable')}</Text>
            <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{t('ashtakavargaUi.transit.unavailableBody')}</Text>
          </View>
        ) : (
          <>
            <View style={[styles.advancedCard, themedSurface]}>
              <Text style={[styles.advancedEyebrow, { color: colors.primary }]}>{t('ashtakavargaUi.transit.snapshot').toUpperCase()}</Text>
              <Text style={[styles.advancedCardTitle, { color: colors.text }]}>{t('ashtakavargaUi.transit.snapshot')}</Text>
              <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{t('ashtakavargaUi.transit.snapshotBody')}</Text>
              {(transit.planet_transits || []).map((row) => (
                <View key={row.planet} style={[styles.transitSnapshotCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.borderStrong }]}>
                  <View style={styles.advancedCardHeader}>
                    <Text style={[styles.kakshyaPlanet, { color: colors.text }]}>{row.planet} · {row.retrograde ? t('ashtakavargaUi.labels.retrograde') : t('ashtakavargaUi.labels.direct')}</Text>
                    <Text style={[styles.transitHouse, { color: colors.primary }]}>{t('ashtakavargaUi.labels.natalHouse', { house: row.natal_house })}</Text>
                  </View>
                  <Text style={[styles.kakshyaCoordinate, { color: colors.text }]}>{row.sign} {Number(row.degree_in_sign || 0).toFixed(2)}°</Text>
                  <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{row.nakshatra}</Text>
                  <View style={styles.transitMetricRow}>
                    <View style={[styles.transitMetric, { borderColor: colors.borderStrong }]}><Text style={[styles.transitMetricLabel, { color: colors.textSecondary }]}>{t('ashtakavargaUi.labels.natalBav')}</Text><Text style={[styles.transitMetricValue, { color: colors.text }]}>{row.natal_bav_bindus}</Text></View>
                    <View style={[styles.transitMetric, { borderColor: colors.borderStrong }]}><Text style={[styles.transitMetricLabel, { color: colors.textSecondary }]}>{t('ashtakavargaUi.labels.natalSav')}</Text><Text style={[styles.transitMetricValue, { color: colors.text }]}>{row.natal_sav_bindus}</Text></View>
                    <View style={[styles.transitMetric, { borderColor: row.kakshya?.active ? colors.success : colors.borderStrong }]}><Text style={[styles.transitMetricLabel, { color: colors.textSecondary }]}>{t('ashtakavargaUi.labels.kakshya')}</Text><Text style={[styles.transitMetricValue, { color: row.kakshya?.active ? colors.success : colors.text }]}>K{row.kakshya?.kakshya_number}</Text><Text style={[styles.transitMetricBand, { color: colors.textSecondary }]}>{row.kakshya?.kakshya_ruler} · {row.kakshya?.active ? t('ashtakavargaUi.labels.bindu') : t('ashtakavargaUi.labels.noBindu')}</Text></View>
                  </View>
                  <Text style={[styles.transitSensitiveLine, { color: row.sensitive_timing?.rashi_match || row.sensitive_timing?.nakshatra_match ? colors.primary : colors.textSecondary }]}>{sensitiveLabel(row)}</Text>
                </View>
              ))}
            </View>

            <View style={[styles.advancedCard, themedSurface]}>
              <View style={styles.advancedCardHeader}>
                <View>
                  <Text style={[styles.advancedEyebrow, { color: colors.primary }]}>{t('ashtakavargaUi.transit.current').toUpperCase()}</Text>
                  <Text style={[styles.advancedCardTitle, { color: colors.text }]}>{t('ashtakavargaUi.transit.current')}</Text>
                </View>
                <Text style={[styles.transitHitCount, { color: colors.primary }]}>{transit.sensitive_hits?.length || 0}/7</Text>
              </View>
              {transit.sensitive_hits?.length ? transit.sensitive_hits.map((row) => (
                <View key={row.planet} style={[styles.transitHitCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.borderStrong }]}>
                  <Text style={[styles.traceTitle, { color: colors.text }]}>{row.planet}</Text>
                  <Text style={[styles.timingCoordinate, { color: colors.text }]}>{row.sign} · {row.nakshatra}</Text>
                  <Text style={[styles.traceText, { color: colors.textSecondary }]}>Rāśi {row.sensitive_timing?.rashi_match ? '✓' : '—'} · Nakshatra {row.sensitive_timing?.nakshatra_match ? '✓' : '—'}{`\n`}→ {row.sensitive_timing?.reference_rashi} · {row.sensitive_timing?.reference_nakshatra}</Text>
                </View>
              )) : <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{t('ashtakavargaUi.transit.noMatch')}</Text>}
            </View>

            <View style={[styles.advancedCard, themedSurface]}>
              <Text style={[styles.advancedEyebrow, { color: colors.primary }]}>{t('ashtakavargaUi.transit.nextDays', { days: transit.calendar_window?.days }).toUpperCase()}</Text>
              <Text style={[styles.advancedCardTitle, { color: colors.text }]}>{t('ashtakavargaUi.transit.nextDays', { days: transit.calendar_window?.days })}</Text>
              <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{t('ashtakavargaUi.transit.boundaryBody')}</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.transitFilterRow}>
                {filterOptions.map(([id, label]) => {
                  const active = transitEventFilter === id;
                  return <TouchableOpacity key={id} onPress={() => setTransitEventFilter(id)} style={[styles.transitFilterChip, { backgroundColor: active ? colors.primary : colors.surfaceMuted, borderColor: active ? colors.primary : colors.borderStrong }]}><Text style={[styles.transitFilterText, { color: active ? colors.onPrimary : colors.textSecondary }]}>{label}</Text></TouchableOpacity>;
                })}
              </ScrollView>
              {visibleEvents.length ? visibleEvents.map((event, index) => (
                <View key={`${event.timestamp_utc}-${event.planet}-${event.type}-${index}`} style={[styles.transitEventCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.borderStrong }]}>
                  <Text style={[styles.transitEventTime, { color: colors.primary }]}>{new Date(event.timestamp_utc).toLocaleString()}</Text>
                  <Text style={[styles.traceTitle, { color: colors.text }]}>{event.planet} · {eventLabels[event.type] || event.type}</Text>
                  <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{event.sign} · {event.nakshatra} · K{event.kakshya_number} {event.kakshya_ruler}</Text>
                  <Text style={[styles.traceText, { color: colors.textSecondary }]}>{t('ashtakavargaUi.labels.natalBav')} {event.natal_bav_bindus} · {t('ashtakavargaUi.labels.natalSav')} {event.natal_sav_bindus} · {t('ashtakavargaUi.labels.kakshya')} {event.kakshya_bindu ? t('ashtakavargaUi.labels.bindu') : t('ashtakavargaUi.labels.noBindu')}{event.sensitive_timing?.double_match ? ' · Rāśi + Nakshatra ✓' : event.sensitive_timing?.rashi_match ? ' · Rāśi ✓' : event.sensitive_timing?.nakshatra_match ? ' · Nakshatra ✓' : ''}</Text>
                </View>
              )) : <Text style={[styles.advancedBody, { color: colors.textSecondary }]}>{t('ashtakavargaUi.transit.noEvents')}</Text>}
            </View>

            <View style={[styles.transitGuardrail, { backgroundColor: colors.surfaceMuted, borderColor: colors.borderStrong }]}>
              <Ionicons name="shield-checkmark-outline" size={18} color={colors.primary} />
              <Text style={[styles.transitGuardrailText, { color: colors.textSecondary }]}>{t('ashtakavargaUi.transit.guardrail')}</Text>
            </View>
          </>
        )}
      </ScrollView>
    );
  };

  const renderActiveTab = () => {
    const tabKey = ASHTAKVARGA_TABS[activeTab]?.key;
    if (tabKey === 'ai') return renderOraclesPulse();
    if (tabKey === 'bav') return renderBavTab();
    if (tabKey === 'matrix') return renderCombinedMatrixTab();
    if (tabKey === 'advanced') return renderAdvancedTab();
    if (tabKey === 'transit') return renderTransitDesk();
    return renderDestinyMap();
  };



  const openSecretScroll = (sign, bindus, index) => {
    setSelectedPillar({ sign, bindus, index });
    setShowSecretScroll(true);
  };

  const openPlanetChart = (planet, planetChart) => {
    if (!planetChart) return;
    setSelectedPillar({
      planet,
      planetChart,
      type: 'planet'
    });
    setShowSecretScroll(true);
  };

  const [lifePredictions, setLifePredictions] = useState(null);
  const [loadingLifePredictions, setLoadingLifePredictions] = useState(false);
  const [showLifePredictions, setShowLifePredictions] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [yearlyStrength, setYearlyStrength] = useState(null);
  const [loadingYearly, setLoadingYearly] = useState(false);
  const [yearlyProgress, setYearlyProgress] = useState(0);
  const [showInfoModal, setShowInfoModal] = useState(false);

  const openInfoModal = useCallback(() => {
    setShowInfoModal(true);
  }, []);

  useEffect(() => {
    if (!onHeaderStateChange || !embedded) return;
    onHeaderStateChange({
      title: 'Ashtakvarga',
      birthData: birthData?.name ? birthData : null,
      onOpenInfo: openInfoModal,
    });
  }, [onHeaderStateChange, embedded, birthData, openInfoModal]);

  const startLoadingAnimation = () => {
    setLoadingProgress(0);
    Animated.loop(
      Animated.timing(loadingRotateAnim, {
        toValue: 1,
        duration: 2000,
        useNativeDriver: true,
      })
    ).start();

    // Slow progress over 35 seconds
    const progressInterval = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 85) {
          clearInterval(progressInterval);
          return 85;
        }
        return prev + Math.random() * 3 + 1; // 1-4% increment
      });
    }, 1000); // Update every second

    return progressInterval;
  };

  const buildLifePredictionsBirthPayload = () => ({
    name: birthData.name,
    date: normalizeBirthForApi(birthData).date ?? birthData.date,
    time: birthData.time,
    latitude: birthData.latitude,
    longitude: birthData.longitude,
    place: birthData.place || '',
    gender: birthData.gender || '',
  });

  const generateLifePredictions = async (forceRegenerate = false) => {
    if (!birthData) {
      console.error('No birth data available for life study');
      return;
    }

    setLoadingLifePredictions(true);
    const progressInterval = startLoadingAnimation();

    try {
      const token = await AsyncStorage.getItem('authToken');

      const response = await fetch(`${API_BASE_URL}${getEndpoint('/ashtakavarga/life-predictions')}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          birth_data: buildLifePredictionsBirthPayload(),
          force_regenerate: Boolean(forceRegenerate),
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (data.credit_cost_next != null && !Number.isNaN(Number(data.credit_cost_next))) {
        setLifePredictionsCreditCost(Math.max(1, Number(data.credit_cost_next)));
      }

      if (response.ok) {
        if (data.job_id) {
          try {
            const result = await pollLifePredictionsJobApi(data.job_id, token);
            if (data.credit_cost_next != null && !Number.isNaN(Number(data.credit_cost_next))) {
              setLifePredictionsCreditCost(Math.max(1, Number(data.credit_cost_next)));
            }
            if (result.credit_cost_next != null && !Number.isNaN(Number(result.credit_cost_next))) {
              setLifePredictionsCreditCost(Math.max(1, Number(result.credit_cost_next)));
            }
            const serverErr =
              result.error ||
              result.predictions?.error ||
              (typeof result.detail === 'string' ? result.detail : null);
            if (serverErr) {
              Alert.alert('Life predictions', String(serverErr));
            } else {
              setLoadingProgress(100);
              setLifePredictions(result);
              setShowLifePredictions(true);
              if (Number(result.credits_charged) > 0) {
                fetchBalance();
              }
            }
          } catch (pollErr) {
            const msg =
              pollErr?.message === 'TIMEOUT'
                ? 'Still processing after 6 minutes. Try opening Life Study again later for your saved study.'
                : pollErr?.message || 'Could not complete predictions.';
            Alert.alert('Life predictions', msg);
          }
        } else {
          const serverErr =
            data.error ||
            data.predictions?.error ||
            (typeof data.detail === 'string' ? data.detail : null);
          if (serverErr) {
            Alert.alert('Life predictions', String(serverErr));
          } else {
            setLoadingProgress(100);
            setLifePredictions(data);
            setShowLifePredictions(true);
            if (Number(data.credits_charged) > 0) {
              fetchBalance();
            }
          }
        }
      } else {
        let message = `Request failed (${response.status})`;
        if (typeof data?.detail === 'string') {
          message = data.detail;
        } else if (Array.isArray(data?.detail) && data.detail.length) {
          message = data.detail.map((d) => d.msg || JSON.stringify(d)).join('\n');
        } else if (data?.error) {
          message = String(data.error);
        }
        console.error('Failed to generate life study:', response.status, message);
        Alert.alert('Life predictions', message);
        if (response.status === 402) {
          fetchBalance();
        }
      }
    } catch (error) {
      console.error('Error generating life study:', error);
    } finally {
      clearInterval(progressInterval);
      loadingRotateAnim.stopAnimation();
      loadingRotateAnim.setValue(0);
      setTimeout(() => {
        setLoadingLifePredictions(false);
        setLoadingProgress(0);
      }, 500);
    }
  };

  const confirmRegenerateLifePredictions = () => {
    setLifePredictionsCreditModalMode('regenerate');
  };

  /** Main CTA: open cached study immediately, or credit modal only if a new generation is needed */
  const onLifePredictionsMainCta = async () => {
    if (!birthData) return;
    setLifePredictionsCacheChecking(true);
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/ashtakavarga/life-predictions')}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          birth_data: buildLifePredictionsBirthPayload(),
          cache_probe: true,
          force_regenerate: false,
        }),
      });
      const data = await response.json().catch(() => ({}));

      if (data.credit_cost_next != null && !Number.isNaN(Number(data.credit_cost_next))) {
        setLifePredictionsCreditCost(Math.max(1, Number(data.credit_cost_next)));
      }

      if (!response.ok) {
        let message = `Request failed (${response.status})`;
        if (typeof data?.detail === 'string') {
          message = data.detail;
        } else if (Array.isArray(data?.detail) && data.detail.length) {
          message = data.detail.map((d) => d.msg || JSON.stringify(d)).join('\n');
        } else if (data?.error) {
          message = String(data.error);
        }
        Alert.alert('Life predictions', message);
        return;
      }

      if (
        data.cached === true &&
        !data.error &&
        !data.predictions?.error
      ) {
        setLifePredictions(data);
        setShowLifePredictions(true);
        return;
      }

      setLifePredictionsCreditModalMode('open');
    } catch (err) {
      console.error('Life predictions cache probe:', err);
      Alert.alert(
        'Life predictions',
        'Could not check for a saved study. Check your connection and try again.'
      );
    } finally {
      setLifePredictionsCacheChecking(false);
    }
  };

  const onConfirmLifePredictionsCreditModal = async () => {
    const authOk = await requireAuthForPaid({
      feature: 'Ashtakavarga life predictions',
      message: 'Sign in to generate an Ashtakavarga life study. Saved studies reopen free.',
      resume: { resumeRoute: 'AshtakvargaOracle', resumeParams: {} },
    });
    if (!authOk) return;
    const mode = lifePredictionsCreditModalMode;
    setLifePredictionsCreditModalMode(null);
    generateLifePredictions(mode === 'regenerate');
  };

  const closeLifePredictionsCreditModal = () => setLifePredictionsCreditModalMode(null);

  const lifePredictionsCreditModalTitle =
    lifePredictionsCreditModalMode === 'regenerate'
      ? 'Refresh Ashtakvarga study?'
      : 'Ashtakvarga study';

  const lifePredictionsCreditModalDescription =
    lifePredictionsCreditModalMode === 'regenerate'
      ? `This runs a fresh AI study and replaces your saved one. It will use ${lifePredictionsCreditCost} credits if the generation succeeds. Your balance: ${credits} credits.`
      : `Starting a new AI study uses up to ${lifePredictionsCreditCost} credits if you do not already have one saved for this profile. Your balance: ${credits} credits.`;

  const fetchYearlyStrength = async (houseNumber) => {
    setLoadingYearly(true);
    setYearlyProgress(0);

    try {
      const token = await AsyncStorage.getItem('authToken');

      // Simulate progress (actual calculation happens on backend)
      const progressInterval = setInterval(() => {
        setYearlyProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 2;
        });
      }, 500);

      const response = await fetch(`${API_BASE_URL}${getEndpoint('/ashtakavarga/yearly-house-strength')}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          birth_data: {
            name: birthData.name,
            date: birthData.date,
            time: birthData.time,
            latitude: birthData.latitude,
            longitude: birthData.longitude
          },
          house_number: houseNumber,
          year: new Date().getFullYear()
        })
      });

      clearInterval(progressInterval);

      if (response.ok) {
        const data = await response.json();
        setYearlyProgress(100);
        setYearlyStrength(data);
      } else {
        console.error('Failed to fetch yearly strength:', response.status);
      }
    } catch (error) {
      console.error('Error fetching yearly strength:', error);
    } finally {
      setTimeout(() => {
        setLoadingYearly(false);
        setYearlyProgress(0);
      }, 500);
    }
  };



  const getPlanetIcon = (planet) => {
    const icons = {
      'Sun': '☉', 'Moon': '☽', 'Mars': '♂', 'Mercury': '☿',
      'Jupiter': '♃', 'Venus': '♀', 'Saturn': '♄'
    };
    return icons[planet] || '⭐';
  };

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: colors.background }]}>
        <LinearGradient colors={[colors.background, colors.backgroundSecondary, colors.background]} style={styles.loadingGradient}>
          <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
            <View style={[styles.loadingSeal, { borderColor: colors.selectionBorder, backgroundColor: colors.selectionSurface }]}>
              <Ionicons name="grid-outline" size={30} color={colors.selectionText} />
            </View>
          </Animated.View>
          <Text style={[styles.loadingTitle, { color: colors.text }]}>Reading the bindus</Text>
          <Text style={[styles.loadingSubtext, { color: colors.textSecondary }]}>Preparing your Ashtakvarga strength map…</Text>
        </LinearGradient>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {!embedded ? <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} translucent={false} /> : null}
      <LinearGradient colors={[colors.background, colors.backgroundSecondary, colors.background]} style={styles.gradient}>
        {/* Embedded in ChartsHub: plain View — SafeAreaView can still pad top on web
            even with edges={[]} and stacks a second gap under the hub tabs. */}
        {(() => {
          const Root = View;
          const rootProps = embedded
            ? { style: [styles.safeArea, Platform.OS === 'web' ? { paddingTop: 0 } : null] }
            : { style: styles.safeArea };
          return (
        <Root {...rootProps}>
          {!embedded ? (
          <SafeAreaView edges={['top']} style={{ backgroundColor: colors.headerSurface }}>
          <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine }]}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.backButton, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}>
              <Ionicons name="arrow-back" size={22} color={colors.textInverse} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.textInverse }]} numberOfLines={1}>
              Ashtakvarga
            </Text>
            {birthData ? (
              <NativeSelectorChip
                birthData={birthData}
                onPress={() => navigation.navigate('SelectNative', { returnTo: 'AshtakvargaOracle' })}
                maxLength={10}
                showIcon={false}
                style={{ backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }}
                textStyle={{ color: colors.textInverse }}
                iconColor={colors.textInverseMuted}
              />
            ) : null}
            <TouchableOpacity onPress={() => setShowInfoModal(true)} style={[styles.infoButton, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}>
              <Ionicons name="information-circle-outline" size={23} color={colors.textInverse} />
            </TouchableOpacity>
          </View>
          </SafeAreaView>
          ) : null}

          <View style={[styles.tabNavigation, { backgroundColor: colors.surfaceRaised, borderColor: colors.borderStrong }, embedded && styles.tabNavigationEmbedded]}>
            {ASHTAKVARGA_TABS.map((tab, index) => {
              const isActive = activeTab === index;
              return (
                <TouchableOpacity
                  key={tab.key}
                  style={[
                    styles.tab,
                    isActive && styles.activeTab,
                    { backgroundColor: isActive ? colors.primary : 'transparent' },
                  ]}
                  onPress={() => setActiveTab(index)}
                >
                  <Ionicons
                    name={tab.icon}
                    size={18}
                    color={isActive ? colors.onPrimary : colors.textSecondary}
                  />
                  <Text
                    style={[
                      styles.tabText,
                      { color: isActive ? colors.onPrimary : colors.textSecondary },
                      isActive && styles.activeTabText,
                    ]}
                  >
                    {t(`ashtakavargaUi.tabs.${tab.labelKey}`)}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          {renderActiveTab()}

          <CreditModal
            visible={lifePredictionsCreditModalMode !== null}
            onConfirm={onConfirmLifePredictionsCreditModal}
            onCancel={closeLifePredictionsCreditModal}
            cost={lifePredictionsCreditCost}
            title={lifePredictionsCreditModalTitle}
            description={lifePredictionsCreditModalDescription}
          />

          <CreditModal
            visible={analysisCreditModalVisible}
            onConfirm={onConfirmAnalysisCreditModal}
            onCancel={closeAnalysisCreditModal}
            cost={lifePredictionsCreditCost}
            title={analysisCreditModalTitle}
            description={analysisCreditModalDescription}
          />

          <Modal
            visible={showLifePredictions}
            transparent
            animationType="slide"
            onRequestClose={() => setShowLifePredictions(false)}
          >
            <View style={[styles.modalOverlay, { backgroundColor: colors.overlay }]}>
              <View style={[styles.predictionsModal, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
                <LinearGradient
                  colors={[colors.surfaceRaised, colors.backgroundSecondary]}
                  style={styles.predictionsGradient}
                >
                  <TouchableOpacity
                    style={styles.regeneratePredictionButton}
                    onPress={confirmRegenerateLifePredictions}
                    disabled={loadingLifePredictions}
                  >
                    <Ionicons name="refresh" size={18} color={colors.primary} />
                    <Text style={[styles.regeneratePredictionText, { color: colors.primary }]}>Regenerate</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.closeButton}
                    onPress={() => setShowLifePredictions(false)}
                  >
                    <Ionicons name="close" size={24} color={colors.text} />
                  </TouchableOpacity>

                  {loadingLifePredictions && lifePredictions ? (
                    <View style={styles.predictionsRegenOverlay}>
                      <ActivityIndicator size="large" color={colors.accent} />
                      <Text style={[styles.predictionsRegenOverlayText, { color: colors.textInverse }]}>Updating study…</Text>
                    </View>
                  ) : null}

                  <ScrollView showsVerticalScrollIndicator={false}>
                    <Text style={[styles.predictionsTitle, { color: colors.text }]}>{Platform.OS === 'ios' ? 'Life Study' : 'Life Insights'}</Text>
                    <Text style={[styles.predictionsSubtitle, { color: colors.primary }]}>{lifePredictions?.methodology || lifePredictions?.predictions?.methodology || (Platform.OS === 'ios' ? 'Vedic chart strength analysis' : 'Chart strength analysis')}</Text>
                    {lifePredictions?.cached ? (
                      <Text style={[styles.predictionsCachedBadge, { color: colors.textSecondary }]}>
                        Saved study — no credits used to view again. Refresh for a fresh AI pass ({lifePredictionsCreditCost} credits).
                      </Text>
                    ) : null}

                    <View style={styles.predictionsContent}>
                      {(() => {
                        const pred = lifePredictions?.predictions;
                        if (!pred) return null;
                        const insights = pred.life_domain_insights;
                        const timing = pred.timing_highlights;
                        const transit = pred.transit_predictions;
                        const dasha = pred.dasha_analysis;
                        const sav = pred.sav_strength_analysis;
                        const life = pred.life_predictions;

                        return (
                          <>
                            {pred.current_life_phase ? (
                              <>
                                <Text style={[styles.sectionTitle, { color: colors.primary }]}>Current life phase</Text>
                                <Text style={[styles.sectionText, { color: colors.textSecondary }]}>{pred.current_life_phase}</Text>
                              </>
                            ) : null}

                            {sav?.overall_pattern ? (
                              <>
                                <Text style={[styles.sectionTitle, { color: colors.primary }]}>SAV overall pattern</Text>
                                <Text style={[styles.sectionText, { color: colors.textSecondary }]}>{sav.overall_pattern}</Text>
                              </>
                            ) : null}

                            {insights && typeof insights === 'object' ? (
                              <>
                                <Text style={[styles.sectionTitle, { color: colors.primary }]}>Life areas (from houses)</Text>
                                {Object.entries(insights).map(([key, text]) => {
                                  if (text == null || String(text).trim() === '') return null;
                                  const label = LIFE_PREDICTION_DOMAIN_LABELS[key] || key.replace(/_/g, ' ');
                                  return (
                                    <View key={key} style={[styles.predictionDomainCard, themedMutedSurface]}>
                                      <Text style={[styles.predictionDomainTitle, { color: colors.primary }]}>{label}</Text>
                                      <Text style={[styles.sectionText, { color: colors.textSecondary, marginBottom: 0 }]}>{String(text)}</Text>
                                    </View>
                                  );
                                })}
                              </>
                            ) : null}

                            {Array.isArray(timing) && timing.length > 0 ? (
                              <>
                                <Text style={[styles.sectionTitle, { color: colors.primary }]}>Timing windows</Text>
                                {timing.map((item, index) => {
                                  if (item == null) return null;
                                  if (typeof item === 'string') {
                                    return (
                                      <Text key={index} style={[styles.bulletPoint, { color: colors.textSecondary }]}>• {item}</Text>
                                    );
                                  }
                                  const windowLabel = item.window || item.period || item.label || `Period ${index + 1}`;
                                  const focus = item.focus || item.summary;
                                  const basis = item.ashtakavarga_basis || item.basis;
                                  return (
                                    <View key={index} style={[styles.timingHighlightCard, { backgroundColor: colors.surfaceMuted, borderLeftColor: colors.accent }]}>
                                      <Text style={[styles.timingHighlightTitle, { color: colors.primary }]}>{windowLabel}</Text>
                                      {focus ? <Text style={[styles.sectionText, { color: colors.textSecondary }]}>{focus}</Text> : null}
                                      {basis ? <Text style={[styles.timingHighlightBasis, { color: colors.textSecondary }]}>Ashtakavarga: {basis}</Text> : null}
                                    </View>
                                  );
                                })}
                              </>
                            ) : null}

                            {transit ? (
                              <>
                                <Text style={[styles.sectionTitle, { color: colors.primary }]}>Transits</Text>
                                {transit.saturn_influence ? (
                                  <>
                                    <Text style={[styles.subSectionTitle, { color: colors.text }]}>Saturn</Text>
                                    <Text style={[styles.sectionText, { color: colors.textSecondary }]}>{transit.saturn_influence}</Text>
                                  </>
                                ) : null}
                                {transit.jupiter_influence ? (
                                  <>
                                    <Text style={[styles.subSectionTitle, { color: colors.text }]}>Jupiter</Text>
                                    <Text style={[styles.sectionText, { color: colors.textSecondary }]}>{transit.jupiter_influence}</Text>
                                  </>
                                ) : null}
                                {transit.rahu_ketu_influence ? (
                                  <>
                                    <Text style={[styles.subSectionTitle, { color: colors.text }]}>Rahu & Ketu</Text>
                                    <Text style={[styles.sectionText, { color: colors.textSecondary }]}>{transit.rahu_ketu_influence}</Text>
                                  </>
                                ) : null}
                                {Array.isArray(transit.timing_recommendations) && transit.timing_recommendations.length > 0 ? (
                                  <>
                                    <Text style={[styles.subSectionTitle, { color: colors.text }]}>Timing tips</Text>
                                    {transit.timing_recommendations.map((line, i) => (
                                      <Text key={i} style={[styles.bulletPoint, { color: colors.textSecondary }]}>• {line}</Text>
                                    ))}
                                  </>
                                ) : null}
                              </>
                            ) : null}

                            {dasha ? (
                              <>
                                <Text style={[styles.sectionTitle, { color: colors.primary }]}>Dasha</Text>
                                {dasha.current_period_strength ? (
                                  <>
                                    <Text style={[styles.subSectionTitle, { color: colors.text }]}>Period strength</Text>
                                    <Text style={[styles.sectionText, { color: colors.textSecondary }]}>{dasha.current_period_strength}</Text>
                                  </>
                                ) : null}
                                {dasha.expected_results ? (
                                  <>
                                    <Text style={[styles.subSectionTitle, { color: colors.text }]}>What to expect</Text>
                                    <Text style={[styles.sectionText, { color: colors.textSecondary }]}>{dasha.expected_results}</Text>
                                  </>
                                ) : null}
                                {Array.isArray(dasha.recommendations) && dasha.recommendations.length > 0 ? (
                                  <>
                                    <Text style={[styles.subSectionTitle, { color: colors.text }]}>Dasha recommendations</Text>
                                    {dasha.recommendations.map((line, i) => (
                                      <Text key={i} style={[styles.bulletPoint, { color: colors.textSecondary }]}>• {line}</Text>
                                    ))}
                                  </>
                                ) : null}
                              </>
                            ) : null}

                            {sav?.strong_areas && sav.strong_areas.length > 0 ? (
                              <>
                                <Text style={[styles.sectionTitle, { color: colors.primary }]}>Strong areas</Text>
                                {sav.strong_areas.map((area, index) => (
                                  <Text key={index} style={[styles.bulletPoint, { color: colors.textSecondary }]}>• {area}</Text>
                                ))}
                              </>
                            ) : null}

                            {sav?.challenging_areas && sav.challenging_areas.length > 0 ? (
                              <>
                                <Text style={[styles.sectionTitle, { color: colors.primary }]}>Challenging areas</Text>
                                {sav.challenging_areas.map((area, index) => (
                                  <Text key={index} style={[styles.bulletPoint, { color: colors.textSecondary }]}>• {area}</Text>
                                ))}
                              </>
                            ) : null}

                            {life?.next_6_months ? (
                              <>
                                <Text style={[styles.sectionTitle, { color: colors.primary }]}>Next 6 months</Text>
                                <Text style={[styles.sectionText, { color: colors.textSecondary }]}>{life.next_6_months}</Text>
                              </>
                            ) : null}

                            {life?.next_year ? (
                              <>
                                <Text style={[styles.sectionTitle, { color: colors.primary }]}>Next year</Text>
                                <Text style={[styles.sectionText, { color: colors.textSecondary }]}>{life.next_year}</Text>
                              </>
                            ) : null}

                            {life?.major_themes && life.major_themes.length > 0 ? (
                              <>
                                <Text style={[styles.sectionTitle, { color: colors.primary }]}>Major themes</Text>
                                {life.major_themes.map((theme, index) => (
                                  <Text key={index} style={[styles.bulletPoint, { color: colors.textSecondary }]}>• {theme}</Text>
                                ))}
                              </>
                            ) : null}

                            {pred.remedial_measures && pred.remedial_measures.length > 0 ? (
                              <>
                                <Text style={[styles.sectionTitle, { color: colors.primary }]}>Remedial measures</Text>
                                {pred.remedial_measures.map((remedy, index) => (
                                  <Text key={index} style={[styles.bulletPoint, { color: colors.textSecondary }]}>• {remedy}</Text>
                                ))}
                              </>
                            ) : null}
                          </>
                        );
                      })()}
                    </View>
                  </ScrollView>
                </LinearGradient>
              </View>
            </View>
          </Modal>

          <Modal
            visible={showSecretScroll && selectedPillar !== null}
            transparent
            animationType="slide"
            onRequestClose={() => {
              setShowSecretScroll(false);
              setYearlyStrength(null);
            }}
          >
            <View style={[styles.modalOverlay, { backgroundColor: colors.overlay }]}>
              <TouchableOpacity
                style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
                activeOpacity={1}
                onPress={() => {
                  setShowSecretScroll(false);
                  setYearlyStrength(null);
                }}
              />
              <View style={[styles.secretScroll, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
                <LinearGradient
                  colors={[colors.surfaceRaised, colors.backgroundSecondary]}
                  style={styles.scrollGradient}
                >
                  <TouchableOpacity
                    style={styles.closeButton}
                    onPress={() => {
                      setShowSecretScroll(false);
                      setYearlyStrength(null);
                    }}
                  >
                    <Ionicons name="close" size={24} color={colors.text} />
                  </TouchableOpacity>

                  {selectedPillar?.type === 'planet' ? (
                    <>
                      <Text style={[styles.scrollTitle, { color: colors.text }]}>
                        {selectedPillar.planet} Bhinnashtakvarga
                      </Text>
                      <Text style={[styles.scrollBindus, { color: colors.primary }]}>
                        {selectedPillar.planetChart.total} Total Points
                      </Text>
                      <View style={styles.planetChartGrid}>
                        {Object.entries(selectedPillar.planetChart.bindus).map(([sign, bindus]) => {
                          const signs = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'];
                          return (
                            <View key={sign} style={[styles.miniPillar, themedMutedSurface]}>
                              <Text style={[styles.miniBindus, { color: colors.text }]}>{bindus}</Text>
                              <Text style={[styles.miniSign, { color: colors.textSecondary }]}>{signs[parseInt(sign)]}</Text>
                            </View>
                          );
                        })}
                      </View>
                      <Text style={[styles.scrollDescription, { color: colors.textSecondary }]}>
                        This shows where {selectedPillar.planet} receives support from other planets. Higher numbers indicate stronger beneficial influences in those zodiac signs.
                      </Text>
                    </>
                  ) : (
                    <ScrollView showsVerticalScrollIndicator={false}>
                      <Text style={[styles.scrollTitle, { color: colors.text }]}>
                        House {(selectedPillar?.index || 0) + 1}: {HOUSE_SIGNIFICATIONS[selectedPillar?.index || 0]?.name}
                      </Text>
                      <Text style={[styles.scrollBindus, { color: colors.primary }]}>
                        {selectedPillar?.bindus || 0} Cosmic Points
                      </Text>

                      <View style={[styles.significationBox, themedMutedSurface]}>
                        <Text style={[styles.significationTitle, { color: colors.primary }]}>House Significations:</Text>
                        <Text style={[styles.significationText, { color: colors.textSecondary }]}>
                          {HOUSE_SIGNIFICATIONS[selectedPillar?.index || 0]?.significations}
                        </Text>
                      </View>

                      <Text style={[styles.scrollDescription, { color: colors.textSecondary }]}>
                        {completeOracleData?.pillar_insights?.[selectedPillar?.index] ||
                         (selectedPillar && selectedPillar.bindus >= 30
                          ? `With ${selectedPillar.bindus} points, this house is strongly supported. Matters related to ${HOUSE_SIGNIFICATIONS[selectedPillar?.index || 0]?.name.toLowerCase()} will flourish with ease and bring positive results.`
                          : selectedPillar && selectedPillar.bindus <= 25
                          ? `With ${selectedPillar.bindus} points, this house needs attention. Matters of ${HOUSE_SIGNIFICATIONS[selectedPillar?.index || 0]?.name.toLowerCase()} may require extra effort and patience.`
                          : selectedPillar
                          ? `With ${selectedPillar.bindus} points, this house offers moderate support. Steady progress in ${HOUSE_SIGNIFICATIONS[selectedPillar?.index || 0]?.name.toLowerCase()} is possible through consistent effort.`
                          : 'Loading cosmic insights...'
                         )}
                      </Text>

                      {!yearlyStrength && !loadingYearly && (
                        <TouchableOpacity
                          style={styles.yearlyButton}
                          onPress={() => fetchYearlyStrength(selectedPillar?.index + 1)}
                        >
                          <LinearGradient
                            colors={[colors.primary, colors.primaryStrong]}
                            style={styles.yearlyButtonGradient}
                          >
                            <Text style={styles.yearlyButtonText}>📊 View Yearly Strength</Text>
                          </LinearGradient>
                        </TouchableOpacity>
                      )}

                      {loadingYearly && (
                        <View style={styles.loadingYearlyContainer}>
                          <Text style={[styles.loadingYearlyText, { color: colors.text }]}>Calculating 365 days...</Text>
                          <View style={[styles.progressBar, { backgroundColor: colors.cardBorder }]}>
                            <View style={[styles.progressFill, { width: `${yearlyProgress}%`, backgroundColor: colors.accent }]} />
                          </View>
                          <Text style={[styles.progressText, { color: colors.accent }]}>{Math.round(yearlyProgress)}%</Text>
                        </View>
                      )}

                      {yearlyStrength && (
                        <View style={[styles.yearlyStrengthContainer, themedMutedSurface]}>
                          <Text style={[styles.yearlyTitle, { color: colors.text }]}>House {yearlyStrength.house} - {yearlyStrength.year} Strength</Text>
                          <Text style={[styles.yearlySubtitle, { color: colors.primary }]}>Birth Chart: {yearlyStrength.birth_bindus} bindus</Text>

                          <ScrollView style={styles.yearlyDataScroll} showsVerticalScrollIndicator={true}>
                            {yearlyStrength.daily_data && yearlyStrength.daily_data.map((day, index) => (
                              <View key={index} style={[
                                styles.dayRow,
                                { backgroundColor: colors.surfaceRaised },
                                day.category === 'strong' && { borderLeftWidth: 3, borderLeftColor: colors.success },
                                day.category === 'weak' && { borderLeftWidth: 3, borderLeftColor: colors.error }
                              ]}>
                                <Text style={[styles.dayDate, { color: colors.text }]}>{day.date}</Text>
                                <Text style={[styles.dayBindus, { color: colors.primary }]}>{day.bindus} bindus</Text>
                                <Text style={[
                                  styles.dayDiff,
                                  { color: day.difference > 0 ? colors.success : colors.error }
                                ]}>
                                  {day.difference > 0 ? '+' : ''}{day.difference}
                                </Text>
                                <Text style={[styles.dayCategory, { color: colors.textSecondary }]}>{day.category}</Text>
                              </View>
                            ))}
                          </ScrollView>
                        </View>
                      )}
                    </ScrollView>
                  )}
                </LinearGradient>
              </View>
            </View>
          </Modal>
        </Root>
          );
        })()}
      </LinearGradient>

      <Modal
        visible={showInfoModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowInfoModal(false)}
      >
        <View style={[styles.modalOverlay, { backgroundColor: colors.overlay }]}>
          <View style={[styles.infoModal, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
            <LinearGradient
              colors={[colors.surfaceRaised, colors.backgroundSecondary]}
              style={styles.infoGradient}
            >
              <TouchableOpacity
                style={styles.closeButton}
                onPress={() => setShowInfoModal(false)}
              >
                <Ionicons name="close" size={24} color={colors.text} />
              </TouchableOpacity>

              <ScrollView showsVerticalScrollIndicator={false}>
                <Text style={[styles.infoTitle, { color: colors.text }]}>Understanding Ashtakvarga</Text>

                <View style={[styles.infoSection, themedMutedSurface]}>
                  <Text style={[styles.infoSectionTitle, { color: colors.primary }]}>🎯 What is Ashtakvarga?</Text>
                  <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                    {Platform.OS === 'ios'
                      ? 'Ashtakvarga is an ancient Vedic astrology system that measures planetary strength through numerical points called "bindus" or "dots". It helps interpret support levels, timing patterns, and chart strength.'
                      : 'Ashtakvarga is an ancient Vedic astrology system that measures planetary strength through numerical points called "bindus" or "dots". It helps interpret support levels, timing patterns, and chart strength.'}
                  </Text>
                </View>

                <View style={[styles.infoSection, themedMutedSurface]}>
                  <Text style={[styles.infoSectionTitle, { color: colors.primary }]}>📊 Sarvashtakvarga Chart</Text>
                  <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                    The main chart you see combines all planetary influences. Each house shows total bindus (points) from all planets. Higher numbers (30+) indicate strength, lower numbers (25-) suggest challenges.
                  </Text>
                </View>

                <View style={[styles.infoSection, themedMutedSurface]}>
                  <Text style={[styles.infoSectionTitle, { color: colors.primary }]}>🪐 Bhinnashtakvarga Charts</Text>
                  <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                    Individual planet charts (Sun, Moon, Mars, etc.) show where each planet receives support. Tap any planet button to see its specific influence pattern across the zodiac signs.
                  </Text>
                </View>

                <View style={[styles.infoSection, themedMutedSurface]}>
                  <Text style={[styles.infoSectionTitle, { color: colors.primary }]}>🔮 How to Use in Our App</Text>
                  <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                    • Tap any house in the main chart for detailed insights{"\n"}
                    • Use the date navigator to see transit effects{"\n"}
                    • Check individual planet charts for specific influences{"\n"}
                    • Generate yearly strength analysis for timing{"\n"}
                    • Higher bindus = favorable periods for that life area
                  </Text>
                </View>

                <View style={[styles.infoSection, themedMutedSurface]}>
                  <Text style={[styles.infoSectionTitle, { color: colors.primary }]}>💡 Reading the Colors</Text>
                  <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                    🟢 Green (30+ bindus): Strong, favorable periods{"\n"}
                    🟠 Orange (26-29 bindus): Moderate strength{"\n"}
                    🔴 Red (25- bindus): Challenging, needs extra effort
                  </Text>
                </View>
              </ScrollView>
            </LinearGradient>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = {
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  loadingContainer: { flex: 1 },
  loadingGradient: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingSeal: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  loadingTitle: {
    ...typographyTokens.display,
    fontSize: 27,
    lineHeight: 32,
    marginBottom: 6,
  },
  loadingSubtext: { fontSize: 14 },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    flex: 1,
    ...typographyTokens.display,
    fontSize: 23,
    lineHeight: 28,
    color: COLORS.white,
  },
  headerRight: { width: 40 },
  infoButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },

  tabNavigation: {
    flexDirection: 'row',
    marginHorizontal: 20,
    marginTop: 16,
    marginBottom: 16,
    padding: 4,
    borderRadius: 18,
    borderWidth: 1,
  },
  tabNavigationEmbedded: {
    marginTop: 0,
    marginBottom: 14,
    paddingTop: 4,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    minHeight: 52,
    justifyContent: 'center',
    paddingVertical: 8,
    borderRadius: 14,
  },
  activeTab: {
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
  },
  tabText: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.6)',
    marginTop: 4,
  },
  activeTabText: {
    fontWeight: '800',
  },

  tabContent: {
    flex: 1,
    paddingHorizontal: 20,
  },
  analysisTabContent: {
    paddingBottom: 20,
  },
  analysisModeTabs: {
    flexDirection: 'row',
    borderRadius: 16,
    padding: 4,
    marginBottom: 14,
  },
  analysisModeTab: {
    flex: 1,
    minHeight: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    paddingHorizontal: 6,
  },
  analysisModeTabText: {
    fontSize: 12,
    fontWeight: '800',
    marginLeft: 5,
  },
  analysisPanelCard: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 16,
    marginBottom: 18,
  },
  analysisPanelHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 14,
  },
  analysisPanelIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  analysisPanelTitleBlock: {
    flex: 1,
  },
  analysisPanelTitle: {
    ...typographyTokens.display,
    fontSize: 21,
    lineHeight: 26,
    marginBottom: 5,
  },
  analysisPanelSubtitle: {
    fontSize: 13,
    lineHeight: 19,
  },
  analysisBenefits: {
    marginBottom: 14,
  },
  analysisBenefitRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 9,
  },
  analysisBenefitText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
    marginLeft: 8,
  },
  analysisQuestionCard: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 16,
    marginBottom: 18,
  },
  askChatCard: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
    marginBottom: 18,
  },
  askChatHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 10,
    marginBottom: 12,
  },
  askChatTitleBlock: {
    flex: 1,
  },
  askMessages: {
    marginBottom: 12,
  },
  askUserBubbleRow: {
    alignItems: 'flex-end',
    marginBottom: 10,
  },
  askUserBubble: {
    maxWidth: '86%',
    borderRadius: 16,
    borderBottomRightRadius: 5,
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  askUserText: {
    color: '#fff',
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '600',
  },
  askAssistantBubbleRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  askAssistantAvatar: {
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
    marginTop: 2,
  },
  askAssistantBubble: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 16,
    borderTopLeftRadius: 5,
    paddingVertical: 11,
    paddingHorizontal: 12,
  },
  askAssistantHeadline: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '800',
    marginBottom: 6,
  },
  askAssistantSection: {
    marginTop: 8,
  },
  askAssistantSectionTitle: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '800',
    marginBottom: 4,
  },
  askAssistantBullet: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 4,
  },
  analysisQuestionTitle: {
    ...typographyTokens.display,
    fontSize: 23,
    marginBottom: 6,
  },
  analysisQuestionSubtitle: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  analysisQuestionInput: {
    borderWidth: 1,
    borderRadius: 14,
    minHeight: 96,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 12,
  },
  analysisSuggestionRow: {
    paddingHorizontal: 4,
    paddingBottom: 14,
  },
  analysisSuggestionScroller: {
    marginHorizontal: -4,
    flexGrow: 0,
  },
  analysisSuggestionChip: {
    borderWidth: 1,
    borderRadius: 999,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginRight: 8,
  },
  analysisSuggestionText: {
    fontSize: 12,
    fontWeight: '600',
  },
  analysisQuestionActions: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  analysisAskButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 14,
    paddingVertical: 12,
    paddingHorizontal: 16,
    minHeight: 48,
    flexGrow: 1,
    flexShrink: 1,
  },
  analysisAskButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '800',
    marginLeft: 8,
    flexShrink: 1,
  },
  analysisClearButton: {
    borderWidth: 1,
    borderRadius: 14,
    paddingVertical: 12,
    paddingHorizontal: 14,
    marginLeft: 10,
  },
  analysisClearButtonText: {
    fontSize: 13,
    fontWeight: '700',
  },
  analysisHistoryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 14,
    paddingVertical: 12,
    paddingHorizontal: 12,
    marginLeft: 10,
  },
  analysisHistoryButtonText: {
    fontSize: 13,
    fontWeight: '700',
    marginLeft: 6,
  },
  askComposer: {
    borderWidth: 1,
    borderRadius: 18,
    minHeight: 52,
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingLeft: 12,
    paddingRight: 6,
    paddingVertical: 6,
  },
  askComposerToolbar: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginBottom: 8,
  },
  askComposerHistoryLink: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 14,
    borderWidth: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  askComposerInput: {
    flex: 1,
    maxHeight: 96,
    minHeight: 38,
    fontSize: 15,
    lineHeight: 21,
    paddingVertical: 8,
    paddingRight: 8,
  },
  askSendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 6,
  },
  analysisAnswerCard: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 16,
    marginBottom: 18,
  },
  analysisAnswerTitle: {
    ...typographyTokens.display,
    fontSize: 25,
    marginBottom: 6,
  },
  analysisAnswerQuestion: {
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 10,
  },
  analysisAnswerHeadline: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 14,
  },
  analysisAnswerSection: {
    marginTop: 10,
  },
  analysisAnswerSectionTitle: {
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 8,
  },
  matrixCard: {
    borderWidth: 1,
    borderRadius: 16,
    padding: 12,
    marginBottom: 14,
  },
  matrixRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    minHeight: 38,
  },
  matrixHeaderRow: {
    minHeight: 42,
  },
  matrixHeaderCell: {
    width: 38,
    textAlign: 'center',
    fontSize: 11,
    fontWeight: '700',
    paddingVertical: 8,
  },
  matrixCell: {
    width: 38,
    textAlign: 'center',
    fontSize: 12,
    fontWeight: '600',
    paddingVertical: 8,
  },
  matrixSignCell: {
    width: 64,
    textAlign: 'left',
    paddingLeft: 4,
  },
  matrixSavCell: {
    width: 42,
    fontWeight: '800',
  },
  matrixHint: {
    fontSize: 13,
    lineHeight: 19,
    marginHorizontal: 2,
  },
  aiInsightSection: {
    marginTop: 12,
  },
  aiInsightSectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 8,
  },

  titleContainer: {
    alignItems: 'flex-start',
    paddingTop: 8,
    paddingBottom: 14,
  },
  sectionEyebrow: {
    ...typographyTokens.eyebrow,
    marginBottom: 8,
  },

  cosmicWeatherHeader: {
    borderRadius: 20,
    overflow: 'hidden',
    marginBottom: 20,
  },
  weatherGradient: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  weatherContent: { alignItems: 'center' },
  cosmicTheme: {
    fontSize: 36,
    fontWeight: '800',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 10,
  },
  cosmicSubtext: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 20,
  },
  strengthIndicator: { alignItems: 'center' },
  strengthValue: {
    fontSize: 48,
    fontWeight: '700',
    color: '#ffd700',
  },
  strengthLabel: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
  },

  narrativeCard: {
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 20,
  },
  narrativeGradient: { padding: 20 },
  narrativeTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 12,
  },
  narrativeText: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.9)',
    lineHeight: 24,
  },
  generateInsightButton: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  buttonGradient: {
    paddingVertical: 16,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
  },

  powerActionsContainer: { marginBottom: 10 },

  lifePredictionsContainer: {
    marginBottom: 18,
    marginTop: 16,
  },
  lifePredictionsButton: {
    borderRadius: 24,
    overflow: 'hidden',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.16,
    shadowRadius: 12,
  },
  loadingButton: {},
  lifePredictionsGradient: {
    paddingVertical: 24,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  lifePredictionsIcon: {
    fontSize: 18,
    marginBottom: 3,
  },
  lifePredictionsIconLarge: {
    fontSize: 28,
    marginBottom: 8,
  },
  lifePredictionsIconSeal: {
    width: 52,
    height: 52,
    borderRadius: 26,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  lifePredictionsHeadline: {
    ...typographyTokens.display,
    fontSize: 28,
    lineHeight: 32,
    color: COLORS.white,
    textAlign: 'center',
    letterSpacing: 0.3,
    marginBottom: 6,
  },
  lifePredictionsTeaser: {
    fontSize: 14,
    lineHeight: 20,
    color: 'rgba(255,255,255,0.92)',
    textAlign: 'center',
    paddingHorizontal: 4,
    marginBottom: 12,
  },
  lifePredictionsChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginBottom: 14,
  },
  lifePredictionsChip: {
    fontSize: 11,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.95)',
    backgroundColor: 'transparent',
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
    overflow: 'hidden',
    marginHorizontal: 4,
    marginVertical: 4,
  },
  lifePredictionsCtaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  lifePredictionsCtaText: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.white,
    letterSpacing: 0.4,
  },
  lifePredictionsText: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 4,
  },
  lifePredictionsSubtext: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.75)',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  lifePredictionsCreditHint: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.88)',
    textAlign: 'center',
    marginBottom: 6,
  },
  bavHint: {
    fontSize: 12,
    lineHeight: 17,
    marginBottom: 10,
    opacity: 0.95,
  },
  loadingContent: {
    alignItems: 'center',
  },
  loadingIconContainer: {
    marginBottom: 8,
  },
  progressContainer: {
    alignItems: 'center',
    marginTop: 12,
    width: '100%',
  },
  progressBar: {
    width: '80%',
    height: 4,
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 2,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#ffd700',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    color: '#ffd700',
    fontWeight: '600',
  },
  warningText: {
    color: '#ff6b6b',
  },
  copyButton: {
    backgroundColor: '#ffd700',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    alignSelf: 'flex-end',
    marginBottom: 10,
  },
  copyButtonText: {
    color: '#000',
    fontWeight: '600',
  },
  powerActionsTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 12,
  },
  pillsContainer: { flexDirection: 'row' },
  actionPill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 12,
  },
  doPill: { backgroundColor: 'rgba(76, 175, 80, 0.2)' },
  avoidPill: { backgroundColor: 'rgba(244, 67, 54, 0.2)' },
  pillIcon: { fontSize: 16, marginRight: 8 },
  pillText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },

  mapTitle: {
    ...typographyTokens.display,
    fontSize: 28,
    lineHeight: 33,
    textAlign: 'left',
    marginBottom: 6,
  },
  mapSubtitle: {
    fontSize: 13,
    lineHeight: 19,
    textAlign: 'left',
  },
  chartContainer: {
    marginTop: 12,
    marginBottom: 18,
    padding: 8,
    borderWidth: 1,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },

  planetaryToggle: {
    marginTop: 4,
    marginBottom: 8,
    paddingVertical: 5
  },
  toggleTitle: {
    ...typographyTokens.display,
    fontSize: 21,
    color: COLORS.white,
    marginBottom: 8,
  },
  planetButton: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 88,
    minHeight: 106,
    paddingHorizontal: 10,
    paddingVertical: 12,
    marginRight: 10,
    borderRadius: 18,
    borderWidth: 1,
  },
  planetIcon: { fontSize: 26, marginBottom: 8 },
  planetName: {
    fontSize: 12,
    color: COLORS.white,
  },
  planetBindus: {
    ...typographyTokens.display,
    fontSize: 20,
    lineHeight: 24,
    marginTop: 5,
  },
  planetChartGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginVertical: 20,
  },
  miniPillar: {
    width: '15%',
    alignItems: 'center',
    marginBottom: 8,
    marginHorizontal: 4,
    borderRadius: 10,
    padding: 8,
    borderWidth: 1,
  },
  miniBindus: {
    fontSize: 14,
    fontWeight: '700',
    color: '#ffd700',
  },
  miniSign: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.8)',
  },

  timeTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 20,
  },
  querySelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 30,
  },
  queryOption: {
    width: '48%',
    alignItems: 'center',
    paddingVertical: 20,
    borderRadius: 16,
    borderWidth: 2,
    backgroundColor: 'rgba(255,255,255,0.05)',
    marginBottom: 12,
  },
  queryIcon: { fontSize: 32, marginBottom: 8 },
  queryTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
    textAlign: 'center',
  },

  timelineContainer: { flex: 1 },
  timelineTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 20,
  },
  timelineEvent: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  eventNode: {
    width: 20,
    height: 20,
    borderRadius: 10,
    marginRight: 15,
    marginTop: 10,
  },
  goldNode: { backgroundColor: '#ffd700' },
  greyNode: { backgroundColor: '#666' },
  eventCard: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  eventTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 4,
  },
  eventDate: {
    fontSize: 12,
    color: '#ffd700',
    marginBottom: 8,
  },
  eventDescription: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    lineHeight: 20,
    marginBottom: 8,
  },
  eventScore: {
    fontSize: 14,
    fontWeight: '700',
    color: '#ffd700',
  },
  timelineSubtext: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.6)',
    textAlign: 'center',
    fontStyle: 'italic',
    marginTop: 20,
  },

  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  secretScroll: {
    width: '100%',
    maxHeight: '70%',
    borderRadius: 28,
    borderWidth: 1,
    overflow: 'hidden',
  },
  scrollGradient: { padding: 30 },
  closeButton: {
    position: 'absolute',
    top: 15,
    right: 15,
    zIndex: 1,
  },
  scrollTitle: {
    ...typographyTokens.display,
    fontSize: 26,
    lineHeight: 31,
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 8,
  },
  scrollBindus: {
    fontSize: 18,
    color: '#ffd700',
    textAlign: 'center',
    marginBottom: 20,
  },
  scrollDescription: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.9)',
    lineHeight: 24,
    textAlign: 'center',
  },

  predictionsModal: {
    width: '95%',
    maxHeight: '85%',
    borderRadius: 28,
    borderWidth: 1,
    overflow: 'hidden',
  },
  predictionsGradient: {
    padding: 20,
    paddingTop: 50,
    position: 'relative',
  },
  regeneratePredictionButton: {
    position: 'absolute',
    top: 14,
    left: 14,
    zIndex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 10,
  },
  regeneratePredictionText: {
    marginLeft: 6,
    fontSize: 14,
    fontWeight: '600',
    color: '#ffd700',
  },
  predictionsRegenOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(10, 5, 30, 0.72)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
    borderRadius: 20,
  },
  predictionsRegenOverlayText: {
    marginTop: 12,
    fontSize: 15,
    color: 'rgba(255,255,255,0.95)',
    fontWeight: '600',
  },
  predictionsCachedBadge: {
    fontSize: 12,
    lineHeight: 17,
    textAlign: 'center',
    marginBottom: 12,
    paddingHorizontal: 8,
    fontStyle: 'italic',
  },
  predictionsTitle: {
    ...typographyTokens.display,
    fontSize: 28,
    lineHeight: 33,
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 8,
  },
  predictionsSubtitle: {
    fontSize: 14,
    color: '#ffd700',
    textAlign: 'center',
    marginBottom: 20,
    fontStyle: 'italic',
  },
  predictionsContent: {
    paddingBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ffd700',
    marginTop: 20,
    marginBottom: 10,
  },
  sectionText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    lineHeight: 20,
    marginBottom: 10,
  },
  bulletPoint: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    lineHeight: 18,
    marginBottom: 6,
    paddingLeft: 10,
  },
  subSectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginTop: 8,
    marginBottom: 4,
  },
  predictionDomainCard: {
    borderWidth: 1,
    borderColor: 'rgba(255,215,0,0.22)',
    borderRadius: 12,
    padding: 12,
    marginBottom: 10,
    backgroundColor: 'rgba(255,255,255,0.06)',
  },
  predictionDomainTitle: {
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 6,
  },
  timingHighlightCard: {
    borderLeftWidth: 3,
    borderLeftColor: 'rgba(255,215,0,0.55)',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    marginBottom: 10,
    backgroundColor: 'rgba(255,255,255,0.05)',
  },
  timingHighlightTitle: {
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 4,
  },
  timingHighlightBasis: {
    fontSize: 12,
    fontStyle: 'italic',
    marginTop: 6,
    opacity: 0.9,
  },
  yearlyButton: {
    borderRadius: 12,
    overflow: 'hidden',
    marginTop: 20,
  },
  yearlyButtonGradient: {
    paddingVertical: 14,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  yearlyButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.white,
  },
  loadingYearlyContainer: {
    marginTop: 20,
    alignItems: 'center',
  },
  loadingYearlyText: {
    fontSize: 14,
    color: COLORS.white,
    marginBottom: 12,
  },
  yearlyStrengthContainer: {
    marginTop: 20,
    padding: 16,
    borderRadius: 12,
    maxHeight: 400,
  },
  yearlyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 4,
  },
  yearlySubtitle: {
    fontSize: 13,
    color: '#ffd700',
    marginBottom: 16,
  },
  yearlyDataScroll: {
    maxHeight: 300,
  },
  dayRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginBottom: 4,
    borderRadius: 8,
  },
  strongDay: {
    backgroundColor: 'rgba(0,255,0,0.1)',
    borderLeftWidth: 3,
    borderLeftColor: '#00ff00',
  },
  weakDay: {
    backgroundColor: 'rgba(255,0,0,0.1)',
    borderLeftWidth: 3,
    borderLeftColor: '#ff6b6b',
  },
  dayDate: {
    fontSize: 11,
    color: COLORS.white,
    flex: 2,
  },
  dayBindus: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffd700',
    flex: 1,
    textAlign: 'center',
  },
  dayDiff: {
    fontSize: 11,
    fontWeight: '600',
    flex: 1,
    textAlign: 'center',
  },
  positiveDiff: {
    color: '#00ff00',
  },
  negativeDiff: {
    color: '#ff6b6b',
  },
  dayCategory: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.7)',
    flex: 1,
    textAlign: 'right',
    textTransform: 'capitalize',
  },
  significationBox: {
    marginVertical: 16,
  },
  significationTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 8,
  },
  significationText: {
    fontSize: 14,
    lineHeight: 22,
  },
  yearlyNote: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.6)',
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 20,
  },
  infoModal: {
    width: '95%',
    maxHeight: '85%',
    borderRadius: 28,
    borderWidth: 1,
    overflow: 'hidden',
  },
  infoGradient: {
    padding: 20,
    paddingTop: 50,
  },
  infoTitle: {
    ...typographyTokens.display,
    fontSize: 28,
    lineHeight: 33,
    textAlign: 'center',
    marginBottom: 20,
  },
  infoSection: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
  },
  infoSectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    lineHeight: 20,
  },
  advancedContent: {
    paddingBottom: 32,
  },
  advancedCard: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 15,
    marginBottom: 12,
  },
  advancedCardTitle: {
    ...typographyTokens.display,
    fontSize: 21,
    lineHeight: 26,
    marginBottom: 5,
  },
  advancedBody: {
    fontSize: 12,
    lineHeight: 17,
  },
  advancedEyebrow: {
    ...typographyTokens.eyebrow,
    marginBottom: 6,
  },
  profileButtonRow: {
    flexDirection: 'row',
    gap: 7,
    marginTop: 11,
  },
  profileButton: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 10,
  },
  profileButtonTitle: {
    fontSize: 11,
    lineHeight: 14,
    fontWeight: '900',
  },
  profileButtonDetail: {
    fontSize: 9,
    lineHeight: 12,
    marginTop: 3,
  },
  advancedAudit: {
    fontSize: 9,
    lineHeight: 13,
    marginTop: 8,
  },
  advancedAction: {
    alignSelf: 'flex-start',
    borderRadius: 20,
    paddingVertical: 10,
    paddingHorizontal: 15,
    marginTop: 12,
  },
  advancedTableScroll: {
    marginTop: 12,
  },
  advancedTableRow: {
    flexDirection: 'row',
    minHeight: 38,
    alignItems: 'center',
    borderBottomWidth: 1,
  },
  advancedTableHeader: {
    minHeight: 40,
  },
  advancedTableCell: {
    width: 64,
    textAlign: 'right',
    paddingHorizontal: 6,
    paddingVertical: 8,
    fontSize: 11,
    fontWeight: '600',
  },
  advancedTableFirstCell: {
    width: 76,
    textAlign: 'left',
    fontWeight: '800',
  },
  advancedTableStrong: {
    fontSize: 13,
    fontWeight: '900',
  },
  advancedPlanetChips: {
    gap: 6,
    paddingVertical: 10,
  },
  advancedPlanetChip: {
    borderWidth: 1,
    borderRadius: 18,
    paddingVertical: 7,
    paddingHorizontal: 11,
  },
  reductionRow: {
    flexDirection: 'row',
    alignItems: 'stretch',
    minHeight: 36,
    borderBottomWidth: 1,
  },
  reductionLabel: {
    width: 112,
    paddingVertical: 9,
    paddingHorizontal: 7,
    fontSize: 10,
    fontWeight: '800',
  },
  reductionCell: {
    width: 34,
    paddingVertical: 9,
    textAlign: 'center',
    fontSize: 10,
    fontWeight: '700',
  },
  traceBlock: {
    borderRadius: 12,
    padding: 11,
    marginTop: 10,
  },
  traceTitle: {
    fontSize: 12,
    fontWeight: '900',
    marginBottom: 5,
  },
  traceText: {
    fontSize: 10,
    lineHeight: 15,
    marginTop: 2,
  },
  advancedSubheading: {
    ...typographyTokens.display,
    fontSize: 18,
    marginTop: 18,
    marginBottom: 4,
  },
  kakshyaCard: {
    borderWidth: 1,
    borderLeftWidth: 4,
    borderRadius: 12,
    padding: 12,
    marginTop: 9,
  },
  advancedCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  kakshyaPlanet: {
    fontSize: 13,
    fontWeight: '900',
  },
  kakshyaStatus: {
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.7,
  },
  kakshyaCoordinate: {
    ...typographyTokens.display,
    fontSize: 18,
    marginTop: 4,
  },
  timingCard: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    marginTop: 9,
  },
  timingCoordinate: {
    ...typographyTokens.display,
    fontSize: 18,
    marginBottom: 3,
  },
  transitLoadingCard: {
    minHeight: 150,
    borderWidth: 1,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    marginBottom: 12,
  },
  transitSnapshotCard: {
    borderWidth: 1,
    borderRadius: 14,
    padding: 12,
    marginTop: 10,
  },
  transitHouse: {
    fontSize: 11,
    fontWeight: '900',
  },
  transitMetricRow: {
    flexDirection: 'row',
    gap: 7,
    marginTop: 10,
  },
  transitMetric: {
    flex: 1,
    minHeight: 76,
    borderWidth: 1,
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 6,
    justifyContent: 'center',
  },
  transitMetricLabel: {
    fontSize: 8,
    lineHeight: 11,
    fontWeight: '900',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  transitMetricValue: {
    fontSize: 18,
    lineHeight: 22,
    fontWeight: '900',
  },
  transitMetricBand: {
    fontSize: 8,
    lineHeight: 11,
    textTransform: 'capitalize',
  },
  transitSensitiveLine: {
    fontSize: 10,
    lineHeight: 14,
    fontWeight: '800',
    marginTop: 10,
    textTransform: 'capitalize',
  },
  transitHitCount: {
    fontSize: 17,
    fontWeight: '900',
  },
  transitHitCard: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 11,
    marginTop: 9,
  },
  transitFilterRow: {
    gap: 7,
    paddingVertical: 12,
  },
  transitFilterChip: {
    borderWidth: 1,
    borderRadius: 18,
    paddingVertical: 7,
    paddingHorizontal: 12,
  },
  transitFilterText: {
    fontSize: 10,
    fontWeight: '900',
  },
  transitEventCard: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 11,
    marginBottom: 8,
  },
  transitEventTime: {
    fontSize: 9,
    lineHeight: 12,
    fontWeight: '800',
    marginBottom: 4,
  },
  transitGuardrail: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 9,
    borderWidth: 1,
    borderRadius: 14,
    padding: 13,
    marginBottom: 12,
  },
  transitGuardrailText: {
    flex: 1,
    fontSize: 10,
    lineHeight: 15,
  },
};
