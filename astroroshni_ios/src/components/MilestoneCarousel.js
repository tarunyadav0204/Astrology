import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

const { width } = Dimensions.get('window');
const CARD_WIDTH = width * 0.75;

export default function MilestoneCarousel({ data, onPress }) {
  if (!data || data.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>No major cosmic milestones detected for this year.</Text>
        <Text style={styles.emptySubText}>Check the Monthly Guide below for details.</Text>
      </View>
    );
  }

  return (
    <ScrollView 
      horizontal 
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={{ paddingLeft: 20, paddingRight: 10 }}
      decelerationRate="fast"
      snapToInterval={CARD_WIDTH + 15}
    >
      {data.map((item, index) => (
        <TouchableOpacity 
          key={index} 
          activeOpacity={0.9} 
          onPress={() => onPress(item)}
        >
          <LinearGradient
            colors={['#FFD700', '#FFA500']} // Gold Gradient
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.card}
          >
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{item.significance || "HIGH IMPACT"}</Text>
            </View>
            
            <Text style={styles.title} numberOfLines={2}>{item.label || item.title}</Text>
            <Text style={styles.date}>{item.start_date} - {item.end_date}</Text>
            
            <View style={styles.footer}>
              <Text style={styles.tapText}>Tap to Analyze</Text>
            </View>
          </LinearGradient>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  card: {
    width: CARD_WIDTH,
    height: 140,
    marginRight: 15,
    borderRadius: 16,
    padding: 16,
    justifyContent: 'space-between'
  },
  badge: {
    backgroundColor: 'rgba(0,0,0,0.2)',
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginBottom: 8
  },
  badgeText: { color: 'black', fontSize: 10, fontWeight: '800', textTransform: 'uppercase' },
  title: { fontSize: 18, fontWeight: 'bold', color: 'black', marginBottom: 4 },
  date: { fontSize: 13, color: '#333', fontWeight: '600' },
  footer: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: 10 },
  tapText: { fontSize: 12, fontWeight: '700', color: 'black', opacity: 0.7 },
  
  emptyContainer: { paddingHorizontal: 20, alignItems: 'center', opacity: 0.7 },
  emptyText: { color: 'white', fontSize: 14 },
  emptySubText: { color: '#888', fontSize: 12 }
});