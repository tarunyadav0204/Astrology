import React, { useEffect, useMemo, useState } from 'react';
import {
  Modal,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../context/ThemeContext';
import WebWheelSpinner from './WebWheelSpinner';

const MONTH_LABELS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

const daysInMonth = (year, monthIndex) => new Date(year, monthIndex + 1, 0).getDate();

const startOfDay = (d) => {
  const next = new Date(d);
  next.setHours(12, 0, 0, 0);
  return next;
};

const clampDateParts = (year, monthIndex, day, minimumDate, maximumDate) => {
  const maxDay = daysInMonth(year, monthIndex);
  const safeDay = Math.min(Math.max(1, day), maxDay);
  let next = new Date(year, monthIndex, safeDay, 12, 0, 0, 0);
  if (minimumDate) {
    const min = startOfDay(minimumDate);
    if (next < min) next = min;
  }
  if (maximumDate) {
    const max = startOfDay(maximumDate);
    if (next > max) next = max;
  }
  return next;
};

/**
 * Native DateTimePicker is a no-op on web.
 * Matches Birth Form PWA spinner (day / month / year wheels).
 */
export default function WebDatePickerModal({
  visible,
  value,
  onChange,
  onClose,
  minimumDate,
  maximumDate,
  title = 'Select date',
}) {
  const { theme, colors } = useTheme();
  const insets = useSafeAreaInsets();
  const isDark = theme === 'dark';

  const initialDate = useMemo(() => {
    const base = value instanceof Date && !Number.isNaN(value.getTime())
      ? value
      : new Date();
    return clampDateParts(
      base.getFullYear(),
      base.getMonth(),
      base.getDate(),
      minimumDate,
      maximumDate,
    );
  }, [value, visible, minimumDate, maximumDate]);

  const [draft, setDraft] = useState(initialDate);

  useEffect(() => {
    if (visible) setDraft(initialDate);
  }, [visible, initialDate]);

  const minYear = minimumDate instanceof Date
    ? minimumDate.getFullYear()
    : 1900;
  const maxYear = maximumDate instanceof Date
    ? maximumDate.getFullYear()
    : new Date().getFullYear() + 5;

  const yearOptions = useMemo(() => {
    const years = [];
    for (let y = maxYear; y >= minYear; y -= 1) {
      years.push({ value: y, label: String(y) });
    }
    return years.length ? years : [{ value: new Date().getFullYear(), label: String(new Date().getFullYear()) }];
  }, [minYear, maxYear]);

  const dayOptions = useMemo(() => {
    const count = daysInMonth(draft.getFullYear(), draft.getMonth());
    return Array.from({ length: count }, (_, i) => ({ value: i + 1, label: String(i + 1) }));
  }, [draft]);

  const monthOptions = useMemo(
    () => MONTH_LABELS.map((label, index) => ({ value: index, label: label.slice(0, 3) })),
    [],
  );

  const textColor = colors?.text || (isDark ? '#fff' : '#111');
  const mutedColor = isDark ? 'rgba(255,255,255,0.2)' : 'rgba(249,115,22,0.35)';
  const sheetGradient = isDark
    ? ['rgba(31, 20, 18, 0.98)', 'rgba(18, 14, 16, 0.98)']
    : ['rgba(255, 247, 237, 0.98)', 'rgba(255, 255, 255, 0.98)'];
  const headerBorder = isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(249, 115, 22, 0.28)';
  const primary = colors?.primary || '#f97316';
  const secondary = colors?.textSecondary || (isDark ? 'rgba(255,255,255,0.65)' : '#666');

  if (Platform.OS !== 'web') return null;

  return (
    <Modal
      visible={!!visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <View style={[styles.overlay, { backgroundColor: isDark ? 'rgba(0,0,0,0.65)' : 'rgba(28,25,23,0.45)' }]}>
        <TouchableOpacity style={styles.backdrop} activeOpacity={1} onPress={onClose} />
        <View style={[styles.sheet, { borderTopColor: primary }]}>
          <LinearGradient
            colors={sheetGradient}
            style={[styles.sheetInner, { paddingBottom: Math.max(20, (insets?.bottom || 0) + 8) }]}
          >
            <View style={[styles.header, { borderBottomColor: headerBorder }]}>
              <TouchableOpacity onPress={onClose} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
                <Text style={[styles.headerBtn, { color: secondary }]}>Cancel</Text>
              </TouchableOpacity>
              <Text style={[styles.title, { color: textColor }]} numberOfLines={1}>{title}</Text>
              <TouchableOpacity
                onPress={() => {
                  onChange?.(draft);
                  onClose?.();
                }}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <Text style={[styles.headerBtn, styles.doneBtn, { color: primary }]}>Done</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.webWheelRow}>
              <WebWheelSpinner
                textColor={textColor}
                mutedColor={mutedColor}
                value={draft.getDate()}
                onChange={(day) => {
                  setDraft(clampDateParts(
                    draft.getFullYear(),
                    draft.getMonth(),
                    Number(day),
                    minimumDate,
                    maximumDate,
                  ));
                }}
                options={dayOptions}
              />
              <WebWheelSpinner
                textColor={textColor}
                mutedColor={mutedColor}
                value={draft.getMonth()}
                onChange={(month) => {
                  setDraft(clampDateParts(
                    draft.getFullYear(),
                    Number(month),
                    draft.getDate(),
                    minimumDate,
                    maximumDate,
                  ));
                }}
                options={monthOptions}
              />
              <WebWheelSpinner
                textColor={textColor}
                mutedColor={mutedColor}
                value={draft.getFullYear()}
                onChange={(year) => {
                  setDraft(clampDateParts(
                    Number(year),
                    draft.getMonth(),
                    draft.getDate(),
                    minimumDate,
                    maximumDate,
                  ));
                }}
                options={yearOptions}
              />
            </View>
          </LinearGradient>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
  },
  sheet: {
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    borderTopWidth: 3,
    overflow: 'hidden',
    zIndex: 1,
  },
  sheetInner: {
    paddingBottom: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  title: {
    flex: 1,
    textAlign: 'center',
    fontSize: 15,
    fontWeight: '700',
    marginHorizontal: 8,
  },
  headerBtn: {
    fontSize: 17,
    fontWeight: '400',
    minWidth: 64,
  },
  doneBtn: {
    fontWeight: '700',
    textAlign: 'right',
  },
  webWheelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 8,
    gap: 8,
  },
});
