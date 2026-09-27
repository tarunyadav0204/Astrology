import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  useWindowDimensions,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';

import { useTheme } from '../../context/ThemeContext';
import { storage } from '../../services/storage';

export default function ProfessionalAnalysisScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const { width } = useWindowDimensions();
  const isTablet = width >= 768;
  const [birthData, setBirthData] = useState(route?.params?.birthData || null);
  const [loading, setLoading] = useState(!route?.params?.birthData);

  useEffect(() => {
    let active = true;
    const loadBirthData = async () => {
      try {
        const stored = route?.params?.birthData || await storage.getBirthDetails();
        if (!active) return;
        if (!stored?.date || !stored?.time) {
          navigation.replace('BirthProfileIntro', { returnTo: 'ProfessionalAnalysis' });
          return;
        }
        setBirthData(stored);
      } finally {
        if (active) setLoading(false);
      }
    };
    loadBirthData();
    return () => { active = false; };
  }, [navigation, route?.params?.birthData]);

  const openHealth = () => navigation.navigate('HealthBlueprint', {
    birthData,
    chartData: route?.params?.chartData || null,
  });

  return (
    <SafeAreaView style={[styles.screen, { backgroundColor: colors.background }]}>
      <View style={[styles.header, isTablet && styles.headerTablet, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cardBorder }]}>
        <TouchableOpacity
          style={[styles.headerButton, isTablet && styles.headerButtonTablet]}
          onPress={() => navigation.goBack()}
          accessibilityRole="button"
          accessibilityLabel={t('professionalAnalysis.actions.back')}
        >
          <Ionicons name="arrow-back" size={isTablet ? 28 : 22} color={colors.textInverse} />
        </TouchableOpacity>
        <View style={styles.headerCopy}>
          <Text style={[styles.headerTitle, isTablet && styles.headerTitleTablet, { color: colors.textInverse }]}>{t('professionalAnalysis.title')}</Text>
          <Text style={[styles.headerSubtitle, isTablet && styles.headerSubtitleTablet, { color: colors.textInverseMuted }]}>{birthData?.name || t('professionalAnalysis.selectedChart')}</Text>
        </View>
        <View style={[styles.headerButton, isTablet && styles.headerButtonTablet]} />
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={[styles.content, isTablet && styles.contentTablet]}
          showsVerticalScrollIndicator={false}
        >
          <View style={[styles.intro, isTablet && styles.introTablet, { backgroundColor: colors.cosmicSurface || colors.headerSurface, borderColor: colors.cosmicLine || colors.cardBorder }]}>
            <Text style={[styles.eyebrow, isTablet && styles.eyebrowTablet, { color: colors.accent }]}>{t('professionalAnalysis.eyebrow')}</Text>
            <Text style={[styles.introTitle, isTablet && styles.introTitleTablet, { color: colors.textInverse }]}>{t('professionalAnalysis.heroTitle')}</Text>
            <Text style={[styles.introBody, isTablet && styles.introBodyTablet, { color: colors.textInverseMuted }]}>{t('professionalAnalysis.heroBody')}</Text>
          </View>

          <Text style={[styles.sectionTitle, isTablet && styles.sectionTitleTablet, { color: colors.text }]}>{t('professionalAnalysis.areasTitle')}</Text>
          <TouchableOpacity
            style={[styles.moduleCard, isTablet && styles.moduleCardTablet, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}
            onPress={openHealth}
            activeOpacity={0.88}
            accessibilityRole="button"
            accessibilityLabel={t('professionalAnalysis.health.accessibility')}
          >
            <View style={[styles.iconWrap, isTablet && styles.iconWrapTablet, { backgroundColor: colors.accentSoft }]}>
              <Ionicons name="medical-outline" size={isTablet ? 31 : 24} color={colors.primary} />
            </View>
            <View style={styles.moduleCopy}>
              <Text style={[styles.moduleTitle, isTablet && styles.moduleTitleTablet, { color: colors.text }]}>{t('professionalAnalysis.health.title')}</Text>
              <Text style={[styles.moduleBody, isTablet && styles.moduleBodyTablet, { color: colors.textSecondary }]}>{t('professionalAnalysis.health.body')}</Text>
              <View style={styles.topicRow}>
                {['constitution', 'vulnerabilities', 'protection', 'disease', 'timing'].map((key) => (
                  <Text key={key} style={[styles.topic, isTablet && styles.topicTablet, { color: colors.primary, borderColor: colors.cardBorder }]}>
                    {t(`professionalAnalysis.health.topics.${key}`)}
                  </Text>
                ))}
              </View>
            </View>
            <Ionicons name="chevron-forward" size={isTablet ? 28 : 22} color={colors.textSecondary} />
          </TouchableOpacity>
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  header: { minHeight: 72, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1, paddingHorizontal: 10 },
  headerTablet: { minHeight: 92, paddingHorizontal: 24 },
  headerButton: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  headerButtonTablet: { width: 58, height: 58 },
  headerCopy: { flex: 1, alignItems: 'center' },
  headerTitle: { fontSize: 17, fontWeight: '900' },
  headerTitleTablet: { fontSize: 25 },
  headerSubtitle: { fontSize: 10, marginTop: 2 },
  headerSubtitleTablet: { fontSize: 14, marginTop: 4 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  content: { padding: 16, paddingBottom: 48 },
  contentTablet: { width: '100%', maxWidth: 1120, alignSelf: 'center', padding: 30, paddingBottom: 72 },
  intro: { borderWidth: 1, borderRadius: 22, padding: 22 },
  introTablet: { borderRadius: 28, padding: 34 },
  eyebrow: { fontSize: 10, fontWeight: '900', letterSpacing: 1.2, textTransform: 'uppercase' },
  eyebrowTablet: { fontSize: 13 },
  introTitle: { fontFamily: 'Georgia', fontSize: 29, lineHeight: 36, fontWeight: '700', marginVertical: 8 },
  introTitleTablet: { fontSize: 42, lineHeight: 50, marginVertical: 12 },
  introBody: { fontSize: 13, lineHeight: 20 },
  introBodyTablet: { maxWidth: 820, fontSize: 18, lineHeight: 28 },
  sectionTitle: { fontFamily: 'Georgia', fontSize: 24, fontWeight: '700', marginTop: 24, marginBottom: 12 },
  sectionTitleTablet: { fontSize: 32, marginTop: 32, marginBottom: 18 },
  moduleCard: { borderWidth: 1, borderRadius: 20, padding: 17, flexDirection: 'row', alignItems: 'center', gap: 14 },
  moduleCardTablet: { borderRadius: 26, padding: 26, gap: 20 },
  iconWrap: { width: 50, height: 50, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  iconWrapTablet: { width: 68, height: 68, borderRadius: 20 },
  moduleCopy: { flex: 1 },
  moduleTitle: { fontSize: 19, fontWeight: '900' },
  moduleTitleTablet: { fontSize: 27 },
  moduleBody: { fontSize: 12, lineHeight: 18, marginTop: 4 },
  moduleBodyTablet: { fontSize: 17, lineHeight: 25, marginTop: 7 },
  topicRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 11 },
  topic: { borderWidth: 1, borderRadius: 12, paddingHorizontal: 8, paddingVertical: 4, fontSize: 9, fontWeight: '800' },
  topicTablet: { borderRadius: 14, paddingHorizontal: 11, paddingVertical: 6, fontSize: 12 },
});
