import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  StatusBar,
  StyleSheet,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';

export default function AshtakvargaHistoryScreen({ navigation }) {
  const { theme, colors } = useTheme();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadHistory = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/ashtakavarga/oracle-history')}?limit=100`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json().catch(() => ({}));
      if (response.ok) {
        setItems(Array.isArray(data?.items) ? data.items : []);
      } else {
        setItems([]);
      }
    } catch (_) {
      setItems([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const renderItem = ({ item }) => {
    const payload = item?.response_payload || {};
    const headline = payload?.headline || payload?.oracle_message || 'Saved Ashtakavarga analysis';
    const label = item.question_text || 'Ashtakavarga overview';
    return (
      <TouchableOpacity
        style={[
          styles.card,
          {
            backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.85)',
            borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.15)',
          },
        ]}
        onPress={() => navigation.navigate('AshtakvargaHistoryDetail', { analysisId: item.id })}
      >
        <View style={styles.cardHeader}>
          <Text style={[styles.cardTitle, { color: colors.text }]} numberOfLines={2}>{label}</Text>
          <Ionicons name="chevron-forward" size={18} color={colors.textSecondary} />
        </View>
        <Text style={[styles.cardMeta, { color: colors.primary }]}>
          {item.chart_type === 'transit' ? 'Transit overlay' : 'Natal baseline'} • {item.date}
        </Text>
        <Text style={[styles.cardHeadline, { color: colors.textSecondary }]} numberOfLines={3}>
          {headline}
        </Text>
      </TouchableOpacity>
    );
  };

  return (
    <View style={{ flex: 1 }}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
      <LinearGradient
        colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.primary] : [colors.gradientStart, colors.gradientStart, colors.gradientStart, colors.gradientStart]}
        style={{ flex: 1 }}
      >
        <SafeAreaView style={{ flex: 1 }}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={colors.text} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]}>Ashtakavarga History</Text>
            <View style={styles.headerSpacer} />
          </View>

          {loading ? (
            <View style={styles.centered}>
              <ActivityIndicator size="large" color={colors.primary} />
            </View>
          ) : (
            <FlatList
              data={items}
              keyExtractor={(item) => String(item.id)}
              renderItem={renderItem}
              contentContainerStyle={items.length === 0 ? styles.emptyContainer : styles.listContent}
              refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => loadHistory(true)} />}
              ListEmptyComponent={
                <View style={styles.centered}>
                  <Text style={[styles.emptyTitle, { color: colors.text }]}>No Ashtakavarga history yet</Text>
                  <Text style={[styles.emptySubtext, { color: colors.textSecondary }]}>
                    Questions you ask in Ashtakavarga Analysis will appear here.
                  </Text>
                </View>
              }
            />
          )}
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    flex: 1,
    fontSize: 20,
    fontWeight: '800',
    marginLeft: 12,
  },
  headerSpacer: {
    width: 40,
  },
  listContent: {
    padding: 20,
    paddingTop: 8,
  },
  card: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 16,
    marginBottom: 14,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  cardTitle: {
    flex: 1,
    fontSize: 16,
    fontWeight: '800',
    marginRight: 10,
  },
  cardMeta: {
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 8,
  },
  cardHeadline: {
    fontSize: 14,
    lineHeight: 21,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  emptyContainer: {
    flexGrow: 1,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    lineHeight: 21,
    textAlign: 'center',
  },
});
