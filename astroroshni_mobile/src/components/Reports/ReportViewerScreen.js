import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, StatusBar, Alert, Linking } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { WebView } from 'react-native-webview';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { downloadPdfToLocalUri, sharePDFOnWhatsApp } from '../../utils/pdfGenerator';

export default function ReportViewerScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const pdfUri = route?.params?.pdfUri || '';
  const pdfUrl = route?.params?.pdfUrl || '';
  const title = route?.params?.title || t('reports.viewerTitle', 'Your report');
  const subtitle = route?.params?.subtitle || t('reports.viewerSubtitle', 'Open the generated PDF inside the app.');
  const [loadError, setLoadError] = useState('');
  const [webReady, setWebReady] = useState(false);

  const viewerSource = useMemo(() => {
    if (!pdfUrl) return pdfUri;
    return `https://docs.google.com/gview?embedded=1&url=${encodeURIComponent(pdfUrl)}`;
  }, [pdfUri, pdfUrl]);

  const canShare = useMemo(() => Boolean(pdfUri || pdfUrl), [pdfUri, pdfUrl]);

  useEffect(() => {
    setLoadError('');
    setWebReady(false);
  }, [pdfUri, pdfUrl]);

  const ensureShareableUri = async () => {
    if (pdfUri) return pdfUri;
    if (!pdfUrl) {
      throw new Error(t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.'));
    }
    const localUri = await downloadPdfToLocalUri(pdfUrl, 'report-viewer');
    return localUri;
  };

  const openExternally = async () => {
    try {
      if (!pdfUri && !pdfUrl) {
        throw new Error(t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.'));
      }
      const target = pdfUrl || pdfUri;
      const supported = await Linking.canOpenURL(target);
      if (!supported) {
        await Linking.openURL(target);
        return;
      }
      await Linking.openURL(target);
    } catch (error) {
      Alert.alert(
        t('reports.pdfErrorTitle', 'PDF error'),
        t('reports.pdfErrorBody', { message: error?.message || 'Unknown error' })
      );
    }
  };

  const shareReport = async () => {
    try {
      if (!pdfUri && !pdfUrl) {
        throw new Error(t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.'));
      }
      await sharePDFOnWhatsApp(await ensureShareableUri());
    } catch (error) {
      Alert.alert(
        t('reports.pdfErrorTitle', 'PDF error'),
        t('reports.pdfErrorBody', { message: error?.message || 'Unknown error' })
      );
    }
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
              <View style={[styles.badge, { backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : colors.surface }]}>
                <Ionicons name="document-text-outline" size={14} color={colors.primary} />
                <Text style={[styles.badgeText, { color: colors.text }]}>
                  {t('reports.openableLabel', 'Openable')}
                </Text>
              </View>
            </View>
            <View style={styles.headerTextWrap}>
              <Text style={[styles.title, { color: colors.text }]} numberOfLines={1} ellipsizeMode="tail">
                {title}
              </Text>
              <Text style={[styles.subtitle, { color: colors.textSecondary }]} numberOfLines={2} ellipsizeMode="tail">
                {subtitle}
              </Text>
            </View>
          </View>

          <View style={styles.actionRow}>
            <TouchableOpacity onPress={shareReport} disabled={!canShare} style={[styles.actionButton, !canShare && styles.actionButtonDisabled]}>
              <Text style={styles.actionButtonText}>{t('reports.sharePdf', 'Share PDF')}</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={openExternally} disabled={!canShare} style={[styles.actionButtonSecondary, { borderColor: colors.cardBorder, backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface }, !canShare && styles.actionButtonDisabled]}>
              <Text style={[styles.actionButtonSecondaryText, { color: colors.text }]}>{t('reports.openExternally', 'Open externally')}</Text>
            </TouchableOpacity>
          </View>

          <View style={[styles.viewerShell, { backgroundColor: isDark ? 'rgba(255,255,255,0.04)' : colors.surface, borderColor: colors.cardBorder }]}>
            {viewerSource ? (
              <WebView
                key={viewerSource}
                source={{ uri: viewerSource }}
                style={styles.webView}
                originWhitelist={['*']}
                javaScriptEnabled
                domStorageEnabled
                allowFileAccess
                allowFileAccessFromFileURLs
                allowUniversalAccessFromFileURLs
                onLoadEnd={() => setWebReady(true)}
                onError={(event) => {
                  setLoadError(event?.nativeEvent?.description || t('reports.pdfPreviewError', 'Could not preview the PDF on this device.'));
                }}
              />
            ) : (
              <View style={styles.emptyState}>
                <Ionicons name="document-outline" size={34} color={colors.textSecondary} />
                <Text style={[styles.emptyStateText, { color: colors.textSecondary }]}>
                  {t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.')}
                </Text>
              </View>
            )}
            {!webReady && viewerSource && !loadError ? (
              <View style={[styles.loadingOverlay, { backgroundColor: isDark ? '#0f172a' : '#fff' }]}>
                <Ionicons name="sparkles" size={20} color={colors.primary} />
                <Text style={[styles.loadingText, { color: colors.text }]}>{t('reports.viewerLoading', 'Loading report...')}</Text>
              </View>
            ) : null}
          </View>

          {loadError ? (
            <View style={[styles.errorCard, { backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface, borderColor: colors.cardBorder }]}>
              <Ionicons name="alert-circle-outline" size={18} color="#f43f5e" />
              <Text style={[styles.errorText, { color: colors.textSecondary }]}>{loadError}</Text>
            </View>
          ) : null}
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1, paddingHorizontal: 16, paddingTop: 8, paddingBottom: 12 },
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
  headerTextWrap: {
    flex: 1,
    minWidth: 0,
    paddingRight: 4,
  },
  title: { fontSize: 20, fontWeight: '900' },
  subtitle: { fontSize: 12, marginTop: 2, lineHeight: 16 },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 999,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  badgeText: { fontSize: 11, fontWeight: '900' },
  actionRow: { flexDirection: 'row', gap: 10, marginBottom: 12 },
  actionButton: {
    flex: 1,
    backgroundColor: '#fb7185',
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 13,
  },
  actionButtonSecondary: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 13,
  },
  actionButtonText: { color: '#fff', fontWeight: '900', fontSize: 13 },
  actionButtonSecondaryText: { fontWeight: '900', fontSize: 13 },
  actionButtonDisabled: { opacity: 0.6 },
  viewerShell: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 22,
    overflow: 'hidden',
  },
  webView: { flex: 1, backgroundColor: 'transparent' },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  loadingText: { fontSize: 13, fontWeight: '800' },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    padding: 24,
  },
  emptyStateText: { textAlign: 'center', fontSize: 13, lineHeight: 18, fontWeight: '700' },
  errorCard: {
    marginTop: 12,
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
    flexDirection: 'row',
    gap: 10,
    alignItems: 'center',
  },
  errorText: { flex: 1, fontSize: 12, lineHeight: 17, fontWeight: '700' },
});
