import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { nudgeAPI } from '../../services/api';
import FocusedStatusBar from '../Common/FocusedStatusBar';
import { appLocaleForI18n } from '../../utils/appLocale';

function formatWhen(iso, locale) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(d);
  } catch {
    return iso;
  }
}

export default function NudgeInboxScreen({ navigation }) {
  const { colors } = useTheme();
  const { t, i18n } = useTranslation();
  const inverseText = colors.onSurfaceInverse || colors.textInverse;
  const inverseTextMuted = colors.onSurfaceInverseMuted || colors.textInverseMuted;
  const dateLocale = appLocaleForI18n(i18n.language);
  const [items, setItems] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await nudgeAPI.getInbox({ limit: 80, offset: 0 });
      setItems(res.data?.items || []);
      setUnreadCount(res.data?.unread_count ?? 0);
    } catch (e) {
      if (__DEV__) console.warn('Nudge inbox:', e?.message);
      setItems([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      load();
    }, [load])
  );

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };

  const openItem = async (item) => {
    try {
      await nudgeAPI.markRead({ ids: [item.id] });
    } catch (_) {
      /* still try navigation */
    }
    setItems((prev) =>
      prev.map((x) => (x.id === item.id ? { ...x, read_at: new Date().toISOString() } : x))
    );
    setUnreadCount((c) => Math.max(0, c - (item.read_at ? 0 : 1)));

    const d = item.data || {};
    const slug = d.slug != null ? String(d.slug).trim() : '';
    const blogUrl = d.blog_url != null ? String(d.blog_url).trim() : '';
    const nudgeId = d.nudge_id != null ? String(d.nudge_id).trim() : '';
    const cta = d.cta != null ? String(d.cta).trim() : '';
    const landingScreenRaw =
      d.landing_screen != null ? String(d.landing_screen).trim().toLowerCase() : '';
    const landingScreen = landingScreenRaw.replace(/[-\s]+/g, '_');
    if (nudgeId) {
      nudgeAPI.recordClick(nudgeId).catch((e) => {
        if (__DEV__) console.warn('Nudge click tracking:', e?.message);
      });
    }

    if (cta === 'astroroshni://blog' || landingScreen === 'blog') {
      const { astroRoshniBlogSlug, normalizeHttpsUrl } = require('../../utils/blogLinks');
      const resolvedSlug = slug || astroRoshniBlogSlug(blogUrl);
      if (resolvedSlug) {
        navigation.navigate('BlogPostDetail', { slug: resolvedSlug });
        return;
      }
      const normalizedBlogUrl = normalizeHttpsUrl(blogUrl);
      if (normalizedBlogUrl) {
        navigation.navigate('BlogLink', { url: normalizedBlogUrl });
        return;
      }
    }
    if (landingScreen === 'information' || cta === 'astroroshni://information') {
      navigation.navigate('Home', {
        resetToGreeting: true,
        showInfoModal: true,
        infoTitle: item.title || t('notificationInbox.information', 'Information'),
        infoBody: item.body || '',
        infoNonce: Date.now(),
      });
      return;
    }
    if (landingScreen === 'event_screen' || cta === 'astroroshni://event') {
      navigation.navigate('EventScreen');
      return;
    }
    if (landingScreen === 'past_life_karma' || cta === 'astroroshni://karma') {
      try {
        const { storage } = require('../../services/storage');
        const selectedBirth = await storage.getBirthDetails();
        const chartId = selectedBirth?.id ?? selectedBirth?._id ?? null;
        navigation.navigate('KarmaAnalysis', { chartId });
      } catch (_) {
        navigation.navigate('KarmaAnalysis');
      }
      return;
    }
    if (['career', 'marriage', 'health', 'wealth', 'progeny', 'education'].includes(landingScreen) || cta === 'astroroshni://analysis') {
      const analysisType =
        ['career', 'marriage', 'health', 'wealth', 'progeny', 'education'].includes(landingScreen)
          ? landingScreen
          : (d.analysis_type != null ? String(d.analysis_type).trim().toLowerCase().replace(/[-\s]+/g, '_') : '');
      const analysisTitles = {
        career: t('notificationInbox.careerAnalysis', 'Career Analysis'),
        marriage: t('notificationInbox.marriageAnalysis', 'Marriage Analysis'),
        health: t('notificationInbox.healthAnalysis', 'Health Analysis'),
        wealth: t('notificationInbox.wealthAnalysis', 'Wealth Analysis'),
        progeny: t('notificationInbox.progenyAnalysis', 'Progeny Analysis'),
        education: t('notificationInbox.educationAnalysis', 'Education Analysis'),
      };
      if (analysisType && analysisTitles[analysisType]) {
        navigation.navigate('AnalysisDetail', { analysisType, title: analysisTitles[analysisType] });
        return;
      }
    }
    if (cta === 'astroroshni://chat' || landingScreen === 'chat' || String(item.trigger_id || '') === 'admin') {
      const q = d.question != null ? String(d.question).trim() : '';
      navigation.navigate('Home', {
        startChat: true,
        ...(q ? { initialMessage: q } : {}),
        ...(nudgeId ? { nudgeId } : {}),
      });
      return;
    }
    Alert.alert(item.title || t('notificationInbox.update', 'Update'), item.body || '', [{ text: t('common.ok', 'OK') }]);
  };

  const markAllRead = async () => {
    try {
      await nudgeAPI.markRead({ ids: [] });
      setItems((prev) => prev.map((x) => ({ ...x, read_at: x.read_at || new Date().toISOString() })));
      setUnreadCount(0);
    } catch (e) {
      Alert.alert(t('common.error', 'Error'), e?.response?.data?.detail || t('notificationInbox.updateFailed', 'Could not update notifications.'));
    }
  };

  const renderItem = ({ item }) => {
    const unread = !item.read_at;
    return (
      <TouchableOpacity
        style={[
          styles.row,
          {
            backgroundColor: colors.surface,
            borderColor: colors.cardBorder,
            borderLeftWidth: unread ? 3 : 1,
            borderLeftColor: unread ? colors.accent : colors.cardBorder,
          },
        ]}
        onPress={() => openItem(item)}
        activeOpacity={0.85}
      >
        <View style={styles.rowTop}>
          <View style={[styles.itemIcon, { backgroundColor: unread ? colors.accentSoft : colors.surfaceMuted }]}>
            <Ionicons name={unread ? 'sparkles-outline' : 'mail-open-outline'} size={17} color={unread ? colors.onAccent : colors.textSecondary} />
          </View>
          <Text style={[styles.title, { color: colors.text }]} numberOfLines={2}>{item.title}</Text>
          {unread && <View style={[styles.unreadDot, { backgroundColor: colors.accent }]} />}
        </View>
        <Text style={[styles.body, { color: colors.textSecondary }]} numberOfLines={3}>
          {item.body}
        </Text>
        <Text style={[styles.meta, { color: colors.textSecondary }]}>
          {formatWhen(item.created_at || item.sent_at, dateLocale)}
          {item.channel ? ` · ${item.channel}` : ''}
        </Text>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.headerSurface }]} edges={['top']}>
      <FocusedStatusBar backgroundColor={colors.headerSurface} barStyle="light-content" />
      <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={23} color={colors.textInverse} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: colors.textInverse }]}>{t('notificationInbox.title', 'Notifications')}</Text>
        {unreadCount > 0 ? (
          <TouchableOpacity onPress={markAllRead} style={styles.markAll}>
            <Text style={[styles.markAllText, { color: colors.accent }]}>{t('notificationInbox.markAllRead', 'Mark all read')}</Text>
          </TouchableOpacity>
        ) : (
          <View style={{ width: 88 }} />
        )}
      </View>

      <View style={[styles.contentShell, { backgroundColor: colors.background }]}>
        {loading ? (
          <View style={styles.centered}>
            <ActivityIndicator size="large" color={colors.accent} />
            <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('notificationInbox.loading', 'Gathering your updates…')}</Text>
          </View>
        ) : (
        <FlatList
          data={items}
          keyExtractor={(it) => String(it.id)}
          renderItem={renderItem}
          ListHeaderComponent={
            <View style={[styles.hero, { backgroundColor: colors.surfaceInverse, borderColor: colors.cosmicLine }]}>
              <View style={[styles.heroRing, styles.heroRingLarge, { borderColor: colors.cosmicLine }]} />
              <View style={[styles.heroRing, styles.heroRingSmall, { borderColor: colors.cosmicLine }]} />
              <Text style={[styles.heroEyebrow, { color: colors.accent }]}>{t('notificationInbox.eyebrow', 'YOUR ASTROLOGY DESK')}</Text>
              <Text style={[styles.heroTitle, { color: inverseText }]}>{unreadCount > 0 ? t('notificationInbox.unreadCount', { count: unreadCount, defaultValue: '{{count}} unread updates' }) : t('notificationInbox.allCaughtUp', 'You are all caught up')}</Text>
              <Text style={[styles.heroBody, { color: inverseTextMuted }]}>{t('notificationInbox.heroBody', 'Personal readings, timing alerts and AstroRoshni updates—kept together in one calm place.')}</Text>
            </View>
          }
          contentContainerStyle={[styles.listContent, items.length === 0 && styles.emptyListContent]}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.accent]} tintColor={colors.accent} />}
          ListEmptyComponent={
            <View style={[styles.emptyCard, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
              <View style={[styles.emptyIcon, { backgroundColor: colors.accentSoft }]}><Ionicons name="notifications-outline" size={25} color={colors.onAccent} /></View>
              <Text style={[styles.emptyTitle, { color: colors.text }]}>{t('notificationInbox.emptyTitle', 'A quiet inbox')}</Text>
              <Text style={[styles.empty, { color: colors.textSecondary }]}>{t('notificationInbox.emptyBody', 'Personal readings and useful updates will appear here when they are ready.')}</Text>
            </View>
          }
        />
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  contentShell: { flex: 1, borderTopLeftRadius: 24, borderTopRightRadius: 24, overflow: 'hidden' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 13,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backBtn: { padding: 8, width: 44 },
  headerTitle: { flex: 1, fontSize: 20, fontFamily: 'serif', fontWeight: '600', textAlign: 'center' },
  markAll: { paddingHorizontal: 8, width: 88, alignItems: 'flex-end' },
  markAllText: { color: '#ff6b35', fontSize: 13, fontWeight: '700' },
  listContent: { padding: 18, paddingBottom: 48 },
  emptyListContent: { flexGrow: 1 },
  hero: { minHeight: 220, borderRadius: 28, borderWidth: 1, padding: 24, marginBottom: 18, overflow: 'hidden', justifyContent: 'flex-end' },
  heroRing: { position: 'absolute', borderWidth: 1, borderRadius: 999 },
  heroRingLarge: { width: 220, height: 220, right: -76, top: -92 },
  heroRingSmall: { width: 150, height: 150, right: -31, top: -58 },
  heroEyebrow: { fontSize: 12, fontWeight: '800', letterSpacing: 2.1, marginBottom: 9 },
  heroTitle: { fontSize: 31, lineHeight: 36, fontFamily: 'serif', fontWeight: '600', maxWidth: '82%' },
  heroBody: { fontSize: 14, lineHeight: 21, marginTop: 10, maxWidth: '87%' },
  row: {
    borderRadius: 20,
    padding: 16,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  rowTop: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  itemIcon: { width: 34, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center', marginRight: 10 },
  unreadDot: { width: 7, height: 7, borderRadius: 4, marginLeft: 8 },
  title: { flex: 1, fontSize: 17, lineHeight: 22, fontFamily: 'serif', fontWeight: '600' },
  body: { fontSize: 14, lineHeight: 21, marginBottom: 10 },
  meta: { fontSize: 11, fontWeight: '600', letterSpacing: 0.25 },
  emptyCard: { borderRadius: 22, borderWidth: 1, padding: 24, alignItems: 'center' },
  emptyIcon: { width: 52, height: 52, borderRadius: 26, alignItems: 'center', justifyContent: 'center', marginBottom: 14 },
  emptyTitle: { fontSize: 22, fontFamily: 'serif', fontWeight: '600', marginBottom: 7 },
  empty: { textAlign: 'center', fontSize: 14, lineHeight: 21, maxWidth: 280 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { marginTop: 12, fontSize: 13 },
});
