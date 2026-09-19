import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
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
  const { colors } = useTheme();
  if (!birthData) return null;

  const displayName = String(birthData.name || 'Selected chart');
  const labelColor = colors.selectionText || colors.text;
  const mutedColor = colors.selectionTextMuted || colors.textSecondary;

  return (
    <TouchableOpacity
      onPress={onPress}
      style={[
        styles.nameChip,
        {
          backgroundColor: colors.selectionSurface,
          borderColor: colors.selectionBorder || colors.cardBorder,
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
        style={[styles.nameChipText, { color: labelColor }, textStyle]}
        numberOfLines={1}
        ellipsizeMode="tail"
        adjustsFontSizeToFit
        minimumFontScale={0.78}
        maxFontSizeMultiplier={1.35}
        accessibilityElementsHidden
      >
        {displayName}
      </Text>
      <Ionicons name="chevron-down" size={12} color={iconColor || mutedColor} style={styles.dropdownIcon} />
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  nameChip: {
    paddingHorizontal: 12,
    minHeight: 44,
    paddingVertical: 6,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
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
