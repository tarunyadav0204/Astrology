import React from 'react';
import { AccessibilityInfo, Animated, Easing, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Circle, Line } from 'react-native-svg';
import { useTheme } from '../../context/ThemeContext';
import { DISPLAY_FONT_FAMILY } from '../../theme/tokens';
import { useTranslation } from 'react-i18next';
import { buildKpHomeRecommendations } from '../../utils/kpHomeRecommendations';
import ComingUpChartCard from './ComingUpChartCard';

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

function OrbitMotif({ colors, subdued = false }) {
  return (
    <View style={[styles.orbitMotif, subdued && styles.orbitMotifSubdued]} accessibilityElementsHidden>
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

function VoiceMark({ colors }) {
  return (
    <View style={[styles.voiceMark, { backgroundColor: colors.accentSoft }]} accessibilityElementsHidden>
      <Ionicons name="mic" size={24} color={colors.onAccent} />
      <View style={styles.voiceMarkWave}>
        {[7, 13, 19, 13, 7].map((height, index) => (
          <View
            key={`${height}-${index}`}
            style={[styles.voiceMarkBar, { height, backgroundColor: colors.onAccent }]}
          />
        ))}
      </View>
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
  firstQuestionFree = false,
  onTalkToTara,
  speechPerMinuteCost = 5,
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
  onOpenPrashna,
  todayPredictions,
  onOpenAscendant,
  onOpenMoon,
  onOpenSun,
  nextPeakData,
  nextPeakLoading,
  localizePlanet,
  onNextPeakAsk,
  onNextPeakTimeline,
  onNextPeakOpenDetail,
}) {
  const { colors, typography } = useTheme();
  const { t, i18n } = useTranslation();
  const displayName = name || t('premiumUi.home.explorer');
  const taraCtaEntrance = React.useRef(new Animated.Value(0)).current;
  const taraCtaShimmer = React.useRef(new Animated.Value(0)).current;
  const taraShimmerAnimation = React.useRef(null);
  const dailyRecommendations = React.useMemo(
    () => buildKpHomeRecommendations(kpTodayData, t),
    [kpTodayData, t],
  );

  React.useEffect(() => {
    let isMounted = true;

    AccessibilityInfo.isReduceMotionEnabled().then((reduceMotionEnabled) => {
      if (!isMounted) return;
      if (reduceMotionEnabled) {
        taraCtaEntrance.setValue(1);
        return;
      }

      Animated.spring(taraCtaEntrance, {
        toValue: 1,
        delay: 260,
        damping: 15,
        stiffness: 145,
        mass: 0.8,
        useNativeDriver: true,
      }).start();

      taraCtaShimmer.setValue(0);
      taraShimmerAnimation.current = Animated.loop(
        Animated.sequence([
          Animated.timing(taraCtaShimmer, {
            toValue: 1,
            duration: 4500,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(taraCtaShimmer, {
            toValue: 0,
            duration: 4500,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ]),
      );
      taraShimmerAnimation.current.start();
    });

    return () => {
      isMounted = false;
      taraCtaEntrance.stopAnimation();
      taraShimmerAnimation.current?.stop();
      taraCtaShimmer.setValue(0);
    };
  }, [taraCtaEntrance, taraCtaShimmer]);

  const taraEntranceScale = taraCtaEntrance.interpolate({
    inputRange: [0, 1],
    outputRange: [0.94, 1],
  });

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
        <View style={[styles.heroCopy, hasChart && styles.heroCopyWithChart]}>
          <Text style={[styles.heroEyebrow, typography.eyebrow, { color: colors.accent }]}>{t('premiumUi.home.taraGuide')}</Text>
          <Text style={[styles.heroTitle, typography.title, hasChart && styles.heroTitleWithChart, { color: colors.textInverse }]}>
            {hasChart
              ? t('premiumUi.home.heroQuestionTitle', 'Your chart has something to say.')
              : t('premiumUi.home.meetTara')}
            {`\n`}
            {hasChart
              ? t('premiumUi.home.heroQuestionSubtitle', 'Ask Tara what it means.')
              : t('premiumUi.home.readLife')}
          </Text>
          <Text style={[styles.heroBody, hasChart && styles.heroBodyWithChart, { color: colors.textInverseMuted }]}>
            {hasChart
              ? t('premiumUi.home.heroWithChart')
              : t('premiumUi.home.heroNoChart')}
          </Text>
        </View>
        <OrbitMotif colors={colors} subdued={hasChart} />
        <View style={styles.heroActions}>
          <Animated.View
            style={[
              styles.primaryActionShell,
              {
                opacity: taraCtaEntrance,
                shadowColor: colors.accent,
                transform: [{ scale: taraEntranceScale }],
              },
            ]}
          >
            {firstQuestionFree ? (
              <View style={[styles.firstQuestionBadge, { backgroundColor: colors.cosmicSurface, borderColor: colors.accent }]}>
                <Ionicons name="gift-outline" size={11} color={colors.accentSoft} />
                <Text style={[styles.firstQuestionBadgeText, { color: colors.accentSoft }]}>
                  {t('premiumUi.home.firstQuestionFreeBadge', 'First question free')}
                </Text>
              </View>
            ) : null}
            <TouchableOpacity
              onPress={hasChart ? onAsk : onCreateChart}
              activeOpacity={0.86}
              accessibilityRole="button"
              accessibilityLabel={hasChart
                ? t('premiumUi.home.askTaraActive', "Ask Tara what's active now")
                : t('premiumUi.home.createFreeChartCta', 'Create my free chart')}
              accessibilityHint={t('premiumUi.home.askTaraPromise', 'Get a personal answer from your complete birth chart')}
            >
              <View style={[styles.primaryActionBorder, { backgroundColor: colors.ctaShimmerTrail || '#a96f12' }]}>
                <LinearGradient
                  colors={[colors.accentSoft, colors.selectionControl || colors.accentSoft]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={styles.primaryAction}
                >
                  <Animated.View
                    pointerEvents="none"
                    style={[
                      styles.primaryActionGradientShift,
                      {
                        opacity: taraCtaShimmer.interpolate({
                          inputRange: [0, 1],
                          outputRange: [0.08, 0.72],
                        }),
                      },
                    ]}
                  >
                    <LinearGradient
                      colors={[
                        colors.ctaShimmerTrail || '#a96f12',
                        colors.ctaShimmerCore || '#ffd65a',
                        '#e7b64f',
                      ]}
                      locations={[0, 0.46, 1]}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 1 }}
                      style={styles.primaryActionGradientLayer}
                    />
                  </Animated.View>
                  <View
                    style={[
                      styles.primaryActionMark,
                      {
                        backgroundColor: colors.cosmicSurface,
                        shadowColor: colors.ctaShimmerCore || '#ffd65a',
                      },
                    ]}
                  >
                    <Animated.View
                      pointerEvents="none"
                      style={[
                        styles.primaryActionMarkGlow,
                        {
                          backgroundColor: colors.ctaShimmerCore || '#ffd65a',
                          opacity: taraCtaShimmer.interpolate({
                            inputRange: [0, 1],
                            outputRange: [0.22, 0.68],
                          }),
                          transform: [{
                            scale: taraCtaShimmer.interpolate({
                              inputRange: [0, 1],
                              outputRange: [0.92, 1.16],
                            }),
                          }],
                        },
                      ]}
                    />
                    <Ionicons name="sparkles" size={17} color={colors.accentSoft} />
                  </View>
                  <View style={styles.primaryActionCopy}>
                    <Text style={[styles.primaryActionText, { color: colors.onAccent }]} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.82}>
                      {hasChart
                        ? t('premiumUi.home.askTaraActive', "Ask Tara what's active now")
                        : t('premiumUi.home.createFreeChartCta', 'Create my free chart')}
                    </Text>
                    <Text style={[styles.primaryActionSubtext, { color: colors.onAccent }]} numberOfLines={1}>
                      {hasChart
                        ? t('premiumUi.home.askTaraPromise', 'Personal guidance from your complete birth chart')
                        : t('premiumUi.home.askTaraNoChartPromise', 'Then ask Tara your first question')}
                    </Text>
                  </View>
                  <View style={[styles.primaryActionArrow, { backgroundColor: colors.accentSoft }]}>
                    <Ionicons name="arrow-forward" size={17} color={colors.onAccent} />
                  </View>
                </LinearGradient>
              </View>
            </TouchableOpacity>
          </Animated.View>
          {hasChart ? (
            <TouchableOpacity onPress={onOpenCharts} activeOpacity={0.72} style={styles.secondaryAction}>
              <Text style={[styles.secondaryActionText, { color: colors.textInverseMuted }]}>{t('premiumUi.home.openChart')}</Text>
              <Ionicons name="arrow-forward" size={14} color={colors.textInverseMuted} />
            </TouchableOpacity>
          ) : null}
        </View>
      </View>

      {onTalkToTara ? (
        <TouchableOpacity
          onPress={onTalkToTara}
          activeOpacity={0.84}
          accessibilityRole="button"
          accessibilityLabel={t('chat.modeIntro.speech.name', 'Talk To Tara')}
          accessibilityHint={t('chat.speechChatCtaSubtext', 'Start a live voice conversation')}
          style={styles.talkToTaraCard}
        >
          <LinearGradient
            colors={[colors.cosmicRaised || colors.cosmicSurface, colors.cosmicSurface]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={[styles.talkToTaraGradient, { borderColor: colors.cosmicLine }]}
          >
            <View style={[styles.talkToTaraGlow, { backgroundColor: colors.cosmicGlow }]} accessibilityElementsHidden />
            <View style={[styles.talkToTaraOrbit, { borderColor: colors.cosmicLine }]} accessibilityElementsHidden />

            <View style={styles.talkToTaraHeader}>
              <VoiceMark colors={colors} />
              <View style={styles.talkToTaraCopy}>
                <View style={styles.talkToTaraBadgeRow}>
                  <Text style={[styles.talkToTaraEyebrow, typography.eyebrow, { color: colors.accent }]}>
                    {t('chat.modeIntro.speech.signature', 'Signature voice')}
                  </Text>
                  <View style={[styles.talkToTaraNewBadge, { backgroundColor: colors.accentSoft }]}>
                    <Text style={[styles.talkToTaraNewBadgeText, { color: colors.onAccent }]}>
                      {t('chat.modeIntro.speech.newBadge', 'New')}
                    </Text>
                  </View>
                </View>
                <Text style={[styles.talkToTaraTitle, { color: colors.textInverse }]}>
                  {t('chat.modeIntro.speech.name', 'Talk To Tara')}
                </Text>
              </View>
            </View>

            <Text style={[styles.talkToTaraBody, { color: colors.textInverseMuted }]} numberOfLines={2}>
              {t('chat.modeIntro.speech.benefit', 'Talk naturally with Tara and hear every reply.')}
            </Text>

            <View style={styles.talkToTaraFooter}>
              <View style={styles.talkToTaraRate}>
                <Ionicons name="time-outline" size={15} color={colors.textInverseMuted} />
                <Text style={[styles.talkToTaraRateText, { color: colors.textInverseMuted }]}>
                  {t('chat.modeIntro.speech.perStartedMinute', {
                    cost: speechPerMinuteCost,
                    defaultValue: '{{cost}} credits / started min',
                  })}
                </Text>
              </View>
              <View style={[styles.talkToTaraCta, { backgroundColor: colors.accentSoft }]}>
                <Text style={[styles.talkToTaraCtaText, { color: colors.onAccent }]}>
                  {t('chat.modeIntro.speech.startTalking', 'Start talking')}
                </Text>
                <Ionicons name="arrow-forward" size={15} color={colors.onAccent} />
              </View>
            </View>
          </LinearGradient>
        </TouchableOpacity>
      ) : null}

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

      {hasChart ? (
        <ComingUpChartCard
          data={nextPeakData}
          loading={nextPeakLoading}
          nativeName={name}
          localizePlanet={localizePlanet}
          onPressDetail={onNextPeakOpenDetail}
          onAskTara={onNextPeakAsk}
          onOpenTimeline={onNextPeakTimeline}
        />
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
        <Metric label={t('menu.prashna', 'Prashna')} value={t('prashna.eyebrow', 'Question chart')} onPress={hasChart ? onOpenPrashna : onCreateChart} colors={colors} icon="help-circle-outline" calculating={t('premiumUi.home.calculating')} />
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
  onOpenPrashna,
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
    ['help-circle-outline', t('menu.prashna', 'Prashna'), t('prashna.shortcutBody', 'Yes or no from the question’s time'), onOpenPrashna],
    ['document-text-outline', t('premiumUi.home.premiumReports'), t('premiumUi.home.longReadings'), onOpenReports],
    ['sunny-outline', t('premiumUi.home.panchang'), t('premiumUi.home.dayRhythm'), onOpenPanchang],
    ['time-outline', t('premiumUi.home.muhurat'), t('premiumUi.home.supportiveTiming'), onOpenMuhurat],
  ];
  const personalAnalyses = analyses.filter((item) => !['yearly', 'muhurat', 'trading', 'financial', 'childbirth'].includes(item.id));
  const timingAnalyses = analyses.filter((item) => ['muhurat', 'trading', 'financial', 'childbirth'].includes(item.id));
  const guidedPaths = paths.filter((item) => item.action !== 'events');
  return (
    <View style={styles.exploreIntroWrap}>
      <View style={[styles.exploreHero, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
        <View pointerEvents="none" style={styles.exploreHeroLinework} accessibilityElementsHidden>
          <View style={[styles.exploreHeroOrbit, styles.exploreHeroOrbitLarge, { borderColor: colors.cosmicLine }]} />
          <View style={[styles.exploreHeroOrbit, styles.exploreHeroOrbitSmall, { borderColor: colors.cosmicLine }]} />
          <View style={[styles.exploreHeroMeridian, { backgroundColor: colors.cosmicLine }]} />
          <View style={[styles.exploreHeroBaseline, { backgroundColor: colors.cosmicLine }]} />
        </View>
        <View style={styles.exploreHeroEyebrowRow}>
          <View style={[styles.exploreHeroEyebrowRule, { backgroundColor: colors.textInverseMuted }]} />
          <Text style={[typography.eyebrow, { color: colors.accent }]}>
            {t('premiumUi.home.vedicStudio')}
          </Text>
        </View>
        <Text style={[typography.title, styles.exploreHeroTitle, { color: colors.textInverse }]}>{t('premiumUi.home.exploreWith')}{`\n`}{t('premiumUi.home.purpose')}</Text>
        <Text style={[styles.exploreHeroBody, { color: colors.textInverseMuted }]}>{t('premiumUi.home.studioBody')}</Text>
      </View>
      <View style={[styles.timingSpotlight, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
        <View pointerEvents="none" style={styles.timingSpotlightGlow} />
        <View style={styles.timingSpotlightHeader}>
          <View style={styles.timingSpotlightHeading}>
            <Text style={[typography.eyebrow, { color: colors.accent }]}>
              {t('premiumUi.home.signatureTiming', 'SIGNATURE TIMING')}
            </Text>
            <Text style={[typography.sectionTitle, styles.timingSpotlightTitle, { color: colors.textInverse }]}>
              {t('premiumUi.home.yourTimeAhead', 'Your time ahead')}
            </Text>
          </View>
          <View style={[styles.timingCostPill, { borderColor: colors.cosmicLine, backgroundColor: colors.cosmicRaised }]}>
            <Ionicons name="diamond-outline" size={12} color={colors.accent} />
            <Text style={[styles.timingCostText, { color: colors.textInverse }]}>
              {t('premiumUi.home.creditsShort', { count: eventsCost })}
            </Text>
          </View>
        </View>
        <Text style={[styles.timingSpotlightBody, { color: colors.textInverseMuted }]}>
          {t(
            'premiumUi.home.timingSpotlightBody',
            'Personal timing from dashas, transits, Parashari, Nadi, Jaimini and KP.'
          )}
        </Text>
        <View style={styles.timingChoices}>
          <TouchableOpacity
            onPress={onOpenYearly}
            activeOpacity={0.82}
            style={[styles.timingChoice, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}
          >
            <View style={[styles.timingChoiceIcon, { backgroundColor: colors.accentSoft }]}>
              <Ionicons name="calendar-outline" size={20} color={colors.onAccent} />
            </View>
            <Text style={[styles.timingChoiceTitle, { color: colors.textInverse }]}>
              {t('premiumUi.home.yearlyTimeline', 'Yearly timeline')}
            </Text>
            <Text style={[styles.timingChoiceBody, { color: colors.textInverseMuted }]} numberOfLines={2}>
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
            style={[styles.timingChoice, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}
          >
            <View style={[styles.timingChoiceIcon, { backgroundColor: colors.accentSoft }]}>
              <Ionicons name="moon-outline" size={20} color={colors.onAccent} />
            </View>
            <Text style={[styles.timingChoiceTitle, { color: colors.textInverse }]}>
              {t('premiumUi.home.monthlyDeepDive', 'Monthly deep dive')}
            </Text>
            <Text style={[styles.timingChoiceBody, { color: colors.textInverseMuted }]} numberOfLines={2}>
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
  hero: { minHeight: 410, borderWidth: 1, borderRadius: 30, padding: 24, overflow: 'hidden' },
  heroCopy: { maxWidth: '69%', zIndex: 2 },
  heroCopyWithChart: { maxWidth: '100%' },
  heroEyebrow: { marginBottom: 14 },
  heroTitle: { fontSize: 40, lineHeight: 42, marginBottom: 14 },
  heroTitleWithChart: { maxWidth: '88%', fontSize: 37, lineHeight: 40 },
  heroBody: { fontSize: 13, lineHeight: 20, fontWeight: '500' },
  heroBodyWithChart: { maxWidth: '100%', paddingRight: 2 },
  orbitMotif: { position: 'absolute', right: -18, top: 44, opacity: 0.58 },
  orbitMotifSubdued: { right: -32, top: 48, opacity: 0.3 },
  heroActions: { marginTop: 24, alignItems: 'center', zIndex: 2 },
  primaryActionShell: { alignSelf: 'stretch', borderRadius: 999, shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.34, shadowRadius: 18, elevation: 8 },
  firstQuestionBadge: { position: 'absolute', alignSelf: 'center', top: -13, zIndex: 3, minHeight: 25, borderWidth: 1, borderRadius: 999, paddingHorizontal: 10, flexDirection: 'row', alignItems: 'center', gap: 5 },
  firstQuestionBadgeText: { fontSize: 9, lineHeight: 11, fontWeight: '900', letterSpacing: 0.8, textTransform: 'uppercase' },
  primaryActionBorder: { minHeight: 64, borderRadius: 999, padding: 1.5, overflow: 'hidden' },
  primaryAction: { flex: 1, minHeight: 61, paddingHorizontal: 8, borderRadius: 999, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 9, overflow: 'hidden' },
  primaryActionGradientShift: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0 },
  primaryActionGradientLayer: { flex: 1 },
  primaryActionMark: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center', shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.72, shadowRadius: 8, elevation: 6 },
  primaryActionMarkGlow: { position: 'absolute', width: 42, height: 42, borderRadius: 21 },
  primaryActionCopy: { flex: 1, minWidth: 0, alignItems: 'flex-start' },
  primaryActionText: { width: '100%', fontSize: 15, lineHeight: 19, fontWeight: '900', letterSpacing: 0.1 },
  primaryActionSubtext: { width: '100%', marginTop: 2, fontSize: 9, lineHeight: 12, fontWeight: '700', opacity: 0.66 },
  primaryActionArrow: { width: 34, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
  secondaryAction: { minHeight: 38, marginTop: 4, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  secondaryActionText: { fontSize: 11, fontWeight: '800' },
  talkToTaraCard: { borderRadius: 24 },
  talkToTaraGradient: { minHeight: 168, borderWidth: 1, borderRadius: 24, padding: 18, overflow: 'hidden' },
  talkToTaraGlow: { position: 'absolute', width: 176, height: 176, borderRadius: 88, right: -54, top: -84 },
  talkToTaraOrbit: { position: 'absolute', width: 142, height: 142, borderRadius: 71, borderWidth: 1, right: -30, top: -68 },
  talkToTaraHeader: { flexDirection: 'row', alignItems: 'center', zIndex: 1 },
  voiceMark: { width: 58, height: 58, borderRadius: 20, alignItems: 'center', justifyContent: 'center', marginRight: 14 },
  voiceMarkWave: { position: 'absolute', right: 6, bottom: 7, height: 20, flexDirection: 'row', alignItems: 'center', gap: 2 },
  voiceMarkBar: { width: 2, borderRadius: 1 },
  talkToTaraCopy: { flex: 1, minWidth: 0 },
  talkToTaraBadgeRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 5 },
  talkToTaraEyebrow: { fontSize: 9 },
  talkToTaraNewBadge: { borderRadius: 999, paddingHorizontal: 7, paddingVertical: 3 },
  talkToTaraNewBadgeText: { fontSize: 8, lineHeight: 10, fontWeight: '900', textTransform: 'uppercase', letterSpacing: 0.5 },
  talkToTaraTitle: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 25, lineHeight: 29 },
  talkToTaraBody: { marginTop: 13, maxWidth: '84%', fontSize: 12, lineHeight: 17, fontWeight: '500', zIndex: 1 },
  talkToTaraFooter: { marginTop: 14, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10, zIndex: 1 },
  talkToTaraRate: { flex: 1, minWidth: 0, flexDirection: 'row', alignItems: 'center', gap: 5 },
  talkToTaraRateText: { flexShrink: 1, fontSize: 9, lineHeight: 12, fontWeight: '700' },
  talkToTaraCta: { minHeight: 36, maxWidth: '48%', borderRadius: 999, paddingHorizontal: 13, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  talkToTaraCtaText: { flexShrink: 1, fontSize: 10, fontWeight: '900' },
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
  timingChoice: { flex: 1, minWidth: 0, minHeight: 176, borderWidth: 1, borderRadius: 18, padding: 13, overflow: 'hidden' },
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
