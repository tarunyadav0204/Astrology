import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  FlatList,
  ScrollView,
  ActivityIndicator,
  useWindowDimensions,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { useTheme } from '../../context/ThemeContext';
import { kpAPI } from '../../services/api';
import { trackEvent } from '../../utils/analytics';

const CACHE_PREFIX = 'kp_today_home_v2:';
const MAX_PAGES = 5;
const BULLETS_PER_PAGE = 4;

const TONE_LABELS = {
  supportive: 'Favourable',
  mixed: 'Mixed',
  challenging: 'Under pressure',
  neutral: 'Steady',
};

const TONE_UI = {
  light: {
    supportive: { accent: '#15803d', pillBg: '#15803d', pillText: '#ffffff' },
    mixed: { accent: '#0369a1', pillBg: '#0369a1', pillText: '#ffffff' },
    challenging: { accent: '#be123c', pillBg: '#be123c', pillText: '#ffffff' },
    neutral: { accent: '#475569', pillBg: '#475569', pillText: '#ffffff' },
  },
  dark: {
    supportive: { accent: '#22c55e', pillBg: '#15803d', pillText: '#ffffff' },
    mixed: { accent: '#38bdf8', pillBg: '#0369a1', pillText: '#ffffff' },
    challenging: { accent: '#fb7185', pillBg: '#be123c', pillText: '#ffffff' },
    neutral: { accent: '#e2e8f0', pillBg: '#64748b', pillText: '#ffffff' },
  },
};

function toneUi(tone, isDark) {
  const palette = isDark ? TONE_UI.dark : TONE_UI.light;
  return palette[tone] || palette.neutral;
}

function formatLocalDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function formatLocalTime(d) {
  const h = String(d.getHours()).padStart(2, '0');
  const m = String(d.getMinutes()).padStart(2, '0');
  return `${h}:${m}`;
}

function formatShortDate(d) {
  try {
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  } catch (_) {
    return formatLocalDate(d);
  }
}

function birthId(birthDetails) {
  return birthDetails?.id || birthDetails?.birth_chart_id || birthDetails?.name || 'anon';
}

function cacheKey(birthDetails) {
  return `${CACHE_PREFIX}${birthId(birthDetails)}:${formatLocalDate(new Date())}`;
}

function isTechnicalLabel(label) {
  const s = String(label || '').trim();
  if (!s) return true;
  return /combined activated|life themes|fructif|significat|house\s*\d+/i.test(s);
}

function humanHeadline(selfTheme, quiet) {
  if (quiet) return 'A quieter day';
  const label = String(selfTheme?.label || '').trim();
  if (label && !isTechnicalLabel(label)) return label;
  const summary = String(selfTheme?.summary || '').trim();
  if (summary) {
    const first = summary.split(/[.!?]/)[0].trim();
    if (first.length >= 12 && first.length <= 72) return first;
    if (summary.length <= 72) return summary;
    return `${summary.slice(0, 69).trim()}…`;
  }
  return 'Your day is ready';
}

function buildReaderPages(todayBlock) {
  const houses = todayBlock?.houses_giving_results || [];
  const selfTheme = (todayBlock?.manifestations || []).find(
    (item) => (item.subject || 'self') === 'self'
  );
  const tone = selfTheme?.outcome_tone || houses[0]?.tone || 'neutral';
  const summary = String(selfTheme?.summary || '').trim();
  const possibilities = Array.isArray(selfTheme?.possibilities)
    ? selfTheme.possibilities.map((p) => String(p || '').trim()).filter(Boolean)
    : [];
  const headline = humanHeadline(selfTheme, !houses.length);
  const quiet = !houses.length;

  if (quiet) {
    return {
      quiet: true,
      tone: 'neutral',
      headline,
      teaser: 'Not much is lined up to give clear results today. You can still check this hour in KP Predictions.',
      pages: [
        {
          id: 'quiet',
          showSummary: true,
          summary:
            'Today looks quieter for clear, fructifying results. That can change through the day as ruling planets and fine dashas shift.',
          bullets: [
            'Check back later, or open KP Predictions for this hour’s sharper timing.',
            'A quiet day does not mean nothing happens — only that fewer houses are strongly confirmed right now.',
          ],
        },
      ],
    };
  }

  let bullets = [...possibilities];
  if (!bullets.length && summary) bullets = [summary];
  if (!bullets.length) {
    bullets = [
      'Several life themes look able to move today. Open full KP Predictions for timing detail.',
    ];
  }

  const capped = bullets.slice(0, MAX_PAGES * BULLETS_PER_PAGE);
  const pages = [];
  for (let i = 0; i < capped.length && pages.length < MAX_PAGES; i += BULLETS_PER_PAGE) {
    pages.push({
      id: `page-${pages.length}`,
      showSummary: pages.length === 0 && !!summary,
      summary,
      bullets: capped.slice(i, i + BULLETS_PER_PAGE),
    });
  }

  return {
    quiet: false,
    tone,
    headline,
    teaser: summary || bullets[0] || 'Your predictions for today are ready.',
    pages,
  };
}

