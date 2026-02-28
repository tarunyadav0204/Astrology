import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, Animated, Easing } from 'react-native';
import Svg, { Rect, Text as SvgText, G, Line, ClipPath, Defs } from 'react-native-svg';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';

const AnimatedG = Animated.createAnimatedComponent(G);

const SouthIndianChart = ({ 
  chartData, 
  chartType,
  showDegreeNakshatra = false, 
  rotatedAscendant = null, 
  onRotate, 
  cosmicTheme = false, 
  showKarakas = false, 
  karakas = null 
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

  const formatDegree = (degree) => {
    return degree.toFixed(2) + '°';
  };

  const getPlanetStatus = (planetName, signIndex) => {
    if (!chartData || !chartData.planets) return 'normal';
    if (['Rahu', 'Ketu', 'Gulika', 'Mandi', 'InduLagna'].includes(planetName)) return 'normal';
    const exaltationSigns = { Sun: 0, Moon: 1, Mars: 9, Mercury: 5, Jupiter: 3, Venus: 11, Saturn: 6 };
    const debilitationSigns = { Sun: 6, Moon: 7, Mars: 3, Mercury: 11, Jupiter: 9, Venus: 5, Saturn: 0 };
    if (exaltationSigns[planetName] === signIndex) return 'exalted';
    if (debilitationSigns[planetName] === signIndex) return 'debilitated';
    return 'normal';
  };

  const getPlanetColor = (planetName, signIndex) => {
    const status = getPlanetStatus(planetName, signIndex);
    if (status === 'exalted') return '#22c55e';      // green
    if (status === 'debilitated') return '#ef4444';  // red
    // Normal planets: theme-aware
    return theme === 'dark'
      ? (colors.text || '#ffffff')
      : '#333';
  };

  const getPlanetsInSign = (signIndex) => {
    if (!chartData.planets || signIndex === -1) return [];
    const planetsInSign = [];
    
    // Add regular planets (exclude InduLagna as it's handled separately)
    Object.entries(chartData.planets)
      .filter(([name, data]) => data.sign === signIndex && name !== 'InduLagna')
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
          degree: data.degree ? data.degree.toFixed(2) : '0.00',
          longitude: data.longitude || 0,
          nakshatra: getNakshatra(data.longitude || 0),
          shortNakshatra: getShortNakshatra(data.longitude || 0),
          formattedDegree: formatDegree(data.degree || 0)
        });
      });
    
    // Add InduLagna if it's in this sign
    if (chartData.planets?.InduLagna && chartData.planets.InduLagna.sign === signIndex) {
      planetsInSign.push({
        symbol: t('planets.InduLagna', 'IL'),
        name: 'InduLagna',
        degree: chartData.planets.InduLagna.degree ? chartData.planets.InduLagna.degree.toFixed(2) : '0.00',
        longitude: chartData.planets.InduLagna.longitude || 0,
        nakshatra: getNakshatra(chartData.planets.InduLagna.longitude || 0),
        shortNakshatra: getShortNakshatra(chartData.planets.InduLagna.longitude || 0),
        formattedDegree: formatDegree(chartData.planets.InduLagna.degree || 0)
      });
    }
    
    return planetsInSign;
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

  return (
    <View style={styles.container}>
      <Svg viewBox="0 0 340 340" style={styles.svg}>
        <Defs>
          <ClipPath id="southChartClip">
            <Rect 
              x="0" y="0" width="340" height="340" 
              rx={cosmicTheme ? "16" : "0"}
              ry={cosmicTheme ? "16" : "0"}
            />
          </ClipPath>
        </Defs>

        {/* Outer border */}
        <Rect 
          x="1.5" y="1.5" width="337" height="337" 
          fill="none" 
          stroke={
            cosmicTheme
              ? "rgba(255, 107, 53, 0.9)"
              : theme === 'dark'
                ? (colors.cardBorder || 'rgba(148, 163, 184, 0.8)')
                : "#ff6f00"
          }
          strokeWidth="3"
          rx={cosmicTheme ? "16" : "0"}
          ry={cosmicTheme ? "16" : "0"}
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
                  ? "rgba(255, 138, 101, 0.6)"
                  : theme === 'dark'
                    ? 'rgba(148, 163, 184, 0.6)'
                    : "#ff8a65"
              }
              strokeWidth="2"
            />
          ))}
          <Line
            x1="0" y1="85" x2="340" y2="85"
            stroke={
              cosmicTheme
                ? "rgba(255, 107, 53, 0.9)"
                : theme === 'dark'
                  ? (colors.cardBorder || 'rgba(148, 163, 184, 0.9)')
                  : "#ff6f00"
            }
            strokeWidth="3"
          />
          <Line
            x1="0" y1="255" x2="340" y2="255"
            stroke={
              cosmicTheme
                ? "rgba(255, 107, 53, 0.9)"
                : theme === 'dark'
                  ? (colors.cardBorder || 'rgba(148, 163, 184, 0.9)')
                  : "#ff6f00"
            }
            strokeWidth="3"
          />
          <Line
            x1="85" y1="0" x2="85" y2="340"
            stroke={
              cosmicTheme
                ? "rgba(255, 107, 53, 0.9)"
                : theme === 'dark'
                  ? (colors.cardBorder || 'rgba(148, 163, 184, 0.9)')
                  : "#ff6f00"
            }
            strokeWidth="3"
          />
          <Line
            x1="255" y1="0" x2="255" y2="340"
            stroke={
              cosmicTheme
                ? "rgba(255, 107, 53, 0.9)"
                : theme === 'dark'
                  ? (colors.cardBorder || 'rgba(148, 163, 184, 0.9)')
                  : "#ff6f00"
            }
            strokeWidth="3"
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
                onPress={() => setContextMenu({ show: true, rashiIndex: pos.sign, signName: rashiNames[pos.sign] })}
              />
              
              {/* House number */}
              <SvgText 
                x={pos.x + 8} 
                y={pos.y + 18} 
                fontSize="12" 
                fill={
                  houseNumber === 1
                    ? (theme === 'dark' ? (colors.primary || '#e91e63') : '#e91e63')
                    : (theme === 'dark' ? (colors.text || '#e5e7eb') : '#333')
                }
                fontWeight={houseNumber === 1 ? "900" : "bold"}
                pointerEvents="none">
                {houseNumber}
              </SvgText>
              
              {/* Ascendant marker for house 1 */}
              {houseNumber === 1 && (
                <G>
                  <SvgText 
                    x={pos.x + pos.width - 8} 
                    y={pos.y + pos.height - 20} 
                    fontSize="9" 
                    fill="#e91e63" 
                    fontWeight="900" 
                    textAnchor="end">
                    ASC
                  </SvgText>
                  {chartData.ascendant && (
                    <SvgText 
                      x={pos.x + pos.width - 8} 
                      y={pos.y + pos.height - 8} 
                      fontSize="7" 
                      fill="#666" 
                      fontWeight="500" 
                      textAnchor="end">
                      {formatDegree(chartData.ascendant % 30)} {getShortNakshatra(chartData.ascendant)}
                    </SvgText>
                  )}
                </G>
              )}
              
              {/* Planets */}
              {planetsInSign.map((planet, pIndex) => (
                <G key={pIndex}>
                  <SvgText 
                    x={pos.x + pos.width / 2} 
                    y={pos.y + 20 + (pIndex * 20)} 
                    fontSize={showKarakas ? "10" : "12"} 
                    fill={getPlanetColor(planet.name, pos.sign)}
                    fontWeight="bold"
                    textAnchor="middle">
                    {planet.symbol}
                  </SvgText>
                  {showDegreeNakshatra && (
                    <SvgText 
                      x={pos.x + pos.width / 2} 
                      y={pos.y + 31 + (pIndex * 20)} 
                      fontSize="8" 
                      fill={theme === 'dark' ? (colors.textSecondary || 'rgba(148, 163, 184, 0.9)') : "#666"}
                      fontWeight="500"
                      textAnchor="middle">
                      {planet.formattedDegree} {planet.shortNakshatra}
                    </SvgText>
                  )}
                </G>
              ))}
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
      
      <Text style={[styles.instructionText, cosmicTheme && styles.instructionTextCosmic]}>
        Touch any sign to make it ascendant
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    width: '100%',
    aspectRatio: 1,
  },
  svg: {
    width: '100%',
    height: '100%',
    aspectRatio: 1,
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