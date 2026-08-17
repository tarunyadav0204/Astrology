import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import Svg, { Circle, Line } from 'react-native-svg';
import { useTheme } from '../../context/ThemeContext';
import { DISPLAY_FONT_FAMILY } from '../../theme/tokens';
import { useTranslation } from 'react-i18next';
import { buildKpHomeRecommendations } from '../../utils/kpHomeRecommendations';

const LANGUAGE_LOCALES = { english: 'en-IN', hindi: 'hi-IN', es: 'es-ES', french: 'fr-FR', german: 'de-DE', russian: 'ru-RU', chinese: 'zh-CN', mandarin: 'zh-CN', tamil: 'ta-IN', telugu: 'te-IN', gujarati: 'gu-IN', marathi: 'mr-IN' };
const formatToday = (language) => new Intl.DateTimeFormat(LANGUAGE_LOCALES[language] || 'en-IN', {
  weekday: 'long', month: 'short', day: 'numeric',
}).format(new Date());

function OrbitMark({ angle, radius, color, size = 7 }) {
  const rad = (angle * Math.PI) / 180;
  const x = 76 + Math.cos(rad) * radius;
  const y = 76 + Math.sin(rad) * radius;
  return <Circle cx={x} cy={y} r={size} fill={color} />;
}

function OrbitMotif({ colors }) {
  return (
    <View style={styles.orbitMotif} accessibilityElementsHidden>
      <Svg width="152" height="152" viewBox="0 0 152 152">
        <Circle cx="76" cy="76" r="68" fill="none" stroke={colors.cosmicLine} strokeWidth="1" />
        <Circle cx="76" cy="76" r="50" fill="none" stroke={colors.cosmicLine} strokeWidth="1" />
        <Circle cx="76" cy="76" r="31" fill={colors.cosmicGlow} stroke={colors.accent} strokeWidth="1" />
        {[0, 30, 60, 90, 120, 150].map((angle) => {
          const rad = (angle * Math.PI) / 180;
          const x1 = 76 + Math.cos(rad) * 50;
          const y1 = 76 + Math.sin(rad) * 50;
          const x2 = 76 - Math.cos(rad) * 50;
          const y2 = 76 - Math.sin(rad) * 50;
          return <Line key={angle} x1={x1} y1={y1} x2={x2} y2={y2} stroke={colors.cosmicLine} strokeWidth="0.7" />;
        })}
        <OrbitMark angle={-22} radius={58} color={colors.accent} size={6} />
        <OrbitMark angle={42} radius={43} color={colors.primary} size={5} />
        <OrbitMark angle={116} radius={58} color={colors.textInverseMuted} size={4} />
        <OrbitMark angle={202} radius={45} color={colors.secondary} size={5} />
        <OrbitMark angle={276} radius={58} color={colors.accentSoft} size={4} />
      </Svg>
    </View>
  );
}

function Metric({ label, value, onPress, colors, icon, calculating }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={!onPress}
      activeOpacity={0.78}
      style={[styles.metric, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}
    >
      <View style={[styles.metricIcon, { backgroundColor: colors.accentSoft }]}>
        <Ionicons name={icon} size={16} color={colors.onAccent} />
      </View>
      <View style={styles.metricCopy}>
        <Text style={[styles.metricLabel, { color: colors.textTertiary }]}>{label}</Text>
        <Text style={[styles.metricValue, { color: colors.text }]} numberOfLines={1}>{value || calculating}</Text>
      </View>
      {onPress ? <Ionicons name="chevron-forward" size={15} color={colors.textTertiary} /> : null}
    </TouchableOpacity>
  );
}

function Recommendation({ number, title, body, onPress, colors }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.82}
      style={[styles.recommendation, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}
    >
      <Text style={[styles.recommendationNumber, { color: colors.primary }]}>{number}</Text>
      <View style={styles.recommendationCopy}>
        <Text style={[styles.recommendationTitle, { color: colors.text }]}>{title}</Text>
        <Text style={[styles.recommendationBody, { color: colors.textSecondary }]} numberOfLines={2}>{body}</Text>
      </View>
      <View style={[styles.arrow, { borderColor: colors.cardBorder }]}>
        <Ionicons name="arrow-forward" size={16} color={colors.text} />
      </View>
    </TouchableOpacity>
  );
}

