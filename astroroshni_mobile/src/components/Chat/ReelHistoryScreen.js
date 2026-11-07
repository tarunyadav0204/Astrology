import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, Text, TouchableOpacity, View, Platform } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { storage } from '../../services/storage';
import { chatAPI } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import { goBackOrHome } from '../../navigation/navHelpers';
import FocusedStatusBar from '../Common/FocusedStatusBar';
import ReelPlayerModal from '../ReelPlayerModal';

const isReady = (status) => status === 'completed';

export default function ReelHistoryScreen({ navigation }) {
  useAnalytics('ReelHistoryScreen');
  const { t, i18n } = useTranslation();
  const { colors } = useTheme();
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedReel, setSelectedReel] = useState(null);

  const playableReels = useMemo(
    () => list.filter((item) => isReady(item.status)),
    [list],
  );

  const loadHistory = useCallback(async () => {
    try {
      if (!await storage.getAuthToken()) { setList([]); return; }
      const response = await chatAPI.getReelHistory();
      setList(Array.isArray(response?.data?.reels) ? response.data.reels : []);
    } catch (_) {
      setList([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const formatDate = (value) => {
    const date = new Date(value);
    if (!value || Number.isNaN(date.getTime())) return '';
    return new Intl.DateTimeFormat(i18n.resolvedLanguage || undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date);
  };
  const statusLabel = (status) => {
    if (status === 'completed') return t('premiumUi.reelStudio.historyReady', 'Ready to play');
    if (status === 'failed') return t('premiumUi.reelStudio.historyFailed', 'Could not be completed');
    return t('premiumUi.reelStudio.historyCreating', 'Creating your reel');
  };
  const renderItem = ({ item, index }) => {
    const ready = isReady(item.status);
    const hindi = String(item.language || '').toLowerCase().startsWith('hi');
    return <View style={[styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
      <TouchableOpacity disabled={!ready} onPress={() => setSelectedReel(item)} style={styles.cardTop} accessibilityRole="button" accessibilityLabel={ready ? t('premiumUi.reelStudio.historyPlay', 'Play reel') : statusLabel(item.status)}>
        <View style={[styles.playButton, { backgroundColor: ready ? colors.accentSoft : colors.surfaceMuted }]}>
          <Ionicons name={ready ? 'play' : item.status === 'failed' ? 'alert-circle-outline' : 'time-outline'} size={22} color={ready ? colors.onAccent : colors.textSecondary} />
        </View>
        <View style={styles.cardCopy}>
          <Text style={[styles.eyebrow, { color: colors.primary }]}>{t('premiumUi.reelStudio.historyItem', 'REEL {{number}}', { number: list.length - index })}</Text>
          <Text style={[styles.question, { color: colors.text }]} numberOfLines={2}>{item.question || t('premiumUi.reelStudio.historyFallbackTitle', 'Your AstroRoshni reel')}</Text>
          <Text style={[styles.meta, { color: colors.textSecondary }]}>{formatDate(item.created_at)} · {hindi ? t('premiumUi.reelStudio.hindi', 'Hindi') : t('premiumUi.reelStudio.english', 'English')}</Text>
        </View>
        {ready && <Ionicons name="chevron-forward" size={20} color={colors.primary} />}
      </TouchableOpacity>
      <View style={[styles.footer, { borderTopColor: colors.cardBorder }]}>
        <Text style={[styles.status, { color: item.status === 'failed' ? colors.error : colors.textSecondary }]}>{statusLabel(item.status)}</Text>
        {ready && <TouchableOpacity onPress={() => setSelectedReel(item)}><Text style={[styles.playText, { color: colors.primary }]}>{t('premiumUi.reelStudio.historyPlay', 'Play reel')}</Text></TouchableOpacity>}
      </View>
    </View>;
  };
  const empty = <View style={styles.empty}><View style={[styles.emptyIcon, { backgroundColor: colors.accentSoft }]}><Ionicons name="film-outline" size={31} color={colors.onAccent} /></View><Text style={[styles.emptyTitle, { color: colors.text }]}>{t('premiumUi.reelStudio.historyEmptyTitle', 'No reels yet')}</Text><Text style={[styles.emptyBody, { color: colors.textSecondary }]}>{t('premiumUi.reelStudio.historyEmptyBody', 'Reels you create from your readings will appear here for playback and sharing.')}</Text><TouchableOpacity onPress={() => navigation.navigate('Home', { startChat: true })} style={[styles.emptyCta, { backgroundColor: colors.primary }]}><Text style={[styles.emptyCtaText, { color: colors.onPrimary }]}>{t('premiumUi.reelStudio.historyGoToChat', 'Go to Ask Tara')}</Text></TouchableOpacity></View>;

  return <View style={[styles.container, { backgroundColor: colors.background }]}>
    <FocusedStatusBar backgroundColor={colors.headerSurface} />
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.headerSurface }]} edges={['top']}>
      <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cardBorder }]}>
        <TouchableOpacity onPress={() => goBackOrHome(navigation)} style={[styles.back, { borderColor: colors.cosmicLine || colors.cardBorder }]}><Ionicons name="arrow-back" size={21} color={colors.textInverse} /></TouchableOpacity>
        <View style={styles.headerCopy}><Text style={[styles.headerEyebrow, { color: colors.accent }]}>{t('historyUi.library')}</Text><Text style={[styles.headerTitle, { color: colors.textInverse }]}>{t('premiumUi.reelStudio.historyTitle', 'Reel History')}</Text></View>
        <View style={[styles.count, { backgroundColor: colors.accentSoft }]}><Text style={[styles.countText, { color: colors.onAccent }]}>{list.length}</Text></View>
      </View>
      <View style={[styles.content, { backgroundColor: colors.background }]}>
        <View style={styles.intro}><Text style={[styles.introTitle, { color: colors.text }]}>{t('premiumUi.reelStudio.historyHeroTitle', 'Your visual readings, ready whenever you are.')}</Text><Text style={[styles.introBody, { color: colors.textSecondary }]}>{t('premiumUi.reelStudio.historyHeroBody', 'Every reel created from your consultations is kept here privately for playback and sharing.')}</Text></View>
        {loading ? <View style={styles.loading}><ActivityIndicator color={colors.primary} /><Text style={[styles.meta, { color: colors.textSecondary }]}>{t('premiumUi.reelStudio.historyLoading', 'Loading your reels…')}</Text></View> : <FlatList data={list} renderItem={renderItem} keyExtractor={(item) => item.job_id} contentContainerStyle={[styles.list, !list.length && styles.emptyList]} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadHistory(); }} tintColor={colors.primary} />} ListEmptyComponent={empty} />}
      </View>
    </SafeAreaView>
    {selectedReel && <ReelPlayerModal
      key={selectedReel.job_id}
      jobId={selectedReel.job_id}
      reelIds={playableReels.map((item) => item.job_id)}
      onSwipeToReel={(jobId) => {
        const nextReel = playableReels.find((item) => item.job_id === jobId);
        if (nextReel) setSelectedReel(nextReel);
      }}
      onClose={() => setSelectedReel(null)}
      allowRecreate={false}
    />}
  </View>;
}

