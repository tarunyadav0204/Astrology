import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
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

const TAB_KEYS = ['chart', 'dasha', 'ashtakvarga'];

export default function ChartsHubScreen({ navigation, route }) {
  useAnalytics('ChartsHubScreen');
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';

  const initialTab = TAB_KEYS.includes(route.params?.tab) ? route.params.tab : 'chart';
  const [activeTab, setActiveTab] = useState(initialTab);
  const [birthData, setBirthData] = useState(route.params?.birthData || null);

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

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
      <SafeAreaView style={styles.safeTop} edges={['top']}>
        <View style={[styles.header, { borderBottomColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)' }]}>
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            style={[styles.backButton, { backgroundColor: isDark ? 'rgba(255,255,255,0.12)' : 'rgba(249,115,22,0.18)' }]}
            accessibilityRole="button"
            accessibilityLabel={t('common.back', 'Back')}
          >
            <Ionicons name="arrow-back" size={20} color={colors.text} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1}>
            {t('chartsHub.title', 'Charts')}
          </Text>
          <View style={styles.headerSpacer} />
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

      <View style={styles.content}>
        {activeTab === 'chart' ? (
          <ChartScreen
            key={`chart-${birthData?.id || birthData?.name || 'none'}`}
            navigation={navigation}
            route={chartRoute}
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
          />
        ) : null}
        {activeTab === 'ashtakvarga' ? (
          <AshtakvargaOracle
            key={`ashtak-${birthData?.id || birthData?.name || 'none'}`}
            navigation={navigation}
            route={ashtakRoute}
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
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
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
});
