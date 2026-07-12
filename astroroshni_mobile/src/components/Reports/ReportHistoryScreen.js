import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  FlatList,
  RefreshControl,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import { reportAPI } from '../../services/api';
import { storage } from '../../services/storage';
import { downloadPdfToLocalUri, sharePDFOnWhatsApp } from '../../utils/pdfGenerator';

const STATUS_META = {
  completed: { icon: 'checkmark-circle', tint: '#22c55e' },
  processing: { icon: 'hourglass-outline', tint: '#f59e0b' },
  pending: { icon: 'time-outline', tint: '#f59e0b' },
  failed: { icon: 'close-circle', tint: '#f43f5e' },
};

const REPORT_TYPE_META = {
  partnership: { icon: '💞', gradient: ['#fb7185', '#f97316'] },
  career: { icon: '💼', gradient: ['#6366F1', '#8B5CF6'] },
  wealth: { icon: '💰', gradient: ['#0EA5E9', '#38BDF8'] },
  health: { icon: '🏥', gradient: ['#22c55e', '#15803d'] },
  progeny: { icon: '👶', gradient: ['#ec4899', '#a855f7'] },
};

const normalize = (value) => String(value || '').trim().toLowerCase();

const buildReportPdfFileName = (reportId) => `report-${String(reportId || 'latest').replace(/[^a-zA-Z0-9_-]+/g, '_')}`;

const formatDate = (value, locale = 'en-IN') => {
  if (!value) return '';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(parsed);
};

