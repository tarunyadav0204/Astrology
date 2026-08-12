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
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { useTheme } from '../../context/ThemeContext';
import { kpAPI } from '../../services/api';
import { trackEvent } from '../../utils/analytics';
import { DISPLAY_FONT_FAMILY } from '../../theme/tokens';
import { useTranslation } from 'react-i18next';

const CACHE_PREFIX = 'kp_today_home_v2:';
const MAX_PAGES = 5;
const BULLETS_PER_PAGE = 4;

const API_LANGUAGES = {
  english: 'en', en: 'en', hindi: 'hi', hi: 'hi', es: 'es', fr: 'fr',
  german: 'de', de: 'de', russian: 'ru', ru: 'ru', chinese: 'zh', zh: 'zh',
  tamil: 'ta', ta: 'ta', telugu: 'te', te: 'te', gujarati: 'gu', gu: 'gu',
  marathi: 'mr', mr: 'mr',
};

const toneLabel = (t, tone) => t(`premiumUi.kpToday.tones.${tone || 'neutral'}`);

function toneUi(tone, colors) {
  const accent = {
    supportive: colors.success,
    mixed: colors.warning,
    challenging: colors.error,
    neutral: colors.textSecondary,
  }[tone] || colors.textSecondary;
  return { accent, pillBg: colors.surfaceMuted, pillText: colors.text };
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

function formatShortDate(d, locale = 'en-IN') {
  try {
    return d.toLocaleDateString(locale, { weekday: 'short', month: 'short', day: 'numeric' });
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

function humanHeadline(selfTheme, quiet, t) {
  if (quiet) return t('premiumUi.kpToday.quieterDay');
  const label = String(selfTheme?.label || '').trim();
  if (label && !isTechnicalLabel(label)) return label;
  const summary = String(selfTheme?.summary || '').trim();
  if (summary) {
    const first = summary.split(/[.!?]/)[0].trim();
    if (first.length >= 12 && first.length <= 72) return first;
    if (summary.length <= 72) return summary;
    return `${summary.slice(0, 69).trim()}…`;
  }
  return t('premiumUi.kpToday.dayReady');
}

function buildReaderPages(todayBlock, t) {
  const houses = todayBlock?.houses_giving_results || [];
  const selfTheme = (todayBlock?.manifestations || []).find(
    (item) => (item.subject || 'self') === 'self'
  );
  const tone = selfTheme?.outcome_tone || houses[0]?.tone || 'neutral';
  const summary = String(selfTheme?.summary || '').trim();
  const possibilities = Array.isArray(selfTheme?.possibilities)
    ? selfTheme.possibilities.map((p) => String(p || '').trim()).filter(Boolean)
    : [];
  const headline = humanHeadline(selfTheme, !houses.length, t);
  const quiet = !houses.length;

  if (quiet) {
    return {
      quiet: true,
      tone: 'neutral',
      headline,
      teaser: t('premiumUi.kpToday.quietTeaser'),
      pages: [
        {
          id: 'quiet',
          showSummary: true,
          summary: t('premiumUi.kpToday.quietSummary'),
          bullets: [
            t('premiumUi.kpToday.quietBulletOne'),
            t('premiumUi.kpToday.quietBulletTwo'),
          ],
        },
      ],
    };
  }

  let bullets = [...possibilities];
  if (!bullets.length && summary) bullets = [summary];
  if (!bullets.length) {
    bullets = [t('premiumUi.kpToday.fallbackBullet')];
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
    teaser: summary || bullets[0] || t('premiumUi.kpToday.predictionsReady'),
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
  const { colors } = useTheme();
  const { t, i18n } = useTranslation();
  const locale = i18n.resolvedLanguage || i18n.language || 'en-IN';
  const insets = useSafeAreaInsets();
  const { width: windowWidth } = useWindowDimensions();
  const [pageIndex, setPageIndex] = useState(0);
  const surface = colors.surfaceRaised || colors.surface;
  const tile = colors.surfaceMuted;
  const border = colors.cardBorder;
  const bodyText = colors.text;
  const mutedText = colors.textSecondary;
  const tone = toneUi(reader?.tone || 'neutral', colors);
  const pages = reader?.pages || [];
  // Sheet is width 100% with overlay pad 16 and maxWidth 440 — page must match that exactly for paging.
  const pageWidth = Math.min(windowWidth - 32, 440);
  const cardPad = 18;
  const pageIndexRef = useRef(0);

  const viewabilityConfig = useRef({
    itemVisiblePercentThreshold: 55,
    minimumViewTime: 40,
  }).current;

  const onViewableItemsChanged = useRef(({ viewableItems }) => {
    const next = viewableItems?.[0]?.index;
    if (typeof next !== 'number' || next < 0) return;
    if (next === pageIndexRef.current) return;
    pageIndexRef.current = next;
    setPageIndex(next);
  }).current;

  useEffect(() => {
    if (visible) {
      pageIndexRef.current = 0;
      setPageIndex(0);
    }
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
              <Text style={[styles.sheetEyebrow, { color: colors.primary }]}>
                {t('premiumUi.kpToday.today')} · {formatShortDate(new Date(), locale)}
              </Text>
              <Text style={[styles.sheetTitle, { color: bodyText }]} numberOfLines={2}>
                {reader?.headline || t('premiumUi.kpToday.dayReady')}
              </Text>
            </View>
            <View style={[styles.tonePill, { backgroundColor: tone.pillBg }]}>
              <Text style={[styles.tonePillText, { color: tone.pillText }]}>
                {toneLabel(t, reader?.tone)}
              </Text>
            </View>
            <TouchableOpacity
              onPress={onClose}
              style={[styles.closeBtn, { backgroundColor: tile }]}
              accessibilityLabel={t('premiumUi.common.close')}
            >
              <Ionicons name="close" size={20} color={bodyText} />
            </TouchableOpacity>
          </View>

          {loading && !pages.length ? (
            <View style={styles.sheetLoading}>
              <ActivityIndicator color={colors.primary} />
              <Text style={[styles.sheetLoadingText, { color: mutedText }]}>
                {t('premiumUi.kpToday.writing')}
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
                viewabilityConfig={viewabilityConfig}
                onViewableItemsChanged={onViewableItemsChanged}
                onScroll={(e) => {
                  const x = e.nativeEvent.contentOffset.x;
                  if (!pageWidth) return;
                  const next = Math.max(
                    0,
                    Math.min(pages.length - 1, Math.round(x / pageWidth))
                  );
                  if (next === pageIndexRef.current) return;
                  pageIndexRef.current = next;
                  setPageIndex(next);
                  trackEvent('kp_today_reader_swipe', { page: next, pages: pages.length });
                }}
                scrollEventThrottle={16}
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
                          {t('premiumUi.kpToday.pageOf', { current: index + 1, total: pages.length })}
                        </Text>
                        {item.showSummary && item.summary ? (
                          <Text style={[styles.summaryText, { color: mutedText }]}>{item.summary}</Text>
                        ) : null}
                        <Text style={[styles.sectionLabel, { color: tone.accent }]}>
                          {t('premiumUi.kpToday.unfold')}
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
                            i === pageIndex ? tone.accent : colors.strokeMuted,
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
              style={[styles.primaryBtn, { backgroundColor: colors.primary }]}
              onPress={() => onOpenKp?.('today')}
              activeOpacity={0.9}
            >
              <Text style={[styles.primaryBtnText, { color: colors.onPrimary }]}>{t('premiumUi.kpToday.open')}</Text>
              <Ionicons name="arrow-forward" size={16} color={colors.onPrimary} />
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
export default function KpTodayCarousel({ birthDetails, onOpenKp, embedded = false }) {
  const { colors } = useTheme();
  const { t, i18n } = useTranslation();
  const locale = i18n.resolvedLanguage || i18n.language || 'en-IN';
  const apiLanguage = API_LANGUAGES[i18n.resolvedLanguage] || API_LANGUAGES[i18n.language] || 'en';
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
      setError(t('premiumUi.kpToday.birthDetailsIncomplete'));
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
        language: apiLanguage,
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
        setError(response.data?.detail || t('premiumUi.kpToday.loadError'));
      }
    } catch (e) {
      if (requestId !== requestIdRef.current) return;
      if (!hasDataRef.current) setError(e.message || t('premiumUi.kpToday.loadError'));
    } finally {
      if (requestId === requestIdRef.current) setLoading(false);
    }
  }, [apiLanguage, t]);

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

  const reader = useMemo(() => buildReaderPages(data?.today, t), [data?.today, t]);

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

  const tone = toneUi(reader.tone, colors);
  const entryTitle = reader.headline || (reader.quiet ? 'A quieter day' : 'Your day is ready');
  const entryToneLine = reader.quiet
    ? 'Fewer clear results confirmed right now'
    : `${toneLabel(t, reader.tone)} · ${formatShortDate(new Date(), locale)}`;

  return (
    <>
      <TouchableOpacity
        activeOpacity={0.88}
        onPress={openSheet}
        disabled={loading && !data}
        style={[
          styles.entryShell,
          embedded && styles.entryShellEmbedded,
          {
            borderColor: colors.cardBorder,
            backgroundColor: colors.surface,
          },
        ]}
        accessibilityRole="button"
        accessibilityLabel={t('premiumUi.kpToday.read')}
      >
        <View style={[styles.entryGradient, { backgroundColor: colors.surface }]}>
          {loading && !data ? (
            <View style={styles.entryLoading}>
              <ActivityIndicator size="small" color={colors.primary} />
              <Text style={[styles.entrySubtitle, { color: colors.textSecondary }]}>
                {t('premiumUi.kpToday.preparing')}
              </Text>
            </View>
          ) : error && !data ? (
            <View>
              <Text style={[styles.entryTitle, { color: colors.text }]}>{t('premiumUi.kpToday.title')}</Text>
              <Text style={[styles.entrySubtitle, { color: colors.textSecondary }]}>{error}</Text>
              <TouchableOpacity onPress={load} style={styles.retry}>
                <Text style={[styles.entryCtaText, { color: colors.primary }]}>{t('premiumUi.common.tryAgain')}</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              <View style={styles.liveRow}>
                <View style={[styles.liveDot, { backgroundColor: tone.accent }]} />
                <Text style={[styles.liveLabel, { color: colors.textTertiary }]}>{t('premiumUi.kpToday.live')} · {formatShortDate(new Date(), locale)}</Text>
                <Text style={[styles.pageCount, { color: colors.textTertiary }]}>
                  {reader.pages.length} {reader.pages.length === 1 ? 'card' : 'cards'}
                </Text>
              </View>
              <View style={styles.entryHeader}>
                <View style={{ flex: 1, minWidth: 0 }}>
                  <Text style={[styles.entryTitle, { color: colors.text }]}>{entryTitle}</Text>
                  <Text style={[styles.entrySubtitle, { color: colors.textSecondary }]}>
                    {entryToneLine}
                  </Text>
                </View>
                <View style={[styles.tonePill, { backgroundColor: tone.pillBg }]}>
                  <Text style={[styles.tonePillText, { color: tone.pillText }]}>
                    {toneLabel(t, reader.tone)}
                  </Text>
                </View>
              </View>
              <Text numberOfLines={2} style={[styles.entryTeaser, { color: colors.text }]}>
                {reader.teaser}
              </Text>
              <View style={styles.entryCta}>
                <Text style={[styles.entryCtaText, { color: colors.primary }]}>
                  {t('premiumUi.kpToday.swipe')}
                </Text>
                <View style={[styles.entryArrow, { borderColor: colors.cardBorder }]}>
                  <Ionicons name="arrow-forward" size={16} color={colors.primary} />
                </View>
              </View>
            </>
          )}
        </View>
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
  entryShellEmbedded: { marginHorizontal: 0, marginTop: 0, marginBottom: 0 },
  entryGradient: { padding: 18 },
  entryLoading: { flexDirection: 'row', alignItems: 'center', gap: 10, minHeight: 56 },
  liveRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 14 },
  liveDot: { width: 7, height: 7, borderRadius: 4, marginRight: 7 },
  liveLabel: { flex: 1, fontSize: 9, lineHeight: 12, fontWeight: '900', letterSpacing: 1.1 },
  pageCount: { fontSize: 10, lineHeight: 13, fontWeight: '700' },
  entryHeader: { flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  entryTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 23, lineHeight: 28, fontWeight: '400' },
  entrySubtitle: { fontSize: 13, lineHeight: 18, marginTop: 2, fontWeight: '500' },
  entryTeaser: { fontSize: 13, lineHeight: 20, fontWeight: '500', marginTop: 12 },
  entryCta: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginTop: 18 },
  entryCtaText: { fontSize: 14, lineHeight: 19, fontWeight: '700' },
  entryArrow: { width: 34, height: 34, borderRadius: 17, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
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
  sheetTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 24, lineHeight: 29, fontWeight: '400', marginTop: 4 },
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
