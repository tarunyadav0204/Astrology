import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Modal, ScrollView } from 'react-native';
import { apiService } from '../services/apiService';

const HouseAnalysisModal = ({ 
  isOpen, 
  onClose, 
  houseNumber, 
  signName, 
  chartData, 
  birthData,
  getPlanetsInHouse,
  getRashiForHouse 
}) => {
  const [yogiData, setYogiData] = useState(chartData.yogiData);
  
  useEffect(() => {
    const fetchYogiData = async () => {
      if (!yogiData && birthData) {
        try {
          const data = await apiService.calculateYogi(birthData);
          setYogiData(data);
        } catch (error) {
          console.error('Failed to fetch Yogi data:', error);
        }
      }
    };
    
    fetchYogiData();
  }, [yogiData, birthData]);
  
  if (!isOpen) return null;

  const houseIndex = houseNumber - 1;
  const rashiIndex = getRashiForHouse(houseIndex);
  const houseLords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
  const houseLord = houseLords[rashiIndex];
  const planetsInHouse = getPlanetsInHouse(houseIndex);
  const lordData = chartData.planets?.[houseLord];
  const lordHouse = lordData ? (() => {
    const lordSign = lordData.sign;
    const ascendantSign = chartData.houses?.[0]?.sign || 0;
    return ((lordSign - ascendantSign + 12) % 12) + 1;
  })() : null;
  
  const getHouseLordship = (planet) => {
    const ascendantSign = chartData.houses?.[0]?.sign || 0;
    const signLordships = {
      'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5], 
      'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
    };
    const planetSigns = signLordships[planet] || [];
    return planetSigns.map(sign => ((sign - ascendantSign + 12) % 12) + 1);
  };
  
  const getFriendship = (planet1, planet2) => {
    const friends = {
      'Sun': ['Moon', 'Mars', 'Jupiter'], 'Moon': ['Sun', 'Mercury'], 'Mars': ['Sun', 'Moon', 'Jupiter'],
      'Mercury': ['Sun', 'Venus'], 'Jupiter': ['Sun', 'Moon', 'Mars'], 'Venus': ['Mercury', 'Saturn'], 'Saturn': ['Mercury', 'Venus']
    };
    const enemies = {
      'Sun': ['Venus', 'Saturn'], 'Moon': [], 'Mars': ['Mercury'], 'Mercury': ['Moon'],
      'Jupiter': ['Mercury', 'Venus'], 'Venus': ['Sun', 'Moon'], 'Saturn': ['Sun', 'Moon', 'Mars']
    };
    if (friends[planet1]?.includes(planet2)) return 'Friend';
    if (enemies[planet1]?.includes(planet2)) return 'Enemy';
    return 'Neutral';
  };
  
  const ownSigns = { 'Mars': [0, 7], 'Venus': [1, 6], 'Mercury': [2, 5], 'Moon': [3], 'Sun': [4], 'Jupiter': [8, 11], 'Saturn': [9, 10] };
  const exaltationSigns = { 'Mars': 9, 'Venus': 11, 'Mercury': 5, 'Moon': 1, 'Sun': 0, 'Jupiter': 3, 'Saturn': 6 };
  const debilitationSigns = { 'Mars': 3, 'Venus': 5, 'Mercury': 11, 'Moon': 7, 'Sun': 6, 'Jupiter': 9, 'Saturn': 0 };

  return (
    <Modal visible={isOpen} transparent={true} animationType="slide">
      <View style={styles.overlay}>
        <View style={styles.modal}>
          <View style={styles.header}>
            <Text style={styles.headerTitle}>🏠 House {houseNumber} Analysis</Text>
            <Text style={styles.headerSubtitle}>({signName})</Text>
          </View>
          
          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            {/* Occupants Analysis */}
            <View style={[styles.section, {
              backgroundColor: 'rgba(233, 30, 99, 0.1)',
              borderColor: 'rgba(233, 30, 99, 0.2)'
            }]}>
              <Text style={[styles.sectionTitle, { color: '#e91e63' }]}>👥 Occupants Analysis</Text>
              {planetsInHouse.length > 0 ? planetsInHouse.map(planet => {
                const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet.name);
                const isNaturalMalefic = ['Mars', 'Saturn', 'Sun', 'Rahu', 'Ketu'].includes(planet.name);
                const lordships = getHouseLordship(planet.name);
                const isInOwnSign = ownSigns[planet.name]?.includes(rashiIndex);
                
                let status = '';
                const hasTrikonaLordship = lordships.some(h => [1, 5, 9].includes(h));
                const hasKendraLordship = lordships.some(h => [1, 4, 7, 10].includes(h));
                
                if (lordships.includes(6)) {
                  status = 'Negative';
                } else if (lordships.includes(8)) {
                  status = hasTrikonaLordship ? 'Mixed (8th lord negative dominates)' : 'Negative';
                } else if (lordships.includes(12)) {
                  status = hasTrikonaLordship || hasKendraLordship ? 'Mixed' : 'Negative';
                } else if (isNaturalBenefic && (hasTrikonaLordship || hasKendraLordship)) {
                  status = 'Positive';
                } else if (isNaturalMalefic && isInOwnSign) {
                  status = 'Positive';
                } else if (isNaturalMalefic && hasKendraLordship) {
                  status = 'Mixed (natural malefic in kendra)';
                } else if (isNaturalMalefic) {
                  status = 'Negative';
                } else {
                  status = 'Neutral';
                }
                
                return (
                  <View key={planet.name} style={styles.planetItem}>
                    <Text style={styles.planetName}>{planet.name}: {isNaturalBenefic ? 'Benefic' : isNaturalMalefic ? 'Malefic' : 'Neutral'}</Text>
                    {lordships.length > 0 && <Text style={styles.planetDetail}>• Lord of {lordships.join(', ')}</Text>}
                    {isInOwnSign && <Text style={styles.ownSign}>• Own Sign</Text>}
                    <Text style={[styles.status, { color: status === 'Positive' ? '#4caf50' : status === 'Negative' ? '#f44336' : '#ff9800' }]}>
                      ● {status}
                    </Text>
                  </View>
                );
              }) : <Text style={styles.emptyText}>Empty house</Text>}
            </View>

            {/* Friendship Analysis */}
            <View style={[styles.section, {
              backgroundColor: 'rgba(76, 175, 80, 0.1)',
              borderColor: 'rgba(76, 175, 80, 0.2)'
            }]}>
              <Text style={[styles.sectionTitle, { color: '#4caf50' }]}>🤝 Friendship Analysis</Text>
              {planetsInHouse.map(planet => {
                const friendship = getFriendship(planet.name, houseLord);
                const isInOwnSign = ownSigns[planet.name]?.includes(rashiIndex);
                
                const planetData = chartData.planets?.[planet.name];
                const nakshatraLords = [
                  'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
                  'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
                  'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
                ];
                const nakshatraIndex = planetData ? Math.floor(planetData.longitude / 13.333333) : 0;
                const nakshatraLord = nakshatraLords[nakshatraIndex];
                const nakshatraFriendship = getFriendship(planet.name, nakshatraLord);
                
                let signStatus = isInOwnSign ? 'Own Sign - Positive' : 
                               friendship === 'Friend' ? 'Friend\'s Sign - Positive' : 
                               friendship === 'Enemy' ? 'Enemy\'s Sign - Negative' : 'Neutral Sign';
                
                let nakshatraStatus = nakshatraFriendship === 'Friend' ? 'Friend\'s Nakshatra - Positive' :
                                     nakshatraFriendship === 'Enemy' ? 'Enemy\'s Nakshatra - Negative' : 'Neutral Nakshatra';
                
                return (
                  <View key={planet.name} style={styles.planetItem}>
                    <Text style={styles.planetName}>{planet.name}: 
                      <Text style={{ color: signStatus.includes('Positive') ? '#4caf50' : signStatus.includes('Negative') ? '#f44336' : '#666' }}>
                        {signStatus}
                      </Text>
                    </Text>
                    <Text style={styles.planetDetail}>
                      Nakshatra: 
                      <Text style={{ color: nakshatraStatus.includes('Positive') ? '#4caf50' : nakshatraStatus.includes('Negative') ? '#f44336' : '#666' }}>
                        {nakshatraStatus}
                      </Text> (Lord: {nakshatraLord})
                    </Text>
                  </View>
                );
              })}
            </View>

            {/* Aspects Analysis */}
            <View style={[styles.section, {
              backgroundColor: 'rgba(255, 152, 0, 0.1)',
              borderColor: 'rgba(255, 152, 0, 0.2)'
            }]}>
              <Text style={[styles.sectionTitle, { color: '#ff9800' }]}>🎯 Aspects Analysis</Text>
              {(() => {
                const aspectingPlanets = [];
                Object.entries(chartData.planets || {}).forEach(([name, data]) => {
                  const planetSign = data.sign;
                  const ascendantSign = chartData.houses?.[0]?.sign || 0;
                  const planetHouse = ((planetSign - ascendantSign + 12) % 12) + 1;
                  let aspects = [];
                  
                  if (!['Rahu', 'Ketu'].includes(name)) {
                    const seventhHouse = (planetHouse + 6) % 12 || 12;
                    if (seventhHouse === houseNumber) aspects.push('7th');
                  }
                  
                  if (['Rahu', 'Ketu'].includes(name)) {
                    const rahuKetuAspects = [(planetHouse + 2) % 12 || 12, (planetHouse + 10) % 12 || 12];
                    if (rahuKetuAspects.includes(houseNumber)) {
                      aspects.push(houseNumber === rahuKetuAspects[0] ? '3rd' : '11th');
                    }
                  }
                  
                  if (name === 'Mars') {
                    const marsAspects = [(planetHouse + 3) % 12 || 12, (planetHouse + 7) % 12 || 12];
                    if (marsAspects.includes(houseNumber)) {
                      aspects.push(houseNumber === marsAspects[0] ? '4th' : '8th');
                    }
                  }
                  
                  if (name === 'Jupiter') {
                    const jupiterAspects = [(planetHouse + 4) % 12 || 12, (planetHouse + 8) % 12 || 12];
                    if (jupiterAspects.includes(houseNumber)) {
                      aspects.push(houseNumber === jupiterAspects[0] ? '5th' : '9th');
                    }
                  }
                  
                  if (name === 'Saturn') {
                    const saturnAspects = [(planetHouse + 2) % 12 || 12, (planetHouse + 9) % 12 || 12];
                    if (saturnAspects.includes(houseNumber)) {
                      aspects.push(houseNumber === saturnAspects[0] ? '3rd' : '10th');
                    }
                  }
                  
                  if (aspects.length > 0) {
                    const lordships = getHouseLordship(name);
                    const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(name);
                    const isMaleficLord = lordships.some(h => [6, 8, 12].includes(h));
                    
                    let aspectNature = isNaturalBenefic && !isMaleficLord ? 'Positive' : 
                                     !isNaturalBenefic || isMaleficLord ? 'Negative' : 'Mixed';
                    
                    aspectingPlanets.push({ name, aspects, nature: aspectNature, lordships });
                  }
                });
                
                return aspectingPlanets.length > 0 ? aspectingPlanets.map(planet => (
                  <View key={planet.name} style={styles.planetItem}>
                    <Text style={styles.planetName}>{planet.name} {planet.aspects.join(', ')} aspect</Text>
                    {planet.lordships.length > 0 && <Text style={styles.planetDetail}>• Lord of {planet.lordships.join(', ')}</Text>}
                    <Text style={[styles.status, { color: planet.nature === 'Positive' ? '#4caf50' : planet.nature === 'Negative' ? '#f44336' : '#ff9800' }]}>
                      ● {planet.nature}
                    </Text>
                  </View>
                )) : <Text style={styles.emptyText}>No planetary aspects</Text>;
              })()}
            </View>

            {/* House Lord Analysis */}
            <View style={[styles.section, {
              backgroundColor: 'rgba(156, 39, 176, 0.1)',
              borderColor: 'rgba(156, 39, 176, 0.2)'
            }]}>
              <Text style={[styles.sectionTitle, { color: '#9c27b0' }]}>👑 House Lord Analysis</Text>
              <View style={styles.planetItem}>
                <Text style={styles.planetName}>{houseLord} (Lord of House {houseNumber})</Text>
                {lordData && (() => {
                  const nakshatraLords = [
                    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
                    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
                    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
                  ];
                  const nakshatraIndex = Math.floor(lordData.longitude / 13.333333);
                  const nakshatraLord = nakshatraLords[nakshatraIndex];
                  const nakshatraFriendship = getFriendship(houseLord, nakshatraLord);
                  
                  let signStatus = exaltationSigns[houseLord] === lordData.sign ? 'Exalted - Positive' :
                                 debilitationSigns[houseLord] === lordData.sign ? 'Debilitated - Negative' :
                                 ownSigns[houseLord]?.includes(lordData.sign) ? 'Own Sign - Positive' :
                                 getFriendship(houseLord, houseLords[lordData.sign]) === 'Friend' ? 'Friend\'s Sign - Positive' :
                                 getFriendship(houseLord, houseLords[lordData.sign]) === 'Enemy' ? 'Enemy\'s Sign - Negative' : 'Neutral';
                  
                  let nakshatraStatus = nakshatraFriendship === 'Friend' ? 'Friend\'s Nakshatra - Positive' :
                                       nakshatraFriendship === 'Enemy' ? 'Enemy\'s Nakshatra - Negative' : 'Neutral Nakshatra';
                  
                  return (
                    <>
                      <Text style={styles.planetDetail}>Currently in House {lordHouse}</Text>
                      <Text style={styles.planetDetail}>
                        Sign Status: 
                        <Text style={{ color: signStatus.includes('Positive') ? '#4caf50' : signStatus.includes('Negative') ? '#f44336' : '#666' }}>
                          {signStatus}
                        </Text>
                      </Text>
                      <Text style={styles.planetDetail}>
                        Nakshatra: 
                        <Text style={{ color: nakshatraStatus.includes('Positive') ? '#4caf50' : nakshatraStatus.includes('Negative') ? '#f44336' : '#666' }}>
                          {nakshatraStatus}
                        </Text> (Lord: {nakshatraLord})
                      </Text>
                    </>
                  );
                })()}
              </View>
            </View>

            {/* Special Conditions */}
            <View style={[styles.section, {
              backgroundColor: 'rgba(63, 81, 181, 0.1)',
              borderColor: 'rgba(63, 81, 181, 0.2)'
            }]}>
              <Text style={[styles.sectionTitle, { color: '#3f51b5' }]}>✨ Special Conditions</Text>
              <View style={styles.planetItem}>
                <Text style={styles.planetName}>Dagdha Rashi: 
                  {(() => {
                    const currentYogiData = yogiData || chartData.yogiData;
                    if (currentYogiData?.dagdha_rashi) {
                      return currentYogiData.dagdha_rashi.sign === rashiIndex ? 
                        <Text style={{ color: '#f44336', fontWeight: '600' }}>Yes - Negative</Text> : 
                        <Text style={{ color: '#4caf50' }}>No</Text>;
                    }
                    return <Text style={{ color: '#ff9800' }}>Loading...</Text>;
                  })()} 
                </Text>
              </View>
              <View style={styles.planetItem}>
                <Text style={styles.planetName}>Tithi Shunya: 
                  {(() => {
                    const currentYogiData = yogiData || chartData.yogiData;
                    if (currentYogiData?.tithi_shunya_rashi) {
                      return currentYogiData.tithi_shunya_rashi.sign === rashiIndex ? 
                        <Text style={{ color: '#f44336', fontWeight: '600' }}>Yes - Negative</Text> : 
                        <Text style={{ color: '#4caf50' }}>No</Text>;
                    }
                    return <Text style={{ color: '#ff9800' }}>Loading...</Text>;
                  })()} 
                </Text>
              </View>
              <View style={styles.planetItem}>
                <Text style={styles.planetName}>Yogi Point: 
                  {(() => {
                    const currentYogiData = yogiData || chartData.yogiData;
                    if (currentYogiData?.yogi && currentYogiData.yogi.sign === rashiIndex) 
                      return <Text style={{ color: '#4caf50', fontWeight: '600' }}>Yogi Point here - Very Positive</Text>;
                    if (currentYogiData?.avayogi && currentYogiData.avayogi.sign === rashiIndex) 
                      return <Text style={{ color: '#f44336', fontWeight: '600' }}>Avayogi Point here - Very Negative</Text>;
                    return currentYogiData ? 
                      <Text style={{ color: '#666' }}>No special Yogi influence</Text> : 
                      <Text style={{ color: '#ff9800' }}>Loading...</Text>;
                  })()} 
                </Text>
              </View>
            </View>

            {/* Overall Assessment */}
            <View style={[styles.section, {
              backgroundColor: 'rgba(96, 125, 139, 0.1)',
              borderColor: 'rgba(96, 125, 139, 0.2)'
            }]}>
              <Text style={[styles.sectionTitle, { color: '#607d8b' }]}>📊 Overall Assessment</Text>
              {(() => {
                let positiveFactors = 0;
                let negativeFactors = 0;
                let neutralFactors = 0;
                
                // Count occupants
                planetsInHouse.forEach(planet => {
                  const lordships = getHouseLordship(planet.name);
                  const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet.name);
                  const isNaturalMalefic = ['Mars', 'Saturn', 'Sun', 'Rahu', 'Ketu'].includes(planet.name);
                  const hasTrikonaLordship = lordships.some(h => [1, 5, 9].includes(h));
                  const hasKendraLordship = lordships.some(h => [1, 4, 7, 10].includes(h));
                  
                  if (lordships.includes(6) || lordships.includes(8)) {
                    negativeFactors++;
                  } else if (isNaturalBenefic && (hasTrikonaLordship || hasKendraLordship)) {
                    positiveFactors++;
                  } else if (isNaturalMalefic) {
                    negativeFactors++;
                  } else {
                    neutralFactors++;
                  }
                });
                
                // Check special conditions
                const currentYogiData = yogiData || chartData.yogiData;
                if (currentYogiData?.dagdha_rashi?.sign === rashiIndex) negativeFactors++;
                if (currentYogiData?.tithi_shunya_rashi?.sign === rashiIndex) negativeFactors++;
                if (currentYogiData?.yogi?.sign === rashiIndex) positiveFactors++;
                if (currentYogiData?.avayogi?.sign === rashiIndex) negativeFactors++;
                
                let overallStatus = 'Neutral';
                let statusColor = '#ff9800';
                
                if (positiveFactors > negativeFactors) {
                  overallStatus = 'Favorable';
                  statusColor = '#4caf50';
                } else if (negativeFactors > positiveFactors) {
                  overallStatus = 'Challenging';
                  statusColor = '#f44336';
                }
                
                return (
                  <View>
                    <View style={styles.overallStatus}>
                      <Text style={styles.planetName}>House Status:</Text>
                      <Text style={[styles.status, { color: statusColor }]}>{overallStatus}</Text>
                    </View>
                    <View style={styles.factorCounts}>
                      <View style={styles.factorItem}>
                        <Text style={[styles.factorNumber, { color: '#4caf50' }]}>{positiveFactors}</Text>
                        <Text style={styles.factorLabel}>Positive</Text>
                      </View>
                      <View style={styles.factorItem}>
                        <Text style={[styles.factorNumber, { color: '#ff9800' }]}>{neutralFactors}</Text>
                        <Text style={styles.factorLabel}>Neutral</Text>
                      </View>
                      <View style={styles.factorItem}>
                        <Text style={[styles.factorNumber, { color: '#f44336' }]}>{negativeFactors}</Text>
                        <Text style={styles.factorLabel}>Negative</Text>
                      </View>
                    </View>
                  </View>
                );
              })()}
            </View>
          </ScrollView>
          
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <Text style={styles.closeButtonText}>Close Analysis</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modal: {
    backgroundColor: 'white',
    borderRadius: 20,
    width: '95%',
    maxHeight: '85%',
    overflow: 'hidden',
  },
  header: {
    backgroundColor: '#e91e63',
    padding: 20,
    alignItems: 'center',
  },
  headerTitle: {
    color: 'white',
    fontSize: 20,
    fontWeight: '600',
  },
  headerSubtitle: {
    color: 'white',
    fontSize: 14,
    opacity: 0.9,
    marginTop: 4,
  },
  content: {
    padding: 20,
    maxHeight: '70%',
  },
  section: {
    marginBottom: 20,
    borderRadius: 12,
    padding: 15,
    borderWidth: 1,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  planetItem: {
    backgroundColor: 'rgba(255,255,255,0.7)',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.1)',
  },
  planetName: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  planetDetail: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  ownSign: {
    fontSize: 12,
    color: '#4caf50',
    marginBottom: 2,
  },
  status: {
    fontSize: 12,
    fontWeight: '600',
    marginTop: 4,
  },
  emptyText: {
    fontSize: 13,
    color: '#666',
    fontStyle: 'italic',
    padding: 8,
  },
  overallStatus: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.7)',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.1)',
  },
  factorCounts: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  factorItem: {
    alignItems: 'center',
    padding: 8,
    backgroundColor: 'rgba(255,255,255,0.5)',
    borderRadius: 8,
    minWidth: 60,
  },
  factorNumber: {
    fontSize: 16,
    fontWeight: '600',
  },
  factorLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  closeButton: {
    backgroundColor: '#e91e63',
    margin: 20,
    padding: 15,
    borderRadius: 25,
    alignItems: 'center',
  },
  closeButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
});

export default HouseAnalysisModal;