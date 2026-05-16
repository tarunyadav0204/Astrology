import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Dimensions,
  Platform,
} from 'react-native';
import { BlurView } from 'expo-blur';
import Icon from '@expo/vector-icons/Ionicons';
import Svg, { Rect, Polygon, Line } from 'react-native-svg';
import { useTranslation } from 'react-i18next';
import { IS_ASTROLOGY_ONLY } from '../../config/appVariant';

const { width } = Dimensions.get('window');

export default function HomeAstrologyToolsSection({
  birthData,
  chartData,
  dashData,
  navigation,
  setShowDashaBrowser,
  theme,
  colors,
  isClassic,
  useGlass,
  toolCardInnerStyle,
  androidLightCardFixStyle,
  hasPremiumToolsAccess,
  onPremiumToolPress,
  renderToolLockOverlay,
}) {
  const { t } = useTranslation();

  const toolGlassBase = [
    styles.toolGlassmorphism,
    androidLightCardFixStyle,
    useGlass && { overflow: 'hidden' },
  ];

  const wrapPress = (handler) => () => onPremiumToolPress(handler);

  return (
    <View style={[styles.toolsSection, { marginTop: 0, marginBottom: 8 }]}>
      <View style={styles.toolsSectionHeaderRow}>
        <View style={styles.toolsSectionHeaderText}>
          <Text style={[styles.toolsSectionTitle, { color: colors.text }]}>
            {IS_ASTROLOGY_ONLY
              ? t('home.sections.premiumTools', 'Premium · Reference Tools')
              : t('home.sections.astrologyTools', '🔧 Astrology Tools')}
          </Text>
          {IS_ASTROLOGY_ONLY && (
            <Text style={[styles.toolsSectionSubtitle, { color: colors.textSecondary }]}>
              {hasPremiumToolsAccess
                ? t('home.premiumTools.unlocked', 'Advanced Vedic calculators for chart study.')
                : t(
                    'home.premiumTools.locked',
                    'Unlock charts, dashas, KP, and more with credits or a subscription.',
                  )}
            </Text>
          )}
        </View>
        {IS_ASTROLOGY_ONLY && (
          <View style={[styles.premiumSectionBadge, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}>
            <Text style={[styles.premiumSectionBadgeText, { color: colors.text }]}>PREMIUM</Text>
          </View>
        )}
      </View>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.toolsScrollContent}
        decelerationRate="fast"
        snapToInterval={width * 0.3 + 12}
      >
        <TouchableOpacity
          style={[styles.toolCard, androidLightCardFixStyle]}
          onPress={wrapPress(() => navigation.navigate('Chart', { birthData }))}
          activeOpacity={0.8}
        >
          <View
            style={[
              ...toolGlassBase,
              isClassic
                ? toolCardInnerStyle
                : {
                    backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(251, 146, 60, 0.15)',
                    borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.3)',
                  },
            ]}
          >
            {useGlass && <BlurView intensity={40} style={StyleSheet.absoluteFill} tint={theme === 'dark' ? 'dark' : 'light'} />}
            {useGlass && (
              <View
                style={[StyleSheet.absoluteFill, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.15)' }]}
                pointerEvents="none"
              />
            )}
            <View style={styles.toolIconContainer}>
              <Svg width="28" height="28" viewBox="0 0 48 48">
                <Rect x="2" y="2" width="44" height="44" fill="none" stroke={isClassic ? '#000' : '#ffffff'} strokeWidth="2" />
                <Polygon points="24,2 46,24 24,46 2,24" fill="none" stroke={isClassic ? '#333' : '#ffd700'} strokeWidth="1.5" />
                <Line x1="2" y1="2" x2="46" y2="46" stroke={isClassic ? '#666' : '#ff8a65'} strokeWidth="1" />
                <Line x1="46" y1="2" x2="2" y2="46" stroke={isClassic ? '#666' : '#ff8a65'} strokeWidth="1" />
              </Svg>
            </View>
            <Text style={[styles.toolTitle, { color: colors.text }]}>{t('home.tools.charts', 'Charts')}</Text>
            {renderToolLockOverlay()}
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.toolCard, androidLightCardFixStyle]}
          onPress={wrapPress(() => setShowDashaBrowser(true))}
          activeOpacity={0.8}
        >
          <View
            style={[
              ...toolGlassBase,
              isClassic
                ? toolCardInnerStyle
                : {
                    backgroundColor: theme === 'dark' ? 'rgba(139, 92, 246, 0.1)' : 'rgba(139, 92, 246, 0.15)',
                    borderColor: 'rgba(139, 92, 246, 0.3)',
                  },
            ]}
          >
            {useGlass && <BlurView intensity={40} style={StyleSheet.absoluteFill} tint={theme === 'dark' ? 'dark' : 'light'} />}
            <View style={styles.toolIconContainer}>
              <Icon name="time-outline" size={24} color={isClassic ? colors.text : '#A78BFA'} />
            </View>
            <Text style={[styles.toolTitle, { color: colors.text }]}>{t('home.tools.dashas', 'Dashas')}</Text>
            {renderToolLockOverlay()}
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.toolCard, androidLightCardFixStyle]}
          onPress={wrapPress(() => navigation.navigate('KPSystem', { birthDetails: birthData }))}
          activeOpacity={0.8}
        >
          <View
            style={[
              ...toolGlassBase,
              isClassic
                ? toolCardInnerStyle
                : {
                    backgroundColor: theme === 'dark' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(16, 185, 129, 0.15)',
                    borderColor: 'rgba(16, 185, 129, 0.3)',
                  },
            ]}
          >
            <View style={styles.toolIconContainer}>
              <Icon name="locate-outline" size={24} color={isClassic ? colors.text : '#34D399'} />
            </View>
            <Text style={[styles.toolTitle, { color: colors.text }]}>{t('menu.kpSystem', 'KP System')}</Text>
            {renderToolLockOverlay()}
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.toolCard, androidLightCardFixStyle]}
          onPress={wrapPress(() =>
            navigation.navigate('KotaChakra', {
              birthChartId: birthData?.id ?? birthData?.birth_chart_id,
            }),
          )}
          activeOpacity={0.8}
        >
          <View style={[...toolGlassBase, isClassic ? toolCardInnerStyle : { backgroundColor: theme === 'dark' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(245, 158, 11, 0.15)', borderColor: 'rgba(245, 158, 11, 0.3)' }]}>
            <View style={styles.toolIconContainer}>
              <Icon name="shield-checkmark-outline" size={24} color={isClassic ? colors.text : '#FBBF24'} />
            </View>
            <Text style={[styles.toolTitle, { color: colors.text }]}>{t('menu.kotaChakra', 'Kota Chakra')}</Text>
            {renderToolLockOverlay()}
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.toolCard, androidLightCardFixStyle]}
          onPress={wrapPress(() => navigation.navigate('Yogas'))}
          activeOpacity={0.8}
        >
          <View style={[...toolGlassBase, isClassic ? toolCardInnerStyle : { backgroundColor: theme === 'dark' ? 'rgba(236, 72, 153, 0.1)' : 'rgba(236, 72, 153, 0.15)', borderColor: 'rgba(236, 72, 153, 0.3)' }]}>
            <View style={styles.toolIconContainer}>
              <Icon name="diamond-outline" size={24} color={isClassic ? colors.text : '#F472B6'} />
            </View>
            <Text style={[styles.toolTitle, { color: colors.text }]}>{t('menu.yogas', 'Yogas')}</Text>
            {renderToolLockOverlay()}
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.toolCard, androidLightCardFixStyle]}
          onPress={wrapPress(() => navigation.navigate('AshtakvargaOracle'))}
          activeOpacity={0.8}
        >
          <View style={[...toolGlassBase, isClassic ? toolCardInnerStyle : { backgroundColor: theme === 'dark' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.15)', borderColor: 'rgba(59, 130, 246, 0.3)' }]}>
            <View style={styles.toolIconContainer}>
              <Icon name="grid-outline" size={24} color={isClassic ? colors.text : '#60A5FA'} />
            </View>
            <Text style={[styles.toolTitle, { color: colors.text }]}>{t('home.tools.ashtakvarga', 'Ashtak-\nvarga')}</Text>
            {renderToolLockOverlay()}
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.toolCard, androidLightCardFixStyle]}
          onPress={wrapPress(() => chartData && navigation.navigate('PlanetaryPositions', { chartData }))}
          activeOpacity={0.8}
        >
          <View style={[...toolGlassBase, isClassic ? toolCardInnerStyle : { backgroundColor: theme === 'dark' ? 'rgba(244, 63, 94, 0.1)' : 'rgba(244, 63, 94, 0.15)', borderColor: 'rgba(244, 63, 94, 0.3)' }]}>
            <View style={styles.toolIconContainer}>
              <Icon name="planet-outline" size={24} color={isClassic ? colors.text : '#FB7185'} />
            </View>
            <Text style={[styles.toolTitle, { color: colors.text }]}>{t('home.tools.positions', 'Positions')}</Text>
            {renderToolLockOverlay()}
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.toolCard, androidLightCardFixStyle]}
          onPress={wrapPress(() => navigation.navigate('CosmicRing'))}
          activeOpacity={0.8}
        >
          <View style={[...toolGlassBase, isClassic ? toolCardInnerStyle : { backgroundColor: theme === 'dark' ? 'rgba(56, 189, 248, 0.1)' : 'rgba(56, 189, 248, 0.15)', borderColor: 'rgba(56, 189, 248, 0.3)' }]}>
            <View style={styles.toolIconContainer}>
              <Icon name="ellipse-outline" size={24} color={isClassic ? colors.text : '#38BDF8'} />
            </View>
            <Text style={[styles.toolTitle, { color: colors.text }]}>{t('home.tools.cosmicRing', 'Cosmic\nRing')}</Text>
            {renderToolLockOverlay()}
          </View>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  toolsSection: {
    marginBottom: 8,
  },
  toolsSectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 12,
    gap: 8,
  },
  toolsSectionHeaderText: {
    flex: 1,
    minWidth: 0,
  },
  toolsSectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  toolsSectionSubtitle: {
    fontSize: 12,
    lineHeight: 17,
    marginTop: 4,
  },
  premiumSectionBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    flexShrink: 0,
  },
  premiumSectionBadgeText: {
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.6,
  },
  toolsScrollContent: {
    paddingHorizontal: 4,
    gap: 12,
  },
  toolCard: {
    width: width * 0.26,
    borderRadius: 16,
    overflow: 'hidden',
  },
  toolGlassmorphism: {
    padding: 10,
    alignItems: 'center',
    minHeight: 80,
    maxHeight: 80,
    justifyContent: 'center',
    position: 'relative',
    borderRadius: 16,
    borderWidth: 1,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.08,
        shadowRadius: 4,
      },
      android: { elevation: 2 },
    }),
  },
  toolIconContainer: {
    marginBottom: 4,
    alignItems: 'center',
    justifyContent: 'center',
  },
  toolTitle: {
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'center',
    lineHeight: 14,
  },
  toolLockOverlay: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
