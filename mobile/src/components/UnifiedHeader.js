import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

export default function UnifiedHeader({
  currentChart,
  onSelectChart,
  onViewAllCharts,
  onNewChart,
  onLogout,
  user,
  showTransitControls,
  transitDate,
  onTransitDateChange,
  onResetToToday,
  onSettings
}) {
  return (
    <View style={styles.container}>
      <View style={styles.leftSection}>
        <Text style={styles.appTitle}>🔮 AstroGPT</Text>
        {currentChart && (
          <Text style={styles.chartInfo}>
            {currentChart.name} • {currentChart.date}
          </Text>
        )}
      </View>
      
      <View style={styles.rightSection}>
        <TouchableOpacity style={styles.headerButton} onPress={onViewAllCharts}>
          <Text style={styles.headerButtonText}>Charts</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.headerButton} onPress={onNewChart}>
          <Text style={styles.headerButtonText}>New</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.headerButton} onPress={onSettings}>
          <Text style={styles.headerButtonText}>⚙️</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.logoutButton} onPress={onLogout}>
          <Text style={styles.logoutButtonText}>Logout</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#e91e63',
    paddingHorizontal: 15,
    paddingVertical: 12,
  },
  leftSection: {
    flex: 1,
  },
  appTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
  },
  chartInfo: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  rightSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerButton: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 4,
  },
  headerButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  logoutButton: {
    backgroundColor: 'rgba(255,255,255,0.3)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 4,
  },
  logoutButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
});