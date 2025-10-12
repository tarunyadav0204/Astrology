import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';

export default function TransitDateControls({
  transitDate,
  onTransitDateChange,
  onResetToToday
}) {
  const [showDatePicker, setShowDatePicker] = useState(false);

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

  const onDateChange = (event, selectedDate) => {
    const currentDate = selectedDate || transitDate;
    setShowDatePicker(Platform.OS === 'ios');
    onTransitDateChange(currentDate);
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity style={styles.button} onPress={() => changeDate(-1)}>
        <Text style={styles.buttonText}>◀</Text>
      </TouchableOpacity>
      
      <TouchableOpacity 
        style={styles.dateContainer} 
        onPress={() => setShowDatePicker(true)}
      >
        <Text style={styles.dateText}>{formatDate(transitDate)}</Text>
        <Text style={styles.tapHint}>📅 Tap to select date</Text>
      </TouchableOpacity>
      
      <TouchableOpacity style={styles.button} onPress={() => changeDate(1)}>
        <Text style={styles.buttonText}>▶</Text>
      </TouchableOpacity>
      
      <TouchableOpacity style={styles.todayButton} onPress={onResetToToday}>
        <Text style={styles.todayButtonText}>Today</Text>
      </TouchableOpacity>
      
      {showDatePicker && (
        <DateTimePicker
          testID="dateTimePicker"
          value={transitDate}
          mode="date"
          is24Hour={true}
          display="default"
          onChange={onDateChange}
        />
      )}
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
    padding: 8,
    backgroundColor: 'rgba(233, 30, 99, 0.1)',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e91e63',
  },
  dateText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  tapHint: {
    fontSize: 10,
    color: '#666',
    marginTop: 2,
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