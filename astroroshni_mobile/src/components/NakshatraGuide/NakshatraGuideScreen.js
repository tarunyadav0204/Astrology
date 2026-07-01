import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Linking,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { chartAPI } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';

const NAKSHATRA_NAMES = [
  'Ashwini',
  'Bharani',
  'Krittika',
  'Rohini',
  'Mrigashira',
  'Ardra',
  'Punarvasu',
  'Pushya',
  'Ashlesha',
  'Magha',
  'Purva Phalguni',
  'Uttara Phalguni',
  'Hasta',
  'Chitra',
  'Swati',
  'Vishakha',
  'Anuradha',
  'Jyeshtha',
  'Mula',
  'Purva Ashadha',
  'Uttara Ashadha',
  'Shravana',
  'Dhanishta',
  'Shatabhisha',
  'Purva Bhadrapada',
  'Uttara Bhadrapada',
  'Revati',
];

const longitudeToNakshatra = (longitude) => {
  const lon = ((Number(longitude) || 0) % 360 + 360) % 360;
  const span = 360 / 27;
  const index = Math.min(26, Math.max(0, Math.floor(lon / span)));
  const degreeInNakshatra = lon % span;
  const pada = Math.min(4, Math.floor(degreeInNakshatra / (span / 4)) + 1);
  return {
    index,
    name: NAKSHATRA_NAMES[index],
    degreeInNakshatra,
    pada,
  };
};

