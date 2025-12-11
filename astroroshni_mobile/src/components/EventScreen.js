import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
  FlatList
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useNavigation } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { chatAPI } from '../services/api';
import { storage } from '../services/storage';
import MonthlyAccordion from './MonthlyAccordion';
import MilestoneCarousel from './MilestoneCarousel';

const { width } = Dimensions.get('window');

export default function EventScreen({ route }) {
  const navigation = useNavigation();
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [milestones, setMilestones] = useState([]);
  const [monthlyData, setMonthlyData] = useState(null);
  
  // Loading states
  const [loadingMilestones, setLoadingMilestones] = useState(false);
  const [loadingMonthly, setLoadingMonthly] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const yearSliderRef = useRef(null);

  // Get birth data from storage
  const getBirthDetails = async () => {
    try {
      return await storage.getBirthDetails();
    } catch (error) {
      console.error('Error getting birth details:', error);
      return null;
    }
  };

  // 1. Fetch Major Milestones (Fast Math)
  const fetchMilestones = useCallback(async (year) => {
    setLoadingMilestones(true);
    try {
      const birthData = await getBirthDetails();
      if (!birthData) return;
      
      const response = await chatAPI.getEventPeriods({
        ...birthData,
        selectedYear: year
      });
      
      if (response.data && response.data.periods) {
        setMilestones(response.data.periods);
      }
    } catch (error) {
      console.error("Error fetching milestones:", error);
    } finally {
      setLoadingMilestones(false);
    }
  }, []);

  // 2. Fetch Monthly Guide (AI Powered - Slower)
  const fetchMonthlyGuide = useCallback(async (year) => {
    setLoadingMonthly(true);
    setMonthlyData(null); // Clear old data to show loading state
    try {
      const birthData = await getBirthDetails();
      if (!birthData) return;
      
      const response = await chatAPI.getMonthlyEvents({
        ...birthData,
        selectedYear: year
      });
      
      if (response.data && response.data.data) {
        setMonthlyData(response.data.data);
      }
    } catch (error) {
      console.error("Error fetching monthly guide:", error);
    } finally {
      setLoadingMonthly(false);
    }
  }, []);

  // Initial Load
  useEffect(() => {
    fetchMilestones(selectedYear);
    fetchMonthlyGuide(selectedYear);
  }, [selectedYear]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    Promise.all([fetchMilestones(selectedYear), fetchMonthlyGuide(selectedYear)])
      .then(() => setRefreshing(false));
  }, [selectedYear]);

  const handleYearChange = (year) => {
    setSelectedYear(year);
    // Auto-scroll to selected year
    const index = year - 1950;
    yearSliderRef.current?.scrollToIndex({ index, animated: true });
  };

  const navigateToChat = (context, type) => {
    navigation.navigate('ChatScreen', {
      initialMessage: `I want to know more about the ${type} prediction for ${context.title || context.month}.`,
      contextData: context,
      contextType: type
    });
  };

  const getMonthName = (monthId) => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months[monthId - 1] || `Month ${monthId}`;
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="white" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Cosmic Timeline</Text>
        <View style={styles.headerSpacer} />
      </View>

      {/* Year Slider */}
      <View style={styles.yearSliderContainer}>
        <FlatList
          ref={yearSliderRef}
          data={Array.from({length: 101}, (_, i) => 1950 + i)}
          keyExtractor={(item) => item.toString()}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.yearSliderContent}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[styles.yearChip, selectedYear === item && styles.selectedYearChip]}
              onPress={() => handleYearChange(item)}
            >
              <Text style={[styles.yearChipText, selectedYear === item && styles.selectedYearChipText]}>
                {item}
              </Text>
            </TouchableOpacity>
          )}
          getItemLayout={(data, index) => ({
            length: 60,
            offset: 60 * index,
            index,
          })}
          initialScrollIndex={selectedYear - 1950}
        />
      </View>

      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="white" />}
      >
        
        {/* SECTION 1: Major Milestones (The "Hook") */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>✨ Major Milestones</Text>
            <Text style={styles.sectionSubtitle}>High impact events for {selectedYear}</Text>
          </View>
          
          {loadingMilestones ? (
            <ActivityIndicator size="small" color="#6C5DD3" style={{ marginTop: 20 }} />
          ) : (
            <MilestoneCarousel 
              data={milestones} 
              onPress={(item) => navigateToChat(item, 'milestone')}
            />
          )}
        </View>

        {/* SECTION 2: Macro Trends (The "Vibe") */}
        {monthlyData?.macro_trends && (
          <LinearGradient colors={['#2A2A40', '#1F1F30']} style={styles.macroCard}>
            <View style={styles.macroHeader}>
              <Ionicons name="planet" size={18} color="#FFD700" />
              <Text style={styles.macroTitle}>The Vibe of {selectedYear}</Text>
            </View>
            {monthlyData.macro_trends.map((trend, index) => (
              <View key={index} style={styles.trendRow}>
                <Text style={styles.bullet}>•</Text>
                <Text style={styles.trendText}>{trend}</Text>
              </View>
            ))}
          </LinearGradient>
        )}

        {/* SECTION 3: Monthly Guide (The "Details") */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📅 Monthly Guide</Text>
          
          {loadingMonthly ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#6C5DD3" />
              <Text style={styles.loadingText}>Aligning the stars for {selectedYear}...</Text>
              <Text style={styles.loadingSubText}>(This uses advanced AI, please wait)</Text>
            </View>
          ) : (
            <View style={styles.accordionContainer}>
              {monthlyData?.monthly_predictions?.map((month, index) => (
                <MonthlyAccordion 
                  key={index} 
                  data={{...month, month: getMonthName(month.month_id)}} 
                  onChatPress={() => navigateToChat({...month, month: getMonthName(month.month_id)}, 'monthly')}
                />
              ))}
            </View>
          )}
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121212' },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#1E1E2E',
    borderBottomWidth: 1,
    borderBottomColor: '#333',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between'
  },
  backButton: {
    padding: 4
  },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: 'white', flex: 1, textAlign: 'center' },
  headerSpacer: { width: 32 },
  
  yearSliderContainer: {
    backgroundColor: '#1E1E2E',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#333'
  },
  yearSliderContent: {
    paddingHorizontal: 10
  },
  yearChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginHorizontal: 4,
    borderRadius: 20,
    backgroundColor: '#2A2A40',
    borderWidth: 1,
    borderColor: '#444'
  },
  selectedYearChip: {
    backgroundColor: '#FFD700',
    borderColor: '#FFD700'
  },
  yearChipText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#AAA'
  },
  selectedYearChipText: {
    color: '#000'
  },
  
  scrollContent: { paddingBottom: 40 },
  
  section: { marginTop: 20 },
  sectionHeader: { paddingHorizontal: 20, marginBottom: 15 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: 'white', marginBottom: 4 },
  sectionSubtitle: { fontSize: 13, color: '#AAA' },
  
  macroCard: {
    margin: 20,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#333'
  },
  macroHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 10, gap: 8 },
  macroTitle: { fontSize: 16, fontWeight: 'bold', color: '#FFD700' },
  trendRow: { flexDirection: 'row', marginBottom: 6 },
  bullet: { color: '#FFD700', marginRight: 8, fontSize: 16 },
  trendText: { color: '#DDD', fontSize: 14, lineHeight: 20, flex: 1 },
  
  loadingContainer: { alignItems: 'center', marginTop: 40 },
  loadingText: { color: 'white', marginTop: 10, fontSize: 16, fontWeight: '600' },
  loadingSubText: { color: '#888', marginTop: 5, fontSize: 12 },
  
  accordionContainer: { paddingHorizontal: 20 }
});