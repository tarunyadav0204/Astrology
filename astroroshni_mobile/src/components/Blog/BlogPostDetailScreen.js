import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Image,
  Dimensions,
  StatusBar,
  Share,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { WebView } from 'react-native-webview';
import { blogAPI } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';
import { COLORS } from '../../utils/constants';

const { width } = Dimensions.get('window');

export default function BlogPostDetailScreen({ route, navigation }) {
  const { slug } = route.params;
  const { theme, colors } = useTheme();
  const insets = useSafeAreaInsets();
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [webViewHeight, setWebViewHeight] = useState(600);

  useEffect(() => {
    fetchPost();
  }, [slug]);

  const fetchPost = async () => {
    try {
      setLoading(true);
      const response = await blogAPI.getPostBySlug(slug);
      setPost(response.data);
    } catch (error) {
      console.error('Error fetching blog post:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    if (!post) return;
    try {
      await Share.share({
        message: `Check out this article on AstroRoshni: ${post.title}\n\nhttps://astroroshni.com/blog/${post.slug}`,
        url: `https://astroroshni.com/blog/${post.slug}`,
        title: post.title,
      });
    } catch (error) {
      console.error('Error sharing post:', error);
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color="#ff6b35" style={styles.loader} />
      </View>
    );
  }

  if (!post) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background, justifyContent: 'center', alignItems: 'center' }]}>
        <Text style={{ color: colors.textSecondary }}>Post not found</Text>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ marginTop: 20 }}>
          <Text style={{ color: '#ff6b35', fontWeight: '700' }}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const isDark = theme === 'dark';
  const textColor = isDark ? '#e5e7eb' : '#374151';
  const headingColor = isDark ? '#ffffff' : '#111827';
  const mutedColor = isDark ? '#9ca3af' : '#6b7280';
  const borderColor = isDark ? '#374151' : '#e5e7eb';
  const cardBg = isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)';

  const htmlContent = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
        <style>
          * { box-sizing: border-box; }
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 17px;
            line-height: 1.72;
            color: ${textColor};
            background-color: transparent;
            margin: 0;
            padding: 0;
            padding-bottom: 0;
            -webkit-font-smoothing: antialiased;
          }
          #content {
            max-width: 100%;
          }
          #content > p:first-of-type {
            font-size: 18px;
            color: ${mutedColor};
            line-height: 1.7;
            margin-top: 0;
          }
          #content h1, #content h2, #content h3, #content h4, #content h5, #content h6 {
            display: block;
            clear: both;
          }
          #content h1 {
            color: ${headingColor};
            font-size: 1.85rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-top: 2.25rem;
            margin-bottom: 0.75rem;
            line-height: 1.25;
            padding: 0.75rem 1rem 0.75rem 1.25rem;
            padding-left: 1.25rem;
            border-left: 4px solid #ff6b35;
            background: ${cardBg};
            border-radius: 0 12px 12px 0;
          }
          #content h2 {
            color: ${headingColor};
            font-size: 1.7rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-top: 2.25rem;
            margin-bottom: 0.75rem;
            line-height: 1.3;
            padding: 0.6rem 0 0.6rem 1.15rem;
            border-left: 4px solid #ff6b35;
            background: ${cardBg};
            border-radius: 0 10px 10px 0;
          }
          #content h3 {
            color: ${headingColor};
            font-size: 1.4rem;
            font-weight: 700;
            letter-spacing: -0.01em;
            margin-top: 1.85rem;
            margin-bottom: 0.5rem;
            line-height: 1.35;
            padding: 0.5rem 0 0.5rem 1rem;
            border-left: 3px solid #ff6b35;
            background: ${cardBg};
            border-radius: 0 8px 8px 0;
          }
          #content h4, #content h5, #content h6 {
            color: ${headingColor};
            font-size: 1.2rem;
            font-weight: 700;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
            line-height: 1.4;
            padding: 0.45rem 0 0.45rem 0.9rem;
            border-left: 3px solid rgba(255, 107, 53, 0.7);
            border-radius: 0 6px 6px 0;
            background: ${cardBg};
          }
          p {
            margin-bottom: 1.25rem;
            margin-top: 0;
          }
          p:empty { display: none; }
          a {
            color: #ff6b35;
            text-decoration: none;
            border-bottom: 1px solid rgba(255, 107, 53, 0.4);
            font-weight: 600;
          }
          strong {
            font-weight: 700;
            color: ${headingColor};
          }
          em { font-style: italic; }
          ul, ol {
            padding-left: 1.5rem;
            margin: 1.25rem 0;
          }
          ul { list-style: none; padding-left: 0; }
          ul li {
            position: relative;
            padding-left: 1.5rem;
            margin-bottom: 0.6rem;
            line-height: 1.6;
          }
          ul li::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0.55em;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #ff6b35;
          }
          ol li { margin-bottom: 0.5rem; line-height: 1.6; }
          blockquote {
            border-left: 4px solid #ff6b35;
            padding: 1rem 1.25rem;
            margin: 1.5rem 0;
            font-style: italic;
            font-size: 1.05rem;
            color: ${mutedColor};
            background: ${cardBg};
            border-radius: 0 12px 12px 0;
          }
          img {
            max-width: 100%;
            height: auto;
            border-radius: 16px;
            margin: 1.5rem 0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.12);
          }
          table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 1.5rem 0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
          }
          thead { display: table-header-group; }
          tr:first-child td, tr:first-child th {
            background: rgba(255, 107, 53, 0.12);
            color: ${headingColor};
            font-weight: 700;
            font-size: 0.9rem;
            padding: 12px 14px;
          }
          tr:first-child td:first-child, tr:first-child th:first-child { border-radius: 12px 0 0 0; }
          tr:first-child td:last-child, tr:first-child th:last-child { border-radius: 0 12px 0 0; }
          td, th {
            border: 1px solid ${borderColor};
            padding: 10px 14px;
            text-align: left;
            vertical-align: top;
            word-break: break-word;
            background: ${isDark ? 'rgba(255,255,255,0.02)' : '#fff'};
          }
          tr:not(:first-child) td, tr:not(:first-child) th { border-top: none; }
          td:first-child, th:first-child { border-left: none; }
          pre, code {
            font-family: ui-monospace, "SF Mono", Menlo, Monaco, Consolas, monospace;
            font-size: 0.9rem;
            background: ${cardBg};
            padding: 0.2em 0.4em;
            border-radius: 6px;
          }
          pre {
            padding: 1rem;
            overflow-x: auto;
            margin: 1rem 0;
          }
          .youtube-embed {
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
            overflow: hidden;
            margin: 1.5rem 0;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.12);
          }
          .youtube-embed iframe {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
          }
        </style>
      </head>
      <body>
        <div id="content">
          ${(() => {
            if (!post.content) return '';
            let content = post.content.replace(/\\n/g, '\n');
            let html = content
              .replace(/^####\s*(.*)$/gim, (_, t) => (t && t.trim()) ? '<h4>' + t.trim() + '</h4>' : '')
              .replace(/^###\s*(.*)$/gim, (_, t) => (t && t.trim()) ? '<h4>' + t.trim() + '</h4>' : '')
              .replace(/^##\s*(.*)$/gim, (_, t) => (t && t.trim()) ? '<h3>' + t.trim() + '</h3>' : '')
              .replace(/^#\s*(.*)$/gim, (_, t) => (t && t.trim()) ? '<h2>' + t.trim() + '</h2>' : '')
              .replace(/\[!\[[^\]]*\]\(https:\/\/(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)(?:[&?][^\s]*)*\)\]/g, 
                  '<div class="youtube-embed"><iframe src="https://www.youtube.com/embed/$1" frameborder="0" allowfullscreen></iframe></div>')
              .replace(/https:\/\/(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)(?:[&?][^\s]*)*/g, 
                  '<div class="youtube-embed"><iframe src="https://www.youtube.com/embed/$1" frameborder="0" allowfullscreen></iframe></div>')
              .replace(/\|(.+)\|/g, (match, content) => {
                  if (content.match(/^[\s\-\|]+$/)) return '';
                  const cells = content.split('|').map(cell => cell.trim());
                  return '<tr>' + cells.map(cell => `<td>${cell}</td>`).join('') + '</tr>';
              })
              .replace(/(<tr>.*<\/tr>)/gs, '<table>$1</table>')
              .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
              .replace(/\*(.*?)\*/g, '<em>$1</em>')
              .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />')
              .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
              .replace(/^- (.+)$/gm, '<li>$1</li>')
              .replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
            
            // Wrap <li> groups in <ul>
            html = html.replace(/(<li>.*<\/li>)+/gs, (match) => `<ul>${match}</ul>`);
            
            html = html
              .replace(/\n\n/g, '</p><p>')
              .replace(/\n/g, '<br>');
            html = '<p>' + html + '</p>';
            // Unwrap block elements from <p> so headers render as blocks and get our styles
            html = html.replace(/<p>\s*<(h[1-6])>/gi, '<$1>').replace(/<\/(h[1-6])>\s*<\/p>/gi, '</$1>');
            html = html.replace(/<p>\s*<table/gi, '<table').replace(/<\/table>\s*<\/p>/gi, '</table>');
            return html;
          })()}
        </div>
        <script>
          function sendHeight() {
            try {
              var height = document.documentElement.scrollHeight || document.body.scrollHeight;
              window.ReactNativeWebView && window.ReactNativeWebView.postMessage(String(height));
            } catch (e) {
              // ignore
            }
          }
          window.onload = sendHeight;
          window.addEventListener('load', sendHeight);
          setTimeout(sendHeight, 250);
          setTimeout(sendHeight, 750);
        </script>
      </body>
    </html>
  `;

  const headerBackground = theme === 'dark' ? colors.background : '#ff6b35';

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: headerBackground }]}>
      <StatusBar barStyle="light-content" backgroundColor={headerBackground} />

      <View style={[styles.topHeader, { backgroundColor: headerBackground }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.topHeaderButton}>
          <Ionicons name="arrow-back" size={22} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.topHeaderTitle}>Blog</Text>
        <TouchableOpacity onPress={handleShare} style={styles.topHeaderButton}>
          <Ionicons name="share-social" size={20} color="#fff" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={[styles.scrollView, { backgroundColor: colors.background }]}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 12 }}
      >
        <View style={[styles.imageContainer, theme === 'light' && styles.imageContainerShadow]}>
          {post.featured_image ? (
            <Image source={{ uri: post.featured_image }} style={styles.headerImage} />
          ) : (
            <LinearGradient colors={['#ff6b35', '#ea580c', '#ec4899']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.headerImagePlaceholder}>
              <Ionicons name="newspaper-outline" size={64} color="rgba(255,255,255,0.95)" />
            </LinearGradient>
          )}
        </View>

        <View style={[styles.contentContainer, { backgroundColor: colors.background }, theme === 'light' && styles.contentCardShadow]}>
          <View style={styles.metaContainer}>
            <View style={[styles.categoryBadge, theme === 'dark' && styles.categoryBadgeDark]}>
              <Text style={styles.categoryText}>{post.category || 'Astrology'}</Text>
            </View>
            <Text style={[styles.dateText, { color: colors.textSecondary }]}>
              {new Date(post.published_at).toLocaleDateString('en-US', {
                month: 'long',
                day: 'numeric',
                year: 'numeric',
              })}
            </Text>
          </View>

          <Text style={[styles.title, { color: colors.text }]}>{post.title}</Text>

          <View style={[styles.authorContainer, theme === 'dark' && styles.authorStripDark]}>
            <View style={styles.authorAvatar}>
              <Text style={styles.authorAvatarText}>A</Text>
            </View>
            <Text style={[styles.authorName, { color: colors.textSecondary }]}>AstroRoshni Team</Text>
          </View>

          {post.excerpt ? (
            <View
              style={[
                styles.excerptContainer,
                {
                  backgroundColor: isDark ? 'rgba(15,23,42,0.9)' : '#fff',
                  borderColor: isDark ? 'rgba(248,250,252,0.08)' : 'rgba(15,23,42,0.06)',
                  shadowColor: '#000',
                  shadowOpacity: isDark ? 0.35 : 0.18,
                  shadowRadius: 18,
                  shadowOffset: { width: 0, height: 8 },
                  elevation: 6,
                },
              ]}
            >
              <View style={styles.excerptPillRow}>
                <View style={styles.excerptChip}>
                  <Text style={styles.excerptChipText}>Key Takeaway</Text>
                </View>
              </View>
              <Text style={[styles.excerptText, { color: colors.text }]}>{post.excerpt}</Text>
            </View>
          ) : null}

          <View style={[styles.contentDivider, { backgroundColor: colors.border }]} />

          <View style={{ height: webViewHeight }}>
            <WebView
              originWhitelist={['*']}
              source={{ html: htmlContent }}
              style={{ backgroundColor: 'transparent' }}
              scrollEnabled={false}
              showsVerticalScrollIndicator={false}
              onMessage={(event) => {
                const height = parseInt(event.nativeEvent.data);
                if (!isNaN(height)) {
                  setWebViewHeight(height);
                }
              }}
            />
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  topHeader: {
    height: 48,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  topHeaderButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  topHeaderTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
  },
  loader: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollView: { flex: 1 },
  imageContainer: {
    width: '100%',
    height: 240,
    position: 'relative',
    marginHorizontal: 20,
    marginTop: 16,
    marginBottom: 0,
    borderRadius: 24,
    overflow: 'hidden',
  },
  imageContainerShadow: {
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.15,
        shadowRadius: 24,
      },
      android: { elevation: 12 },
    }),
  },
  headerImage: {
    width: '100%',
    height: '100%',
  },
  headerImagePlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  contentContainer: {
    paddingHorizontal: 24,
    paddingTop: 28,
    paddingBottom: 24,
    borderTopLeftRadius: 32,
    borderTopRightRadius: 32,
    marginTop: -24,
  },
  contentCardShadow: {
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: -4 },
        shadowOpacity: 0.06,
        shadowRadius: 16,
      },
      android: { elevation: 8 },
    }),
  },
  metaContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 18,
  },
  categoryBadge: {
    backgroundColor: 'rgba(255, 107, 53, 0.12)',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
  },
  categoryBadgeDark: {
    backgroundColor: 'rgba(255, 107, 53, 0.2)',
  },
  categoryText: {
    color: '#ff6b35',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  dateText: {
    fontSize: 14,
    fontWeight: '500',
  },
  title: {
    fontSize: 26,
    fontWeight: '800',
    lineHeight: 34,
    marginBottom: 18,
    letterSpacing: -0.02,
  },
  authorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 14,
  },
  authorStripDark: {
    backgroundColor: 'rgba(255,255,255,0.06)',
  },
  authorAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#ff6b35',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  authorAvatarText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 15,
  },
  authorName: {
    fontSize: 15,
    fontWeight: '600',
  },
  contentDivider: {
    height: 1,
    marginVertical: 24,
  },
  excerptContainer: {
    marginTop: 18,
    marginBottom: 10,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 18,
    borderWidth: 1,
  },
  excerptPillRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  excerptChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    backgroundColor: '#f97316',
  },
  excerptChipText: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1,
    textTransform: 'uppercase',
    color: '#1f2937',
  },
  excerptLabel: {
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1.1,
  },
  excerptText: {
    fontSize: 15,
    lineHeight: 22,
  },
});
