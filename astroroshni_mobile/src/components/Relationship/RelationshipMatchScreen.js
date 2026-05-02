import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { useCredits } from '../../credits/CreditContext';
import { chartAPI, pricingAPI, relationshipAPI } from '../../services/api';
import { storage } from '../../services/storage';
import { generateRelationshipReportPDF, getLogoDataUriForModule, sharePDFOnWhatsApp } from '../../utils/pdfGenerator';

const CLIMATE_COLORS = {
  highly_favorable: '#16a34a',
  favorable: '#22c55e',
  mixed: '#f59e0b',
  challenging: '#ef4444',
};

const dedupeProfiles = (profiles = []) => {
  const seen = new Set();
  return profiles.filter((profile) => {
    const key = String(
      profile?.id ??
      profile?._id ??
      `${profile?.name || ''}|${profile?.date || ''}|${profile?.time || ''}|${profile?.latitude || ''}|${profile?.longitude || ''}`
    );
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
};

const sanitizeBirthData = (profile = {}) => ({
  name: profile.name,
  date: profile.date,
  time: profile.time,
  place: profile.place,
  latitude: profile.latitude,
  longitude: profile.longitude,
});

const formatWindowRange = (windowData) => {
  if (!windowData?.start_date || !windowData?.end_date) return null;
  const start = new Date(windowData.start_date);
  const end = new Date(windowData.end_date);
  const fmt = (value) => value.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  return `${fmt(start)} - ${fmt(end)}`;
};

const summarizeProfile = (profile, t) => {
  if (!profile) return t('relationshipMatch.notSelected');
  const bits = [profile.date, profile.time, profile.place].filter(Boolean);
  return bits.join(' • ') || t('relationshipMatch.profileReady');
};

const getCurrentClimateLabel = (climate, t) =>
  t(`relationshipMatch.climate.${climate || 'mixed'}`);

const scoreText = (value, fallback = '--') =>
  typeof value === 'number' ? `${Math.round(value)}%` : fallback;

const combineScores = (...values) => {
  const valid = values.filter((value) => typeof value === 'number');
  if (!valid.length) return null;
  return valid.reduce((sum, value) => sum + value, 0) / valid.length;
};

const bandTone = (band = '') => {
  const normalized = String(band).toLowerCase();
  if (normalized.includes('strong') || normalized.includes('supportive')) return 'supportive';
  if (normalized.includes('sensitive') || normalized.includes('challeng')) return 'challenging';
  return 'neutral';
};

const titleCase = (value = '') =>
  String(value)
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());

const cleanReportText = (value = '') =>
  String(value)
    .replace(/<term\b[^>]*>(.*?)<\/term>/gi, '$1')
    .replace(/<\/?[^>]+>/g, '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\*\*/g, '')
    .trim();

const ASHTAKOOTA_ORDER = [
  ['varna', 'relationshipMatch.ashtakoota.varna'],
  ['vashya', 'relationshipMatch.ashtakoota.vashya'],
  ['tara', 'relationshipMatch.ashtakoota.tara'],
  ['yoni', 'relationshipMatch.ashtakoota.yoni'],
  ['graha_maitri', 'relationshipMatch.ashtakoota.grahaMaitri'],
  ['gana', 'relationshipMatch.ashtakoota.gana'],
  ['bhakoot', 'relationshipMatch.ashtakoota.bhakoot'],
  ['nadi', 'relationshipMatch.ashtakoota.nadi'],
];

const normalizeChartProfile = (chart = {}) => ({
  id: chart.id || chart._id,
  name: chart.name,
  date: chart.date,
  time: chart.time,
  place: chart.place,
  latitude: chart.latitude,
  longitude: chart.longitude,
  gender: chart.gender,
  relation: chart.relation,
});

export default function RelationshipMatchScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { theme, colors, androidLightCardFixStyle } = useTheme();
  const { credits } = useCredits();
  const isDark = theme === 'dark';

  const [savedProfiles, setSavedProfiles] = useState([]);
  const [personOne, setPersonOne] = useState(null);
  const [personTwo, setPersonTwo] = useState(null);
  const [loadingBootstrap, setLoadingBootstrap] = useState(true);
  const [loadingResult, setLoadingResult] = useState(false);
  const [result, setResult] = useState(null);
  const [pricing, setPricing] = useState({});
  const [pricingOriginal, setPricingOriginal] = useState({});
  const [premiumReport, setPremiumReport] = useState(null);
  const [loadingPremiumReport, setLoadingPremiumReport] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [expandedGunaKey, setExpandedGunaKey] = useState(null);
  const [expandedDetailKey, setExpandedDetailKey] = useState(null);

  const loadScreenData = useCallback(async () => {
    try {
      setLoadingBootstrap(true);
      const [currentBirthData, localProfiles, pricingResponse, chartsResponse] = await Promise.all([
        storage.getBirthDetails(),
        storage.getBirthProfiles(),
        pricingAPI.getPricing().catch(() => null),
        chartAPI.getExistingCharts('', 50, 0).catch(() => null),
      ]);

      const apiProfiles = Array.isArray(chartsResponse?.data?.charts)
        ? chartsResponse.data.charts.map(normalizeChartProfile)
        : [];

      const mergedProfiles = dedupeProfiles([
        ...(currentBirthData ? [currentBirthData] : []),
        ...(Array.isArray(localProfiles) ? localProfiles : []),
        ...apiProfiles,
      ]).filter((profile) => profile?.name && profile?.date && profile?.time);

      setSavedProfiles(mergedProfiles);

      if (pricingResponse?.data?.pricing) {
        setPricing(pricingResponse.data.pricing);
        setPricingOriginal(pricingResponse.data.pricing_original || {});
      }

      if (!mergedProfiles.length) {
        setPersonOne(null);
        setPersonTwo(null);
        return;
      }

    } catch (error) {
      console.error('Relationship match bootstrap failed:', error);
    } finally {
      setLoadingBootstrap(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      const returnedProfile = route.params?.birthData || route.params?.birthDetails;
      const returnedTarget = route.params?.selectorTarget;

      if (returnedProfile && returnedTarget) {
        if (returnedTarget === 'personOne') {
          setPersonOne(returnedProfile);
        } else if (returnedTarget === 'personTwo') {
          setPersonTwo(returnedProfile);
        }
        navigation.setParams({
          birthData: undefined,
          birthDetails: undefined,
          birthChartId: undefined,
          selectorTarget: undefined,
        });
      }

      loadScreenData();
    }, [loadScreenData, navigation, route.params])
  );

  const premiumChatCost = pricing.partnership ?? 0;
  const marriageCost = pricing.marriage ?? 0;
  const premiumReportCost = pricing.marriage ?? 0;

  const currentWindow = result?.timing_overlay?.shared?.current_window;
  const favorableWindows = result?.timing_overlay?.shared?.next_favorable_windows || [];
  const firstFavorableWindow = favorableWindows[0];
  const positives = (result?.evidence_summary?.positive_factors || []).slice(0, 3);
  const cautions = (result?.evidence_summary?.caution_factors || []).slice(0, 3);
  const contradictions = result?.evidence_summary?.contradictions || [];
  const firstContradiction = contradictions[0];
  const pairManglikStatus = result?.manglik_analysis?.compatibility?.status;
  const effectiveScore = result?.guna_milan?.effective_total_score ?? result?.guna_milan?.total_score;
  const currentClimate = currentWindow?.climate || 'mixed';
  const overallPercentage = result?.overall_score?.percentage;
  const evidenceObjects = result?.evidence_objects || {};
  const supportiveEvidence = evidenceObjects?.supportive || [];
  const challengingEvidence = evidenceObjects?.challenging || [];
  const neutralEvidence = evidenceObjects?.neutral || [];
  const crossChart = result?.relationship_indicators?.cross_chart || {};
  const boyProfile = result?.profiles?.boy || {};
  const girlProfile = result?.profiles?.girl || {};
  const boySeventh = boyProfile?.seventh_house || {};
  const girlSeventh = girlProfile?.seventh_house || {};
  const boyNavamsa = boyProfile?.navamsa_synthesis || {};
  const girlNavamsa = girlProfile?.navamsa_synthesis || {};
  const gunaMilan = result?.guna_milan || {};
  const ashtakootaKoots = gunaMilan?.koots || {};
  const personTimingRows = [
    {
      key: 'personOne',
      label: personOne?.name || t('relationshipMatch.personOne'),
      timing: result?.timing_overlay?.boy,
    },
    {
      key: 'personTwo',
      label: personTwo?.name || t('relationshipMatch.personTwo'),
      timing: result?.timing_overlay?.girl,
    },
  ];

  const compareMissingCharts = !personOne || !personTwo;
  const compareDisabled = loadingResult;

  const handleAnalyze = async () => {
    if (!personOne || !personTwo) {
      Alert.alert(t('relationshipMatch.incompleteTitle'), t('relationshipMatch.incompleteBody'));
      return;
    }

    try {
      setLoadingResult(true);
      setPremiumReport(null);
      const response = await relationshipAPI.analyzeCompatibility(
        sanitizeBirthData(personOne),
        sanitizeBirthData(personTwo)
      );
      const payload = response?.data?.compatibility_analysis || response?.data;
      setResult(payload);
      setExpandedDetailKey(null);
    } catch (error) {
      console.error('Relationship match failed:', error);
      Alert.alert(
        t('relationshipMatch.errorTitle'),
        error?.response?.data?.detail || t('relationshipMatch.errorBody')
      );
    } finally {
      setLoadingResult(false);
    }
  };

  const unlockPremiumReport = async (forceRegenerate = false) => {
    if (!result || !personOne || !personTwo) return;
    if (premiumReportCost > 0 && credits < premiumReportCost && (!premiumReport || forceRegenerate)) {
      navigation.navigate('Credits');
      return;
    }

    try {
      setLoadingPremiumReport(true);
      const response = await relationshipAPI.getPremiumCompatibilityReport(
        sanitizeBirthData(personOne),
        sanitizeBirthData(personTwo),
        'english',
        forceRegenerate
      );
      setPremiumReport(response?.data?.premium_report || null);
    } catch (error) {
      console.error('Premium compatibility report failed:', error);
      Alert.alert(
        t('relationshipMatch.premiumErrorTitle'),
        error?.response?.data?.detail || t('relationshipMatch.premiumErrorBody')
      );
    } finally {
      setLoadingPremiumReport(false);
    }
  };

  const downloadPremiumReport = async () => {
    if (!result) {
      Alert.alert(t('relationshipMatch.noReportTitle'), t('relationshipMatch.noReportBody'));
      return;
    }
    if (!premiumReport) {
      Alert.alert(t('relationshipMatch.unlockBeforeDownloadTitle'), t('relationshipMatch.unlockBeforeDownloadBody'));
      return;
    }

    try {
      setIsExportingPdf(true);
      const logoDataUri = await getLogoDataUriForModule(require('../../../assets/logo.png'));
      const pdfUri = await generateRelationshipReportPDF({
        personOne,
        personTwo,
        result,
        premiumReport,
        logoDataUri,
      });
      await sharePDFOnWhatsApp(pdfUri);
    } catch (error) {
      console.error('Relationship report export failed:', error);
      Alert.alert(t('relationshipMatch.downloadErrorTitle'), error?.message || t('relationshipMatch.downloadErrorBody'));
    } finally {
      setIsExportingPdf(false);
    }
  };

  const openPremiumChat = () => {
    if (!result) return;
    if (premiumChatCost > 0 && credits < premiumChatCost) {
      navigation.navigate('Credits');
      return;
    }
    navigation.navigate('Home', {
      prefillPartnership: {
        nativeChart: personOne,
        partnerChart: personTwo,
        relationshipType: t('relationshipMatch.followupLabel'),
        initialPrompt: t('relationshipMatch.premiumPrompt', {
          personOne: personOne?.name || t('relationshipMatch.personOne'),
          personTwo: personTwo?.name || t('relationshipMatch.personTwo'),
          risk: firstContradiction || cautions[0] || t('relationshipMatch.defaultRiskPrompt'),
        }),
      },
    });
  };

  const openMarriageAnalysis = async () => {
    if (marriageCost > 0 && credits < marriageCost) {
      navigation.navigate('Credits');
      return;
    }
    if (personOne) {
      await storage.setBirthDetails(personOne);
    }
    navigation.navigate('AnalysisDetail', {
      analysisType: 'marriage',
      title: t('relationshipMatch.myMarriageAnalysis'),
      cost: marriageCost,
      originalCost: pricingOriginal.marriage,
    });
  };

  const renderSelectorCard = (label, profile, target, icon, genderFilter) => (
    <TouchableOpacity
      activeOpacity={0.85}
      onPress={() => navigation.navigate('SelectNative', {
        returnTo: 'RelationshipMatch',
        selectorTarget: target,
        nativeGenderFilter: genderFilter,
      })}
      style={[
        styles.selectorCard,
        {
          backgroundColor: colors.cardBackground,
          borderColor: colors.cardBorder,
        },
        androidLightCardFixStyle,
      ]}
    >
      <View style={styles.selectorHeader}>
        <View style={styles.selectorHeaderLeft}>
          <View style={[styles.selectorIconWrap, { backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : colors.surface }]}>
            <Ionicons name={icon} size={18} color={colors.primary} />
          </View>
          <View style={styles.selectorHeaderText}>
            <Text style={[styles.selectorLabel, { color: colors.textSecondary }]}>{label}</Text>
            <Text style={[styles.selectorName, { color: colors.text }]}>
              {profile?.name || t('relationshipMatch.selectProfile')}
            </Text>
          </View>
        </View>
        <Ionicons name="chevron-forward" size={18} color={colors.textTertiary} />
      </View>
      <Text style={[styles.selectorMeta, { color: colors.textSecondary }]}>
        {summarizeProfile(profile, t)}
      </Text>
    </TouchableOpacity>
  );

  const renderFactorList = (items, tone) => (
    <View style={styles.factorList}>
      {items.map((item, index) => (
        <View
          key={`${tone}_${index}`}
          style={[
            styles.factorRow,
            {
              backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : colors.surface,
              borderColor: tone === 'positive' ? 'rgba(34,197,94,0.28)' : 'rgba(245,158,11,0.28)',
            },
          ]}
        >
          <Ionicons
            name={tone === 'positive' ? 'sparkles' : 'alert-circle'}
            size={16}
            color={tone === 'positive' ? colors.success : colors.warning}
          />
          <Text style={[styles.factorText, { color: colors.text }]}>{cleanReportText(item)}</Text>
        </View>
      ))}
    </View>
  );

  const renderEvidenceRows = (items, emptyText) => (
    items?.length ? (
      <View style={styles.factorList}>
        {items.map((item, index) => (
          <View
            key={`${item.code || item.summary}_${index}`}
            style={[
              styles.evidenceCard,
              {
                backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : colors.surface,
                borderColor:
                  item.polarity === 'supportive'
                    ? 'rgba(34,197,94,0.24)'
                    : item.polarity === 'challenging'
                    ? 'rgba(239,68,68,0.22)'
                    : 'rgba(148,163,184,0.22)',
              },
            ]}
          >
            <View style={styles.evidenceHeader}>
              <Text style={[styles.evidenceCategory, { color: colors.primary }]}>
                {titleCase(item.category)}
              </Text>
              <Text style={[styles.evidenceWeight, { color: colors.textTertiary }]}>
                {Math.round((item.weight || 0) * 100)}%
              </Text>
            </View>
            <Text style={[styles.evidenceSummary, { color: colors.text }]}>{cleanReportText(item.summary)}</Text>
          </View>
        ))}
      </View>
    ) : (
      <Text style={[styles.emptyBody, { color: colors.textSecondary }]}>{emptyText}</Text>
    )
  );

  const renderAshtakootaBreakdown = () => {
    const rows = ASHTAKOOTA_ORDER
      .map(([key, labelKey]) => {
        const item = ashtakootaKoots?.[key];
        if (!item) return null;
        return {
          key,
          label: t(labelKey),
          score: item.score,
          maxScore: item.max_score,
          description: item.description,
          interpretation: item.interpretation,
          exception: gunaMilan?.exceptions?.[key],
        };
      })
      .filter(Boolean);

    if (!rows.length) return null;

    return (
      <View
        style={[
          styles.sectionCard,
          {
            backgroundColor: colors.cardBackground,
            borderColor: colors.cardBorder,
          },
          androidLightCardFixStyle,
        ]}
      >
        <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('relationshipMatch.ashtakoota.title')}</Text>
        <Text style={[styles.sectionSubtitle, { color: colors.textSecondary }]}>
          {t('relationshipMatch.ashtakoota.subtitle', {
            raw: gunaMilan.total_score ?? '--',
            effective: gunaMilan.effective_total_score ?? gunaMilan.total_score ?? '--',
          })}
        </Text>
        <View style={styles.gunaList}>
          {rows.map((row) => {
            const score = Number(row.score || 0);
            const maxScore = Number(row.maxScore || 0);
            const pct = maxScore > 0 ? Math.max(0, Math.min(100, (score / maxScore) * 100)) : 0;
            const exceptionReasons = row.exception?.applies ? (row.exception.reasons || []) : [];
            const isWeak = maxScore > 0 && pct < 50;
            return (
              <TouchableOpacity
                key={row.key}
                activeOpacity={0.85}
                onPress={() => setExpandedGunaKey((current) => (current === row.key ? null : row.key))}
                style={[
                  styles.gunaRow,
                  {
                    backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : colors.surface,
                    borderColor: isWeak ? 'rgba(245,158,11,0.35)' : colors.cardBorder,
                  },
                ]}
              >
                <View style={styles.gunaRowHeader}>
                  <View style={styles.gunaTitleWrap}>
                    <Text style={[styles.gunaName, { color: colors.text }]}>{row.label}</Text>
                  </View>
                  <View style={styles.gunaScoreWrap}>
                    <Text style={[styles.gunaScore, { color: isWeak ? colors.warning : colors.text }]}>
                      {score}/{maxScore}
                    </Text>
                    <Ionicons
                      name={expandedGunaKey === row.key ? 'chevron-up' : 'chevron-down'}
                      size={16}
                      color={colors.textTertiary}
                    />
                  </View>
                </View>
                <View style={[styles.gunaBarTrack, { backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.12)' }]}>
                  <View
                    style={[
                      styles.gunaBarFill,
                      {
                        width: `${pct}%`,
                        backgroundColor: isWeak ? colors.warning : colors.success,
                      },
                    ]}
                  />
                </View>
                {expandedGunaKey === row.key ? (
                  <View style={styles.gunaExpandedContent}>
                    {row.description ? (
                      <Text style={[styles.gunaDescription, { color: colors.textSecondary }]}>
                        {cleanReportText(row.description)}
                      </Text>
                    ) : null}
                    {row.interpretation ? (
                      <View style={styles.gunaInterpretationBlock}>
                        {cleanReportText(row.interpretation)
                          .split('\n')
                          .filter((line) => line.trim())
                          .map((line, lineIndex) => {
                            const isHeading = lineIndex === 0 || line.endsWith('measures') || line.startsWith('How to read');
                            return (
                              <Text
                                key={`${row.key}_line_${lineIndex}`}
                                style={[
                                  isHeading ? styles.gunaInterpretationHeading : styles.gunaInterpretationText,
                                  { color: isHeading ? colors.primary : colors.textSecondary },
                                ]}
                              >
                                {line}
                              </Text>
                            );
                          })}
                      </View>
                    ) : null}
                    {exceptionReasons.length ? (
                      <Text style={[styles.gunaException, { color: colors.success }]}>
                        {exceptionReasons.map(cleanReportText).join(' ')}
                      </Text>
                    ) : null}
                  </View>
                ) : null}
              </TouchableOpacity>
            );
          })}
        </View>
      </View>
    );
  };

  const renderBandPill = (band) => {
    const tone = bandTone(band);
    const textColor =
      tone === 'supportive' ? colors.success :
      tone === 'challenging' ? colors.error :
      colors.warning;
    return (
      <View
        style={[
          styles.bandPill,
          {
            backgroundColor:
              tone === 'supportive'
                ? 'rgba(34,197,94,0.16)'
                : tone === 'challenging'
                ? 'rgba(239,68,68,0.16)'
                : 'rgba(245,158,11,0.16)',
          },
        ]}
      >
        <Text style={[styles.bandPillText, { color: textColor }]}>{band || t('relationshipMatch.notAvailable')}</Text>
      </View>
    );
  };

  const renderMarriageSupportCard = (label, profile, seventh, navamsa) => {
    const d9NavamsaScore = combineScores(seventh?.d9_strength?.score, navamsa?.score);
    return (
      <View
        key={label}
        style={[
          styles.personCard,
          {
            backgroundColor: colors.cardBackground,
            borderColor: colors.cardBorder,
          },
          androidLightCardFixStyle,
        ]}
      >
        <View style={styles.personCardHeader}>
          <View>
            <Text style={[styles.personCardTitle, { color: colors.text }]}>{label}</Text>
            <Text style={[styles.personCardMeta, { color: colors.textSecondary }]}>
              {profile?.ascendant_sign_name || t('relationshipMatch.notAvailable')} ascendant
            </Text>
          </View>
          {renderBandPill(navamsa?.band || seventh?.d1_strength?.band)}
        </View>

        <View style={styles.personMetricRow}>
          <View style={styles.personMetric}>
            <Text style={[styles.personMetricValue, { color: colors.text }]}>{scoreText(seventh?.d1_strength?.score)}</Text>
            <Text style={[styles.personMetricLabel, { color: colors.textSecondary }]}>{t('relationshipMatch.d1Marriage')}</Text>
          </View>
          <View style={styles.personMetric}>
            <Text style={[styles.personMetricValue, { color: colors.text }]}>{scoreText(d9NavamsaScore)}</Text>
            <Text style={[styles.personMetricLabel, { color: colors.textSecondary }]}>{t('relationshipMatch.d9Marriage')}</Text>
          </View>
        </View>

        <Text style={[styles.personNarrative, { color: colors.textSecondary }]}>
          {t('relationshipMatch.rootFruit', { value: titleCase(navamsa?.root_vs_fruit || 'consistent') })}
        </Text>

        {renderFactorList((navamsa?.supportive_factors || []).slice(0, 2), 'positive')}
        {renderFactorList((navamsa?.challenging_factors || []).slice(0, 2), 'warning')}
      </View>
    );
  };

  const renderTimingCard = (row) => {
    const current = row.timing?.current_window || {};
    const best = row.timing?.best_window || {};
    return (
      <View
        key={row.key}
        style={[
          styles.personCard,
          {
            backgroundColor: colors.cardBackground,
            borderColor: colors.cardBorder,
          },
          androidLightCardFixStyle,
        ]}
      >
        <View style={styles.personCardHeader}>
          <View>
            <Text style={[styles.personCardTitle, { color: colors.text }]}>{row.label}</Text>
            <Text style={[styles.personCardMeta, { color: colors.textSecondary }]}>
              {t('relationshipMatch.currentClimateLabel', { value: getCurrentClimateLabel(current?.climate, t) })}
            </Text>
          </View>
          {renderBandPill(getCurrentClimateLabel(current?.climate, t))}
        </View>
        <View style={styles.personMetricRow}>
          <View style={styles.personMetric}>
            <Text style={[styles.personMetricValue, { color: colors.text }]}>{scoreText(current?.score)}</Text>
            <Text style={[styles.personMetricLabel, { color: colors.textSecondary }]}>{t('relationshipMatch.currentWindowScore')}</Text>
          </View>
          <View style={styles.personMetric}>
            <Text style={[styles.personMetricValue, { color: colors.text }]}>{scoreText(best?.score)}</Text>
            <Text style={[styles.personMetricLabel, { color: colors.textSecondary }]}>{t('relationshipMatch.bestWindowScore')}</Text>
          </View>
        </View>
        {current?.supports?.length ? renderFactorList(current.supports.slice(0, 2), 'positive') : null}
        {current?.risks?.length ? renderFactorList(current.risks.slice(0, 2), 'warning') : null}
      </View>
    );
  };

  const renderPremiumSection = (section, index) => (
    <View
      key={`${section.key || section.title}_${index}`}
      style={[
        styles.premiumReportSection,
        {
          backgroundColor: colors.cardBackground,
          borderColor: colors.cardBorder,
        },
        androidLightCardFixStyle,
      ]}
    >
      <Text style={[styles.premiumSectionTitle, { color: colors.text }]}>{cleanReportText(section.title)}</Text>
      {section.static_summary ? (
        <Text style={[styles.premiumSectionStatic, { color: colors.textSecondary }]}>{cleanReportText(section.static_summary)}</Text>
      ) : null}
      {section.ai_interpretation ? (
        <Text style={[styles.premiumSectionBody, { color: colors.text }]}>{cleanReportText(section.ai_interpretation)}</Text>
      ) : null}
      {section.practical_meaning ? (
        <View style={styles.premiumSubBlock}>
          <Text style={[styles.premiumSubLabel, { color: colors.primary }]}>{t('relationshipMatch.practicalMeaning')}</Text>
          <Text style={[styles.premiumSubText, { color: colors.textSecondary }]}>{cleanReportText(section.practical_meaning)}</Text>
        </View>
      ) : null}
      {section.decision_guidance ? (
        <View style={styles.premiumSubBlock}>
          <Text style={[styles.premiumSubLabel, { color: colors.primary }]}>{t('relationshipMatch.decisionGuidance')}</Text>
          <Text style={[styles.premiumSubText, { color: colors.textSecondary }]}>{cleanReportText(section.decision_guidance)}</Text>
        </View>
      ) : null}
      {section.facts?.length ? renderFactorList(section.facts.slice(0, 5), 'positive') : null}
    </View>
  );

  const resetToSelection = () => {
    setResult(null);
    setPremiumReport(null);
    setExpandedDetailKey(null);
    setExpandedGunaKey(null);
  };

  const renderSelectionStep = () => (
    <>
      <View
        style={[
          styles.heroCard,
          {
            backgroundColor: colors.cardBackground,
            borderColor: colors.cardBorder,
          },
          androidLightCardFixStyle,
        ]}
      >
        <Text style={[styles.heroEyebrow, { color: colors.primary }]}>{t('relationshipMatch.freeBadge')}</Text>
        <Text style={[styles.heroTitle, { color: colors.text }]}>{t('relationshipMatch.selectionTitle')}</Text>
        <Text style={[styles.heroBody, { color: colors.textSecondary }]}>
          {t('relationshipMatch.selectionBody')}
        </Text>
      </View>

      {renderSelectorCard(t('relationshipMatch.boyChart'), personOne, 'personOne', 'person', 'male')}
      {renderSelectorCard(t('relationshipMatch.girlChart'), personTwo, 'personTwo', 'person-add', 'female')}

      {!savedProfiles.length && !loadingBootstrap ? (
        <View
          style={[
            styles.sectionCard,
            {
              backgroundColor: colors.cardBackground,
              borderColor: colors.cardBorder,
            },
            androidLightCardFixStyle,
          ]}
        >
          <Text style={[styles.emptyTitle, { color: colors.text }]}>{t('relationshipMatch.noProfilesTitle')}</Text>
          <Text style={[styles.emptyBody, { color: colors.textSecondary }]}>{t('relationshipMatch.noProfilesBody')}</Text>
          <TouchableOpacity
            onPress={() => navigation.navigate('SelectNative', {
              returnTo: 'RelationshipMatch',
              selectorTarget: 'personOne',
              nativeGenderFilter: 'male',
            })}
            style={[styles.primaryButton, { backgroundColor: colors.primary }]}
          >
            <Text style={styles.primaryButtonText}>{t('relationshipMatch.selectSavedChart')}</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      <TouchableOpacity
        disabled={compareDisabled}
        activeOpacity={0.9}
        onPress={handleAnalyze}
        style={[
          styles.compareButton,
          { opacity: compareDisabled || compareMissingCharts ? 0.6 : 1 },
        ]}
      >
        <LinearGradient colors={[colors.primary, colors.secondary]} style={styles.compareGradient}>
          {loadingResult ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Ionicons name="git-compare" size={18} color="#fff" />
              <Text style={styles.compareText}>{t('relationshipMatch.compareButton')}</Text>
              <View style={styles.comparePill}>
                <Text style={styles.comparePillText}>{t('relationshipMatch.freeCompare')}</Text>
              </View>
            </>
          )}
        </LinearGradient>
      </TouchableOpacity>

      <Text style={[styles.helperNote, { color: colors.textTertiary }]}>
        {t('relationshipMatch.helperNote')}
      </Text>
    </>
  );

  const renderPremiumReportCard = () => (
    <View
      style={[
        styles.sectionCard,
        {
          backgroundColor: isDark ? 'rgba(249,115,22,0.08)' : '#fff4eb',
          borderColor: isDark ? 'rgba(249,115,22,0.25)' : 'rgba(234,88,12,0.18)',
        },
        androidLightCardFixStyle,
      ]}
    >
      <View style={styles.premiumHeader}>
        <View style={[styles.lockWrap, { backgroundColor: colors.primary }]}>
          <Ionicons name="sparkles" size={16} color="#fff" />
        </View>
        <View style={styles.premiumHeaderText}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('relationshipMatch.premiumReportTitle')}</Text>
          <Text style={[styles.sectionSubtitle, { color: colors.textSecondary }]}>
            {cleanReportText(premiumReport.headline || premiumReport.compatibility_verdict || t('relationshipMatch.premiumTitle'))}
          </Text>
        </View>
      </View>

      {premiumReport.compatibility_verdict ? (
        <Text style={[styles.premiumReportVerdict, { color: colors.text }]}>
          {cleanReportText(premiumReport.compatibility_verdict)}
        </Text>
      ) : null}

      {(premiumReport.sections || []).map(renderPremiumSection)}

      {premiumReport.final_summary ? (
        <View style={styles.premiumClosingBlock}>
          <Text style={[styles.premiumSubLabel, { color: colors.primary }]}>{t('relationshipMatch.finalSummary')}</Text>
          <Text style={[styles.premiumSubText, { color: colors.textSecondary }]}>{cleanReportText(premiumReport.final_summary)}</Text>
        </View>
      ) : null}

      {(premiumReport.priority_actions || []).length ? (
        <View style={styles.premiumClosingBlock}>
          <Text style={[styles.premiumSubLabel, { color: colors.primary }]}>{t('relationshipMatch.priorityActions')}</Text>
          {renderFactorList(premiumReport.priority_actions.slice(0, 5), 'positive')}
        </View>
      ) : null}

      <TouchableOpacity onPress={openPremiumChat} style={[styles.primaryButton, { backgroundColor: colors.primary }]}>
        <Text style={styles.primaryButtonText}>
          {t('relationshipMatch.askAiCta', { credits: premiumChatCost })}
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        onPress={() => unlockPremiumReport(true)}
        style={[
          styles.secondaryButton,
          {
            borderColor: colors.cardBorder,
            backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : '#fff',
          },
        ]}
        disabled={loadingPremiumReport}
      >
        <Text style={[styles.secondaryButtonText, { color: colors.text }]}>
          {loadingPremiumReport
            ? t('relationshipMatch.generatingPremium')
            : t('relationshipMatch.regeneratePremiumReport', { credits: premiumReportCost })}
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderPremiumUpsell = () => {
    if (premiumReport) {
      return renderPremiumReportCard();
    }

    return (
      <View
        style={[
          styles.premiumCard,
          {
            backgroundColor: isDark ? 'rgba(249,115,22,0.08)' : '#fff4eb',
            borderColor: isDark ? 'rgba(249,115,22,0.25)' : 'rgba(234,88,12,0.18)',
          },
          androidLightCardFixStyle,
        ]}
      >
        <View style={styles.premiumHeader}>
          <View style={[styles.lockWrap, { backgroundColor: colors.primary }]}>
            <Ionicons name="lock-closed" size={16} color="#fff" />
          </View>
          <View style={styles.premiumHeaderText}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('relationshipMatch.premiumTitle')}</Text>
            <Text style={[styles.sectionSubtitle, { color: colors.textSecondary }]}>
              {t('relationshipMatch.premiumTease')}
            </Text>
          </View>
        </View>

        <View style={styles.lockedBullets}>
          {[
            t('relationshipMatch.locked.one'),
            t('relationshipMatch.locked.two'),
            t('relationshipMatch.locked.three'),
            t('relationshipMatch.locked.four'),
          ].map((line) => (
            <View key={line} style={styles.lockedRow}>
              <Ionicons name="ellipse" size={8} color={colors.primary} />
              <Text style={[styles.lockedText, { color: colors.textSecondary }]}>{line}</Text>
            </View>
          ))}
        </View>

        <TouchableOpacity
          onPress={() => unlockPremiumReport(false)}
          style={[styles.primaryButton, { backgroundColor: colors.primary }]}
          disabled={loadingPremiumReport}
        >
          <Text style={styles.primaryButtonText}>
            {loadingPremiumReport
              ? t('relationshipMatch.generatingPremium')
              : t('relationshipMatch.unlockPremiumReport', { credits: premiumReportCost })}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={openPremiumChat}
          style={[
            styles.secondaryButton,
            {
              borderColor: colors.cardBorder,
              backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : '#fff',
            },
          ]}
        >
          <Text style={[styles.secondaryButtonText, { color: colors.text }]}>
            {t('relationshipMatch.askAiCta', { credits: premiumChatCost })}
          </Text>
        </TouchableOpacity>
      </View>
    );
  };

  const renderDetailAccordion = (key, title, subtitle, children) => {
    const expanded = expandedDetailKey === key;
    return (
      <View
        style={[
          styles.sectionCard,
          {
            backgroundColor: colors.cardBackground,
            borderColor: colors.cardBorder,
          },
          androidLightCardFixStyle,
        ]}
      >
        <TouchableOpacity
          activeOpacity={0.85}
          onPress={() => setExpandedDetailKey((current) => (current === key ? null : key))}
          style={styles.detailAccordionHeader}
        >
          <View style={styles.detailAccordionText}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{title}</Text>
            {subtitle ? (
              <Text style={[styles.sectionSubtitle, { color: colors.textSecondary }]}>{subtitle}</Text>
            ) : null}
          </View>
          <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={20} color={colors.textSecondary} />
        </TouchableOpacity>
        {expanded ? <View style={styles.detailAccordionBody}>{children}</View> : null}
      </View>
    );
  };

  const renderOptionalDetails = () => (
    <>
      {renderDetailAccordion(
        'guna',
        t('relationshipMatch.detailGunaTitle'),
        t('relationshipMatch.detailGunaSubtitle'),
        renderAshtakootaBreakdown()
      )}

      {renderDetailAccordion(
        'chart',
        t('relationshipMatch.detailChartTitle'),
        t('relationshipMatch.detailChartSubtitle'),
        <>
          <View style={styles.metricsRow}>
            {[
              {
                label: t('relationshipMatch.metrics.guna'),
                value: effectiveScore != null ? `${effectiveScore}/36` : '--',
              },
              {
                label: t('relationshipMatch.metrics.manglik'),
                value: pairManglikStatus || '--',
              },
              {
                label: t('relationshipMatch.metrics.timing'),
                value: scoreText(result?.timing_overlay?.shared?.joint_readiness_score),
              },
              {
                label: t('relationshipMatch.metrics.window'),
                value: getCurrentClimateLabel(currentClimate, t),
              },
            ].map((metric) => (
              <View
                key={metric.label}
                style={[
                  styles.metricCard,
                  {
                    backgroundColor: isDark ? 'rgba(255,255,255,0.04)' : colors.surface,
                    borderColor: colors.cardBorder,
                  },
                ]}
              >
                <Text style={[styles.metricValue, { color: colors.text }]}>{metric.value}</Text>
                <Text style={[styles.metricLabel, { color: colors.textSecondary }]}>{metric.label}</Text>
              </View>
            ))}
          </View>

          <View style={styles.subsectionSpacer}>
            <Text style={[styles.subsectionTitle, { color: colors.text }]}>{t('relationshipMatch.whyTitle')}</Text>
            <Text style={[styles.sectionSubtitle, { color: colors.textSecondary }]}>
              {t('relationshipMatch.whyBody')}
            </Text>
            {renderEvidenceRows(
              supportiveEvidence.slice(0, 3),
              t('relationshipMatch.noStrengthsYet')
            )}
            {challengingEvidence.length ? (
              <View style={styles.subsectionSpacer}>
                <Text style={[styles.subsectionTitle, { color: colors.text }]}>{t('relationshipMatch.watchoutsTitle')}</Text>
                {renderEvidenceRows(
                  challengingEvidence.slice(0, 3),
                  t('relationshipMatch.noRisksYet')
                )}
              </View>
            ) : null}
          </View>

          <View style={styles.subsectionSpacer}>
            <Text style={[styles.subsectionTitle, { color: colors.text }]}>{t('relationshipMatch.crossChartTitle')}</Text>
            <Text style={[styles.sectionSubtitle, { color: colors.textSecondary }]}>
              {t('relationshipMatch.crossChartBody', { band: crossChart?.band || t('relationshipMatch.notAvailable') })}
            </Text>
            <View style={styles.metricsRow}>
              {[
                { label: t('relationshipMatch.crossMetrics.moon'), value: scoreText(crossChart?.moon_element_match?.score) },
                { label: t('relationshipMatch.crossMetrics.venusMars'), value: scoreText(crossChart?.venus_to_mars?.score) },
                { label: t('relationshipMatch.crossMetrics.marsVenus'), value: scoreText(crossChart?.mars_to_venus?.score) },
                { label: t('relationshipMatch.crossMetrics.navamsaPair'), value: scoreText(crossChart?.navamsa_pair_support) },
              ].map((metric) => (
                <View
                  key={metric.label}
                  style={[
                    styles.metricCard,
                    {
                      backgroundColor: isDark ? 'rgba(255,255,255,0.04)' : colors.surface,
                      borderColor: colors.cardBorder,
                    },
                  ]}
                >
                  <Text style={[styles.metricValue, { color: colors.text }]}>{metric.value}</Text>
                  <Text style={[styles.metricLabel, { color: colors.textSecondary }]}>{metric.label}</Text>
                </View>
              ))}
            </View>
            {renderFactorList((crossChart?.positive_factors || []).slice(0, 2), 'positive')}
            {renderFactorList((crossChart?.caution_factors || []).slice(0, 2), 'warning')}
          </View>

          <View style={styles.subsectionSpacer}>
            <Text style={[styles.subsectionTitle, { color: colors.text }]}>{t('relationshipMatch.marriageSupportTitle')}</Text>
            <Text style={[styles.sectionSubtitle, { color: colors.textSecondary }]}>
              {t('relationshipMatch.marriageSupportBody')}
            </Text>
            {renderMarriageSupportCard(personOne?.name || t('relationshipMatch.personOne'), boyProfile, boySeventh, boyNavamsa)}
            {renderMarriageSupportCard(personTwo?.name || t('relationshipMatch.personTwo'), girlProfile, girlSeventh, girlNavamsa)}
          </View>

          <View style={styles.subsectionSpacer}>
            <Text style={[styles.subsectionTitle, { color: colors.text }]}>{t('relationshipMatch.timingDeepTitle')}</Text>
            <Text style={[styles.sectionSubtitle, { color: colors.textSecondary }]}>
              {t('relationshipMatch.timingDeepBody')}
            </Text>
            {personTimingRows.map(renderTimingCard)}
            {neutralEvidence.length ? (
              <View style={styles.subsectionSpacer}>
                <Text style={[styles.subsectionTitle, { color: colors.text }]}>{t('relationshipMatch.neutralEvidenceTitle')}</Text>
                {renderEvidenceRows(neutralEvidence.slice(0, 2), t('relationshipMatch.notAvailable'))}
              </View>
            ) : null}
          </View>
        </>
      )}
    </>
  );

  const renderFreeReportStep = () => (
    <>
      <View
        style={[
          styles.resultHero,
          {
            backgroundColor: colors.cardBackground,
            borderColor: colors.cardBorder,
          },
          androidLightCardFixStyle,
        ]}
      >
        <View style={styles.resultTopRow}>
          <View style={styles.scoreBlock}>
            <Text style={[styles.heroEyebrow, { color: colors.primary }]}>{t('relationshipMatch.freeReportLabel')}</Text>
            <Text style={[styles.resultVerdict, { color: colors.text }]}>
              {result?.recommendation?.recommendation || t('relationshipMatch.defaultVerdict')}
            </Text>
          </View>
          <View
            style={[
              styles.climateBadge,
              { backgroundColor: `${CLIMATE_COLORS[currentClimate] || '#f59e0b'}20` },
            ]}
          >
            <Text style={[styles.climateBadgeText, { color: CLIMATE_COLORS[currentClimate] || colors.warning }]}>
              {getCurrentClimateLabel(currentClimate, t)}
            </Text>
          </View>
        </View>
        <Text style={[styles.scoreValue, { color: colors.text }]}>
          {scoreText(overallPercentage)}
        </Text>
        <Text style={[styles.scoreLabel, { color: colors.textSecondary }]}>
          {t('relationshipMatch.compatibilityScore')}
        </Text>
        <Text style={[styles.resultBody, { color: colors.textSecondary }]}>
          {result?.recommendation?.timing_note || t('relationshipMatch.defaultTimingNote')}
        </Text>
        <TouchableOpacity
          onPress={resetToSelection}
          style={[
            styles.secondaryButton,
            {
              borderColor: colors.cardBorder,
              backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : colors.surface,
            },
          ]}
        >
          <Text style={[styles.secondaryButtonText, { color: colors.text }]}>
            {t('relationshipMatch.changeCharts')}
          </Text>
        </TouchableOpacity>
      </View>

      {renderPremiumUpsell()}

      <View
        style={[
          styles.sectionCard,
          {
            backgroundColor: colors.cardBackground,
            borderColor: colors.cardBorder,
          },
          androidLightCardFixStyle,
        ]}
      >
        <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('relationshipMatch.keyStrengths')}</Text>
        {positives.length ? renderFactorList(positives, 'positive') : (
          <Text style={[styles.emptyBody, { color: colors.textSecondary }]}>{t('relationshipMatch.noStrengthsYet')}</Text>
        )}
      </View>

      <View
        style={[
          styles.sectionCard,
          {
            backgroundColor: colors.cardBackground,
            borderColor: colors.cardBorder,
          },
          androidLightCardFixStyle,
        ]}
      >
        <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('relationshipMatch.keyRisks')}</Text>
        {cautions.length ? renderFactorList(cautions, 'warning') : (
          <Text style={[styles.emptyBody, { color: colors.textSecondary }]}>{t('relationshipMatch.noRisksYet')}</Text>
        )}
      </View>

      {firstFavorableWindow ? (
        <View
          style={[
            styles.windowCard,
            {
              backgroundColor: colors.cardBackground,
              borderColor: colors.cardBorder,
            },
            androidLightCardFixStyle,
          ]}
        >
          <View style={styles.windowHeader}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('relationshipMatch.bestWindow')}</Text>
            <View style={[styles.windowScorePill, { backgroundColor: 'rgba(34,197,94,0.16)' }]}>
              <Text style={[styles.windowScoreText, { color: colors.success }]}>{scoreText(firstFavorableWindow.score)}</Text>
            </View>
          </View>
          <Text style={[styles.windowDate, { color: colors.text }]}>{formatWindowRange(firstFavorableWindow)}</Text>
          <Text style={[styles.windowMeta, { color: colors.textSecondary }]}>
            {t('relationshipMatch.bestWindowBody')}
          </Text>
        </View>
      ) : null}

      {renderOptionalDetails()}
    </>
  );

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={isDark ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd] : [colors.background, colors.backgroundSecondary, colors.backgroundTertiary]}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity
              onPress={() => navigation.goBack()}
              style={[styles.headerButton, { backgroundColor: isDark ? 'rgba(255,255,255,0.16)' : colors.surface }]}
            >
              <Ionicons name="arrow-back" size={22} color={colors.text} />
            </TouchableOpacity>
            <View style={styles.headerCenter}>
              <Text style={[styles.headerTitle, { color: colors.text }]}>{t('relationshipMatch.title')}</Text>
              <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>{t('relationshipMatch.subtitle')}</Text>
            </View>
            {premiumReport ? (
              <TouchableOpacity
                onPress={downloadPremiumReport}
                style={[styles.headerButton, { backgroundColor: isDark ? 'rgba(255,255,255,0.16)' : colors.surface }]}
                disabled={isExportingPdf}
                accessibilityRole="button"
                accessibilityLabel={t('relationshipMatch.downloadFullReport')}
              >
                {isExportingPdf ? (
                  <ActivityIndicator size="small" color={colors.text} />
                ) : (
                  <Ionicons name="download-outline" size={22} color={colors.text} />
                )}
              </TouchableOpacity>
            ) : (
              <View style={styles.headerButton} />
            )}
          </View>

          <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
            {result ? renderFreeReportStep() : renderSelectionStep()}
          </ScrollView>
        </SafeAreaView>
      </LinearGradient>

    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 18,
    paddingTop: 8,
    paddingBottom: 14,
  },
  headerButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
    paddingHorizontal: 12,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    textAlign: 'center',
  },
  headerSubtitle: {
    fontSize: 12,
    marginTop: 2,
    textAlign: 'center',
  },
  content: {
    paddingHorizontal: 18,
    paddingBottom: 32,
    gap: 14,
  },
  heroCard: {
    borderRadius: 24,
    borderWidth: 1,
    padding: 20,
    marginBottom: 4,
  },
  heroTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  heroEyebrow: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
  },
  heroTitle: {
    fontSize: 24,
    fontWeight: '800',
    marginTop: 8,
  },
  heroBody: {
    fontSize: 14,
    lineHeight: 22,
    marginTop: 12,
  },
  freeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
    alignSelf: 'flex-start',
  },
  freeBadgeText: {
    fontSize: 12,
    fontWeight: '700',
  },
  ruleRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 16,
    alignItems: 'center',
  },
  ruleText: {
    flex: 1,
    fontSize: 12,
    lineHeight: 18,
  },
  selectorCard: {
    borderRadius: 20,
    borderWidth: 1,
    padding: 16,
  },
  selectorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  selectorHeaderLeft: {
    flexDirection: 'row',
    flex: 1,
    gap: 12,
    alignItems: 'center',
  },
  selectorIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  selectorHeaderText: {
    flex: 1,
  },
  selectorLabel: {
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  selectorName: {
    fontSize: 16,
    fontWeight: '700',
    marginTop: 4,
  },
  selectorMeta: {
    marginTop: 10,
    fontSize: 13,
    lineHeight: 19,
  },
  sectionCard: {
    borderRadius: 20,
    borderWidth: 1,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '800',
  },
  sectionSubtitle: {
    fontSize: 13,
    lineHeight: 20,
    marginTop: 6,
  },
  compareButton: {
    borderRadius: 20,
    overflow: 'hidden',
    marginTop: 2,
  },
  compareGradient: {
    minHeight: 58,
    paddingHorizontal: 18,
    paddingVertical: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 10,
  },
  compareText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '800',
  },
  comparePill: {
    backgroundColor: 'rgba(255,255,255,0.18)',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  comparePillText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
  },
  helperNote: {
    textAlign: 'center',
    fontSize: 12,
    lineHeight: 18,
    marginTop: -2,
  },
  resultHero: {
    borderRadius: 24,
    borderWidth: 1,
    padding: 20,
    marginTop: 6,
  },
  resultTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 10,
  },
  scoreBlock: {
    flex: 1,
  },
  scoreValue: {
    fontSize: 34,
    fontWeight: '900',
  },
  scoreLabel: {
    fontSize: 13,
    fontWeight: '700',
    marginTop: 4,
  },
  climateBadge: {
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  climateBadgeText: {
    fontSize: 12,
    fontWeight: '800',
  },
  resultVerdict: {
    fontSize: 20,
    fontWeight: '800',
    marginTop: 16,
  },
  resultBody: {
    fontSize: 14,
    lineHeight: 22,
    marginTop: 8,
  },
  metricsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  metricCard: {
    width: '47.5%',
    borderRadius: 18,
    borderWidth: 1,
    padding: 14,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '800',
  },
  metricLabel: {
    fontSize: 12,
    marginTop: 6,
    lineHeight: 18,
  },
  detailAccordionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  detailAccordionText: {
    flex: 1,
  },
  detailAccordionBody: {
    marginTop: 14,
  },
  gunaList: {
    marginTop: 14,
    gap: 10,
  },
  gunaRow: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 12,
  },
  gunaRowHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
    alignItems: 'flex-start',
  },
  gunaTitleWrap: {
    flex: 1,
  },
  gunaName: {
    fontSize: 14,
    fontWeight: '800',
  },
  gunaDescription: {
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4,
  },
  gunaScore: {
    fontSize: 14,
    fontWeight: '900',
  },
  gunaScoreWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  gunaBarTrack: {
    height: 6,
    borderRadius: 999,
    overflow: 'hidden',
    marginTop: 10,
  },
  gunaBarFill: {
    height: '100%',
    borderRadius: 999,
  },
  gunaExpandedContent: {
    marginTop: 12,
  },
  gunaInterpretationBlock: {
    marginTop: 10,
    gap: 6,
  },
  gunaInterpretationHeading: {
    fontSize: 12,
    lineHeight: 18,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  gunaInterpretationText: {
    fontSize: 13,
    lineHeight: 20,
  },
  gunaException: {
    fontSize: 12,
    lineHeight: 18,
    marginTop: 8,
    fontWeight: '700',
  },
  factorList: {
    marginTop: 12,
    gap: 10,
  },
  factorRow: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  factorText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 20,
  },
  evidenceCard: {
    borderWidth: 1,
    borderRadius: 16,
    padding: 12,
  },
  evidenceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  evidenceCategory: {
    fontSize: 11,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  evidenceWeight: {
    fontSize: 11,
    fontWeight: '700',
  },
  evidenceSummary: {
    fontSize: 13,
    lineHeight: 20,
  },
  subsectionSpacer: {
    marginTop: 18,
  },
  subsectionTitle: {
    fontSize: 15,
    fontWeight: '800',
    marginBottom: 10,
  },
  bandPill: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  bandPillText: {
    fontSize: 11,
    fontWeight: '800',
  },
  personCard: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 14,
    marginTop: 12,
  },
  personCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
    alignItems: 'flex-start',
  },
  personCardTitle: {
    fontSize: 16,
    fontWeight: '800',
  },
  personCardMeta: {
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4,
  },
  personMetricRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 14,
  },
  personMetric: {
    flex: 1,
  },
  personMetricValue: {
    fontSize: 18,
    fontWeight: '800',
  },
  personMetricLabel: {
    fontSize: 11,
    lineHeight: 16,
    marginTop: 4,
  },
  personNarrative: {
    marginTop: 12,
    fontSize: 13,
    lineHeight: 20,
  },
  windowCard: {
    borderRadius: 20,
    borderWidth: 1,
    padding: 16,
  },
  windowHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  windowScorePill: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  windowScoreText: {
    fontSize: 12,
    fontWeight: '800',
  },
  windowDate: {
    marginTop: 12,
    fontSize: 18,
    fontWeight: '800',
  },
  windowMeta: {
    marginTop: 8,
    fontSize: 13,
    lineHeight: 20,
  },
  premiumCard: {
    borderRadius: 22,
    borderWidth: 1,
    padding: 18,
  },
  premiumReportSection: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 14,
    marginTop: 12,
  },
  premiumSectionTitle: {
    fontSize: 16,
    fontWeight: '800',
  },
  premiumSectionStatic: {
    fontSize: 13,
    lineHeight: 20,
    marginTop: 6,
  },
  premiumSectionBody: {
    fontSize: 14,
    lineHeight: 22,
    marginTop: 10,
  },
  premiumHeader: {
    flexDirection: 'row',
    gap: 12,
  },
  lockWrap: {
    width: 34,
    height: 34,
    borderRadius: 17,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 2,
  },
  premiumHeaderText: {
    flex: 1,
  },
  premiumReportVerdict: {
    fontSize: 15,
    lineHeight: 23,
    marginTop: 14,
    fontWeight: '700',
  },
  premiumSubBlock: {
    marginTop: 12,
  },
  premiumSubLabel: {
    fontSize: 12,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
    marginBottom: 4,
  },
  premiumSubText: {
    fontSize: 13,
    lineHeight: 21,
  },
  premiumClosingBlock: {
    marginTop: 14,
  },
  lockedBullets: {
    marginTop: 14,
    gap: 8,
  },
  lockedRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  lockedText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 20,
  },
  primaryButton: {
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingVertical: 14,
    marginTop: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '800',
    textAlign: 'center',
  },
  secondaryButton: {
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingVertical: 14,
    marginTop: 10,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryButtonText: {
    fontSize: 14,
    fontWeight: '700',
    textAlign: 'center',
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '800',
  },
  emptyBody: {
    fontSize: 14,
    lineHeight: 22,
    marginTop: 8,
  },
});
