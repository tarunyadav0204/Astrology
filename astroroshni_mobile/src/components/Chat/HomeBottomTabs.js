import React, { useEffect, useState } from 'react';
import { Platform, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { BlurView } from 'expo-blur';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from '@expo/vector-icons/Ionicons';
import Svg, { Line, Polygon, Rect } from 'react-native-svg';
import { useTranslation } from 'react-i18next';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../context/ThemeContext';
import { hindiReadableTextStyle, isHindiLocale } from '../../utils/hindiText';
import { getWebBottomInset } from '../../platform/webSafeArea';

let createPortal = null;
if (Platform.OS === 'web') {
  try {
    // eslint-disable-next-line global-require
    createPortal = require('react-dom').createPortal;
  } catch (_) {
    createPortal = null;
  }
}

export function getHomeBottomTabMetrics(bottomInset = 0) {
  const contentHeight = Platform.OS === 'ios' ? 80 : Platform.OS === 'web' ? 56 : 70;
  const safeBottom = Platform.OS === 'ios'
    ? 10
    : Platform.OS === 'web'
      ? Math.min(getWebBottomInset(bottomInset), 12)
      : Math.max(0, bottomInset || 0);

  return {
    contentHeight,
    safeBottom,
    totalHeight: contentHeight + safeBottom,
  };
}

export default function HomeBottomTabs({
  activeTab = 'today',
  onToday,
  onAskTara,
  onExplore,
  onCharts,
  onYou,
  visible = true,
}) {
  const { t, i18n } = useTranslation();
  const insets = useSafeAreaInsets();
  const { theme, colors, isPanditMode } = useTheme();
  const {
    contentHeight: tabContentHeight,
    safeBottom: tabSafeBottom,
  } = getHomeBottomTabMetrics(insets.bottom);
  const isHindiUi = isPanditMode || isHindiLocale(i18n.language);
  const tabActiveWeight = isHindiUi ? '600' : '800';
  const tabIdleWeight = isHindiUi ? '500' : '600';
  const tabSafeColor = colors.tabBarSurface || colors.headerSurface;
  const tabBarGradient = [tabSafeColor, tabSafeColor];
  const tabActiveColor = colors.tabActiveColor || colors.accent;
  const tabIdleColor = colors.tabIdleColor || colors.textInverseMuted;
  const [webMounted, setWebMounted] = useState(false);

  useEffect(() => {
    setWebMounted(true);
  }, []);

  if (!visible) return null;

  const tabColor = (key) => (activeTab === key ? tabActiveColor : tabIdleColor);
  const tabWeight = (key) => (activeTab === key ? tabActiveWeight : tabIdleWeight);

  const bottomTabs = (
    <View
      style={[
        styles.bottomTabs,
        {
          bottom: 0,
          height: tabContentHeight + tabSafeBottom,
          paddingBottom: tabSafeBottom,
          ...(Platform.OS === 'web'
            ? {
                position: 'fixed',
                left: 0,
                right: 0,
                width: '100%',
                maxWidth: 520,
                marginLeft: 'auto',
                marginRight: 'auto',
                zIndex: 10000,
                backgroundColor: tabSafeColor,
              }
            : null),
        },
      ]}
      {...(Platform.OS === 'web' ? { dataSet: { arHomeBottomNav: '1' } } : null)}
    >
      <LinearGradient
        colors={tabBarGradient}
        style={StyleSheet.absoluteFill}
        start={{ x: 0, y: 0 }}
        end={{ x: 0, y: 1 }}
      />
      {Platform.OS === 'ios' && (
        <BlurView
          intensity={theme === 'dark' ? 20 : 60}
          style={StyleSheet.absoluteFill}
          tint={theme === 'dark' ? 'dark' : 'light'}
        />
      )}

      <TouchableOpacity
        style={styles.tabItem}
        onPress={onToday}
        activeOpacity={0.7}
        accessibilityRole="tab"
        accessibilityState={{ selected: activeTab === 'today' }}
        accessibilityLabel={t('premiumUi.home.tabs.today')}
      >
        <View style={styles.tabIconContainer}>
          <Icon name="today-outline" size={22} color={tabColor('today')} />
        </View>
        <Text style={[
          styles.tabLabel,
          hindiReadableTextStyle(isHindiUi ? 'hi' : i18n.language, styles.tabLabel),
          { color: tabColor('today'), fontWeight: tabWeight('today') },
        ]}>
          {t('premiumUi.home.tabs.today')}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.tabItem}
        onPress={onAskTara}
        activeOpacity={0.7}
        accessibilityRole="tab"
        accessibilityState={{ selected: activeTab === 'ask' }}
        accessibilityLabel={t('premiumUi.home.tabs.askTara')}
      >
        <View style={styles.tabIconContainer}>
          <Icon name="sparkles-outline" size={22} color={tabColor('ask')} />
        </View>
        <Text style={[styles.tabLabel, hindiReadableTextStyle(isHindiUi ? 'hi' : i18n.language, styles.tabLabel), { color: tabColor('ask'), fontWeight: tabWeight('ask') }]}>
          {t('premiumUi.home.tabs.askTara')}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.tabItem}
        onPress={onExplore}
        activeOpacity={0.7}
        accessibilityRole="tab"
        accessibilityState={{ selected: activeTab === 'explore' }}
        accessibilityLabel={t('premiumUi.home.tabs.explore')}
      >
        <View style={styles.tabIconContainer}>
          <Icon name="compass-outline" size={22} color={tabColor('explore')} />
        </View>
        <Text style={[styles.tabLabel, hindiReadableTextStyle(isHindiUi ? 'hi' : i18n.language, styles.tabLabel), { color: tabColor('explore'), fontWeight: tabWeight('explore') }]}>
          {t('premiumUi.home.tabs.explore')}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.tabItem}
        onPress={onCharts}
        activeOpacity={0.7}
        accessibilityRole="tab"
        accessibilityState={{ selected: activeTab === 'charts' }}
        accessibilityLabel={t('premiumUi.home.tabs.charts')}
      >
        <View style={styles.tabIconContainer}>
          <Svg width="22" height="22" viewBox="0 0 48 48">
            <Rect x="2" y="2" width="44" height="44" fill="none" stroke={tabColor('charts')} strokeWidth="3" />
            <Polygon points="24,2 46,24 24,46 2,24" fill="none" stroke={activeTab === 'charts' ? (isPanditMode ? tabActiveColor : '#ffd700') : tabIdleColor} strokeWidth="2" />
            <Line x1="2" y1="2" x2="46" y2="46" stroke={tabColor('charts')} strokeWidth="1.5" />
            <Line x1="46" y1="2" x2="2" y2="46" stroke={tabColor('charts')} strokeWidth="1.5" />
          </Svg>
        </View>
        <Text style={[styles.tabLabel, hindiReadableTextStyle(isHindiUi ? 'hi' : i18n.language, styles.tabLabel), { color: tabColor('charts'), fontWeight: tabWeight('charts') }]}>
          {t('premiumUi.home.tabs.charts')}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.tabItem}
        onPress={onYou}
        activeOpacity={0.7}
        accessibilityRole="tab"
        accessibilityState={{ selected: activeTab === 'you' }}
        accessibilityLabel={t('premiumUi.home.tabs.you')}
      >
        <View style={styles.tabIconContainer}>
          <Icon name="person-outline" size={22} color={tabColor('you')} />
        </View>
        <Text style={[styles.tabLabel, hindiReadableTextStyle(isHindiUi ? 'hi' : i18n.language, styles.tabLabel), { color: tabColor('you'), fontWeight: tabWeight('you') }]}>
          {t('premiumUi.home.tabs.you')}
        </Text>
      </TouchableOpacity>
    </View>
  );

  if (Platform.OS === 'web') {
    if (!webMounted || !createPortal || typeof document === 'undefined') return null;
    return createPortal(bottomTabs, document.body);
  }
  return bottomTabs;
}

const styles = StyleSheet.create({
  bottomTabs: {
    flexDirection: 'row',
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    zIndex: 10000,
    overflow: Platform.OS === 'web' ? 'visible' : 'hidden',
    ...Platform.select({
      ios: {
        height: 80,
        paddingTop: 0,
        paddingBottom: 0,
      },
      android: {
        height: 70,
        paddingTop: 0,
        paddingBottom: 0,
      },
      web: {
        height: undefined,
        paddingTop: 0,
        paddingBottom: 0,
      },
    }),
  },
  tabItem: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 0,
  },
  tabIconContainer: {
    width: 42,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 4,
  },
  tabLabel: {
    fontSize: 11,
    marginTop: 2,
    letterSpacing: 0.3,
  },
});
