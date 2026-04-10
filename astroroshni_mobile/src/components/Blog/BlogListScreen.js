import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  Image,
  StatusBar,
  Platform,
} from 'react-native';
import { ScrollView as GHScrollView } from 'react-native-gesture-handler';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { blogAPI } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';
import { appLocaleForI18n } from '../../utils/appLocale';

export default function BlogListScreen({ navigation }) {
  const { t, i18n } = useTranslation();
  const { theme, colors } = useTheme();
  const dateLocale = appLocaleForI18n(i18n.language);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    await Promise.all([fetchPosts(), fetchCategories()]);
    setLoading(false);
  };

  const fetchPosts = async (category = null) => {
    try {
      const response = await blogAPI.getPosts('published', category);
      setPosts(response.data);
    } catch (error) {
      console.error('Error fetching blog posts:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await blogAPI.getBlogCategories();
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching blog categories:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchPosts(selectedCategory);
    setRefreshing(false);
  };

  const handleCategorySelect = (category) => {
    const newCategory = selectedCategory === category ? null : category;
    setSelectedCategory(newCategory);
    fetchPosts(newCategory);
  };

  const renderCategoryHeader = () => {
    if (!categories || categories.length === 0) return null;
    return (
      <View style={styles.categoriesContainer}>
        <GHScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoriesList}
          style={styles.categoriesScrollView}
        >
          {categories.map((category) => {
            const isSelected = selectedCategory === category;
            return (
              <TouchableOpacity
                key={String(category)}
                style={[styles.categoryChip, isSelected && { backgroundColor: '#ff6b35' }]}
                onPress={() => handleCategorySelect(category)}
                activeOpacity={0.8}
              >
                <Text style={[styles.categoryText, { color: isSelected ? '#fff' : colors.text }]}>
                  {category}
                </Text>
              </TouchableOpacity>
            );
          })}
        </GHScrollView>
      </View>
    );
  };

  const renderPostItem = ({ item }) => (
    <TouchableOpacity
      style={[styles.postCard, { backgroundColor: colors.surface }]}
      onPress={() => navigation.navigate('BlogPostDetail', { slug: item.slug })}
      activeOpacity={0.9}
    >
      {item.featured_image ? (
        <Image source={{ uri: item.featured_image }} style={styles.postImage} />
      ) : (
        <LinearGradient colors={['#ff6b35', '#ec4899']} style={styles.postImagePlaceholder}>
          <Ionicons name="newspaper-outline" size={40} color="#fff" />
        </LinearGradient>
      )}
      <View style={styles.postContent}>
        <View style={styles.postMeta}>
          <Text style={[styles.postCategory, { color: '#ff6b35' }]}>{item.category || t('blog.defaultCategory')}</Text>
          <Text style={[styles.postDate, { color: colors.textSecondary }]}>
            {new Date(item.published_at).toLocaleDateString(dateLocale, { month: 'short', day: 'numeric', year: 'numeric' })}
          </Text>
        </View>
        <Text style={[styles.postTitle, { color: colors.text }]} numberOfLines={2}>{item.title}</Text>
        <Text style={[styles.postExcerpt, { color: colors.textSecondary }]} numberOfLines={3}>{item.excerpt}</Text>
        <View style={styles.readMore}>
          <Text style={styles.readMoreText}>{t('blog.readMore')}</Text>
          <Ionicons name="arrow-forward" size={16} color="#ff6b35" />
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#ff6b35" />
      <LinearGradient
        colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd] : ['#fff', '#fef7f0']}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={colors.text} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]}>{t('blog.screenTitle')}</Text>
            <View style={{ width: 40 }} />
          </View>

          {loading ? (
            <View style={styles.loader}>
              <ActivityIndicator size="large" color="#ff6b35" />
            </View>
          ) : (
            <FlatList
              data={posts}
              renderItem={renderPostItem}
              keyExtractor={(item) => item.id.toString()}
              ListHeaderComponent={renderCategoryHeader}
              contentContainerStyle={styles.postList}
              showsVerticalScrollIndicator={false}
              nestedScrollEnabled={Platform.OS === 'android'}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#ff6b35']} />
              }
              ListEmptyComponent={
                <View style={styles.emptyState}>
                  <Ionicons name="newspaper-outline" size={64} color={colors.textSecondary} />
                  <Text style={[styles.emptyText, { color: colors.textSecondary }]}>{t('blog.empty')}</Text>
                </View>
              }
            />
          )}
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
  },
  categoriesContainer: {
    paddingBottom: 10,
    width: '100%',
  },
  categoriesScrollView: {
    flexGrow: 0,
  },
  categoriesScrollViewWidth: {
    width: '100%',
  },
  categoriesList: {
    paddingHorizontal: 20,
    alignItems: 'center',
    flexDirection: 'row',
  },
  categoryChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    marginRight: 10,
  },
  categoryText: {
    fontSize: 14,
    fontWeight: '600',
  },
  loader: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  postList: {
    padding: 20,
    paddingTop: 10,
    paddingBottom: 100,
  },
  postCard: {
    borderRadius: 20,
    marginBottom: 24,
    overflow: 'hidden',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
  },
  postImage: {
    width: '100%',
    height: 180,
  },
  postImagePlaceholder: {
    width: '100%',
    height: 180,
    justifyContent: 'center',
    alignItems: 'center',
  },
  postContent: {
    padding: 16,
  },
  postMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  postCategory: {
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  postDate: {
    fontSize: 12,
  },
  postTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 8,
    lineHeight: 24,
  },
  postExcerpt: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  readMore: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  readMoreText: {
    color: '#ff6b35',
    fontWeight: '700',
    fontSize: 14,
    marginRight: 4,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 100,
  },
  emptyText: {
    marginTop: 16,
    fontSize: 16,
  },
});
