import React, { useState, useMemo, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');

// --- CONSTANTS & HELPERS ---

const YOGINI_CONFIG = {
  Mangala: { color: ['#11998e', '#38ef7d'], icon: 'moon', label: 'Success' },
  Pingala: { color: ['#ff9966', '#ff5e62'], icon: 'sunny', label: 'Aggression' },
  Dhanya:  { color: ['#f2994a', '#f2c94c'], icon: 'wallet', label: 'Wealth' },
  Bhramari:{ color: ['#cb2d3e', '#ef473a'], icon: 'airplane', label: 'Travel' },
  Bhadrika:{ color: ['#56ab2f', '#a8e063'], icon: 'people', label: 'Career' },
  Ulka:    { color: ['#2980b9', '#6dd5fa'], icon: 'thunderstorm', label: 'Workload' },
  Siddha:  { color: ['#8E2DE2', '#4A00E0'], icon: 'star', label: 'Victory' },
  Sankata: { color: ['#833ab4', '#fd1d1d'], icon: 'alert-circle', label: 'Crisis' },
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
  } catch {
    return '';
  }
};

// --- SUB-COMPONENTS ---

const DashaProgress = ({ percentage = 0 }) => (
  <View style={styles.progressContainer}>
    <View style={styles.track} />
    <LinearGradient
      colors={['#8E2DE2', '#4A00E0']}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 0 }}
      style={[styles.fill, { width: `${percentage}%` }]}
    />
    <Text style={styles.progressText}>{Math.round(percentage)}% Completed</Text>
  </View>
);

const YoginiCard = ({ item, isCurrent, isExpanded, onPress, currentAntardasha }) => {
  const config = YOGINI_CONFIG[item.name] || YOGINI_CONFIG['Mangala'];
  
  return (
    <View>
      <TouchableOpacity 
        style={[styles.card, isCurrent && styles.activeCard]} 
        onPress={onPress}
        activeOpacity={0.9}
      >
        {/* Header Strip */}
        <LinearGradient
          colors={config.color}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.cardHeader}
        />

        <View style={styles.cardContent}>
          {/* Left: Icon & Name */}
          <View style={styles.cardLeft}>
            <View style={[styles.iconBox, { backgroundColor: config.color[0] + '20' }]}>
              <Ionicons name={config.icon} size={24} color={config.color[0]} />
            </View>
            <View>
              <Text style={styles.yoginiName}>{item.name}</Text>
              <Text style={styles.yoginiLord}>{item.lord}</Text>
            </View>
          </View>

          {/* Right: Dates & Badge */}
          <View style={styles.cardRight}>
            <View style={[styles.vibeBadge, { backgroundColor: config.color[0] + '15' }]}>
              <Text style={[styles.vibeText, { color: config.color[0] }]}>{config.label}</Text>
            </View>
            <Text style={styles.dateText}>
              {formatDate(item.start)} - {formatDate(item.end)}
            </Text>
          </View>
        </View>

        {/* Expansion Indicator */}
        {isCurrent && (
          <View style={styles.currentIndicator}>
            <Text style={styles.currentText}>Currently Running</Text>
          </View>
        )}
      </TouchableOpacity>

      {/* Expanded Sub-Periods (Antardasha) */}
      {isExpanded && item.sub_periods && (
        <View style={styles.subList}>
          {item.sub_periods.map((sub, idx) => {
            const now = new Date();
            const subStart = new Date(sub.start);
            const subEnd = new Date(sub.end);
            const isCurrentAntar = now >= subStart && now <= subEnd;
            
            return (
              <View key={idx} style={[styles.subItem, isCurrentAntar && styles.currentSubItem]}>
                <View style={styles.subTimelineLine} />
                <View style={[styles.subDot, { backgroundColor: YOGINI_CONFIG[sub.name]?.color[0] || '#ccc' }]} />
                
                <View style={styles.subContent}>
                  <Text style={[styles.subName, isCurrentAntar && styles.currentSubName]}>{sub.name} ({sub.lord})</Text>
                  <Text style={[styles.subDates, isCurrentAntar && styles.currentSubDates]}>{formatDate(sub.start)} - {formatDate(sub.end)}</Text>
                </View>
                
                <Text style={[styles.subVibe, { color: YOGINI_CONFIG[sub.name]?.color[0] || '#888' }, isCurrentAntar && styles.currentSubVibe]}>
                  {YOGINI_CONFIG[sub.name]?.label}
                </Text>
                
                {isCurrentAntar && (
                  <View style={styles.currentAntarIndicator}>
                    <Text style={styles.currentAntarText}>Current</Text>
                  </View>
                )}
              </View>
            );
          })}
        </View>
      )}
    </View>
  );
};

