import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Share,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTranslation } from 'react-i18next';

import { storage } from '../../services/storage';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import { useCredits } from '../../credits/CreditContext';
import { useAuthGate } from '../../auth/AuthGateContext';
import { pricingAPI } from '../../services/api';
import CreditModal from '../CreditModal';
import {
  exportHtmlAsPdf,
  sharePDFOnWhatsApp,
  PDF_PRINT_STYLES,
} from '../../utils/pdfGenerator';

const POLL_MS = 3000;
const MAX_POLLS = 120;
const DATE_LOCALES = {
  english: 'en-IN', hindi: 'hi-IN', es: 'es-ES', french: 'fr-FR', german: 'de-DE',
  russian: 'ru-RU', chinese: 'zh-CN', mandarin: 'zh-CN', tamil: 'ta-IN',
  telugu: 'te-IN', gujarati: 'gu-IN', marathi: 'mr-IN',
};

const DOMAIN_HOUSES = {
  vitality_and_personality: 1,
  wealth_family_speech: 2,
  courage_siblings_skills: 3,
  home_comfort_mother: 4,
  children_creativity_speculation: 5,
  health_service_obstacles: 6,
  partnerships_marriage: 7,
  longevity_shared_resources: 8,
  fortune_dharma_father: 9,
  career_reputation: 10,
  gains_network_aspirations: 11,
  expenses_moksha_rest: 12,
};

