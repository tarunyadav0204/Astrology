import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

const DateNavigationControls = ({ transitDate, onTransitDateChange, onResetToToday }) => {
  const handleDateChange = (operation, unit) => {
    const newDate = new Date(transitDate);
    
    switch (operation) {
      case 'add':
        switch (unit) {
          case 'day': newDate.setDate(newDate.getDate() + 1); break;
          case 'week': newDate.setDate(newDate.getDate() + 7); break;
          case 'month': newDate.setMonth(newDate.getMonth() + 1); break;
          default: return;
        }
        break;
      case 'sub':
        switch (unit) {
          case 'day': newDate.setDate(newDate.getDate() - 1); break;
          case 'week': newDate.setDate(newDate.getDate() - 7); break;
          case 'month': newDate.setMonth(newDate.getMonth() - 1); break;
          default: return;
        }
        break;
      default:
        return;
    }
    
    onTransitDateChange(newDate);
  };

  return (
    <View style={styles.container}>
      {/* Date Display */}
      <Text style={styles.dateDisplay}>
        {transitDate?.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: '2-digit' })}
      </Text>
      
      {/* Navigation Buttons */}
      <TouchableOpacity onPress={() => handleDateChange('sub', 'month')} style={styles.navButton}>
        <Text style={styles.navButtonText}>‹M</Text>
      </TouchableOpacity>
      
      <TouchableOpacity onPress={() => handleDateChange('sub', 'week')} style={styles.navButton}>
        <Text style={styles.navButtonText}>‹W</Text>
      </TouchableOpacity>
      
      <TouchableOpacity onPress={() => handleDateChange('sub', 'day')} style={styles.navButton}>
        <Text style={styles.navButtonText}>‹D</Text>
      </TouchableOpacity>
      
      <TouchableOpacity onPress={onResetToToday} style={styles.nowButton}>
        <Text style={styles.nowButtonText}>Now</Text>
      </TouchableOpacity>
      
      <TouchableOpacity onPress={() => handleDateChange('add', 'day')} style={styles.navButton}>
        <Text style={styles.navButtonText}>D›</Text>
      </TouchableOpacity>
      
      <TouchableOpacity onPress={() => handleDateChange('add', 'week')} style={styles.navButton}>
        <Text style={styles.navButtonText}>W›</Text>
      </TouchableOpacity>
      
      <TouchableOpacity onPress={() => handleDateChange('add', 'month')} style={styles.navButton}>
        <Text style={styles.navButtonText}>M›</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    padding: 8,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e91e63',
    marginBottom: 4,
    flexWrap: 'wrap',
  },
  dateDisplay: {
    color: '#e91e63',
    fontSize: 12,
    fontWeight: '600',
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: 'white',
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#e91e63',
    minWidth: 80,
    textAlign: 'center',
  },
  navButton: {
    backgroundColor: 'rgba(233, 30, 99, 0.1)',
    borderWidth: 1,
    borderColor: '#e91e63',
    paddingHorizontal: 6,
    paddingVertical: 4,
    borderRadius: 4,
    minWidth: 28,
    alignItems: 'center',
  },
  navButtonText: {
    color: '#e91e63',
    fontSize: 11,
    fontWeight: '600',
  },
  nowButton: {
    backgroundColor: '#e91e63',
    borderWidth: 1,
    borderColor: '#e91e63',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    minWidth: 32,
    alignItems: 'center',
  },
  nowButtonText: {
    color: 'white',
    fontSize: 11,
    fontWeight: '600',
  },
});

export default DateNavigationControls;