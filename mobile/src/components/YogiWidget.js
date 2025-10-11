import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function YogiWidget() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>🧘 Yogi Points</Text>
      <View style={styles.content}>
        <View style={styles.yogiItem}>
          <Text style={styles.yogiLabel}>Yogi Planet:</Text>
          <Text style={styles.yogiValue}>Jupiter</Text>
        </View>
        <View style={styles.yogiItem}>
          <Text style={styles.yogiLabel}>Avayogi Planet:</Text>
          <Text style={styles.yogiValue}>Saturn</Text>
        </View>
        <View style={styles.yogiItem}>
          <Text style={styles.yogiLabel}>Dagdha Rashi:</Text>
          <Text style={styles.yogiValue}>Virgo</Text>
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
    marginBottom: 15,
  },
  content: {
    gap: 10,
  },
  yogiItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  yogiLabel: {
    fontSize: 14,
    color: '#666',
  },
  yogiValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
});