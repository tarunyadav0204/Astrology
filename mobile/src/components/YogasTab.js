import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Modal } from 'react-native';

export default function YogasTab({ chartData, birthData }) {
  const [yogas, setYogas] = useState([]);
  const [selectedYoga, setSelectedYoga] = useState(null);
  const [loading, setLoading] = useState(true);

  // Common data used across multiple yoga checks (0-indexed signs)
  const exaltationSigns = { 'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 'Jupiter': 3, 'Venus': 11, 'Saturn': 6 };
  const debilitationSigns = { 'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11, 'Jupiter': 9, 'Venus': 5, 'Saturn': 0 };
  const ownSigns = { 'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5], 'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10] };

  useEffect(() => {
    if (chartData && birthData) {
      calculateYogas();
    }
  }, [chartData, birthData]);

  const calculateYogas = () => {
    setLoading(true);
    
    if (!chartData?.planets) {
      setYogas([]);
      setLoading(false);
      return;
    }
    
    const detectedYogas = [];
    const planets = chartData.planets;
    const mainPlanets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

    // Gaja Kesari Yoga - Jupiter in Kendra from Moon
    if (planets.Moon && planets.Jupiter) {
      const moonSign = planets.Moon.sign;
      const jupiterSign = planets.Jupiter.sign;
      const kendraFromMoon = [moonSign, (moonSign + 3) % 12 || 12, (moonSign + 6) % 12 || 12, (moonSign + 9) % 12 || 12];
      
      if (kendraFromMoon.includes(jupiterSign)) {
        detectedYogas.push({
          name: 'Gaja Kesari Yoga',
          type: 'Raja Yoga',
          strength: 'Strong',
          description: 'Jupiter is in Kendra from Moon, creating the auspicious Gaja Kesari Yoga.',
          effects: 'Fame, respect, intelligence, good character, leadership qualities, prosperity, long life.',
          planets: ['Moon', 'Jupiter'],
          houses: [moonSign, jupiterSign]
        });
      }
    }

    // Chandra Mangal Yoga - Moon and Mars together
    if (planets.Moon && planets.Mars && planets.Moon.sign === planets.Mars.sign) {
      detectedYogas.push({
        name: 'Chandra Mangal Yoga',
        type: 'Wealth Yoga',
        strength: 'Medium',
        description: 'Moon and Mars are conjunct in the same sign.',
        effects: 'Business acumen, wealth through real estate, property gains, material prosperity.',
        planets: ['Moon', 'Mars'],
        houses: [planets.Moon.sign]
      });
    }

    // Budh Aditya Yoga - Sun and Mercury together
    if (planets.Sun && planets.Mercury && planets.Sun.sign === planets.Mercury.sign) {
      detectedYogas.push({
        name: 'Budh Aditya Yoga',
        type: 'Intelligence Yoga',
        strength: 'Medium',
        description: 'Sun and Mercury are conjunct in the same sign.',
        effects: 'Intelligence, communication skills, administrative abilities, success in education and career.',
        planets: ['Sun', 'Mercury'],
        houses: [planets.Sun.sign]
      });
    }

    // Guru Mangal Yoga - Jupiter and Mars together
    if (planets.Jupiter && planets.Mars && planets.Jupiter.sign === planets.Mars.sign) {
      detectedYogas.push({
        name: 'Guru Mangal Yoga',
        type: 'Leadership Yoga',
        strength: 'Strong',
        description: 'Jupiter and Mars are conjunct in the same sign.',
        effects: 'Leadership, courage, spiritual wisdom, success in ventures, good fortune.',
        planets: ['Jupiter', 'Mars'],
        houses: [planets.Jupiter.sign]
      });
    }

    // Shukra Guru Yoga - Venus and Jupiter together
    if (planets.Venus && planets.Jupiter && planets.Venus.sign === planets.Jupiter.sign) {
      detectedYogas.push({
        name: 'Shukra Guru Yoga',
        type: 'Prosperity Yoga',
        strength: 'Strong',
        description: 'Venus and Jupiter are conjunct in the same sign.',
        effects: 'Wealth, luxury, artistic talents, spiritual growth, harmonious relationships.',
        planets: ['Venus', 'Jupiter'],
        houses: [planets.Venus.sign]
      });
    }

    // Pancha Mahapurusha Yogas - need ascendant to calculate houses
    if (chartData.ascendant) {
      const mahapurushaYogas = [
        { planet: 'Mars', yoga: 'Ruchaka Yoga', effects: 'Courage, leadership, military success, physical strength, commanding personality.' },
        { planet: 'Mercury', yoga: 'Bhadra Yoga', effects: 'Intelligence, communication skills, business acumen, scholarly achievements, wit.' },
        { planet: 'Jupiter', yoga: 'Hamsa Yoga', effects: 'Wisdom, spirituality, teaching abilities, respect, moral character, prosperity.' },
        { planet: 'Venus', yoga: 'Malavya Yoga', effects: 'Beauty, artistic talents, luxury, comfort, harmonious relationships, creativity.' },
        { planet: 'Saturn', yoga: 'Sasha Yoga', effects: 'Discipline, hard work, organizational skills, authority, longevity, patience.' }
      ];

      mahapurushaYogas.forEach(({ planet, yoga, effects }) => {
        if (planets[planet]) {
          const planetSign = planets[planet].sign;
          
          // Calculate house position from ascendant
          const ascendantSign = chartData.ascendant;
          let housePosition = planetSign - ascendantSign + 1;
          if (housePosition <= 0) housePosition += 12;
          
          const isInKendra = [1, 4, 7, 10].includes(housePosition);
          const isExalted = exaltationSigns[planet] === planetSign;
          const isOwnSign = ownSigns[planet]?.includes(planetSign);
          
          if (isInKendra && (isExalted || isOwnSign)) {
            detectedYogas.push({
              name: yoga,
              type: 'Pancha Mahapurusha Yoga',
              strength: 'Very Strong',
              description: `${planet} is in its ${isExalted ? 'exaltation' : 'own sign'} in ${housePosition}th house (Kendra).`,
              effects: effects,
              planets: [planet],
              houses: [housePosition]
            });
          }
        }
      });
    }

    // Neecha Bhanga Raja Yoga - Debilitated planet with cancellation
    mainPlanets.forEach(planet => {
      if (planets[planet]) {
        const planetSign = planets[planet].sign;
        const isDebilitated = debilitationSigns[planet] === planetSign;
        
        if (isDebilitated) {
          // Check if debilitation is cancelled by exalted planet in same sign
          const sameSignPlanets = mainPlanets.filter(p => 
            p !== planet && planets[p] && planets[p].sign === planetSign
          );
          
          const hasExaltedPlanet = sameSignPlanets.some(p => 
            exaltationSigns[p] === planets[p].sign
          );
          
          if (hasExaltedPlanet) {
            detectedYogas.push({
              name: 'Neecha Bhanga Raja Yoga',
              type: 'Raja Yoga',
              strength: 'Strong',
              description: `${planet} is debilitated but cancellation creates Raja Yoga.`,
              effects: 'Rise from humble beginnings to great heights, unexpected success, overcoming obstacles.',
              planets: [planet],
              houses: [planetSign]
            });
          }
        }
      }
    });

    // Kala Sarpa Dosha - All planets between Rahu and Ketu
    if (planets.Rahu && planets.Ketu) {
      const rahuSign = planets.Rahu.sign;
      const ketuSign = planets.Ketu.sign;
      
      const allPlanetsBetween = mainPlanets.every(planet => {
        if (!planets[planet]) return true;
        const planetSign = planets[planet].sign;
        
        // Check if planet is between Rahu and Ketu
        if (rahuSign < ketuSign) {
          return planetSign > rahuSign && planetSign < ketuSign;
        } else {
          return planetSign > rahuSign || planetSign < ketuSign;
        }
      });
      
      if (allPlanetsBetween) {
        detectedYogas.push({
          name: 'Kala Sarpa Dosha',
          type: 'Dosha',
          strength: 'Negative',
          description: 'All planets are hemmed between Rahu and Ketu.',
          effects: 'Obstacles, delays, struggles in life, but can give spiritual growth and ultimate success.',
          planets: ['Rahu', 'Ketu'],
          houses: [rahuSign, ketuSign],
          remedies: 'Rahu-Ketu remedies, Sarpa Dosha puja, charity, and spiritual practices.'
        });
      }
    }

    // Kemadrum Yoga - Moon isolated
    if (planets.Moon) {
      const moonSign = planets.Moon.sign;
      const prevSign = moonSign === 1 ? 12 : moonSign - 1;
      const nextSign = moonSign === 12 ? 1 : moonSign + 1;
      
      const planetsInMoonSign = mainPlanets.filter(p => 
        p !== 'Moon' && planets[p] && planets[p].sign === moonSign
      );
      
      const planetsInPrevSign = mainPlanets.filter(p => 
        planets[p] && planets[p].sign === prevSign
      );
      
      const planetsInNextSign = mainPlanets.filter(p => 
        planets[p] && planets[p].sign === nextSign
      );
      
      if (planetsInMoonSign.length === 0 && planetsInPrevSign.length === 0 && planetsInNextSign.length === 0) {
        detectedYogas.push({
          name: 'Kemadrum Yoga',
          type: 'Dosha',
          strength: 'Negative',
          description: 'Moon has no planets on either side, creating isolation.',
          effects: 'Mental stress, emotional instability, financial difficulties, lack of support.',
          planets: ['Moon'],
          houses: [moonSign],
          remedies: 'Strengthen Moon through pearl gemstone, Moon mantras, and Monday fasting.'
        });
      }
    }

    setYogas(detectedYogas);
    setLoading(false);
  };

  const getStrengthColor = (strength) => {
    switch (strength) {
      case 'Very Strong': return '#22c55e';
      case 'Strong': return '#3b82f6';
      case 'Medium': return '#f59e0b';
      case 'Negative': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'Raja Yoga': return '#8b5cf6';
      case 'Wealth Yoga': return '#10b981';
      case 'Intelligence Yoga': return '#f59e0b';
      case 'Leadership Yoga': return '#22c55e';
      case 'Prosperity Yoga': return '#3b82f6';
      case 'Pancha Mahapurusha Yoga': return '#f59e0b';
      case 'Dosha': return '#ef4444';
      default: return '#6b7280';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Analyzing Yogas...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>🔮 Detected Yogas ({yogas.length})</Text>
      
      <ScrollView style={styles.yogasList}>
        {yogas.length === 0 ? (
          <View style={styles.noYogasContainer}>
            <Text style={styles.noYogasText}>No significant yogas detected in this chart.</Text>
          </View>
        ) : (
          yogas.map((yoga, index) => (
            <TouchableOpacity 
              key={index} 
              style={styles.yogaCard}
              onPress={() => setSelectedYoga(yoga)}
            >
              <View style={styles.yogaHeader}>
                <Text style={styles.yogaName}>{yoga.name}</Text>
                <Text style={[
                  styles.strengthBadge,
                  { backgroundColor: getStrengthColor(yoga.strength) }
                ]}>
                  {yoga.strength}
                </Text>
              </View>
              
              <View style={styles.yogaTags}>
                <Text style={[
                  styles.typeBadge,
                  { backgroundColor: getTypeColor(yoga.type) }
                ]}>
                  {yoga.type}
                </Text>
                {yoga.planets && (
                  <Text style={styles.planetsText}>
                    {yoga.planets.join(', ')}
                  </Text>
                )}
              </View>
              
              <Text style={styles.yogaDescription}>
                {yoga.description.length > 80 ? 
                  `${yoga.description.substring(0, 80)}...` : 
                  yoga.description
                }
              </Text>
            </TouchableOpacity>
          ))
        )}
      </ScrollView>

      {/* Detailed Yoga Modal */}
      <Modal
        visible={selectedYoga !== null}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setSelectedYoga(null)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>🔮 {selectedYoga?.name}</Text>
            <TouchableOpacity 
              onPress={() => setSelectedYoga(null)}
              style={styles.closeButton}
            >
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.modalContent}>
            <View style={styles.modalInfo}>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Type:</Text>
                <Text style={[
                  styles.typeBadge,
                  { backgroundColor: getTypeColor(selectedYoga?.type) }
                ]}>
                  {selectedYoga?.type}
                </Text>
              </View>
              
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Strength:</Text>
                <Text style={[
                  styles.strengthBadge,
                  { backgroundColor: getStrengthColor(selectedYoga?.strength) }
                ]}>
                  {selectedYoga?.strength}
                </Text>
              </View>
              
              {selectedYoga?.planets && (
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>Planets:</Text>
                  <Text style={styles.infoValue}>{selectedYoga.planets.join(', ')}</Text>
                </View>
              )}
              
              {selectedYoga?.houses && (
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>Signs:</Text>
                  <Text style={styles.infoValue}>{selectedYoga.houses.join(', ')}</Text>
                </View>
              )}
            </View>
            
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>📖 Description</Text>
              <Text style={styles.sectionText}>{selectedYoga?.description}</Text>
            </View>
            
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>✨ Effects</Text>
              <Text style={styles.sectionText}>{selectedYoga?.effects}</Text>
            </View>
            
            {selectedYoga?.remedies && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>💎 Remedies</Text>
                <Text style={styles.sectionText}>{selectedYoga.remedies}</Text>
              </View>
            )}
          </ScrollView>
        </View>
      </Modal>
    </View>
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
    padding: 32,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#e91e63',
    textAlign: 'center',
    marginBottom: 16,
  },
  yogasList: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#e91e63',
    borderRadius: 8,
  },
  noYogasContainer: {
    padding: 32,
    alignItems: 'center',
  },
  noYogasText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  yogaCard: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    backgroundColor: 'white',
  },
  yogaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  yogaName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
    flex: 1,
  },
  strengthBadge: {
    fontSize: 11,
    fontWeight: '600',
    color: 'white',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 12,
    overflow: 'hidden',
  },
  yogaTags: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
    gap: 8,
  },
  typeBadge: {
    fontSize: 11,
    color: 'white',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
    overflow: 'hidden',
  },
  planetsText: {
    fontSize: 11,
    color: '#666',
  },
  yogaDescription: {
    fontSize: 12,
    color: '#666',
    lineHeight: 16,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'white',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e91e63',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#e91e63',
    flex: 1,
  },
  closeButton: {
    padding: 8,
    backgroundColor: '#e91e63',
    borderRadius: 4,
  },
  closeButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
  modalInfo: {
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  infoLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    minWidth: 60,
  },
  infoValue: {
    fontSize: 14,
    color: '#333',
    flex: 1,
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    color: '#ff6f00',
  },
  sectionText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#333',
    textAlign: 'justify',
  },
});