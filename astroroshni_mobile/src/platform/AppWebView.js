import React from 'react';
import { View, StyleSheet, Platform } from 'react-native';

/**
 * Cross-platform WebView: native uses react-native-webview; web uses an iframe.
 * Props mirror the common react-native-webview subset used in this app.
 */
export default function AppWebView({
  source,
  style,
  onLoadEnd,
  onError,
  onHttpError,
  originWhitelist,
  mixedContentMode,
  javaScriptEnabled,
  domStorageEnabled,
  startInLoadingState,
  scalesPageToFit,
  ...rest
}) {
  if (Platform.OS !== 'web') {
    // Lazy require keeps the native module out of the web graph when Metro
    // resolves this file for native; for web we never enter this branch.
    const { WebView } = require('react-native-webview');
    return (
      <WebView
        source={source}
        style={style}
        onLoadEnd={onLoadEnd}
        onError={onError}
        onHttpError={onHttpError}
        originWhitelist={originWhitelist}
        mixedContentMode={mixedContentMode}
        javaScriptEnabled={javaScriptEnabled}
        domStorageEnabled={domStorageEnabled}
        startInLoadingState={startInLoadingState}
        scalesPageToFit={scalesPageToFit}
        {...rest}
      />
    );
  }

  const uri = source?.uri || (typeof source?.html === 'string' ? null : null);
  const html = source?.html;

  if (html) {
    return (
      <View style={[styles.fill, style]}>
        <iframe
          title="AstroRoshni content"
          srcDoc={html}
          style={styles.iframe}
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
          onLoad={() => onLoadEnd?.({ nativeEvent: {} })}
        />
      </View>
    );
  }

  if (!uri) {
    return <View style={[styles.fill, style]} />;
  }

  // Sandboxed iframes often cannot host the browser PDF viewer (blank frame).
  // Leave http(s)/blob PDF embeds unsandboxed; keep sandbox for other pages.
  const looksLikePdf =
    typeof uri === 'string' &&
    (uri.startsWith('blob:') ||
      /\.pdf(\?|#|$)/i.test(uri) ||
      /storage\.googleapis\.com/i.test(uri));

  return (
    <View style={[styles.fill, style]}>
      <iframe
        title="AstroRoshni content"
        src={uri}
        style={styles.iframe}
        {...(looksLikePdf
          ? {}
          : {
              sandbox:
                'allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox',
            })}
        onLoad={() => onLoadEnd?.({ nativeEvent: {} })}
        onError={() =>
          onError?.({ nativeEvent: { description: 'Failed to load content' } })
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  fill: {
    flex: 1,
    width: '100%',
    height: '100%',
    overflow: 'hidden',
  },
  iframe: {
    border: 'none',
    width: '100%',
    height: '100%',
  },
});
