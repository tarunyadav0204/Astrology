import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { apiService } from '../services/apiService';

export default function HouseAnalysisTab({ chartData, birthData }) {
  const [houseData, setHouseData] = useState([]);
  const [selectedHouse, setSelectedHouse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailedAnalysis, setDetailedAnalysis] = useState(null);
  useEffect(() => {
    if (chartData && birthData) {
      fetchHouseAnalysis();
    }
  }, [chartData, birthData]);
  
  const fetchHouseAnalysis = async () => {
    setLoading(true);
    try {
      // Use the same analysis logic as the existing modal
      analyzeHousesDetailed();
    } catch (error) {
      console.error('Error analyzing houses:', error);
      analyzeHousesBasic();
    }
    setLoading(false);
  };
  
  const analyzeHousesDetailed = () => {
    const houseSignifications = {
      1: "Self, personality, physical appearance, overall life direction",
      2: "Wealth, family, speech, material possessions",
      3: "Siblings, courage, communication, short journeys",
      4: "Home, mother, education, emotional foundations",
      5: "Children, creativity, intelligence, past life karma",
      6: "Health, enemies, service, daily work routine",
      7: "Marriage, partnerships, business relationships",
      8: "Transformation, occult, longevity, hidden matters",
      9: "Higher learning, spirituality, luck, long journeys",
      10: "Career, reputation, status, public image",
      11: "Gains, friends, hopes, aspirations",
      12: "Losses, expenses, spirituality, foreign connections"
    };
    
    const houseLords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
    const houses = [];
    
    for (let i = 1; i <= 12; i++) {
      const houseIndex = i - 1;
      const rashiIndex = getRashiForHouse(houseIndex);
      const houseLord = houseLords[rashiIndex];
      const planetsInHouse = getPlanetsInHouse(houseIndex);
      
      // Calculate overall assessment
      let positiveFactors = 0;
      let negativeFactors = 0;
      
      planetsInHouse.forEach(planet => {
        const lordships = getHouseLordship(planet.name);
        const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet.name);
        const hasTrikonaLordship = lordships.some(h => [1, 5, 9].includes(h));
        const hasKendraLordship = lordships.some(h => [1, 4, 7, 10].includes(h));
        
        if (lordships.includes(6) || lordships.includes(8)) {
          negativeFactors++;
        } else if (isNaturalBenefic && (hasTrikonaLordship || hasKendraLordship)) {
          positiveFactors++;
        } else if (['Mars', 'Saturn', 'Sun', 'Rahu', 'Ketu'].includes(planet.name)) {
          negativeFactors++;
        }
      });
      
      // Add aspects analysis
      const aspectingPlanets = getAspectingPlanets(i);
      aspectingPlanets.forEach(aspect => {
        const lordships = getHouseLordship(aspect.planet);
        const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(aspect.planet);
        const isMaleficLord = lordships.some(h => [6, 8, 12].includes(h));
        
        if (isNaturalBenefic && !isMaleficLord) {
          positiveFactors++;
        } else if (!isNaturalBenefic || isMaleficLord) {
          negativeFactors++;
        }
      });
      
      let overallStatus = 'Neutral';
      let strengthScore = 50;
      
      if (positiveFactors > negativeFactors) {
        overallStatus = 'Favorable';
        strengthScore = 70 + (positiveFactors * 5);
      } else if (negativeFactors > positiveFactors) {
        overallStatus = 'Challenging';
        strengthScore = 30 - (negativeFactors * 5);
      }
      
      houses.push({
        number: i,
        name: `House ${i}`,
        significations: houseSignifications[i],
        signName: getSignName(rashiIndex),
        lord: houseLord,
        occupants: planetsInHouse.map(p => p.name),
        planetsData: planetsInHouse,
        isEmpty: planetsInHouse.length === 0,
        strength: overallStatus,
        strengthScore: Math.max(0, Math.min(100, strengthScore)),
        rashiIndex,
        positiveFactors,
        negativeFactors,
        aspectingPlanets
      });
    }
    setHouseData(houses);
  };
  
  const getAspectingPlanets = (houseNumber) => {
    if (!chartData?.planets) return [];
    
    const aspectingPlanets = [];
    const ascendantSign = chartData.houses?.[0]?.sign || 0;
    
    Object.entries(chartData.planets).forEach(([name, data]) => {
      const planetSign = data.sign;
      const planetHouse = ((planetSign - ascendantSign + 12) % 12) + 1;
      let aspects = [];
      
      // 7th aspect for all planets except Rahu/Ketu
      if (!['Rahu', 'Ketu'].includes(name)) {
        const seventhHouse = (planetHouse + 6) % 12 || 12;
        if (seventhHouse === houseNumber) aspects.push('7th');
      }
      
      // Special aspects
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
        aspectingPlanets.push({ planet: name, aspects, lordships });
      }
    });
    
    return aspectingPlanets;
  };
  
  const analyzeHousesBasic = () => {
    const houseSignifications = {
      1: "Self, personality, physical appearance, overall life direction",
      2: "Wealth, family, speech, material possessions",
      3: "Siblings, courage, communication, short journeys",
      4: "Home, mother, education, emotional foundations",
      5: "Children, creativity, intelligence, past life karma",
      6: "Health, enemies, service, daily work routine",
      7: "Marriage, partnerships, business relationships",
      8: "Transformation, occult, longevity, hidden matters",
      9: "Higher learning, spirituality, luck, long journeys",
      10: "Career, reputation, status, public image",
      11: "Gains, friends, hopes, aspirations",
      12: "Losses, expenses, spirituality, foreign connections"
    };
    
    const houses = [];
    for (let i = 1; i <= 12; i++) {
      const occupants = getPlanetsInHouse(i);
      houses.push({
        number: i,
        name: `House ${i}`,
        significations: houseSignifications[i],
        occupants: occupants.map(p => p),
        isEmpty: occupants.length === 0,
        strength: 'Neutral',
        strengthScore: 50
      });
    }
    setHouseData(houses);
  };
  
  const getRashiForHouse = (houseIndex) => {
    if (!chartData?.houses) return 0;
    const ascendantSign = chartData.houses[0]?.sign || 0;
    return (ascendantSign + houseIndex) % 12;
  };
  
  const getHouseLordship = (planet) => {
    if (!chartData?.houses) return [];
    const ascendantSign = chartData.houses[0]?.sign || 0;
    const signLordships = {
      'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5], 
      'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
    };
    const planetSigns = signLordships[planet] || [];
    return planetSigns.map(sign => ((sign - ascendantSign + 12) % 12) + 1);
  };
  
  const getSignName = (sign) => {
    const signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                   'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
    return signs[sign] || 'Unknown';
  };

  const getPlanetsInHouse = (houseIndex) => {
    if (!chartData?.planets) return [];
    const ascendantSign = chartData.houses?.[0]?.sign || 0;
    
    return Object.entries(chartData.planets)
      .filter(([name, data]) => {
        const planetHouse = ((data.sign - ascendantSign + 12) % 12);
        return planetHouse === houseIndex;
      })
      .map(([name, data]) => ({ name, ...data }));
  };

  const getStrengthColor = (strength) => {
    if (typeof strength === 'string') {
      switch (strength) {
        case 'Favorable': return '#4caf50';
        case 'Challenging': return '#f44336';
        case 'Neutral': return '#ff9800';
        default: return '#6b7280';
      }
    }
    if (strength >= 70) return '#4caf50';
    if (strength >= 40) return '#ff9800';
    return '#f44336';
  };
  
  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#e91e63" />
        <Text style={styles.loadingText}>Analyzing Houses...</Text>
      </View>
    );
  }
  
  if (selectedHouse) {
    return (
      <ScrollView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity 
            onPress={() => setSelectedHouse(null)}
            style={styles.backButton}
          >
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.selectedTitle}>🏠 {selectedHouse.name}</Text>
        </View>
        
        <View style={styles.detailCard}>
          <View style={styles.basicInfo}>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>House:</Text>
              <Text style={styles.infoValue}>{selectedHouse.number}</Text>
            </View>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Sign:</Text>
              <Text style={styles.infoValue}>{selectedHouse.signName}</Text>
            </View>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Lord:</Text>
              <Text style={styles.infoValue}>{selectedHouse.lord}</Text>
            </View>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Strength:</Text>
              <View style={[styles.strengthBadge, { backgroundColor: getStrengthColor(selectedHouse.strength) }]}>
                <Text style={styles.strengthText}>{selectedHouse.strength}</Text>
              </View>
            </View>
          </View>
          
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>📖 Significations</Text>
            <Text style={styles.sectionText}>{selectedHouse.significations}</Text>
          </View>
          
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>👥 Occupants Analysis</Text>
            {selectedHouse.isEmpty ? (
              <Text style={styles.emptyText}>Empty house</Text>
            ) : (
              selectedHouse.planetsData?.map((planet, idx) => {
                const lordships = getHouseLordship(planet.name);
                const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet.name);
                const isNaturalMalefic = ['Mars', 'Saturn', 'Sun', 'Rahu', 'Ketu'].includes(planet.name);
                const hasTrikonaLordship = lordships.some(h => [1, 5, 9].includes(h));
                const hasKendraLordship = lordships.some(h => [1, 4, 7, 10].includes(h));
                
                let status = '';
                if (lordships.includes(6)) {
                  status = 'Negative';
                } else if (lordships.includes(8)) {
                  status = hasTrikonaLordship ? 'Mixed (8th lord negative dominates)' : 'Negative';
                } else if (lordships.includes(12)) {
                  status = hasTrikonaLordship || hasKendraLordship ? 'Mixed' : 'Negative';
                } else if (isNaturalBenefic && (hasTrikonaLordship || hasKendraLordship)) {
                  status = 'Positive';
                } else if (isNaturalMalefic) {
                  status = 'Negative';
                } else {
                  status = 'Neutral';
                }
                
                return (
                  <View key={idx} style={styles.planetAnalysis}>
                    <Text style={styles.planetName}>
                      {planet.name}: {isNaturalBenefic ? 'Benefic' : isNaturalMalefic ? 'Malefic' : 'Neutral'}
                    </Text>
                    {lordships.length > 0 && (
                      <Text style={styles.planetDetail}>• Lord of {lordships.join(', ')}</Text>
                    )}
                    <Text style={[styles.status, { 
                      color: status === 'Positive' ? '#4caf50' : 
                             status === 'Negative' ? '#f44336' : '#ff9800' 
                    }]}>
                      ● {status}
                    </Text>
                  </View>
                );
              })
            )}
          </View>
          
          {selectedHouse.aspectingPlanets?.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>🎯 Aspects Analysis</Text>
              {selectedHouse.aspectingPlanets.map((aspect, idx) => {
                const lordships = aspect.lordships || [];
                const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(aspect.planet);
                const isMaleficLord = lordships.some(h => [6, 8, 12].includes(h));
                
                let aspectNature = isNaturalBenefic && !isMaleficLord ? 'Positive' : 
                                 !isNaturalBenefic || isMaleficLord ? 'Negative' : 'Mixed';
                
                return (
                  <View key={idx} style={styles.planetAnalysis}>
                    <Text style={styles.planetName}>
                      {aspect.planet} {aspect.aspects.join(', ')} aspect
                    </Text>
                    {lordships.length > 0 && (
                      <Text style={styles.planetDetail}>• Lord of {lordships.join(', ')}</Text>
                    )}
                    <Text style={[styles.status, { 
                      color: aspectNature === 'Positive' ? '#4caf50' : 
                             aspectNature === 'Negative' ? '#f44336' : '#ff9800' 
                    }]}>
                      ● {aspectNature}
                    </Text>
                  </View>
                );
              })}
            </View>
          )}
          
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>📊 Overall Assessment</Text>
            <View style={styles.overallStatus}>
              <Text style={styles.planetName}>House Status:</Text>
              <Text style={[styles.status, { color: getStrengthColor(selectedHouse.strength) }]}>
                {selectedHouse.strength}
              </Text>
            </View>
            <View style={styles.factorCounts}>
              <View style={styles.factorItem}>
                <Text style={[styles.factorNumber, { color: '#4caf50' }]}>
                  {selectedHouse.positiveFactors || 0}
                </Text>
                <Text style={styles.factorLabel}>Positive</Text>
              </View>
              <View style={styles.factorItem}>
                <Text style={[styles.factorNumber, { color: '#f44336' }]}>
                  {selectedHouse.negativeFactors || 0}
                </Text>
                <Text style={styles.factorLabel}>Negative</Text>
              </View>
            </View>
            <Text style={styles.scoreText}>Score: {selectedHouse.strengthScore?.toFixed(1)}/100</Text>
          </View>
          

        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>🏠 House Analysis</Text>
      
      {houseData.map(house => (
        <TouchableOpacity 
          key={house.number} 
          style={styles.houseCard}
          onPress={() => setSelectedHouse(house)}
        >
          <View style={styles.houseHeader}>
            <Text style={styles.houseTitle}>{house.name}</Text>
            <View style={[styles.strengthBadge, { backgroundColor: getStrengthColor(house.strength) }]}>
              <Text style={styles.strengthText}>{house.strength}</Text>
            </View>
          </View>
          
          <Text style={styles.houseSignification}>
            {house.significations.length > 80 ? 
              `${house.significations.substring(0, 80)}...` : 
              house.significations
            }
          </Text>
          
          <View style={styles.houseDetails}>
            <Text style={styles.detailLabel}>Lord:</Text>
            <Text style={styles.detailValue}>{house.lord || 'Unknown'}</Text>
          </View>
          
          <View style={styles.houseDetails}>
            <Text style={styles.detailLabel}>Occupants:</Text>
            <Text style={styles.detailValue}>
              {house.occupants.length > 0 ? house.occupants.join(', ') : 'None'}
            </Text>
          </View>
          
          {house.signName && (
            <View style={styles.houseDetails}>
              <Text style={styles.detailLabel}>Sign:</Text>
              <Text style={styles.detailValue}>{house.signName}</Text>
            </View>
          )}
          
          <Text style={styles.tapHint}>Tap for detailed analysis →</Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#e91e63',
    textAlign: 'center',
    marginBottom: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  backButton: {
    backgroundColor: '#e91e63',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginRight: 12,
  },
  backButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  selectedTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#e91e63',
    flex: 1,
  },
  houseCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
    borderLeftWidth: 4,
    borderLeftColor: '#e91e63',
  },
  houseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  houseTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#e91e63',
    flex: 1,
  },
  strengthBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  strengthText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  houseSignification: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
    marginBottom: 12,
  },
  houseDetails: {
    flexDirection: 'row',
    marginBottom: 6,
  },
  detailLabel: {
    fontSize: 13,
    color: '#666',
    width: 80,
    fontWeight: '600',
  },
  detailValue: {
    fontSize: 13,
    color: '#333',
    flex: 1,
  },
  tapHint: {
    fontSize: 12,
    color: '#e91e63',
    fontStyle: 'italic',
    textAlign: 'right',
    marginTop: 8,
  },
  detailCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  basicInfo: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  infoLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#e91e63',
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ff6f00',
    marginBottom: 8,
  },
  sectionText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#333',
    textAlign: 'justify',
  },
  additionalInfo: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  additionalLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginTop: 4,
  },
  additionalText: {
    fontSize: 12,
    color: '#333',
    marginBottom: 4,
  },
  emptyText: {
    fontSize: 14,
    color: '#999',
    fontStyle: 'italic',
  },
  planetsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  planetBadge: {
    backgroundColor: '#e91e63',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  planetText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  planetAnalysis: {
    backgroundColor: 'rgba(255,255,255,0.7)',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.1)',
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
    marginBottom: 8,
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
  scoreText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    fontWeight: '600',
  },
  eventsContainer: {
    marginTop: 8,
  },
  eventsTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
    marginBottom: 4,
  },
  eventText: {
    fontSize: 12,
    color: '#333',
    marginBottom: 2,
  },
  remedyText: {
    fontSize: 12,
    color: '#333',
    marginBottom: 4,
  },
});