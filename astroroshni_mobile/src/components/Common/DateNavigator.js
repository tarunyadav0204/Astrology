import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform, Modal } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { COLORS } from '../../utils/constants';
import WebDatePickerModal from './WebDatePickerModal';

/**
 * Compact date stepper used by ChartScreen transit and KP significators.
 * ChartView layout (single row) by default.
 * With includeTime: same date row + a second centered time row (±H) so it never wraps awkwardly.
 */
const DateNavigator = ({
  date,
  onDateChange,
  cosmicTheme = false,
  resetDate = null,
  includeTime = false,
}) => {
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [tempDate, setTempDate] = useState(date);

  const normalizeOutgoing = (value) => {
    const next = new Date(value);
    if (!includeTime) {
      next.setHours(12, 0, 0, 0);
    }
    return next;
  };

  const openDatePicker = () => {
    setTempDate(date instanceof Date ? date : new Date());
    setShowDatePicker(true);
  };

  const openTimePicker = () => {
    setTempDate(date instanceof Date ? date : new Date());
    setShowTimePicker(true);
  };

  const adjustDate = (amount, unit = 'day') => {
    const newDate = new Date(date);
    if (unit === 'hour') {
      newDate.setHours(newDate.getHours() + amount);
    } else {
      if (!includeTime) {
        newDate.setHours(12, 0, 0, 0);
      }
      newDate.setDate(newDate.getDate() + amount);
    }
    onDateChange(normalizeOutgoing(newDate));
  };

  const handleReset = () => {
    const next = resetDate ? new Date(resetDate) : new Date();
    onDateChange(normalizeOutgoing(next));
  };

  const safeDate = date instanceof Date && !Number.isNaN(date.getTime()) ? date : new Date();
  const dateOnlyLabel = safeDate.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: '2-digit',
  });
  const timeLabel = safeDate.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });

  const shellStyle = cosmicTheme
    ? {
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.3)',
      }
    : {
        backgroundColor: COLORS.surface,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
      };

  const ghostBtn = cosmicTheme
    ? { backgroundColor: 'rgba(255, 255, 255, 0.15)' }
    : { backgroundColor: COLORS.lightGray };
  const accentBtn = cosmicTheme
    ? { backgroundColor: 'rgba(255, 107, 53, 0.8)' }
    : { backgroundColor: COLORS.accent };
  const ghostText = { color: cosmicTheme ? 'rgba(255, 255, 255, 0.9)' : COLORS.accent };

  const renderPicker = (visible, setVisible, mode) => {
    if (Platform.OS === 'web') {
      if (mode !== 'date') return null;
      return (
        <WebDatePickerModal
          visible={visible}
          value={tempDate}
          title="Select date"
          onClose={() => setVisible(false)}
          onChange={(next) => {
            if (includeTime && next instanceof Date) {
              const merged = new Date(next);
              merged.setHours(safeDate.getHours(), safeDate.getMinutes(), 0, 0);
              onDateChange(merged);
            } else {
              onDateChange(normalizeOutgoing(next));
            }
          }}
        />
      );
    }

    if (Platform.OS === 'ios') {
      return (
        <Modal
          visible={visible}
          transparent
          animationType="fade"
          onRequestClose={() => setVisible(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.datePickerContainer}>
              <DateTimePicker
                value={tempDate}
                mode={mode}
                display="spinner"
                onChange={(_, selectedDate) => {
                  if (selectedDate) setTempDate(selectedDate);
                }}
              />
              <TouchableOpacity
                style={styles.doneButton}
                onPress={() => {
                  if (mode === 'time' && includeTime) {
                    const merged = new Date(safeDate);
                    merged.setHours(tempDate.getHours(), tempDate.getMinutes(), 0, 0);
                    onDateChange(merged);
                  } else if (includeTime && mode === 'date') {
                    const merged = new Date(tempDate);
                    merged.setHours(safeDate.getHours(), safeDate.getMinutes(), 0, 0);
                    onDateChange(merged);
                  } else {
                    onDateChange(normalizeOutgoing(tempDate));
                  }
                  setVisible(false);
                }}
              >
                <Text style={styles.doneButtonText}>Done</Text>
              </TouchableOpacity>
            </View>
            <TouchableOpacity
              style={styles.closeOverlay}
              onPress={() => {
                setTempDate(date);
                setVisible(false);
              }}
            />
          </View>
        </Modal>
      );
    }

    return visible ? (
      <DateTimePicker
        value={tempDate}
        mode={mode}
        display="default"
        onChange={(event, selectedDate) => {
          setVisible(false);
          if (!selectedDate) return;
          if (mode === 'time' && includeTime) {
            const merged = new Date(safeDate);
            merged.setHours(selectedDate.getHours(), selectedDate.getMinutes(), 0, 0);
            onDateChange(merged);
          } else if (includeTime && mode === 'date') {
            const merged = new Date(selectedDate);
            merged.setHours(safeDate.getHours(), safeDate.getMinutes(), 0, 0);
            onDateChange(merged);
          } else {
            onDateChange(normalizeOutgoing(selectedDate));
          }
        }}
      />
    ) : null;
  };

  return (
    <View style={styles.dateNav}>
      <View style={[styles.navShell, shellStyle]}>
        <View style={styles.compactNavRow}>
          <View style={styles.navButtonGroup}>
            <TouchableOpacity style={[styles.compactNavButton, ghostBtn]} onPress={() => adjustDate(-30)} hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }}>
              <Text style={[styles.compactNavText, ghostText]}>-M</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.compactNavButton, ghostBtn]} onPress={() => adjustDate(-7)} hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }}>
              <Text style={[styles.compactNavText, ghostText]}>-W</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.compactNavButton, ghostBtn]} onPress={() => adjustDate(-1)} hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }}>
              <Text style={[styles.compactNavText, ghostText]}>-D</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[styles.compactDateButton, accentBtn]}
            onPress={Platform.OS === 'web' ? openDatePicker : handleReset}
            onLongPress={handleReset}
            hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }}
          >
            <Text style={[styles.compactDateText, { color: COLORS.white }]}>{dateOnlyLabel}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.compactCalendarButton, accentBtn]}
            onPress={openDatePicker}
            hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }}
          >
            <Text style={styles.calendarIcon}>📅</Text>
          </TouchableOpacity>

          <View style={styles.navButtonGroup}>
            <TouchableOpacity style={[styles.compactNavButton, ghostBtn]} onPress={() => adjustDate(1)} hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }}>
              <Text style={[styles.compactNavText, ghostText]}>+D</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.compactNavButton, ghostBtn]} onPress={() => adjustDate(7)} hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }}>
              <Text style={[styles.compactNavText, ghostText]}>+W</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.compactNavButton, ghostBtn]} onPress={() => adjustDate(30)} hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }}>
              <Text style={[styles.compactNavText, ghostText]}>+M</Text>
            </TouchableOpacity>
          </View>
        </View>

        {includeTime ? (
          <View style={[
            styles.timeRow,
            { borderTopColor: cosmicTheme ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)' },
          ]}>
            <TouchableOpacity style={[styles.compactNavButton, ghostBtn]} onPress={() => adjustDate(-1, 'hour')} hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }}>
              <Text style={[styles.compactNavText, ghostText]}>-H</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.timeChip, accentBtn]} onPress={Platform.OS === 'web' ? undefined : openTimePicker} onLongPress={handleReset}>
              <Text style={[styles.compactDateText, { color: COLORS.white }]}>{timeLabel}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.compactNavButton, ghostBtn]} onPress={() => adjustDate(1, 'hour')} hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }}>
              <Text style={[styles.compactNavText, ghostText]}>+H</Text>
            </TouchableOpacity>
          </View>
        ) : null}
      </View>

      {renderPicker(showDatePicker, setShowDatePicker, 'date')}
      {includeTime && Platform.OS !== 'web' ? renderPicker(showTimePicker, setShowTimePicker, 'time') : null}
    </View>
  );
};

const styles = StyleSheet.create({
  dateNav: {
    marginBottom: 12,
    alignSelf: 'stretch',
  },
  navShell: {
    borderRadius: 12,
    paddingVertical: 6,
    paddingHorizontal: 8,
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
    justifyContent: 'space-evenly',
  },
  timeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255, 255, 255, 0.15)',
  },
  navButtonGroup: {
    flexDirection: 'row',
    gap: 6,
  },
  compactNavButton: {
    paddingHorizontal: 6,
    paddingVertical: 6,
    borderRadius: 8,
    minWidth: 32,
  },
  compactNavText: {
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'center',
  },
  compactDateButton: {
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 8,
    minWidth: 75,
    height: 32,
    justifyContent: 'center',
  },
  timeChip: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 8,
    minWidth: 96,
    height: 32,
    justifyContent: 'center',
  },
  compactDateText: {
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
  },
  compactCalendarButton: {
    padding: 6,
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
