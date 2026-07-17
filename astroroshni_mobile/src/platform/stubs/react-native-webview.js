import React from 'react';
import { View, StyleSheet } from 'react-native';

function WebView({ source, style, onLoadEnd, onError }) {
  const uri = source?.uri;
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

  if (!uri) return <View style={[styles.fill, style]} />;

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
  fill: { flex: 1, width: '100%', height: '100%', overflow: 'hidden' },
  iframe: { border: 'none', width: '100%', height: '100%' },
});

module.exports = {
  __esModule: true,
  default: WebView,
  WebView,
};