function normalizeDate(value) {
  if (!value || typeof value !== 'string') return value;
  if (value.includes('T')) return value.split('T')[0];
  if (value.length === 10 && value[4] === '-' && value[7] === '-') return value;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function birthPayload(birth) {
  let time = birth?.time;
  if (typeof time === 'string' && time.includes(':')) {
    const parts = time.split(':');
    time = `${String(parseInt(parts[0], 10)).padStart(2, '0')}:${String(parseInt(parts[1], 10)).padStart(2, '0')}`;
  }
  return {
    name: birth?.name || 'User',
    date: normalizeDate(birth?.date),
    time,
    latitude: Number(birth?.latitude),
    longitude: Number(birth?.longitude),
    place: birth?.place || '',
    gender: birth?.gender || '',
  };
}

function displayStudyDate(value, language, savedLabel) {
  if (!value) return savedLabel;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return savedLabel;
  return date.toLocaleDateString(DATE_LOCALES[language] || 'en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

async function requestStudy(birth, forceRegenerate = false, translate = null, exactBirth = false) {
  const tr = (key, fallback) => translate ? translate(key, fallback) : fallback;
  const token = await AsyncStorage.getItem('authToken');
  const birthData = exactBirth
    ? {
        name: birth?.name || 'User',
        date: birth?.date,
        time: birth?.time,
        latitude: Number(birth?.latitude),
        longitude: Number(birth?.longitude),
        place: birth?.place || '',
        gender: birth?.gender || '',
      }
    : birthPayload(birth);
  const response = await fetch(`${API_BASE_URL}${getEndpoint('/ashtakavarga/life-predictions')}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      birth_data: birthData,
      cache_probe: !forceRegenerate,
      force_regenerate: forceRegenerate,
    }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof body?.detail === 'string' ? body.detail : body?.error || `Request failed (${response.status})`;
    throw new Error(message);
  }
  if (!body.job_id) return body;

  for (let attempt = 0; attempt < MAX_POLLS; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, POLL_MS));
    const poll = await fetch(`${API_BASE_URL}${getEndpoint(`/ashtakavarga/life-predictions/status/${body.job_id}`)}`, {
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    });
    const pollBody = await poll.json().catch(() => ({}));
    if (!poll.ok) throw new Error(pollBody?.detail || pollBody?.error || `Request failed (${poll.status})`);
    if (pollBody.status === 'completed' && pollBody.result) return pollBody.result;
    if (pollBody.status === 'failed') throw new Error(pollBody.error || tr('ashtakavargaStudy.errors.generation', 'Study generation failed'));
  }
  throw new Error(tr('ashtakavargaStudy.errors.processing', 'The study is still processing. Please open it again shortly.'));
}

function textLines(value) {
  if (!Array.isArray(value)) return [];
  return value.filter((line) => line != null && String(line).trim()).map(String);
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(/\n/g, '<br>');
}

function pdfSection(title, body) {
  if (!body) return '';
  return `<section class="section"><h2>${escapeHtml(title)}</h2>${body}</section>`;
}

function pdfParagraph(value, className = '') {
  if (value == null || String(value).trim() === '') return '';
  return `<p${className ? ` class="${className}"` : ''}>${escapeHtml(value)}</p>`;
}

function pdfList(items) {
  const lines = textLines(items);
  if (!lines.length) return '';
  return `<ul>${lines.map((line) => `<li>${escapeHtml(line)}</li>`).join('')}</ul>`;
}

function StudySection({ id, title, children, colors, registerSection }) {
  if (!children) return null;
  return (
    <View
      onLayout={(event) => registerSection(id, event.nativeEvent.layout.y)}
      style={[styles.sectionCard, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}
    >
      <Text style={[styles.sectionTitle, { color: colors.text }]}>{title}</Text>
      {children}
    </View>
  );
}

function Paragraph({ children, colors, muted = false }) {
  if (children == null || String(children).trim() === '') return null;
  return <Text style={[styles.paragraph, { color: muted ? colors.textSecondary : colors.text }]}>{String(children)}</Text>;
}

function BulletList({ items, colors }) {
  return textLines(items).map((line, index) => (
    <View key={`${line}-${index}`} style={styles.bulletRow}>
      <View style={[styles.bulletDot, { backgroundColor: colors.accent }]} />
      <Text style={[styles.bulletText, { color: colors.textSecondary }]}>{line}</Text>
    </View>
  ));
}

export default function AshtakvargaStudyScreen({ navigation, route }) {
  const { t, i18n } = useTranslation();
  const { theme, colors } = useTheme();
  const { credits, fetchBalance } = useCredits();
  const { requireAuthForPaid } = useAuthGate();
  const scrollRef = useRef(null);
  const sectionOffsets = useRef({});
  const [birth, setBirth] = useState(route.params?.birthData || null);
  const [study, setStudy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [refreshModalVisible, setRefreshModalVisible] = useState(false);
  const [creditCost, setCreditCost] = useState(15);
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const studyDate = displayStudyDate(
    study?.generated_at,
    i18n.resolvedLanguage || i18n.language,
    t('ashtakavargaStudy.savedStudy'),
  );

  const loadSavedStudy = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const selectedBirth = birth || await storage.getBirthDetails();
      if (!selectedBirth) throw new Error(t('ashtakavargaStudy.errors.selectNative'));
      setBirth(selectedBirth);
      const result = await requestStudy(
        selectedBirth,
        false,
        (key, fallback) => t(key, { defaultValue: fallback }),
        route.params?.exactBirth === true,
      );
      if (!result?.cached || !result?.predictions) {
        throw new Error(t('ashtakavargaStudy.errors.noSaved'));
      }
      setStudy(result);
    } catch (loadError) {
      setError(loadError?.message || t('ashtakavargaStudy.errors.load'));
    } finally {
      setLoading(false);
    }
  }, [birth, t]);

  useEffect(() => {
    loadSavedStudy();
  }, []);

  useEffect(() => {
    let cancelled = false;
    pricingAPI.getPricing().then((response) => {
      const nextCost = response?.data?.pricing?.ashtakavarga;
      if (!cancelled && nextCost != null && !Number.isNaN(Number(nextCost))) {
        setCreditCost(Math.max(1, Number(nextCost)));
      }
    }).catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const pred = study?.predictions || {};
  const sav = pred.sav_strength_analysis || {};
  const life = pred.life_predictions || {};
  const transit = pred.transit_predictions || {};
  const dasha = pred.dasha_analysis || {};
  const insights = pred.life_domain_insights || {};
  const domainLabel = (key) => {
    const house = DOMAIN_HOUSES[key];
    return house
      ? t(`premiumUi.home.houseAreas.${house}`, { defaultValue: key.replace(/_/g, ' ') })
      : key.replace(/_/g, ' ');
  };

  const visibleSections = useMemo(() => [
    pred.current_life_phase && { id: 'phase', label: t('ashtakavargaStudy.nav.now') },
    (sav.overall_pattern || sav.strong_areas?.length || sav.challenging_areas?.length) && { id: 'strengths', label: t('ashtakavargaStudy.nav.strengths') },
    Object.keys(insights).length && { id: 'houses', label: t('ashtakavargaStudy.nav.houses') },
    pred.timing_highlights?.length && { id: 'timing', label: t('ashtakavargaStudy.nav.timing') },
    Object.keys(transit).length && { id: 'transits', label: t('ashtakavargaStudy.nav.transits') },
    Object.keys(dasha).length && { id: 'dasha', label: t('ashtakavargaStudy.nav.dasha') },
    (life.next_6_months || life.next_year || life.major_themes?.length) && { id: 'outlook', label: t('ashtakavargaStudy.nav.outlook') },
    pred.remedial_measures?.length && { id: 'remedies', label: t('ashtakavargaStudy.nav.remedies') },
  ].filter(Boolean), [pred, sav, insights, transit, dasha, life, t]);

  const registerSection = useCallback((id, y) => {
    sectionOffsets.current[id] = y;
  }, []);

  const jumpTo = (id) => {
    const y = sectionOffsets.current[id];
    if (typeof y === 'number') scrollRef.current?.scrollTo({ y: Math.max(0, y - 16), animated: true });
  };

  const shareStudy = async () => {
    const lines = [
      `${t('ashtakavargaStudy.title')}${birth?.name ? ` — ${birth.name}` : ''}`,
      pred.current_life_phase,
      sav.overall_pattern,
      life.next_6_months,
      life.next_year,
      ...textLines(life.major_themes),
    ].filter(Boolean);
    try {
      await Share.share({ message: lines.join('\n\n') });
    } catch (_) {
      Alert.alert(t('ashtakavargaStudy.errors.shareTitle'), t('ashtakavargaStudy.errors.share'));
    }
  };

  const exportStudyPdf = async () => {
    if (!study?.predictions || generatingPdf) return;
    setGeneratingPdf(true);
    try {
      const houseHtml = Object.entries(insights).map(([key, value]) => (
        `<div class="subsection"><h3>${escapeHtml(domainLabel(key))}</h3>${pdfParagraph(value)}</div>`
      )).join('');
      const timingHtml = (pred.timing_highlights || []).map((item, index) => {
        if (typeof item === 'string') return `<div class="timing">${pdfParagraph(item)}</div>`;
        const title = item?.window || item?.period || item?.label || t('ashtakavargaStudy.sections.period', { number: index + 1 });
        const basis = item?.ashtakavarga_basis || item?.basis;
        return `<div class="timing"><h3>${escapeHtml(title)}</h3>${pdfParagraph(item?.focus || item?.summary)}${basis ? pdfParagraph(t('ashtakavargaStudy.sections.basis', { basis }), 'basis') : ''}</div>`;
      }).join('');
      const transitHtml = [
        transit.saturn_influence && `<h3>${escapeHtml(t('ashtakavargaStudy.sections.saturn'))}</h3>${pdfParagraph(transit.saturn_influence)}`,
        transit.jupiter_influence && `<h3>${escapeHtml(t('ashtakavargaStudy.sections.jupiter'))}</h3>${pdfParagraph(transit.jupiter_influence)}`,
        transit.rahu_ketu_influence && `<h3>${escapeHtml(t('ashtakavargaStudy.sections.rahuKetu'))}</h3>${pdfParagraph(transit.rahu_ketu_influence)}`,
        textLines(transit.timing_recommendations).length && `<h3>${escapeHtml(t('ashtakavargaStudy.sections.timingGuidance'))}</h3>${pdfList(transit.timing_recommendations)}`,
      ].filter(Boolean).join('');
      const dashaHtml = [
        dasha.current_period_strength && `<h3>${escapeHtml(t('ashtakavargaStudy.sections.periodStrength'))}</h3>${pdfParagraph(dasha.current_period_strength)}`,
        dasha.expected_results && `<h3>${escapeHtml(t('ashtakavargaStudy.sections.whatToExpect'))}</h3>${pdfParagraph(dasha.expected_results)}`,
        pdfList(dasha.recommendations),
      ].filter(Boolean).join('');
      const outlookHtml = [
        life.next_6_months && `<h3>${escapeHtml(t('ashtakavargaStudy.sections.nextSixMonths'))}</h3>${pdfParagraph(life.next_6_months)}`,
        life.next_year && `<h3>${escapeHtml(t('ashtakavargaStudy.sections.nextYear'))}</h3>${pdfParagraph(life.next_year)}`,
        textLines(life.major_themes).length && `<h3>${escapeHtml(t('ashtakavargaStudy.sections.majorThemes'))}</h3>${pdfList(life.major_themes)}`,
      ].filter(Boolean).join('');
      const strengthHtml = [
        pdfParagraph(sav.overall_pattern),
        textLines(sav.strong_areas).length && `<h3>${escapeHtml(t('ashtakavargaStudy.sections.supportiveAreas'))}</h3>${pdfList(sav.strong_areas)}`,
        textLines(sav.challenging_areas).length && `<h3>${escapeHtml(t('ashtakavargaStudy.sections.careAreas'))}</h3>${pdfList(sav.challenging_areas)}`,
      ].filter(Boolean).join('');

      const html = `<!doctype html>
        <html><head><meta charset="utf-8"><style>
          @page { margin: 18mm 15mm; }
          body { margin: 0; color: #272033; background: #fff; font-family: Arial, "Noto Sans", sans-serif; font-size: 11pt; line-height: 1.58; }
          .header { padding-bottom: 20px; margin-bottom: 24px; border-bottom: 3px solid #8b1d4a; }
          .brand { color: #8b1d4a; font-size: 10pt; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; }
          h1 { margin: 7px 0 5px; color: #241322; font-size: 25pt; }
          .meta { color: #6f6671; font-size: 10pt; }
          .method { margin-top: 10px; color: #534856; }
          .section { margin: 0 0 24px; }
          h2 { margin: 0 0 11px; padding-left: 10px; border-left: 4px solid #d5a32d; color: #8b1d4a; font-size: 16pt; }
          h3 { margin: 12px 0 5px; color: #322137; font-size: 11.5pt; }
          p { margin: 0 0 10px; }
          ul { margin: 6px 0 10px; padding-left: 22px; }
          li { margin: 0 0 6px; }
          .subsection { padding: 10px 0; border-bottom: 1px solid #eee7e3; }
          .timing { margin: 0 0 10px; padding: 10px 12px; background: #faf6ee; border-left: 3px solid #d5a32d; }
          .basis { color: #6f6671; font-size: 9.5pt; font-style: italic; }
          .footer { margin-top: 28px; padding-top: 12px; border-top: 1px solid #ddd; color: #777; font-size: 8.5pt; text-align: center; }
          ${PDF_PRINT_STYLES}
        </style></head><body>
          <header class="header">
            <div class="brand">AstroRoshni</div>
            <h1>${escapeHtml(t('ashtakavargaStudy.title'))}</h1>
            <div class="meta">${escapeHtml(t('ashtakavargaStudy.pdf.preparedFor', { name: birth?.name || route.params?.birthName || t('ashtakavargaStudy.selectedNative'), date: studyDate }))}</div>
            <div class="method">${escapeHtml(study?.methodology || pred?.methodology || t('ashtakavargaStudy.methodology'))}</div>
          </header>
          ${pdfSection(t('ashtakavargaStudy.sections.currentPhase'), pdfParagraph(pred.current_life_phase))}
          ${pdfSection(t('ashtakavargaStudy.sections.strengthPattern'), strengthHtml)}
          ${pdfSection(t('ashtakavargaStudy.sections.lifeAreas'), houseHtml)}
          ${pdfSection(t('ashtakavargaStudy.sections.timingWindows'), timingHtml)}
          ${pdfSection(t('ashtakavargaStudy.sections.transitInfluences'), transitHtml)}
          ${pdfSection(t('ashtakavargaStudy.sections.dashaAnalysis'), dashaHtml)}
          ${pdfSection(t('ashtakavargaStudy.sections.forwardOutlook'), outlookHtml)}
          ${pdfSection(t('ashtakavargaStudy.sections.remedialMeasures'), pdfList(pred.remedial_measures))}
          <footer class="footer">${escapeHtml(t('ashtakavargaStudy.pdf.disclaimer'))}</footer>
        </body></html>`;

      const pdfUri = await exportHtmlAsPdf(html, { timeoutMs: 45000 });
      await sharePDFOnWhatsApp(pdfUri, {
        dialogTitle: t('ashtakavargaStudy.pdf.dialogTitle', { name: birth?.name || route.params?.birthName || t('ashtakavargaStudy.selectedNative') }),
        reportType: 'ashtakavarga_study',
        source: 'ashtakavarga_study_screen',
      });
    } catch (pdfError) {
      console.error('Ashtakavarga PDF export error:', pdfError);
      Alert.alert(t('ashtakavargaStudy.errors.pdfTitle'), t('ashtakavargaStudy.errors.pdf'));
    } finally {
      setGeneratingPdf(false);
    }
  };

  const refreshStudy = async () => {
    const authOk = await requireAuthForPaid({
      feature: t('ashtakavargaStudy.title'),
      message: t('ashtakavargaStudy.refresh.signIn'),
      resume: { resumeRoute: 'AshtakvargaStudy', resumeParams: {} },
    });
    if (!authOk) return;
    setRefreshModalVisible(false);
    setRefreshing(true);
    try {
      const selectedBirth = birth || await storage.getBirthDetails();
      if (!selectedBirth) throw new Error(t('ashtakavargaStudy.errors.selectNative'));
      const result = await requestStudy(selectedBirth, true, (key, fallback) => t(key, { defaultValue: fallback }));
      setStudy(result);
      if (Number(result?.credits_charged) > 0) fetchBalance();
      scrollRef.current?.scrollTo({ y: 0, animated: true });
    } catch (refreshError) {
      Alert.alert(t('ashtakavargaStudy.actions.refresh'), refreshError?.message || t('ashtakavargaStudy.errors.refresh'));
    } finally {
      setRefreshing(false);
    }
  };

  const openActions = () => {
    Alert.alert(t('ashtakavargaStudy.actions.title'), t('ashtakavargaStudy.actions.prompt'), [
      { text: t('ashtakavargaStudy.actions.exportPdf'), onPress: exportStudyPdf },
      { text: t('ashtakavargaStudy.actions.shareSummary'), onPress: shareStudy },
      { text: t('ashtakavargaStudy.actions.refresh'), onPress: () => setRefreshModalVisible(true) },
      { text: t('ashtakavargaStudy.actions.cancel'), style: 'cancel' },
    ]);
  };

  const cardStyle = { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder };

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}> 
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
      <LinearGradient
        colors={theme === 'dark'
          ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd]
          : [colors.background, colors.backgroundSecondary, colors.background]}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <View style={[styles.header, { borderBottomColor: colors.cardBorder }]}> 
            <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.headerButton, cardStyle]} accessibilityLabel={t('ashtakavargaStudy.a11y.back')}>
              <Ionicons name="arrow-back" size={23} color={colors.text} />
            </TouchableOpacity>
            <View style={styles.headerCopy}>
              <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1}>{t('ashtakavargaStudy.title')}</Text>
              <Text style={[styles.headerMeta, { color: colors.textSecondary }]} numberOfLines={1}>
                {birth?.name || route.params?.birthName || t('ashtakavargaStudy.selectedNative')} · {studyDate}
              </Text>
            </View>
            <TouchableOpacity
              onPress={exportStudyPdf}
              disabled={!study || generatingPdf}
              style={[styles.headerButton, cardStyle, styles.headerActionSpacing]}
              accessibilityLabel={t('ashtakavargaStudy.a11y.exportPdf')}
            >
              {generatingPdf
                ? <ActivityIndicator size="small" color={colors.primary} />
                : <Ionicons name="document-text-outline" size={21} color={colors.text} />}
            </TouchableOpacity>
            <TouchableOpacity onPress={openActions} style={[styles.headerButton, cardStyle]} accessibilityLabel={t('ashtakavargaStudy.a11y.actions')}>
              <Ionicons name="ellipsis-vertical" size={21} color={colors.text} />
            </TouchableOpacity>
          </View>

          {loading ? (
            <View style={styles.centered}>
              <ActivityIndicator size="large" color={colors.primary} />
              <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('ashtakavargaStudy.opening')}</Text>
            </View>
          ) : error ? (
            <View style={styles.centered}>
              <Ionicons name="document-text-outline" size={44} color={colors.textSecondary} />
              <Text style={[styles.errorTitle, { color: colors.text }]}>{t('ashtakavargaStudy.unavailable')}</Text>
              <Text style={[styles.errorText, { color: colors.textSecondary }]}>{error}</Text>
              <TouchableOpacity onPress={loadSavedStudy} style={[styles.retryButton, { backgroundColor: colors.primary }]}> 
                <Text style={[styles.retryText, { color: colors.textInverse }]}>{t('ashtakavargaStudy.tryAgain')}</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.reader}>
              <View style={[styles.jumpBar, { backgroundColor: colors.background, borderBottomColor: colors.cardBorder }]}> 
                <Text style={[styles.jumpLabel, { color: colors.textSecondary }]}>{t('ashtakavargaStudy.jumpTo')}</Text>
                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  contentContainerStyle={styles.jumpChips}
                >
                  {visibleSections.map((section) => (
                    <TouchableOpacity
                      key={section.id}
                      onPress={() => jumpTo(section.id)}
                      style={[styles.jumpChip, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}
                    >
                      <Text style={[styles.jumpChipText, { color: colors.primary }]}>{section.label}</Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>

              <View style={styles.scrollClip}>
                <ScrollView
                  ref={scrollRef}
                  contentContainerStyle={styles.content}
                  showsVerticalScrollIndicator={false}
                >
                  <View style={[styles.hero, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}> 
                    <Text style={[styles.eyebrow, { color: colors.accent }]}>{t('ashtakavargaStudy.longForm')}</Text>
                    <Text style={[styles.heroTitle, { color: colors.textInverse }]}>{t('ashtakavargaStudy.heroTitle')}</Text>
                    <Text style={[styles.heroSubtitle, { color: colors.textInverseMuted }]}>
                      {study?.methodology || pred?.methodology || t('ashtakavargaStudy.methodology')}
                    </Text>
                    <View style={styles.savedRow}>
                      <Ionicons name="bookmark" size={15} color={colors.accent} />
                      <Text style={[styles.savedText, { color: colors.textInverseMuted }]}>{t('ashtakavargaStudy.savedReopen')}</Text>
                    </View>
                  </View>

                  {pred.current_life_phase ? <StudySection id="phase" title={t('ashtakavargaStudy.sections.currentPhase')} colors={colors} registerSection={registerSection}>
                    <Paragraph colors={colors} muted>{pred.current_life_phase}</Paragraph>
                  </StudySection> : null}

                  {(sav.overall_pattern || sav.strong_areas?.length || sav.challenging_areas?.length) ? <StudySection id="strengths" title={t('ashtakavargaStudy.sections.strengthPattern')} colors={colors} registerSection={registerSection}>
                    <Paragraph colors={colors} muted>{sav.overall_pattern}</Paragraph>
                    {textLines(sav.strong_areas).length ? <Text style={[styles.subheading, { color: colors.text }]}>{t('ashtakavargaStudy.sections.supportiveAreas')}</Text> : null}
                    <BulletList items={sav.strong_areas} colors={colors} />
                    {textLines(sav.challenging_areas).length ? <Text style={[styles.subheading, { color: colors.text }]}>{t('ashtakavargaStudy.sections.careAreas')}</Text> : null}
                    <BulletList items={sav.challenging_areas} colors={colors} />
                  </StudySection> : null}

                  {Object.keys(insights).length ? <StudySection id="houses" title={t('ashtakavargaStudy.sections.lifeAreas')} colors={colors} registerSection={registerSection}>
                    {Object.entries(insights).map(([key, value], index) => (
                      <View key={key} style={[styles.domainRow, index > 0 && { borderTopColor: colors.cardBorder, borderTopWidth: StyleSheet.hairlineWidth }]}> 
                        <Text style={[styles.domainTitle, { color: colors.primary }]}>{domainLabel(key)}</Text>
                        <Paragraph colors={colors} muted>{value}</Paragraph>
                      </View>
                    ))}
                  </StudySection> : null}

                  {pred.timing_highlights?.length ? <StudySection id="timing" title={t('ashtakavargaStudy.sections.timingWindows')} colors={colors} registerSection={registerSection}>
                    {(pred.timing_highlights || []).map((item, index) => {
                      if (typeof item === 'string') return <BulletList key={`${item}-${index}`} items={[item]} colors={colors} />;
                      return (
                        <View key={`${item?.window || item?.period}-${index}`} style={[styles.timingCard, { backgroundColor: colors.surfaceMuted, borderLeftColor: colors.accent }]}> 
                          <Text style={[styles.subheading, { color: colors.text }]}>{item?.window || item?.period || item?.label || t('ashtakavargaStudy.sections.period', { number: index + 1 })}</Text>
                          <Paragraph colors={colors} muted>{item?.focus || item?.summary}</Paragraph>
                          {item?.ashtakavarga_basis || item?.basis ? (
                            <Text style={[styles.basis, { color: colors.textSecondary }]}>{t('ashtakavargaStudy.sections.basis', { basis: item.ashtakavarga_basis || item.basis })}</Text>
                          ) : null}
                        </View>
                      );
                    })}
                  </StudySection> : null}

                  {Object.keys(transit).length ? <StudySection id="transits" title={t('ashtakavargaStudy.sections.transitInfluences')} colors={colors} registerSection={registerSection}>
                    {transit.saturn_influence ? <><Text style={[styles.subheading, { color: colors.text }]}>{t('ashtakavargaStudy.sections.saturn')}</Text><Paragraph colors={colors} muted>{transit.saturn_influence}</Paragraph></> : null}
                    {transit.jupiter_influence ? <><Text style={[styles.subheading, { color: colors.text }]}>{t('ashtakavargaStudy.sections.jupiter')}</Text><Paragraph colors={colors} muted>{transit.jupiter_influence}</Paragraph></> : null}
                    {transit.rahu_ketu_influence ? <><Text style={[styles.subheading, { color: colors.text }]}>{t('ashtakavargaStudy.sections.rahuKetu')}</Text><Paragraph colors={colors} muted>{transit.rahu_ketu_influence}</Paragraph></> : null}
                    {textLines(transit.timing_recommendations).length ? <><Text style={[styles.subheading, { color: colors.text }]}>{t('ashtakavargaStudy.sections.timingGuidance')}</Text><BulletList items={transit.timing_recommendations} colors={colors} /></> : null}
                  </StudySection> : null}

                  {Object.keys(dasha).length ? <StudySection id="dasha" title={t('ashtakavargaStudy.sections.dashaAnalysis')} colors={colors} registerSection={registerSection}>
                    {dasha.current_period_strength ? <><Text style={[styles.subheading, { color: colors.text }]}>{t('ashtakavargaStudy.sections.periodStrength')}</Text><Paragraph colors={colors} muted>{dasha.current_period_strength}</Paragraph></> : null}
                    {dasha.expected_results ? <><Text style={[styles.subheading, { color: colors.text }]}>{t('ashtakavargaStudy.sections.whatToExpect')}</Text><Paragraph colors={colors} muted>{dasha.expected_results}</Paragraph></> : null}
                    <BulletList items={dasha.recommendations} colors={colors} />
                  </StudySection> : null}

                  {(life.next_6_months || life.next_year || life.major_themes?.length) ? <StudySection id="outlook" title={t('ashtakavargaStudy.sections.forwardOutlook')} colors={colors} registerSection={registerSection}>
                    {life.next_6_months ? <><Text style={[styles.subheading, { color: colors.text }]}>{t('ashtakavargaStudy.sections.nextSixMonths')}</Text><Paragraph colors={colors} muted>{life.next_6_months}</Paragraph></> : null}
                    {life.next_year ? <><Text style={[styles.subheading, { color: colors.text }]}>{t('ashtakavargaStudy.sections.nextYear')}</Text><Paragraph colors={colors} muted>{life.next_year}</Paragraph></> : null}
                    {textLines(life.major_themes).length ? <><Text style={[styles.subheading, { color: colors.text }]}>{t('ashtakavargaStudy.sections.majorThemes')}</Text><BulletList items={life.major_themes} colors={colors} /></> : null}
                  </StudySection> : null}

                  {pred.remedial_measures?.length ? <StudySection id="remedies" title={t('ashtakavargaStudy.sections.remedialMeasures')} colors={colors} registerSection={registerSection}>
                    <BulletList items={pred.remedial_measures} colors={colors} />
                  </StudySection> : null}
                </ScrollView>
              </View>
            </View>
          )}
          {refreshing ? (
            <View style={[styles.refreshOverlay, { backgroundColor: colors.overlay }]}> 
              <View style={[styles.refreshCard, cardStyle]}>
                <ActivityIndicator size="large" color={colors.primary} />
                <Text style={[styles.refreshTitle, { color: colors.text }]}>{t('ashtakavargaStudy.refresh.working')}</Text>
                <Text style={[styles.refreshText, { color: colors.textSecondary }]}>{t('ashtakavargaStudy.refresh.workingBody')}</Text>
              </View>
            </View>
          ) : null}
          <CreditModal
            visible={refreshModalVisible}
            onConfirm={refreshStudy}
            onCancel={() => setRefreshModalVisible(false)}
            cost={creditCost}
            title={t('ashtakavargaStudy.refresh.title')}
            description={t('ashtakavargaStudy.refresh.description', { cost: creditCost, credits })}
            confirmLabel={t('ashtakavargaStudy.actions.refresh')}
          />
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  header: { minHeight: 66, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', borderBottomWidth: StyleSheet.hairlineWidth },
  headerButton: { width: 42, height: 42, borderRadius: 21, alignItems: 'center', justifyContent: 'center', borderWidth: 1 },
  headerActionSpacing: { marginRight: 8 },
  headerCopy: { flex: 1, paddingHorizontal: 12 },
  headerTitle: { fontSize: 20, fontWeight: '800' },
  headerMeta: { fontSize: 12, marginTop: 2 },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 28 },
  loadingText: { fontSize: 14, marginTop: 14 },
  errorTitle: { fontSize: 20, fontWeight: '800', marginTop: 14 },
  errorText: { fontSize: 14, lineHeight: 21, textAlign: 'center', marginTop: 8 },
  retryButton: { borderRadius: 999, paddingHorizontal: 22, paddingVertical: 12, marginTop: 18 },
  retryText: { fontWeight: '800' },
  reader: { flex: 1 },
  jumpBar: { paddingHorizontal: 16, paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth },
  jumpLabel: { fontSize: 11, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 },
  jumpChips: { flexDirection: 'row', gap: 7, paddingRight: 10 },
  jumpChip: { borderWidth: 1, borderRadius: 999, paddingHorizontal: 11, paddingVertical: 6 },
  jumpChipText: { fontSize: 12, fontWeight: '700' },
  scrollClip: { flex: 1 },
  content: { padding: 16, paddingBottom: 40 },
  hero: { borderWidth: 1, borderRadius: 24, padding: 20, marginBottom: 14 },
  eyebrow: { fontSize: 11, fontWeight: '800', letterSpacing: 1.2, marginBottom: 10 },
  heroTitle: { fontSize: 25, lineHeight: 31, fontWeight: '900' },
  heroSubtitle: { fontSize: 14, lineHeight: 20, marginTop: 8 },
  savedRow: { flexDirection: 'row', alignItems: 'center', marginTop: 15, gap: 7 },
  savedText: { fontSize: 12, flex: 1 },
  sectionCard: { borderWidth: 1, borderRadius: 20, padding: 17, marginBottom: 13 },
  sectionTitle: { fontSize: 19, lineHeight: 24, fontWeight: '800', marginBottom: 12 },
  subheading: { fontSize: 15, lineHeight: 20, fontWeight: '800', marginTop: 5, marginBottom: 5 },
  paragraph: { fontSize: 15, lineHeight: 23, marginBottom: 10 },
  bulletRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 9 },
  bulletDot: { width: 6, height: 6, borderRadius: 3, marginTop: 8, marginRight: 10 },
  bulletText: { flex: 1, fontSize: 15, lineHeight: 22 },
  domainRow: { paddingVertical: 10 },
  domainTitle: { fontSize: 14, fontWeight: '800', marginBottom: 5, textTransform: 'capitalize' },
  timingCard: { borderRadius: 14, borderLeftWidth: 3, padding: 13, marginBottom: 10 },
  basis: { fontSize: 12, lineHeight: 18, fontStyle: 'italic' },
  refreshOverlay: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center', padding: 28 },
  refreshCard: { width: '100%', maxWidth: 360, borderWidth: 1, borderRadius: 22, padding: 24, alignItems: 'center' },
  refreshTitle: { fontSize: 18, fontWeight: '800', marginTop: 14 },
  refreshText: { fontSize: 14, lineHeight: 20, textAlign: 'center', marginTop: 7 },
});
