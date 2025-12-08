import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, Modal, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useCredits } from '../../credits/CreditContext';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../../utils/constants';

const LuckGauge = ({ score, signal }) => {
  const getColor = () => {
    if (signal === 'GREEN') return ['#00C853', '#69F0AE'];
    if (signal === 'RED') return ['#D50000', '#FF5252'];
    return ['#FFD600', '#FFFF00'];
  };

  return (
    <View style={styles.gaugeContainer}>
      <LinearGradient colors={getColor()} style={styles.gaugeCircle}>
        <View style={styles.gaugeInner}>
          <Text style={styles.scoreText}>{score}</Text>
          <Text style={styles.scoreLabel}>LUCK SCORE</Text>
        </View>
      </LinearGradient>
    </View>
  );
};

const IntradayTimeline = ({ timings }) => {
  return (
    <View style={styles.timelineContainer}>
      <Text style={styles.sectionHeader}>MARKET TIMING (09:15 - 15:30)</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.timelineScroll}>
        {timings.map((slot, index) => {
          let borderColor = '#FFD600';
          let bgColor = 'rgba(255, 214, 0, 0.1)';
          
          if (slot.color === 'green') {
             borderColor = '#00C853';
             bgColor = 'rgba(0, 200, 83, 0.1)';
          } else if (slot.color === 'red') {
             borderColor = '#D50000';
             bgColor = 'rgba(213, 0, 0, 0.1)';
          }

          return (
            <View key={index} style={[styles.timeSlot, { backgroundColor: bgColor, borderColor: borderColor }]}>
              <Text style={styles.timeText}>{slot.start}</Text>
              <Text style={[styles.qualityText, { color: borderColor }]}>{slot.name}</Text>
              <Text style={styles.timeText}>{slot.end}</Text>
            </View>
          );
        })}
      </ScrollView>
    </View>
  );
};

const FormattedText = ({ text, style }) => {
  if (!text) return <Text style={style}></Text>;
  
  const parts = text.split(/\*(.*?)\*/g);
  
  return (
    <Text style={style}>
      {parts.map((part, index) => {
        if (index % 2 === 1) {
          return <Text key={index} style={{ fontWeight: 'bold', color: '#FFD700' }}>{part}</Text>;
        }
        return part;
      })}
    </Text>
  );
};

const RiskBadge = ({ risks }) => {
  if (!risks || risks.length === 0 || risks[0] === 'None') return null;
  const displayRisks = Array.isArray(risks) ? risks.map(r => r.name).join(', ') : risks;
  
  if (displayRisks === 'None' || displayRisks === '') return null;

  return (
    <View style={styles.riskContainer}>
      <Ionicons name="warning" size={20} color="#FF5252" />
      <Text style={styles.riskText}>WARNING: {displayRisks} Active</Text>
    </View>
  );
};

