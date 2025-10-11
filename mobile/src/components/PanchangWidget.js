import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function PanchangWidget({ transitDate }) {
  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>📅 Panchang</Text>
      <Text style={styles.date}>{formatDate(transitDate)}</Text>
      
      <View style={styles.content}>
        <View style={styles.panchangItem}>
          <Text style={styles.panchangLabel}>Tithi:</Text>
          <Text style={styles.panchangValue}>Shukla Panchami</Text>
        </View>
        <View style={styles.panchangItem}>
          <Text style={styles.panchangLabel}>Vara:</Text>
          <Text style={styles.panchangValue}>Monday</Text>
        </View>
        <View style={styles.panchangItem}>
          <Text style={styles.panchangLabel}>Nakshatra:</Text>
          <Text style={styles.panchangValue}>Rohini</Text>
        </View>
        <View style={styles.panchangItem}>
          <Text style={styles.panchangLabel}>Yoga:</Text>
          <Text style={styles.panchangValue}>Siddha</Text>
        </View>
        <View style={styles.panchangItem}>
          <Text style={styles.panchangLabel}>Karana:</Text>
          <Text style={styles.panchangValue}>Bava</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'white',
    borderRadius: 8,
    margin: 10,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#e91e63',
    textAlign: 'center',
    marginBottom: 10,
  },
  date: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginBottom: 15,
  },
  content: {
    gap: 8,
  },
  panchangItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  panchangLabel: {
    fontSize: 14,
    color: '#666',
  },
  panchangValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
});