function KpTodayReaderSheet({
  visible,
  reader,
  loading,
  onClose,
  onOpenKp,
}) {
  const { theme, colors } = useTheme();
  const insets = useSafeAreaInsets();
  const { width: windowWidth } = useWindowDimensions();
  const isDark = theme === 'dark';
  const [pageIndex, setPageIndex] = useState(0);
  const surface = isDark ? '#1a1030' : '#FFFDFC';
  const tile = isDark ? '#241540' : '#FFF7ED';
  const border = isDark ? 'rgba(255,255,255,0.16)' : '#FED7AA';
  const bodyText = isDark ? '#f8fafc' : '#0f172a';
  const mutedText = isDark ? '#cbd5e1' : '#44403c';
  const tone = toneUi(reader?.tone || 'neutral', isDark);
  const pages = reader?.pages || [];
  // Sheet is width 100% with overlay pad 16 and maxWidth 440 — page must match that exactly for paging.
  const pageWidth = Math.min(windowWidth - 32, 440);
  const cardPad = 18;

  useEffect(() => {
    if (visible) setPageIndex(0);
  }, [visible, reader?.headline]);

  if (!visible) return null;

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose} statusBarTranslucent>
      <View style={styles.overlay}>
        <TouchableOpacity style={StyleSheet.absoluteFill} activeOpacity={1} onPress={onClose} />
        <View
          style={[
            styles.sheet,
            {
              width: pageWidth,
              backgroundColor: surface,
              borderColor: border,
              paddingBottom: Math.max(insets.bottom, 14),
            },
          ]}
        >
          <View style={styles.handle} />
          <View style={styles.sheetHeader}>
            <View style={{ flex: 1, minWidth: 0 }}>
              <Text style={[styles.sheetEyebrow, { color: isDark ? '#fdba74' : '#ea580c' }]}>
                Today · {formatShortDate(new Date())}
              </Text>
              <Text style={[styles.sheetTitle, { color: bodyText }]} numberOfLines={2}>
                {reader?.headline || 'Your day is ready'}
              </Text>
            </View>
            <View style={[styles.tonePill, { backgroundColor: tone.pillBg }]}>
              <Text style={[styles.tonePillText, { color: tone.pillText }]}>
                {TONE_LABELS[reader?.tone] || 'Steady'}
              </Text>
            </View>
            <TouchableOpacity
              onPress={onClose}
              style={[styles.closeBtn, { backgroundColor: tile }]}
              accessibilityLabel="Close"
            >
              <Ionicons name="close" size={20} color={bodyText} />
            </TouchableOpacity>
          </View>

          {loading && !pages.length ? (
            <View style={styles.sheetLoading}>
              <ActivityIndicator color={colors.primary} />
              <Text style={[styles.sheetLoadingText, { color: mutedText }]}>
                Writing today’s predictions…
              </Text>
            </View>
          ) : (
            <>
              <FlatList
                horizontal
                data={pages}
                keyExtractor={(item) => item.id}
                style={{ width: pageWidth }}
                showsHorizontalScrollIndicator={false}
                pagingEnabled
                decelerationRate="fast"
                bounces={false}
                nestedScrollEnabled
                getItemLayout={(_, index) => ({
                  length: pageWidth,
                  offset: pageWidth * index,
                  index,
                })}
                onMomentumScrollEnd={(e) => {
                  const next = Math.round(e.nativeEvent.contentOffset.x / pageWidth);
                  const clamped = Math.max(0, Math.min(next, pages.length - 1));
                  if (clamped !== pageIndex) {
                    setPageIndex(clamped);
                    trackEvent('kp_today_reader_swipe', { page: clamped, pages: pages.length });
                  }
                }}
                renderItem={({ item, index }) => (
                  <View style={[styles.pageSlot, { width: pageWidth, paddingHorizontal: cardPad }]}>
                    <View
                      style={[
                        styles.longCard,
                        {
                          backgroundColor: tile,
                          borderColor: border,
                          borderLeftColor: tone.accent,
                        },
                      ]}
                    >
                      <ScrollView
                        showsVerticalScrollIndicator={false}
                        contentContainerStyle={styles.longCardScroll}
                      >
                        <Text style={[styles.pageMeta, { color: mutedText }]}>
                          {index + 1} of {pages.length}
                        </Text>
                        {item.showSummary && item.summary ? (
                          <Text style={[styles.summaryText, { color: mutedText }]}>{item.summary}</Text>
                        ) : null}
                        <Text style={[styles.sectionLabel, { color: tone.accent }]}>
                          What may unfold
                        </Text>
                        {(item.bullets || []).map((line) => (
                          <View key={line} style={styles.bulletRow}>
                            <View style={[styles.dot, { backgroundColor: tone.accent }]} />
                            <Text style={[styles.bulletText, { color: bodyText }]}>{line}</Text>
                          </View>
                        ))}
                      </ScrollView>
                    </View>
                  </View>
                )}
              />
              {pages.length > 1 ? (
                <View style={styles.dots}>
                  {pages.map((p, i) => (
                    <View
                      key={p.id}
                      style={[
                        styles.dotPage,
                        {
                          backgroundColor:
                            i === pageIndex ? tone.accent : isDark ? 'rgba(255,255,255,0.25)' : '#cbd5e1',
                        },
                      ]}
                    />
                  ))}
                </View>
              ) : null}
            </>
          )}

          <View style={[styles.footer, { borderTopColor: border }]}>
            <TouchableOpacity
              style={[styles.primaryBtn, { backgroundColor: isDark ? '#ea580c' : colors.primary }]}
              onPress={() => onOpenKp?.('today')}
              activeOpacity={0.9}
            >
              <Text style={styles.primaryBtnText}>Open KP Predictions</Text>
              <Ionicons name="arrow-forward" size={16} color="#fff" />
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

