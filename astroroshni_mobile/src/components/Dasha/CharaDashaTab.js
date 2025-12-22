import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { chartAPI } from '../../services/api';

// Element-based colors for zodiac signs
const SIGN_CONFIG = {
  Aries: { element: 'Fire', color: ['#FF6B6B', '#EE5A6F'], icon: '♈' },
  Taurus: { element: 'Earth', color: ['#8B7355', '#A0826D'], icon: '♉' },
  Gemini: { element: 'Air', color: ['#FFD93D', '#F9CA24'], icon: '♊' },
  Cancer: { element: 'Water', color: ['#6C5CE7', '#A29BFE'], icon: '♋' },
  Leo: { element: 'Fire', color: ['#FD79A8', '#FDCB6E'], icon: '♌' },
  Virgo: { element: 'Earth', color: ['#6AB04C', '#7BED9F'], icon: '♍' },
  Libra: { element: 'Air', color: ['#4ECDC4', '#45B7D1'], icon: '♎' },
  Scorpio: { element: 'Water', color: ['#5F27CD', '#341F97'], icon: '♏' },
  Sagittarius: { element: 'Fire', color: ['#FF9F43', '#EE5A24'], icon: '♐' },
  Capricorn: { element: 'Earth', color: ['#2C3E50', '#34495E'], icon: '♑' },
  Aquarius: { element: 'Air', color: ['#00B894', '#00CEC9'], icon: '♒' },
  Pisces: { element: 'Water', color: ['#A29BFE', '#6C5CE7'], icon: '♓' }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
};

const DashaProgress = ({ percentage }) => (
  <View style={styles.progressContainer}>
    <View style={styles.track} />
    <LinearGradient
      colors={['#FF6B6B', '#EE5A6F']}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 0 }}
      style={[styles.fill, { width: `${percentage}%` }]}
    />
    <Text style={styles.progressText}>{Math.round(percentage)}% Completed</Text>
  </View>
);

