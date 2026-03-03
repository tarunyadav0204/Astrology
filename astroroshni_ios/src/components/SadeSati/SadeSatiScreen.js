import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/Ionicons';
import { chartAPI } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';

const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const ordinalSuffix = (n) => {
  if (n >= 11 && n <= 13) return 'th';
  switch (n % 10) { case 1: return 'st'; case 2: return 'nd'; case 3: return 'rd'; default: return 'th'; }
};
const formatDateOrdinal = (isoDate) => {
  if (!isoDate || typeof isoDate !== 'string') return isoDate || '';
  const [y, m, d] = isoDate.split('T')[0].split('-').map(Number);
  if (!y || !m || !d) return isoDate;
  return `${d}${ordinalSuffix(d)} ${MONTH_NAMES[m - 1] || m} ${y}`;
};

export default function SadeSatiScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const birthData = route.params?.birthData || null;
  const [periods, setPeriods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showInfoModal, setShowInfoModal] = useState(false);

  useEffect(() => {
    if (!birthData?.name) {
      navigation.replace('BirthProfileIntro', { returnTo: 'SadeSati' });
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const formatted = {
          name: birthData.name,
          date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
          time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
          latitude: parseFloat(birthData.latitude) || 0,
          longitude: parseFloat(birthData.longitude) || 0,
          place: birthData.place || '',
        };
        const res = await chartAPI.getSadeSatiPeriods(formatted);
        if (!cancelled) setPeriods(res?.data?.periods || []);
      } catch (e) {
        if (!cancelled) {
          Alert.alert(t('common.error', 'Error'), t('home.sadeSati.loadError', 'Could not load Sade Sati periods.'));
          setPeriods([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [birthData, t]);

  const isLight = theme === 'light';
  const headerBg = isLight ? colors.cardBackground : 'rgba(15,23,42,0.98)';
  const screenBg = isLight ? colors.background : '#0f172a';
  const rowBg = isLight ? '#f8fafc' : 'rgba(255,255,255,0.05)';
  const rowBorder = isLight ? colors.cardBorder : 'rgba(148,163,184,0.2)';

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: screenBg }]} edges={['top']}>
      <View style={[styles.header, { backgroundColor: headerBg, borderBottomColor: rowBorder }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Icon name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.text }]} numberOfLines={1}>
          {t('home.sadeSati.title', 'Sade Sati Periods')}
        </Text>
        <TouchableOpacity onPress={() => setShowInfoModal(true)} style={styles.backBtn} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
          <Icon name="information-circle-outline" size={26} color={colors.text} />
        </TouchableOpacity>
      </View>

      <Modal visible={showInfoModal} transparent animationType="fade">
        <TouchableOpacity
          style={[styles.infoOverlay, { backgroundColor: isLight ? 'rgba(0,0,0,0.45)' : 'rgba(0,0,0,0.6)' }]}
          activeOpacity={1}
          onPress={() => setShowInfoModal(false)}
        >
          <TouchableOpacity activeOpacity={1} onPress={(e) => e.stopPropagation()} style={[styles.infoModalBox, { backgroundColor: isLight ? colors.cardBackground : colors.backgroundSecondary, borderColor: colors.cardBorder }]}>
            <Text style={[styles.infoModalTitle, { color: colors.text }]}>{t('home.sadeSati.infoTitle', 'What is Sade Sati?')}</Text>
            <ScrollView style={styles.infoModalScroll} showsVerticalScrollIndicator={false}>
              <Text style={[styles.infoModalBody, { color: colors.textSecondary }]}>{t('home.sadeSati.infoBody', 'Sade Sati is the roughly 7.5-year period when transiting Saturn passes through the Moon sign, the sign before it, and the sign after it in your birth chart. In Vedic astrology it is considered a significant transit that can bring challenges, delays, and life lessons, but also maturity and growth. The intensity and effects depend on your chart. This screen shows when your Sade Sati periods occur and which one is currently active.')}</Text>
            </ScrollView>
            <TouchableOpacity style={[styles.infoModalClose, { backgroundColor: colors.primary }]} onPress={() => setShowInfoModal(false)}>
              <Text style={styles.infoModalCloseText}>{t('languageModal.close', 'Close')}</Text>
            </TouchableOpacity>
          </TouchableOpacity>
        </TouchableOpacity>
      </Modal>
      {loading ? (
        <View style={styles.loadingWrap}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('home.loading.ticker', 'Loading...')}</Text>
        </View>
      ) : (
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={true}
        >
          {!birthData && (
            <Text style={[styles.empty, { color: colors.textSecondary }]}>{t('home.sadeSati.noBirthData', 'Birth details required.')}</Text>
          )}
          {birthData && periods.length === 0 && (
            <Text style={[styles.empty, { color: colors.textSecondary }]}>{t('home.sadeSati.noPeriods', 'No periods found.')}</Text>
          )}
          {birthData && periods.map((p, i) => (
            <View
              key={`${p.start_date}-${i}`}
              style={[
                styles.row,
                { backgroundColor: rowBg, borderColor: rowBorder },
                p.is_current && styles.rowCurrent,
              ]}
            >
              <Text style={[styles.rowDates, { color: colors.text }]}>
                {formatDateOrdinal(p.start_date)} — {formatDateOrdinal(p.end_date)}
              </Text>
              {p.is_current && (
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>{t('home.ticker.active', 'Active')}</Text>
                </View>
              )}
            </View>
          ))}

          {birthData && (
            <View style={[styles.ctaCard, { backgroundColor: isLight ? colors.surface : 'rgba(249, 115, 22, 0.12)', borderColor: isLight ? colors.cardBorder : 'rgba(249, 115, 22, 0.3)' }]}>
              <Text style={[styles.ctaHeadline, { color: colors.text }]}>
                {t('home.sadeSati.ctaHeadline', 'Will my Sade Sati be challenging or more manageable?')}
              </Text>
              <Text style={[styles.ctaSubtext, { color: colors.textSecondary }]}>
                {t('home.sadeSati.ctaSubtext', 'Get a reading based on your chart — intensity, timing, and remedies.')}
              </Text>
              <TouchableOpacity
                style={[styles.ctaButton, { backgroundColor: colors.primary }]}
                onPress={() => navigation.navigate('Home', { startChat: true, initialMessage: t('home.sadeSati.ctaHeadline', 'Will my Sade Sati be challenging or more manageable?') })}
                activeOpacity={0.85}
              >
                <Icon name="chatbubble-ellipses-outline" size={18} color="#fff" style={styles.ctaButtonIcon} />
                <Text style={styles.ctaButtonText}>{t('home.sadeSati.ctaButton', 'Ask in Chat')}</Text>
              </TouchableOpacity>
            </View>
          )}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 14,
    borderBottomWidth: 1,
  },
  backBtn: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 17,
    fontWeight: '700',
    flex: 1,
    textAlign: 'center',
  },
  loadingWrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    paddingBottom: 32,
  },
  empty: {
    padding: 24,
    textAlign: 'center',
    fontSize: 14,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 14,
    marginBottom: 10,
    borderRadius: 12,
    borderWidth: 1,
  },
  rowCurrent: {
    borderColor: 'rgba(239, 68, 68, 0.6)',
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
  },
  rowDates: {
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
  },
  badge: {
    backgroundColor: '#EF4444',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
  },
  ctaCard: {
    marginTop: 24,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    alignItems: 'center',
  },
  ctaHeadline: {
    fontSize: 17,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 8,
    paddingHorizontal: 4,
  },
  ctaSubtext: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 16,
    lineHeight: 20,
    paddingHorizontal: 4,
  },
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 24,
  },
  ctaButtonIcon: {
    marginRight: 8,
  },
  ctaButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
  infoOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  infoModalBox: {
    width: '100%',
    maxWidth: 400,
    maxHeight: '80%',
    borderRadius: 20,
    borderWidth: 1,
    padding: 20,
  },
  infoModalTitle: {
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 12,
    textAlign: 'center',
  },
  infoModalScroll: {
    maxHeight: 280,
  },
  infoModalBody: {
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'left',
  },
  infoModalClose: {
    marginTop: 16,
    paddingVertical: 12,
    borderRadius: 24,
    alignItems: 'center',
  },
  infoModalCloseText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
});