export default function TradingDashboardScreen({ navigation }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showCreditModal, setShowCreditModal] = useState(true);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [dailyCost, setDailyCost] = useState(5);
  const [premiumCost, setPremiumCost] = useState(50);
  const [isPremium, setIsPremium] = useState(false);
  const { credits, fetchBalance } = useCredits();

  useEffect(() => {
    fetchBalance();
    fetchCosts();
    checkCacheFirst();
  }, []);

  const fetchCosts = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}/credits/settings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        const baseCost = data.trading_daily_cost || 5;
        const multiplier = data.premium_chat_cost || 10;
        setDailyCost(baseCost);
        setPremiumCost(baseCost * multiplier);
      }
    } catch (error) {
      // Keep default cost if fetch fails
    }
  };

  const checkCacheFirst = async () => {
    try {
      // Try to fetch cached data first
      let birthData = null;
      
      const birthDataStr = await AsyncStorage.getItem('userBirthData');
      if (birthDataStr) {
        birthData = JSON.parse(birthDataStr);
      }
      
      if (!birthData) {
        const birthDetailsStr = await AsyncStorage.getItem('birthDetails');
        if (birthDetailsStr) {
          birthData = JSON.parse(birthDetailsStr);
        }
      }
      
      if (birthData) {
        const token = await AsyncStorage.getItem('authToken');
        const now = new Date();
        const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        
        const response = await fetch(`${API_BASE_URL}/trading/daily-forecast`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json', 
            'Authorization': `Bearer ${token}` 
          },
          body: JSON.stringify({ ...birthData, target_date: today })
        });
        
        if (response.ok) {
          const json = await response.json();
          if (json.status === 'success' && json.cached) {
            // Found cached data, skip credit modal
            setData(json);
            setShowCreditModal(false);
            return;
          }
        }
      }
    } catch (error) {
      // If cache check fails, continue with credit modal
    }
  };

  const fetchForecast = async (forceRegenerate = false) => {
    try {
      setLoading(true);
      
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
              timezone: firstChart.timezone,
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
      const token = await AsyncStorage.getItem('authToken');
      
      // FIX: Use local time instead of UTC to avoid date discrepancy
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const today = `${year}-${month}-${day}`;
      

      
      // Ensure birthData has required fields
      if (!birthData || !birthData.name || !birthData.date) {
        navigation.replace('SelectNative');
        return;
      }

      console.log('🚀 Making API request to:', `${API_BASE_URL}/api/trading/daily-forecast`);
      console.log('📤 Request payload:', JSON.stringify({ ...birthData, target_date: today, premium_analysis: isPremium }));
      
      const response = await fetch(`${API_BASE_URL}/api/trading/daily-forecast`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ ...birthData, target_date: today, premium_analysis: isPremium, force_regenerate: forceRegenerate })
      });

      console.log('📥 Response status:', response.status);
      console.log('📥 Response headers:', JSON.stringify(Object.fromEntries(response.headers.entries())));

      if (response.status === 402) {
        console.log('❌ Insufficient credits (402)');
        Alert.alert("Insufficient Credits", "You need 5 credits for daily forecast. Please purchase more credits.", [
          { text: "OK", onPress: () => navigation.navigate('Credits') }
        ]);
        return;
      }

      const text = await response.text();
      console.log('📄 Raw response text:', text);
      console.log('📏 Response length:', text.length);
      
      try {
        const json = JSON.parse(text);
        console.log('✅ Parsed JSON:', JSON.stringify(json, null, 2));
        
        if (json.status === 'success') {
          setData(json);
          fetchBalance();
        } else {
          console.log('❌ API returned error status:', json.status, json.message);
          Alert.alert("Analysis Error", json.message || "Failed to generate forecast", [
            { text: "Retry", onPress: fetchForecast },
            { text: "Go Back", onPress: () => navigation.goBack() }
          ]);
        }
      } catch (parseError) {
        console.log('❌ JSON Parse Error:', parseError.message);
        console.log('❌ Failed to parse response:', text.substring(0, 500));
        Alert.alert("Parse Error", `Invalid response format from server. Response: ${text.substring(0, 100)}...`, [
          { text: "Go Back", onPress: () => navigation.goBack() }
        ]);
      }

    } catch (e) {
      console.log('❌ Network/Connection Error:', e.message);
      console.log('❌ Full error:', e);
      Alert.alert("Connection Error", `Network issue: ${e.message}. Please check your connection.`, [
        { text: "Retry", onPress: fetchForecast },
        { text: "Go Back", onPress: () => navigation.goBack() }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const confirmAndRunAnalysis = () => {
    const cost = isPremium ? premiumCost : dailyCost;
    if (credits < cost) {
      const analysisType = isPremium ? "premium trading analysis" : "daily forecast";
      Alert.alert("Insufficient Credits", `You need ${cost} credits for ${analysisType}. Please purchase more credits.`, [
        { text: "Buy Credits", onPress: () => navigation.navigate('Credits') },
        { text: "Cancel", onPress: () => navigation.goBack() }
      ]);
      return;
    }
    setShowCreditModal(false);
    fetchForecast();
  };

  if (showCreditModal && !data) return (
    <View style={styles.centerContainer}>
      <LinearGradient colors={['#0f0c29', '#302b63']} style={styles.bg}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.loadingContainer}>
            <Ionicons name="card" size={48} color="#FFD700" />
            <Text style={styles.errorTitle}>Trading Analysis</Text>
            
            <View style={styles.premiumToggle}>
              <TouchableOpacity 
                style={[styles.toggleOption, !isPremium && styles.toggleActive]} 
                onPress={() => setIsPremium(false)}
              >
                <Text style={[styles.toggleText, !isPremium && styles.toggleTextActive]}>Standard</Text>
                <Text style={styles.toggleCost}>{dailyCost} credits</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.toggleOption, isPremium && styles.toggleActive]} 
                onPress={() => setIsPremium(true)}
              >
                <Text style={[styles.toggleText, isPremium && styles.toggleTextActive]}>Premium AI</Text>
                <Text style={styles.toggleCost}>{premiumCost} credits</Text>
              </TouchableOpacity>
            </View>
            
            <Text style={styles.errorSubtitle}>Your balance: {credits} credits</Text>
            <View style={styles.buttonRow}>
              <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.retryButton, {backgroundColor: '#666'}]}>
                <Text style={[styles.retryText, {color: '#fff'}]}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={confirmAndRunAnalysis} style={styles.retryButton}>
                <Text style={styles.retryText}>Run Analysis</Text>
              </TouchableOpacity>
            </View>
          </View>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );

  if (loading) return (
    <View style={styles.centerContainer}>
        <LinearGradient colors={['#0f0c29', '#302b63']} style={styles.bg}>
          <SafeAreaView style={styles.safeArea}>
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#00C853" />
              <Text style={styles.loadingText}>Aligning Market Stars...</Text>
              <View style={styles.skeletonContainer}>
                <View style={styles.skeletonGauge} />
                <View style={styles.skeletonText} />
                <View style={styles.skeletonText} />
              </View>
            </View>
          </SafeAreaView>
        </LinearGradient>
    </View>
  );

  if (!data) return (
    <View style={styles.centerContainer}>
        <LinearGradient colors={['#0f0c29', '#302b63']} style={styles.bg}>
          <SafeAreaView style={styles.safeArea}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()}>
                    <Ionicons name="arrow-back" size={24} color="#fff" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Trading Cockpit</Text>
                <View style={{width:24}}/>
            </View>
            <View style={styles.loadingContainer}>
              <Ionicons name="warning-outline" size={48} color="#FF6D00" />
              <Text style={styles.errorTitle}>No Forecast Available</Text>
              <Text style={styles.errorSubtitle}>Unable to load trading data</Text>
              <View style={styles.buttonRow}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.retryButton, {backgroundColor: '#666'}]}>
                  <Text style={[styles.retryText, {color: '#fff'}]}>Go Back</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={fetchForecast} style={styles.retryButton}>
                    <Ionicons name="refresh" size={16} color="#000" />
                    <Text style={styles.retryText}>Try Again</Text>
                </TouchableOpacity>
              </View>
            </View>
          </SafeAreaView>
        </LinearGradient>
    </View>
  );

  const { raw_forecast, intraday_timings, ai_analysis } = data;
  const isGreen = raw_forecast.signal === 'GREEN';

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#0f0c29', '#302b63', '#24243e']} style={styles.bg}>
        <SafeAreaView style={styles.safeArea}>
          <ScrollView>
            
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()}>
                    <Ionicons name="arrow-back" size={24} color="#fff" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Trading Cockpit</Text>
                <TouchableOpacity onPress={() => setShowRegenerateModal(true)}>
                    <Ionicons name="refresh" size={24} color="#fff" />
                </TouchableOpacity>
            </View>

            <View style={styles.heroSection}>
              <Text style={styles.dateText}>{new Date().toDateString()}</Text>
              
              <LuckGauge score={raw_forecast.luck_score} signal={raw_forecast.signal} />
              
              <Text style={[styles.verdictText, { color: isGreen ? '#69F0AE' : '#FF5252' }]}>
                {ai_analysis.verdict}
              </Text>
              
              <View style={styles.strategyChip}>
                <Ionicons name="flash" size={16} color="#FFD700" />
                <Text style={styles.strategyText}>Mood: {raw_forecast.market_mood.nature?.toUpperCase() || "NEUTRAL"}</Text>
              </View>
              
              <RiskBadge risks={raw_forecast.risk_factors} />
            </View>

            <IntradayTimeline timings={intraday_timings.timings} />

            <View style={styles.gridContainer}>
              <View style={styles.gridItem}>
                <Text style={styles.gridLabel}>Tara Bala</Text>
                <Text style={styles.gridValue}>{raw_forecast.details.tara_bala.type}</Text>
                <Text style={styles.gridSub}>{raw_forecast.details.tara_bala.quality}</Text>
              </View>
              <View style={styles.gridItem}>
                <Text style={styles.gridLabel}>Moon House</Text>
                <Text style={styles.gridValue}>{raw_forecast.details.chandra_bala.transit_house_from_natal}th</Text>
                <Text style={styles.gridSub}>{raw_forecast.details.chandra_bala.quality}</Text>
              </View>
              <View style={styles.gridItem}>
                <Text style={styles.gridLabel}>Strength</Text>
                <Text style={styles.gridValue}>{raw_forecast.details.ashtakavarga.points}</Text>
                <Text style={styles.gridSub}>Points</Text>
              </View>
            </View>

            <TouchableOpacity onPress={() => setShowDetailModal(true)}>
              <View style={styles.aiCard}>
                <View style={styles.aiHeader}>
                  <Ionicons name="analytics" size={20} color="#fff" />
                  <Text style={styles.aiTitle}>AI Analysis (Tap to Read)</Text>
                </View>
                <Text style={styles.aiText} numberOfLines={3}>{ai_analysis.summary}</Text>
                <Text style={styles.readMoreText}>Read full report...</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity style={styles.calendarButton} onPress={() => navigation.navigate('TradingCalendar')}>
              <Text style={styles.calendarButtonText}>View Monthly Planner</Text>
              <Ionicons name="calendar" size={20} color="#fff" />
            </TouchableOpacity>

          </ScrollView>

          <Modal visible={showRegenerateModal} transparent animationType="slide">
            <View style={styles.modalOverlay}>
              <View style={styles.modalContent}>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>Regenerate Analysis</Text>
                  <TouchableOpacity onPress={() => setShowRegenerateModal(false)}>
                    <Ionicons name="close-circle" size={28} color="#FF5252" />
                  </TouchableOpacity>
                </View>
                
                <View style={styles.premiumToggle}>
                  <TouchableOpacity 
                    style={[styles.toggleOption, !isPremium && styles.toggleActive]} 
                    onPress={() => setIsPremium(false)}
                  >
                    <Text style={[styles.toggleText, !isPremium && styles.toggleTextActive]}>Standard</Text>
                    <Text style={styles.toggleCost}>{dailyCost} credits</Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={[styles.toggleOption, isPremium && styles.toggleActive]} 
                    onPress={() => setIsPremium(true)}
                  >
                    <Text style={[styles.toggleText, isPremium && styles.toggleTextActive]}>Premium AI</Text>
                    <Text style={styles.toggleCost}>{premiumCost} credits</Text>
                  </TouchableOpacity>
                </View>
                
                <Text style={styles.errorSubtitle}>Your balance: {credits} credits</Text>
                <View style={styles.buttonRow}>
                  <TouchableOpacity onPress={() => setShowRegenerateModal(false)} style={[styles.retryButton, {backgroundColor: '#666'}]}>
                    <Text style={[styles.retryText, {color: '#fff'}]}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity onPress={() => { setShowRegenerateModal(false); fetchForecast(true); }} style={styles.retryButton}>
                    <Text style={styles.retryText}>Regenerate</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </Modal>

          <Modal visible={showDetailModal} transparent animationType="slide">
            <View style={styles.modalOverlay}>
                <View style={styles.modalContent}>
                    <View style={styles.modalHeader}>
                        <Text style={styles.modalTitle}>Daily Trading Report</Text>
                        <TouchableOpacity onPress={() => setShowDetailModal(false)}>
                            <Ionicons name="close-circle" size={28} color="#FF5252" />
                        </TouchableOpacity>
                    </View>
                    
                    <ScrollView contentContainerStyle={styles.modalScroll}>
                        
                        <View style={styles.reportSection}>
                            <Text style={styles.reportLabel}>EXECUTIVE SUMMARY</Text>
                            <FormattedText text={ai_analysis.summary} style={styles.reportText} />
                        </View>

                        {ai_analysis.detailed_report && ai_analysis.detailed_report.map((item, index) => (
                            <View key={index} style={styles.reportSection}>
                                <Text style={styles.reportLabel}>{item.title.toUpperCase()}</Text>
                                <FormattedText text={item.content} style={styles.reportText} />
                            </View>
                        ))}

                        {ai_analysis.risk_warning && ai_analysis.risk_warning !== "None" && (
                            <View style={[styles.reportSection, {borderLeftColor: '#FF5252'}]}>
                                <Text style={[styles.reportLabel, {color: '#FF5252'}]}>RISK WARNING</Text>
                                <FormattedText text={ai_analysis.risk_warning} style={styles.reportText} />
                            </View>
                        )}

                    </ScrollView>
                </View>
            </View>
          </Modal>

        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  bg: { flex: 1, width: '100%', height: '100%' },
  safeArea: { flex: 1 },
  centerContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  retryButton: { backgroundColor: 'white', padding: 12, borderRadius: 8, marginTop: 20, flexDirection: 'row', alignItems: 'center', gap: 8 },
  retryText: { color: 'black', fontWeight: 'bold', fontSize: 14 },
  errorTitle: { color: '#fff', fontSize: 18, fontWeight: 'bold', marginTop: 16 },
  errorSubtitle: { color: '#aaa', fontSize: 14, marginTop: 4, textAlign: 'center' },
  
  loadingContainer: { alignItems: 'center', justifyContent: 'center', flex: 1 },
  loadingText: { color: 'white', marginTop: 20, fontSize: 16 },
  skeletonContainer: { marginTop: 30, alignItems: 'center' },
  skeletonGauge: { width: 120, height: 120, borderRadius: 60, backgroundColor: 'rgba(255,255,255,0.1)', marginBottom: 20 },
  skeletonText: { width: 200, height: 16, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 8, marginBottom: 12 },
  
  header: { flexDirection: 'row', justifyContent: 'space-between', padding: 20 },
  headerTitle: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  
  heroSection: { alignItems: 'center', paddingVertical: 10 },
  dateText: { color: '#aaa', fontSize: 14, marginBottom: 15 },
  
  gaugeContainer: { width: 180, height: 180, justifyContent: 'center', alignItems: 'center', marginBottom: 15 },
  gaugeCircle: { width: 160, height: 160, borderRadius: 80, padding: 4, justifyContent: 'center', alignItems: 'center' },
  gaugeInner: { width: 140, height: 140, borderRadius: 70, backgroundColor: '#1a1a2e', justifyContent: 'center', alignItems: 'center' },
  scoreText: { color: '#fff', fontSize: 42, fontWeight: 'bold' },
  scoreLabel: { color: '#888', fontSize: 10, marginTop: 4 },
  
  verdictText: { fontSize: 24, fontWeight: '900', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 8 },
  
  strategyChip: { flexDirection: 'row', backgroundColor: 'rgba(255, 255, 255, 0.1)', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, alignItems: 'center', gap: 6 },
  strategyText: { color: '#FFD700', fontWeight: 'bold', fontSize: 12 },
  
  riskContainer: { flexDirection: 'row', marginTop: 12, backgroundColor: 'rgba(255, 82, 82, 0.15)', padding: 8, borderRadius: 8, alignItems: 'center', gap: 6 },
  riskText: { color: '#FF5252', fontWeight: 'bold', fontSize: 11 },
  
  timelineContainer: { marginVertical: 20, height: 90 },
  sectionHeader: { color: '#fff', marginLeft: 20, marginBottom: 10, fontWeight: 'bold', fontSize: 12, opacity: 0.8 },
  timelineScroll: { paddingHorizontal: 20, gap: 8 },
  timeSlot: { width: 90, height: 60, borderWidth: 1, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  timeText: { color: '#ccc', fontSize: 9 },
  qualityText: { fontSize: 14, fontWeight: 'bold', marginVertical: 2 },
  
  gridContainer: { flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: 20, marginBottom: 20 },
  gridItem: { width: '31%', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 12, padding: 10, alignItems: 'center' },
  gridLabel: { color: '#888', fontSize: 10, marginBottom: 2 },
  gridValue: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  gridSub: { color: '#aaa', fontSize: 9 },
  
  aiCard: { marginHorizontal: 20, backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 16, padding: 16, marginBottom: 20 },
  aiHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  aiTitle: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  aiText: { color: '#ddd', lineHeight: 20, fontSize: 13 },
  
  calendarButton: { marginHorizontal: 20, backgroundColor: '#6366F1', flexDirection: 'row', justifyContent: 'center', alignItems: 'center', padding: 14, borderRadius: 12, gap: 10, marginBottom: 30 },
  calendarButtonText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  
  readMoreText: { color: '#6366F1', fontSize: 12, fontWeight: 'bold', marginTop: 8 },
  
  modalOverlay: { position: 'absolute', top:0, bottom:0, left:0, right:0, backgroundColor:'rgba(0,0,0,0.85)', justifyContent:'flex-end' },
  modalContent: { backgroundColor: '#1a1a2e', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 20, height: '85%', borderWidth: 1, borderColor: '#333' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.1)', paddingBottom: 15 },
  modalTitle: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  modalScroll: { paddingBottom: 40 },
  
  reportSection: { marginBottom: 24, borderLeftWidth: 3, borderLeftColor: '#6366F1', paddingLeft: 12 },
  reportLabel: { color: '#6366F1', fontSize: 12, fontWeight: 'bold', marginBottom: 6, letterSpacing: 1, textTransform: 'uppercase' },
  reportText: { color: '#ddd', fontSize: 15, lineHeight: 24 },
  
  buttonRow: { flexDirection: 'row', gap: 12, marginTop: 20 },
  
  premiumToggle: { flexDirection: 'row', marginVertical: 16, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 8, padding: 4 },
  toggleOption: { flex: 1, padding: 12, borderRadius: 6, alignItems: 'center' },
  toggleActive: { backgroundColor: '#FFD700' },
  toggleText: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  toggleTextActive: { color: '#000' },
  toggleCost: { color: '#aaa', fontSize: 12, marginTop: 2 }
});