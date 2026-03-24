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
import { nudgeAPI } from '../../services/api';

function formatWhen(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

export default function NudgeInboxScreen({ navigation }) {
  const { colors } = useTheme();
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
    const cta = d.cta != null ? String(d.cta).trim() : '';

    if (cta === 'astroroshni://blog' && slug) {
      navigation.navigate('BlogPostDetail', { slug });
      return;
    }
    if (cta === 'astroroshni://chat' || String(item.trigger_id || '') === 'admin') {
      const q = d.question != null ? String(d.question).trim() : '';
      navigation.navigate('Home', {
        startChat: true,
        ...(q ? { initialMessage: q } : {}),
      });
      return;
    }
    Alert.alert(item.title || 'Update', item.body || '', [{ text: 'OK' }]);
  };

  const markAllRead = async () => {
    try {
      await nudgeAPI.markRead({ ids: [] });
      setItems((prev) => prev.map((x) => ({ ...x, read_at: x.read_at || new Date().toISOString() })));
      setUnreadCount(0);
    } catch (e) {
      Alert.alert('Error', e?.response?.data?.detail || 'Could not update');
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
            borderLeftWidth: unread ? 4 : 0,
            borderLeftColor: unread ? '#ff6b35' : 'transparent',
          },
        ]}
        onPress={() => openItem(item)}
        activeOpacity={0.85}
      >
        <Text style={[styles.title, { color: colors.text }]} numberOfLines={2}>
          {item.title}
        </Text>
        <Text style={[styles.body, { color: colors.textSecondary }]} numberOfLines={3}>
          {item.body}
        </Text>
        <Text style={[styles.meta, { color: colors.textSecondary }]}>
          {formatWhen(item.created_at || item.sent_at)}
          {item.channel ? ` · ${item.channel}` : ''}
        </Text>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.background }]} edges={['top']}>
      <View style={[styles.header, { borderBottomColor: colors.cardBorder }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: colors.text }]}>Notifications</Text>
        {unreadCount > 0 ? (
          <TouchableOpacity onPress={markAllRead} style={styles.markAll}>
            <Text style={styles.markAllText}>Mark all read</Text>
          </TouchableOpacity>
        ) : (
          <View style={{ width: 88 }} />
        )}
      </View>

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#ff6b35" />
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(it) => String(it.id)}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#ff6b35']} />}
          ListEmptyComponent={
            <Text style={[styles.empty, { color: colors.textSecondary }]}>
              No messages yet. When we send you updates, they'll show up here.
            </Text>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backBtn: { padding: 8, width: 44 },
  headerTitle: { flex: 1, fontSize: 18, fontWeight: '800', textAlign: 'center' },
  markAll: { paddingHorizontal: 8, width: 88, alignItems: 'flex-end' },
  markAllText: { color: '#ff6b35', fontSize: 13, fontWeight: '700' },
  listContent: { padding: 16, paddingBottom: 40 },
  row: {
    borderRadius: 14,
    padding: 14,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  title: { fontSize: 16, fontWeight: '700', marginBottom: 6 },
  body: { fontSize: 14, lineHeight: 20, marginBottom: 8 },
  meta: { fontSize: 11 },
  empty: { textAlign: 'center', marginTop: 48, paddingHorizontal: 24, fontSize: 15 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
});
