import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList } from 'react-native';
import { apiService } from '../services/apiService';

const planetIcons = {
  'Sun': '☉',
  'Moon': '☽',
  'Mars': '♂',
  'Mercury': '☿',
  'Jupiter': '♃',
  'Venus': '♀',
  'Saturn': '♄',
  'Rahu': '☊',
  'Ketu': '☋'
};

export default function DashaWidget({
  title,
  dashaType,
  birthData,
  onDashaClick,
  selectedDashas,
  onDashaSelection,
  transitDate
}) {
  const [selectedDasha, setSelectedDasha] = useState(null);
  const [dashaData, setDashaData] = useState([]);
  const scrollViewRef = useRef(null);

  useEffect(() => {
    if (birthData) {
      fetchDashaData();
    }
  }, [birthData, dashaType, transitDate]);
  
  useEffect(() => {
    if (birthData) {
      // Only fetch when relevant parent dasha changes
      if (dashaType === 'maha') return; // Maha doesn't depend on selections
      if (dashaType === 'antar' && selectedDashas.maha) fetchDashaData();
      if (dashaType === 'pratyantar' && selectedDashas.antar) fetchDashaData();
      if (dashaType === 'sookshma' && selectedDashas.pratyantar) fetchDashaData();
      if (dashaType === 'prana' && selectedDashas.sookshma) fetchDashaData();
    }
  }, [selectedDashas.maha, selectedDashas.antar, selectedDashas.pratyantar, selectedDashas.sookshma]);

  const fetchDashaData = async () => {
    try {
      const data = await apiService.calculateDashas(birthData);
      
      if (dashaType === 'maha') {
        const targetDate = transitDate || new Date();
        const processedDashas = data.maha_dashas.map(dasha => ({
          ...dasha,
          current: new Date(dasha.start) <= targetDate && targetDate <= new Date(dasha.end)
        }));
        setDashaData(processedDashas);
        const currentDasha = processedDashas.find(d => d.current);
        if (selectedDashas.maha) {
          setSelectedDasha(selectedDashas.maha);
        } else if (currentDasha) {
          setSelectedDasha(currentDasha);
          onDashaSelection('maha', currentDasha);
        }
      } else {
        // Calculate hierarchical sub-dashas using backend
        const targetDate = transitDate || new Date();
        const currentMaha = data.maha_dashas.find(d => {
          return new Date(d.start) <= targetDate && targetDate <= new Date(d.end);
        });
        
        if (currentMaha) {
          let parentDasha = currentMaha;
          
          // Use selected dashas or current dashas for hierarchy
          if (dashaType === 'antar') {
            parentDasha = (selectedDashas && selectedDashas.maha) ? selectedDashas.maha : currentMaha;
          } else if (dashaType === 'pratyantar') {
            const mahaForAntar = (selectedDashas && selectedDashas.maha) ? selectedDashas.maha : currentMaha;
            if (selectedDashas && selectedDashas.antar) {
              parentDasha = selectedDashas.antar;
            } else {
              const currentSelectedDashas = selectedDashas;
              const antarDashas = await calculateSubDashas(mahaForAntar, 'antar', targetDate, currentSelectedDashas);
              parentDasha = antarDashas.find(d => d.current) || antarDashas[0];
            }
          } else if (dashaType === 'sookshma') {
            if (selectedDashas && selectedDashas.pratyantar) {
              parentDasha = selectedDashas.pratyantar;
            } else {
              const currentSelectedDashas = selectedDashas;
              const mahaForAntar = (currentSelectedDashas && currentSelectedDashas.maha) ? currentSelectedDashas.maha : currentMaha;
              const antarDashas = await calculateSubDashas(mahaForAntar, 'antar', targetDate, currentSelectedDashas);
              const antarForPratyantar = (currentSelectedDashas && currentSelectedDashas.antar) ? currentSelectedDashas.antar : antarDashas.find(d => d.current) || antarDashas[0];
              const pratyantarDashas = await calculateSubDashas(antarForPratyantar, 'pratyantar', targetDate, currentSelectedDashas);
              parentDasha = pratyantarDashas.find(d => d.current) || pratyantarDashas[0];
            }
          } else if (dashaType === 'prana') {
            if (selectedDashas && selectedDashas.sookshma) {
              parentDasha = selectedDashas.sookshma;
            } else {
              const currentSelectedDashas = selectedDashas;
              const mahaForAntar = (currentSelectedDashas && currentSelectedDashas.maha) ? currentSelectedDashas.maha : currentMaha;
              const antarDashas = await calculateSubDashas(mahaForAntar, 'antar', targetDate, currentSelectedDashas);
              const antarForPratyantar = (currentSelectedDashas && currentSelectedDashas.antar) ? currentSelectedDashas.antar : antarDashas.find(d => d.current) || antarDashas[0];
              const pratyantarDashas = await calculateSubDashas(antarForPratyantar, 'pratyantar', targetDate, currentSelectedDashas);
              const pratyantarForSookshma = (currentSelectedDashas && currentSelectedDashas.pratyantar) ? currentSelectedDashas.pratyantar : pratyantarDashas.find(d => d.current) || pratyantarDashas[0];
              const sookshmaDashas = await calculateSubDashas(pratyantarForSookshma, 'sookshma', targetDate, currentSelectedDashas);
              parentDasha = sookshmaDashas.find(d => d.current) || sookshmaDashas[0];
            }
          }
          
          const currentSelectedDashas = selectedDashas;
          const subDashas = await calculateSubDashas(parentDasha, dashaType, targetDate, currentSelectedDashas);
          
          setDashaData(subDashas);
          
          if (selectedDashas[dashaType]) {
            // Update selection from parent state
            const matchingDasha = subDashas.find(d => 
              d.planet === selectedDashas[dashaType].planet && 
              d.start === selectedDashas[dashaType].start
            );
            if (matchingDasha) {
              setSelectedDasha(matchingDasha);
            }
          } else if (subDashas.length > 0) {
            // Auto-select current or first dasha for cascading effect
            const currentDasha = subDashas.find(d => d.current);
            const dashaToSelect = currentDasha || subDashas[0];
            setSelectedDasha(dashaToSelect);
            onDashaSelection(dashaType, dashaToSelect);
          }
        }
      }
    } catch (error) {
      console.error('Error fetching dasha data:', error);
    }
  };

  const calculateSubDashas = async (parentDasha, type, targetDate = null, currentSelectedDashas = selectedDashas) => {
    try {
      // Prepare request data with hierarchy information
      const requestData = {
        birth_data: birthData,
        parent_dasha: parentDasha,
        dasha_type: type,
        target_date: (targetDate || transitDate || new Date()).toISOString().split('T')[0]
      };
      
      // Add hierarchy information for proper calculation
      if (type === 'pratyantar' && currentSelectedDashas.maha) {
        requestData.maha_lord = currentSelectedDashas.maha.planet;
      } else if (type === 'sookshma' && currentSelectedDashas.maha && currentSelectedDashas.antar) {
        requestData.maha_lord = currentSelectedDashas.maha.planet;
        requestData.antar_lord = currentSelectedDashas.antar.planet;
      } else if (type === 'prana' && currentSelectedDashas.maha && currentSelectedDashas.antar && currentSelectedDashas.pratyantar) {
        requestData.maha_lord = currentSelectedDashas.maha.planet;
        requestData.antar_lord = currentSelectedDashas.antar.planet;
        requestData.pratyantar_lord = currentSelectedDashas.pratyantar.planet;
      }
      
      const data = await apiService.calculateSubDashas(requestData);
      return data.sub_dashas || [];
    } catch (error) {
      console.error('Error calculating sub-dashas:', error);
      return [];
    }
  };

  const handleDashaPress = (dasha, index) => {
    setSelectedDasha(dasha);
    onDashaClick(dasha.start);
    onDashaSelection(dashaType, dasha);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      <FlatList
        ref={scrollViewRef}
        data={dashaData}
        style={styles.dashaList}
        showsVerticalScrollIndicator={false}
        keyExtractor={(item, index) => `${dashaType}-${item.planet}-${item.start}`}
        getItemLayout={(data, index) => ({
          length: 48,
          offset: 48 * index,
          index,
        })}
        renderItem={({ item: dasha, index }) => (
          <TouchableOpacity
            style={[
              styles.dashaCard,
              index % 2 === 0 && styles.evenDashaCard,
              selectedDasha && selectedDasha.planet === dasha.planet && selectedDasha.start === dasha.start && styles.selectedDashaCard
            ]}
            onPress={() => handleDashaPress(dasha, index)}
          >
            <View style={styles.dashaCardContent}>
              <View style={styles.dashaHeader}>
                <Text style={[
                  styles.dashaText,
                  dasha.current && styles.currentDashaText
                ]}>
                  {planetIcons[dasha.planet] || '🪐'} {dasha.planet}
                </Text>
                <Text style={[
                  styles.dashaDate,
                  dasha.current && styles.currentDashaDate
                ]}>
                  {new Date(dasha.start).getDate()}/{(new Date(dasha.start).getMonth() + 1).toString().padStart(2, '0')}/{new Date(dasha.start).getFullYear().toString().slice(-2)} - {new Date(dasha.end).getDate()}/{(new Date(dasha.end).getMonth() + 1).toString().padStart(2, '0')}/{new Date(dasha.end).getFullYear().toString().slice(-2)}
                </Text>
              </View>
            </View>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'white',
    borderRadius: 12,
    margin: 8,
    padding: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
    height: 180,
  },
  title: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#e91e63',
    marginBottom: 8,
    textAlign: 'center',
  },
  dashaList: {
    flex: 1,
  },
  dashaCard: {
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: 'rgba(116, 185, 255, 0.2)',
    borderRadius: 6,
    padding: 6,
    marginBottom: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  evenDashaCard: {
    backgroundColor: 'rgba(255, 243, 224, 0.3)',
  },
  currentDashaCard: {
    backgroundColor: 'rgba(255, 111, 0, 0.15)',
    borderColor: 'rgba(255, 111, 0, 0.4)',
    shadowColor: '#ff6f00',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  dashaCardContent: {
    flex: 1,
  },
  dashaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dashaText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#2d3436',
    flex: 1,
  },
  currentDashaText: {
    color: '#2d3436',
  },
  dashaDate: {
    fontSize: 8,
    color: '#636e72',
    flexShrink: 0,
  },
  currentDashaDate: {
    color: '#636e72',
  },
  selectedDashaCard: {
    backgroundColor: 'rgba(233, 30, 99, 0.15)',
    borderColor: 'rgba(233, 30, 99, 0.4)',
  },
});