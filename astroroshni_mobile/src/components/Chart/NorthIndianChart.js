import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Modal, Animated, Easing } from 'react-native';
import Svg, { Rect, Polygon, Line, Text as SvgText, G, Defs, LinearGradient, Stop, Circle, Path, ClipPath } from 'react-native-svg';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';

// Create animated versions of SVG components
const AnimatedLine = Animated.createAnimatedComponent(Line);
const AnimatedPolygon = Animated.createAnimatedComponent(Polygon);
const AnimatedRect = Animated.createAnimatedComponent(Rect);
const AnimatedG = Animated.createAnimatedComponent(G);

const NorthIndianChart = ({ 
  chartData, 
  chartType,
  birthData, 
  showDegreeNakshatra = true, 
  cosmicTheme = false, 
  rotatedAscendant = null, 
  onRotate, 
  showKarakas = false, 
  karakas = null, 
  highlightHouse = null, 
  glowAnimation = null, 
  hideInstructions = false,
  onHousePress // New prop for drawer
}) => {
  const { theme, colors } = useTheme();
  const { t } = useTranslation();
  
  const [tooltip, setTooltip] = useState({ show: false, text: '' });
  
  // Animation refs
  const drawAnim = useRef(new Animated.Value(0)).current;
  const lastDataRef = useRef(null);
  const [isAnimating, setIsAnimating] = useState(true);

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
    
    const runAnimation = () => {
      drawAnim.setValue(0);
      setIsAnimating(true);

      Animated.timing(drawAnim, {
        toValue: 1,
        duration: 800,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }).start(() => setIsAnimating(false));
    };

    runAnimation();
  }, [chartData, chartType, rotatedAscendant]);

  const handlePlanetPress = (planet) => {
    const tooltipText = `${planet.name}: ${planet.degree}° in ${planet.nakshatra}`;
    setTooltip({ show: true, text: tooltipText });
    setTimeout(() => setTooltip({ show: false, text: '' }), 2000);
  };

  const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
  
  const handleHousePressInternal = (houseNum) => {
    const houseIndex = houseNum - 1;
    const rashiIndex = getRashiForHouse(houseIndex);
    const planetsInHouse = getPlanetsInHouse(houseIndex);
    
    if (onHousePress) {
      onHousePress({
        houseNum,
        rashiIndex,
        signName: rashiNames[rashiIndex],
        planets: planetsInHouse,
        chartData
      });
    }
  };

  const getHouseGlowColor = (houseNum) => {
    if (highlightHouse !== houseNum) return null;
    return cosmicTheme ? 'rgba(255, 215, 0, 0.6)' : 'rgba(255, 107, 53, 0.6)';
  };

  const getHouseData = (houseNum) => {
    // Perfectly symmetrical coordinates for a 400x400 SVG
    const houseData = {
      1: { center: { x: 200, y: 100 }, path: "M200,0 L300,100 L200,200 L100,100 Z" },
      2: { center: { x: 100, y: 50 }, path: "M0,0 L200,0 L100,100 Z" },
      3: { center: { x: 50, y: 100 }, path: "M0,0 L100,100 L0,200 Z" },
      4: { center: { x: 100, y: 200 }, path: "M0,200 L100,100 L200,200 L100,300 Z" },
      5: { center: { x: 50, y: 300 }, path: "M0,200 L100,300 L0,400 Z" },
      6: { center: { x: 100, y: 350 }, path: "M0,400 L100,300 L200,400 Z" },
      7: { center: { x: 200, y: 300 }, path: "M200,200 L300,300 L200,400 L100,300 Z" },
      8: { center: { x: 300, y: 350 }, path: "M200,400 L300,300 L400,400 Z" },
      9: { center: { x: 350, y: 300 }, path: "M300,300 L400,200 L400,400 Z" },
      10: { center: { x: 300, y: 200 }, path: "M200,200 L300,100 L400,200 L300,300 Z" },
      11: { center: { x: 350, y: 100 }, path: "M300,100 L400,0 L400,200 Z" },
      12: { center: { x: 300, y: 50 }, path: "M200,0 L400,0 L300,100 Z" }
    };
    return houseData[houseNum];
  };

  const getRashiForHouse = (houseIndex) => {
    if (!chartData || !chartData.houses || !chartData.houses[houseIndex]) return houseIndex;
    if (rotatedAscendant !== null) {
      return (rotatedAscendant + houseIndex) % 12;
    }
    return chartData.houses[houseIndex].sign;
  };

  const getPlanetStatus = (planet) => {
    if (!chartData) return 'normal';
    if (['Rahu', 'Ketu', 'Gulika', 'Mandi', 'InduLagna'].includes(planet.name)) return 'normal';
    const planets = chartData.planets || chartData;
    const planetData = planets[planet.name];
    if (!planetData) return 'normal';
    const planetSign = planetData.sign;
    const exaltationSigns = { 'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 'Jupiter': 3, 'Venus': 11, 'Saturn': 6 };
    const debilitationSigns = { 'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11, 'Jupiter': 9, 'Venus': 5, 'Saturn': 0 };
    if (exaltationSigns[planet.name] === planetSign) return 'exalted';
    if (debilitationSigns[planet.name] === planetSign) return 'debilitated';
    return 'normal';
  };

  const getPlanetColor = (planet) => {
    if (planet.name === 'InduLagna') return '#9c27b0';
    const status = getPlanetStatus(planet);
    if (status === 'exalted') return '#22c55e';
    if (status === 'debilitated') return '#ef4444';
    return cosmicTheme ? (theme === 'dark' ? 'rgba(255, 255, 255, 0.95)' : 'rgba(0, 0, 0, 0.9)') : (theme === 'dark' ? '#fff' : '#2d3436');
  };

  const getPlanetSymbolWithStatus = (planet) => {
    const status = getPlanetStatus(planet);
    const planets = chartData.planets || chartData;
    const planetData = planets[planet.name];
    const isRetrograde = planetData?.retrograde;
    let symbol = planet.symbol;
    if (isRetrograde && planet.name !== 'Rahu' && planet.name !== 'Ketu') symbol += '(R)';
    if (status === 'exalted') symbol += '↑';
    if (status === 'debilitated') symbol += '↓';
    if (showKarakas && karakas && typeof karakas === 'object') {
      const karaka = Object.entries(karakas).find(([_, data]) => data?.planet === planet.name);
      if (karaka) {
        const karakaAbbr = { 'Atmakaraka': 'AK', 'Amatyakaraka': 'AmK', 'Bhratrukaraka': 'BK', 'Matrukaraka': 'MK', 'Putrakaraka': 'PK', 'Gnatikaraka': 'GK', 'Darakaraka': 'DK' }[karaka[0]];
        if (karakaAbbr) symbol += `(${karakaAbbr})`;
      }
    }
    return symbol;
  };

  const getNakshatra = (longitude) => {
    const nakshatras = ['Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'];
    const nakshatraIndex = Math.floor(longitude / 13.333333);
    return nakshatras[nakshatraIndex] || 'Unknown';
  };

  const getShortNakshatra = (longitude) => {
    const shortNakshatras = ['Ash', 'Bha', 'Kri', 'Roh', 'Mri', 'Ard', 'Pun', 'Pus', 'Asl', 'Mag', 'PPh', 'UPh', 'Has', 'Chi', 'Swa', 'Vis', 'Anu', 'Jye', 'Mul', 'PAs', 'UAs', 'Shr', 'Dha', 'Sha', 'PBh', 'UBh', 'Rev'];
    const nakshatraIndex = Math.floor(longitude / 13.333333);
    return shortNakshatras[nakshatraIndex] || 'Unk';
  };

  const formatDegree = (degree) => {
    if (typeof degree !== 'number') return '0.00°';
    return degree.toFixed(2) + '°';
  };

  const getPlanetsInHouse = (houseIndex) => {
    if (!chartData) return [];
    const planets = chartData.planets || chartData;
    if (!planets || typeof planets !== 'object') return [];
    const rashiForThisHouse = getRashiForHouse(houseIndex);
    const planetsInHouse = [];
    const planetNames = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Uranus', 'Neptune', 'Pluto', 'Gulika', 'Mandi'];
    planetNames.forEach(name => {
      const data = planets[name];
      if (data && typeof data === 'object' && data.sign === rashiForThisHouse) {
        planetsInHouse.push({
          symbol: t(`planets.${name}`, name.substring(0, 2)),
          name: name,
          degree: typeof data.degree === 'number' ? data.degree.toFixed(2) : '0.00',
          longitude: data.longitude || 0,
          nakshatra: getNakshatra(data.longitude || 0),
          shortNakshatra: getShortNakshatra(data.longitude || 0),
          formattedDegree: formatDegree(data.degree || 0)
        });
      }
    });
    if (planets.InduLagna && planets.InduLagna.sign === rashiForThisHouse) {
      planetsInHouse.push({
        symbol: t('planets.InduLagna', 'IL'),
        name: 'InduLagna',
        degree: typeof planets.InduLagna.degree === 'number' ? planets.InduLagna.degree.toFixed(2) : '0.00',
        longitude: planets.InduLagna.longitude || 0,
        nakshatra: getNakshatra(planets.InduLagna.longitude || 0),
        shortNakshatra: getShortNakshatra(planets.InduLagna.longitude || 0),
        formattedDegree: formatDegree(planets.InduLagna.degree || 0)
      });
    }
    return planetsInHouse;
  };

  const gridStrokeDash = drawAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [1000, 0]
  });

  return (
    <View style={styles.container}>
      <Svg viewBox="0 0 400 400" style={styles.svg}>
        <Defs>
          <ClipPath id="chartClip">
            <Rect 
              x="2" y="2" width="396" height="396" 
              rx={cosmicTheme ? "16" : "0"}
              ry={cosmicTheme ? "16" : "0"}
            />
          </ClipPath>
          <LinearGradient id="chartGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            {cosmicTheme ? (
              theme === 'dark' ? [
                <Stop key="0" offset="0%" stopColor="rgba(255, 255, 255, 0.15)" />,
                <Stop key="50" offset="50%" stopColor="rgba(255, 255, 255, 0.08)" />,
                <Stop key="100" offset="100%" stopColor="rgba(255, 255, 255, 0.12)" />
              ] : [
                <Stop key="0" offset="0%" stopColor="rgba(249, 115, 22, 0.15)" />,
                <Stop key="50" offset="50%" stopColor="rgba(249, 115, 22, 0.08)" />,
                <Stop key="100" offset="100%" stopColor="rgba(249, 115, 22, 0.12)" />
              ]
            ) : [
                <Stop key="0" offset="0%" stopColor="rgba(255, 255, 255, 0.9)" />,
                <Stop key="50" offset="50%" stopColor="rgba(248, 250, 252, 0.95)" />,
                <Stop key="100" offset="100%" stopColor="rgba(241, 245, 249, 0.9)" />
              ]}
          </LinearGradient>
        </Defs>

        {/* Outer square border */}
        <AnimatedRect 
          x="2" y="2" width="396" height="396" 
          fill="transparent" 
          stroke={cosmicTheme ? "rgba(255, 107, 53, 0.9)" : "#e91e63"} 
          strokeWidth={cosmicTheme ? "2" : "3"}
          rx={cosmicTheme ? "16" : "0"}
          ry={cosmicTheme ? "16" : "0"}
          strokeDasharray="1600"
          strokeDashoffset={gridStrokeDash}
          pointerEvents="none"
        />
        
        {/* Inner diamond border */}
        <AnimatedPolygon 
          points="200,2 398,200 200,398 2,200" 
          fill="none" 
          stroke={cosmicTheme ? "rgba(255, 215, 0, 0.8)" : "#ff6f00"} 
          strokeWidth={cosmicTheme ? "2" : "3"}
          strokeDasharray="1200"
          strokeDashoffset={gridStrokeDash}
          pointerEvents="none"
        />
        
        {/* Diagonal lines */}
        <G clipPath="url(#chartClip)">
          <AnimatedLine 
            x1="2" y1="2" x2="398" y2="398" 
            stroke={cosmicTheme ? "rgba(255, 138, 101, 0.6)" : "#ff8a65"} 
            strokeWidth="2"
            strokeDasharray="600"
            strokeDashoffset={gridStrokeDash}
            pointerEvents="none"
          />
          <AnimatedLine 
            x1="398" y1="2" x2="2" y2="398" 
            stroke={cosmicTheme ? "rgba(255, 138, 101, 0.6)" : "#ff8a65"} 
            strokeWidth="2"
            strokeDasharray="600"
            strokeDashoffset={gridStrokeDash}
            pointerEvents="none"
          />
        </G>

        {/* Houses */}
        {[1,2,3,4,5,6,7,8,9,10,11,12].map((houseNumber) => {
          const houseIndex = houseNumber - 1;
          const rashiIndex = getRashiForHouse(houseIndex);
          const planetsInHouse = getPlanetsInHouse(houseIndex);
          const houseData = getHouseData(houseNumber);
          
          return (
            <G key={houseNumber} pointerEvents="none">
              {highlightHouse === houseNumber && glowAnimation && (
                <Circle cx={houseData.center.x} cy={houseData.center.y} r="60" fill={getHouseGlowColor(houseNumber)} opacity={glowAnimation} />
              )}
              
              <SvgText 
                x={houseNumber === 1 ? houseData.center.x - 5 :
                   houseNumber === 2 ? houseData.center.x - 10 :
                   houseNumber === 3 ? houseData.center.x + 10 :
                   houseNumber === 4 ? houseData.center.x + 40 :
                   houseNumber === 5 ? houseData.center.x + 10 :
                   houseNumber === 6 ? houseData.center.x - 15 :
                   houseNumber === 7 ? houseData.center.x - 5 :
                   houseNumber === 8 ? houseData.center.x - 5 :
                   houseNumber === 9 ? houseData.center.x - 20 :
                   houseNumber === 10 ? houseData.center.x - 50 :
                   houseNumber === 11 ? houseData.center.x - 25 :
                   houseData.center.x - 5} 
                y={houseNumber === 1 ? houseData.center.y + 55 :
                   houseNumber === 2 ? houseData.center.y + 25 :
                   houseNumber === 6 ? houseData.center.y - 10 :
                   houseNumber === 7 ? houseData.center.y - 40 :
                   houseNumber === 8 ? houseData.center.y - 10 :
                   houseNumber === 12 ? houseData.center.y + 20 :
                   houseNumber === 5 ? houseData.center.y + 10 : houseData.center.y + 5} 
                fontSize="18" 
                fill={cosmicTheme ? 
                  (rashiIndex === (chartData?.houses?.[0]?.sign ?? 0) ? "#ff6b35" : (theme === 'dark' ? "rgba(255, 255, 255, 0.9)" : "rgba(0, 0, 0, 0.8)")) :
                  (rashiIndex === (chartData?.houses?.[0]?.sign ?? 0) ? "#e91e63" : (theme === 'dark' ? "#fff" : "#333"))} 
                fontWeight={rashiIndex === (chartData?.houses?.[0]?.sign ?? 0) ? "900" : "bold"}>
                {rashiIndex + 1}
              </SvgText>
              
              {houseNumber === 1 && (
                <G>
                  <SvgText x={houseData.center.x + 25} y={houseData.center.y + 35} fontSize="12" fill={cosmicTheme ? "#ff6b35" : "#e91e63"} fontWeight="900" textAnchor="middle">ASC</SvgText>
                  {chartData?.ascendant && (
                    <SvgText x={houseData.center.x + 25} y={houseData.center.y + 50} fontSize="8" fill={cosmicTheme ? (theme === 'dark' ? "rgba(255, 255, 255, 0.7)" : "rgba(0, 0, 0, 0.6)") : (theme === 'dark' ? "rgba(255, 255, 255, 0.7)" : "#666")} fontWeight="500" textAnchor="middle">
                      {formatDegree(chartData.ascendant % 30)} {getShortNakshatra(chartData.ascendant)}
                    </SvgText>
                  )}
                </G>
              )}
              
              {planetsInHouse.map((planet, pIndex) => {
                const totalPlanets = planetsInHouse.length;
                let planetX, planetY;
                
                if (totalPlanets === 1) {
                  if (houseNumber === 1) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y - 15;
                  } else if ([3, 4, 5].includes(houseNumber)) {
                    planetX = houseData.center.x - 15;
                    planetY = houseData.center.y + 10;
                  } else if ([6, 7, 8].includes(houseNumber)) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y + 30;
                  } else if (houseNumber === 9) {
                    planetX = houseData.center.x + 10;
                    planetY = houseData.center.y - 20;
                  } else if (houseNumber === 10) {
                    planetX = houseData.center.x + 15;
                    planetY = houseData.center.y - 20;
                  } else if (houseNumber === 11) {
                    planetX = houseData.center.x + 5;
                    planetY = houseData.center.y - 15;
                  } else if (houseNumber === 12) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y - 15;
                  } else if (houseNumber === 2) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y - 25;
                  } else {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y - 10;
                  }
                } else if (totalPlanets <= 4) {
                  if ([3, 5, 9, 11].includes(houseNumber)) {
                    const rowSpacing = 35;
                    if (houseNumber === 3) {
                      planetX = houseData.center.x - 35;
                      planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                    } else if (houseNumber === 5) {
                      planetX = houseData.center.x - 25;
                      planetY = houseData.center.y - 20 + (pIndex * rowSpacing);
                    } else if (houseNumber === 9) {
                      planetX = houseData.center.x + 25;
                      planetY = houseData.center.y - 40 + (pIndex * rowSpacing);
                    } else if (houseNumber === 11) {
                      planetX = houseData.center.x + 15;
                      planetY = houseData.center.y - 55 + (pIndex * rowSpacing);
                    }
                  } else {
                    const row = Math.floor(pIndex / 2);
                    const col = pIndex % 2;
                    const spacing = 25;
                    const rowSpacing = 32;
                    
                    if (houseNumber === 1) {
                      planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                      planetY = houseData.center.y - 20 + (row * rowSpacing);
                    } else if (houseNumber === 4) {
                      planetX = houseData.center.x - 25 + (col === 0 ? -spacing : spacing);
                      planetY = houseData.center.y + 5 + (row * rowSpacing);
                    } else if ([6, 7, 8].includes(houseNumber)) {
                      planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                      planetY = houseData.center.y + 25 + (row * rowSpacing);
                    } else if (houseNumber === 10) {
                      planetX = houseData.center.x + 15 + (col === 0 ? -spacing : spacing);
                      planetY = houseData.center.y - 25 + (row * rowSpacing);
                    } else if (houseNumber === 12) {
                      planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                      planetY = houseData.center.y - 5 + (row * rowSpacing);
                    } else if (houseNumber === 2) {
                      planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                      planetY = houseData.center.y - 5 + (row * rowSpacing);
                    } else {
                      planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                      planetY = houseData.center.y - 25 + (row * rowSpacing);
                    }
                  }
                } else {
                  const rowSpacing = 26;
                  
                  if (houseNumber === 1) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y - 25 + (pIndex * rowSpacing);
                  } else if ([3, 4, 5].includes(houseNumber)) {
                    planetX = houseData.center.x - 25;
                    planetY = houseData.center.y + 0 + (pIndex * rowSpacing);
                  } else if ([6, 7, 8].includes(houseNumber)) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y + 20 + (pIndex * rowSpacing);
                  } else if (houseNumber === 9) {
                    planetX = houseData.center.x + 15;
                    planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                  } else if (houseNumber === 10) {
                    planetX = houseData.center.x + 15;
                    planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                  } else if (houseNumber === 11) {
                    planetX = houseData.center.x + 10;
                    planetY = houseData.center.y - 25 + (pIndex * rowSpacing);
                  } else if (houseNumber === 12) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y - 5 + (pIndex * rowSpacing);
                  } else if (houseNumber === 2) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y - 10 + (pIndex * rowSpacing);
                  } else {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                  }
                }
                
                return (
                  <G key={pIndex}>
                    <SvgText x={planetX} y={planetY - 8} fontSize={showKarakas ? (totalPlanets > 4 ? "8" : totalPlanets > 2 ? "10" : "11") : (totalPlanets > 4 ? "10" : totalPlanets > 2 ? "12" : "14")} fill={getPlanetColor(planet)} fontWeight="900" textAnchor="middle">{getPlanetSymbolWithStatus(planet)}</SvgText>
                    {showDegreeNakshatra && (
                      <SvgText x={planetX} y={planetY + 8} fontSize={totalPlanets > 4 ? "7" : totalPlanets > 2 ? "9" : "10"} fill={cosmicTheme ? (theme === 'dark' ? "rgba(255, 255, 255, 0.7)" : "rgba(0, 0, 0, 0.6)") : (theme === 'dark' ? "rgba(255, 255, 255, 0.7)" : "#666")} fontWeight="500" textAnchor="middle">
                        {planet.formattedDegree} {planet.shortNakshatra}
                      </SvgText>
                    )}
                  </G>
                );
              })}
            </G>
          );
        })}

        {/* House Hit Areas - Moved to end to be on top */}
        <G pointerEvents="auto">
          {[1,2,3,4,5,6,7,8,9,10,11,12].map((houseNum) => (
            <Path
              key={`hit-${houseNum}`}
              d={getHouseData(houseNum).path}
              fill="transparent"
              onPress={() => handleHousePressInternal(houseNum)}
            />
          ))}
        </G>
      </Svg>
      
      {tooltip.show && (
        <View style={[styles.tooltip, { backgroundColor: theme === 'dark' ? 'rgba(233, 30, 99, 0.9)' : 'rgba(249, 115, 22, 0.9)' }]}>
          <Text style={styles.tooltipText}>{tooltip.text}</Text>
        </View>
      )}
      
      {!hideInstructions && (
        <Text style={[styles.instructionText, { color: theme === 'dark' ? (cosmicTheme ? 'rgba(255, 255, 255, 0.7)' : '#666') : (cosmicTheme ? 'rgba(0, 0, 0, 0.6)' : '#666') }]}>
          Touch any house for deep insights
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, width: '100%', aspectRatio: 1 },
  svg: { width: '100%', height: '100%', aspectRatio: 1 },
  tooltip: { position: 'absolute', top: 20, left: 20, right: 20, padding: 12, borderRadius: 12, alignItems: 'center', zIndex: 100 },
  tooltipText: { color: 'white', fontSize: 14, fontWeight: 'bold', textAlign: 'center' },
  instructionText: { textAlign: 'center', fontSize: 12, fontStyle: 'italic', marginTop: 24, marginBottom: 12 },
});

export default NorthIndianChart;
