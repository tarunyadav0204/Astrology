import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Image,
  Platform,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ScrollView as GHScrollView } from 'react-native-gesture-handler';
import { useTranslation } from 'react-i18next';
import { blogAPI } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';
import { appLocaleForI18n } from '../../utils/appLocale';
import { goBackOrHome } from '../../navigation/navHelpers';
import FocusedStatusBar from '../Common/FocusedStatusBar';

export default function BlogListScreen({ navigation }) {
  const { t, i18n } = useTranslation();
  const { colors } = useTheme();
  const dateLocale = appLocaleForI18n(i18n.language);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [error, setError] = useState(false);

  const fetchPosts = useCallback(async (category = null) => {
    try {
      setError(false);
      const response = await blogAPI.getPosts('published', category);
      setPosts(Array.isArray(response.data) ? response.data : []);
    } catch (requestError) {
      console.error('Error fetching blog posts:', requestError);
      setError(true);
    }
  }, []);

  const fetchCategories = useCallback(async () => {
    try {
      const response = await blogAPI.getBlogCategories();
      setCategories(Array.isArray(response.data) ? response.data : []);
    } catch (requestError) {
      console.error('Error fetching blog categories:', requestError);
    }
  }, []);

  useEffect(() => {
    let active = true;
    Promise.all([fetchPosts(), fetchCategories()]).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [fetchCategories, fetchPosts]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchPosts(selectedCategory);
    setRefreshing(false);
  };

  const selectCategory = async (category) => {
    const next = selectedCategory === category ? null : category;
    setSelectedCategory(next);
    setLoading(true);
    await fetchPosts(next);
    setLoading(false);
  };

  const featured = posts[0];
  const remainingPosts = useMemo(() => (featured ? posts.slice(1) : []), [featured, posts]);
  const openPost = (post) => navigation.navigate('BlogPostDetail', { slug: post.slug });
  const formatDate = (value) => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? '' : date.toLocaleDateString(dateLocale, { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const CategoryRail = () => categories.length ? (
    <GHScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.categoryRail}>
      <TouchableOpacity
        style={[styles.categoryChip, { borderColor: colors.cardBorder, backgroundColor: selectedCategory == null ? colors.primary : colors.surfaceRaised }]}
        onPress={() => selectCategory(null)}
      >
        <Text style={[styles.categoryChipText, { color: selectedCategory == null ? colors.onPrimary : colors.text }]}>{t('knowledgeSupport.allTopics')}</Text>
      </TouchableOpacity>
      {categories.map((category) => {
        const selected = selectedCategory === category;
        return (
          <TouchableOpacity
            key={String(category)}
            style={[styles.categoryChip, { borderColor: colors.cardBorder, backgroundColor: selected ? colors.primary : colors.surfaceRaised }]}
            onPress={() => selectCategory(category)}
          >
            <Text style={[styles.categoryChipText, { color: selected ? colors.onPrimary : colors.text }]}>{category}</Text>
          </TouchableOpacity>
        );
      })}
    </GHScrollView>
  ) : null;

  const ListHeader = () => (
    <>
      <View style={[styles.hero, { backgroundColor: colors.surfaceInverse, borderColor: colors.cosmicLine || colors.cardBorder }]}>
        <View pointerEvents="none" style={styles.heroLinework}>
          <View style={[styles.orbit, styles.orbitLarge, { borderColor: colors.accent }]} />
          <View style={[styles.orbit, styles.orbitSmall, { borderColor: colors.accent }]} />
          <View style={[styles.heroRule, { backgroundColor: colors.accent }]} />
        </View>
        <Text style={[styles.eyebrow, { color: colors.accent }]}>{t('knowledgeSupport.heroEyebrow')}</Text>
        <Text style={[styles.heroTitle, { color: colors.onSurfaceInverse }]}>{t('knowledgeSupport.heroTitle')}</Text>
        <Text style={[styles.heroBody, { color: colors.onSurfaceInverseMuted }]}>{t('knowledgeSupport.heroBody')}</Text>
      </View>
      <View style={styles.sectionHeading}>
        <View>
          <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{t('knowledgeSupport.libraryEyebrow')}</Text>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('knowledgeSupport.latestTitle')}</Text>
        </View>
        <Text style={[styles.articleCount, { color: colors.textTertiary }]}>{t('knowledgeSupport.articleCount', { count: posts.length })}</Text>
      </View>
      <CategoryRail />
      {featured ? (
        <TouchableOpacity style={[styles.featuredCard, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]} onPress={() => openPost(featured)} activeOpacity={0.9}>
          {featured.featured_image ? <Image source={{ uri: featured.featured_image }} style={styles.featuredImage} /> : (
            <View style={[styles.featuredImage, styles.placeholder, { backgroundColor: colors.cosmicRaised }]}><Ionicons name="book-outline" size={38} color={colors.accent} /></View>
          )}
          <View style={styles.featuredCopy}>
            <View style={styles.metaRow}>
              <Text style={[styles.category, { color: colors.primary }]}>{featured.category || t('blog.defaultCategory')}</Text>
              <Text style={[styles.date, { color: colors.textTertiary }]}>{formatDate(featured.published_at)}</Text>
            </View>
            <Text style={[styles.featuredTitle, { color: colors.text }]}>{featured.title}</Text>
            {featured.excerpt ? <Text style={[styles.excerpt, { color: colors.textSecondary }]} numberOfLines={3}>{featured.excerpt}</Text> : null}
            <View style={styles.readRow}><Text style={[styles.readText, { color: colors.primary }]}>{t('blog.readMore')}</Text><Ionicons name="arrow-forward" size={17} color={colors.primary} /></View>
          </View>
        </TouchableOpacity>
      ) : null}
      {remainingPosts.length ? <Text style={[styles.moreTitle, { color: colors.text }]}>{t('knowledgeSupport.moreTitle')}</Text> : null}
    </>
  );

  const renderPost = ({ item, index }) => (
    <TouchableOpacity style={[styles.postCard, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]} onPress={() => openPost(item)} activeOpacity={0.88}>
      <View style={styles.postNumber}><Text style={[styles.postNumberText, { color: colors.primary }]}>{String(index + 2).padStart(2, '0')}</Text></View>
      <View style={styles.postCopy}>
        <Text style={[styles.category, { color: colors.primary }]}>{item.category || t('blog.defaultCategory')}</Text>
        <Text style={[styles.postTitle, { color: colors.text }]} numberOfLines={2}>{item.title}</Text>
        <Text style={[styles.date, { color: colors.textTertiary }]}>{formatDate(item.published_at)}</Text>
      </View>
      <View style={[styles.arrowButton, { backgroundColor: colors.accentSoft }]}><Ionicons name="arrow-forward" size={18} color={colors.onAccent} /></View>
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <FocusedStatusBar backgroundColor={colors.headerSurface} />
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.headerSurface }]} edges={['top']}>
        <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine || colors.cardBorder }]}>
          <TouchableOpacity onPress={() => goBackOrHome(navigation)} style={[styles.headerButton, { borderColor: colors.cosmicLine || colors.cardBorder }]} accessibilityLabel={t('knowledgeSupport.back')}>
            <Ionicons name="arrow-back" size={21} color={colors.textInverse} />
          </TouchableOpacity>
          <View style={styles.headerCopy}><Text style={[styles.headerEyebrow, { color: colors.accent }]}>{t('knowledgeSupport.knowledge')}</Text><Text style={[styles.headerTitle, { color: colors.textInverse }]}>{t('blog.screenTitle')}</Text></View>
          <View style={[styles.headerSeal, { borderColor: colors.cosmicLine || colors.cardBorder }]}><Ionicons name="library-outline" size={20} color={colors.accent} /></View>
        </View>
        <View style={[styles.contentShell, { backgroundColor: colors.background }]}>
        {loading ? <View style={styles.loader}><ActivityIndicator size="large" color={colors.primary} /></View> : (
          <FlatList
            data={remainingPosts}
            renderItem={renderPost}
            keyExtractor={(item, index) => String(item.id || item.slug || index)}
            ListHeaderComponent={ListHeader}
            contentContainerStyle={styles.content}
            showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} colors={[colors.primary]} />}
            ListEmptyComponent={!featured ? <View style={styles.empty}><Ionicons name={error ? 'cloud-offline-outline' : 'book-outline'} size={34} color={colors.primary} /><Text style={[styles.emptyTitle, { color: colors.text }]}>{error ? t('knowledgeSupport.loadFailed') : t('blog.empty')}</Text><Text style={[styles.emptyBody, { color: colors.textSecondary }]}>{error ? t('knowledgeSupport.tryAgain') : t('knowledgeSupport.emptyBody')}</Text></View> : null}
          />
        )}
        </View>
      </SafeAreaView>
    </View>
  );
}

