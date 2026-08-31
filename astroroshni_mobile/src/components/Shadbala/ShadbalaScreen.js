import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import api, { chartAPI } from '../../services/api';
import { getEndpoint } from '../../utils/constants';
import { useAstrologyTranslation } from '../../utils/astrologyTranslation';
import { typographyTokens } from '../../theme/tokens';
import NativeSelectorChip from '../Common/NativeSelectorChip';

const VISIBLE_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
const HOUSE_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
const HOUSE_LABELS = {
  1: 'Self', 2: 'Wealth', 3: 'Siblings', 4: 'Home', 5: 'Children', 6: 'Health',
  7: 'Partner', 8: 'Transformation', 9: 'Fortune', 10: 'Career', 11: 'Gains', 12: 'Release',
};
const PLANET_ICONS = {
  Sun: '☉', Moon: '☽', Mars: '♂', Mercury: '☿', Jupiter: '♃', Venus: '♀', Saturn: '♄',
};

const formatComponentName = (name) => name
  .split('_')
  .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
  .join(' ');

const numericValue = (value) => (typeof value === 'number' && Number.isFinite(value) ? value : 0);
const displayNumber = (value, digits = 1) => (
  typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : '—'
);

const ShadbalaScreen = ({ route, navigation }) => {
  const { birthData } = route.params || {};
  const { colors } = useTheme();
  const { t, translatePlanet } = useAstrologyTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [shadbalaData, setData] = useState(null);
  const [selectedPlanet, setSelectedPlanet] = useState(null);
  const [expandedBreakdown, setExpandedBreakdown] = useState(null);
  const [activeTab, setActiveTab] = useState('planetary');

  const chartIdentity = birthData?.id || birthData?._id || `${birthData?.name || ''}-${birthData?.date || ''}-${birthData?.time || ''}`;

  useEffect(() => {
    if (!birthData?.name) {
      navigation.replace('BirthProfileIntro', { returnTo: 'Shadbala' });
      return;
    }
    fetchShadbala();
  }, [chartIdentity]);

  const fetchShadbala = async () => {
    try {
      setLoading(true);
      setError(null);
      setData(null);
      const chartResponse = await chartAPI.calculateChartOnly(birthData);
      const response = await api.post(getEndpoint('/calculate-classical-shadbala'), {
        birth_data: birthData,
        chart_data: chartResponse.data,
      });
      const clonedData = JSON.parse(JSON.stringify(response.data));
      setData(clonedData);
      const firstPlanet = VISIBLE_PLANETS.find((planet) => clonedData.shadbala?.[planet]);
      setSelectedPlanet(firstPlanet || null);
    } catch (fetchError) {
      console.error('Shadbala fetch error:', fetchError);
      setError(t('premiumUi.shadbala.couldNotCalculate'));
    } finally {
      setLoading(false);
    }
  };

  const planetData = shadbalaData?.shadbala || {};
  const bhavaBala = shadbalaData?.bhava_bala || {};
  const supplementaryHouseStrength = shadbalaData?.supplementary_house_strength || {};

  const planets = useMemo(() => VISIBLE_PLANETS
    .filter((planet) => planetData[planet])
    .map((planet) => ({ name: planet, ...planetData[planet] })), [planetData]);

  const rankedPlanets = useMemo(() => [...planets]
    .sort((first, second) => numericValue(first.relative_rank) - numericValue(second.relative_rank)), [planets]);

  const selected = selectedPlanet ? planetData[selectedPlanet] : null;
  const selectedRank = rankedPlanets.findIndex((planet) => planet.name === selectedPlanet) + 1;
  const strongestPlanet = rankedPlanets[0];
  const maxRequiredRatio = Math.max(...planets.map((planet) => numericValue(planet.required_ratio)), 1);

  const gradeTreatment = (grade) => {
    if (['High', 'Excellent'].includes(grade)) return { foreground: colors.success, background: colors.successSoft || colors.surfaceMuted };
    if (['Meets requirement', 'Good'].includes(grade)) return { foreground: colors.info, background: colors.infoSoft || colors.surfaceMuted };
    if (grade === 'Average') return { foreground: colors.warning, background: colors.warningSoft || colors.surfaceMuted };
    return { foreground: colors.error, background: colors.errorSoft || colors.surfaceMuted };
  };

  const houseGradeTreatment = (grade) => {
    if (['A+', 'A'].includes(grade)) return gradeTreatment('Excellent');
    if (['B+', 'B'].includes(grade)) return gradeTreatment('Good');
    if (['C+', 'C'].includes(grade)) return gradeTreatment('Average');
    return gradeTreatment('Low');
  };

  const renderHeader = () => (
    <View style={[styles.headerShell, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine }]}>
      <SafeAreaView edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.headerButton, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]} accessibilityLabel={t('premiumUi.common.goBack')}>
            <Ionicons name="arrow-back" size={21} color={colors.textInverse} />
          </TouchableOpacity>
          <View style={styles.headerCopy}>
            <Text style={[styles.headerEyebrow, { color: colors.accent }]}>{t('premiumUi.shadbala.planetaryPower')}</Text>
            <Text style={[styles.headerTitle, { color: colors.textInverse }]}>{t('menu.shadbala', 'Shadbala')}</Text>
          </View>
          <NativeSelectorChip
            birthData={birthData}
            onPress={() => navigation.navigate('SelectNative', { returnTo: 'Shadbala' })}
            maxLength={9}
            showIcon={false}
            style={{ backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }}
            textStyle={{ color: colors.textInverseMuted }}
            iconColor={colors.accent}
          />
        </View>
      </SafeAreaView>
    </View>
  );

  const renderLoading = () => (
    <View style={styles.centerState}>
      <View style={[styles.loadingMark, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
        <ActivityIndicator size="small" color={colors.accent} />
      </View>
      <Text style={[styles.stateTitle, { color: colors.text }]}>{t('premiumUi.shadbala.weighing')}</Text>
      <Text style={[styles.stateBody, { color: colors.textSecondary }]}>{t('premiumUi.shadbala.calculating')}</Text>
    </View>
  );

  const renderError = () => (
    <View style={styles.centerState}>
      <View style={[styles.errorMark, { backgroundColor: colors.errorSoft || colors.surfaceMuted }]}>
        <Ionicons name="alert-circle-outline" size={26} color={colors.error} />
      </View>
      <Text style={[styles.stateTitle, { color: colors.text }]}>{t('premiumUi.shadbala.unavailable')}</Text>
      <Text style={[styles.stateBody, { color: colors.textSecondary }]}>{error}</Text>
      <TouchableOpacity onPress={fetchShadbala} style={[styles.retryButton, { backgroundColor: colors.primary }]}>
        <Text style={[styles.retryText, { color: colors.onPrimary }]}>{t('premiumUi.common.tryAgain')}</Text>
      </TouchableOpacity>
    </View>
  );

  const renderPlanetComparison = () => (
    <View style={[styles.comparisonCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
      <Text style={[styles.cardEyebrow, { color: colors.primaryStrong }]}>{t('premiumUi.shadbala.sevenPlanets')}</Text>
      <Text style={[styles.cardTitle, { color: colors.text }]}>{t('premiumUi.shadbala.atGlance')}</Text>
      <Text style={[styles.cardIntro, { color: colors.textSecondary }]}>{t('premiumUi.shadbala.selectPlanet')}</Text>
      <View style={styles.comparisonList}>
        {rankedPlanets.map((planet, index) => {
          const active = selectedPlanet === planet.name;
          const treatment = gradeTreatment(planet.classical_status || planet.grade);
          const barWidth = `${Math.max((numericValue(planet.required_ratio) / maxRequiredRatio) * 100, 4)}%`;
          return (
            <TouchableOpacity key={planet.name} onPress={() => setSelectedPlanet(planet.name)} activeOpacity={0.75} style={[styles.comparisonRow, active && { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
              <View style={[styles.planetGlyphSmall, { backgroundColor: active ? colors.selectionControl : colors.surfaceMuted }]}>
                <Text style={[styles.planetGlyphTextSmall, { color: active ? colors.selectionText : colors.text }]}>{PLANET_ICONS[planet.name]}</Text>
              </View>
              <View style={styles.comparisonContent}>
                <View style={styles.comparisonHeading}>
                  <Text style={[styles.comparisonName, { color: colors.text }]}>{translatePlanet(planet.name)}</Text>
                  <Text style={[styles.comparisonValue, { color: treatment.foreground }]}>{displayNumber(planet.required_ratio, 2)}×</Text>
                </View>
                <View style={[styles.comparisonTrack, { backgroundColor: colors.surfaceMuted }]}>
                  <View style={[styles.comparisonFill, { backgroundColor: active ? colors.primary : treatment.foreground, width: barWidth }]} />
                </View>
              </View>
              <Text style={[styles.rankText, { color: colors.textTertiary }]}>#{index + 1}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );

  const renderComponents = () => {
    const components = Object.entries(selected?.components || {});
    const maxComponent = Math.max(...components.map(([, value]) => numericValue(value)), 1);
    return (
      <View style={[styles.contentCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
        <Text style={[styles.cardEyebrow, { color: colors.primaryStrong }]}>{t('premiumUi.shadbala.sixSources')}</Text>
        <Text style={[styles.cardTitle, { color: colors.text }]}>{t('strengthComponents', 'Strength components')}</Text>
        <View style={styles.componentList}>
          {components.map(([key, value], index) => (
            <View key={key} style={[styles.componentRow, index < components.length - 1 && { borderBottomColor: colors.cardBorder, borderBottomWidth: StyleSheet.hairlineWidth }]}>
              <View style={styles.componentHeading}>
                <Text style={[styles.componentName, { color: colors.text }]}>{t(`components.${key}`, formatComponentName(key))}</Text>
                <Text style={[styles.componentValue, { color: colors.primaryStrong }]}>{displayNumber(value, 1)}</Text>
              </View>
              <View style={[styles.componentTrack, { backgroundColor: colors.surfaceMuted }]}>
                <View style={[styles.componentFill, { backgroundColor: colors.primary, width: `${Math.max((numericValue(value) / maxComponent) * 100, 3)}%` }]} />
              </View>
            </View>
          ))}
        </View>
      </View>
    );
  };

  const renderBreakdown = (type, title, entries) => {
    if (!entries || Object.keys(entries).length === 0) return null;
    const expanded = expandedBreakdown === type;
    return (
      <View style={[styles.breakdownCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
        <TouchableOpacity onPress={() => setExpandedBreakdown(expanded ? null : type)} style={styles.breakdownHeader} accessibilityRole="button" accessibilityState={{ expanded }}>
          <View style={[styles.breakdownIcon, { backgroundColor: colors.accentSoft }]}>
            <Ionicons name={type === 'sthana' ? 'location-outline' : 'time-outline'} size={19} color={colors.primaryStrong} />
          </View>
          <View style={styles.breakdownCopy}>
            <Text style={[styles.breakdownTitle, { color: colors.text }]}>{title}</Text>
            <Text style={[styles.breakdownCount, { color: colors.textSecondary }]}>{t('premiumUi.shadbala.classicalFactors', { count: Object.keys(entries).length })}</Text>
          </View>
          <Ionicons name={expanded ? 'remove' : 'add'} size={20} color={colors.primaryStrong} />
        </TouchableOpacity>
        {expanded ? (
          <View style={[styles.breakdownRows, { borderTopColor: colors.cardBorder }]}>
            {Object.entries(entries).map(([key, value], index, all) => (
              <View key={key} style={[styles.detailRow, index < all.length - 1 && { borderBottomColor: colors.cardBorder, borderBottomWidth: StyleSheet.hairlineWidth }]}>
                <Text style={[styles.detailName, { color: colors.textSecondary }]}>{t(`components.${key}`, formatComponentName(key))}</Text>
                <Text style={[styles.detailValue, { color: colors.text }]}>{typeof value === 'number' ? value.toFixed(1) : value}</Text>
              </View>
            ))}
          </View>
        ) : null}
      </View>
    );
  };

  const renderClassicalStandard = () => (
    <View style={[styles.contentCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
      <Text style={[styles.cardEyebrow, { color: colors.primaryStrong }]}>{t('premiumUi.shadbala.classicalStandard', 'CLASSICAL STANDARD')}</Text>
      <Text style={[styles.cardTitle, { color: colors.text }]}>{t('premiumUi.shadbala.requirementComparison', 'Requirement comparison')}</Text>
      <Text style={[styles.cardIntro, { color: colors.textSecondary }]}>{t('premiumUi.shadbala.requirementExplanation', 'Parashara assigns a different minimum to each planet. Rank is based on the ratio to that minimum, not the largest raw total.')}</Text>
      <View style={styles.standardGrid}>
        <View style={[styles.standardCell, { backgroundColor: colors.surfaceMuted }]}>
          <Text style={[styles.standardLabel, { color: colors.textSecondary }]}>{t('premiumUi.shadbala.minimum', 'Minimum')}</Text>
          <Text style={[styles.standardValue, { color: colors.text }]}>{displayNumber(selected.minimum_required_points, 0)}</Text>
          <Text style={[styles.standardNote, { color: colors.textTertiary }]}>{displayNumber(selected.minimum_required_rupas, 2)} {t('rupas', 'Rupas')}</Text>
        </View>
        <View style={[styles.standardCell, { backgroundColor: colors.surfaceMuted }]}>
          <Text style={[styles.standardLabel, { color: colors.textSecondary }]}>{t('premiumUi.shadbala.requiredRatio', 'Required ratio')}</Text>
          <Text style={[styles.standardValue, { color: gradeTreatment(selected.classical_status || selected.grade).foreground }]}>{displayNumber(selected.required_ratio, 2)}×</Text>
          <Text style={[styles.standardNote, { color: colors.textTertiary }]}>{displayNumber(selected.required_percent, 1)}%</Text>
        </View>
        <View style={[styles.standardCell, { backgroundColor: colors.surfaceMuted }]}>
          <Text style={[styles.standardLabel, { color: colors.textSecondary }]}>{t('premiumUi.shadbala.relativeRank', 'Relative rank')}</Text>
          <Text style={[styles.standardValue, { color: colors.text }]}>#{selectedRank}</Text>
          <Text style={[styles.standardNote, { color: colors.textTertiary }]}>{t('premiumUi.shadbala.ofSeven', 'of 7 planets')}</Text>
        </View>
      </View>
      <View style={[styles.phalaRow, { borderTopColor: colors.cardBorder }]}>
        <View style={styles.phalaCell}>
          <Text style={[styles.standardLabel, { color: colors.textSecondary }]}>{t('premiumUi.shadbala.ishtaPhala')}</Text>
          <Text style={[styles.phalaValue, { color: colors.success }]}>{displayNumber(selected.ishta_phala, 2)}</Text>
          <Text style={[styles.standardNote, { color: colors.textTertiary }]}>{t('premiumUi.shadbala.ishtaMeaning', 'Agreeable result-giving capacity')}</Text>
        </View>
        <View style={[styles.phalaDivider, { backgroundColor: colors.cardBorder }]} />
        <View style={styles.phalaCell}>
          <Text style={[styles.standardLabel, { color: colors.textSecondary }]}>{t('premiumUi.shadbala.kashtaPhala')}</Text>
          <Text style={[styles.phalaValue, { color: colors.warning }]}>{displayNumber(selected.kashta_phala, 2)}</Text>
          <Text style={[styles.standardNote, { color: colors.textTertiary }]}>{t('premiumUi.shadbala.kashtaMeaning', 'Difficult result-giving capacity')}</Text>
        </View>
      </View>
    </View>
  );

  const renderMethodNotice = () => {
    const validation = shadbalaData?.validation;
    if (!validation) return null;
    return (
      <View style={[styles.methodCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
        <View style={[styles.methodIcon, { backgroundColor: colors.accentSoft }]}><Ionicons name="information-circle-outline" size={20} color={colors.primaryStrong} /></View>
        <View style={styles.methodCopy}>
          <Text style={[styles.methodTitle, { color: colors.text }]}>{t('premiumUi.shadbala.methodLimits', 'Method and limits')}</Text>
          <Text style={[styles.methodBody, { color: colors.textSecondary }]}>{validation.note}</Text>
          <Text style={[styles.methodMeta, { color: colors.textTertiary }]}>{t('premiumUi.shadbala.conventionDependent', 'Convention-dependent')}: {(validation.convention_dependent_rows || []).join(', ')}</Text>
        </View>
      </View>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} />
      {renderHeader()}
      {loading ? renderLoading() : error ? renderError() : (
        <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
          <View style={[styles.heroCard, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
            <View style={[styles.orbitLarge, { borderColor: colors.cosmicLine }]} />
            <View style={[styles.orbitSmall, { borderColor: colors.cosmicLine }]} />
            <Text style={[styles.heroEyebrow, { color: colors.accent }]}>{t('premiumUi.shadbala.classicalProfile')}</Text>
            <Text style={[styles.heroTitle, { color: colors.textInverse }]}>{t('premiumUi.shadbala.notEqual')}</Text>
            <Text style={[styles.heroBody, { color: colors.textInverseMuted }]}>{t('premiumUi.shadbala.heroBody')}</Text>
            <View style={[styles.heroMetrics, { borderTopColor: colors.cosmicLine }]}>
              <View style={styles.heroMetric}>
                <Text style={[styles.heroMetricLabel, { color: colors.textInverseMuted }]}>{t('premiumUi.shadbala.strongest')}</Text>
                <Text style={[styles.heroMetricValue, { color: colors.accent }]}>{strongestPlanet ? translatePlanet(strongestPlanet.name) : '—'}</Text>
              </View>
              <View style={[styles.heroDivider, { backgroundColor: colors.cosmicLine }]} />
              <View style={styles.heroMetric}>
                <Text style={[styles.heroMetricLabel, { color: colors.textInverseMuted }]}>{t('premiumUi.shadbala.planetsWeighed')}</Text>
                <Text style={[styles.heroMetricValue, { color: colors.accent }]}>{planets.length}</Text>
              </View>
            </View>
          </View>

          <View style={[styles.tabBar, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]} accessibilityRole="tablist">
            {[
              ['planetary', t('premiumUi.shadbala.planetaryPower', 'Planetary Shadbala')],
              ['bhava', t('premiumUi.shadbala.bhavaBala', 'Classical Bhava Bala')],
              ['supplementary', t('premiumUi.shadbala.houseScore', 'App house score')],
            ].map(([key, label]) => {
              const active = activeTab === key;
              return (
                <TouchableOpacity
                  key={key}
                  onPress={() => setActiveTab(key)}
                  style={[styles.tabButton, active && { backgroundColor: colors.selectionControl }]}
                  accessibilityRole="tab"
                  accessibilityState={{ selected: active }}
                >
                  <Text style={[styles.tabText, { color: active ? colors.selectionText : colors.textSecondary }]} numberOfLines={2}>{label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          {activeTab === 'planetary' ? (
            <>
              {renderPlanetComparison()}

              {selected ? (
                <>
              <View style={[styles.selectedCard, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
                <View style={[styles.planetGlyph, { backgroundColor: colors.selectionControl, borderColor: colors.selectionBorder }]}>
                  <Text style={[styles.planetGlyphText, { color: colors.selectionText }]}>{PLANET_ICONS[selectedPlanet]}</Text>
                </View>
                <View style={styles.selectedCopy}>
                  <Text style={[styles.selectedEyebrow, { color: colors.selectionTextMuted }]}>{t('premiumUi.shadbala.selectedRank', { rank: selectedRank })}</Text>
                  <Text style={[styles.selectedName, { color: colors.selectionText }]}>{translatePlanet(selectedPlanet)}</Text>
                  <View style={[styles.gradeBadge, { backgroundColor: gradeTreatment(selected.classical_status || selected.grade).background }]}>
                    <Text style={[styles.gradeText, { color: gradeTreatment(selected.classical_status || selected.grade).foreground }]}>{displayNumber(selected.required_percent, 0)}%</Text>
                  </View>
                </View>
                <View style={styles.selectedScore}>
                  <Text style={[styles.selectedScoreValue, { color: colors.selectionText }]}>{displayNumber(selected.total_rupas, 2)}</Text>
                  <Text style={[styles.selectedScoreLabel, { color: colors.selectionTextMuted }]}>{t('rupas', 'Rupas')}</Text>
                  <Text style={[styles.selectedPoints, { color: colors.selectionTextMuted }]}>{displayNumber(selected.total_points, 0)} {t('points', 'points')}</Text>
                </View>
              </View>

              {renderClassicalStandard()}
              {renderComponents()}
              {selected.detailed_breakdown ? (
                <View style={styles.breakdownSection}>
                  <View style={styles.sectionHeading}>
                    <Text style={[styles.sectionEyebrow, { color: colors.primaryStrong }]}>{t('premiumUi.shadbala.deeper')}</Text>
                    <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('premiumUi.shadbala.classicalBreakdown')}</Text>
                  </View>
                  {renderBreakdown('sthana', t('sthanaBalaBreakdown', 'Sthana Bala'), selected.detailed_breakdown.sthana_components)}
                  {renderBreakdown('kala', t('kalaBalaBreakdown', 'Kala Bala'), selected.detailed_breakdown.kala_components)}
                </View>
              ) : null}
                </>
              ) : null}

              {renderMethodNotice()}
            </>
          ) : null}

          {activeTab === 'bhava' && Object.keys(bhavaBala).length > 0 ? (
            <View style={styles.houseSection}>
              <View style={styles.sectionHeading}>
                <Text style={[styles.sectionEyebrow, { color: colors.primaryStrong }]}>{t('premiumUi.shadbala.bhavaSource', 'BPHS 27.26–31')}</Text>
                <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('premiumUi.shadbala.bhavaBala', 'Classical Bhava Bala')}</Text>
                <Text style={[styles.sectionIntro, { color: colors.textSecondary }]}>{t('premiumUi.shadbala.bhavaBalaDescription', 'House strength from the lord’s Shadbala, direction, degree-based aspects, occupants and birth phase. Values are Virupas.')}</Text>
              </View>
              {HOUSE_NUMBERS.map((number) => {
                const data = bhavaBala[String(number)];
                if (!data) return null;
                return (
                  <View key={number} style={[styles.bhavaClassicalCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
                    <View style={styles.bhavaClassicalHeader}>
                      <View>
                        <Text style={[styles.bhavHouseNum, { color: colors.primaryStrong }]}>H{number} · {data.sign_name}</Text>
                        <Text style={[styles.bhavaLord, { color: colors.text }]}>{t('premiumUi.shadbala.lord', 'Lord')}: {translatePlanet(data.lord)}</Text>
                      </View>
                      <View style={styles.bhavaTotal}>
                        <Text style={[styles.bhavaTotalValue, { color: colors.text }]}>{displayNumber(data.total_rupas, 2)}</Text>
                        <Text style={[styles.bhavaTotalUnit, { color: colors.textSecondary }]}>{t('rupas', 'Rupas')} · #{data.relative_rank}</Text>
                      </View>
                    </View>
                    <View style={[styles.bhavaComponents, { borderTopColor: colors.cardBorder }]}>
                      {[
                        [t('premiumUi.shadbala.fromLord', 'From lord'), data.from_lord],
                        [t('premiumUi.shadbala.bhavaDig', 'Dig Bala'), data.dig_bala],
                        [t('premiumUi.shadbala.bhavaDrishti', 'Drishti'), data.drishti_bala],
                        [t('premiumUi.shadbala.planetsIn', 'Planets in'), data.planets_in_bala],
                        [t('premiumUi.shadbala.dayNight', 'Day/Night'), data.day_night_bala],
                      ].map(([label, value]) => (
                        <View key={label} style={styles.bhavaComponent}>
                          <Text style={[styles.bhavaComponentLabel, { color: colors.textSecondary }]}>{label}</Text>
                          <Text style={[styles.bhavaComponentValue, { color: colors.text }]}>{displayNumber(value, 1)}</Text>
                        </View>
                      ))}
                    </View>
                  </View>
                );
              })}
            </View>
          ) : null}

          {activeTab === 'supplementary' && Object.keys(supplementaryHouseStrength).length > 0 ? (
            <View style={styles.houseSection}>
              <View style={styles.sectionHeading}>
                <Text style={[styles.sectionEyebrow, { color: colors.primaryStrong }]}>{t('premiumUi.shadbala.supplementary', 'SUPPLEMENTARY')}</Text>
                <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('premiumUi.shadbala.houseScore', 'App house-strength score')}</Text>
                <Text style={[styles.sectionIntro, { color: colors.textSecondary }]}>{t('premiumUi.shadbala.houseScoreDescription', 'A separate weighted diagnostic. It is not the classical Parashara Bhava Bala worksheet.')}</Text>
              </View>
              <View style={styles.bhavGrid}>
                {HOUSE_NUMBERS.map((number) => {
                  const data = supplementaryHouseStrength[String(number)];
                  if (!data) return null;
                  const grade = data.grade || '—';
                  const treatment = houseGradeTreatment(grade);
                  return (
                    <View key={number} style={[styles.bhavCell, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
                      <View style={styles.houseHeading}>
                        <Text style={[styles.bhavHouseNum, { color: colors.primaryStrong }]}>H{number}</Text>
                        <View style={[styles.bhavGradeBadge, { backgroundColor: treatment.background }]}>
                          <Text style={[styles.bhavGradeText, { color: treatment.foreground }]}>{grade}</Text>
                        </View>
                      </View>
                      <Text style={[styles.bhavHouseLabel, { color: colors.text }]} numberOfLines={1}>{t(`house.${number}`, HOUSE_LABELS[number])}</Text>
                      <Text style={[styles.bhavStrength, { color: colors.textSecondary }]}>{t('premiumUi.shadbala.strength', { value: displayNumber(data.total_strength, 0) })}</Text>
                    </View>
                  );
                })}
              </View>
            </View>
          ) : null}
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  headerShell: { borderBottomWidth: StyleSheet.hairlineWidth },
  header: { minHeight: 72, paddingHorizontal: 18, paddingVertical: 10, flexDirection: 'row', alignItems: 'center', gap: 12 },
  headerButton: { width: 42, height: 42, borderRadius: 21, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  headerCopy: { flex: 1 },
  headerEyebrow: { ...typographyTokens.eyebrow, fontSize: 9, marginBottom: 3 },
  headerTitle: { ...typographyTokens.sectionTitle, fontSize: 25 },
  centerState: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 28 },
  loadingMark: { width: 58, height: 58, borderRadius: 29, borderWidth: 1, alignItems: 'center', justifyContent: 'center', marginBottom: 18 },
  errorMark: { width: 58, height: 58, borderRadius: 29, alignItems: 'center', justifyContent: 'center', marginBottom: 18 },
  stateTitle: { ...typographyTokens.sectionTitle, fontSize: 22, textAlign: 'center', marginBottom: 7 },
  stateBody: { fontSize: 14, lineHeight: 21, textAlign: 'center', maxWidth: 300 },
  retryButton: { minHeight: 44, borderRadius: 22, paddingHorizontal: 22, alignItems: 'center', justifyContent: 'center', marginTop: 18 },
  retryText: { fontSize: 13, fontWeight: '800' },
  scrollContent: { paddingHorizontal: 18, paddingTop: 18, paddingBottom: 52 },
  heroCard: { borderRadius: 28, borderWidth: 1, padding: 24, overflow: 'hidden', marginBottom: 16 },
  orbitLarge: { position: 'absolute', width: 190, height: 190, borderRadius: 95, borderWidth: 1, right: -84, top: -92 },
  orbitSmall: { position: 'absolute', width: 124, height: 124, borderRadius: 62, borderWidth: 1, right: -18, top: -64 },
  heroEyebrow: { ...typographyTokens.eyebrow, marginBottom: 14 },
  heroTitle: { ...typographyTokens.display, fontSize: 35, lineHeight: 40, maxWidth: 285, marginBottom: 12 },
  heroBody: { fontSize: 15, lineHeight: 23, maxWidth: 315 },
  heroMetrics: { flexDirection: 'row', borderTopWidth: StyleSheet.hairlineWidth, marginTop: 22, paddingTop: 17 },
  heroMetric: { flex: 1 },
  heroMetricLabel: { ...typographyTokens.eyebrow, fontSize: 9, marginBottom: 5 },
  heroMetricValue: { ...typographyTokens.sectionTitle, fontSize: 20 },
  heroDivider: { width: StyleSheet.hairlineWidth, marginHorizontal: 16 },
  tabBar: { flexDirection: 'row', borderRadius: 18, borderWidth: 1, padding: 4, marginBottom: 16 },
  tabButton: { flex: 1, minHeight: 48, borderRadius: 14, paddingHorizontal: 6, alignItems: 'center', justifyContent: 'center' },
  tabText: { fontSize: 10, lineHeight: 14, fontWeight: '800', textAlign: 'center' },
  comparisonCard: { borderRadius: 22, borderWidth: 1, padding: 18, marginBottom: 16 },
  cardEyebrow: { ...typographyTokens.eyebrow, fontSize: 9, marginBottom: 5 },
  cardTitle: { ...typographyTokens.sectionTitle, fontSize: 23, marginBottom: 5 },
  cardIntro: { fontSize: 13, lineHeight: 19 },
  comparisonList: { marginTop: 16, gap: 6 },
  comparisonRow: { minHeight: 56, borderRadius: 15, borderWidth: 1, borderColor: 'transparent', flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 8, paddingVertical: 7 },
  planetGlyphSmall: { width: 38, height: 38, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  planetGlyphTextSmall: { fontSize: 22 },
  comparisonContent: { flex: 1 },
  comparisonHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 },
  comparisonName: { fontSize: 13, fontWeight: '700' },
  comparisonValue: { fontSize: 12, fontWeight: '800' },
  comparisonTrack: { height: 5, borderRadius: 3, overflow: 'hidden' },
  comparisonFill: { height: '100%', borderRadius: 3 },
  rankText: { width: 25, textAlign: 'right', fontSize: 10, fontWeight: '700' },
  selectedCard: { borderRadius: 22, borderWidth: 1, padding: 17, flexDirection: 'row', alignItems: 'center', gap: 13, marginBottom: 16 },
  planetGlyph: { width: 58, height: 58, borderRadius: 19, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  planetGlyphText: { fontSize: 35 },
  selectedCopy: { flex: 1, alignItems: 'flex-start' },
  selectedEyebrow: { ...typographyTokens.eyebrow, fontSize: 8, marginBottom: 3 },
  selectedName: { ...typographyTokens.sectionTitle, fontSize: 22, marginBottom: 5 },
  gradeBadge: { borderRadius: 999, paddingHorizontal: 8, paddingVertical: 4 },
  gradeText: { fontSize: 9, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.6 },
  selectedScore: { alignItems: 'flex-end' },
  selectedScoreValue: { ...typographyTokens.sectionTitle, fontSize: 27 },
  selectedScoreLabel: { fontSize: 10, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.7 },
  selectedPoints: { fontSize: 10, marginTop: 6 },
  contentCard: { borderRadius: 22, borderWidth: 1, padding: 18, marginBottom: 22 },
  standardGrid: { flexDirection: 'row', gap: 8, marginTop: 15 },
  standardCell: { flex: 1, minHeight: 92, borderRadius: 14, padding: 10 },
  standardLabel: { fontSize: 9, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.45 },
  standardValue: { ...typographyTokens.sectionTitle, fontSize: 20, marginTop: 7 },
  standardNote: { fontSize: 9, lineHeight: 13, marginTop: 3 },
  phalaRow: { flexDirection: 'row', borderTopWidth: StyleSheet.hairlineWidth, marginTop: 15, paddingTop: 15 },
  phalaCell: { flex: 1 },
  phalaDivider: { width: StyleSheet.hairlineWidth, marginHorizontal: 14 },
  phalaValue: { ...typographyTokens.sectionTitle, fontSize: 22, marginTop: 5 },
  componentList: { marginTop: 11 },
  componentRow: { paddingVertical: 12 },
  componentHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 8 },
  componentName: { fontSize: 13, fontWeight: '600', flex: 1 },
  componentValue: { fontSize: 13, fontWeight: '800' },
  componentTrack: { height: 6, borderRadius: 3, overflow: 'hidden' },
  componentFill: { height: '100%', borderRadius: 3 },
  breakdownSection: { marginBottom: 20 },
  sectionHeading: { marginBottom: 13 },
  sectionEyebrow: { ...typographyTokens.eyebrow, fontSize: 9, marginBottom: 5 },
  sectionTitle: { ...typographyTokens.sectionTitle, fontSize: 24 },
  sectionIntro: { fontSize: 13, lineHeight: 19, marginTop: 6 },
  breakdownCard: { borderRadius: 20, borderWidth: 1, marginBottom: 10, overflow: 'hidden' },
  breakdownHeader: { minHeight: 70, paddingHorizontal: 14, paddingVertical: 11, flexDirection: 'row', alignItems: 'center', gap: 12 },
  breakdownIcon: { width: 42, height: 42, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  breakdownCopy: { flex: 1 },
  breakdownTitle: { ...typographyTokens.sectionTitle, fontSize: 17 },
  breakdownCount: { fontSize: 11, marginTop: 3 },
  breakdownRows: { borderTopWidth: StyleSheet.hairlineWidth, paddingHorizontal: 16 },
  detailRow: { minHeight: 46, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  detailName: { flex: 1, fontSize: 12 },
  detailValue: { fontSize: 13, fontWeight: '800' },
  methodCard: { borderRadius: 18, borderWidth: 1, padding: 14, flexDirection: 'row', gap: 11, marginBottom: 19 },
  methodIcon: { width: 38, height: 38, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  methodCopy: { flex: 1 },
  methodTitle: { ...typographyTokens.sectionTitle, fontSize: 16, marginBottom: 4 },
  methodBody: { fontSize: 11, lineHeight: 17 },
  methodMeta: { fontSize: 9, lineHeight: 14, marginTop: 6 },
  houseSection: { marginTop: 3 },
  bhavaClassicalCard: { borderRadius: 18, borderWidth: 1, padding: 14, marginBottom: 10 },
  bhavaClassicalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12 },
  bhavaLord: { ...typographyTokens.sectionTitle, fontSize: 16, marginTop: 5 },
  bhavaTotal: { alignItems: 'flex-end' },
  bhavaTotalValue: { ...typographyTokens.sectionTitle, fontSize: 23 },
  bhavaTotalUnit: { fontSize: 10, marginTop: 2 },
  bhavaComponents: { flexDirection: 'row', flexWrap: 'wrap', borderTopWidth: StyleSheet.hairlineWidth, marginTop: 12, paddingTop: 10 },
  bhavaComponent: { width: '33.33%', marginBottom: 8 },
  bhavaComponentLabel: { fontSize: 9, lineHeight: 13 },
  bhavaComponentValue: { fontSize: 12, fontWeight: '800', marginTop: 2 },
  bhavGrid: { flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: -5 },
  bhavCell: { width: '47.2%', minHeight: 102, marginHorizontal: '1.4%', marginBottom: 10, padding: 12, borderRadius: 17, borderWidth: 1 },
  houseHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  bhavHouseNum: { ...typographyTokens.eyebrow, fontSize: 10 },
  bhavGradeBadge: { minWidth: 28, borderRadius: 999, paddingHorizontal: 7, paddingVertical: 4, alignItems: 'center' },
  bhavGradeText: { fontSize: 9, fontWeight: '800' },
  bhavHouseLabel: { ...typographyTokens.sectionTitle, fontSize: 16 },
  bhavStrength: { fontSize: 11, marginTop: 4 },
});

export default ShadbalaScreen;