export default function NakshatraGuideScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const birthData = route.params?.birthData || null;
  const chartDataParam = route.params?.chartData || null;
  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState(chartDataParam);
  const [videosByNakshatra, setVideosByNakshatra] = useState({});
  const [guideLoading, setGuideLoading] = useState(true);
  const [guideError, setGuideError] = useState('');

  const isLight = theme === 'light';
  const backgroundColor = isLight ? colors.background : '#0b1020';
  const cardBg = isLight ? colors.cardBackground : 'rgba(15,23,42,0.94)';
  const borderColor = isLight ? colors.cardBorder : 'rgba(148,163,184,0.18)';
  const guideCardBg = isLight ? '#0f172a' : '#050816';

  const resolveChartData = useCallback(async () => {
    if (chartDataParam) {
      setChartData(chartDataParam);
      setLoading(false);
      return;
    }
    if (!birthData?.date || !birthData?.time) {
      setLoading(false);
      return;
    }
    try {
      const formattedBirthData = {
        id: birthData.id || birthData.birth_chart_id,
        birth_chart_id: birthData.birth_chart_id || birthData.id,
        name: birthData.name,
        date: birthData.date,
        time: birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        location: birthData.place || birthData.location || 'Unknown',
      };
      const res = await chartAPI.calculateChartOnly(formattedBirthData);
      setChartData(res?.data || null);
    } catch (error) {
      console.log('[NakshatraGuide] failed to load chart data:', error?.response?.data || error?.message || error);
    } finally {
      setLoading(false);
    }
  }, [birthData, chartDataParam]);

  const loadGuideVideos = useCallback(async () => {
    setGuideLoading(true);
    setGuideError('');
    try {
      const res = await chartAPI.getNakshatraGuideVideos();
      setVideosByNakshatra(res?.data?.videos || {});
    } catch (error) {
      console.log('[NakshatraGuide] failed to load videos:', error?.response?.data || error?.message || error);
      setGuideError(t('home.nakshatraGuide.loadError', 'Could not load guide videos.'));
      setVideosByNakshatra({});
    } finally {
      setGuideLoading(false);
    }
  }, [t]);

  useEffect(() => {
    resolveChartData();
    loadGuideVideos();
  }, [loadGuideVideos, resolveChartData]);

  const moonLongitude = chartData?.planets?.Moon?.longitude ?? chartData?.moon?.longitude ?? null;
  const moonNakshatra = useMemo(() => {
    if (moonLongitude == null) return null;
    return longitudeToNakshatra(moonLongitude);
  }, [moonLongitude]);

  const guideEntry = useMemo(() => {
    if (!moonNakshatra?.name) return null;
    const raw = videosByNakshatra?.[moonNakshatra.name];
    if (!raw) return null;
    if (typeof raw === 'string') {
      return { url: raw, title: '', description: '' };
    }
    return {
      url: raw?.url || raw?.videoUrl || raw?.video_url || raw?.link || raw?.youtubeUrl || raw?.youtube_url || '',
      title: raw?.title || '',
      description: raw?.description || '',
      enabled: raw?.enabled !== false,
    };
  }, [moonNakshatra, videosByNakshatra]);

  const screenTitle = t('home.nakshatraGuide.screenTitle', 'Know your Nakshatra');
  const subtitle = t(
    'home.nakshatraGuide.subtitle',
    'Your Moon Nakshatra is the key detail to know here.'
  );

  return (
    <SafeAreaView style={[styles.container, { backgroundColor }]} edges={['top']}>
      <View style={[styles.header, { borderBottomColor: borderColor, backgroundColor: cardBg }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1}>
          {screenTitle}
        </Text>
        <View style={styles.backBtn} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={[styles.heroCard, { backgroundColor: cardBg, borderColor }]}>
          <Text style={[styles.heroEyebrow, { color: colors.primary }]}>
            {t('home.nakshatraGuide.heroLabel', 'Know yourself')}
          </Text>
          <Text style={[styles.heroTitle, { color: colors.text }]}>
            {t('home.nakshatraGuide.heroTitle', 'Your Moon Nakshatra')}
          </Text>
          <Text style={[styles.heroBody, { color: colors.textSecondary }]}>
            {subtitle}
          </Text>

          <View style={[styles.badgeRow, { borderTopColor: borderColor }]}>
            <View style={[styles.infoBadge, { backgroundColor: isLight ? '#eef2ff' : 'rgba(99,102,241,0.18)' }]}>
              <Text style={[styles.badgeLabel, { color: colors.textSecondary }]}>
                {t('home.nakshatraGuide.nakshatraLabel', 'Nakshatra')}
              </Text>
              <Text style={[styles.badgeValue, { color: colors.text }]}>
                {moonNakshatra?.name || t('common.unknown', 'Unknown')}
              </Text>
            </View>
            <View style={[styles.infoBadge, { backgroundColor: isLight ? '#ecfeff' : 'rgba(14,165,233,0.18)' }]}>
              <Text style={[styles.badgeLabel, { color: colors.textSecondary }]}>
                {t('home.nakshatraGuide.padaLabel', 'Pada')}
              </Text>
              <Text style={[styles.badgeValue, { color: colors.text }]}>
                {moonNakshatra?.pada ? `${moonNakshatra.pada}` : t('common.unknown', 'Unknown')}
              </Text>
            </View>
          </View>

          {guideEntry?.title ? (
            <View style={[styles.guideInfoStrip, { borderTopColor: borderColor }]}>
              <Text style={[styles.guideInfoLabel, { color: colors.textSecondary }]}>
                {t('home.nakshatraGuide.videoLabel', 'Video')}
              </Text>
              <Text style={[styles.guideInfoTitle, { color: colors.text }]}>
                {guideEntry.title}
              </Text>
              {!!guideEntry.description && (
                <Text style={[styles.guideInfoBody, { color: colors.textSecondary }]}>
                  {guideEntry.description}
                </Text>
              )}
            </View>
          ) : null}

          <View style={[styles.guideActionStrip, { borderTopColor: borderColor }]}>
            {loading || guideLoading ? (
              <View style={styles.guideActionInline}>
                <ActivityIndicator size="small" color={colors.primary} />
                <Text style={[styles.guideActionText, { color: colors.textSecondary }]}>
                  {t('home.nakshatraGuide.loading', 'Loading your guide...')}
                </Text>
              </View>
            ) : guideEntry?.url ? (
              <>
                <Text style={[styles.guideActionBody, { color: colors.textSecondary }]}>
                  {t('home.nakshatraGuide.openVideoBody', 'Tap the button to open the video in YouTube.')}
                </Text>
                <TouchableOpacity
                  onPress={() => Linking.openURL(guideEntry.url)}
                  style={[styles.guideActionButton, { backgroundColor: colors.primary }]}
                  activeOpacity={0.88}
                >
                  <Ionicons name="logo-youtube" size={16} color="#fff" />
                  <Text style={styles.guideActionButtonText}>
                    {t('home.nakshatraGuide.openVideo', 'Open video')}
                  </Text>
                </TouchableOpacity>
              </>
            ) : (
              <Text style={[styles.guideActionBody, { color: colors.textSecondary }]}>
                {guideError ||
                  t(
                    'home.nakshatraGuide.comingSoonBody',
                    'Video coming up. Check this space in a few days.'
                  )}
              </Text>
            )}
          </View>
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 14,
    borderBottomWidth: 1,
  },
  backBtn: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  headerTitle: { flex: 1, textAlign: 'center', fontSize: 18, fontWeight: '800' },
  content: {
    paddingHorizontal: 16,
    paddingVertical: 16,
    gap: 14,
  },
  heroCard: {
    borderWidth: 1,
    borderRadius: 20,
    padding: 16,
  },
  heroEyebrow: { fontSize: 12, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 8 },
  heroTitle: { fontSize: 26, fontWeight: '900', marginBottom: 10 },
  heroBody: { fontSize: 15, lineHeight: 22, marginBottom: 14 },
  badgeRow: {
    flexDirection: 'row',
    gap: 12,
    paddingTop: 14,
    borderTopWidth: 1,
    marginTop: 2,
    marginBottom: 14,
  },
  infoBadge: {
    flex: 1,
    borderRadius: 16,
    paddingVertical: 12,
    paddingHorizontal: 14,
  },
  badgeLabel: { fontSize: 12, fontWeight: '700', marginBottom: 4 },
  badgeValue: { fontSize: 17, fontWeight: '800' },
  guideInfoStrip: {
    marginTop: 16,
    paddingTop: 14,
    borderTopWidth: 1,
    gap: 4,
  },
  guideInfoLabel: {
    fontSize: 11,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  guideInfoTitle: {
    fontSize: 16,
    fontWeight: '900',
  },
  guideInfoBody: {
    fontSize: 13,
    lineHeight: 19,
  },
  guideActionStrip: {
    marginTop: 16,
    paddingTop: 14,
    borderTopWidth: 1,
    alignItems: 'center',
    gap: 10,
  },
  guideActionInline: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  guideActionText: {
    fontSize: 13,
    fontWeight: '700',
  },
  guideActionBody: {
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
  guideActionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 999,
  },
  guideActionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '800',
  },
});