/**
 * Home entry + full-prediction reader popup for KP Today.
 */
export default function KpTodayCarousel({ birthDetails, onOpenKp }) {
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const requestIdRef = useRef(0);
  const viewedRef = useRef(false);
  const hasDataRef = useRef(false);
  const skipFocusRefreshRef = useRef(true);
  const birthDetailsRef = useRef(birthDetails);
  birthDetailsRef.current = birthDetails;

  const birthKey = useMemo(() => {
    if (!birthDetails) return '';
    return [
      birthId(birthDetails),
      String(birthDetails.date || ''),
      String(birthDetails.time || ''),
      String(birthDetails.latitude ?? ''),
      String(birthDetails.longitude ?? ''),
    ].join('|');
  }, [
    birthDetails?.id,
    birthDetails?.birth_chart_id,
    birthDetails?.name,
    birthDetails?.date,
    birthDetails?.time,
    birthDetails?.latitude,
    birthDetails?.longitude,
  ]);

  const load = useCallback(async () => {
    const details = birthDetailsRef.current;
    if (!details?.date || !details?.time || details.latitude == null || details.longitude == null) {
      setLoading(false);
      setError('Birth details incomplete.');
      return;
    }

    const requestId = ++requestIdRef.current;
    const key = cacheKey(details);

    try {
      const cachedRaw = await AsyncStorage.getItem(key);
      if (cachedRaw && requestId === requestIdRef.current) {
        const cached = JSON.parse(cachedRaw);
        if (cached?.today) {
          setData(cached);
          hasDataRef.current = true;
          setLoading(false);
          setError(null);
        }
      }
    } catch (_) {
      /* ignore */
    }

    if (!hasDataRef.current) setLoading(true);
    try {
      const now = new Date();
      const birthDate = String(details.date).split('T')[0];
      let birthTime = String(details.time);
      if (birthTime.includes('T')) birthTime = birthTime.split('T')[1];
      birthTime = birthTime.slice(0, 5);

      const response = await kpAPI.getFructification({
        birth_date: birthDate,
        birth_time: birthTime,
        latitude: details.latitude,
        longitude: details.longitude,
        timezone: '',
        as_of_date: formatLocalDate(now),
        as_of_time: formatLocalTime(now),
        language: 'en',
        synthesize: true,
      });

      if (requestId !== requestIdRef.current) return;
      if (response.data?.success && response.data?.data) {
        const payload = response.data.data;
        setData(payload);
        hasDataRef.current = true;
        setError(null);
        try {
          await AsyncStorage.setItem(key, JSON.stringify(payload));
        } catch (_) {
          /* ignore */
        }
      } else if (!hasDataRef.current) {
        setError(response.data?.detail || 'Could not load today’s predictions.');
      }
    } catch (e) {
      if (requestId !== requestIdRef.current) return;
      if (!hasDataRef.current) setError(e.message || 'Could not load today’s predictions.');
    } finally {
      if (requestId === requestIdRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!birthKey) return undefined;
    viewedRef.current = false;
    hasDataRef.current = false;
    setData(null);
    setError(null);
    load();
    return () => {
      requestIdRef.current += 1;
    };
  }, [birthKey, load]);

  useFocusEffect(
    useCallback(() => {
      if (skipFocusRefreshRef.current) {
        skipFocusRefreshRef.current = false;
        return undefined;
      }
      if (hasDataRef.current) load();
      return undefined;
    }, [load])
  );

  const reader = useMemo(() => buildReaderPages(data?.today), [data?.today]);

  useEffect(() => {
    if (!data || viewedRef.current) return;
    viewedRef.current = true;
    trackEvent(reader.quiet ? 'kp_today_carousel_quiet_day_view' : 'kp_today_carousel_view', {
      quiet: reader.quiet,
      page_count: reader.pages.length,
    });
  }, [data, reader.quiet, reader.pages.length]);

  const openSheet = useCallback(() => {
    trackEvent('kp_today_reader_open', { quiet: reader.quiet });
    setSheetOpen(true);
  }, [reader.quiet]);

  const closeSheet = useCallback(() => {
    setSheetOpen(false);
  }, []);

  const openKp = useCallback(
    (scope = 'today') => {
      trackEvent('kp_today_carousel_cta_open_kp', { scope, source: 'reader' });
      setSheetOpen(false);
      onOpenKp?.(scope);
    },
    [onOpenKp]
  );

  if (!birthDetails?.date) return null;

  const tone = toneUi(reader.tone, isDark);
  const entryTitle = reader.quiet ? 'A quieter day' : 'Your day is ready';
  const entryToneLine = reader.quiet
    ? 'Fewer clear results confirmed right now'
    : `${TONE_LABELS[reader.tone] || 'Steady'} · ${formatShortDate(new Date())}`;

  return (
    <>
      <TouchableOpacity
        activeOpacity={0.88}
        onPress={openSheet}
        disabled={loading && !data}
        style={[
          styles.entryShell,
          {
            borderColor: isDark ? 'rgba(253,186,116,0.45)' : '#FDBA74',
            backgroundColor: colors.surface,
          },
        ]}
        accessibilityRole="button"
        accessibilityLabel="Read today’s predictions"
      >
        <LinearGradient
          colors={isDark ? ['#31145A', '#22113B'] : ['#FFF7ED', '#FFFBEB']}
          style={styles.entryGradient}
        >
          {loading && !data ? (
            <View style={styles.entryLoading}>
              <ActivityIndicator size="small" color={colors.primary} />
              <Text style={[styles.entrySubtitle, { color: colors.textSecondary }]}>
                Preparing today’s predictions…
              </Text>
            </View>
          ) : error && !data ? (
            <View>
              <Text style={[styles.entryTitle, { color: colors.text }]}>Today’s predictions</Text>
              <Text style={[styles.entrySubtitle, { color: colors.textSecondary }]}>{error}</Text>
              <TouchableOpacity onPress={load} style={styles.retry}>
                <Text style={[styles.entryCtaText, { color: colors.primary }]}>Retry</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              <View style={styles.entryHeader}>
                <View style={[styles.entryIcon, { backgroundColor: `${tone.accent}22` }]}>
                  <Ionicons name="sunny-outline" size={20} color={tone.accent} />
                </View>
                <View style={{ flex: 1, minWidth: 0 }}>
                  <Text style={[styles.entryTitle, { color: colors.text }]}>{entryTitle}</Text>
                  <Text style={[styles.entrySubtitle, { color: colors.textSecondary }]}>
                    {entryToneLine}
                  </Text>
                </View>
                <View style={[styles.tonePill, { backgroundColor: tone.pillBg }]}>
                  <Text style={[styles.tonePillText, { color: tone.pillText }]}>
                    {TONE_LABELS[reader.tone] || 'Steady'}
                  </Text>
                </View>
              </View>
              <Text numberOfLines={2} style={[styles.entryTeaser, { color: colors.text }]}>
                {reader.teaser}
              </Text>
              <View style={styles.entryCta}>
                <Text style={[styles.entryCtaText, { color: isDark ? '#fdba74' : '#ea580c' }]}>
                  Read today’s predictions
                </Text>
                <Ionicons name="arrow-forward" size={17} color={isDark ? '#fdba74' : '#ea580c'} />
              </View>
            </>
          )}
        </LinearGradient>
      </TouchableOpacity>

      <KpTodayReaderSheet
        visible={sheetOpen}
        reader={reader}
        loading={loading}
        onClose={closeSheet}
        onOpenKp={openKp}
      />
    </>
  );
}

const styles = StyleSheet.create({
  entryShell: {
    marginHorizontal: 16,
    marginTop: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderRadius: 20,
    overflow: 'hidden',
  },
  entryGradient: { padding: 17 },
  entryLoading: { flexDirection: 'row', alignItems: 'center', gap: 10, minHeight: 56 },
  entryHeader: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  entryIcon: {
    width: 42,
    height: 42,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  entryTitle: { fontSize: 18, lineHeight: 23, fontWeight: '700' },
  entrySubtitle: { fontSize: 13, lineHeight: 18, marginTop: 2, fontWeight: '500' },
  entryTeaser: { fontSize: 14, lineHeight: 21, fontWeight: '600', marginTop: 12 },
  entryCta: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 14 },
  entryCtaText: { fontSize: 14, lineHeight: 19, fontWeight: '700' },
  retry: { marginTop: 10 },
  tonePill: { borderRadius: 999, paddingHorizontal: 8, paddingVertical: 3 },
  tonePillText: { fontSize: 11, fontWeight: '800' },

  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(10, 4, 18, 0.72)',
    paddingHorizontal: 16,
  },
  sheet: {
    maxHeight: '86%',
    borderRadius: 24,
    borderWidth: 1,
    paddingTop: 4,
    overflow: 'hidden',
  },
  pageSlot: {
    justifyContent: 'flex-start',
  },
  handle: {
    width: 42,
    height: 5,
    borderRadius: 999,
    backgroundColor: 'rgba(148,163,184,0.55)',
    alignSelf: 'center',
    marginTop: 10,
    marginBottom: 12,
  },
  sheetHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    paddingHorizontal: 18,
    paddingBottom: 12,
  },
  sheetEyebrow: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
  sheetTitle: { fontSize: 20, lineHeight: 26, fontWeight: '800', marginTop: 4 },
  closeBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sheetLoading: {
    minHeight: 220,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    padding: 24,
  },
  sheetLoadingText: { fontSize: 14, fontWeight: '600' },
  longCard: {
    height: 460,
    borderWidth: 1,
    borderLeftWidth: 4,
    borderRadius: 18,
    overflow: 'hidden',
  },
  longCardScroll: { padding: 16, paddingBottom: 24 },
  pageMeta: { fontSize: 12, fontWeight: '700', marginBottom: 10 },
  summaryText: { fontSize: 15, lineHeight: 23, fontWeight: '500', marginBottom: 14 },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.4,
    textTransform: 'uppercase',
    marginBottom: 10,
  },
  bulletRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 12 },
  dot: { width: 7, height: 7, borderRadius: 4, marginTop: 7 },
  bulletText: { flex: 1, fontSize: 15, lineHeight: 23, fontWeight: '500' },
  dots: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 6,
    marginTop: 12,
    marginBottom: 4,
  },
  dotPage: { width: 6, height: 6, borderRadius: 3 },
  footer: {
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingHorizontal: 18,
    paddingTop: 12,
    gap: 10,
  },
  primaryBtn: {
    borderRadius: 14,
    paddingVertical: 13,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  primaryBtnText: { color: '#fff', fontSize: 15, fontWeight: '800' },
});
