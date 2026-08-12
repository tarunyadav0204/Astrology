import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  Platform,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { storage } from '../../services/storage';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import { goBackOrHome } from '../../navigation/navHelpers';
import FocusedStatusBar from '../Common/FocusedStatusBar';

const getDateKey = (timestamp) => {
  if (!timestamp) return 'unknown';
  const value = new Date(timestamp);
  if (Number.isNaN(value.getTime())) return 'unknown';
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
};

export default function ChatHistoryScreen({ navigation }) {
  useAnalytics('ChatHistoryScreen');
  const { t, i18n } = useTranslation();
  const { colors } = useTheme();
  const [historyRows, setHistoryRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const loadChatHistory = useCallback(async (pageNum = 1, append = false) => {
    try {
      const authToken = await storage.getAuthToken();
      if (!authToken) {
        navigation.replace('Login');
        return;
      }
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat-v2/history')}?page=${pageNum}&limit=5&list_mode=dates`, {
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` },
      });
      if (response.status === 401) {
        await storage.removeAuthToken();
        navigation.replace('Login');
        return;
      }
      if (!response.ok) throw new Error('history_request_failed');
      const data = await response.json();
      let rows = Array.isArray(data.dates) ? data.dates : [];
      if (!rows.length && Array.isArray(data.sessions)) {
        rows = data.sessions.map((session) => {
          const timestamp = session.last_activity_at || session.created_at;
          const dateKey = getDateKey(timestamp);
          return {
            date_key: dateKey,
            date_label: dateKey,
            last_activity_at: timestamp,
            message_count: Number(session.main_question_count || 1),
            session_ids: session.session_id ? [session.session_id] : [],
          };
        });
      }
      setHistoryRows((current) => {
        if (!append) return rows;
        const known = new Set(current.map((row) => row.date_key));
        return [...current, ...rows.filter((row) => !known.has(row.date_key))];
      });
      setHasMore(Boolean(data.pagination?.has_more));
      setPage(pageNum);
    } catch (error) {
      if (!append) setHistoryRows([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
      setLoadingMore(false);
    }
  }, [navigation]);

  useEffect(() => { loadChatHistory(); }, [loadChatHistory]);

  const filteredRows = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return historyRows;
    return historyRows.filter((row) => String(row.date_label || row.date_key || '').toLowerCase().includes(query));
  }, [historyRows, searchQuery]);

  const openDay = (item) => {
    const sessionIds = [...new Set((item.session_ids || []).filter(Boolean))];
    if (!sessionIds.length) {
      Alert.alert(t('historyUi.chat.noMessages'), t('historyUi.chat.noMessagesBody'));
      return;
    }
    navigation.navigate('ChatView', {
      session: {
        session_id: `day_${item.date_key}`,
        created_at: item.date_key,
        date_key: item.date_key,
        date_label: item.date_label || item.date_key,
        message_count: Number(item.message_count || 0),
        session_ids: sessionIds,
        native_name: null,
        messages: [],
      },
    });
  };

  const formatDay = (item) => {
    const parsed = item.date_key ? new Date(`${item.date_key}T00:00:00`) : null;
    if (!parsed || Number.isNaN(parsed.getTime())) return item.date_label || item.date_key;
    return new Intl.DateTimeFormat(i18n.resolvedLanguage || undefined, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).format(parsed);
  };

  const renderItem = ({ item }) => {
    const parsed = item.date_key ? new Date(`${item.date_key}T00:00:00`) : null;
    const validDate = parsed && !Number.isNaN(parsed.getTime());
    const month = validDate ? new Intl.DateTimeFormat(i18n.resolvedLanguage || undefined, { month: 'short' }).format(parsed).toUpperCase() : '—';
    const day = validDate ? parsed.getDate() : '—';
    return (
      <TouchableOpacity
        onPress={() => openDay(item)}
        activeOpacity={0.88}
        style={[styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}
      >
        <View
          style={[styles.dateTile, { backgroundColor: colors.surfaceInverse, borderColor: colors.accent }]}
        >
          <Text style={[styles.month, { color: colors.onSurfaceInverseMuted || colors.textInverseMuted }]}>{month}</Text>
          <Text style={[styles.day, { color: colors.onSurfaceInverse || colors.textInverse }]}>{day}</Text>
        </View>
        <View style={styles.cardBody}>
          <Text style={[styles.cardEyebrow, { color: colors.primary }]}>{t('historyUi.chat.dayLabel')}</Text>
          <Text style={[styles.cardTitle, { color: colors.text }]} numberOfLines={2}>{formatDay(item)}</Text>
          <Text style={[styles.cardMeta, { color: colors.textSecondary }]}>
            {t('historyUi.chat.messageCount', { count: Number(item.message_count || 0) })}
          </Text>
          <Text style={[styles.cardHint, { color: colors.textTertiary }]}>{t('historyUi.chat.openDay')}</Text>
        </View>
        <View style={[styles.arrow, { borderColor: colors.cardBorder }]}>
          <Ionicons name="arrow-forward" size={17} color={colors.primary} />
        </View>
      </TouchableOpacity>
    );
  };

  const emptyState = (
    <View style={styles.emptyState}>
      <View style={[styles.emptyIcon, { backgroundColor: colors.accentSoft }]}>
        <Ionicons name="chatbubbles-outline" size={30} color={colors.onAccent} />
      </View>
      <Text style={[styles.emptyTitle, { color: colors.text }]}>{searchQuery ? t('historyUi.chat.noMatches') : t('historyUi.chat.emptyTitle')}</Text>
      <Text style={[styles.emptyBody, { color: colors.textSecondary }]}>{searchQuery ? t('historyUi.chat.noMatchesBody') : t('historyUi.chat.emptyBody')}</Text>
      {!searchQuery && (
        <TouchableOpacity onPress={() => navigation.navigate('Home', { startChat: true })} style={[styles.emptyCta, { backgroundColor: colors.primary }]}>
          <Text style={[styles.emptyCtaText, { color: colors.onPrimary }]}>{t('historyUi.chat.startChat')}</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <FocusedStatusBar backgroundColor={colors.headerSurface} />
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.headerSurface }]} edges={['top']}>
        <View
          style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cardBorder }]}
        >
          <TouchableOpacity onPress={() => goBackOrHome(navigation)} style={[styles.backButton, { borderColor: colors.cosmicLine || colors.cardBorder }]}>
            <Ionicons name="arrow-back" size={21} color={colors.textInverse} />
          </TouchableOpacity>
          <View style={styles.headerCopy}>
            <Text style={[styles.headerEyebrow, { color: colors.accent }]}>{t('historyUi.library')}</Text>
            <Text style={[styles.headerTitle, { color: colors.textInverse }]}>{t('historyUi.chat.title')}</Text>
          </View>
          <View style={[styles.countPill, { backgroundColor: colors.accentSoft }]}>
            <Text style={[styles.countText, { color: colors.onAccent }]}>{historyRows.length}</Text>
          </View>
        </View>

        <View style={[styles.contentShell, { backgroundColor: colors.background }]}>
        <View style={styles.intro}>
          <Text style={[styles.introTitle, { color: colors.text }]}>{t('historyUi.chat.heroTitle')}</Text>
          <Text style={[styles.introBody, { color: colors.textSecondary }]}>{t('historyUi.chat.heroBody')}</Text>
        </View>

        <View
          style={[styles.search, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}
        >
          <Ionicons name="search-outline" size={19} color={colors.textSecondary} />
          <TextInput
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholder={t('historyUi.chat.search')}
            placeholderTextColor={colors.textTertiary}
            style={[styles.searchInput, { color: colors.text }]}
          />
          {searchQuery ? (
            <TouchableOpacity onPress={() => setSearchQuery('')} accessibilityLabel={t('historyUi.clearSearch')}>
              <Ionicons name="close-circle" size={19} color={colors.textSecondary} />
            </TouchableOpacity>
          ) : null}
        </View>

        {loading ? (
          <View style={styles.loadingState}>
            <ActivityIndicator color={colors.primary} />
            <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('historyUi.chat.loading')}</Text>
          </View>
        ) : (
          <FlatList
            data={filteredRows}
            renderItem={renderItem}
            keyExtractor={(item, index) => item.date_key || `day-${index}`}
            contentContainerStyle={[styles.list, !filteredRows.length && styles.emptyList]}
            showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadChatHistory(1); }} tintColor={colors.primary} />}
            ListEmptyComponent={emptyState}
            ListFooterComponent={hasMore && filteredRows.length ? (
              <TouchableOpacity
                disabled={loadingMore}
                onPress={() => { setLoadingMore(true); loadChatHistory(page + 1, true); }}
                style={[styles.loadMore, { borderColor: colors.cardBorder, backgroundColor: colors.surfaceRaised }]}
              >
                {loadingMore ? <ActivityIndicator color={colors.primary} /> : <Text style={[styles.loadMoreText, { color: colors.primary }]}>{t('historyUi.loadMore')}</Text>}
              </TouchableOpacity>
            ) : null}
          />
        )}
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  contentShell: { flex: 1 },
  header: { minHeight: 78, paddingHorizontal: 18, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1 },
  backButton: { width: 42, height: 42, borderRadius: 21, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  headerCopy: { flex: 1, paddingHorizontal: 14 },
  headerEyebrow: { fontSize: 10, fontWeight: '900', letterSpacing: 2 },
  headerTitle: { fontSize: 23, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontWeight: '600', marginTop: 2 },
  countPill: { minWidth: 38, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 10 },
  countText: { fontSize: 13, fontWeight: '900' },
  intro: { paddingHorizontal: 20, paddingTop: 24, paddingBottom: 18 },
  introTitle: { fontSize: 31, lineHeight: 36, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontWeight: '500' },
  introBody: { fontSize: 14, lineHeight: 21, marginTop: 8, maxWidth: 470 },
  search: { marginHorizontal: 20, marginBottom: 16, minHeight: 52, borderWidth: 1, borderRadius: 18, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', gap: 10 },
  searchInput: { flex: 1, fontSize: 15, paddingVertical: 12 },
  list: { paddingHorizontal: 20, paddingBottom: 40, gap: 12 },
  emptyList: { flexGrow: 1 },
  card: { borderWidth: 1, borderRadius: 22, padding: 14, flexDirection: 'row', alignItems: 'center', gap: 14 },
  dateTile: { width: 58, height: 68, borderRadius: 18, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  month: { fontSize: 9, letterSpacing: 1.3, fontWeight: '900' },
  day: { fontSize: 25, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), marginTop: 1 },
  cardBody: { flex: 1, minWidth: 0 },
  cardEyebrow: { fontSize: 9, fontWeight: '900', letterSpacing: 1.5, textTransform: 'uppercase' },
  cardTitle: { fontSize: 17, lineHeight: 22, fontWeight: '700', marginTop: 3 },
  cardMeta: { fontSize: 12, marginTop: 5, fontWeight: '600' },
  cardHint: { fontSize: 11, marginTop: 5 },
  arrow: { width: 34, height: 34, borderRadius: 17, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  loadingState: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  loadingText: { fontSize: 13, fontWeight: '700' },
  emptyState: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 28, paddingVertical: 40 },
  emptyIcon: { width: 64, height: 64, borderRadius: 24, alignItems: 'center', justifyContent: 'center', marginBottom: 18 },
  emptyTitle: { fontSize: 22, fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontWeight: '600', textAlign: 'center' },
  emptyBody: { fontSize: 14, lineHeight: 21, textAlign: 'center', marginTop: 8, maxWidth: 340 },
  emptyCta: { marginTop: 20, paddingHorizontal: 22, paddingVertical: 13, borderRadius: 18 },
  emptyCtaText: { fontSize: 14, fontWeight: '900' },
  loadMore: { minHeight: 48, marginTop: 4, borderWidth: 1, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
  loadMoreText: { fontSize: 13, fontWeight: '900' },
});
