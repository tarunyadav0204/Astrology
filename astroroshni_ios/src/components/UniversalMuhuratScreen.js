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

export default function UniversalMuhuratScreen({ route, navigation }) {
  const { config } = route.params; 
  const { credits, fetchBalance } = useCredits();
  
  const [loading, setLoading] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const [results, setResults] = useState(null);
  const [creditInfo, setCreditInfo] = useState({ cost: 0, current_credits: 0, can_afford: false });
  
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date(new Date().setDate(new Date().getDate() + 30)));
  const [showStartPicker, setShowStartPicker] = useState(false);
  const [showEndPicker, setShowEndPicker] = useState(false);
  
  const [location, setLocation] = useState(null);
  const [showLocationPicker, setShowLocationPicker] = useState(false);

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

  const loadProfile = async () => {
    try {
      const data = await storage.getBirthData();
      if (!data?.name) {
        navigation.replace('BirthProfileIntro', { returnTo: 'UniversalMuhurat' });
        return;
      }
      setUserProfile(data);
      if (data.latitude) {
        setLocation({
          latitude: parseFloat(data.latitude),
          longitude: parseFloat(data.longitude),
          name: data.place || "My Location"
        });
      }
    } catch(e) { console.error(e); }
  };

  const loadCreditInfo = async () => {
    try {
      const token = await storage.getAuthToken();
      
      const costEndpointMap = {
        'childbirth-planner': '/credits/settings/childbirth-cost',
        'childbirth': '/credits/settings/childbirth-cost',
        'vehicle-purchase': '/credits/settings/vehicle-cost',
        'griha-pravesh': '/credits/settings/griha-pravesh-cost',
        'gold-purchase': '/credits/settings/gold-cost',
        'business-opening': '/credits/settings/business-cost'
      };
      
      const featureName = config.endpoint ? config.endpoint.split('/').pop() : config.id;
      const costEndpoint = costEndpointMap[featureName] || costEndpointMap[config.id];
      
      if (costEndpoint) {
        const response = await fetch(`${API_BASE_URL}${getEndpoint(costEndpoint)}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const costData = await response.json();
        const cost = costData.cost || 0;
        
        setCreditInfo(prev => ({
          ...prev,
          cost: cost,
          current_credits: credits,
          can_afford: credits >= cost
        }));
      }
    } catch(e) {
      console.error('Failed to load credit info:', e);
    }
  };

  const calculate = async () => {
    if (!userProfile || !location) {
      Alert.alert("Missing Data", "Please verify your profile and location.");
      return;
    }

    if (credits < creditInfo.cost) {
      Alert.alert(
        "Insufficient Credits", 
        `You need ${creditInfo.cost} credits but have ${credits}. Please purchase more credits.`,
        [
          { text: "Cancel", style: "cancel" },
          { text: "Buy Credits", onPress: () => navigation.navigate('CreditScreen') }
        ]
      );
      return;
    }

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
    setLoading(true);
    try {
      const token = await storage.getAuthToken();
      
      const payload = {
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        latitude: parseFloat(location.latitude),
        longitude: parseFloat(location.longitude),
        
        user_dob: userProfile.date,
        user_time: userProfile.time,
        user_lat: parseFloat(userProfile.latitude),
        user_lon: parseFloat(userProfile.longitude)
      };

      const response = await fetch(`${API_BASE_URL}${getEndpoint(config.endpoint)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(payload)
      });

      const json = await response.json();
      
      if (response.status === 402) {
        Alert.alert("Insufficient Credits", json.detail?.message || "Please buy more credits.", [
          { text: "Cancel" }, { text: "Buy", onPress: () => navigation.navigate('CreditScreen') }
        ]);
      } else if (json.status === 'success') {
        setResults(json.data);
        await fetchBalance();
        setCreditInfo(prev => ({
          ...prev,
          current_credits: json.remaining_credits || credits - prev.cost,
          can_afford: (json.remaining_credits || credits - prev.cost) >= prev.cost
        }));
      } else {
        Alert.alert("Error", "Calculation failed.");
      }
    } catch (e) {
      Alert.alert("Error", "Network Error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#120E24', '#261C45']} style={styles.bg}>
        <SafeAreaView style={styles.safeArea}>
          <ScrollView contentContainerStyle={styles.scroll}>
            
            <View style={styles.header}>
              <TouchableOpacity onPress={() => navigation.goBack()}>
                <Icon name="arrow-back" size={24} color={COLORS.white} />
              </TouchableOpacity>
              <Text style={styles.headerTitle}>{config.title}</Text>
              <View style={{width: 24}}/>
            </View>

            <View style={styles.creditCard}>
              <View style={styles.creditRow}>
                <Text style={styles.creditLabel}>💎 Cost: {creditInfo.cost} credits</Text>
                <Text style={[styles.creditBalance, { color: credits >= creditInfo.cost ? '#00C853' : '#FF5722' }]}>
                  Balance: {credits}
                </Text>
              </View>
              {credits < creditInfo.cost && (
                <TouchableOpacity 
                  style={styles.buyCreditsBtn} 
                  onPress={() => navigation.navigate('CreditScreen')}
                >
                  <Text style={styles.buyCreditsText}>Buy Credits</Text>
                </TouchableOpacity>
              )}
            </View>

            <View style={styles.card}>
              <Text style={[styles.cardTitle, {color: config.gradient[0]}]}>📅 DATE RANGE</Text>
              <View style={styles.row}>
                <TouchableOpacity onPress={() => setShowStartPicker(true)} style={styles.picker}>
                  <Text style={styles.pickerLabel}>From</Text>
                  <Text style={styles.pickerValue}>{startDate.toLocaleDateString()}</Text>
                </TouchableOpacity>
                <Icon name="arrow-forward" size={20} color="#666" />
                <TouchableOpacity onPress={() => setShowEndPicker(true)} style={styles.picker}>
                  <Text style={styles.pickerLabel}>To</Text>
                  <Text style={styles.pickerValue}>{endDate.toLocaleDateString()}</Text>
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.card}>
              <Text style={[styles.cardTitle, {color: config.gradient[0]}]}>📍 LOCATION</Text>
              <TouchableOpacity style={styles.locBtn} onPress={() => setShowLocationPicker(true)}>
                <Icon name="location" size={20} color="#fff" />
                <Text style={styles.locText}>{location?.name || "Select City"}</Text>
                <Text style={styles.changeText}>Change</Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity 
              style={[styles.btn, credits < creditInfo.cost && styles.disabledButton]} 
              onPress={calculate} 
              disabled={loading || credits < creditInfo.cost}
            >
              <LinearGradient 
                colors={credits >= creditInfo.cost ? config.gradient : ['#666', '#888']} 
                style={styles.btnGrad}
              >
                {loading ? (
                  <ActivityIndicator color="#fff"/>
                ) : (
                  <Text style={styles.btnText}>
                    {credits >= creditInfo.cost ? 'Find Auspicious Time' : 'Insufficient Credits'}
                  </Text>
                )}
              </LinearGradient>
            </TouchableOpacity>

            {results && (
              <View style={styles.results}>
                <Text style={styles.resHeader}>Recommended Slots</Text>
                {results.recommendations.length === 0 ? (
                  <View style={styles.noDataContainer}>
                    <Text style={styles.noData}>No auspicious dates found in this period</Text>
                    <Text style={styles.noDataSub}>Vedic astrology has strict rules for auspicious timing. Try:</Text>
                    <Text style={styles.noDataTip}>• Extending the date range to 60-90 days</Text>
                    <Text style={styles.noDataTip}>• Avoiding eclipse periods and inauspicious months</Text>
                  </View>
                ) : (
                  results.recommendations.map((day, idx) => (
                    <View key={idx} style={styles.resultItem}>
                      <Text style={styles.resultDate}>{new Date(day.date).toDateString()}</Text>
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
                        onChange={(event, selectedDate) => {
                          if (selectedDate) setStartDate(selectedDate);
                        }}
                        minimumDate={new Date()}
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
                        <TouchableOpacity onPress={() => setShowEndPicker(false)}>
                          <Text style={[styles.pickerButton, styles.pickerButtonDone]}>Done</Text>
                        </TouchableOpacity>
                      </View>
                      <DateTimePicker
                        value={endDate}
                        mode="date"
                        display="spinner"
                        onChange={(event, selectedDate) => {
                          if (selectedDate) setEndDate(selectedDate);
                        }}
                        minimumDate={startDate}
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
                  onChange={(event, selectedDate) => {
                    setShowStartPicker(false);
                    if (selectedDate) setStartDate(selectedDate);
                  }}
                  minimumDate={new Date()}
                />
              )}
              
              {showEndPicker && (
                <DateTimePicker
                  value={endDate}
                  mode="date"
                  display="default"
                  onChange={(event, selectedDate) => {
                    setShowEndPicker(false);
                    if (selectedDate) setEndDate(selectedDate);
                  }}
                  minimumDate={startDate}
                />
              )}
            </>
          )}

          {showLocationPicker && (
            <LocationPicker
              onLocationSelect={(location) => {
                setLocation(location);
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
  bg: { flex: 1 },
  safeArea: { flex: 1 },
  scroll: { padding: 20 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  headerTitle: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  creditCard: { backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 12, padding: 15, marginBottom: 20, borderWidth: 1, borderColor: 'rgba(255,255,255,0.15)' },
  creditRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  creditLabel: { color: 'rgba(255,255,255,0.9)', fontSize: 14, fontWeight: '600' },
  creditBalance: { fontSize: 14, fontWeight: 'bold' },
  buyCreditsBtn: { backgroundColor: '#FF5722', paddingVertical: 8, paddingHorizontal: 16, borderRadius: 6, alignSelf: 'flex-start', marginTop: 8 },
  buyCreditsText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  card: { backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 16, padding: 20, marginBottom: 20, borderWidth: 1, borderColor: 'rgba(255,255,255,0.2)' },
  cardTitle: { fontSize: 14, fontWeight: 'bold', marginBottom: 15, color: 'rgba(255,255,255,0.8)' },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  picker: { backgroundColor: 'rgba(0,0,0,0.3)', padding: 12, borderRadius: 8, width: '42%' },
  pickerLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 12 },
  pickerValue: { color: '#fff', fontSize: 16, fontWeight: 'bold', marginTop: 2 },
  locBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.3)', padding: 12, borderRadius: 8, gap: 10 },
  locText: { flex: 1, color: '#fff', fontSize: 16 },
  changeText: { color: 'rgba(255,255,255,0.6)', fontSize: 12 },
  btn: { borderRadius: 12, overflow: 'hidden', marginBottom: 20 },
  btnGrad: { padding: 16, alignItems: 'center' },
  btnText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  disabledButton: { opacity: 0.6 },
  results: { marginTop: 20 },
  resHeader: { color: '#fff', fontSize: 18, fontWeight: 'bold', marginBottom: 15 },
  noDataContainer: { backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 12, padding: 20, alignItems: 'center' },
  noData: { color: 'rgba(255,255,255,0.8)', fontSize: 16, marginBottom: 8, textAlign: 'center' },
  noDataSub: { color: 'rgba(255,255,255,0.6)', fontSize: 14, marginBottom: 10, textAlign: 'center' },
  noDataTip: { color: 'rgba(255,255,255,0.5)', fontSize: 13, marginBottom: 5 },
  resultItem: { backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 12, padding: 15, marginBottom: 15 },
  resultDate: { color: '#fff', fontSize: 16, fontWeight: 'bold', marginBottom: 10 },
  slotGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  slot: { backgroundColor: 'rgba(0, 200, 83, 0.15)', paddingVertical: 6, paddingHorizontal: 12, borderRadius: 6, alignItems: 'center', minWidth: 70 },
  slotTime: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  slotLagna: { color: '#FFD700', fontSize: 10 },
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