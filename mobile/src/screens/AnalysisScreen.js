import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function AnalysisScreen() {
  const [selectedTab, setSelectedTab] = useState('houses');

  const analysisTypes = [
    { id: 'houses', name: 'Houses', icon: '🏠' },
    { id: 'planets', name: 'Planets', icon: '🪐' },
    { id: 'yogas', name: 'Yogas', icon: '🔮' },
    { id: 'dashas', name: 'Dashas', icon: '⏰' },
  ];

  const renderHouseAnalysis = () => (
    <View style={styles.analysisContent}>
      <Text style={styles.sectionTitle}>House Analysis</Text>
      {[1,2,3,4,5,6,7,8,9,10,11,12].map(house => (
        <View key={house} style={styles.analysisCard}>
          <Text style={styles.cardTitle}>House {house}</Text>
          <Text style={styles.cardDescription}>
            {getHouseDescription(house)}
          </Text>
          <View style={styles.cardDetails}>
            <Text style={styles.detailText}>Lord: Mars</Text>
            <Text style={styles.detailText}>Occupants: Sun, Mercury</Text>
            <Text style={styles.detailText}>Aspects: Jupiter (5th)</Text>
          </View>
        </View>
      ))}
    </View>
  );

  const renderPlanetAnalysis = () => (
    <View style={styles.analysisContent}>
      <Text style={styles.sectionTitle}>Planetary Analysis</Text>
      {['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].map(planet => (
        <View key={planet} style={styles.analysisCard}>
          <Text style={styles.cardTitle}>{planet}</Text>
          <Text style={styles.cardDescription}>
            {getPlanetDescription(planet)}
          </Text>
          <View style={styles.cardDetails}>
            <Text style={styles.detailText}>House: 1st</Text>
            <Text style={styles.detailText}>Sign: Aries</Text>
            <Text style={styles.detailText}>Degree: 15°30'</Text>
            <Text style={styles.detailText}>Nakshatra: Ashwini</Text>
          </View>
        </View>
      ))}
    </View>
  );

  const renderYogaAnalysis = () => (
    <View style={styles.analysisContent}>
      <Text style={styles.sectionTitle}>Yoga Analysis</Text>
      <View style={styles.analysisCard}>
        <Text style={styles.cardTitle}>Raja Yoga</Text>
        <Text style={styles.cardDescription}>
          Formed by Jupiter in 10th house aspecting the ascendant. This yoga brings success, recognition, and leadership qualities.
        </Text>
        <Text style={styles.strengthText}>Strength: Strong</Text>
      </View>
      <View style={styles.analysisCard}>
        <Text style={styles.cardTitle}>Dhana Yoga</Text>
        <Text style={styles.cardDescription}>
          Venus in 2nd house with Mercury creates wealth-generating combinations. Financial prosperity is indicated.
        </Text>
        <Text style={styles.strengthText}>Strength: Moderate</Text>
      </View>
    </View>
  );

  const renderDashaAnalysis = () => (
    <View style={styles.analysisContent}>
      <Text style={styles.sectionTitle}>Dasha Periods</Text>
      <View style={styles.analysisCard}>
        <Text style={styles.cardTitle}>Current Mahadasha</Text>
        <Text style={styles.cardDescription}>Jupiter Mahadasha (2020-2036)</Text>
        <Text style={styles.detailText}>
          Jupiter is well-placed in the 10th house, bringing career growth, wisdom, and spiritual development.
        </Text>
      </View>
      <View style={styles.analysisCard}>
        <Text style={styles.cardTitle}>Current Antardasha</Text>
        <Text style={styles.cardDescription}>Saturn Antardasha (2023-2025)</Text>
        <Text style={styles.detailText}>
          Period of hard work and discipline. Focus on building solid foundations for future success.
        </Text>
      </View>
    </View>
  );

  const getHouseDescription = (house) => {
    const descriptions = {
      1: "Self, personality, physical appearance, and overall life direction",
      2: "Wealth, family, speech, and material possessions",
      3: "Siblings, courage, communication, and short journeys",
      4: "Home, mother, education, and emotional foundations",
      5: "Children, creativity, intelligence, and past life karma",
      6: "Health, enemies, service, and daily work routine",
      7: "Marriage, partnerships, and business relationships",
      8: "Transformation, occult, longevity, and hidden matters",
      9: "Higher learning, spirituality, luck, and long journeys",
      10: "Career, reputation, status, and public image",
      11: "Gains, friends, hopes, and aspirations",
      12: "Losses, expenses, spirituality, and foreign connections"
    };
    return descriptions[house] || "House analysis";
  };

  const getPlanetDescription = (planet) => {
    const descriptions = {
      Sun: "Represents soul, ego, father, authority, and leadership qualities",
      Moon: "Represents mind, emotions, mother, and mental peace",
      Mars: "Represents energy, courage, siblings, and physical strength",
      Mercury: "Represents intelligence, communication, and analytical abilities",
      Jupiter: "Represents wisdom, spirituality, teachers, and good fortune",
      Venus: "Represents love, beauty, relationships, and material comforts",
      Saturn: "Represents discipline, hard work, delays, and life lessons"
    };
    return descriptions[planet] || "Planetary analysis";
  };

  const renderContent = () => {
    switch (selectedTab) {
      case 'houses': return renderHouseAnalysis();
      case 'planets': return renderPlanetAnalysis();
      case 'yogas': return renderYogaAnalysis();
      case 'dashas': return renderDashaAnalysis();
      default: return renderHouseAnalysis();
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Astrological Analysis</Text>
        
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false}
          style={styles.tabSelector}
        >
          {analysisTypes.map((type) => (
            <TouchableOpacity
              key={type.id}
              style={[
                styles.tab,
                selectedTab === type.id && styles.activeTab
              ]}
              onPress={() => setSelectedTab(type.id)}
            >
              <Text style={styles.tabIcon}>{type.icon}</Text>
              <Text style={[
                styles.tabText,
                selectedTab === type.id && styles.activeTabText
              ]}>
                {type.name}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      <ScrollView style={styles.content}>
        {renderContent()}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    backgroundColor: 'white',
    paddingVertical: 15,
    paddingHorizontal: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 5,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#e91e63',
    textAlign: 'center',
    marginBottom: 15,
  },
  tabSelector: {
    flexDirection: 'row',
  },
  tab: {
    backgroundColor: '#f0f0f0',
    borderRadius: 20,
    paddingVertical: 10,
    paddingHorizontal: 15,
    marginRight: 10,
    alignItems: 'center',
    minWidth: 80,
  },
  activeTab: {
    backgroundColor: '#e91e63',
  },
  tabIcon: {
    fontSize: 20,
    marginBottom: 4,
  },
  tabText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '600',
  },
  activeTabText: {
    color: 'white',
  },
  content: {
    flex: 1,
  },
  analysisContent: {
    padding: 15,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  analysisCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#e91e63',
    marginBottom: 8,
  },
  cardDescription: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
    marginBottom: 10,
  },
  cardDetails: {
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingTop: 10,
  },
  detailText: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  strengthText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginTop: 5,
  },
});