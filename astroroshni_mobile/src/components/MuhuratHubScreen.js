import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/Ionicons';
import { COLORS } from '../utils/constants';
import { pricingAPI } from '../services/api';

const { width } = Dimensions.get('window');

// Cost key for each card: maps to pricing from API (credits/settings/analysis-pricing)
const COST_KEYS = {
  childbirth: 'childbirth',
  vehicle: 'vehicle',
  property: 'griha_pravesh',
  gold: 'gold',
  business: 'business'
};

// CONFIGURATION: Add new Muhurats here in the future
const MUHURAT_TYPES = [
  {
    id: 'childbirth',
    title: 'C-Section',
    subtitle: 'Safe delivery planning',
    icon: 'medical',
    gradient: ['#FF6B6B', '#EE5D5D'],
    route: 'ChildbirthPlanner' // Keep legacy separate if needed
  },
  {
    id: 'vehicle',
    title: 'Vehicle Buy',
    subtitle: 'Safety & Longevity',
    icon: 'car-sport',
    gradient: ['#FF9800', '#F57C00'],
    endpoint: '/muhurat/vehicle-purchase'
  },
  {
    id: 'property',
    title: 'Griha Pravesh',
    subtitle: 'Peace & Prosperity',
    icon: 'home',
    gradient: ['#4CAF50', '#388E3C'],
    endpoint: '/muhurat/griha-pravesh'
  },
  {
    id: 'gold',
    title: 'Gold Purchase',
    subtitle: 'Wealth & Prosperity',
    icon: 'diamond',
    gradient: ['#FFD700', '#FFA500'],
    endpoint: '/muhurat/gold-purchase'
  },
  {
    id: 'business',
    title: 'Business Opening',
    subtitle: 'Success & Growth',
    icon: 'briefcase',
    gradient: ['#9C27B0', '#7B1FA2'],
    endpoint: '/muhurat/business-opening'
  }
];

export default function MuhuratHubScreen({ navigation }) {
  const [pricing, setPricing] = useState({});
  const [pricingOriginal, setPricingOriginal] = useState({});

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await pricingAPI.getAnalysisPricing();
        const data = res?.data || res;
        if (!cancelled && data?.pricing) {
          setPricing(data.pricing);
          setPricingOriginal(data.pricing_original || {});
        }
      } catch (e) {
        // keep defaults
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const handlePress = (item) => {
    if (item.route) {
      navigation.navigate(item.route);
    } else {
      // Pass the config to the Universal Screen
      navigation.navigate('UniversalMuhurat', { config: item });
    }
  };

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#120E24', '#261C45']} style={styles.bg}>
        <SafeAreaView style={styles.safeArea}>
          
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Icon name="arrow-back" size={24} color={COLORS.white} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Auspicious Timings</Text>
            <View style={{width: 24}}/>
          </View>

          <Text style={styles.subHeader}>Select an event to plan</Text>

          <ScrollView contentContainerStyle={styles.grid}>
            {MUHURAT_TYPES.map((item, index) => {
              const costKey = COST_KEYS[item.id];
              const cost = costKey != null ? (pricing[costKey] ?? 0) : 0;
              const originalCost = costKey != null ? pricingOriginal[costKey] : null;
              const showCost = cost > 0;
              return (
                <TouchableOpacity 
                  key={index} 
                  style={styles.card} 
                  onPress={() => handlePress(item)}
                >
                  {showCost && (
                    <View style={styles.costBadge}>
                      <Icon name="flash" size={8} color="#854d0e" />
                      {originalCost != null && originalCost > cost ? (
                        <View style={styles.costWithDiscount}>
                          <Text style={[styles.costText, styles.costOriginal]}>{originalCost}</Text>
                          <Text style={styles.costText}>{cost}</Text>
                        </View>
                      ) : (
                        <Text style={styles.costText}>{cost}</Text>
                      )}
                    </View>
                  )}
                  <LinearGradient colors={item.gradient} style={styles.iconCircle}>
                    <Icon name={item.icon} size={28} color="#fff" />
                  </LinearGradient>
                  <Text style={styles.cardTitle}>{item.title}</Text>
                  <Text style={styles.cardSubtitle}>{item.subtitle}</Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>

        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  bg: { flex: 1 },
  safeArea: { flex: 1 },
  header: { flexDirection: 'row', justifyContent: 'space-between', padding: 20, alignItems: 'center' },
  headerTitle: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  subHeader: { color: '#aaa', marginLeft: 20, marginBottom: 20 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 15 },
  card: { 
    width: (width - 50) / 2, 
    backgroundColor: 'rgba(255,255,255,0.08)', 
    borderRadius: 16, 
    padding: 15, 
    margin: 5, 
    marginBottom: 15,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)'
  },
  iconCircle: { width: 50, height: 50, borderRadius: 25, justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
  cardTitle: { color: '#fff', fontSize: 16, fontWeight: 'bold', marginBottom: 4 },
  cardSubtitle: { color: '#888', fontSize: 11, textAlign: 'center' },
  costBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(255, 215, 0, 0.95)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#fff',
    zIndex: 1,
  },
  costText: {
    fontSize: 9,
    fontWeight: '800',
    color: '#854d0e',
    marginLeft: 2,
  },
  costWithDiscount: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  costOriginal: {
    textDecorationLine: 'line-through',
    color: '#854d0e',
    opacity: 0.8,
  },
});