export default function ReportHistoryScreen({ navigation }) {
  useAnalytics('ReportHistoryScreen');
  const { t, i18n } = useTranslation();
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [openingId, setOpeningId] = useState(null);

  const loadHistory = useCallback(async () => {
    try {
      const token = await storage.getAuthToken();
      if (!token) {
        setHistory([]);
        return;
      }
      const res = await reportAPI.getHistory({ limit: 100, offset: 0 });
      const items = res?.data?.data || [];
      setHistory(Array.isArray(items) ? items : []);
    } catch (error) {
      const status = error?.response?.status;
      if (status !== 404) {
        console.error('[ReportHistory] load failed', error);
      }
      setHistory([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const onRefresh = () => {
    setRefreshing(true);
    loadHistory();
  };

  const resolvePdfUrl = async (reportId) => {
    const response = await reportAPI.getReportPdfUrl(reportId);
    return response?.data?.pdf_url || '';
  };

  const loadPdfToDevice = async (reportId, pdfUrl) => {
    const localUri = await downloadPdfToLocalUri(pdfUrl, buildReportPdfFileName(reportId));
    return localUri;
  };

  const openReport = async (item) => {
    if (normalize(item.status) !== 'completed') {
      Alert.alert(
        t('reports.historyNotReadyTitle', 'Report not ready'),
        t('reports.historyNotReadyBody', 'This report is still being prepared.')
      );
      return;
    }

    try {
      setOpeningId(item.report_id);
      const pdfUrl = await resolvePdfUrl(item.report_id);
      if (!pdfUrl) {
        throw new Error('PDF URL unavailable');
      }
      const pdfUri = await loadPdfToDevice(item.report_id, pdfUrl);
      const reportTitle = item.title || t('reports.viewerTitle', 'Your report');
      navigation.navigate('ReportViewer', {
        pdfUri,
        pdfUrl,
        title: reportTitle,
        subtitle: item.person_a_name && item.person_b_name
          ? `${item.person_a_name} vs ${item.person_b_name}`
          : t('reports.viewerSubtitle', 'Open the generated PDF inside the app.'),
      });
    } catch (error) {
      console.error('[ReportHistory] open failed', error);
      Alert.alert(
        t('reports.pdfErrorTitle', 'PDF error'),
        t('reports.pdfErrorBody', {
          defaultValue: `We could not load the PDF right now. ${error?.message || 'Unknown error'}`,
          message: error?.message || 'Unknown error',
        })
      );
    } finally {
      setOpeningId(null);
    }
  };

  const shareReport = async (item) => {
    if (normalize(item.status) !== 'completed') {
      Alert.alert(
        t('reports.historyNotReadyTitle', 'Report not ready'),
        t('reports.historyNotReadyBody', 'This report is still being prepared.')
      );
      return;
    }

    try {
      setOpeningId(item.report_id);
      const pdfUrl = await resolvePdfUrl(item.report_id);
      if (!pdfUrl) {
        throw new Error('PDF URL unavailable');
      }
      const pdfUri = await loadPdfToDevice(item.report_id, pdfUrl);
      await sharePDFOnWhatsApp(pdfUri);
    } catch (error) {
      console.error('[ReportHistory] share failed', error);
      Alert.alert(
        t('reports.pdfErrorTitle', 'PDF error'),
        t('reports.pdfErrorBody', {
          defaultValue: `We could not load the PDF right now. ${error?.message || 'Unknown error'}`,
          message: error?.message || 'Unknown error',
        })
      );
    } finally {
      setOpeningId(null);
    }
  };

  const renderItem = ({ item }) => {
    const reportMeta = REPORT_TYPE_META[item.report_type] || REPORT_TYPE_META.partnership;
    const statusMeta = STATUS_META[normalize(item.status)] || STATUS_META.pending;
    const isOpening = openingId === item.report_id;
    const dateLabel = formatDate(item.completed_at || item.created_at, i18n.language === 'en' ? 'en-IN' : undefined);
    return (
      <View style={[styles.card, { backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface, borderColor: colors.cardBorder }]}>
        <View style={styles.cardTopRow}>
          <View style={[styles.iconWrap, { backgroundColor: `${reportMeta.gradient[0]}18` }]}>
            <Text style={styles.iconText}>{reportMeta.icon}</Text>
          </View>
          <View style={styles.cardBody}>
            <Text style={[styles.cardTitle, { color: colors.text }]} numberOfLines={1}>
              {item.title || t('reports.viewerTitle', 'Your report')}
            </Text>
            <Text style={[styles.cardSubtitle, { color: colors.textSecondary }]} numberOfLines={2}>
              {item.person_a_name && item.person_b_name
                ? `${item.person_a_name} vs ${item.person_b_name}`
                : item.subtitle || t('reports.historySubtitleFallback', 'Generated report')}
            </Text>
            <View style={styles.metaRow}>
              <View style={[styles.statusPill, { backgroundColor: `${statusMeta.tint}18` }]}>
                <Ionicons name={statusMeta.icon} size={12} color={statusMeta.tint} />
                <Text style={[styles.statusText, { color: statusMeta.tint }]}>
                  {t(`reports.status.${normalize(item.status)}`, item.status || 'pending')}
                </Text>
              </View>
              {item.language ? (
                <View style={[styles.languagePill, { borderColor: colors.cardBorder }]}>
                  <Text style={[styles.languagePillText, { color: colors.textSecondary }]}>{String(item.language).toUpperCase()}</Text>
                </View>
              ) : null}
            </View>
            <Text style={[styles.dateText, { color: colors.textTertiary }]}>
              {dateLabel}
            </Text>
          </View>
        </View>

        <View style={styles.actionRow}>
          <TouchableOpacity
            onPress={() => openReport(item)}
            disabled={isOpening || normalize(item.status) !== 'completed'}
            style={[styles.primaryButton, { backgroundColor: isDark ? colors.primary : colors.primary }, (isOpening || normalize(item.status) !== 'completed') && styles.disabledButton]}
          >
            {isOpening ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.primaryButtonText}>{t('reports.openPdf', 'Open PDF')}</Text>
            )}
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => shareReport(item)}
            disabled={isOpening || normalize(item.status) !== 'completed'}
            style={[styles.secondaryButton, { borderColor: colors.cardBorder, backgroundColor: isDark ? 'rgba(255,255,255,0.04)' : colors.surface }, (isOpening || normalize(item.status) !== 'completed') && styles.disabledButton]}
          >
            <Text style={[styles.secondaryButtonText, { color: colors.text }]}>{t('reports.sharePdf', 'Share PDF')}</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle={isDark ? 'light-content' : 'dark-content'} backgroundColor={colors.background} />
      <LinearGradient
        colors={isDark ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd] : [colors.background, colors.backgroundSecondary, colors.backgroundTertiary]}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <View style={styles.headerTopRow}>
              <TouchableOpacity
                onPress={() => navigation.goBack()}
                style={[styles.backButton, { backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : colors.surface }]}
              >
                <Ionicons name="arrow-back" size={22} color={colors.text} />
              </TouchableOpacity>
              <View style={[styles.headerBadge, { backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : colors.surface }]}>
                <Ionicons name="time-outline" size={14} color={colors.primary} />
                <Text style={[styles.headerBadgeText, { color: colors.text }]}>
                  {t('reports.historyTitle', 'Report History')}
                </Text>
              </View>
            </View>
            <View style={styles.headerTextWrap}>
              <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1} ellipsizeMode="tail">
                {t('reports.historyTitle', 'Report History')}
              </Text>
              <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]} numberOfLines={2} ellipsizeMode="tail">
                {t('reports.historySubtitle', 'Open past reports, share them again, or review what you already generated.')}
              </Text>
            </View>
          </View>

          {loading ? (
            <View style={styles.loadingState}>
              <ActivityIndicator size="large" color={colors.primary} />
              <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
                {t('reports.historyLoading', 'Loading report history...')}
              </Text>
            </View>
          ) : (
            <FlatList
              data={history}
              keyExtractor={(item) => String(item.report_id)}
              renderItem={renderItem}
              contentContainerStyle={history.length ? styles.listContent : styles.emptyListContent}
              refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
              ListEmptyComponent={(
                <View style={styles.emptyState}>
                  <View style={[styles.emptyIconWrap, { backgroundColor: `${colors.primary}18` }]}>
                    <Ionicons name="documents-outline" size={28} color={colors.primary} />
                  </View>
                  <Text style={[styles.emptyTitle, { color: colors.text }]}>
                    {t('reports.historyEmptyTitle', 'No reports yet')}
                  </Text>
                  <Text style={[styles.emptyBody, { color: colors.textSecondary }]}>
                    {t('reports.historyEmptyBody', 'When you generate a report, it will appear here so you can open it again later.')}
                  </Text>
                  <TouchableOpacity
                    onPress={() => navigation.navigate('ReportsStudio')}
                    style={[styles.emptyCta, { backgroundColor: colors.primary }]}
                  >
                    <Text style={styles.emptyCtaText}>
                      {t('reports.goToReports', 'Create a report')}
                    </Text>
                  </TouchableOpacity>
                </View>
              )}
            />
          )}
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1, paddingHorizontal: 16, paddingTop: 8 },
  header: {
    gap: 10,
    marginBottom: 14,
  },
  headerTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  backButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 18,
  },
  headerBadgeText: { fontSize: 11, fontWeight: '900' },
  headerTextWrap: {
    flex: 1,
    minWidth: 0,
    paddingRight: 4,
  },
  headerTitle: { fontSize: 20, fontWeight: '900' },
  headerSubtitle: { fontSize: 12, marginTop: 3, lineHeight: 17 },
  loadingState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: { fontSize: 13, fontWeight: '700' },
  listContent: {
    paddingBottom: 28,
    gap: 12,
  },
  emptyListContent: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  card: {
    borderWidth: 1,
    borderRadius: 22,
    padding: 14,
    gap: 14,
  },
  cardTopRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  iconWrap: {
    width: 50,
    height: 50,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconText: { fontSize: 22 },
  cardBody: { flex: 1 },
  cardTitle: { fontSize: 15, fontWeight: '900' },
  cardSubtitle: { fontSize: 12, marginTop: 4, lineHeight: 17 },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 10,
  },
  statusPill: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statusText: { fontSize: 11, fontWeight: '900', textTransform: 'capitalize' },
  languagePill: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 1,
  },
  languagePillText: { fontSize: 11, fontWeight: '900' },
  dateText: { marginTop: 8, fontSize: 11, fontWeight: '700' },
  actionRow: {
    flexDirection: 'row',
    gap: 10,
  },
  primaryButton: {
    flex: 1,
    minHeight: 46,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryButton: {
    flex: 1,
    minHeight: 46,
    borderRadius: 16,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButtonText: { color: '#fff', fontWeight: '900', fontSize: 13 },
  secondaryButtonText: { fontWeight: '900', fontSize: 13 },
  disabledButton: { opacity: 0.55 },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingVertical: 42,
    gap: 10,
  },
  emptyIconWrap: {
    width: 60,
    height: 60,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyTitle: { fontSize: 18, fontWeight: '900', textAlign: 'center' },
  emptyBody: { fontSize: 13, lineHeight: 19, textAlign: 'center' },
  emptyCta: {
    marginTop: 10,
    paddingHorizontal: 18,
    paddingVertical: 12,
    borderRadius: 16,
  },
  emptyCtaText: { color: '#fff', fontWeight: '900', fontSize: 13 },
});
