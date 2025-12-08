import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/Ionicons';
import DateTimePicker from '@react-native-community/datetimepicker';
import { storage } from '../services/storage';
import { API_BASE_URL, getEndpoint, COLORS } from '../utils/constants';
import LocationPicker from './LocationPicker';


export default function ChildbirthPlannerScreen({ navigation }) {
  const [loading, setLoading] = useState(false);
  const [motherProfile, setMotherProfile] = useState(null);
  
  // Date state
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date(new Date().setDate(new Date().getDate() + 7)));
  const [showStartPicker, setShowStartPicker] = useState(false);
  const [showEndPicker, setShowEndPicker] = useState(false);
  
  // Location state
  const [deliveryLocation, setDeliveryLocation] = useState(null);
  const [showLocationPicker, setShowLocationPicker] = useState(false);
  
  // Results
  const [results, setResults] = useState(null);
  
  // Credits
  const [creditInfo, setCreditInfo] = useState({ cost: 0, current_credits: 0, can_afford: false });

  useEffect(() => {
    loadProfile();
    loadCreditInfo();
  }, []);

  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      // Reload profile when returning from SelectNative
      loadProfile();
    });
    return unsubscribe;
  }, [navigation]);

  const loadProfile = async () => {
    try {
      const data = await storage.getBirthData();
      if (data) {
        setMotherProfile(data);
        // SAFETY: Ensure lat/long exist before setting delivery location
        if (data.latitude && data.longitude) {
          setDeliveryLocation({
            latitude: parseFloat(data.latitude),
            longitude: parseFloat(data.longitude),
            name: data.place || "Mother's location"
          });
        }
      }
    } catch(e) { 
      console.error(e); 
    }
  };

  const loadCreditInfo = async () => {
    try {
      const token = await storage.getAuthToken();
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/muhurat/childbirth-planner/cost')}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setCreditInfo(data);
    } catch(e) {
      console.error('Failed to load credit info:', e);
    }
  };

  const calculateDates = async () => {
    if (!motherProfile) {
      Alert.alert("Missing Information", "Please select mother's chart first.");
      return;
    }
    
    if (!deliveryLocation) {
      Alert.alert("Missing Information", "Please select delivery location.");
      return;
    }

    const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
    if (daysDiff > 30) {
      Alert.alert("Date Range Limit", "Date range cannot exceed 30 days. Please adjust your selection.");
      return;
    }

    if (!creditInfo.can_afford) {
      Alert.alert(
        "Insufficient Credits", 
        `You need ${creditInfo.cost} credits but have ${creditInfo.current_credits}. Please purchase more credits.`,
        [
          { text: "Cancel", style: "cancel" },
          { text: "Buy Credits", onPress: () => navigation.navigate('CreditScreen') }
        ]
      );
      return;
    }

    setLoading(true);
    try {
      const token = await storage.getAuthToken();
      const payload = {
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        delivery_latitude: parseFloat(deliveryLocation.latitude),
        delivery_longitude: parseFloat(deliveryLocation.longitude),
        delivery_timezone: motherProfile.timezone || "UTC+5:30",
        
        mother_dob: motherProfile.date,
        mother_time: motherProfile.time,
        mother_lat: parseFloat(motherProfile.latitude),
        mother_lon: parseFloat(motherProfile.longitude),
        mother_timezone: motherProfile.timezone || "UTC+5:30"
      };

      const response = await fetch(`${API_BASE_URL}${getEndpoint('/muhurat/childbirth-planner')}`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify(payload)
      });

      const json = await response.json();
      if (response.status === 402) {
        Alert.alert(
          "Insufficient Credits", 
          json.detail?.message || "Not enough credits",
          [
            { text: "Cancel", style: "cancel" },
            { text: "Buy Credits", onPress: () => navigation.navigate('CreditScreen') }
          ]
        );
      } else if (json.status === 'success') {
        setResults(json.data);
        // Update credit info after successful calculation
        setCreditInfo(prev => ({
          ...prev,
          current_credits: json.remaining_credits,
          can_afford: json.remaining_credits >= prev.cost
        }));
      } else {
        Alert.alert("Error", "Calculation failed. Please check inputs.");
      }
    } catch (e) {
      Alert.alert("Error", "Network request failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']} style={styles.gradient}>
        <SafeAreaView style={styles.safeArea}>
          <ScrollView contentContainerStyle={styles.scroll}>
            
            {/* Header */}
            <View style={styles.header}>
              <TouchableOpacity onPress={() => navigation.goBack()}>
                <Icon name="arrow-back" size={24} color={COLORS.white} />
              </TouchableOpacity>
              <Text style={styles.headerTitle}>Childbirth Planner</Text>
              <View style={styles.placeholder} />
            </View>

            {/* Credit Info Card */}
            <View style={styles.creditCard}>
              <View style={styles.creditRow}>
                <Text style={styles.creditLabel}>💎 Cost: {creditInfo.cost} credits</Text>
                <Text style={[styles.creditBalance, { color: creditInfo.can_afford ? '#00C853' : '#FF5722' }]}>
                  Balance: {creditInfo.current_credits}
                </Text>
              </View>
              {!creditInfo.can_afford && (
                <TouchableOpacity 
                  style={styles.buyCreditsBtn} 
                  onPress={() => navigation.navigate('CreditScreen')}
                >
                  <Text style={styles.buyCreditsText}>Buy Credits</Text>
                </TouchableOpacity>
              )}
            </View>

            {/* Mother Selection Card */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>👩 MOTHER'S CHART</Text>
              <TouchableOpacity style={styles.locationBtn} onPress={() => navigation.navigate('SelectNative', { returnTo: 'ChildbirthPlanner' })}>
                <Icon name="person" size={20} color={COLORS.white} />
                <Text style={styles.locationText}>
                  {motherProfile?.name || "Select mother's chart"}
                </Text>
                <Icon name="chevron-forward" size={20} color="rgba(255,255,255,0.6)" />
              </TouchableOpacity>
              <Text style={styles.hint}>Required for nakshatra calculations</Text>
            </View>

            {/* Date Selection Card */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>📅 SELECT DATE RANGE</Text>
              <View style={styles.dateRow}>
                <TouchableOpacity style={styles.dateBtn} onPress={() => setShowStartPicker(true)}>
                  <Text style={styles.dateLabel}>From</Text>
                  <Text style={styles.dateValue}>{startDate.toLocaleDateString()}</Text>
                </TouchableOpacity>
                <Icon name="arrow-forward" size={20} color="rgba(255,255,255,0.6)" />
                <TouchableOpacity style={styles.dateBtn} onPress={() => setShowEndPicker(true)}>
                  <Text style={styles.dateLabel}>To</Text>
                  <Text style={styles.dateValue}>{endDate.toLocaleDateString()}</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Location Card */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>🏥 DELIVERY LOCATION</Text>
              <TouchableOpacity style={styles.locationBtn} onPress={() => setShowLocationPicker(true)}>
                <Icon name="location" size={20} color={COLORS.white} />
                <Text style={styles.locationText}>
                  {deliveryLocation?.name || "Select delivery location"}
                </Text>
                <Icon name="chevron-forward" size={20} color="rgba(255,255,255,0.6)" />
              </TouchableOpacity>
              <Text style={styles.hint}>Default: {motherProfile?.place || "Mother's location"}</Text>
            </View>

            {/* Calculate Button */}
            <TouchableOpacity 
              style={[styles.calcButton, !creditInfo.can_afford && styles.disabledButton]} 
              onPress={calculateDates} 
              disabled={loading || !creditInfo.can_afford}
            >
              <LinearGradient 
                colors={creditInfo.can_afford ? ['#ff6b35', '#ff8c5a'] : ['#666', '#888']} 
                style={styles.calcGradient}
              >
                {loading ? (
                  <ActivityIndicator color={COLORS.white} />
                ) : (
                  <Text style={styles.calcButtonText}>
                    {creditInfo.can_afford ? 'Find Auspicious Dates' : 'Insufficient Credits'}
                  </Text>
                )}
              </LinearGradient>
            </TouchableOpacity>

            {/* Results */}
            {results && (
              <View style={styles.resultsContainer}>
                <Text style={styles.resultHeader}>✨ Recommended Slots</Text>
                {results.recommendations.length === 0 ? (
                  <View style={styles.noDataCard}>
                    <Text style={styles.noDataText}>No fully auspicious dates found in this range.</Text>
                    <Text style={styles.noDataHint}>Try extending the date range.</Text>
                  </View>
                ) : (
                  results.recommendations.map((day, idx) => (
                    <View key={idx} style={styles.resultItem}>
                      <View style={styles.dateHeader}>
                        <Text style={styles.dateTitle}>{new Date(day.date).toDateString()}</Text>
                        <View style={styles.tag}>
                          <Text style={styles.tagText}>{day.nakshatra}</Text>
                        </View>
                      </View>
                      
                      <View style={styles.slotGrid}>
                        {day.slots.map((slot, sIdx) => (
                          <View key={sIdx} style={styles.slot}>
                            <Text style={styles.slotTime}>{slot.time}</Text>
                            <Text style={styles.slotLagna}>{slot.lagna}</Text>
                          </View>
                        ))}
                      </View>
                    </View>
                  ))
                )}
              </View>
            )}

          </ScrollView>

          {/* Date Pickers */}
          {showStartPicker && (
            <DateTimePicker
              value={startDate}
              mode="date"
              minimumDate={new Date()}
              onChange={(e, d) => { 
                setShowStartPicker(false); 
                if(d) setStartDate(d); 
              }}
            />
          )}
          {showEndPicker && (
            <DateTimePicker
              value={endDate}
              mode="date"
              minimumDate={startDate}
              onChange={(e, d) => { 
                setShowEndPicker(false); 
                if(d) {
                  const daysDiff = Math.ceil((d - startDate) / (1000 * 60 * 60 * 24));
                  if (daysDiff > 30) {
                    Alert.alert("Date Range Limit", "Please select a date within 30 days of start date.");
                    return;
                  }
                  setEndDate(d);
                }
              }}
            />
          )}



          {/* Location Picker Modal */}
          {showLocationPicker && (
            <LocationPicker
              onLocationSelect={(location) => {
                setDeliveryLocation(location);
                setShowLocationPicker(false);
              }}
              onClose={() => setShowLocationPicker(false)}
            />
          )}

        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  scroll: { padding: 20 },
  header: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    marginBottom: 20 
  },
  headerTitle: { 
    color: COLORS.white, 
    fontSize: 20, 
    fontWeight: 'bold' 
  },
  placeholder: { width: 24 },
  
  creditCard: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 12,
    padding: 15,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.15)'
  },
  creditRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8
  },
  creditLabel: {
    color: 'rgba(255,255,255,0.9)',
    fontSize: 14,
    fontWeight: '600'
  },
  creditBalance: {
    fontSize: 14,
    fontWeight: 'bold'
  },
  buyCreditsBtn: {
    backgroundColor: '#FF5722',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignSelf: 'flex-start'
  },
  buyCreditsText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: 'bold'
  },
  
  card: { 
    backgroundColor: 'rgba(255,255,255,0.1)', 
    borderRadius: 16, 
    padding: 20, 
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)'
  },
  cardTitle: { 
    color: 'rgba(255,255,255,0.8)', 
    fontSize: 14, 
    fontWeight: 'bold', 
    marginBottom: 15 
  },
  dateRow: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center' 
  },
  dateBtn: { 
    backgroundColor: 'rgba(0,0,0,0.3)', 
    padding: 12, 
    borderRadius: 8, 
    width: '42%' 
  },
  dateLabel: { 
    color: 'rgba(255,255,255,0.6)', 
    fontSize: 12 
  },
  dateValue: { 
    color: COLORS.white, 
    fontSize: 16, 
    fontWeight: 'bold', 
    marginTop: 2 
  },
  
  locationBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.3)',
    padding: 12,
    borderRadius: 8,
    gap: 10
  },
  locationText: {
    flex: 1,
    color: COLORS.white,
    fontSize: 16
  },
  hint: { 
    color: 'rgba(255,255,255,0.6)', 
    fontSize: 12, 
    marginTop: 10 
  },
  
  calcButton: { 
    borderRadius: 12, 
    overflow: 'hidden',
    marginBottom: 20 
  },
  calcGradient: {
    padding: 16, 
    alignItems: 'center'
  },
  calcButtonText: { 
    color: COLORS.white, 
    fontWeight: 'bold', 
    fontSize: 16 
  },
  disabledButton: {
    opacity: 0.6
  },
  
  resultsContainer: { marginTop: 10 },
  resultHeader: { 
    color: COLORS.white, 
    fontSize: 18, 
    fontWeight: 'bold', 
    marginBottom: 15 
  },
  resultItem: { 
    backgroundColor: 'rgba(255,255,255,0.05)', 
    borderRadius: 12, 
    padding: 15, 
    marginBottom: 15, 
    borderLeftWidth: 4, 
    borderLeftColor: '#00C853' 
  },
  dateHeader: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    marginBottom: 10 
  },
  dateTitle: { 
    color: COLORS.white, 
    fontSize: 16, 
    fontWeight: 'bold' 
  },
  tag: { 
    backgroundColor: 'rgba(255,255,255,0.1)', 
    paddingHorizontal: 8, 
    paddingVertical: 2, 
    borderRadius: 4 
  },
  tagText: { 
    color: 'rgba(255,255,255,0.8)', 
    fontSize: 12 
  },
  
  slotGrid: { 
    flexDirection: 'row', 
    flexWrap: 'wrap', 
    gap: 8 
  },
  slot: { 
    backgroundColor: 'rgba(0, 200, 83, 0.15)', 
    paddingVertical: 6, 
    paddingHorizontal: 12, 
    borderRadius: 6, 
    alignItems: 'center', 
    minWidth: 70 
  },
  slotTime: { 
    color: COLORS.white, 
    fontWeight: 'bold', 
    fontSize: 14 
  },
  slotLagna: { 
    color: '#FFD700', 
    fontSize: 10 
  },
  noDataCard: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center'
  },
  noDataText: { 
    color: 'rgba(255,255,255,0.8)', 
    textAlign: 'center',
    fontSize: 16,
    marginBottom: 8
  },
  noDataHint: {
    color: 'rgba(255,255,255,0.6)',
    textAlign: 'center',
    fontSize: 14
  }
});