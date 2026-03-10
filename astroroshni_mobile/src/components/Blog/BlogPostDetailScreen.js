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

  const htmlContent = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: ${theme === 'dark' ? '#e5e7eb' : '#374151'};
            background-color: transparent;
            margin: 0;
            padding: 0;
            padding-bottom: 50px; /* Space for nudge */
          }
          img {
            max-width: 100%;
            height: auto;
            border-radius: 12px;
            margin: 16px 0;
          }
          h1, h2, h3, h4, h5, h6 {
            color: ${theme === 'dark' ? '#ffffff' : '#111827'};
            margin-top: 24px;
            margin-bottom: 16px;
          }
          p {
            margin-bottom: 16px;
          }
          a {
            color: #ff6b35;
            text-decoration: none;
          }
          ul, ol {
            padding-left: 20px;
            margin-bottom: 16px;
          }
          li {
            margin-bottom: 8px;
          }
          blockquote {
            border-left: 4px solid #ff6b35;
            padding-left: 16px;
            margin: 16px 0;
            font-style: italic;
            color: ${theme === 'dark' ? '#9ca3af' : '#6b7280'};
          }
          table {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
            margin: 16px 0;
          }
          td, th {
            border: 1px solid ${theme === 'dark' ? '#374151' : '#e5e7eb'};
            padding: 8px;
            text-align: left;
            vertical-align: top;
            word-break: break-word;
          }
          .youtube-embed {
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
            overflow: hidden;
            margin: 16px 0;
            border-radius: 12px;
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
              .replace(/^### (.*$)/gim, '<h4>$1</h4>')
              .replace(/^## (.*$)/gim, '<h3>$1</h3>')
              .replace(/^# (.*$)/gim, '<h2>$1</h2>')
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
              
            return `<p>${html}</p>`;
          })()}
        </div>
        <script>
          function sendHeight() {
            try {
              var height = document.documentElement.scrollHeight || document.body.scrollHeight;
              window.ReactNativeWebView && window.ReactNativeWebView.postMessage(String(height + 50));
            } catch (e) {
              // ignore
            }
          }
          window.onload = sendHeight;
          window.addEventListener('load', sendHeight);
          setTimeout(sendHeight, 500);
          setTimeout(sendHeight, 1500);
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
        contentContainerStyle={{ paddingBottom: 100 }}
      >
        <View style={styles.imageContainer}>
          {post.featured_image ? (
            <Image source={{ uri: post.featured_image }} style={styles.headerImage} />
          ) : (
            <LinearGradient colors={['#ff6b35', '#ec4899']} style={styles.headerImagePlaceholder}>
              <Ionicons name="newspaper-outline" size={64} color="#fff" />
            </LinearGradient>
          )}
        </View>

        <View style={styles.contentContainer}>
          <View style={styles.metaContainer}>
            <View style={styles.categoryBadge}>
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

          <View style={styles.authorContainer}>
            <View style={styles.authorAvatar}>
              <Text style={styles.authorAvatarText}>A</Text>
            </View>
            <Text style={[styles.authorName, { color: colors.text }]}>AstroRoshni Team</Text>
          </View>

          <View style={{ height: 1, backgroundColor: colors.border, marginVertical: 20 }} />

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
    height: 220,
    position: 'relative',
    marginTop: 12,
    marginBottom: 24,
    borderRadius: 24,
    overflow: 'hidden',
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
  headerOverlay: {
    // no-op (kept for compatibility if needed later)
  },
  contentContainer: {
    padding: 24,
    borderTopLeftRadius: 32,
    borderTopRightRadius: 32,
    marginTop: -30,
    backgroundColor: 'inherit', // Handled by ScrollView color
  },
  metaContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  categoryBadge: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  categoryText: {
    color: '#ff6b35',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  dateText: {
    fontSize: 14,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    lineHeight: 36,
    marginBottom: 20,
  },
  authorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  authorAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#ff6b35',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  authorAvatarText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 14,
  },
  authorName: {
    fontSize: 15,
    fontWeight: '600',
  },
});
