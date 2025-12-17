import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

const AshtakvargaChart = ({ chartData, ashtakvargaData, onHousePress, cosmicTheme = true }) => {
  
  const getBinduColor = (bindus) => {
    if (bindus >= 30) return '#81C784'; // Strong - Darker Green
    if (bindus <= 25) return '#E57373'; // Weak - Darker Red
    return '#FFB74D'; // Moderate - Darker Orange
  };

  const getSignName = (signIndex) => {
    const signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
    return signs[signIndex] || 'Unknown';
  };

  return (
    <View style={styles.container}>
      <View style={styles.grid}>
        {[1,2,3,4,5,6,7,8,9,10,11,12].map((houseNumber) => {
          const ashtakvargaHouseData = ashtakvargaData?.[houseNumber.toString()];
          const bindus = ashtakvargaHouseData?.bindus || 0;
          const signIndex = ashtakvargaHouseData?.sign || 0;
          const signName = getSignName(signIndex);
          const binduColor = getBinduColor(bindus);
          
          return (
            <TouchableOpacity
              key={houseNumber}
              style={[styles.houseBox, { backgroundColor: binduColor }]}
              onPress={() => onHousePress?.(houseNumber, bindus, signName)}
            >
              <Text style={styles.houseNumber}>{houseNumber}</Text>
              <Text style={styles.bindus}>{bindus}</Text>
              <Text style={styles.signName}>{signName}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 10,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  houseBox: {
    width: '30%',
    aspectRatio: 1,
    margin: '1.5%',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  houseNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 4,
  },
  bindus: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
    marginBottom: 2,
  },
  signName: {
    fontSize: 10,
    color: 'white',
    textAlign: 'center',
  },
});

export default AshtakvargaChart;