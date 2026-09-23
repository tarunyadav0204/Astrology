import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, Animated, Easing, Platform } from 'react-native';
import Svg, { Circle, Rect, Text as SvgText, G, Line, ClipPath, Defs } from 'react-native-svg';
import { dashaLevelSuffix, dashaPaint, labelBox, placeCircleClear, placeTransitLabels, signPointAt, textHalfWidth, transitBav } from './NorthIndianChart';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';

const AnimatedG = Animated.createAnimatedComponent(G);

const SouthIndianChart = ({
  chartData,
  chartType,
  showDegreeNakshatra = true,
  rotatedAscendant = null,
  onRotate,
  cosmicTheme = false,
  showKarakas = false,
  karakas = null,
  size = null, // PWA/web: explicit pixel square (avoids % SVG collapse)
  transitOverlay = null,
  dashaHighlight = null,
  signPoints = null,
  bavBySign = null,
  onTransitPlanetPress = null,
  onHousePress = null,
}) => {
  const [contextMenu, setContextMenu] = useState({ show: false, rashiIndex: null, signName: null });
  const { t } = useTranslation();
  const { theme, colors } = useTheme();

  const lastDataRef = useRef(null);

  useEffect(() => {
    if (!chartData) return;

    // Deep compare chartData to prevent unnecessary animation resets
    const dataString = JSON.stringify({
      planets: chartData.planets,
      houses: chartData.houses,
      chartType,
      rotatedAscendant
    });

    if (lastDataRef.current === dataString) {
      return;
    }
    lastDataRef.current = dataString;
  }, [chartData, chartType, rotatedAscendant]);
  const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

  // Fixed sign positions in South Indian chart
  const gridPositions = [
    { x: 0, y: 0, width: 85, height: 85, sign: 11 },     // Pisces
    { x: 85, y: 0, width: 85, height: 85, sign: 0 },     // Aries
    { x: 170, y: 0, width: 85, height: 85, sign: 1 },    // Taurus
    { x: 255, y: 0, width: 85, height: 85, sign: 2 },    // Gemini
    { x: 0, y: 85, width: 85, height: 85, sign: 10 },    // Aquarius
    { x: 255, y: 85, width: 85, height: 85, sign: 3 },   // Cancer
    { x: 0, y: 170, width: 85, height: 85, sign: 9 },    // Capricorn
    { x: 255, y: 170, width: 85, height: 85, sign: 4 },  // Leo
    { x: 0, y: 255, width: 85, height: 85, sign: 8 },    // Sagittarius
    { x: 85, y: 255, width: 85, height: 85, sign: 7 },   // Scorpio
    { x: 170, y: 255, width: 85, height: 85, sign: 6 },  // Libra
    { x: 255, y: 255, width: 85, height: 85, sign: 5 }   // Virgo
  ];

  const getNakshatra = (longitude) => {
    const nakshatras = [
      'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
      'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
      'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
      'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
      'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
    ];
    const nakshatraIndex = Math.floor(longitude / 13.333333);
    return nakshatras[nakshatraIndex] || 'Unknown';
  };

  const getShortNakshatra = (longitude) => {
    const shortNakshatras = [
      'Ash', 'Bha', 'Kri', 'Roh', 'Mri', 'Ard',
      'Pun', 'Pus', 'Asl', 'Mag', 'PPh', 'UPh',
      'Has', 'Chi', 'Swa', 'Vis', 'Anu', 'Jye',
      'Mul', 'PAs', 'UAs', 'Shr', 'Dha', 'Sha',
      'PBh', 'UBh', 'Rev'
    ];
    const nakshatraIndex = Math.floor(longitude / 13.333333);
    return shortNakshatras[nakshatraIndex] || 'Unk';
  };

  const getNakshatraPada = (longitude) => {
    const lon = typeof longitude === 'number' && !Number.isNaN(longitude) ? longitude : 0;
    const degreeInNakshatra = lon % 13.333333;
    return Math.floor(degreeInNakshatra / 3.333333) + 1;
  };

  const formatDegree = (degree) => {
    if (typeof degree !== 'number' || Number.isNaN(degree)) return '0°';
    return `${Math.round(degree)}°`;
  };

  const formatDegreeFull = (degree) => {
    if (typeof degree !== 'number' || Number.isNaN(degree)) return '0.0000°';
    return degree.toFixed(4) + '°';
  };

  const getPlanetStatus = (planetName, signIndex) => {
    if (!chartData || !chartData.planets) return 'normal';
    if (['Rahu', 'Ketu', 'Gulika', 'Mandi', 'InduLagna'].includes(planetName)) return 'normal';
    const dignitySign = chartData?._place_by_house === true
      ? chartData.planets?.[planetName]?.sign
      : signIndex;
    const exaltationSigns = { Sun: 0, Moon: 1, Mars: 9, Mercury: 5, Jupiter: 3, Venus: 11, Saturn: 6 };
    const debilitationSigns = { Sun: 6, Moon: 7, Mars: 3, Mercury: 11, Jupiter: 9, Venus: 5, Saturn: 0 };
    if (exaltationSigns[planetName] === dignitySign) return 'exalted';
    if (debilitationSigns[planetName] === dignitySign) return 'debilitated';
    return 'normal';
  };

  const getPlanetColor = (planetName, signIndex) => {
    const status = getPlanetStatus(planetName, signIndex);
    if (status === 'exalted') return '#22c55e';      // green
    if (status === 'debilitated') return '#ef4444';  // red
    // Normal planets: theme-aware
    return cosmicTheme ? colors.chartText : (theme === 'dark' ? (colors.text || '#ffffff') : '#333');
  };

  const getPlanetsInSign = (signIndex) => {
    if (!chartData || !chartData.planets || signIndex === -1) return [];
    const planetsInSign = [];
    const useHousePlacement = chartData?._place_by_house === true;
    const houseForSign = getHouseNumber(signIndex);

    // Add regular planets (exclude InduLagna as it's handled separately)
    Object.entries(chartData.planets)
      .filter(([name, data]) => (
        name !== 'InduLagna'
        && (useHousePlacement && typeof data?.house === 'number'
          ? data.house === houseForSign
          : data?.sign === signIndex)
      ))
      .forEach(([name, data]) => {
        let symbol = t(`planets.${name}`, name.substring(0, 2));

        // Add Karaka abbreviation if showKarakas is true
        if (showKarakas && karakas && typeof karakas === 'object') {
          const karaka = Object.entries(karakas).find(([_, karakaData]) => karakaData?.planet === name);
          if (karaka) {
            const karakaAbbr = {
              'Atmakaraka': 'AK',
              'Amatyakaraka': 'AmK',
              'Bhratrukaraka': 'BK',
              'Matrukaraka': 'MK',
              'Putrakaraka': 'PK',
              'Gnatikaraka': 'GK',
              'Darakaraka': 'DK'
            }[karaka[0]];
            if (karakaAbbr) symbol += `(${karakaAbbr})`;
          }
        }

        const status = getPlanetStatus(name, signIndex);
        if (status === 'exalted') symbol += '↑';
        if (status === 'debilitated') symbol += '↓';

        planetsInSign.push({
          symbol: symbol,
          name: name,
          degree: typeof data.degree === 'number' ? data.degree : 0,
          longitude: data.longitude || 0,
          retrograde: !!data.retrograde,
          nakshatra: getNakshatra(data.longitude || 0),
          shortNakshatra: getShortNakshatra(data.longitude || 0),
          pada: getNakshatraPada(data.longitude || 0),
          formattedDegree: formatDegree(data.degree ?? 0),
          formattedDegreeFull: formatDegreeFull(data.degree ?? 0)
        });
      });

    // Add InduLagna if it's in this sign
    if (
      chartData.planets?.InduLagna
      && (useHousePlacement && typeof chartData.planets.InduLagna.house === 'number'
        ? chartData.planets.InduLagna.house === houseForSign
        : chartData.planets.InduLagna.sign === signIndex)
    ) {
      planetsInSign.push({
        symbol: t('planets.InduLagna', 'IL'),
        name: 'InduLagna',
        degree: typeof chartData.planets.InduLagna.degree === 'number' ? chartData.planets.InduLagna.degree : 0,
        longitude: chartData.planets.InduLagna.longitude || 0,
        retrograde: !!chartData.planets.InduLagna.retrograde,
        nakshatra: getNakshatra(chartData.planets.InduLagna.longitude || 0),
        shortNakshatra: getShortNakshatra(chartData.planets.InduLagna.longitude || 0),
        pada: getNakshatraPada(chartData.planets.InduLagna.longitude || 0),
        formattedDegree: formatDegree(chartData.planets.InduLagna.degree ?? 0),
        formattedDegreeFull: formatDegreeFull(chartData.planets.InduLagna.degree ?? 0)
      });
    }

    return planetsInSign;
  };

  const getTransitPlanetsInSign = (signIndex) => {
    const planets = transitOverlay?.planets;
    if (!planets || signIndex === -1) return [];
    const names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
    return names.flatMap((name) => {
      const data = planets[name];
      if (!data || data.sign !== signIndex) return [];
      const retrograde = !!data.retrograde && name !== 'Rahu' && name !== 'Ketu';
      return [{
        symbol: t(`planets.${name}`, name.substring(0, 2)),
        name,
        retrograde,
        bav: transitBav(bavBySign, name, data.sign),
        shortNakshatra: getShortNakshatra(data.longitude || 0),
        formattedDegree: formatDegree(data.degree ?? 0),
      }];
    });
  };

  const getHouseNumber = (signIndex) => {
    if (!chartData.houses || signIndex === -1) return '';

    if (rotatedAscendant !== null) {
      const offset = (signIndex - rotatedAscendant + 12) % 12;
      return offset + 1;
    }

    for (let i = 0; i < chartData.houses.length; i++) {
      if (chartData.houses[i].sign === signIndex) {
        return i + 1;
      }
    }
    return '';
  };

  const southPlanetSlot = (pos, index, count, houseNum) => {
    const top = pos.y + 19;
    const bottom = pos.y + pos.height - (houseNum === 1 ? 24 : 4);
    const slot = Math.max(9, (bottom - top) / Math.max(count, 1));
    const degreesFit = showDegreeNakshatra && slot >= 17;
    const symbolFont = Math.max(
      7,
      Math.min(showKarakas ? 10 : 12, Math.floor(degreesFit ? slot * 0.46 : slot * 0.7)),
    );
    const symbolY = top + index * slot + Math.min(symbolFont * 0.85, slot * (degreesFit ? 0.4 : 0.62));
    const degreeY = top + (index + 1) * slot - 2;
    return { symbolY, degreeY, symbolFont, degreeFont: 7, degreesFit };
  };

  const handleCellPress = (signIndex) => {
    const houseNumber = getHouseNumber(signIndex);
    if (onHousePress && typeof houseNumber === 'number') {
      onHousePress({
        houseNum: houseNumber,
        rashiIndex: signIndex,
        signName: rashiNames[signIndex],
        planets: getPlanetsInSign(signIndex),
        chartData,
      });
      return;
    }
    setContextMenu({ show: true, rashiIndex: signIndex, signName: rashiNames[signIndex] });
  };

  return (
    <View
      style={[
        styles.container,
        size ? { width: size, height: size, alignSelf: 'center' } : null,
      ]}
    >
      <Svg
        viewBox="0 0 340 340"
        width={size || '100%'}
        height={size || '100%'}
        overflow="visible"
        preserveAspectRatio="xMidYMid meet"
        style={[styles.svg, size ? { width: size, height: size } : null]}
      >
        <Defs>
          <ClipPath id="southChartClip">
            <Rect
              x="0" y="0" width="340" height="340"
              rx={cosmicTheme ? "16" : "0"}
              ry={cosmicTheme ? "16" : "0"}
            />
          </ClipPath>
        </Defs>

        <Rect
          x="1.5" y="1.5" width="337" height="337"
          fill="none"
          stroke={cosmicTheme
            ? (colors.chartLineStrong || colors.chartLine || '#334155')
            : theme === 'dark'
              ? (colors.cardBorder || 'rgba(148, 163, 184, 0.8)')
              : '#ff6f00'}
          strokeWidth={cosmicTheme ? 2.5 : 3}
          rx="0"
          ry="0"
        />

        <G clipPath="url(#southChartClip)" pointerEvents="none">
          {/* Grid lines */}
          {[
            { x1: 85, y1: 0, x2: 85, y2: 85 },
            { x1: 170, y1: 0, x2: 170, y2: 85 },
            { x1: 255, y1: 0, x2: 255, y2: 85 },
            { x1: 85, y1: 255, x2: 85, y2: 340 },
            { x1: 170, y1: 255, x2: 170, y2: 340 },
            { x1: 255, y1: 255, x2: 255, y2: 340 },
            { x1: 0, y1: 85, x2: 85, y2: 85 },
            { x1: 0, y1: 170, x2: 85, y2: 170 },
            { x1: 0, y1: 255, x2: 85, y2: 255 },
            { x1: 255, y1: 85, x2: 340, y2: 85 },
            { x1: 255, y1: 170, x2: 340, y2: 170 },
            { x1: 255, y1: 255, x2: 340, y2: 255 },
          ].map((p, idx) => (
            <Line
              key={idx}
              x1={p.x1}
              y1={p.y1}
              x2={p.x2}
              y2={p.y2}
              stroke={
                cosmicTheme
                  ? colors.chartLine
                  : theme === 'dark'
                    ? 'rgba(148, 163, 184, 0.6)'
                    : "#ff8a65"
              }
              strokeWidth={cosmicTheme ? "1" : "2"}
            />
          ))}
          <Line
            x1="0" y1="85" x2="340" y2="85"
            stroke={
              cosmicTheme
                ? colors.chartLine
                : theme === 'dark'
                  ? (colors.cardBorder || 'rgba(148, 163, 184, 0.9)')
                  : "#ff6f00"
            }
            strokeWidth={cosmicTheme ? "1.5" : "3"}
          />
          <Line
            x1="0" y1="255" x2="340" y2="255"
            stroke={
              cosmicTheme
                ? colors.chartLine
                : theme === 'dark'
                  ? (colors.cardBorder || 'rgba(148, 163, 184, 0.9)')
                  : "#ff6f00"
            }
            strokeWidth={cosmicTheme ? "1.5" : "3"}
          />
          <Line
            x1="85" y1="0" x2="85" y2="340"
            stroke={
              cosmicTheme
                ? colors.chartLine
                : theme === 'dark'
                  ? (colors.cardBorder || 'rgba(148, 163, 184, 0.9)')
                  : "#ff6f00"
            }
            strokeWidth={cosmicTheme ? "1.5" : "3"}
          />
          <Line
            x1="255" y1="0" x2="255" y2="340"
            stroke={
              cosmicTheme
                ? colors.chartLine
                : theme === 'dark'
                  ? (colors.cardBorder || 'rgba(148, 163, 184, 0.9)')
                  : "#ff6f00"
            }
            strokeWidth={cosmicTheme ? "1.5" : "3"}
          />
        </G>

        {/* Grid cells */}
        {gridPositions.map((pos, index) => {
          const planetsInSign = getPlanetsInSign(pos.sign);
          const houseNumber = getHouseNumber(pos.sign);

          return (
            <G key={index}>
              {/* Hit area for the entire cell */}
              <Rect
                x={pos.x} y={pos.y} width={pos.width} height={pos.height}
                fill="transparent"
                onPress={() => handleCellPress(pos.sign)}
              />

              {/* House number */}
              <SvgText
                x={pos.x + 8}
                y={pos.y + 18}
                fontSize="12"
                fill={
                  houseNumber === 1
                    ? (cosmicTheme ? colors.primary : (theme === 'dark' ? (colors.primary || '#e91e63') : '#e91e63'))
                    : (cosmicTheme ? colors.chartTextMuted : (theme === 'dark' ? (colors.text || '#e5e7eb') : '#333'))
                }
                fontWeight={houseNumber === 1 ? "900" : "bold"}
                pointerEvents="none">
                {houseNumber}
              </SvgText>

              {(() => {
                if (signPointAt(signPoints, pos.sign) == null) return null;
                const cellPolygon = [
                  [pos.x + 2, pos.y + 2],
                  [pos.x + pos.width - 2, pos.y + 2],
                  [pos.x + pos.width - 2, pos.y + pos.height - 2],
                  [pos.x + 2, pos.y + pos.height - 2],
                ];
                const occupied = planetsInSign.map((planet, pIndex) => {
                  const slot = southPlanetSlot(pos, pIndex, planetsInSign.length, houseNumber);
                  const dashaTag = dashaLevelSuffix(planet.name, dashaHighlight);
                  const symbolFont = slot.symbolFont;
                  const tagFont = Math.max(6, Math.round(symbolFont * 0.42));
                  const symbolHalf = textHalfWidth(planet.symbol, symbolFont);
                  const tagExtra = dashaTag ? textHalfWidth(dashaTag, tagFont) + 2 : 0;
                  const degreeHalf = slot.degreesFit
                    ? textHalfWidth(`${planet.formattedDegree} ${planet.shortNakshatra}`, slot.degreeFont)
                    : 0;
                  const half = Math.max(symbolHalf + tagExtra, degreeHalf) + 4;
                  const above = Math.ceil(symbolFont * 0.95) + (dashaTag ? tagFont : 1);
                  const below = slot.degreesFit ? Math.max(4, slot.degreeY - slot.symbolY + 3) : 3;
                  return labelBox(pos.x + pos.width / 2, slot.symbolY, half, above, below);
                });
                const houseLabel = String(houseNumber || '');
                if (houseLabel) {
                  const houseHalf = textHalfWidth(houseLabel, 12) + 2;
                  occupied.push(labelBox(pos.x + 8 + houseHalf, pos.y + 14, houseHalf, 12, 5));
                }
                if (houseNumber === 1) {
                  occupied.push(labelBox(
                    pos.x + pos.width - 22,
                    pos.y + pos.height - 18,
                    22,
                    14,
                    showDegreeNakshatra ? 16 : 8,
                  ));
                }
                const savSpot = placeCircleClear(cellPolygon, occupied, 11);
                if (!savSpot) return null;
                return (
                  <G pointerEvents="none">
                    <Circle
                      cx={savSpot.x}
                      cy={savSpot.y}
                      r={savSpot.radius}
                      fill={cosmicTheme ? colors.chartSurface : (theme === 'dark' ? '#111827' : '#ffffff')}
                      stroke={cosmicTheme ? (colors.chartLineStrong || colors.chartLine) : (theme === 'dark' ? '#94a3b8' : '#e91e63')}
                      strokeWidth="1.25"
                    />
                    <SvgText
                      x={savSpot.x}
                      y={savSpot.y + 4}
                      fontSize="11"
                      fill={cosmicTheme ? colors.chartText : (theme === 'dark' ? '#fff' : '#333')}
                      fontWeight="700"
                      textAnchor="middle"
                    >
                      {signPointAt(signPoints, pos.sign)}
                    </SvgText>
                  </G>
                );
              })()}

              {/* Ascendant marker for house 1 */}
              {houseNumber === 1 && (
                <G>
                  <SvgText
                    x={pos.x + pos.width - 8}
                    y={pos.y + pos.height - 20}
                    fontSize="9"
                    fill={cosmicTheme ? colors.primary : "#e91e63"}
                    fontWeight="900"
                    textAnchor="end">
                    ASC
                  </SvgText>
                  {(chartData?.ascendant ?? null) != null && (
                    <SvgText
                      x={pos.x + pos.width - 8}
                      y={pos.y + pos.height - 8}
                      fontSize="7"
                      fill={cosmicTheme ? colors.chartTextMuted : "#666"}
                      fontWeight="500"
                      textAnchor="end">
                      {formatDegree(chartData.ascendant % 30)} {getShortNakshatra(chartData.ascendant)}
                    </SvgText>
                  )}
                </G>
              )}

              {/* Planets */}
              {planetsInSign.map((planet, pIndex) => {
                const slot = southPlanetSlot(pos, pIndex, planetsInSign.length, houseNumber);
                const dashaTag = dashaLevelSuffix(planet.name, dashaHighlight);
                const planetFont = slot.symbolFont + (dashaTag && planetsInSign.length < 3 ? 2 : 0);
                const symbolX = pos.x + pos.width / 2;
                const symbolY = slot.symbolY;
                const paint = dashaTag ? dashaPaint(colors) : null;
                return (
                <G key={pIndex}>
                  <SvgText
                    x={symbolX}
                    y={symbolY}
                    fontSize={planetFont}
                    fill={paint ? paint.fill : getPlanetColor(planet.name, pos.sign)}
                    fontWeight="bold"
                    textAnchor="middle"
                    onPress={chartType === 'transit' && onTransitPlanetPress && bavBySign?.[planet.name]
                      ? () => onTransitPlanetPress(planet.name)
                      : undefined}
                  >
                    {planet.symbol}
                  </SvgText>
                  {chartType === 'transit' && transitBav(bavBySign, planet.name, pos.sign) != null ? (
                    <SvgText
                      x={symbolX + textHalfWidth(planet.symbol, planetFont) + 2}
                      y={symbolY}
                      fontSize={Math.max(7, Math.round(planetFont * 0.62))}
                      fill={cosmicTheme ? colors.chartTextMuted : (theme === 'dark' ? '#cbd5e1' : '#666')}
                      fontWeight="700"
                      textAnchor="start"
                      pointerEvents="none"
                    >
                      {transitBav(bavBySign, planet.name, pos.sign)}
                    </SvgText>
                  ) : null}
                  {dashaTag ? (
                    <SvgText
                      x={symbolX + textHalfWidth(planet.symbol, planetFont)}
                      y={symbolY - Math.round(planetFont * 0.55)}
                      fontSize={Math.max(6, Math.round(planetFont * 0.42))}
                      fill={paint.glow}
                      fontWeight="700"
                      textAnchor="start"
                      pointerEvents="none"
                    >
                      {dashaTag}
                    </SvgText>
                  ) : null}
                  {slot.degreesFit && (
                    <SvgText
                      x={symbolX}
                      y={slot.degreeY}
                      fontSize={slot.degreeFont}
                      fill={paint ? paint.fill : (cosmicTheme ? colors.chartTextMuted : (theme === 'dark' ? (colors.textSecondary || 'rgba(148, 163, 184, 0.9)') : "#666"))}
                      fontWeight="500"
                      textAnchor="middle">
                      {planet.formattedDegree} {planet.shortNakshatra}
                    </SvgText>
                  )}
                </G>
                );
              })}
              {(() => {
                const transits = getTransitPlanetsInSign(pos.sign);
                if (!transits.length) return null;
                const polygon = [
                  [pos.x + 2, pos.y + 2],
                  [pos.x + pos.width - 2, pos.y + 2],
                  [pos.x + pos.width - 2, pos.y + pos.height - 2],
                  [pos.x + 2, pos.y + pos.height - 2],
                ];
                const occupied = planetsInSign.map((planet, pIndex) => {
                  const slot = southPlanetSlot(pos, pIndex, planetsInSign.length, houseNumber);
                  const dashaTag = dashaLevelSuffix(planet.name, dashaHighlight);
                  const symbolFont = slot.symbolFont;
                  const tagFont = Math.max(6, Math.round(symbolFont * 0.42));
                  const symbolHalf = textHalfWidth(planet.symbol, symbolFont);
                  const tagExtra = dashaTag ? textHalfWidth(dashaTag, tagFont) + 2 : 0;
                  const degreeHalf = slot.degreesFit
                    ? textHalfWidth(`${planet.formattedDegree} ${planet.shortNakshatra}`, slot.degreeFont)
                    : 0;
                  const half = Math.max(symbolHalf + tagExtra, degreeHalf) + 4;
                  const above = Math.ceil(symbolFont * 0.95) + (dashaTag ? tagFont : 1);
                  const below = slot.degreesFit ? Math.max(4, slot.degreeY - slot.symbolY + 3) : 3;
                  return labelBox(pos.x + pos.width / 2, slot.symbolY, half, above, below);
                });
                const houseLabel = String(houseNumber || '');
                if (houseLabel) {
                  const houseHalf = textHalfWidth(houseLabel, 12) + 2;
                  occupied.push(labelBox(
                    pos.x + 8 + houseHalf - 2,
                    pos.y + 16,
                    houseHalf,
                    14,
                    4,
                  ));
                }
                if (houseNumber === 1) {
                  occupied.push(labelBox(
                    pos.x + pos.width - 20,
                    pos.y + pos.height - 16,
                    20,
                    12,
                    showDegreeNakshatra ? 16 : 6,
                  ));
                }
                if (signPointAt(signPoints, pos.sign) != null) {
                  const cellPolygon = [
                    [pos.x + 2, pos.y + 2],
                    [pos.x + pos.width - 2, pos.y + 2],
                    [pos.x + pos.width - 2, pos.y + pos.height - 2],
                    [pos.x + 2, pos.y + pos.height - 2],
                  ];
                  const savSpot = placeCircleClear(cellPolygon, occupied, 11);
                  if (savSpot?.box) occupied.push(savSpot.box);
                }
                const layout = placeTransitLabels(polygon, occupied, transits.map((planet) => ({
                  symbol: planet.symbol,
                  retrograde: planet.retrograde,
                  degree: planet.formattedDegree,
                  nakshatra: planet.shortNakshatra,
                  name: planet.name,
                  bav: planet.bav,
                })), showDegreeNakshatra);
                if (!layout) return null;
                const transitColor = colors.accent || colors.primary;
                return (
                  <>
                    <G pointerEvents="box-none">
                      {layout.specs.map((spec, transitIndex) => {
                        const slot = layout.placed[transitIndex];
                        if (!slot) return null;
                        return (
                          <G key={`transit-${spec.text}-${transitIndex}`}>
                            <SvgText
                              x={slot.x}
                              y={slot.y}
                              fontSize={spec.fontSize}
                              fill={transitColor}
                              fontWeight="800"
                              textAnchor="middle"
                              onPress={spec.name && onTransitPlanetPress ? () => onTransitPlanetPress(spec.name) : undefined}
                            >
                              {spec.text}
                            </SvgText>
                            {spec.detail ? (
                              <SvgText
                                x={slot.x}
                                y={slot.y + (spec.detailOffset || 9)}
                                fontSize={spec.detailSize || 7}
                                fill={transitColor}
                                fontWeight="600"
                                textAnchor="middle"
                              >
                                {spec.detail}
                              </SvgText>
                            ) : null}
                          </G>
                        );
                      })}
                    </G>
                  </>
                );
              })()}
              <Rect
                x={pos.x}
                y={pos.y}
                width={pos.width}
                height={pos.height}
                fill="transparent"
                onPress={() => handleCellPress(pos.sign)}
              />
            </G>
          );
        })}
      </Svg>

      {/* Context Menu Modal */}
      <Modal
        visible={contextMenu.show}
        transparent
        animationType="fade"
        onRequestClose={() => setContextMenu({ show: false, rashiIndex: null, signName: null })}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setContextMenu({ show: false, rashiIndex: null, signName: null })}
        >
          <View style={styles.contextMenuContainer}>
            <Text style={styles.contextMenuTitle}>{contextMenu.signName}</Text>
            <TouchableOpacity
              style={styles.contextMenuItem}
              onPress={() => {
                onRotate?.(contextMenu.rashiIndex);
                setContextMenu({ show: false, rashiIndex: null, signName: null });
              }}
            >
              <Text style={styles.contextMenuIcon}>🔄</Text>
              <Text style={styles.contextMenuText}>Make Ascendant</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>

      <Text style={[
        styles.instructionText,
        cosmicTheme && styles.instructionTextCosmic,
        Platform.OS === 'web' && styles.instructionTextWeb,
      ]}>
        Touch any sign to make it ascendant
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: Platform.select({
    web: {
      width: '100%',
      aspectRatio: 1,
      alignSelf: 'stretch',
      position: 'relative',
    },
    default: {
      flex: 1,
      width: '100%',
      aspectRatio: 1,
    },
  }),
  svg: Platform.select({
    web: {
      width: '100%',
      aspectRatio: 1,
      display: 'block',
    },
    default: {
      width: '100%',
      height: '100%',
      aspectRatio: 1,
    },
  }),
  instructionTextWeb: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 8,
    marginTop: 0,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  contextMenuContainer: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    minWidth: 200,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  contextMenuTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#e91e63',
    marginBottom: 16,
    textAlign: 'center',
  },
  contextMenuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    gap: 12,
  },
  contextMenuIcon: {
    fontSize: 20,
  },
  contextMenuText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  instructionText: {
    textAlign: 'center',
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
    marginTop: 8,
  },
  instructionTextCosmic: {
    color: 'rgba(255, 255, 255, 0.7)',
  },
});

export default SouthIndianChart;