export default function PremiumTodayOverview({
  name,
  hasChart,
  ascendant,
  moon,
  sun,
  mahadasha,
  nakshatra,
  panchangWindow,
  onSelectNative,
  onCreateChart,
  onAsk,
  onOpenCharts,
  onOpenDasha,
  onOpenNakshatra,
  onOpenPanchang,
  onOpenCareer,
  onOpenKarma,
  kpTodayData,
  onOpenRecommendedAnalysis,
  onAskRecommended,
  onOpenExplore,
  todayPredictions,
  onOpenAscendant,
  onOpenMoon,
  onOpenSun,
}) {
  const { colors, typography } = useTheme();
  const { t, i18n } = useTranslation();
  const displayName = name || t('premiumUi.home.explorer');
  const dailyRecommendations = React.useMemo(
    () => buildKpHomeRecommendations(kpTodayData, t),
    [kpTodayData, t],
  );

  return (
    <View style={styles.container}>
      <View style={styles.identityRow}>
        <View style={styles.identityCopy}>
          <Text style={[styles.eyebrow, typography.eyebrow, { color: colors.textTertiary }]}>{t('premiumUi.home.yourSky')} · {formatToday(i18n.resolvedLanguage || i18n.language)}</Text>
          <Text style={[styles.identity, { color: colors.text }]} numberOfLines={1}>{t('premiumUi.home.hello', { name: displayName })}</Text>
        </View>
        <TouchableOpacity
          onPress={hasChart ? onSelectNative : onCreateChart}
          activeOpacity={0.8}
          style={[styles.profileButton, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}
        >
          <View style={[styles.avatar, { backgroundColor: colors.accentSoft }]}>
            <Text style={[styles.avatarText, { color: colors.onAccent }]}>{displayName.slice(0, 1).toUpperCase()}</Text>
          </View>
          <Text
            style={[styles.profileButtonText, { color: colors.text }]}
            numberOfLines={1}
            adjustsFontSizeToFit
            minimumFontScale={0.8}
          >
            {hasChart ? t('premiumUi.home.changeChart') : t('premiumUi.home.addChart')}
          </Text>
          <Ionicons name="chevron-down" size={14} color={colors.textTertiary} />
        </TouchableOpacity>
      </View>

      <View style={[styles.hero, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
        <View style={styles.heroCopy}>
          <Text style={[styles.heroEyebrow, typography.eyebrow, { color: colors.accent }]}>{t('premiumUi.home.taraGuide')}</Text>
          <Text style={[styles.heroTitle, typography.title, { color: colors.textInverse }]}>{t('premiumUi.home.meetTara')}{`\n`}{t('premiumUi.home.readLife')}</Text>
          <Text style={[styles.heroBody, { color: colors.textInverseMuted }]}> 
            {hasChart
              ? t('premiumUi.home.heroWithChart')
              : t('premiumUi.home.heroNoChart')}
          </Text>
        </View>
        <OrbitMotif colors={colors} />
        <View style={styles.heroActions}>
          <TouchableOpacity onPress={onAsk} activeOpacity={0.86} style={[styles.primaryAction, { backgroundColor: colors.primary }]}>
            <Ionicons name="sparkles-outline" size={17} color={colors.onPrimary} />
            <Text style={[styles.primaryActionText, { color: colors.onPrimary }]}>{t('premiumUi.home.askTara')}</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={hasChart ? onOpenCharts : onCreateChart} activeOpacity={0.82} style={[styles.secondaryAction, { borderColor: colors.cosmicLine }]}>
            <Text style={[styles.secondaryActionText, { color: colors.textInverse }]}>{hasChart ? t('premiumUi.home.openChart') : t('premiumUi.home.createChart')}</Text>
            <Ionicons name="arrow-forward" size={16} color={colors.textInverse} />
          </TouchableOpacity>
        </View>
      </View>

      {hasChart ? (
        <View style={[styles.bigThree, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
          {[
            [t('premiumUi.home.ascendant'), ascendant, onOpenAscendant],
            [t('premiumUi.home.moon'), moon, onOpenMoon],
            [t('premiumUi.home.sun'), sun, onOpenSun],
          ].map(([label, value, onPress], index) => (
            <React.Fragment key={label}>
              {index ? <View style={[styles.bigThreeDivider, { backgroundColor: colors.cardBorder }]} /> : null}
              <TouchableOpacity
                style={styles.bigThreeItem}
                onPress={onPress}
                activeOpacity={0.7}
                accessibilityRole="button"
                accessibilityLabel={t('premiumUi.home.learnAbout', { label })}
              >
                <View style={styles.bigThreeLabelRow}>
                  <Text style={[styles.bigThreeLabel, { color: colors.textTertiary }]}>{label}</Text>
                  <Ionicons name="information-circle-outline" size={11} color={colors.textTertiary} />
                </View>
                <Text style={[styles.bigThreeValue, { color: colors.text }]} numberOfLines={1}>{value || '—'}</Text>
              </TouchableOpacity>
            </React.Fragment>
          ))}
        </View>
      ) : null}

      {todayPredictions ? (
        <View style={styles.predictionSection}>
          <View style={styles.sectionHeader}>
            <View>
              <Text style={[styles.sectionEyebrow, typography.eyebrow, { color: colors.primary }]}>{t('premiumUi.home.kpLive')}</Text>
              <Text style={[styles.sectionTitle, typography.sectionTitle, { color: colors.text }]}>{t('premiumUi.home.unfoldToday')}</Text>
            </View>
          </View>
          {todayPredictions}
        </View>
      ) : null}

      <View style={styles.sectionHeader}>
        <View>
          <Text style={[styles.sectionEyebrow, typography.eyebrow, { color: colors.primary }]}>{t('premiumUi.home.rightNow')}</Text>
          <Text style={[styles.sectionTitle, typography.sectionTitle, { color: colors.text }]}>{t('premiumUi.home.timingGlance')}</Text>
        </View>
      </View>
      <View style={styles.metrics}>
        <Metric label={t('premiumUi.home.activePeriod')} value={mahadasha ? t('premiumUi.home.mahadasha', { name: mahadasha }) : null} onPress={hasChart ? onOpenDasha : onCreateChart} colors={colors} icon="time-outline" calculating={t('premiumUi.home.calculating')} />
        <Metric label={t('premiumUi.home.todaysNakshatra')} value={nakshatra} onPress={onOpenNakshatra} colors={colors} icon="star-outline" calculating={t('premiumUi.home.calculating')} />
        <Metric label={t('premiumUi.home.dayWindow')} value={panchangWindow || t('premiumUi.home.openPanchang')} onPress={onOpenPanchang} colors={colors} icon="sunny-outline" calculating={t('premiumUi.home.calculating')} />
      </View>

      <View style={styles.sectionHeader}>
        <View>
          <Text style={[styles.sectionEyebrow, typography.eyebrow, { color: colors.primary }]}>{t('premiumUi.homeRecommendations.eyebrow')}</Text>
          <Text style={[styles.sectionTitle, typography.sectionTitle, { color: colors.text }]}>{t('premiumUi.homeRecommendations.title')}</Text>
        </View>
      </View>
      <View style={styles.recommendations}>
        {dailyRecommendations.length ? [...dailyRecommendations, ...(!dailyRecommendations[2] ? [{
          id: 'daily-rhythm-fallback',
          kind: 'panchang',
          title: t('premiumUi.homeRecommendations.fallbackPanchangTitle'),
          body: t('premiumUi.homeRecommendations.fallbackPanchangBody'),
        }] : [])].slice(0, 3).map((item, index) => (
          <Recommendation
            key={item.id}
            number={String(index + 1).padStart(2, '0')}
            title={item.title}
            body={item.body}
            onPress={() => {
              if (item.kind === 'ask') {
                onAskRecommended?.(item.question, item.area, item.houses);
              } else if (item.kind === 'panchang') {
                onOpenPanchang?.();
              } else {
                onOpenRecommendedAnalysis?.(item.analysisType);
              }
            }}
            colors={colors}
          />
        )) : (
          <>
            <Recommendation number="01" title={t('premiumUi.homeRecommendations.fallbackAskTitle')} body={t('premiumUi.homeRecommendations.fallbackAskBody')} onPress={onAsk} colors={colors} />
            <Recommendation number="02" title={t('premiumUi.homeRecommendations.fallbackPanchangTitle')} body={t('premiumUi.homeRecommendations.fallbackPanchangBody')} onPress={onOpenPanchang} colors={colors} />
            <Recommendation number="03" title={t('premiumUi.home.karmaPatterns')} body={t('premiumUi.home.karmaBody')} onPress={onOpenKarma} colors={colors} />
          </>
        )}
      </View>

      <TouchableOpacity onPress={onOpenExplore} activeOpacity={0.82} style={[styles.exploreButton, { borderColor: colors.borderStrong }]}>
        <View>
          <Text style={[styles.exploreTitle, { color: colors.text }]}>{t('premiumUi.home.exploreAll')}</Text>
          <Text style={[styles.exploreSub, { color: colors.textSecondary }]}>{t('premiumUi.home.exploreSub')}</Text>
        </View>
        <Ionicons name="grid-outline" size={20} color={colors.primary} />
      </TouchableOpacity>
    </View>
  );
}

const FEATURE_ICONS = {
  partnership: 'people-outline', kundliMatch: 'heart-outline', mundane: 'earth-outline', events: 'calendar-outline',
  karma: 'infinite-outline', career: 'briefcase-outline', wealth: 'wallet-outline', marriage: 'heart-circle-outline',
  health: 'pulse-outline', education: 'book-outline', progeny: 'people-circle-outline', yearly: 'calendar-number-outline',
  muhurat: 'time-outline', trading: 'trending-up-outline', financial: 'stats-chart-outline', childbirth: 'flower-outline',
};

function CatalogueGroup({ eyebrow, title, items, onSelect, colors, typography, t }) {
  if (!items?.length) return null;
  return (
    <View style={styles.catalogueSection}>
      <Text style={[typography.eyebrow, { color: colors.primary, marginBottom: 6 }]}>{eyebrow}</Text>
      <Text style={[typography.sectionTitle, styles.catalogueTitle, { color: colors.text }]}>{title}</Text>
      <View style={[styles.catalogueSurface, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}> 
        {items.map((item, index) => (
          <React.Fragment key={item.id}>
            {index ? <View style={[styles.catalogueDivider, { backgroundColor: colors.cardBorder }]} /> : null}
            <TouchableOpacity onPress={() => onSelect(item)} activeOpacity={0.78} style={styles.catalogueRow}>
              <View style={[styles.catalogueIcon, { backgroundColor: colors.accentSoft }]}> 
                <Ionicons name={FEATURE_ICONS[item.id] || 'sparkles-outline'} size={17} color={colors.onAccent} />
              </View>
              <View style={styles.catalogueCopy}>
                <Text style={[styles.catalogueRowTitle, { color: colors.text }]}>{item.title}</Text>
                <Text style={[styles.catalogueRowBody, { color: colors.textSecondary }]} numberOfLines={1}>{item.description}</Text>
              </View>
              {Number(item.cost) > 0 ? (
                <Text style={[styles.catalogueCost, { color: colors.textTertiary }]}>{t('premiumUi.home.creditsShort', { count: item.cost })}</Text>
              ) : (
                <Text style={[styles.catalogueCost, { color: colors.success }]}>{t('premiumUi.home.free')}</Text>
              )}
              <Ionicons name="chevron-forward" size={16} color={colors.textTertiary} />
            </TouchableOpacity>
          </React.Fragment>
        ))}
      </View>
    </View>
  );
}

export function PremiumExploreIntro({
  onOpenCharts,
  onOpenReports,
  onOpenPanchang,
  onOpenMuhurat,
  onOpenYearly,
  onOpenMonthly,
  eventsCost = 100,
  paths = [],
  analyses = [],
  onSelectPath,
  onSelectAnalysis,
}) {
  const { colors, typography } = useTheme();
  const { t } = useTranslation();
  const shortcuts = [
    ['grid-outline', t('premiumUi.home.chartsDashas'), t('premiumUi.home.technicalWorkbench'), onOpenCharts],
    ['document-text-outline', t('premiumUi.home.premiumReports'), t('premiumUi.home.longReadings'), onOpenReports],
    ['sunny-outline', t('premiumUi.home.panchang'), t('premiumUi.home.dayRhythm'), onOpenPanchang],
    ['time-outline', t('premiumUi.home.muhurat'), t('premiumUi.home.supportiveTiming'), onOpenMuhurat],
  ];
  const personalAnalyses = analyses.filter((item) => !['yearly', 'muhurat', 'trading', 'financial', 'childbirth'].includes(item.id));
  const timingAnalyses = analyses.filter((item) => ['muhurat', 'trading', 'financial', 'childbirth'].includes(item.id));
  const guidedPaths = paths.filter((item) => item.action !== 'events');
  return (
    <View style={styles.exploreIntroWrap}>
      <View style={[styles.exploreHero, { backgroundColor: colors.surfaceInverse, borderColor: colors.cosmicLine }]}>
        <View pointerEvents="none" style={styles.exploreHeroLinework} accessibilityElementsHidden>
          <View style={[styles.exploreHeroOrbit, styles.exploreHeroOrbitLarge, { borderColor: colors.onSurfaceInverseMuted || colors.cosmicLine }]} />
          <View style={[styles.exploreHeroOrbit, styles.exploreHeroOrbitSmall, { borderColor: colors.onSurfaceInverseMuted || colors.cosmicLine }]} />
          <View style={[styles.exploreHeroMeridian, { backgroundColor: colors.onSurfaceInverseMuted || colors.cosmicLine }]} />
          <View style={[styles.exploreHeroBaseline, { backgroundColor: colors.onSurfaceInverseMuted || colors.cosmicLine }]} />
        </View>
        <View style={styles.exploreHeroEyebrowRow}>
          <View style={[styles.exploreHeroEyebrowRule, { backgroundColor: colors.onSurfaceInverseMuted || colors.onSurfaceInverse }]} />
          <Text style={[typography.eyebrow, { color: colors.onSurfaceInverseMuted || colors.onSurfaceInverse }]}>
            {t('premiumUi.home.vedicStudio')}
          </Text>
        </View>
        <Text style={[typography.title, styles.exploreHeroTitle, { color: colors.onSurfaceInverse }]}>{t('premiumUi.home.exploreWith')}{`\n`}{t('premiumUi.home.purpose')}</Text>
        <Text style={[styles.exploreHeroBody, { color: colors.onSurfaceInverseMuted }]}>{t('premiumUi.home.studioBody')}</Text>
      </View>
      <View style={[styles.timingSpotlight, { backgroundColor: colors.surfaceInverse, borderColor: colors.cosmicLine }]}>
        <View pointerEvents="none" style={styles.timingSpotlightGlow} />
        <View style={styles.timingSpotlightHeader}>
          <View style={styles.timingSpotlightHeading}>
            <Text style={[typography.eyebrow, { color: colors.accent }]}>
              {t('premiumUi.home.signatureTiming', 'SIGNATURE TIMING')}
            </Text>
            <Text style={[typography.sectionTitle, styles.timingSpotlightTitle, { color: colors.onSurfaceInverse }]}>
              {t('premiumUi.home.yourTimeAhead', 'Your time ahead')}
            </Text>
          </View>
          <View style={[styles.timingCostPill, { borderColor: colors.cosmicLine, backgroundColor: colors.cosmicGlow }]}>
            <Ionicons name="diamond-outline" size={12} color={colors.accent} />
            <Text style={[styles.timingCostText, { color: colors.onSurfaceInverse }]}>
              {t('premiumUi.home.creditsShort', { count: eventsCost })}
            </Text>
          </View>
        </View>
        <Text style={[styles.timingSpotlightBody, { color: colors.onSurfaceInverseMuted }]}>
          {t(
            'premiumUi.home.timingSpotlightBody',
            'Personal timing from dashas, transits, Parashari, Nadi, Jaimini and KP.'
          )}
        </Text>
        <View style={styles.timingChoices}>
          <TouchableOpacity
            onPress={onOpenYearly}
            activeOpacity={0.82}
            style={[styles.timingChoice, { backgroundColor: colors.cosmicGlow, borderColor: colors.cosmicLine }]}
          >
            <View style={[styles.timingChoiceIcon, { backgroundColor: colors.accentSoft }]}>
              <Ionicons name="calendar-outline" size={20} color={colors.onAccent} />
            </View>
            <Text style={[styles.timingChoiceTitle, { color: colors.onSurfaceInverse }]}>
              {t('premiumUi.home.yearlyTimeline', 'Yearly timeline')}
            </Text>
            <Text style={[styles.timingChoiceBody, { color: colors.onSurfaceInverseMuted }]} numberOfLines={2}>
              {t('premiumUi.home.yearlyTimelineBody', '12 monthly chapters and major turning points')}
            </Text>
            <View style={styles.timingChoiceCta}>
              <Text style={[styles.timingChoiceCtaText, { color: colors.accent }]}>
                {t('premiumUi.home.exploreYear', 'Explore my year')}
              </Text>
              <Ionicons name="arrow-forward" size={14} color={colors.accent} />
            </View>
          </TouchableOpacity>
          <TouchableOpacity
            onPress={onOpenMonthly}
            activeOpacity={0.82}
            style={[styles.timingChoice, { backgroundColor: colors.cosmicGlow, borderColor: colors.cosmicLine }]}
          >
            <View style={[styles.timingChoiceIcon, { backgroundColor: colors.accentSoft }]}>
              <Ionicons name="moon-outline" size={20} color={colors.onAccent} />
            </View>
            <Text style={[styles.timingChoiceTitle, { color: colors.onSurfaceInverse }]}>
              {t('premiumUi.home.monthlyDeepDive', 'Monthly deep dive')}
            </Text>
            <Text style={[styles.timingChoiceBody, { color: colors.onSurfaceInverseMuted }]} numberOfLines={2}>
              {t('premiumUi.home.monthlyDeepDiveBody', 'Detailed triggers and scenarios for one month')}
            </Text>
            <View style={styles.timingChoiceCta}>
              <Text style={[styles.timingChoiceCtaText, { color: colors.accent }]}>
                {t('premiumUi.home.chooseMonth', 'Choose a month')}
              </Text>
              <Ionicons name="arrow-forward" size={14} color={colors.accent} />
            </View>
          </TouchableOpacity>
        </View>
      </View>
      <CatalogueGroup eyebrow={t('premiumUi.home.waysBegin')} title={t('premiumUi.home.guidedExperiences')} items={guidedPaths} onSelect={onSelectPath} colors={colors} typography={typography} t={t} />
      <CatalogueGroup eyebrow={t('premiumUi.home.completeChart')} title={t('premiumUi.home.personalReadings')} items={personalAnalyses} onSelect={onSelectAnalysis} colors={colors} typography={typography} t={t} />
      <View style={[styles.studioDirectory, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
        {shortcuts.map(([icon, title, body, onPress]) => (
          <TouchableOpacity key={title} onPress={onPress} activeOpacity={0.82} style={[styles.shortcut, { borderBottomColor: colors.cardBorder }]}>
            <View style={[styles.shortcutIcon, { backgroundColor: colors.accentSoft }]}>
              <Ionicons name={icon} size={17} color={colors.onAccent} />
            </View>
            <View style={styles.shortcutCopy}>
              <Text style={[styles.shortcutTitle, { color: colors.text }]}>{title}</Text>
              <Text style={[styles.shortcutBody, { color: colors.textSecondary }]} numberOfLines={1}>{body}</Text>
            </View>
            <Ionicons name="arrow-forward" size={16} color={colors.textTertiary} />
          </TouchableOpacity>
        ))}
      </View>
      <CatalogueGroup eyebrow={t('premiumUi.home.planNext')} title={t('premiumUi.home.timingDecisions')} items={timingAnalyses} onSelect={onSelectAnalysis} colors={colors} typography={typography} t={t} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 18 },
  identityRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  identityCopy: { flex: 1, minWidth: 0 },
  eyebrow: { fontSize: 9, marginBottom: 6 },
  identity: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 23, lineHeight: 28 },
  profileButton: { width: 148, flexShrink: 0, flexDirection: 'row', alignItems: 'center', gap: 7, padding: 6, paddingRight: 10, borderWidth: 1, borderRadius: 999 },
  avatar: { width: 30, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 15, fontWeight: '700' },
  profileButtonText: { maxWidth: 78, fontSize: 11, fontWeight: '800' },
  hero: { minHeight: 350, borderWidth: 1, borderRadius: 30, padding: 24, overflow: 'hidden' },
  heroCopy: { maxWidth: '69%', zIndex: 2 },
  heroEyebrow: { marginBottom: 14 },
  heroTitle: { fontSize: 40, lineHeight: 42, marginBottom: 14 },
  heroBody: { fontSize: 13, lineHeight: 20, fontWeight: '500' },
  orbitMotif: { position: 'absolute', right: -18, top: 44, opacity: 0.58 },
  heroActions: { marginTop: 22, flexDirection: 'row', gap: 10, zIndex: 2 },
  primaryAction: { height: 48, paddingHorizontal: 18, borderRadius: 999, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, flex: 1 },
  primaryActionText: { fontSize: 14, fontWeight: '900' },
  secondaryAction: { height: 48, paddingHorizontal: 16, borderRadius: 999, borderWidth: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  secondaryActionText: { fontSize: 13, fontWeight: '800' },
  bigThree: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderRadius: 18, paddingVertical: 14 },
  bigThreeItem: { flex: 1, alignItems: 'center', paddingHorizontal: 5 },
  bigThreeDivider: { width: 1, height: 29 },
  bigThreeLabelRow: { flexDirection: 'row', alignItems: 'center', gap: 3, marginBottom: 4 },
  bigThreeLabel: { fontSize: 8, fontWeight: '800', letterSpacing: 0.8 },
  bigThreeValue: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 15 },
  predictionSection: { gap: 12 },
  sectionHeader: { marginTop: 12, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end' },
  sectionEyebrow: { marginBottom: 6 },
  sectionTitle: { fontSize: 24, lineHeight: 29 },
  metrics: { gap: 8 },
  metric: { minHeight: 70, borderRadius: 18, borderWidth: 1, padding: 12, flexDirection: 'row', alignItems: 'center' },
  metricIcon: { width: 38, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  metricCopy: { flex: 1 },
  metricLabel: { fontSize: 9, fontWeight: '800', letterSpacing: 1.1, textTransform: 'uppercase', marginBottom: 4 },
  metricValue: { fontSize: 14, fontWeight: '800' },
  recommendations: { gap: 8 },
  recommendation: { minHeight: 96, borderWidth: 1, borderRadius: 18, padding: 14, flexDirection: 'row', alignItems: 'center' },
  recommendationNumber: { width: 30, alignSelf: 'flex-start', fontSize: 10, fontWeight: '900', letterSpacing: 0.8 },
  recommendationCopy: { flex: 1, paddingRight: 10 },
  recommendationTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 19, marginBottom: 5 },
  recommendationBody: { fontSize: 12, lineHeight: 17, fontWeight: '500' },
  arrow: { width: 34, height: 34, borderRadius: 17, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  exploreButton: { minHeight: 76, borderWidth: 1, borderRadius: 18, padding: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  exploreTitle: { fontSize: 14, fontWeight: '900', marginBottom: 4 },
  exploreSub: { fontSize: 11, lineHeight: 15, fontWeight: '500', maxWidth: 280 },
  exploreIntroWrap: { gap: 22 },
  exploreHero: { minHeight: 260, marginHorizontal: -20, marginTop: -10, borderBottomLeftRadius: 30, borderBottomRightRadius: 30, borderWidth: 0, paddingHorizontal: 36, paddingVertical: 34, justifyContent: 'center', overflow: 'hidden' },
  exploreHeroLinework: { ...StyleSheet.absoluteFillObject, opacity: 0.26 },
  exploreHeroOrbit: { position: 'absolute', borderWidth: 1 },
  exploreHeroOrbitLarge: { width: 196, height: 196, borderRadius: 98, right: -62, top: -90 },
  exploreHeroOrbitSmall: { width: 124, height: 124, borderRadius: 62, right: -18, top: -48 },
  exploreHeroMeridian: { position: 'absolute', width: StyleSheet.hairlineWidth, height: 174, right: 54, top: -24, transform: [{ rotate: '28deg' }] },
  exploreHeroBaseline: { position: 'absolute', height: StyleSheet.hairlineWidth, left: 36, right: 36, bottom: 20 },
  exploreHeroEyebrowRow: { flexDirection: 'row', alignItems: 'center', gap: 11, marginBottom: 12 },
  exploreHeroEyebrowRule: { width: 24, height: StyleSheet.hairlineWidth },
  exploreHeroTitle: { fontSize: 38, lineHeight: 41, marginBottom: 14 },
  exploreHeroBody: { fontSize: 13, lineHeight: 20, maxWidth: 330, fontWeight: '500' },
  timingSpotlight: { borderWidth: 1, borderRadius: 26, padding: 18, overflow: 'hidden' },
  timingSpotlightGlow: { position: 'absolute', width: 180, height: 180, borderRadius: 90, right: -75, top: -105, backgroundColor: 'rgba(245, 158, 11, 0.12)' },
  timingSpotlightHeader: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 },
  timingSpotlightHeading: { flex: 1, minWidth: 0 },
  timingSpotlightTitle: { fontSize: 28, lineHeight: 32, marginTop: 5 },
  timingCostPill: { flexDirection: 'row', alignItems: 'center', gap: 5, borderWidth: 1, borderRadius: 999, paddingHorizontal: 9, paddingVertical: 6 },
  timingCostText: { fontSize: 10, fontWeight: '900' },
  timingSpotlightBody: { fontSize: 12, lineHeight: 18, marginTop: 8, marginBottom: 16, maxWidth: 320 },
  timingChoices: { flexDirection: 'row', gap: 10 },
  timingChoice: { flex: 1, minWidth: 0, minHeight: 176, borderWidth: 1, borderRadius: 18, padding: 13 },
  timingChoiceIcon: { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  timingChoiceTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 18, lineHeight: 21, marginBottom: 6 },
  timingChoiceBody: { fontSize: 10, lineHeight: 15, fontWeight: '500', flexGrow: 1 },
  timingChoiceCta: { flexDirection: 'row', alignItems: 'center', gap: 5, marginTop: 12 },
  timingChoiceCtaText: { fontSize: 10, fontWeight: '900', textTransform: 'uppercase', letterSpacing: 0.4 },
  studioDirectory: { borderWidth: 1, borderRadius: 22, overflow: 'hidden' },
  shortcut: { minHeight: 72, paddingHorizontal: 14, flexDirection: 'row', alignItems: 'center', borderBottomWidth: StyleSheet.hairlineWidth },
  shortcutIcon: { width: 38, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  shortcutCopy: { flex: 1 },
  shortcutTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 17, marginBottom: 3 },
  shortcutBody: { fontSize: 11, lineHeight: 15, fontWeight: '500' },
  catalogueSection: { gap: 0 },
  catalogueTitle: { fontSize: 25, lineHeight: 30, marginBottom: 12 },
  catalogueSurface: { borderWidth: 1, borderRadius: 22, overflow: 'hidden' },
  catalogueRow: { minHeight: 76, paddingHorizontal: 14, flexDirection: 'row', alignItems: 'center' },
  catalogueDivider: { height: StyleSheet.hairlineWidth, marginLeft: 64 },
  catalogueIcon: { width: 38, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  catalogueCopy: { flex: 1, minWidth: 0, paddingRight: 8 },
  catalogueRowTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 17, marginBottom: 3 },
  catalogueRowBody: { fontSize: 11, lineHeight: 15, fontWeight: '500' },
  catalogueCost: { fontSize: 10, fontWeight: '800', marginRight: 7, textTransform: 'uppercase' },
});
