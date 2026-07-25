import React, { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import WebView from '../../platform/AppWebView';
import { useTheme } from '../../context/ThemeContext';
import { normalizeHttpsUrl } from '../../utils/blogLinks';

export default function BlogLinkScreen({ route, navigation }) {
  const { colors } = useTheme();
  const url = useMemo(() => normalizeHttpsUrl(route.params?.url), [route.params?.url]);
  const screenTitle = String(route.params?.title || 'AstroRoshni').trim() || 'AstroRoshni';
  const [loading, setLoading] = useState(!!url);
  const [failed, setFailed] = useState(false);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top']}>
      <View style={[styles.header, { borderBottomColor: colors.cardBorder }]}>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Go back"
          onPress={() => navigation.goBack()}
          style={styles.backButton}
        >
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.text }]} numberOfLines={1}>
          {screenTitle}
        </Text>
        <View style={styles.headerSpacer} />
      </View>

      {!url || failed ? (
        <View style={styles.message}>
          <Text style={[styles.messageTitle, { color: colors.text }]}>
            This article could not be opened
          </Text>
          <Text style={[styles.messageBody, { color: colors.textSecondary }]}>
            The blog link is invalid or temporarily unavailable.
          </Text>
        </View>
      ) : (
        <View style={styles.content}>
          <WebView
            source={{ uri: url }}
            style={styles.webView}
            originWhitelist={['https://*']}
            javaScriptEnabled
            domStorageEnabled
            startInLoadingState
            onLoadEnd={() => setLoading(false)}
            onError={() => {
              setLoading(false);
              setFailed(true);
            }}
            onHttpError={(event) => {
              if (Number(event?.nativeEvent?.statusCode || 0) >= 400) {
                setLoading(false);
                setFailed(true);
              }
            }}
          />
          {loading ? (
            <View style={[styles.loader, { backgroundColor: colors.background }]}>
              <ActivityIndicator size="large" color="#ff6b35" />
            </View>
          ) : null}
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backButton: {
    width: 56,
    height: 56,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    flex: 1,
    textAlign: 'center',
    fontSize: 18,
    fontWeight: '700',
  },
  headerSpacer: { width: 56 },
  content: { flex: 1 },
  webView: { flex: 1 },
  loader: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
  },
  message: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  messageTitle: { fontSize: 18, fontWeight: '700', textAlign: 'center' },
  messageBody: { marginTop: 8, fontSize: 15, lineHeight: 22, textAlign: 'center' },
});
