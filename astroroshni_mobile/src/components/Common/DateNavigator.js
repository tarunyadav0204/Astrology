import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform, Modal } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { COLORS } from '../../utils/constants';

const DateNavigator = ({ date, onDateChange, cosmicTheme = false, resetDate = null }) => {
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [tempDate, setTempDate] = useState(date);

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
            ]}>-M</Text>
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
            ]}>-W</Text>
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
            ]}>-D</Text>
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
          ]}>{date.toLocaleDateString('en-US', {month: 'short', day: 'numeric', year: '2-digit'})}</Text>
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
            ]}>+D</Text>
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
            ]}>+W</Text>
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
            ]}>+M</Text>
          </TouchableOpacity>
        </View>
      </View>
      
      {Platform.OS === 'ios' ? (
        <Modal
          visible={showDatePicker}
          transparent={true}
          animationType="fade"
          onRequestClose={() => setShowDatePicker(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.datePickerContainer}>
              <DateTimePicker
                value={tempDate}
                mode="date"
                display="spinner"
                onChange={(event, selectedDate) => {
                  if (selectedDate) {
                    setTempDate(selectedDate);
                  }
                }}
              />
              <TouchableOpacity 
                style={styles.doneButton} 
                onPress={() => {
                  onDateChange(tempDate);
                  setShowDatePicker(false);
                }}
              >
                <Text style={styles.doneButtonText}>Done</Text>
              </TouchableOpacity>
            </View>
            <TouchableOpacity 
              style={styles.closeOverlay}
              onPress={() => {
                setTempDate(date);
                setShowDatePicker(false);
              }}
            />
          </View>
        </Modal>
      ) : (
        showDatePicker && (
          <DateTimePicker
            value={tempDate}
            mode="date"
            display="default"
            onChange={(event, selectedDate) => {
              setShowDatePicker(false);
              if (selectedDate) {
                onDateChange(selectedDate);
              }
            }}
          />
        )
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  dateNav: {
    marginBottom: 12,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: -1,
  },
  datePickerContainer: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    paddingBottom: 20,
    minHeight: 250,
    minWidth: 300,
    zIndex: 1,
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
    paddingHorizontal: 8,
    paddingVertical: 8,
    borderRadius: 8,
    minWidth: 32,
  },
  compactNavText: {
    fontSize: 11,
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
