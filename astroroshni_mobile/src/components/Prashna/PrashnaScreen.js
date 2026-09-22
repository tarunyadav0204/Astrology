import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, Text, TouchableOpacity, View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { prashnaAPI } from '../../services/api';
import { useCredits } from '../../credits/CreditContext';
import { useAuthGate } from '../../auth/AuthGateContext';
import AnalysisCreditModal from '../Analysis/AnalysisCreditModal';
import PlaceSearchField from '../PlaceSearchField';
import { detectQuestionPlace, loadSavedQuestionPlace, saveQuestionPlace } from '../../utils/questionPlace';

const pad = (value) => String(value).padStart(2, '0');
const nowStamp = () => {
  const now = new Date();
  const detected = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return {
    date: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`,
    time: `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`,
    timezone: detected === 'Asia/Calcutta' ? 'Asia/Kolkata' : detected,
  };
};

const tone = (result, colors) => ({
  favorable: { bg: 'rgba(22,163,74,.12)', border: 'rgba(22,163,74,.35)', text: '#15803d' },
  unfavorable: { bg: 'rgba(220,38,38,.10)', border: 'rgba(220,38,38,.30)', text: '#b91c1c' },
  mixed: { bg: 'rgba(217,119,6,.10)', border: 'rgba(217,119,6,.32)', text: '#b45309' },
  cannot_judge: { bg: colors.surfaceMuted, border: colors.cardBorder, text: colors.text },
}[result] || { bg: colors.surfaceMuted, border: colors.cardBorder, text: colors.text });

// API details are developer-facing and may be English or framework-generated.
// Keep the customer-facing error stable and localized.
const apiError = (_error, fallback) => fallback;

export default function PrashnaScreen({ navigation, route }) {
  const { t, i18n } = useTranslation();
  const { colors } = useTheme();
  const { credits, pricing, pricingOriginal, fetchBalance, fetchPricing } = useCredits();
  const { requireAuthForPaid } = useAuthGate();
  const [questionId, setQuestionId] = useState('');
  const [topics, setTopics] = useState([]);
  const [topic, setTopic] = useState('');
  const [catalogueLoading, setCatalogueLoading] = useState(true);
  const [place, setPlace] = useState(null);
  const [placeLoading, setPlaceLoading] = useState(true);
  const placeEdited = useRef(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showWorking, setShowWorking] = useState(false);
  const [castMoment, setCastMoment] = useState(null);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [showHowItWorks, setShowHowItWorks] = useState(false);
  const [gateCost, setGateCost] = useState(3);
  const [gateCredits, setGateCredits] = useState(credits);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const found = await detectQuestionPlace() || await loadSavedQuestionPlace();
        if (active && !placeEdited.current && found) setPlace(found);
      } finally {
        if (active) setPlaceLoading(false);
      }
    })();
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const response = await prashnaAPI.getTopics();
        const rows = (response?.data || response)?.topics;
        if (!Array.isArray(rows) || rows.length === 0) throw new Error('empty_prashna_catalogue');
        if (active) { setTopics(rows); setTopic(rows[0].id); }
      } catch (err) {
        if (active) setError(apiError(err, t('prashna.screen.topicsLoadError')));
      } finally { if (active) setCatalogueLoading(false); }
    })();
    return () => { active = false; };
  }, [t]);

  useEffect(() => {
    const readingId = Number(route?.params?.readingId);
    if (!Number.isInteger(readingId) || readingId < 1) return undefined;
    let active = true;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const response = await prashnaAPI.getReading(readingId);
        const data = response?.data || response;
        if (!active) return;
        if (['favorable', 'unfavorable', 'mixed', 'cannot_judge'].includes(data?.verdict?.result)) {
          setResult(data);
        } else {
          setError(t('prashna.screen.calculationError'));
        }
      } catch (err) {
        if (active) setError(apiError(err, t('prashna.screen.calculationError')));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [route?.params?.readingId, t]);

  const localizedTopics = useMemo(() => topics.map((item) => ({
    ...item,
    label: t(`prashna.topics.${item.id}`, { defaultValue: item.label }),
    questions: (item.questions || []).map((question) => ({
      ...question,
      text: t(`prashna.questions.${question.id}`, { defaultValue: question.text }),
    })),
  })), [topics, t, i18n.language]);
  const selected = useMemo(() => localizedTopics.find((item) => item.id === topic), [localizedTopics, topic]);
  const selectedQuestion = useMemo(() => selected?.questions?.find((item) => item.id === questionId), [selected, questionId]);
  const locationReady = Number.isFinite(Number(place?.latitude)) && Number.isFinite(Number(place?.longitude));
  const displayedCost = Number(pricing?.prashna ?? 3);
  const displayedOriginalCost = Number(pricingOriginal?.prashna);

  const castQuestion = async (attempt) => {
    const response = await prashnaAPI.analyze({ question_id: questionId, ...attempt });
    const data = response?.data || response;
    if (!['favorable', 'unfavorable', 'mixed', 'cannot_judge'].includes(data?.verdict?.result)) {
      throw new Error('invalid_prashna_result');
    }
    setResult(data);
    await fetchBalance();
  };

  const openCreditGate = async () => {
    if (!questionId || !locationReady || loading) return;
    const authOk = await requireAuthForPaid({
      feature: t('prashna.screen.authFeature'),
      message: t('prashna.screen.authMessage'),
      resume: { resumeRoute: 'Prashna', resumeParams: {} },
    });
    if (!authOk) return;
    const requestedMoment = castMoment || {
      ...nowStamp(), latitude: Number(place.latitude), longitude: Number(place.longitude), place: place.name || '',
    };
    let checkedCost = displayedCost;
    setLoading(true); setError('');
    try {
      const [priceResult, balanceResult] = await Promise.all([
        fetchPricing({ force: true }), fetchBalance(),
      ]);
      checkedCost = Number(priceResult?.pricing?.prashna ?? displayedCost);
      const currentBalance = Number.isFinite(Number(balanceResult)) ? Number(balanceResult) : Number(credits || 0);
      setGateCost(checkedCost);
      setGateCredits(currentBalance);
      if (currentBalance < checkedCost) {
        setShowCreditModal(true);
        return;
      }
      setCastMoment(requestedMoment);
      await castQuestion(requestedMoment);
    } catch (err) {
      if (err?.response?.status === 402) {
        const latestBalance = await fetchBalance();
        setGateCost(checkedCost);
        setGateCredits(Number(latestBalance || 0));
        setShowCreditModal(true);
      } else {
        setError(apiError(err, t('prashna.screen.calculationError')));
      }
    } finally { setLoading(false); }
  };

  const chooseTopic = (id) => { setTopic(id); setQuestionId(''); setCastMoment(null); setError(''); };
  const reset = () => { setQuestionId(''); setResult(null); setCastMoment(null); setError(''); setShowWorking(false); };

  const renderResult = () => {
    const code = result.verdict.result;
    const visual = tone(code, colors);
    const questionTopic = result.question?.topic || result.classical?.topic || topic;
    const intent = result.question?.intent || result.classical?.intent || 'outcome';
    const outcomeKey = `prashna.outcomes.${questionTopic}.${intent}`;
    const outcome = t(outcomeKey, {
      defaultValue: t(`prashna.outcomes.${questionTopic}.outcome`, { defaultValue: t('prashna.outcomes.career.outcome') }),
    });
    const matched = (result.classical?.rules || []).filter((row) => row.matched);
    const supports = matched.filter((row) => row.polarity === 'support');
    const obstructions = matched.filter((row) => row.polarity === 'obstruction');
    const localizedQuestion = t(`prashna.questions.${result.question?.question_id || questionId}`, {
      defaultValue: selectedQuestion?.text || result.question?.original_question,
    });
    const evidenceCard = (polarity, rules, color) => rules.length > 0 && (
      <View style={[styles.card, { borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}>
        <Text style={[styles.cardTitle, { color }]}>{t(`prashna.screen.${polarity === 'support' ? 'supports' : 'obstructs'}`)}</Text>
        <Text style={[styles.point, { color: colors.text }]}>• {t(`prashna.evidence.${questionTopic}.${polarity}`)}</Text>
        <Text style={[styles.tech, { color: colors.textSecondary }]}>
          {t('prashna.screen.matchedRuleRefs', { rules: rules.map((rule) => `${rule.id} · ${rule.source_section}`).join('; ') })}
        </Text>
      </View>
    );
    return <>
      <Text style={[styles.kicker, { color: colors.primary }]}>{t('prashna.screen.selectedQuestion')}</Text>
      <Text style={[styles.confirmedQuestion, { color: colors.text }]}>{localizedQuestion}</Text>
      <Text style={[styles.meta, { color: colors.textSecondary }]}>
        {t('prashna.screen.fixedMoment', {
          date: result.clock.date,
          time: result.clock.time,
          place: result.clock.place || t('prashna.screen.selectedLocation'),
        })}
      </Text>

      <View style={[styles.verdict, { backgroundColor: visual.bg, borderColor: visual.border }]}>
        <Text style={[styles.verdictTitle, { color: visual.text }]}>{t(`prashna.result.headings.${code}`, { outcome })}</Text>
        <Text style={[styles.body, { color: colors.text }]}>{t(`prashna.result.summaries.${code}`, { outcome })}</Text>
      </View>

      {evidenceCard('support', supports, '#15803d')}
      {evidenceCard('obstruction', obstructions, '#b91c1c')}

      <View style={[styles.meaning, { backgroundColor: colors.surfaceMuted }]}>
        <Text style={[styles.cardTitle, { color: colors.text }]}>{t('prashna.screen.decisionMeaning')}</Text>
        <Text style={[styles.body, { color: colors.text }]}>{t(`prashna.result.decisions.${code}`)}</Text>
        <Text style={[styles.limit, { color: colors.textSecondary }]}>{t('prashna.result.limits')}</Text>
      </View>

      <TouchableOpacity style={styles.workingButton} onPress={() => setShowWorking(!showWorking)}>
        <Ionicons name={showWorking ? 'chevron-up' : 'chevron-down'} color={colors.primary} size={17} />
        <Text style={[styles.workingText, { color: colors.primary }]}>{t(`prashna.screen.${showWorking ? 'hideWorking' : 'showWorking'}`)}</Text>
      </TouchableOpacity>
      {showWorking && <View style={[styles.technical, { borderColor: colors.cardBorder }]}>
        <Text style={[styles.cardTitle, { color: colors.text }]}>{t('prashna.screen.methodCalculation')}</Text>
        <Text style={[styles.tech, { color: colors.textSecondary }]}>Praśnatantra–Tājika · {result.classical.ruleset_version}</Text>
        <Text style={[styles.tech, { color: colors.textSecondary }]}>{t('prashna.calculation.ayanamsha')} · {t('prashna.calculation.houseSystem')}</Text>
        <Text style={[styles.tech, { color: colors.textSecondary }]}>UTC {result.clock.utc} · {(result.calculation.ephemeris || []).join(', ')}</Text>
        <Text style={[styles.cardTitle, { color: colors.text, marginTop: 12 }]}>{t('prashna.screen.classicalRoles')}</Text>
        {(result.classical.roles || []).map((role) => <Text key={`${role.house}-${role.role}`} style={[styles.tech, { color: colors.textSecondary }]}>
          {t('prashna.screen.houseRole', {
            house: role.house,
            role: t(`prashna.roles.${questionTopic}.${role.house}`, { defaultValue: role.role }),
            lord: t(`prashna.planets.${String(role.lord).toLowerCase()}`, { defaultValue: role.lord }),
          })}
        </Text>)}
        <Text style={[styles.cardTitle, { color: colors.text, marginTop: 12 }]}>{t('prashna.screen.matchedRules')}</Text>
        {matched.map((rule) => <Text key={rule.id} style={[styles.tech, { color: colors.textSecondary }]}>{rule.id} · {rule.source_section}</Text>)}
      </View>}
      <TouchableOpacity onPress={reset} style={[styles.secondary, { borderColor: colors.cardBorder }]}>
        <Text style={{ color: colors.text, fontWeight: '700' }}>{t('prashna.screen.askNew')}</Text>
      </TouchableOpacity>
    </>;
  };

  const renderForm = () => <>
    <Text style={[styles.pageTitle, { color: colors.text }]}>{t('prashna.screen.pageTitle')}</Text>
    <Text style={[styles.brandLine, { color: colors.primary }]}>{t('prashna.screen.brandLine')}</Text>
    <Text style={[styles.lead, { color: colors.textSecondary }]}>{t('prashna.screen.lead')}</Text>
    <TouchableOpacity onPress={() => setShowHowItWorks(true)} style={styles.howLink} accessibilityRole="button" accessibilityLabel={t('prashna.screen.howLink')}>
      <Ionicons name="information-circle-outline" size={18} color={colors.primary} />
      <Text style={[styles.howLinkText, { color: colors.primary }]}>{t('prashna.screen.howLink')}</Text>
    </TouchableOpacity>
    <View style={[styles.info, { backgroundColor: colors.surfaceMuted }]}>
      <Text style={[styles.cardTitle, { color: colors.text }]}>{t('prashna.screen.goodUses')}</Text>
      <Text style={[styles.body, { color: colors.textSecondary }]}>{t('prashna.screen.goodUsesBody')}</Text>
      <Text style={[styles.cardTitle, { color: colors.text, marginTop: 10 }]}>{t('prashna.screen.notAvailable')}</Text>
      <Text style={[styles.body, { color: colors.textSecondary }]}>{t('prashna.screen.notAvailableBody')}</Text>
    </View>
    <Text style={[styles.label, { color: colors.text }]}>{t('prashna.screen.categoryLabel')}</Text>
    {catalogueLoading ? <ActivityIndicator color={colors.primary} /> : <View style={styles.chips}>{localizedTopics.map((item) => <TouchableOpacity key={item.id} onPress={() => chooseTopic(item.id)} style={[styles.chip, { borderColor: topic === item.id ? colors.primary : colors.cardBorder, backgroundColor: topic === item.id ? colors.primary : colors.cardBackground }]}><Text style={{ color: topic === item.id ? '#fff' : colors.text, fontWeight: '600' }}>{item.label}</Text></TouchableOpacity>)}</View>}
    <Text style={[styles.label, { color: colors.text }]}>{t('prashna.screen.questionLabel')}</Text>
    <Text style={[styles.hint, { color: colors.textSecondary }]}>{t('prashna.screen.questionHint')}</Text>
    <View style={styles.questionList}>{(selected?.questions || []).map((question) => {
      const active = questionId === question.id;
      return <TouchableOpacity key={question.id} onPress={() => { setQuestionId(question.id); setCastMoment(null); setError(''); }}
        style={[styles.questionOption, { borderColor: active ? colors.primary : colors.cardBorder,
          backgroundColor: active ? colors.surfaceMuted : colors.cardBackground }]}>
        <Ionicons name={active ? 'radio-button-on' : 'radio-button-off'} size={20} color={active ? colors.primary : colors.textSecondary} />
        <Text style={[styles.questionText, { color: colors.text }]}>{question.text}</Text>
      </TouchableOpacity>;
    })}</View>
    {selectedQuestion ? <Text style={[styles.notice, { color: colors.textSecondary }]}>{t('prashna.screen.castNotice')}</Text> : null}
    <Text style={[styles.label, { color: colors.text }]}>{t('prashna.screen.placeLabel')}</Text>
    {castMoment ? <View style={[styles.fixedPlace, { borderColor: colors.cardBorder }]}><Text style={{ color: colors.text }}>{castMoment.place || t('prashna.screen.selectedLocation')}</Text></View> : placeLoading ? <ActivityIndicator color={colors.primary} /> : <PlaceSearchField
      selectedName={place?.name || ''} selectedLatitude={place?.latitude} selectedLongitude={place?.longitude}
      placeholder={t('prashna.screen.placePlaceholder')}
      onDraftChange={(name) => { placeEdited.current = true; setPlace({ name, latitude: null, longitude: null, source: 'draft' }); }}
      onSelect={(next) => { placeEdited.current = true; const saved = { ...next, source: next.source || 'manual' }; setPlace(saved); saveQuestionPlace(saved); }}
    />}
    {error ? <Text style={styles.error}>{error}</Text> : null}
    <TouchableOpacity disabled={!questionId || !locationReady || loading} onPress={openCreditGate} style={[styles.primary, { backgroundColor: colors.primary, opacity: questionId && locationReady && !loading ? 1 : .5 }]}>
      {loading ? <ActivityIndicator color="#fff" /> : <View style={styles.castButtonContent}>
        <Text style={styles.primaryText}>{t('prashna.screen.castButton')}</Text>
        <View style={styles.castPrice}><Ionicons name="diamond-outline" size={13} color="#fff" />
          {Number.isFinite(displayedOriginalCost) && displayedOriginalCost > displayedCost ? <Text style={styles.originalPrice}>{displayedOriginalCost}</Text> : null}
          <Text style={styles.primaryText}>{displayedCost}</Text>
        </View>
      </View>}
    </TouchableOpacity>
  </>;

  return <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top']}>
    <View style={[styles.header, { borderBottomColor: colors.cardBorder }]}><TouchableOpacity onPress={() => navigation.goBack()}><Ionicons name="arrow-back" size={23} color={colors.text} /></TouchableOpacity><View><Text style={[styles.kicker, { color: colors.primary }]}>{t('prashna.screen.headerEyebrow')}</Text><Text style={[styles.headerTitle, { color: colors.text }]}>Prashna</Text></View></View>
    <Modal visible={showHowItWorks} transparent animationType="fade" statusBarTranslucent onRequestClose={() => setShowHowItWorks(false)}>
      <Pressable style={[styles.modalOverlay, { backgroundColor: colors.overlay }]} onPress={() => setShowHowItWorks(false)}>
        <Pressable style={[styles.howSheet, { backgroundColor: colors.surfaceRaised || colors.cardBackground, borderColor: colors.cardBorder }]} onPress={(event) => event.stopPropagation()}>
          <View style={styles.howHeader}>
            <View style={styles.howHeaderCopy}>
              <Text style={[styles.kicker, { color: colors.primary }]}>{t('prashna.how.eyebrow')}</Text>
              <Text style={[styles.howTitle, { color: colors.text }]}>{t('prashna.how.title')}</Text>
            </View>
            <TouchableOpacity onPress={() => setShowHowItWorks(false)} hitSlop={12} accessibilityRole="button" accessibilityLabel={t('prashna.screen.close')}>
              <Ionicons name="close" size={24} color={colors.textSecondary} />
            </TouchableOpacity>
          </View>
          <ScrollView contentContainerStyle={styles.howContent} showsVerticalScrollIndicator={false}>
            <Text style={[styles.howIntro, { color: colors.text }]}>{t('prashna.how.intro')}</Text>
            {[1, 2, 3, 4].map((step) => <View key={step} style={styles.howStep}>
              <View style={[styles.stepNumber, { backgroundColor: colors.primary }]}><Text style={styles.stepNumberText}>{step}</Text></View>
              <View style={styles.stepCopy}><Text style={[styles.stepTitle, { color: colors.text }]}>{t(`prashna.how.step${step}Title`)}</Text><Text style={[styles.stepBody, { color: colors.textSecondary }]}>{t(`prashna.how.step${step}Body`)}</Text></View>
            </View>)}
            <View style={[styles.howNote, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
              <Text style={[styles.stepTitle, { color: colors.text }]}>{t('prashna.how.recastTitle')}</Text>
              <Text style={[styles.stepBody, { color: colors.textSecondary }]}>{t('prashna.how.recastBody')}</Text>
            </View>
            <Text style={[styles.howLimit, { color: colors.textSecondary }]}>{t('prashna.how.limits')}</Text>
          </ScrollView>
          <TouchableOpacity onPress={() => setShowHowItWorks(false)} style={[styles.gotItButton, { backgroundColor: colors.primary }]}>
            <Text style={styles.gotItText}>{t('prashna.how.gotIt')}</Text>
          </TouchableOpacity>
        </Pressable>
      </Pressable>
    </Modal>
    <AnalysisCreditModal visible={showCreditModal} onClose={() => setShowCreditModal(false)}
      onConfirm={() => setShowCreditModal(false)}
      onGetCredits={() => { setShowCreditModal(false); navigation.navigate('Credits'); }}
      credits={gateCredits} cost={gateCost} canAfford={false}
      title={t('prashna.screen.moreCredits')}
      description={t('prashna.screen.creditBody', { cost: gateCost, credits: gateCredits })}
      getCreditsLabel={t('prashna.screen.getCredits')} cancelLabel={t('prashna.screen.cancel')} />
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">{result ? renderResult() : renderForm()}</ScrollView>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  container: { flex: 1 }, header: { padding: 15, flexDirection: 'row', gap: 14, alignItems: 'center', borderBottomWidth: StyleSheet.hairlineWidth },
  headerTitle: { fontSize: 20, fontWeight: '800' }, kicker: { fontSize: 10, fontWeight: '800', letterSpacing: .8 },
  content: { padding: 18, paddingBottom: 50 }, pageTitle: { fontSize: 25, lineHeight: 31, fontWeight: '800', marginBottom: 8 },
  brandLine: { fontSize: 10, lineHeight: 15, fontWeight: '900', letterSpacing: .65, marginBottom: 7 },
  lead: { fontSize: 14, lineHeight: 21, marginBottom: 6 },
  howLink: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 5, paddingVertical: 5, marginBottom: 12 },
  howLinkText: { fontSize: 14, fontWeight: '800', textDecorationLine: 'underline' },
  info: { borderRadius: 14, padding: 14, marginBottom: 8 },
  card: { borderWidth: 1, borderRadius: 14, padding: 14, marginTop: 12 }, cardTitle: { fontSize: 15, fontWeight: '800', marginBottom: 6 },
  body: { fontSize: 14, lineHeight: 21 }, label: { fontSize: 14, fontWeight: '700', marginTop: 17, marginBottom: 8 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 }, chip: { borderWidth: 1, borderRadius: 22, paddingHorizontal: 12, paddingVertical: 8 },
  hint: { fontSize: 12, lineHeight: 18, marginBottom: 7 }, questionList: { gap: 8 },
  questionOption: { borderWidth: 1, borderRadius: 13, padding: 12, flexDirection: 'row', alignItems: 'flex-start', gap: 9 },
  questionText: { flex: 1, fontSize: 14, lineHeight: 20, fontWeight: '600' },
  notice: { fontSize: 13, lineHeight: 20, marginTop: 14 }, error: { color: '#b91c1c', marginTop: 12, lineHeight: 19 },
  primary: { marginTop: 20, borderRadius: 14, minHeight: 50, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 14 }, primaryText: { color: '#fff', fontSize: 15, fontWeight: '800' },
  castButtonContent: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  castPrice: { flexDirection: 'row', alignItems: 'center', gap: 4 }, originalPrice: { color: 'rgba(255,255,255,.65)', textDecorationLine: 'line-through', fontSize: 12 },
  secondary: { marginTop: 12, borderWidth: 1, borderRadius: 14, minHeight: 48, alignItems: 'center', justifyContent: 'center' },
  roleLabel: { marginTop: 13, marginBottom: 4, fontSize: 12, fontWeight: '700' }, point: { fontSize: 14, lineHeight: 21, marginTop: 5 },
  confirmedQuestion: { fontSize: 20, lineHeight: 27, fontWeight: '700', marginTop: 5 }, meta: { fontSize: 12, lineHeight: 18, marginTop: 5, marginBottom: 14 },
  verdict: { borderWidth: 1, borderRadius: 16, padding: 16 }, verdictTitle: { fontSize: 22, lineHeight: 28, fontWeight: '800', marginBottom: 8 },
  meaning: { borderRadius: 14, padding: 14, marginTop: 12 }, limit: { fontSize: 12, lineHeight: 18, marginTop: 10 },
  workingButton: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 17, paddingVertical: 5 }, workingText: { fontSize: 13, fontWeight: '700' },
  technical: { borderWidth: 1, borderRadius: 13, padding: 13, marginTop: 5 }, tech: { fontSize: 12, lineHeight: 18, marginTop: 4 },
  fixedPlace: { borderWidth: 1, borderRadius: 12, padding: 13 },
  modalOverlay: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 18 },
  howSheet: { width: '100%', maxWidth: 500, maxHeight: '88%', borderWidth: 1, borderRadius: 22, overflow: 'hidden' },
  howHeader: { flexDirection: 'row', alignItems: 'flex-start', paddingHorizontal: 20, paddingTop: 20, paddingBottom: 12 },
  howHeaderCopy: { flex: 1, paddingRight: 12 }, howTitle: { fontSize: 26, lineHeight: 32, fontWeight: '800', marginTop: 3 },
  howContent: { paddingHorizontal: 20, paddingBottom: 16 }, howIntro: { fontSize: 15, lineHeight: 23, marginBottom: 18 },
  emphasis: { fontStyle: 'italic', fontWeight: '800' }, howStep: { flexDirection: 'row', alignItems: 'flex-start', gap: 11, marginBottom: 16 },
  stepNumber: { width: 25, height: 25, borderRadius: 13, alignItems: 'center', justifyContent: 'center', marginTop: 1 },
  stepNumberText: { color: '#fff', fontSize: 12, fontWeight: '900' }, stepCopy: { flex: 1 },
  stepTitle: { fontSize: 14, lineHeight: 19, fontWeight: '800', marginBottom: 3 }, stepBody: { fontSize: 13, lineHeight: 20 },
  howNote: { borderWidth: 1, borderRadius: 13, padding: 13, marginTop: 2 }, howLimit: { fontSize: 12, lineHeight: 18, marginTop: 14 },
  gotItButton: { minHeight: 48, alignItems: 'center', justifyContent: 'center', marginHorizontal: 20, marginBottom: 18, borderRadius: 13 },
  gotItText: { color: '#fff', fontSize: 15, fontWeight: '800' },
});
