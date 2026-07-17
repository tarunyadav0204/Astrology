import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  Platform,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { storage } from '../../services/storage';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useTranslation } from 'react-i18next';
import ChartScreen from './ChartScreen';
import CascadingDashaBrowser from '../Dasha/CascadingDashaBrowser';
import AshtakvargaOracle from '../Ashtakvarga/AshtakvargaOracle';
import NativeSelectorChip from '../Common/NativeSelectorChip';

const TAB_KEYS = ['chart', 'dasha', 'ashtakvarga'];

export default function ChartsHubScreen({ navigation, route }) {
  useAnalytics('ChartsHubScreen');
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';

  const initialTab = TAB_KEYS.includes(route.params?.tab) ? route.params.tab : 'chart';
  const [activeTab, setActiveTab] = useState(initialTab);
  const [birthData, setBirthData] = useState(route.params?.birthData || null);
  const [chartHeader, setChartHeader] = useState(null);
  const [dashaHeader, setDashaHeader] = useState(null);
  const [ashtakHeader, setAshtakHeader] = useState(null);

  const loadBirthData = useCallback(async () => {
    try {
      const data = await storage.getBirthDetails();
      if (data?.name) {
        setBirthData(data);
      }
    } catch (error) {
      console.error('ChartsHub birth data load failed:', error);
    }
  }, []);

  useEffect(() => {
    if (TAB_KEYS.includes(route.params?.tab)) {
      setActiveTab(route.params.tab);
    }
    if (route.params?.birthData?.name) {
      setBirthData(route.params.birthData);
    }
  }, [route.params?.tab, route.params?.birthData]);

  useFocusEffect(
    useCallback(() => {
      loadBirthData();
    }, [loadBirthData])
  );

  const onChartHeaderStateChange = useCallback((next) => {
    setChartHeader(next);
  }, []);

  const onDashaHeaderStateChange = useCallback((next) => {
    setDashaHeader(next);
  }, []);

  const onAshtakHeaderStateChange = useCallback((next) => {
    setAshtakHeader(next);
  }, []);

  const tabs = useMemo(
    () => [
      { key: 'chart', label: t('chartsHub.tabs.chart', 'Chart') },
      { key: 'dasha', label: t('chartsHub.tabs.dasha', 'Dasha') },
      { key: 'ashtakvarga', label: t('chartsHub.tabs.ashtakvarga', 'Ashtakvarga') },
    ],
    [t]
  );

  const chartRoute = useMemo(
    () => ({
      key: 'ChartsHubChart',
      name: 'Chart',
      params: {
        embedded: true,
        birthData: birthData || undefined,
      },
    }),
    [birthData]
  );

  const ashtakRoute = useMemo(
    () => ({
      key: 'ChartsHubAshtak',
      name: 'AshtakvargaOracle',
      params: { embedded: true },
    }),
    []
  );

  const showChartHeader = activeTab === 'chart' && !!chartHeader?.chartName;
  const showDashaHeader = activeTab === 'dasha';
  const showAshtakHeader = activeTab === 'ashtakvarga';
  const actionBtnBg = isDark ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)';
  const dashaTitle = dashaHeader?.title || t('dasha.browserTitle', 'Dasha Browser');
  const dashaBirth = dashaHeader?.birthData || birthData;
  const ashtakTitle = ashtakHeader?.title || t('chartsHub.tabs.ashtakvarga', 'Ashtakvarga');
  const ashtakBirth = ashtakHeader?.birthData || birthData;

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
      <SafeAreaView style={styles.safeTop} edges={['top']}>
        <View style={[styles.header, { borderBottomColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)' }]}>
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            style={[styles.backButton, { backgroundColor: actionBtnBg }]}
            accessibilityRole="button"
            accessibilityLabel={t('common.back', 'Back')}
          >
            <Ionicons name="arrow-back" size={20} color={colors.text} />
          </TouchableOpacity>

          {showChartHeader ? (
            <>
              <View style={styles.headerCenter}>
                <Text style={[styles.chartTitle, { color: colors.text }]} numberOfLines={1}>
                  {chartHeader.chartName}
                </Text>
                {(chartHeader.birthData || birthData) ? (
                  <NativeSelectorChip
                    birthData={chartHeader.birthData || birthData}
                    onPress={() => navigation.navigate('SelectNative', { returnTo: 'ChartsHub' })}
                    maxLength={14}
                    style={styles.nativeChip}
                    textStyle={styles.nativeChipText}
                    showIcon={false}
                  />
                ) : null}
              </View>
              <TouchableOpacity
                onPress={chartHeader.onShare}
                style={[styles.headerAction, { backgroundColor: actionBtnBg }]}
                disabled={!!chartHeader.isSharing}
                accessibilityRole="button"
                accessibilityLabel={t('common.share', 'Share')}
              >
                <Ionicons name="share-outline" size={18} color={colors.text} />
              </TouchableOpacity>
              <View style={[styles.positionBadge, { backgroundColor: actionBtnBg }]}>
                <Text style={[styles.positionText, { color: colors.text }]}>
                  {chartHeader.positionLabel}
                </Text>
              </View>
            </>
          ) : showDashaHeader ? (
            <>
              <View style={styles.headerCenter}>
                <Text style={[styles.chartTitle, { color: colors.text }]} numberOfLines={1}>
                  {dashaTitle}
                </Text>
                {dashaBirth?.name ? (
                  <NativeSelectorChip
                    birthData={dashaBirth}
                    onPress={() =>
                      navigation.navigate('SelectNative', {
                        returnTo: 'ChartsHub',
                        returnParams: { tab: 'dasha' },
                      })
                    }
                    maxLength={14}
                    style={styles.nativeChip}
                    textStyle={styles.nativeChipText}
                    showIcon={false}
                  />
                ) : null}
              </View>
              <View style={styles.headerSpacer} />
            </>
          ) : showAshtakHeader ? (
            <>
              <View style={styles.headerCenter}>
                <Text style={[styles.chartTitle, { color: colors.text }]} numberOfLines={1}>
                  {ashtakTitle}
                </Text>
                {ashtakBirth?.name ? (
                  <NativeSelectorChip
                    birthData={ashtakBirth}
                    onPress={() =>
                      navigation.navigate('SelectNative', {
                        returnTo: 'ChartsHub',
                        returnParams: { tab: 'ashtakvarga' },
                      })
                    }
                    maxLength={14}
                    style={styles.nativeChip}
                    textStyle={styles.nativeChipText}
                    showIcon={false}
                  />
                ) : null}
              </View>
              <TouchableOpacity
                onPress={() => ashtakHeader?.onOpenInfo?.()}
                style={[styles.headerAction, { backgroundColor: actionBtnBg }]}
                accessibilityRole="button"
                accessibilityLabel={t('common.info', 'Info')}
              >
                <Ionicons name="information-circle-outline" size={20} color={colors.text} />
              </TouchableOpacity>
            </>
          ) : (
            <>
              <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1}>
                {t('chartsHub.title', 'Charts')}
              </Text>
              <View style={styles.headerSpacer} />
            </>
          )}
        </View>

        <View style={[styles.tabRow, { backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(249,115,22,0.08)' }]}>
          {tabs.map((tab) => {
            const selected = activeTab === tab.key;
            return (
              <TouchableOpacity
                key={tab.key}
                style={[
                  styles.tabChip,
                  selected && {
                    backgroundColor: isDark ? 'rgba(249,115,22,0.9)' : '#fff',
                    shadowColor: '#000',
                    shadowOpacity: 0.08,
                    shadowRadius: 4,
                    shadowOffset: { width: 0, height: 1 },
                    elevation: 2,
                  },
                ]}
                onPress={() => setActiveTab(tab.key)}
                activeOpacity={0.8}
              >
                <Text
                  style={[
                    styles.tabLabel,
                    {
                      color: selected
                        ? isDark
                          ? '#fff'
                          : colors.primary
                        : colors.textSecondary,
                      fontWeight: selected ? '800' : '600',
                    },
                  ]}
                  numberOfLines={1}
                >
                  {tab.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </SafeAreaView>

      <View style={[styles.content, Platform.OS === 'web' ? styles.contentWeb : null]}>
        {activeTab === 'chart' ? (
          <ChartScreen
            key={`chart-${birthData?.id || birthData?.name || 'none'}`}
            navigation={navigation}
            route={chartRoute}
            onHeaderStateChange={onChartHeaderStateChange}
          />
        ) : null}
        {activeTab === 'dasha' ? (
          <CascadingDashaBrowser
            key={`dasha-${birthData?.id || birthData?.name || 'none'}`}
            embedded
            visible
            birthData={birthData}
            onClose={() => navigation.goBack()}
            onRequireBirthData={() =>
              navigation.navigate('BirthProfileIntro', { returnTo: 'ChartsHub' })
            }
            selectNativeReturnTo="ChartsHub"
            onHeaderStateChange={onDashaHeaderStateChange}
          />
        ) : null}
        {activeTab === 'ashtakvarga' ? (
          <AshtakvargaOracle
            key={`ashtak-${birthData?.id || birthData?.name || 'none'}`}
            navigation={navigation}
            route={ashtakRoute}
            onHeaderStateChange={onAshtakHeaderStateChange}
          />
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeTop: {
    backgroundColor: 'transparent',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    gap: 8,
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerCenter: {
    flex: 1,
    minWidth: 0,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chartTitle: {
    fontSize: 15,
    fontWeight: '800',
    textAlign: 'center',
  },
  nativeChip: {
    marginTop: 2,
    paddingHorizontal: 6,
    paddingVertical: 1,
  },
  nativeChipText: {
    fontSize: 10,
  },
  headerAction: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  positionBadge: {
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 12,
    minWidth: 40,
    alignItems: 'center',
  },
  positionText: {
    fontSize: 11,
    fontWeight: '700',
  },
  headerTitle: {
    flex: 1,
    textAlign: 'center',
    fontSize: 17,
    fontWeight: '800',
  },
  headerSpacer: {
    width: 36,
  },
  tabRow: {
    flexDirection: 'row',
    marginHorizontal: 12,
    marginTop: 8,
    marginBottom: 8,
    padding: 4,
    borderRadius: 12,
  },
  tabChip: {
    flex: 1,
    paddingVertical: 9,
    paddingHorizontal: 6,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabLabel: {
    fontSize: 13,
  },
  content: {
    flex: 1,
  },
  contentWeb: {
    minHeight: 0,
    overflow: 'hidden',
  },
});