const serif = Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' });
const styles = StyleSheet.create({
  container: { flex: 1 }, safeArea: { flex: 1 }, contentShell: { flex: 1 },
  header: { minHeight: 78, paddingHorizontal: 18, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1 },
  headerButton: { width: 42, height: 42, borderRadius: 21, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  headerCopy: { flex: 1, paddingHorizontal: 14 }, headerEyebrow: { fontSize: 9, fontWeight: '900', letterSpacing: 1.7 },
  headerTitle: { fontFamily: serif, fontSize: 21, fontWeight: '600', marginTop: 2 },
  headerSeal: { width: 42, height: 42, borderRadius: 21, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  loader: { flex: 1, alignItems: 'center', justifyContent: 'center' }, content: { padding: 16, paddingBottom: 80 },
  hero: { minHeight: 270, borderRadius: 30, borderWidth: 1, overflow: 'hidden', padding: 26, justifyContent: 'flex-end' },
  heroLinework: { ...StyleSheet.absoluteFillObject, opacity: 0.55 }, orbit: { position: 'absolute', borderWidth: 1 },
  orbitLarge: { width: 190, height: 190, borderRadius: 95, right: -57, top: -72 }, orbitSmall: { width: 116, height: 116, borderRadius: 58, right: -17, top: -32 },
  heroRule: { position: 'absolute', width: 72, height: 1, left: 26, top: 38 }, eyebrow: { fontSize: 11, fontWeight: '900', letterSpacing: 2 },
  heroTitle: { fontFamily: serif, fontSize: 40, lineHeight: 44, fontWeight: '500', maxWidth: '88%', marginTop: 11 },
  heroBody: { fontSize: 15, lineHeight: 22, fontWeight: '600', maxWidth: '92%', marginTop: 14 },
  sectionHeading: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', paddingTop: 30, paddingHorizontal: 2 },
  sectionEyebrow: { fontSize: 10, fontWeight: '900', letterSpacing: 1.8 }, sectionTitle: { fontFamily: serif, fontSize: 29, marginTop: 4 }, articleCount: { fontSize: 11, fontWeight: '700', paddingBottom: 5 },
  categoryRail: { paddingVertical: 18, gap: 8 }, categoryChip: { borderWidth: 1, borderRadius: 999, paddingHorizontal: 16, paddingVertical: 10 }, categoryChipText: { fontSize: 12, fontWeight: '800' },
  featuredCard: { borderWidth: 1, borderRadius: 26, overflow: 'hidden', marginBottom: 28 }, featuredImage: { width: '100%', height: 190 }, placeholder: { alignItems: 'center', justifyContent: 'center' },
  featuredCopy: { padding: 20 }, metaRow: { flexDirection: 'row', justifyContent: 'space-between', gap: 12 }, category: { fontSize: 10, fontWeight: '900', letterSpacing: 1.3, textTransform: 'uppercase' }, date: { fontSize: 11, fontWeight: '600' },
  featuredTitle: { fontFamily: serif, fontSize: 27, lineHeight: 32, marginTop: 10 }, excerpt: { fontSize: 14, lineHeight: 21, marginTop: 10 }, readRow: { flexDirection: 'row', alignItems: 'center', gap: 7, marginTop: 15 }, readText: { fontSize: 12, fontWeight: '900' },
  moreTitle: { fontFamily: serif, fontSize: 24, marginBottom: 12 }, postCard: { minHeight: 126, borderWidth: 1, borderRadius: 22, flexDirection: 'row', alignItems: 'center', padding: 16, marginBottom: 12 },
  postNumber: { width: 34, alignSelf: 'stretch', paddingTop: 2 }, postNumberText: { fontSize: 11, fontWeight: '900' }, postCopy: { flex: 1, paddingRight: 10 }, postTitle: { fontFamily: serif, fontSize: 19, lineHeight: 24, marginVertical: 7 }, arrowButton: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  empty: { minHeight: 300, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 28 }, emptyTitle: { fontFamily: serif, fontSize: 22, marginTop: 14, textAlign: 'center' }, emptyBody: { fontSize: 14, lineHeight: 20, marginTop: 7, textAlign: 'center' },
});
