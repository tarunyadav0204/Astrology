import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { storage } from '../../services/storage';
import { prashnaAPI } from '../../services/api';
import LocationPicker from '../LocationPicker';
import {
  detectQuestionPlace,
  loadSavedQuestionPlace,
  saveQuestionPlace,
} from '../../utils/questionPlace';

const CATEGORIES = [
  { id: 'general', house: 11 },
  { id: 'career', house: 10 },
  { id: 'marriage', house: 7 },
  { id: 'wealth', house: 2 },
  { id: 'health', house: 6 },
  { id: 'property', house: 4 },
  { id: 'children', house: 5 },
  { id: 'education', house: 5 },
  { id: 'travel', house: 9 },
  { id: 'legal', house: 6 },
];

const pad = (value) => String(value).padStart(2, '0');

const nowStamp = () => {
  const now = new Date();
  return {
    date: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`,
    time: `${pad(now.getHours())}:${pad(now.getMinutes())}`,
  };
};

const verdictTone = (answer, colors) => {
  if (answer === 'yes') return { bg: 'rgba(22, 163, 74, 0.14)', border: 'rgba(22, 163, 74, 0.35)', text: '#15803d' };
  if (answer === 'no') return { bg: 'rgba(220, 38, 38, 0.12)', border: 'rgba(220, 38, 38, 0.32)', text: '#b91c1c' };
  return { bg: colors.surfaceMuted || 'rgba(245, 158, 11, 0.14)', border: 'rgba(180, 83, 9, 0.32)', text: '#b45309' };
};

const CONFIDENCE_LABEL = { high: 'Clear', medium: 'Fairly clear', low: 'Tentative' };

const GATE_STATUS = { pass: 'pass', warn: 'caution', block: 'block' };

const tajikaTechnicalLine = (result) => {
  const direct = result?.tajika?.direct || {};
  const you = result?.significators?.lagnesha?.planet;
  const matter = result?.significators?.karyesha?.planet;
  const names = you && matter ? `${you} and ${matter}` : 'the two planets';
  const yoga = direct.type;
  if (!yoga || yoga === 'None') {
    return `Tajika yoga: none. ${names} are not applying to an exact aspect within orb.`;
  }
  if (yoga === 'SamePlanet') {
    return `Tajika yoga: same planet (${you || 'one graha'}) stands for both you and the matter.`;
  }
  const parts = [`Tajika yoga: ${yoga}`];
  if (direct.aspect && direct.aspect !== 'None') parts.push(direct.aspect);
  if (direct.remaining_degrees != null) parts.push(`${direct.remaining_degrees}° remaining`);
  if (direct.detail) parts.push(direct.detail);
  return parts.join(' · ');
};

export default function PrashnaScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const [birthData, setBirthData] = useState(route.params?.birthData || null);
  const initial = nowStamp();

  const [question, setQuestion] = useState('');
  const [category, setCategory] = useState('general');
  const [date, setDate] = useState(initial.date);
  const [time, setTime] = useState(initial.time);
  const [place, setPlace] = useState(null);
  const [placeLoading, setPlaceLoading] = useState(true);
  const [showLocationPicker, setShowLocationPicker] = useState(false);
  const [horaryNumber, setHoraryNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [showTechnical, setShowTechnical] = useState(false);

  const applyPlace = (next) => {
    if (!next) return;
    setPlace(next);
    saveQuestionPlace(next);
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const detected = await detectQuestionPlace();
        if (!cancelled && detected) {
          applyPlace(detected);
          return;
        }
        const saved = await loadSavedQuestionPlace();
        if (!cancelled && saved) {
          applyPlace(saved);
        }
      } finally {
        if (!cancelled) setPlaceLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (birthData?.name) return;
    let cancelled = false;
    (async () => {
      try {
        let data = await storage.getBirthDetails();
        if (!data) {
          const profiles = await storage.getBirthProfiles();
          if (profiles?.length) data = profiles.find((profile) => profile.relation === 'self') || profiles[0];
        }
        if (!cancelled && data?.name) setBirthData(data);
      } catch {
        // Birth profile is optional for Prashna; the question place is what matters.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [birthData]);

  const placeLabel = place?.name || t('prashna.placePlaceholder', 'Select the place of asking');

  const canCast = useMemo(() => {
    const lat = parseFloat(place?.latitude);
    const lon = parseFloat(place?.longitude);
    return question.trim().length >= 3 && Number.isFinite(lat) && Number.isFinite(lon);
  }, [question, place]);

  const useCurrentPlace = async () => {
    setPlaceLoading(true);
    setError('');
    try {
      const detected = await detectQuestionPlace();
      if (!detected) {
        setError(t('prashna.placeDetectError', 'Could not detect your current city. Search and select it.'));
        setShowLocationPicker(true);
        return;
      }
      applyPlace(detected);
    } finally {
      setPlaceLoading(false);
    }
  };

  const useNow = () => {
    const stamp = nowStamp();
    setDate(stamp.date);
    setTime(stamp.time);
  };

  const castQuestion = async () => {
    if (!canCast || loading) return;
    setLoading(true);
    setError('');
    try {
      const number = horaryNumber.trim() ? parseInt(horaryNumber.trim(), 10) : null;
      if (number != null && (number < 1 || number > 249 || Number.isNaN(number))) {
        setError(t('prashna.numberError', 'Horary number must be between 1 and 249.'));
        setLoading(false);
        return;
      }
      const response = await prashnaAPI.analyze({
        question: question.trim(),
        category,
        date,
        time,
        latitude: parseFloat(place.latitude),
        longitude: parseFloat(place.longitude),
        timezone: '',
        place: place.name || '',
        horary_number: number,
        name: birthData?.name || 'Prashna',
      });
      setResult(response?.data || response);
    } catch (err) {
      const detail = err?.response?.data?.detail || err?.message;
      setError(detail || t('prashna.loadError', 'Could not cast the Prashna chart.'));
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setResult(null);
    setError('');
    setShowTechnical(false);
    const stamp = nowStamp();
    setDate(stamp.date);
    setTime(stamp.time);
  };

  const renderHeader = () => (
    <View style={[styles.header, { backgroundColor: colors.cardBackground, borderBottomColor: colors.cardBorder }]}>
      <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn} accessibilityLabel={t('premiumUi.common.goBack', 'Back')}>
        <Ionicons name="arrow-back" size={22} color={colors.text} />
      </TouchableOpacity>
      <View style={styles.headerCopy}>
        <Text style={[styles.eyebrow, { color: colors.primary }]}>{t('prashna.eyebrow', 'Question chart')}</Text>
        <Text style={[styles.title, { color: colors.text }]}>{t('prashna.title', 'Prashna')}</Text>
      </View>
    </View>
  );

  const renderForm = () => (
    <>
      <Text style={[styles.lead, { color: colors.textSecondary }]}>
        {t('prashna.lead', 'The chart is cast for this question’s time and place, not your birth chart. Chat can use the same engine later.')}
      </Text>

      <Text style={[styles.label, { color: colors.text }]}>{t('prashna.questionLabel', 'Your question')}</Text>
      <TextInput
        value={question}
        onChangeText={setQuestion}
        placeholder={t('prashna.questionPlaceholder', 'Ask one clear question')}
        placeholderTextColor={colors.textSecondary}
        multiline
        style={[styles.input, styles.questionInput, { color: colors.text, borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}
      />

      <Text style={[styles.label, { color: colors.text }]}>{t('prashna.topicLabel', 'Topic')}</Text>
      <View style={styles.chipWrap}>
        {CATEGORIES.map((item) => {
          const selected = category === item.id;
          return (
            <TouchableOpacity
              key={item.id}
              onPress={() => setCategory(item.id)}
              style={[
                styles.chip,
                {
                  backgroundColor: selected ? colors.primary : colors.cardBackground,
                  borderColor: selected ? colors.primary : colors.cardBorder,
                },
              ]}
            >
              <Text style={[styles.chipText, { color: selected ? colors.onPrimary || '#fff' : colors.text }]}>
                {t(`prashna.topics.${item.id}`, item.id)}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <View style={styles.row}>
        <View style={styles.rowItem}>
          <Text style={[styles.label, { color: colors.text }]}>{t('prashna.date', 'Date')}</Text>
          <TextInput
            value={date}
            onChangeText={setDate}
            placeholder="YYYY-MM-DD"
            placeholderTextColor={colors.textSecondary}
            style={[styles.input, { color: colors.text, borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}
          />
        </View>
        <View style={styles.rowItem}>
          <Text style={[styles.label, { color: colors.text }]}>{t('prashna.time', 'Time')}</Text>
          <TextInput
            value={time}
            onChangeText={setTime}
            placeholder="HH:MM"
            placeholderTextColor={colors.textSecondary}
            style={[styles.input, { color: colors.text, borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}
          />
        </View>
      </View>
      <TouchableOpacity onPress={useNow} style={styles.linkBtn}>
        <Ionicons name="time-outline" size={16} color={colors.primary} />
        <Text style={[styles.linkText, { color: colors.primary }]}>{t('prashna.useNow', 'Use current time')}</Text>
      </TouchableOpacity>

      <Text style={[styles.label, { color: colors.text }]}>{t('prashna.place', 'Place of asking')}</Text>
      <TouchableOpacity
        onPress={() => setShowLocationPicker(true)}
        style={[styles.placeCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}
      >
        <Ionicons name="location-outline" size={18} color={colors.primary} />
        <Text style={[styles.placeText, { color: colors.text }]}>
          {placeLoading ? t('prashna.detectingPlace', 'Detecting current city…') : placeLabel}
        </Text>
        <Text style={[styles.changeText, { color: colors.primary }]}>{t('prashna.changePlace', 'Change')}</Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={useCurrentPlace} style={styles.linkBtn} disabled={placeLoading}>
        <Ionicons name="navigate-outline" size={16} color={colors.primary} />
        <Text style={[styles.linkText, { color: colors.primary }]}>{t('prashna.useCurrentPlace', 'Use current location')}</Text>
      </TouchableOpacity>
      <Text style={[styles.hint, { color: colors.textSecondary }]}>
        {t('prashna.placeHint', 'Prashna is cast for where the question is asked, not the birth place.')}
      </Text>

      <Text style={[styles.label, { color: colors.text }]}>{t('prashna.numberLabel', 'KP number (optional)')}</Text>
      <TextInput
        value={horaryNumber}
        onChangeText={setHoraryNumber}
        keyboardType="number-pad"
        placeholder={t('prashna.numberPlaceholder', '1–249')}
        placeholderTextColor={colors.textSecondary}
        style={[styles.input, { color: colors.text, borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}
      />
      <Text style={[styles.hint, { color: colors.textSecondary }]}>
        {t('prashna.numberHint', 'Optional KP overlay. It does not replace the question-time chart.')}
      </Text>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <TouchableOpacity
        onPress={castQuestion}
        disabled={!canCast || loading}
        style={[styles.castBtn, { backgroundColor: colors.primary, opacity: !canCast || loading ? 0.55 : 1 }]}
      >
        {loading ? (
          <ActivityIndicator color={colors.onPrimary || '#fff'} />
        ) : (
          <Text style={[styles.castText, { color: colors.onPrimary || '#fff' }]}>{t('prashna.cast', 'Cast Prashna')}</Text>
        )}
      </TouchableOpacity>
    </>
  );

  const renderResult = () => {
    if (!result) return null;
    const verdict = result.verdict || {};
    const explanation = result.explanation || {};
    const tone = verdictTone(verdict.answer, colors);
    const snapshot = result.chart_snapshot || {};
    const people = [
      explanation.you ? { key: 'you', ...explanation.you } : null,
      explanation.matter ? { key: 'matter', ...explanation.matter } : null,
      explanation.moon ? { key: 'moon', ...explanation.moon } : null,
    ].filter(Boolean);
    const confidenceLabel =
      explanation.confidence_label || CONFIDENCE_LABEL[verdict.confidence] || '';
    return (
      <>
        <View style={[styles.verdictCard, { backgroundColor: tone.bg, borderColor: tone.border }]}>
          <Text style={[styles.verdictLabel, { color: tone.text }]}>
            {explanation.headline || verdict.label || verdict.answer}
          </Text>
          {confidenceLabel || explanation.confidence_why ? (
            <Text style={[styles.confidence, { color: colors.textSecondary }]}>
              {confidenceLabel}
              {explanation.confidence_why ? ` — ${explanation.confidence_why}` : ''}
            </Text>
          ) : null}
        </View>

        <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('prashna.resultWhy', 'Why this answer')}</Text>
        <Text style={[styles.body, { color: colors.text }]}>{explanation.why || verdict.summary}</Text>

        {people.length ? (
          <>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('prashna.resultCast', 'Who stands for what')}</Text>
            {people.map((row) => (
              <View key={row.key} style={[styles.sigRow, { borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}>
                <Text style={[styles.sigPlanet, { color: colors.text }]}>{row.title}</Text>
                <Text style={[styles.sigMeta, { color: colors.textSecondary }]}>{row.body}</Text>
              </View>
            ))}
          </>
        ) : null}

        {explanation.readable ? (
          <>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('prashna.resultFit', 'Is this chart fit to read?')}</Text>
            <Text style={[styles.body, { color: colors.text }]}>{explanation.readable}</Text>
          </>
        ) : null}

        {explanation.timing ? (
          <>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('prashna.timing', 'Timing')}</Text>
            <Text style={[styles.body, { color: colors.text }]}>{explanation.timing}</Text>
          </>
        ) : null}

        {explanation.setup ? (
          <Text style={[styles.setup, { color: colors.textSecondary }]}>{explanation.setup}</Text>
        ) : null}

        {explanation.arudha ? <Text style={[styles.body, { color: colors.textSecondary }]}>{explanation.arudha}</Text> : null}
        {explanation.kp ? <Text style={[styles.body, { color: colors.textSecondary }]}>{explanation.kp}</Text> : null}

        {explanation.caveat ? (
          <View style={[styles.noteCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
            <Text style={[styles.body, { color: colors.text }]}>{explanation.caveat}</Text>
          </View>
        ) : null}

        <TouchableOpacity onPress={() => setShowTechnical((open) => !open)} style={styles.linkBtn}>
          <Ionicons name={showTechnical ? 'chevron-up' : 'chevron-down'} size={16} color={colors.primary} />
          <Text style={[styles.linkText, { color: colors.primary }]}>
            {showTechnical
              ? t('prashna.hideTechnical', 'Hide technical notes')
              : t('prashna.showTechnical', 'Show technical notes')}
          </Text>
        </TouchableOpacity>

        {showTechnical ? (
          <View style={[styles.techBox, { borderColor: colors.cardBorder }]}>
            <Text style={[styles.techLine, { color: colors.textSecondary }]}>
              {result.clock?.date} {result.clock?.time} · {result.clock?.place || placeLabel}
            </Text>
            <Text style={[styles.techLine, { color: colors.textSecondary }]}>
              {t('prashna.lagna', 'Lagna')}: {snapshot.ascendant?.sign_name} {snapshot.ascendant?.degree}°
            </Text>
            <Text style={[styles.techLine, { color: colors.textSecondary }]}>
              {tajikaTechnicalLine(result)}
            </Text>
            {(result.gates || []).map((gate) => (
              <Text key={gate.id} style={[styles.techLine, { color: colors.textSecondary }]}>
                {t('prashna.gates', 'Readability')}: {GATE_STATUS[gate.status] || gate.status} — {gate.label}
              </Text>
            ))}
          </View>
        ) : null}

        <TouchableOpacity onPress={resetForm} style={[styles.secondaryBtn, { borderColor: colors.cardBorder }]}>
          <Text style={[styles.secondaryText, { color: colors.text }]}>{t('prashna.newQuestion', 'New question')}</Text>
        </TouchableOpacity>
      </>
    );
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top']}>
      {renderHeader()}
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          {result ? renderResult() : renderForm()}
        </ScrollView>
      </KeyboardAvoidingView>
      {showLocationPicker ? (
        <LocationPicker
          onLocationSelect={(selected) => {
            applyPlace({
              latitude: selected.latitude,
              longitude: selected.longitude,
              name: selected.name,
              source: 'manual',
            });
            setShowLocationPicker(false);
          }}
          onClose={() => setShowLocationPicker(false)}
        />
      ) : null}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  flex: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backBtn: { width: 36, height: 36, alignItems: 'center', justifyContent: 'center' },
  headerCopy: { marginLeft: 8, flex: 1 },
  eyebrow: { fontSize: 11, letterSpacing: 0.6, textTransform: 'uppercase' },
  title: { fontSize: 20, fontWeight: '700' },
  content: { padding: 18, paddingBottom: 48 },
  lead: { fontSize: 14, lineHeight: 20, marginBottom: 18 },
  label: { fontSize: 13, fontWeight: '600', marginBottom: 8, marginTop: 12 },
  input: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 11,
    fontSize: 15,
  },
  questionInput: { minHeight: 92, textAlignVertical: 'top' },
  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { borderWidth: 1, borderRadius: 20, paddingHorizontal: 12, paddingVertical: 7 },
  chipText: { fontSize: 13, fontWeight: '600', textTransform: 'capitalize' },
  row: { flexDirection: 'row', gap: 10 },
  rowItem: { flex: 1 },
  linkBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 8 },
  linkText: { fontSize: 13, fontWeight: '600' },
  placeCard: { flexDirection: 'row', alignItems: 'center', gap: 8, borderWidth: 1, borderRadius: 12, padding: 12 },
  placeText: { flex: 1, fontSize: 14 },
  changeText: { fontSize: 13, fontWeight: '700' },
  hint: { fontSize: 12, lineHeight: 18, marginTop: 6 },
  error: { color: '#b91c1c', marginTop: 12, fontSize: 13 },
  castBtn: { marginTop: 22, borderRadius: 14, paddingVertical: 14, alignItems: 'center' },
  castText: { fontSize: 16, fontWeight: '700' },
  verdictCard: { borderWidth: 1, borderRadius: 16, padding: 16, marginBottom: 8 },
  verdictLabel: { fontSize: 22, fontWeight: '800', lineHeight: 28 },
  confidence: { marginTop: 8, fontSize: 13, lineHeight: 19 },
  summary: { marginTop: 10, fontSize: 15, lineHeight: 22 },
  noteCard: { borderWidth: 1, borderRadius: 12, padding: 14, marginTop: 16 },
  techBox: { borderWidth: 1, borderRadius: 12, padding: 12, marginTop: 8, gap: 6 },
  techLine: { fontSize: 12, lineHeight: 18 },
  sectionTitle: { marginTop: 20, marginBottom: 8, fontSize: 16, fontWeight: '700' },
  body: { fontSize: 15, lineHeight: 23 },
  setup: { fontSize: 13, lineHeight: 20, marginTop: 16 },
  sigRow: { borderWidth: 1, borderRadius: 12, padding: 12, marginBottom: 8 },
  sigPlanet: { fontSize: 16, fontWeight: '700' },
  sigMeta: { marginTop: 4, fontSize: 13 },
  gateRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, marginBottom: 8 },
  gateDot: { width: 8, height: 8, borderRadius: 4, marginTop: 6 },
  gateText: { flex: 1, fontSize: 13, lineHeight: 19 },
  secondaryBtn: { marginTop: 24, borderWidth: 1, borderRadius: 14, paddingVertical: 13, alignItems: 'center' },
  secondaryText: { fontSize: 15, fontWeight: '700' },
});
