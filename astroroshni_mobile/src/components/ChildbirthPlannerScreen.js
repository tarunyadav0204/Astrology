import React, { useState, useEffect } from 'react';
import { useFocusEffect } from '@react-navigation/native';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator, Platform, Modal } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/Ionicons';
import DateTimePicker from '@react-native-community/datetimepicker';
import { storage } from '../services/storage';
import { API_BASE_URL, getEndpoint, COLORS } from '../utils/constants';
import LocationPicker from './LocationPicker';
import { useCredits } from '../credits/CreditContext';


export default function ChildbirthPlannerScreen({ navigation }) {
  const { credits, fetchBalance } = useCredits();
  const [loading, setLoading] = useState(false);
  const [motherProfile, setMotherProfile] = useState(null);
  
  // Date state
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date(new Date().setDate(new Date().getDate() + 30)));
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

  useFocusEffect(
    React.useCallback(() => {
      fetchBalance();
      loadCreditInfo();
    }, [])
  );

  useEffect(() => {
    setCreditInfo(prev => ({
      ...prev,
      current_credits: credits,
      can_afford: credits >= prev.cost
    }));
  }, [credits]);

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
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/credits/settings/childbirth-cost')}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setCreditInfo({
        cost: data.cost || 0,
        current_credits: credits,
        can_afford: credits >= (data.cost || 0)
      });
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

    // Confirmation dialog before deducting credits
    Alert.alert(
      "Confirm Calculation", 
      `This will deduct ${creditInfo.cost} credits from your account. Do you want to proceed?`,
      [
        { text: "Cancel", style: "cancel" },
        { text: "Proceed", onPress: () => performCalculation() }
      ]
    );
  };

  const performCalculation = async () => {
    try {
      const token = await storage.getAuthToken();
      
      const payload = {
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        delivery_latitude: parseFloat(deliveryLocation.latitude),
        delivery_longitude: parseFloat(deliveryLocation.longitude),
        
        mother_dob: motherProfile.date,
        mother_time: motherProfile.time,
        mother_lat: parseFloat(motherProfile.latitude),
        mother_lon: parseFloat(motherProfile.longitude)
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
        await fetchBalance();
        setCreditInfo(prev => ({
          ...prev,
          current_credits: json.remaining_credits || credits - prev.cost,
          can_afford: (json.remaining_credits || credits - prev.cost) >= prev.cost
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
                <Text style={[styles.creditBalance, { color: credits >= creditInfo.cost ? '#00C853' : '#FF5722' }]}>
                  Balance: {credits}
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
                    <Text style={styles.noDataText}>No auspicious dates found in this period</Text>
                    <Text style={styles.noDataHint}>Vedic astrology has strict rules for auspicious timing. Try:</Text>
                    <Text style={styles.noDataTip}>• Extending the date range to 60-90 days</Text>
                    <Text style={styles.noDataTip}>• Avoiding eclipse periods and inauspicious months</Text>
                    <Text style={styles.noDataTip}>• Checking different lunar months</Text>
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
          {Platform.OS === 'ios' ? (
            <>
              <Modal visible={showStartPicker} transparent animationType="slide">
                <View style={styles.modalOverlay}>
                  <View style={styles.pickerContainer}>
                    <View style={styles.pickerGradient}>
                      <View style={styles.pickerHeader}>
                        <TouchableOpacity onPress={() => setShowStartPicker(false)}>
                          <Text style={styles.pickerButton}>Cancel</Text>
                        </TouchableOpacity>
                        <TouchableOpacity onPress={() => setShowStartPicker(false)}>
                          <Text style={[styles.pickerButton, styles.pickerButtonDone]}>Done</Text>
                        </TouchableOpacity>
                      </View>
                      <DateTimePicker
                        value={startDate}
                        mode="date"
                        display="spinner"
                        minimumDate={new Date()}
                        onChange={(event, selectedDate) => {
                          if (selectedDate) setStartDate(selectedDate);
                        }}
                        style={styles.iosPicker}
                      />
                    </View>
                  </View>
                </View>
              </Modal>
              
              <Modal visible={showEndPicker} transparent animationType="slide">
                <View style={styles.modalOverlay}>
                  <View style={styles.pickerContainer}>
                    <View style={styles.pickerGradient}>
                      <View style={styles.pickerHeader}>
                        <TouchableOpacity onPress={() => setShowEndPicker(false)}>
                          <Text style={styles.pickerButton}>Cancel</Text>
                        </TouchableOpacity>
                        <TouchableOpacity onPress={() => {
                          const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
                          if (daysDiff > 30) {
                            Alert.alert("Date Range Limit", "Please select a date within 30 days of start date.");
                            return;
                          }
                          setShowEndPicker(false);
                        }}>
                          <Text style={[styles.pickerButton, styles.pickerButtonDone]}>Done</Text>
                        </TouchableOpacity>
                      </View>
                      <DateTimePicker
                        value={endDate}
                        mode="date"
                        display="spinner"
                        minimumDate={startDate}
                        onChange={(event, selectedDate) => {
                          if (selectedDate) setEndDate(selectedDate);
                        }}
                        style={styles.iosPicker}
                      />
                    </View>
                  </View>
                </View>
              </Modal>
            </>
          ) : (
            <>
              {showStartPicker && (
                <DateTimePicker
                  value={startDate}
                  mode="date"
                  display="default"
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
                  display="default"
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
            </>
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
    fontSize: 14,
    marginBottom: 10
  },
  noDataTip: {
    color: 'rgba(255,255,255,0.5)',
    fontSize: 13,
    marginBottom: 5,
    paddingLeft: 10
  },
  modalOverlay: { 
    flex: 1, 
    backgroundColor: 'rgba(0, 0, 0, 0.5)', 
    justifyContent: 'flex-end' 
  },
  pickerContainer: { 
    backgroundColor: '#fff',
    borderTopLeftRadius: 20, 
    borderTopRightRadius: 20, 
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 10
  },
  pickerGradient: { 
    paddingBottom: 30,
    backgroundColor: '#fff'
  },
  pickerHeader: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center',
    paddingHorizontal: 20, 
    paddingVertical: 16, 
    borderBottomWidth: 0.5, 
    borderBottomColor: 'rgba(0, 0, 0, 0.1)',
    backgroundColor: '#f8f9fa'
  },
  pickerButton: { 
    fontSize: 17, 
    color: '#007AFF', 
    fontWeight: '400' 
  },
  pickerButtonDone: { 
    color: '#007AFF', 
    fontWeight: '600' 
  },
  iosPicker: {
    backgroundColor: '#fff',
    marginHorizontal: 20
  }
});