import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';

export default function RelationshipsTab({ chartData, birthData }) {
  const [selectedMatrix, setSelectedMatrix] = useState('permanent');
  const [loading, setLoading] = useState(true);
  const [matrices, setMatrices] = useState(null);

  const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
  const planetAbbr = { 'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me', 'Jupiter': 'Ju', 'Venus': 'Ve', 'Saturn': 'Sa' };

  useEffect(() => {
    if (chartData && birthData) {
      calculateRelationshipMatrices();
    }
  }, [chartData, birthData]);

  const calculateRelationshipMatrices = () => {
    setLoading(true);
    
    if (!chartData?.planets) {
      setMatrices(null);
      setLoading(false);
      return;
    }

    const permanent = getPermanentFriendships();
    const temporal = getTemporalFriendships();
    const fiveFold = getFiveFoldFriendships(permanent, temporal);

    setMatrices({ permanent, temporal, fiveFold });
    setLoading(false);
  };

  const getPermanentFriendships = () => {
    return {
      'Sun': { 'Moon': 'F', 'Mars': 'F', 'Mercury': 'N', 'Jupiter': 'F', 'Venus': 'E', 'Saturn': 'E' },
      'Moon': { 'Sun': 'F', 'Mars': 'N', 'Mercury': 'F', 'Jupiter': 'N', 'Venus': 'N', 'Saturn': 'N' },
      'Mars': { 'Sun': 'F', 'Moon': 'N', 'Mercury': 'N', 'Jupiter': 'F', 'Venus': 'N', 'Saturn': 'E' },
      'Mercury': { 'Sun': 'F', 'Moon': 'E', 'Mars': 'N', 'Jupiter': 'N', 'Venus': 'F', 'Saturn': 'N' },
      'Jupiter': { 'Sun': 'F', 'Moon': 'N', 'Mars': 'F', 'Mercury': 'E', 'Venus': 'E', 'Saturn': 'N' },
      'Venus': { 'Sun': 'E', 'Moon': 'E', 'Mars': 'E', 'Mercury': 'F', 'Jupiter': 'N', 'Saturn': 'F' },
      'Saturn': { 'Sun': 'E', 'Moon': 'E', 'Mars': 'E', 'Mercury': 'F', 'Jupiter': 'E', 'Venus': 'F' }
    };
  };

  const getTemporalFriendships = () => {
    const temporal = {};
    const chartPlanets = chartData.planets;
    
    planets.forEach(planet1 => {
      temporal[planet1] = {};
      
      planets.forEach(planet2 => {
        if (planet1 === planet2) {
          temporal[planet1][planet2] = '-';
          return;
        }
        
        if (!chartPlanets[planet1] || !chartPlanets[planet2]) {
          temporal[planet1][planet2] = 'N';
          return;
        }
        
        const planet1Sign = chartPlanets[planet1].sign;
        const planet2Sign = chartPlanets[planet2].sign;
        
        // Calculate house position of planet2 from planet1
        let houseFromPlanet1 = planet2Sign - planet1Sign + 1;
        if (houseFromPlanet1 <= 0) houseFromPlanet1 += 12;
        
        // Temporal friendship: 2,3,4,10,11,12 are friends, others are enemies
        const friendHouses = [2, 3, 4, 10, 11, 12];
        temporal[planet1][planet2] = friendHouses.includes(houseFromPlanet1) ? 'F' : 'E';
      });
    });
    
    return temporal;
  };

  const getFiveFoldFriendships = (permanent, temporal) => {
    const fiveFold = {};
    
    planets.forEach(planet1 => {
      fiveFold[planet1] = {};
      
      planets.forEach(planet2 => {
        if (planet1 === planet2) {
          fiveFold[planet1][planet2] = '-';
          return;
        }
        
        const perm = permanent[planet1][planet2];
        const temp = temporal[planet1][planet2];
        
        // Five-fold relationship calculation
        if (perm === 'F' && temp === 'F') fiveFold[planet1][planet2] = 'BF'; // Best Friend
        else if (perm === 'F' && temp === 'E') fiveFold[planet1][planet2] = 'N';  // Neutral
        else if (perm === 'F' && temp === 'N') fiveFold[planet1][planet2] = 'F';  // Friend
        else if (perm === 'E' && temp === 'F') fiveFold[planet1][planet2] = 'N';  // Neutral
        else if (perm === 'E' && temp === 'E') fiveFold[planet1][planet2] = 'GE'; // Great Enemy
        else if (perm === 'E' && temp === 'N') fiveFold[planet1][planet2] = 'E';  // Enemy
        else if (perm === 'N' && temp === 'F') fiveFold[planet1][planet2] = 'F';  // Friend
        else if (perm === 'N' && temp === 'E') fiveFold[planet1][planet2] = 'E';  // Enemy
        else fiveFold[planet1][planet2] = 'N'; // Neutral
      });
    });
    
    return fiveFold;
  };

  const getRelationshipColor = (relationship) => {
    switch (relationship) {
      case 'BF': return '#d1fae5'; // Best Friend - Light Green
      case 'F': return '#dbeafe';  // Friend - Light Blue
      case 'N': return '#fef3c7';  // Neutral - Light Yellow
      case 'E': return '#fee2e2';  // Enemy - Light Red
      case 'GE': return '#fecaca'; // Great Enemy - Light Pink
      case '-': return '#f3f4f6'; // Self - Light Gray
      default: return '#f9fafb';
    }
  };

  const getRelationshipTextColor = (relationship) => {
    switch (relationship) {
      case 'BF': return '#065f46'; // Best Friend - Dark Green
      case 'F': return '#1e40af';  // Friend - Dark Blue
      case 'N': return '#92400e';  // Neutral - Dark Yellow
      case 'E': return '#991b1b';  // Enemy - Dark Red
      case 'GE': return '#7f1d1d'; // Great Enemy - Darker Red
      case '-': return '#6b7280'; // Self - Gray
      default: return '#374151';
    }
  };

  const renderMatrix = (matrix, title) => {
    return (
      <View style={styles.matrixSection}>
        <Text style={styles.matrixTitle}>{title}</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.matrixContainer}>
            <View style={styles.matrixHeader}>
              <Text style={styles.headerCell}></Text>
              {planets.map(planet => (
                <Text key={planet} style={styles.headerCell}>{planetAbbr[planet]}</Text>
              ))}
            </View>
            
            {planets.map(planet1 => (
              <View key={planet1} style={styles.matrixRow}>
                <Text style={styles.rowHeader}>{planetAbbr[planet1]}</Text>
                {planets.map(planet2 => {
                  const relationship = matrix[planet1]?.[planet2] || 'N';
                  return (
                    <View 
                      key={planet2} 
                      style={[
                        styles.relationshipCell,
                        { backgroundColor: getRelationshipColor(relationship) }
                      ]}
                    >
                      <Text style={[
                        styles.relationshipText,
                        { color: getRelationshipTextColor(relationship) }
                      ]}>
                        {relationship}
                      </Text>
                    </View>
                  );
                })}
              </View>
            ))}
          </View>
        </ScrollView>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Calculating Friendship Matrices...</Text>
      </View>
    );
  }

  if (!matrices) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Unable to calculate relationships. Please check chart data.</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Matrix Selection Tabs */}
      <View style={styles.tabContainer}>
        {[
          { key: 'permanent', label: 'Permanent' },
          { key: 'temporal', label: 'Temporal' },
          { key: 'fiveFold', label: 'Five Fold' }
        ].map(tab => (
          <TouchableOpacity
            key={tab.key}
            onPress={() => setSelectedMatrix(tab.key)}
            style={[
              styles.tab,
              selectedMatrix === tab.key && styles.activeTab
            ]}
          >
            <Text style={[
              styles.tabText,
              selectedMatrix === tab.key && styles.activeTabText
            ]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Legend */}
      <View style={styles.legend}>
        {selectedMatrix === 'fiveFold' ? (
          <>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#d1fae5', borderColor: '#065f46' }]} />
              <Text style={styles.legendText}>BF - Best Friend</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#dbeafe', borderColor: '#1e40af' }]} />
              <Text style={styles.legendText}>F - Friend</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#fef3c7', borderColor: '#92400e' }]} />
              <Text style={styles.legendText}>N - Neutral</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#fee2e2', borderColor: '#991b1b' }]} />
              <Text style={styles.legendText}>E - Enemy</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#fecaca', borderColor: '#7f1d1d' }]} />
              <Text style={styles.legendText}>GE - Great Enemy</Text>
            </View>
          </>
        ) : (
          <>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#dbeafe', borderColor: '#1e40af' }]} />
              <Text style={styles.legendText}>F - Friend</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#fef3c7', borderColor: '#92400e' }]} />
              <Text style={styles.legendText}>N - Neutral</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#fee2e2', borderColor: '#991b1b' }]} />
              <Text style={styles.legendText}>E - Enemy</Text>
            </View>
          </>
        )}
      </View>

      {/* Matrix Display */}
      {selectedMatrix === 'permanent' && renderMatrix(matrices.permanent, '🤝 Permanent Friendship Matrix')}
      {selectedMatrix === 'temporal' && renderMatrix(matrices.temporal, '⏰ Temporal Friendship Matrix (Based on Chart Positions)')}
      {selectedMatrix === 'fiveFold' && renderMatrix(matrices.fiveFold, '🌟 Five Fold Friendship Matrix (Combined Result)')}
      
      <View style={styles.noteContainer}>
        <Text style={styles.noteText}><Text style={styles.noteTitle}>Note:</Text> Relationships are shown from row planet to column planet.</Text>
        {selectedMatrix === 'temporal' && (
          <Text style={styles.noteText}><Text style={styles.noteTitle}>Temporal Friendship:</Text> Based on house positions in the birth chart. Houses 2,3,4,10,11,12 from a planet are friends.</Text>
        )}
        {selectedMatrix === 'fiveFold' && (
          <Text style={styles.noteText}><Text style={styles.noteTitle}>Five Fold Friendship:</Text> Combines permanent and temporal relationships to give the final compound relationship.</Text>
        )}
      </View>
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
    padding: 32,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  tabContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e91e63',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderWidth: 1,
    borderColor: '#e91e63',
    borderBottomWidth: 0,
    borderTopLeftRadius: 8,
    borderTopRightRadius: 8,
    marginRight: 4,
  },
  activeTab: {
    backgroundColor: '#e91e63',
  },
  tabText: {
    textAlign: 'center',
    fontSize: 12,
    fontWeight: '600',
    color: '#e91e63',
  },
  activeTabText: {
    color: 'white',
  },
  legend: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    gap: 8,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
    marginBottom: 4,
  },
  legendColor: {
    width: 15,
    height: 15,
    borderRadius: 2,
    marginRight: 6,
    borderWidth: 1,
  },
  legendText: {
    fontSize: 11,
    color: '#333',
  },
  matrixSection: {
    backgroundColor: 'white',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    padding: 16,
    marginBottom: 16,
  },
  matrixTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#e91e63',
    marginBottom: 16,
  },
  matrixContainer: {
    minWidth: 280,
  },
  matrixHeader: {
    flexDirection: 'row',
    marginBottom: 4,
  },
  headerCell: {
    width: 35,
    textAlign: 'center',
    fontSize: 10,
    fontWeight: '600',
    color: '#e91e63',
    paddingVertical: 8,
  },
  matrixRow: {
    flexDirection: 'row',
    marginBottom: 1,
  },
  rowHeader: {
    width: 35,
    textAlign: 'center',
    fontSize: 10,
    fontWeight: '600',
    color: '#e91e63',
    paddingVertical: 8,
  },
  relationshipCell: {
    width: 35,
    height: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 1,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  relationshipText: {
    fontSize: 10,
    fontWeight: '600',
  },
  noteContainer: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  noteText: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
    lineHeight: 16,
  },
  noteTitle: {
    fontWeight: '600',
    color: '#333',
  },
});