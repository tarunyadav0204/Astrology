import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

export default function TransitDateControls({
  transitDate,
  onTransitDateChange,
  onResetToToday
}) {
  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const changeDate = (days) => {
    const newDate = new Date(transitDate);
    newDate.setDate(newDate.getDate() + days);
    onTransitDateChange(newDate);
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity style={styles.button} onPress={() => changeDate(-1)}>
        <Text style={styles.buttonText}>◀</Text>
      </TouchableOpacity>
      
      <View style={styles.dateContainer}>
        <Text style={styles.dateText}>{formatDate(transitDate)}</Text>
      </View>
      
      <TouchableOpacity style={styles.button} onPress={() => changeDate(1)}>
        <Text style={styles.buttonText}>▶</Text>
      </TouchableOpacity>
      
      <TouchableOpacity style={styles.todayButton} onPress={onResetToToday}>
        <Text style={styles.todayButtonText}>Today</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'white',
    padding: 10,
    margin: 10,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  button: {
    backgroundColor: '#e91e63',
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 10,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  dateContainer: {
    flex: 1,
    alignItems: 'center',
  },
  dateText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  todayButton: {
    backgroundColor: '#ff6f00',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 4,
    marginLeft: 10,
  },
  todayButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
});