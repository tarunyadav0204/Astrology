import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
  StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { COLORS } from '../../utils/constants';
import { storage } from '../../services/storage';
import { useCredits } from '../../credits/CreditContext';
import CascadingDashaBrowser from '../Dasha/CascadingDashaBrowser';

const { width } = Dimensions.get('window');

export default function ProfileScreen({ navigation }) {
  const { credits } = useCredits();
  const [userData, setUserData] = useState(null);
  const [birthData, setBirthData] = useState(null);
  const [stats, setStats] = useState({ totalChats: 0, chartsViewed: 0, daysActive: 0 });
  const [chartData, setChartData] = useState(null);
  const [loadingChart, setLoadingChart] = useState(false);
  const [showDashaBrowser, setShowDashaBrowser] = useState(false);
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    loadUserData();
    startAnimations();
  }, []);

  const startAnimations = () => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 8,
        useNativeDriver: true,
      }),
    ]).start();

    Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 20000,
        useNativeDriver: true,
      })
    ).start();
  };

  const loadUserData = async () => {
    try {
      const user = await storage.getUserData();
      setUserData(user);
      
      // Fetch user's self birth chart from API
      const { authAPI } = require('../../services/api');
      const response = await authAPI.getSelfBirthChart();
      
      if (response.data.has_self_chart) {
        setBirthData(response.data);
        setStats({
          totalChats: 24,
          chartsViewed: 12,
          daysActive: 7,
        });
        loadChartData(response.data);
      } else {
        // User hasn't set their own birth details
        setBirthData(null);
      }
    } catch (error) {
      console.error('Error loading user data:', error);
      setBirthData(null);
    }
  };
  
  const loadChartData = async (birth) => {
    try {
      setLoadingChart(true);
      const formattedData = {
        ...birth,
        date: typeof birth.date === 'string' ? birth.date.split('T')[0] : birth.date,
        time: typeof birth.time === 'string' ? birth.time.split('T')[1]?.slice(0, 5) || birth.time : birth.time,
        latitude: parseFloat(birth.latitude),
        longitude: parseFloat(birth.longitude),
        timezone: birth.timezone || 'Asia/Kolkata'
      };
      
      const { chartAPI } = require('../../services/api');
      const response = await chartAPI.calculateChartOnly(formattedData);
      console.log('Chart API Response:', JSON.stringify(response.data, null, 2));
      setChartData(response.data);
    } catch (error) {
      console.error('Error loading chart data:', error);
    } finally {
      setLoadingChart(false);
    }
  };

  const getSignName = (signNumber) => {
    const signs = {
      1: 'Aries', 2: 'Taurus', 3: 'Gemini', 4: 'Cancer',
      5: 'Leo', 6: 'Virgo', 7: 'Libra', 8: 'Scorpio',
      9: 'Sagittarius', 10: 'Capricorn', 11: 'Aquarius', 12: 'Pisces'
    };
    return signs[signNumber] || signNumber;
  };
  
  const getSignIcon = (signNumber) => {
    const icons = {
      1: '♈', 2: '♉', 3: '♊', 4: '♋',
      5: '♌', 6: '♍', 7: '♎', 8: '♏',
      9: '♐', 10: '♑', 11: '♒', 12: '♓'
    };
    return icons[signNumber] || '⭐';
  };

  const getZodiacSign = (date) => {
    if (!date) return '♈';
    const month = new Date(date).getMonth() + 1;
    const day = new Date(date).getDate();
    
    if ((month === 3 && day >= 21) || (month === 4 && day <= 19)) return '♈';
    if ((month === 4 && day >= 20) || (month === 5 && day <= 20)) return '♉';
    if ((month === 5 && day >= 21) || (month === 6 && day <= 20)) return '♊';
    if ((month === 6 && day >= 21) || (month === 7 && day <= 22)) return '♋';
    if ((month === 7 && day >= 23) || (month === 8 && day <= 22)) return '♌';
    if ((month === 8 && day >= 23) || (month === 9 && day <= 22)) return '♍';
    if ((month === 9 && day >= 23) || (month === 10 && day <= 22)) return '♎';
    if ((month === 10 && day >= 23) || (month === 11 && day <= 21)) return '♏';
    if ((month === 11 && day >= 22) || (month === 12 && day <= 21)) return '♐';
    if ((month === 12 && day >= 22) || (month === 1 && day <= 19)) return '♑';
    if ((month === 1 && day >= 20) || (month === 2 && day <= 18)) return '♒';
    return '♓';
  };

  const spin = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const StatCard = ({ icon, value, label, color }) => (
    <Animated.View style={[styles.statCard, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
      <LinearGradient
        colors={[color + '20', color + '10']}
        style={styles.statGradient}
      >
        <Text style={[styles.statIcon, { color }]}>{icon}</Text>
        <Text style={styles.statValue}>{value}</Text>
        <Text style={styles.statLabel}>{label}</Text>
      </LinearGradient>
    </Animated.View>
  );

  const ActionButton = ({ icon, label, onPress, color = COLORS.accent }) => (
    <TouchableOpacity style={styles.actionButton} onPress={onPress}>
      <LinearGradient
        colors={[color, color + 'dd']}
        style={styles.actionGradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View style={styles.actionContent}>
          <Ionicons name={icon} size={20} color={COLORS.white} />
          <Text style={styles.actionLabel}>{label}</Text>
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a0033" translucent={false} />
      <LinearGradient
        colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={COLORS.white} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>My Profile</Text>
            <View style={styles.editButton} />
          </View>

          <ScrollView 
            style={styles.scrollView}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
            <Animated.View style={[styles.profileHeader, { opacity: fadeAnim }]}>
              <View style={styles.avatarContainer}>
                <Animated.View style={[styles.zodiacRing, { transform: [{ rotate: spin }] }]}>
                  <LinearGradient
                    colors={['#ff6b35', '#ffd700', '#ff6b35']}
                    style={styles.ringGradient}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                  />
                </Animated.View>
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>{getZodiacSign(birthData?.date)}</Text>
                </View>
              </View>
              <Text style={styles.userName}>{userData?.name || 'User'}</Text>
              <Text style={styles.userSubtitle}>
                {birthData?.date ? new Date(birthData.date).toLocaleDateString('en-US', { 
                  month: 'long', 
                  day: 'numeric', 
                  year: 'numeric' 
                }) : 'Birth date not set'}
              </Text>
              {birthData?.time && (
                <Text style={styles.userSubtitle}>🕐 {birthData.time}</Text>
              )}
              {!birthData?.date && (
                <TouchableOpacity 
                  style={styles.connectChartButton}
                  onPress={() => navigation.navigate('SelectNative', { fromProfile: true })}
                >
                  <LinearGradient
                    colors={['#ff6b35', '#ff8c5a']}
                    style={styles.connectChartGradient}
                  >
                    <Text style={styles.connectChartText}>📊 Connect Chart to Profile</Text>
                  </LinearGradient>
                </TouchableOpacity>
              )}
              {birthData?.place && (
                <Text style={styles.userLocation}>📍 {birthData.place}</Text>
              )}
            </Animated.View>

            <Animated.View style={[styles.creditsCard, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
              <LinearGradient
                colors={['#ff6b35', '#ff8c5a', '#ffab7a']}
                style={styles.creditsGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <View style={styles.creditsContent}>
                  <View>
                    <Text style={styles.creditsLabel}>Available Credits</Text>
                    <Text style={styles.creditsValue}>{credits}</Text>
                  </View>
                  <TouchableOpacity 
                    style={styles.addCreditsButton}
                    onPress={() => navigation.navigate('Credits')}
                  >
                    <Text style={styles.addCreditsText}>+ Add</Text>
                  </TouchableOpacity>
                </View>
              </LinearGradient>
            </Animated.View>

            <View style={styles.statsGrid}>
              <StatCard icon="💬" value={stats.totalChats} label="Chats" color="#4a90e2" />
              <StatCard icon="📊" value={stats.chartsViewed} label="Charts" color="#9c27b0" />
              <StatCard icon="🔥" value={stats.daysActive} label="Days" color="#ff6b35" />
            </View>

            <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
              <Text style={styles.sectionTitle}>✨ Birth Chart Essence</Text>
              <View style={styles.chartSummaryCard}>
                <LinearGradient
                  colors={['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']}
                  style={styles.chartSummaryGradient}
                >
                  <TouchableOpacity 
                    style={styles.miniChart}
                    onPress={() => {
                      if (birthData) {
                        navigation.navigate('Chart', { birthData });
                      } else {
                        navigation.navigate('Home');
                      }
                    }}
                  >
                    <Text style={styles.miniChartIcon}>🔮</Text>
                    <Text style={styles.miniChartText}>View Full Chart</Text>
                  </TouchableOpacity>
                  
                  <View style={styles.chartDetails}>
                    <View style={styles.chartDetailRow}>
                      <Text style={styles.chartDetailLabel}>☀️ Sun Sign</Text>
                      <Text style={styles.chartDetailValue}>{loadingChart ? 'Calculating...' : `${getSignIcon(chartData?.planets?.Sun?.sign)} ${getSignName(chartData?.planets?.Sun?.sign)}`}</Text>
                    </View>
                    <View style={styles.chartDetailRow}>
                      <Text style={styles.chartDetailLabel}>🌙 Moon Sign</Text>
                      <Text style={styles.chartDetailValue}>{loadingChart ? 'Calculating...' : `${getSignIcon(chartData?.planets?.Moon?.sign)} ${getSignName(chartData?.planets?.Moon?.sign)}`}</Text>
                    </View>
                    <View style={styles.chartDetailRow}>
                      <Text style={styles.chartDetailLabel}>⬆️ Ascendant</Text>
                      <Text style={styles.chartDetailValue}>{loadingChart ? 'Calculating...' : `${getSignIcon(chartData?.houses?.[1]?.sign || chartData?.ascendant?.sign || chartData?.lagna?.sign)} ${getSignName(chartData?.houses?.[1]?.sign || chartData?.ascendant?.sign || chartData?.lagna?.sign)}`}</Text>
                    </View>
                  </View>
                </LinearGradient>
              </View>
            </Animated.View>

            <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
              <Text style={styles.sectionTitle}>⚡ Quick Actions</Text>
              <View style={styles.actionsGrid}>
                <ActionButton 
                  icon="chatbubbles" 
                  label="New Chat" 
                  onPress={() => navigation.navigate('Home', { startChat: true })}
                  color="#4a90e2"
                />
                <ActionButton 
                  icon="pie-chart" 
                  label="View Chart" 
                  onPress={() => {
                    if (birthData) {
                      navigation.navigate('Chart', { birthData });
                    } else {
                      navigation.navigate('Home');
                    }
                  }}
                  color="#9c27b0"
                />
                <ActionButton 
                  icon="time" 
                  label="Dashas" 
                  onPress={() => {
                    if (birthData) {
                      setShowDashaBrowser(true);
                    } else {
                      navigation.navigate('Home');
                    }
                  }}
                  color="#ff6b35"
                />
                <ActionButton 
                  icon="calendar" 
                  label="History" 
                  onPress={() => navigation.navigate('ChatHistory')}
                  color="#4caf50"
                />
              </View>
            </Animated.View>

            <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
              <Text style={styles.sectionTitle}>⚙️ Settings</Text>
              <View style={styles.settingsCard}>
                <TouchableOpacity style={styles.settingItem} onPress={() => navigation.navigate('BirthForm')}>
                  <View style={styles.settingLeft}>
                    <Ionicons name="person-outline" size={22} color="#ff6b35" />
                    <Text style={styles.settingText}>Edit Birth Details</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color="#999" />
                </TouchableOpacity>
                
                <View style={styles.settingDivider} />
                
                <TouchableOpacity style={styles.settingItem}>
                  <View style={styles.settingLeft}>
                    <Ionicons name="language-outline" size={22} color="#4a90e2" />
                    <Text style={styles.settingText}>Language</Text>
                  </View>
                  <Text style={styles.settingValue}>English</Text>
                </TouchableOpacity>
                
                <View style={styles.settingDivider} />
                
                <TouchableOpacity style={styles.settingItem}>
                  <View style={styles.settingLeft}>
                    <Ionicons name="notifications-outline" size={22} color="#9c27b0" />
                    <Text style={styles.settingText}>Notifications</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color="#999" />
                </TouchableOpacity>
                
                <View style={styles.settingDivider} />
                
                <TouchableOpacity style={styles.settingItem}>
                  <View style={styles.settingLeft}>
                    <Ionicons name="share-social-outline" size={22} color="#4caf50" />
                    <Text style={styles.settingText}>Share Profile</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color="#999" />
                </TouchableOpacity>
              </View>
            </Animated.View>

            <TouchableOpacity 
              style={styles.logoutButton}
              onPress={async () => {
                await storage.clearAll();
                navigation.navigate('Login');
              }}
            >
              <Text style={styles.logoutText}>🚪 Logout</Text>
            </TouchableOpacity>

            <View style={styles.bottomSpacer} />
          </ScrollView>
        </SafeAreaView>
      </LinearGradient>
      
      <CascadingDashaBrowser 
        visible={showDashaBrowser} 
        onClose={() => setShowDashaBrowser(false)}
        birthData={birthData}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 16 },
  backButton: { width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(255, 255, 255, 0.1)', alignItems: 'center', justifyContent: 'center' },
  headerTitle: { fontSize: 20, fontWeight: '700', color: COLORS.white },
  editButton: { width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(255, 255, 255, 0.1)', alignItems: 'center', justifyContent: 'center' },
  scrollView: { flex: 1 },
  scrollContent: { paddingHorizontal: 20, paddingBottom: 40 },
  profileHeader: { alignItems: 'center', marginTop: 20, marginBottom: 30 },
  avatarContainer: { position: 'relative', marginBottom: 16 },
  zodiacRing: { position: 'absolute', width: 120, height: 120, borderRadius: 60, top: -10, left: -10 },
  ringGradient: { width: '100%', height: '100%', borderRadius: 60, opacity: 0.3 },
  avatar: { width: 100, height: 100, borderRadius: 50, backgroundColor: 'rgba(255, 255, 255, 0.15)', alignItems: 'center', justifyContent: 'center', borderWidth: 3, borderColor: 'rgba(255, 255, 255, 0.3)' },
  avatarText: { fontSize: 48 },
  userName: { fontSize: 28, fontWeight: '700', color: COLORS.white, marginBottom: 4 },
  userSubtitle: { fontSize: 14, color: 'rgba(255, 255, 255, 0.7)', marginBottom: 4 },
  userLocation: { fontSize: 13, color: 'rgba(255, 255, 255, 0.6)' },
  creditsCard: { marginBottom: 24, borderRadius: 20, overflow: 'hidden', shadowColor: '#ff6b35', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.3, shadowRadius: 12, elevation: 8 },
  creditsGradient: { padding: 24 },
  creditsContent: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  creditsLabel: { fontSize: 14, color: 'rgba(255, 255, 255, 0.9)', marginBottom: 4 },
  creditsValue: { fontSize: 36, fontWeight: '700', color: COLORS.white },
  addCreditsButton: { backgroundColor: 'rgba(255, 255, 255, 0.25)', paddingHorizontal: 20, paddingVertical: 12, borderRadius: 20, borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.3)' },
  addCreditsText: { color: COLORS.white, fontSize: 16, fontWeight: '700' },
  statsGrid: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 24, gap: 12 },
  statCard: { flex: 1, borderRadius: 16, overflow: 'hidden' },
  statGradient: { padding: 16, alignItems: 'center' },
  statIcon: { fontSize: 32, marginBottom: 8 },
  statValue: { fontSize: 24, fontWeight: '700', color: COLORS.white, marginBottom: 4 },
  statLabel: { fontSize: 12, color: 'rgba(255, 255, 255, 0.8)' },
  section: { marginBottom: 24 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: COLORS.white, marginBottom: 12 },
  chartSummaryCard: { borderRadius: 16, overflow: 'hidden' },
  chartSummaryGradient: { padding: 20 },
  miniChart: { alignItems: 'center', marginBottom: 20, paddingVertical: 20, borderRadius: 12, backgroundColor: 'rgba(255, 255, 255, 0.05)' },
  miniChartIcon: { fontSize: 48, marginBottom: 8 },
  miniChartText: { color: COLORS.white, fontSize: 14, fontWeight: '600' },
  chartDetails: { gap: 12 },
  chartDetailRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  chartDetailLabel: { fontSize: 14, color: 'rgba(255, 255, 255, 0.7)' },
  chartDetailValue: { fontSize: 14, fontWeight: '600', color: COLORS.white },
  actionsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  actionButton: { width: (width - 52) / 2, borderRadius: 16, overflow: 'hidden', shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 5 },
  actionGradient: { padding: 12, justifyContent: 'center' },
  actionContent: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  actionLabel: { color: COLORS.white, fontSize: 13, fontWeight: '600' },
  settingsCard: { backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: 16, padding: 4 },
  settingItem: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16 },
  settingLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  settingText: { fontSize: 16, color: COLORS.white, fontWeight: '500' },
  settingValue: { fontSize: 14, color: 'rgba(255, 255, 255, 0.6)' },
  settingDivider: { height: 1, backgroundColor: 'rgba(255, 255, 255, 0.1)', marginHorizontal: 16 },
  logoutButton: { backgroundColor: 'rgba(255, 107, 53, 0.2)', borderWidth: 1, borderColor: 'rgba(255, 107, 53, 0.5)', borderRadius: 16, padding: 16, alignItems: 'center', marginTop: 12 },
  logoutText: { color: '#ff6b35', fontSize: 16, fontWeight: '700' },
  bottomSpacer: { height: 20 },
  connectChartButton: {
    marginTop: 12,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  connectChartGradient: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  connectChartText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
});
