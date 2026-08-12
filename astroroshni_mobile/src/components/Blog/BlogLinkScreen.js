import React, { useMemo, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import WebView from '../../platform/AppWebView';
import { useTheme } from '../../context/ThemeContext';
import { normalizeHttpsUrl } from '../../utils/blogLinks';
import { goBackOrHome } from '../../navigation/navHelpers';
import FocusedStatusBar from '../Common/FocusedStatusBar';

export default function BlogLinkScreen({ route, navigation }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const url = useMemo(() => normalizeHttpsUrl(route.params?.url), [route.params?.url]);
  const screenTitle = String(route.params?.title || 'AstroRoshni').trim() || 'AstroRoshni';
  const [loading, setLoading] = useState(!!url);
  const [failed, setFailed] = useState(false);

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <FocusedStatusBar backgroundColor={colors.headerSurface} />
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.headerSurface }]} edges={['top']}>
        <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine || colors.cardBorder }]}>
          <TouchableOpacity accessibilityRole="button" accessibilityLabel={t('knowledgeSupport.back')} onPress={() => goBackOrHome(navigation)} style={[styles.headerButton, { borderColor: colors.cosmicLine || colors.cardBorder }]}>
            <Ionicons name="arrow-back" size={21} color={colors.textInverse} />
          </TouchableOpacity>
          <View style={styles.headerCopy}><Text style={[styles.eyebrow, { color: colors.accent }]}>{t('knowledgeSupport.article')}</Text><Text style={[styles.title, { color: colors.textInverse }]} numberOfLines={1}>{screenTitle}</Text></View>
          <View style={[styles.headerButton, { borderColor: colors.cosmicLine || colors.cardBorder }]}><Ionicons name="book-outline" size={19} color={colors.accent} /></View>
        </View>
        <View style={[styles.contentShell, { backgroundColor: colors.background }]}>
        {!url || failed ? (
          <View style={styles.message}>
            <View style={[styles.messageIcon, { backgroundColor: colors.accentSoft }]}><Ionicons name="cloud-offline-outline" size={27} color={colors.onAccent} /></View>
            <Text style={[styles.messageTitle, { color: colors.text }]}>{t('knowledgeSupport.articleUnavailable')}</Text>
            <Text style={[styles.messageBody, { color: colors.textSecondary }]}>{t('knowledgeSupport.articleUnavailableBody')}</Text>
            <TouchableOpacity onPress={() => goBackOrHome(navigation)} style={[styles.returnButton, { backgroundColor: colors.primary }]}><Text style={[styles.returnText, { color: colors.onPrimary }]}>{t('blog.goBack')}</Text></TouchableOpacity>
          </View>
        ) : (
          <View style={styles.content}>
            <WebView source={{ uri: url }} style={styles.webView} originWhitelist={['https://*']} javaScriptEnabled domStorageEnabled startInLoadingState onLoadEnd={() => setLoading(false)} onError={() => { setLoading(false); setFailed(true); }} onHttpError={(event) => { if (Number(event?.nativeEvent?.statusCode || 0) >= 400) { setLoading(false); setFailed(true); } }} />
            {loading ? <View style={[styles.loader, { backgroundColor: colors.background }]}><ActivityIndicator size="large" color={colors.primary} /><Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('knowledgeSupport.openingArticle')}</Text></View> : null}
          </View>
        )}
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 }, safeArea: { flex: 1 }, contentShell: { flex: 1 }, header: { minHeight: 78, paddingHorizontal: 18, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1 },
  headerButton: { width: 42, height: 42, borderRadius: 21, borderWidth: 1, alignItems: 'center', justifyContent: 'center' }, headerCopy: { flex: 1, paddingHorizontal: 14 },
  eyebrow: { fontSize: 9, fontWeight: '900', letterSpacing: 1.7 }, title: { fontSize: 19, fontWeight: '700', marginTop: 2 }, content: { flex: 1 }, webView: { flex: 1 },
  loader: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center', gap: 12 }, loadingText: { fontSize: 13, fontWeight: '700' }, message: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 34 },
  messageIcon: { width: 62, height: 62, borderRadius: 22, alignItems: 'center', justifyContent: 'center', marginBottom: 18 }, messageTitle: { fontSize: 24, fontFamily: 'serif', textAlign: 'center' },
  messageBody: { marginTop: 10, fontSize: 15, lineHeight: 22, textAlign: 'center' }, returnButton: { minHeight: 48, borderRadius: 17, paddingHorizontal: 24, alignItems: 'center', justifyContent: 'center', marginTop: 22 }, returnText: { fontSize: 14, fontWeight: '900' },
});
