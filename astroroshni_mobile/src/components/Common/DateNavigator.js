import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { COLORS } from '../../utils/constants';

const DateNavigator = ({ date, onDateChange }) => {
  const [showDatePicker, setShowDatePicker] = useState(false);

  const adjustDate = (days) => {
    const newDate = new Date(date);
    newDate.setDate(newDate.getDate() + days);
    onDateChange(newDate);
  };

  return (
    <View style={styles.dateNav}>
      <View style={styles.compactNavRow}>
        <View style={styles.navButtonGroup}>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(-30)}>
            <Text style={styles.compactNavText}>-1M</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(-7)}>
            <Text style={styles.compactNavText}>-1W</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(-1)}>
            <Text style={styles.compactNavText}>-1D</Text>
          </TouchableOpacity>
        </View>
        
        <TouchableOpacity style={styles.compactDateButton} onPress={() => onDateChange(new Date())}>
          <Text style={styles.compactDateText}>{date.toLocaleDateString('en-US', {month: 'short', day: 'numeric'})}</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.compactCalendarButton} onPress={() => setShowDatePicker(true)}>
          <Text style={styles.calendarIcon}>📅</Text>
        </TouchableOpacity>
        
        <View style={styles.navButtonGroup}>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(1)}>
            <Text style={styles.compactNavText}>+1D</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(7)}>
            <Text style={styles.compactNavText}>+1W</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(30)}>
            <Text style={styles.compactNavText}>+1M</Text>
          </TouchableOpacity>
        </View>
      </View>
      
      {showDatePicker && (
        <View>
          <DateTimePicker
            value={date}
            mode="date"
            display={Platform.OS === 'ios' ? 'spinner' : 'default'}
            onChange={(event, selectedDate) => {
              if (Platform.OS === 'android') {
                setShowDatePicker(false);
                if (selectedDate) {
                  onDateChange(selectedDate);
                }
              } else {
                if (selectedDate) {
                  onDateChange(selectedDate);
                }
              }
            }}
          />
          {Platform.OS === 'ios' && (
            <TouchableOpacity 
              style={styles.doneButton} 
              onPress={() => setShowDatePicker(false)}
            >
              <Text style={styles.doneButtonText}>Done</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  dateNav: {
    marginBottom: 12,
  },
  compactNavRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  navButtonGroup: {
    flexDirection: 'row',
    gap: 4,
  },
  compactNavButton: {
    paddingHorizontal: 6,
    paddingVertical: 4,
    backgroundColor: COLORS.lightGray,
    borderRadius: 6,
    minWidth: 28,
  },
  compactNavText: {
    color: COLORS.accent,
    fontSize: 9,
    fontWeight: '600',
    textAlign: 'center',
  },
  compactDateButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: COLORS.accent,
    borderRadius: 8,
    minWidth: 80,
    height: 32,
    justifyContent: 'center',
  },
  compactDateText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
  },
  compactCalendarButton: {
    padding: 8,
    backgroundColor: COLORS.accent,
    borderRadius: 8,
    height: 32,
    width: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },
  calendarIcon: {
    fontSize: 16,
  },
  doneButton: {
    backgroundColor: COLORS.accent,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    alignSelf: 'center',
    marginTop: 10,
  },
  doneButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
});

export default DateNavigator;
