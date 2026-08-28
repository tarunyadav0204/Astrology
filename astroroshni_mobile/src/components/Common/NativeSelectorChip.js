import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { COLORS } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import Ionicons from '@expo/vector-icons/Ionicons';

const NativeSelectorChip = ({
  birthData,
  onPress,
  style,
  textStyle,
  iconColor,
  showIcon = true
}) => {
  const { theme, colors, isPanditMode } = useTheme();
  if (!birthData) return null;

  const displayName = String(birthData.name || 'Selected chart');

  const chipBg = theme === 'dark'
    ? 'rgba(255, 255, 255, 0.15)'
    : isPanditMode
      ? 'rgba(24, 24, 27, 0.06)'
      : 'rgba(249, 115, 22, 0.15)';
  const chipBorder = theme === 'dark'
    ? 'rgba(255, 255, 255, 0.2)'
    : isPanditMode
      ? 'rgba(24, 24, 27, 0.12)'
      : 'rgba(249, 115, 22, 0.2)';

  return (
    <TouchableOpacity
      onPress={onPress}
      style={[
        styles.nameChip,
        {
          backgroundColor: chipBg,
          borderColor: chipBorder,
        },
        style
      ]}
      activeOpacity={0.7}
      hitSlop={{ top: 10, bottom: 10, left: 4, right: 4 }}
      accessibilityRole="button"
      accessibilityLabel={`Change chart. Current chart: ${displayName}`}
      accessibilityHint="Opens the birth chart selector"
    >
      {showIcon && <Text style={styles.chipIcon}>👤</Text>}
      <Text
        style={[styles.nameChipText, { color: colors.textSecondary }, textStyle]}
        numberOfLines={1}
        ellipsizeMode="tail"
        adjustsFontSizeToFit
        minimumFontScale={0.78}
        maxFontSizeMultiplier={1.35}
        accessibilityElementsHidden
      >
        {displayName}
      </Text>
      <Ionicons name="chevron-down" size={12} color={iconColor || colors.textTertiary} style={styles.dropdownIcon} />
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  nameChip: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    paddingHorizontal: 12,
    minHeight: 44,
    paddingVertical: 6,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  chipIcon: {
    fontSize: 12,
    marginRight: 4,
  },
  nameChipText: {
    flexShrink: 1,
    minWidth: 0,
    fontSize: 12,
    fontWeight: '600',
  },
  dropdownIcon: {
    marginLeft: 4,
  },
});

export default NativeSelectorChip;
