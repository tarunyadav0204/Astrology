import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { COLORS } from '../../utils/constants';

const DateNavigator = ({ date, onDateChange, cosmicTheme = false, resetDate = null }) => {
  const [showDatePicker, setShowDatePicker] = useState(false);

  const adjustDate = (days) => {
    const newDate = new Date(date);
    newDate.setDate(newDate.getDate() + days);
    onDateChange(newDate);
  };

  const handleReset = () => {
    onDateChange(resetDate || new Date());
  };

  return (
    <View style={styles.dateNav}>
      <View style={[
        styles.compactNavRow,
        cosmicTheme ? {
          backgroundColor: 'rgba(0, 0, 0, 0.4)',
          borderWidth: 1,
          borderColor: 'rgba(255, 255, 255, 0.3)',
        } : {
          backgroundColor: COLORS.surface,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.1,
          shadowRadius: 4,
          elevation: 3,
        }
      ]}>
        <View style={styles.navButtonGroup}>
          <TouchableOpacity style={[
            styles.compactNavButton,
            cosmicTheme ? {
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
            } : {
              backgroundColor: COLORS.lightGray,
            }
          ]} onPress={() => adjustDate(-30)}>
            <Text style={[
              styles.compactNavText,
              { color: cosmicTheme ? 'rgba(255, 255, 255, 0.9)' : COLORS.accent }
            ]}>-1M</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[
            styles.compactNavButton,
            cosmicTheme ? {
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
            } : {
              backgroundColor: COLORS.lightGray,
            }
          ]} onPress={() => adjustDate(-7)}>
            <Text style={[
              styles.compactNavText,
              { color: cosmicTheme ? 'rgba(255, 255, 255, 0.9)' : COLORS.accent }
            ]}>-1W</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[
            styles.compactNavButton,
            cosmicTheme ? {
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
            } : {
              backgroundColor: COLORS.lightGray,
            }
          ]} onPress={() => adjustDate(-1)}>
            <Text style={[
              styles.compactNavText,
              { color: cosmicTheme ? 'rgba(255, 255, 255, 0.9)' : COLORS.accent }
            ]}>-1D</Text>
          </TouchableOpacity>
        </View>
        
        <TouchableOpacity style={[
          styles.compactDateButton,
          cosmicTheme ? {
            backgroundColor: 'rgba(255, 107, 53, 0.8)',
          } : {
            backgroundColor: COLORS.accent,
          }
        ]} onPress={handleReset}>
          <Text style={[
            styles.compactDateText,
            { color: COLORS.white }
          ]}>{date.toLocaleDateString('en-US', {month: 'short', day: 'numeric'})}</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={[
          styles.compactCalendarButton,
          cosmicTheme ? {
            backgroundColor: 'rgba(255, 107, 53, 0.8)',
          } : {
            backgroundColor: COLORS.accent,
          }
        ]} onPress={() => setShowDatePicker(true)}>
          <Text style={styles.calendarIcon}>📅</Text>
        </TouchableOpacity>
        
        <View style={styles.navButtonGroup}>
          <TouchableOpacity style={[
            styles.compactNavButton,
            cosmicTheme ? {
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
            } : {
              backgroundColor: COLORS.lightGray,
            }
          ]} onPress={() => adjustDate(1)}>
            <Text style={[
              styles.compactNavText,
              { color: cosmicTheme ? 'rgba(255, 255, 255, 0.9)' : COLORS.accent }
            ]}>+1D</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[
            styles.compactNavButton,
            cosmicTheme ? {
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
            } : {
              backgroundColor: COLORS.lightGray,
            }
          ]} onPress={() => adjustDate(7)}>
            <Text style={[
              styles.compactNavText,
              { color: cosmicTheme ? 'rgba(255, 255, 255, 0.9)' : COLORS.accent }
            ]}>+1W</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[
            styles.compactNavButton,
            cosmicTheme ? {
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
            } : {
              backgroundColor: COLORS.lightGray,
            }
          ]} onPress={() => adjustDate(30)}>
            <Text style={[
              styles.compactNavText,
              { color: cosmicTheme ? 'rgba(255, 255, 255, 0.9)' : COLORS.accent }
            ]}>+1M</Text>
          </TouchableOpacity>
        </View>
      </View>
      
      {showDatePicker && (
        <View style={styles.datePickerOverlay}>
          <TouchableOpacity 
            style={styles.overlayBackground}
            activeOpacity={1}
            onPress={() => setShowDatePicker(false)}
          />
          <View style={styles.datePickerContainer}>
            <DateTimePicker
              value={date}
              mode="date"
              display={Platform.OS === 'ios' ? 'spinner' : 'default'}
              textColor="#ffffff"
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
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  dateNav: {
    marginBottom: 12,
  },
  datePickerOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1000,
    justifyContent: 'center',
    alignItems: 'center',
  },
  overlayBackground: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  datePickerContainer: {
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    borderRadius: 12,
    padding: 16,
    zIndex: 1001,
  },
  compactNavRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: 12,
    padding: 8,
  },
  navButtonGroup: {
    flexDirection: 'row',
    gap: 4,
  },
  compactNavButton: {
    paddingHorizontal: 6,
    paddingVertical: 4,
    borderRadius: 6,
    minWidth: 28,
  },
  compactNavText: {
    fontSize: 9,
    fontWeight: '600',
    textAlign: 'center',
  },
  compactDateButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    minWidth: 80,
    height: 32,
    justifyContent: 'center',
  },
  compactDateText: {
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
  },
  compactCalendarButton: {
    padding: 8,
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
