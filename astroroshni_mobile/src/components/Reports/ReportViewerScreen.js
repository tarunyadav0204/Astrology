import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  Alert,
  Linking,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { WebView } from 'react-native-webview';
import * as FileSystem from 'expo-file-system/legacy';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { downloadPdfToLocalUri, sharePDFOnWhatsApp } from '../../utils/pdfGenerator';

const LOAD_TIMEOUT_MS = 20000;
const MAX_BASE64_HTML_CHARS = 5_500_000;

function buildGviewUrl(remoteUrl) {
  return `https://docs.google.com/gview?embedded=1&url=${encodeURIComponent(remoteUrl)}&cb=${Date.now()}`;
}

function buildPdfJsHtml(base64Pdf, { isDark = true } = {}) {
  const bg = isDark ? '#111827' : '#f3f4f6';
  const statusColor = isDark ? '#d1d5db' : '#4b5563';
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=4" />
  <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
  <style>
    html, body { margin: 0; padding: 0; background: ${bg}; }
    #status { color: ${statusColor}; font: 600 14px/1.4 -apple-system, BlinkMacSystemFont, sans-serif; padding: 28px 20px; text-align: center; }
    #pages { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 12px; }
    canvas { width: 100%; max-width: 100%; height: auto; background: #fff; box-shadow: 0 8px 24px rgba(15,23,42,0.18); border-radius: 2px; }
  </style>
</head>
<body>
  <div id="status">Preparing pages…</div>
  <div id="pages"></div>
  <script>
    (function () {
      function post(msg) {
        try { window.ReactNativeWebView && window.ReactNativeWebView.postMessage(String(msg)); } catch (e) {}
      }
      try {
        pdfjsLib.GlobalWorkerOptions.workerSrc =
          'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        var raw = atob(${JSON.stringify(base64Pdf)});
        var bytes = new Uint8Array(raw.length);
        for (var i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
        pdfjsLib.getDocument({ data: bytes }).promise.then(async function (pdf) {
          var root = document.getElementById('pages');
          var status = document.getElementById('status');
          status.textContent = 'Rendering ' + pdf.numPages + ' pages…';
          for (var pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
            var page = await pdf.getPage(pageNum);
            var viewport = page.getViewport({ scale: 1.35 });
            var canvas = document.createElement('canvas');
            var ctx = canvas.getContext('2d');
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            root.appendChild(canvas);
            await page.render({ canvasContext: ctx, viewport: viewport }).promise;
          }
          status.style.display = 'none';
          post('ready');
        }).catch(function (err) {
          document.getElementById('status').textContent = 'Could not render PDF';
          post('error:' + (err && err.message ? err.message : 'render_failed'));
        });
      } catch (err) {
        document.getElementById('status').textContent = 'Could not open PDF';
        post('error:' + (err && err.message ? err.message : 'boot_failed'));
      }
    })();
  </script>
</body>
</html>`;
}

function ToolbarIcon({ onPress, disabled, icon, color, backgroundColor, accessibilityLabel }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      style={[
        styles.toolbarIcon,
        { backgroundColor },
        disabled && styles.toolbarIconDisabled,
      ]}
      hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
    >
      <Ionicons name={icon} size={20} color={color} />
    </TouchableOpacity>
  );
}

export default function ReportViewerScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const pdfUri = route?.params?.pdfUri || '';
  const pdfUrl = route?.params?.pdfUrl || '';
  const title = route?.params?.title || t('reports.viewerTitle', 'Your report');
  const subtitle = route?.params?.subtitle || '';
  const [loadError, setLoadError] = useState('');
  const [webReady, setWebReady] = useState(false);
  const [preparing, setPreparing] = useState(true);
  const [viewerSource, setViewerSource] = useState(null);
  const [sharing, setSharing] = useState(false);
  const loadTimerRef = useRef(null);

  const canShare = useMemo(() => Boolean(pdfUri || pdfUrl), [pdfUri, pdfUrl]);
  const chromeBg = isDark ? colors.background : colors.background;
  const surface = isDark ? 'rgba(255,255,255,0.06)' : colors.surface;
  const surfaceBorder = isDark ? 'rgba(255,255,255,0.1)' : colors.cardBorder;
  const iconMuted = colors.textSecondary;
  const pageBg = isDark ? '#0b1220' : '#e8eaef';

  const clearLoadTimer = () => {
    if (loadTimerRef.current) {
      clearTimeout(loadTimerRef.current);
      loadTimerRef.current = null;
    }
  };

  const markReady = useCallback(() => {
    clearLoadTimer();
    setWebReady(true);
    setPreparing(false);
  }, []);

  const markError = useCallback((message) => {
    clearLoadTimer();
    setLoadError(message || t('reports.pdfPreviewError', 'Could not preview the PDF on this device.'));
    setPreparing(false);
    setWebReady(false);
  }, [t]);

  const prepareViewer = useCallback(async () => {
    setLoadError('');
    setWebReady(false);
    setPreparing(true);
    setViewerSource(null);
    clearLoadTimer();

    try {
      if (!pdfUri && !pdfUrl) {
        markError(t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.'));
        return;
      }

      if (Platform.OS === 'ios' && pdfUri) {
        setViewerSource({ uri: pdfUri });
        setPreparing(false);
        loadTimerRef.current = setTimeout(() => {
          markError(t('reports.viewerLoadTimeout', 'Preview is taking too long. Try Open externally.'));
        }, LOAD_TIMEOUT_MS);
        return;
      }

      if (pdfUrl) {
        setViewerSource({ uri: buildGviewUrl(pdfUrl) });
        setPreparing(false);
        loadTimerRef.current = setTimeout(() => {
          markError(t('reports.viewerLoadTimeout', 'Preview is taking too long. Try Open externally.'));
        }, LOAD_TIMEOUT_MS);
        return;
      }

      const base64 = await FileSystem.readAsStringAsync(pdfUri, {
        encoding: FileSystem.EncodingType.Base64,
      });
      if (!base64 || base64.length > MAX_BASE64_HTML_CHARS) {
        markError(t('reports.viewerTooLarge', 'This PDF is too large to preview in-app. Use Open externally.'));
        return;
      }
      setViewerSource({ html: buildPdfJsHtml(base64, { isDark }), baseUrl: 'https://cdnjs.cloudflare.com/' });
      setPreparing(false);
      loadTimerRef.current = setTimeout(() => {
        markError(t('reports.viewerLoadTimeout', 'Preview is taking too long. Try Open externally.'));
      }, LOAD_TIMEOUT_MS);
    } catch (error) {
      console.error('[ReportViewer] prepare failed', error);
      markError(error?.message || t('reports.pdfPreviewError', 'Could not preview the PDF on this device.'));
    }
  }, [pdfUri, pdfUrl, isDark, markError, t]);

  useEffect(() => {
    prepareViewer();
    return () => clearLoadTimer();
  }, [prepareViewer]);

  const ensureShareableUri = async () => {
    if (pdfUri) return pdfUri;
    if (!pdfUrl) {
      throw new Error(t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.'));
    }
    return downloadPdfToLocalUri(pdfUrl, 'report-viewer');
  };

  const openExternally = async () => {
    try {
      if (!pdfUri && !pdfUrl) {
        throw new Error(t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.'));
      }
      await Linking.openURL(pdfUrl || pdfUri);
    } catch (error) {
      Alert.alert(
        t('reports.pdfErrorTitle', 'PDF error'),
        t('reports.pdfErrorBody', { message: error?.message || 'Unknown error' })
      );
    }
  };

  const shareReport = async () => {
    if (sharing) return;
    try {
      setSharing(true);
      if (!pdfUri && !pdfUrl) {
        throw new Error(t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.'));
      }
      await sharePDFOnWhatsApp(await ensureShareableUri());
    } catch (error) {
      Alert.alert(
        t('reports.pdfErrorTitle', 'PDF error'),
        t('reports.pdfErrorBody', { message: error?.message || 'Unknown error' })
      );
    } finally {
      setSharing(false);
    }
  };

  const showLoading = preparing || (!webReady && viewerSource && !loadError);
  const statusLabel = loadError
    ? t('reports.viewerStatusError', 'Preview unavailable')
    : webReady
      ? t('reports.viewerStatusReady', 'Ready')
      : t('reports.viewerStatusLoading', 'Loading');

  return (
    <View style={[styles.container, { backgroundColor: chromeBg }]}>
      <StatusBar barStyle={isDark ? 'light-content' : 'dark-content'} backgroundColor={chromeBg} />
      <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
        <View style={[styles.toolbar, { borderBottomColor: surfaceBorder }]}>
          <ToolbarIcon
            onPress={() => navigation.goBack()}
            icon="chevron-back"
            color={colors.text}
            backgroundColor={surface}
            accessibilityLabel={t('common.back', 'Back')}
          />

          <View style={styles.toolbarCenter}>
            <Text style={[styles.toolbarTitle, { color: colors.text }]} numberOfLines={1}>
              {title}
            </Text>
            {subtitle ? (
              <Text style={[styles.toolbarSubtitle, { color: colors.textSecondary }]} numberOfLines={1}>
                {subtitle}
              </Text>
            ) : null}
          </View>

          <View style={styles.toolbarActions}>
            <ToolbarIcon
              onPress={shareReport}
              disabled={!canShare || sharing}
              icon={sharing ? 'hourglass-outline' : 'share-outline'}
              color={colors.text}
              backgroundColor={surface}
              accessibilityLabel={t('reports.sharePdf', 'Share PDF')}
            />
            <ToolbarIcon
              onPress={openExternally}
              disabled={!canShare}
              icon="open-outline"
              color={colors.text}
              backgroundColor={surface}
              accessibilityLabel={t('reports.openExternally', 'Open externally')}
            />
          </View>
        </View>

        <View style={[styles.statusStrip, { backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(15,23,42,0.03)' }]}>
          <View style={[
            styles.statusDot,
            {
              backgroundColor: loadError
                ? '#f43f5e'
                : webReady
                  ? '#22c55e'
                  : colors.primary,
            },
          ]}
          />
          <Text style={[styles.statusText, { color: colors.textSecondary }]} numberOfLines={1}>
            {statusLabel}
          </Text>
          <Text style={[styles.statusHint, { color: colors.textTertiary || colors.textSecondary }]} numberOfLines={1}>
            {t('reports.viewerHint', 'Pinch to zoom · Share anytime')}
          </Text>
        </View>

        <View style={[styles.viewerShell, { backgroundColor: pageBg }]}>
          {viewerSource ? (
            <WebView
              key={viewerSource.uri || 'pdf-html'}
              source={viewerSource}
              style={styles.webView}
              originWhitelist={['*']}
              javaScriptEnabled
              domStorageEnabled
              mixedContentMode="always"
              allowFileAccess
              allowFileAccessFromFileURLs
              allowUniversalAccessFromFileURLs
              setSupportMultipleWindows={false}
              startInLoadingState={false}
              onLoadEnd={() => {
                if (viewerSource?.html) return;
                markReady();
              }}
              onMessage={(event) => {
                const data = String(event?.nativeEvent?.data || '');
                if (data === 'ready') {
                  markReady();
                  return;
                }
                if (data.startsWith('error:')) {
                  markError(data.slice(6) || t('reports.pdfPreviewError', 'Could not preview the PDF on this device.'));
                }
              }}
              onError={(event) => {
                markError(event?.nativeEvent?.description || t('reports.pdfPreviewError', 'Could not preview the PDF on this device.'));
              }}
              onHttpError={() => {
                markError(t('reports.pdfPreviewError', 'Could not preview the PDF on this device.'));
              }}
            />
          ) : !preparing ? (
            <View style={styles.emptyState}>
              <View style={[styles.emptyIconWrap, { backgroundColor: surface }]}>
                <Ionicons name="document-text-outline" size={28} color={iconMuted} />
              </View>
              <Text style={[styles.emptyTitle, { color: colors.text }]}>
                {t('reports.viewerEmptyTitle', 'Preview unavailable')}
              </Text>
              <Text style={[styles.emptyBody, { color: colors.textSecondary }]}>
                {loadError || t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.')}
              </Text>
              {canShare ? (
                <TouchableOpacity
                  onPress={openExternally}
                  style={styles.emptyCta}
                  accessibilityRole="button"
                >
                  <Ionicons name="open-outline" size={16} color="#fff" />
                  <Text style={styles.emptyCtaText}>{t('reports.openExternally', 'Open externally')}</Text>
                </TouchableOpacity>
              ) : null}
            </View>
          ) : null}

          {showLoading ? (
            <View style={[styles.loadingOverlay, { backgroundColor: pageBg }]}>
              <View style={[styles.loadingCard, { backgroundColor: isDark ? 'rgba(15,23,42,0.92)' : '#fff', borderColor: surfaceBorder }]}>
                <ActivityIndicator size="small" color={colors.primary} />
                <Text style={[styles.loadingTitle, { color: colors.text }]}>
                  {t('reports.viewerLoading', 'Loading report...')}
                </Text>
                <Text style={[styles.loadingBody, { color: colors.textSecondary }]}>
                  {t('reports.viewerLoadingHint', 'Preparing a clean preview of your PDF.')}
                </Text>
              </View>
            </View>
          ) : null}
        </View>

        {loadError && viewerSource ? (
          <SafeAreaView edges={['bottom']} style={[styles.errorBar, { backgroundColor: isDark ? '#1f2937' : '#fff7ed', borderTopColor: surfaceBorder }]}>
            <Ionicons name="alert-circle" size={18} color="#ea580c" />
            <Text style={[styles.errorBarText, { color: isDark ? '#fed7aa' : '#9a3412' }]} numberOfLines={2}>
              {loadError}
            </Text>
            <TouchableOpacity onPress={openExternally} style={styles.errorBarButton}>
              <Text style={styles.errorBarButtonText}>{t('reports.openExternally', 'Open externally')}</Text>
            </TouchableOpacity>
          </SafeAreaView>
        ) : (
          <SafeAreaView edges={['bottom']} style={{ backgroundColor: pageBg }} />
        )}
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  toolbar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  toolbarCenter: {
    flex: 1,
    minWidth: 0,
  },
  toolbarTitle: {
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: -0.2,
  },
  toolbarSubtitle: {
    fontSize: 12,
    marginTop: 2,
    fontWeight: '500',
  },
  toolbarActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  toolbarIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  toolbarIconDisabled: { opacity: 0.45 },
  statusStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  statusDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  statusHint: {
    flex: 1,
    textAlign: 'right',
    fontSize: 11,
    fontWeight: '500',
    opacity: 0.85,
  },
  viewerShell: {
    flex: 1,
    overflow: 'hidden',
  },
  webView: { flex: 1, backgroundColor: 'transparent' },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 28,
  },
  loadingCard: {
    width: '100%',
    maxWidth: 320,
    borderRadius: 18,
    borderWidth: StyleSheet.hairlineWidth,
    paddingVertical: 22,
    paddingHorizontal: 20,
    alignItems: 'center',
    gap: 8,
  },
  loadingTitle: {
    fontSize: 15,
    fontWeight: '700',
    marginTop: 4,
  },
  loadingBody: {
    fontSize: 12,
    lineHeight: 17,
    textAlign: 'center',
    fontWeight: '500',
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    gap: 10,
  },
  emptyIconWrap: {
    width: 64,
    height: 64,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  emptyTitle: {
    fontSize: 17,
    fontWeight: '700',
  },
  emptyBody: {
    fontSize: 13,
    lineHeight: 19,
    textAlign: 'center',
    fontWeight: '500',
  },
  emptyCta: {
    marginTop: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#ea580c',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  emptyCtaText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '700',
  },
  errorBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 14,
    paddingTop: 12,
    paddingBottom: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  errorBarText: {
    flex: 1,
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '600',
  },
  errorBarButton: {
    backgroundColor: '#ea580c',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  errorBarButtonText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
  },
});