const SignCard = ({ item, isCurrent, isExpanded, onPress }) => {
  const config = SIGN_CONFIG[item.sign_name] || SIGN_CONFIG['Aries'];
  
  return (
    <View>
      <TouchableOpacity 
        style={[styles.card, isCurrent && styles.activeCard]} 
        onPress={onPress}
        activeOpacity={0.9}
      >
        <LinearGradient
          colors={config.color}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.cardHeader}
        />

        <View style={styles.cardContent}>
          <View style={styles.cardLeft}>
            <View style={[styles.iconBox, { backgroundColor: config.color[0] + '20' }]}>
              <Text style={[styles.zodiacIcon, { color: config.color[0] }]}>{config.icon}</Text>
            </View>
            <View>
              <Text style={styles.signName}>{item.sign_name}</Text>
              <Text style={styles.signMeta}>{config.element} • {item.duration_years} Years</Text>
            </View>
          </View>

          <View style={styles.cardRight}>
            <View style={[styles.elementBadge, { backgroundColor: config.color[0] + '15' }]}>
              <Text style={[styles.elementText, { color: config.color[0] }]}>{config.element}</Text>
            </View>
            <Text style={styles.dateText}>
              {formatDate(item.start_date)} - {formatDate(item.end_date)}
            </Text>
          </View>
        </View>

        {isCurrent && (
          <View style={styles.currentIndicator}>
            <Text style={styles.currentText}>Currently Running</Text>
          </View>
        )}
      </TouchableOpacity>

      {isExpanded && item.sub_periods && (
        <View style={styles.subList}>
          {item.sub_periods.map((sub, idx) => (
            <View key={idx} style={styles.subItem}>
              <View style={styles.subTimelineLine} />
              <View style={[styles.subDot, { backgroundColor: SIGN_CONFIG[sub.sign]?.color[0] || '#ccc' }]} />
              
              <View style={styles.subContent}>
                <Text style={styles.subName}>{sub.sign}</Text>
                <Text style={styles.subDates}>{formatDate(sub.start_date)} - {formatDate(sub.end_date)}</Text>
              </View>
              
              <Text style={[styles.subElement, { color: SIGN_CONFIG[sub.sign]?.color[0] || '#888' }]}>
                {SIGN_CONFIG[sub.sign]?.element}
              </Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
};

export default function CharaDashaTab({ birthData }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    if (birthData) {
      loadCharaDasha();
    }
  }, [birthData]);

  const loadCharaDasha = async () => {
    setLoading(true);
    try {
      const formattedData = {
        ...birthData,
        date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
        time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'Asia/Kolkata'
      };

      const response = await chartAPI.calculateCharaDasha(formattedData);
      
      if (response.data.status === 'success') {
        setData(response.data);
        
        // Auto-expand current period
        const currentIdx = response.data.periods.findIndex(p => p.is_current);
        if (currentIdx >= 0) {
          setExpandedId(currentIdx);
          // Load sub-periods for current
          loadAntardashas(response.data.periods[currentIdx].sign_id, currentIdx);
        }
      }
    } catch (error) {
      console.error('Chara Dasha error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAntardashas = async (signId, index) => {
    try {
      const formattedData = {
        ...birthData,
        date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
        time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'Asia/Kolkata'
      };

      const response = await chartAPI.calculateCharaAntardasha(formattedData, signId);
      
      if (response.data.status === 'success') {
        setData(prev => {
          const updated = { ...prev };
          updated.periods[index].sub_periods = response.data.antar_periods;
          return updated;
        });
      }
    } catch (error) {
      console.error('Antardasha error:', error);
    }
  };

  const handlePress = (index, signId) => {
    if (expandedId === index) {
      setExpandedId(null);
    } else {
      setExpandedId(index);
      if (!data.periods[index].sub_periods) {
        loadAntardashas(signId, index);
      }
    }
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>Loading Chara Dasha...</Text>
      </View>
    );
  }

  if (!data) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>No data available</Text>
      </View>
    );
  }

  const currentPeriod = data.periods.find(p => p.is_current);
  const progress = currentPeriod ? (() => {
    const start = new Date(currentPeriod.start_date);
    const end = new Date(currentPeriod.end_date);
    const now = new Date();
    const total = end - start;
    const elapsed = now - start;
    return Math.max(0, Math.min(100, (elapsed / total) * 100));
  })() : 0;

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }} showsVerticalScrollIndicator={false}>
      
      {/* Hero Section */}
      <View style={styles.heroContainer}>
        <LinearGradient
          colors={['#ffffff', '#f8f9fa']}
          style={styles.heroCard}
        >
          <View style={styles.heroHeader}>
            <Text style={styles.heroTitle}>Jaimini Chara Dasha</Text>
            <TouchableOpacity>
              <Ionicons name="information-circle-outline" size={22} color="#666" />
            </TouchableOpacity>
          </View>

          {currentPeriod && (
            <>
              <View style={styles.activeRow}>
                <View style={styles.currentSignBox}>
                  <Text style={styles.currentSignIcon}>{SIGN_CONFIG[currentPeriod.sign_name]?.icon}</Text>
                  <Text style={styles.currentSignName}>{currentPeriod.sign_name}</Text>
                  <Text style={styles.currentElement}>{SIGN_CONFIG[currentPeriod.sign_name]?.element} Sign</Text>
                </View>
              </View>

              <DashaProgress percentage={progress} />
              
              <View style={styles.dateRange}>
                <Text style={styles.dateLabel}>Ends: {formatDate(currentPeriod.end_date)}</Text>
                <Text style={styles.remainingText}>
                  {currentPeriod.duration_years} Year Period
                </Text>
              </View>
            </>
          )}
        </LinearGradient>
      </View>

      {/* Timeline List */}
      <Text style={styles.sectionTitle}>12 Sign Periods (120 Years)</Text>
      
      <View style={styles.listContainer}>
        {data.periods.map((item, index) => {
          const isCurrent = item.is_current;
          const isExpanded = expandedId === index;
          
          return (
            <SignCard 
              key={index} 
              item={item} 
              isCurrent={isCurrent}
              isExpanded={isExpanded}
              onPress={() => handlePress(index, item.sign_id)}
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
    backgroundColor: '#F5F7FA',
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
    shadowColor: '#FF6B6B',
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
    alignItems: 'center',
    marginBottom: 20,
  },
  currentSignBox: {
    alignItems: 'center',
  },
  currentSignIcon: {
    fontSize: 48,
    marginBottom: 8,
  },
  currentSignName: {
    fontSize: 28,
    fontWeight: '800',
    color: '#1a1a1a',
  },
  currentElement: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginTop: 4,
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
    color: '#FF6B6B',
    fontWeight: '700',
  },
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
    borderColor: '#FF6B6B',
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
  zodiacIcon: {
    fontSize: 24,
  },
  signName: {
    fontSize: 17,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  signMeta: {
    fontSize: 13,
    color: '#888',
    marginTop: 2,
  },
  cardRight: {
    alignItems: 'flex-end',
  },
  elementBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    marginBottom: 6,
  },
  elementText: {
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
    backgroundColor: '#fff5f5',
    paddingVertical: 4,
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  currentText: {
    fontSize: 11,
    color: '#FF6B6B',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  subList: {
    backgroundColor: '#fafafa',
    marginTop: -16,
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
    height: 40,
  },
  subTimelineLine: {
    position: 'absolute',
    left: 7,
    top: 0,
    bottom: -16,
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
  subDates: {
    fontSize: 11,
    color: '#999',
  },
  subElement: {
    fontSize: 12,
    fontWeight: '600',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 40,
  },
});
