import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform, Modal, ActivityIndicator } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import WebDatePickerModal from './WebDatePickerModal';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';

const INTL_LOCALES = {
  english: 'en-IN',
  hindi: 'hi-IN',
  es: 'es-ES',
  french: 'fr-FR',
  german: 'de-DE',
  russian: 'ru-RU',
  chinese: 'zh-CN',
  mandarin: 'zh-CN',
  tamil: 'ta-IN',
  telugu: 'te-IN',
  gujarati: 'gu-IN',
  marathi: 'mr-IN',
};

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
  loading = false,
}) => {
  const { colors } = useTheme();
  const { t, i18n } = useTranslation();
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
  const intlLocale = INTL_LOCALES[i18n.resolvedLanguage] || INTL_LOCALES[i18n.language] || 'en-IN';
  const dateOnlyLabel = safeDate.toLocaleDateString(intlLocale, {
    month: 'short',
    day: 'numeric',
    year: '2-digit',
  });
  const timeLabel = safeDate.toLocaleTimeString(intlLocale, {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });

  const shellStyle = { backgroundColor: colors.surface, borderColor: colors.cardBorder };
  const ghostBtn = { backgroundColor: colors.surfaceMuted };
  const accentBtn = { backgroundColor: colors.primary };
  const ghostText = { color: colors.textSecondary };

  const renderPicker = (visible, setVisible, mode) => {
    if (Platform.OS === 'web') {
      if (mode !== 'date') return null;
      return (
        <WebDatePickerModal
          visible={visible}
          value={tempDate}
          title={t('premiumUi.common.selectDate')}
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
            <View style={[styles.datePickerContainer, { backgroundColor: colors.surfaceRaised || colors.surface, borderColor: colors.cardBorder }]}>
              <DateTimePicker
                value={tempDate}
                mode={mode}
                display="spinner"
                onChange={(_, selectedDate) => {
                  if (selectedDate) setTempDate(selectedDate);
                }}
              />
              <TouchableOpacity
                style={[styles.doneButton, { backgroundColor: colors.primary }]}
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
                <Text style={[styles.doneButtonText, { color: colors.onPrimary }]}>{t('premiumUi.common.done')}</Text>
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
          <TouchableOpacity style={[styles.dayStepButton, ghostBtn]} onPress={() => adjustDate(-1)} hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }} accessibilityLabel={t('premiumUi.common.previousDay')}>
            <Ionicons name="chevron-back" size={18} color={colors.text} />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.compactDateButton, { backgroundColor: colors.surfaceRaised || colors.surface, borderColor: colors.cardBorder }]}
            onPress={openDatePicker}
            hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }}
            accessibilityState={{ busy: loading }}
          >
            {loading ? (
              <ActivityIndicator size="small" color={colors.primary} />
            ) : (
              <Ionicons name="calendar-clear-outline" size={15} color={colors.primary} />
            )}
            <Text style={[styles.compactDateText, { color: colors.text }]}>{dateOnlyLabel}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.dayStepButton, ghostBtn]} onPress={() => adjustDate(1)} hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }} accessibilityLabel={t('premiumUi.common.nextDay')}>
            <Ionicons name="chevron-forward" size={18} color={colors.text} />
          </TouchableOpacity>
        </View>

        <View style={[styles.rangeRow, { borderTopColor: colors.cardBorder }]}>
          <TouchableOpacity style={styles.rangeButton} onPress={() => adjustDate(-30)}><Text style={[styles.rangeButtonText, ghostText]}>{t('premiumUi.common.minusMonth')}</Text></TouchableOpacity>
          <TouchableOpacity style={styles.rangeButton} onPress={() => adjustDate(-7)}><Text style={[styles.rangeButtonText, ghostText]}>{t('premiumUi.common.minusWeek')}</Text></TouchableOpacity>
          <TouchableOpacity style={[styles.todayButton, { backgroundColor: colors.accentSoft }]} onPress={handleReset}><Text style={[styles.todayButtonText, { color: colors.onAccent }]}>{t('premiumUi.common.today')}</Text></TouchableOpacity>
          <TouchableOpacity style={styles.rangeButton} onPress={() => adjustDate(7)}><Text style={[styles.rangeButtonText, ghostText]}>{t('premiumUi.common.plusWeek')}</Text></TouchableOpacity>
          <TouchableOpacity style={styles.rangeButton} onPress={() => adjustDate(30)}><Text style={[styles.rangeButtonText, ghostText]}>{t('premiumUi.common.plusMonth')}</Text></TouchableOpacity>
        </View>

        {includeTime ? (
          <View style={[
            styles.timeRow,
            { borderTopColor: colors.cardBorder },
          ]}>
            <TouchableOpacity style={[styles.compactNavButton, ghostBtn]} onPress={() => adjustDate(-1, 'hour')} hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }}>
              <Text style={[styles.compactNavText, ghostText]}>-H</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.timeChip, accentBtn]} onPress={Platform.OS === 'web' ? undefined : openTimePicker} onLongPress={handleReset}>
              <Text style={[styles.compactDateText, { color: colors.onPrimary }]}>{timeLabel}</Text>
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
    marginTop: 14,
    marginBottom: 12,
    alignSelf: 'stretch',
  },
  navShell: {
    borderRadius: 20,
    borderWidth: 1,
    paddingVertical: 10,
    paddingHorizontal: 10,
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
    borderWidth: 1,
    borderRadius: 20,
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
  },
  dayStepButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rangeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 9,
    paddingTop: 9,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  rangeButton: {
    paddingVertical: 5,
    paddingHorizontal: 3,
  },
  rangeButtonText: {
    fontSize: 9,
    fontWeight: '700',
  },
  todayButton: {
    paddingHorizontal: 11,
    paddingVertical: 6,
    borderRadius: 999,
  },
  todayButtonText: {
    fontSize: 9,
    fontWeight: '800',
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
    flex: 1,
    height: 38,
    marginHorizontal: 10,
    paddingHorizontal: 10,
    borderRadius: 19,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 7,
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
  doneButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    alignSelf: 'center',
    marginTop: 10,
  },
  doneButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
});

export default DateNavigator;
