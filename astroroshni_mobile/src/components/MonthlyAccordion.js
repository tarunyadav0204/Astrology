import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, LayoutAnimation } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';

export default function MonthlyAccordion({ data, onChatPress }) {
  const [expanded, setExpanded] = useState(false);

  const toggleExpand = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpanded(!expanded);
  };

  // Get top focus tags
  const tags = data.focus_areas ? data.focus_areas.slice(0, 3) : [];

  return (
    <View style={styles.card}>
      {/* Header (Always Visible) */}
      <TouchableOpacity onPress={toggleExpand} style={styles.header} activeOpacity={0.7}>
        <View style={styles.leftCol}>
          <Text style={styles.monthName}>{data.month}</Text>
        </View>
        
        <View style={styles.rightCol}>
          {!expanded && (
            <View style={styles.tagContainer}>
              {tags.map((tag, i) => (
                <View key={i} style={styles.miniTag}>
                  <Text style={styles.miniTagText}>{tag}</Text>
                </View>
              ))}
            </View>
          )}
          <Ionicons 
            name={expanded ? "chevron-up" : "chevron-down"} 
            size={20} 
            color="#666" 
          />
        </View>
      </TouchableOpacity>

      {/* Expanded Content */}
      {expanded && (
        <View style={styles.content}>
          {/* Theme Header */}
          <View style={styles.themeRow}>
            <Text style={styles.label}>FOCUS:</Text>
            <View style={styles.expandedTagContainer}>
              {tags.map((tag, i) => (
                <View key={i} style={styles.fullTag}>
                  <Text style={styles.fullTagText}>{tag}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Events List */}
          <View style={styles.eventsList}>
            {data.events?.map((event, index) => (
              <View key={index} style={styles.eventItem}>
                <View style={[styles.intensityDot, { backgroundColor: getIntensityColor(event.intensity) }]} />
                <View style={{flex: 1}}>
                  <Text style={styles.eventType}>{event.type}</Text>
                  <Text style={styles.eventDesc}>{event.prediction}</Text>
                </View>
              </View>
            ))}
          </View>

          {/* CTA Button */}
          <TouchableOpacity style={styles.chatButton} onPress={onChatPress}>
            <Ionicons name="chatbubbles-outline" size={18} color="white" />
            <Text style={styles.chatButtonText}>Analyze {data.month}</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const getIntensityColor = (intensity) => {
  switch(intensity?.toLowerCase()) {
    case 'high': return '#FF4444';
    case 'medium': return '#FFAA00';
    default: return '#4CAF50';
  }
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1E1E2E',
    borderRadius: 12,
    marginBottom: 10,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#333'
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    height: 60,
  },
  leftCol: { width: 60 },
  monthName: { fontSize: 16, fontWeight: 'bold', color: 'white', textTransform: 'uppercase' },
  rightCol: { flex: 1, flexDirection: 'row', justifyContent: 'flex-end', alignItems: 'center', gap: 10 },
  tagContainer: { flexDirection: 'row', gap: 6 },
  miniTag: { backgroundColor: '#333', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  miniTagText: { color: '#CCC', fontSize: 10, fontWeight: '600' },
  
  content: {
    padding: 16,
    paddingTop: 0,
    borderTopWidth: 1,
    borderTopColor: '#2A2A35'
  },
  themeRow: { flexDirection: 'row', alignItems: 'center', marginTop: 12, marginBottom: 12 },
  label: { color: '#888', fontSize: 11, fontWeight: 'bold', marginRight: 10 },
  expandedTagContainer: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  fullTag: { backgroundColor: '#3D3D5C', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 8 },
  fullTagText: { color: '#B0B0E0', fontSize: 12, fontWeight: '600' },
  
  eventsList: { gap: 12 },
  eventItem: { flexDirection: 'row', gap: 10, alignItems: 'flex-start' },
  intensityDot: { width: 8, height: 8, borderRadius: 4, marginTop: 6 },
  eventType: { color: '#FFF', fontSize: 13, fontWeight: 'bold', marginBottom: 2 },
  eventDesc: { color: '#CCC', fontSize: 13, lineHeight: 18 },
  
  chatButton: {
    flexDirection: 'row',
    backgroundColor: '#6C5DD3',
    padding: 12,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 16,
    gap: 8
  },
  chatButtonText: { color: 'white', fontWeight: 'bold', fontSize: 14 }
});