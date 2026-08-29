import React, { useEffect, useMemo, useRef } from 'react';
import { Animated, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Circle, Line, Path, Polygon, Rect, Text as SvgText } from 'react-native-svg';

const GOLD = '#FFD58A';
const CREAM = '#FFF8ED';
const MUTED = '#EBCFC8';
const PLANET_ABBR = {
  Ascendant: 'As', Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
  Uranus: 'Ur', Neptune: 'Ne', Pluto: 'Pl',
};
const HOUSE_POINTS = {
  1: [150, 48], 2: [96, 32], 3: [48, 61], 4: [67, 105],
  5: [48, 151], 6: [96, 180], 7: [150, 162], 8: [204, 180],
  9: [252, 151], 10: [233, 105], 11: [252, 61], 12: [204, 32],
};
const ZODIAC_GLYPHS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];
const ACCENT_GLOWS = {
  gold: 'rgba(255, 193, 92, 0.22)', rose: 'rgba(240, 79, 157, 0.22)',
  violet: 'rgba(151, 105, 255, 0.23)', ember: 'rgba(255, 112, 46, 0.23)',
};
// Scene copy reveals over ~300–450 ms. Select it shortly before its spoken
// boundary so the animation finishes as the corresponding audio begins.
// 450 ms reveal + up to one 250 ms playback-status interval.
const VISUAL_COPY_LEAD_MILLIS = 700;
const CAPTION_LEAD_MILLIS = 200;
const HINDI_SCENE_LABELS = {
  opening: 'परिचय', natal_chart: 'जन्म कुंडली', transit_chart: 'गोचर कुंडली',
  divisional_chart: 'वर्ग कुंडली',
  house_highlight: 'सक्रिय भाव', planet_highlight: 'प्रमुख ग्रह', dasha_timeline: 'दशा क्रम',
  date_window: 'समय अवधि', comparison: 'तुलना', action_steps: 'अगले कदम', warning: 'सावधानी',
  key_takeaway: 'मुख्य सीख', closing: 'समापन', zodiac_spotlight: 'राशि संकेत',
  aspect_lines: 'ग्रह दृष्टि', conjunction: 'युति', balance: 'संतुलन', quote: 'मुख्य बात',
  myth_reveal: 'सच्चाई', decision_path: 'निर्णय मार्ग', constellation_summary: 'समग्र संकेत',
  host_focus: 'विशेष चर्चा', celestial_interlude: 'आकाशीय संकेत', topic_cards: 'मुख्य विषय',
  ashtakavarga_table: 'अष्टकवर्ग तालिका',
  house_activation_map: 'भाव सक्रियता',
};
const ACTIVATION_LAYERS = [
  { key: 'natal_promise', color: '#FFD166', en: 'NATAL', hi: 'जन्म' },
  { key: 'dasha_activation', color: '#BB86FC', en: 'DASHA', hi: 'दशा' },
  { key: 'transit_activation', color: '#62D6FF', en: 'TRANSIT', hi: 'गोचर' },
  { key: 'ashtakavarga_support', color: '#67E8A5', en: 'SAV', hi: 'SAV' },
];

function normalisePlanet(value) {
  return String(value || '').trim().toLowerCase();
}

function HouseChart({ scene, chart, compact, chartLabel = 'D1 · RASI' }) {
  const planets = Array.isArray(chart?.planets) ? chart.planets : [];
  const highlightedHouses = new Set(
    (Array.isArray(scene?.houses) ? scene.houses : []).map((value) => Number(value)),
  );
  const highlightedPlanets = new Set(
    (Array.isArray(scene?.planets) ? scene.planets : []).map(normalisePlanet),
  );
  const ascendantSign = Number.isFinite(Number(chart?.ascendant_sign))
    ? Number(chart.ascendant_sign)
    : Math.floor(Number(chart?.ascendant || 0) / 30);
  const byHouse = useMemo(() => {
    const result = {};
    planets.forEach((planet) => {
      const house = Number(planet?.house);
      if (house >= 1 && house <= 12) {
        if (!result[house]) result[house] = [];
        result[house].push(planet);
      }
    });
    return result;
  }, [planets]);
  const activeHouseNumbers = useMemo(() => {
    const result = new Set(highlightedHouses);
    planets.forEach((planet) => {
      if (highlightedPlanets.has(normalisePlanet(planet?.name))) result.add(Number(planet?.house));
    });
    return Array.from(result).filter((house) => HOUSE_POINTS[house]);
  }, [highlightedHouses, highlightedPlanets, planets]);

  return (
    <View style={[styles.chartWrap, compact && styles.chartWrapCompact]}>
      <View style={styles.chartIdentity}><Text style={styles.chartIdentityText}>{chartLabel}</Text></View>
      <Svg width="100%" height="100%" viewBox="0 0 300 210">
        <Rect x="20" y="10" width="260" height="190" rx="5" stroke={GOLD} strokeWidth="1.4" opacity="0.86" fill="rgba(30,2,48,0.2)" />
        <Polygon points="150,10 280,105 150,200 20,105" stroke={GOLD} strokeWidth="1.15" opacity="0.78" fill="none" />
        <Line x1="20" y1="10" x2="150" y2="105" stroke={GOLD} opacity="0.64" />
        <Line x1="280" y1="10" x2="150" y2="105" stroke={GOLD} opacity="0.64" />
        <Line x1="280" y1="200" x2="150" y2="105" stroke={GOLD} opacity="0.64" />
        <Line x1="20" y1="200" x2="150" y2="105" stroke={GOLD} opacity="0.64" />
        {['aspect_lines', 'conjunction'].includes(String(scene?.type)) && activeHouseNumbers.slice(1).map((house, index) => (
          <Line
            key={`aspect-${house}`}
            x1={HOUSE_POINTS[activeHouseNumbers[0]]?.[0] || 150}
            y1={HOUSE_POINTS[activeHouseNumbers[0]]?.[1] || 105}
            x2={HOUSE_POINTS[house][0]}
            y2={HOUSE_POINTS[house][1]}
            stroke={index % 2 ? '#E2BBFF' : '#FFB45B'}
            strokeWidth="2"
            opacity="0.8"
          />
        ))}
        {Object.entries(HOUSE_POINTS).map(([houseKey, point]) => {
          const house = Number(houseKey);
          const [x, y] = point;
          const housePlanets = byHouse[house] || [];
          const planetIsActive = housePlanets.some((planet) => highlightedPlanets.has(normalisePlanet(planet.name)));
          const active = highlightedHouses.has(house) || planetIsActive;
          const sign = ((ascendantSign + house - 1) % 12) + 1;
          const labels = housePlanets.map((planet) => PLANET_ABBR[planet.name] || String(planet.name || '').slice(0, 2));
          return (
            <React.Fragment key={house}>
              {active && <Circle cx={x} cy={y + 2} r={compact ? 18 : 22} fill="rgba(255,174,82,0.2)" stroke={GOLD} strokeWidth="1.3" />}
              <SvgText x={x} y={y - 5} textAnchor="middle" fill={active ? GOLD : '#BFA1B8'} fontSize="8" fontWeight="700">{sign}</SvgText>
              {!!labels.length && (
                <SvgText x={x} y={y + 10} textAnchor="middle" fill={active ? CREAM : '#E6D1DE'} fontSize={labels.length > 2 ? '8' : '9'} fontWeight={active ? '800' : '600'}>
                  {labels.slice(0, 4).join(' ')}
                </SvgText>
              )}
            </React.Fragment>
          );
        })}
        <Circle cx="150" cy="105" r="7" fill="#FFB45B" opacity="0.82" />
      </Svg>
    </View>
  );
}

function TimelineVisual({ scene, compact, isHindi }) {
  const dates = Array.isArray(scene?.dates) ? scene.dates : [];
  return (
    <View style={[styles.timeline, compact && styles.timelineCompact]}>
      <LinearGradient colors={['#FFB45B', '#FFD58A', 'rgba(255,213,138,0.18)']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.timelineLine} />
      {dates.slice(0, 3).map((date, index) => (
        <View key={`${date}-${index}`} style={styles.timelinePointWrap}>
          <View style={[styles.timelinePoint, index === 0 && styles.timelinePointActive]}><View style={styles.timelinePointCore} /></View>
          <Text numberOfLines={2} style={styles.timelineLabel}>{String(date).toUpperCase()}</Text>
        </View>
      ))}
    </View>
  );
}

