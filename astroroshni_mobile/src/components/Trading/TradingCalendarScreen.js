import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList, ActivityIndicator, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useCredits } from '../../credits/CreditContext';
import { API_BASE_URL } from '../../utils/constants';
import AsyncStorage from '@react-native-async-storage/async-storage';

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function TradingCalendarScreen({ navigation }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [calendarData, setCalendarData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDay, setSelectedDay] = useState(null);
  const [showCreditModal, setShowCreditModal] = useState(true);
  const [monthlyCost, setMonthlyCost] = useState(20);
  const [premiumAnalysis, setPremiumAnalysis] = useState(false);
  const [premiumCost, setPremiumCost] = useState(200);
  const { credits, fetchBalance } = useCredits();

  useEffect(() => {
    fetchBalance();
    fetchCosts();
  }, []);

  const fetchCosts = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}/credits/settings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        const baseCost = data.trading_monthly_cost || 20;
        const multiplier = data.premium_chat_cost || 10;
        setMonthlyCost(baseCost);
        setPremiumCost(baseCost * multiplier);
      }
    } catch (error) {
      // Keep default cost if fetch fails
    }
  };

  const confirmAndRunAnalysis = () => {
    const cost = premiumAnalysis ? premiumCost : monthlyCost;
    if (credits < cost) {
      Alert.alert("Insufficient Credits", `You need ${cost} credits for monthly calendar. Please purchase more credits.`, [
        { text: "Buy Credits", onPress: () => navigation.navigate('Credits') },
        { text: "Cancel", onPress: () => navigation.goBack() }
      ]);
      return;
    }
    setShowCreditModal(false);
    fetchMonthlyData(currentDate.getFullYear(), currentDate.getMonth() + 1);
  };

  useEffect(() => {
    if (!showCreditModal) {
      fetchMonthlyData(currentDate.getFullYear(), currentDate.getMonth() + 1);
    }
  }, [currentDate, showCreditModal]);

  const fetchMonthlyData = async (year, month) => {
    setLoading(true);
    try {
      // Try multiple storage keys like other analysis pages
      let birthData = null;
      
      // Try userBirthData first
      const birthDataStr = await AsyncStorage.getItem('userBirthData');
      if (birthDataStr) {
        birthData = JSON.parse(birthDataStr);
      }
      
      // If not found, try birthDetails key (used by other analysis pages)
      if (!birthData) {
        const birthDetailsStr = await AsyncStorage.getItem('birthDetails');
        if (birthDetailsStr) {
          birthData = JSON.parse(birthDetailsStr);
        }
      }
      
      // If still not found, try to load from API like other analysis pages
      if (!birthData) {
        try {
          const token = await AsyncStorage.getItem('authToken');
          const { chartAPI } = require('../../services/api');
          const response = await chartAPI.getExistingCharts();
          
          if (response.data && response.data.charts && response.data.charts.length > 0) {
            // Use first chart as birth data
            const firstChart = response.data.charts[0];
            birthData = {
              name: firstChart.name,
              date: firstChart.date,
              time: firstChart.time,
              latitude: firstChart.latitude,
              longitude: firstChart.longitude,
              place: firstChart.place,
              gender: firstChart.gender
            };
            // Save for future use
            await AsyncStorage.setItem('userBirthData', JSON.stringify(birthData));
          } else {
            // No natives exist, go to birth form
            navigation.replace('BirthForm');
            return;
          }
        } catch (error) {
          // If API fails, go to birth form as fallback
          navigation.replace('BirthForm');
          return;
        }
      }
      
      // Ensure birthData has required fields
      if (!birthData || !birthData.name || !birthData.date) {
        navigation.replace('SelectNative');
        return;
      }
      
      const token = await AsyncStorage.getItem('authToken');
      
      const response = await fetch(`${API_BASE_URL}/api/trading/monthly-calendar?year=${year}&month=${month}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({...birthData, premium_analysis: premiumAnalysis})
      });

      if (response.status === 402) {
        Alert.alert("Insufficient Credits", "You need more credits for monthly calendar. Please purchase more credits.", [
          { text: "OK", onPress: () => navigation.navigate('Credits') }
        ]);
        return;
      }

      const text = await response.text();
      const lines = text.split('\n');
      let foundData = false;
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const json = JSON.parse(line.substring(6));
            if (json.status === 'complete') {
                setCalendarData(json.data);
                foundData = true;
                break;
            } else if (json.status === 'error') {
                Alert.alert("Calendar Error", json.message || "Failed to generate calendar", [
                  { text: "Retry", onPress: () => fetchMonthlyData(year, month) },
                  { text: "Go Back", onPress: () => navigation.goBack() }
                ]);
                return;
            }
          } catch(e) {}
        }
      }
      
      if (!foundData) {
        Alert.alert("Data Error", "No calendar data received", [
          { text: "Retry", onPress: () => fetchMonthlyData(year, month) },
          { text: "Go Back", onPress: () => navigation.goBack() }
        ]);
      }
    } catch (error) {
      console.error(error);
      Alert.alert("Connection Error", "Network issue. Please check your connection.", [
        { text: "Retry", onPress: () => fetchMonthlyData(year, month) },
        { text: "Go Back", onPress: () => navigation.goBack() }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const changeMonth = async (direction) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() + direction);
    
    // Check if this month is already paid for (cached)
    const isPaid = await checkMonthCache(newDate.getFullYear(), newDate.getMonth() + 1);
    
    if (isPaid) {
      setCurrentDate(newDate);
      setSelectedDay(null);
    } else {
      // Show credit confirmation for new month
      const cost = premiumAnalysis ? premiumCost : monthlyCost;
      Alert.alert(
        "New Month Analysis", 
        `This will cost ${cost} credits to analyze ${newDate.toLocaleString('default', { month: 'long', year: 'numeric' })}. Continue?`,
        [
          { text: "Cancel" },
          { 
            text: "Pay & Analyze", 
            onPress: () => {
              if (credits < cost) {
                Alert.alert("Insufficient Credits", `You need ${cost} credits for monthly calendar.`, [
                  { text: "Buy Credits", onPress: () => navigation.navigate('Credits') },
                  { text: "Go Back", onPress: () => navigation.goBack() }
                ]);
              } else {
                setCurrentDate(newDate);
                setSelectedDay(null);
              }
            }
          }
        ]
      );
    }
  };

  const checkMonthCache = async (year, month) => {
    try {
      let birthData = null;
      const birthDataStr = await AsyncStorage.getItem('userBirthData');
      if (birthDataStr) {
        birthData = JSON.parse(birthDataStr);
      }
      
      if (!birthData) return false;
      
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}/api/trading/monthly-calendar?year=${year}&month=${month}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({...birthData, premium_analysis: premiumAnalysis})
      });
      
      if (response.ok) {
        const text = await response.text();
        return text.includes('"cached": true');
      }
      return false;
    } catch {
      return false;
    }
  };

  const getSignalColor = (signal) => {
    if (signal === 'GREEN') return '#00C853';
    if (signal === 'YELLOW') return '#FFD600';
    if (signal === 'ORANGE') return '#FF6D00';
    if (signal === 'RED') return '#D50000';
    return '#666';
  };

  const renderDayItem = ({ item }) => {
    if (!item) return <View style={styles.dayCellEmpty} />;
    const color = getSignalColor(item.signal);
    const dayNum = new Date(item.date).getDate();
    const isSelected = selectedDay && selectedDay.date === item.date;

    return (
      <TouchableOpacity 
        style={[styles.dayCell, isSelected && { borderColor: '#fff', borderWidth: 1 }]} 
        onPress={() => setSelectedDay(item)}
      >
        <View style={[styles.signalDot, { backgroundColor: color }]} />
        <Text style={styles.dayText}>{dayNum}</Text>
        <Text style={[styles.scoreText, { color }]}>{item.score}</Text>
      </TouchableOpacity>
    );
  };

  const getGridData = () => {
    if (!calendarData.length) return [];
    const firstDayObj = new Date(calendarData[0].date);
    const startDayOfWeek = firstDayObj.getDay(); 
    return [...Array(startDayOfWeek).fill(null), ...calendarData];
  };

  if (showCreditModal) return (
    <View style={styles.container}>
      <LinearGradient colors={['#0f0c29', '#302b63']} style={styles.bg}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Ionicons name="arrow-back" size={24} color="#fff" />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Trading Planner</Text>
            <View style={{ width: 24 }} />
          </View>
          <View style={styles.loader}>
            <Ionicons name="calendar" size={48} color="#FFD700" />
            <Text style={styles.emptyTitle}>Monthly Trading Calendar</Text>
            
            <View style={styles.premiumToggle}>
              <TouchableOpacity 
                style={[styles.toggleOption, !premiumAnalysis && styles.toggleSelected]} 
                onPress={() => setPremiumAnalysis(false)}
              >
                <Text style={[styles.toggleText, !premiumAnalysis && styles.toggleTextSelected]}>Standard AI</Text>
                <Text style={[styles.toggleCost, !premiumAnalysis && styles.toggleCostSelected]}>{monthlyCost} credits</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.toggleOption, premiumAnalysis && styles.toggleSelected]} 
                onPress={() => setPremiumAnalysis(true)}
              >
                <Text style={[styles.toggleText, premiumAnalysis && styles.toggleTextSelected]}>Premium AI</Text>
                <Text style={[styles.toggleCost, premiumAnalysis && styles.toggleCostSelected]}>{premiumCost} credits</Text>
              </TouchableOpacity>
            </View>
            
            <Text style={styles.loadingText}>Your balance: {credits} credits</Text>
            <View style={styles.buttonRow}>
              <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.retryButton, {backgroundColor: '#666'}]}>
                <Text style={[styles.retryText, {color: '#fff'}]}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={confirmAndRunAnalysis} style={styles.retryButton}>
                <Text style={styles.retryText}>Generate Calendar</Text>
              </TouchableOpacity>
            </View>
          </View>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#0f0c29', '#302b63', '#24243e']} style={styles.bg}>
        <SafeAreaView style={styles.safeArea}>
          
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Ionicons name="arrow-back" size={24} color="#fff" />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Trading Planner</Text>
            <View style={{ width: 24 }} />
          </View>

          <View style={styles.monthNav}>
            <TouchableOpacity onPress={() => changeMonth(-1)}>
              <Ionicons name="chevron-back" size={24} color="#fff" />
            </TouchableOpacity>
            <Text style={styles.monthTitle}>
              {currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}
            </Text>
            <TouchableOpacity onPress={() => changeMonth(1)}>
              <Ionicons name="chevron-forward" size={24} color="#fff" />
            </TouchableOpacity>
          </View>

          <View style={styles.weekHeader}>
            {DAYS.map(day => <Text key={day} style={styles.weekText}>{day}</Text>)}
          </View>

          {loading ? (
            <View style={styles.loader}>
              <ActivityIndicator size="large" color="#6366F1" />
              <Text style={styles.loadingText}>Calculating Planetary Alignments...</Text>
              <View style={styles.skeletonGrid}>
                {Array(28).fill(0).map((_, i) => (
                  <View key={i} style={styles.skeletonDay} />
                ))}
              </View>
            </View>
          ) : calendarData.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="calendar-outline" size={48} color="#666" />
              <Text style={styles.emptyTitle}>No Calendar Data</Text>
              <View style={styles.buttonRow}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.retryButton, {backgroundColor: '#666'}]}>
                  <Text style={[styles.retryText, {color: '#fff'}]}>Go Back</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => fetchMonthlyData(currentDate.getFullYear(), currentDate.getMonth() + 1)} style={styles.retryButton}>
                  <Ionicons name="refresh" size={16} color="#fff" />
                  <Text style={styles.retryText}>Reload</Text>
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <FlatList
              data={getGridData()}
              renderItem={renderDayItem}
              keyExtractor={(item, index) => index.toString()}
              numColumns={7}
              contentContainerStyle={styles.grid}
            />
          )}

          {selectedDay && (
            <View style={styles.detailCard}>
              <View style={styles.detailHeader}>
                <Text style={styles.detailDate}>{new Date(selectedDay.date).toDateString()}</Text>
                <View style={[styles.detailBadge, { backgroundColor: getSignalColor(selectedDay.signal) }]}>
                  <Text style={styles.detailBadgeText}>{selectedDay.signal}</Text>
                </View>
              </View>
              <Text style={styles.detailAction}>{selectedDay.action}</Text>
              <Text style={styles.detailReason}>{selectedDay.reason}</Text>
              <Text style={styles.detailStrategy}>Strategy: {selectedDay.strategy}</Text>
            </View>
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
  header: { flexDirection: 'row', justifyContent: 'space-between', padding: 20, alignItems: 'center' },
  headerTitle: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  monthNav: { flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: 40, marginBottom: 20, alignItems: 'center' },
  monthTitle: { color: '#fff', fontSize: 20, fontWeight: '600' },
  weekHeader: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 10, paddingHorizontal: 10 },
  weekText: { color: '#888', width: 40, textAlign: 'center', fontSize: 12 },
  grid: { paddingHorizontal: 10 },
  dayCell: { width: '13%', aspectRatio: 1, margin: '0.6%', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  dayCellEmpty: { width: '13%', margin: '0.6%' },
  signalDot: { width: 6, height: 6, borderRadius: 3, position: 'absolute', top: 6, right: 6 },
  dayText: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  scoreText: { fontSize: 10, marginTop: 2, fontWeight: '600' },
  loader: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { color: '#aaa', marginTop: 10, fontSize: 14 },
  skeletonGrid: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 30, paddingHorizontal: 20 },
  skeletonDay: { width: '13%', aspectRatio: 1, margin: '0.6%', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 8 },
  emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptyTitle: { color: '#aaa', fontSize: 16, marginTop: 16, marginBottom: 20 },
  retryButton: { backgroundColor: '#6366F1', padding: 12, borderRadius: 8, flexDirection: 'row', alignItems: 'center', gap: 8 },
  retryText: { color: '#fff', fontWeight: 'bold' },
  detailCard: { backgroundColor: 'rgba(255,255,255,0.1)', margin: 20, padding: 20, borderRadius: 16, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.2)' },
  detailHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  detailDate: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  detailBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 4 },
  detailBadgeText: { color: '#000', fontSize: 10, fontWeight: 'bold' },
  detailAction: { color: '#fff', fontSize: 24, fontWeight: '900', marginBottom: 5 },
  detailReason: { color: '#ccc', fontSize: 14, marginBottom: 10 },
  detailStrategy: { color: '#FFD700', fontSize: 12, fontStyle: 'italic' },
  
  buttonRow: { flexDirection: 'row', gap: 12, marginTop: 20 },
  
  premiumToggle: { flexDirection: 'row', backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 8, padding: 4, marginVertical: 16 },
  toggleOption: { flex: 1, paddingVertical: 8, paddingHorizontal: 12, borderRadius: 6, alignItems: 'center' },
  toggleSelected: { backgroundColor: '#FFD700' },
  toggleText: { color: '#ccc', fontSize: 12, fontWeight: '600' },
  toggleTextSelected: { color: '#000' },
  toggleCost: { color: '#999', fontSize: 10, marginTop: 2 },
  toggleCostSelected: { color: '#000' }
});