// --- MAIN COMPONENT ---

export default function YoginiDashaTab({ data }) {
  // console.log('YoginiDashaTab received data:', JSON.stringify(data, null, 2));
  
  // Find current period index (safe with optional chaining)
  const currentIndex = useMemo(() => {
    if (!data?.timeline || !Array.isArray(data.timeline)) {
      console.log('No timeline in data:', data);
      return -1;
    }
    return data.timeline.findIndex(item => 
      item.name === data?.current?.mahadasha?.name && 
      item.start === data?.current?.mahadasha?.start && 
      item.end === data?.current?.mahadasha?.end
    );
  }, [data]);
  
  const [expandedId, setExpandedId] = useState(null);
  
  // Auto-expand current period on mount
  useEffect(() => {
    if (currentIndex >= 0 && expandedId === null) {
      console.log('Setting expandedId to:', currentIndex);
      console.log('Current period has sub_periods:', !!data?.timeline?.[currentIndex]?.sub_periods);
      setExpandedId(currentIndex);
    }
  }, [currentIndex, data, expandedId]);

  if (!data) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>Loading Yogini Dasha data...</Text>
      </View>
    );
  }

  // Check if data has the expected structure
  if (!data?.timeline || !Array.isArray(data.timeline) || !data?.current) {
    console.log('Data missing expected structure. Available keys:', Object.keys(data || {}));
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>Data structure error. Check console for details.</Text>
        <Text style={styles.loadingText}>Available keys: {Object.keys(data || {}).join(', ')}</Text>
      </View>
    );
  }

  const handlePress = (name) => {
    setExpandedId(expandedId === name ? null : name);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }} showsVerticalScrollIndicator={false}>
      
      {/* 1. HERO SECTION: Current Context */}
      <View style={styles.heroContainer}>
        <LinearGradient
          colors={['#ffffff', '#f8f9fa']}
          style={styles.heroCard}
        >
          <View style={styles.heroHeader}>
            <Text style={styles.heroTitle}>Current Yogini Phase</Text>
            <TouchableOpacity>
              <Ionicons name="information-circle-outline" size={22} color="#666" />
            </TouchableOpacity>
          </View>

          <View style={styles.activeRow}>
            <View>
              <Text style={styles.label}>Mahadasha</Text>
              <Text style={styles.activeValue}>{data?.current?.mahadasha?.name || 'N/A'}</Text>
              <Text style={styles.activeLord}>{YOGINI_CONFIG[data?.current?.mahadasha?.name]?.label || 'Unknown'}</Text>
            </View>
            
            <View style={styles.arrowContainer}>
              <Ionicons name="chevron-forward" size={20} color="#ccc" />
            </View>

            <View>
              <Text style={[styles.label, { textAlign: 'right' }]}>Antardasha</Text>
              <Text style={[styles.activeValue, { textAlign: 'right', color: '#8E2DE2' }]}>
                {data?.current?.antardasha?.name || 'N/A'}
              </Text>
              <Text style={[styles.activeLord, { textAlign: 'right' }]}>
                {YOGINI_CONFIG[data?.current?.antardasha?.name]?.label || 'Unknown'}
              </Text>
            </View>
          </View>

          <DashaProgress percentage={data?.current?.progress || 0} />
          
          <View style={styles.dateRange}>
            <Text style={styles.dateLabel}>Ends: {formatDate(data?.current?.antardasha?.end)}</Text>
            <Text style={styles.remainingText}>
               Critical Timing
            </Text>
          </View>
        </LinearGradient>
      </View>

      {/* 2. TAB CONTROLS (Mocking your existing style) */}
      <View style={styles.tabsContainer}>
        <TouchableOpacity style={styles.activeTab}>
          <Text style={styles.activeTabText}>Periods</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.inactiveTab}>
          <Text style={styles.inactiveTabText}>Analysis</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.inactiveTab}>
          <Text style={styles.inactiveTabText}>Remedies</Text>
        </TouchableOpacity>
      </View>

      {/* 3. TIMELINE LIST */}
      <Text style={styles.sectionTitle}>Yogini Cycle (36 Years)</Text>
      
      <View style={styles.listContainer}>
        {data.timeline.map((item, index) => {
          const isCurrent = item.name === data?.current?.mahadasha?.name && 
                           item.start === data?.current?.mahadasha?.start && 
                           item.end === data?.current?.mahadasha?.end;
          const isExpanded = expandedId === index;
          
          if (isCurrent) {
            // console.log(`Current period at index ${index}: expanded=${isExpanded}, has sub_periods=${!!item.sub_periods}`);
          }
          
          return (
            <YoginiCard 
              key={index} 
              item={item} 
              isCurrent={isCurrent}
              isExpanded={isExpanded}
              onPress={() => handlePress(index)}
              currentAntardasha={data?.current?.antardasha}
            />
          );
        })}
      </View>

    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA', // Soft off-white background
  },
  heroContainer: {
    padding: 20,
    paddingBottom: 10,
  },
  heroCard: {
    borderRadius: 20,
    padding: 20,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#eee',
    shadowColor: '#8E2DE2',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
  heroHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  heroTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#333',
  },
  activeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  label: {
    fontSize: 12,
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 4,
  },
  activeValue: {
    fontSize: 24,
    fontWeight: '800',
    color: '#1a1a1a',
  },
  activeLord: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginTop: 2,
  },
  arrowContainer: {
    marginHorizontal: 8,
  },
  progressContainer: {
    height: 24,
    backgroundColor: '#f0f0f0',
    borderRadius: 12,
    overflow: 'hidden',
    position: 'relative',
    justifyContent: 'center',
  },
  track: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#f3f3f3',
  },
  fill: {
    height: '100%',
    borderRadius: 12,
  },
  progressText: {
    position: 'absolute',
    width: '100%',
    textAlign: 'center',
    fontSize: 11,
    fontWeight: '700',
    color: '#fff',
    textShadowColor: 'rgba(0,0,0,0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  dateRange: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  dateLabel: {
    fontSize: 13,
    color: '#666',
    fontWeight: '500',
  },
  remainingText: {
    fontSize: 13,
    color: '#8E2DE2',
    fontWeight: '700',
  },
  
  // Tabs
  tabsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
    gap: 12,
  },
  activeTab: {
    backgroundColor: '#8E2DE2',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 20,
  },
  activeTabText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 14,
  },
  inactiveTab: {
    backgroundColor: '#fff',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#eee',
  },
  inactiveTabText: {
    color: '#666',
    fontWeight: '600',
    fontSize: 14,
  },

  // List
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#333',
    marginLeft: 20,
    marginBottom: 12,
  },
  listContainer: {
    paddingHorizontal: 20,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#f0f0f0',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  activeCard: {
    borderColor: '#8E2DE2',
    borderWidth: 1.5,
  },
  cardHeader: {
    height: 4,
    width: '100%',
  },
  cardContent: {
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconBox: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  yoginiName: {
    fontSize: 17,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  yoginiLord: {
    fontSize: 13,
    color: '#888',
    marginTop: 2,
  },
  cardRight: {
    alignItems: 'flex-end',
  },
  vibeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    marginBottom: 6,
  },
  vibeText: {
    fontSize: 11,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  dateText: {
    fontSize: 12,
    color: '#999',
    fontWeight: '500',
  },
  currentIndicator: {
    backgroundColor: '#f8f0ff',
    paddingVertical: 4,
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  currentText: {
    fontSize: 11,
    color: '#8E2DE2',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },

  // Sub List
  subList: {
    backgroundColor: '#fafafa',
    marginTop: -16, // Pull up to connect with card
    marginBottom: 16,
    marginHorizontal: 10,
    borderBottomLeftRadius: 16,
    borderBottomRightRadius: 16,
    padding: 16,
    paddingTop: 24,
  },
  subItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    minHeight: 40,
    paddingHorizontal: 8,
    paddingVertical: 8,
    borderRadius: 8,
  },
  currentSubItem: {
    backgroundColor: '#f8f0ff',
    borderWidth: 1,
    borderColor: '#8E2DE2',
  },
  subTimelineLine: {
    position: 'absolute',
    left: 15,
    top: 0,
    bottom: -16, // Connect to next
    width: 2,
    backgroundColor: '#eee',
    zIndex: -1,
  },
  subDot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 3,
    borderColor: '#fff',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 2,
    marginRight: 12,
  },
  subContent: {
    flex: 1,
  },
  subName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  currentSubName: {
    color: '#8E2DE2',
    fontWeight: '700',
  },
  subDates: {
    fontSize: 11,
    color: '#999',
  },
  currentSubDates: {
    color: '#8E2DE2',
    fontWeight: '600',
  },
  subVibe: {
    fontSize: 12,
    fontWeight: '600',
  },
  currentSubVibe: {
    fontWeight: '700',
  },
  currentAntarIndicator: {
    backgroundColor: '#8E2DE2',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    marginLeft: 8,
  },
  currentAntarText: {
    fontSize: 9,
    color: '#fff',
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 40,
  },
});