function shortDate(value) {
  const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return String(value || '').toUpperCase();
  const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
  return `${months[Number(match[2]) - 1]} ${match[1]}`;
}

function periodProgress(period, asOf) {
  const start = Date.parse(period?.start);
  const end = Date.parse(period?.end);
  const current = Date.parse(asOf);
  if (![start, end, current].every(Number.isFinite) || end <= start) return 0;
  return Math.max(0.03, Math.min(1, (current - start) / (end - start)));
}

function DashaTimelineVisual({ chart, compact, isHindi }) {
  const dasha = chart?.dasha || {};
  const levels = Array.isArray(dasha.levels) ? dasha.levels : [];
  const mahaPeriods = Array.isArray(dasha.mahadashas) ? dasha.mahadashas : [];
  const currentMahaIndex = Math.max(0, mahaPeriods.findIndex((period) => period.current));
  const visibleMaha = mahaPeriods.slice(Math.max(0, currentMahaIndex - 1), currentMahaIndex + 3);
  const levelNames = isHindi
    ? { maha: 'महादशा', antar: 'अंतरदशा', pratyantar: 'प्रत्यंतर' }
    : { maha: 'MAHA', antar: 'ANTAR', pratyantar: 'PRATYANTAR' };
  return (
    <View style={[styles.dashaWrap, compact && styles.dashaWrapCompact]}>
      <View style={styles.dashaChain}>
        {levels.map((level, index) => (
          <React.Fragment key={`${level.kind}-${level.planet}`}>
            {index > 0 && <Text style={styles.dashaArrow}>›</Text>}
            <View style={[styles.dashaChip, index === levels.length - 1 && styles.dashaChipActive]}>
              <Text style={styles.dashaLevel}>{levelNames[level.kind] || level.kind}</Text>
              <Text style={styles.dashaPlanet}>{String(level.planet).toUpperCase()}</Text>
            </View>
          </React.Fragment>
        ))}
      </View>
      {levels.filter((level) => level.start && level.end).slice(0, 2).map((level, index) => (
        <View key={`band-${level.kind}`} style={[styles.dashaBand, index === 1 && styles.dashaBandNested]}>
          <View style={styles.dashaBandLabels}>
            <Text style={styles.dashaBandName}>{`${String(level.planet).toUpperCase()} · ${levelNames[level.kind]}`}</Text>
            <Text style={styles.dashaDates}>{`${shortDate(level.start)} — ${shortDate(level.end)}`}</Text>
          </View>
          <View style={styles.dashaTrack}>
            <LinearGradient colors={index ? ['#D2B5FF', '#A66BE6'] : ['#FFD58A', '#F08A4B']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={[styles.dashaFill, { width: `${periodProgress(level, dasha.as_of) * 100}%` }]} />
            <View style={[styles.dashaNow, { left: `${periodProgress(level, dasha.as_of) * 100}%` }]} />
          </View>
        </View>
      ))}
      {!!visibleMaha.length && (
        <View style={styles.mahaSequence}>
          {visibleMaha.map((period) => (
            <View key={`${period.planet}-${period.start}`} style={[styles.mahaPeriod, period.current && styles.mahaPeriodActive]}>
              <Text style={[styles.mahaPlanet, period.current && styles.mahaPlanetActive]}>{PLANET_ABBR[period.planet] || String(period.planet).slice(0, 2)}</Text>
              <Text style={styles.mahaYear}>{String(period.start || '').slice(0, 4)}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

function StepsVisual({ scene, compact, isHindi }) {
  const steps = Array.isArray(scene?.steps) && scene.steps.length
    ? scene.steps
    : (isHindi ? ['संकेत समझें', 'अपना रास्ता चुनें', 'स्पष्टता से बढ़ें'] : ['See the pattern', 'Choose your response', 'Move with clarity']);
  return (
    <View style={[styles.steps, compact && styles.stepsCompact]}>
      {steps.slice(0, 3).map((step, index) => (
        <View key={`${step}-${index}`} style={[styles.stepCard, index === 0 && styles.stepCardActive]}>
          <Text style={styles.stepNumber}>{`0${index + 1}`}</Text>
          <Text numberOfLines={3} style={styles.stepText}>{String(step).toUpperCase()}</Text>
        </View>
      ))}
    </View>
  );
}

function ZodiacVisual({ scene, chart, compact, spin, isHindi }) {
  const ascendantSign = Number.isFinite(Number(chart?.ascendant_sign))
    ? Number(chart.ascendant_sign)
    : Math.floor(Number(chart?.ascendant || 0) / 30);
  const rotation = spin.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '-360deg'] });
  return (
    <View style={[styles.symbolVisual, compact && styles.symbolVisualCompact]}>
      <Animated.View style={[StyleSheet.absoluteFillObject, { transform: [{ rotate: rotation }] }]}>
        <Svg width="100%" height="100%" viewBox="0 0 300 205">
          <Circle cx="150" cy="102" r="78" fill="rgba(27,2,45,0.2)" stroke={GOLD} opacity="0.56" />
          <Circle cx="150" cy="102" r="49" fill="none" stroke="#E4B9FF" opacity="0.28" />
          {ZODIAC_GLYPHS.map((glyph, index) => {
            const angle = (Math.PI * 2 * index) / 12 - Math.PI / 2;
            const x = 150 + Math.cos(angle) * 67;
            const y = 106 + Math.sin(angle) * 67;
            const active = index === ascendantSign;
            return <SvgText key={glyph} x={x} y={y} textAnchor="middle" fill={active ? GOLD : '#D8BDCF'} fontSize={active ? '18' : '13'} fontWeight={active ? '900' : '500'}>{glyph}</SvgText>;
          })}
        </Svg>
      </Animated.View>
      <View style={styles.zodiacCore}>
        <Text style={styles.zodiacGlyph}>{ZODIAC_GLYPHS[ascendantSign] || '✦'}</Text>
        <Text style={styles.zodiacCoreLabel}>{scene?.planets?.[0] || (isHindi ? 'लग्न' : 'LAGNA')}</Text>
      </View>
    </View>
  );
}

function BalanceVisual({ scene, compact, isHindi }) {
  const labels = [scene?.planets?.[0] || (isHindi ? 'संभावना' : 'PROMISE'), scene?.planets?.[1] || (isHindi ? 'दबाव' : 'PRESSURE')];
  return (
    <View style={[styles.balanceWrap, compact && styles.balanceWrapCompact]}>
      <View style={styles.balanceBeam} />
      <View style={styles.balancePivot}><Text style={styles.balancePivotText}>✦</Text></View>
      {labels.map((label, index) => (
        <View key={`${label}-${index}`} style={[styles.balanceSide, index === 0 ? styles.balanceLeft : styles.balanceRight]}>
          <LinearGradient colors={index === 0 ? ['#FFD58A', '#EF8C5B'] : ['#D8BEFF', '#6B3E9A']} style={styles.balanceOrb} />
          <Text numberOfLines={2} style={styles.balanceLabel}>{String(label).toUpperCase()}</Text>
        </View>
      ))}
    </View>
  );
}

function StatementVisual({ scene, compact, isHindi }) {
  const isWarning = ['warning', 'myth_reveal'].includes(String(scene?.type));
  return (
    <View style={[styles.statementWrap, compact && styles.statementWrapCompact]}>
      <Text style={styles.statementMark}>{isWarning ? '!' : '“'}</Text>
      <View style={styles.statementRule} />
      <Text numberOfLines={compact ? 3 : 4} style={[styles.statementText, isWarning && styles.statementWarning]}>
        {scene?.headline || 'A pattern worth noticing'}
      </Text>
      <Text style={styles.statementTag}>{isWarning ? (isHindi ? 'ध्यान से देखें' : 'LOOK CLOSER') : (isHindi ? 'आपकी रीडिंग से' : 'FROM YOUR READING')}</Text>
    </View>
  );
}

function DecisionVisual({ scene, compact, isHindi }) {
  const labels = Array.isArray(scene?.steps) && scene.steps.length
    ? scene.steps.slice(0, 3)
    : (isHindi ? ['समझें', 'चुनें', 'आगे बढ़ें'] : ['NOTICE', 'CHOOSE', 'MOVE']);
  return (
    <View style={[styles.decisionWrap, compact && styles.decisionWrapCompact]}>
      <View style={styles.decisionOrigin}><Text style={styles.decisionOriginText}>{isHindi ? 'आप' : 'YOU'}</Text></View>
      <View style={styles.decisionStem} />
      <View style={styles.decisionPaths}>
        {labels.map((label, index) => (
          <View key={`${label}-${index}`} style={[styles.decisionNode, index === 1 && styles.decisionNodeActive]}>
            <Text numberOfLines={2} style={styles.decisionNodeText}>{String(label).toUpperCase()}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

function ComparisonVisual({ scene, compact, isHindi }) {
  const labels = Array.isArray(scene?.planets) && scene.planets.length > 1
    ? scene.planets.slice(0, 2)
    : (isHindi ? ['जन्म', 'वर्तमान'] : ['NATAL', 'CURRENT']);
  return (
    <View style={[styles.comparisonWrap, compact && styles.comparisonWrapCompact]}>
      {labels.map((label, index) => (
        <View key={`${label}-${index}`} style={styles.comparisonSide}>
          <Svg width="100%" height="75%" viewBox="0 0 130 130">
            <Circle cx="65" cy="65" r="47" fill="rgba(32,3,50,0.22)" stroke={index ? '#D1B6FF' : GOLD} opacity="0.82" />
            <Path d="M13 65 C35 25 95 25 117 65 C95 105 35 105 13 65" stroke={index ? '#D1B6FF' : '#FFAF58'} fill="none" opacity="0.7" />
            <Circle cx={index ? 96 : 34} cy={index ? 90 : 45} r="7" fill={index ? '#B894F0' : '#FFAE58'} />
          </Svg>
          <Text style={styles.comparisonLabel}>{String(label).toUpperCase()}</Text>
        </View>
      ))}
      <View style={styles.comparisonVs}><Text style={styles.comparisonVsText}>×</Text></View>
    </View>
  );
}

function TopicCardsVisual({ scene, compact, isHindi }) {
  const cards = [
    ...(scene?.planets || []), ...(scene?.houses || []).map((house) => `${isHindi ? 'भाव' : 'HOUSE'} ${house}`), ...(scene?.dates || []),
  ].slice(0, 3);
  const values = cards.length ? cards : (isHindi ? ['पैटर्न', 'समय', 'कदम'] : ['PATTERN', 'TIMING', 'ACTION']);
  return (
    <View style={[styles.topicCards, compact && styles.topicCardsCompact]}>
      {values.map((value, index) => (
        <View key={`${value}-${index}`} style={[styles.topicCard, { transform: [{ rotate: `${(index - 1) * 3}deg` }] }]}>
          <Text style={styles.topicSymbol}>{['☉', '◇', '✦'][index]}</Text>
          <Text numberOfLines={2} style={styles.topicLabel}>{String(value).toUpperCase()}</Text>
        </View>
      ))}
    </View>
  );
}

function OrbitVisual({ compact, spin }) {
  const rotation = spin.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '360deg'] });
  return (
    <View style={[styles.orbitWrap, compact && styles.orbitWrapCompact]}>
      <Animated.View style={[StyleSheet.absoluteFillObject, { transform: [{ rotate: rotation }] }]}>
        <Svg width="100%" height="100%" viewBox="0 0 300 200">
          <Circle cx="150" cy="98" r="62" stroke={GOLD} opacity="0.25" fill="none" />
          <Path d="M34 98 C68 28 232 28 266 98 C232 168 68 168 34 98" stroke={GOLD} strokeWidth="1.2" opacity="0.66" fill="none" />
          <Path d="M150 12 C212 34 220 161 150 186 C82 161 88 34 150 12" stroke="#F3B36C" strokeWidth="1" opacity="0.45" fill="none" />
          <Circle cx="35" cy="94" r="7" fill="#FFAA55" />
          <Circle cx="219" cy="151" r="4" fill="#D9B5FF" />
        </Svg>
      </Animated.View>
      <LinearGradient colors={['#FFF0A8', '#FFB24F', '#5A174F']} start={{ x: 0.15, y: 0.1 }} end={{ x: 0.9, y: 0.9 }} style={[styles.sun, compact && styles.sunCompact]} />
    </View>
  );
}

function OpeningVisual({ compact, isHindi }) {
  return (
    <View style={[styles.bookendWrap, compact && styles.bookendWrapCompact]}>
      <View style={[styles.bookendHalo, styles.openingHalo]} />
      <View style={styles.openingHosts}>
        <LinearGradient colors={['#FFE19E', '#ED5B9B', '#501258']} style={styles.openingHostOrb} />
        <View style={styles.openingConnection}>
          <View style={styles.openingConnectionDot} />
          <View style={styles.openingConnectionLine} />
          <View style={styles.openingMic}>
            <View style={styles.openingMicHead} />
            <View style={styles.openingMicStem} />
          </View>
          <View style={styles.openingConnectionLine} />
          <View style={styles.openingConnectionDot} />
        </View>
        <LinearGradient colors={['#D5BDFF', '#7751B6', '#2D174E']} style={styles.openingHostOrb} />
      </View>
      <View style={styles.openingNames}>
        <Text style={styles.openingName}>{isHindi ? 'अनन्या' : 'ANANYA'}</Text>
        <Text style={styles.openingName}>{isHindi ? 'अर्जुन' : 'ARJUN'}</Text>
      </View>
      <Text style={styles.bookendKicker}>{isHindi ? 'आपकी व्यक्तिगत रीडिंग' : 'YOUR PERSONAL READING'}</Text>
      <Text style={[styles.bookendTitle, compact && styles.bookendTitleCompact]}>ASTROROSHNI</Text>
      <Text style={styles.bookendSubtitle}>{isHindi ? 'दो मेज़बान · आपकी एक कहानी' : 'TWO HOSTS · ONE STORY · YOUR CHART'}</Text>
    </View>
  );
}

function ClosingVisual({ compact, isHindi }) {
  return (
    <View style={[styles.bookendWrap, compact && styles.bookendWrapCompact]}>
      <View style={[styles.bookendHalo, styles.closingHalo]} />
      <View style={styles.closingMarkOuter}>
        <View style={styles.closingMarkInner}><Text style={styles.closingMarkText}>AR</Text></View>
      </View>
      <Text style={styles.bookendKicker}>{isHindi ? 'सुनने के लिए धन्यवाद' : 'THANK YOU FOR LISTENING'}</Text>
      <Text style={[styles.closingTitle, compact && styles.closingTitleCompact]}>{isHindi ? 'फिर मिलेंगे' : 'UNTIL NEXT TIME'}</Text>
      <View style={styles.closingHosts}>
        <Text style={styles.closingHostName}>{isHindi ? 'अनन्या' : 'ANANYA'}</Text>
        <Text style={styles.closingStar}>✦</Text>
        <Text style={styles.closingHostName}>{isHindi ? 'अर्जुन' : 'ARJUN'}</Text>
      </View>
    </View>
  );
}

function HostExchangeVisual({ compact, isHindi }) {
  return (
    <View style={[styles.hostExchangeWrap, compact && styles.hostExchangeWrapCompact]}>
      <View style={styles.hostExchangePerson}>
        <LinearGradient colors={['#FFE19E', '#ED5B9B', '#501258']} style={styles.hostExchangeOrb} />
        <Text style={styles.hostExchangeName}>{isHindi ? 'अनन्या' : 'ANANYA'}</Text>
      </View>
      <View style={styles.hostExchangeSignal}>
        {[11, 24, 16, 31, 19, 27, 13].map((height, index) => (
          <View key={`${height}-${index}`} style={[styles.hostExchangeBar, { height }]} />
        ))}
        <Text style={styles.hostExchangeLabel}>{isHindi ? 'बातचीत' : 'IN CONVERSATION'}</Text>
      </View>
      <View style={styles.hostExchangePerson}>
        <LinearGradient colors={['#D5BDFF', '#7751B6', '#2D174E']} style={styles.hostExchangeOrb} />
        <Text style={styles.hostExchangeName}>{isHindi ? 'अर्जुन' : 'ARJUN'}</Text>
      </View>
    </View>
  );
}

function AshtakavargaVisual({ scene, chart, compact, isHindi }) {
  const rows = Array.isArray(chart?.ashtakavarga?.rows) ? chart.ashtakavarga.rows.slice(0, 12) : [];
  const highlighted = new Set((scene?.houses || []).map((house) => Number(house)));
  const selectedPlanet = (scene?.planets || []).find((planet) => rows.some((row) => row?.bav?.[planet] != null));
  const savValues = rows.map((row) => Number(row?.sav || 0));
  const strongest = savValues.length ? Math.max(...savValues) : 0;
  const weakest = savValues.length ? Math.min(...savValues) : 0;
  return (
    <View style={[styles.ashtakavargaWrap, compact && styles.ashtakavargaWrapCompact]}>
      <View style={styles.ashtakavargaHeader}>
        <Text style={styles.ashtakavargaTitle}>{isHindi ? 'भाव शक्ति · SAV' : 'HOUSE STRENGTH · SAV'}</Text>
        {!!selectedPlanet && <Text style={styles.ashtakavargaPlanet}>{`${PLANET_ABBR[selectedPlanet] || selectedPlanet.slice(0, 2)} BAV`}</Text>}
      </View>
      <View style={styles.ashtakavargaGrid}>
        {rows.map((row) => {
          const sav = Number(row?.sav || 0);
          const active = highlighted.has(Number(row?.house));
          const strong = sav === strongest;
          const weak = sav === weakest;
          const bav = selectedPlanet ? Number(row?.bav?.[selectedPlanet] || 0) : null;
          return (
            <View
              key={row.house}
              style={[
                styles.ashtakavargaCell,
                strong && styles.ashtakavargaCellStrong,
                weak && styles.ashtakavargaCellWeak,
                active && styles.ashtakavargaCellActive,
              ]}
            >
              <Text style={styles.ashtakavargaHouse}>{isHindi ? `भाव ${row.house}` : `H${row.house}`}</Text>
              <Text style={styles.ashtakavargaSav}>{sav}</Text>
              {bav != null && <Text style={styles.ashtakavargaBav}>{`${PLANET_ABBR[selectedPlanet] || ''} ${bav}`}</Text>}
            </View>
          );
        })}
      </View>
    </View>
  );
}

function HouseActivationMap({ chart, compact, isHindi }) {
  const rows = Array.isArray(chart?.house_activation?.rows)
    ? chart.house_activation.rows.slice(0, 12)
    : [];
  return (
    <View style={[styles.activationWrap, compact && styles.activationWrapCompact]}>
      <View style={styles.activationLegend}>
        {ACTIVATION_LAYERS.map((layer) => (
          <View key={layer.key} style={styles.activationLegendItem}>
            <View style={[styles.activationLegendDot, { backgroundColor: layer.color }]} />
            <Text style={styles.activationLegendText}>{isHindi ? layer.hi : layer.en}</Text>
          </View>
        ))}
      </View>
      <View style={styles.activationGrid}>
        {rows.map((row) => {
          const activeLayers = ACTIVATION_LAYERS.filter((layer) => row?.[layer.key]);
          return (
            <View
              key={row.house}
              style={[
                styles.activationHouse,
                activeLayers.length > 0 && styles.activationHouseActive,
                activeLayers.length >= 3 && styles.activationHousePeak,
              ]}
            >
              <Text style={styles.activationHouseLabel}>{isHindi ? `भाव ${row.house}` : `HOUSE ${row.house}`}</Text>
              <Text style={[styles.activationHouseNumber, activeLayers.length > 0 && styles.activationHouseNumberActive]}>{row.house}</Text>
              <View style={styles.activationDots}>
                {ACTIVATION_LAYERS.map((layer) => (
                  <View
                    key={layer.key}
                    style={[
                      styles.activationDot,
                      { backgroundColor: layer.color, opacity: row?.[layer.key] ? 1 : 0.13 },
                      row?.[layer.key] && { shadowColor: layer.color, shadowOpacity: 0.95, shadowRadius: 5 },
                    ]}
                  />
                ))}
              </View>
              {row.sav != null && <Text style={styles.activationSav}>{`SAV ${row.sav}`}</Text>}
            </View>
          );
        })}
      </View>
    </View>
  );
}

function SceneArtwork({ scene, chart, compact, spin, isHindi }) {
  const type = String(scene?.type || 'key_takeaway');
  if (type === 'opening') return <OpeningVisual compact={compact} isHindi={isHindi} />;
  if (type === 'closing') return <ClosingVisual compact={compact} isHindi={isHindi} />;
  if (type === 'host_focus') return <HostExchangeVisual compact={compact} isHindi={isHindi} />;
  if (type === 'house_activation_map' && chart?.house_activation?.rows?.length) {
    return <HouseActivationMap chart={chart} compact={compact} isHindi={isHindi} />;
  }
  if (type === 'house_activation_map') return <TopicCardsVisual scene={scene} compact={compact} isHindi={isHindi} />;
  if (type === 'ashtakavarga_table' && chart?.ashtakavarga?.rows?.length) {
    return <AshtakavargaVisual scene={scene} chart={chart} compact={compact} isHindi={isHindi} />;
  }
  if (type === 'ashtakavarga_table') return <TopicCardsVisual scene={scene} compact={compact} isHindi={isHindi} />;
  if (type === 'divisional_chart') {
    const division = String(scene?.division || '');
    const divisional = chart?.divisional_charts?.[division];
    if (divisional?.planets?.length) {
      return <HouseChart scene={scene} chart={divisional} compact={compact} chartLabel={divisional.label || division} />;
    }
    return <TopicCardsVisual scene={scene} compact={compact} isHindi={isHindi} />;
  }
  if (['natal_chart', 'house_highlight', 'planet_highlight', 'aspect_lines', 'conjunction'].includes(type) && chart?.planets?.length) {
    return <HouseChart scene={scene} chart={chart} compact={compact} chartLabel="D1 · RASI" />;
  }
  if (['natal_chart', 'house_highlight', 'planet_highlight', 'aspect_lines', 'conjunction'].includes(type)) {
    return <TopicCardsVisual scene={scene} compact={compact} isHindi={isHindi} />;
  }
  if (type === 'dasha_timeline' && chart?.dasha?.levels?.length) {
    return <DashaTimelineVisual chart={chart} compact={compact} isHindi={isHindi} />;
  }
  if (type === 'dasha_timeline') return <TopicCardsVisual scene={scene} compact={compact} isHindi={isHindi} />;
  if (type === 'date_window' && scene?.dates?.length) {
    return <TimelineVisual scene={scene} compact={compact} isHindi={isHindi} />;
  }
  if (type === 'date_window') return <TopicCardsVisual scene={scene} compact={compact} isHindi={isHindi} />;
  if (type === 'action_steps') return <StepsVisual scene={scene} compact={compact} isHindi={isHindi} />;
  if (type === 'zodiac_spotlight') return <ZodiacVisual scene={scene} chart={chart} compact={compact} spin={spin} isHindi={isHindi} />;
  if (type === 'balance') return <BalanceVisual scene={scene} compact={compact} isHindi={isHindi} />;
  if (['quote', 'myth_reveal', 'warning', 'key_takeaway'].includes(type)) return <StatementVisual scene={scene} compact={compact} isHindi={isHindi} />;
  if (type === 'decision_path') return <DecisionVisual scene={scene} compact={compact} isHindi={isHindi} />;
  if (['comparison', 'transit_chart'].includes(type)) return <ComparisonVisual scene={scene} compact={compact} isHindi={isHindi} />;
  if (['topic_cards', 'constellation_summary'].includes(type)) return <TopicCardsVisual scene={scene} compact={compact} isHindi={isHindi} />;
  if (type === 'celestial_interlude') return <OrbitVisual compact={compact} spin={spin} />;
  return <TopicCardsVisual scene={scene} compact={compact} isHindi={isHindi} />;
}

function Host({ name, role, active, side }) {
  return (
    <View style={[styles.host, side === 'right' && styles.hostRight]}>
      {side === 'left' && <LinearGradient colors={['#FFD58A', '#EF4F9D', '#40104D']} style={[styles.hostOrb, active && styles.hostOrbActive]} />}
      <View style={side === 'right' && styles.hostCopyRight}>
        <Text style={[styles.hostName, active ? styles.hostNameActive : styles.hostMuted]}>{name}</Text>
        <Text style={[styles.hostRole, active ? styles.hostRoleActive : styles.hostMuted]}>{role}</Text>
      </View>
      {side === 'right' && <LinearGradient colors={['#C8ACFF', '#6543A1', '#281248']} style={[styles.hostOrb, active && styles.hostOrbActive]} />}
    </View>
  );
}

function normaliseSpeaker(value) {
  const speaker = String(value || '').trim().toLowerCase();
  if (speaker === 'male' || speaker === 'arjun') return 'male';
  if (speaker === 'female' || speaker === 'ananya') return 'female';
  return '';
}

export default function PodcastVisualStage({ manifest, positionMillis = 0, durationMillis = 0, paused = false, compact = false }) {
  const scenes = Array.isArray(manifest?.scenes) ? manifest.scenes : [];
  const chapters = Array.isArray(manifest?.chapters) ? manifest.chapters : [];
  const turns = Array.isArray(manifest?.turns) ? manifest.turns : [];
  const captions = Array.isArray(manifest?.captions) ? manifest.captions : [];
  const isHindi = String(manifest?.language || '').toLowerCase().startsWith('hi');
  const progress = durationMillis > 0 ? Math.max(0, Math.min(1, positionMillis / durationMillis)) : 0;
  const visualProgress = durationMillis > 0
    ? Math.max(0, Math.min(1, (positionMillis + VISUAL_COPY_LEAD_MILLIS) / durationMillis))
    : 0;
  const sceneIndex = useMemo(() => {
    if (!scenes.length) return 0;
    const found = scenes.findIndex((scene) => visualProgress < Number(scene.end_fraction ?? 1));
    return found >= 0 ? found : scenes.length - 1;
  }, [scenes, visualProgress]);
  const activeSpeaker = useMemo(() => {
    const turn = turns.find((item) => progress >= Number(item.start_fraction || 0) && progress < Number(item.end_fraction || 1));
    const timedSpeaker = normaliseSpeaker(turn?.speaker);
    if (timedSpeaker) return timedSpeaker;
    // Defensive fallback for old/corrupt manifests that only contain the
    // generic "narration" role. Never leave Ananya highlighted forever.
    const segmentIndex = Number(scenes[sceneIndex]?.segment_start);
    const fallbackIndex = Number.isFinite(segmentIndex) ? segmentIndex : sceneIndex;
    return fallbackIndex % 2 === 0 ? 'female' : 'male';
  }, [progress, sceneIndex, scenes, turns]);
  const ananyaActive = !paused && activeSpeaker === 'female';
  const arjunActive = !paused && activeSpeaker === 'male';
  const captionProgress = durationMillis > 0
    ? Math.max(0, Math.min(1, (positionMillis + CAPTION_LEAD_MILLIS) / durationMillis))
    : 0;
  const activeCaption = useMemo(() => {
    if (!captions.length) return null;
    const found = captions.find((caption) => (
      captionProgress >= Number(caption.start_fraction || 0)
      && captionProgress < Number(caption.end_fraction || 1)
    ));
    return found || captions[captions.length - 1];
  }, [captionProgress, captions]);
  const scene = scenes[sceneIndex] || {
    type: 'opening', headline: 'Your AstroRoshni Story',
    supporting_text: 'Your chart, explained as the conversation unfolds.',
  };
  const fade = useRef(new Animated.Value(1)).current;
  const lift = useRef(new Animated.Value(0)).current;
  const shift = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(1)).current;
  const spin = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animation = Animated.loop(Animated.timing(spin, {
      toValue: 1, duration: 24000, useNativeDriver: true,
    }));
    if (!paused) animation.start();
    return () => animation.stop();
  }, [paused, spin]);

  useEffect(() => {
    const transition = String(scene?.transition || 'rise');
    fade.setValue(0);
    lift.setValue(transition === 'rise' ? 18 : 0);
    shift.setValue(transition === 'slide_left' ? 42 : transition === 'slide_right' ? -42 : 0);
    scale.setValue(transition === 'zoom' ? 0.86 : transition === 'reveal' ? 0.95 : 1);
    Animated.parallel([
      Animated.timing(fade, { toValue: 1, duration: 300, useNativeDriver: true }),
      Animated.timing(lift, { toValue: 0, duration: 420, useNativeDriver: true }),
      Animated.timing(shift, { toValue: 0, duration: 430, useNativeDriver: true }),
      Animated.timing(scale, { toValue: 1, duration: 450, useNativeDriver: true }),
    ]).start();
  }, [sceneIndex, scene?.transition, fade, lift, scale, shift]);

  const sceneLabel = isHindi
    ? (HINDI_SCENE_LABELS[String(scene.type || '')] || 'मुख्य संकेत')
    : String(scene.type || 'INSIGHT').replace(/_/g, ' ').toUpperCase();
  const progressUnits = chapters.length ? chapters : scenes;
  return (
    <LinearGradient colors={['#220238', '#4C1552', '#A63356', '#F07838']} locations={[0, 0.42, 0.73, 1]} style={[styles.stage, compact && styles.stageCompact]}>
      <View style={styles.stars} pointerEvents="none">
        {[12, 44, 76, 91, 27, 63, 84, 34, 57, 7, 96].map((left, index) => (
          <View key={`${left}-${index}`} style={[styles.star, { left: `${left}%`, top: `${8 + ((index * 19) % 78)}%`, opacity: 0.2 + (index % 3) * 0.16 }]} />
        ))}
        <View style={styles.orbitArc} />
        <View style={[styles.accentGlow, { backgroundColor: ACCENT_GLOWS[scene?.accent] || ACCENT_GLOWS.gold }]} />
      </View>

      <View style={styles.brandRow}>
        <View style={styles.brandMark}><Text style={styles.brandMarkText}>AR</Text></View>
        <Text style={styles.brand}>ASTROROSHNI</Text>
        <View style={styles.liveChip}><Text style={styles.liveText}>{paused ? (isHindi ? 'रुका हुआ' : 'PAUSED') : (isHindi ? 'वीडियो पॉडकास्ट' : 'VISUAL PODCAST')}</Text></View>
      </View>
      <View style={styles.hostsRow}>
        <Host name={isHindi ? 'अनन्या' : 'ANANYA'} role={ananyaActive ? (isHindi ? 'बोल रही हैं' : 'SPEAKING') : (isHindi ? 'सुन रही हैं' : 'LISTENING')} active={ananyaActive} side="left" />
        <Host name={isHindi ? 'अर्जुन' : 'ARJUN'} role={arjunActive ? (isHindi ? 'बोल रहे हैं' : 'SPEAKING') : (isHindi ? 'सुन रहे हैं' : 'LISTENING')} active={arjunActive} side="right" />
      </View>

      <Animated.View style={[styles.sceneContent, activeCaption && styles.sceneContentCaptioned, { opacity: fade, transform: [{ translateX: shift }, { translateY: lift }, { scale }] }]}>
        {activeCaption ? (
          <View style={styles.sceneContextBadge}>
            <Text style={styles.sceneContextText}>{sceneLabel}</Text>
          </View>
        ) : null}
        <SceneArtwork scene={scene} chart={manifest?.chart} compact={compact} spin={spin} isHindi={isHindi} />
        {!activeCaption ? (
          <View style={styles.copyBlock}>
            <Text style={styles.eyebrow}>{sceneLabel}</Text>
            <Text numberOfLines={compact ? 2 : 3} ellipsizeMode="tail" adjustsFontSizeToFit minimumFontScale={0.68} style={[styles.headline, compact && styles.headlineCompact]}>{scene.headline}</Text>
            {!!scene.supporting_text && <Text numberOfLines={compact ? 2 : 3} ellipsizeMode="tail" style={[styles.supporting, compact && styles.supportingCompact]}>{scene.supporting_text}</Text>}
          </View>
        ) : null}
      </Animated.View>

      {activeCaption ? (
        <View style={styles.captionBox}>
          <Text style={[
            styles.captionSpeaker,
            normaliseSpeaker(activeCaption.speaker) === 'male' && styles.captionSpeakerMale,
          ]}>
            {normaliseSpeaker(activeCaption.speaker) === 'male'
              ? (isHindi ? 'अर्जुन' : 'ARJUN')
              : (isHindi ? 'अनन्या' : 'ANANYA')}
          </Text>
          <Text numberOfLines={2} ellipsizeMode="tail" style={[styles.captionText, compact && styles.captionTextCompact]}>
            {activeCaption.text}
          </Text>
        </View>
      ) : null}

      <View style={styles.sceneProgress}>
        {progressUnits.map((item, index) => {
          const start = Number(item.start_fraction || 0);
          const end = Math.max(start + 0.001, Number(item.end_fraction || 1));
          const fill = progress >= end ? 1 : progress <= start ? 0 : Math.max(0, Math.min(1, (progress - start) / (end - start)));
          return <View key={index} style={styles.sceneProgressItem}><View style={[styles.sceneProgressFill, { width: `${fill * 100}%` }]} /></View>;
        })}
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  stage: { width: '100%', height: 470, borderRadius: 22, overflow: 'hidden', paddingHorizontal: 16, paddingTop: 15, paddingBottom: 12 },
  stageCompact: { height: 380, paddingHorizontal: 13, paddingTop: 12, paddingBottom: 9 },
  stars: { ...StyleSheet.absoluteFillObject },
  star: { position: 'absolute', width: 2.5, height: 2.5, borderRadius: 2, backgroundColor: '#FFF1C8' },
  orbitArc: { position: 'absolute', width: 520, height: 230, borderRadius: 260, borderWidth: 1, borderColor: 'rgba(255,213,138,0.16)', left: -95, top: 100, transform: [{ rotate: '-11deg' }] },
  accentGlow: { position: 'absolute', width: 230, height: 230, borderRadius: 115, right: -95, top: 80 },
  brandRow: { flexDirection: 'row', alignItems: 'center', zIndex: 2 },
  brandMark: { width: 27, height: 27, borderRadius: 14, borderWidth: 1, borderColor: GOLD, alignItems: 'center', justifyContent: 'center' },
  brandMarkText: { color: CREAM, fontSize: 9, fontWeight: '900' },
  brand: { marginLeft: 8, color: CREAM, fontSize: 10, fontWeight: '900', letterSpacing: 2.1 },
  liveChip: { marginLeft: 'auto', paddingHorizontal: 8, paddingVertical: 5, borderRadius: 12, backgroundColor: 'rgba(29,2,47,0.4)', borderWidth: 1, borderColor: 'rgba(255,213,138,0.16)' },
  liveText: { color: '#FBE7D6', fontSize: 6.5, fontWeight: '900', letterSpacing: 0.75 },
  hostsRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 10, zIndex: 2 },
  host: { flexDirection: 'row', alignItems: 'center' },
  hostRight: { justifyContent: 'flex-end' },
  hostOrb: { width: 27, height: 27, borderRadius: 14, opacity: 0.42, marginRight: 7 },
  hostOrbActive: { opacity: 1, borderWidth: 2, borderColor: '#FFF1B8', transform: [{ scale: 1.14 }], shadowColor: '#FFD58A', shadowOpacity: 0.9, shadowRadius: 10, shadowOffset: { width: 0, height: 0 }, elevation: 8 },
  hostCopyRight: { alignItems: 'flex-end', marginRight: 7 },
  hostName: { color: CREAM, fontSize: 9, fontWeight: '900', letterSpacing: 1.1 },
  hostNameActive: { color: '#FFF8D8' },
  hostRole: { color: GOLD, fontSize: 6.5, fontWeight: '800', letterSpacing: 0.8, marginTop: 2 },
  hostRoleActive: { color: '#FFE49D' },
  hostMuted: { opacity: 0.36 },
  sceneContent: { flex: 1, justifyContent: 'space-between' },
  sceneContentCaptioned: { justifyContent: 'flex-start' },
  sceneContextBadge: { alignSelf: 'flex-start', marginTop: 7, marginBottom: 2, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 10, backgroundColor: 'rgba(31,2,47,0.38)', borderWidth: 1, borderColor: 'rgba(255,213,138,0.2)' },
  sceneContextText: { color: GOLD, fontSize: 7, fontWeight: '900', letterSpacing: 1.5 },
  orbitWrap: { height: 210, alignItems: 'center', justifyContent: 'center', marginTop: 1 },
  orbitWrapCompact: { height: 150, marginTop: -3 },
  sun: { position: 'absolute', width: 76, height: 76, borderRadius: 38, shadowColor: '#FFCA72', shadowOpacity: 0.75, shadowRadius: 18, shadowOffset: { width: 0, height: 0 } },
  sunCompact: { width: 58, height: 58, borderRadius: 29 },
  bookendWrap: { height: 210, marginTop: 1, alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  bookendWrapCompact: { height: 152, marginTop: -2 },
  bookendHalo: { position: 'absolute', width: 190, height: 190, borderRadius: 95, borderWidth: 1, borderColor: 'rgba(255,213,138,0.2)' },
  openingHalo: { backgroundColor: 'rgba(239,79,157,0.08)', shadowColor: '#FFB05E', shadowOpacity: 0.45, shadowRadius: 28, shadowOffset: { width: 0, height: 0 } },
  openingHosts: { width: 210, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  openingHostOrb: { width: 43, height: 43, borderRadius: 22, borderWidth: 1.5, borderColor: 'rgba(255,248,237,0.76)', shadowColor: '#FFD58A', shadowOpacity: 0.7, shadowRadius: 10, shadowOffset: { width: 0, height: 0 } },
  openingConnection: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginHorizontal: 5 },
  openingConnectionDot: { width: 4, height: 4, borderRadius: 2, backgroundColor: GOLD },
  openingConnectionLine: { flex: 1, height: 1, backgroundColor: 'rgba(255,213,138,0.6)' },
  openingMic: { width: 25, height: 25, borderRadius: 13, marginHorizontal: 5, borderWidth: 1, borderColor: GOLD, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(48,5,61,0.8)' },
  openingMicHead: { width: 7, height: 10, borderRadius: 4, borderWidth: 1.3, borderColor: CREAM },
  openingMicStem: { width: 1.3, height: 4, backgroundColor: CREAM },
  openingNames: { width: 210, flexDirection: 'row', justifyContent: 'space-between', marginTop: 5 },
  openingName: { width: 55, color: CREAM, fontSize: 7, fontWeight: '900', textAlign: 'center', letterSpacing: 0.9 },
  bookendKicker: { color: GOLD, fontSize: 7, fontWeight: '900', letterSpacing: 1.5, marginTop: 10 },
  bookendTitle: { color: CREAM, fontFamily: 'serif', fontSize: 27, lineHeight: 31, letterSpacing: 1.2, marginTop: 2 },
  bookendTitleCompact: { fontSize: 22, lineHeight: 25 },
  bookendSubtitle: { color: MUTED, fontSize: 6.5, fontWeight: '800', letterSpacing: 1.15, marginTop: 3 },
  closingHalo: { width: 164, height: 164, borderRadius: 82, backgroundColor: 'rgba(118,81,182,0.12)', borderColor: 'rgba(213,189,255,0.26)', shadowColor: '#D5BDFF', shadowOpacity: 0.35, shadowRadius: 30, shadowOffset: { width: 0, height: 0 } },
  closingMarkOuter: { width: 58, height: 58, borderRadius: 29, borderWidth: 1, borderColor: 'rgba(255,213,138,0.45)', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(42,4,57,0.5)' },
  closingMarkInner: { width: 42, height: 42, borderRadius: 21, borderWidth: 1.4, borderColor: GOLD, alignItems: 'center', justifyContent: 'center' },
  closingMarkText: { color: CREAM, fontFamily: 'serif', fontSize: 14, fontWeight: '800' },
  closingTitle: { color: CREAM, fontFamily: 'serif', fontSize: 24, lineHeight: 29, marginTop: 2 },
  closingTitleCompact: { fontSize: 20, lineHeight: 23 },
  closingHosts: { flexDirection: 'row', alignItems: 'center', marginTop: 6 },
  closingHostName: { color: MUTED, fontSize: 7, fontWeight: '900', letterSpacing: 1.1 },
  closingStar: { color: GOLD, fontSize: 9, marginHorizontal: 8 },
  hostExchangeWrap: { height: 210, marginTop: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around', paddingHorizontal: 8 },
  hostExchangeWrapCompact: { height: 152, marginTop: -2 },
  hostExchangePerson: { alignItems: 'center', width: 65 },
  hostExchangeOrb: { width: 58, height: 58, borderRadius: 29, borderWidth: 1.5, borderColor: 'rgba(255,248,237,0.72)', shadowColor: '#FFD58A', shadowOpacity: 0.52, shadowRadius: 12, shadowOffset: { width: 0, height: 0 } },
  hostExchangeName: { color: CREAM, fontSize: 7.5, fontWeight: '900', letterSpacing: 1, marginTop: 8 },
  hostExchangeSignal: { width: 105, height: 74, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5, borderTopWidth: 1, borderBottomWidth: 1, borderColor: 'rgba(255,213,138,0.24)' },
  hostExchangeBar: { width: 3, borderRadius: 2, backgroundColor: GOLD, opacity: 0.82 },
  hostExchangeLabel: { position: 'absolute', bottom: -15, color: MUTED, fontSize: 5.5, fontWeight: '900', letterSpacing: 1.1 },
  chartWrap: { height: 214, marginTop: 0 },
  chartWrapCompact: { height: 158, marginTop: -2 },
  chartIdentity: { position: 'absolute', zIndex: 2, left: 24, top: 15, paddingHorizontal: 7, paddingVertical: 3, borderRadius: 8, backgroundColor: 'rgba(38,3,54,0.82)', borderWidth: 1, borderColor: 'rgba(255,213,138,0.42)' },
  chartIdentityText: { color: GOLD, fontSize: 6.5, fontWeight: '900', letterSpacing: 0.9 },
  ashtakavargaWrap: { height: 210, marginTop: 1, paddingHorizontal: 2 },
  ashtakavargaWrapCompact: { height: 152, marginTop: -2 },
  ashtakavargaHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 5 },
  ashtakavargaTitle: { color: GOLD, fontSize: 8, fontWeight: '900', letterSpacing: 1.25 },
  ashtakavargaPlanet: { color: '#E4C7FF', fontSize: 7, fontWeight: '900', letterSpacing: 1 },
  ashtakavargaGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: 4 },
  ashtakavargaCell: { width: '24%', minHeight: 43, borderRadius: 8, borderWidth: 1, borderColor: 'rgba(255,213,138,0.22)', backgroundColor: 'rgba(35,3,53,0.48)', alignItems: 'center', justifyContent: 'center', paddingVertical: 3 },
  ashtakavargaCellStrong: { borderColor: 'rgba(139,255,190,0.68)', backgroundColor: 'rgba(35,128,91,0.2)' },
  ashtakavargaCellWeak: { borderColor: 'rgba(255,156,128,0.55)', backgroundColor: 'rgba(157,52,66,0.18)' },
  ashtakavargaCellActive: { borderWidth: 2, borderColor: GOLD, backgroundColor: 'rgba(255,174,82,0.2)' },
  ashtakavargaHouse: { color: '#DCC5D6', fontSize: 6.5, fontWeight: '800' },
  ashtakavargaSav: { color: CREAM, fontSize: 14, lineHeight: 16, fontWeight: '900' },
  ashtakavargaBav: { color: '#E4C7FF', fontSize: 6, fontWeight: '800' },
  activationWrap: { height: 210, marginTop: 1, paddingHorizontal: 2 },
  activationWrapCompact: { height: 152, marginTop: -2 },
  activationLegend: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 9, marginBottom: 6 },
  activationLegendItem: { flexDirection: 'row', alignItems: 'center' },
  activationLegendDot: { width: 6, height: 6, borderRadius: 3, marginRight: 3, shadowOpacity: 0.8, shadowRadius: 4, shadowOffset: { width: 0, height: 0 } },
  activationLegendText: { color: '#EBD9E4', fontSize: 5.5, fontWeight: '900', letterSpacing: 0.45 },
  activationGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: 4 },
  activationHouse: { width: '24%', minHeight: 43, borderRadius: 10, borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)', backgroundColor: 'rgba(30,2,47,0.42)', alignItems: 'center', justifyContent: 'center', paddingVertical: 3 },
  activationHouseActive: { borderColor: 'rgba(255,213,138,0.5)', backgroundColor: 'rgba(72,18,83,0.7)', shadowColor: '#D8A5FF', shadowOpacity: 0.36, shadowRadius: 7, shadowOffset: { width: 0, height: 0 }, elevation: 3 },
  activationHousePeak: { borderColor: '#FFF0AA', backgroundColor: 'rgba(118,49,92,0.82)', shadowColor: '#FFD166', shadowOpacity: 0.72, shadowRadius: 10, elevation: 6 },
  activationHouseLabel: { color: '#BFAABD', fontSize: 5.2, fontWeight: '800', letterSpacing: 0.35 },
  activationHouseNumber: { color: '#806B7C', fontFamily: 'serif', fontSize: 13, lineHeight: 14, fontWeight: '700' },
  activationHouseNumberActive: { color: CREAM },
  activationDots: { flexDirection: 'row', gap: 3, marginTop: 1 },
  activationDot: { width: 4.5, height: 4.5, borderRadius: 3, shadowOffset: { width: 0, height: 0 } },
  activationSav: { color: '#BFAFC0', fontSize: 4.8, fontWeight: '700', marginTop: 1 },
  timeline: { height: 205, marginTop: 3, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 2 },
  timelineCompact: { height: 150, marginTop: -2 },
  timelineLine: { position: 'absolute', left: 17, right: 17, top: '48%', height: 2 },
  timelinePointWrap: { width: '31%', alignItems: 'center', zIndex: 1 },
  timelinePoint: { width: 27, height: 27, borderRadius: 14, borderWidth: 1.6, borderColor: GOLD, backgroundColor: '#4A155A', alignItems: 'center', justifyContent: 'center' },
  timelinePointActive: { backgroundColor: '#FFAD57', shadowColor: '#FFD58A', shadowOpacity: 0.8, shadowRadius: 9, shadowOffset: { width: 0, height: 0 } },
  timelinePointCore: { width: 6, height: 6, borderRadius: 3, backgroundColor: CREAM },
  timelineLabel: { color: CREAM, fontSize: 8.5, fontWeight: '800', textAlign: 'center', marginTop: 10, letterSpacing: 0.5 },
  dashaWrap: { height: 205, marginTop: 3, paddingHorizontal: 5, justifyContent: 'center' },
  dashaWrapCompact: { height: 150, marginTop: -2 },
  dashaChain: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginBottom: 11 },
  dashaChip: { minWidth: 61, paddingHorizontal: 7, paddingVertical: 5, borderRadius: 9, borderWidth: 1, borderColor: 'rgba(255,213,138,0.3)', backgroundColor: 'rgba(42,4,57,0.55)', alignItems: 'center' },
  dashaChipActive: { borderColor: GOLD, backgroundColor: 'rgba(255,174,82,0.17)' },
  dashaLevel: { color: '#D7BDD1', fontSize: 5.5, fontWeight: '800', letterSpacing: 0.65 },
  dashaPlanet: { color: CREAM, fontSize: 9, fontWeight: '900', marginTop: 2, letterSpacing: 0.5 },
  dashaArrow: { color: GOLD, fontSize: 16, marginHorizontal: 3 },
  dashaBand: { marginBottom: 8 },
  dashaBandNested: { marginHorizontal: 18 },
  dashaBandLabels: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 3 },
  dashaBandName: { color: CREAM, fontSize: 6.5, fontWeight: '900', letterSpacing: 0.55 },
  dashaDates: { color: '#D9C4D3', fontSize: 5.8, fontWeight: '700' },
  dashaTrack: { height: 8, borderRadius: 5, backgroundColor: 'rgba(27,2,43,0.62)', borderWidth: 1, borderColor: 'rgba(255,213,138,0.16)' },
  dashaFill: { height: '100%', minWidth: 4, borderRadius: 4 },
  dashaNow: { position: 'absolute', top: -3, width: 2, height: 12, borderRadius: 1, backgroundColor: CREAM, shadowColor: '#FFF4C2', shadowOpacity: 0.9, shadowRadius: 4, shadowOffset: { width: 0, height: 0 } },
  mahaSequence: { flexDirection: 'row', justifyContent: 'center', marginTop: 2, gap: 4 },
  mahaPeriod: { minWidth: 39, paddingVertical: 4, borderRadius: 7, borderWidth: 1, borderColor: 'rgba(255,213,138,0.18)', alignItems: 'center', backgroundColor: 'rgba(32,3,49,0.4)' },
  mahaPeriodActive: { borderColor: GOLD, backgroundColor: 'rgba(255,174,82,0.16)' },
  mahaPlanet: { color: '#D4BDCE', fontSize: 7, fontWeight: '900' },
  mahaPlanetActive: { color: GOLD },
  mahaYear: { color: '#BFA7BA', fontSize: 5.5, marginTop: 1 },
  steps: { height: 205, marginTop: 3, flexDirection: 'row', alignItems: 'center', gap: 7 },
  stepsCompact: { height: 150, marginTop: -2, gap: 5 },
  stepCard: { flex: 1, minHeight: 112, borderWidth: 1, borderColor: 'rgba(255,213,138,0.22)', borderRadius: 13, backgroundColor: 'rgba(33,3,51,0.24)', padding: 9, justifyContent: 'center' },
  stepCardActive: { borderColor: GOLD, backgroundColor: 'rgba(255,174,82,0.09)' },
  stepNumber: { color: GOLD, fontFamily: 'serif', fontSize: 22, lineHeight: 25 },
  stepText: { color: CREAM, fontSize: 8.5, fontWeight: '800', lineHeight: 12, marginTop: 10, letterSpacing: 0.5 },
  symbolVisual: { height: 205, marginTop: 3, alignItems: 'center', justifyContent: 'center' },
  symbolVisualCompact: { height: 150, marginTop: -2 },
  zodiacCore: { position: 'absolute', width: 72, height: 72, borderRadius: 36, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(45,5,61,0.78)', borderWidth: 1, borderColor: 'rgba(255,213,138,0.5)' },
  zodiacGlyph: { color: GOLD, fontSize: 25, lineHeight: 30 },
  zodiacCoreLabel: { color: CREAM, fontSize: 7, fontWeight: '900', letterSpacing: 1, marginTop: 1 },
  balanceWrap: { height: 205, marginTop: 3, alignItems: 'center', justifyContent: 'center' },
  balanceWrapCompact: { height: 150, marginTop: -2 },
  balanceBeam: { position: 'absolute', width: '72%', height: 2, backgroundColor: GOLD, top: '48%', transform: [{ rotate: '-4deg' }] },
  balancePivot: { position: 'absolute', width: 44, height: 44, borderRadius: 22, backgroundColor: '#481252', borderWidth: 1, borderColor: GOLD, alignItems: 'center', justifyContent: 'center', top: '39%' },
  balancePivotText: { color: GOLD, fontSize: 19 },
  balanceSide: { position: 'absolute', width: 96, alignItems: 'center', top: '27%' },
  balanceLeft: { left: 18 },
  balanceRight: { right: 18, top: '36%' },
  balanceOrb: { width: 58, height: 58, borderRadius: 29, shadowColor: '#FFD58A', shadowOpacity: 0.6, shadowRadius: 11, shadowOffset: { width: 0, height: 0 } },
  balanceLabel: { color: CREAM, textAlign: 'center', fontSize: 8, fontWeight: '900', letterSpacing: 0.8, marginTop: 8 },
  statementWrap: { height: 205, marginTop: 3, paddingHorizontal: 22, justifyContent: 'center' },
  statementWrapCompact: { height: 150, marginTop: -2, paddingHorizontal: 15 },
  statementMark: { color: GOLD, fontFamily: 'serif', fontSize: 54, lineHeight: 48 },
  statementRule: { width: 48, height: 2, backgroundColor: '#FFAD57', marginVertical: 7 },
  statementText: { color: CREAM, fontFamily: 'serif', fontSize: 21, lineHeight: 25 },
  statementWarning: { color: '#FFE0BF' },
  statementTag: { color: GOLD, fontSize: 7, fontWeight: '900', letterSpacing: 1.6, marginTop: 10 },
  decisionWrap: { height: 205, marginTop: 3, alignItems: 'center', justifyContent: 'center' },
  decisionWrapCompact: { height: 150, marginTop: -2 },
  decisionOrigin: { width: 48, height: 48, borderRadius: 24, backgroundColor: '#FFAD57', alignItems: 'center', justifyContent: 'center', zIndex: 2 },
  decisionOriginText: { color: '#35103E', fontSize: 8, fontWeight: '900', letterSpacing: 1 },
  decisionStem: { width: 2, height: 34, backgroundColor: GOLD },
  decisionPaths: { width: '100%', flexDirection: 'row', justifyContent: 'space-around' },
  decisionNode: { width: '29%', minHeight: 45, borderRadius: 13, borderWidth: 1, borderColor: 'rgba(255,213,138,0.35)', backgroundColor: 'rgba(38,3,54,0.48)', alignItems: 'center', justifyContent: 'center', padding: 7 },
  decisionNodeActive: { borderColor: GOLD, backgroundColor: 'rgba(255,174,82,0.14)' },
  decisionNodeText: { color: CREAM, textAlign: 'center', fontSize: 7.5, fontWeight: '900', lineHeight: 10 },
  comparisonWrap: { height: 205, marginTop: 3, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  comparisonWrapCompact: { height: 150, marginTop: -2 },
  comparisonSide: { width: '47%', height: '88%', alignItems: 'center' },
  comparisonLabel: { color: CREAM, fontSize: 8, fontWeight: '900', letterSpacing: 1.2, marginTop: -5 },
  comparisonVs: { position: 'absolute', left: '46%', top: '40%', width: 30, height: 30, borderRadius: 15, backgroundColor: '#4C1552', borderWidth: 1, borderColor: GOLD, alignItems: 'center', justifyContent: 'center' },
  comparisonVsText: { color: GOLD, fontSize: 18, lineHeight: 20 },
  topicCards: { height: 205, marginTop: 3, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5 },
  topicCardsCompact: { height: 150, marginTop: -2 },
  topicCard: { width: '30%', minHeight: 125, borderRadius: 15, borderWidth: 1, borderColor: 'rgba(255,213,138,0.45)', backgroundColor: 'rgba(39,3,54,0.5)', alignItems: 'center', justifyContent: 'center', padding: 7 },
  topicSymbol: { color: GOLD, fontSize: 26, lineHeight: 30 },
  topicLabel: { color: CREAM, textAlign: 'center', fontSize: 7.5, fontWeight: '900', lineHeight: 10, letterSpacing: 0.7, marginTop: 10 },
  copyBlock: { paddingHorizontal: 4, paddingBottom: 4 },
  eyebrow: { color: GOLD, fontSize: 8, fontWeight: '900', letterSpacing: 2.3 },
  headline: { color: CREAM, fontFamily: 'serif', fontSize: 29, lineHeight: 32, marginTop: 5 },
  headlineCompact: { fontSize: 23, lineHeight: 26, marginTop: 3 },
  supporting: { color: MUTED, fontSize: 11.5, lineHeight: 16, marginTop: 5 },
  supportingCompact: { fontSize: 9.5, lineHeight: 13, marginTop: 3 },
  captionBox: { minHeight: 54, marginTop: 5, marginHorizontal: 2, paddingHorizontal: 14, paddingVertical: 7, borderRadius: 13, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(24,2,37,0.7)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.13)' },
  captionSpeaker: { color: '#FFD58A', fontSize: 7, fontWeight: '900', letterSpacing: 1.25, marginBottom: 2, textAlign: 'center' },
  captionSpeakerMale: { color: '#D8BEFF' },
  captionText: { color: '#FFF8F0', fontSize: 15, lineHeight: 20, fontWeight: '700', textAlign: 'center' },
  captionTextCompact: { fontSize: 12.5, lineHeight: 17 },
  sceneProgress: { height: 3, flexDirection: 'row', gap: 4, marginTop: 5 },
  sceneProgressItem: { flex: 1, height: 2.5, borderRadius: 2, overflow: 'hidden', backgroundColor: 'rgba(255,255,255,0.2)' },
  sceneProgressFill: { height: '100%', borderRadius: 2, backgroundColor: GOLD },
});
