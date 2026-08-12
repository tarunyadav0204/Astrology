import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
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
import { goBackOrHome } from '../../navigation/navHelpers';
import FocusedStatusBar from '../Common/FocusedStatusBar';

const STATUS_META = {
  completed: { icon: 'checkmark-circle', tone: 'success' },
  processing: { icon: 'hourglass-outline', tone: 'warning' },
  pending: { icon: 'time-outline', tone: 'warning' },
  failed: { icon: 'close-circle', tone: 'error' },
};

const REPORT_TYPE_META = {
  partnership: { icon: 'people-outline' },
  career: { icon: 'briefcase-outline' },
  wealth: { icon: 'wallet-outline' },
  health: { icon: 'fitness-outline' },
  progeny: { icon: 'happy-outline' },
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
  const { colors } = useTheme();
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
    const statusColor = colors[statusMeta.tone] || colors.primary;
    const isOpening = openingId === item.report_id;
    const dateLabel = formatDate(item.completed_at || item.created_at, i18n.language === 'en' ? 'en-IN' : undefined);
    return (
      <View style={[styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
        <View style={styles.cardTopRow}>
          <View style={[styles.iconWrap, { backgroundColor: colors.accentSoft }]}>
            <Ionicons name={reportMeta.icon} size={22} color={colors.onAccent} />
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
              <View style={[styles.statusPill, { backgroundColor: colors.surfaceMuted }]}>
                <Ionicons name={statusMeta.icon} size={12} color={statusColor} />
                <Text style={[styles.statusText, { color: statusColor }]}>
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
            style={[styles.primaryButton, { backgroundColor: colors.primary }, (isOpening || normalize(item.status) !== 'completed') && styles.disabledButton]}
          >
            {isOpening ? (
              <ActivityIndicator color={colors.onPrimary} />
            ) : (
              <Text style={[styles.primaryButtonText, { color: colors.onPrimary }]}>{t('reports.openPdf', 'Open PDF')}</Text>
            )}
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => shareReport(item)}
            disabled={isOpening || normalize(item.status) !== 'completed'}
            style={[styles.secondaryButton, { borderColor: colors.cardBorder, backgroundColor: colors.surface }, (isOpening || normalize(item.status) !== 'completed') && styles.disabledButton]}
          >
            <Text style={[styles.secondaryButtonText, { color: colors.text }]}>{t('reports.sharePdf', 'Share PDF')}</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <FocusedStatusBar backgroundColor={colors.headerSurface} />
      <LinearGradient colors={[colors.background, colors.backgroundSecondary, colors.background]} style={styles.gradient}>
        <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.headerSurface }]} edges={['top']}>
          <View
            style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cardBorder }]}
          >
            <TouchableOpacity
              onPress={() => goBackOrHome(navigation)}
              style={[styles.backButton, { borderColor: colors.cosmicLine || colors.cardBorder }]}
            >
              <Ionicons name="arrow-back" size={22} color={colors.textInverse} />
            </TouchableOpacity>
            <View style={styles.headerTextWrap}>
              <Text style={[styles.headerEyebrow, { color: colors.accent }]}>{t('historyUi.library')}</Text>
              <Text style={[styles.headerTitle, { color: colors.textInverse }]} numberOfLines={1} ellipsizeMode="tail">
                {t('reports.historyTitle', 'Report History')}
              </Text>
            </View>
            <View style={[styles.headerBadge, { backgroundColor: colors.accentSoft }]}>
              <Text style={[styles.headerBadgeText, { color: colors.onAccent }]}>{history.length}</Text>
            </View>
          </View>

          <View style={[styles.contentShell, { backgroundColor: colors.background }]}>
          <View style={styles.intro}>
            <Text style={[styles.introTitle, { color: colors.text }]}>{t('historyUi.report.heroTitle')}</Text>
            <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>{t('reports.historySubtitle', 'Open past reports, share them again, or review what you already generated.')}</Text>
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
          </View>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  contentShell: { flex: 1 },
  header: {
    minHeight: 78,
    paddingHorizontal: 18,
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
  },
  backButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerBadge: {
    minWidth: 38,
    height: 34,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
    borderRadius: 17,
  },
  headerBadgeText: { fontSize: 13, fontWeight: '900' },
  headerTextWrap: {
    flex: 1,
    minWidth: 0,
    paddingHorizontal: 14,
  },
  headerEyebrow: { fontSize: 10, fontWeight: '900', letterSpacing: 2 },
  headerTitle: { fontSize: 23, fontFamily: 'serif', fontWeight: '600', marginTop: 2 },
  intro: { paddingHorizontal: 20, paddingTop: 24, paddingBottom: 20 },
  introTitle: { fontSize: 31, lineHeight: 36, fontFamily: 'serif', fontWeight: '500' },
  headerSubtitle: { fontSize: 14, marginTop: 8, lineHeight: 21, maxWidth: 470 },
  loadingState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: { fontSize: 13, fontWeight: '700' },
  listContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
    gap: 12,
  },
  emptyListContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: 20,
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