const styles = StyleSheet.create({
  container: { flex: 1 }, safeArea: { flex: 1 }, content: { flex: 1 },
  header: { minHeight: 78, paddingHorizontal: 18, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1 }, back: { width: 42, height: 42, borderRadius: 21, borderWidth: 1, alignItems: 'center', justifyContent: 'center' }, headerCopy: { flex: 1, paddingHorizontal: 14 }, headerEyebrow: { fontSize: 10, fontWeight: '900', letterSpacing: 2 }, headerTitle: { fontSize: 23, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontWeight: '600', marginTop: 2 }, count: { minWidth: 38, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 10 }, countText: { fontSize: 13, fontWeight: '900' },
  intro: { paddingHorizontal: 20, paddingTop: 24, paddingBottom: 20 }, introTitle: { fontSize: 29, lineHeight: 35, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontWeight: '500' }, introBody: { fontSize: 14, lineHeight: 21, marginTop: 8 }, list: { paddingHorizontal: 20, paddingBottom: 100, gap: 12 }, emptyList: { flexGrow: 1 },
  card: { borderWidth: 1, borderRadius: 22, overflow: 'hidden' }, cardTop: { padding: 15, flexDirection: 'row', alignItems: 'center', gap: 13 }, playButton: { width: 48, height: 48, borderRadius: 18, justifyContent: 'center', alignItems: 'center' }, cardCopy: { flex: 1, minWidth: 0 }, eyebrow: { fontSize: 9, fontWeight: '900', letterSpacing: 1.4 }, question: { fontSize: 15, lineHeight: 21, fontWeight: '700', marginTop: 4 }, meta: { fontSize: 11, fontWeight: '600', marginTop: 7 }, footer: { minHeight: 44, paddingHorizontal: 16, borderTopWidth: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }, status: { fontSize: 12, fontWeight: '700' }, playText: { fontSize: 12, fontWeight: '900' },
  loading: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 }, empty: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 28, paddingVertical: 40 }, emptyIcon: { width: 64, height: 64, borderRadius: 24, alignItems: 'center', justifyContent: 'center', marginBottom: 18 }, emptyTitle: { fontSize: 22, fontWeight: '700', textAlign: 'center' }, emptyBody: { fontSize: 14, lineHeight: 21, textAlign: 'center', marginTop: 8 }, emptyCta: { marginTop: 20, paddingHorizontal: 22, paddingVertical: 13, borderRadius: 18 }, emptyCtaText: { fontSize: 14, fontWeight: '900' },
});
