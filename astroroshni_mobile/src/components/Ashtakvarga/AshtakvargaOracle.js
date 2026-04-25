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
  Clipboard,
  Alert,
  ActivityIndicator,
  StyleSheet,
  TextInput,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { ScrollView as GHScrollView } from 'react-native-gesture-handler';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
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
import { pricingAPI } from '../../services/api';
import CreditModal from '../CreditModal';

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
  { key: 'matrix', label: 'Matrix', icon: 'table-outline' },
  { key: 'sav', label: 'SAV', icon: 'grid-outline' },
  { key: 'bav', label: 'BAV', icon: 'planet-outline' },
  { key: 'ai', label: 'Analysis', icon: 'analytics-outline' },
];
const SIGN_SHORT_NAMES = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'];
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

export default function AshtakvargaOracle({ navigation }) {
  const { theme, colors } = useTheme();
  const { credits, fetchBalance } = useCredits();
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
            navigation.replace('BirthProfileIntro', { returnTo: 'AshtakvargaOracle' });
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
    }, [navigation])
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
  }, [birthData, selectedDate]);

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
        navigation.replace('BirthProfileIntro', { returnTo: 'AshtakvargaOracle' });
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
        chart_type: isSameDate ? 'lagna' : 'transit'
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

  const onConfirmAnalysisCreditModal = () => {
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
    <View style={[styles.analysisModeTabs, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(249,115,22,0.08)' }]}>
      {ASHTAKVARGA_ANALYSIS_MODES.map((mode) => {
        const isActive = analysisMode === mode.key;
        return (
          <TouchableOpacity
            key={mode.key}
            style={[
              styles.analysisModeTab,
              isActive && {
                backgroundColor: theme === 'dark' ? 'rgba(255,215,0,0.18)' : 'rgba(249,115,22,0.16)',
              },
            ]}
            onPress={() => setAnalysisMode(mode.key)}
          >
            <Ionicons
              name={mode.icon}
              size={17}
              color={isActive ? colors.primary : colors.textSecondary}
            />
            <Text style={[styles.analysisModeTabText, { color: isActive ? colors.primary : colors.textSecondary }]}>
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
      <View style={[styles.analysisAnswerCard, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.78)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)' }]}>
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
    <View style={[styles.analysisPanelCard, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.72)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)' }]}>
      <View style={styles.analysisPanelHeader}>
        <View style={[styles.analysisPanelIcon, { backgroundColor: theme === 'dark' ? 'rgba(255,215,0,0.15)' : 'rgba(249,115,22,0.12)' }]}>
          <Ionicons name="person-circle-outline" size={24} color={colors.primary} />
        </View>
        <View style={styles.analysisPanelTitleBlock}>
          <Text style={[styles.analysisPanelTitle, { color: colors.text }]}>Birth Chart Ashtakvarga Predictions</Text>
          <Text style={[styles.analysisPanelSubtitle, { color: colors.textSecondary }]}>
            A full natal reading from your bindus, houses, dasha context, and life-area strengths.
          </Text>
        </View>
      </View>
      <View style={styles.analysisBenefits}>
        {renderAnalysisBenefit('home-outline', 'Lifelong strengths and weaker houses')}
        {renderAnalysisBenefit('briefcase-outline', 'Career, relationship, money, and health themes')}
        {renderAnalysisBenefit('refresh-circle-outline', 'Saved readings reopen without using credits')}
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
        <View style={[styles.analysisPanelCard, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.72)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)' }]}>
          <View style={styles.analysisPanelHeader}>
            <View style={[styles.analysisPanelIcon, { backgroundColor: theme === 'dark' ? 'rgba(255,215,0,0.15)' : 'rgba(249,115,22,0.12)' }]}>
              <Ionicons name="today-outline" size={24} color={colors.primary} />
            </View>
            <View style={styles.analysisPanelTitleBlock}>
              <Text style={[styles.analysisPanelTitle, { color: colors.text }]}>Transit Ashtakvarga Predictions</Text>
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
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <>
                  <Ionicons name="analytics-outline" size={16} color="#fff" />
                  <Text style={styles.analysisAskButtonText}>Generate Transit Reading</Text>
                </>
              )}
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.analysisHistoryButton, { borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)' }]}
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
            <Text style={styles.askUserText}>{message.text}</Text>
          </View>
        </View>
      );
    }

    const answer = message.data || {};
    const headline = answer.headline || answer.oracle_message || '';
    const sections = Array.isArray(answer.sections) ? answer.sections : [];

    return (
      <View key={message.id} style={styles.askAssistantBubbleRow}>
        <View style={[styles.askAssistantAvatar, { backgroundColor: theme === 'dark' ? 'rgba(255,215,0,0.16)' : 'rgba(249,115,22,0.12)' }]}>
          <Ionicons name="sparkles-outline" size={16} color={colors.primary} />
        </View>
        <View style={[styles.askAssistantBubble, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.8)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)' }]}>
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
    <View style={[styles.askChatCard, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.7)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)' }]}>
      <View style={styles.askChatHeader}>
        <View style={styles.askChatTitleBlock}>
          <Text style={[styles.analysisQuestionTitle, { color: colors.text }]}>Ask Ashtakvarga</Text>
          <Text style={[styles.analysisQuestionSubtitle, { color: colors.textSecondary }]}>
            Keep asking follow-ups about career, money, marriage, weak houses, planets, or timing.
          </Text>
        </View>
        <TouchableOpacity
          style={[styles.analysisHistoryButton, { borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)' }]}
          onPress={() => navigation.navigate('AshtakvargaHistory')}
        >
          <Ionicons name="time-outline" size={15} color={colors.textSecondary} />
          <Text style={[styles.analysisHistoryButtonText, { color: colors.textSecondary }]}>History</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.askMessages}>
        {askMessages.length === 0 ? (
          <View style={styles.askAssistantBubbleRow}>
            <View style={[styles.askAssistantAvatar, { backgroundColor: theme === 'dark' ? 'rgba(255,215,0,0.16)' : 'rgba(249,115,22,0.12)' }]}>
              <Ionicons name="sparkles-outline" size={16} color={colors.primary} />
            </View>
            <View style={[styles.askAssistantBubble, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.8)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)' }]}>
              <Text style={[styles.askAssistantHeadline, { color: colors.text }]}>
                What would you like to understand from your Ashtakvarga?
              </Text>
              <Text style={[styles.askAssistantBullet, { color: colors.textSecondary }]}>
                Start with one life area, then ask follow-ups as the reading unfolds.
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
            style={[styles.analysisSuggestionChip, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(249,115,22,0.12)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.14)' : 'rgba(249,115,22,0.18)' }]}
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
          style={[styles.askComposerHistoryLink, { borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)', backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)' }]}
          onPress={() => navigation.navigate('AshtakvargaHistory')}
        >
          <Ionicons name="time-outline" size={15} color={colors.textSecondary} />
          <Text style={[styles.analysisHistoryButtonText, { color: colors.textSecondary }]}>History</Text>
        </TouchableOpacity>
      </View>

      <View style={[styles.askComposer, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.04)' : '#fff', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)' }]}>
        <TextInput
          value={analysisQuestion}
          onChangeText={setAnalysisQuestion}
          placeholder="Ask a follow-up..."
          placeholderTextColor={theme === 'dark' ? 'rgba(255,255,255,0.45)' : 'rgba(107,114,128,0.9)'}
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
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Ionicons name="send" size={18} color="#fff" />
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
          <Text style={[styles.mapTitle, { color: colors.text }]}>Ashtakvarga Predictions</Text>
          <Text style={[styles.mapSubtitle, { color: colors.textSecondary }]}>
            Choose the kind of reading you want before using credits.
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
              <Text style={{ color: '#fff', fontWeight: '600' }}>Retry</Text>
            </TouchableOpacity>
          )}
        </ScrollView>
      );
    }

    return (
      <ScrollView style={styles.tabContent} contentContainerStyle={{ paddingBottom: 20 }} showsVerticalScrollIndicator={false}>
        <View style={styles.titleContainer}>
          <Text style={[styles.mapTitle, { color: colors.text }]}>Sarvashtakvarga Chart</Text>
          <Text style={[styles.mapSubtitle, { color: colors.textSecondary }]}>Tap any house to see its cosmic strength</Text>
        </View>
        
        <DateNavigator 
          date={selectedDate}
          onDateChange={setSelectedDate}
          cosmicTheme={true}
          resetDate={birthData ? (parseCalendarDateInput(birthData.date) || new Date()) : new Date()}
        />
        
        <View style={[styles.chartContainer, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)', borderWidth: 1, borderColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.2)', borderRadius: 16 }]}>
          <AshtakvargaChart 
            chartData={oracleData.chart_data}
            ashtakvargaData={oracleData.chart_ashtakavarga}
            birthAshtakvargaData={birthOracleData?.chart_ashtakavarga}
            onHousePress={(houseNum, bindus, signName) => {
              openSecretScroll(signName, bindus, houseNum - 1);
            }}
            cosmicTheme={true}
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
              colors={['#2c3e50', '#34495e', '#5d6d7e']}
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
                  <Text style={styles.lifePredictionsText}>
                    Consulting Dots of Destiny...
                  </Text>
                  <View style={styles.progressContainer}>
                    <View style={styles.progressBar}>
                      <View style={[styles.progressFill, { width: `${loadingProgress}%` }]} />
                    </View>
                    <Text style={styles.progressText}>{Math.round(loadingProgress)}%</Text>
                  </View>
                </View>
              ) : (
                <View style={styles.loadingContent}>
                  <ActivityIndicator size="small" color="#fff" style={{ marginBottom: 8 }} />
                  <Text style={styles.lifePredictionsText}>Checking saved reading…</Text>
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
            colors={['#5b2c83', '#8e44ad', '#c39bd3']}
            style={styles.lifePredictionsGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <>
              <Text style={styles.lifePredictionsIconLarge}>🌟</Text>
              <Text style={styles.lifePredictionsHeadline}>Dots of Destiny</Text>
              <Text style={styles.lifePredictionsTeaser}>
                Full reading from your bindus — career, relationships, timing windows, dasha & remedies.
              </Text>
              <View style={styles.lifePredictionsChips}>
                <Text style={styles.lifePredictionsChip}>12 houses</Text>
                <Text style={styles.lifePredictionsChip}>Transits</Text>
                <Text style={styles.lifePredictionsChip}>Dasha</Text>
              </View>
              <View style={styles.lifePredictionsCtaRow}>
                <Text style={styles.lifePredictionsCtaText}>Open life predictions</Text>
                <Ionicons name="chevron-forward" size={20} color="#fff" style={{ opacity: 0.95, marginLeft: 4 }} />
              </View>
              <Text style={styles.lifePredictionsCreditHint}>
                {lifePredictionsCreditCost} credits first run · saved reading replays free
              </Text>
              <Text style={styles.lifePredictionsSubtext}>Vinay Aditya · Ashtakavarga methodology</Text>
            </>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    );
  };

  const renderBavTab = () => (
    <ScrollView style={styles.tabContent} contentContainerStyle={{ paddingBottom: 20 }} showsVerticalScrollIndicator={false}>
      <View style={styles.titleContainer}>
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
                style={[styles.planetButton, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.15)', borderWidth: 1, borderColor: theme === 'dark' ? 'rgba(255,255,255,0.2)' : 'rgba(249,115,22,0.3)' }]}
                onPress={() => openPlanetChart(planet, planetChart)}
              >
                <Text style={[styles.planetIcon, { color: '#FFFFFF' }]}>{getPlanetIcon(planet)}</Text>
                <Text style={[styles.planetName, { color: colors.text }]}>{planet}</Text>
                <Text style={[styles.planetBindus, { color: '#FFFFFF' }]}>{totalBindus}</Text>
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
    const rows = SIGN_SHORT_NAMES.map((sign, index) => ({
      sign: `${sign} (${index + 1})`,
      values: planets.map((planet) => individualCharts?.[planet]?.bindus?.[index] ?? 0),
      sav: savHouses?.[(index + 1).toString()]?.bindus ?? 0,
    }));

    return (
      <ScrollView style={styles.tabContent} contentContainerStyle={{ paddingBottom: 20 }} showsVerticalScrollIndicator={false}>
        <View style={styles.titleContainer}>
          <Text style={[styles.mapTitle, { color: colors.text }]}>SAV + BAV Matrix</Text>
          <Text style={[styles.mapSubtitle, { color: colors.textSecondary }]}>See every sign’s Bhinnashtakvarga values together with the Sarvashtakvarga total.</Text>
        </View>

        <View style={[styles.matrixCard, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.2)' }]}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View>
              <View style={[styles.matrixRow, styles.matrixHeaderRow, { borderBottomColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)' }]}>
                <Text style={[styles.matrixHeaderCell, styles.matrixSignCell, { color: colors.text }]}>Sign</Text>
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
                      ? { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.03)' : 'rgba(255,255,255,0.5)' }
                      : null,
                    { borderBottomColor: theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(249,115,22,0.12)' },
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

  const renderActiveTab = () => {
    const tabKey = ASHTAKVARGA_TABS[activeTab]?.key;
    if (tabKey === 'ai') return renderOraclesPulse();
    if (tabKey === 'bav') return renderBavTab();
    if (tabKey === 'matrix') return renderCombinedMatrixTab();
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
      console.error('No birth data available for life predictions');
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
                ? 'Still processing after 6 minutes. Try opening Life predictions again later for your saved reading.'
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
        console.error('Failed to generate life predictions:', response.status, message);
        Alert.alert('Life predictions', message);
        if (response.status === 402) {
          fetchBalance();
        }
      }
    } catch (error) {
      console.error('Error generating life predictions:', error);
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

  /** Main CTA: open cached reading immediately, or credit modal only if a new generation is needed */
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
        'Could not check for a saved reading. Check your connection and try again.'
      );
    } finally {
      setLifePredictionsCacheChecking(false);
    }
  };

  const onConfirmLifePredictionsCreditModal = () => {
    const mode = lifePredictionsCreditModalMode;
    setLifePredictionsCreditModalMode(null);
    generateLifePredictions(mode === 'regenerate');
  };

  const closeLifePredictionsCreditModal = () => setLifePredictionsCreditModalMode(null);

  const lifePredictionsCreditModalTitle =
    lifePredictionsCreditModalMode === 'regenerate'
      ? 'Regenerate Dots of Destiny?'
      : 'Dots of Destiny reading';

  const lifePredictionsCreditModalDescription =
    lifePredictionsCreditModalMode === 'regenerate'
      ? `This runs a fresh AI reading and replaces your saved one. It will use ${lifePredictionsCreditCost} credits if the generation succeeds. Your balance: ${credits} credits.`
      : `Starting a new AI reading uses up to ${lifePredictionsCreditCost} credits if you do not already have one saved for this profile. Your balance: ${credits} credits.`;

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
      <View style={styles.loadingContainer}>
        <LinearGradient colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd] : [colors.gradientStart, colors.gradientStart, colors.gradientStart]} style={styles.loadingGradient}>
          <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
            <Text style={styles.loadingText}>🔮</Text>
          </Animated.View>
          <Text style={[styles.loadingSubtext, { color: colors.text }]}>Consulting the Oracle...</Text>
        </LinearGradient>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
      <LinearGradient colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.primary] : [colors.gradientStart, colors.gradientStart, colors.gradientStart, colors.gradientStart]} style={styles.gradient}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={colors.text} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1}>
              Ashtakvarga
            </Text>
            {birthData ? (
              <NativeSelectorChip
                birthData={birthData}
                onPress={() => navigation.navigate('SelectNative', { returnTo: 'AshtakvargaOracle' })}
                maxLength={10}
                showIcon={false}
              />
            ) : null}
            <TouchableOpacity onPress={() => setShowInfoModal(true)} style={styles.infoButton}>
              <Ionicons name="information-circle-outline" size={24} color={colors.text} />
            </TouchableOpacity>
          </View>

          <View style={styles.tabNavigation}>
            {ASHTAKVARGA_TABS.map((tab, index) => {
              const isActive = activeTab === index;
              return (
                <TouchableOpacity
                  key={tab.key}
                  style={[
                    styles.tab,
                    isActive && styles.activeTab,
                    {
                      backgroundColor: isActive
                        ? (theme === 'dark' ? 'rgba(255, 215, 0, 0.18)' : 'rgba(249,115,22,0.15)')
                        : (theme === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(249,115,22,0.06)'),
                    },
                  ]}
                  onPress={() => setActiveTab(index)}
                >
                  <Ionicons
                    name={tab.icon}
                    size={18}
                    color={isActive ? colors.primary : colors.textSecondary}
                  />
                  <Text
                    style={[
                      styles.tabText,
                      { color: isActive ? colors.primary : colors.textSecondary },
                      isActive && styles.activeTabText,
                    ]}
                  >
                    {tab.label}
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
            <View style={styles.modalOverlay}>
              <View style={styles.predictionsModal}>
                <LinearGradient
                  colors={['rgba(26, 0, 51, 0.95)', 'rgba(45, 27, 78, 0.9)']}
                  style={styles.predictionsGradient}
                >
                  <TouchableOpacity
                    style={styles.regeneratePredictionButton}
                    onPress={confirmRegenerateLifePredictions}
                    disabled={loadingLifePredictions}
                  >
                    <Ionicons name="refresh" size={18} color="#ffd700" />
                    <Text style={styles.regeneratePredictionText}>Regenerate</Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={styles.closeButton}
                    onPress={() => setShowLifePredictions(false)}
                  >
                    <Ionicons name="close" size={24} color={colors.text} />
                  </TouchableOpacity>

                  {loadingLifePredictions && lifePredictions ? (
                    <View style={styles.predictionsRegenOverlay}>
                      <ActivityIndicator size="large" color="#ffd700" />
                      <Text style={styles.predictionsRegenOverlayText}>Updating reading…</Text>
                    </View>
                  ) : null}
                  
                  <ScrollView showsVerticalScrollIndicator={false}>
                    <Text style={[styles.predictionsTitle, { color: colors.text }]}>Life Predictions</Text>
                    <Text style={[styles.predictionsSubtitle, { color: colors.primary }]}>{lifePredictions?.methodology || lifePredictions?.predictions?.methodology || "Vinay Aditya's Dots of Destiny"}</Text>
                    {lifePredictions?.cached ? (
                      <Text style={[styles.predictionsCachedBadge, { color: colors.textSecondary }]}>
                        Saved reading — no credits used to view again. Regenerate for a fresh AI pass ({lifePredictionsCreditCost} credits).
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
                                    <View key={key} style={styles.predictionDomainCard}>
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
                                    <View key={index} style={styles.timingHighlightCard}>
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
            <View style={styles.modalOverlay}>
              <TouchableOpacity 
                style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
                activeOpacity={1}
                onPress={() => {
                  setShowSecretScroll(false);
                  setYearlyStrength(null);
                }}
              />
              <View style={styles.secretScroll}>
                <LinearGradient
                  colors={theme === 'dark' ? ['rgba(26, 0, 51, 0.95)', 'rgba(45, 27, 78, 0.9)'] : ['rgba(254, 252, 251, 0.98)', 'rgba(254, 252, 251, 0.95)']}
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
                            <View key={sign} style={[styles.miniPillar, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.15)', borderRadius: 8, padding: 8, borderWidth: 1, borderColor: theme === 'dark' ? 'rgba(255,255,255,0.2)' : 'rgba(249,115,22,0.3)' }]}>
                              <Text style={[styles.miniBindus, { color: '#FFFFFF' }]}>{bindus}</Text>
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
                      
                      <View style={[styles.significationBox, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)', borderWidth: 1, borderColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.2)', borderRadius: 12, padding: 16, marginBottom: 20 }]}>
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
                            colors={['#ff6b35', '#ffd700']}
                            style={styles.yearlyButtonGradient}
                          >
                            <Text style={styles.yearlyButtonText}>📊 View Yearly Strength</Text>
                          </LinearGradient>
                        </TouchableOpacity>
                      )}
                      
                      {loadingYearly && (
                        <View style={styles.loadingYearlyContainer}>
                          <Text style={[styles.loadingYearlyText, { color: colors.text }]}>Calculating 365 days...</Text>
                          <View style={styles.progressBar}>
                            <View style={[styles.progressFill, { width: `${yearlyProgress}%` }]} />
                          </View>
                          <Text style={styles.progressText}>{Math.round(yearlyProgress)}%</Text>
                        </View>
                      )}
                      
                      {yearlyStrength && (
                        <View style={[styles.yearlyStrengthContainer, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)', borderWidth: 1, borderColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.2)' }]}>
                          <Text style={[styles.yearlyTitle, { color: colors.text }]}>House {yearlyStrength.house} - {yearlyStrength.year} Strength</Text>
                          <Text style={[styles.yearlySubtitle, { color: colors.primary }]}>Birth Chart: {yearlyStrength.birth_bindus} bindus</Text>
                          
                          <ScrollView style={styles.yearlyDataScroll} showsVerticalScrollIndicator={true}>
                            {yearlyStrength.daily_data && yearlyStrength.daily_data.map((day, index) => (
                              <View key={index} style={[
                                styles.dayRow,
                                { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)' },
                                day.category === 'strong' && styles.strongDay,
                                day.category === 'weak' && styles.weakDay
                              ]}>
                                <Text style={[styles.dayDate, { color: colors.text }]}>{day.date}</Text>
                                <Text style={[styles.dayBindus, { color: colors.primary }]}>{day.bindus} bindus</Text>
                                <Text style={[
                                  styles.dayDiff,
                                  day.difference > 0 ? styles.positiveDiff : styles.negativeDiff
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
        </SafeAreaView>
      </LinearGradient>

      <Modal
        visible={showInfoModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowInfoModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.infoModal}>
            <LinearGradient
              colors={theme === 'dark' ? ['rgba(26, 0, 51, 0.95)', 'rgba(45, 27, 78, 0.9)'] : ['rgba(254, 252, 251, 0.98)', 'rgba(254, 252, 251, 0.95)']}
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
                
                <View style={[styles.infoSection, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.2)' }]}>
                  <Text style={[styles.infoSectionTitle, { color: colors.primary }]}>🎯 What is Ashtakvarga?</Text>
                  <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                    Ashtakvarga is an ancient Vedic astrology system that measures planetary strength through numerical points called "bindus" or "dots". It provides precise predictions about life events and timing.
                  </Text>
                </View>

                <View style={[styles.infoSection, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.2)' }]}>
                  <Text style={[styles.infoSectionTitle, { color: colors.primary }]}>📊 Sarvashtakvarga Chart</Text>
                  <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                    The main chart you see combines all planetary influences. Each house shows total bindus (points) from all planets. Higher numbers (30+) indicate strength, lower numbers (25-) suggest challenges.
                  </Text>
                </View>

                <View style={[styles.infoSection, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.2)' }]}>
                  <Text style={[styles.infoSectionTitle, { color: colors.primary }]}>🪐 Bhinnashtakvarga Charts</Text>
                  <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                    Individual planet charts (Sun, Moon, Mars, etc.) show where each planet receives support. Tap any planet button to see its specific influence pattern across the zodiac signs.
                  </Text>
                </View>

                <View style={[styles.infoSection, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.2)' }]}>
                  <Text style={[styles.infoSectionTitle, { color: colors.primary }]}>🔮 How to Use in Our App</Text>
                  <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                    • Tap any house in the main chart for detailed insights{"\n"}
                    • Use the date navigator to see transit effects{"\n"}
                    • Check individual planet charts for specific influences{"\n"}
                    • Generate yearly strength analysis for timing{"\n"}
                    • Higher bindus = favorable periods for that life area
                  </Text>
                </View>

                <View style={[styles.infoSection, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.2)' }]}>
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
  loadingText: { fontSize: 60, marginBottom: 20 },
  loadingSubtext: { color: COLORS.white, fontSize: 16 },
  
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
    paddingHorizontal: 20,
    paddingVertical: 15,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    flex: 1,
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
  },
  headerRight: { width: 40 },
  infoButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  tabNavigation: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
    borderRadius: 20,
    marginHorizontal: 3,
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
    fontWeight: '600',
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
    fontSize: 19,
    lineHeight: 24,
    fontWeight: '800',
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
    fontSize: 20,
    fontWeight: '800',
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
    fontSize: 22,
    fontWeight: '800',
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
    alignItems: 'center',
    paddingVertical: 5,
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
    borderRadius: 18,
    overflow: 'hidden',
    elevation: 10,
    shadowColor: '#6c3483',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
  },
  loadingButton: {
    shadowColor: '#2c3e50',
  },
  lifePredictionsGradient: {
    paddingVertical: 18,
    paddingHorizontal: 16,
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
  lifePredictionsHeadline: {
    fontSize: 22,
    fontWeight: '800',
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
    backgroundColor: 'rgba(0,0,0,0.2)',
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
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 4,
  },
  mapSubtitle: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.7)',
    textAlign: 'center',
    marginBottom: 10,
  },
  chartContainer: {
    marginBottom: 2,
    paddingHorizontal: 5,
    paddingTop: 8,
    paddingBottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  planetaryToggle: { 
    marginTop: 16,
    marginBottom: 8,
    paddingVertical: 5
  },
  toggleTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 8,
  },
  planetButton: {
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 6,
    marginRight: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  planetIcon: { fontSize: 20, marginBottom: 4 },
  planetName: {
    fontSize: 12,
    color: COLORS.white,
  },
  planetBindus: {
    fontSize: 10,
    color: '#ffd700',
    fontWeight: '600',
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
    borderRadius: 20,
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
    fontSize: 24,
    fontWeight: '700',
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
    borderRadius: 20,
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
    fontSize: 24,
    fontWeight: '700',
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
    borderRadius: 20,
    overflow: 'hidden',
  },
  infoGradient: {
    padding: 20,
    paddingTop: 50,
  },
  infoTitle: {
    fontSize: 24,
    fontWeight: '700',
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
};
