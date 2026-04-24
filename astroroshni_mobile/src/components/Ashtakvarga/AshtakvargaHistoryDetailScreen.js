import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  StatusBar,
  StyleSheet,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';

export default function AshtakvargaHistoryDetailScreen({ navigation, route }) {
  const { theme, colors } = useTheme();
  const analysisId = route.params?.analysisId;
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDetail();
  }, [analysisId]);

  const loadDetail = async () => {
    setLoading(true);
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}${getEndpoint(`/ashtakavarga/oracle-history/${analysisId}`)}`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json().catch(() => ({}));
      if (response.ok) {
        setItem(data);
      } else {
        setItem(null);
      }
    } catch (_) {
      setItem(null);
    } finally {
      setLoading(false);
    }
  };

  const payload = item?.response_payload || {};
  const sections = Array.isArray(payload?.sections) ? payload.sections : [];

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
            <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1}>Saved Ashtakavarga Analysis</Text>
          </View>

          {loading ? (
            <View style={styles.centered}>
              <ActivityIndicator size="large" color={colors.primary} />
            </View>
          ) : !item ? (
            <View style={styles.centered}>
              <Text style={[styles.emptyTitle, { color: colors.text }]}>Analysis not found</Text>
              <Text style={[styles.emptySubtext, { color: colors.textSecondary }]}>
                This saved analysis could not be loaded.
              </Text>
            </View>
          ) : (
            <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
              <View style={[styles.card, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.82)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.16)' }]}>
                <Text style={[styles.question, { color: colors.text }]}>
                  {item.question_text || 'Ashtakavarga overview'}
                </Text>
                <Text style={[styles.meta, { color: colors.primary }]}>
                  {item.chart_type === 'transit' ? 'Transit overlay' : 'Natal baseline'} • {item.date}
                </Text>
                {payload?.headline ? (
                  <Text style={[styles.headline, { color: colors.textSecondary }]}>{payload.headline}</Text>
                ) : null}
              </View>

              {sections.map((section, index) => (
                <View
                  key={`${section.title}-${index}`}
                  style={[styles.card, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.82)', borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.16)' }]}
                >
                  <Text style={[styles.sectionTitle, { color: colors.text }]}>{section.title}</Text>
                  {(section.bullets || []).map((bullet, bulletIndex) => (
                    <Text key={`${section.title}-${bulletIndex}`} style={[styles.bullet, { color: colors.textSecondary }]}>
                      • {String(bullet)}
                    </Text>
                  ))}
                </View>
              ))}
            </ScrollView>
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
    marginRight: 12,
  },
  headerTitle: {
    flex: 1,
    fontSize: 20,
    fontWeight: '800',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  content: {
    padding: 20,
    paddingTop: 8,
  },
  card: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 16,
    marginBottom: 14,
  },
  question: {
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 8,
  },
  meta: {
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 10,
  },
  headline: {
    fontSize: 14,
    lineHeight: 21,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 8,
  },
  bullet: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 6,
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
